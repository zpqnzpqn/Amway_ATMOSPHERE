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

An official-grade Home Assistant custom integration for **Amway Atmosphere Sky** and **Amway Atmosphere Mini** air treatment systems. Built on reverse-engineered protocols of the official *Amway Healthy Home* platform, featuring native **Apple HomeKit Air Purifier & Air Quality** bridging.

---

> 💡 **First-time setup?** Check out the step-by-step 👉 [**Quick Setup & Token Guide**](docs/setup-guide.md)

## ✨ Features

- **🌀 Comprehensive Purifier & Fan Control (`fan`)**:
  - **Atmosphere Sky**: 5 discrete fan speed steps (20%, 40%, 60%, 80%, 100%).
  - **Atmosphere Mini**: 3 discrete fan speed steps (33%, 67%, 100%).
  - **Preset Modes**: `Auto`, `Night`, `Turbo` (Sky only).
  - **Power Control**: Responsive power toggle and real-time status reflection.
- **🍃 Apple HomeKit 5-Tier Air Quality Sensor (`sensor`)**:
  - Seamless 1-to-1 mapping to Apple HomeKit's native `AirQuality` characteristic:
    - `1`: Excellent
    - `2`: Good
    - `3`: Fair
    - `4`: Inferior
    - `5`: Poor
  - Numeric **Clean Air Value** sensor (`cleanAirVal`).
- **🛡️ Multi-Stage Filter Lifecycle Tracking (`sensor`)**:
  - Pre-filter Life (`0–100%`)
  - HEPA Filter Life (`0–100%`)
  - Carbon Odor Filter Life (`0–100%`, Sky only)
- **🗂️ Apple Home "Show as Separate Tiles" Support**:
  - Splits the unified appliance into discrete **Purifier** and **Air Quality** cards in the Apple Home app.
  - Exposes clean, independent entities in Home Assistant for flexible dashboard composition.

---

## 📱 Apple Home (iOS / macOS) Separate Tiles Setup Guide

When synced to Apple Home via Home Assistant's **HomeKit Bridge**, the purifier and its air quality sensor may initially appear combined under a single accessory tile. You can easily separate them into individual cards:

1. Open the **Home** app on iPhone, iPad, or Mac.
2. Long-press or click the **Atmosphere Air Purifier** accessory.
3. Tap the **Settings (gear icon)** in the bottom right corner.
4. Select **"Show as Separate Tiles"**.
5. Done! Apple Home will split the device into two dedicated cards:
   - **Tile 1**: Air Purifier power toggle, percentage fan speed slider, and Auto / Night / Turbo preset selector.
   - **Tile 2**: Indoor Air Quality rating (Excellent / Good / Fair / Inferior / Poor) and gauge.
   You can move or pin each card to different rooms and favorites.

> 🍏 **Advanced HomeKit Guide & Sensor Mapping**: For the 5-sensor HomeKit compatibility evaluation table, sample YAML configs, and multi-filter lowest-life binding, see 👉 [**Apple HomeKit Setup Guide**](docs/setup-guide.md#-apple-homekit-完美設定教學-type-air_purifier)

---

## 📦 Installation

### Method 1: Via HACS Custom Repository (Recommended)

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

1. Download the latest release from the [Releases](https://github.com/zpqnzpqn/Amway_ATMOSPHERE/releases) page.
2. Copy the `custom_components/amway_atmosphere` directory into your Home Assistant's `config/custom_components/` directory:
   ```text
   config/custom_components/amway_atmosphere/
   ```
3. **Restart Home Assistant**.

---

## ⚙️ Configuration (Config Flow)

1. In Home Assistant, go to **Settings** $\rightarrow$ **Devices & Services** $\rightarrow$ **Add Integration**.
2. Search for and select **Amway Atmosphere**.
3. Choose your preferred connection method:

### Method A: Direct Access Token (Recommended)
Because official mobile apps utilize AppAuth PKCE, the most stable and password-safe method is using an Access Token:
1. Run the standalone helper tool on your computer:
   ```bash
   python3 tools/get_token.py --proxy
   ```
2. Follow the on-screen instructions:
   - Connect your smartphone to the same Wi-Fi and set the HTTP proxy to your computer's IP.
   - Open the **Amway Healthy Home** app and log in or toggle device power.
   - The tool will automatically capture and display your token, then shut down cleanly.
3. Paste the captured **Access Token** into Home Assistant setup wizard and click **Submit**.

### Method B: Phone Number & Password
Enter your registered phone number (e.g., `09xxxxxxxx` or `+8869xxxxxxxx`) and password to connect directly.

### Method C: Browser Manual Code
Use `python3 tools/get_token.py --manual` to authenticate via your web browser and exchange authorization codes.

4. Once configured, all Atmosphere Sky and Atmosphere Mini purifiers linked to your Amway account will be discovered automatically!

---

## 📊 Dashboard Cards Examples (Lovelace)

### 1. Purifier Tile Card
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

### 2. Air Quality Gauge Card
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

### 3. Filter Lifespan Tracking Card
```yaml
type: entities
title: Filter Consumables Life
entities:
  - entity: sensor.atmosphere_sky_prefilter_life
    name: Pre-Filter Life
  - entity: sensor.atmosphere_sky_hepa_life
    name: HEPA Filter Life
  - entity: sensor.atmosphere_sky_carbon_life
    name: Carbon Odor Filter Life
```

---

## 🛠️ Architecture & Technical Details

- **IoT Class**: `cloud_polling` (Periodically updates device shadow state every 30 seconds).
- **Fast Control Dispatch**: Remote button commands (`RemoteButton`: Power, Fan speeds, Auto, Night, Turbo) are dispatched directly to AWS IoT Device Shadow using AWS Signature Version 4 (SigV4) authentication. An immediate coordinator refresh is scheduled within 1 second to ensure instant feedback.
- **Authentication**: Gluu OAuth2 IDP (`oxauth/restv1`) with automatic background access token renewal via refresh tokens.
- **Regions & Compatibility**: Compatible with the global Amway Healthy Home cloud infrastructure (verified with Taiwan region accounts).

---

## ⚠️ Disclaimer

This project is an independent, community-driven open-source integration and is neither affiliated with nor endorsed by Amway Corp. All product names, trademarks, and registered trademarks are property of their respective owners.
