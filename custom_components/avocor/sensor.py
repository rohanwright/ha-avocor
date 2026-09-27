"""Sensor platform for the Avocor Interactive Display integration."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import AvocorConfigEntry, AvocorCoordinator
from .entity import AvocorEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AvocorConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor entities."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            AvocorSerialNumberSensor(coordinator),
            AvocorFirmwareVersionSensor(coordinator),
        ]
    )


class AvocorSerialNumberSensor(AvocorEntity, SensorEntity):
    """Reports the display's serial number."""

    _attr_translation_key = "serial_number"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:barcode"

    def __init__(self, coordinator: AvocorCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, "serial_number")

    @property
    def native_value(self) -> str | None:
        """Return the serial number read during setup."""
        return self.coordinator.serial_number


class AvocorFirmwareVersionSensor(AvocorEntity, SensorEntity):
    """Reports the display's firmware version."""

    _attr_translation_key = "firmware_version"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:chip"

    def __init__(self, coordinator: AvocorCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, "firmware_version")

    @property
    def native_value(self) -> str | None:
        """Return the firmware version read during setup."""
        return self.coordinator.firmware_version
