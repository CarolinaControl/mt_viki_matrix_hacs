"""Async TCP client for the MT-VIKI HDMI matrix control protocol.

The matrix accepts plain-text ASCII commands terminated with '.' over a
raw TCP socket (default port 8080) — the same command set used on its
RS232 port. A successful switch reply is typically "OK" (or the switch
just echoes/ack's silently on some firmware); a failure is "ERR".

This client keeps one persistent connection open, serializes writes with
a lock (so responses can't get interleaved), and reconnects automatically
if the socket drops.
"""
from __future__ import annotations

import asyncio
import logging

from .const import CMD_TERMINATOR, SOCKET_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class MatrixConnectionError(Exception):
    """Raised when the matrix can't be reached."""


class MtVikiMatrixHub:
    """Manages the TCP connection to one HDMI matrix."""

    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()

    @property
    def host(self) -> str:
        return self._host

    async def async_connect(self) -> None:
        """Open (or re-open) the TCP connection."""
        async with self._lock:
            await self._connect_locked()

    async def _connect_locked(self) -> None:
        if self._writer is not None and not self._writer.is_closing():
            return
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port),
                timeout=SOCKET_TIMEOUT,
            )
        except (OSError, asyncio.TimeoutError) as err:
            self._reader = None
            self._writer = None
            raise MatrixConnectionError(
                f"Could not connect to matrix at {self._host}:{self._port}"
            ) from err

    async def async_close(self) -> None:
        """Close the TCP connection."""
        async with self._lock:
            if self._writer is not None:
                self._writer.close()
                try:
                    await self._writer.wait_closed()
                except OSError:
                    pass
            self._reader = None
            self._writer = None

    async def async_test_connection(self) -> bool:
        """Used by the config flow to validate host/port before setup."""
        try:
            await self.async_connect()
        except MatrixConnectionError:
            return False
        return True

    async def async_send_command(self, command: str) -> str:
        """Send a raw protocol command (without trailing '.') and return the reply.

        Commands and replies in this protocol are short, so we read until
        a newline or the socket goes idle for SOCKET_TIMEOUT — whichever
        comes first. Some firmware doesn't reply to every command, so a
        timeout on read is treated as "no reply" rather than an error.
        """
        if not command.endswith(CMD_TERMINATOR):
            command += CMD_TERMINATOR

        async with self._lock:
            for attempt in (1, 2):
                try:
                    await self._connect_locked()
                    assert self._writer is not None
                    assert self._reader is not None

                    _LOGGER.debug("Sending to %s: %s", self._host, command)
                    self._writer.write(command.encode("ascii"))
                    await self._writer.drain()

                    try:
                        raw = await asyncio.wait_for(
                            self._reader.readline(), timeout=SOCKET_TIMEOUT
                        )
                        reply = raw.decode("ascii", errors="ignore").strip()
                        _LOGGER.debug("Reply from %s: %s", self._host, reply)
                        return reply
                    except asyncio.TimeoutError:
                        return ""

                except (OSError, MatrixConnectionError) as err:
                    _LOGGER.warning(
                        "Matrix command failed (attempt %s): %s", attempt, err
                    )
                    self._writer = None
                    self._reader = None
                    if attempt == 2:
                        raise MatrixConnectionError(str(err)) from err
                    await asyncio.sleep(0.5)

        return ""
