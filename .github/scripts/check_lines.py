"""Sanity-check every language Greg speaks.

Loaded standalone rather than imported, because importing the integration
proper drags in Home Assistant and this needs to run on a bare runner.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

ROOT = pathlib.Path("custom_components/greg/lines")


def load():
    spec = importlib.util.spec_from_file_location(
        "greglines", ROOT / "__init__.py", submodule_search_locations=[str(ROOT)]
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["greglines"] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    lines = load()
    problems: list[str] = []

    for code, module in lines.LANGUAGES.items():
        if getattr(module, "LANGUAGE", None) != code:
            problems.append(f"{code}: LANGUAGE says {getattr(module, 'LANGUAGE', None)!r}")
        if not getattr(module, "LANGUAGE_NAME", ""):
            problems.append(f"{code}: no LANGUAGE_NAME")

        pools = getattr(module, "POOLS", {})
        missing = set(lines.POOL_KEYS) - set(pools)
        if missing:
            problems.append(f"{code}: POOLS missing {sorted(missing)}")

        for key, pool in pools.items():
            if len(pool) != len(set(pool)):
                dupes = sorted({l for l in pool if pool.count(l) > 1})
                problems.append(f"{code}/{key}: duplicates, e.g. {dupes[:2]}")
            if any(not str(l).strip() for l in pool):
                problems.append(f"{code}/{key}: contains an empty line")

    # English is the fallback for everything, so it must be complete.
    for key in lines.POOL_KEYS:
        if not lines.en.POOLS.get(key):
            problems.append(f"en/{key} is empty, and English is the fallback")
    if not lines.en.OPENERS:
        problems.append("en has no openers, and English is the fallback")

    if problems:
        print("Line problems:\n")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)

    print("Languages:")
    for code, cov in lines.coverage().items():
        written = sum(v for k, v in cov.items() if k != "openers")
        name = lines.LANGUAGES[code].LANGUAGE_NAME
        state = "complete" if written else "not written yet, falls back to English"
        print(f"  {code} ({name}): {written} lines, {cov['openers']} openers - {state}")


if __name__ == "__main__":
    main()
