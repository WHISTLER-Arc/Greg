"""Constants for Greg integration."""

DOMAIN = "greg"
VERSION = "1.6.5b2"
VERSION_DISPLAY = "v1.6.5b2"

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
DEFAULT_RESET_DELAY = 8
DEFAULT_SILENCE_TIMEOUT = 20
DEFAULT_EXISTENTIAL_INTERVAL = 42
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

SERVICE_SET_LINES = "set_lines"

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

# The settings Greg's own panel can change. Everything else stays in the options
# flow, because the panel has no business rendering twelve sliders.
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

