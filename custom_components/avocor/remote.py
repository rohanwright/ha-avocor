"""Remote platform for the Avocor Interactive Display integration.

Exposes the display's remote-control key injection (RCU) as a Home
Assistant `remote` entity, so keys such as menu navigation or source
selection can be sent via the `remote.send_command` service.
"""
from __future__ import annotations

import asyncio
from typing import Any

from homeassistant.components.remote import (
    ATTR_DELAY_SECS,
    ATTR_NUM_REPEATS,
    DEFAULT_DELAY_SECS,
    DEFAULT_NUM_REPEATS,
    RemoteEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import REMOTE_KEYS
from .coordinator import AvocorConfigEntry, AvocorRuntimeData
from .entity import AvocorEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AvocorConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the remote entity."""
    async_add_entities([AvocorRemote(entry.runtime_data)])


class AvocorRemote(AvocorEntity, RemoteEntity):
    """Sends remote-control key presses to the display."""

    _attr_name = None

    def __init__(self, runtime_data: AvocorRuntimeData) -> None:
        """Initialize the remote entity."""
        super().__init__(runtime_data.fast_coordinator, "remote")
        self._slow_coordinator = runtime_data.slow_coordinator

    @property
    def is_on(self) -> bool:
        """Return True if the display is powered on."""
        return self.coordinator.data.power_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the display on."""
        await self.coordinator.client.set_power(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the display off."""
        await self.coordinator.client.set_power(False)
        await self.coordinator.async_request_refresh()

    async def async_send_command(self, command: list[str], **kwargs: Any) -> None:
        """Send one or more remote-control key presses.

        Valid key names: menu, info, up, down, left, right, ok, exit, hdmi1,
        hdmi2, hdmi_front, displayport, type_c, ops, scaling, freeze, mute,
        auto, volume_up, volume_down.
        """
        num_repeats: int = kwargs.get(ATTR_NUM_REPEATS, DEFAULT_NUM_REPEATS)
        delay_secs: float = kwargs.get(ATTR_DELAY_SECS, DEFAULT_DELAY_SECS)

        for key in command:
            if key not in REMOTE_KEYS:
                raise ServiceValidationError(
                    f"Unknown remote key {key!r}; valid keys are: "
                    f"{', '.join(sorted(REMOTE_KEYS))}"
                )

        for _ in range(num_repeats):
            for key in command:
                await self.coordinator.client.send_remote_key(key)
                await asyncio.sleep(delay_secs)

        # A key press can affect power/input or picture/audio settings
        # (e.g. a source key vs. mute/volume/freeze); refresh both rather
        # than trying to classify which coordinator owns each key.
        await self.coordinator.async_request_refresh()
        await self._slow_coordinator.async_request_refresh()
