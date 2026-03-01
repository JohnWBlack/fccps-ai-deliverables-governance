#!/usr/bin/env python3
"""Create consent-aware, PII-scrubbed public survey JSON artifacts."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "project_files" / "03 - Values & Principles"
OUT_DIR = REPO_ROOT / "public" / "survey_exports"
DEFAULT_INPUTS = [
    SRC_ROOT / "FCCPS_AI_Survey_Analysis_Workbook_results-imported.json",
    SRC_ROOT / "Values_Principles_Survey_Part1_Results_v20260227-0737.json",
]
CONSENT_REGISTRY_PATH = SRC_ROOT / "consent_registry.json"
REPORT_PATH = OUT_DIR / "sanitization_report.json"

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]\d{3}[-.\s]\d{4}(?!\d)")
POSSIBLE_NAME_RE = re.compile(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}$")

CONSENT_ALLOW_TOKENS = ("with attribution", "allow attribution", "attribution ok", "quote with name", "public attribution")
CONSENT_DENY_TOKENS = ("no attribution", "without attribution", "anonymous", "do not attribute", "no quote attribution")


@dataclass
class ConsentInfo:
    respondent_id: str | None
    allow_attribution: bool | None
    display_name: str | None


@dataclass
class Stats:
    files_scanned: int = 0
    files_written: int = 0
    emails_redacted: int = 0
    phones_redacted: int = 0
    names_anonymized: int = 0
    attribution_allowed_rows: int = 0
    attribution_denied_rows: int = 0


def hash_email(value: str) -> str:
    return hashlib.sha256(value.strip().lower().encode("utf-8")).hexdigest()


def load_registry() -> dict[str, dict[str, Any]]:
    if not CONSENT_REGISTRY_PATH.exists():
        return {}
    data = json.loads(CONSENT_REGISTRY_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise RuntimeError("consent_registry.json must be a list of objects")

    out: dict[str, dict[str, Any]] = {}
    for item in data:
        if not isinstance(item, dict):
            continue
        email_hash = str(item.get("email_sha256") or "").strip().lower()
        if not email_hash:
            continue
        out[email_hash] = {
            "allow_attribution": bool(item.get("allow_attribution", False)),
            "display_name": str(item.get("display_name") or "").strip() or None,
        }
    return out


def detect_consent(strings: list[str]) -> bool | None:
    joined = " | ".join(strings).lower()
    if any(token in joined for token in CONSENT_DENY_TOKENS):
        return False
    if any(token in joined for token in CONSENT_ALLOW_TOKENS):
        return True
    return None


def detect_email_hashes(strings: list[str]) -> list[str]:
    hashes: list[str] = []
    for text in strings:
        for match in EMAIL_RE.findall(text):
            hashes.append(hash_email(match))
    return sorted(set(hashes))


def derive_consent(strings: list[str], registry: dict[str, dict[str, Any]]) -> ConsentInfo:
    consent_from_text = detect_consent(strings)
    hashes = detect_email_hashes(strings)

    if hashes:
        # Conservative: any deny in registry forces deny.
        registry_rows = [registry[h] for h in hashes if h in registry]
        if any(not bool(r.get("allow_attribution")) for r in registry_rows):
            allow = False
        elif registry_rows and all(bool(r.get("allow_attribution")) for r in registry_rows):
            allow = True
        else:
            allow = consent_from_text

        first_hash = hashes[0]
        display = None
        if first_hash in registry:
            display = registry[first_hash].get("display_name")
        respondent_id = f"RESP-{first_hash[:8]}"
        return ConsentInfo(respondent_id=respondent_id, allow_attribution=allow, display_name=display)

    return ConsentInfo(respondent_id=None, allow_attribution=consent_from_text, display_name=None)


def redact_contact(text: str, stats: Stats) -> str:
    email_matches = EMAIL_RE.findall(text)
    phone_matches = PHONE_RE.findall(text)
    if email_matches:
        stats.emails_redacted += len(email_matches)
        text = EMAIL_RE.sub("[redacted-email]", text)
    if phone_matches:
        stats.phones_redacted += len(phone_matches)
        text = PHONE_RE.sub("[redacted-phone]", text)
    return text


def anonymize_name(text: str, info: ConsentInfo, stats: Stats) -> str:
    if info.allow_attribution is True:
        return text
    if not info.respondent_id:
        return text
    if POSSIBLE_NAME_RE.fullmatch(text.strip()):
        stats.names_anonymized += 1
        return info.respondent_id
    return text


def scrub_obj(obj: Any, registry: dict[str, dict[str, Any]], stats: Stats, inherited: ConsentInfo | None = None) -> Any:
    if isinstance(obj, dict):
        local_strings = [v for v in obj.values() if isinstance(v, str)]
        info = derive_consent(local_strings, registry)
        if info.respondent_id is None and inherited is not None:
            info = inherited

        if info.allow_attribution is True:
            stats.attribution_allowed_rows += 1
        elif info.allow_attribution is False:
            stats.attribution_denied_rows += 1

        out: dict[str, Any] = {}
        for key, value in obj.items():
            key_lower = str(key).lower()
            if isinstance(value, str):
                scrubbed = redact_contact(value, stats)
                if any(token in key_lower for token in ("name", "participant", "respondent", "attribution")):
                    scrubbed = anonymize_name(scrubbed, info, stats)
                out[key] = scrubbed
            else:
                out[key] = scrub_obj(value, registry, stats, inherited=info)
        return out

    if isinstance(obj, list):
        strings = [value for value in obj if isinstance(value, str)]
        info = derive_consent(strings, registry)
        if info.respondent_id is None and inherited is not None:
            info = inherited

        if info.allow_attribution is True:
            stats.attribution_allowed_rows += 1
        elif info.allow_attribution is False:
            stats.attribution_denied_rows += 1

        out: list[Any] = []
        for value in obj:
            if isinstance(value, str):
                scrubbed = redact_contact(value, stats)
                scrubbed = anonymize_name(scrubbed, info, stats)
                out.append(scrubbed)
            else:
                out.append(scrub_obj(value, registry, stats, inherited=info))
        return out

    if isinstance(obj, str):
        scrubbed = redact_contact(obj, stats)
        if inherited:
            scrubbed = anonymize_name(scrubbed, inherited, stats)
        return scrubbed

    return obj


def input_paths() -> list[Path]:
    return [path for path in DEFAULT_INPUTS if path.exists()]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stats = Stats()
    registry = load_registry()

    scanned: list[dict[str, Any]] = []
    for src_path in input_paths():
        stats.files_scanned += 1
        payload = json.loads(src_path.read_text(encoding="utf-8"))
        scrubbed = scrub_obj(payload, registry, stats)

        dest_path = OUT_DIR / src_path.name
        dest_path.write_text(json.dumps(scrubbed, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        stats.files_written += 1
        scanned.append(
            {
                "source": src_path.relative_to(REPO_ROOT).as_posix(),
                "output": dest_path.relative_to(REPO_ROOT).as_posix(),
                "source_sha256": hashlib.sha256(src_path.read_bytes()).hexdigest(),
                "output_sha256": hashlib.sha256(dest_path.read_bytes()).hexdigest(),
            }
        )

    report = {
        "status": "ok",
        "files": scanned,
        "counts": {
            "files_scanned": stats.files_scanned,
            "files_written": stats.files_written,
            "emails_redacted": stats.emails_redacted,
            "phones_redacted": stats.phones_redacted,
            "names_anonymized": stats.names_anonymized,
            "attribution_allowed_rows": stats.attribution_allowed_rows,
            "attribution_denied_rows": stats.attribution_denied_rows,
        },
        "consent_registry_used": CONSENT_REGISTRY_PATH.exists(),
        "consent_registry_path": CONSENT_REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
    }

    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
