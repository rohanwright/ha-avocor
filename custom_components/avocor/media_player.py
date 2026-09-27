"""Media player platform for the Avocor Interactive Display integration."""
from __future__ import annotations

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import INPUT_SOURCES
from .coordinator import AvocorConfigEntry, AvocorCoordinator
from .entity import AvocorEntity

_SUPPORTED_FEATURES = (
    MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.SELECT_SOURCE
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AvocorConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the media player entity."""
    async_add_entities([AvocorMediaPlayer(entry.runtime_data)])


class AvocorMediaPlayer(AvocorEntity, MediaPlayerEntity):
    """Representation of an Avocor display as a media player."""

    _attr_name = None
    _attr_device_class = MediaPlayerDeviceClass.TV
    _attr_supported_features = _SUPPORTED_FEATURES
    _attr_source_list = list(INPUT_SOURCES)

    def __init__(self, coordinator: AvocorCoordinator) -> None:
        """Initialize the media player."""
        super().__init__(coordinator, "media_player")

    @property
    def state(self) -> MediaPlayerState:
        """Return the state of the display."""
        if self.coordinator.data.power_on:
            return MediaPlayerState.ON
        return MediaPlayerState.OFF

    @property
    def source(self) -> str | None:
        """Return the current input source."""
        return self.coordinator.data.input_source

    @property
    def volume_level(self) -> float | None:
        """Return the volume level, 0..1."""
        return self.coordinator.data.volume / 100

    @property
    def is_volume_muted(self) -> bool:
        """Return True if audio is muted."""
        return self.coordinator.data.muted

    async def async_turn_on(self) -> None:
        """Turn the display on."""
        await self.coordinator.client.set_power(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        """Turn the display off."""
        await self.coordinator.client.set_power(False)
        await self.coordinator.async_request_refresh()

    async def async_select_source(self, source: str) -> None:
        """Select an input source."""
        await self.coordinator.client.set_input(source)
        await self.coordinator.async_request_refresh()

    async def async_set_volume_level(self, volume: float) -> None:
        """Set the volume level, 0..1."""
        await self.coordinator.client.set_volume(round(volume * 100))
        await self.coordinator.async_request_refresh()

    async def async_volume_up(self) -> None:
        """Increase the volume."""
        await self.coordinator.client.volume_up()
        await self.coordinator.async_request_refresh()

    async def async_volume_down(self) -> None:
        """Decrease the volume."""
        await self.coordinator.client.volume_down()
        await self.coordinator.async_request_refresh()

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute or unmute audio."""
        await self.coordinator.client.set_mute(mute)
        await self.coordinator.async_request_refresh()
