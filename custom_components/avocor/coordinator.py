"""DataUpdateCoordinator for the Avocor Interactive Display integration."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AvocorClient, AvocorError
from .const import DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


@dataclass
class AvocorData:
    """A snapshot of the display's polled state."""

    power_on: bool
    input_source: str | None
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


type AvocorConfigEntry = ConfigEntry[AvocorCoordinator]


class AvocorCoordinator(DataUpdateCoordinator[AvocorData]):
    """Polls an Avocor display for its current state."""

    config_entry: AvocorConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: AvocorConfigEntry,
        client: AvocorClient,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name="Avocor Display",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client
        self.serial_number: str | None = None
        self.model_name: str | None = None
        self.firmware_version: str | None = None

    async def _async_update_data(self) -> AvocorData:
        """Poll the display for its current state."""
        try:
            power_on = await self.client.get_power()

            if not power_on:
                # Most sub-systems are unreadable while the panel is off;
                # avoid spamming failed reads at it every scan interval.
                return AvocorData(
                    power_on=False,
                    input_source=None,
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

            return AvocorData(
                power_on=True,
                input_source=await self.client.get_input(),
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
