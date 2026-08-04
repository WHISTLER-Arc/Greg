"""Greg's line pools, one module per language.

Adding a language is one file and one entry in LANGUAGES below. Copy
TEMPLATE.py, write it, add the entry. Nothing else in the integration needs to
know the language exists.

Anything a language has not written yet falls back to English, so a partial
translation is a perfectly valid contribution. Half a language is better than
none, and Greg will simply be English in the gaps.
"""
from __future__ import annotations

from . import en, nl, pt

# Order here is the order they appear in the settings dropdown. English first
# because it is the original, the rest alphabetically by their own name.
LANGUAGES = {
    "en": en,
    "nl": nl,
    "pt": pt,
}

DEFAULT_LANGUAGE = "en"
POOL_KEYS = ("soft", "medium", "chaos", "existential", "silence")

# Regional codes that must not be served by their base language, because the
# two are different enough that the wrong one is worse than English.
#
# pt-BR is the case in point. Brazilian and European Portuguese are routinely
# treated as interchangeable by software that should know better, and being
# handed the other one when you explicitly asked is its own small insult. A
# Brazilian gets English until somebody writes pt-br.py, which at least reads
# as an honest gap rather than a wrong guess.
DISTINCT_REGIONS = {"pt-br"}


def available() -> dict[str, str]:
    """Language codes mapped to what they call themselves."""
    return {code: mod.LANGUAGE_NAME for code, mod in LANGUAGES.items()}


def resolve(language: str | None) -> str:
    """Return a language code we actually have.

    Accepts anything Home Assistant might hand over, including regional codes
    like nl-BE, and falls back to English rather than failing. A user whose HA
    is set to a language Greg does not speak gets English, not a broken
    integration.

    Regional codes normally collapse to their base language, so nl-BE is served
    by nl. The exceptions are in DISTINCT_REGIONS, which go to English instead.
    """
    if not language:
        return DEFAULT_LANGUAGE
    code = str(language).replace("_", "-").lower()
    if code in LANGUAGES:
        return code
    if code in DISTINCT_REGIONS:
        return DEFAULT_LANGUAGE
    base = code.split("-")[0]
    if base in LANGUAGES:
        return base
    return DEFAULT_LANGUAGE


def pool(language: str | None, key: str) -> list[str]:
    """Lines for one reaction, in the closest language we have.

    Falls back to English per pool rather than per language, so a language that
    has written three of the five is used for those three.
    """
    module = LANGUAGES[resolve(language)]
    lines = getattr(module, "POOLS", {}).get(key)
    if lines:
        return lines
    return en.POOLS[key]


def openers(language: str | None) -> list[str]:
    """Throat-clearing for the given language, English if it has none."""
    module = LANGUAGES[resolve(language)]
    return getattr(module, "OPENERS", None) or en.OPENERS


def coverage() -> dict[str, dict[str, int]]:
    """How much of each language is actually written.

    Used by the tests and by anyone wondering whether a language is finished.
    """
    return {
        code: {
            **{k: len(getattr(mod, "POOLS", {}).get(k) or []) for k in POOL_KEYS},
            "openers": len(getattr(mod, "OPENERS", None) or []),
        }
        for code, mod in LANGUAGES.items()
    }
