"""Greg switch entity — master on/off."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, VERSION_DISPLAY
from . import SIGNAL_STATE_UPDATED, GregCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    coordinator: GregCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GregEnabledSwitch(coordinator, entry)])


class GregEnabledSwitch(SwitchEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_icon = "mdi:robot-outline"

    def __init__(self, coordinator: GregCoordinator, entry: ConfigEntry) -> None:
        self.coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_enabled"
        self._attr_name = "Enabled"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="Greg",
            manufacturer="WHISTLER & Arc",
            model="Sentient Coffee Table",
            sw_version=VERSION_DISPLAY,
        )

    @property
    def is_on(self) -> bool:
        return self.coordinator.enabled

    async def async_turn_on(self, **kwargs) -> None:
        self.coordinator.set_enabled(True)

    async def async_turn_off(self, **kwargs) -> None:
        self.coordinator.set_enabled(False)

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_STATE_UPDATED, self._handle_update
            )
        )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()
