# Specification: Amway Atmosphere Home Assistant Integration

## 1. Overview
The `amway_atmosphere` integration connects Amway Atmosphere Sky and Atmosphere Mini air purifiers to Home Assistant (HACS) and bridges them seamlessly into Apple HomeKit with full support for:
- Air Purifier controls (On/Off, Speed steps, Auto/Night/Turbo presets)
- Indoor Air Quality telemetry (`dust` level 1–5 & `cleanAirVal`)
- Multi-stage filter lifecycle tracking (Pre-filter, HEPA filter, Carbon filter)
- Discrete tiles/multi-card support in Apple Home and Home Assistant Lovelace.

---

## 2. User Stories

### US-01: Air Purifier Control in Apple Home & Home Assistant
- **As a** Home Assistant / Apple Home user,
- **I want to** turn on/off the Atmosphere purifier and adjust fan speeds,
- **So that** I can control room air flow via HomeKit sliders or automated scenes.
- **Acceptance Criteria**:
  - Sky: 5 fan speed steps mapped to 20%, 40%, 60%, 80%, 100%.
  - Mini: 3 fan speed steps mapped to 33%, 67%, 100%.
  - Supports `preset_mode` for `Auto`, `Night`, and `Turbo` (Sky only).
  - Correctly reflects offline state if device is disconnected.

### US-02: Air Quality Sensor Monitoring
- **As a** user concerned with indoor air quality,
- **I want to** view real-time particulate and dust readings,
- **So that** I can trigger notifications or air purification routines.
- **Acceptance Criteria**:
  - Exposes an `Air Quality` sensor reporting levels 1 to 5, mapped directly to Apple HomeKit's native 5-level standard:
    - 1: Excellent (優良)
    - 2: Good (良好)
    - 3: Fair (普通)
    - 4: Inferior (不良)
    - 5: Poor (極差)
  - Exposes `cleanAirVal` as a numeric sensor.

### US-03: Filter Lifecycle Tracking
- **As a** user maintaining the appliance,
- **I want to** monitor remaining filter life for each stage,
- **So that** I know when cleaning or replacement is needed.
- **Acceptance Criteria**:
  - Pre-filter: `0–100%`
  - HEPA filter: `0–100%`
  - Carbon filter: `0–100%` (Atmosphere Sky)
  - Alerts when filter life falls below critical threshold.

### US-04: Multi-Card & Separate Tiles Display
- **As a** user designing my home dashboard,
- **I want to** display the purifier controls, air quality index, and filter status on separate cards/tiles,
- **So that** my dashboard is clean and informative.
- **Acceptance Criteria**:
  - In Apple Home: Supports toggling "Show as Separate Tiles (顯示為個別標籤頁)".
  - In Home Assistant: Purifier, AQI, and Filters are separate entities that can be placed on distinct cards (Tile Card, Gauge Card, Bar Card).

---

## 3. Architecture & Cloud Seams

### Seams
1. **OAuth2 Gateway (`Gluu`)**:
   - Authorize: `https://gluu-prod01-prod.amstack-amwayidv2-prod.amwayglobal.com/oxauth/restv1/authorize`
   - Token: `https://gluu-prod01-prod.amstack-amwayidv2-prod.amwayglobal.com/oxauth/restv1/token`
2. **REST Inventory & Telemetry Gateway (`Conex API`)**:
   - Base URL: `https://conex-api.amwayglobal.com/rest/`
   - Devices Endpoint: `GET /rest/v1/things`
3. **Device Shadow Control (`AWS IoT`)**:
   - Desired Payload: `{"state": {"desired": {"RemoteButton": "<ButtonName>"}}}`
   - Endpoints via STS credentials or REST command proxy.
