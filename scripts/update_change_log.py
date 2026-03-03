#!/usr/bin/env python3
"""Append deterministic automated entries to the governance decision/change log."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CHANGE_LOG_PATH = REPO_ROOT / "governance_docs" / "FCCPS_AIAC_Decision_Change_Log.md"
TRACKED_SOR_FILES = [
    REPO_ROOT / "sor" / "workstreams.yml",
    REPO_ROOT / "sor" / "deliverables.yml",
    REPO_ROOT / "sor" / "timeline.yml",
    REPO_ROOT / "sor" / "principles.yml",
    REPO_ROOT / "sor" / "supporting_documents.yml",
]


def today_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def resolve_last_updated(path: Path) -> str | None:
    if not path.exists() or path.suffix.lower() != ".yml":
        return None
    try:
        payload = load_yaml(path)
    except Exception:
        return None
    metadata = payload.get("metadata") if isinstance(payload, dict) else None
    if isinstance(metadata, dict) and metadata.get("last_updated"):
        return str(metadata.get("last_updated"))
    return None


def fingerprint_for_files(paths: list[Path]) -> tuple[str, list[tuple[str, str]]]:
    hashes: list[tuple[str, str]] = []
    for path in paths:
        if not path.exists():
            continue
        rel = str(path.relative_to(REPO_ROOT)).replace("\\", "/")
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        hashes.append((rel, sha))

    digest = hashlib.sha256(json.dumps(hashes, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    return digest, hashes


def bump_last_updated_line(lines: list[str], date_str: str) -> list[str]:
    needle = "**Last updated:**"
    for i, line in enumerate(lines):
        if line.strip().lower().startswith(needle.lower()):
            lines[i] = f"**Last updated:** {date_str}  "
            return lines
    return lines


def extract_next_change_id(markdown: str, date_str: str) -> str:
    token = f"CHG-{date_str}-"
    max_seq = 0
    for raw in markdown.splitlines():
        if token not in raw:
            continue
        for part in raw.split("|"):
            part = part.strip()
            if part.startswith(token):
                suffix = part.replace(token, "", 1)
                if suffix.isdigit():
                    max_seq = max(max_seq, int(suffix))
    return f"CHG-{date_str}-{max_seq + 1:02d}"


def find_change_table_insert_index(lines: list[str]) -> int:
    header_idx = -1
    for i, line in enumerate(lines):
        if line.strip().startswith("| Change ID |"):
            header_idx = i
            break
    if header_idx == -1:
        raise RuntimeError("Could not locate 'Change log' table header in FCCPS_AIAC_Decision_Change_Log.md")

    i = header_idx + 2  # skip header + separator
    while i < len(lines) and lines[i].strip().startswith("|"):
        i += 1
    return i


def main() -> None:
    parser = argparse.ArgumentParser(description="Append deterministic automated changelog rows when SoR content fingerprint changes.")
    parser.add_argument("--trigger", default="Automated SoR pipeline update", help="Trigger text stored in the Change log table")
    parser.add_argument("--owner", default="Automation", help="Owner text stored in the Change log table")
    args = parser.parse_args()

    if not CHANGE_LOG_PATH.exists():
        raise FileNotFoundError(f"Missing change log document: {CHANGE_LOG_PATH}")

    fingerprint, file_hashes = fingerprint_for_files(TRACKED_SOR_FILES)
    if not file_hashes:
        print("ℹ️ No tracked SoR files found; skipping change log update.")
        return

    markdown = CHANGE_LOG_PATH.read_text(encoding="utf-8")
    marker = f"auto_ref:{fingerprint}"
    if marker in markdown:
        print("ℹ️ Decision/change log already includes current SoR fingerprint; no update needed.")
        return

    date_str = today_iso()
    change_id = extract_next_change_id(markdown, date_str)

    last_updated_bits: list[str] = []
    impacted_artifacts: list[str] = []
    for rel, _sha in file_hashes:
        impacted_artifacts.append(rel)
        path = REPO_ROOT / rel
        last_updated = resolve_last_updated(path)
        if last_updated:
            last_updated_bits.append(f"{Path(rel).name}@{last_updated}")

    short_impacts = "; ".join(impacted_artifacts[:4])
    if len(impacted_artifacts) > 4:
        short_impacts += "; ..."

    details = (
        f"Automated SoR refresh captured for {len(impacted_artifacts)} tracked file(s)"
        if not last_updated_bits
        else f"Automated SoR refresh captured ({'; '.join(last_updated_bits[:4])})"
    )
    details = details.replace("|", "/")
    trigger = str(args.trigger).replace("|", "/")
    impact = f"Impacts snapshot + governance docs ({short_impacts}) {marker}".replace("|", "/")
    owner = str(args.owner).replace("|", "/")

    lines = markdown.splitlines()
    lines = bump_last_updated_line(lines, date_str)
    insert_at = find_change_table_insert_index(lines)
    new_row = f"| {change_id} | {date_str} | {details} | {trigger} | {impact} | {owner} |"
    lines.insert(insert_at, new_row)

    CHANGE_LOG_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"📝 Appended change log entry {change_id} ({marker})")


if __name__ == "__main__":
    main()
