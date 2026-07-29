"""Config flow for Greg integration."""
from __future__ import annotations

import re
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

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
    CONF_SENSITIVITY,
    CONF_SUPPRESS_CHIME,
    DEFAULT_VOLUME,
    DEFAULT_QUIET_START,
    DEFAULT_QUIET_END,
    DEFAULT_SOFT_THRESHOLD,
    DEFAULT_MEDIUM_THRESHOLD,
    DEFAULT_CHAOS_THRESHOLD,
    DEFAULT_RESET_DELAY,
    DEFAULT_SILENCE_TIMEOUT,
    DEFAULT_EXISTENTIAL_INTERVAL,
    DEFAULT_SENSITIVITY,
    DEFAULT_SUPPRESS_CHIME,
    VERSION_DISPLAY,
)

TIME_PATTERN = re.compile(r"^\d{2}:\d{2}$")


def _validate_time(value: str) -> str:
    if not TIME_PATTERN.match(value):
        raise vol.Invalid("invalid_time")
    return value


class GregConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the Greg setup flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict = {}
        self._show_advanced: bool = False

    async def async_step_user(self, user_input=None):
        """Simple setup step — sensor, speaker, volume, quiet hours."""
        errors = {}

        if user_input is not None:
            # Validate volume
            volume = user_input.get(CONF_VOLUME, DEFAULT_VOLUME)
            if not (0.0 <= volume <= 1.0):
                errors[CONF_VOLUME] = "invalid_volume"

            # Validate quiet hours times if enabled
            if user_input.get(CONF_QUIET_HOURS_ENABLED):
                for key in (CONF_QUIET_START, CONF_QUIET_END):
                    val = user_input.get(key, "")
                    if not TIME_PATTERN.match(val):
                        errors[key] = "invalid_time"

            if not errors:
                self._data.update(user_input)
                # Apply defaults for advanced settings not shown here
                self._data.setdefault(CONF_SOFT_THRESHOLD, DEFAULT_SOFT_THRESHOLD)
                self._data.setdefault(CONF_MEDIUM_THRESHOLD, DEFAULT_MEDIUM_THRESHOLD)
                self._data.setdefault(CONF_CHAOS_THRESHOLD, DEFAULT_CHAOS_THRESHOLD)
                self._data.setdefault(CONF_RESET_DELAY, DEFAULT_RESET_DELAY)
                self._data.setdefault(CONF_SILENCE_TIMEOUT, DEFAULT_SILENCE_TIMEOUT)
                self._data.setdefault(CONF_EXISTENTIAL_INTERVAL, DEFAULT_EXISTENTIAL_INTERVAL)
                self._data.setdefault(CONF_SENSITIVITY, DEFAULT_SENSITIVITY)
                self._data.setdefault(CONF_SUPPRESS_CHIME, DEFAULT_SUPPRESS_CHIME)

                if user_input.get("show_advanced"):
                    return await self.async_step_advanced()

                return self.async_create_entry(
                    title=f"Greg {VERSION_DISPLAY}",
                    data=self._data,
                )

        schema = vol.Schema({
            vol.Required(CONF_VIBRATION_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="binary_sensor")
            ),
            vol.Required(CONF_MEDIA_PLAYER): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="media_player")
            ),
            vol.Required(CONF_TTS_ENGINE): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="tts")
            ),
            vol.Optional(CONF_VOLUME, default=DEFAULT_VOLUME): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0.0, max=1.0, step=0.05, mode="slider")
            ),
            vol.Optional(CONF_QUIET_HOURS_ENABLED, default=True): selector.BooleanSelector(),
            vol.Optional(CONF_QUIET_START, default=DEFAULT_QUIET_START): selector.TextSelector(),
            vol.Optional(CONF_QUIET_END, default=DEFAULT_QUIET_END): selector.TextSelector(),
            vol.Optional("show_advanced", default=False): selector.BooleanSelector(),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_advanced(self, user_input=None):
        """Advanced settings step."""
        errors = {}

        if user_input is not None:
            if not errors:
                self._data.update(user_input)
                return self.async_create_entry(
                    title=f"Greg {VERSION_DISPLAY}",
                    data=self._data,
                )

        schema = vol.Schema({
            vol.Optional(CONF_SOFT_THRESHOLD, default=DEFAULT_SOFT_THRESHOLD): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=10, step=1, mode="slider")
            ),
            vol.Optional(CONF_MEDIUM_THRESHOLD, default=DEFAULT_MEDIUM_THRESHOLD): selector.NumberSelector(
                selector.NumberSelectorConfig(min=2, max=15, step=1, mode="slider")
            ),
            vol.Optional(CONF_CHAOS_THRESHOLD, default=DEFAULT_CHAOS_THRESHOLD): selector.NumberSelector(
                selector.NumberSelectorConfig(min=3, max=20, step=1, mode="slider")
            ),
            vol.Optional(CONF_RESET_DELAY, default=DEFAULT_RESET_DELAY): selector.NumberSelector(
                selector.NumberSelectorConfig(min=2, max=30, step=1, mode="slider")
            ),
            vol.Optional(CONF_SILENCE_TIMEOUT, default=DEFAULT_SILENCE_TIMEOUT): selector.NumberSelector(
                selector.NumberSelectorConfig(min=5, max=60, step=5, mode="slider")
            ),
            vol.Optional(CONF_EXISTENTIAL_INTERVAL, default=DEFAULT_EXISTENTIAL_INTERVAL): selector.NumberSelector(
                selector.NumberSelectorConfig(min=10, max=120, step=1, mode="slider")
            ),
            vol.Optional(CONF_SENSITIVITY, default=DEFAULT_SENSITIVITY): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=100, step=1, mode="slider")
            ),
            vol.Optional(CONF_SUPPRESS_CHIME, default=DEFAULT_SUPPRESS_CHIME): selector.BooleanSelector(),
        })

        return self.async_show_form(
            step_id="advanced",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return GregOptionsFlow(config_entry)


class GregOptionsFlow(config_entries.OptionsFlow):
    """Handle Greg options (post-setup settings)."""

    def __init__(self, config_entry) -> None:
        self._entry = config_entry
        self._data: dict = {}

    def _get(self, key, default):
        """Return current value: options override data, both override default."""
        return self._entry.options.get(key, self._entry.data.get(key, default))

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            show_advanced = user_input.pop("show_advanced", False)
            self._data = user_input
            if show_advanced:
                return await self.async_step_advanced()
            return self.async_create_entry(title="", data=self._data)

        schema = vol.Schema({
            vol.Required(CONF_VIBRATION_SENSOR, default=self._get(CONF_VIBRATION_SENSOR, "")): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="binary_sensor")
            ),
            vol.Required(CONF_MEDIA_PLAYER, default=self._get(CONF_MEDIA_PLAYER, "")): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="media_player")
            ),
            vol.Required(CONF_TTS_ENGINE, default=self._get(CONF_TTS_ENGINE, "")): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="tts")
            ),
            vol.Optional(CONF_VOLUME, default=self._get(CONF_VOLUME, DEFAULT_VOLUME)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0.0, max=1.0, step=0.05, mode="slider")
            ),
            vol.Optional(CONF_QUIET_HOURS_ENABLED, default=self._get(CONF_QUIET_HOURS_ENABLED, True)): selector.BooleanSelector(),
            vol.Optional(CONF_QUIET_START, default=self._get(CONF_QUIET_START, DEFAULT_QUIET_START)): selector.TextSelector(),
            vol.Optional(CONF_QUIET_END, default=self._get(CONF_QUIET_END, DEFAULT_QUIET_END)): selector.TextSelector(),
            vol.Optional("show_advanced", default=False): selector.BooleanSelector(),
        })

        return self.async_show_form(step_id="init", data_schema=schema)

    async def async_step_advanced(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(title="", data=self._data)

        schema = vol.Schema({
            vol.Optional(CONF_SOFT_THRESHOLD, default=self._get(CONF_SOFT_THRESHOLD, DEFAULT_SOFT_THRESHOLD)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=10, step=1, mode="slider")
            ),
            vol.Optional(CONF_MEDIUM_THRESHOLD, default=self._get(CONF_MEDIUM_THRESHOLD, DEFAULT_MEDIUM_THRESHOLD)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=2, max=15, step=1, mode="slider")
            ),
            vol.Optional(CONF_CHAOS_THRESHOLD, default=self._get(CONF_CHAOS_THRESHOLD, DEFAULT_CHAOS_THRESHOLD)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=3, max=20, step=1, mode="slider")
            ),
            vol.Optional(CONF_RESET_DELAY, default=self._get(CONF_RESET_DELAY, DEFAULT_RESET_DELAY)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=2, max=30, step=1, mode="slider")
            ),
            vol.Optional(CONF_SILENCE_TIMEOUT, default=self._get(CONF_SILENCE_TIMEOUT, DEFAULT_SILENCE_TIMEOUT)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=5, max=60, step=5, mode="slider")
            ),
            vol.Optional(CONF_EXISTENTIAL_INTERVAL, default=self._get(CONF_EXISTENTIAL_INTERVAL, DEFAULT_EXISTENTIAL_INTERVAL)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=10, max=120, step=1, mode="slider")
            ),
            vol.Optional(CONF_SENSITIVITY, default=self._get(CONF_SENSITIVITY, DEFAULT_SENSITIVITY)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=100, step=1, mode="slider")
            ),
            vol.Optional(CONF_SUPPRESS_CHIME, default=self._get(CONF_SUPPRESS_CHIME, DEFAULT_SUPPRESS_CHIME)): selector.BooleanSelector(),
        })

        return self.async_show_form(step_id="advanced", data_schema=schema)
