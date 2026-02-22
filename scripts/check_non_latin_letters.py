#!/usr/bin/env python3
"""
check_non_latin_letters.py
Scans projects for non-Latin characters in text files.
Reports files containing Cyrillic, Chinese, Arabic, Japanese, Korean, etc.
"""

import os
import sys
import io
import argparse

# Force UTF-8 output on Windows consoles
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Default base dir: two levels up from this script (Legacy root).
_DEFAULT_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# File extensions to scan (text-based files)
TEXT_EXTENSIONS = {
    ".py",
    ".go",
    ".rs",
    ".js",
    ".ts",
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
    ".dockerignore",
    ".makefile",
    ".cmake",
    "Makefile",
    "Dockerfile",
    ".gitignore",
    ".gitattributes",
    "LICENSE",
}

# Directories to skip entirely
SKIP_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    "vendor",
    "target",
    ".cargo",
    "build",
    "dist",
    ".idea",
    ".vscode",
    ".gradle",
}

# Unicode block ranges that are NOT allowed (non-Latin scripts)
NON_LATIN_RANGES = [
    (0x0400, 0x04FF, "Cyrillic"),
    (0x0500, 0x052F, "Cyrillic Supplement"),
    (0x4E00, 0x9FFF, "CJK Unified Ideographs"),
    (0x3040, 0x309F, "Hiragana"),
    (0x30A0, 0x30FF, "Katakana"),
    (0xAC00, 0xD7AF, "Hangul Syllables"),
    (0x0600, 0x06FF, "Arabic"),
    (0x0590, 0x05FF, "Hebrew"),
    (0x0900, 0x097F, "Devanagari"),
    (0x0E00, 0x0E7F, "Thai"),
    (0x1F600, 0x1F64F, "Emoticons"),
    (0x1F300, 0x1F5FF, "Misc Symbols"),
]


def detect_non_latin(text):
    """Returns list of non-Latin hits grouped by line."""
    results = []
    for line_no, line in enumerate(text.splitlines(), 1):
        symbols = []
        scripts = set()
        for char in line:
            cp = ord(char)
            for start, end, name in NON_LATIN_RANGES:
                if start <= cp <= end:
                    symbols.append(char)
                    scripts.add(name)
                    break
        if symbols:
            unique_symbols = "".join(dict.fromkeys(symbols))
            results.append((line_no, sorted(scripts), unique_symbols, line.strip()))
    return results


def should_scan(filename):
    """Check if a file should be scanned based on extension."""
    name = os.path.basename(filename)
    _, ext = os.path.splitext(name)
    return ext.lower() in TEXT_EXTENSIONS or name in TEXT_EXTENSIONS


def scan_project(project_path, base_dir):
    """Scan a single project directory. Returns dict of file -> issues."""
    issues = {}
    for root, dirs, files in os.walk(project_path):
        # Skip unwanted dirs in-place
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for fname in files:
            if not should_scan(fname):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                hits = detect_non_latin(content)
                if hits:
                    rel = os.path.relpath(fpath, base_dir)
                    issues[rel] = hits
            except (OSError, PermissionError):
                pass
    return issues


def main():
    parser = argparse.ArgumentParser(
        description="Scan projects for non-Latin characters in text files."
    )
    parser.add_argument(
        "--dir",
        "-d",
        default=None,
        metavar="PATH",
        help=(
            "Base directory containing project folders to scan. "
            "Defaults to the script's grandparent directory."
        ),
    )
    parser.add_argument(
        "folders",
        nargs="*",
        help="Folder names/paths to scan. If omitted, all top-level project folders are scanned.",
    )
    args = parser.parse_args()

    if args.dir is not None:
        base_dir = os.path.abspath(args.dir)
        if not os.path.isdir(base_dir):
            print(f"ERROR: Directory not found: {args.dir}")
            sys.exit(1)
    else:
        base_dir = _DEFAULT_BASE_DIR

    print(f"Scanning base: {base_dir}\n")
    print("=" * 70)

    total_files_with_issues = 0
    projects_with_issues = []

    entries = []
    if args.folders:
        for folder in args.folders:
            candidate = (
                folder if os.path.isabs(folder) else os.path.join(base_dir, folder)
            )
            if not os.path.isdir(candidate):
                print(f"ERROR: Folder not found or not a directory: {folder}")
                sys.exit(1)
            entries.append((os.path.basename(os.path.normpath(candidate)), candidate))
        entries.sort(key=lambda item: item[0].lower())
    else:
        # Get top-level project dirs
        try:
            scandir_entries = [
                e
                for e in os.scandir(base_dir)
                if e.is_dir() and e.name not in SKIP_DIRS and not e.name.startswith(".")
            ]
        except OSError as e:
            print(f"ERROR: Cannot scan base dir: {e}")
            sys.exit(1)

        scandir_entries.sort(key=lambda e: e.name.lower())
        entries = [(e.name, e.path) for e in scandir_entries]

    for project_name, project_path in entries:
        proj_issues = scan_project(project_path, base_dir)
        if proj_issues:
            projects_with_issues.append(project_name)
            print(f"\n[FAIL] {project_name}")
            for fpath, hits in sorted(proj_issues.items()):
                print(f"  {fpath}")
                for line_no, scripts, symbols, line_text in hits:
                    preview = line_text[:120] + ("..." if len(line_text) > 120 else "")
                    print(
                        f"    line {line_no:4d}: [{', '.join(scripts)}] symbols: '{symbols}'  |  {preview}"
                    )
                total_files_with_issues += len(proj_issues)
        else:
            print(f"[OK]   {project_name}")

    print("\n" + "=" * 70)
    if projects_with_issues:
        print(f"\nSUMMARY: {len(projects_with_issues)} project(s) with non-Latin text:")
        for p in projects_with_issues:
            print(f"  - {p}")
        print(f"\nTotal files with issues: {total_files_with_issues}")
        sys.exit(1)
    else:
        print("\nAll projects contain only Latin text. OK.")
        sys.exit(0)


if __name__ == "__main__":
    main()
