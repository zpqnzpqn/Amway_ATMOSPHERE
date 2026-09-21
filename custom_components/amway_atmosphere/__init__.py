"""The Amway Atmosphere custom integration."""

from __future__ import annotations

import logging
from typing import List

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AmwayApiClient
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_COUNTRY,
    CONF_EXPIRES_AT,
    CONF_PASSWORD,
    CONF_REFRESH_TOKEN,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    DEFAULT_COUNTRY,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .coordinator import AmwayAtmosphereCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: List[str] = ["fan", "sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Amway Atmosphere from a config entry."""
    session = async_get_clientsession(hass)

    async def _handle_token_refreshed(new_tokens: dict) -> None:
        """Persist refreshed tokens back into config entry data."""
        data = {**entry.data}
        data[CONF_ACCESS_TOKEN] = new_tokens["access_token"]
        if "refresh_token" in new_tokens:
            data[CONF_REFRESH_TOKEN] = new_tokens["refresh_token"]
        hass.config_entries.async_update_entry(entry, data=data)

    client = AmwayApiClient(
        session=session,
        access_token=entry.data[CONF_ACCESS_TOKEN],
        refresh_token=entry.data.get(CONF_REFRESH_TOKEN),
        username=entry.data.get(CONF_USERNAME),
        password=entry.data.get(CONF_PASSWORD),
        country=entry.data.get(CONF_COUNTRY, DEFAULT_COUNTRY),
        on_token_refreshed=_handle_token_refreshed,
    )

    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    coordinator = AmwayAtmosphereCoordinator(
        hass=hass, client=client, scan_interval_seconds=scan_interval
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Prune obsolete switch entities from entity registry (Auto/Night/Turbo mode switches now handled natively in fan entity)
    try:
        from homeassistant.helpers import entity_registry as er

        ent_reg = er.async_get(hass)
        for entity_entry in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
            if entity_entry.domain == "switch":
                ent_reg.async_remove(entity_entry.entity_id)
    except Exception as err:
        _LOGGER.debug("Could not prune obsolete switch entities: %s", err)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
