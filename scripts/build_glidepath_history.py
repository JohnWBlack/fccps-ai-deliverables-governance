#!/usr/bin/env python3
"""Build deterministic public/glidepath_history.json from snapshot + KPI artifacts."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = REPO_ROOT / "public"
SNAPSHOT_PATH = PUBLIC_DIR / "public_snapshot.json"
KPIS_PATH = PUBLIC_DIR / "kpis.json"
OUTPUT_PATH = PUBLIC_DIR / "glidepath_history.json"

# NOTE: If committee-provided axis weights change, update only these mappings.
WHAT_WEIGHTS: dict[str, float] = {
    "KPI-SCHED-01": 3.0,
    "KPI-SCHED-02": 2.0,
    "KPI-SCHED-03": 1.5,
    "KPI-SCHED-04": 0.5,
    "KPI-PUB-01": 2.0,
    "KPI-PUB-02": 1.0,
}

HOW_WEIGHTS: dict[str, float] = {
    "KPI-CONV-01": 1.5,
    "KPI-CONV-02": 1.0,
    "KPI-CONV-03": 1.0,
    "KPI-CONV-04": 0.75,
    "KPI-CONV-05": 0.75,
    "KPI-CONV-06": 0.75,
    "KPI-CONV-07": 0.5,
    "KPI-CONV-08": 0.5,
    "KPI-CONV-09": 0.75,
    "KPI-CONV-10": 0.5,
    "KPI-FRESH-01": 1.0,
    "KPI-FRESH-02": 1.0,
    "KPI-FRESH-03": 1.0,
}

CORRIDOR_GATES: list[dict[str, Any]] = [
    {"gate_id": "m1", "date": "2026-01-23", "what_min": 1.0, "what_max": 2.0, "how_min": 1.0, "how_max": 2.0, "board_ready_deadline": False},
    {"gate_id": "m2", "date": "2026-02-06", "what_min": 2.0, "what_max": 3.0, "how_min": 2.0, "how_max": 3.0, "board_ready_deadline": False},
    {"gate_id": "m3", "date": "2026-02-20", "what_min": 3.0, "what_max": 4.5, "how_min": 3.0, "how_max": 4.5, "board_ready_deadline": False},
    {"gate_id": "m4", "date": "2026-03-06", "what_min": 4.0, "what_max": 5.5, "how_min": 4.0, "how_max": 5.5, "board_ready_deadline": False},
    {"gate_id": "m5", "date": "2026-03-20", "what_min": 5.0, "what_max": 6.5, "how_min": 5.0, "how_max": 6.5, "board_ready_deadline": False},
    {"gate_id": "m6", "date": "2026-04-10", "what_min": 6.0, "what_max": 7.5, "how_min": 6.0, "how_max": 7.5, "board_ready_deadline": False},
    {"gate_id": "m7", "date": "2026-04-24", "what_min": 7.5, "what_max": 9.0, "how_min": 7.5, "how_max": 9.0, "board_ready_deadline": True},
    {"gate_id": "m8", "date": "2026-05-15", "what_min": 8.5, "what_max": 10.0, "how_min": 8.5, "how_max": 10.0, "board_ready_deadline": False},
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def to_0_10(score_0_100: float) -> float:
    return round(max(0.0, min(100.0, score_0_100)) / 10.0, 2)


def is_instrumented(kpi: dict[str, Any]) -> bool:
    details = kpi.get("details")
    if isinstance(details, dict) and details.get("instrumented") is False:
        return False
    return kpi.get("score") is not None


def axis_score(
    kpis_by_id: dict[str, dict[str, Any]],
    weights: dict[str, float],
) -> tuple[float, float, list[str]]:
    total_weight = sum(weights.values())
    included_weight = 0.0
    weighted_sum = 0.0
    included_ids: list[str] = []

    for kpi_id, weight in weights.items():
        kpi = kpis_by_id.get(kpi_id)
        if not kpi or not is_instrumented(kpi):
            continue
        score = kpi.get("score")
        if not isinstance(score, (int, float)):
            continue
        included_weight += weight
        weighted_sum += float(score) * weight
        included_ids.append(kpi_id)

    coverage = 0.0 if total_weight <= 0 else round(included_weight / total_weight, 4)
    avg_0_100 = 0.0 if included_weight <= 0 else weighted_sum / included_weight
    return to_0_10(avg_0_100), coverage, sorted(included_ids)


def fallback_next_gate(timeline_events: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    now = datetime.now(timezone.utc)
    candidates: list[tuple[datetime, str, str]] = []

    for event in timeline_events:
        event_id = str(event.get("id", ""))
        if not re.match(r"^m\d+$", event_id, flags=re.IGNORECASE):
            continue
        date_str = event.get("date")
        date_val = parse_date(date_str)
        if not date_val or date_val < now:
            continue
        if event.get("status") not in {"upcoming", None}:
            continue
        candidates.append((date_val, event_id, str(date_str)))

    if not candidates:
        return None, None

    candidates.sort(key=lambda item: item[0])
    _, gate_id, gate_date = candidates[0]
    return gate_id, gate_date


def resolve_next_gate(
    kpis_by_id: dict[str, dict[str, Any]],
    timeline_events: list[dict[str, Any]],
) -> tuple[str | None, str | None]:
    for candidate_id in ("KPI-READY-03", "KPI-SCHED-01"):
        details = (kpis_by_id.get(candidate_id) or {}).get("details")
        if isinstance(details, dict):
            gate_id = details.get("next_gate_id")
            gate_date = details.get("next_gate_date")
            if gate_id and gate_date:
                return str(gate_id), str(gate_date)
    return fallback_next_gate(timeline_events)


def base_document() -> dict[str, Any]:
    return {
        "meta": {
            "description": "Historical WHAT/HOW glidepath points with gate corridor targets.",
            "schema_version": "1.0.0",
        },
        "corridor": {
            "gates": CORRIDOR_GATES,
        },
        "weights": {
            "what": WHAT_WEIGHTS,
            "how": HOW_WEIGHTS,
        },
        "points": [],
    }


def build_current_point(snapshot: dict[str, Any], kpis_payload: dict[str, Any]) -> dict[str, Any]:
    version_key = snapshot.get("meta", {}).get("version_key")
    generated_at = snapshot.get("meta", {}).get("generated_at")
    timeline_events = snapshot.get("timeline_events", [])

    kpis = kpis_payload.get("kpis", [])
    kpis_by_id = {str(item.get("id")): item for item in kpis if item.get("id")}

    what_score, coverage_what, included_what = axis_score(kpis_by_id, WHAT_WEIGHTS)
    how_score, coverage_how, included_how = axis_score(kpis_by_id, HOW_WEIGHTS)
    next_gate_id, next_gate_date = resolve_next_gate(kpis_by_id, timeline_events)

    return {
        "generated_at": generated_at,
        "version_key": version_key,
        "next_gate_id": next_gate_id,
        "next_gate_date": next_gate_date,
        "what_score": what_score,
        "how_score": how_score,
        "coverage_what": coverage_what,
        "coverage_how": coverage_how,
        "included_kpis": {
            "what": included_what,
            "how": included_how,
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    if not SNAPSHOT_PATH.exists() or not KPIS_PATH.exists():
        raise FileNotFoundError("Required inputs missing: public_snapshot.json and kpis.json must exist")

    snapshot = load_json(SNAPSHOT_PATH)
    kpis_payload = load_json(KPIS_PATH)

    history = base_document()
    if OUTPUT_PATH.exists():
        existing = load_json(OUTPUT_PATH)
        if isinstance(existing, dict):
            history.update({k: v for k, v in existing.items() if k in {"meta", "corridor", "weights", "points"}})

    history["meta"]["generated_at"] = utc_now_iso()
    current_point = build_current_point(snapshot, kpis_payload)

    points = history.get("points") if isinstance(history.get("points"), list) else []
    if points and isinstance(points[-1], dict) and points[-1].get("version_key") == current_point.get("version_key"):
        print("ℹ️  Glidepath history unchanged (same version_key); no update written.")
        return

    points.append(current_point)
    history["points"] = points

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_json(OUTPUT_PATH, history)
    print(f"📉 Glidepath history written to {OUTPUT_PATH}")
    print(f"🧭 Points stored: {len(points)}")


if __name__ == "__main__":
    main()
