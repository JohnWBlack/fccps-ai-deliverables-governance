#!/usr/bin/env python3
"""Run deterministic 9-stage cognitive pipeline over ingest outputs and SoR context."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent.cognitive_pipeline import run_cognitive_pipeline

REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = REPO_ROOT / "public"
PROJECT_INGEST_DIR = PUBLIC_DIR / "project_ingest"
INGEST_SUMMARY_PATH = PROJECT_INGEST_DIR / "ingest_summary.json"
INGEST_INDEX_PATH = PROJECT_INGEST_DIR / "index.json"
WORKSTREAMS_PATH = REPO_ROOT / "sor" / "workstreams.yml"
DELIVERABLES_PATH = REPO_ROOT / "sor" / "deliverables.yml"
OUTPUT_PATH = PROJECT_INGEST_DIR / "cognitive_control_report.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_if_changed(path: Path, payload: dict[str, Any]) -> bool:
    serialized = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if current == serialized:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialized, encoding="utf-8")
    return True


def load_yaml(path: Path) -> dict[str, Any]:
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8"))


def main() -> None:
    required = [INGEST_SUMMARY_PATH, INGEST_INDEX_PATH, WORKSTREAMS_PATH, DELIVERABLES_PATH]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit("Missing required inputs for cognitive agent:\n- " + "\n- ".join(missing))

    report = run_cognitive_pipeline(
        ingest_summary=load_json(INGEST_SUMMARY_PATH),
        index_payload=load_json(INGEST_INDEX_PATH),
        workstreams_payload=load_yaml(WORKSTREAMS_PATH),
        deliverables_payload=load_yaml(DELIVERABLES_PATH),
    )

    changed = write_json_if_changed(OUTPUT_PATH, report)
    status = "updated" if changed else "unchanged"

    counts = report.get("counts", {}) if isinstance(report, dict) else {}
    print(f"🧠 Cognitive control report {status}: {OUTPUT_PATH}")
    print(
        "📊 Cognitive summary: "
        + f"candidates={counts.get('candidates', 0)}, "
        + f"recommended_actions={counts.get('recommended_actions', 0)}, "
        + f"ingest_promoted={counts.get('ingest_promoted', 0)}, "
        + f"ingest_converted={counts.get('ingest_converted', 0)}"
    )


if __name__ == "__main__":
    main()
