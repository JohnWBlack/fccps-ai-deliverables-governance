#!/usr/bin/env python3
"""Build deterministic glidepath diagnostics for explainable next actions."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = REPO_ROOT / "public"
GLIDEPATH_HISTORY_PATH = PUBLIC_DIR / "glidepath_history.json"
KPIS_PATH = PUBLIC_DIR / "kpis.json"
KPI_EVIDENCE_PATH = PUBLIC_DIR / "kpi_evidence.json"
SNAPSHOT_PATH = PUBLIC_DIR / "public_snapshot.json"
PROJECT_INGEST_INDEX_PATH = PUBLIC_DIR / "project_ingest" / "index.json"
OUTPUT_PATH = PUBLIC_DIR / "glidepath_diagnostics.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def write_json_if_changed(path: Path, payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if current != rendered:
        path.write_text(rendered, encoding="utf-8")


def score_to_gate_id(score: float, gates: list[dict[str, Any]], axis_prefix: str) -> str | None:
    min_key = f"{axis_prefix}_min"
    max_key = f"{axis_prefix}_max"

    in_range: list[tuple[float, str]] = []
    closest: list[tuple[float, str]] = []
    for gate in gates:
        gate_id = str(gate.get("gate_id") or "")
        if not gate_id:
            continue
        min_val = float(gate.get(min_key, 0.0))
        max_val = float(gate.get(max_key, 10.0))
        midpoint = (min_val + max_val) / 2.0
        distance = abs(score - midpoint)
        closest.append((distance, gate_id))
        if min_val <= score <= max_val:
            in_range.append((distance, gate_id))

    ranked = in_range or closest
    if not ranked:
        return None
    ranked.sort(key=lambda item: (item[0], item[1]))
    return ranked[0][1]


def signed_out(value: float, low: float, high: float) -> float:
    if value < low:
        return round(value - low, 2)
    if value > high:
        return round(value - high, 2)
    return 0.0


def evidence_paths_for_kpi(kpi_id: str, evidence_payload: dict[str, Any]) -> list[str]:
    evidence_by_kpi = evidence_payload.get("evidence", {})
    if not isinstance(evidence_by_kpi, dict):
        return []
    entries = evidence_by_kpi.get(kpi_id, [])
    if not isinstance(entries, list):
        return []
    paths = {
        str(item.get("doc_path"))
        for item in entries
        if isinstance(item, dict) and isinstance(item.get("doc_path"), str) and str(item.get("doc_path")).strip()
    }
    return sorted(paths)


def rank_kpis(
    kpis_by_id: dict[str, dict[str, Any]],
    evidence_payload: dict[str, Any],
    weights: dict[str, float],
    mode: str,
) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    for kpi_id in sorted(weights.keys()):
        weight = float(weights[kpi_id])
        kpi = kpis_by_id.get(kpi_id)
        if not isinstance(kpi, dict):
            continue
        score = kpi.get("score")
        if not isinstance(score, (int, float)):
            continue

        score_float = float(score)
        metric = ((100.0 - score_float) if mode == "blockers" else score_float) * weight
        paths = evidence_paths_for_kpi(kpi_id, evidence_payload)
        evidence_entries = evidence_payload.get("evidence", {}).get(kpi_id, [])
        evidence_count = len(evidence_entries) if isinstance(evidence_entries, list) else 0
        ranked.append(
            {
                "kpi_id": kpi_id,
                "weight": round(weight, 4),
                "score": round(score_float, 2),
                "evidence_count": evidence_count,
                "evidence_paths": paths,
                "_rank_metric": round(metric, 6),
            }
        )

    ranked.sort(key=lambda item: (-float(item["_rank_metric"]), str(item["kpi_id"])))
    for item in ranked:
        item.pop("_rank_metric", None)
    return ranked


def due_by_gate(snapshot: dict[str, Any], next_gate_date: str | None) -> list[dict[str, Any]]:
    gate_dt = parse_date(next_gate_date)
    deliverables = snapshot.get("deliverables", [])
    if gate_dt is None or not isinstance(deliverables, list):
        return []

    due: list[dict[str, Any]] = []
    for item in deliverables:
        if not isinstance(item, dict):
            continue
        due_date = parse_date(item.get("due_date"))
        if due_date is None or due_date > gate_dt:
            continue
        due.append(
            {
                "id": str(item.get("id") or ""),
                "status": str(item.get("status") or "unknown"),
                "workstream": str(item.get("workstream_id") or "committee"),
                "_due_date": str(item.get("due_date") or ""),
            }
        )

    due = [item for item in due if item["id"]]
    due.sort(key=lambda item: (item["_due_date"], item["id"]))
    for item in due:
        item.pop("_due_date", None)
    return due


def ingest_summary(index_payload: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(index_payload, dict):
        return {"present": False, "entries_count": 0, "categories": []}

    entries = index_payload.get("entries", [])
    if not isinstance(entries, list):
        return {"present": True, "entries_count": 0, "categories": []}

    categories = sorted(
        {
            str(entry.get("category"))
            for entry in entries
            if isinstance(entry, dict) and isinstance(entry.get("category"), str) and str(entry.get("category")).strip()
        }
    )
    return {"present": True, "entries_count": len(entries), "categories": categories}


def build_diagnostics() -> dict[str, Any]:
    glidepath = load_json(GLIDEPATH_HISTORY_PATH)
    kpis_payload = load_json(KPIS_PATH)
    evidence_payload = load_json(KPI_EVIDENCE_PATH)
    snapshot = load_json(SNAPSHOT_PATH)
    ingest_index = load_json(PROJECT_INGEST_INDEX_PATH) if PROJECT_INGEST_INDEX_PATH.exists() else None

    gates = glidepath.get("corridor", {}).get("gates", [])
    points = glidepath.get("points", [])
    weights = glidepath.get("weights", {})

    if not isinstance(gates, list) or not gates:
        raise ValueError("glidepath_history.json corridor.gates is missing or empty")
    if not isinstance(points, list) or not points:
        raise ValueError("glidepath_history.json points is missing or empty")

    latest_point = points[-1] if isinstance(points[-1], dict) else {}
    what_score = float(latest_point.get("what_score", 0.0))
    how_score = float(latest_point.get("how_score", 0.0))
    next_gate_id = str(latest_point.get("next_gate_id") or "")

    gate_by_id = {
        str(gate.get("gate_id")): gate
        for gate in gates
        if isinstance(gate, dict) and gate.get("gate_id")
    }
    next_gate = gate_by_id.get(next_gate_id)
    if not isinstance(next_gate, dict):
        raise ValueError("Latest glidepath point references a missing next_gate_id")

    what_min = float(next_gate.get("what_min", 0.0))
    what_max = float(next_gate.get("what_max", 10.0))
    how_min = float(next_gate.get("how_min", 0.0))
    how_max = float(next_gate.get("how_max", 10.0))

    what_out = signed_out(what_score, what_min, what_max)
    how_out = signed_out(how_score, how_min, how_max)
    axes_out = [axis for axis, delta in (("what", what_out), ("how", how_out)) if delta != 0]

    what_match_id = score_to_gate_id(what_score, gates, "what")
    how_match_id = score_to_gate_id(how_score, gates, "how")

    kpi_list = kpis_payload.get("kpis", [])
    kpis_by_id = {
        str(item.get("id")): item
        for item in kpi_list
        if isinstance(item, dict) and item.get("id")
    }

    what_weights = weights.get("what", {}) if isinstance(weights.get("what"), dict) else {}
    how_weights = weights.get("how", {}) if isinstance(weights.get("how"), dict) else {}

    diagnostics = {
        "generated_at": utc_now_iso(),
        "version_key": str(snapshot.get("meta", {}).get("version_key") or ""),
        "now": {
            "what": round(what_score, 2),
            "how": round(how_score, 2),
            "what_corridor_id": what_match_id,
            "how_corridor_id": how_match_id,
            "corridor_matches": [
                f"WHAT~{str(what_match_id).upper()}" if what_match_id else "WHAT~UNKNOWN",
                f"HOW~{str(how_match_id).upper()}" if how_match_id else "HOW~UNKNOWN",
            ],
        },
        "next_gate": {
            "id": next_gate_id,
            "corridor": {
                "what_min": what_min,
                "what_max": what_max,
                "how_min": how_min,
                "how_max": how_max,
            },
            "midpoint": {
                "what": round((what_min + what_max) / 2.0, 2),
                "how": round((how_min + how_max) / 2.0, 2),
            },
        },
        "outside_corridor": {
            "what_out": what_out,
            "how_out": how_out,
            "axes_out": axes_out,
        },
        "what_blockers_top": rank_kpis(kpis_by_id, evidence_payload, what_weights, mode="blockers"),
        "how_drivers_top": rank_kpis(kpis_by_id, evidence_payload, how_weights, mode="drivers"),
        "deliverables_due_next_gate": due_by_gate(snapshot, latest_point.get("next_gate_date")),
        "project_ingest": ingest_summary(ingest_index),
    }

    if OUTPUT_PATH.exists():
        existing = load_json(OUTPUT_PATH)
        if (
            isinstance(existing, dict)
            and str(existing.get("version_key") or "") == diagnostics["version_key"]
            and isinstance(existing.get("generated_at"), str)
        ):
            diagnostics["generated_at"] = str(existing.get("generated_at"))

    return diagnostics


def main() -> None:
    diagnostics = build_diagnostics()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_json_if_changed(OUTPUT_PATH, diagnostics)
    print(f"📌 Glidepath diagnostics written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
