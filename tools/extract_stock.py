#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 The OSverflow Project
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ElementTree
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from verify_source import (  # noqa: E402
    CONTRACTS,
    load_manifest,
    load_stock_ims_manifest,
    verify_prebuilt_files,
    verify_stock_ims_files,
)

DIRECT_IMAGES = ("boot.img", "dtbo.img", "vendor_boot.img")
SUPER_PARTITIONS = {
    "vendor_a.img": "vendor.img",
    "vendor_dlkm_a.img": "vendor_dlkm.img",
    "system_dlkm_a.img": "system_dlkm.img",
}
STOCK_IMS_PARTITIONS = ("system_a", "system_ext_a")
CHUNK_PATTERN = re.compile(r"super\.img_sparsechunk\.(\d+)")


def md5(path: Path) -> str:
    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_tool(value: str) -> Path:
    candidate = Path(value)
    resolved = candidate.resolve() if candidate.is_file() else None
    if resolved is None:
        found = shutil.which(value)
        resolved = Path(found).resolve() if found else None
    if resolved is None or not resolved.is_file() or not os.access(resolved, os.X_OK):
        raise SystemExit(f"required executable not found: {value}")
    return resolved


def inspect_firmware(firmware: Path, contract: str) -> tuple[dict[str, Path], list[Path]]:
    firmware = firmware.resolve()
    if not firmware.is_dir():
        raise SystemExit(f"firmware directory not found: {firmware}")
    flashfile = firmware / "flashfile.xml"
    if not flashfile.is_file() or flashfile.is_symlink():
        raise SystemExit("missing regular flashfile.xml")

    try:
        document = ElementTree.parse(flashfile).getroot()
    except ElementTree.ParseError as error:
        raise SystemExit(f"invalid flashfile.xml: {error}") from error

    model = document.find("./header/phone_model")
    version = document.find("./header/software_version")
    release, incremental = contract.split("/", maxsplit=1)
    software = "" if version is None else version.get("version", "")
    expected = re.compile(
        rf"^lyriq_g-user 15 {re.escape(release)} {re.escape(incremental)} "
        r"release-keys(?: .+)?$"
    )
    if model is None or model.get("model") != "lyriq_g":
        raise SystemExit("firmware model is not lyriq_g")
    if expected.fullmatch(software) is None:
        raise SystemExit(f"firmware build does not match the pinned contract: {software}")

    manufacturer_md5: dict[str, str] = {}
    for step in document.findall("./steps/step"):
        name = step.get("filename")
        digest = step.get("MD5")
        if not name or not digest:
            continue
        digest = digest.lower()
        if re.fullmatch(r"[0-9a-f]{32}", digest) is None:
            raise SystemExit(f"invalid manufacturer MD5 for {name}")
        if name in manufacturer_md5 and manufacturer_md5[name] != digest:
            raise SystemExit(f"conflicting manufacturer MD5 for {name}")
        manufacturer_md5[name] = digest

    direct = {name: firmware / name for name in DIRECT_IMAGES}
    indexed_chunks: list[tuple[int, Path]] = []
    for path in firmware.glob("super.img_sparsechunk.*"):
        match = CHUNK_PATTERN.fullmatch(path.name)
        if match is None:
            raise SystemExit(f"invalid sparse-chunk name: {path.name}")
        indexed_chunks.append((int(match.group(1)), path))
    indexed_chunks.sort(key=lambda item: item[0])
    if not indexed_chunks:
        raise SystemExit("no super sparse chunks found")
    if [index for index, _ in indexed_chunks] != list(range(len(indexed_chunks))):
        raise SystemExit("super sparse chunks are not contiguous from zero")
    chunks = [path for _, path in indexed_chunks]

    for path in [*direct.values(), *chunks]:
        if not path.is_file() or path.is_symlink():
            raise SystemExit(f"missing regular firmware input: {path.name}")
        expected_md5 = manufacturer_md5.get(path.name)
        if expected_md5 is None:
            raise SystemExit(f"flashfile.xml has no MD5 for {path.name}")
        if md5(path) != expected_md5:
            raise SystemExit(f"manufacturer MD5 mismatch: {path.name}")
    return direct, chunks


def run_tool(arguments: list[Path | str]) -> None:
    result = subprocess.run(
        [str(argument) for argument in arguments],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.returncode:
        raise SystemExit(
            f"tool failed ({result.returncode}): {Path(str(arguments[0])).name}\n{result.stdout}"
        )


def extract_fstab(debugfs: Path, vendor: Path, destination: Path) -> None:
    result = subprocess.run(
        [str(debugfs), "-R", "cat /etc/fstab.mt6893", str(vendor)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise SystemExit(
            f"debugfs failed ({result.returncode}): {result.stderr.decode(errors='replace')}"
        )
    destination.write_bytes(result.stdout)


def extract_ext4_file(debugfs: Path, image: Path, source: str, destination: Path) -> None:
    result = subprocess.run(
        [str(debugfs), "-R", f"cat /{source}", str(image)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise SystemExit(
            f"debugfs failed ({result.returncode}): {result.stderr.decode(errors='replace')}"
        )
    destination.write_bytes(result.stdout)


def copy_regular_file(source: Path, destination: Path) -> None:
    if not source.is_file() or source.is_symlink():
        raise SystemExit(f"missing regular stock IMS input: {source}")
    shutil.copy2(source, destination)


def extract_stock_ims(
    fsck_erofs: Path,
    debugfs: Path,
    unpacked: Path,
    vendor: Path,
    work: Path,
    destination: Path,
) -> None:
    manifest = load_stock_ims_manifest()
    entries = manifest["files"]
    assert isinstance(entries, list)
    trees = {
        "system": work / "system",
        "system_ext": work / "system_ext",
    }
    for partition, tree in trees.items():
        run_tool(
            [
                fsck_erofs,
                f"--extract={tree}",
                unpacked / f"{partition}_a.img",
            ]
        )

    destination.mkdir()
    for entry in entries:
        partition = str(entry["partition"])
        source = str(entry["source_path"])
        target = destination / str(entry["destination"])
        target.parent.mkdir(parents=True, exist_ok=True)
        if partition == "vendor":
            extract_ext4_file(debugfs, vendor, source, target)
        else:
            copy_regular_file(trees[partition] / source, target)
    verify_stock_ims_files(destination, entries)


def extract(arguments: argparse.Namespace) -> None:
    manifest = load_manifest(arguments.contract)
    entries = manifest["files"]
    assert isinstance(entries, list)
    contract = manifest["stock_payload_build"]
    assert isinstance(contract, str)

    output = arguments.output.resolve()
    if output.exists():
        raise SystemExit(f"output path already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)

    simg2img = resolve_tool(arguments.simg2img)
    lpunpack = resolve_tool(arguments.lpunpack)
    debugfs = resolve_tool(arguments.debugfs)
    fsck_erofs = resolve_tool(arguments.fsck_erofs) if arguments.with_stock_ims else None
    direct, chunks = inspect_firmware(arguments.firmware, contract)

    with tempfile.TemporaryDirectory(prefix=f".{output.name}.", dir=output.parent) as temporary:
        work = Path(temporary)
        result = work / "result"
        unpacked = work / "unpacked"
        result.mkdir()
        unpacked.mkdir()
        raw_super = work / "super.raw.img"

        run_tool([simg2img, *chunks, raw_super])
        partitions = [name.removesuffix(".img") for name in SUPER_PARTITIONS]
        if arguments.with_stock_ims:
            partitions.extend(STOCK_IMS_PARTITIONS)
        lpunpack_arguments: list[Path | str] = [lpunpack]
        for partition in partitions:
            lpunpack_arguments.extend(("-p", partition))
        lpunpack_arguments.extend((raw_super, unpacked))
        run_tool(lpunpack_arguments)

        for name, source in direct.items():
            shutil.copy2(source, result / name)
        for source_name, output_name in SUPER_PARTITIONS.items():
            source = unpacked / source_name
            if not source.is_file():
                raise SystemExit(f"lpunpack did not produce {source_name}")
            os.replace(source, result / output_name)
        extract_fstab(debugfs, result / "vendor.img", result / "fstab.mt6893")

        if arguments.with_stock_ims:
            assert fsck_erofs is not None
            extract_stock_ims(
                fsck_erofs,
                debugfs,
                unpacked,
                result / "vendor.img",
                work,
                result / "stock-ims",
            )

        verify_prebuilt_files(result, entries)
        os.replace(result, output)

    print(f"LYRIQ_STOCK_EXTRACTION_OK output={output}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract hash-pinned Lyriq build inputs from Motorola Software Fix firmware"
    )
    parser.add_argument("firmware", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--contract", choices=tuple(CONTRACTS), default="3-10")
    parser.add_argument("--simg2img", default="simg2img")
    parser.add_argument("--lpunpack", default="lpunpack")
    parser.add_argument("--debugfs", default="debugfs")
    parser.add_argument("--fsck-erofs", default="fsck.erofs")
    parser.add_argument("--with-stock-ims", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    extract(parse_args())
