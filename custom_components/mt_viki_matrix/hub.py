"""Async HTTP client for the MT-VIKI HDMI matrix's built-in web control API.

Despite the manual documenting a plain-text RS232/TCP protocol, the L-series
units (MT-HD44L / MT-HD88L / MT-HD1616L) actually expose control through a
tiny HTTP CGI endpoint used by their web GUI:

    POST http://<ip>/cgi-bin/matrixs.cgi
    Authorization: Basic YWRtaW46YWRtaW4=   (fixed admin:admin, baked into firmware)
    Content-Type: application/x-www-form-urlencoded
    Body: matrixdata={"COMMAND": "SW <input> <output> "}

This was confirmed against a working community Home Assistant integration
for the MT-HD88L (github.com/Timman70/MT-VIKI-MT-HD88L-Matrix-Switch).
There is no known query/status endpoint, so state in Home Assistant is
optimistic only.
"""
from __future__ import annotations

import json
import logging

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

# Fixed by the device firmware — the web GUI always authenticates as
# admin/admin regardless of what you've set on the device itself.
_AUTH_HEADER = "Basic YWRtaW46YWRtaW4="
_TIMEOUT = aiohttp.ClientTimeout(total=5)


class MatrixConnectionError(Exception):
    """Raised when the matrix's HTTP endpoint can't be reached."""


class MtVikiMatrixHub:
    """Talks to one matrix's cgi-bin HTTP control endpoint."""

    def __init__(self, hass: HomeAssistant, host: str) -> None:
        self._session = async_get_clientsession(hass)
        self._host = host

    @property
    def host(self) -> str:
        return self._host

    def _url(self) -> str:
        return f"http://{self._host}/cgi-bin/matrixs.cgi"

    async def _post_command(self, command: str) -> str:
        payload = {"COMMAND": command}
        data = {"matrixdata": json.dumps(payload)}
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": _AUTH_HEADER,
        }
        try:
            async with self._session.post(
                self._url(), data=data, headers=headers, timeout=_TIMEOUT
            ) as resp:
                text = await resp.text()
                _LOGGER.debug(
                    "Sent %r -> HTTP %s: %s", command, resp.status, text
                )
                return text
        except (aiohttp.ClientError, TimeoutError) as err:
            raise MatrixConnectionError(
                f"Could not reach matrix at {self._host}: {err}"
            ) from err

    async def async_switch(self, input_ch: int, output_ch: int) -> None:
        """Route one input to one output."""
        await self._post_command(f"SW {input_ch} {output_ch} ")

    async def async_test_connection(self) -> bool:
        """Used by the config flow. Does a lightweight reachability check
        (not a real switch command) so setup doesn't accidentally rewire
        anything before the user has configured inputs/outputs."""
        try:
            async with self._session.get(
                f"http://{self._host}/", timeout=_TIMEOUT
            ) as resp:
                # Any HTTP response at all means something is listening
                # and speaking HTTP on this host.
                return resp.status < 500
        except (aiohttp.ClientError, TimeoutError):
            return False
