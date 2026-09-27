"""Number platform for the Avocor Interactive Display integration."""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import AvocorClient
from .coordinator import AvocorConfigEntry, AvocorCoordinator, AvocorData
from .entity import AvocorEntity


@dataclass(frozen=True, kw_only=True)
class AvocorNumberDescription(NumberEntityDescription):
    """Describes an Avocor picture-adjustment number entity."""

    value_fn: Callable[[AvocorData], int]
    set_value_fn: Callable[[AvocorClient, int], Awaitable[None]]


NUMBER_DESCRIPTIONS: tuple[AvocorNumberDescription, ...] = (
    AvocorNumberDescription(
        key="backlight",
        translation_key="backlight",
        icon="mdi:brightness-6",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda data: data.backlight,
        set_value_fn=lambda client, value: client.set_backlight(value),
    ),
    AvocorNumberDescription(
        key="brightness",
        translation_key="brightness",
        icon="mdi:brightness-5",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda data: data.brightness,
        set_value_fn=lambda client, value: client.set_brightness(value),
    ),
    AvocorNumberDescription(
        key="contrast",
        translation_key="contrast",
        icon="mdi:contrast-box",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda data: data.contrast,
        set_value_fn=lambda client, value: client.set_contrast(value),
    ),
    AvocorNumberDescription(
        key="sharpness",
        translation_key="sharpness",
        icon="mdi:image-filter-hdr",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda data: data.sharpness,
        set_value_fn=lambda client, value: client.set_sharpness(value),
    ),
    AvocorNumberDescription(
        key="hue",
        translation_key="hue",
        icon="mdi:invert-colors",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda data: data.hue,
        set_value_fn=lambda client, value: client.set_hue(value),
    ),
    AvocorNumberDescription(
        key="saturation",
        translation_key="saturation",
        icon="mdi:palette-swatch",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda data: data.saturation,
        set_value_fn=lambda client, value: client.set_saturation(value),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AvocorConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the number entities."""
    coordinator = entry.runtime_data
    async_add_entities(
        AvocorNumber(coordinator, description) for description in NUMBER_DESCRIPTIONS
    )


class AvocorNumber(AvocorEntity, NumberEntity):
    """A picture-adjustment number entity."""

    entity_description: AvocorNumberDescription

    def __init__(
        self, coordinator: AvocorCoordinator, description: AvocorNumberDescription
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> int:
        """Return the current value."""
        return self.entity_description.value_fn(self.coordinator.data)

    async def async_set_native_value(self, value: float) -> None:
        """Set a new value."""
        await self.entity_description.set_value_fn(self.coordinator.client, int(value))
        await self.coordinator.async_request_refresh()
