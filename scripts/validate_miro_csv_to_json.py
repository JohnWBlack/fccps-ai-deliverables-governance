#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "project_files" / "03 - Values & Principles"
OUT_DIR = SRC_DIR / "derived_json"
ROLLUP_PATH = OUT_DIR / "values_principles_rollup.json"
EXPECTED_TRANSFORM_VERSION = "1.1.0"
REQUIRED_FIELDS = {
    "id",
    "source_csv_path",
    "source_row_index",
    "raw_fields",
    "text",
    "inferred_type",
    "parent_id",
    "group_path",
    "confidence",
}
VALID_TYPES = {"prompt", "column_header", "sticky", "tag", "vote", "note"}
VALID_CONFIDENCE = {"high", "med", "low"}


def fail(msg: str) -> None:
    print(f"❌ {msg}")
    sys.exit(1)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_object(obj: dict[str, Any], index: int, filename: str) -> None:
    missing = REQUIRED_FIELDS - set(obj.keys())
    if missing:
        fail(f"{filename}[{index}] missing required fields: {sorted(missing)}")
    if not isinstance(obj["id"], str) or not obj["id"]:
        fail(f"{filename}[{index}] id must be a non-empty string")
    if not isinstance(obj["source_csv_path"], str) or not obj["source_csv_path"]:
        fail(f"{filename}[{index}] source_csv_path must be a non-empty string")
    if not isinstance(obj["source_row_index"], int) or obj["source_row_index"] < 1:
        fail(f"{filename}[{index}] source_row_index must be a positive int")
    if not isinstance(obj["raw_fields"], list):
        fail(f"{filename}[{index}] raw_fields must be a list")
    if not isinstance(obj["text"], str):
        fail(f"{filename}[{index}] text must be a string")
    if obj["inferred_type"] not in VALID_TYPES:
        fail(f"{filename}[{index}] inferred_type invalid: {obj['inferred_type']}")
    if obj["parent_id"] is not None and not isinstance(obj["parent_id"], str):
        fail(f"{filename}[{index}] parent_id must be string|null")
    if not isinstance(obj["group_path"], list) or not all(isinstance(x, str) for x in obj["group_path"]):
        fail(f"{filename}[{index}] group_path must be an array of strings")
    if obj["confidence"] not in VALID_CONFIDENCE:
        fail(f"{filename}[{index}] confidence invalid: {obj['confidence']}")


def main() -> None:
    if not OUT_DIR.exists():
        fail(f"Derived output folder not found: {OUT_DIR}")

    csv_paths = sorted(
        [path for path in SRC_DIR.glob("**/*.csv") if OUT_DIR not in path.parents],
        key=lambda path: path.as_posix().lower(),
    )
    if not csv_paths:
        fail("No source CSV files found")

    all_ids: set[str] = set()
    total_objects = 0

    for csv_path in csv_paths:
        base = csv_path.stem
        data_path = OUT_DIR / f"{base}.json"
        manifest_path = OUT_DIR / f"{base}.manifest.json"

        if not data_path.exists():
            fail(f"Missing derived JSON: {data_path}")
        if not manifest_path.exists():
            fail(f"Missing manifest JSON: {manifest_path}")

        data = load_json(data_path)
        manifest = load_json(manifest_path)

        if not isinstance(data, list):
            fail(f"{data_path.name} must be an array")
        if not isinstance(manifest, dict):
            fail(f"{manifest_path.name} must be an object")

        expected_rel = csv_path.relative_to(REPO_ROOT).as_posix()
        expected_hash = sha256_file(csv_path)

        if manifest.get("source_csv_path") != expected_rel:
            fail(f"{manifest_path.name} source_csv_path mismatch")
        if manifest.get("source_sha256") != expected_hash:
            fail(f"{manifest_path.name} source_sha256 mismatch")
        if manifest.get("object_count") != len(data):
            fail(f"{manifest_path.name} object_count mismatch")
        if not isinstance(manifest.get("row_count_raw"), int) or manifest["row_count_raw"] < len(data):
            fail(f"{manifest_path.name} row_count_raw invalid")
        if manifest.get("transform_version") != EXPECTED_TRANSFORM_VERSION:
            fail(
                f"{manifest_path.name} transform_version mismatch: "
                f"expected {EXPECTED_TRANSFORM_VERSION}, got {manifest.get('transform_version')}"
            )

        for idx, obj in enumerate(data):
            if not isinstance(obj, dict):
                fail(f"{data_path.name}[{idx}] must be an object")
            validate_object(obj, idx, data_path.name)
            if obj["id"] in all_ids:
                fail(f"Duplicate id across files: {obj['id']}")
            all_ids.add(obj["id"])
        total_objects += len(data)

    if not ROLLUP_PATH.exists():
        fail(f"Missing rollup: {ROLLUP_PATH}")

    rollup = load_json(ROLLUP_PATH)
    if not isinstance(rollup, dict):
        fail("Rollup must be an object")
    nodes = rollup.get("nodes")
    cross_links = rollup.get("cross_links")
    if not isinstance(nodes, list) or not isinstance(cross_links, list):
        fail("Rollup nodes/cross_links must be arrays")
    if len(nodes) != total_objects:
        fail("Rollup nodes count does not match total per-CSV objects")

    node_ids: set[str] = set()
    for idx, node in enumerate(nodes):
        if not isinstance(node, dict):
            fail(f"Rollup nodes[{idx}] must be an object")
        validate_object(node, idx, "values_principles_rollup.json")
        node_id = str(node.get("id"))
        if node_id in node_ids:
            fail(f"Duplicate rollup node id: {node_id}")
        node_ids.add(node_id)

    for idx, link in enumerate(cross_links):
        if not isinstance(link, dict):
            fail(f"Rollup cross_links[{idx}] must be an object")
        source_id = str(link.get("source_id") or "")
        target_id = str(link.get("target_id") or "")
        if source_id not in node_ids or target_id not in node_ids:
            fail(f"Rollup cross_links[{idx}] references unknown node ids")

    print("✅ Miro CSV derived JSON validation passed")
    print(f"📁 CSV files validated: {len(csv_paths)}")
    print(f"🧱 Derived objects validated: {total_objects}")
    print(f"🔗 Rollup cross-links: {len(cross_links)}")


if __name__ == "__main__":
    main()
