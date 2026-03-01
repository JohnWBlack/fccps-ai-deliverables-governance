#!/usr/bin/env python3
"""Autopilot synthesis from Miro rollup into canonical sor/principles.yml with circuit breakers."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "project_files" / "03 - Values & Principles"
DERIVED_DIR = SRC_DIR / "derived_json"
ROLLUP_PATH = DERIVED_DIR / "values_principles_rollup.json"
SOR_PATH = REPO_ROOT / "sor" / "principles.yml"
PUBLIC_REPORT_PATH = REPO_ROOT / "public" / "autopilot_report.json"
TRANSFORM_VERSION = "1.0.0"
MAX_CHANGE_RATIO = 0.20
PIPELINE = [
    "validate_sor.py",
    "build_snapshot.py",
    "build_kpis.py",
    "quality_checks.py",
    "build_catalog.py",
    "build_glidepath_history.py",
    "pii_scan.py",
    "scrub_survey_exports.py",
    "validate_public.py",
    "validate_no_pii.py",
]


class CircuitBreakerError(RuntimeError):
    """Raised when a required guardrail is violated."""


@dataclass
class PrincipleCandidate:
    short_label: str
    statement: str
    confidence: str
    supporting_node_ids: list[str]


@dataclass
class ExistingPrinciple:
    id: str
    stable_key: str
    short_label: str
    statement: str
    confidence: str
    source_refs: list[dict[str, Any]]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_key(value: str) -> str:
    lowered = value.lower().strip()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    return lowered.strip("-") or "principle"


def run_cmd(args: list[str]) -> None:
    completed = subprocess.run(args, cwd=str(REPO_ROOT), text=True, capture_output=True)
    if completed.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(args)}\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_existing_principles() -> list[ExistingPrinciple]:
    if not SOR_PATH.exists():
        return []
    data = yaml.safe_load(SOR_PATH.read_text(encoding="utf-8")) or {}
    principles = data.get("principles", [])
    existing: list[ExistingPrinciple] = []
    for entry in principles:
        if not isinstance(entry, dict):
            continue
        short = str(entry.get("short_label") or "")
        entry_id = str(entry.get("id") or "")
        if not short or not entry_id:
            continue
        existing.append(
            ExistingPrinciple(
                id=entry_id,
                stable_key=str(entry.get("stable_key") or stable_key(short)),
                short_label=short,
                statement=str(entry.get("statement") or ""),
                confidence=str(entry.get("confidence") or "med"),
                source_refs=entry.get("source_refs") if isinstance(entry.get("source_refs"), list) else [],
            )
        )
    return existing


def collect_manifest_hashes() -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(DERIVED_DIR.glob("*.manifest.json"), key=lambda p: p.name.lower()):
        manifest = load_json(path)
        csv_path = str(manifest.get("source_csv_path") or "")
        csv_hash = str(manifest.get("source_sha256") or "")
        if csv_path and csv_hash:
            hashes[csv_path] = csv_hash
    return hashes


def build_nodes_by_id(rollup: dict[str, Any]) -> dict[str, dict[str, Any]]:
    nodes = rollup.get("nodes", [])
    if not isinstance(nodes, list):
        raise CircuitBreakerError("Rollup nodes must be an array")
    by_id: dict[str, dict[str, Any]] = {}
    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_id = str(node.get("id") or "")
        if node_id:
            by_id[node_id] = node
    return by_id


def build_prompt(rollup: dict[str, Any], prior: list[ExistingPrinciple]) -> list[dict[str, str]]:
    minimal_nodes = [
        {
            "id": node.get("id"),
            "text": node.get("text"),
            "inferred_type": node.get("inferred_type"),
            "parent_id": node.get("parent_id"),
            "group_path": node.get("group_path"),
            "confidence": node.get("confidence"),
        }
        for node in rollup.get("nodes", [])
        if isinstance(node, dict)
    ]
    prior_payload = [
        {
            "id": entry.id,
            "stable_key": entry.stable_key,
            "short_label": entry.short_label,
            "statement": entry.statement,
        }
        for entry in prior
    ]

    instruction = {
        "task": "Synthesize canonical district AI principles from Miro-derived nodes",
        "requirements": [
            "Return strict JSON object with key principles",
            "Each principle must contain: short_label, statement, confidence (high|med|low), supporting_node_ids[]",
            "Use only supporting_node_ids present in provided nodes",
            "Use concise policy-level statements",
            "Do not output markdown or commentary",
        ],
        "output_schema": {
            "principles": [
                {
                    "short_label": "string",
                    "statement": "string",
                    "confidence": "high|med|low",
                    "supporting_node_ids": ["string"],
                }
            ]
        },
    }

    return [
        {"role": "system", "content": "You are a deterministic policy synthesis engine. Output JSON only."},
        {
            "role": "user",
            "content": json.dumps(
                {
                    "instruction": instruction,
                    "prior_principles": prior_payload,
                    "rollup_nodes": minimal_nodes,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
        },
    ]


def call_openai(messages: list[dict[str, str]]) -> dict[str, Any]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise CircuitBreakerError("OPENAI_API_KEY is required for autopilot synthesis")

    payload = {
        "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        "temperature": 0,
        "messages": messages,
        "response_format": {"type": "json_object"},
    }

    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise CircuitBreakerError(f"OpenAI API error ({exc.code}): {detail}") from exc
    except urllib.error.URLError as exc:
        raise CircuitBreakerError(f"OpenAI request failed: {exc}") from exc

    content = (
        body.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )
    if not isinstance(content, str) or not content.strip():
        raise CircuitBreakerError("OpenAI response missing message content")

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise CircuitBreakerError(f"OpenAI content was not valid JSON: {content[:500]}") from exc


def normalize_synthesis(payload: dict[str, Any], nodes_by_id: dict[str, dict[str, Any]]) -> list[PrincipleCandidate]:
    raw = payload.get("principles")
    if not isinstance(raw, list) or not raw:
        raise CircuitBreakerError("Synthesis payload must include non-empty principles[]")

    candidates: list[PrincipleCandidate] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        short = str(item.get("short_label") or "").strip()
        statement = str(item.get("statement") or "").strip()
        confidence = str(item.get("confidence") or "").strip().lower()
        supporting = item.get("supporting_node_ids")
        if not short or not statement:
            continue
        if confidence not in {"high", "med", "low"}:
            raise CircuitBreakerError(f"Invalid confidence for {short}: {confidence}")
        if not isinstance(supporting, list) or not supporting:
            raise CircuitBreakerError(f"Principle '{short}' missing supporting_node_ids")
        cleaned_supporting = [str(node_id) for node_id in supporting if str(node_id) in nodes_by_id]
        if not cleaned_supporting:
            raise CircuitBreakerError(f"Principle '{short}' has no valid supporting_node_ids")
        candidates.append(
            PrincipleCandidate(
                short_label=short,
                statement=statement,
                confidence=confidence,
                supporting_node_ids=sorted(set(cleaned_supporting)),
            )
        )

    if not candidates:
        raise CircuitBreakerError("No valid principles parsed from synthesis payload")
    return candidates


def deterministic_synthesis(rollup: dict[str, Any], prior: list[ExistingPrinciple]) -> list[PrincipleCandidate]:
    nodes_by_id = build_nodes_by_id(rollup)
    messages = build_prompt(rollup, prior)

    first = call_openai(messages)
    second = call_openai(messages)

    first_norm = normalize_synthesis(first, nodes_by_id)
    second_norm = normalize_synthesis(second, nodes_by_id)

    canonical_first = json.dumps([candidate.__dict__ for candidate in first_norm], sort_keys=True)
    canonical_second = json.dumps([candidate.__dict__ for candidate in second_norm], sort_keys=True)
    if canonical_first != canonical_second:
        raise CircuitBreakerError("Stability breaker: synthesis outputs differ across two deterministic runs")

    return first_norm


def assign_ids(
    candidates: list[PrincipleCandidate],
    existing: list[ExistingPrinciple],
    manifest_hashes: dict[str, str],
    nodes_by_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    by_key = {item.stable_key: item for item in existing}

    existing_ids = [item.id for item in existing]
    max_id_num = 0
    for item_id in existing_ids:
        match = re.match(r"^P-(\d+)$", item_id)
        if match:
            max_id_num = max(max_id_num, int(match.group(1)))

    results: list[dict[str, Any]] = []
    changed_ids: list[str] = []
    added_ids: list[str] = []

    seen_keys: set[str] = set()

    for candidate in sorted(candidates, key=lambda value: stable_key(value.short_label)):
        key = stable_key(candidate.short_label)
        if key in seen_keys:
            continue
        seen_keys.add(key)

        existing_item = by_key.get(key)
        if existing_item:
            principle_id = existing_item.id
        else:
            max_id_num += 1
            principle_id = f"P-{max_id_num:03d}"
            added_ids.append(principle_id)

        source_refs: list[dict[str, Any]] = []
        for node_id in candidate.supporting_node_ids:
            node = nodes_by_id[node_id]
            csv_path = str(node.get("source_csv_path") or "")
            row_index = int(node.get("source_row_index") or 0)
            csv_hash = manifest_hashes.get(csv_path, "")
            source_refs.append(
                {
                    "node_id": node_id,
                    "source_csv_path": csv_path,
                    "source_row_index": row_index,
                    "source_sha256": csv_hash,
                }
            )

        source_refs = sorted(source_refs, key=lambda entry: (entry["source_csv_path"], entry["source_row_index"], entry["node_id"]))

        item = {
            "id": principle_id,
            "stable_key": key,
            "short_label": candidate.short_label,
            "statement": candidate.statement,
            "confidence": candidate.confidence,
            "status": "active",
            "source_refs": source_refs,
        }
        results.append(item)

        if existing_item:
            if (
                existing_item.statement != candidate.statement
                or existing_item.short_label != candidate.short_label
                or existing_item.confidence != candidate.confidence
            ):
                changed_ids.append(principle_id)

    # No deletions allowed: carry forward any existing principle not produced in this run.
    result_ids = {entry["id"] for entry in results}
    for legacy in existing:
        if legacy.id in result_ids:
            continue
        results.append(
            {
                "id": legacy.id,
                "stable_key": legacy.stable_key,
                "short_label": legacy.short_label,
                "statement": legacy.statement,
                "confidence": legacy.confidence,
                "status": "active",
                "source_refs": legacy.source_refs,
            }
        )

    results = sorted(results, key=lambda entry: entry["id"])

    existing_count = len(existing)
    change_count = len(set(changed_ids + added_ids))
    change_ratio = 0.0 if existing_count == 0 else round(change_count / existing_count, 4)

    stats = {
        "existing_count": existing_count,
        "final_count": len(results),
        "added_ids": sorted(added_ids),
        "changed_ids": sorted(set(changed_ids)),
        "change_count": change_count,
        "change_ratio": change_ratio,
    }
    return results, stats


def write_yaml_principles(principles: list[dict[str, Any]], report_hashes: dict[str, str]) -> None:
    payload = {
        "metadata": {
            "version": TRANSFORM_VERSION,
            "generated_at": utc_now_iso(),
            "description": "Canonical principles synthesized from Miro CSV derived graph",
            "input_hashes": report_hashes,
        },
        "principles": principles,
    }
    SOR_PATH.parent.mkdir(parents=True, exist_ok=True)
    SOR_PATH.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=False), encoding="utf-8")


def create_backup_tag() -> str:
    tag = f"autopilot-backup-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    run_cmd(["git", "tag", tag])
    return tag


def rollback_to_tag(tag: str) -> None:
    run_cmd(["git", "reset", "--hard", tag])


def run_pipeline() -> None:
    for script in PIPELINE:
        run_cmd([sys.executable, str(REPO_ROOT / "scripts" / script)])


def maybe_open_issue(report: dict[str, Any], reason: str) -> str | None:
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        return None

    title = f"Autopilot circuit breaker: {reason[:80]}"
    body = "\n".join(
        [
            "Autopilot run failed circuit breakers.",
            "",
            f"Reason: {reason}",
            "",
            "Report JSON:",
            "```json",
            json.dumps(report, indent=2, sort_keys=True),
            "```",
        ]
    )

    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/issues",
        data=json.dumps({"title": title, "body": body, "labels": ["autopilot", "circuit-breaker"]}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return str(payload.get("html_url") or "")
    except Exception:
        return None


def write_report(report: dict[str, Any]) -> None:
    PUBLIC_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    PUBLIC_REPORT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    report: dict[str, Any] = {
        "generated_at": utc_now_iso(),
        "status": "started",
        "transform_version": TRANSFORM_VERSION,
        "inputs": {},
        "circuit_breakers": {},
        "changes": {},
    }

    backup_tag: str | None = None
    try:
        if not ROLLUP_PATH.exists():
            raise CircuitBreakerError(f"Missing rollup input: {ROLLUP_PATH}")

        rollup = load_json(ROLLUP_PATH)
        nodes_by_id = build_nodes_by_id(rollup)
        manifest_hashes = collect_manifest_hashes()
        existing = load_existing_principles()

        report["inputs"] = {
            "rollup_sha256": sha256_file(ROLLUP_PATH),
            "manifest_hashes": manifest_hashes,
            "existing_principles_count": len(existing),
        }

        synthesized = deterministic_synthesis(rollup, existing)
        low_confidence_count = sum(1 for item in synthesized if item.confidence == "low")
        report["circuit_breakers"]["stability"] = "pass"
        report["circuit_breakers"]["low_confidence_count"] = low_confidence_count

        if low_confidence_count > 0:
            raise CircuitBreakerError("Confidence breaker: synthesis produced low-confidence principles")

        principles, change_stats = assign_ids(synthesized, existing, manifest_hashes, nodes_by_id)
        report["changes"] = change_stats

        if change_stats["existing_count"] > 0 and change_stats["change_ratio"] > MAX_CHANGE_RATIO:
            raise CircuitBreakerError(
                f"Bounded-change breaker: change ratio {change_stats['change_ratio']:.4f} exceeds {MAX_CHANGE_RATIO:.2f}"
            )
        report["circuit_breakers"]["bounded_change"] = "pass"

        backup_tag = create_backup_tag()
        report["backup_tag"] = backup_tag

        write_yaml_principles(principles, report["inputs"])
        run_pipeline()

        report["status"] = "success"
        report["principle_ids"] = [entry["id"] for entry in principles]
        write_report(report)
        print("✅ Autopilot synthesis completed")
        return

    except CircuitBreakerError as exc:
        report["status"] = "aborted"
        report["failure_reason"] = str(exc)
    except Exception as exc:  # noqa: BLE001
        report["status"] = "failed"
        report["failure_reason"] = str(exc)

    if backup_tag:
        try:
            rollback_to_tag(backup_tag)
            report["rollback"] = f"reset to {backup_tag}"
        except Exception as rollback_exc:  # noqa: BLE001
            report["rollback"] = f"rollback failed: {rollback_exc}"

    issue_url = maybe_open_issue(report, str(report.get("failure_reason", "autopilot failure")))
    if issue_url:
        report["issue_url"] = issue_url

    write_report(report)
    print(f"❌ {report.get('failure_reason', 'autopilot failed')}")
    sys.exit(1)


if __name__ == "__main__":
    main()
