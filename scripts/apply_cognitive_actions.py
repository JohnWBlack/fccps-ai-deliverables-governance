#!/usr/bin/env python3
"""Apply high-confidence cognitive recommendations into SoR supporting-doc links."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = REPO_ROOT / "public" / "project_ingest" / "cognitive_control_report.json"
DELIVERABLES_PATH = REPO_ROOT / "sor" / "deliverables.yml"
OUTPUT_PATH = REPO_ROOT / "sor" / "supporting_documents.yml"
TRANSFORM_VERSION = "1.0.0"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def today_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def dump_yaml(payload: dict[str, Any]) -> str:
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=False)


def write_text_if_changed(path: Path, text: str) -> bool:
    rendered = text if text.endswith("\n") else text + "\n"
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if current == rendered:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    return True


def build_supporting_documents(
    *,
    cognitive_report: dict[str, Any],
    deliverables: list[dict[str, Any]],
    min_confidence: float,
) -> dict[str, Any]:
    deliverable_map = {
        str(item.get("id")): item
        for item in deliverables
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }

    grouped: dict[str, dict[str, Any]] = {}
    actions = cognitive_report.get("recommended_actions", []) if isinstance(cognitive_report, dict) else []
    if not isinstance(actions, list):
        actions = []

    for action in actions:
        if not isinstance(action, dict):
            continue
        confidence = float(action.get("confidence") or 0.0)
        if confidence < min_confidence:
            continue

        deliverable_id = str(action.get("recommended_deliverable_id") or "").strip()
        source_path = str(action.get("source_path") or "").strip()
        if not deliverable_id or not source_path:
            continue
        if deliverable_id not in deliverable_map:
            continue

        bucket = grouped.setdefault(
            deliverable_id,
            {
                "deliverable_id": deliverable_id,
                "workstream_id": str(action.get("recommended_workstream_id") or ""),
                "action": str(action.get("recommended_action") or "review_and_update_deliverable_evidence"),
                "confidence_values": [],
                "evidence_paths": set(),
            },
        )
        bucket["confidence_values"].append(confidence)
        bucket["evidence_paths"].add(source_path)

    links: list[dict[str, Any]] = []
    for deliverable_id in sorted(grouped.keys(), key=str.lower):
        item = grouped[deliverable_id]
        values = [float(v) for v in item.get("confidence_values", [])]
        evidence_paths = sorted(str(path) for path in item.get("evidence_paths", set()))
        links.append(
            {
                "deliverable_id": deliverable_id,
                "workstream_id": str(item.get("workstream_id") or ""),
                "action": str(item.get("action") or "review_and_update_deliverable_evidence"),
                "confidence_max": round(max(values), 4) if values else 0.0,
                "confidence_mean": round(sum(values) / len(values), 4) if values else 0.0,
                "sources_count": len(evidence_paths),
                "evidence_paths": evidence_paths,
            }
        )

    return {
        "metadata": {
            "version": TRANSFORM_VERSION,
            "last_updated": today_iso(),
            "generated_at": utc_now_iso(),
            "description": "Deterministic supporting-document links generated from cognitive_control_report recommendations.",
            "source_report_path": REPORT_PATH.relative_to(REPO_ROOT).as_posix(),
            "source_report_sha256": sha256_file(REPORT_PATH),
            "min_confidence": round(min_confidence, 4),
        },
        "links": links,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply cognitive recommendations into supporting_documents.yml")
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.75,
        help="Minimum recommendation confidence to include in supporting_documents.yml",
    )
    args = parser.parse_args()

    if not REPORT_PATH.exists():
        raise SystemExit(f"Missing required cognitive report: {REPORT_PATH}")
    if not DELIVERABLES_PATH.exists():
        raise SystemExit(f"Missing required SoR file: {DELIVERABLES_PATH}")

    min_confidence = max(0.0, min(1.0, float(args.min_confidence)))
    cognitive_report = load_json(REPORT_PATH)
    deliverables_payload = load_yaml(DELIVERABLES_PATH)
    deliverables = deliverables_payload.get("deliverables", []) if isinstance(deliverables_payload, dict) else []
    if not isinstance(deliverables, list):
        raise SystemExit("sor/deliverables.yml is missing deliverables[] list")

    supporting_documents = build_supporting_documents(
        cognitive_report=cognitive_report,
        deliverables=deliverables,
        min_confidence=min_confidence,
    )
    changed = write_text_if_changed(OUTPUT_PATH, dump_yaml(supporting_documents))
    status = "updated" if changed else "unchanged"

    print(f"🧩 supporting_documents.yml {status}: {OUTPUT_PATH}")
    print(
        "📎 Auto-applied supporting links: "
        + f"{len(supporting_documents.get('links', []))} "
        + f"(min_confidence={min_confidence:.2f})"
    )


if __name__ == "__main__":
    main()
