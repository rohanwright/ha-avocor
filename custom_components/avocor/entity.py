"""Base entity for the Avocor Interactive Display integration."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import AvocorCoordinator


class AvocorEntity(CoordinatorEntity[AvocorCoordinator]):
    """Base entity tying every platform entity to one display device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: AvocorCoordinator, key: str) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=coordinator.config_entry.data.get("name"),
            manufacturer=MANUFACTURER,
            model=coordinator.model_name,
            sw_version=coordinator.firmware_version,
            serial_number=coordinator.serial_number,
        )
