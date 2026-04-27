#!/usr/bin/env python3
"""Build canonical public risk_register.json from SoR risks + deliverable linkages."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SOR_DIR = REPO_ROOT / "sor"
PUBLIC_DIR = REPO_ROOT / "public"
OUTPUT_PATH = PUBLIC_DIR / "risk_register.json"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def write_json_if_changed(path: Path, payload: dict[str, Any]) -> bool:
    rendered = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if current == rendered:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    return True


def build_risk_register() -> dict[str, Any]:
    risks_data = load_yaml(SOR_DIR / "risks.yml")
    deliverables_data = load_yaml(SOR_DIR / "deliverables.yml")

    risk_entries = risks_data.get("risks", []) if isinstance(risks_data.get("risks"), list) else []
    deliverables = deliverables_data.get("deliverables", []) if isinstance(deliverables_data.get("deliverables"), list) else []

    valid_risk_ids = {
        str(item.get("id") or "").strip()
        for item in risk_entries
        if isinstance(item, dict) and str(item.get("id") or "").strip()
    }

    linked: dict[str, list[dict[str, Any]]] = {risk_id: [] for risk_id in sorted(valid_risk_ids)}
    unknown_refs: set[str] = set()

    for deliverable in deliverables:
        if not isinstance(deliverable, dict):
            continue

        deliverable_id = str(deliverable.get("id") or "").strip()
        if not deliverable_id:
            continue

        risk_refs = deliverable.get("risk_refs") or []
        if not isinstance(risk_refs, list):
            continue

        principle_refs = sorted({str(item).strip() for item in (deliverable.get("principle_refs") or []) if str(item).strip()})
        for risk_ref in risk_refs:
            risk_id = str(risk_ref or "").strip()
            if not risk_id:
                continue
            entry = {
                "deliverable_id": deliverable_id,
                "title": str(deliverable.get("title") or deliverable_id),
                "status": str(deliverable.get("status") or "unknown"),
                "checkpoint_id": str(deliverable.get("checkpoint_id") or ""),
                "workstream_id": str(deliverable.get("workstream_id") or ""),
                "due_date": str(deliverable.get("due_date") or ""),
                "public_url": str(deliverable.get("public_url") or "") or None,
                "principle_refs": principle_refs,
            }
            if risk_id in linked:
                linked[risk_id].append(entry)
            else:
                unknown_refs.add(risk_id)

    risks_payload: list[dict[str, Any]] = []
    for risk in risk_entries:
        if not isinstance(risk, dict):
            continue
        risk_id = str(risk.get("id") or "").strip()
        if not risk_id:
            continue

        evidence = sorted(linked.get(risk_id, []), key=lambda item: (str(item.get("checkpoint_id") or ""), str(item.get("deliverable_id") or "")))
        statuses = sorted({str(item.get("status") or "unknown") for item in evidence})
        principle_union = sorted({ref for item in evidence for ref in (item.get("principle_refs") or [])})

        risks_payload.append(
            {
                "id": risk_id,
                "name": str(risk.get("name") or risk_id),
                "status": str(risk.get("status") or "active"),
                "description": str(risk.get("description") or "") or None,
                "linked_deliverables_count": len(evidence),
                "linked_statuses": statuses,
                "linked_principle_refs": principle_union,
                "linked_deliverables": evidence,
            }
        )

    linked_counts = [int(item.get("linked_deliverables_count") or 0) for item in risks_payload]
    linked_nonzero = sum(1 for value in linked_counts if value > 0)

    return {
        "meta": {
            "generated_at": utc_now_iso(),
            "schema_version": "1.0.0",
            "source": {
                "risks": "sor/risks.yml",
                "deliverables": "sor/deliverables.yml",
            },
            "risk_sor_version": str((risks_data.get("metadata") or {}).get("version") or ""),
            "risk_sor_last_updated": str((risks_data.get("metadata") or {}).get("last_updated") or ""),
            "deliverables_sor_last_updated": str((deliverables_data.get("metadata") or {}).get("last_updated") or ""),
        },
        "summary": {
            "total_risks": len(risks_payload),
            "risks_with_linked_deliverables": linked_nonzero,
            "risks_without_linked_deliverables": max(0, len(risks_payload) - linked_nonzero),
            "unknown_risk_refs_in_deliverables": sorted(unknown_refs),
        },
        "risks": risks_payload,
    }


def main() -> None:
    payload = build_risk_register()
    changed = write_json_if_changed(OUTPUT_PATH, payload)
    print(f"🧷 Risk register written to {OUTPUT_PATH}")
    if not changed:
        print("ℹ️  risk_register.json unchanged")
    print(
        "📊 "
        + f"risks={payload.get('summary', {}).get('total_risks', 0)}, "
        + f"linked={payload.get('summary', {}).get('risks_with_linked_deliverables', 0)}, "
        + f"unlinked={payload.get('summary', {}).get('risks_without_linked_deliverables', 0)}"
    )


if __name__ == "__main__":
    main()
