"""Support for Amway Atmosphere Air Purifier as Home Assistant Fan entity."""

from __future__ import annotations

import logging
import math
from typing import Any, List, Optional

from homeassistant.components.fan import (
    FanEntity,
    FanEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import AtmosphereDeviceState
from .const import (
    DOMAIN,
    MINI_PRESET_MODES,
    MODEL_SKY,
    PRESET_MODE_AUTO,
    PRESET_MODE_NIGHT,
    PRESET_MODE_TURBO,
    SKY_PRESET_MODES,
)
from .coordinator import AmwayAtmosphereCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Amway Atmosphere fan entities from a config entry."""
    coordinator: AmwayAtmosphereCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        AmwayAtmosphereFan(coordinator, thing_id)
        for thing_id in coordinator.data
    ]
    async_add_entities(entities)


class AmwayAtmosphereFan(CoordinatorEntity[AmwayAtmosphereCoordinator], FanEntity):
    """Representation of an Amway Atmosphere air purifier."""

    _attr_has_entity_name = True
    _attr_name = None  # Uses device name directly as primary entity

    def __init__(
        self, coordinator: AmwayAtmosphereCoordinator, thing_id: str
    ) -> None:
        """Initialize the fan entity."""
        super().__init__(coordinator)
        self._thing_id = thing_id
        self._attr_unique_id = f"{thing_id}_fan"

    @property
    def _device(self) -> Optional[AtmosphereDeviceState]:
        return self.coordinator.data.get(self._thing_id)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry information."""
        dev = self._device
        device_name = dev.device_name if dev else self._thing_id
        model_name = f"Atmosphere {dev.thing_type}" if dev else "Atmosphere Purifier"
        return DeviceInfo(
            identifiers={(DOMAIN, self._thing_id)},
            name=device_name,
            manufacturer="Amway",
            model=model_name,
            configuration_url="https://www.amway.com.tw/sky/",
        )

    @property
    def available(self) -> bool:
        """Return True if device is reported connected by the cloud."""
        dev = self._device
        return dev is not None and dev.connected

    @property
    def supported_features(self) -> FanEntityFeature:
        """Supported features of the air purifier."""
        return (
            FanEntityFeature.SET_SPEED
            | FanEntityFeature.PRESET_MODE
            | FanEntityFeature.TURN_ON
            | FanEntityFeature.TURN_OFF
        )

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the purifier supports."""
        dev = self._device
        if dev and dev.is_sky:
            return 5
        return 3

    @property
    def is_on(self) -> bool:
        """Return true if the purifier is running."""
        dev = self._device
        return dev is not None and dev.speed > 0

    @property
    def percentage(self) -> Optional[int]:
        """Return the current speed percentage."""
        dev = self._device
        if not dev or dev.speed <= 0:
            return 0
        pct = round((dev.speed / self.speed_count) * 100)
        return min(100, max(0, pct))

    @property
    def preset_modes(self) -> List[str]:
        """Return supported preset modes."""
        dev = self._device
        if dev and dev.is_sky:
            return SKY_PRESET_MODES
        return MINI_PRESET_MODES

    @property
    def preset_mode(self) -> Optional[str]:
        """Return current preset mode."""
        dev = self._device
        if not dev or not self.is_on:
            return None
        # In Atmosphere shadow, custom.mode: 1 = Auto, 2 = Night, 3 = Turbo (if Sky)
        mode = dev.mode
        if mode == 1:
            return PRESET_MODE_AUTO
        if mode == 2:
            return PRESET_MODE_NIGHT
        if mode == 3 and dev.is_sky:
            return PRESET_MODE_TURBO
        return None

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the purifier."""
        if percentage == 0:
            await self.async_turn_off()
            return

        # Map percentage to discrete speed step
        step_size = 100.0 / self.speed_count
        speed_step = max(1, min(self.speed_count, round(percentage / step_size)))
        button_name = f"Speed{speed_step}"

        await self.coordinator.async_send_remote_button(self._thing_id, button_name)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set preset mode."""
        button_map = {
            PRESET_MODE_AUTO: "Auto",
            PRESET_MODE_NIGHT: "Night",
            PRESET_MODE_TURBO: "Turbo",
        }
        button_name = button_map.get(preset_mode)
        if not button_name:
            raise ValueError(f"Unsupported preset mode: {preset_mode}")

        dev = self._device
        if button_name == "Turbo" and dev and not dev.is_sky:
            raise ValueError("Turbo mode is only supported on Atmosphere Sky")

        await self.coordinator.async_send_remote_button(self._thing_id, button_name)

    async def async_turn_on(
        self,
        percentage: Optional[int] = None,
        preset_mode: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the air purifier."""
        if preset_mode:
            await self.async_set_preset_mode(preset_mode)
            return

        if percentage is not None:
            await self.async_set_percentage(percentage)
            return

        # Default turn on with Power button (or Auto)
        await self.coordinator.async_send_remote_button(self._thing_id, "Power")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the air purifier."""
        if self.is_on:
            await self.coordinator.async_send_remote_button(self._thing_id, "Power")
