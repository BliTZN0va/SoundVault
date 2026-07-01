#!/usr/bin/env python3
"""
SoundVault release script — bumps version, builds .exe, creates GitHub release.

Usage:
    python tools/release.py patch        # 1.0.0 -> 1.0.1
    python tools/release.py minor        # 1.0.1 -> 1.1.0
    python tools/release.py major        # 1.1.0 -> 2.0.0
    python tools/release.py              # print current version
    python tools/release.py patch --dry-run
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = PROJECT_ROOT / "VERSION"
CONFIG_FILE = PROJECT_ROOT / "config.json"


def read_version():
    return VERSION_FILE.read_text().strip()


def write_version(version):
    VERSION_FILE.write_text(version + "\n")
    print(f"  VERSION -> {version}")


def bump_version(current, part):
    major, minor, patch = map(int, current.split("."))
    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "patch":
        patch += 1
    else:
        raise ValueError(f"Unknown bump part: {part}")
    return f"{major}.{minor}.{patch}"


def update_config_version(new_version):
    if not CONFIG_FILE.exists():
        print("  config.json not found, skipping")
        return
    with open(CONFIG_FILE) as f:
        config = json.load(f)
    config["version"] = new_version
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    print(f"  config.json version -> {new_version}")


def git_tag(version):
    result = subprocess.run(
        ["git", "tag", "-a", f"v{version}", "-m", f"Release v{version}"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("  Failed to create git tag:", result.stderr, file=sys.stderr)
        return False
    print(f"  Git tag v{version} created")
    return True


def git_push_tag(version):
    result = subprocess.run(
        ["git", "push", "origin", f"v{version}"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("  Failed to push tag:", result.stderr, file=sys.stderr)
        return False
    print(f"  Tag v{version} pushed to origin")
    return True


def build_exe():
    spec_file = PROJECT_ROOT / "SoundVault.spec"
    if not spec_file.exists():
        print("  SoundVault.spec not found, skipping PyInstaller build", file=sys.stderr)
        return False

    print("  Building with PyInstaller...")
    result = subprocess.run(
        ["pyinstaller", str(spec_file)],
        capture_output=True, text=True, cwd=PROJECT_ROOT
    )
    if result.returncode != 0:
        print("  PyInstaller build failed:", result.stderr, file=sys.stderr)
        return False

    exe_path = PROJECT_ROOT / "dist" / "SoundVault.exe"
    if exe_path.exists():
        print(f"  Built: {exe_path}")
        return True

    print("  dist/SoundVault.exe not found after build", file=sys.stderr)
    return False


def create_gh_release(version, dry_run=False):
    exe_path = PROJECT_ROOT / "dist" / "SoundVault.exe"
    if not exe_path.exists():
        print("  dist/SoundVault.exe not found, skipping release", file=sys.stderr)
        return False

    cmd = [
        "gh", "release", "create",
        f"v{version}",
        str(exe_path),
        "--title", f"SoundVault v{version}",
        "--notes", f"Release v{version}  \nSee the commit history for details.",
    ]

    if dry_run:
        print(f"  [DRY-RUN] Would run: {' '.join(cmd)}")
        return True

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("  Failed to create GitHub release:", result.stderr, file=sys.stderr)
        return False

    print(f"  GitHub release v{version} created")
    return True


def main():
    dry_run = "--dry-run" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--dry-run"]

    current = read_version()
    print(f"Current version: {current}")

    if not args:
        return

    part = args[0]
    if part not in ("major", "minor", "patch"):
        print(f"Usage: {sys.argv[0]} [major|minor|patch] [--dry-run]", file=sys.stderr)
        sys.exit(1)

    new_version = bump_version(current, part)
    print(f"New version: {new_version}")

    if dry_run:
        print("\n[DRY-RUN] Steps that would be executed:")
        print(f"  1. Write {new_version} to VERSION")
        print(f"  2. Update config.json version")
        print(f"  3. Build with PyInstaller")
        print(f"  4. Create git tag v{new_version}")
        print(f"  5. Push tag to origin")
        print(f"  6. Create GitHub release v{new_version}")
        return

    # 1. Update VERSION file
    write_version(new_version)

    # 2. Update config.json
    update_config_version(new_version)

    # 3. Build
    if not build_exe():
        print("Build failed. Aborting.", file=sys.stderr)
        sys.exit(1)

    # 4. Git tag
    if not git_tag(new_version):
        sys.exit(1)

    # 5. Push tag
    if not git_push_tag(new_version):
        print("Tag push failed. Tag exists locally.", file=sys.stderr)

    # 6. GitHub release
    create_gh_release(new_version)

    print(f"\nDone! Released v{new_version}")


if __name__ == "__main__":
    main()
