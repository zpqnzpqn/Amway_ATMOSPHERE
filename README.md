# Amway Atmosphere for Home Assistant & Apple HomeKit

<p align="center">
  <a href="README.md"><b>English</b></a> |
  <a href="README_zh-Hant.md"><b>繁體中文</b></a> |
  <a href="README_ja.md"><b>日本語</b></a>
</p>

---

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://www.home-assistant.io)
[![Apple HomeKit](https://img.shields.io/badge/Apple%20HomeKit-Compatible-black.svg)](https://www.apple.com/home-app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://github.com/zpqnzpqn/Amway_ATMOSPHERE/actions/workflows/test.yml/badge.svg)](https://github.com/zpqnzpqn/Amway_ATMOSPHERE/actions)
[![Validate](https://github.com/zpqnzpqn/Amway_ATMOSPHERE/actions/workflows/validate.yml/badge.svg)](https://github.com/zpqnzpqn/Amway_ATMOSPHERE/actions)

An official-grade Home Assistant custom integration for **Amway Atmosphere Sky** and **Amway Atmosphere Mini** air treatment systems. Built on reverse-engineered protocols of the official *Amway Healthy Home* platform, featuring responsive **AWS IoT Device Shadow bi-directional control** and native **Apple HomeKit Air Purifier & Air Quality** bridging.

---

> 🚀 **Release Notes (Release v1.0.0 - General Availability)**  
> This marks the first official production release (v1.0.0), rigorously verified across physical hardware and 38 automated unit tests:
> - **Direct Login**: Connect seamlessly using your registered Phone Number and Password with automatic Gluu AppAuth PKCE token exchange and background token refresh.
> - **Full Model Support**: Supports Atmosphere Sky (5 discrete speed steps, 3 filter stages, Turbo mode) and Atmosphere Mini (3 speed steps, 2-in-1 filter).
> - **Unified Fan Entity**: Preset modes (`Auto`, `Night`, `Turbo`) are built directly into the purifier entity, with automatic pruning of legacy redundant switches.
> - **HomeKit Serial Number Sync**: Automatically maps physical device serial number and firmware/hardware revisions to Apple HomeKit `AccessoryInformation`.
> - For detailed setup and HomeKit bridging, see the 👉 [**Setup & HomeKit Guide**](docs/setup-guide_en.md).

---

## ✨ Key Features

- **🌀 Native Purifier & Fan Control (`fan`)**:
  - **Atmosphere Sky**: 5 discrete fan speed steps (20%, 40%, 60%, 80%, 100%).
  - **Atmosphere Mini**: 3 discrete fan speed steps (33%, 67%, 100%).
  - **Preset Modes**: `Auto`, `Night`, `Turbo` (Sky only).
  - **Instant Cloud Dispatch**: Sends `RemoteButton` commands directly to AWS IoT Device Shadow using SigV4 signed REST requests with sub-second state reflection.
- **🍃 Apple HomeKit 5-Tier Air Quality Sensor (`sensor`)**:
  - Direct 1-to-1 mapping to Apple HomeKit's native `AirQuality` characteristic:
    - `1`: Excellent
    - `2`: Good
    - `3`: Fair
    - `4`: Inferior
    - `5`: Poor
  - Numeric **Clean Air Delivery Value** sensor (`cleanAirVal`).
- **🛡️ Multi-Stage Filter Lifecycle Tracking (`sensor`)**:
  - Pre-filter Life (`0–100%`)
  - HEPA Filter Life (`0–100%`)
  - Carbon Odor Filter Life (`0–100%`, Sky only)
- **📱 Apple Home Hardware Serial Number Synchronization**:
  - Dynamic bridge hook ensures the device's real hardware serial number and firmware version appear accurately under Apple Home Accessory Details.
- **🗂️ Apple Home "Show as Separate Tiles" Support**:
  - Seamlessly splits the unified appliance into dedicated **Purifier** and **Air Quality** tiles in Apple Home.

---

## 📦 Installation

### Method 1: Via HACS Custom Repository (Recommended)

> 💡 **Don't have HACS installed yet?** Refer to the 👉 [**HACS Official Documentation**](https://www.hacs.xyz/docs/use) to install and configure HACS first, or use **Method 2** below to install manually without HACS.

1. Open **HACS** in your Home Assistant sidebar.
2. Click the three dots menu icon in the top right corner $\rightarrow$ **Custom repositories**.
3. In the repository URL field, enter:
   ```text
   https://github.com/zpqnzpqn/Amway_ATMOSPHERE
   ```
4. Select **Integration** as the Category, then click **Add**.
5. Search for **Amway Atmosphere** and click **Download**.
6. **Restart Home Assistant**.

### Method 2: Manual Installation

1. Download the latest release source from the [Releases](https://github.com/zpqnzpqn/Amway_ATMOSPHERE/releases) page.
2. Copy the `custom_components/amway_atmosphere` directory into your Home Assistant directory:
   ```text
   config/custom_components/amway_atmosphere/
   ```
3. **Restart Home Assistant**.

---

## ⚙️ Configuration (Config Flow)

1. In Home Assistant, navigate to **Settings** $\rightarrow$ **Devices & Services** $\rightarrow$ **Add Integration**.
2. Search for and select **Amway Atmosphere**.
3. Choose your preferred authentication method:
   - **Method A: Direct Phone Number & Password (Recommended)**:
     Enter your registered mobile phone number (e.g. `0912345678` or `+886912345678`) and password. The integration completes OAuth2 authentication and automatically handles background token refreshes.
   - **Method B: Direct Access Token**:
     If you prefer zero password storage, execute `python3 tools/get_token.py --proxy` to capture an Access Token and paste it directly.
4. Once completed, your Atmosphere purifiers and sensors will automatically appear in Home Assistant!

---

## 🍏 Apple HomeKit Recommended Configuration

To expose your purifier as a native Apple HomeKit Air Purifier with filter life warnings, add the following to your `configuration.yaml`:

```yaml
homekit:
  - name: "Amway HomeKit Bridge"
    port: 21064
    mode: bridge
    filter:
      include_entities:
        - fan.atmosphere_sky_air_treatment_system # or your fan.<device_name>
        - sensor.atmosphere_sky_air_treatment_system_air_quality
    entity_config:
      fan.atmosphere_sky_air_treatment_system:
        type: air_purifier
        # Link native filter life percentage to your lowest filter life sensor
        linked_filter_life_level_sensor: sensor.atmosphere_sky_lowest_filter_life
```

> 💡 For the complete **5-Sensor HomeKit Compatibility Evaluation Table** and multi-stage lowest filter life template sensor, see 👉 [**Setup & HomeKit Guide**](docs/setup-guide_en.md#-apple-homekit-setup-guide-type-air_purifier).

---

## 📊 Dashboard Cards (Lovelace)

### 1. Air Purifier Control (Tile Card)
```yaml
type: tile
entity: fan.atmosphere_sky
name: Living Room Purifier
features:
  - type: fan-speed
  - type: fan-preset-modes
    style: dropdown
    preset_modes:
      - auto
      - night
      - turbo
```

### 2. Indoor Air Quality (Gauge Card)
```yaml
type: gauge
entity: sensor.atmosphere_sky_air_quality
name: Indoor Air Quality
needle: true
segments:
  - from: 1
    color: "#4caf50"
    label: Excellent
  - from: 2
    color: "#8bc34a"
    label: Good
  - from: 3
    color: "#ffc107"
    label: Fair
  - from: 4
    color: "#ff9800"
    label: Inferior
  - from: 5
    color: "#f44336"
    label: Poor
```

---

## 🛠️ Architecture & Technical Specifications

- **IoT Class**: `cloud_polling` (Polls Conex API for Device Shadow updates every 30 seconds by default).
- **Fast Remote Dispatch**: Sends `RemoteButton` commands directly to AWS IoT Device Shadow using SigV4 signed REST requests, triggering immediate coordinator refresh within 1 second.
- **Robust Auth**: Employs standard Gluu OAuth2 IDP (`oxauth/restv1`) with transparent background token refreshes using refresh tokens.
- **Regional Support**: Built on the Amway Global Healthy Home cloud platform, thoroughly tested in the Taiwan market.

---

## ⚠️ Disclaimer

This project is an independent community open-source project and is not affiliated with, endorsed by, or sponsored by Amway Corp. All trademarks and registered trademarks are the property of their respective owners.
