"""Greg integration - a Marvin-inspired personality for your coffee table."""
from __future__ import annotations

import logging
import random
import asyncio
from datetime import datetime, time
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers import entity_registry as er
from datetime import timedelta

from .const import (
    DOMAIN,
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
    HELPER_VIBRATION_COUNTER,
    HELPER_MOOD,
    HELPER_MOOD_LEVEL,
    HELPER_LAST_EVENT,
    HELPER_QUIET_MODE,
    MOOD_ANNOYED,
    MOOD_JUDGING,
    MOOD_EXISTENTIAL,
    LINES_SOFT,
    LINES_MEDIUM,
    LINES_CHAOS,
    LINES_EXISTENTIAL,
    LINES_SILENCE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Greg from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = GregCoordinator(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = coordinator
    await coordinator.async_setup()

    entry.async_on_unload(entry.add_update_listener(coordinator.async_reload))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Greg."""
    coordinator = hass.data[DOMAIN].pop(entry.entry_id, None)
    if coordinator:
        await coordinator.async_unload()
    return True


class GregCoordinator:
    """Manages Greg's state, reactions, and TTS output."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._config = {**entry.data, **entry.options}
        self._counter = 0
        self._reset_handle = None
        self._silence_handle = None
        self._existential_handle = None
        self._unsub_sensor = None
        self._last_spoken = None
        self._last_lines_used: dict[str, str] = {}

    async def async_setup(self) -> None:
        """Set up helpers and listeners."""
        await self._ensure_helpers()

        sensor = self._config[CONF_VIBRATION_SENSOR]
        self._unsub_sensor = async_track_state_change_event(
            self.hass, [sensor], self._handle_vibration
        )

        interval = self._config.get(CONF_EXISTENTIAL_INTERVAL, 37)
        self._existential_handle = async_track_time_interval(
            self.hass,
            self._handle_existential,
            timedelta(minutes=interval),
        )

        _LOGGER.info("Greg is running. He is not pleased about it.")

    async def async_unload(self) -> None:
        """Clean up listeners."""
        if self._unsub_sensor:
            self._unsub_sensor()
        if self._existential_handle:
            self._existential_handle()
        if self._reset_handle:
            self._reset_handle()
        if self._silence_handle:
            self._silence_handle()

    async def async_reload(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Reload on options change."""
        self._config = {**entry.data, **entry.options}
        await self.async_unload()
        await self.async_setup()

    async def _ensure_helpers(self) -> None:
        """Create required helpers if they don't exist."""
        # Vibration counter
        if not self.hass.states.get(HELPER_VIBRATION_COUNTER):
            await self.hass.services.async_call(
                "input_number", "set_value",
                {"entity_id": HELPER_VIBRATION_COUNTER, "value": 0},
                blocking=False,
            )

        # Mood select
        if not self.hass.states.get(HELPER_MOOD):
            await self.hass.services.async_call(
                "input_select", "select_option",
                {"entity_id": HELPER_MOOD, "option": MOOD_ANNOYED},
                blocking=False,
            )

        # Quiet mode boolean
        if not self.hass.states.get(HELPER_QUIET_MODE):
            await self.hass.services.async_call(
                "input_boolean", "turn_off",
                {"entity_id": HELPER_QUIET_MODE},
                blocking=False,
            )

    @callback
    def _handle_vibration(self, event) -> None:
        """Handle vibration sensor trigger."""
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state not in ("on", "vibrating", "detected"):
            return

        if self._is_quiet_time():
            return

        self._counter += 1

        # Update helpers
        self.hass.async_create_task(self._update_helpers())

        # Cancel existing reset
        if self._reset_handle:
            self._reset_handle.cancel()

        # Cancel silence timer
        if self._silence_handle:
            self._silence_handle.cancel()

        # Schedule counter reset
        reset_delay = self._config.get(CONF_RESET_DELAY, 8)
        self._reset_handle = self.hass.loop.call_later(
            reset_delay, lambda: self.hass.async_create_task(self._reset_counter())
        )

        # React based on counter
        self.hass.async_create_task(self._react())

    async def _react(self) -> None:
        """Choose and speak the appropriate reaction."""
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
        """Reset vibration counter and start silence timer."""
        self._counter = 0
        await self._update_helpers()

        # Start silence countdown
        silence_mins = self._config.get(CONF_SILENCE_TIMEOUT, 20)
        self._silence_handle = self.hass.loop.call_later(
            silence_mins * 60,
            lambda: self.hass.async_create_task(self._handle_silence())
        )

    async def _handle_silence(self) -> None:
        """Speak silence mode line."""
        if self._is_quiet_time():
            return
        await self._speak(LINES_SILENCE, "silence")

    @callback
    def _handle_existential(self, now=None) -> None:
        """Periodic existential crisis."""
        if self._counter > 0 and not self._is_quiet_time():
            self.hass.async_create_task(self._speak(LINES_EXISTENTIAL, "existential"))

    async def _speak(self, pool: list, pool_key: str) -> None:
        """Pick a line and speak it, avoiding immediate repeats."""
        last = self._last_lines_used.get(pool_key)
        available = [l for l in pool if l != last]
        if not available:
            available = pool

        line = random.choice(available)
        self._last_lines_used[pool_key] = line

        player = self._config[CONF_MEDIA_PLAYER]
        volume = self._config.get(CONF_VOLUME, 0.35)
        suppress_chime = self._config.get(CONF_SUPPRESS_CHIME, True)

        try:
            # Attempt chime suppression by briefly setting volume to 0 then back
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

            # Update last event
            await self.hass.services.async_call(
                "input_text", "set_value",
                {"entity_id": HELPER_LAST_EVENT, "value": str(datetime.now())},
                blocking=False,
            )

        except Exception as err:
            _LOGGER.error("Greg failed to speak: %s", err)

    async def _update_helpers(self) -> None:
        """Sync helper states with internal counter."""
        try:
            await self.hass.services.async_call(
                "input_number", "set_value",
                {"entity_id": HELPER_VIBRATION_COUNTER, "value": self._counter},
                blocking=False,
            )

            # Update mood
            soft = self._config.get(CONF_SOFT_THRESHOLD, 1)
            medium = self._config.get(CONF_MEDIUM_THRESHOLD, 3)
            chaos = self._config.get(CONF_CHAOS_THRESHOLD, 6)

            if self._counter >= chaos:
                mood = MOOD_EXISTENTIAL
                mood_level = 100
            elif self._counter >= medium:
                mood = MOOD_JUDGING
                mood_level = 50 + int((self._counter / chaos) * 50)
            else:
                mood = MOOD_ANNOYED
                mood_level = int((self._counter / medium) * 50)

            await self.hass.services.async_call(
                "input_select", "select_option",
                {"entity_id": HELPER_MOOD, "option": mood},
                blocking=False,
            )

            await self.hass.services.async_call(
                "input_number", "set_value",
                {"entity_id": HELPER_MOOD_LEVEL, "value": mood_level},
                blocking=False,
            )

        except Exception as err:
            _LOGGER.error("Greg helper update failed: %s", err)

    def _is_quiet_time(self) -> bool:
        """Check if current time falls in quiet hours."""
        if not self._config.get(CONF_QUIET_HOURS_ENABLED):
            return False

        # Also check the manual quiet mode toggle
        quiet_state = self.hass.states.get(HELPER_QUIET_MODE)
        if quiet_state and quiet_state.state == "on":
            return True

        try:
            start_str = self._config.get(CONF_QUIET_START, "22:00")
            end_str = self._config.get(CONF_QUIET_END, "08:00")
            start = time(*map(int, start_str.split(":")))
            end = time(*map(int, end_str.split(":")))
            now = datetime.now().time()

            if start > end:  # Spans midnight
                return now >= start or now < end
            return start <= now < end

        except Exception:
            return False
