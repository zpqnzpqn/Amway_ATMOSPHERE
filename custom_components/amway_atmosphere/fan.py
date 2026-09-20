"""Support for Amway Atmosphere Air Purifier as Home Assistant Fan entity."""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional

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
    DEFAULT_NAME_MINI,
    DEFAULT_NAME_SKY,
    DOMAIN,
    MINI_NIGHT_MAX_SPEED,
    MINI_PRESET_MODES,
    MINI_SPEED_PERCENTAGES,
    MODEL_SKY,
    PRESET_MODE_AUTO,
    PRESET_MODE_NIGHT,
    PRESET_MODE_TURBO,
    SKY_NIGHT_MAX_SPEED,
    SKY_PRESET_MODES,
    SKY_SPEED_PERCENTAGES,
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
    known_thing_ids = set()

    def _discover_new_entities() -> None:
        new_entities = []
        for thing_id in coordinator.data:
            if thing_id not in known_thing_ids:
                known_thing_ids.add(thing_id)
                new_entities.append(AmwayAtmosphereFan(coordinator, thing_id))
        if new_entities:
            async_add_entities(new_entities)

    _discover_new_entities()
    entry.async_on_unload(coordinator.async_add_listener(_discover_new_entities))


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
        device_name = (
            dev.device_name
            if (dev and dev.device_name)
            else (DEFAULT_NAME_MINI if (dev and dev.is_mini) else DEFAULT_NAME_SKY)
        )
        model_name = (
            DEFAULT_NAME_SKY if (dev and dev.is_sky) else DEFAULT_NAME_MINI
        )
        return DeviceInfo(
            identifiers={(DOMAIN, self._thing_id)},
            name=self._thing_id,
            manufacturer="Amway",
            model=model_name,
            serial_number=self._thing_id,
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

        # Turbo mode is always 100%
        if self.preset_mode == PRESET_MODE_TURBO:
            return 100

        if dev.is_sky:
            # 5 speeds: 20%, 40%, 60%, 80%, 100%
            idx = min(len(SKY_SPEED_PERCENTAGES), max(1, dev.speed)) - 1
            return SKY_SPEED_PERCENTAGES[idx]
        else:
            # 3 speeds: 33%, 67%, 100%
            idx = min(len(MINI_SPEED_PERCENTAGES), max(1, dev.speed)) - 1
            return MINI_SPEED_PERCENTAGES[idx]

    @property
    def preset_modes(self) -> List[str]:
        """Return supported preset modes (Auto, Night, Turbo)."""
        dev = self._device
        if dev and dev.is_sky:
            return SKY_PRESET_MODES
        return MINI_PRESET_MODES

    @property
    def preset_mode(self) -> Optional[str]:
        """Return current preset mode (Auto, Night, or Turbo)."""
        dev = self._device
        if not dev or not self.is_on:
            return None

        # Mode in Atmosphere Shadow:
        # 1 = Auto, 2 = Night, 3 = Turbo (Sky only), 0 = Manual
        mode = dev.mode
        if mode == 1:
            return PRESET_MODE_AUTO
        if mode == 2:
            return PRESET_MODE_NIGHT
        if mode == 3 and dev.is_sky:
            return PRESET_MODE_TURBO
        return None

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage with Night mode boundary constraints."""
        if percentage == 0:
            await self.async_turn_off()
            return

        dev = self._device
        is_sky = dev.is_sky if dev else True

        # Map percentage to speed step
        if is_sky:
            if percentage <= 20:
                speed_step = 1
            elif percentage <= 40:
                speed_step = 2
            elif percentage <= 60:
                speed_step = 3
            elif percentage <= 80:
                speed_step = 4
            else:
                speed_step = 5
        else:
            if percentage <= 33:
                speed_step = 1
            elif percentage <= 67:
                speed_step = 2
            else:
                speed_step = 3

        # Constraint: When in Night mode, speed is strictly constrained
        # (Sky: speed 1 or 2; Mini: speed 1 only)
        if self.preset_mode == PRESET_MODE_NIGHT:
            max_night_speed = SKY_NIGHT_MAX_SPEED if is_sky else MINI_NIGHT_MAX_SPEED
            speed_step = min(speed_step, max_night_speed)

        button_name = f"Speed{speed_step}"
        await self.coordinator.async_send_remote_button(self._thing_id, button_name)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set preset mode with strict 3-way mutual locking (Auto / Night / Turbo)."""
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

        # Mutual locking: Sending the target button automatically switches mode in Cloud Shadow,
        # clearing the other two modes.
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

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return entity specific state attributes."""
        dev = self._device
        attrs = {
            "serial_number": self._thing_id,
            "thing_id": self._thing_id,
        }
        if dev:
            attrs["speed_step"] = dev.speed
            attrs["mode_raw"] = dev.mode
            if dev.mode == 1:
                attrs["operating_mode"] = "Auto"
            elif dev.mode == 2:
                attrs["operating_mode"] = "Night"
            elif dev.mode == 3:
                attrs["operating_mode"] = "Turbo"
            else:
                attrs["operating_mode"] = "Manual"
        return attrs

