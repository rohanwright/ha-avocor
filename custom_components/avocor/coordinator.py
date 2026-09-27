"""DataUpdateCoordinators for the Avocor Interactive Display integration.

Two coordinators poll the display at different rates: `AvocorFastCoordinator`
covers power and input source, which can change from outside Home Assistant
(a physical remote, an IR receiver) and benefit from being noticed quickly.
`AvocorSlowCoordinator` covers volume, mute, picture settings, and freeze
state, which change far less often externally -- this integration's own
writes already trigger an immediate refresh of the relevant coordinator, so
the slow poll only exists to catch changes made outside HA.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AvocorClient, AvocorError
from .const import FAST_SCAN_INTERVAL, SLOW_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


@dataclass
class AvocorFastData:
    """Power and input source, polled frequently."""

    power_on: bool
    input_source: str | None


@dataclass
class AvocorSlowData:
    """Everything else, polled infrequently."""

    volume: int
    muted: bool
    picture_mode: str | None
    backlight: int
    brightness: int
    contrast: int
    sharpness: int
    hue: int
    saturation: int
    frozen: bool


type AvocorConfigEntry = ConfigEntry[AvocorRuntimeData]


class AvocorFastCoordinator(DataUpdateCoordinator[AvocorFastData]):
    """Polls power and input source."""

    config_entry: AvocorConfigEntry

    def __init__(
        self, hass: HomeAssistant, config_entry: AvocorConfigEntry, client: AvocorClient
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name="Avocor Display (power/input)",
            update_interval=timedelta(seconds=FAST_SCAN_INTERVAL),
        )
        self.client = client

    async def _async_update_data(self) -> AvocorFastData:
        """Poll the display for power and input state."""
        try:
            power_on = await self.client.get_power()
            input_source = await self.client.get_input() if power_on else None
            return AvocorFastData(power_on=power_on, input_source=input_source)
        except AvocorError as err:
            raise UpdateFailed(f"Error communicating with display: {err}") from err


class AvocorSlowCoordinator(DataUpdateCoordinator[AvocorSlowData]):
    """Polls volume, mute, picture settings, and freeze state."""

    config_entry: AvocorConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: AvocorConfigEntry,
        client: AvocorClient,
        fast_coordinator: AvocorFastCoordinator,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name="Avocor Display (settings)",
            update_interval=timedelta(seconds=SLOW_SCAN_INTERVAL),
        )
        self.client = client
        self._fast_coordinator = fast_coordinator

    async def _async_update_data(self) -> AvocorSlowData:
        """Poll the display for its other, less time-sensitive state."""
        # Most sub-systems are unreadable while the panel is off; rely on
        # the fast coordinator's last known power state rather than issuing
        # another read here.
        if self._fast_coordinator.data is not None and not self._fast_coordinator.data.power_on:
            return AvocorSlowData(
                volume=0,
                muted=False,
                picture_mode=None,
                backlight=0,
                brightness=0,
                contrast=0,
                sharpness=0,
                hue=0,
                saturation=0,
                frozen=False,
            )

        try:
            return AvocorSlowData(
                volume=await self.client.get_volume(),
                muted=await self.client.get_mute(),
                picture_mode=await self.client.get_picture_mode(),
                backlight=await self.client.get_backlight(),
                brightness=await self.client.get_brightness(),
                contrast=await self.client.get_contrast(),
                sharpness=await self.client.get_sharpness(),
                hue=await self.client.get_hue(),
                saturation=await self.client.get_saturation(),
                frozen=await self.client.get_freeze(),
            )
        except AvocorError as err:
            raise UpdateFailed(f"Error communicating with display: {err}") from err


@dataclass
class AvocorRuntimeData:
    """Runtime state stored on the config entry."""

    client: AvocorClient
    fast_coordinator: AvocorFastCoordinator
    slow_coordinator: AvocorSlowCoordinator
    model_name: str | None = None
    serial_number: str | None = None
    firmware_version: str | None = None
