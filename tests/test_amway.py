"""Unit tests for Amway Atmosphere integration."""

import datetime
import json
import math
import pytest

from custom_components.amway_atmosphere.api import (
    AtmosphereDeviceState,
    sign_aws_v4,
)
from custom_components.amway_atmosphere.config_flow import _extract_code
from custom_components.amway_atmosphere.const import (
    AIR_QUALITY_LEVELS,
    DEFAULT_NAME_MINI,
    DEFAULT_NAME_SKY,
    MODEL_MINI,
    MODEL_SKY,
    PRESET_MODE_AUTO,
    PRESET_MODE_NIGHT,
    PRESET_MODE_TURBO,
)


class TestAmwayAuth:
    """Test authentication and code parsing helpers."""

    def test_extract_code_from_full_url(self):
        url = "amwayhealthyhome://loginRedirect?code=7a3b4c5d-1111-2222-3333-444455556666&state=amway_ha&scope=openid"
        assert _extract_code(url) == "7a3b4c5d-1111-2222-3333-444455556666"

    def test_extract_code_from_raw_code(self):
        raw = " 7a3b4c5d-1111-2222-3333-444455556666 \n"
        assert _extract_code(raw) == "7a3b4c5d-1111-2222-3333-444455556666"

    def test_get_authorization_url_targets_official_account2_portal(self):
        from custom_components.amway_atmosphere.api import AmwayApiClient

        url_tw = AmwayApiClient.get_authorization_url(country="TW")
        assert "account2.amwayglobal.com/v1/proxy/oauth2" in url_tw
        assert "clientapp=healthyhomeTW" in url_tw
        assert "redirect_uri=amwayhealthyhome%3A%2F%2FloginRedirect" in url_tw
        assert "client_id=7b90a30d-b404-4da7-a72b-449db798387c" in url_tw
        # Critical assertion: Must NOT target the green LDAP maintenance endpoint
        assert "gluu-prod01-prod.amstack-amwayidv2-prod" not in url_tw

    def test_device_connected_extracted_from_shadow_system(self):
        import asyncio
        from unittest.mock import AsyncMock
        from custom_components.amway_atmosphere.api import AmwayApiClient

        async def _run():
            from unittest.mock import MagicMock
            mock_session = MagicMock()
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json = AsyncMock(return_value=[
                {
                    "thingId": "TEST_THING_01",
                    "thingType": "sky",
                    "info": {"thingInfo": {"deviceName": "Living Room"}},
                    "shadow": {
                        "payload": json.dumps({
                            "state": {
                                "reported": {
                                    "system": {"connected": True},
                                    "display": {"speed": 2, "dust": 1},
                                }
                            }
                        })
                    }
                }
            ])
            mock_session.request.return_value.__aenter__.return_value = mock_resp

            client = AmwayApiClient(session=mock_session, access_token="mock_token")
            devices = await client.async_get_devices()
            assert len(devices) == 1
            assert devices[0].connected is True
            assert devices[0].speed == 2
            # Verify official full name is used instead of app name
            assert devices[0].device_name == DEFAULT_NAME_SKY

        asyncio.run(_run())

    def test_official_device_full_names_from_api_and_entities(self):
        """Test that device names ignore app name and strictly follow official model full name."""
        import asyncio
        from unittest.mock import AsyncMock, MagicMock
        from custom_components.amway_atmosphere.api import AmwayApiClient
        from custom_components.amway_atmosphere.fan import AmwayAtmosphereFan
        from custom_components.amway_atmosphere.sensor import AmwayAirQualitySensor

        async def _run():
            mock_session = MagicMock()
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json = AsyncMock(return_value=[
                {
                    "thingId": "SKY_DEVICE_01",
                    "thingType": "sky",
                    "info": {"thingInfo": {"deviceName": "My Custom Sky Room"}},
                    "shadow": {}
                },
                {
                    "thingId": "MINI_DEVICE_02",
                    "thingType": "sky-mini",
                    "info": {"thingInfo": {"deviceName": "My Custom Mini Bedroom"}},
                    "shadow": {}
                }
            ])
            mock_session.request.return_value.__aenter__.return_value = mock_resp

            client = AmwayApiClient(session=mock_session, access_token="mock_token")
            devices = await client.async_get_devices()
            assert len(devices) == 2

            sky_dev = devices[0]
            mini_dev = devices[1]

            # 1. API device_name strictly follows official names
            assert sky_dev.device_name == "Atmosphere Sky™ Air Treatment System"
            assert mini_dev.device_name == "Atmosphere Mini™ Air Treatment System"

            # 2. Fan and Sensor device_info name, model and serial_number strictly match
            coordinator = MagicMock()
            coordinator.data = {sky_dev.thing_id: sky_dev, mini_dev.thing_id: mini_dev}

            fan_sky = AmwayAtmosphereFan(coordinator, sky_dev.thing_id)
            sensor_sky = AmwayAirQualitySensor(coordinator, sky_dev.thing_id)
            assert fan_sky.device_info["name"] == "SKY_DEVICE_01"
            assert fan_sky.device_info["model"] == "Atmosphere Sky™ Air Treatment System"
            assert fan_sky.device_info["serial_number"] == "SKY_DEVICE_01"
            assert fan_sky.extra_state_attributes["serial_number"] == "SKY_DEVICE_01"

            assert sensor_sky.device_info["name"] == "SKY_DEVICE_01"
            assert sensor_sky.device_info["model"] == "Atmosphere Sky™ Air Treatment System"
            assert sensor_sky.device_info["serial_number"] == "SKY_DEVICE_01"
            assert sensor_sky.extra_state_attributes["serial_number"] == "SKY_DEVICE_01"

            fan_mini = AmwayAtmosphereFan(coordinator, mini_dev.thing_id)
            sensor_mini = AmwayAirQualitySensor(coordinator, mini_dev.thing_id)
            assert fan_mini.device_info["name"] == "MINI_DEVICE_02"
            assert fan_mini.device_info["model"] == "Atmosphere Mini™ Air Treatment System"
            assert fan_mini.device_info["serial_number"] == "MINI_DEVICE_02"
            assert fan_mini.extra_state_attributes["serial_number"] == "MINI_DEVICE_02"

            assert sensor_mini.device_info["name"] == "MINI_DEVICE_02"
            assert sensor_mini.device_info["model"] == "Atmosphere Mini™ Air Treatment System"
            assert sensor_mini.device_info["serial_number"] == "MINI_DEVICE_02"
            assert sensor_mini.extra_state_attributes["serial_number"] == "MINI_DEVICE_02"

        asyncio.run(_run())

    def test_auto_mode_speed_display_and_manual_switch_unlock(self):
        """Test Plan A: Auto mode tracks live speed percentage; manual percentage adjustment clears all 3 locks."""
        import asyncio
        from unittest.mock import AsyncMock, MagicMock
        from custom_components.amway_atmosphere.fan import AmwayAtmosphereFan

        async def _run():
            coordinator = MagicMock()
            dev = AtmosphereDeviceState(
                thing_id="sky-001",
                thing_type=MODEL_SKY,
                device_name="Atmosphere Sky™ Air Treatment System",
                connected=True,
                speed=1,
                dust_level=1,
                mode=1,  # Auto mode
                clean_air_val=100,
                prefilter_life_left=90,
                hepa_life_left=95,
                carbon_life_left=80,
                child_lock=False,
                raw_shadow={},
            )
            coordinator.data = {"sky-001": dev}
            coordinator.async_send_remote_button = AsyncMock()

            fan = AmwayAtmosphereFan(coordinator, "sky-001")

            # 1. In Auto mode at Speed 1 -> preset is Auto, percentage is 20%
            assert fan.preset_mode == PRESET_MODE_AUTO
            assert fan.percentage == 20

            # 2. Air quality worsens -> Purifier automatically speeds up to Speed 4
            dev.speed = 4
            assert fan.preset_mode == PRESET_MODE_AUTO
            assert fan.percentage == 80

            # 3. User manually adjusts percentage to 40% (Speed 2)
            await fan.async_set_percentage(40)
            coordinator.async_send_remote_button.assert_called_with("sky-001", "Speed2")

            # 4. Cloud shadow switches mode to Manual (mode = 0)
            dev.mode = 0
            dev.speed = 2
            assert fan.percentage == 40
            # All three locks (Auto, Night, Turbo) are OFF (preset_mode is None)
            assert fan.preset_mode is None

        asyncio.run(_run())




class TestAwsSigV4:
    """Test AWS Signature Version 4 calculation."""

    def test_sign_aws_v4_headers(self):
        url = "https://axnk9oqlqxcqh-ats.iot.us-east-1.amazonaws.com/things/test-sky-01/shadow"
        payload = b'{"state":{"desired":{"RemoteButton":"Speed3"}}}'
        headers = {"Content-Type": "application/x-amz-json-1.0"}
        frozen_time = datetime.datetime(2026, 9, 20, 12, 0, 0, tzinfo=datetime.timezone.utc)

        signed = sign_aws_v4(
            method="POST",
            url=url,
            region="us-east-1",
            service="iotdata",
            access_key="ASIATESTKEY123",
            secret_key="secretkey456",
            session_token="token789",
            payload=payload,
            headers=headers,
            now=frozen_time,
        )

        assert "authorization" in signed
        assert signed["authorization"].startswith("AWS4-HMAC-SHA256 Credential=ASIATESTKEY123/20260920/us-east-1/iotdata/aws4_request")
        assert "SignedHeaders=content-type;host;x-amz-content-sha256;x-amz-date;x-amz-security-token" in signed["authorization"]
        assert signed["x-amz-date"] == "20260920T120000Z"
        assert signed["x-amz-security-token"] == "token789"
        assert signed["host"] == "axnk9oqlqxcqh-ats.iot.us-east-1.amazonaws.com"


class TestAtmosphereDeviceStateParsing:
    """Test parsing raw cloud payloads into AtmosphereDeviceState."""

    def test_sky_state_parsing(self):
        raw_shadow = {
            "state": {
                "reported": {
                    "display": {"speed": 4, "dust": 2},
                    "system": {
                        "childLock": False,
                        "custom": {"mode": 1, "cleanAirVal": 350},
                    },
                    "prefilter": {"lifeLeft": 85},
                    "hepa": {"lifeLeft": 92},
                    "carbon": {"lifeLeft": 78},
                }
            }
        }
        dev = AtmosphereDeviceState(
            thing_id="sky-001",
            thing_type=MODEL_SKY,
            device_name="Living Room Sky",
            connected=True,
            speed=4,
            dust_level=2,
            mode=1,
            clean_air_val=350,
            prefilter_life_left=85,
            hepa_life_left=92,
            carbon_life_left=78,
            child_lock=False,
            raw_shadow=raw_shadow,
        )

        assert dev.is_sky is True
        assert dev.is_mini is False
        assert dev.max_speed == 5
        assert dev.speed == 4
        assert dev.dust_level == 2
        assert AIR_QUALITY_LEVELS[dev.dust_level] == "good"

    def test_mini_state_parsing(self):
        dev = AtmosphereDeviceState(
            thing_id="mini-001",
            thing_type=MODEL_MINI,
            device_name="Bedroom Mini",
            connected=True,
            speed=2,
            dust_level=1,
            mode=2,
            clean_air_val=180,
            prefilter_life_left=90,
            hepa_life_left=88,
            carbon_life_left=None,
            child_lock=True,
            raw_shadow={},
        )

        assert dev.is_sky is False
        assert dev.is_mini is True
        assert dev.max_speed == 3
        assert dev.speed == 2
        assert dev.carbon_life_left is None
        assert AIR_QUALITY_LEVELS[dev.dust_level] == "excellent"


class TestSpeedPercentageMapping:
    """Test fan speed and HomeKit percentage mappings."""

    def test_sky_5_speeds_to_percentage(self):
        # 5 speeds: 1..5
        speed_count = 5
        percentages = [round((s / speed_count) * 100) for s in range(1, 6)]
        assert percentages == [20, 40, 60, 80, 100]

    def test_mini_3_speeds_to_percentage(self):
        # 3 speeds: 1..3
        speed_count = 3
        percentages = [round((s / speed_count) * 100) for s in range(1, 4)]
        assert percentages == [33, 67, 100]

    def test_percentage_to_speed_step_sky(self):
        speed_count = 5
        step_size = 100.0 / speed_count
        test_cases = [
            (5, 1),
            (20, 1),
            (25, 1),
            (35, 2),
            (40, 2),
            (55, 3),
            (60, 3),
            (75, 4),
            (80, 4),
            (95, 5),
            (100, 5),
        ]
        for pct, expected_speed in test_cases:
            step = max(1, min(speed_count, round(pct / step_size)))
            assert step == expected_speed, f"Percentage {pct}% should map to speed {expected_speed}"

    def test_percentage_to_speed_step_mini(self):
        speed_count = 3
        step_size = 100.0 / speed_count
        test_cases = [
            (10, 1),
            (33, 1),
            (50, 2),
            (67, 2),
            (80, 2),
            (85, 3),
            (100, 3),
        ]
        for pct, expected_speed in test_cases:
            step = max(1, min(speed_count, round(pct / step_size)))
            assert step == expected_speed, f"Percentage {pct}% should map to speed {expected_speed}"


class TestHomeKitAirQualityMapping:
    """Test that all 5 dust levels map to HomeKit air quality ratings."""

    def test_all_five_ratings(self):
        assert AIR_QUALITY_LEVELS[1] == "excellent"
        assert AIR_QUALITY_LEVELS[2] == "good"
        assert AIR_QUALITY_LEVELS[3] == "fair"
        assert AIR_QUALITY_LEVELS[4] == "inferior"
        assert AIR_QUALITY_LEVELS[5] == "poor"


class TestAmwayEntities:
    """Test Fan and Sensor entity behaviors."""

    def test_fan_entity_sky(self):
        import asyncio
        from unittest.mock import AsyncMock, MagicMock
        from custom_components.amway_atmosphere.fan import AmwayAtmosphereFan

        async def _run():
            coordinator = MagicMock()
            dev = AtmosphereDeviceState(
                thing_id="sky-001",
                thing_type=MODEL_SKY,
                device_name="Living Room Sky",
                connected=True,
                speed=3,
                dust_level=1,
                mode=1,  # Auto
                clean_air_val=300,
                prefilter_life_left=90,
                hepa_life_left=95,
                carbon_life_left=80,
                child_lock=False,
                raw_shadow={},
            )
            coordinator.data = {"sky-001": dev}
            coordinator.async_send_remote_button = AsyncMock()

            fan = AmwayAtmosphereFan(coordinator, "sky-001")
            assert fan.is_on is True
            assert fan.speed_count == 5
            assert fan.percentage == 60
            assert fan.preset_mode == PRESET_MODE_AUTO
            assert PRESET_MODE_TURBO in fan.preset_modes

            await fan.async_set_percentage(100)
            coordinator.async_send_remote_button.assert_called_with("sky-001", "Speed5")

            await fan.async_set_preset_mode(PRESET_MODE_TURBO)
            coordinator.async_send_remote_button.assert_called_with("sky-001", "Turbo")

            await fan.async_turn_off()
            coordinator.async_send_remote_button.assert_called_with("sky-001", "Power")

        asyncio.run(_run())

    def test_fan_entity_mini(self):
        import asyncio
        from unittest.mock import AsyncMock, MagicMock
        from custom_components.amway_atmosphere.fan import AmwayAtmosphereFan

        async def _run():
            coordinator = MagicMock()
            dev = AtmosphereDeviceState(
                thing_id="mini-001",
                thing_type=MODEL_MINI,
                device_name="Mini",
                connected=True,
                speed=1,
                dust_level=2,
                mode=2,  # Night
                clean_air_val=120,
                prefilter_life_left=90,
                hepa_life_left=85,
                carbon_life_left=None,
                child_lock=False,
                raw_shadow={},
            )
            coordinator.data = {"mini-001": dev}
            coordinator.async_send_remote_button = AsyncMock()

            fan = AmwayAtmosphereFan(coordinator, "mini-001")
            assert fan.speed_count == 3
            assert fan.percentage == 33
            assert fan.preset_mode == PRESET_MODE_NIGHT
            assert PRESET_MODE_TURBO not in fan.preset_modes

            with pytest.raises(ValueError):
                await fan.async_set_preset_mode(PRESET_MODE_TURBO)

        asyncio.run(_run())

    def test_fan_preset_modes_interlocking(self):
        import asyncio
        from unittest.mock import AsyncMock, MagicMock
        from custom_components.amway_atmosphere.fan import AmwayAtmosphereFan

        async def _run():
            coordinator = MagicMock()
            dev = AtmosphereDeviceState(
                thing_id="sky-001",
                thing_type=MODEL_SKY,
                device_name="Sky",
                connected=True,
                speed=2,
                dust_level=1,
                mode=1,  # Currently Auto
                clean_air_val=300,
                prefilter_life_left=90,
                hepa_life_left=95,
                carbon_life_left=80,
                child_lock=False,
                raw_shadow={},
            )
            coordinator.data = {"sky-001": dev}
            coordinator.async_send_remote_button = AsyncMock()

            fan = AmwayAtmosphereFan(coordinator, "sky-001")
            assert fan.preset_mode == PRESET_MODE_AUTO

            # 1. Switch to Night (disables Auto/Turbo)
            await fan.async_set_preset_mode(PRESET_MODE_NIGHT)
            coordinator.async_send_remote_button.assert_called_with("sky-001", "Night")

            # 2. Switch to Turbo (disables Auto/Night)
            coordinator.async_send_remote_button.reset_mock()
            await fan.async_set_preset_mode(PRESET_MODE_TURBO)
            coordinator.async_send_remote_button.assert_called_with("sky-001", "Turbo")

            # 3. Switch to Auto (disables Night/Turbo)
            coordinator.async_send_remote_button.reset_mock()
            await fan.async_set_preset_mode(PRESET_MODE_AUTO)
            coordinator.async_send_remote_button.assert_called_with("sky-001", "Auto")

            # 4. Switch to Manual/Percentage unlocks preset modes
            coordinator.async_send_remote_button.reset_mock()
            await fan.async_set_percentage(40)
            coordinator.async_send_remote_button.assert_called_with("sky-001", "Speed2")

        asyncio.run(_run())

    def test_night_mode_speed_constraint(self):
        import asyncio
        from unittest.mock import AsyncMock, MagicMock
        from custom_components.amway_atmosphere.fan import AmwayAtmosphereFan

        async def _run():
            coordinator = MagicMock()
            # Sky in Night mode (mode=2)
            dev_sky = AtmosphereDeviceState(
                thing_id="sky-001",
                thing_type=MODEL_SKY,
                device_name="Sky",
                connected=True,
                speed=1,
                dust_level=1,
                mode=2,  # Night
                clean_air_val=300,
                prefilter_life_left=90,
                hepa_life_left=95,
                carbon_life_left=80,
                child_lock=False,
                raw_shadow={},
            )
            # Mini in Night mode (mode=2)
            dev_mini = AtmosphereDeviceState(
                thing_id="mini-001",
                thing_type=MODEL_MINI,
                device_name="Mini",
                connected=True,
                speed=1,
                dust_level=1,
                mode=2,  # Night
                clean_air_val=150,
                prefilter_life_left=90,
                hepa_life_left=90,
                carbon_life_left=None,
                child_lock=False,
                raw_shadow={},
            )
            coordinator.data = {"sky-001": dev_sky, "mini-001": dev_mini}
            coordinator.async_send_remote_button = AsyncMock()

            fan_sky = AmwayAtmosphereFan(coordinator, "sky-001")
            fan_mini = AmwayAtmosphereFan(coordinator, "mini-001")

            # Sky in night mode: Requesting 100% (Speed 5) should be clamped to Speed 2
            await fan_sky.async_set_percentage(100)
            coordinator.async_send_remote_button.assert_called_with("sky-001", "Speed2")

            # Sky in night mode: Requesting 20% (Speed 1) stays Speed 1
            coordinator.async_send_remote_button.reset_mock()
            await fan_sky.async_set_percentage(20)
            coordinator.async_send_remote_button.assert_called_with("sky-001", "Speed1")

            # Mini in night mode: Requesting 100% (Speed 3) should be clamped to Speed 1
            coordinator.async_send_remote_button.reset_mock()
            await fan_mini.async_set_percentage(100)
            coordinator.async_send_remote_button.assert_called_with("mini-001", "Speed1")

        asyncio.run(_run())

    def test_turbo_mode_speed_100(self):
        from unittest.mock import MagicMock
        from custom_components.amway_atmosphere.fan import AmwayAtmosphereFan

        coordinator = MagicMock()
        dev_turbo = AtmosphereDeviceState(
            thing_id="sky-001",
            thing_type=MODEL_SKY,
            device_name="Sky",
            connected=True,
            speed=5,
            dust_level=1,
            mode=3,  # Turbo mode
            clean_air_val=350,
            prefilter_life_left=90,
            hepa_life_left=95,
            carbon_life_left=80,
            child_lock=False,
            raw_shadow={},
        )
        coordinator.data = {"sky-001": dev_turbo}
        fan = AmwayAtmosphereFan(coordinator, "sky-001")

        assert fan.preset_mode == PRESET_MODE_TURBO
        assert fan.percentage == 100


    def test_sensors(self):
        from unittest.mock import MagicMock
        from custom_components.amway_atmosphere.sensor import (
            AmwayAirQualitySensor,
            AmwayCleanAirSensor,
            AmwayFilterSensor,
            AmwayPM25Sensor,
        )

        coordinator = MagicMock()
        dev = AtmosphereDeviceState(
            thing_id="sky-001",
            thing_type=MODEL_SKY,
            device_name="Sky",
            connected=True,
            speed=2,
            dust_level=4,
            mode=1,
            clean_air_val=420,
            prefilter_life_left=75,
            hepa_life_left=88,
            carbon_life_left=65,
            child_lock=False,
            raw_shadow={},
        )
        coordinator.data = {"sky-001": dev}

        aq_sensor = AmwayAirQualitySensor(coordinator, "sky-001")
        assert aq_sensor.native_value == "inferior"
        assert aq_sensor.extra_state_attributes["dust_level"] == 4

        pm25_sensor = AmwayPM25Sensor(coordinator, "sky-001")
        assert pm25_sensor.native_value == 80.0
        assert pm25_sensor._attr_unique_id == "sky-001_pm25"

        clean_sensor = AmwayCleanAirSensor(coordinator, "sky-001")
        assert clean_sensor.native_value == 420

        pre_sensor = AmwayFilterSensor(
            coordinator, "sky-001", "prefilter", "Pre", "prefilter_life_left", "mdi:filter"
        )
        assert pre_sensor.native_value == 75

        hepa_sensor = AmwayFilterSensor(
            coordinator, "sky-001", "hepa", "HEPA", "hepa_life_left", "mdi:air-filter"
        )
        assert hepa_sensor.native_value == 88

        carbon_sensor = AmwayFilterSensor(
            coordinator, "sky-001", "carbon", "Carbon", "carbon_life_left", "mdi:molecule"
        )
        assert carbon_sensor.native_value == 65


class TestAmwayConfigFlow:
    """Test config flow logic."""

    def test_config_flow_extract_code_variants(self):
        # Full URL format
        url1 = "amwayhealthyhome://loginRedirect?code=98765432-aaaa-bbbb-cccc-dddddddddddd&state=amway_ha"
        assert _extract_code(url1) == "98765432-aaaa-bbbb-cccc-dddddddddddd"

        # URL with trailing query params
        url2 = "https://example.com/redirect?code=12345678-aaaa-bbbb-cccc-dddddddddddd&other=val"
        assert _extract_code(url2) == "12345678-aaaa-bbbb-cccc-dddddddddddd"

        # Plain code with spaces
        code3 = "  12345678-aaaa-bbbb-cccc-dddddddddddd  "
        assert _extract_code(code3) == "12345678-aaaa-bbbb-cccc-dddddddddddd"

    def test_normalize_username(self):
        from custom_components.amway_atmosphere.api import normalize_username

        # Taiwan phone number variations
        assert normalize_username("0912345678", "TW") == "+886912345678"
        assert normalize_username("0912-345-678", "TW") == "+886912345678"
        assert normalize_username("  0912 345 678  ", "TW") == "+886912345678"
        assert normalize_username("912345678", "TW") == "+886912345678"
        assert normalize_username("886912345678", "TW") == "+886912345678"
        assert normalize_username("+886912345678", "TW") == "+886912345678"

        # Other markets or emails unchanged
        assert normalize_username("test@example.com", "TW") == "test@example.com"
        assert normalize_username("0801234567", "JP") == "0801234567"


class TestDirectAuthClient:
    """Test direct login and credential retrieval."""

    def test_direct_login_request_generation(self):
        import asyncio
        from unittest.mock import AsyncMock, MagicMock
        from custom_components.amway_atmosphere.api import AmwayApiClient, generate_pkce

        # 1. Test PKCE generation
        verifier, challenge = generate_pkce()
        assert len(verifier) >= 43
        assert len(challenge) > 20

        async def _run():
            mock_session = MagicMock()

            # Step 1 GET: redirects with jansKey
            mock_resp_step1 = AsyncMock()
            mock_resp_step1.status = 302
            mock_resp_step1.headers = {
                "Location": "https://account2.amwayglobal.com?jansKey=mock-jans-key-999&exp_at=1770000000"
            }

            # Step 2 POST: credentials verification
            mock_resp_step2 = AsyncMock()
            mock_resp_step2.status = 200
            mock_resp_step2.json = AsyncMock(
                return_value={
                    "gluuUser": {"profile": {"partyId": "12345678"}},
                }
            )

            # Step 3 GET: returns auth code redirect
            mock_resp_step3 = AsyncMock()
            mock_resp_step3.status = 302
            mock_resp_step3.headers = {
                "Location": "amwayhealthyhome://loginRedirect?code=mock-code-777&scope=all"
            }

            # Step 4 POST: token exchange
            mock_resp_step4 = AsyncMock()
            mock_resp_step4.status = 200
            mock_resp_step4.json = AsyncMock(
                return_value={
                    "access_token": "mock-conex-token-abc",
                    "refresh_token": "mock-refresh-token-xyz",
                    "expires_in": 3600,
                    "scope": "durables:parties:read",
                }
            )

            # Route get calls
            get_context_1 = AsyncMock()
            get_context_1.__aenter__.return_value = mock_resp_step1
            get_context_3 = AsyncMock()
            get_context_3.__aenter__.return_value = mock_resp_step3
            mock_session.get.side_effect = [get_context_1, get_context_3]

            # Route post calls
            post_context_2 = AsyncMock()
            post_context_2.__aenter__.return_value = mock_resp_step2
            post_context_4 = AsyncMock()
            post_context_4.__aenter__.return_value = mock_resp_step4
            mock_session.post.side_effect = [post_context_2, post_context_4]

            result = await AmwayApiClient.async_login_with_password(
                mock_session, "0912345678", "secret123", country="TW"
            )

            assert result["access_token"] == "mock-conex-token-abc"
            assert result["refresh_token"] == "mock-refresh-token-xyz"
            assert result["expires_in"] == 3600
            assert result["username"] == "+886912345678"
            assert result["party_id"] == "12345678"

            # Verify POST calls
            assert mock_session.post.call_count == 2
            step2_call = mock_session.post.call_args_list[0]
            assert "https://account2.amwayglobal.com/v1/token" in step2_call[0]
            headers = step2_call[1]["headers"]
            assert headers["x-amw-clientapp"] == "healthyhomeTW"
            assert "j" in headers
            body = step2_call[1]["json"]
            assert body["username"] == "+886912345678"
            assert body["jnsKey"] == "mock-jans-key-999"

            step4_call = mock_session.post.call_args_list[1]
            assert "oxauth/restv1/token" in step4_call[0][0]
            assert step4_call[1]["data"]["code"] == "mock-code-777"
            assert "code_verifier" in step4_call[1]["data"]

        asyncio.run(_run())

    def test_get_devices_passes_required_query_params(self):
        import asyncio
        from unittest.mock import AsyncMock, MagicMock
        from custom_components.amway_atmosphere.api import AmwayApiClient

        async def _run():
            mock_session = MagicMock()
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json = AsyncMock(return_value=[])
            mock_session.request.return_value.__aenter__.return_value = mock_resp

            client = AmwayApiClient(mock_session, access_token="test-token")
            devices = await client.async_get_devices()
            assert devices == []

            call_args = mock_session.request.call_args
            assert call_args[1]["params"]["thingType"] == "sky,neptune,sky-mini"
            assert call_args[1]["params"]["info"] == "true"
            assert call_args[1]["params"]["shadow"] == "true"

        asyncio.run(_run())

    def test_send_remote_button_reads_secret_access_key(self):
        import asyncio
        from unittest.mock import AsyncMock, MagicMock
        from custom_components.amway_atmosphere.api import AmwayApiClient

        async def _run():
            mock_session = MagicMock()

            # Mock get_aws_credentials
            cred_resp = AsyncMock()
            cred_resp.status = 200
            cred_resp.json = AsyncMock(
                return_value={
                    "Credentials": {
                        "AccessKeyId": "ASIAKEY123",
                        "SecretAccessKey": "SECRET456",
                        "SessionToken": "TOKEN789",
                        "Expiration": "2026-09-21T00:00:00Z",
                    }
                }
            )

            # Mock shadow update post
            shadow_resp = AsyncMock()
            shadow_resp.status = 200

            async def _mock_request(method, url, **kwargs):
                if "credentials" in url:
                    return cred_resp
                return shadow_resp

            mock_session.request.return_value.__aenter__.side_effect = lambda: cred_resp
            mock_session.post.return_value.__aenter__.return_value = shadow_resp

            client = AmwayApiClient(mock_session, access_token="test-token")
            await client.async_send_remote_button("test-sky-01", "Power")

            mock_session.post.assert_called_once()
            call_args = mock_session.post.call_args
            assert "https://axnk9oqlqxcqh-ats.iot.us-east-1.amazonaws.com/things/test-sky-01/shadow" in call_args[0]
            headers = call_args[1]["headers"]
            assert "AWS4-HMAC-SHA256" in headers["authorization"]

        asyncio.run(_run())

    def test_direct_access_token_config_flow(self):
        """Test config flow when user provides Access Token directly."""
        import asyncio
        from unittest.mock import AsyncMock, MagicMock, patch
        from custom_components.amway_atmosphere.api import AmwayApiClient
        from custom_components.amway_atmosphere.config_flow import AmwayAtmosphereConfigFlow
        from custom_components.amway_atmosphere.const import CONF_ACCESS_TOKEN

        async def _run():
            flow = AmwayAtmosphereConfigFlow()
            flow.hass = MagicMock()

            mock_device = MagicMock()
            mock_device.thing_id = "test-device-id"
            mock_device.device_name = "Living Room Purifier"

            with patch.object(
                AmwayApiClient,
                "async_get_devices",
                new=AsyncMock(return_value=[mock_device]),
            ):
                try:
                    result = await flow.async_step_user(
                        {CONF_ACCESS_TOKEN: "valid-amway-access-token"}
                    )
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                assert result["type"] == "create_entry"
                assert result["title"] == "Amway Atmosphere (test-device-id)"
                assert result["data"][CONF_ACCESS_TOKEN] == "valid-amway-access-token"

        asyncio.run(_run())

    def test_get_token_helpers(self):
        """Test standalone tools/get_token.py helper functions."""
        from tools.get_token import get_local_ip

        ip = get_local_ip()
        assert isinstance(ip, str)
        assert len(ip.split(".")) == 4


class TestAmwayPlatformsAndPruning:
    """Test that switch platform is removed and obsolete switch entities are pruned."""

    def test_platforms_only_contains_fan_and_sensor(self):
        """Verify PLATFORMS only forwards fan and sensor, not switch."""
        from custom_components.amway_atmosphere import PLATFORMS

        assert "fan" in PLATFORMS
        assert "sensor" in PLATFORMS
        assert "switch" not in PLATFORMS

    def test_async_setup_entry_prunes_obsolete_switch_entities(self):
        """Verify async_setup_entry prunes any obsolete switch entities in entity_registry."""
        import asyncio
        from unittest.mock import AsyncMock, MagicMock, patch
        from custom_components.amway_atmosphere import async_setup_entry

        async def _run():
            hass = MagicMock()
            hass.config_entries.async_forward_entry_setups = AsyncMock()
            entry = MagicMock()
            entry.entry_id = "test_entry_123"
            entry.data = {
                "access_token": "test_token",
                "refresh_token": "test_refresh",
            }
            entry.options = {}

            # Mock entity registry with a switch entity and a fan entity
            mock_switch_entity = MagicMock()
            mock_switch_entity.domain = "switch"
            mock_switch_entity.entity_id = "switch.atmosphere_sky_auto_mode"

            mock_fan_entity = MagicMock()
            mock_fan_entity.domain = "fan"
            mock_fan_entity.entity_id = "fan.atmosphere_sky"

            mock_ent_reg = MagicMock()
            with patch(
                "homeassistant.helpers.entity_registry.async_get",
                return_value=mock_ent_reg,
            ), patch(
                "homeassistant.helpers.entity_registry.async_entries_for_config_entry",
                return_value=[mock_switch_entity, mock_fan_entity],
            ), patch(
                "custom_components.amway_atmosphere.coordinator.AmwayAtmosphereCoordinator.async_config_entry_first_refresh",
                new=AsyncMock(),
            ):
                await async_setup_entry(hass, entry)

                # Prune should remove switch entity but NOT fan entity
                mock_ent_reg.async_remove.assert_called_once_with("switch.atmosphere_sky_auto_mode")

        asyncio.run(_run())


class TestAmwayAuthAndTokenLifecycle:
    """TDD tests for OAuth code exchange, token refresh, and login guardrails."""

    def test_phone_password_flow_authenticates_and_stores_refresh_token(self):
        import asyncio
        import time
        from unittest.mock import AsyncMock, MagicMock, patch
        from custom_components.amway_atmosphere.api import AmwayApiClient
        from custom_components.amway_atmosphere.config_flow import AmwayAtmosphereConfigFlow
        from custom_components.amway_atmosphere.const import (
            CONF_ACCESS_TOKEN,
            CONF_COUNTRY,
            CONF_EXPIRES_AT,
            CONF_PASSWORD,
            CONF_REFRESH_TOKEN,
            CONF_USERNAME,
        )

        async def _run():
            flow = AmwayAtmosphereConfigFlow()
            flow.hass = MagicMock()

            mock_login_res = {
                "access_token": "mock-oauth-access-token",
                "refresh_token": "mock-oauth-refresh-token",
                "username": "+886912345678",
                "party_id": "90436550",
                "expires_in": 3600,
            }
            mock_device = AtmosphereDeviceState(
                thing_id="sky-test-01",
                thing_type=MODEL_SKY,
                device_name="Atmosphere Sky™ Air Treatment System",
            )

            with patch.object(
                AmwayApiClient, "async_login_with_password", AsyncMock(return_value=mock_login_res)
            ) as mock_login, patch.object(
                AmwayApiClient, "async_get_devices", AsyncMock(return_value=[mock_device])
            ):
                result = await flow.async_step_user(
                    {
                        CONF_USERNAME: "0912345678",
                        CONF_PASSWORD: "user_secret_password",
                        CONF_COUNTRY: "TW",
                    }
                )

                mock_login.assert_called_once()
                assert result["type"] == "create_entry"
                assert result["title"] == "Amway Atmosphere (sky-test-01)"
                assert result["data"][CONF_ACCESS_TOKEN] == "mock-oauth-access-token"
                assert result["data"][CONF_REFRESH_TOKEN] == "mock-oauth-refresh-token"
                assert result["data"][CONF_USERNAME] == "+886912345678"
                assert result["data"][CONF_EXPIRES_AT] > time.time()

        asyncio.run(_run())

    def test_config_flow_schema_strictly_phone_and_password(self):
        import asyncio
        from unittest.mock import MagicMock
        from custom_components.amway_atmosphere.config_flow import AmwayAtmosphereConfigFlow
        from custom_components.amway_atmosphere.const import (
            CONF_ACCESS_TOKEN,
            CONF_AUTH_CODE,
            CONF_COUNTRY,
            CONF_PASSWORD,
            CONF_USERNAME,
        )

        async def _run():
            flow = AmwayAtmosphereConfigFlow()
            flow.hass = MagicMock()

            result = await flow.async_step_user(None)
            assert result["type"] == "form"
            assert result["step_id"] == "user"

            # Check that schema only presents phone number, password, country
            raw_keys = result["data_schema"].schema.keys()
            schema_keys = [getattr(k, "schema", k) for k in raw_keys]

            assert CONF_USERNAME in schema_keys
            assert CONF_PASSWORD in schema_keys
            assert CONF_COUNTRY in schema_keys
            # auth_code and access_token MUST NOT be present in user schema
            assert CONF_AUTH_CODE not in schema_keys
            assert CONF_ACCESS_TOKEN not in schema_keys

        asyncio.run(_run())

    def test_json_token_payload_with_refresh_token(self):
        import asyncio
        import json
        from unittest.mock import AsyncMock, MagicMock, patch
        from custom_components.amway_atmosphere.api import AmwayApiClient
        from custom_components.amway_atmosphere.config_flow import AmwayAtmosphereConfigFlow
        from custom_components.amway_atmosphere.const import (
            CONF_ACCESS_TOKEN,
            CONF_REFRESH_TOKEN,
        )

        async def _run():
            flow = AmwayAtmosphereConfigFlow()
            flow.hass = MagicMock()

            json_payload = json.dumps({
                "access_token": "json-jwt-access-token",
                "refresh_token": "json-refresh-token-xyz",
                "expires_in": 7200,
            })
            mock_device = AtmosphereDeviceState(
                thing_id="mini-test-01",
                thing_type=MODEL_MINI,
                device_name="Atmosphere Mini™ Air Treatment System",
            )

            with patch.object(
                AmwayApiClient, "async_get_devices", AsyncMock(return_value=[mock_device])
            ):
                result = await flow.async_step_user({CONF_ACCESS_TOKEN: json_payload})

                assert result["type"] == "create_entry"
                assert result["title"] == "Amway Atmosphere (mini-test-01)"
                assert result["data"][CONF_ACCESS_TOKEN] == "json-jwt-access-token"
                assert result["data"][CONF_REFRESH_TOKEN] == "json-refresh-token-xyz"

        asyncio.run(_run())

    def test_username_password_no_devices_found_blocks_entry_creation(self):
        import asyncio
        from unittest.mock import AsyncMock, MagicMock, patch
        from custom_components.amway_atmosphere.api import AmwayApiClient
        from custom_components.amway_atmosphere.config_flow import AmwayAtmosphereConfigFlow
        from custom_components.amway_atmosphere.const import (
            CONF_PASSWORD,
            CONF_USERNAME,
        )

        async def _run():
            flow = AmwayAtmosphereConfigFlow()
            flow.hass = MagicMock()

            mock_login_res = {
                "access_token": "web-session-token-without-durables",
                "username": "+886912345678",
                "party_id": "90436550",
            }

            with patch.object(
                AmwayApiClient, "async_login_with_password", AsyncMock(return_value=mock_login_res)
            ), patch.object(
                AmwayApiClient, "async_get_devices", AsyncMock(return_value=[])
            ):
                # When user enters username and password, but Conex API returns 0 devices
                result = await flow.async_step_user({
                    CONF_USERNAME: "0912345678",
                    CONF_PASSWORD: "user_secret_password",
                })

                # Must NOT create entry; must show form with no_devices_found error
                assert result["type"] == "form"
                assert result["errors"]["base"] == "no_devices_found"

        asyncio.run(_run())

    def test_token_refresh_lifecycle_and_callback(self):
        import asyncio
        from unittest.mock import AsyncMock, MagicMock, patch
        from custom_components.amway_atmosphere.api import AmwayApiClient

        async def _run():
            session = MagicMock()
            mock_callback = AsyncMock()

            client = AmwayApiClient(
                session=session,
                access_token="initial-access-token",
                refresh_token="valid-refresh-token",
                on_token_refreshed=mock_callback,
            )

            new_tokens = {
                "access_token": "newly-refreshed-access-token",
                "refresh_token": "renewed-refresh-token",
                "expires_in": 3600,
            }

            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json = AsyncMock(return_value=new_tokens)
            mock_resp.raise_for_status = MagicMock()

            # Mock context manager for session.post
            session.post.return_value.__aenter__.return_value = mock_resp

            tokens = await client.async_refresh_token()
            assert client.access_token == "newly-refreshed-access-token"
            assert client.refresh_token == "renewed-refresh-token"
            mock_callback.assert_called_once_with(new_tokens)

        asyncio.run(_run())

    def test_tools_get_token_print_banner_and_payload(self):
        import json
        from tools.get_token import print_banner

        # Test dictionary payload with refresh_token
        dict_payload = {
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
        }
        # Verify it executes cleanly without exceptions
        print_banner(dict_payload)

        # Test single string token
        print_banner("plain-string-token")

    def test_device_info_name_strictly_uses_thing_id(self):
        """Verify that HA device name uses thing_id strictly for Fan and Sensor."""
        from unittest.mock import MagicMock
        from custom_components.amway_atmosphere.api import AtmosphereDeviceState, MODEL_SKY
        from custom_components.amway_atmosphere.fan import AmwayAtmosphereFan
        from custom_components.amway_atmosphere.sensor import AmwayAirQualitySensor

        coordinator = MagicMock()
        dev = AtmosphereDeviceState(
            thing_id="MOCK_SKY_SERIAL_12345",
            thing_type=MODEL_SKY,
            device_name="Atmosphere Sky™ Air Treatment System",
            sw_version="1.8.5266",
            hw_version="sky3613B",
        )
        coordinator.data = {"MOCK_SKY_SERIAL_12345": dev}

        fan = AmwayAtmosphereFan(coordinator, "MOCK_SKY_SERIAL_12345")
        sensor = AmwayAirQualitySensor(coordinator, "MOCK_SKY_SERIAL_12345")

        assert fan.device_info["name"] == "MOCK_SKY_SERIAL_12345"
        assert sensor.device_info["name"] == "MOCK_SKY_SERIAL_12345"
        assert fan.device_info["serial_number"] == "MOCK_SKY_SERIAL_12345"
        assert sensor.device_info["serial_number"] == "MOCK_SKY_SERIAL_12345"
        assert fan.device_info["sw_version"] == "1.8.5266"
        assert sensor.device_info["sw_version"] == "1.8.5266"
        assert fan.device_info["hw_version"] == "sky3613B"
        assert sensor.device_info["hw_version"] == "sky3613B"

        # Check extra state attributes
        assert fan.extra_state_attributes["serial_number"] == "MOCK_SKY_SERIAL_12345"
        assert fan.extra_state_attributes["serial"] == "MOCK_SKY_SERIAL_12345"
        assert sensor.extra_state_attributes["serial_number"] == "MOCK_SKY_SERIAL_12345"
        assert sensor.extra_state_attributes["serial"] == "MOCK_SKY_SERIAL_12345"

    def test_api_client_extracts_firmware_and_hardware_versions(self):
        """Verify async_get_devices extracts sw_version and hw_version."""
        import asyncio
        from unittest.mock import AsyncMock, MagicMock
        from custom_components.amway_atmosphere.api import AmwayApiClient

        async def _test():
            mock_session = MagicMock()
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json = AsyncMock(return_value=[
                {
                    "thingId": "MOCK_SKY_SERIAL_12345",
                    "thingType": "sky",
                    "shadow": {
                        "payload": json.dumps({
                            "state": {
                                "reported": {
                                    "system": {
                                        "connected": True,
                                        "appFirmwareVersion": "1.8.5266",
                                    },
                                    "display": {"speed": 1, "dust": 1},
                                }
                            }
                        })
                    },
                    "thing": {
                        "attributes": {
                            "hardware_version": "sky3613B",
                            "version_current": "1.8.6086",
                        }
                    }
                }
            ])
            mock_session.request.return_value.__aenter__.return_value = mock_resp

            client = AmwayApiClient(session=mock_session, access_token="token")
            devices = await client.async_get_devices()
            assert len(devices) == 1
            dev = devices[0]
            assert dev.thing_id == "MOCK_SKY_SERIAL_12345"
            assert dev.sw_version == "1.8.5266"
            assert dev.hw_version == "sky3613B"

        asyncio.run(_test())

    def test_homekit_serial_number_patch(self):
        """Test _patch_homekit_serial_number correctly configures HomeKit AccessoryInformation SerialNumber."""
        import sys
        from unittest.mock import MagicMock
        from custom_components.amway_atmosphere import _patch_homekit_serial_number

        # Create a mock homeassistant.components.homekit.accessories module
        mock_hk_acc = MagicMock()
        class MockHomeAccessory:
            def __init__(self, hass, driver, name, entity_id, aid, config, *args, **kwargs):
                self.entity_id = entity_id
                self.aid = aid
                self.serv_info = MagicMock()

            def get_service(self, name):
                if name == "AccessoryInformation":
                    return self.serv_info
                return None

        mock_hk_acc.HomeAccessory = MockHomeAccessory

        # Register into sys.modules
        fake_module_name = "homeassistant.components.homekit.accessories"
        orig_mod = sys.modules.get(fake_module_name)
        sys.modules[fake_module_name] = mock_hk_acc

        try:
            mock_hass = MagicMock()
            mock_state = MagicMock()
            mock_state.attributes = {"serial_number": "MOCK_SKY_SERIAL_12345"}
            mock_hass.states.get.return_value = mock_state
            mock_hass.config_entries.async_entries.return_value = []

            _patch_homekit_serial_number(mock_hass)

            # 1. Fallback via entity state attributes
            acc1 = mock_hk_acc.HomeAccessory(
                mock_hass, MagicMock(), "Amway Sky", "fan.mock_sky_serial_12345", 1, {}
            )
            acc1.serv_info.configure_char.assert_called_with(
                "SerialNumber", value="MOCK_SKY_SERIAL_12345"
            )

            # 2. Lookup via HA device registry
            import homeassistant.helpers.device_registry as dr
            import homeassistant.helpers.entity_registry as er

            mock_ent_entry = MagicMock()
            mock_ent_entry.device_id = "mock_dev_id"
            mock_dev_entry = MagicMock()
            mock_dev_entry.serial_number = "MOCK_SKY_SERIAL_12345"

            er.async_get.return_value.async_get.return_value = mock_ent_entry
            dr.async_get.return_value.async_get.return_value = mock_dev_entry

            acc2 = mock_hk_acc.HomeAccessory(
                mock_hass, MagicMock(), "Amway Sky", "fan.mock_sky_serial_12345", 2, {}
            )
            acc2.serv_info.configure_char.assert_called_with(
                "SerialNumber", value="MOCK_SKY_SERIAL_12345"
            )
        finally:
            if orig_mod is not None:
                sys.modules[fake_module_name] = orig_mod
            else:
                sys.modules.pop(fake_module_name, None)




