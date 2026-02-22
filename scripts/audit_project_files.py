#!/usr/bin/env python3
"""
audit_project_files.py

Checks top-level projects in Legacy for:
1) default git branch;
2) git history policy:
   - exactly 1 commit;
   - commit subject is "Initial commit";
   - commit author is "heapcore";
   - only local branch is "main";
3) text formatting issues:
   - double trailing newline at EOF;
   - excessive blank lines between non-empty lines;
   - trailing spaces in lines;
   - Python files are skipped (handled by Ruff in --fix mode).
4) README requirements:
   - WARNING notice is present;
   - README has canonical `## License` section.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

SKIP_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    "vendor",
    "target",
    "build",
    "dist",
    ".idea",
    ".vscode",
    ".venv",
    "venv",
}

TEXT_EXTENSIONS = {
    ".py",
    ".go",
    ".rs",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".cs",
    ".php",
    ".rb",
    ".sh",
    ".bash",
    ".zsh",
    ".fish",
    ".ps1",
    ".bat",
    ".cmd",
    ".md",
    ".txt",
    ".rst",
    ".adoc",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".env",
    ".html",
    ".htm",
    ".css",
    ".scss",
    ".sass",
    ".less",
    ".sql",
    ".xml",
    ".csv",
    ".dockerfile",
    ".makefile",
}

TEXT_FILENAMES = {
    "Dockerfile",
    "Makefile",
    "LICENSE",
    ".gitignore",
    ".gitattributes",
    "README",
    "README.md",
    "README.rst",
    "README.txt",
}


@dataclass
class FileIssue:
    path: str
    issue: str
    line: int | None = None


@dataclass
class ProjectReport:
    name: str
    default_branch: str
    git_note: str
    git_policy_issues: list[str] = field(default_factory=list)
    formatting_issues: list[FileIssue] = field(default_factory=list)
    readme_warning_ok: bool = False
    readme_title_ok: bool = False
    readme_title_error: str | None = None
    readme_license_section_ok: bool = False
    readme_license_section_warning: str | None = None
    readme_path: str | None = None


def run_git(project_path: Path, args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        ["git", "-C", str(project_path)] + args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, proc.stdout.strip()


def detect_default_branch(project_path: Path) -> tuple[str, str]:
    if not (project_path / ".git").exists():
        return "-", "no git"

    code, out = run_git(
        project_path, ["symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"]
    )
    if code == 0 and out.startswith("refs/remotes/origin/"):
        return out.replace("refs/remotes/origin/", "", 1), "origin/HEAD"

    code, out = run_git(project_path, ["remote", "show", "origin"])
    if code == 0:
        for line in out.splitlines():
            line = line.strip()
            if line.lower().startswith("head branch:"):
                branch = line.split(":", 1)[1].strip()
                if branch:
                    return branch, "remote show origin"

    code, out = run_git(project_path, ["branch", "--show-current"])
    if code == 0 and out:
        return out, "fallback: current branch"

    return "?", "unknown"


def evaluate_git_policy(project_path: Path) -> list[str]:
    issues: list[str] = []

    if not (project_path / ".git").exists():
        return ["no git repository"]

    code, out = run_git(project_path, ["rev-list", "--count", "HEAD"])
    if code != 0:
        issues.append("cannot read commit count")
    else:
        try:
            commit_count = int(out)
            if commit_count != 1:
                issues.append(f"commit count must be 1, actual: {commit_count}")
        except ValueError:
            issues.append(f"invalid commit count output: {out!r}")

    code, out = run_git(project_path, ["log", "-1", "--pretty=%s"])
    if code != 0:
        issues.append("cannot read latest commit subject")
    else:
        expected_subject = "Initial commit"
        if out != expected_subject:
            issues.append(
                f"latest commit subject must be {expected_subject!r}, actual: {out!r}"
            )

    code, out = run_git(project_path, ["log", "-1", "--pretty=%an"])
    if code != 0:
        issues.append("cannot read latest commit author")
    else:
        expected_author = "heapcore"
        if out != expected_author:
            issues.append(
                f"latest commit author must be {expected_author!r}, actual: {out!r}"
            )

    code, out = run_git(project_path, ["branch", "--format=%(refname:short)"])
    if code != 0:
        issues.append("cannot read local branches")
    else:
        branches = [line.strip() for line in out.splitlines() if line.strip()]
        if not branches:
            issues.append("no local branches found")
        else:
            if "main" not in branches:
                issues.append("local branch 'main' is missing")
            if len(branches) != 1 or branches[0] != "main":
                issues.append(
                    f"only one local branch 'main' is allowed, actual: {branches}"
                )

    code, out = run_git(project_path, ["branch", "-r", "--format=%(refname:short)"])
    if code == 0:
        remote_branches = [line.strip() for line in out.splitlines() if line.strip()]
        if remote_branches:
            # "origin" is the short form of "origin/HEAD" in some git versions.
            allowed = {"origin/main", "origin/HEAD", "origin"}
            extra = [b for b in remote_branches if b not in allowed]
            if "origin/main" not in remote_branches:
                issues.append("remote branch 'origin/main' is missing")
            if extra:
                issues.append(
                    f"only remote branch 'origin/main' is allowed, actual: {remote_branches}"
                )

    return issues


def should_scan_file(path: Path) -> bool:
    name = path.name
    if name in TEXT_FILENAMES:
        return True
    return path.suffix.lower() in TEXT_EXTENSIONS


def normalize_newlines(content: str) -> str:
    return content.replace("\r\n", "\n").replace("\r", "\n")


def normalize_text_style(content: str) -> str:
    """
    Apply requested text normalization:
    - remove trailing spaces/tabs in each line;
    - replace 3+ consecutive newlines with exactly 2;
    - keep at most one trailing newline at EOF.
    """
    text = normalize_newlines(content)
    text = "\n".join(line.rstrip(" \t") for line in text.split("\n"))
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.rstrip("\n")
    if text:
        text += "\n"
    return text


def find_triple_newline_lines(text: str) -> list[int]:
    """Return line numbers where '\\n\\n\\n' starts."""
    lines = []
    start = 0
    while True:
        idx = text.find("\n\n\n", start)
        if idx == -1:
            break
        line_no = text.count("\n", 0, idx) + 1
        lines.append(line_no)
        start = idx + 1
    return lines


def trailing_newline_issue_line(text: str) -> int:
    """
    Return a 1-based line number for extra trailing newline at EOF.
    For content ending in '\\n\\n', this points to the final empty line.
    """
    return len(text.split("\n"))


def find_trailing_space_lines(text: str) -> list[int]:
    """Return line numbers that have trailing spaces or tabs."""
    lines = []
    for i, line in enumerate(text.split("\n"), start=1):
        if line.endswith(" ") or line.endswith("\t"):
            lines.append(i)
    return lines


def find_readme(project_path: Path) -> Path | None:
    candidates = [
        project_path / "README.md",
        project_path / "README.rst",
        project_path / "README.txt",
        project_path / "README",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def has_warning(readme_text: str) -> bool:
    text = normalize_newlines(readme_text)
    return re.search(r"(?m)^> \*\*WARNING:\*\* .+$", text) is not None


def evaluate_readme_title(
    readme_text: str, project_name: str
) -> tuple[bool, str | None]:
    """Check README first line equals '# <project_name>'."""
    lines = normalize_newlines(readme_text).split("\n")
    if not lines:
        return False, "README is empty"
    expected = f"# {project_name}"
    first_line = lines[0].strip()
    if first_line != expected:
        return False, f"first line must be {expected!r}, actual: {first_line!r}"
    return True, None


def evaluate_license_section(readme_text: str) -> tuple[bool, str | None]:
    """
    Check that README contains:
      ## License
    and that the section content is exactly:
      See `LICENSE`.
    """
    lines = normalize_newlines(readme_text).split("\n")
    license_idx = None
    for i, line in enumerate(lines):
        if line.strip().lower() == "## license":
            license_idx = i
            break

    if license_idx is None:
        return False, "README is missing `## License` section"

    collected = []
    for line in lines[license_idx + 1 :]:
        stripped = line.strip()
        if stripped.startswith("## "):
            break
        collected.append(line)

    section_text = "\n".join(collected).strip()
    expected = "See `LICENSE`."
    if section_text != expected:
        return (
            False,
            f"`## License` content differs from expected text. Expected: {expected!r}; actual: {section_text!r}",
        )
    return True, None


def ensure_readme_content(readme_text: str, project_name: str) -> str:
    text = normalize_newlines(readme_text).rstrip("\n")
    heading_re = re.compile(r"(?m)^##\s+(.+?)\s*$")
    matches = list(heading_re.finditer(text))

    if matches:
        preface = text[: matches[0].start()].strip("\n")
        sections: list[dict[str, str]] = []
        for i, match in enumerate(matches):
            title = match.group(1).strip()
            body_start = match.end()
            body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[body_start:body_end].strip("\n")
            sections.append({"title": title, "body": body})
    else:
        preface = text
        sections = []

    warning_line = "> **WARNING:** This repository may be unstable or non-functional. Use at your own risk."
    preface_lines = preface.split("\n") if preface else []
    expected_title = f"# {project_name}"
    if preface_lines:
        preface_lines[0] = expected_title
    else:
        preface_lines = [expected_title]
    preface_body_lines = []
    for line in preface_lines[1:]:
        if line.strip().lower().startswith("> **warning:**"):
            continue
        preface_body_lines.append(line)
    preface_body = "\n".join(preface_body_lines).strip("\n")

    sections = [sec for sec in sections if sec["title"].strip().lower() != "warning"]

    sections = [sec for sec in sections if sec["title"].strip().lower() != "links"]

    sections = [sec for sec in sections if sec["title"].strip().lower() != "license"]
    sections.append({"title": "License", "body": "See `LICENSE`."})

    rendered: list[str] = []
    rendered.append(expected_title)
    rendered.append(warning_line)
    if preface_body:
        rendered.append(preface_body)
    for sec in sections:
        block = f"## {sec['title'].strip()}"
        if sec["body"].strip():
            block += f"\n\n{sec['body'].strip()}"
        rendered.append(block)

    return normalize_text_style("\n\n".join(rendered))


def apply_fixes_to_project(project_path: Path) -> int:
    changed_files = 0

    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for file_name in files:
            full_path = Path(root) / file_name
            if not should_scan_file(full_path):
                continue

            try:
                original = full_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            if full_path.suffix.lower() == ".py":
                continue

            fixed = normalize_text_style(original)
            if fixed != original:
                full_path.write_text(fixed, encoding="utf-8", newline="\n")
                changed_files += 1

    readme_path = find_readme(project_path)
    if readme_path:
        original = readme_path.read_text(encoding="utf-8", errors="ignore")
        fixed = ensure_readme_content(original, project_path.name)
        if fixed != original:
            readme_path.write_text(fixed, encoding="utf-8", newline="\n")
            changed_files += 1

    return changed_files


def scan_project(project_path: Path) -> ProjectReport:
    default_branch, git_note = detect_default_branch(project_path)
    report = ProjectReport(
        name=project_path.name, default_branch=default_branch, git_note=git_note
    )
    report.git_policy_issues = evaluate_git_policy(project_path)

    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for file_name in files:
            full_path = Path(root) / file_name
            rel_path = full_path.relative_to(project_path)

            if not should_scan_file(full_path):
                continue

            try:
                text = full_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            text = normalize_newlines(text)

            if full_path.suffix.lower() == ".py":
                continue

            if text.endswith("\n\n"):
                report.formatting_issues.append(
                    FileIssue(
                        str(rel_path),
                        "double trailing newline at EOF",
                        line=trailing_newline_issue_line(text),
                    )
                )

            triple_lines = find_triple_newline_lines(text)
            if triple_lines:
                for line_no in triple_lines:
                    report.formatting_issues.append(
                        FileIssue(
                            str(rel_path),
                            "triple newline between lines",
                            line=line_no,
                        )
                    )

            trailing_space_lines = find_trailing_space_lines(text)
            if trailing_space_lines:
                for line_no in trailing_space_lines:
                    report.formatting_issues.append(
                        FileIssue(
                            str(rel_path),
                            "trailing spaces",
                            line=line_no,
                        )
                    )

    readme_path = find_readme(project_path)
    if readme_path:
        report.readme_path = str(readme_path.relative_to(project_path))
        text = normalize_newlines(
            readme_path.read_text(encoding="utf-8", errors="ignore")
        )
        title_ok, title_error = evaluate_readme_title(text, project_path.name)
        report.readme_title_ok = title_ok
        report.readme_title_error = title_error
        report.readme_warning_ok = has_warning(text)
        section_ok, section_warning = evaluate_license_section(text)
        report.readme_license_section_ok = section_ok
        report.readme_license_section_warning = section_warning
    else:
        report.readme_title_ok = False
        report.readme_title_error = "README file is missing"
        report.readme_warning_ok = False
        report.readme_license_section_ok = False
        report.readme_license_section_warning = "README file is missing"

    return report


def collect_projects(base_dir: Path, only: list[str]) -> list[Path]:
    if only:
        projects = []
        for item in only:
            p = Path(item)
            if not p.is_absolute():
                p = base_dir / item
            if not p.is_dir():
                print(f"ERROR: project folder not found: {item}")
                sys.exit(1)
            projects.append(p)
        return sorted(projects, key=lambda p: p.name.lower())

    return sorted(
        [p for p in base_dir.iterdir() if p.is_dir() and not p.name.startswith(".")],
        key=lambda p: p.name.lower(),
    )


def run_ruff_fix(project_path: Path) -> None:
    """
    Run Ruff fix/format for a project. Best-effort: errors are printed but not fatal.
    """
    try:
        check_proc = subprocess.run(
            ["ruff", "check", "--fix", str(project_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if check_proc.returncode != 0 and check_proc.stdout.strip():
            print(
                f"[ruff check --fix] {project_path.name}:\n{check_proc.stdout.strip()}"
            )
        if check_proc.returncode != 0 and check_proc.stderr.strip():
            print(
                f"[ruff check --fix][stderr] {project_path.name}:\n{check_proc.stderr.strip()}"
            )

        format_proc = subprocess.run(
            ["ruff", "format", str(project_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if format_proc.returncode != 0 and format_proc.stdout.strip():
            print(f"[ruff format] {project_path.name}:\n{format_proc.stdout.strip()}")
        if format_proc.returncode != 0 and format_proc.stderr.strip():
            print(
                f"[ruff format][stderr] {project_path.name}:\n{format_proc.stderr.strip()}"
            )
    except FileNotFoundError:
        print(
            "WARNING: Ruff is not installed or not found in PATH. Python auto-fix was skipped."
        )


def print_report(reports: list[ProjectReport]) -> int:
    print(f"Scanned projects: {len(reports)}")
    print("=" * 90)
    exit_code = 0

    for r in reports:
        print(f"\n[{r.name}]")
        print(f"  default branch: {r.default_branch} ({r.git_note})")
        if not r.git_policy_issues:
            print("  git policy: OK")
        else:
            print("  git policy: FAIL")
            for issue in r.git_policy_issues:
                print(f"    - {issue}")
            exit_code = 1

        if r.readme_path is None:
            print("  README: missing")
            exit_code = 1
        else:
            print(f"  README: {r.readme_path}")
            print(f"  README title: {'OK' if r.readme_title_ok else 'FAIL'}")
            if not r.readme_title_ok:
                print(f"    error: {r.readme_title_error}")
            print(f"  README warning: {'OK' if r.readme_warning_ok else 'FAIL'}")
            if r.readme_license_section_ok:
                print("  README license section: OK")
            else:
                print(
                    f"  WARNING: README license section: {r.readme_license_section_warning}"
                )
            if not (r.readme_title_ok and r.readme_warning_ok):
                exit_code = 1

        if r.formatting_issues:
            print(f"  formatting issues: {len(r.formatting_issues)}")
            for issue in r.formatting_issues:
                if issue.line is not None:
                    print(f"    - {issue.path}: line {issue.line}: {issue.issue}")
                else:
                    print(f"    - {issue.path}: {issue.issue}")
            exit_code = 1
        else:
            print("  formatting issues: none")

    print("\n" + "=" * 90)
    if exit_code == 0:
        print("All checks passed.")
    else:
        print("Checks failed. See details above.")

    # --- Summary of repos with issues ---
    problem_repos: list[tuple[str, list[str]]] = []
    for r in reports:
        problems: list[str] = []
        if r.git_policy_issues:
            problems.append(f"git policy ({len(r.git_policy_issues)} issue(s))")
        readme_problems: list[str] = []
        if r.readme_path is None:
            readme_problems.append("missing")
        else:
            if not r.readme_title_ok:
                readme_problems.append("title")
            if not r.readme_warning_ok:
                readme_problems.append("warning")
            if not r.readme_license_section_ok:
                readme_problems.append("license section")
        if readme_problems:
            problems.append(f"README ({', '.join(readme_problems)})")
        if r.formatting_issues:
            problems.append(f"formatting ({len(r.formatting_issues)} issue(s))")
        if problems:
            problem_repos.append((r.name, problems))

    if problem_repos:
        print(f"\nRepos with issues ({len(problem_repos)}/{len(reports)}):")
        for name, problems in problem_repos:
            print(f"  {name}: {'; '.join(problems)}")

    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check project branches, blank-line hygiene, and README requirements."
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-fix README/title/warning/license and text formatting issues.",
    )
    parser.add_argument(
        "--dir",
        "-d",
        default=None,
        metavar="PATH",
        help=(
            "Base directory containing project repos to audit. "
            "Defaults to the script's grandparent directory."
        ),
    )
    parser.add_argument(
        "projects",
        nargs="*",
        help="Optional list of project folders (names or paths). If omitted, scans all top-level folders in --dir.",
    )
    args = parser.parse_args()

    if args.dir is not None:
        base_dir = Path(args.dir).resolve()
        if not base_dir.is_dir():
            print(f"ERROR: directory not found: {args.dir}")
            sys.exit(1)
    else:
        base_dir = Path(__file__).resolve().parents[2]  # Legacy root fallback

    projects = collect_projects(base_dir, args.projects)
    if args.fix:
        total_changed = 0
        for project in projects:
            run_ruff_fix(project)
            total_changed += apply_fixes_to_project(project)
        print(f"Applied fixes. Changed files: {total_changed}")

    reports = [scan_project(p) for p in projects]
    return print_report(reports)


if __name__ == "__main__":
    sys.exit(main())
