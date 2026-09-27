"""Select platform for the Avocor Interactive Display integration."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import PICTURE_MODES
from .coordinator import AvocorConfigEntry, AvocorRuntimeData
from .entity import AvocorEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AvocorConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the select entities."""
    async_add_entities([AvocorPictureModeSelect(entry.runtime_data)])


class AvocorPictureModeSelect(AvocorEntity, SelectEntity):
    """Selects the display's picture mode (scheme)."""

    _attr_translation_key = "picture_mode"
    _attr_options = list(PICTURE_MODES)
    _attr_icon = "mdi:palette"

    def __init__(self, runtime_data: AvocorRuntimeData) -> None:
        """Initialize the select entity."""
        super().__init__(runtime_data.slow_coordinator, "picture_mode")

    @property
    def current_option(self) -> str | None:
        """Return the current picture mode."""
        return self.coordinator.data.picture_mode

    async def async_select_option(self, option: str) -> None:
        """Set the picture mode."""
        await self.coordinator.client.set_picture_mode(option)
        await self.coordinator.async_request_refresh()
