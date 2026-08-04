"""Validate a release and extract its notes from the changelog.

Run with the version being released, for example 1.4.5 or 1.4.5b1. Refuses
unless the version files, the changelog and the requested version all agree,
and writes the changelog section out for the release body.

The point is that nothing gets released that the changelog does not describe,
and no build ever again reports a version it is not.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys

BASE = pathlib.Path("custom_components/greg")


def fail(problems: list[str]) -> None:
    print("Release blocked:\n")
    for p in problems:
        print(f"  - {p}")
    print()
    sys.exit(1)


def base_version(version: str) -> str:
    """Strip a pre-release suffix, so 1.5.0b1 becomes 1.5.0.

    A beta is a candidate for the release it is named after, and is described by
    that release's changelog section. Giving every beta its own section would be
    noise, and would mean writing the notes twice.
    """
    return re.sub(r"(a|b|rc)\d+$", "", version)


def tag_exists(tag: str) -> bool:
    out = subprocess.run(
        ["git", "tag", "--list", tag], capture_output=True, text=True, check=True
    )
    return bool(out.stdout.strip())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("version", help="version being released, e.g. 1.4.5 or 1.4.5b1")
    ap.add_argument("--notes-out", default="release-notes.md")
    ap.add_argument("--allow-existing-tag", action="store_true")
    args = ap.parse_args()

    want = args.version.lstrip("v")
    tag = f"v{want}"
    problems: list[str] = []

    manifest = json.loads((BASE / "manifest.json").read_text())["version"]
    if manifest != want:
        problems.append(f"manifest.json says {manifest}, you asked for {want}")

    const = (BASE / "const.py").read_text()
    version_m = re.search(r'^VERSION = "([^"]+)"', const, re.M)
    display_m = re.search(r'^VERSION_DISPLAY = "([^"]+)"', const, re.M)

    if not version_m or not display_m:
        problems.append("could not find VERSION / VERSION_DISPLAY in const.py")
    else:
        if version_m.group(1) != want:
            problems.append(
                f"const.py VERSION is {version_m.group(1)}, you asked for {want}"
            )
        if display_m.group(1) != f"v{want}":
            problems.append(
                f"const.py VERSION_DISPLAY is {display_m.group(1)}, expected v{want}"
            )

    notes_version = base_version(want)
    changelog = pathlib.Path("CHANGELOG.md").read_text()
    section = re.search(
        rf"^## \[{re.escape(notes_version)}\][^\n]*\n(.*?)(?=^## \[|\Z)",
        changelog,
        re.M | re.S,
    )
    if not section:
        problems.append(
            f"CHANGELOG.md has no '## [{notes_version}]' section. "
            "Write the changelog before releasing."
        )
    elif not section.group(1).strip():
        problems.append(f"the '## [{notes_version}]' changelog section is empty")

    if not args.allow_existing_tag and tag_exists(tag):
        problems.append(f"tag {tag} already exists")

    if problems:
        fail(problems)

    notes = section.group(1).strip()
    if notes_version != want:
        notes = (
            f"Test build of {notes_version}. Not for general use.\n\n"
            "What it will contain when it ships:\n\n" + notes
        )
    pathlib.Path(args.notes_out).write_text(notes + "\n", encoding="utf-8")

    print(f"Version agrees everywhere: {want}")
    if notes_version != want:
        print(f"Pre-release, notes taken from the [{notes_version}] section")
    print(f"Tag to create: {tag}")
    print(f"Notes written to {args.notes_out} ({len(notes.splitlines())} lines)")


if __name__ == "__main__":
    main()
