"""Greg sensor entities — mood, level, last line, daily tally."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, MOOD_IMAGES, IMG_STATIC_URL_BASE, VERSION_DISPLAY
from . import SIGNAL_STATE_UPDATED, GregCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    coordinator: GregCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            GregMoodSensor(coordinator, entry),
            GregMoodLevelSensor(coordinator, entry),
            GregLastLineSensor(coordinator, entry),
            GregVibrationsTodaySensor(coordinator, entry),
        ]
    )


class _GregBase(SensorEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, coordinator: GregCoordinator, entry: ConfigEntry) -> None:
        self.coordinator = coordinator
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="Greg",
            manufacturer="WHISTLER & Arc",
            model="Sentient Coffee Table",
            sw_version=VERSION_DISPLAY,
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_STATE_UPDATED, self._handle_update
            )
        )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()


class GregMoodSensor(_GregBase):
    _attr_icon = "mdi:emoticon-sad-outline"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_mood"
        self._attr_name = "Mood"

    @property
    def native_value(self):
        return self.coordinator.mood

    @property
    def extra_state_attributes(self):
        mood = self.coordinator.mood
        return {
            "image": f"{IMG_STATIC_URL_BASE}/{MOOD_IMAGES.get(mood)}",
            "image_file": MOOD_IMAGES.get(mood),
            "quiet_hours": self.coordinator.is_quiet_now,
            "enabled": self.coordinator.enabled,
        }


class GregMoodLevelSensor(_GregBase):
    _attr_icon = "mdi:gauge"
    _attr_native_unit_of_measurement = "%"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_mood_level"
        self._attr_name = "Mood level"

    @property
    def native_value(self):
        return self.coordinator.mood_level


class GregLastLineSensor(_GregBase):
    _attr_icon = "mdi:comment-quote-outline"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_last_line"
        self._attr_name = "Last line"

    @property
    def native_value(self):
        # Sensor state values cap at 255 chars; some lines exceed that.
        line = self.coordinator.last_line
        return (line[:252] + "...") if len(line) > 255 else line

    @property
    def extra_state_attributes(self):
        return {"full_line": self.coordinator.last_line}


class GregVibrationsTodaySensor(_GregBase):
    _attr_icon = "mdi:counter"
    _attr_native_unit_of_measurement = "events"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_vibrations_today"
        self._attr_name = "Disturbances today"

    @property
    def native_value(self):
        return self.coordinator.vibrations_today
