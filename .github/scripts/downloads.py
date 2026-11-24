#!/usr/bin/env python3
"""How many times Greg has actually been downloaded.

HACS shows one number and it is not this one. It reads the download count of a
single asset on a single release, the one it would install right now, so it
resets to near zero every time Greg is released and never adds up. That is a
release-traffic gauge, not a total.

This walks every release and sums every asset, which is the all-time figure.
The README badge shows the same number; this one also breaks it down per
release, which is useful for seeing whether a version was adopted or ignored.

Counts downloads of the release zip, so it counts updates by people who already
had Greg, and anything else that fetches the file. It starts from the first
release that carried an asset: nothing before that was ever counted by GitHub
and nothing can backfill it.

    python3 .github/scripts/downloads.py

Needs no token for a public repository, but will use GITHUB_TOKEN or GH_TOKEN
if one is in the environment, which raises the rate limit from 60 an hour to
5000.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

REPO = "WHISTLER-Arc/Greg"
API = f"https://api.github.com/repos/{REPO}/releases"


def fetch(url: str) -> list[dict]:
    request = urllib.request.Request(
        url, headers={"Accept": "application/vnd.github+json"}
    )
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def main() -> int:
    releases: list[dict] = []
    page = 1
    while True:
        try:
            batch = fetch(f"{API}?per_page=100&page={page}")
        except urllib.error.HTTPError as error:
            print(f"GitHub said {error.code}: {error.reason}", file=sys.stderr)
            if error.code == 403:
                print("Rate limited. Set GITHUB_TOKEN and try again.", file=sys.stderr)
            return 1
        except urllib.error.URLError as error:
            print(f"Could not reach GitHub: {error.reason}", file=sys.stderr)
            return 1
        if not batch:
            break
        releases.extend(batch)
        page += 1

    if not releases:
        print("No releases found, which would be surprising.")
        return 1

    total = 0
    rows: list[tuple[str, int, str]] = []
    for release in releases:
        count = sum(asset.get("download_count", 0) for asset in release.get("assets", []))
        total += count
        kind = "pre" if release.get("prerelease") else ""
        rows.append((release["tag_name"], count, kind))

    width = max(len(tag) for tag, _, _ in rows)
    counted = sum(1 for _, count, _ in rows if count)

    for tag, count, kind in rows:
        marker = f"  {kind}" if kind else ""
        shown = f"{count:>7,}" if count else "      -"
        print(f"  {tag:<{width}}  {shown}{marker}")

    print()
    print(f"  {'total':<{width}}  {total:>7,}")
    print()

    if not counted:
        print("Every release reads zero, which means none of them carry an asset.")
        print("GitHub does not count downloads of the source zipball it generates")
        print("itself, so there is nothing to count until a release ships greg.zip.")
    elif counted < len(rows):
        print(f"{counted} of {len(rows)} releases carry an asset. The rest predate it")
        print("and were never counted, so the total starts from the first one that did.")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        # Piping into head closes stdout early, and Python's own flush at exit
        # then raises again on the way out and prints a traceback over the
        # output you asked for. Point stdout at nothing so that flush is quiet.
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(130)
