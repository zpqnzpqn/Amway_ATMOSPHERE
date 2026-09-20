# Amway Atmosphere Integration

Integration context for connecting Amway Atmosphere Sky and Atmosphere Mini air treatment systems to Home Assistant via HACS and bridging to Apple HomeKit.

## Language

### Systems & Devices

**Amway Atmosphere**:
The unified Home Assistant integration domain (`amway_atmosphere`) supporting the Atmosphere series air treatment systems.
_Avoid_: Amway Sky integration, Atmosphere plugin

**Atmosphere Sky**:
The flagship large-room air treatment system manufactured by Amway, featuring 3-stage filtration, 5 fan speeds, Turbo mode, Wi-Fi, and BLE.
_Avoid_: Sky unit, Amway air purifier

**Atmosphere Mini**:
The compact-room air treatment system manufactured by Amway, featuring a 3-in-1 filtration cartridge, 3 fan speeds, Wi-Fi, and BLE.
_Avoid_: Mini unit, Sky Mini

### Software & Cloud Infrastructure

**Amway Healthy Home**:
The current official mobile application (package `com.amwayglobal.healthyhome`) used for cloud connectivity, device control, and telemetry.
_Avoid_: Atmosphere Connect (deprecated legacy app discontinued in April 2024)

**Conex API**:
The centralized Amway cloud REST gateway (`conex-api.amwayglobal.com/rest/`) providing device inventories, telemetry queries, and STS credential generation.
_Avoid_: Amway backend, healthy home server

**Device Shadow**:
The AWS IoT state document reflecting reported telemetry (`display`, `custom`, `carbon`, `hepa`, `prefilter`) and receiving desired button commands.
_Avoid_: Device state JSON, MQTT payload

**RemoteButton**:
The canonical command enumeration (`Power`, `Auto`, `Night`, `Turbo`, `Speed1`–`Speed5`, `ChildLock`) dispatched to trigger device state transitions.
_Avoid_: Command code, action trigger

**HACS Integration**:
The Home Assistant Community Store custom component adhering to official HACS repository standards and directory conventions.
_Avoid_: HA plugin, HA addon

**HomeKit Bridge**:
The Home Assistant integration exposing local entities to the Apple Home ecosystem as native HomeKit accessories.
_Avoid_: Homebridge, Apple Home plugin

**Supported Regions**:
The integration connects to Amway Healthy Home cloud infrastructure, supporting Taiwan and Japan region accounts with primary verified testing on Taiwan accounts.
_Avoid_: US legacy region, Atmosphere Connect region

### Entities & HomeKit Mapping

**Purifier Entity**:
The Home Assistant `fan` platform representation mapped to HomeKit's `AirPurifier` service with percentage speeds and preset modes.
_Avoid_: Switch entity, climate entity

**Air Quality Sensor**:
The Home Assistant `sensor` entity reporting particulate levels or indoor air quality index (`dust` level 1–5, `cleanAirVal`) bridging to HomeKit's `AirQualitySensor`.
_Avoid_: Pollution meter

**Filter Sensor**:
The Home Assistant `sensor` entity tracking remaining lifespan percentage (`lifeLeft`) for Pre-filter, HEPA filter, and Carbon filter.
_Avoid_: Consumables tracker

**Polling Coordinator**:
The Home Assistant `DataUpdateCoordinator` managing scheduled polling intervals and cached device state updates.
_Avoid_: MQTT listener, webhook handler

**Separate Tiles**:
The Apple Home configuration mode that decomposes grouped appliance accessories into discrete interactive dashboard cards.
_Avoid_: Split accessories, unlinked accessories
