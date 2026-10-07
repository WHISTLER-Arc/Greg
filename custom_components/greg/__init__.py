"""Greg integration - a Marvin-inspired personality for your coffee table."""
from __future__ import annotations

import logging
import os
import random
import asyncio
import shutil
from datetime import datetime, time, timedelta
from time import monotonic

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_interval,
    async_track_time_change,
)
from homeassistant.components.frontend import (
    async_register_built_in_panel,
    async_remove_panel,
)
from homeassistant.components.http import StaticPathConfig

from .lines import (
    DEFAULT_LANGUAGE as FALLBACK_LANGUAGE,
    POOL_KEYS,
    available as available_languages,
    openers as openers_for,
    pool as pool_for,
    resolve as resolve_language,
)

from .const import (
    DOMAIN,
    PLATFORMS,
    CONF_VIBRATION_SENSOR,
    CONF_MEDIA_PLAYER,
    CONF_TTS_ENGINE,
    CONF_VOLUME,
    CONF_QUIET_HOURS_ENABLED,
    CONF_QUIET_START,
    CONF_QUIET_END,
    CONF_CONDITIONS,
    CONF_SOFT_THRESHOLD,
    CONF_MEDIUM_THRESHOLD,
    CONF_CHAOS_THRESHOLD,
    CONF_RESET_DELAY,
    CONF_SILENCE_TIMEOUT,
    CONF_EXISTENTIAL_INTERVAL,
    CONF_SENSITIVITY,
    CONF_SUPPRESS_CHIME,
    CONF_EMIT_EVENTS,
    CONF_SPEECH_MODE,
    CONF_OPENERS,
    CONF_TTS_VOICE,
    tts_voice_key,
    CONF_LANGUAGE,
    normalise_thresholds,
    choose_locale,
    match_voice,
    clamp_timing,
    THRESHOLD_KEYS,
    THRESHOLD_MIN,
    THRESHOLD_MAX,
    LADDER_TRACK_MAX,
    TIMING_LIMITS,
    DEFAULT_SOFT_THRESHOLD,
    DEFAULT_MEDIUM_THRESHOLD,
    DEFAULT_CHAOS_THRESHOLD,
    DEFAULT_SENSITIVITY,
    DEFAULT_VOLUME,
    DEFAULT_EMIT_EVENTS,
    DEFAULT_SPEECH_MODE,
    DEFAULT_OPENERS,
    DEFAULT_QUIET_START,
    DEFAULT_QUIET_END,
    DEFAULT_TTS_VOICE,
    DEFAULT_LANGUAGE,
    SPEECH_MODE_EVENT_ONLY,
    SENSITIVITY_MAX_DEBOUNCE,
    DECK_SEAM_GUARD,
    OPENER_CHANCE,
    EVENT_LINE,
    VERSION_DISPLAY,
    MOOD_RESTING,
    MOOD_ANNOYED,
    MOOD_JUDGING,
    MOOD_EXISTENTIAL,
    MOOD_IMAGES,
    SERVICE_POKE,
    SERVICE_UNINSTALL,
    SERVICE_SET_OPTIONS,
    SERVICE_SET_LINES,
    BASIC_OPTION_KEYS,
    CONDITION_IS,
    CONDITION_IS_NOT,
    CONDITION_OPS,
    CONDITIONS_MAX,
    CONDITION_SKIP_STATES,
    SPEAKER_DEAD_STATES,
    ATTR_AUDIO_BLOCKED,
    CONF_CUSTOM_LINES,
    CONF_CUSTOM_ONLY,
    DEFAULT_CUSTOM_ONLY,
    CUSTOM_LINE_MAX,
    CUSTOM_LINES_MAX_PER_POOL,
    WWW_ASSET_DIR,
    PANEL_URL_PATH,
    PANEL_TITLE,
    PANEL_ICON,
    PANEL_STATIC_URL_BASE,
    PANEL_JS_URL,
    PANEL_DATA_KEY,
    IMG_STATIC_URL_BASE,
)

_LOGGER = logging.getLogger(__name__)


def _clean_conditions(raw) -> list[dict]:
    """Normalise condition rows, dropping anything unusable.

    A row missing its entity or its state is dropped rather than failed. The
    panel adds a row the moment you press +, so a half-filled row is the normal
    state of the form while you are still typing in it, and treating those as
    unmet would silence Greg mid-edit.
    """
    if not isinstance(raw, list):
        return []

    rows: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        entity_id = str(item.get("entity_id") or "").strip()
        state = " ".join(str(item.get("state") or "").split())
        op = item.get("op") or CONDITION_IS
        if not entity_id or "." not in entity_id or not state:
            continue
        if op not in CONDITION_OPS:
            op = CONDITION_IS
        rows.append({"entity_id": entity_id, "op": op, "state": state})
        if len(rows) >= CONDITIONS_MAX:
            break
    return rows

# Dispatcher signals so entities update the instant coordinator state changes.
SIGNAL_STATE_UPDATED = f"{DOMAIN}_state_updated"


async def _async_register_panel(hass: HomeAssistant) -> None:
    """Register Greg's sidebar panel and static asset paths. Idempotent."""
    panel_state = hass.data.setdefault(PANEL_DATA_KEY, {"registered": False})
    if panel_state["registered"]:
        return

    panel_dir = os.path.join(os.path.dirname(__file__), "panel")
    img_dir = os.path.join(os.path.dirname(__file__), "images")

    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(PANEL_STATIC_URL_BASE, panel_dir, False),
            StaticPathConfig(IMG_STATIC_URL_BASE, img_dir, True),
        ]
    )

    async_register_built_in_panel(
        hass,
        component_name="custom",
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        frontend_url_path=PANEL_URL_PATH,
        require_admin=False,
        config={
            "_panel_custom": {
                "name": "greg-panel",
                "embed_iframe": False,
                "trust_external": False,
                "js_url": PANEL_JS_URL,
            }
        },
    )
    panel_state["registered"] = True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Greg from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # The title is written once at setup and never revisited, so an entry created
    # on an older Greg keeps advertising that version forever. Correct it here so
    # an upgrade is reflected without the user having to remove and re-add him.
    expected_title = f"Greg {VERSION_DISPLAY}"
    if entry.title != expected_title:
        hass.config_entries.async_update_entry(entry, title=expected_title)

    coordinator = GregCoordinator(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = coordinator
    await coordinator.async_setup()

    # Entity platforms (sensor + switch) own Greg's state now.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(coordinator.async_reload))

    await _async_register_panel(hass)
    _async_register_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Greg."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    coordinator = hass.data[DOMAIN].pop(entry.entry_id, None)
    if coordinator:
        await coordinator.async_unload()

    # If no Greg entries remain, tear down panel + services.
    if not hass.data[DOMAIN]:
        panel_state = hass.data.get(PANEL_DATA_KEY)
        if panel_state and panel_state["registered"]:
            async_remove_panel(hass, PANEL_URL_PATH)
            panel_state["registered"] = False
        for service in (
            SERVICE_POKE,
            SERVICE_UNINSTALL,
            SERVICE_SET_OPTIONS,
            SERVICE_SET_LINES,
        ):
            if hass.services.has_service(DOMAIN, service):
                hass.services.async_remove(DOMAIN, service)

    return unload_ok


def _delete_www_assets(path: str) -> None:
    """Delete Greg's mood images. Blocking, so this runs in the executor.

    Scoped to /config/www/greg only. Nothing outside that directory is touched.
    """
    if os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Final cleanup when Greg is permanently removed.

    Entities, the device and coordinator storage are already gone by this point:
    HA cascades those off the config entry. What is left is the panel, and the
    mood images in /config/www, which HA does not clean up for us.

    Static paths registered with async_register_static_paths cannot be released
    at runtime. They clear on restart, which is why the wizard asks for one.
    """
    panel_state = hass.data.get(PANEL_DATA_KEY)
    if panel_state and panel_state.get("registered"):
        async_remove_panel(hass, PANEL_URL_PATH)
        panel_state["registered"] = False
    hass.data.pop(PANEL_DATA_KEY, None)
    hass.data.pop(DOMAIN, None)

    www_dir = hass.config.path("www", WWW_ASSET_DIR)
    await hass.async_add_executor_job(_delete_www_assets, www_dir)

    _LOGGER.info("Greg has been removed. He would have had something to say about this.")


@callback
def _async_register_services(hass: HomeAssistant) -> None:
    """Register Greg's services once."""
    if hass.services.has_service(DOMAIN, SERVICE_POKE):
        return

    async def _handle_poke(call) -> None:
        """Force Greg to react on demand."""
        for coordinator in hass.data.get(DOMAIN, {}).values():
            if isinstance(coordinator, GregCoordinator):
                await coordinator.async_poke()

    async def _handle_uninstall(call) -> None:
        """Remove Greg. Only what Greg owns, nothing else.

        Removing the config entry cascades through HA: platforms unload, then
        entities, the device and coordinator storage go with it. async_remove_entry
        handles the panel and the mood images afterwards.

        Nothing here matches on entity name. A user may legitimately own entities
        called greg_something that we did not create, and those must survive.
        """
        entry_ids = [
            entry_id
            for entry_id, value in hass.data.get(DOMAIN, {}).items()
            if isinstance(value, GregCoordinator)
        ]
        for entry_id in entry_ids:
            await hass.config_entries.async_remove(entry_id)

        if call.data.get("restart"):
            await hass.services.async_call(
                "homeassistant", "restart", {}, blocking=False
            )

    async def _handle_set_options(call) -> None:
        """Write basic settings back from Greg's panel.

        Updating the entry fires the update listener, which reloads him, so this
        deliberately takes every changed field in one call rather than one call
        per control. That is also why the panel has an Apply button.
        """
        fields = {key: call.data[key] for key in BASIC_OPTION_KEYS if key in call.data}
        if CONF_CONDITIONS in fields:
            fields[CONF_CONDITIONS] = _clean_conditions(fields[CONF_CONDITIONS])
        for key in TIMING_LIMITS:
            if key in fields:
                fields[key] = clamp_timing(key, fields[key])
        if not fields:
            return

        for entry_id, coordinator in list(hass.data.get(DOMAIN, {}).items()):
            if not isinstance(coordinator, GregCoordinator):
                continue
            entry = hass.config_entries.async_get_entry(entry_id)
            if entry is None:
                continue
            merged = {**entry.options, **fields}
            # Against what is stored rather than only what was sent, so a call
            # naming one threshold cannot cross it with the two it left alone.
            # The panel sends all three together; an automation need not.
            if any(key in fields for key in THRESHOLD_KEYS):
                current = {**entry.data, **merged}
                soft, medium, chaos = normalise_thresholds(
                    current.get(CONF_SOFT_THRESHOLD, DEFAULT_SOFT_THRESHOLD),
                    current.get(CONF_MEDIUM_THRESHOLD, DEFAULT_MEDIUM_THRESHOLD),
                    current.get(CONF_CHAOS_THRESHOLD, DEFAULT_CHAOS_THRESHOLD),
                )
                merged[CONF_SOFT_THRESHOLD] = soft
                merged[CONF_MEDIUM_THRESHOLD] = medium
                merged[CONF_CHAOS_THRESHOLD] = chaos
            if merged != dict(entry.options):
                hass.config_entries.async_update_entry(entry, options=merged)

    async def _handle_set_lines(call) -> None:
        """Write the owner's own lines back from Greg's panel.

        Takes one language and one pool at a time. The panel edits one list in
        front of you, and sending the whole nested blob every keystroke would
        make a lost race between two open tabs far too easy.

        Cleaning happens here rather than in the panel because the service is
        also the scripting interface, and anything reachable by an automation
        has to defend itself. Blank lines go, duplicates go, whitespace is
        trimmed, and the count and length are capped.
        """
        language = call.data[CONF_LANGUAGE]
        pool_key = call.data["pool"]

        seen: set[str] = set()
        cleaned: list[str] = []
        for raw in call.data.get("lines", []):
            line = " ".join(str(raw).split())[:CUSTOM_LINE_MAX].strip()
            if not line or line in seen:
                continue
            seen.add(line)
            cleaned.append(line)
            if len(cleaned) >= CUSTOM_LINES_MAX_PER_POOL:
                break

        for entry_id, coordinator in list(hass.data.get(DOMAIN, {}).items()):
            if not isinstance(coordinator, GregCoordinator):
                continue
            entry = hass.config_entries.async_get_entry(entry_id)
            if entry is None:
                continue

            existing = entry.options.get(CONF_CUSTOM_LINES) or {}
            stored = {k: dict(v) for k, v in existing.items() if isinstance(v, dict)}
            per_language = stored.setdefault(language, {})

            if cleaned:
                per_language[pool_key] = cleaned
            else:
                # An empty list is how the panel says "I deleted them all", so
                # drop the key rather than storing an empty list forever.
                per_language.pop(pool_key, None)
                if not per_language:
                    stored.pop(language, None)

            merged = {**entry.options, CONF_CUSTOM_LINES: stored}
            if CONF_CUSTOM_ONLY in call.data:
                merged[CONF_CUSTOM_ONLY] = call.data[CONF_CUSTOM_ONLY]
            if merged != dict(entry.options):
                hass.config_entries.async_update_entry(entry, options=merged)

    hass.services.async_register(DOMAIN, SERVICE_POKE, _handle_poke)
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_LINES,
        _handle_set_lines,
        schema=vol.Schema(
            {
                vol.Required(CONF_LANGUAGE): vol.In(list(available_languages().keys())),
                vol.Required("pool"): vol.In(list(POOL_KEYS)),
                vol.Required("lines"): [cv.string],
                vol.Optional(CONF_CUSTOM_ONLY): cv.boolean,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_OPTIONS,
        _handle_set_options,
        schema=vol.Schema(
            {
                vol.Optional(CONF_VIBRATION_SENSOR): cv.entity_id,
                vol.Optional(CONF_MEDIA_PLAYER): cv.entity_id,
                vol.Optional(CONF_TTS_ENGINE): cv.entity_id,
                vol.Optional(CONF_VOLUME): vol.All(
                    vol.Coerce(float), vol.Range(min=0.0, max=1.0)
                ),
                vol.Optional(CONF_SENSITIVITY): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=100)
                ),
                vol.Optional(CONF_QUIET_HOURS_ENABLED): cv.boolean,
                vol.Optional(CONF_QUIET_START): cv.matches_regex(r"^\d{2}:\d{2}$"),
                vol.Optional(CONF_QUIET_END): cv.matches_regex(r"^\d{2}:\d{2}$"),
                # Deliberately only shape-checked here. Rows are cleaned in
                # the handler, where a half-filled row is dropped rather than
                # failing the whole call and making Apply look broken.
                vol.Optional(CONF_CONDITIONS): vol.All(cv.ensure_list, [dict]),
                # Empty is valid and means follow Home Assistant.
                vol.Optional(CONF_LANGUAGE): vol.In(
                    ["", *available_languages().keys()]
                ),
                # Thresholds are range-checked but not order-checked here. A
                # crossed pair is sorted out in the handler instead of failing
                # the call, because an automation that nudges one threshold
                # should not error just because the result needs tidying.
                **{
                    vol.Optional(key): vol.All(
                        vol.Coerce(int), vol.Range(min=THRESHOLD_MIN, max=THRESHOLD_MAX)
                    )
                    for key in THRESHOLD_KEYS
                },
                **{
                    vol.Optional(key): vol.All(
                        vol.Coerce(int), vol.Range(min=low, max=high)
                    )
                    for key, (low, high, _default) in TIMING_LIMITS.items()
                },
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_UNINSTALL,
        _handle_uninstall,
        schema=vol.Schema({vol.Optional("restart", default=False): cv.boolean}),
    )


class GregCoordinator:
    """Manages Greg's state, reactions, and TTS output. Source of truth for entities."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._config = {**entry.data, **entry.options}
        # Internal session counter (churns fast, not entity-worthy)
        self._counter = 0
        # Persistent / entity-facing state
        self.enabled = True
        self.mood = MOOD_RESTING
        self.mood_level = 0
        self.last_line = ""
        self.vibrations_today = 0
        # Why the last thing he tried to say did not come out, or None. Read by
        # the panel so a silent Greg can explain himself.
        self.speech_problem = None
        # Timers / listeners
        self._reset_handle = None
        self._silence_handle = None
        self._existential_handle = None
        self._unsub_sensor = None
        self._unsub_midnight = None
        # Decks are keyed by language and pool, so switching language starts a
        # clean deck rather than carrying half a cycle of the old one across.
        self._decks: dict[tuple[str, str], list] = {}
        self._deck_pos: dict[tuple[str, str], int] = {}
        # Monotonic timestamp of the last sensor event Greg actually accepted.
        self._last_accepted: float | None = None

    # ---- lifecycle -------------------------------------------------------

    async def async_setup(self) -> None:
        sensor = self._config[CONF_VIBRATION_SENSOR]
        self._unsub_sensor = async_track_state_change_event(
            self.hass, [sensor], self._handle_vibration
        )

        # Was 37 here and 42 in const.py, so a fresh install that never
        # opened the dialog ran five minutes fast. One clamp, one default.
        interval = clamp_timing(
            CONF_EXISTENTIAL_INTERVAL, self._config.get(CONF_EXISTENTIAL_INTERVAL)
        )
        self._existential_handle = async_track_time_interval(
            self.hass, self._handle_existential, timedelta(minutes=interval)
        )

        # Daily tally reset at local midnight.
        self._unsub_midnight = async_track_time_change(
            self.hass, self._reset_daily_tally, hour=0, minute=0, second=0
        )

        _LOGGER.info("Greg is running. He is not pleased about it.")

    async def async_unload(self) -> None:
        for handle_attr in ("_unsub_sensor", "_existential_handle", "_unsub_midnight"):
            handle = getattr(self, handle_attr)
            if handle:
                handle()
                setattr(self, handle_attr, None)
        for timer_attr in ("_reset_handle", "_silence_handle"):
            timer = getattr(self, timer_attr)
            if timer:
                timer.cancel()
                setattr(self, timer_attr, None)
        # A reload may change the sensor or the sensitivity, so the old
        # refractory window should not carry over into the new config.
        self._last_accepted = None

    async def async_reload(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        # A deck is a shuffled copy of a pool, so a pool that just changed has a
        # deck that no longer matches it. Without this, a line you have only just
        # written is not heard until the current deck runs out, which for a
        # fifty line pool can be most of an evening, and it looks like the panel
        # simply did not save.
        #
        # Only the decks that actually changed are dropped. Reload fires on every
        # settings change, including a nudge of the volume slider, and clearing
        # all of them would restart every cycle and cause the repetition the
        # deck exists to prevent.
        previous = self.custom_lines()
        previously_only = self._config.get(CONF_CUSTOM_ONLY, DEFAULT_CUSTOM_ONLY)

        self._config = {**entry.data, **entry.options}

        current = self.custom_lines()
        if previously_only != self._config.get(CONF_CUSTOM_ONLY, DEFAULT_CUSTOM_ONLY):
            self._decks.clear()
            self._deck_pos.clear()
        else:
            for lang in set(previous) | set(current):
                before = previous.get(lang) or {}
                after = current.get(lang) or {}
                for pool_key in set(before) | set(after):
                    if before.get(pool_key) != after.get(pool_key):
                        self._decks.pop((lang, pool_key), None)
                        self._deck_pos.pop((lang, pool_key), None)

        await self.async_unload()
        await self.async_setup()
        # The entities survive a reload, so nothing makes them re-read their
        # attributes unless we ask. basic_config is published from there, and
        # without this the panel goes on being served the settings as they were
        # before the change it just made.
        self._notify()

    # ---- entity helpers --------------------------------------------------

    @callback
    def _notify(self) -> None:
        """Tell entities to refresh from current coordinator state."""
        async_dispatcher_send(self.hass, SIGNAL_STATE_UPDATED)

    def set_enabled(self, value: bool) -> None:
        """Called by the switch entity."""
        self.enabled = value
        if not value:
            # Going silent: drop to resting, clear counter.
            self._counter = 0
            self.mood = MOOD_RESTING
            self.mood_level = 0
        self._notify()

    # ---- reactions -------------------------------------------------------

    def _debounce_seconds(self) -> float:
        """How long Greg ignores the sensor after accepting a disturbance.

        Derived from sensitivity: 100 returns 0 and filters nothing, lower
        values widen the window. A cheap vibration sensor often fires several
        times for one physical tap, and without this every one of those counts
        as a separate disturbance and rockets Greg into chaos over nothing.
        """
        raw = self._config.get(CONF_SENSITIVITY, DEFAULT_SENSITIVITY)
        try:
            sensitivity = float(raw)
        except (TypeError, ValueError):
            sensitivity = float(DEFAULT_SENSITIVITY)
        sensitivity = max(1.0, min(100.0, sensitivity))
        return (100.0 - sensitivity) / 100.0 * SENSITIVITY_MAX_DEBOUNCE

    @callback
    def _is_bounce(self) -> bool:
        """True when this event lands inside the refractory window."""
        now = monotonic()
        window = self._debounce_seconds()
        if window > 0 and self._last_accepted is not None:
            if now - self._last_accepted < window:
                return True
        self._last_accepted = now
        return False

    @callback
    def _handle_vibration(self, event) -> None:
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state not in ("on", "vibrating", "detected"):
            return
        if not self.enabled or self._is_blocked():
            return
        # Filtered before anything is counted, so a bouncy sensor does not
        # inflate the daily tally either.
        if self._is_bounce():
            return

        self._counter += 1
        self.vibrations_today += 1

        if self._reset_handle:
            self._reset_handle.cancel()
        if self._silence_handle:
            self._silence_handle.cancel()

        reset_delay = clamp_timing(CONF_RESET_DELAY, self._config.get(CONF_RESET_DELAY))
        self._reset_handle = self.hass.loop.call_later(
            reset_delay, lambda: self.hass.async_create_task(self._reset_counter())
        )

        self._update_mood()
        self.hass.async_create_task(self._react())

    async def async_poke(self) -> None:
        """Force a reaction regardless of sensor (greg.poke service / panel button)."""
        if not self.enabled or self._is_blocked():
            return
        self._counter += 1
        self.vibrations_today += 1
        self._update_mood()
        await self._react()

    async def _react(self) -> None:
        soft, medium, chaos = self.thresholds

        if self._counter >= chaos:
            await self._speak("chaos")
        elif self._counter >= medium:
            await self._speak("medium")
        elif self._counter >= soft:
            await self._speak("soft")

    async def _reset_counter(self) -> None:
        self._counter = 0
        self._update_mood()
        silence_mins = clamp_timing(
            CONF_SILENCE_TIMEOUT, self._config.get(CONF_SILENCE_TIMEOUT)
        )
        self._silence_handle = self.hass.loop.call_later(
            silence_mins * 60,
            lambda: self.hass.async_create_task(self._handle_silence()),
        )

    async def _handle_silence(self) -> None:
        if not self.enabled or self._is_blocked():
            return
        await self._speak("silence")

    @callback
    def _handle_existential(self, now=None) -> None:
        if self._counter > 0 and self.enabled and not self._is_blocked():
            self.hass.async_create_task(
                self._speak("existential")
            )

    @callback
    def _reset_daily_tally(self, now=None) -> None:
        self.vibrations_today = 0
        self._notify()

    # ---- mood + speech ---------------------------------------------------

    @callback
    def _update_mood(self) -> None:
        """Compute mood + level from the session counter and notify entities."""
        soft, medium, chaos = self.thresholds

        if self._counter >= chaos:
            self.mood = MOOD_EXISTENTIAL
            self.mood_level = 100
        elif self._counter >= medium:
            self.mood = MOOD_JUDGING
            self.mood_level = 50 + int((self._counter / chaos) * 50)
        elif self._counter >= soft:
            self.mood = MOOD_ANNOYED
            self.mood_level = int((self._counter / medium) * 50)
        else:
            self.mood = MOOD_RESTING
            self.mood_level = 0
        self.mood_level = max(0, min(100, self.mood_level))
        self._notify()

    def _next_line(self, pool_key: str) -> str:
        """Return the next line from the shuffled deck for this pool.

        Every line plays once before any of them come round again. The awkward
        case is the seam between two cycles: a line near the end of one deck can
        land near the start of the next and be heard twice in quick succession
        despite the shuffle being perfectly fair. So the last few of the outgoing
        deck are pushed out of the first few of the incoming one.
        """
        language = self.language
        pool = self.lines_for(language, pool_key)
        deck_key = (language, pool_key)

        deck = self._decks.get(deck_key, [])
        pos = self._deck_pos.get(deck_key, 0)

        if pos >= len(deck):
            tail = set(deck[-DECK_SEAM_GUARD:]) if deck else set()
            new_deck = list(pool)
            random.shuffle(new_deck)

            if tail and len(new_deck) > DECK_SEAM_GUARD * 2:
                for i in range(DECK_SEAM_GUARD):
                    if new_deck[i] not in tail:
                        continue
                    candidates = [
                        j
                        for j in range(DECK_SEAM_GUARD, len(new_deck))
                        if new_deck[j] not in tail
                    ]
                    if not candidates:
                        break
                    j = random.choice(candidates)
                    new_deck[i], new_deck[j] = new_deck[j], new_deck[i]

            self._decks[deck_key] = new_deck
            self._deck_pos[deck_key] = 0
            deck = new_deck
            pos = 0

        self._deck_pos[deck_key] = pos + 1
        return deck[pos]

    def custom_lines(self, language: str | None = None, pool_key: str | None = None):
        """Whatever the owner has written, for a language, or a pool, or all.

        Stored as {language: {pool: [line]}}. Read defensively because this
        comes out of a config entry a user can edit by hand, and a malformed
        blob should cost you your custom lines rather than the integration.
        """
        raw = self._config.get(CONF_CUSTOM_LINES) or {}
        if not isinstance(raw, dict):
            return {} if language is None else ([] if pool_key else {})

        if language is None:
            return raw
        per_language = raw.get(language) or {}
        if not isinstance(per_language, dict):
            return [] if pool_key else {}
        if pool_key is None:
            return per_language
        lines = per_language.get(pool_key) or []
        return [str(l) for l in lines if str(l).strip()] if isinstance(lines, list) else []

    def lines_for(self, language: str, pool_key: str) -> list[str]:
        """The pool Greg actually draws from, built-ins plus anything written.

        Custom lines are appended rather than merged in place, so the deck
        shuffle treats them exactly like the rest and a new line is no more or
        less likely to come up than a built-in one.

        With custom_only on, the built-ins are dropped, but only when there is
        something to drop them for. A pool nobody has written for keeps its
        built-in lines regardless, because the alternative is Greg silently
        having nothing to say, and every bug in this release has been some
        version of that.
        """
        built_in = list(pool_for(language, pool_key))
        mine = [l for l in self.custom_lines(language, pool_key) if l not in built_in]
        if not mine:
            return built_in
        if self._config.get(CONF_CUSTOM_ONLY, DEFAULT_CUSTOM_ONLY):
            return mine
        return built_in + mine

    @property
    def custom_only(self) -> bool:
        return bool(self._config.get(CONF_CUSTOM_ONLY, DEFAULT_CUSTOM_ONLY))

    @property
    def pool_sizes(self) -> dict:
        """Counts per pool for the current language, for the panel's editor.

        Counts rather than the lines themselves, because the built-in pools are
        250 lines the browser already cannot change and has no reason to hold.
        """
        language = self.language
        return {
            key: {
                "built_in": len(pool_for(language, key)),
                "mine": len(self.custom_lines(language, key)),
                "in_use": len(self.lines_for(language, key)),
            }
            for key in POOL_KEYS
        }

    def _maybe_opener(self) -> str:
        """Return an opener, or an empty string most of the time.

        Deliberately not deck-managed. Openers are padding and padding repeats,
        which is exactly what makes it sound like speech rather than a recital.
        """
        if not self._config.get(CONF_OPENERS, DEFAULT_OPENERS):
            return ""
        if random.random() >= OPENER_CHANCE:
            return ""
        return random.choice(openers_for(self.language))

    def _engine_language(self, tts_engine: str, language: str, voice: str = "") -> str | None:
        """A language code this engine has actually advertised, or None.

        The choosing is in const.py, where it can be tested without a Home
        Assistant to hand. This part is only asking the engine what it says it
        supports, which is the part that can throw.
        """
        try:
            component = self.hass.data.get("tts")
            entity = component.get_entity(tts_engine) if component else None
            supported = getattr(entity, "supported_languages", None)
        except Exception:  # noqa: BLE001 - never let this stop him speaking
            return None
        return choose_locale(language, supported, voice)

    def _engine_voice(self, tts_engine: str, engine_language: str | None, voice: str) -> str | None:
        """The voice to send, which is very nearly always the one configured.

        An engine advertising a voice list is useful, but it is not the whole
        truth: Piper will happily load a voice file sitting in its share
        folder that Wyoming never advertised. Refusing those meant a custom
        voice could not be used at all, which is what rujelus22 ran into on
        the forum, so an unrecognised name is now sent with a note in the log
        rather than thrown away.

        A name that matches apart from its accents or its case is corrected to
        the spelling the engine gave, which is the pt_PT-tugao-medium trap
        from 1.5.5 fixed rather than merely diagnosed.
        """
        try:
            component = self.hass.data.get("tts")
            entity = component.get_entity(tts_engine) if component else None
            getter = getattr(entity, "async_get_supported_voices", None)
            available = getter(engine_language) if (getter and engine_language) else None
        except Exception:  # noqa: BLE001 - never let this stop him speaking
            return voice or None

        resolved, how = match_voice(voice, available)
        if how == "corrected":
            _LOGGER.info(
                "Greg's voice for %s was written %r and the engine spells it %r, "
                "so he is using the engine's spelling.",
                engine_language, voice, resolved,
            )
        elif how == "unlisted":
            _LOGGER.warning(
                "Greg's voice for %s, %r, is not one this engine advertises. He is "
                "asking for it anyway, which is right if you installed it yourself. "
                "If he goes quiet or sounds wrong, check the spelling: it is matched "
                "character for character, accents included. Advertised: %s",
                engine_language,
                voice,
                ", ".join(sorted(str(getattr(v, "voice_id", v)) for v in (available or ()))[:8]) or "none",
            )
        return resolved

    async def _speak(self, pool_key: str) -> None:
        # Resolved once and reused, so the line, the event and the TTS call can
        # never disagree about which language this is.
        language = self.language
        line = self._next_line(pool_key)
        opener = self._maybe_opener()
        spoken_text = f"{opener} {line}" if opener else line

        self.last_line = spoken_text
        self._notify()

        player = self._config[CONF_MEDIA_PLAYER]
        volume = self._config.get(CONF_VOLUME, DEFAULT_VOLUME)
        tts_engine = self._config.get(CONF_TTS_ENGINE, "tts.google_en_com")
        suppress_chime = self._config.get(CONF_SUPPRESS_CHIME, True)

        speech_mode = self._config.get(CONF_SPEECH_MODE, DEFAULT_SPEECH_MODE)
        will_speak = speech_mode != SPEECH_MODE_EVENT_ONLY

        # Fired before the speaking, so a listener that wants to say something
        # cleverer instead is not racing Greg's own audio. The speaker and engine
        # ride along so an automation can reuse Greg's setup without hardcoding it.
        if self._config.get(CONF_EMIT_EVENTS, DEFAULT_EMIT_EVENTS):
            self.hass.bus.async_fire(
                EVENT_LINE,
                {
                    "entry_id": self.entry.entry_id,
                    "message": spoken_text,
                    "line": line,
                    "category": pool_key,
                    "language": language,
                    "mood": self.mood,
                    "mood_level": self.mood_level,
                    "vibrations_today": self.vibrations_today,
                    "quiet_hours": self._is_quiet_time(),
                    "spoken": will_speak,
                    "media_player": player,
                    "tts_engine": tts_engine,
                    "volume": volume,
                },
            )

        if not will_speak:
            return

        # After the event, so an automation listening for greg_line still hears
        # about the line even when Greg himself cannot deliver it.
        problem = self._speaker_problem()
        if problem:
            self.speech_problem = problem
            _LOGGER.warning("Greg could not speak: %s", problem)
            self._notify()
            return
        self.speech_problem = None

        try:
            if suppress_chime:
                await self.hass.services.async_call(
                    "media_player", "volume_set",
                    {"entity_id": player, "volume_level": 0},
                    blocking=True,
                )
                await asyncio.sleep(0.3)
                await self.hass.services.async_call(
                    "media_player", "volume_set",
                    {"entity_id": player, "volume_level": volume},
                    blocking=True,
                )

            payload = {
                "entity_id": tts_engine,
                "media_player_entity_id": player,
                "message": spoken_text,
            }
            # Without this the engine speaks whatever language it defaults to,
            # which is how Dutch lines came out sounding like an English voice
            # reading Dutch letters aloud. Only sent when the engine has said it
            # understands it, because an unrecognised code is refused outright
            # and Greg says nothing at all.
            # Worked out before the language, because a voice names the
            # locale it speaks and is the better authority on which one to
            # ask for.
            #
            # The per-language voice wins, because a voice belongs to a
            # language. The bare tts_voice only applies to English: it predates
            # Greg speaking anything else, so anyone who set it set an English
            # voice, and letting it fall through to Dutch would quietly
            # recreate the exact bug this is fixing. Existing English setups
            # are untouched, every other language starts from the engine's own
            # default until given a voice of its own.
            voice = self._config.get(tts_voice_key(language)) or ""
            if not voice and language == FALLBACK_LANGUAGE:
                voice = self._config.get(CONF_TTS_VOICE, DEFAULT_TTS_VOICE)

            engine_language = self._engine_language(tts_engine, language, voice)
            if engine_language:
                payload["language"] = engine_language
            # Only sent when the user has actually named a voice. Engines that
            # take no voice option (Google Translate, for one) reject the key
            # outright, so an empty setting has to mean "say nothing about it".
            voice = self._engine_voice(tts_engine, engine_language, voice)
            if voice:
                payload["options"] = {"voice": voice}

            await self.hass.services.async_call(
                "tts", "speak", payload, blocking=False
            )
        except Exception as err:
            _LOGGER.error("Greg failed to speak: %s", err)
            self.speech_problem = f"The speaker refused the line: {err}"
            self._notify()

    # ---- the gate --------------------------------------------------------

    def _is_quiet_time(self) -> bool:
        if not self._config.get(CONF_QUIET_HOURS_ENABLED):
            return False
        try:
            start_str = self._config.get(CONF_QUIET_START, "22:00")
            end_str = self._config.get(CONF_QUIET_END, "08:00")
            start = time(*map(int, start_str.split(":")))
            end = time(*map(int, end_str.split(":")))
            now = datetime.now().time()
            if start > end:  # spans midnight
                return now >= start or now < end
            return start <= now < end
        except Exception:
            return False

    def _conditions(self) -> list[dict]:
        """The stored condition rows, cleaned.

        Read defensively rather than trusted: these come from a config entry an
        older version wrote, that an automation can write through
        greg.set_options, and that somebody can edit by hand.
        """
        return _clean_conditions(self._config.get(CONF_CONDITIONS))

    def _failing_condition(self) -> str | None:
        """The first condition row not currently met, described for a human.

        None means every row passes, which is also what an empty list gives, so
        anyone who has written no conditions is unaffected.
        """
        for row in self._conditions():
            entity_id = row["entity_id"]
            state_obj = self.hass.states.get(entity_id)

            # Missing, unavailable or unknown never blocks. See
            # CONDITION_SKIP_STATES for why this is the safe direction.
            if state_obj is None:
                _LOGGER.debug(
                    "Greg condition skipped, %s does not exist", entity_id
                )
                continue
            actual = state_obj.state
            if actual in CONDITION_SKIP_STATES:
                _LOGGER.debug(
                    "Greg condition skipped, %s is %s", entity_id, actual
                )
                continue

            matches = actual.casefold() == row["state"].casefold()
            if row["op"] == CONDITION_IS_NOT:
                matches = not matches
            if not matches:
                return f"{entity_id} is {actual}"
        return None

    def _speaker_problem(self) -> str | None:
        """Why the configured speaker cannot be spoken to, or None.

        This is a pre-flight rather than error handling, because tts.speak is
        called with blocking=False and never reports back. Everything here is a
        states lookup, so it costs nothing and cannot itself fail.
        """
        player = self._config.get(CONF_MEDIA_PLAYER)
        if not player:
            return "No speaker is set."

        state = self.hass.states.get(player)
        if state is None:
            return f"{player} does not exist any more."
        if state.state in SPEAKER_DEAD_STATES:
            return f"{player} is {state.state}."
        if state.attributes.get(ATTR_AUDIO_BLOCKED):
            return (
                f"{player} is not allowed to play audio yet. Open the page it "
                "runs on and tap it once."
            )
        return None

    def _is_blocked(self) -> bool:
        """The single gate in front of everything Greg does.

        Quiet hours and conditions block independently, so anyone who has set
        neither is never blocked and anyone who has set both gets the union.
        A blocked Greg reacts to nothing at all: no line, no tally, no mood
        movement, exactly as quiet hours has always behaved.
        """
        return self._is_quiet_time() or self._failing_condition() is not None

    @property
    def thresholds(self) -> tuple[int, int, int]:
        """Soft, medium and chaos, in an order Greg can actually climb.

        Normalised here rather than trusted, because the advanced dialog has
        always allowed any order and an install that crossed them years ago
        never passes back through the panel that now prevents it. Everything
        that reads a threshold reads this, so a crossed pair is impossible to
        act on rather than merely discouraged.
        """
        return normalise_thresholds(
            self._config.get(CONF_SOFT_THRESHOLD, DEFAULT_SOFT_THRESHOLD),
            self._config.get(CONF_MEDIUM_THRESHOLD, DEFAULT_MEDIUM_THRESHOLD),
            self._config.get(CONF_CHAOS_THRESHOLD, DEFAULT_CHAOS_THRESHOLD),
        )

    @property
    def language_options(self) -> dict:
        """What the panel offers in its language dropdown.

        Built from the lines package, so a new language file appears here on its
        own without anything else being told about it.
        """
        return {"": "Follow Home Assistant", **available_languages()}

    @property
    def language(self) -> str:
        """The language Greg is actually speaking.

        An empty setting means follow Home Assistant, which is what almost
        everybody wants. Anything Greg does not speak resolves to English.
        """
        configured = self._config.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
        return resolve_language(configured or self.hass.config.language)

    @property
    def is_quiet_now(self) -> bool:
        """Quiet hours specifically, not the gate as a whole.

        Kept meaning what it has always meant. The mood sensor publishes it as
        the quiet_hours attribute and people have automations reading that, so
        widening it to include conditions would quietly change what those see.
        """
        return self._is_quiet_time()

    @property
    def blocked_by(self) -> str | None:
        """Why Greg is staying quiet, or None when he is not.

        Published so the panel can say which condition is holding him rather
        than leaving someone to work out why a poke did nothing.
        """
        if self._is_quiet_time():
            return "quiet hours"
        return self._failing_condition()

    @property
    def is_blocked(self) -> bool:
        return self._is_blocked()

    @property
    def basic_config(self) -> dict:
        """The settings Greg's panel is allowed to show and change.

        Published as a state attribute because a custom panel can read entity
        states and nothing else. It has no route to the config entry.
        """
        cfg = self._config
        soft, medium, chaos = self.thresholds
        return {
            CONF_VIBRATION_SENSOR: cfg.get(CONF_VIBRATION_SENSOR),
            CONF_MEDIA_PLAYER: cfg.get(CONF_MEDIA_PLAYER),
            CONF_TTS_ENGINE: cfg.get(CONF_TTS_ENGINE),
            CONF_VOLUME: cfg.get(CONF_VOLUME, DEFAULT_VOLUME),
            CONF_SENSITIVITY: cfg.get(CONF_SENSITIVITY, DEFAULT_SENSITIVITY),
            CONF_QUIET_HOURS_ENABLED: cfg.get(CONF_QUIET_HOURS_ENABLED, True),
            CONF_QUIET_START: cfg.get(CONF_QUIET_START, DEFAULT_QUIET_START),
            CONF_QUIET_END: cfg.get(CONF_QUIET_END, DEFAULT_QUIET_END),
            # Cleaned rather than raw, so the panel renders what Greg will
            # actually act on rather than what happens to be stored.
            CONF_CONDITIONS: self._conditions(),
            # The configured value, which may be empty meaning follow Home
            # Assistant. The panel edits this. self.language is what that
            # resolves to, which is a different question and reported below.
            CONF_LANGUAGE: cfg.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
            # Normalised, so the ladder draws the thresholds Greg will act on.
            # An install that crossed them in the dialog years ago sees them
            # already sorted rather than seeing its own broken order drawn
            # back at it, and saving makes that permanent.
            CONF_SOFT_THRESHOLD: soft,
            CONF_MEDIUM_THRESHOLD: medium,
            CONF_CHAOS_THRESHOLD: chaos,
            # How far the ladder's track runs. Twelve taps normally, stretched
            # when an existing chaos sits above it, so nothing anybody set in
            # the dialog is quietly dragged down by a panel that cannot draw
            # it. Published rather than hardcoded in the panel so the two
            # cannot drift.
            "ladder_max": max(LADDER_TRACK_MAX, chaos),
            CONF_RESET_DELAY: clamp_timing(
                CONF_RESET_DELAY, cfg.get(CONF_RESET_DELAY, DEFAULT_RESET_DELAY)
            ),
            CONF_SILENCE_TIMEOUT: clamp_timing(
                CONF_SILENCE_TIMEOUT, cfg.get(CONF_SILENCE_TIMEOUT, DEFAULT_SILENCE_TIMEOUT)
            ),
            CONF_EXISTENTIAL_INTERVAL: clamp_timing(
                CONF_EXISTENTIAL_INTERVAL,
                cfg.get(CONF_EXISTENTIAL_INTERVAL, DEFAULT_EXISTENTIAL_INTERVAL),
            ),
        }
