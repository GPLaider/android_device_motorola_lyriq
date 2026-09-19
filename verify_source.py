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
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
CONTRACTS = {
    "3-10": ROOT / "prebuilts/manifest.json",
    "3-14": ROOT / "prebuilts/manifest-3-14.json",
}
KERNEL_REFERENCE = ROOT / "kernel-source-reference.json"
STOCK_IMS_MANIFEST = ROOT / "prebuilts/stock-ims-manifest.json"
APP_CLIENTS_MANIFEST = ROOT / "prebuilts/app-clients-manifest.json"
EUICC_MANIFEST = ROOT / "prebuilts/euicc-v7-manifest.json"

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
    "stock-contracts.mk",
    "kernel-source-reference.json",
    "prebuilts/manifest.json",
    "prebuilts/manifest-3-14.json",
    "prebuilts/stock-ims-manifest.json",
    "prebuilts/app-clients-manifest.json",
    "prebuilts/euicc-v7-manifest.json",
    "stock-ims/NOTICE",
    "stock-ims/permissions/privapp-permissions-lyriq-stock-ims.xml",
    "app-clients/NOTICE",
    "euicc/NOTICE",
    "docs/INPUTS.md",
    "docs/KERNEL_SOURCE.md",
    "docs/PROVENANCE.md",
    "docs/RELEASE_GATES.md",
    "tools/extract_stock.py",
    "tools/test_extract_stock.py",
    "tools/fetch_app_clients.py",
)

FORBIDDEN_SUFFIXES = {
    ".img", ".bin", ".zip", ".apk", ".apex", ".pk8", ".pem", ".key",
    ".p12", ".pfx", ".jks", ".keystore", ".der", ".class", ".pyc",
    ".orig", ".webp", ".png", ".mp4",
}

# Intentional binary inputs are only allowed when pinned by a sibling
# <name>.sha256 file whose recorded digest matches the on-disk artifact.
HASH_PINNED_ARTIFACTS = {
    "bootanimation.zip": "bootanimation.sha256",
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
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_files() -> list[Path]:
    if (ROOT / ".git").exists():
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
        )
        return [ROOT / item.decode("utf-8") for item in result.stdout.split(b"\0") if item]
    ignored_roots = {".local-prebuilts", ".local-signing", "__pycache__"}
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and not ignored_roots.intersection(path.relative_to(ROOT).parts)
        and not path.name.endswith((".stamp.mk", ".pyc"))
    ]


def load_manifest(contract_id: str = "3-10") -> dict[str, object]:
    path = CONTRACTS.get(contract_id)
    if path is None:
        raise SystemExit(f"unknown stock contract: {contract_id}")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("schema") != 1 or manifest.get("device") != "lyriq":
        raise SystemExit("invalid Lyriq prebuilt manifest identity")
    if manifest.get("contract_id") != contract_id:
        raise SystemExit(f"stock contract ID mismatch: {contract_id}")
    if manifest.get("models") != ["XT2303-2"]:
        raise SystemExit("invalid supported model set")
    for key in ("stock_payload_build", "boot_fingerprint", "software_build_fingerprint"):
        if not isinstance(manifest.get(key), str) or not manifest[key]:
            raise SystemExit(f"missing stock contract field: {key}")
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
    return manifest


def safe_relative_path(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise SystemExit(f"invalid {label}: {value}")
    path = PurePosixPath(value)
    if path.is_absolute() or str(path) != value or any(part in {"", ".", ".."} for part in path.parts):
        raise SystemExit(f"invalid {label}: {value}")
    return value


def load_stock_ims_manifest() -> dict[str, object]:
    manifest = json.loads(STOCK_IMS_MANIFEST.read_text(encoding="utf-8"))
    if set(manifest) != {"schema", "device", "compatible_contracts", "files"}:
        raise SystemExit("invalid stock IMS manifest fields")
    if (
        manifest.get("schema") != 1
        or manifest.get("device") != "lyriq"
        or manifest.get("compatible_contracts") != list(CONTRACTS)
    ):
        raise SystemExit("invalid stock IMS manifest identity")
    entries = manifest.get("files")
    if not isinstance(entries, list) or len(entries) != 27:
        raise SystemExit("stock IMS contract must contain exactly 27 files")

    sources: set[tuple[str, str]] = set()
    destinations: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {
            "partition", "source_path", "destination", "size", "sha256"
        }:
            raise SystemExit("invalid stock IMS entry fields")
        partition = entry.get("partition")
        if partition not in {"system", "system_ext", "vendor"}:
            raise SystemExit(f"invalid stock IMS partition: {partition}")
        source = safe_relative_path(entry.get("source_path"), "stock IMS source path")
        destination = safe_relative_path(entry.get("destination"), "stock IMS destination")
        source_key = (str(partition), source)
        if source_key in sources or destination in destinations:
            raise SystemExit(f"duplicate stock IMS mapping: {destination}")
        size = entry.get("size")
        digest = entry.get("sha256")
        if not isinstance(size, int) or size <= 0:
            raise SystemExit(f"invalid stock IMS size: {destination}")
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise SystemExit(f"invalid stock IMS digest: {destination}")
        sources.add(source_key)
        destinations.add(destination)
    return manifest


def load_app_clients_manifest() -> dict[str, object]:
    manifest = json.loads(APP_CLIENTS_MANIFEST.read_text(encoding="utf-8"))
    if set(manifest) != {"schema", "device", "files"}:
        raise SystemExit("invalid app-client manifest fields")
    if manifest.get("schema") != 1 or manifest.get("device") != "lyriq":
        raise SystemExit("invalid app-client manifest identity")
    entries = manifest.get("files")
    if not isinstance(entries, list) or len(entries) != 2:
        raise SystemExit("app-client contract must contain exactly two APKs")

    expected = {
        "FDroid": {
            "filename": "FDroid-1.23.2.apk",
            "package_name": "org.fdroid.fdroid",
            "version_code": 1023052,
            "version_name": "1.23.2",
            "url": "https://f-droid.org/repo/org.fdroid.fdroid_1023052.apk",
            "source_url": "https://f-droid.org/repo/org.fdroid.fdroid_1023052_src.tar.gz",
            "license": "GPL-3.0-or-later",
        },
        "GrapheneOSApps": {
            "filename": "GrapheneOSAppStore-36.apk",
            "package_name": "app.grapheneos.apps",
            "version_code": 36,
            "version_name": "36",
            "url": "https://github.com/GrapheneOS/AppStore/releases/download/36/AppStore-36.apk",
            "source_url": "https://github.com/GrapheneOS/AppStore/tree/9bdf70a2c9a2dd757fe163c599907dcda3960c62",
            "license": "MIT",
        },
    }
    modules: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {
            "module", "filename", "package_name", "version_code", "version_name",
            "url", "source_url", "license", "size", "sha256", "certificate_sha256"
        }:
            raise SystemExit("invalid app-client entry fields")
        module = entry.get("module")
        if not isinstance(module, str) or module in modules or module not in expected:
            raise SystemExit(f"invalid or duplicate app-client module: {module}")
        pinned = expected[module]
        for key, value in pinned.items():
            if entry.get(key) != value:
                raise SystemExit(f"unexpected app-client {key}: {module}")
        filename = safe_relative_path(entry.get("filename"), "app-client filename")
        if PurePosixPath(filename).name != filename or not filename.endswith(".apk"):
            raise SystemExit(f"invalid app-client filename: {filename}")
        for key in ("url", "source_url"):
            parsed = urlsplit(str(entry[key]))
            if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
                raise SystemExit(f"invalid app-client HTTPS URL: {module}")
        size = entry.get("size")
        if not isinstance(size, int) or size <= 0:
            raise SystemExit(f"invalid app-client size: {module}")
        for key in ("sha256", "certificate_sha256"):
            digest = entry.get(key)
            if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                raise SystemExit(f"invalid app-client {key}: {module}")
        modules.add(module)
    return manifest


def load_euicc_manifest() -> dict[str, object]:
    manifest = json.loads(EUICC_MANIFEST.read_text(encoding="utf-8"))
    if set(manifest) != {
        "schema", "device", "profile", "compatible_stock_contracts",
        "files", "apk_certificates"
    }:
        raise SystemExit("invalid eUICC closure manifest fields")
    if (
        manifest.get("schema") != 1
        or manifest.get("device") != "lyriq"
        or manifest.get("profile") != "oem-de-dsds-v7"
        or manifest.get("compatible_stock_contracts") != ["3-10"]
    ):
        raise SystemExit("invalid eUICC closure identity")
    entries = manifest.get("files")
    if not isinstance(entries, list) or len(entries) != 5:
        raise SystemExit("eUICC closure must contain exactly five files")
    destinations: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"destination", "size", "sha256"}:
            raise SystemExit("invalid eUICC closure entry fields")
        destination = safe_relative_path(entry.get("destination"), "eUICC destination")
        if destination in destinations:
            raise SystemExit(f"duplicate eUICC destination: {destination}")
        if not isinstance(entry.get("size"), int) or int(entry["size"]) <= 0:
            raise SystemExit(f"invalid eUICC size: {destination}")
        if not isinstance(entry.get("sha256"), str) or re.fullmatch(
            r"[0-9a-f]{64}", str(entry["sha256"])
        ) is None:
            raise SystemExit(f"invalid eUICC digest: {destination}")
        destinations.add(destination)
    certificates = manifest.get("apk_certificates")
    if not isinstance(certificates, dict) or set(certificates) != {
        "euicc/priv-app/EuiccGoogle/EuiccGoogle.apk",
        "euicc/app/EuiccPartnerApp/EuiccPartnerApp.apk",
    }:
        raise SystemExit("invalid eUICC APK certificate map")
    if any(re.fullmatch(r"[0-9a-f]{64}", str(value)) is None for value in certificates.values()):
        raise SystemExit("invalid eUICC APK certificate digest")
    return manifest


def verify_contract_bindings() -> None:
    bindings = (ROOT / "stock-contracts.mk").read_text(encoding="utf-8")
    for contract_id, path in CONTRACTS.items():
        manifest = load_manifest(contract_id)
        for value in (
            sha256(path),
            manifest["stock_payload_build"],
            manifest["boot_fingerprint"],
        ):
            if str(value) not in bindings:
                raise SystemExit(f"make gate is not bound to stock contract {contract_id}")
    if sha256(STOCK_IMS_MANIFEST) not in bindings:
        raise SystemExit("make gate is not bound to the stock IMS contract")
    if sha256(APP_CLIENTS_MANIFEST) not in bindings:
        raise SystemExit("make gate is not bound to the app-client contract")
    if sha256(EUICC_MANIFEST) not in bindings:
        raise SystemExit("make gate is not bound to the eUICC closure")


def verify_kernel_reference() -> None:
    reference = json.loads(KERNEL_REFERENCE.read_text(encoding="utf-8"))
    if (
        reference.get("schema") != 1
        or reference.get("device") != "lyriq"
        or reference.get("status") != "reference-only-not-reproducible"
        or reference.get("live_kernel_release")
        != "6.6.89-android15-8-gdcee9aa4fcbc-ab14676413-4k"
    ):
        raise SystemExit("invalid Lyriq kernel-source reference identity")
    if reference.get("gki") != {
        "repository": "https://android.googlesource.com/kernel/common",
        "tag": "android15-6.6-2025-06_r38",
        "commit": "dcee9aa4fcbcdddb2cebcf0861342ad61af662f5",
        "ci_build_id": 14676413,
    }:
        raise SystemExit("unexpected Lyriq GKI source reference")
    if (
        reference.get("motorola_release_branch")
        != "android-15-release-v1tl35.73-60-3"
        or reference.get("motorola_repositories")
        != [
            {
                "repository": "https://github.com/MotorolaMobilityLLC/kernel-mtk",
                "commit": "945dea4ed4b43c260eb9fb6135115bccd62bd80d",
            },
            {
                "repository": "https://github.com/MotorolaMobilityLLC/kernel-kernel_device_modules-6.6",
                "commit": "1a9caf9b0398f0bcb59538decfcb68d4067543bb",
            },
            {
                "repository": "https://github.com/MotorolaMobilityLLC/motorola-kernel-modules",
                "commit": "d238112737a64f6d3eb47b2fce266f9c0b21c6c3",
            },
            {
                "repository": "https://github.com/MotorolaMobilityLLC/vendor-mediatek-kernel_modules-mtkcam",
                "commit": "226de36e40cbfc09496838491dfa7b85e1cdfd01",
            },
            {
                "repository": "https://github.com/MotorolaMobilityLLC/vendor-mediatek-kernel_modules-gpu",
                "commit": "7cdfce8d90a2ef4c6b11e7f60dcad6314445a77f",
            },
        ]
    ):
        raise SystemExit("unexpected Motorola kernel-source reference")
    if reference.get("unresolved_external_repositories") != [
        "vendor-mediatek-kernel_modules-connectivity-common",
        "vendor-mediatek-kernel_modules-connectivity-conninfra",
        "vendor-mediatek-kernel_modules-connectivity-connfem",
        "vendor-mediatek-kernel_modules-connectivity-gps",
        "vendor-mediatek-kernel_modules-connectivity-fmradio",
        "vendor-mediatek-kernel_modules-connectivity-wlan-adaptor",
        "vendor-mediatek-kernel_modules-connectivity-bt-linux_v2",
        "vendor-mediatek-kernel_modules-hbt_driver_cus",
    ]:
        raise SystemExit("kernel external-module gap is not recorded")
    if reference.get("unresolved_vendor_module_release_prefix") != "dd1959dca923":
        raise SystemExit("vendor-module source gap is not recorded")
    if reference.get("unmapped_build_paths") != [
        "vendor/mediatek/tests/kernel/ktf_testcase"
    ]:
        raise SystemExit("kernel unmapped build path is not recorded")


def verify_tree() -> None:
    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            raise SystemExit(f"missing required source: {relative}")

    for path in source_files():
        relative = path.relative_to(ROOT)
        if path.is_symlink():
            raise SystemExit(f"tracked symlink not allowed: {relative}")
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            anchor = HASH_PINNED_ARTIFACTS.get(relative.as_posix())
            if anchor is None:
                raise SystemExit(f"binary, generated, or key artifact not allowed: {relative}")
            anchor_path = ROOT / anchor
            if not anchor_path.is_file():
                raise SystemExit(f"hash anchor missing for pinned artifact: {relative}")
            anchor_fields = anchor_path.read_text(encoding="utf-8").split()
            if (
                len(anchor_fields) != 2
                or anchor_fields[1] != relative.name
                or re.fullmatch(r"[0-9a-f]{64}", anchor_fields[0]) is None
            ):
                raise SystemExit(f"malformed hash anchor for pinned artifact: {relative}")
            if sha256(path) != anchor_fields[0]:
                raise SystemExit(f"pinned artifact hash mismatch: {relative}")
            continue
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

    bootanimation_assignments = re.findall(
        r"^TARGET_BOOTANIMATION\s*:=\s*(\S+)\s*$", integration, re.MULTILINE
    )
    if bootanimation_assignments != ["//device/motorola/lyriq:OSverflowBootAnimation"]:
        raise SystemExit("boot animation integration does not reference the pinned module")

    gmscompat_inherit = "$(call inherit-product, packages/apps/GmsCompat/product.mk)"
    if (ROOT / "osverflow_lyriq.mk").read_text(encoding="utf-8").count(gmscompat_inherit) != 1:
        raise SystemExit("GmsCompat product integration must occur exactly once")

    lunch_choices = (ROOT / "AndroidProducts.mk").read_text(encoding="utf-8")
    for variant in ("user", "userdebug"):
        choice = f"osverflow_lyriq-bp4a-{variant}"
        if choice not in lunch_choices:
            raise SystemExit(f"missing Lyriq lunch choice: {choice}")

    stock_ims = load_stock_ims_manifest()
    entries = stock_ims["files"]
    assert isinstance(entries, list)
    expected = {str(entry["destination"]) for entry in entries}
    android_bp = (ROOT / "Android.bp").read_text(encoding="utf-8")
    referenced = set(re.findall(r'"\.local-prebuilts/stock-ims/([^"\]]+)"', android_bp))
    if referenced != expected:
        missing = sorted(expected - referenced)
        extra = sorted(referenced - expected)
        raise SystemExit(f"stock IMS build mapping mismatch: missing={missing}, extra={extra}")

    app_clients = load_app_clients_manifest()
    app_entries = app_clients["files"]
    assert isinstance(app_entries, list)
    expected_apps = {str(entry["filename"]) for entry in app_entries}
    referenced_apps = set(
        re.findall(r'"\.local-prebuilts/app-clients/([^"\]]+)"', android_bp)
    )
    if referenced_apps != expected_apps:
        missing = sorted(expected_apps - referenced_apps)
        extra = sorted(referenced_apps - expected_apps)
        raise SystemExit(f"app-client build mapping mismatch: missing={missing}, extra={extra}")

    euicc = load_euicc_manifest()
    euicc_entries = euicc["files"]
    assert isinstance(euicc_entries, list)
    expected_euicc = {
        str(entry["destination"])[len("euicc/"):]
        for entry in euicc_entries if str(entry["destination"]).startswith("euicc/")
    }
    referenced_euicc = set(re.findall(r'"\.local-prebuilts/euicc/([^"\]]+)"', android_bp))
    if referenced_euicc != expected_euicc:
        raise SystemExit("eUICC build mapping does not match its closure manifest")


def verify_prebuilt_files(root: Path, entries: list[dict[str, object]]) -> None:
    verify_local_files(root, entries, "name")


def verify_stock_ims_files(root: Path, entries: list[dict[str, object]]) -> None:
    verify_local_files(root, entries, "destination")


def verify_app_client_files(root: Path, entries: list[dict[str, object]]) -> None:
    verify_local_files(root, entries, "filename")


def verify_euicc_files(root: Path, entries: list[dict[str, object]]) -> None:
    verify_local_files(root, entries, "destination")


def verify_local_files(
    root: Path, entries: list[dict[str, object]], path_field: str
) -> None:
    for entry in entries:
        relative = str(entry[path_field])
        path = root / relative
        if not path.is_file():
            raise SystemExit(f"missing local prebuilt: {relative}")
        if path.stat().st_size != entry["size"]:
            raise SystemExit(f"size mismatch: {relative}")
        if sha256(path) != entry["sha256"]:
            raise SystemExit(f"SHA-256 mismatch: {relative}")


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

        nested = path.parent / "stock-ims/lib64/fixture.so"
        nested.parent.mkdir(parents=True)
        nested.write_bytes(payload)
        stock_entry = {**entry, "destination": "lib64/fixture.so"}
        verify_stock_ims_files(nested.parents[1], [stock_entry])
        nested.unlink()
        try:
            verify_stock_ims_files(nested.parents[1], [stock_entry])
        except SystemExit:
            pass
        else:
            raise SystemExit("stock IMS verifier accepted a missing payload")


def write_stamp(path: Path, manifest: dict[str, object]) -> None:
    contract_id = str(manifest["contract_id"])
    content = (
        "LYRIQ_PRODUCTION_GATE_STATUS := OK\n"
        "LYRIQ_GATE_DEVICE := lyriq\n"
        f"LYRIQ_GATE_CONTRACT_ID := {contract_id}\n"
        f"LYRIQ_GATE_STOCK_PAYLOAD_BUILD := {manifest['stock_payload_build']}\n"
        f"LYRIQ_GATE_CONTRACT_SHA256 := {sha256(CONTRACTS[contract_id])}\n"
        f"LYRIQ_GATE_STOCK_IMS_CONTRACT_SHA256 := {sha256(STOCK_IMS_MANIFEST)}\n"
        f"LYRIQ_GATE_APP_CLIENTS_CONTRACT_SHA256 := {sha256(APP_CLIENTS_MANIFEST)}\n"
        f"LYRIQ_GATE_EUICC_CLOSURE_SHA256 := {sha256(EUICC_MANIFEST)}\n"
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
    parser.add_argument("--contract", choices=tuple(CONTRACTS), default="3-10")
    parser.add_argument("--prebuilts", type=Path)
    parser.add_argument("--stamp", type=Path)
    return parser.parse_args()


def main() -> None:
    arguments = parse_args()
    if arguments.stamp is not None and arguments.prebuilts is None:
        raise SystemExit("--stamp requires --prebuilts")
    verify_tree()
    verify_contract_bindings()
    verify_kernel_reference()
    manifest = load_manifest(arguments.contract)
    stock_ims = load_stock_ims_manifest()
    app_clients = load_app_clients_manifest()
    euicc = load_euicc_manifest()
    self_check()
    if arguments.prebuilts is not None:
        entries = manifest["files"]
        assert isinstance(entries, list)
        verify_prebuilt_files(
            arguments.prebuilts.resolve(),
            [entry for entry in entries if entry["name"] != "vendor.img"],
        )
        ims_entries = stock_ims["files"]
        assert isinstance(ims_entries, list)
        verify_stock_ims_files(arguments.prebuilts.resolve() / "stock-ims", ims_entries)
        app_entries = app_clients["files"]
        assert isinstance(app_entries, list)
        verify_app_client_files(arguments.prebuilts.resolve() / "app-clients", app_entries)
        euicc_entries = euicc["files"]
        assert isinstance(euicc_entries, list)
        verify_euicc_files(arguments.prebuilts.resolve(), euicc_entries)
        if arguments.stamp is not None:
            write_stamp(arguments.stamp.resolve(), manifest)
        print("LYRIQ_STOCK_IMS_CONTRACT_OK")
        print("LYRIQ_APP_CLIENTS_CONTRACT_OK")
        print("LYRIQ_EUICC_CLOSURE_OK")
        print("LYRIQ_PREBUILT_CONTRACT_OK")
    print("LYRIQ_DEVICE_SOURCE_OK")


if __name__ == "__main__":
    main()
