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


def _patch_homekit_serial_number(hass: HomeAssistant) -> None:
    """Ensure HomeKit accessories receive their exact device serial number from Home Assistant."""
    try:
        import importlib
        hk_acc = importlib.import_module("homeassistant.components.homekit.accessories")
    except (ImportError, Exception) as err:
        _LOGGER.debug("HomeKit integration not available for serial number bridging: %s", err)
        return

    if getattr(hk_acc.HomeAccessory, "_orig_init_amway", None) is not None:
        # Already patched
        return

    orig_init = hk_acc.HomeAccessory.__init__
    hk_acc.HomeAccessory._orig_init_amway = orig_init

    def patched_init(
        self,
        hass: HomeAssistant,
        driver: Any,
        name: str,
        entity_id: str,
        aid: int,
        config: dict,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        orig_init(
            self,
            hass,
            driver,
            name,
            entity_id,
            aid,
            config,
            *args,
            **kwargs,
        )

        try:
            from homeassistant.helpers import device_registry as dr, entity_registry as er

            real_serial = None
            entity_reg = er.async_get(hass)
            dev_reg = dr.async_get(hass)

            # 1. Lookup real serial number from HA device registry
            if entity_reg and dev_reg:
                ent_entry = entity_reg.async_get(entity_id)
                if ent_entry and getattr(ent_entry, "device_id", None):
                    dev_entry = dev_reg.async_get(ent_entry.device_id)
                    if (
                        dev_entry
                        and getattr(dev_entry, "serial_number", None)
                        and isinstance(dev_entry.serial_number, str)
                    ):
                        real_serial = dev_entry.serial_number

            # 2. Fallback to entity state attributes if registry lookup is empty
            if not real_serial:
                state = hass.states.get(entity_id)
                if state and state.attributes:
                    val = (
                        state.attributes.get("serial_number")
                        or state.attributes.get("serial")
                        or state.attributes.get("thing_id")
                    )
                    if val and isinstance(val, (str, int)):
                        real_serial = str(val)

            # 3. If a serial number is found, map it directly to HomeKit AccessoryInformation SerialNumber
            if real_serial:
                serv_info = self.get_service("AccessoryInformation")
                if serv_info:
                    serv_info.configure_char("SerialNumber", value=str(real_serial)[:64])
                    _LOGGER.debug(
                        "Mapped HomeKit accessory %s (aid=%s) SerialNumber to %s",
                        entity_id,
                        aid,
                        real_serial,
                    )
        except Exception as err:
            _LOGGER.debug("Could not assign serial number for HomeKit accessory %s: %s", entity_id, err)

    hk_acc.HomeAccessory.__init__ = patched_init
    _LOGGER.info("Successfully enabled HomeKit serial number synchronization for Amway Atmosphere")

    # Update any existing accessories in running HomeKit bridges
    try:
        from homeassistant.helpers import device_registry as dr, entity_registry as er

        entity_reg = er.async_get(hass)
        dev_reg = dr.async_get(hass)

        for hk_entry in hass.config_entries.async_entries("homekit"):
            entry_data = getattr(hk_entry, "runtime_data", None)
            homekit_obj = getattr(entry_data, "homekit", None) if entry_data else None
            if homekit_obj and getattr(homekit_obj, "bridge", None):
                for acc in list(homekit_obj.bridge.accessories.values()):
                    acc_ent_id = getattr(acc, "entity_id", None)
                    if not acc_ent_id:
                        continue
                    real_serial = None
                    if entity_reg and dev_reg:
                        ent_entry = entity_reg.async_get(acc_ent_id)
                        if ent_entry and getattr(ent_entry, "device_id", None):
                            dev_entry = dev_reg.async_get(ent_entry.device_id)
                            if (
                                dev_entry
                                and getattr(dev_entry, "serial_number", None)
                                and isinstance(dev_entry.serial_number, str)
                            ):
                                real_serial = dev_entry.serial_number
                    if not real_serial:
                        state = hass.states.get(acc_ent_id)
                        if state and state.attributes:
                            val = (
                                state.attributes.get("serial_number")
                                or state.attributes.get("serial")
                                or state.attributes.get("thing_id")
                            )
                            if val and isinstance(val, (str, int)):
                                real_serial = str(val)
                    if real_serial:
                        serv_info = acc.get_service("AccessoryInformation")
                        if serv_info:
                            serv_info.configure_char("SerialNumber", value=str(real_serial)[:64])
    except Exception as err:
        _LOGGER.debug("Could not update existing HomeKit accessories: %s", err)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Amway Atmosphere component."""
    _patch_homekit_serial_number(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Amway Atmosphere from a config entry."""
    _patch_homekit_serial_number(hass)
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
