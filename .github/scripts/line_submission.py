"""Turn a lines submission into a checklist somebody can tick in ninety seconds.

Reads the issue body, pulls out the language, the credit and the lines grouped
by pool, and prints a comment with one checkbox per line. Reviewing is then a
matter of ticking the keepers and leaving the rest, and a later pass reads the
ticks back off the comment.

Deliberately does no judging of its own. It reformats and it counts duplicates
against the shipped pools, and that is all. Whether a line is funny is not a
thing a script gets an opinion about.
"""
from __future__ import annotations

import argparse
import ast
import pathlib
import re
import sys

POOLS = ("soft", "medium", "chaos", "existential", "silence")
LINES_DIR = pathlib.Path("custom_components/greg/lines")


def shipped(language: str) -> set[str]:
    """Every line already in the pools for one language, to spot repeats."""
    path = LINES_DIR / f"{language}.py"
    if not path.exists():
        return set()
    module = ast.parse(path.read_text(encoding="utf-8"))
    out: set[str] = set()
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        name = getattr(node.targets[0], "id", "")
        if name.startswith("LINES_") and isinstance(node.value, ast.List):
            out.update(
                e.value for e in node.value.elts if isinstance(e, ast.Constant)
            )
    return out


def parse(body: str):
    """Language, credit, and {pool: [line]} out of the issue body."""
    language = "en"
    match = re.search(r"^\s*(?:Language|language)\s*:?\s*`?([a-z]{2})`?\s*$", body, re.M)
    if match:
        language = match.group(1)

    credit = ""
    match = re.search(r"credited?\s*:?\s*\n+\s*(.+)", body, re.I)
    if match:
        credit = match.group(1).strip()
    if credit.startswith("<!--"):
        credit = ""

    found: dict[str, list[str]] = {}
    pool = None
    for raw in body.splitlines():
        line = raw.strip()
        heading = re.match(r"^#{2,4}\s*([a-z]+)\s*$", line, re.I)
        if heading and heading.group(1).lower() in POOLS:
            pool = heading.group(1).lower()
            continue
        if pool and line.startswith(("-", "*")):
            text = line.lstrip("-* ").strip()
            if text and not text.startswith("<!--"):
                found.setdefault(pool, []).append(text)
    return language, credit, found


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--body-file", required=True)
    ap.add_argument("--out", default="comment.md")
    args = ap.parse_args()

    body = pathlib.Path(args.body_file).read_text(encoding="utf-8")
    language, credit, found = parse(body)
    known = shipped(language)

    total = sum(len(v) for v in found.values())
    if not total:
        pathlib.Path(args.out).write_text(
            "Greg could not find any lines in this. They want to sit under a "
            "`### chaos` style heading, one per bullet. His panel does that for "
            "you: **Settings → Greg → Lines you wrote → Share the good ones.**\n",
            encoding="utf-8",
        )
        print("no lines found")
        return

    out = [
        f"Thanks. **{total} lines** for `{language}`"
        + (f", credited to **{credit}**." if credit else ", no credit requested."),
        "",
        "Tick the ones to keep. Anything left unticked is not taken, and no "
        "reply is needed for those.",
        "",
    ]

    dupes = 0
    for pool in POOLS:
        lines = found.get(pool)
        if not lines:
            continue
        out.append(f"**{pool}**")
        out.append("")
        for text in lines:
            if text in known:
                dupes += 1
                out.append(f"- [ ] ~~{text}~~ <sub>already a {pool} line</sub>")
            else:
                out.append(f"- [ ] {text}")
        out.append("")

    if dupes:
        out.append(
            f"{dupes} of these are already in the pools and are struck through. "
            "Ticking one does nothing, CI would reject it as a duplicate."
        )
        out.append("")
    out.append(
        "<sub>Greg's line sorter. It reformats and counts, it does not have "
        "opinions about which are funny.</sub>"
    )

    pathlib.Path(args.out).write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"{total} lines, {dupes} already shipped, language {language}")


if __name__ == "__main__":
    main()
