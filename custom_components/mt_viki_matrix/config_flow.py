"""Config flow for the MT-VIKI HDMI Matrix integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_INPUTS, CONF_OUTPUTS, DEFAULT_NAME, DOMAIN
from .hub import MtVikiMatrixHub

# Matrices in this family ship as 4x4, 8x8 or 16x16, but let the user pick
# any size in case of an asymmetric or custom-ordered unit.
SIZE_PRESETS = {
    "4x4": (4, 4),
    "8x8": (8, 8),
    "16x16": (16, 16),
    "custom": None,
}

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Required(CONF_HOST): str,
        vol.Required("size", default="8x8"): vol.In(list(SIZE_PRESETS)),
    }
)


async def _validate_host(hass: HomeAssistant, host: str) -> None:
    hub = MtVikiMatrixHub(hass, host)
    if not await hub.async_test_connection():
        raise CannotConnect


class MtVikiMatrixConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MT-VIKI HDMI Matrix."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await _validate_host(self.hass, user_input[CONF_HOST])
            except CannotConnect:
                errors["base"] = "cannot_connect"
            else:
                self._data = user_input
                if SIZE_PRESETS[user_input["size"]] is not None:
                    inputs, outputs = SIZE_PRESETS[user_input["size"]]
                    self._data[CONF_INPUTS] = inputs
                    self._data[CONF_OUTPUTS] = outputs
                    return self._create_entry()
                return await self.async_step_custom_size()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )

    async def async_step_custom_size(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        schema = vol.Schema(
            {
                vol.Required(CONF_INPUTS, default=8): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=32)
                ),
                vol.Required(CONF_OUTPUTS, default=8): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=32)
                ),
            }
        )
        if user_input is not None:
            self._data[CONF_INPUTS] = user_input[CONF_INPUTS]
            self._data[CONF_OUTPUTS] = user_input[CONF_OUTPUTS]
            return self._create_entry()

        return self.async_show_form(
            step_id="custom_size", data_schema=schema, errors=errors
        )

    def _create_entry(self) -> FlowResult:
        return self.async_create_entry(title=self._data[CONF_NAME], data=self._data)


class CannotConnect(Exception):
    """Error to indicate we cannot connect to the matrix."""
