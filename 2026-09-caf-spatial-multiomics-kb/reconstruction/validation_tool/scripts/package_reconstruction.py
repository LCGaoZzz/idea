#!/usr/bin/env python3
"""Validate and create a deterministic, policy-filtered reconstruction ZIP."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = SKILL_ROOT / "scripts" / "validate_reconstruction.py"
SCHEMA_VERSION = "1.0.0"
CHUNK_SIZE = 1024 * 1024
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
DEFAULT_MAX_FILE_BYTES = 100 * 1024 * 1024
DEFAULT_MAX_FILES = 20_000
DEFAULT_MAX_TOTAL_BYTES = 512 * 1024 * 1024
SOURCE_DIRS = {"sources", "uploads", "raw_data", "raw-data", "private_data"}
CACHE_PARTS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".ipynb_checkpoints",
    "renv",
    "packrat",
}
SENSITIVE_NAMES = {
    ".env",
    "credentials",
    "credentials.json",
    "secrets.json",
    "id_rsa",
    "id_ed25519",
    "cookies.txt",
    "netrc",
    ".netrc",
}
SENSITIVE_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".jks"}
ARCHIVE_SUFFIXES = {".zip", ".tgz", ".gz", ".bz2", ".xz", ".7z", ".rar"}
SECRET_PATTERNS = (
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b"),
    re.compile(rb"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
)
REQUIRED_ROOT_FILES = {
    "source_inventory.json",
    "working_state.json",
    "reconstruction_manifest.json",
    "traceability.tsv",
    "REPORT.md",
    "validation_report.json",
}


class PackageError(ValueError):
    """Raised when a project cannot be packaged without violating policy."""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _deterministic_time() -> str:
    raw = os.environ.get("SOURCE_DATE_EPOCH")
    if raw is None:
        return "1980-01-01T00:00:00Z"
    try:
        value = int(raw)
    except ValueError as exc:
        raise PackageError("SOURCE_DATE_EPOCH must be an integer") from exc
    return datetime.fromtimestamp(value, timezone.utc).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PackageError(f"cannot read required JSON {path.name}: {exc}") from exc
    if not isinstance(value, dict):
        raise PackageError(f"required JSON {path.name} must contain an object")
    return value


def _run_validator(project_dir: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(VALIDATOR),
            "--project-dir",
            str(project_dir),
            "--write-report",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    report_path = project_dir / "validation_report.json"
    if not report_path.is_file():
        raise PackageError(
            "validator did not produce validation_report.json: "
            + (completed.stderr.strip() or completed.stdout.strip())
        )
    report = _read_json(report_path)
    if completed.returncode != 0 or report.get("valid") is not True:
        errors = report.get("errors", [])
        raise PackageError(f"validator rejected the project with {len(errors)} error(s)")
    return report


def _iter_files(root: Path) -> list[Path]:
    return sorted(
        (path for path in root.rglob("*") if path.is_file() or _is_link_like(path)),
        key=lambda path: path.relative_to(root).as_posix().casefold(),
    )


def _is_link_like(path: Path) -> bool:
    return path.is_symlink() or bool(getattr(path, "is_junction", lambda: False)())


def _has_link_component(project_dir: Path, relative: Path) -> bool:
    current = project_dir
    for part in relative.parts:
        current = current / part
        if _is_link_like(current):
            return True
    return False


def _source_roots(project_dir: Path) -> tuple[Path, ...]:
    inventory = _read_json(project_dir / "source_inventory.json")
    roots: set[Path] = set()
    for source in inventory.get("sources", []):
        if not isinstance(source, dict) or source.get("availability") != "available":
            continue
        raw = source.get("location")
        if not isinstance(raw, str) or not raw.strip():
            continue
        normalized = Path(raw.replace("\\", "/"))
        if normalized.is_absolute() or normalized == Path(".") or ".." in normalized.parts:
            continue
        roots.add(normalized)
    return tuple(sorted(roots, key=lambda item: item.as_posix().casefold()))


def _reason_excluded(
    relative: Path,
    path: Path,
    *,
    include_sources: bool,
    source_redistribution_authorized: bool,
    max_file_bytes: int,
    output_path: Path,
    inventoried_source_roots: tuple[Path, ...],
    project_dir: Path,
) -> str | None:
    if _has_link_component(project_dir, relative):
        return "symbolic links and junctions are not packaged"
    parts = relative.parts
    if any(part in CACHE_PARTS for part in parts):
        return "version-control, dependency, or cache path"
    if path.resolve() == output_path:
        return "output archive is not recursively packaged"
    is_inventoried_source = any(
        relative == source_root or source_root in relative.parents
        for source_root in inventoried_source_roots
    )
    if (parts and parts[0] in SOURCE_DIRS) or is_inventoried_source:
        if not include_sources:
            return "inventoried source bytes excluded by default; provenance remains in source_inventory.json"
        if not source_redistribution_authorized:
            return "source redistribution was not explicitly authorized"
    name_folded = path.name.casefold()
    if name_folded in {value.casefold() for value in SENSITIVE_NAMES}:
        return "sensitive filename"
    if path.suffix.casefold() in SENSITIVE_SUFFIXES:
        return "sensitive key/certificate suffix"
    if path.suffix.casefold() in ARCHIVE_SUFFIXES:
        return "nested source/archive bytes are excluded"
    if path.stat().st_size > max_file_bytes:
        return f"file exceeds package limit {max_file_bytes} bytes"
    return None


def _contains_secret(data: bytes) -> bool:
    return any(pattern.search(data) for pattern in SECRET_PATTERNS)


def _role(relative: str) -> str:
    if relative == "REPORT.md":
        return "canonical_reconstruction_report"
    if relative == "traceability.tsv":
        return "traceability_table"
    if relative.endswith("manifest.json") or relative in {
        "source_inventory.json",
        "working_state.json",
        "validation_report.json",
        "repository_audit.json",
        "acquisition_log.json",
    }:
        return "structured_provenance"
    if relative.startswith("runs/"):
        return "runtime_evidence"
    if relative.startswith("code/"):
        return "generated_or_adapted_code"
    if relative.startswith(("results/", "figures/", "outputs/")):
        return "result_artifact"
    return "project_artifact"


def _delivery_markdown(manifest: dict[str, Any], validation: dict[str, Any]) -> bytes:
    analyses = manifest.get("analyses", []) if isinstance(manifest.get("analyses"), list) else []
    execution_records = (
        manifest.get("execution_records", [])
        if isinstance(manifest.get("execution_records"), list)
        else []
    )
    succeeded = [
        item
        for item in execution_records
        if isinstance(item, dict) and item.get("attempt_status") == "succeeded"
    ]
    status = str(validation.get("derived_overall_status", "受阻"))
    lines = [
        "# Reconstruction delivery",
        "",
        f"- Project: `{manifest.get('project_id', 'unknown')}`",
        f"- Derived status: `{status}`",
        f"- Analyses represented: `{len(analyses)}`",
        f"- Qualifying successful executions: `{len(succeeded)}`",
        "- Validation: `validation_report.json` (`valid: true`)",
        "",
        "## Start here",
        "",
        "1. Read `REPORT.md` for the evidence-bounded interpretation.",
        "2. Read `traceability.tsv` to follow every claim through Methods, code, I/O, and status.",
        "3. Read `reconstruction_manifest.json` for the authoritative structured record.",
        "4. Read `validation_report.json` for contract scope, warnings, and limitations.",
        "5. Read `repository_audit.json` when present for static execution-readiness findings.",
        "",
        "## Meaning of the status",
        "",
    ]
    if status == "已执行验证":
        lines.append("This package contains validator-qualified runtime evidence for every analysis.")
    elif status == "材料完整但未执行":
        lines.append("Materials are aligned, but no validator-qualified execution is claimed.")
    elif status == "材料冲突":
        lines.append("Conflicting evidence remains visible; successful code execution would not erase it.")
    else:
        lines.append("The project is blocked or partial; exact blockers remain in the manifest and report.")
    lines.extend(
        [
            "",
            "The validator checks structure, linkage, hashes, and bounded provenance. It does not by itself prove biological correctness or signed process-to-artifact causality.",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def _zip_write(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(filename=name, date_time=ZIP_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def package_project(
    project_dir: Path,
    output: Path,
    *,
    include_sources: bool = False,
    source_redistribution_authorized: bool = False,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
    max_files: int = DEFAULT_MAX_FILES,
    max_total_bytes: int = DEFAULT_MAX_TOTAL_BYTES,
) -> dict[str, Any]:
    project_dir = project_dir.resolve(strict=True)
    if not project_dir.is_dir():
        raise PackageError("project-dir must be a directory")
    output = output.resolve()
    if output.exists():
        raise PackageError(f"refusing to overwrite existing archive: {output}")
    if include_sources and not source_redistribution_authorized:
        raise PackageError("--include-sources requires --source-redistribution-authorized")
    validation = _run_validator(project_dir)
    manifest = _read_json(project_dir / "reconstruction_manifest.json")
    inventoried_source_roots = _source_roots(project_dir)
    missing = sorted(name for name in REQUIRED_ROOT_FILES if not (project_dir / name).is_file())
    if missing:
        raise PackageError("required project files are missing after validation: " + ", ".join(missing))

    payloads: dict[str, bytes] = {}
    included: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    candidates = _iter_files(project_dir)
    if len(candidates) > max_files:
        raise PackageError(f"project exceeds package inventory limit of {max_files} paths")
    included_total_bytes = 0
    for path in candidates:
        relative_path = path.relative_to(project_dir)
        relative = relative_path.as_posix()
        reason = _reason_excluded(
            relative_path,
            path,
            include_sources=include_sources,
            source_redistribution_authorized=source_redistribution_authorized,
            max_file_bytes=max_file_bytes,
            output_path=output,
            inventoried_source_roots=inventoried_source_roots,
            project_dir=project_dir,
        )
        if reason:
            excluded.append({"path": relative, "bytes": path.lstat().st_size, "reason": reason})
            continue
        data = path.read_bytes()
        included_total_bytes += len(data)
        if included_total_bytes > max_total_bytes:
            raise PackageError(f"included files exceed package byte limit {max_total_bytes}")
        if _contains_secret(data):
            raise PackageError(f"high-confidence secret pattern found in candidate package file: {relative}")
        payloads[relative] = data
        included.append(
            {
                "path": relative,
                "role": _role(relative),
                "bytes": len(data),
                "sha256": _sha256_bytes(data),
            }
        )

    delivery = _delivery_markdown(manifest, validation)
    payloads["DELIVERY.md"] = delivery
    included.append(
        {
            "path": "DELIVERY.md",
            "role": "reader_entrypoint",
            "bytes": len(delivery),
            "sha256": _sha256_bytes(delivery),
        }
    )
    included.sort(key=lambda item: str(item["path"]).casefold())
    excluded.sort(key=lambda item: str(item["path"]).casefold())
    package_manifest = {
        "schema_version": SCHEMA_VERSION,
        "package_kind": "omicos_bioinformatics_reconstruction",
        "deterministic_timestamp_utc": _deterministic_time(),
        "project_id": manifest.get("project_id"),
        "derived_overall_status": validation.get("derived_overall_status"),
        "validation_report_sha256": _sha256(project_dir / "validation_report.json"),
        "source_policy": {
            "include_sources": include_sources,
            "source_redistribution_authorized": source_redistribution_authorized,
            "default": "exclude source bytes; retain source manifest and fingerprints",
        },
        "included_files": included,
        "excluded_files": excluded,
        "generated_files": ["DELIVERY.md", "package_manifest.json", "SHA256SUMS"],
    }
    manifest_bytes = (
        json.dumps(package_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    payloads["package_manifest.json"] = manifest_bytes
    checksum_lines = [
        f"{_sha256_bytes(payloads[name])}  {name}"
        for name in sorted(payloads, key=str.casefold)
    ]
    checksums = ("\n".join(checksum_lines) + "\n").encode("utf-8")
    payloads["SHA256SUMS"] = checksums

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    if temporary.exists():
        raise PackageError(f"temporary archive path already exists: {temporary}")
    try:
        with zipfile.ZipFile(temporary, "x") as archive:
            for name in sorted(payloads, key=str.casefold):
                _zip_write(archive, name, payloads[name])
        os.replace(temporary, output)
    finally:
        if temporary.exists():
            temporary.unlink()
    return {
        "ok": True,
        "archive_path": str(output),
        "archive_sha256": _sha256(output),
        "archive_bytes": output.stat().st_size,
        "validation_report_sha256": package_manifest["validation_report_sha256"],
        "package_manifest_sha256": _sha256_bytes(manifest_bytes),
        "derived_overall_status": validation.get("derived_overall_status"),
        "included_file_count": len(payloads),
        "excluded_file_count": len(excluded),
        "included_uncompressed_bytes": sum(len(value) for value in payloads.values()),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--include-sources", action="store_true")
    parser.add_argument("--source-redistribution-authorized", action="store_true")
    parser.add_argument("--max-file-bytes", type=int, default=DEFAULT_MAX_FILE_BYTES)
    parser.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES)
    parser.add_argument("--max-total-bytes", type=int, default=DEFAULT_MAX_TOTAL_BYTES)
    parser.add_argument("--receipt", type=Path)
    return parser


def main() -> int:
    args = _parser().parse_args()
    project_dir = args.project_dir.resolve()
    output = args.output or project_dir.with_name(project_dir.name + "-reconstruction.zip")
    try:
        result = package_project(
            project_dir,
            output,
            include_sources=args.include_sources,
            source_redistribution_authorized=args.source_redistribution_authorized,
            max_file_bytes=args.max_file_bytes,
            max_files=args.max_files,
            max_total_bytes=args.max_total_bytes,
        )
        if args.receipt:
            receipt = args.receipt.resolve()
            if receipt.exists():
                raise PackageError(f"refusing to overwrite receipt: {receipt}")
            receipt.parent.mkdir(parents=True, exist_ok=True)
            receipt.write_text(
                json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
    except (PackageError, OSError, subprocess.SubprocessError, zipfile.BadZipFile) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
