# scripts/build_catalog.py
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional, Dict, Any


EXCLUDE_DIRS_DEFAULT = [
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
]
EXCLUDE_GLOBS_DEFAULT = [
    "**/.DS_Store",
    "**/Thumbs.db",
    "**/~$*",
    "**/*.tmp",
    "**/*.lnk",
    "**/*.url",
    "**/desktop.ini",
    "**/.env",
    "**/.env.*",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run_git(args: List[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )


def is_git_repo(repo_root: Path) -> bool:
    p = run_git(["rev-parse", "--is-inside-work-tree"], cwd=repo_root)
    return p.returncode == 0 and p.stdout.strip() == "true"


def git_default_branch(repo_root: Path) -> str:
    # Try to detect default branch; fall back to 'main'
    p = run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root)
    b = p.stdout.strip() or "main"
    return b


def git_repo_identity(repo_root: Path) -> tuple[str, str]:
    env_repo = os.getenv("GITHUB_REPOSITORY")
    if env_repo and "/" in env_repo:
        owner, name = env_repo.split("/", 1)
        return owner, name

    p = run_git(["remote", "get-url", "origin"], cwd=repo_root)
    if p.returncode != 0:
        return "unknown", repo_root.name

    remote = p.stdout.strip().replace(".git", "")
    if "/" not in remote:
        return "unknown", repo_root.name
    owner, name = remote.rstrip("/").split("/")[-2:]
    return owner, name


def git_last_commit_date_iso(repo_root: Path, rel_path: str) -> Optional[str]:
    # ISO-8601 committer date
    p = run_git(["log", "-1", "--format=%cI", "--", rel_path], cwd=repo_root)
    if p.returncode != 0:
        return None
    s = p.stdout.strip()
    return s or None


def git_last_commit_sha(repo_root: Path, rel_path: str) -> Optional[str]:
    p = run_git(["log", "-1", "--format=%H", "--", rel_path], cwd=repo_root)
    if p.returncode != 0:
        return None
    s = p.stdout.strip()
    return s or None


def match_any_glob(path_posix: str, globs: Iterable[str]) -> bool:
    # fnmatch works on POSIX-like strings if we normalize to '/'
    for g in globs:
        if fnmatch.fnmatch(path_posix, g):
            return True
    return False


def derive_tags(rel_path_posix: str) -> List[str]:
    """
    Tags based primarily on folder names (path segments),
    plus a simple extension tag.
    """
    parts = rel_path_posix.split("/")
    dirs = parts[:-1]
    filename = parts[-1]
    ext = filename.split(".")[-1].lower() if "." in filename else ""

    tags: List[str] = []

    # Folder-based tags (cap to avoid tag explosion)
    for d in dirs[:4]:
        if d:
            tags.append(d)

    # Common “category” tags to help UI groupings
    if rel_path_posix.startswith("sor/"):
        tags.append("category:sor")
    elif rel_path_posix.startswith("public/"):
        tags.append("category:public")
    elif rel_path_posix.startswith("scripts/"):
        tags.append("category:scripts")
    elif rel_path_posix.startswith("docs/"):
        tags.append("category:docs")
    elif rel_path_posix.startswith("governance_docs/"):
        tags.append("category:governance_docs")
    elif rel_path_posix.startswith("project_files/"):
        tags.append("category:project_files")

    if ext:
        tags.append(f"ext:{ext}")

    # De-dupe while preserving order
    seen = set()
    out = []
    for t in tags:
        if t not in seen:
            out.append(t)
            seen.add(t)
    return out


def walk_repo_files(repo_root: Path, exclude_dirs: List[str], exclude_globs: List[str]) -> List[Path]:
    files: List[Path] = []
    for root, dirnames, filenames in os.walk(repo_root):
        root_path = Path(root)

        # prune excluded directories in-place for os.walk
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]

        for fn in filenames:
            full_path = root_path / fn
            rel = full_path.relative_to(repo_root)
            rel_posix = rel.as_posix()

            if match_any_glob(rel_posix, exclude_globs):
                continue

            files.append(full_path)

    return sorted(files)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".", help="Repo root path")
    ap.add_argument("--out", default="public/file_catalog.json", help="Output JSON path (relative to repo root)")
    ap.add_argument("--exclude-dir", action="append", default=[], help="Additional directory names to exclude")
    ap.add_argument("--exclude-glob", action="append", default=[], help="Additional glob patterns to exclude (POSIX paths)")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    out_path = (repo_root / args.out).resolve()

    exclude_dirs = EXCLUDE_DIRS_DEFAULT + args.exclude_dir
    exclude_globs = EXCLUDE_GLOBS_DEFAULT + args.exclude_glob

    git_ok = is_git_repo(repo_root)
    branch = git_default_branch(repo_root) if git_ok else "unknown"

    repo_owner, repo_name = git_repo_identity(repo_root)

    files = walk_repo_files(repo_root, exclude_dirs, exclude_globs)

    entries: List[Dict[str, Any]] = []
    for fp in files:
        rel = fp.relative_to(repo_root)
        rel_posix = rel.as_posix()
        try:
            stat_result = fp.stat()
        except FileNotFoundError:
            # File disappeared during scan (e.g., cloud sync race); skip deterministically.
            continue

        size = stat_result.st_size
        ext = fp.suffix.lower().lstrip(".")
        ftype = ext if ext else "none"

        last_commit_date = git_last_commit_date_iso(repo_root, rel_posix) if git_ok else None
        last_commit_sha = git_last_commit_sha(repo_root, rel_posix) if git_ok else None

        # Fallback to filesystem mtime if not tracked / not available
        if not last_commit_date:
            mtime = datetime.fromtimestamp(stat_result.st_mtime, tz=timezone.utc)
            last_commit_date = mtime.isoformat().replace("+00:00", "Z")

        entry = {
            "path": rel_posix,
            "filename": fp.name,
            "extension": ext,
            "type": ftype,
            "size_bytes": size,
            "last_modified_iso": last_commit_date,
            "last_commit_sha": last_commit_sha,
            "tags": derive_tags(rel_posix),
        }
        entries.append(entry)

    payload = {
        "meta": {
            "generated_at": utc_now_iso(),
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "repo_root_name": repo_name,
            "branch": branch,
            "git_repo": git_ok,
            "excluded_dirs": exclude_dirs,
            "excluded_globs": exclude_globs,
        },
        "files": entries,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out_path} ({len(entries)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())