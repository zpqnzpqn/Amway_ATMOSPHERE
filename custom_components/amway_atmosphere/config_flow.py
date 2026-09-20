"""Config flow for Amway Atmosphere integration."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional
import urllib.parse

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol

from .api import AmwayApiClient
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_AUTH_CODE,
    CONF_EXPIRES_AT,
    CONF_REFRESH_TOKEN,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def _extract_code(user_input_str: str) -> str:
    """Extract code from raw input string or full redirect URL."""
    clean_str = user_input_str.strip()
    if "code=" in clean_str:
        parsed = urllib.parse.urlparse(clean_str)
        params = urllib.parse.parse_qs(parsed.query)
        code_vals = params.get("code")
        if code_vals and code_vals[0]:
            return code_vals[0]
        # Fallback substring
        return clean_str.split("code=")[1].split("&")[0]
    return clean_str


class AmwayAtmosphereConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Amway Atmosphere."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self._auth_url: str = AmwayApiClient.get_authorization_url()
        self._reauth_entry: Optional[config_entries.ConfigEntry] = None

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            raw_code = user_input.get(CONF_AUTH_CODE, "")
            auth_code = _extract_code(raw_code)

            if not auth_code:
                errors[CONF_AUTH_CODE] = "invalid_auth_code"
            else:
                session = async_get_clientsession(self.hass)
                try:
                    tokens = await AmwayApiClient.async_exchange_code(
                        session, auth_code
                    )
                    access_token = tokens["access_token"]
                    refresh_token = tokens.get("refresh_token")
                    expires_in = tokens.get("expires_in", 3600)
                    expires_at = time.time() + expires_in

                    # Verify credentials by fetching devices
                    client = AmwayApiClient(session, access_token, refresh_token)
                    devices = await client.async_get_devices()

                    # Set unique ID based on account or devices
                    unique_id = f"amway_atmosphere_{devices[0].thing_id if devices else 'account'}"
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title="Amway Atmosphere",
                        data={
                            CONF_ACCESS_TOKEN: access_token,
                            CONF_REFRESH_TOKEN: refresh_token,
                            CONF_EXPIRES_AT: expires_at,
                        },
                    )
                except Exception as err:
                    _LOGGER.exception("Failed to authenticate with Amway: %s", err)
                    errors["base"] = "cannot_connect"

        schema = vol.Schema(
            {
                vol.Required(CONF_AUTH_CODE): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            description_placeholders={"auth_url": self._auth_url},
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Dict[str, Any]
    ) -> FlowResult:
        """Handle re-authentication with Amway."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Confirm re-authentication with Amway."""
        errors: Dict[str, str] = {}

        if user_input is not None and self._reauth_entry:
            raw_code = user_input.get(CONF_AUTH_CODE, "")
            auth_code = _extract_code(raw_code)

            session = async_get_clientsession(self.hass)
            try:
                tokens = await AmwayApiClient.async_exchange_code(session, auth_code)
                self.hass.config_entries.async_update_entry(
                    self._reauth_entry,
                    data={
                        **self._reauth_entry.data,
                        CONF_ACCESS_TOKEN: tokens["access_token"],
                        CONF_REFRESH_TOKEN: tokens.get("refresh_token"),
                        CONF_EXPIRES_AT: time.time() + tokens.get("expires_in", 3600),
                    },
                )
                await self.hass.config_entries.async_reload(self._reauth_entry.entry_id)
                return self.async_abort(reason="reauth_successful")
            except Exception as err:
                _LOGGER.exception("Re-auth failed: %s", err)
                errors["base"] = "cannot_connect"

        schema = vol.Schema({vol.Required(CONF_AUTH_CODE): str})
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=schema,
            description_placeholders={"auth_url": self._auth_url},
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create options flow handler."""
        return AmwayAtmosphereOptionsFlow(config_entry)


class AmwayAtmosphereOptionsFlow(config_entries.OptionsFlow):
    """Handle Amway Atmosphere options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=10, max=300)),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
