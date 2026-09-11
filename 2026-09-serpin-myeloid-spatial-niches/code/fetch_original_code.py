"""Fetch pinned, hash-verified author code. Never execute downloaded notebooks."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tempfile
from urllib.parse import quote
from urllib.request import Request, urlopen

MAX_BYTES = 32 * 1024 * 1024


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def safe_target(root: Path, relative: str) -> Path:
    p = PurePosixPath(relative)
    if p.is_absolute() or ".." in p.parts or "\\" in relative or not p.parts:
        raise ValueError(f"Unsafe repository path: {relative!r}")
    root = root.resolve()
    target = root.joinpath(*p.parts).resolve()
    if not target.is_relative_to(root) or target == root:
        raise ValueError("Target escapes output directory")
    return target


def write_verified(target: Path, data: bytes, expected: str, *, overwrite: bool = False) -> str:
    if git_blob_sha(data) != expected:
        raise ValueError(f"Git blob SHA mismatch for {target.name}")
    if target.exists():
        if git_blob_sha(target.read_bytes()) == expected:
            return "already_verified"
        if not overwrite:
            raise FileExistsError(f"Different local file exists: {target}; use --overwrite deliberately")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as f:
            temporary = Path(f.name)
            f.write(data)
        temporary.replace(target)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return "downloaded_verified"


def readable_notebook(data: bytes) -> str:
    notebook = json.loads(data)
    parts = ["READING COPY ONLY. Cells retain original source; no outputs or execution.\n"]
    for i, cell in enumerate(notebook.get("cells", [])):
        source = cell.get("source", [])
        text = source if isinstance(source, str) else "".join(source)
        parts.append(f"\n===== CELL {i} | {cell.get('cell_type')} | id={cell.get('id', 'not_supplied')} =====\n{text}\n")
    return "".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("original_code"))
    parser.add_argument("--manifest", type=Path,
                        default=Path(__file__).resolve().parents[1] / "provenance" / "upstream_manifest.json")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    repository, commit = manifest["repository"], manifest["commit"]
    if repository != "BDBrownLab/Falcomata_PDAC_2026" or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Unexpected repository or unpinned commit")
    args.out.mkdir(parents=True, exist_ok=True)
    report = {"repository": repository, "commit": commit, "executed_notebooks": False, "files": []}
    for item in manifest["files"]:
        row = {"path": item["path"], "expected_git_blob_sha": item["git_blob_sha"]}
        try:
            target = safe_target(args.out, item["path"])
            url = f"https://raw.githubusercontent.com/{repository}/{commit}/{quote(item['path'], safe='/')}"
            request = Request(url, headers={"User-Agent": "serpin-niche-idea-source-reader/1"})
            with urlopen(request, timeout=30) as response:
                data = response.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                raise ValueError("File exceeds size safety limit")
            row["status"] = write_verified(target, data, item["git_blob_sha"], overwrite=args.overwrite)
            if target.suffix == ".ipynb":
                target.with_suffix(".ipynb.source.txt").write_text(readable_notebook(data), encoding="utf-8")
        except Exception as exc:
            row.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        report["files"].append(row)
        print(f"{row['status']}: {item['path']}")
    report["all_verified"] = all(x["status"] != "failed" for x in report["files"])
    (args.out / "fetch_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if not report["all_verified"]:
        raise SystemExit("One or more downloads failed; inspect fetch_report.json. No notebooks were executed.")


if __name__ == "__main__": main()
