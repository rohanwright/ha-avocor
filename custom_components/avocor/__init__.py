"""The Avocor Interactive Display integration."""
from __future__ import annotations

import logging

from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .api import AvocorClient, AvocorError
from .const import CONF_DISPLAY_ID, DEFAULT_DISPLAY_ID
from .coordinator import AvocorConfigEntry, AvocorCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BUTTON,
    Platform.MEDIA_PLAYER,
    Platform.NUMBER,
    Platform.REMOTE,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: AvocorConfigEntry) -> bool:
    """Set up Avocor Interactive Display from a config entry."""
    client = AvocorClient(
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data.get(CONF_DISPLAY_ID, DEFAULT_DISPLAY_ID),
    )

    try:
        await client.connect()
    except AvocorError as err:
        raise ConfigEntryNotReady(
            f"Could not connect to display at {entry.data[CONF_HOST]}:"
            f"{entry.data[CONF_PORT]}: {err}"
        ) from err

    coordinator = AvocorCoordinator(hass, entry, client)

    try:
        coordinator.model_name = await client.get_model_name()
        coordinator.serial_number = await client.get_serial_number()
        coordinator.firmware_version = await client.get_firmware_version()
    except AvocorError as err:
        _LOGGER.debug("Could not read display identification: %s", err)

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: AvocorConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.client.disconnect()
    return unload_ok
