#!/usr/bin/env python3
"""Generate or validate install-manifest.json checksums."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "install-manifest.json"
TRACKED_FILES = ("eve-coder.py", "eve-cli.sh")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_manifest() -> dict[str, dict[str, str]]:
    return {
        "files": {
            name: sha256_file(ROOT / name)
            for name in TRACKED_FILES
        }
    }


def write_manifest(manifest: dict[str, dict[str, str]]) -> None:
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def check_manifest(manifest: dict[str, dict[str, str]]) -> int:
    if not MANIFEST_PATH.exists():
        print("install-manifest.json is missing", file=sys.stderr)
        return 1

    current = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if current != manifest:
        print("install-manifest.json is out of date", file=sys.stderr)
        return 1
    print("install-manifest.json is up to date")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if install-manifest.json does not match current file hashes",
    )
    args = parser.parse_args()

    manifest = build_manifest()
    if args.check:
        return check_manifest(manifest)

    write_manifest(manifest)
    print(f"updated {MANIFEST_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
