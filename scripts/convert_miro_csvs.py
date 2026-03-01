#!/usr/bin/env python3
"""Deterministically convert Miro CSV exports into structured JSON artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "project_files" / "03 - Values & Principles"
OUT_DIR = SRC_ROOT / "derived_json"
ROLLUP_PATH = OUT_DIR / "values_principles_rollup.json"
TRANSFORM_VERSION = "1.1.0"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def read_csv_rows(path: Path) -> list[list[str]]:
    rows: list[list[str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.reader(handle):
            rows.append([cell.strip() for cell in row])
    return rows


def first_text(row: list[str]) -> str:
    for cell in row:
        if cell:
            return cell
    return ""


def infer_type(text: str, row: list[str]) -> str:
    value = text.lower().strip()
    non_empty = [cell for cell in row if cell]

    if not value:
        return "note"
    if re.fullmatch(r"<[^>]+>", value):
        return "tag"
    if value in {"pass", "revise", "park"}:
        return "column_header"
    if value.startswith(("f1", "f2", "f3", "frame")):
        return "column_header"
    if value.startswith("candidate") and len(non_empty) > 1:
        return "column_header"
    if any(token in value for token in ["read-only", "no editing", "write principles", "failure-reason", "quality criteria"]):
        return "prompt"
    if re.search(r"\bfr\d+\b", value):
        return "tag"
    if any(token in value for token in ["pass", "revise", "park"]) and len(non_empty) >= 3:
        return "vote"
    if len(value) <= 70 and not value.endswith(".") and re.search(r"[a-z]", value):
        return "column_header"
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
    cleaned = normalize_text(value).lower()
    cleaned = re.sub(r"[\"'`“”]", "", cleaned)
    head = re.split(r"[\.:;\-]", cleaned, maxsplit=1)[0]
    return " ".join(head.split()[:8])


def build_for_csv(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any], int, int]:
    rows = read_csv_rows(path)
    rel = path.relative_to(REPO_ROOT).as_posix()
    prefix = slug(path.stem)

    items: list[dict[str, Any]] = []
    headers: list[tuple[str, str]] = []
    links = 0
    low_confidence = 0

    for row_index, row in enumerate(rows, start=1):
        text = first_text(row)
        if not text:
            continue

        inferred = infer_type(text, row)
        parent_id = headers[-1][0] if inferred in {"sticky", "tag", "vote", "note"} and headers else None
        group_path = [entry[1] for entry in headers]

        node_id = f"{prefix}::{row_index:04d}"
        if inferred == "column_header":
            headers.append((node_id, text))

        confidence = confidence_for(inferred, parent_id)
        if parent_id:
            links += 1
        if confidence == "low":
            low_confidence += 1

        items.append(
            {
                "id": node_id,
                "source_csv_path": rel,
                "source_row_index": row_index,
                "raw_fields": row,
                "text": text,
                "inferred_type": inferred,
                "parent_id": parent_id,
                "group_path": group_path,
                "confidence": confidence,
            }
        )

    manifest = {
        "source_csv_path": rel,
        "source_sha256": sha256_file(path),
        "row_count_raw": len(rows),
        "object_count": len(items),
        "transform_version": TRANSFORM_VERSION,
    }
    return items, manifest, links, low_confidence


def build_rollup(nodes: list[dict[str, Any]]) -> dict[str, Any]:
    by_norm: dict[str, list[str]] = {}
    by_short: dict[str, list[str]] = {}

    for node in nodes:
        text = str(node.get("text", ""))
        normalized = normalize_text(text).lower()
        shortened = short_label(text)
        if normalized:
            by_norm.setdefault(normalized, []).append(str(node["id"]))
        if shortened:
            by_short.setdefault(shortened, []).append(str(node["id"]))

    links: list[dict[str, str]] = []
    for method, buckets in (("same_text", by_norm), ("same_short_label", by_short)):
        for key, ids in buckets.items():
            unique_ids = sorted(set(ids))
            if len(unique_ids) < 2:
                continue
            for idx, src in enumerate(unique_ids):
                for dst in unique_ids[idx + 1 :]:
                    links.append({"source_id": src, "target_id": dst, "method": method, "key": key})

    return {
        "meta": {
            "transform_version": TRANSFORM_VERSION,
            "source_root": SRC_ROOT.relative_to(REPO_ROOT).as_posix(),
        },
        "nodes": nodes,
        "cross_links": links,
    }


def convert_all() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    csv_paths = sorted(
        [path for path in SRC_ROOT.glob("**/*.csv") if OUT_DIR not in path.parents],
        key=lambda path: path.as_posix().lower(),
    )

    all_nodes: list[dict[str, Any]] = []
    summary: list[dict[str, Any]] = []

    for path in csv_paths:
        nodes, manifest, links, low_confidence = build_for_csv(path)
        all_nodes.extend(nodes)
        summary.append(
            {
                "csv": path.relative_to(SRC_ROOT).as_posix(),
                "items": len(nodes),
                "links": links,
                "low_confidence": low_confidence,
            }
        )

        base_name = path.stem
        (OUT_DIR / f"{base_name}.json").write_text(
            json.dumps(nodes, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (OUT_DIR / f"{base_name}.manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    rollup = build_rollup(all_nodes)
    ROLLUP_PATH.write_text(json.dumps(rollup, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

    return {
        "csv_count": len(csv_paths),
        "node_count": len(all_nodes),
        "cross_links": len(rollup.get("cross_links", [])),
        "summary": summary,
    }


def main() -> None:
    report = convert_all()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
