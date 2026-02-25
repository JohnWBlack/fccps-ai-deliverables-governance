#!/usr/bin/env python3
"""Validate derived public artifacts with lightweight structural checks."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = REPO_ROOT / "public"
SCHEMA_PATH = REPO_ROOT / "governance_docs" / "schema" / "glidepath_history.schema.json"
GLIDEPATH_PATH = PUBLIC_DIR / "glidepath_history.json"

REQUIRED_TOP_LEVEL = {"meta", "corridor", "weights", "points"}
REQUIRED_POINT_FIELDS = {
    "generated_at",
    "version_key",
    "what_score",
    "how_score",
    "coverage_what",
    "coverage_how",
    "included_kpis",
}
REQUIRED_GATE_IDS = {f"m{i}" for i in range(1, 9)}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def fail(message: str) -> None:
    print(f"❌ {message}")
    sys.exit(1)


def validate_glidepath_history(payload: dict[str, Any]) -> None:
    if not REQUIRED_TOP_LEVEL.issubset(set(payload.keys())):
        missing = sorted(REQUIRED_TOP_LEVEL - set(payload.keys()))
        fail(f"glidepath_history.json missing top-level keys: {missing}")

    corridor = payload.get("corridor")
    if not isinstance(corridor, dict):
        fail("glidepath_history.json corridor must be an object")

    gates = corridor.get("gates")
    if not isinstance(gates, list):
        fail("glidepath_history.json corridor.gates must be a list")

    gate_ids = {str(g.get("gate_id")) for g in gates if isinstance(g, dict) and g.get("gate_id")}
    if not REQUIRED_GATE_IDS.issubset(gate_ids):
        missing = sorted(REQUIRED_GATE_IDS - gate_ids)
        fail(f"glidepath_history.json corridor missing gate(s): {missing}")

    m7 = next((g for g in gates if isinstance(g, dict) and g.get("gate_id") == "m7"), None)
    if not isinstance(m7, dict):
        fail("glidepath_history.json corridor missing m7 gate")
    if str(m7.get("date")) != "2026-04-24":
        fail("glidepath_history.json m7 date must be 2026-04-24")
    if m7.get("board_ready_deadline") is not True:
        fail("glidepath_history.json m7 must set board_ready_deadline=true")

    for gate in gates:
        if not isinstance(gate, dict):
            fail("glidepath_history.json corridor gate entries must be objects")
        for field in ("what_min", "what_max", "how_min", "how_max"):
            value = gate.get(field)
            if not isinstance(value, (int, float)):
                fail(f"glidepath_history.json gate {gate.get('gate_id')} field {field} must be numeric")
            if value < 0 or value > 10:
                fail(f"glidepath_history.json gate {gate.get('gate_id')} field {field} must be in [0,10]")

    points = payload.get("points")
    if not isinstance(points, list):
        fail("glidepath_history.json points must be a list")

    seen_version_keys: set[str] = set()
    for idx, point in enumerate(points):
        if not isinstance(point, dict):
            fail(f"glidepath_history.json points[{idx}] must be an object")
        if not REQUIRED_POINT_FIELDS.issubset(set(point.keys())):
            missing = sorted(REQUIRED_POINT_FIELDS - set(point.keys()))
            fail(f"glidepath_history.json points[{idx}] missing fields: {missing}")

        version_key = str(point.get("version_key", ""))
        if not version_key:
            fail(f"glidepath_history.json points[{idx}] version_key must be non-empty")
        if version_key in seen_version_keys:
            fail(f"glidepath_history.json duplicate version_key in points: {version_key}")
        seen_version_keys.add(version_key)

        for field in ("what_score", "how_score"):
            value = point.get(field)
            if not isinstance(value, (int, float)) or value < 0 or value > 10:
                fail(f"glidepath_history.json points[{idx}] {field} must be numeric in [0,10]")

        for field in ("coverage_what", "coverage_how"):
            value = point.get(field)
            if not isinstance(value, (int, float)) or value < 0 or value > 1:
                fail(f"glidepath_history.json points[{idx}] {field} must be numeric in [0,1]")

        included = point.get("included_kpis")
        if not isinstance(included, dict):
            fail(f"glidepath_history.json points[{idx}] included_kpis must be an object")
        for axis in ("what", "how"):
            axis_items = included.get(axis)
            if not isinstance(axis_items, list):
                fail(f"glidepath_history.json points[{idx}] included_kpis.{axis} must be a list")


def main() -> None:
    if not SCHEMA_PATH.exists():
        fail(f"Schema file not found: {SCHEMA_PATH}")
    if not GLIDEPATH_PATH.exists():
        fail(f"Required artifact not found: {GLIDEPATH_PATH}")

    _ = load_json(SCHEMA_PATH)
    glidepath = load_json(GLIDEPATH_PATH)
    validate_glidepath_history(glidepath)

    print("✅ Public artifact validation passed")
    print(f"📄 Validated schema: {SCHEMA_PATH}")
    print(f"📉 Validated artifact: {GLIDEPATH_PATH}")


if __name__ == "__main__":
    main()
