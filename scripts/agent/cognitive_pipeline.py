from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

TRANSFORM_VERSION = "1.1.0"

STAGE_DEFS = [
    (1, "Curiosity / Motivation", "Set goals, priorities", "Propose exploration candidates"),
    (2, "Perception & Attention", "Validate inputs, label edge cases", "Filter, preprocess, detect salience"),
    (3, "Memory Activation", "Provide domain knowledge, curate corpora", "Retrieve relevant context"),
    (4, "Comprehension", "Interpret ambiguous cases", "Produce grounded representations"),
    (5, "Basic Reasoning", "Define rules, constraints", "Execute inference steps"),
    (6, "Critical Thinking", "Judge tradeoffs, ethical implications", "Run verification, counterfactuals"),
    (7, "Self-Reflection", "Review decisions, update objectives", "Produce introspection logs"),
    (8, "Metacognition", "Adjust strategy, set thresholds", "Calibrate confidence, select strategies"),
    (9, "Cognitive Control", "Final approval, policy decisions", "Orchestrate workflows, enforce constraints"),
]

TOPIC_KEYWORDS = {
    "principles": {"principle", "principles", "values"},
    "policy": {"policy", "recommendation", "outline"},
    "baseline": {"baseline", "definitions", "shared"},
    "risk": {"risk", "risks", "privacy", "security", "integrity"},
    "equity": {"equity", "access", "accessibility"},
    "communications": {"community", "communications", "faq"},
    "implementation": {"implementation", "adoption", "professional", "development"},
}

TOPIC_TO_WORKSTREAM = {
    "policy": "WS-POL",
    "principles": "WS-POL",
    "baseline": "WS-RSB",
    "risk": "WS-DPS",
    "equity": "WS-EQA",
    "communications": "WS-CCI",
    "implementation": "WS-IPC",
}

STATUS_WEIGHT = {
    "in_progress": 0.1,
    "not_started": 0.07,
    "completed": 0.03,
    "cancelled": -0.2,
}


@dataclass
class StageResult:
    stage_id: int
    stage: str
    human_role: str
    ai_role: str
    summary: str
    confidence: float
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage_id": self.stage_id,
            "stage": self.stage,
            "human_role": self.human_role,
            "ai_role": self.ai_role,
            "summary": self.summary,
            "confidence": round(max(0.0, min(1.0, self.confidence)), 4),
            "details": self.details,
        }


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def normalize_tokens(value: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", value.lower()) if len(token) >= 3}


def infer_topics(source_path: str) -> list[str]:
    tokens = normalize_tokens(source_path)
    matched: list[str] = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        if tokens.intersection(keywords):
            matched.append(topic)
    return sorted(matched)


def infer_workstream(source_path: str, workstreams: list[dict[str, Any]]) -> str | None:
    source_lower = source_path.lower()

    explicit_folder_match = re.search(r"/workstreams/([a-z0-9_-]+)/", "/" + source_lower.replace("\\", "/"))
    if explicit_folder_match:
        folder_code = explicit_folder_match.group(1).upper()
        for ws in workstreams:
            ws_id = str(ws.get("id") or "")
            if ws_id.upper().endswith(folder_code):
                return ws_id

    for ws in workstreams:
        ws_id = str(ws.get("id") or "")
        ws_name = str(ws.get("name") or "")
        if not ws_id:
            continue

        ws_tail = ws_id.split("-")[-1].lower()
        ws_name_tokens = normalize_tokens(ws_name)

        if ws_tail and ws_tail in source_lower:
            return ws_id
        if ws_name_tokens and ws_name_tokens.intersection(normalize_tokens(source_path)):
            return ws_id

    return None


def infer_workstream_candidates(source_path: str, topics: list[str], workstreams: list[dict[str, Any]]) -> list[str]:
    inferred = infer_workstream(source_path, workstreams)
    if inferred:
        return [inferred]

    ranked: list[str] = []
    for topic in topics:
        ws_id = TOPIC_TO_WORKSTREAM.get(topic)
        if ws_id:
            ranked.append(ws_id)

    known_ws = {
        str(ws.get("id") or "")
        for ws in workstreams
        if isinstance(ws, dict) and str(ws.get("id") or "")
    }
    deduped = []
    for ws_id in ranked:
        if ws_id in known_ws and ws_id not in deduped:
            deduped.append(ws_id)
    return deduped


def lexical_overlap_score(source_path: str, deliverable: dict[str, Any]) -> float:
    source_tokens = normalize_tokens(source_path)
    title_tokens = normalize_tokens(str(deliverable.get("title") or ""))
    desc_tokens = normalize_tokens(str(deliverable.get("description") or ""))
    target_tokens = title_tokens.union(desc_tokens)
    if not source_tokens or not target_tokens:
        return 0.0
    overlap = len(source_tokens.intersection(target_tokens))
    return min(1.0, overlap / max(4, len(source_tokens)))


def salience_score(candidate: dict[str, Any]) -> float:
    source_path = str(candidate.get("source_path") or "")
    mode = str(candidate.get("mode") or "")
    topics = set(candidate.get("topics") or [])

    score = 0.35
    if mode == "promoted":
        score += 0.25
    if "/workstreams/" in "/" + source_path.lower().replace("\\", "/"):
        score += 0.15
    if "/meetings/" in "/" + source_path.lower().replace("\\", "/"):
        score += 0.1
    if topics:
        score += min(0.2, 0.06 * len(topics))
    if "internal" in source_path.lower():
        score += 0.03
    return round(max(0.0, min(1.0, score)), 4)


def edge_case_flags(candidate: dict[str, Any]) -> list[str]:
    source_path = str(candidate.get("source_path") or "")
    flags: list[str] = []
    if not candidate.get("topics"):
        flags.append("no_topic_signal")
    if len(source_path) > 140:
        flags.append("long_path_name")
    if "members' corners" in source_path.lower():
        flags.append("member_submission_context")
    if "otter_ai" in source_path.lower():
        flags.append("transcript_source")
    return flags


def score_deliverable_match(candidate: dict[str, Any], deliverable: dict[str, Any]) -> tuple[float, dict[str, float], list[str]]:
    reasons: list[str] = []
    components = {
        "workstream": 0.0,
        "topic": 0.0,
        "status": 0.0,
        "lexical": 0.0,
        "mode": 0.0,
        "salience": 0.0,
    }

    c_ws = str(candidate.get("workstream_id") or "")
    d_ws = str(deliverable.get("workstream_id") or "")
    if c_ws and d_ws and c_ws == d_ws:
        components["workstream"] = 0.45
        reasons.append("same_workstream")

    c_topics = set(candidate.get("topics") or [])
    d_tokens = normalize_tokens(f"{deliverable.get('title', '')} {deliverable.get('description', '')}")
    topic_hits = 0
    for topic in c_topics:
        for keyword in TOPIC_KEYWORDS.get(topic, set()):
            if keyword in d_tokens:
                topic_hits += 1
                break
    if topic_hits > 0:
        components["topic"] = min(0.25, 0.09 * topic_hits)
        reasons.append("topic_overlap")

    status = str(deliverable.get("status") or "")
    status_weight = STATUS_WEIGHT.get(status, 0.0)
    if status_weight != 0:
        components["status"] = status_weight
        reasons.append(f"status_{status}")

    lexical = lexical_overlap_score(str(candidate.get("source_path") or ""), deliverable)
    if lexical > 0:
        components["lexical"] = min(0.2, lexical * 0.2)
        reasons.append("lexical_overlap")

    if str(candidate.get("mode") or "") == "promoted":
        components["mode"] = 0.08
        reasons.append("promoted_signal")

    salience = float(candidate.get("salience") or 0.0)
    if salience > 0:
        components["salience"] = min(0.1, salience * 0.1)

    score = sum(components.values())
    return round(max(0.0, min(1.0, score)), 4), components, reasons


def run_cognitive_pipeline(
    *,
    ingest_summary: dict[str, Any],
    index_payload: dict[str, Any],
    workstreams_payload: dict[str, Any],
    deliverables_payload: dict[str, Any],
) -> dict[str, Any]:
    traces: list[StageResult] = []

    promoted = ingest_summary.get("promoted", []) if isinstance(ingest_summary, dict) else []
    converted = ingest_summary.get("converted", []) if isinstance(ingest_summary, dict) else []
    promoted = promoted if isinstance(promoted, list) else []
    converted = converted if isinstance(converted, list) else []

    stage_inputs = {
        "promoted_count": len(promoted),
        "converted_count": len(converted),
        "priority_policy": [
            "favor promoted artifacts",
            "favor in-progress deliverables",
            "penalize ambiguity",
        ],
    }
    traces.append(StageResult(*STAGE_DEFS[0], summary="Established autonomous update objective and priorities.", confidence=1.0, details=stage_inputs))

    candidates: list[dict[str, Any]] = []
    for item in promoted:
        if isinstance(item, dict):
            candidates.append({"source_path": str(item.get("source_path") or ""), "mode": "promoted"})
    for item in converted:
        if isinstance(item, dict):
            candidates.append({"source_path": str(item.get("source_path") or ""), "mode": "converted"})

    dedup: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        source_path = candidate.get("source_path") or ""
        if not source_path:
            continue
        existing = dedup.get(source_path)
        if existing is None or existing.get("mode") != "promoted":
            dedup[source_path] = candidate
    candidates = [dedup[key] for key in sorted(dedup.keys(), key=str.lower)]

    for candidate in candidates:
        candidate["topics"] = infer_topics(str(candidate.get("source_path") or ""))
        candidate["salience"] = salience_score(candidate)
        candidate["edge_case_flags"] = edge_case_flags(candidate)

    salience_bands = {
        "high": sum(1 for c in candidates if float(c.get("salience") or 0) >= 0.75),
        "medium": sum(1 for c in candidates if 0.55 <= float(c.get("salience") or 0) < 0.75),
        "low": sum(1 for c in candidates if float(c.get("salience") or 0) < 0.55),
    }
    traces.append(
        StageResult(
            *STAGE_DEFS[1],
            summary="Filtered ingest deltas and computed salience/edge-case perception signals.",
            confidence=0.95,
            details={"candidate_count": len(candidates), "salience_bands": salience_bands},
        )
    )

    workstreams = workstreams_payload.get("workstreams", []) if isinstance(workstreams_payload, dict) else []
    deliverables = deliverables_payload.get("deliverables", []) if isinstance(deliverables_payload, dict) else []
    workstreams = workstreams if isinstance(workstreams, list) else []
    deliverables = deliverables if isinstance(deliverables, list) else []

    workstream_by_id = {
        str(ws.get("id") or ""): ws
        for ws in workstreams
        if isinstance(ws, dict) and str(ws.get("id") or "")
    }
    deliverables_by_workstream: dict[str, list[dict[str, Any]]] = {}
    for deliverable in deliverables:
        if not isinstance(deliverable, dict):
            continue
        ws_id = str(deliverable.get("workstream_id") or "")
        deliverables_by_workstream.setdefault(ws_id, []).append(deliverable)

    traces.append(
        StageResult(
            *STAGE_DEFS[2],
            summary="Activated SoR memory graph for workstreams, deliverables, and status distributions.",
            confidence=0.95,
            details={
                "workstream_count": len(workstreams),
                "deliverable_count": len(deliverables),
                "workstreams_with_deliverables": sum(1 for ws_id in deliverables_by_workstream.keys() if ws_id),
            },
        )
    )

    for candidate in candidates:
        source_path = str(candidate.get("source_path") or "")
        ws_candidates = infer_workstream_candidates(source_path, list(candidate.get("topics") or []), workstreams)
        candidate["workstream_candidates"] = ws_candidates
        candidate["workstream_id"] = ws_candidates[0] if ws_candidates else None
        inferred_ws = str(candidate.get("workstream_id") or "")
        memory_deliverables = deliverables_by_workstream.get(inferred_ws, [])[:3]
        candidate["memory_retrieval"] = {
            "workstream_name": str(workstream_by_id.get(inferred_ws, {}).get("name") or ""),
            "deliverable_ids": [str(item.get("id") or "") for item in memory_deliverables if isinstance(item, dict)],
        }

    traces.append(
        StageResult(
            *STAGE_DEFS[3],
            summary="Built grounded candidate representations with memory-backed workstream hypotheses.",
            confidence=0.84,
            details={
                "with_inferred_workstream": sum(1 for c in candidates if c.get("workstream_id")),
                "with_memory_links": sum(1 for c in candidates if (c.get("memory_retrieval") or {}).get("deliverable_ids")),
            },
        )
    )

    match_candidates: list[dict[str, Any]] = []
    for candidate in candidates:
        ranked: list[dict[str, Any]] = []
        for deliverable in deliverables:
            if not isinstance(deliverable, dict):
                continue
            score, components, reasons = score_deliverable_match(candidate, deliverable)
            if score <= 0:
                continue
            ranked.append(
                {
                    "deliverable_id": str(deliverable.get("id") or ""),
                    "deliverable_title": str(deliverable.get("title") or ""),
                    "workstream_id": str(deliverable.get("workstream_id") or ""),
                    "status": str(deliverable.get("status") or ""),
                    "score": round(score, 4),
                    "components": components,
                    "reasons": reasons,
                }
            )
        ranked.sort(key=lambda item: (-float(item["score"]), item["deliverable_id"]))
        if ranked:
            match_candidates.append({"candidate": candidate, "matches": ranked[:3]})

    traces.append(
        StageResult(
            *STAGE_DEFS[4],
            summary="Executed weighted reasoning over workstream, topic, status, lexical, and salience signals.",
            confidence=0.86,
            details={
                "matched_candidate_count": len(match_candidates),
                "average_top_score": round(
                    sum(float(item["matches"][0]["score"]) for item in match_candidates) / max(1, len(match_candidates)),
                    4,
                ),
            },
        )
    )

    validated_actions: list[dict[str, Any]] = []
    critical_flags = {"ambiguous_alternative": 0, "workstream_conflict": 0, "sensitive_source": 0}
    for item in match_candidates:
        top = item["matches"][0]
        if float(top.get("score") or 0.0) < 0.55:
            continue
        candidate = item["candidate"]
        risk_flags: list[str] = []
        second_best = item["matches"][1] if len(item["matches"]) > 1 else None
        delta = round(float(top.get("score") or 0.0) - float((second_best or {}).get("score") or 0.0), 4)
        if not candidate.get("workstream_id"):
            risk_flags.append("missing_workstream_inference")
        inferred_ws = str(candidate.get("workstream_id") or "")
        recommended_ws = str(top.get("workstream_id") or "")
        if inferred_ws and recommended_ws and inferred_ws != recommended_ws:
            risk_flags.append("workstream_conflict")
            critical_flags["workstream_conflict"] += 1
        if delta < 0.08 and second_best is not None:
            risk_flags.append("ambiguous_alternative")
            critical_flags["ambiguous_alternative"] += 1
        source_path = str(candidate.get("source_path") or "")
        if "members' corners" in source_path.lower():
            risk_flags.append("sensitive_source")
            critical_flags["sensitive_source"] += 1
        if float(top.get("score") or 0.0) < 0.7:
            risk_flags.append("medium_confidence")

        validated_actions.append(
            {
                "source_path": source_path,
                "mode": candidate.get("mode"),
                "topics": candidate.get("topics"),
                "salience": candidate.get("salience"),
                "inferred_workstream_id": candidate.get("workstream_id"),
                "recommended_deliverable_id": top.get("deliverable_id"),
                "recommended_deliverable_title": top.get("deliverable_title"),
                "recommended_workstream_id": top.get("workstream_id"),
                "recommended_action": "review_and_update_deliverable_evidence",
                "confidence": top.get("score"),
                "counterfactual_delta": delta,
                "risk_flags": risk_flags,
                "candidate_matches": item["matches"],
            }
        )

    traces.append(
        StageResult(
            *STAGE_DEFS[5],
            summary="Ran counterfactual and conflict checks to stress-test reasoning hypotheses.",
            confidence=0.88,
            details={"validated_actions": len(validated_actions), "critical_flags": critical_flags},
        )
    )

    low_confidence_count = sum(1 for action in validated_actions if float(action.get("confidence") or 0.0) < 0.7)
    ambiguity_rate = round(
        sum(1 for action in validated_actions if "ambiguous_alternative" in list(action.get("risk_flags") or []))
        / max(1, len(validated_actions)),
        4,
    )
    missing_ws_rate = round(
        sum(1 for action in validated_actions if "missing_workstream_inference" in list(action.get("risk_flags") or []))
        / max(1, len(validated_actions)),
        4,
    )
    traces.append(
        StageResult(
            *STAGE_DEFS[6],
            summary="Generated introspection diagnostics over uncertainty, ambiguity, and mapping gaps.",
            confidence=0.9,
            details={
                "low_confidence_actions": low_confidence_count,
                "unmapped_candidates": max(0, len(candidates) - len(match_candidates)),
                "ambiguity_rate": ambiguity_rate,
                "missing_workstream_rate": missing_ws_rate,
            },
        )
    )

    calibrated_threshold = 0.62
    if ambiguity_rate >= 0.25:
        calibrated_threshold += 0.05
    if missing_ws_rate >= 0.3:
        calibrated_threshold += 0.03

    calibrated_actions: list[dict[str, Any]] = []
    for action in validated_actions:
        confidence = float(action.get("confidence") or 0.0)
        risk_flags = list(action.get("risk_flags") or [])
        penalty = 0.0
        if "ambiguous_alternative" in risk_flags:
            penalty += 0.08
        if "workstream_conflict" in risk_flags:
            penalty += 0.06
        if "sensitive_source" in risk_flags:
            penalty += 0.05
        if "missing_workstream_inference" in risk_flags:
            penalty += 0.04
        adjusted = max(0.0, min(1.0, confidence - penalty))
        action["confidence_adjusted"] = round(adjusted, 4)
        action["confidence_penalty"] = round(penalty, 4)
        if adjusted >= calibrated_threshold:
            calibrated_actions.append(action)

    if not calibrated_actions:
        recommended_review_mode = "manual_required"
    elif any("sensitive_source" in list(action.get("risk_flags") or []) for action in calibrated_actions):
        recommended_review_mode = "guided_review"
    elif all(float(action.get("confidence_adjusted") or 0) >= 0.8 for action in calibrated_actions):
        recommended_review_mode = "fast_track_review"
    else:
        recommended_review_mode = "guided_review"

    auto_apply_candidates = [
        {
            "source_path": str(action.get("source_path") or ""),
            "recommended_deliverable_id": str(action.get("recommended_deliverable_id") or ""),
            "confidence_adjusted": float(action.get("confidence_adjusted") or 0.0),
        }
        for action in calibrated_actions
        if float(action.get("confidence_adjusted") or 0.0) >= max(0.75, calibrated_threshold)
        and "sensitive_source" not in list(action.get("risk_flags") or [])
    ]
    auto_apply_candidates.sort(key=lambda item: (-float(item["confidence_adjusted"]), str(item["recommended_deliverable_id"]), str(item["source_path"])))

    traces.append(
        StageResult(
            *STAGE_DEFS[7],
            summary="Calibrated confidence thresholds and selected execution strategy.",
            confidence=0.9,
            details={
                "recommended_review_mode": recommended_review_mode,
                "calibrated_threshold": round(calibrated_threshold, 4),
                "retained_actions": len(calibrated_actions),
                "auto_apply_candidates": len(auto_apply_candidates),
            },
        )
    )

    requires_human_approval = recommended_review_mode != "fast_track_review"
    auto_apply_enabled = len(auto_apply_candidates) > 0

    final = {
        "generated_at": utc_now_iso(),
        "transform_version": TRANSFORM_VERSION,
        "objective": "Detect ingest impact on SoR/supporting documents and emit deterministic update triggers.",
        "counts": {
            "ingest_promoted": len(promoted),
            "ingest_converted": len(converted),
            "candidates": len(candidates),
            "recommended_actions": len(calibrated_actions),
            "auto_apply_candidates": len(auto_apply_candidates),
        },
        "recommended_review_mode": recommended_review_mode,
        "recommended_actions": sorted(calibrated_actions, key=lambda item: (str(item.get("recommended_deliverable_id") or ""), str(item.get("source_path") or ""))),
        "auto_apply_candidates": auto_apply_candidates,
        "stage_trace": [trace.to_dict() for trace in traces],
        "governance": {
            "requires_human_approval": requires_human_approval,
            "auto_apply_sor_changes": auto_apply_enabled,
            "approval_policy": "Auto-apply may proceed for high-confidence, non-sensitive actions; always enforce validate_sor.py and validate_public.py before publish.",
            "minimum_auto_apply_confidence": max(0.75, round(calibrated_threshold, 4)),
        },
    }

    traces.append(
        StageResult(
            *STAGE_DEFS[8],
            summary="Produced final cognitive-control policy packet and autonomous execution candidates.",
            confidence=1.0,
            details={
                "report_ready": True,
                "recommended_actions": len(calibrated_actions),
                "auto_apply_enabled": auto_apply_enabled,
            },
        )
    )
    final["stage_trace"] = [trace.to_dict() for trace in traces]
    return final
