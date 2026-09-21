# Amway Atmosphere Air Treatment System Home Assistant & Apple HomeKit Setup Guide

<p align="center">
  <a href="setup-guide_en.md"><b>English</b></a> |
  <a href="setup-guide.md"><b>繁體中文</b></a> |
  <a href="setup-guide_ja.md"><b>日本語</b></a>
</p>

> 🚀 **v1.0.0 General Availability (GA) Release Notes**  
> This guide is designed for all Home Assistant and Apple HomeKit users to help you quickly connect, configure, and automate Amway Atmosphere Sky and Atmosphere Mini air treatment systems.  
> This release includes direct phone number & password authentication, AWS IoT Shadow cloud bi-directional real-time control, native Apple HomeKit Air Purifier & 5-tier Air Quality bridging, and physical hardware serial number synchronization.

---

> 💡 **Prerequisites (Install the Integration)**:  
> The integration must first be installed into your Home Assistant instance. You can install it via the HACS Custom Repository and restart HA (if you don't have HACS installed yet, refer to the 👉 [**HACS Official Documentation**](https://www.hacs.xyz/docs/use) to set it up); or manually download the source code into `config/custom_components/amway_atmosphere/`.

## 🚀 Connection & Authentication Methods

### Method 1: Direct Phone Number & Password Login (Recommended, Browser-Free)

This integration implements the native OAuth2 + PKCE authentication flow used by the official Amway Healthy Home app. **No redirect URLs, no browser jumping, and no packet-capture tools are needed**. Complete your setup directly within the Home Assistant user interface:

1. In Home Assistant, navigate to **Settings $\rightarrow$ Devices & Services $\rightarrow$ Add Integration** $\rightarrow$ search for **Amway Atmosphere**.
2. Enter your registered **Phone Number** (e.g., `0912345678` or `+886912345678`) and **Password**.
3. Default country code is `TW` (Taiwan, or your registered region).
4. Click **Submit**. The integration automatically exchanges credentials for tokens and configures background auto-refresh!
5. Your Atmosphere air purifier and associated sensors will appear immediately in Home Assistant!

---

### Method 2: Access Token Direct Login (Zero Password Storage Risk)

If you prefer not to store your Amway account password in Home Assistant, you can use the companion helper tool to obtain a token directly:

```bash
python3 tools/get_token.py --proxy
```
Follow the terminal instructions and trigger requests in your mobile app. Once captured, the tool prints and copies the token so you can paste it directly into the setup dialog.

---

## 🍏 Apple HomeKit Setup Guide (type: air_purifier)

This integration is fully compatible with Apple HomeKit specifications, bridging your Amway air purifier as a **native Air Purifier** accessory to the Apple Home app, along with dedicated sensors:

### 1. 5-Sensor HomeKit Compatibility Evaluation Table

| Sensor Name | Sample Value | Native HomeKit Support | HomeKit Type / Characteristic | Presentation & Notes |
| :--- | :--- | :--- | :--- | :--- |
| **HEPA Filter Life** | 40% | ✅ Native Support | Subordinate to `air_purifier` via `FilterLifeLevel` characteristic | When linked to the purifier accessory, tapping the purifier tile in Apple Home directly displays "Filter Life: 40%". When life drops below the threshold, Apple Home automatically pushes a "Filter Replacement Needed" system alert. |
| **Carbon Filter Life** | 13% | ⚠️ Choose One or Use Lowest Minimum | Same as above (HomeKit allows only one Filter reading per purifier) | HomeKit specification dictates that an Air Purifier accessory can only have one `FilterLifeLevel`. It is recommended to bind the filter that depletes fastest (e.g. Carbon 13%), or use a Home Assistant template sensor taking the minimum of all three filters. |
| **Pre-Filter Life** | 58% | ⚠️ Choose One or Use Lowest Minimum | Same as above | Same as above. |
| **Air Quality** | good | ✅ Native Support | `AirQualitySensor` (Air Quality Sensor) | HomeKit natively supports 5-level rating (Excellent / Good / Fair / Inferior / Poor). Displays as a dedicated icon at the top of the room in Apple Home, showing "Good". |
| **Clean Air Value** | 795 | ❌ No Native Type | None (Apple HomeKit has no generic numeric/CADR accessory type) | Apple HomeKit does not allow arbitrary untyped numbers. Forcing it as Temperature/Humidity/PM2.5 distorts units and analysis (e.g. displaying 795°C or 795%). **Keep this sensor on your Home Assistant dashboard; do not bridge it to HomeKit.** |

---

### 2. 🛠️ Recommended HomeKit Bridge Configuration (configuration.yaml)

To achieve the best presentation in the Apple Home app, configure the HomeKit bridge in Home Assistant's `configuration.yaml` as follows (excluding incompatible numeric sensors and bridging only the purifier and air quality rating):

```yaml
homekit:
  - name: "Amway HomeKit Bridge"
    port: 21064
    mode: bridge
    filter:
      include_entities:
        - fan.atmosphere_sky_air_treatment_system # or your fan.<thing_id>
        - sensor.atmosphere_sky_air_treatment_system_air_quality
    entity_config:
      fan.atmosphere_sky_air_treatment_system:
        type: air_purifier
        # Link native purifier filter life percentage and depletion alarm to lowest filter life sensor
        linked_filter_life_level_sensor: sensor.atmosphere_sky_lowest_filter_life
```

> 💡 **Entity ID Note**: If your entity was generated using your device serial number (e.g. `fan.23342a03013613bab`), substitute it with your actual `entity_id`.

---

### 3. 💡 Advanced Tip: Multi-Stage Filter "Automatic Lowest Life" Sensor

Because the Atmosphere Sky includes Pre-filter, HEPA, and Carbon filters, you can use a Home Assistant Template Sensor to track the lowest remaining life:

#### Option A: Add to `configuration.yaml`
```yaml
template:
  - sensor:
      - name: "Atmosphere Sky Lowest Filter Life"
        unique_id: atmosphere_sky_lowest_filter_life
        unit_of_measurement: "%"
        state: >
          {{ [
            states('sensor.atmosphere_sky_air_treatment_system_hepa_filter_life') | int(100),
            states('sensor.atmosphere_sky_air_treatment_system_carbon_filter_life') | int(100),
            states('sensor.atmosphere_sky_air_treatment_system_pre_filter_life') | int(100)
          ] | min }}
```

#### Option B: Create via Home Assistant Web UI (No YAML Editing)
1. Go to **Settings $\rightarrow$ Devices & Services $\rightarrow$ Helpers**.
2. Click **+ Create Helper $\rightarrow$ Template $\rightarrow$ Template a sensor**.
3. Enter Name: `Atmosphere Sky Lowest Filter Life`, paste the Jinja expression into State Template, and set Unit of measurement to `%`.

Then set `linked_filter_life_level_sensor` to `sensor.atmosphere_sky_lowest_filter_life`. Whichever filter depletes first (e.g. Carbon at 13%), Apple Home will immediately reflect the value and notify you when replacement is required!

---

### 4. Apple Home Highlights & User Experience

* **Native Air Purifier Accessory**: Features dedicated fan spinning animation, power on/off, and fan speed percentage control.
* **Integrated Preset Modes**: `Auto`, `Night`, and `Turbo` modes are built directly into the purifier controls without creating separate confusing switches.
* **Native Filter Life Indicator**: Through `linked_filter_life_level_sensor`, opening the purifier accessory in Apple Home displays real-time filter life percentage and replacement warnings.
* **5-Tier Air Quality Rating**: Natively maps to HomeKit's 5 rating levels (Excellent, Good, Fair, Inferior, Poor) displayed prominently at the top of the room.
* **Physical Serial Number & Firmware Sync**: Automatically maps the device's physical serial number (`thing_id`, e.g. `23342A03013613BAB`) and firmware/hardware versions to HomeKit `AccessoryInformation`. In Apple Home, tap **Accessory Details** to view the authentic hardware serial number matching Home Assistant! *(If paired previously, reload the HomeKit bridge in HA to refresh the cache)*
* **Siri Voice Control**:
  * *"Hey Siri, set the air purifier to Auto mode"*
  * *"Hey Siri, set the air purifier fan speed to 60%"*

---

## ❓ Frequently Asked Questions (FAQ)

### Q1: What happens when the token expires after phone & password login?
**Completely seamless automatic refresh!**  
This integration features an automatic background token renewal mechanism. Before the Access Token expires, the integration automatically contacts the Amway Gluu authorization server using the Refresh Token. Even if a Refresh Token expires unexpectedly, the integration uses the stored credentials to silently re-authenticate without interrupting your daily automations.

### Q2: Is logging in via Access Token secure?
**Very secure!**  
The key advantage of token login is that **your account password is never stored in Home Assistant**. The Access Token is strictly scoped to reading and controlling your registered devices, without exposing sensitive personal or payment details.

### Q3: Which models are supported?
* **Atmosphere Sky™ Air Treatment System**: Full support for 5 fan speed steps, Auto/Night/Turbo preset modes, Pre-filter/HEPA/Carbon filter life monitoring, and particle Air Quality index.
* **Atmosphere Mini™ Air Treatment System**: Full support for 3 fan speed steps, Auto/Night preset modes, and 2-in-1 filter life monitoring.
