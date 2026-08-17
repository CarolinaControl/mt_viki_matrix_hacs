"""Media player entities for the MT-VIKI HDMI Matrix — one per output."""
from __future__ import annotations

import logging

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CMD_CLOSE_OUTPUT,
    CMD_SWITCH,
    CONF_INPUTS,
    CONF_OUTPUTS,
    DOMAIN,
)
from .hub import MtVikiMatrixHub

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up one media_player entity per matrix output."""
    hub: MtVikiMatrixHub = hass.data[DOMAIN][entry.entry_id]
    num_inputs = entry.data[CONF_INPUTS]
    num_outputs = entry.data[CONF_OUTPUTS]
    matrix_name = entry.data[CONF_NAME]

    sources = [f"Input {i}" for i in range(1, num_inputs + 1)]

    entities = [
        MtVikiMatrixOutput(hub, entry.entry_id, matrix_name, output, sources)
        for output in range(1, num_outputs + 1)
    ]
    async_add_entities(entities)


class MtVikiMatrixOutput(MediaPlayerEntity):
    """One matrix output, represented as a media_player with source select."""

    _attr_has_entity_name = True
    _attr_supported_features = (
        MediaPlayerEntityFeature.SELECT_SOURCE
        | MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
    )
    _attr_should_poll = False

    def __init__(
        self,
        hub: MtVikiMatrixHub,
        entry_id: str,
        matrix_name: str,
        output_num: int,
        sources: list[str],
    ) -> None:
        self._hub = hub
        self._output_num = output_num
        self._attr_name = f"Output {output_num}"
        self._attr_unique_id = f"{entry_id}_output_{output_num}"
        self._attr_source_list = sources
        self._attr_source = None
        self._attr_state = MediaPlayerState.OFF
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=matrix_name,
            manufacturer="MT-VIKI",
            model="HDMI Matrix",
        )

    async def async_select_source(self, source: str) -> None:
        """Route the chosen input to this output."""
        try:
            input_num = int(source.removeprefix("Input ").strip())
        except ValueError:
            _LOGGER.error("Unknown source '%s'", source)
            return

        command = CMD_SWITCH.format(inp=input_num, out=self._output_num)
        await self._hub.async_send_command(command)

        self._attr_source = source
        self._attr_state = MediaPlayerState.ON
        self.async_write_ha_state()

    async def async_turn_off(self) -> None:
        """Blank this output."""
        command = CMD_CLOSE_OUTPUT.format(out=self._output_num)
        await self._hub.async_send_command(command)
        self._attr_state = MediaPlayerState.OFF
        self.async_write_ha_state()

    async def async_turn_on(self) -> None:
        """Restore the last-selected source on this output, if known."""
        if self._attr_source is not None:
            await self.async_select_source(self._attr_source)
        else:
            self._attr_state = MediaPlayerState.ON
            self.async_write_ha_state()
