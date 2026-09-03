#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 The OSverflow Project
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from extract_stock import inspect_firmware  # noqa: E402


def manufacturer_md5(payload: bytes) -> str:
    return hashlib.md5(payload, usedforsecurity=False).hexdigest()


def main() -> None:
    files = {
        "boot.img": b"boot",
        "dtbo.img": b"dtbo",
        "vendor_boot.img": b"vendor-boot",
        "super.img_sparsechunk.0": b"chunk-zero",
        "super.img_sparsechunk.1": b"chunk-one",
    }
    with tempfile.TemporaryDirectory(prefix="lyriq-extractor-test-") as temporary:
        root = Path(temporary)
        for name, payload in files.items():
            (root / name).write_bytes(payload)
        steps = "\n".join(
            f'<step MD5="{manufacturer_md5(payload)}" filename="{name}" operation="flash" />'
            for name, payload in files.items()
        )
        (root / "flashfile.xml").write_text(
            "<flashing><header>"
            '<phone_model model="lyriq_g" />'
            '<software_version version="lyriq_g-user 15 TEST-BUILD TEST-INCREMENTAL release-keys" />'
            f"</header><steps>{steps}</steps></flashing>",
            encoding="utf-8",
        )
        _, chunks = inspect_firmware(root, "TEST-BUILD/TEST-INCREMENTAL")
        assert [path.name for path in chunks] == [
            "super.img_sparsechunk.0",
            "super.img_sparsechunk.1",
        ]
        (root / "boot.img").write_bytes(b"modified")
        try:
            inspect_firmware(root, "TEST-BUILD/TEST-INCREMENTAL")
        except SystemExit:
            pass
        else:
            raise AssertionError("modified manufacturer input was accepted")
    print("LYRIQ_STOCK_EXTRACTOR_TEST_OK")


if __name__ == "__main__":
    main()
