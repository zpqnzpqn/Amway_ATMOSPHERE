"""Test configuration and stubs for Home Assistant."""

import sys
from unittest.mock import MagicMock


class MockGeneric:
    """Mock generic class supporting subscripting like Class[T]."""

    @classmethod
    def __class_getitem__(cls, item):
        return cls


class MockEntity:
    """Base mock entity."""

    def __init__(self, *args, **kwargs):
        pass


class MockCoordinatorEntity(MockGeneric, MockEntity):
    """Mock CoordinatorEntity."""

    def __init__(self, coordinator, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.coordinator = coordinator


class MockDataUpdateCoordinator(MockGeneric):
    """Mock DataUpdateCoordinator."""

    def __init__(self, *args, **kwargs):
        pass


class MockFanEntity(MockGeneric, MockEntity):
    """Mock FanEntity."""
    pass


class MockSensorEntity(MockGeneric, MockEntity):
    """Mock SensorEntity."""
    pass


# Home Assistant submodules
ha = MagicMock()
sys.modules["homeassistant"] = ha
sys.modules["homeassistant.core"] = MagicMock()
sys.modules["homeassistant.config_entries"] = MagicMock()
sys.modules["homeassistant.data_entry_flow"] = MagicMock()
sys.modules["homeassistant.helpers"] = MagicMock()
sys.modules["homeassistant.helpers.aiohttp_client"] = MagicMock()
sys.modules["homeassistant.helpers.entity"] = MagicMock()
sys.modules["homeassistant.helpers.entity.DeviceInfo"] = dict
sys.modules["homeassistant.helpers.entity_platform"] = MagicMock()

coord_mod = MagicMock()
coord_mod.CoordinatorEntity = MockCoordinatorEntity
coord_mod.DataUpdateCoordinator = MockDataUpdateCoordinator
coord_mod.UpdateFailed = Exception
sys.modules["homeassistant.helpers.update_coordinator"] = coord_mod

fan_mod = MagicMock()
fan_mod.FanEntity = MockFanEntity
fan_mod.FanEntityFeature = MagicMock()
sys.modules["homeassistant.components.fan"] = fan_mod

sensor_mod = MagicMock()
sensor_mod.SensorEntity = MockSensorEntity
sensor_mod.SensorDeviceClass = MagicMock()
sensor_mod.SensorStateClass = MagicMock()
sys.modules["homeassistant.components.sensor"] = sensor_mod

sys.modules["voluptuous"] = MagicMock()

