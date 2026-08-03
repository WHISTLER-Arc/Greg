"""Copy this file to your language code, for example de.py, and write it.

READ THIS FIRST, because it is the whole job.

Do not translate the English lines. Translating them produces sentences that
are correct and not funny, which is worse than nothing.

Greg's humour lives in the register, not the words. The joke in "I am
load-bearing and nothing else" is bureaucratic engineering language applied to
feelings. Carry that across literally and you get a true statement about
furniture. What you want is the equivalent register in your own language,
found natively, written by someone who thinks in it.

So: read a few English lines to get the character, then close the file and
write your own. Same character, your language, your jokes.

WHO GREG IS

  A coffee table with far more processing power than the job requires, and the
  emotional burden that comes with it. Formal, measured, deadpan. Resigned
  rather than angry. He notices everything and can do nothing about any of it.

  He is never called Marvin, and no line is ever lifted from Douglas Adams.
  Same factory, different unit.

THE RULES

  - Formal register, delivered flat. The gap between the formality and the
    triviality of the complaint is where the joke lives.
  - Contractions are fine.
  - No em-dashes, no semicolons, no tricolons.
  - One to three sentences. Long enough to build, short enough to land.
  - Keep them speakable. These go through text to speech, so read them aloud.
    Anything that trips your tongue will trip Piper.

THE FIVE POOLS

  soft         one disturbance, barely anything
  medium       several, the room is getting busy
  chaos        everything at once, he has given up counting
  existential  unprompted, roughly every 42 minutes, he has been thinking
  silence      twenty minutes of nothing, and he is enjoying it

  Fifty each is the target, matching English. Fewer is fine to start with.
  Anything you leave empty falls back to English, so a partial language is a
  perfectly good contribution.

WHEN YOU ARE DONE

  Add one line to __init__.py:

      from . import en, nl, pt, de
      LANGUAGES = {"en": en, "nl": nl, "pt": pt, "de": de}

  Then open a pull request. CI checks for duplicates and empty lines, so you
  will hear about those before anyone else does.
"""

LANGUAGE = "xx"
LANGUAGE_NAME = "Your language, as your language calls it"

LINES_SOFT: list[str] = []

LINES_MEDIUM: list[str] = []

LINES_CHAOS: list[str] = []

LINES_EXISTENTIAL: list[str] = []

LINES_SILENCE: list[str] = []

# Short throat-clearing that lands in front of a line about a third of the
# time. The value is in the two thirds where there is nothing at all, so keep
# these very short and very flat.
OPENERS: list[str] = []

POOLS = {
    "soft": LINES_SOFT,
    "medium": LINES_MEDIUM,
    "chaos": LINES_CHAOS,
    "existential": LINES_EXISTENTIAL,
    "silence": LINES_SILENCE,
}
