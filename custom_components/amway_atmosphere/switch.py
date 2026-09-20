"""Support for Amway Atmosphere mode switches with mutual locking."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from homeassistant.components.switch import SwitchEntity
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
    PRESET_MODE_AUTO,
    PRESET_MODE_NIGHT,
    PRESET_MODE_TURBO,
)
from .coordinator import AmwayAtmosphereCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Amway Atmosphere mode switch entities from a config entry."""
    coordinator: AmwayAtmosphereCoordinator = hass.data[DOMAIN][entry.entry_id]
    known_thing_ids = set()

    def _discover_new_entities() -> None:
        new_entities: List[SwitchEntity] = []
        for thing_id, dev in coordinator.data.items():
            if thing_id not in known_thing_ids:
                known_thing_ids.add(thing_id)
                # Auto and Night mode switches are supported on all models
                new_entities.append(AmwayAutoModeSwitch(coordinator, thing_id))
                new_entities.append(AmwayNightModeSwitch(coordinator, thing_id))

                # Turbo mode switch is supported only on Atmosphere Sky
                if dev.is_sky:
                    new_entities.append(AmwayTurboModeSwitch(coordinator, thing_id))

        if new_entities:
            async_add_entities(new_entities)

    _discover_new_entities()
    entry.async_on_unload(coordinator.async_add_listener(_discover_new_entities))


class AmwayModeSwitchBase(CoordinatorEntity[AmwayAtmosphereCoordinator], SwitchEntity):
    """Base class for Amway Atmosphere mode switches."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: AmwayAtmosphereCoordinator, thing_id: str
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)
        self._thing_id = thing_id

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
        """Return True if device is connected."""
        dev = self._device
        return dev is not None and dev.connected

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        dev = self._device
        return {
            "serial_number": self._thing_id,
            "thing_id": self._thing_id,
            "operating_mode_raw": dev.mode if dev else None,
        }

    async def _async_revert_to_manual(self) -> None:
        """Revert purifier to manual mode at current speed when a mode switch is turned off."""
        dev = self._device
        current_speed = max(1, dev.speed) if (dev and dev.speed > 0) else 1
        await self.coordinator.async_send_remote_button(
            self._thing_id, f"Speed{current_speed}"
        )


class AmwayAutoModeSwitch(AmwayModeSwitchBase):
    """Switch entity for Atmosphere Auto Mode."""

    def __init__(
        self, coordinator: AmwayAtmosphereCoordinator, thing_id: str
    ) -> None:
        super().__init__(coordinator, thing_id)
        self._attr_name = "Auto Mode"
        self._attr_unique_id = f"{thing_id}_switch_auto"
        self._attr_icon = "mdi:fan-auto"

    @property
    def is_on(self) -> bool:
        """Return True if purifier is in Auto mode (mode = 1)."""
        dev = self._device
        return dev is not None and dev.speed > 0 and dev.mode == 1

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on Auto mode (automatically deactivates Night and Turbo)."""
        await self.coordinator.async_send_remote_button(self._thing_id, "Auto")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off Auto mode, reverting to manual speed."""
        if self.is_on:
            await self._async_revert_to_manual()


class AmwayNightModeSwitch(AmwayModeSwitchBase):
    """Switch entity for Atmosphere Night Mode."""

    def __init__(
        self, coordinator: AmwayAtmosphereCoordinator, thing_id: str
    ) -> None:
        super().__init__(coordinator, thing_id)
        self._attr_name = "Night Mode"
        self._attr_unique_id = f"{thing_id}_switch_night"
        self._attr_icon = "mdi:weather-night"

    @property
    def is_on(self) -> bool:
        """Return True if purifier is in Night mode (mode = 2)."""
        dev = self._device
        return dev is not None and dev.speed > 0 and dev.mode == 2

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on Night mode (automatically deactivates Auto and Turbo)."""
        await self.coordinator.async_send_remote_button(self._thing_id, "Night")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off Night mode, reverting to manual speed."""
        if self.is_on:
            await self._async_revert_to_manual()


class AmwayTurboModeSwitch(AmwayModeSwitchBase):
    """Switch entity for Atmosphere Sky Turbo Mode."""

    def __init__(
        self, coordinator: AmwayAtmosphereCoordinator, thing_id: str
    ) -> None:
        super().__init__(coordinator, thing_id)
        self._attr_name = "Turbo Mode"
        self._attr_unique_id = f"{thing_id}_switch_turbo"
        self._attr_icon = "mdi:fan-speed-3"

    @property
    def is_on(self) -> bool:
        """Return True if purifier is in Turbo mode (mode = 3)."""
        dev = self._device
        return dev is not None and dev.speed > 0 and dev.is_sky and dev.mode == 3

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on Turbo mode (automatically deactivates Auto and Night)."""
        dev = self._device
        if dev and not dev.is_sky:
            raise ValueError("Turbo mode is only supported on Atmosphere Sky")
        await self.coordinator.async_send_remote_button(self._thing_id, "Turbo")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off Turbo mode, reverting to manual speed."""
        if self.is_on:
            await self._async_revert_to_manual()
