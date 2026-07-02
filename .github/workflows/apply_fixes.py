#!/usr/bin/env python3
"""Apply code changes from analysis_output.json to the repository.
Uses search-and-replace to modify source files in-place."""

import json
import sys
from pathlib import Path


def apply_changes(analysis_file: Path, repo_dir: Path) -> list[str]:
    """Apply all code changes from the analysis file. Returns list of modified file paths."""
    if not analysis_file.exists():
        print(f"File not found: {analysis_file}")
        return []

    with open(analysis_file, encoding="utf-8") as f:
        analysis = json.load(f)

    changes = analysis.get("code_changes", [])
    if not changes:
        print("No code changes to apply.")
        return []

    modified = []
    for change in changes:
        file_path = Path(change.get("file", ""))
        search = change.get("search", "")
        replace = change.get("replace", "")
        description = change.get("description", "no description")

        if not file_path or not search:
            print(f"  Skipping change for {file_path or 'unknown file'} — missing file or search string")
            continue

        target = repo_dir / file_path
        if not target.exists():
            print(f"  SKIP: {file_path} does not exist")
            continue

        try:
            content = target.read_text(encoding="utf-8")
        except Exception as e:
            print(f"  SKIP: Cannot read {file_path}: {e}")
            continue

        if search not in content:
            print(f"  SKIP: {file_path} — search string not found in file. The AI may have fabricated the snippet.")
            print(f"  Search preview: {search[:120]}...")
            continue

        count = content.count(search)
        if count > 1:
            print(f"  WARN: {file_path} — search string found {count} times (ambiguous). Skipping to be safe.")
            continue

        new_content = content.replace(search, replace)
        try:
            target.write_text(new_content, encoding="utf-8")
            print(f"  APPLIED: {file_path} — {description}")
            if str(file_path) not in modified:
                modified.append(str(file_path))
        except Exception as e:
            print(f"  ERROR: Failed to write {file_path}: {e}")

    print(f"\nApplied changes to {len(modified)} file(s): {modified}")
    return modified


def main():
    if len(sys.argv) < 2:
        print("Usage: apply_fixes.py <analysis_file> [repo_dir]")
        sys.exit(1)

    analysis_file = Path(sys.argv[1])
    repo_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(".")

    modified = apply_changes(analysis_file, repo_dir)

    if modified:
        with open("modified_files.txt", "w") as f:
            f.write("\n".join(modified))
        print("Wrote modified_files.txt")
    else:
        with open("modified_files.txt", "w") as f:
            f.write("")
        print("No files were modified.")


if __name__ == "__main__":
    main()
