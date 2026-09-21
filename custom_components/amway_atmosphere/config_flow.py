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

from .api import AmwayApiClient, normalize_username
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_COUNTRY,
    CONF_EXPIRES_AT,
    CONF_PARTY_ID,
    CONF_PASSWORD,
    CONF_REFRESH_TOKEN,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    DEFAULT_COUNTRY,
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
        return clean_str.split("code=")[1].split("&")[0]
    return clean_str


class AmwayAtmosphereConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Amway Atmosphere."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self._reauth_entry: Optional[config_entries.ConfigEntry] = None

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle initial step: Phone + Password direct login."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            raw_token = user_input.get(CONF_ACCESS_TOKEN, "").strip()
            raw_username = user_input.get(CONF_USERNAME, "").strip()
            password = user_input.get(CONF_PASSWORD, "").strip()
            country = user_input.get(CONF_COUNTRY, DEFAULT_COUNTRY).strip().upper()

            session = async_get_clientsession(self.hass)

            # Direct Phone/Username and Password Login
            if raw_username and password:
                try:
                    login_res = await AmwayApiClient.async_login_with_password(
                        session=session,
                        username=raw_username,
                        password=password,
                        country=country,
                    )
                    access_token = login_res["access_token"]
                    refresh_token = login_res.get("refresh_token")
                    norm_username = login_res["username"]
                    party_id = login_res.get("party_id")
                    expires_in = login_res.get("expires_in", 3600)
                    expires_at = time.time() + expires_in

                    # Verify connection and discover devices
                    client = AmwayApiClient(
                        session=session,
                        access_token=access_token,
                        refresh_token=refresh_token,
                        username=norm_username,
                        password=password,
                        country=country,
                    )
                    devices = await client.async_get_devices()

                    if not devices:
                        _LOGGER.warning(
                            "Amway account '%s' authenticated successfully, but 0 devices found.",
                            norm_username,
                        )
                        errors["base"] = "no_devices_found"
                    else:
                        unique_id = f"amway_atmosphere_{party_id or devices[0].thing_id or norm_username}"
                        await self.async_set_unique_id(unique_id)
                        self._abort_if_unique_id_configured()

                        return self.async_create_entry(
                            title=f"Amway Atmosphere ({devices[0].thing_id})",
                            data={
                                CONF_USERNAME: norm_username,
                                CONF_PASSWORD: password,
                                CONF_COUNTRY: country,
                                CONF_ACCESS_TOKEN: access_token,
                                CONF_REFRESH_TOKEN: refresh_token,
                                CONF_PARTY_ID: party_id,
                                CONF_EXPIRES_AT: expires_at,
                            },
                        )
                except Exception as err:
                    _LOGGER.exception("Failed to authenticate with Amway credentials: %s", err)
                    err_msg = str(err).lower()
                    if "401" in err_msg or "403" in err_msg or "unauthorized" in err_msg or "invalid" in err_msg:
                        errors["base"] = "invalid_auth"
                    else:
                        errors["base"] = "cannot_connect"

            # Direct Access Token or JSON Token Payload (for programmatic / testing support)
            elif raw_token:
                access_token = raw_token
                refresh_token = None
                expires_at = time.time() + 86400 * 365

                if raw_token.startswith("{") and "access_token" in raw_token:
                    try:
                        import json as py_json
                        token_dict = py_json.loads(raw_token)
                        access_token = token_dict.get("access_token", raw_token)
                        refresh_token = token_dict.get("refresh_token")
                        if "expires_in" in token_dict:
                            expires_at = time.time() + token_dict["expires_in"]
                    except Exception:
                        pass

                try:
                    client = AmwayApiClient(
                        session=session,
                        access_token=access_token,
                        refresh_token=refresh_token,
                        country=country,
                    )
                    devices = await client.async_get_devices()
                    if not devices:
                        errors["base"] = "no_devices_found"
                    else:
                        unique_id = f"amway_atmosphere_{devices[0].thing_id}"
                        await self.async_set_unique_id(unique_id)
                        self._abort_if_unique_id_configured()

                        return self.async_create_entry(
                            title=f"Amway Atmosphere ({devices[0].thing_id})",
                            data={
                                CONF_ACCESS_TOKEN: access_token,
                                CONF_REFRESH_TOKEN: refresh_token,
                                CONF_COUNTRY: country,
                                CONF_EXPIRES_AT: expires_at,
                            },
                        )
                except Exception as err:
                    _LOGGER.exception("Failed to connect Amway with provided token: %s", err)
                    errors["base"] = "invalid_auth"

            else:
                errors["base"] = "invalid_auth"

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Optional(CONF_COUNTRY, default=DEFAULT_COUNTRY): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
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
            saved_username = (
                self._reauth_entry.data.get(CONF_USERNAME)
                or user_input.get(CONF_USERNAME)
            )
            password = user_input.get(CONF_PASSWORD)
            country = self._reauth_entry.data.get(CONF_COUNTRY, DEFAULT_COUNTRY)

            session = async_get_clientsession(self.hass)
            try:
                if saved_username and password:
                    login_res = await AmwayApiClient.async_login_with_password(
                        session=session,
                        username=saved_username,
                        password=password,
                        country=country,
                    )
                    self.hass.config_entries.async_update_entry(
                        self._reauth_entry,
                        data={
                            **self._reauth_entry.data,
                            CONF_USERNAME: saved_username,
                            CONF_PASSWORD: password,
                            CONF_ACCESS_TOKEN: login_res["access_token"],
                            CONF_REFRESH_TOKEN: login_res.get("refresh_token")
                            or self._reauth_entry.data.get(CONF_REFRESH_TOKEN),
                            CONF_EXPIRES_AT: time.time() + login_res.get("expires_in", 3600),
                        },
                    )
                    await self.hass.config_entries.async_reload(self._reauth_entry.entry_id)
                    return self.async_abort(reason="reauth_successful")
                else:
                    errors["base"] = "invalid_auth"
            except Exception as err:
                _LOGGER.exception("Re-auth failed: %s", err)
                errors["base"] = "cannot_connect"

        saved_username = (
            self._reauth_entry.data.get(CONF_USERNAME) if self._reauth_entry else None
        )
        if saved_username:
            schema = vol.Schema({vol.Required(CONF_PASSWORD): str})
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=schema,
                description_placeholders={"username": saved_username},
                errors=errors,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=schema,
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
