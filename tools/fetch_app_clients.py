#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 The OSverflow Project
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import io
import os
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from verify_source import load_app_clients_manifest, verify_app_client_files  # noqa: E402


def copy_limited(source: object, destination: Path, maximum: int) -> None:
    written = 0
    with destination.open("wb") as output:
        while chunk := source.read(1024 * 1024):
            written += len(chunk)
            if written > maximum:
                raise SystemExit(f"download exceeds pinned size: {destination.name}")
            output.write(chunk)
        output.flush()
        os.fsync(output.fileno())


def fetch(output: Path, timeout: int) -> None:
    output = output.resolve()
    if output.exists():
        raise SystemExit(f"output path already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest = load_app_clients_manifest()
    entries = manifest["files"]
    assert isinstance(entries, list)

    with tempfile.TemporaryDirectory(prefix=f".{output.name}.", dir=output.parent) as temporary:
        result = Path(temporary) / "result"
        result.mkdir()
        for entry in entries:
            request = urllib.request.Request(
                str(entry["url"]), headers={"User-Agent": "OSverflow-input-fetch/1"}
            )
            with urllib.request.urlopen(request, timeout=timeout) as response:
                copy_limited(response, result / str(entry["filename"]), int(entry["size"]))
        verify_app_client_files(result, entries)
        os.replace(result, output)
    print(f"LYRIQ_APP_CLIENTS_FETCH_OK output={output}")


def self_check() -> None:
    payload = b"app-client-fetch-check\n"
    with tempfile.TemporaryDirectory(prefix="lyriq-app-fetch-") as temporary:
        destination = Path(temporary) / "payload.apk"
        copy_limited(io.BytesIO(payload), destination, len(payload))
        assert destination.read_bytes() == payload
        try:
            copy_limited(io.BytesIO(payload + b"x"), destination, len(payload))
        except SystemExit:
            pass
        else:
            raise SystemExit("app-client downloader accepted an oversized payload")
    print("LYRIQ_APP_CLIENTS_FETCHER_TEST_OK")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch hash-pinned Lyriq app clients")
    parser.add_argument("output", nargs="?", type=Path)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> None:
    arguments = parse_args()
    if arguments.self_test:
        if arguments.output is not None:
            raise SystemExit("--self-test does not accept an output path")
        self_check()
        return
    if arguments.output is None:
        raise SystemExit("output path is required")
    if arguments.timeout <= 0:
        raise SystemExit("--timeout must be positive")
    fetch(arguments.output, arguments.timeout)


if __name__ == "__main__":
    main()
