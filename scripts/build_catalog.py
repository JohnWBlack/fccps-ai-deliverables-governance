#!/usr/bin/env python3
"""Build a public-safe file inventory for the repository."""

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "public" / "file_catalog.json"
EXCLUDED_PATTERNS = [
    ".git",
    "node_modules",
    ".env",
    "secrets",
    "Thumbs.db",
    "thumbs.db",
    "desktop.ini",
    "*.tmp",
    "*.lnk",
    "*.url",
]


def should_exclude(path: Path) -> bool:
    lower_path = str(path).replace("\\", "/").lower()
    name = path.name.lower()

    if any(part in {".git", "node_modules", "secrets"} for part in path.parts):
        return True
    if name in {"thumbs.db", "desktop.ini"}:
        return True
    if name.endswith((".tmp", ".lnk", ".url")):
        return True
    if "/.env" in lower_path or name == ".env":
        return True
    return False


def iso_from_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def derive_tags(path: Path) -> list[str]:
    tags: list[str] = []
    for segment in path.parts[:-1]:
        cleaned = segment.strip().lower().replace(" ", "_").replace("-", "_")
        if cleaned and cleaned not in tags:
            tags.append(cleaned)

    path_lower = str(path).lower()
    if "meeting" in path_lower and "meeting" not in tags:
        tags.append("meeting")
    if "workstream" in path_lower and "workstreams" not in tags:
        tags.append("workstreams")
    return tags


def git_current_branch() -> str:
    env_branch = os.getenv("GITHUB_REF_NAME")
    if env_branch:
        return env_branch
    try:
        out = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=REPO_ROOT, text=True)
        return out.strip()
    except Exception:
        return "unknown"


def repo_identity() -> tuple[str, str]:
    gh_repo = os.getenv("GITHUB_REPOSITORY", "")
    if "/" in gh_repo:
        owner, name = gh_repo.split("/", 1)
        return owner, name

    try:
        remote = subprocess.check_output(
            ["git", "remote", "get-url", "origin"], cwd=REPO_ROOT, text=True
        ).strip()
        remote = remote.replace(".git", "")
        if remote.endswith("/"):
            remote = remote[:-1]
        owner, name = remote.split("/")[-2:]
        return owner, name
    except Exception:
        return "unknown", REPO_ROOT.name


def build_catalog() -> dict[str, Any]:
    owner, repo_name = repo_identity()
    items: list[dict[str, Any]] = []

    for file_path in sorted(REPO_ROOT.rglob("*")):
        if not file_path.is_file() or should_exclude(file_path):
            continue

        rel = file_path.relative_to(REPO_ROOT)
        ext = file_path.suffix.lower().lstrip(".")

        items.append(
            {
                "path": str(rel).replace("\\", "/"),
                "filename": file_path.name,
                "extension": ext,
                "size_bytes": file_path.stat().st_size,
                "last_modified_iso": iso_from_mtime(file_path),
                "tags": derive_tags(rel),
            }
        )

    return {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "repo_owner": owner,
            "repo_name": repo_name,
            "branch": git_current_branch(),
            "excluded_patterns": EXCLUDED_PATTERNS,
        },
        "files": items,
    }


def main() -> None:
    catalog = build_catalog()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        json.dump(catalog, handle, indent=2, ensure_ascii=False)
    print(f"📚 File catalog written to {OUTPUT_PATH}")
    print(f"📄 Cataloged {len(catalog['files'])} files")


if __name__ == "__main__":
    main()
