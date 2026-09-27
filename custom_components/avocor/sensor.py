"""Sensor platform for the Avocor Interactive Display integration."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
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
    """Set up the sensor entities."""
    runtime_data = entry.runtime_data
    async_add_entities(
        [
            AvocorSerialNumberSensor(runtime_data),
            AvocorFirmwareVersionSensor(runtime_data),
        ]
    )


class AvocorSerialNumberSensor(AvocorEntity, SensorEntity):
    """Reports the display's serial number."""

    _attr_translation_key = "serial_number"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:barcode"

    def __init__(self, runtime_data: AvocorRuntimeData) -> None:
        """Initialize the sensor."""
        super().__init__(runtime_data.fast_coordinator, "serial_number")
        self._serial_number = runtime_data.serial_number

    @property
    def native_value(self) -> str | None:
        """Return the serial number read during setup."""
        return self._serial_number


class AvocorFirmwareVersionSensor(AvocorEntity, SensorEntity):
    """Reports the display's firmware version."""

    _attr_translation_key = "firmware_version"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:chip"

    def __init__(self, runtime_data: AvocorRuntimeData) -> None:
        """Initialize the sensor."""
        super().__init__(runtime_data.fast_coordinator, "firmware_version")
        self._firmware_version = runtime_data.firmware_version

    @property
    def native_value(self) -> str | None:
        """Return the firmware version read during setup."""
        return self._firmware_version
