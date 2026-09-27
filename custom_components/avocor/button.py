"""Button platform for the Avocor Interactive Display integration."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import AvocorConfigEntry, AvocorRuntimeData
from .entity import AvocorEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AvocorConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button entities."""
    async_add_entities([AvocorFactoryResetButton(entry.runtime_data)])


class AvocorFactoryResetButton(AvocorEntity, ButtonEntity):
    """Restores picture/audio/OSD settings to factory defaults.

    Deliberately uses only the "reset all but communication" variant of the
    display's factory reset command, so this integration's own RS232/network
    settings are preserved and the connection survives the reset.
    """

    _attr_translation_key = "factory_reset"
    _attr_icon = "mdi:restore"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, runtime_data: AvocorRuntimeData) -> None:
        """Initialize the button."""
        super().__init__(runtime_data.slow_coordinator, "factory_reset")

    async def async_press(self) -> None:
        """Restore factory defaults, keeping communication settings."""
        await self.coordinator.client.factory_reset(keep_communication=True)
        await self.coordinator.async_request_refresh()
