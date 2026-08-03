"""Greg in European Portuguese. Not written yet.

pt-PT specifically. Brazilian Portuguese is a different language for comic
purposes and would want its own file rather than inheriting this one.

Everything here falls back to English until it is. Read TEMPLATE.py before
adding anything, and do not translate the English lines.
"""

LANGUAGE = "pt"
LANGUAGE_NAME = "Português (Portugal)"

LINES_SOFT: list[str] = []

LINES_MEDIUM: list[str] = []

LINES_CHAOS: list[str] = []

LINES_EXISTENTIAL: list[str] = []

LINES_SILENCE: list[str] = []

OPENERS: list[str] = []

POOLS = {
    "soft": LINES_SOFT,
    "medium": LINES_MEDIUM,
    "chaos": LINES_CHAOS,
    "existential": LINES_EXISTENTIAL,
    "silence": LINES_SILENCE,
}
