"""Greg integration - a Marvin-inspired personality for your coffee table."""
from __future__ import annotations

import logging
import os
import random
import asyncio
import shutil
from datetime import datetime, time, timedelta

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
    CONF_SUPPRESS_CHIME,
    MOOD_RESTING,
    MOOD_ANNOYED,
    MOOD_JUDGING,
    MOOD_EXISTENTIAL,
    MOOD_IMAGES,
    SERVICE_POKE,
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
        if hass.services.has_service(DOMAIN, SERVICE_POKE):
            hass.services.async_remove(DOMAIN, SERVICE_POKE)

    return unload_ok


@callback
def _async_register_services(hass: HomeAssistant) -> None:
    """Register the greg.poke service once."""
    if hass.services.has_service(DOMAIN, SERVICE_POKE):
        return

    async def _handle_poke(call) -> None:
        """Force Greg to react on demand."""
        for coordinator in hass.data.get(DOMAIN, {}).values():
            if isinstance(coordinator, GregCoordinator):
                await coordinator.async_poke()

    hass.services.async_register(DOMAIN, SERVICE_POKE, _handle_poke)


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
        self._last_lines_used: dict[str, str] = {}

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

    @callback
    def _handle_vibration(self, event) -> None:
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state not in ("on", "vibrating", "detected"):
            return
        if not self.enabled or self._is_quiet_time():
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

    async def _speak(self, pool: list, pool_key: str) -> None:
        last = self._last_lines_used.get(pool_key)
        available = [l for l in pool if l != last] or pool
        line = random.choice(available)
        self._last_lines_used[pool_key] = line

        self.last_line = line
        self._notify()

        player = self._config[CONF_MEDIA_PLAYER]
        volume = self._config.get(CONF_VOLUME, 0.35)
        suppress_chime = self._config.get(CONF_SUPPRESS_CHIME, True)

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
                    "entity_id": self._config.get(CONF_TTS_ENGINE, "tts.google_en_com"),
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
