"""DataUpdateCoordinator for Amway Atmosphere."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Dict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import AmwayApiClient, AtmosphereDeviceState
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class AmwayAtmosphereCoordinator(DataUpdateCoordinator[Dict[str, AtmosphereDeviceState]]):
    """Class to manage fetching Amway Atmosphere device data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: AmwayApiClient,
        scan_interval_seconds: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval_seconds),
        )
        self.client = client

    async def _async_update_data(self) -> Dict[str, AtmosphereDeviceState]:
        """Fetch data from Conex API."""
        try:
            devices = await self.client.async_get_devices()
            return {device.thing_id: device for device in devices}
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Amway Conex API: {err}") from err

    async def async_send_remote_button(self, thing_id: str, button_name: str) -> None:
        """Send a button command to a device shadow and request refresh."""
        await self.client.async_send_remote_button(thing_id, button_name)
        # Give AWS IoT and device a brief moment to update reported state before refreshing
        await asyncio.sleep(1.0)
        await self.async_request_refresh()
