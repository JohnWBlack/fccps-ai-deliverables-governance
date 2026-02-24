#!/usr/bin/env python3
"""Extract reference IDs from markdown corpus into public/ref_index.json."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = REPO_ROOT / "public"
CATALOG_PATH = PUBLIC_DIR / "file_catalog.json"
OUTPUT_PATH = PUBLIC_DIR / "ref_index.json"

SCAN_GLOBS = [
    "project_files/**/*.md",
    "governance_docs/**/*.md",
    "docs/**/*.md",
    "CHANGELOG_PUBLIC.md",
]
DOCX_GLOBS = ["project_files/**/*.docx", "governance_docs/**/*.docx"]

TOKEN_PATTERNS = {
    "principle_ids": re.compile(r"\bP-\d{2,3}\b", re.IGNORECASE),
    "risk_ids": re.compile(r"\bR-\d{2,3}\b", re.IGNORECASE),
    "workstream_ids": re.compile(r"\bWS-[A-Z0-9-]+\b", re.IGNORECASE),
    "deliverable_ids": re.compile(r"\bD-[A-Z0-9-]+\b", re.IGNORECASE),
    "milestone_ids": re.compile(r"\bms_[a-z0-9_-]+\b", re.IGNORECASE),
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_catalog() -> dict[str, Any]:
    if not CATALOG_PATH.exists():
        return {"files": []}
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def find_md_files() -> list[Path]:
    files: set[Path] = set()
    for pattern in SCAN_GLOBS:
        if "**" in pattern:
            files.update(REPO_ROOT.glob(pattern))
        else:
            candidate = REPO_ROOT / pattern
            if candidate.exists():
                files.add(candidate)
    return sorted([p for p in files if p.is_file()])


def find_docx_files() -> list[Path]:
    files: set[Path] = set()
    for pattern in DOCX_GLOBS:
        files.update(REPO_ROOT.glob(pattern))
    return sorted([p for p in files if p.is_file()])


def normalize_token(token: str, key: str) -> str:
    token = token.upper()
    if key == "milestone_ids":
        return token.lower()
    return token


def extract_from_markdown(path: Path) -> tuple[dict[str, list[str]], dict[str, int]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    extracted = {k: [] for k in TOKEN_PATTERNS}
    anchors: dict[str, int] = {}

    for line_number, line in enumerate(text.splitlines(), start=1):
        for key, pattern in TOKEN_PATTERNS.items():
            matches = [normalize_token(m.group(0), key) for m in pattern.finditer(line)]
            if not matches:
                continue
            extracted[key].extend(matches)
            if key not in anchors:
                anchors[key] = line_number

    for key in extracted:
        extracted[key] = sorted(set(extracted[key]))

    return extracted, anchors


def last_modified_for(path: Path, catalog_index: dict[str, dict[str, Any]]) -> str:
    rel = path.relative_to(REPO_ROOT).as_posix()
    catalog_entry = catalog_index.get(rel)
    if catalog_entry:
        return catalog_entry.get("last_modified_iso", utc_now_iso())

    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return mtime.isoformat().replace("+00:00", "Z")


def build_ref_index() -> dict[str, Any]:
    catalog = load_catalog()
    catalog_index = {f.get("path"): f for f in catalog.get("files", []) if isinstance(f, dict)}

    md_files = find_md_files()
    docx_files = find_docx_files()
    docs: list[dict[str, Any]] = []

    for file_path in md_files:
        extracted, anchors = extract_from_markdown(file_path)
        docs.append(
            {
                "doc_path": file_path.relative_to(REPO_ROOT).as_posix(),
                "doc_type": "md",
                "last_modified_iso": last_modified_for(file_path, catalog_index),
                "extracted": extracted,
                "anchors": anchors,
            }
        )

    docs.sort(key=lambda item: item["doc_path"])

    return {
        "meta": {
            "generated_at": utc_now_iso(),
            "scanned_files_count": len(md_files),
            "skipped_files_count": len(docx_files),
            "note_if_docx_skipped": "docx parsing skipped in v1; markdown corpus only",
        },
        "docs": docs,
    }


def main() -> None:
    payload = build_ref_index()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"🔎 Reference index written to {OUTPUT_PATH}")
    print(f"📚 Scanned markdown files: {payload['meta']['scanned_files_count']}")
    print(f"📄 Skipped docx files: {payload['meta']['skipped_files_count']}")


if __name__ == "__main__":
    main()
