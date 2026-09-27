"""Config flow for the Avocor Interactive Display integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.helpers import config_validation as cv

from .api import AvocorClient, AvocorError
from .const import (
    CONF_DISPLAY_ID,
    DEFAULT_DISPLAY_ID,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Optional(CONF_DISPLAY_ID, default=DEFAULT_DISPLAY_ID): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=255)
        ),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)


async def _validate_and_get_serial(data: dict[str, Any]) -> str:
    """Connect to the display and return its serial number, or raise."""
    client = AvocorClient(
        data[CONF_HOST], data[CONF_PORT], data[CONF_DISPLAY_ID], timeout=5.0
    )
    try:
        await client.connect()
        return await client.get_serial_number()
    finally:
        await client.disconnect()


class AvocorConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Avocor Interactive Display."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._async_abort_entries_match(
                {CONF_HOST: user_input[CONF_HOST], CONF_PORT: user_input[CONF_PORT]}
            )
            try:
                serial_number = await _validate_and_get_serial(user_input)
            except AvocorError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error validating Avocor connection")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(serial_number)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
