"""Support for Amway Atmosphere air quality and filter sensors."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
try:
    from homeassistant.const import CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
except Exception:
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER = "µg/m³"
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import AtmosphereDeviceState
from .const import (
    AIR_QUALITY_LEVELS,
    DEFAULT_NAME_MINI,
    DEFAULT_NAME_SKY,
    DOMAIN,
)
from .coordinator import AmwayAtmosphereCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Amway Atmosphere sensor entities from a config entry."""
    coordinator: AmwayAtmosphereCoordinator = hass.data[DOMAIN][entry.entry_id]
    known_thing_ids = set()

    def _discover_new_entities() -> None:
        new_entities: List[SensorEntity] = []
        for thing_id, dev in coordinator.data.items():
            if thing_id not in known_thing_ids:
                known_thing_ids.add(thing_id)
                # Air Quality Sensor (Levels 1-5 qualitative enum)
                new_entities.append(AmwayAirQualitySensor(coordinator, thing_id))

                # PM2.5 Sensor (Numeric density for Apple HomeKit native Air Quality)
                new_entities.append(AmwayPM25Sensor(coordinator, thing_id))

                # Clean Air Value Sensor
                new_entities.append(AmwayCleanAirSensor(coordinator, thing_id))

                # Filter Life Sensors
                new_entities.append(
                    AmwayFilterSensor(
                        coordinator,
                        thing_id,
                        filter_type="prefilter",
                        name="Pre-Filter Life",
                        key="prefilter_life_left",
                        icon="mdi:filter-outline",
                    )
                )
                new_entities.append(
                    AmwayFilterSensor(
                        coordinator,
                        thing_id,
                        filter_type="hepa",
                        name="HEPA Filter Life",
                        key="hepa_life_left",
                        icon="mdi:air-filter",
                    )
                )

                # Carbon Filter Life (Sky models only)
                if dev.is_sky or dev.carbon_life_left is not None:
                    new_entities.append(
                        AmwayFilterSensor(
                            coordinator,
                            thing_id,
                            filter_type="carbon",
                            name="Carbon Filter Life",
                            key="carbon_life_left",
                            icon="mdi:molecule",
                        )
                    )
        if new_entities:
            async_add_entities(new_entities)

    _discover_new_entities()
    entry.async_on_unload(coordinator.async_add_listener(_discover_new_entities))


class AmwayAtmosphereSensorBase(
    CoordinatorEntity[AmwayAtmosphereCoordinator], SensorEntity
):
    """Base class for Amway Atmosphere sensors."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: AmwayAtmosphereCoordinator, thing_id: str
    ) -> None:
        """Initialize sensor."""
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
            sw_version=dev.sw_version if dev else None,
            hw_version=dev.hw_version if dev else None,
            configuration_url="https://www.amway.com.tw/sky/",
        )

    @property
    def available(self) -> bool:
        """Return True if device is connected."""
        dev = self._device
        return dev is not None and dev.connected

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return base extra state attributes including serial_number."""
        return {
            "serial_number": self._thing_id,
            "serial": self._thing_id,
            "serial_no": self._thing_id,
            "thing_id": self._thing_id,
        }


class AmwayAirQualitySensor(AmwayAtmosphereSensorBase):
    """Air Quality rating sensor directly mapped to Apple HomeKit 5-tier standard."""

    def __init__(
        self, coordinator: AmwayAtmosphereCoordinator, thing_id: str
    ) -> None:
        super().__init__(coordinator, thing_id)
        self._attr_name = "Air Quality"
        self._attr_unique_id = f"{thing_id}_air_quality"
        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_options = ["excellent", "good", "fair", "inferior", "poor"]
        self._attr_icon = "mdi:air-purifier"

    @property
    def native_value(self) -> Optional[str]:
        """Return qualitative air rating."""
        dev = self._device
        if not dev or dev.dust_level is None:
            return None
        return AIR_QUALITY_LEVELS.get(dev.dust_level, "good")

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Extra air quality attributes."""
        attrs = dict(super().extra_state_attributes)
        dev = self._device
        if dev:
            attrs.update({
                "dust_level": dev.dust_level,
                "clean_air_val": dev.clean_air_val,
            })
        return attrs


# Standard PM2.5 density mappings (µg/m³) based on Apple HomeKit thresholds:
# Level 1 (Excellent): <= 9.0 µg/m³
# Level 2 (Good): 10 ~ 35.4 µg/m³
# Level 3 (Fair): 35.5 ~ 55.4 µg/m³
# Level 4 (Inferior): 55.5 ~ 125.4 µg/m³
# Level 5 (Poor): > 125.4 µg/m³
DUST_LEVEL_TO_PM25: Dict[int, float] = {
    1: 5.0,
    2: 18.0,
    3: 45.0,
    4: 80.0,
    5: 150.0,
}


class AmwayPM25Sensor(AmwayAtmosphereSensorBase):
    """PM2.5 Sensor directly providing numeric density for Apple HomeKit Air Quality accessories."""

    def __init__(
        self, coordinator: AmwayAtmosphereCoordinator, thing_id: str
    ) -> None:
        super().__init__(coordinator, thing_id)
        self._attr_name = "PM2.5"
        self._attr_unique_id = f"{thing_id}_pm25"
        self._attr_device_class = SensorDeviceClass.PM25
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
        self._attr_icon = "mdi:air-filter"

    @property
    def native_value(self) -> Optional[float]:
        """Return numeric PM2.5 reading."""
        dev = self._device
        if not dev or dev.dust_level is None:
            return None
        return DUST_LEVEL_TO_PM25.get(dev.dust_level, 18.0)


class AmwayCleanAirSensor(AmwayAtmosphereSensorBase):
    """Clean air delivery value sensor."""

    def __init__(
        self, coordinator: AmwayAtmosphereCoordinator, thing_id: str
    ) -> None:
        super().__init__(coordinator, thing_id)
        self._attr_name = "Clean Air Value"
        self._attr_unique_id = f"{thing_id}_clean_air_val"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:weather-windy"

    @property
    def native_value(self) -> Optional[int]:
        """Return clean air reading."""
        dev = self._device
        if not dev:
            return None
        return dev.clean_air_val


class AmwayFilterSensor(AmwayAtmosphereSensorBase):
    """Filter lifecycle percentage sensor."""

    def __init__(
        self,
        coordinator: AmwayAtmosphereCoordinator,
        thing_id: str,
        filter_type: str,
        name: str,
        key: str,
        icon: str,
    ) -> None:
        super().__init__(coordinator, thing_id)
        self._filter_key = key
        self._attr_name = name
        self._attr_unique_id = f"{thing_id}_{filter_type}_life"
        self._attr_native_unit_of_measurement = "%"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = icon

    @property
    def native_value(self) -> Optional[int]:
        """Return remaining filter life percentage."""
        dev = self._device
        if not dev:
            return None
        val = getattr(dev, self._filter_key, None)
        if val is None:
            return None
        return max(0, min(100, int(val)))
