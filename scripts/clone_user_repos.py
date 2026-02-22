#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path


def fetch_user_repos(username: str, token: str | None = None) -> list[dict]:
    repos: list[dict] = []
    page = 1
    per_page = 100

    while True:
        query = urllib.parse.urlencode(
            {"per_page": per_page, "page": page, "type": "owner", "sort": "full_name"}
        )
        url = f"https://api.github.com/users/{username}/repos?{query}"
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        req.add_header("User-Agent", "clone-user-repos-script")
        if token:
            req.add_header("Authorization", f"Bearer {token}")

        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if not data:
            break

        repos.extend(data)
        if len(data) < per_page:
            break
        page += 1

    return repos


def run_git_clone(clone_url: str, destination: Path) -> int:
    command = ["git", "clone", clone_url, str(destination)]
    return subprocess.run(command, check=False).returncode


def run_git(
    args: list[str], cwd: Path, capture_output: bool = False
) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        cwd=str(cwd),
        check=False,
        text=True,
        capture_output=capture_output,
    )


def is_git_repo(path: Path) -> bool:
    proc = run_git(["git", "rev-parse", "--is-inside-work-tree"], cwd=path, capture_output=True)
    return proc.returncode == 0 and proc.stdout.strip() == "true"


def update_existing_repo(repo_name: str, dest: Path, dry_run: bool) -> tuple[int, int, int]:
    if not is_git_repo(dest):
        print(f"[fail] {repo_name}: {dest} exists but is not a git repository")
        return 0, 1, 0

    print(f"[update] {repo_name}: {dest}")
    if dry_run:
        return 1, 0, 0

    fetch = run_git(["git", "fetch", "--all", "--prune"], cwd=dest)
    if fetch.returncode != 0:
        print(f"[fail] {repo_name}: git fetch --all --prune failed")
        return 0, 1, 0

    # Determine currently checked-out branch (empty string if detached HEAD).
    current_branch_proc = run_git(
        ["git", "symbolic-ref", "--quiet", "--short", "HEAD"], cwd=dest, capture_output=True
    )
    current_branch = (
        current_branch_proc.stdout.strip() if current_branch_proc.returncode == 0 else ""
    )

    # Iterate over all local branches that have a tracking upstream.
    branches_proc = run_git(
        ["git", "for-each-ref", "--format=%(refname:short)|%(upstream:short)", "refs/heads"],
        cwd=dest,
        capture_output=True,
    )
    if branches_proc.returncode != 0:
        print(f"[warn] {repo_name}: failed to inspect local branches")
        return 1, 0, 1

    warn_count = 0
    failed = False

    for line in branches_proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        branch, upstream = (line.split("|", 1) + [""])[:2]
        branch = branch.strip()
        upstream = upstream.strip()
        if not branch:
            continue

        if not upstream:
            print(f"[warn] {repo_name}: branch '{branch}' has no upstream")
            warn_count += 1
            continue

        counts = run_git(
            ["git", "rev-list", "--left-right", "--count", f"{branch}...{upstream}"],
            cwd=dest,
            capture_output=True,
        )
        if counts.returncode != 0:
            print(f"[warn] {repo_name}: failed to compare '{branch}' with '{upstream}'")
            warn_count += 1
            continue

        parts = counts.stdout.strip().split()
        if len(parts) != 2:
            print(f"[warn] {repo_name}: unexpected ahead/behind output for '{branch}'")
            warn_count += 1
            continue

        ahead, behind = int(parts[0]), int(parts[1])

        if ahead > 0:
            print(f"[warn] {repo_name}: branch '{branch}' has {ahead} unpushed commit(s) to '{upstream}'")
            warn_count += 1

        if behind == 0:
            continue  # already up to date

        if branch == current_branch:
            # Fast-forward the checked-out branch via pull.
            pull = run_git(["git", "pull", "--ff-only"], cwd=dest)
            if pull.returncode != 0:
                print(f"[fail] {repo_name}: git pull --ff-only failed on branch '{branch}'")
                failed = True
            else:
                print(f"[ff] {repo_name}: '{branch}' <- {behind} commit(s) from '{upstream}'")
        else:
            # Fast-forward a non-checked-out branch via local fetch (no checkout needed).
            ff = run_git(
                ["git", "fetch", ".", f"{upstream}:{branch}"],
                cwd=dest,
                capture_output=True,
            )
            if ff.returncode != 0:
                print(
                    f"[warn] {repo_name}: cannot fast-forward '{branch}' to '{upstream}'"
                    + (f": {ff.stderr.strip()}" if ff.stderr.strip() else "")
                )
                warn_count += 1
            else:
                print(f"[ff] {repo_name}: '{branch}' <- {behind} commit(s) from '{upstream}'")

    if failed:
        return 0, 1, warn_count
    return 1, 0, warn_count


def clone_repos(
    username: str,
    target_folder: Path,
    token: str | None = None,
    dry_run: bool = False,
) -> tuple[int, int, int, int, int]:
    repos = fetch_user_repos(username, token=token)
    target_folder.mkdir(parents=True, exist_ok=True)

    cloned = 0
    updated = 0
    skipped = 0
    failed = 0
    warnings = 0

    for repo in repos:
        name = repo["name"]
        clone_url = repo["clone_url"]
        dest = target_folder / name

        if dest.exists():
            upd, fail, warn = update_existing_repo(f"{username}/{name}", dest, dry_run)
            updated += upd
            failed += fail
            warnings += warn
            continue

        print(f"[clone] {username}/{name} -> {dest}")
        if dry_run:
            cloned += 1
            continue

        code = run_git_clone(clone_url, dest)
        if code == 0:
            cloned += 1
        else:
            print(f"[fail] {username}/{name}: git clone exited with code {code}")
            failed += 1

    return cloned, updated, skipped, failed, warnings



def _name_from_url(url: str) -> str:
    """Derive a local folder name from a git URL."""
    # SCP-style:   git@host:path/to/repo.git  -> repo
    # URL-style:   ssh://git@host:port/path/repo.git -> repo
    if "://" not in url:
        path = url.split(":", 1)[-1]
    else:
        path = url.split("://", 1)[-1]
    name = path.rstrip("/").split("/")[-1]
    return name[:-4] if name.endswith(".git") else name


def resolve_manual_entry(entry: dict) -> list[tuple[str, str]]:
    """
    Convert a manual config entry into a list of (clone_url, local_name) pairs.

    Each item in entry["repos"] can be:
    - a string (bare repo name)  — requires entry["base_url"]
    - {"url": "git@host:path/repo.git"}            — name derived from URL
    - {"url": "git@host:path/repo.git", "name": "custom-name"}
    """
    base = entry.get("base_url", "").rstrip("/")
    result: list[tuple[str, str]] = []
    for repo in entry["repos"]:
        if isinstance(repo, str):
            name = repo.strip()
            url = f"{base}/{name}.git" if base else name
        else:
            url = repo["url"].strip()
            name = repo.get("name", "").strip() or _name_from_url(url)
        if name:
            result.append((url, name))
    return result


def clone_manual_repos(
    repos: list[tuple[str, str]],
    target_folder: Path,
    dry_run: bool = False,
) -> tuple[int, int, int, int, int]:
    target_folder.mkdir(parents=True, exist_ok=True)

    cloned = 0
    updated = 0
    skipped = 0
    failed = 0
    warnings = 0

    for clone_url, name in repos:
        dest = target_folder / name
        if dest.exists():
            upd, fail, warn = update_existing_repo(name, dest, dry_run)
            updated += upd
            failed += fail
            warnings += warn
            continue

        print(f"[clone] {clone_url} -> {dest}")
        if dry_run:
            cloned += 1
            continue

        code = run_git_clone(clone_url, dest)
        if code == 0:
            cloned += 1
            continue

        # Retry with .git suffix only if not already present.
        if not clone_url.endswith(".git"):
            clone_url_git = f"{clone_url}.git"
            print(f"[retry] {clone_url_git} -> {dest}")
            code = run_git_clone(clone_url_git, dest)
            if code == 0:
                cloned += 1
                continue

        print(f"[fail] {name}: git clone exited with code {code}")
        failed += 1

    return cloned, updated, skipped, failed, warnings


def load_config(path: Path) -> dict:
    """
    Load and validate the JSON config file.

    Expected format:
    {
      "root": "D:/Projects",          // optional if --root is passed via CLI
      "github": [                     // optional
        {"user": "alice", "folder": "Games"},
        {"user": "bob",   "folder": "Other"}
      ],
      "manual": [                     // optional
        {
          "base_url": "http://host/token/username",
          "folder": "Studying",
          "repos": ["repo1", "repo2"]
        }
      ]
    }
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"Error: cannot read config file {path}: {exc}", file=sys.stderr)
        sys.exit(2)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON in {path}: {exc}", file=sys.stderr)
        sys.exit(2)

    if not isinstance(data, dict):
        print("Error: config must be a JSON object", file=sys.stderr)
        sys.exit(2)

    github_entries = data.get("github", [])
    if not isinstance(github_entries, list):
        print("Error: 'github' must be a list", file=sys.stderr)
        sys.exit(2)
    for i, entry in enumerate(github_entries):
        if not isinstance(entry, dict) or "user" not in entry or "folder" not in entry:
            print(
                f"Error: github[{i}] must have 'user' and 'folder' keys",
                file=sys.stderr,
            )
            sys.exit(2)

    manual_entries = data.get("manual", [])
    if not isinstance(manual_entries, list):
        print("Error: 'manual' must be a list", file=sys.stderr)
        sys.exit(2)
    for i, entry in enumerate(manual_entries):
        if not isinstance(entry, dict) or "folder" not in entry or "repos" not in entry:
            print(
                f"Error: manual[{i}] must have 'folder' and 'repos' keys",
                file=sys.stderr,
            )
            sys.exit(2)
        if not isinstance(entry["repos"], list):
            print(f"Error: manual[{i}].repos must be a list", file=sys.stderr)
            sys.exit(2)
        for j, repo in enumerate(entry["repos"]):
            if isinstance(repo, str):
                if not entry.get("base_url"):
                    print(
                        f"Error: manual[{i}].repos[{j}] is a bare name but 'base_url' is missing",
                        file=sys.stderr,
                    )
                    sys.exit(2)
            elif not isinstance(repo, dict) or "url" not in repo:
                print(
                    f"Error: manual[{i}].repos[{j}] must be a string or object with 'url'",
                    file=sys.stderr,
                )
                sys.exit(2)

    return data


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Clone/update repositories according to a JSON config file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Config file format (JSON):\n"
            "  {\n"
            '    "root": "D:/Projects",\n'
            '    "github": [\n'
            '      {"user": "alice", "folder": "Games"},\n'
            '      {"user": "bob",   "folder": "Other"}\n'
            "    ],\n"
            '    "manual": [\n'
            "      {\n"
            '        "base_url": "http://host/token/username",\n'
            '        "folder": "Studying",\n'
            '        "repos": ["repo1", "repo2"]\n'
            "      }\n"
            "    ]\n"
            "  }"
        ),
    )
    parser.add_argument(
        "config",
        type=Path,
        help="Path to the JSON config file with repo-to-folder mapping.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Override root directory from the config file.",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"),
        help="GitHub token (optional). Falls back to GITHUB_TOKEN/GH_TOKEN env vars.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions without running git clone.",
    )
    args = parser.parse_args()

    config = load_config(args.config)

    if args.root is not None:
        root = args.root.resolve()
    elif "root" in config:
        root = Path(config["root"]).resolve()
    else:
        print(
            "Error: 'root' must be specified in the config file or via --root",
            file=sys.stderr,
        )
        return 2

    print(f"Root: {root}")

    total_cloned = 0
    total_updated = 0
    total_skipped = 0
    total_failed = 0
    total_warnings = 0

    for entry in config.get("github", []):
        user = entry["user"]
        target = root / entry["folder"]
        print(f"\n=== github:{user} -> {target} ===")
        cloned, updated, skipped, failed, warnings = clone_repos(
            username=user,
            target_folder=target,
            token=args.token,
            dry_run=args.dry_run,
        )
        total_cloned += cloned
        total_updated += updated
        total_skipped += skipped
        total_failed += failed
        total_warnings += warnings
        print(
            f"Summary for {user}: cloned={cloned}, updated={updated}, "
            f"skipped={skipped}, failed={failed}, warnings={warnings}"
        )

    for entry in config.get("manual", []):
        target = root / entry["folder"]
        resolved = resolve_manual_entry(entry)
        print(f"\n=== manual -> {target} ===")
        cloned, updated, skipped, failed, warnings = clone_manual_repos(
            repos=resolved,
            target_folder=target,
            dry_run=args.dry_run,
        )
        total_cloned += cloned
        total_updated += updated
        total_skipped += skipped
        total_failed += failed
        total_warnings += warnings
        print(
            f"Summary for manual: cloned={cloned}, updated={updated}, "
            f"skipped={skipped}, failed={failed}, warnings={warnings}"
        )

    print(
        f"\nTOTAL: cloned={total_cloned}, updated={total_updated}, "
        f"skipped={total_skipped}, failed={total_failed}, warnings={total_warnings}"
    )
    return 1 if total_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
