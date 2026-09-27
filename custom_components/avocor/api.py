"""Async TCP client for Avocor Interactive Displays.

Implements the "TCP/IP Control Configuration" protocol documented in the
AVE-5530 User Manual (External Control chapter): a persistent TCP connection
on the display's control port (the manual documents 4664, but shipping units
default to 4884), exchanging fixed-format frames:

    [STX] [IDT] [TYPE] [CMD] [VALUE/REPLY] [ETX]

STX (0x07) and ETX (0x08) are fixed frame delimiters. IDT is the display ID.
TYPE is 0x01 for a read/action request and 0x02 for a write request. CMD is
a 3-character ASCII mnemonic (e.g. "POW") sent as its literal ASCII bytes.
VALUE/REPLY is one or more parameter bytes: a read (TYPE 0x01) request omits
it entirely -- only CMD is sent, with no byte between it and ETX -- while a
write (TYPE 0x02) request and every response always carry it.

The manual states a response always carries TYPE 0x00, but real hardware
instead echoes back the same TYPE that was requested (0x01 for a read reply,
0x02 for a write ack); this client validates against the echoed type rather
than a fixed 0x00.

The manual also does not document a length-prefixed frame. For commands
whose reply is a single numeric byte, the reply is read as exactly one byte
before ETX. For the identification commands (serial number, model name,
firmware version), the manual's stated reply lengths do not match real
hardware, so those replies are instead read up to the terminating ETX --
safe there specifically because their payloads are printable ASCII, which
never contains the ETX control byte (0x08). This would not be safe for a
single numeric value byte, which could legitimately equal 0x08.
"""
from __future__ import annotations

import asyncio
import logging

from .const import (
    ASPECT_RATIOS,
    ASPECT_RATIOS_REVERSE,
    CMD_ASPECT_RATIO,
    CMD_BACKLIGHT,
    CMD_BRIGHTNESS,
    CMD_CONTRAST,
    CMD_FACTORY_RESET,
    CMD_FIRMWARE_VERSION,
    CMD_FREEZE,
    CMD_HUE,
    CMD_INPUT,
    CMD_MODEL_NAME,
    CMD_MUTE,
    CMD_PICTURE_MODE,
    CMD_POWER,
    CMD_REMOTE_KEY,
    CMD_SATURATION,
    CMD_SERIAL_NUMBER,
    CMD_SHARPNESS,
    CMD_VOLUME,
    CMD_VOLUME_DOWN,
    CMD_VOLUME_UP,
    DEFAULT_DISPLAY_ID,
    ETX,
    FACTORY_RESET_KEEP_COMMUNICATION,
    FREEZE_OFF,
    FREEZE_ON,
    INPUT_SOURCES,
    INPUT_SOURCES_REVERSE,
    PICTURE_MODES,
    PICTURE_MODES_REVERSE,
    REMOTE_KEYS,
    STX,
    TEXT_REPLY_COMMANDS,
    CommandType,
)

_LOGGER = logging.getLogger(__name__)

#: Header bytes before the reply payload: STX, IDT, TYPE, and 3 CMD bytes.
_HEADER_LENGTH = 6


class AvocorError(Exception):
    """Base error for the Avocor client."""


class AvocorConnectionError(AvocorError):
    """Raised when the TCP connection to the display could not be used."""


class AvocorResponseError(AvocorError):
    """Raised when the display's response frame is malformed or unexpected."""


class AvocorClient:
    """A persistent TCP connection to an Avocor display's control port."""

    def __init__(
        self,
        host: str,
        port: int,
        display_id: int = DEFAULT_DISPLAY_ID,
        timeout: float = 5.0,
    ) -> None:
        """Initialize the client."""
        self._host = host
        self._port = port
        self._display_id = display_id
        self._timeout = timeout
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()

    @property
    def is_connected(self) -> bool:
        """Return whether the TCP connection is currently open."""
        return self._writer is not None and not self._writer.is_closing()

    async def connect(self) -> None:
        """Open the TCP connection to the display."""
        if self.is_connected:
            return
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port), self._timeout
            )
        except (OSError, asyncio.TimeoutError) as err:
            raise AvocorConnectionError(
                f"Could not connect to {self._host}:{self._port}: {err}"
            ) from err

    async def disconnect(self) -> None:
        """Close the TCP connection."""
        if self._writer is not None:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except OSError:
                pass
        self._reader = None
        self._writer = None

    async def _request(
        self, cmd: str, cmd_type: CommandType, value: int = 0x00
    ) -> bytes:
        """Send one command frame and return its raw reply payload bytes."""
        # A read/action request carries no value byte at all -- only a write
        # carries the parameter it is setting. Response frames always carry
        # a value/reply payload regardless of the request type.
        value_bytes = bytes([value]) if cmd_type == CommandType.WRITE else b""
        frame = (
            bytes([STX, self._display_id, cmd_type])
            + cmd.encode("ascii")
            + value_bytes
            + bytes([ETX])
        )

        async with self._lock:
            if not self.is_connected:
                await self.connect()
            assert self._writer is not None
            assert self._reader is not None

            try:
                self._writer.write(frame)
                await asyncio.wait_for(self._writer.drain(), self._timeout)
                header = await asyncio.wait_for(
                    self._reader.readexactly(_HEADER_LENGTH), self._timeout
                )
                if cmd in TEXT_REPLY_COMMANDS:
                    rest = await asyncio.wait_for(
                        self._reader.readuntil(bytes([ETX])), self._timeout
                    )
                else:
                    rest = await asyncio.wait_for(
                        self._reader.readexactly(2), self._timeout
                    )
            except (
                OSError,
                asyncio.IncompleteReadError,
                asyncio.LimitOverrunError,
                asyncio.TimeoutError,
            ) as err:
                await self.disconnect()
                raise AvocorConnectionError(
                    f"Communication with {self._host}:{self._port} failed: {err}"
                ) from err

        response = header + rest
        if response[0] != STX or response[-1] != ETX:
            raise AvocorResponseError(f"Malformed response frame: {response!r}")
        # Real hardware echoes back the TYPE it was sent, not a fixed 0x00
        # as the manual states.
        if response[2] != cmd_type:
            raise AvocorResponseError(f"Unexpected response type in: {response!r}")
        reply_cmd = response[3:6].decode("ascii", errors="replace")
        if reply_cmd != cmd:
            raise AvocorResponseError(
                f"Expected reply for {cmd!r} but got {reply_cmd!r}"
            )
        return response[_HEADER_LENGTH:-1]

    async def _read(self, cmd: str) -> bytes:
        return await self._request(cmd, CommandType.READ)

    async def _write(self, cmd: str, value: int) -> bytes:
        return await self._request(cmd, CommandType.WRITE, value)

    @staticmethod
    def _decode_text(payload: bytes) -> str:
        return payload.decode("ascii", errors="ignore").strip("\x00").strip()

    # -- Power -------------------------------------------------------------

    async def get_power(self) -> bool:
        """Return True if the display is powered on."""
        payload = await self._read(CMD_POWER)
        return bool(payload[0])

    async def set_power(self, on: bool) -> None:
        """Turn the display on or off."""
        await self._write(CMD_POWER, 0x01 if on else 0x00)

    # -- Input source --------------------------------------------------------

    async def get_input(self) -> str | None:
        """Return the currently selected input source name."""
        payload = await self._read(CMD_INPUT)
        return INPUT_SOURCES_REVERSE.get(payload[0])

    async def set_input(self, source: str) -> None:
        """Select an input source by name."""
        if source not in INPUT_SOURCES:
            raise ValueError(f"Unknown input source: {source}")
        await self._write(CMD_INPUT, INPUT_SOURCES[source])

    # -- Volume / mute -------------------------------------------------------

    async def get_volume(self) -> int:
        """Return the current volume, 0-100."""
        payload = await self._read(CMD_VOLUME)
        return payload[0]

    async def set_volume(self, level: int) -> None:
        """Set the volume, 0-100."""
        await self._write(CMD_VOLUME, max(0, min(100, level)))

    async def volume_up(self) -> None:
        """Increase the volume by 5 (device-side step)."""
        await self._write(CMD_VOLUME_UP, 0x01)

    async def volume_down(self) -> None:
        """Decrease the volume by 5 (device-side step)."""
        await self._write(CMD_VOLUME_DOWN, 0x00)

    async def get_mute(self) -> bool:
        """Return True if audio is muted."""
        payload = await self._read(CMD_MUTE)
        return bool(payload[0])

    async def set_mute(self, mute: bool) -> None:
        """Mute or unmute audio."""
        await self._write(CMD_MUTE, 0x01 if mute else 0x00)

    # -- Picture mode ---------------------------------------------------------

    async def get_picture_mode(self) -> str | None:
        """Return the current picture mode (scheme) name."""
        payload = await self._read(CMD_PICTURE_MODE)
        return PICTURE_MODES_REVERSE.get(payload[0])

    async def set_picture_mode(self, mode: str) -> None:
        """Set the picture mode (scheme) by name."""
        if mode not in PICTURE_MODES:
            raise ValueError(f"Unknown picture mode: {mode}")
        await self._write(CMD_PICTURE_MODE, PICTURE_MODES[mode])

    # -- Picture adjustments (0-100) -------------------------------------------

    async def _get_level(self, cmd: str) -> int:
        payload = await self._read(cmd)
        return payload[0]

    async def _set_level(self, cmd: str, value: int) -> None:
        await self._write(cmd, max(0, min(100, value)))

    async def get_backlight(self) -> int:
        return await self._get_level(CMD_BACKLIGHT)

    async def set_backlight(self, value: int) -> None:
        await self._set_level(CMD_BACKLIGHT, value)

    async def get_brightness(self) -> int:
        return await self._get_level(CMD_BRIGHTNESS)

    async def set_brightness(self, value: int) -> None:
        await self._set_level(CMD_BRIGHTNESS, value)

    async def get_contrast(self) -> int:
        return await self._get_level(CMD_CONTRAST)

    async def set_contrast(self, value: int) -> None:
        await self._set_level(CMD_CONTRAST, value)

    async def get_sharpness(self) -> int:
        return await self._get_level(CMD_SHARPNESS)

    async def set_sharpness(self, value: int) -> None:
        await self._set_level(CMD_SHARPNESS, value)

    async def get_hue(self) -> int:
        return await self._get_level(CMD_HUE)

    async def set_hue(self, value: int) -> None:
        await self._set_level(CMD_HUE, value)

    async def get_saturation(self) -> int:
        return await self._get_level(CMD_SATURATION)

    async def set_saturation(self, value: int) -> None:
        await self._set_level(CMD_SATURATION, value)

    # -- Aspect ratio ----------------------------------------------------------

    async def get_aspect_ratio(self) -> str | None:
        """Return the current scaling/aspect ratio name."""
        payload = await self._read(CMD_ASPECT_RATIO)
        return ASPECT_RATIOS_REVERSE.get(payload[0])

    async def set_aspect_ratio(self, aspect_ratio: str) -> None:
        """Set the scaling/aspect ratio by name."""
        if aspect_ratio not in ASPECT_RATIOS:
            raise ValueError(f"Unknown aspect ratio: {aspect_ratio}")
        await self._write(CMD_ASPECT_RATIO, ASPECT_RATIOS[aspect_ratio])

    # -- Freeze ------------------------------------------------------------

    async def get_freeze(self) -> bool:
        """Return True if the screen image is frozen."""
        payload = await self._read(CMD_FREEZE)
        return bool(payload[0])

    async def set_freeze(self, frozen: bool) -> None:
        """Freeze or unfreeze the screen image."""
        await self._write(CMD_FREEZE, FREEZE_ON if frozen else FREEZE_OFF)

    # -- Remote key injection -----------------------------------------------

    async def send_remote_key(self, key: str) -> None:
        """Simulate a remote-control key press by name (see const.REMOTE_KEYS)."""
        if key not in REMOTE_KEYS:
            raise ValueError(f"Unknown remote key: {key}")
        await self._write(CMD_REMOTE_KEY, REMOTE_KEYS[key])

    # -- Maintenance ----------------------------------------------------------

    async def factory_reset(self, keep_communication: bool = True) -> None:
        """Restore factory defaults.

        Only "reset all but communication" is safe to call over this same
        TCP connection; a full reset also wipes the network/serial settings
        this integration depends on to reach the display.
        """
        if not keep_communication:
            raise ValueError(
                "Resetting communication settings would sever this connection "
                "and is not supported by this integration."
            )
        await self._write(CMD_FACTORY_RESET, FACTORY_RESET_KEEP_COMMUNICATION)

    # -- Identification (read-only) ------------------------------------------

    async def get_serial_number(self) -> str:
        """Return the display's serial number."""
        return self._decode_text(await self._read(CMD_SERIAL_NUMBER))

    async def get_model_name(self) -> str:
        """Return the display's model name."""
        return self._decode_text(await self._read(CMD_MODEL_NAME))

    async def get_firmware_version(self) -> str:
        """Return the display's firmware version."""
        return self._decode_text(await self._read(CMD_FIRMWARE_VERSION))
