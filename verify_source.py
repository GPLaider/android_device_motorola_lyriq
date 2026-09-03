#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 The OSverflow Project
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ElementTree
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "prebuilts/manifest.json"

REQUIRED = (
    "README.md",
    "LICENSE",
    "NOTICE",
    "SECURITY.md",
    "Android.bp",
    "AndroidProducts.mk",
    "BoardConfig.mk",
    "device.mk",
    "osverflow_lyriq.mk",
    "prebuilt-images.mk",
    "lyriq-release-gate.mk",
    "prebuilts/manifest.json",
    "docs/INPUTS.md",
    "docs/PROVENANCE.md",
    "docs/RELEASE_GATES.md",
)

FORBIDDEN_SUFFIXES = {
    ".img", ".bin", ".zip", ".apk", ".apex", ".pk8", ".pem", ".key",
    ".p12", ".pfx", ".jks", ".keystore", ".der", ".class", ".pyc",
    ".orig", ".webp", ".png", ".mp4",
}

TEXT_PATTERNS = (
    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"), "private key"),
    (re.compile(r"LPA:1\$", re.IGNORECASE), "eSIM activation code"),
    (re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+", re.IGNORECASE), "local Windows path"),
    (re.compile(r"/mnt/(?:buildrouter|[a-z])/(?:Users/)?[^\s]+", re.IGNORECASE), "local build path"),
    (re.compile(r"\bZY[0-9A-Z]{8,}\b"), "device serial"),
)

SOURCE_FORBIDDEN = (
    "config_defaultPifConfig",
    "spoofBuild=true",
    "spoofSignature=true",
    "PRODUCT_AVF_ENABLED := true",
    "init.lyriq.esim.rc",
    "android.hardware.telephony.euicc.xml",
    "TARGET_BOOTANIMATION :=",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_files() -> list[Path]:
    if (ROOT / ".git").is_dir():
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
        )
        return [ROOT / item.decode("utf-8") for item in result.stdout.split(b"\0") if item]
    return [path for path in ROOT.rglob("*") if path.is_file() and ".git" not in path.parts]


def load_manifest() -> dict[str, object]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("schema") != 1 or manifest.get("device") != "lyriq":
        raise SystemExit("invalid Lyriq prebuilt manifest identity")
    if manifest.get("models") != ["XT2303-2"]:
        raise SystemExit("invalid supported model set")
    if manifest.get("stock_payload_build") != "V1TLS35.73-60-3-10/40dcc-72d036":
        raise SystemExit("unexpected stock payload contract")
    entries = manifest.get("files")
    if not isinstance(entries, list) or not entries:
        raise SystemExit("empty prebuilt contract")
    names: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise SystemExit("invalid prebuilt entry")
        name = entry.get("name")
        size = entry.get("size")
        digest = entry.get("sha256")
        if not isinstance(name, str) or Path(name).name != name or name in names:
            raise SystemExit(f"invalid or duplicate prebuilt name: {name}")
        if not isinstance(size, int) or size <= 0:
            raise SystemExit(f"invalid prebuilt size: {name}")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise SystemExit(f"invalid prebuilt digest: {name}")
        names.add(name)
    contract_digest = sha256(MANIFEST)
    release_gate = (ROOT / "lyriq-release-gate.mk").read_text(encoding="utf-8")
    if contract_digest not in release_gate:
        raise SystemExit("make gate is not bound to the current prebuilt manifest")
    return manifest


def verify_tree() -> None:
    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            raise SystemExit(f"missing required source: {relative}")

    for path in source_files():
        relative = path.relative_to(ROOT)
        if path.is_symlink():
            raise SystemExit(f"tracked symlink not allowed: {relative}")
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            raise SystemExit(f"binary, generated, or key artifact not allowed: {relative}")
        data = path.read_bytes()
        if b"\x00" in data:
            raise SystemExit(f"binary content not allowed: {relative}")
        text = data.decode("utf-8")
        for pattern, label in TEXT_PATTERNS:
            if pattern.search(text):
                raise SystemExit(f"{label} detected in {relative}")
        if path.suffix.lower() in {".bp", ".mk", ".py", ".rc", ".te", ".xml"}:
            if "SPDX-License-Identifier: Apache-2.0" not in text:
                raise SystemExit(f"missing Apache-2.0 SPDX marker: {relative}")
        if path.suffix.lower() == ".xml":
            try:
                ElementTree.fromstring(text)
            except ElementTree.ParseError as error:
                raise SystemExit(f"invalid XML in {relative}: {error}") from error

    integration = "\n".join(
        (ROOT / relative).read_text(encoding="utf-8")
        for relative in ("BoardConfig.mk", "device.mk", "osverflow_lyriq.mk", "prebuilt-images.mk")
    )
    for marker in SOURCE_FORBIDDEN:
        if marker in integration:
            raise SystemExit(f"excluded experiment entered build integration: {marker}")


def verify_prebuilt_files(root: Path, entries: list[dict[str, object]]) -> None:
    for entry in entries:
        path = root / str(entry["name"])
        if not path.is_file():
            raise SystemExit(f"missing local prebuilt: {path.name}")
        if path.stat().st_size != entry["size"]:
            raise SystemExit(f"size mismatch: {path.name}")
        if sha256(path) != entry["sha256"]:
            raise SystemExit(f"SHA-256 mismatch: {path.name}")


def self_check() -> None:
    payload = b"lyriq-contract-check\n"
    entry: dict[str, object] = {
        "name": "fixture.dat",
        "size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }
    with tempfile.TemporaryDirectory(prefix="lyriq-contract-") as directory:
        path = Path(directory) / "fixture.dat"
        path.write_bytes(payload)
        verify_prebuilt_files(path.parent, [entry])
        path.write_bytes(payload + b"x")
        try:
            verify_prebuilt_files(path.parent, [entry])
        except SystemExit:
            pass
        else:
            raise SystemExit("prebuilt verifier accepted a modified payload")


def write_stamp(path: Path, manifest: dict[str, object]) -> None:
    content = (
        "LYRIQ_PRODUCTION_GATE_STATUS := OK\n"
        "LYRIQ_GATE_DEVICE := lyriq\n"
        f"LYRIQ_GATE_STOCK_PAYLOAD_BUILD := {manifest['stock_payload_build']}\n"
        f"LYRIQ_GATE_CONTRACT_SHA256 := {sha256(MANIFEST)}\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify the Lyriq source and local input contract")
    parser.add_argument("--prebuilts", type=Path)
    parser.add_argument("--stamp", type=Path)
    return parser.parse_args()


def main() -> None:
    arguments = parse_args()
    if arguments.stamp is not None and arguments.prebuilts is None:
        raise SystemExit("--stamp requires --prebuilts")
    verify_tree()
    manifest = load_manifest()
    self_check()
    if arguments.prebuilts is not None:
        entries = manifest["files"]
        assert isinstance(entries, list)
        verify_prebuilt_files(arguments.prebuilts.resolve(), entries)
        if arguments.stamp is not None:
            write_stamp(arguments.stamp.resolve(), manifest)
        print("LYRIQ_PREBUILT_CONTRACT_OK")
    print("LYRIQ_DEVICE_SOURCE_OK")


if __name__ == "__main__":
    main()
