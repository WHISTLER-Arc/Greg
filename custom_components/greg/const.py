"""Constants for Greg integration."""
import re
import unicodedata

DOMAIN = "greg"
VERSION = "1.7.0b2"
VERSION_DISPLAY = "v1.7.0b2"

# Config keys
CONF_VIBRATION_SENSOR = "vibration_sensor"
CONF_MEDIA_PLAYER = "media_player"
CONF_TTS_ENGINE = "tts_engine"
CONF_VOLUME = "volume"
CONF_QUIET_HOURS_ENABLED = "quiet_hours_enabled"
CONF_QUIET_START = "quiet_start"
CONF_QUIET_END = "quiet_end"
CONF_CONDITIONS = "conditions"

# Advanced config keys
CONF_SOFT_THRESHOLD = "soft_threshold"
CONF_MEDIUM_THRESHOLD = "medium_threshold"
CONF_CHAOS_THRESHOLD = "chaos_threshold"
CONF_RESET_DELAY = "reset_delay"
CONF_SILENCE_TIMEOUT = "silence_timeout"
CONF_EXISTENTIAL_INTERVAL = "existential_interval"
CONF_SENSITIVITY = "sensitivity"
CONF_SUPPRESS_CHIME = "suppress_chime"
CONF_EMIT_EVENTS = "emit_events"
CONF_SPEECH_MODE = "speech_mode"
CONF_OPENERS = "openers"
CONF_TTS_VOICE = "tts_voice"
CONF_LANGUAGE = "language"

# Defaults - conservative, not annoying
DEFAULT_VOLUME = 0.35
DEFAULT_QUIET_START = "22:00"
DEFAULT_QUIET_END = "08:00"
DEFAULT_SOFT_THRESHOLD = 1
DEFAULT_MEDIUM_THRESHOLD = 3
DEFAULT_CHAOS_THRESHOLD = 6

# The ladder has to climb. Greg checks chaos first, so a stored chaos below
# medium means he skips medium entirely and nothing on screen says why: the
# advanced dialog has always let the three be set in any order, and installs
# out there already hold values that cross.
#
# Sorted rather than pushed apart, because the numbers are likelier to be what
# somebody meant than the labels are. Soft 1, medium 6, chaos 4 reads as "he
# escalates at 1, 4 and 6", so that is what it becomes, rather than shoving
# chaos out to 7 where it was never asked to be.
#
# Called from the panel, the set_options service and the options dialog, so
# the rule exists once. Also applied when Greg reads his own config, because
# an install that crossed them before this shipped never passes back through
# any of the three.
THRESHOLD_MIN = 1
THRESHOLD_KEYS = (CONF_SOFT_THRESHOLD, CONF_MEDIUM_THRESHOLD, CONF_CHAOS_THRESHOLD)


def normalise_thresholds(soft, medium, chaos) -> tuple[int, int, int]:
    """Three thresholds that strictly increase, from whatever was stored."""
    defaults = (DEFAULT_SOFT_THRESHOLD, DEFAULT_MEDIUM_THRESHOLD, DEFAULT_CHAOS_THRESHOLD)
    values = []
    for raw, fallback in zip((soft, medium, chaos), defaults):
        try:
            values.append(int(raw))
        except (TypeError, ValueError):
            values.append(fallback)

    values.sort()
    # Equal is as broken as crossed: two pools sharing a number means the lower
    # one can never be reached. Each is pushed to at least one above the last.
    out = []
    floor = THRESHOLD_MIN
    for value in values:
        value = max(value, floor)
        out.append(value)
        floor = value + 1
    return tuple(out)


DEFAULT_RESET_DELAY = 8
DEFAULT_SILENCE_TIMEOUT = 20
DEFAULT_EXISTENTIAL_INTERVAL = 42

# What the ladder's track shows by default, in taps. Chosen because the useful
# range is the low end: the counter resets after a few quiet seconds, so
# reaching twelve taps in one go already takes determination.
#
# An install whose chaos was set higher in the advanced dialog, which allowed
# up to 20, gets a track that stretches to fit it rather than having its
# setting quietly dragged down the first time the panel saves.
LADDER_TRACK_MAX = 12
THRESHOLD_MAX = 20

# Low, high and fallback for each timing value, matching the advanced dialog's
# own sliders. Kept here so the service, the dialog and the panel agree on what
# is acceptable rather than each carrying its own numbers.
TIMING_LIMITS = {
    CONF_RESET_DELAY: (2, 30, DEFAULT_RESET_DELAY),
    CONF_SILENCE_TIMEOUT: (5, 60, DEFAULT_SILENCE_TIMEOUT),
    CONF_EXISTENTIAL_INTERVAL: (10, 120, DEFAULT_EXISTENTIAL_INTERVAL),
}


def clamp_timing(key: str, value) -> int:
    """One timing value, forced inside its limits.

    Junk falls back to the default rather than raising: these arrive from a
    config entry somebody can edit by hand and from a service any automation
    can call, and neither should be able to stop Greg loading.
    """
    low, high, fallback = TIMING_LIMITS[key]
    try:
        number = int(value)
    except (TypeError, ValueError):
        return fallback
    return max(low, min(high, number))
DEFAULT_SENSITIVITY = 75
# Sensitivity is a refractory window, not a gain. Once Greg registers a
# disturbance he ignores further sensor events for a moment, so a sensor that
# fires a burst on one physical tap still only counts as one tap. 100 filters
# nothing; 1 filters for very nearly this many seconds.
SENSITIVITY_MAX_DEBOUNCE = 10.0
DEFAULT_SUPPRESS_CHIME = True

# Greg fires an event every time he picks a line, so automations can react to it,
# log it, or run it through something cleverer before anything is said out loud.
EVENT_LINE = f"{DOMAIN}_line"
DEFAULT_EMIT_EVENTS = True

# Who does the talking. In event_only Greg picks the line and fires the event but
# says nothing, leaving the speaking to whatever is listening.
SPEECH_MODE_GREG = "greg"
SPEECH_MODE_EVENT_ONLY = "event_only"
SPEECH_MODES = [SPEECH_MODE_GREG, SPEECH_MODE_EVENT_ONLY]
DEFAULT_SPEECH_MODE = SPEECH_MODE_GREG

# Openers and the five line pools now live in the lines package, one module
# per language. See lines/TEMPLATE.py for how to add one.
#
# Empty means follow whatever language Home Assistant is set to, which is right
# for almost everybody. Set it explicitly if your HA is in one language and you
# would rather Greg moaned in another.
DEFAULT_LANGUAGE = ""
OPENER_CHANCE = 0.3
DEFAULT_OPENERS = True

# How many lines either side of a reshuffle are kept apart. A fair shuffle will
# happily put a line at the end of one cycle and the start of the next, which
# sounds like a repeat even though every line is still played exactly once.
DECK_SEAM_GUARD = 5

# Passed straight through to the TTS engine as options.voice when set. Left empty
# Greg uses whatever the engine defaults to, which is fine until you also use that
# engine for something else and would rather it did not sound like a tired table.
#
# This one applies to English only. It predates Greg speaking anything else, so
# anyone who set it set an English voice, and letting it carry into Dutch would
# recreate the very bug the per-language voices below exist to fix.
DEFAULT_TTS_VOICE = ""

# A voice per language, because one voice cannot pronounce three languages. The
# key is built from the language code, so tts_voice_nl, tts_voice_pt and so on,
# and the config flow generates a field for whatever languages are installed.
# Adding a language file still needs nothing else changed.
#
# This matters more than it looks. Piper takes a voice name like
# nl_NL-ronnie-medium, and a voice is tied to one language. Handing it Dutch
# text while it holds an English voice does not produce accented Dutch, it
# produces an English speaker reading Dutch letters aloud.
CONF_TTS_VOICE_PREFIX = "tts_voice_"


def tts_voice_key(language: str) -> str:
    """Config key holding the voice for one language."""
    return f"{CONF_TTS_VOICE_PREFIX}{language}"


# A Piper voice is named for the locale it speaks: en_US-glados-high. That
# makes the voice the better authority on which locale to ask the engine for,
# and reported by rujelus22 on the forum it is the difference between Greg
# using the voice you chose and ignoring it.
_VOICE_LOCALE = re.compile(r"^([A-Za-z]{2,3})_([A-Za-z]{2,4})[-_]")


def voice_locale(voice: str) -> str | None:
    """The locale a voice name carries, or None if it carries none."""
    match = _VOICE_LOCALE.match(str(voice or ""))
    if not match:
        return None
    return f"{match.group(1).lower()}_{match.group(2).upper()}"


def _fold(name: str) -> str:
    """A voice name with its accents and its case taken off.

    Only for comparing. What gets sent to the engine is always a real name,
    either exactly what the user typed or exactly what the engine advertised.
    """
    stripped = unicodedata.normalize("NFKD", str(name or ""))
    return "".join(c for c in stripped if not unicodedata.combining(c)).casefold()


def match_voice(voice: str, available) -> tuple[str | None, str]:
    """Resolve a configured voice against what the engine advertises.

    Returns the name to send and why, one of:

    - "exact", the engine advertises it.
    - "corrected", it matches one the engine advertises apart from accents or
      case, so the advertised spelling is sent instead. This is the
      pt_PT-tugao-medium against pt_PT-tugão-medium trap from 1.5.5, now
      fixed for the user rather than refused.
    - "unlisted", nothing matches. It is sent anyway: Piper will load a voice
      sitting in its share folder that Wyoming never advertised, and refusing
      those is what stopped a custom voice working at all.
    - "none", no voice is configured.
    """
    if not voice:
        return None, "none"

    names = [str(getattr(v, "voice_id", v)) for v in (available or ())]
    if not names or voice in names:
        return voice, "exact"

    folded = _fold(voice)
    for name in names:
        if _fold(name) == folded:
            return name, "corrected"
    return voice, "unlisted"


def choose_locale(language: str, supported, voice: str = "") -> str | None:
    """The locale to ask the engine for, or None to let it choose.

    Greg's codes are bare, en and nl and pt. Engines advertise locales, and
    Home Assistant does not reconcile the two: hand it a code the engine has
    not advertised and it refuses outright rather than falling back, which
    silences him completely.

    A configured voice decides this when it can, because a voice belongs to
    exactly one locale and the whole point of naming one is to be given it.
    Only when it speaks the language Greg is speaking, so an English voice
    left over from an English-only setup cannot drag Dutch to en_US.

    Failing that, a locale whose region matches its language wins, which is
    how nl reaches nl_NL rather than nl_BE. That rule does nothing for
    English, where en_en does not exist, so what is left is alphabetical: with
    both installed, en_GB beats en_US. Harmless until you own an en_US voice,
    at which point Greg checks it against the en_GB voice list and throws it
    away. Hence the voice going first.
    """
    codes = [str(c) for c in (supported or ())]
    if not codes:
        return None

    locale = voice_locale(voice)
    if locale and locale.split("_")[0] == language.lower():
        for code in codes:
            if code.lower() == locale.lower():
                return code

    if language in codes:
        return language

    candidates = [c for c in codes if c.lower().split("_")[0] == language.lower()]
    if not candidates:
        return None
    preferred = f"{language}_{language}".lower()
    for code in candidates:
        if code.lower() == preferred:
            return code
    return sorted(candidates)[0]

# Lines written by the person who owns the table, kept in the config entry
# rather than in a file, so they survive updates and need no filesystem access.
#
# Shape mirrors the lines package, {language: {pool: [line, ...]}}, because a
# line belongs to a language as much as a translation does. Somebody's Dutch
# joke should not turn up while Greg is speaking English.
CONF_CUSTOM_LINES = "custom_lines"

# Off, custom lines join the built-in ones and Greg draws from both. On, he uses
# only what you wrote, for anyone who wants a different table rather than a
# slightly expanded one.
#
# It never empties a pool. Switch it on with nothing written for a pool and that
# pool falls back to the built-in lines, because a silent Greg is a broken Greg
# and this setting is not worth breaking him over.
CONF_CUSTOM_ONLY = "custom_only"
DEFAULT_CUSTOM_ONLY = False

# One line has to be speakable and not accidentally enormous. Long enough for
# the longest built-in line with room to spare, short enough that a paste
# accident does not become Greg's new personality.
CUSTOM_LINE_MAX = 300
CUSTOM_LINES_MAX_PER_POOL = 200

# Conditions Greg consults before reacting, alongside quiet hours rather than
# instead of it. Each row is {entity_id, op, state} and every row must pass, so
# a row that fails keeps him quiet the same way a quiet hour does.
#
# Deliberately smaller than Home Assistant's own condition syntax. Rows cover
# the "core conditions" pattern this was asked for, and anything wanting or,
# templates or numeric ranges points a row at a template binary_sensor. That
# logic then belongs to the house rather than to Greg, and it is one row here
# either way.
#
# It also keeps the gate synchronous. Rows are a states lookup and a string
# compare, so _is_blocked() stays callable from the two @callback paths and
# from the property the mood sensor publishes.
CONDITION_IS = "is"
CONDITION_IS_NOT = "is_not"
CONDITION_OPS = (CONDITION_IS, CONDITION_IS_NOT)

# Enough for the handful of core conditions a house actually has. The cap
# exists so a malformed automation cannot write ten thousand rows into the
# config entry, not because anyone will reach it.
CONDITIONS_MAX = 20

# An entity that is missing, unavailable or unknown does NOT block. Treating it
# as a failed condition means one renamed entity silences Greg permanently with
# nothing in the log to say why, which is the worse failure by a distance: a
# Greg who talks when he should not is a nuisance, a Greg who has gone silent
# for good looks broken.
CONDITION_SKIP_STATES = ("unavailable", "unknown")

# A speaker in one of these states cannot be spoken to. Checked before Greg
# says anything, because tts.speak is fired with blocking=False: the call
# returns straight away and anything that fails afterwards lands in Home
# Assistant's log rather than in Greg's own error handling. Without the check
# he reports having spoken and the room stays silent, which is the hardest
# thing about him to debug and the thing behind issue #2.
SPEAKER_DEAD_STATES = ("unavailable", "unknown")

# Published by browser_mod, and by anything else playing through a browser,
# when the page has not been interacted with yet. Browsers refuse to play audio
# that no user gesture asked for, so the line is accepted and silently dropped.
ATTR_AUDIO_BLOCKED = "audio_interaction_required"

SERVICE_SET_LINES = "set_lines"
SERVICE_IMPORT_LINES = "import_lines"

# Backups are plain text, in the same shape the Share button already writes
# for a GitHub issue, with one heading level added for the language:
#
#     ## en
#     ### soft
#     - Oh. You again.
#
# Text rather than JSON so a backup can be read, edited and written by hand in
# any text editor, and so a file somebody sends you can be pasted straight into
# an issue and the other way round. Anything that is not a heading or a bullet
# is ignored, which makes the title line, blank lines and anybody's notes free.
#
# custom_only is deliberately not in the file. It is a setting, not a line.
BACKUP_LANGUAGE_PREFIX = "## "
BACKUP_POOL_PREFIX = "### "
BACKUP_LINE_PREFIX = "- "

IMPORT_MERGE = "merge"
IMPORT_REPLACE = "replace"
IMPORT_MODES = (IMPORT_MERGE, IMPORT_REPLACE)


def format_lines_backup(custom_lines, pools, header: str = "") -> str:
    """Everything somebody has written, as the text of a backup file.

    The pool order is passed in rather than imported, so this file stays
    importable on its own and the tests need no Home Assistant.
    """
    out = [header] if header else []
    for language in sorted(custom_lines or {}):
        per_language = custom_lines.get(language) or {}
        if not isinstance(per_language, dict):
            continue
        written = [(pool, per_language.get(pool) or []) for pool in pools]
        written = [(pool, lines) for pool, lines in written if lines]
        if not written:
            continue
        out.append(f"\n{BACKUP_LANGUAGE_PREFIX}{language}")
        for pool, lines in written:
            out.append(f"\n{BACKUP_POOL_PREFIX}{pool}\n")
            out.extend(f"{BACKUP_LINE_PREFIX}{line}" for line in lines)
    return "\n".join(out).strip() + "\n"


def parse_lines_backup(text: str, languages, pools) -> tuple[dict, dict]:
    """Read a backup file into {language: {pool: [line]}}, and what was skipped.

    Deliberately forgiving. This is a file a person may well have typed
    themselves, and the useful answer to a stray blank line or a note at the
    top is to get on with it. What cannot be guessed at is counted and
    reported, so the panel can say "ignored 4 lines under a pool called
    'funny'" rather than quietly dropping them.
    """
    known_languages = {str(code).lower(): str(code) for code in (languages or ())}
    known_pools = {str(pool).lower(): str(pool) for pool in (pools or ())}

    found: dict[str, dict[str, list[str]]] = {}
    skipped = {"languages": [], "pools": [], "lines": 0, "orphans": 0}
    language = None
    pool = None

    for raw in str(text or "").splitlines():
        line = raw.strip()
        if not line:
            continue

        if line.startswith(BACKUP_POOL_PREFIX):
            name = line[len(BACKUP_POOL_PREFIX):].strip().lower()
            pool = known_pools.get(name)
            if pool is None and name not in skipped["pools"]:
                skipped["pools"].append(name)
            continue

        if line.startswith(BACKUP_LANGUAGE_PREFIX):
            name = line[len(BACKUP_LANGUAGE_PREFIX):].strip().lower()
            # A language heading ends the pool with it, so lines cannot leak
            # from one language's pool into the next language.
            pool = None
            language = known_languages.get(name)
            if language is None and name not in skipped["languages"]:
                skipped["languages"].append(name)
            continue

        if not line.startswith(BACKUP_LINE_PREFIX):
            continue

        content = " ".join(line[len(BACKUP_LINE_PREFIX):].split())
        if not content:
            continue
        if language is None or pool is None:
            # A bullet before any heading, or under one that was not
            # understood. Counted rather than guessed at.
            if language is None and pool is None:
                skipped["orphans"] += 1
            else:
                skipped["lines"] += 1
            continue

        bucket = found.setdefault(language, {}).setdefault(pool, [])
        if content not in bucket:
            bucket.append(content)

    return found, skipped

# Mood states
MOOD_RESTING = "resting"
MOOD_ANNOYED = "annoyed"
MOOD_JUDGING = "judging"
MOOD_EXISTENTIAL = "existential"
MOOD_OPTIONS = [MOOD_RESTING, MOOD_ANNOYED, MOOD_JUDGING, MOOD_EXISTENTIAL]

# Single source of truth for mood -> image filename.
# Filenames intentionally match mood labels 1:1 so nothing needs translating.
# Change a filename here and the card, panel, and docs all follow.
MOOD_IMAGES = {
    MOOD_RESTING: "greg_resting.png",
    MOOD_ANNOYED: "greg_annoyed.png",
    MOOD_JUDGING: "greg_judging.png",
    MOOD_EXISTENTIAL: "greg_existential.png",
}

# Platforms owned by this integration
PLATFORMS = ["sensor", "switch"]

# Services
SERVICE_POKE = "poke"
SERVICE_UNINSTALL = "uninstall"
SERVICE_SET_OPTIONS = "set_options"

# The settings Greg's own panel can change. The thresholds and the three timing
# values joined them in 1.7: as one ladder and three numbers they are four
# controls rather than six sliders, which is what kept them out of a 300px
# column before. They remain in the advanced dialog as well, like every other
# setting here.
#
# What is still dialog-only is the stuff with no sensible panel shape: the
# per-language voice names, openers, the chime workaround, and the two switches
# for people wiring Greg into their own automations.
BASIC_OPTION_KEYS = (
    CONF_VIBRATION_SENSOR,
    CONF_MEDIA_PLAYER,
    CONF_TTS_ENGINE,
    CONF_VOLUME,
    CONF_SENSITIVITY,
    CONF_QUIET_HOURS_ENABLED,
    CONF_QUIET_START,
    CONF_QUIET_END,
    CONF_CONDITIONS,
    CONF_LANGUAGE,
    CONF_SOFT_THRESHOLD,
    CONF_MEDIUM_THRESHOLD,
    CONF_CHAOS_THRESHOLD,
    CONF_RESET_DELAY,
    CONF_SILENCE_TIMEOUT,
    CONF_EXISTENTIAL_INTERVAL,
)

# Greg's mood images live here once installed. This is the only path outside
# the integration folder that Greg owns, and the only one the wizard deletes.
WWW_ASSET_DIR = "greg"

# Panel
PANEL_URL_PATH = "greg"
PANEL_TITLE = "Greg"
PANEL_ICON = "mdi:robot-outline"
PANEL_STATIC_URL_BASE = "/greg_panel"
# Versioned so a Greg update actually reaches the browser. Without the query
# string the URL never changes, so neither the HTTP cache nor Home Assistant's
# service worker ever refetches, and every panel change stays invisible until
# the user clears their caches by hand. A hard refresh alone does not do it,
# because the service worker keys on the URL and answers from its own store.
PANEL_JS_URL = f"/greg_panel/greg-panel.js?v={VERSION}"
PANEL_DATA_KEY = f"{DOMAIN}_panel"
# Images are served to the panel from here (maps to www/greg in repo, copied into integration)
IMG_STATIC_URL_BASE = "/greg_images"

