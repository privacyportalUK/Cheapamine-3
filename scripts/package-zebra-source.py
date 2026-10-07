#!/usr/bin/env python3
"""Package unchanged Zebra 1.1.37 sources and its pinned dependencies for release."""

import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import urllib.error
import urllib.request
import zipfile

MANIFEST = Path(__file__).resolve().parents[1] / "release" / "ZEBRA-SOURCE-MANIFEST.json"
EXPECTED_OUTPUT_SHA256 = "82474d45586c525cd964a9d953747ad98ebfb8cc5a0066de6ead45a33c20e07b"
MAX_INPUT_BYTES = 128 * 1024 * 1024
README = """Zebra 1.1.37 corresponding source materials

This archive contains the unchanged Zebra source at commit
61ba43b5d3ded7b7b4fd922e27b80c0124964243, including its license,
build scripts and Package.resolved. The other four ZIPs contain the exact
Swift package dependency revisions identified by that lockfile.

Each inner ZIP retains its upstream source tree, notices and licenses.
SOURCE-MANIFEST.json records the source repository, exact commit, download URL
and verified SHA-256 for each source archive. This distribution does not
relicense those components or imply endorsement by their authors.

The Zebra .deb distributed within Cheapmine 3 R3 is the unchanged official
1.1.37 rootless release asset, SHA-256:
962d7af1ea58dff44cc3cc4896533865b18aca10d1ac30cc8d7d8516cd781b9a

Zebra source: https://github.com/zbrateam/Zebra
Build instructions are included in Zebra's README.md and Makefile.
The outer ZIP is deterministic: fixed timestamps, file permissions, entry
order and uncompressed storage. Every downloaded input is hash-checked.
"""


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(entry, directory):
    """Download only a pinned codeload source archive and verify its exact bytes."""
    name = entry["archive"]
    if Path(name).name != name or not name.endswith(".zip"):
        raise ValueError("Invalid source archive name")
    if not entry["url"].startswith("https://codeload.github.com/"):
        raise ValueError("Source URL must use GitHub codeload")
    destination = directory / name
    for attempt in range(3):
        try:
            request = urllib.request.Request(entry["url"], headers={"User-Agent": "Cheapmine-3-source-package"})
            length = 0
            with urllib.request.urlopen(request, timeout=60) as response, destination.open("wb") as output:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    length += len(chunk)
                    if length > MAX_INPUT_BYTES:
                        raise ValueError("Source archive exceeds size limit")
                    output.write(chunk)
            actual = sha256_file(destination)
            if actual != entry["sha256"]:
                raise ValueError("SHA-256 mismatch for " + name + ": " + actual)
            with zipfile.ZipFile(destination) as archive:
                if archive.testzip() is not None:
                    raise ValueError("Invalid source ZIP: " + name)
            return name, destination
        except (urllib.error.URLError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(attempt + 1)
    raise RuntimeError("Download did not complete")


def write_entry(archive, name, data):
    info = zipfile.ZipInfo("Zebra-1.1.37-sources/" + name, date_time=(1980, 1, 1, 0, 0, 0))
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    info.compress_type = zipfile.ZIP_STORED
    archive.writestr(info, data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_directory", type=Path)
    args = parser.parse_args()
    manifest_bytes = MANIFEST.read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest["schema"] != 1 or manifest["version"] != "1.1.37":
        raise ValueError("Unsupported source manifest")
    archive_name = manifest["archive_name"]
    if Path(archive_name).name != archive_name:
        raise ValueError("Invalid output name")
    args.output_directory.mkdir(parents=True, exist_ok=True)
    output_path = args.output_directory / archive_name
    with tempfile.TemporaryDirectory(prefix="cheapmine-zebra-source-") as temporary:
        temporary = Path(temporary)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            downloaded = dict(pool.map(lambda entry: fetch(entry, temporary), manifest["entries"]))
        entries = {
            "README.txt": README.encode("utf-8"),
            "SOURCE-MANIFEST.json": manifest_bytes,
        }
        entries.update({name: path.read_bytes() for name, path in downloaded.items()})
        staged = args.output_directory / (archive_name + ".tmp")
        try:
            with zipfile.ZipFile(staged, "w", compression=zipfile.ZIP_STORED) as archive:
                for name, data in sorted(entries.items()):
                    write_entry(archive, name, data)
            actual = sha256_file(staged)
            if EXPECTED_OUTPUT_SHA256 and actual != EXPECTED_OUTPUT_SHA256:
                raise ValueError("Unexpected output SHA-256: " + actual)
            os.replace(staged, output_path)
        finally:
            if staged.exists():
                staged.unlink()
    print(json.dumps({"file": output_path.name, "sha256": actual, "bytes": output_path.stat().st_size}, sort_keys=True))


if __name__ == "__main__":
    main()
