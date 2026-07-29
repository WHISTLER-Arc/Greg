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
    DEFAULT_SENSITIVITY,
    DEFAULT_VOLUME,
    DEFAULT_EMIT_EVENTS,
    DEFAULT_SPEECH_MODE,
    SPEECH_MODE_EVENT_ONLY,
    SENSITIVITY_MAX_DEBOUNCE,
    EVENT_LINE,
    MOOD_RESTING,
    MOOD_ANNOYED,
    MOOD_JUDGING,
    MOOD_EXISTENTIAL,
    MOOD_IMAGES,
    SERVICE_POKE,
    SERVICE_UNINSTALL,
    WWW_ASSET_DIR,
    LINES_SOFT,
    LINES_MEDIUM,
    LINES_CHAOS,
    LINES_EXISTENTIAL,
    LINES_SILENCE,
    PANEL_URL_PATH,
    PANEL_TITLE,
    PANEL_ICON,
    PANEL_STATIC_URL_BASE,
    PANEL_JS_URL,
    PANEL_DATA_KEY,
    IMG_STATIC_URL_BASE,
)

_LOGGER = logging.getLogger(__name__)

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
        for service in (SERVICE_POKE, SERVICE_UNINSTALL):
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

    hass.services.async_register(DOMAIN, SERVICE_POKE, _handle_poke)
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
        # Timers / listeners
        self._reset_handle = None
        self._silence_handle = None
        self._existential_handle = None
        self._unsub_sensor = None
        self._unsub_midnight = None
        self._decks: dict[str, list] = {}
        self._deck_pos: dict[str, int] = {}
        # Monotonic timestamp of the last sensor event Greg actually accepted.
        self._last_accepted: float | None = None

    # ---- lifecycle -------------------------------------------------------

    async def async_setup(self) -> None:
        sensor = self._config[CONF_VIBRATION_SENSOR]
        self._unsub_sensor = async_track_state_change_event(
            self.hass, [sensor], self._handle_vibration
        )

        interval = self._config.get(CONF_EXISTENTIAL_INTERVAL, 37)
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
        self._config = {**entry.data, **entry.options}
        await self.async_unload()
        await self.async_setup()

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
        if not self.enabled or self._is_quiet_time():
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

        reset_delay = self._config.get(CONF_RESET_DELAY, 8)
        self._reset_handle = self.hass.loop.call_later(
            reset_delay, lambda: self.hass.async_create_task(self._reset_counter())
        )

        self._update_mood()
        self.hass.async_create_task(self._react())

    async def async_poke(self) -> None:
        """Force a reaction regardless of sensor (greg.poke service / panel button)."""
        if not self.enabled or self._is_quiet_time():
            return
        self._counter += 1
        self.vibrations_today += 1
        self._update_mood()
        await self._react()

    async def _react(self) -> None:
        soft = self._config.get(CONF_SOFT_THRESHOLD, 1)
        medium = self._config.get(CONF_MEDIUM_THRESHOLD, 3)
        chaos = self._config.get(CONF_CHAOS_THRESHOLD, 6)

        if self._counter >= chaos:
            await self._speak(LINES_CHAOS, "chaos")
        elif self._counter >= medium:
            await self._speak(LINES_MEDIUM, "medium")
        elif self._counter >= soft:
            await self._speak(LINES_SOFT, "soft")

    async def _reset_counter(self) -> None:
        self._counter = 0
        self._update_mood()
        silence_mins = self._config.get(CONF_SILENCE_TIMEOUT, 20)
        self._silence_handle = self.hass.loop.call_later(
            silence_mins * 60,
            lambda: self.hass.async_create_task(self._handle_silence()),
        )

    async def _handle_silence(self) -> None:
        if not self.enabled or self._is_quiet_time():
            return
        await self._speak(LINES_SILENCE, "silence")

    @callback
    def _handle_existential(self, now=None) -> None:
        if self._counter > 0 and self.enabled and not self._is_quiet_time():
            self.hass.async_create_task(
                self._speak(LINES_EXISTENTIAL, "existential")
            )

    @callback
    def _reset_daily_tally(self, now=None) -> None:
        self.vibrations_today = 0
        self._notify()

    # ---- mood + speech ---------------------------------------------------

    @callback
    def _update_mood(self) -> None:
        """Compute mood + level from the session counter and notify entities."""
        medium = self._config.get(CONF_MEDIUM_THRESHOLD, 3)
        chaos = self._config.get(CONF_CHAOS_THRESHOLD, 6)
        soft = self._config.get(CONF_SOFT_THRESHOLD, 1)

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

    def _next_line(self, pool: list, pool_key: str) -> str:
        """Return the next line from the shuffled deck for this pool.

        Plays every line before repeating any. On reshuffle, guards the boundary
        so the last line of one cycle cannot be the first of the next.
        """
        deck = self._decks.get(pool_key, [])
        pos = self._deck_pos.get(pool_key, 0)

        if pos >= len(deck):
            last_line = deck[pos - 1] if deck else None
            new_deck = list(pool)
            random.shuffle(new_deck)
            if last_line is not None and new_deck[0] == last_line and len(new_deck) > 1:
                swap_idx = random.randrange(1, len(new_deck))
                new_deck[0], new_deck[swap_idx] = new_deck[swap_idx], new_deck[0]
            self._decks[pool_key] = new_deck
            self._deck_pos[pool_key] = 0
            deck = new_deck
            pos = 0

        self._deck_pos[pool_key] = pos + 1
        return deck[pos]

    async def _speak(self, pool: list, pool_key: str) -> None:
        line = self._next_line(pool, pool_key)

        self.last_line = line
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
                    "message": line,
                    "category": pool_key,
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

            await self.hass.services.async_call(
                "tts", "speak",
                {
                    "entity_id": tts_engine,
                    "media_player_entity_id": player,
                    "message": line,
                },
                blocking=False,
            )
        except Exception as err:
            _LOGGER.error("Greg failed to speak: %s", err)

    # ---- quiet hours -----------------------------------------------------

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

    @property
    def is_quiet_now(self) -> bool:
        return self._is_quiet_time()
