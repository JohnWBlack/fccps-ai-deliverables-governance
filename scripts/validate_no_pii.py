#!/usr/bin/env python3
"""Fail if tracked public-facing files contain likely email/phone PII."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCAN_PREFIXES = ("project_files/", "governance_docs/", "public/")
TEXT_EXTENSIONS = {".md", ".txt", ".json", ".csv", ".yml", ".yaml"}
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]\d{3}[-.\s]\d{4}(?!\d)")
ALLOWED_EMAILS = {
    "events@brookings.edu",
}


def tracked_files() -> list[Path]:
    out = subprocess.check_output(["git", "ls-files"], cwd=REPO_ROOT, text=True)
    files: list[Path] = []
    for rel in out.splitlines():
        rel = rel.strip()
        if not rel or not rel.startswith(SCAN_PREFIXES):
            continue
        path = REPO_ROOT / rel
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        files.append(path)
    return files


def main() -> None:
    leaks: list[tuple[str, str, str, int]] = []

    for path in tracked_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for lineno, line in enumerate(text.splitlines(), start=1):
            if "[redacted-email]" in line:
                line = line.replace("[redacted-email]", "")
            if "[redacted-phone]" in line:
                line = line.replace("[redacted-phone]", "")

            for match in EMAIL_RE.finditer(line):
                value = match.group(0)
                if value.lower() in ALLOWED_EMAILS:
                    continue
                leaks.append((path.relative_to(REPO_ROOT).as_posix(), "email", value, lineno))
            for match in PHONE_RE.finditer(line):
                leaks.append((path.relative_to(REPO_ROOT).as_posix(), "phone", match.group(0), lineno))

    if leaks:
        print("❌ PII leak check failed. Found likely direct identifiers in tracked files:")
        for rel_path, pii_type, value, lineno in leaks[:200]:
            print(f"  - {rel_path}:{lineno} [{pii_type}] {value}")
        if len(leaks) > 200:
            print(f"  ... and {len(leaks) - 200} additional matches")
        sys.exit(1)

    print("✅ No email/phone PII found in tracked project_files/governance_docs/public text artifacts")


if __name__ == "__main__":
    main()
