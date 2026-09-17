#!/usr/bin/env python3
"""Verify the complete archive and its members; do not execute or extract content."""
import hashlib
import json
from pathlib import Path
import tarfile


def verify() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "integrity/complete_bundle_manifest.json").read_text(encoding="utf-8"))
    record = manifest["repository_archive"]
    archive = root / record["path"]
    data = archive.read_bytes()
    if len(data) != record["size_bytes"] or hashlib.sha256(data).hexdigest() != record["sha256"]:
        raise ValueError("Archive integrity mismatch")
    expected = {row["path"]: row for row in manifest["members"]}
    with tarfile.open(archive, "r:xz") as tar:
        entries = tar.getmembers()
        if any(not entry.isfile() for entry in entries):
            raise ValueError("Unexpected non-file archive member")
        if len(entries) != len(expected) or {entry.name for entry in entries} != set(expected):
            raise ValueError("Member set mismatch or duplicate member")
        for entry in entries:
            stream = tar.extractfile(entry)
            if stream is None:
                raise ValueError(f"Unreadable member: {entry.name}")
            payload = stream.read()
            row = expected[entry.name]
            if len(payload) != row["size_bytes"] or hashlib.sha256(payload).hexdigest() != row["sha256"]:
                raise ValueError(f"Member integrity mismatch: {entry.name}")
    for name in manifest["browsable_byte_identical_mirrors"]:
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected[name]["sha256"]:
            raise ValueError(f"Browsable mirror mismatch: {name}")
    print(f"PASS: archive, {len(expected)} members, and browsable mirrors verified")


if __name__ == "__main__":
    verify()
