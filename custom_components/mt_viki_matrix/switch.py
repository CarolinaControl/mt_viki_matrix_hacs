"""Buzzer on/off switch for the MT-VIKI HDMI Matrix."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CMD_BEEP_OFF, CMD_BEEP_ON, DOMAIN
from .hub import MtVikiMatrixHub


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the buzzer switch."""
    hub: MtVikiMatrixHub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MtVikiMatrixBuzzer(hub, entry.entry_id, entry.data[CONF_NAME])])


class MtVikiMatrixBuzzer(SwitchEntity):
    """Controls the matrix's audible switch-confirmation beep.

    This is optimistic: the protocol has no query command for buzzer
    state, so the switch simply reflects the last command it sent.
    """

    _attr_has_entity_name = True
    _attr_name = "Buzzer"
    _attr_should_poll = False

    def __init__(self, hub: MtVikiMatrixHub, entry_id: str, matrix_name: str) -> None:
        self._hub = hub
        self._attr_unique_id = f"{entry_id}_buzzer"
        self._attr_is_on = True
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=matrix_name,
            manufacturer="MT-VIKI",
            model="HDMI Matrix",
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._hub.async_send_command(CMD_BEEP_ON)
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._hub.async_send_command(CMD_BEEP_OFF)
        self._attr_is_on = False
        self.async_write_ha_state()
