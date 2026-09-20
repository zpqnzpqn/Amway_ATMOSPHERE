# Amway Atmosphere for Home Assistant & Apple HomeKit

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://www.home-assistant.io)
[![Apple HomeKit](https://img.shields.io/badge/Apple%20HomeKit-Compatible-black.svg)](https://www.apple.com/home-app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An official-grade Home Assistant custom integration for **Amway Atmosphere Sky** and **Amway Atmosphere Mini** air treatment systems, fully reverse-engineered from the current official *Amway Healthy Home* app (Taiwan region) with native **Apple HomeKit Air Purifier & Air Quality** bridging.

---

## ✨ Features

- **🌀 Comprehensive Fan & Purifier Control (`fan`)**:
  - **Atmosphere Sky**: 5 discrete fan speed steps (20%, 40%, 60%, 80%, 100%).
  - **Atmosphere Mini**: 3 discrete fan speed steps (33%, 67%, 100%).
  - **Preset Modes**: `Auto`, `Night`, `Turbo` (Sky only).
  - **Power Toggle**: Smooth On/Off and state tracking.
- **🍃 Apple HomeKit 5-Tier Air Quality Sensor (`sensor`)**:
  - Direct mapping to Apple HomeKit's native `AirQuality` characteristic:
    - `1`: Excellent (優良)
    - `2`: Good (良好)
    - `3`: Fair (普通)
    - `4`: Inferior (不良)
    - `5`: Poor (極差)
  - Numeric **Clean Air Value** sensor (`cleanAirVal`).
- **🛡️ Multi-Stage Filter Lifecycle Tracking (`sensor`)**:
  - Pre-filter Life (`0–100%`)
  - HEPA Filter Life (`0–100%`)
  - Carbon Odor Filter Life (`0–100%`, Sky only)
- **🗂️ Multi-Card / Separate Tiles Support (多張獨立卡片)**:
  - Supports Apple Home's **"顯示為個別標籤頁 (Show as Separate Tiles)"** to split the appliance into discrete Purifier and Air Quality cards.
  - Exposes independent entities in Home Assistant for flexible dashboard layout.

---

## 📱 Apple Home (家庭 App) 多張卡片設定指南

當您透過 Home Assistant 的 **HomeKit Bridge (家庭橋接)** 將安麗清淨機同步至 Apple Home 時，預設可能會合併在同一個配件磁貼中。如果您希望像原廠配件一樣拆分成多張獨立卡片：

1. 開啟 iPhone、iPad 或 Mac 上的 **「家庭 (Home)」** App。
2. 長按進入 **「Atmosphere 空氣清淨機」** 配件頁面。
3. 點擊右下角的 **「設定 (齒輪圖示)」**。
4. 點選 **「顯示為個別標籤頁 (Show as Separate Tiles)」**。
5. 完成！Apple Home 會自動將設備拆解為兩張獨立卡片：
   - **卡片 1**：空氣清淨機開關、百分比風速滑桿、自動/夜間/超速模式。
   - **卡片 2**：室內空氣品質等級 (良好/普通/不良) 與感測儀。
   您可以隨意將它們釘選或移動到不同的房間與首頁。

---

## 📦 安裝步驟 (Installation)

### 方法一：透過 HACS 自訂儲存庫安裝（推薦）
1. 打開 Home Assistant 側邊欄中的 **HACS**。
2. 點擊右上角的選單圖示（三個點） $\rightarrow$ **「自訂儲存庫 (Custom repositories)」**。
3. 在儲存庫網址輸入本專案 GitHub 網址，類別選擇 **「整合 (Integration)」**，點選新增。
4. 搜尋 **「Amway Atmosphere」** 並點選 **「下載」**。
5. 重新啟動 Home Assistant。

### 方法二：手動安裝
1. 下載本專案原始碼。
2. 將 `custom_components/amway_atmosphere` 資料夾完整複製至您的 Home Assistant 設定目錄下的 `config/custom_components/`。
3. 重新啟動 Home Assistant。

---

## ⚙️ 設定步驟 (Configuration)

1. 在 Home Assistant 中前往 **「設定」 $\rightarrow$ 「裝置與服務」 $\rightarrow$ 「新增整合」**。
2. 搜尋並選擇 **「Amway Atmosphere」**。
3. 畫面上會顯示登入連結：
   - 點擊連結在瀏覽器中開啟安麗官方登入頁面（支援安麗台灣帳號）。
   - 登入完成後，瀏覽器會嘗試跳轉至 `amwayhealthyhome://loginRedirect?code=...`（此時瀏覽器提示找不到網頁是正常的）。
   - 複製網址列的完整網址（或其中的 `code` 數值），貼回 Home Assistant 的輸入框中並送出。
4. 整合將自動完成驗證，並自動探索您帳號下綁定的所有 Atmosphere Sky 和 Mini 設備！

---

## 📊 Home Assistant 儀表板卡片範例 (Lovelace Cards)

### 1. 清淨機控制卡片 (Tile Card)
```yaml
type: tile
entity: fan.atmosphere_sky
name: 客廳清淨機
features:
  - type: fan-speed
  - type: fan-preset-modes
    style: dropdown
    preset_modes:
      - auto
      - night
      - turbo
```

### 2. 空氣品質儀表盤 (Gauge Card)
```yaml
type: gauge
entity: sensor.atmosphere_sky_air_quality
name: 室內空氣品質
needle: true
segments:
  - from: 1
    color: "#4caf50"
    label: 優良
  - from: 2
    color: "#8bc34a"
    label: 良好
  - from: 3
    color: "#ffc107"
    label: 普通
  - from: 4
    color: "#ff9800"
    label: 不良
  - from: 5
    color: "#f44336"
    label: 極差
```

### 3. 濾網壽命監控清單 (Entities Card)
```yaml
type: entities
title: 濾網耗材壽命
entities:
  - entity: sensor.atmosphere_sky_prefilter_life
    name: 前置濾網壽命
  - entity: sensor.atmosphere_sky_hepa_life
    name: HEPA 濾網壽命
  - entity: sensor.atmosphere_sky_carbon_life
    name: 活性碳氣味濾網壽命
```

---

## 🛠️ 技術細節與架構 (Architecture)

- **IoT Class**: `cloud_polling`（預設每 30 秒自動透過 Conex API 同步 Shadow 狀態）。
- **即時控制**: 當發送按鈕控制指令（如調整風速、開關機、切換 Turbo/Auto）時，整合透過 AWS IoT REST API (SigV4 簽名) 直接向設備 Shadow 發送 `RemoteButton` 期望狀態，並在 1 秒內主動觸發 Coordinator 刷新，兼顧反應速度與連線穩定度。
- **認證架構**:
  - Gluu OAuth2 IDP (`oxauth/restv1`) 自動維持 Access Token 與 Refresh Token。
  - 憑證過期時自動進行背景 Refresh，無需手動重新登入。

---

## ⚠️ 免責聲明 (Disclaimer)

本專案為第三方開源整合，非安麗官方 (Amway Corp.) 出品或支援。所有商標及產品名稱均為安麗公司所有。
