"""Base entity for the Avocor Interactive Display integration."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import AvocorFastCoordinator, AvocorSlowCoordinator


class AvocorEntity(CoordinatorEntity[AvocorFastCoordinator | AvocorSlowCoordinator]):
    """Base entity tying every platform entity to one display device."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: AvocorFastCoordinator | AvocorSlowCoordinator, key: str
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        entry = coordinator.config_entry
        runtime_data = entry.runtime_data
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data.get("name"),
            manufacturer=MANUFACTURER,
            model=runtime_data.model_name,
            sw_version=runtime_data.firmware_version,
            serial_number=runtime_data.serial_number,
        )
