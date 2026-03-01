#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "project_files" / "03 - Values & Principles"
OUT_DIR = SRC_DIR / "derived_json"
ROLLUP_PATH = OUT_DIR / "values_principles_rollup.json"
TRANSFORM_VERSION = "1.0.0"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def read_csv_rows(path: Path) -> list[list[str]]:
    rows: list[list[str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.reader(f):
            rows.append([c.strip() for c in row])
    return rows


def first_text(row: list[str]) -> str:
    for cell in row:
        if cell:
            return cell
    return ""


def infer_type(text: str, row: list[str]) -> str:
    t = text.lower().strip()
    non_empty = [c for c in row if c]
    if not t:
        return "note"
    if re.fullmatch(r"<[^>]+>", t):
        return "tag"
    if t in {"pass", "revise", "park"}:
        return "column_header"
    if t.startswith(("f1", "f2", "f3")):
        return "column_header"
    if t.startswith("candidate") and len(non_empty) > 1:
        return "column_header"
    if any(k in t for k in ["read-only", "no editing", "write principles", "failure-reason", "quality criteria"]):
        return "prompt"
    if len(t) <= 70 and not t.endswith(".") and re.search(r"[a-z]", t):
        return "column_header"
    if any(k in t for k in ["pass", "revise", "park"]) and len(non_empty) >= 3:
        return "vote"
    if re.search(r"\bfr\d+\b", t):
        return "tag"
    return "sticky"


def confidence_for(inferred_type: str, parent_id: str | None) -> str:
    if inferred_type in {"prompt", "column_header"}:
        return "high"
    if parent_id:
        return "med"
    return "low"


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def short_label(value: str) -> str:
    base = normalize_text(value).lower()
    base = re.sub(r"[\"'`“”]", "", base)
    lead = re.split(r"[\.:;\-]", base, maxsplit=1)[0]
    return " ".join(lead.split()[:8])


def build_for_csv(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any], int, int]:
    rows = read_csv_rows(path)
    rel = path.relative_to(REPO_ROOT).as_posix()
    prefix = slug(path.stem)
    items: list[dict[str, Any]] = []
    headers: list[tuple[str, str]] = []
    links = 0
    low = 0

    for idx, row in enumerate(rows, start=1):
        text = first_text(row)
        if not text:
            continue
        inferred = infer_type(text, row)
        parent_id = headers[-1][0] if inferred in {"sticky", "tag", "vote", "note"} and headers else None
        group_path = [h[1] for h in headers]

        obj_id = f"{prefix}::{idx:04d}"
        if inferred == "column_header":
            headers.append((obj_id, text))
        conf = confidence_for(inferred, parent_id)
        if parent_id:
            links += 1
        if conf == "low":
            low += 1

        items.append(
            {
                "id": obj_id,
                "source_csv_path": rel,
                "source_row_index": idx,
                "raw_fields": row,
                "text": text,
                "inferred_type": inferred,
                "parent_id": parent_id,
                "group_path": group_path,
                "confidence": conf,
            }
        )

    manifest = {
        "source_csv_path": rel,
        "source_sha256": sha256_file(path),
        "row_count_raw": len(rows),
        "object_count": len(items),
        "transform_version": TRANSFORM_VERSION,
    }
    return items, manifest, links, low


def build_rollup(all_items: list[dict[str, Any]]) -> dict[str, Any]:
    by_norm: dict[str, list[str]] = {}
    by_short: dict[str, list[str]] = {}
    for item in all_items:
        text = item.get("text", "")
        n = normalize_text(text).lower()
        s = short_label(text)
        if n:
            by_norm.setdefault(n, []).append(item["id"])
        if s:
            by_short.setdefault(s, []).append(item["id"])

    links: list[dict[str, str]] = []
    for method, buckets in (("same_text", by_norm), ("same_short_label", by_short)):
        for key, ids in buckets.items():
            uniq = sorted(set(ids))
            if len(uniq) < 2:
                continue
            for i, src in enumerate(uniq):
                for dst in uniq[i + 1 :]:
                    links.append({"source_id": src, "target_id": dst, "method": method, "key": key})

    return {
        "meta": {"transform_version": TRANSFORM_VERSION},
        "nodes": all_items,
        "cross_links": links,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_paths = sorted(SRC_DIR.glob("*.csv"), key=lambda p: p.name.lower())

    all_items: list[dict[str, Any]] = []
    summary: list[dict[str, Any]] = []

    for path in csv_paths:
        items, manifest, links, low = build_for_csv(path)
        all_items.extend(items)
        summary.append({"csv": path.name, "items": len(items), "links": links, "low_confidence": low})

        base = path.stem
        (OUT_DIR / f"{base}.json").write_text(json.dumps(items, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        (OUT_DIR / f"{base}.manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

    rollup = build_rollup(all_items)
    ROLLUP_PATH.write_text(json.dumps(rollup, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({"summary": summary, "cross_links": len(rollup["cross_links"])}, indent=2))


if __name__ == "__main__":
    main()
