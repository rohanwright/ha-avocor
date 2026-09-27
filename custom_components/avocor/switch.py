"""Switch platform for the Avocor Interactive Display integration."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import AvocorConfigEntry, AvocorCoordinator
from .entity import AvocorEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AvocorConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch entities."""
    async_add_entities([AvocorFreezeSwitch(entry.runtime_data)])


class AvocorFreezeSwitch(AvocorEntity, SwitchEntity):
    """Freezes the currently displayed image, e.g. for whiteboard use."""

    _attr_translation_key = "freeze"
    _attr_icon = "mdi:pause-box-outline"

    def __init__(self, coordinator: AvocorCoordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, "freeze")

    @property
    def is_on(self) -> bool:
        """Return True if the image is frozen."""
        return self.coordinator.data.frozen

    async def async_turn_on(self, **kwargs) -> None:
        """Freeze the image."""
        await self.coordinator.client.set_freeze(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Unfreeze the image."""
        await self.coordinator.client.set_freeze(False)
        await self.coordinator.async_request_refresh()
