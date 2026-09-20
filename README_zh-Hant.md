# Amway Atmosphere for Home Assistant & Apple HomeKit (繁體中文)

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

專為 **Amway Atmosphere Sky** 與 **Amway Atmosphere Mini** 空氣清淨機打造的 Home Assistant 官方級自訂整合元件。基於最新版 *Amway Healthy Home* App 雲端通訊協議逆向工程實作，並具備與 **Apple HomeKit 空氣清淨機與空氣品質感測器** 的原生橋接整合。

---

> 💡 **第一次連線設定？** 請直接參閱 👉 [**新手快速連線與 Token 取得指南 (Setup Guide)**](docs/setup-guide.md)

## ✨ 主要功能特點

- **🌀 完整風扇與清淨機控制實體 (`fan`)**:
  - **Atmosphere Sky**: 5 段獨立風速調節（20%、40%、60%、80%、100%）。
  - **Atmosphere Mini**: 3 段獨立風速調節（33%、67%、100%）。
  - **預設模式 (Preset Modes)**: 支援 `自動 (Auto)`、`夜間 (Night)`、`超速 (Turbo)`（僅 Sky 支援）。
  - **電源控制**: 即時開關機切換與設備狀態精確反饋。
- **🍃 Apple HomeKit 5 級空氣品質感測器 (`sensor`)**:
  - 完美對應 Apple HomeKit 原生 `AirQuality` 特徵數值：
    - `1`: 優良 (Excellent)
    - `2`: 良好 (Good)
    - `3`: 普通 (Fair)
    - `4`: 不良 (Inferior)
    - `5`: 極差 (Poor)
  - 數值型 **潔淨空氣輸出值 (Clean Air Value)** 感測器 (`cleanAirVal`)。
- **🛡️ 多重濾網壽命追蹤感測器 (`sensor`)**:
  - 前置濾網壽命 (`0–100%`)
  - HEPA 濾網壽命 (`0–100%`)
  - 活性碳氣味濾網壽命 (`0–100%`，僅 Sky 支援)
- **🗂️ Apple Home (家庭 App) 多張卡片支援 (顯示為個別標籤頁)**:
  - 支援 Apple Home 的 **「顯示為個別標籤頁 (Show as Separate Tiles)」**，將清淨機拆解為「清淨機開關與風速」和「室內空氣品質感測儀」兩張獨立卡片。
  - 在 Home Assistant 內呈現獨立乾淨的各類實體，便於自訂儀表板。

---

## 📱 Apple Home (家庭 App) 多張卡片設定指南

當您透過 Home Assistant 的 **HomeKit Bridge (家庭橋接)** 將清淨機同步至 Apple Home 時，預設會合併在同一個配件磁貼中。如果您希望像原廠 HomeKit 配件一樣拆解為獨立磁貼：

1. 開啟 iPhone、iPad 或 Mac 上的 **「家庭 (Home)」** App。
2. 長按進入 **「Atmosphere 空氣清淨機」** 配件頁面。
3. 點擊右下角的 **「設定 (齒輪圖示)」**。
4. 點選 **「顯示為個別標籤頁 (Show as Separate Tiles)」**。
5. 完成！Apple Home 會自動將設備拆解為兩張獨立卡片：
   - **卡片 1**：空氣清淨機開關、百分比風速滑桿、自動/夜間/超速模式切換。
   - **卡片 2**：室內空氣品質等級儀表與狀態指示。
   您可以隨意將它們移動或釘選至常用配件與各個房間。

---

## 📦 安裝步驟 (Installation)

### 方法一：透過 HACS 自訂儲存庫安裝（推薦）

1. 開啟 Home Assistant 側邊欄中的 **HACS**。
2. 點擊右上角選單圖示（三個點 `...`）$\rightarrow$ **「自訂儲存庫 (Custom repositories)」**。
3. 在儲存庫網址輸入：
   ```text
   https://github.com/zpqnzpqn/Amway_ATMOSPHERE
   ```
4. 類別選擇 **「整合 (Integration)」**，點選 **「新增 (Add)」**。
5. 在 HACS 清單中搜尋 **「Amway Atmosphere」** 並點選 **「下載」**。
6. **重新啟動 Home Assistant**。

### 方法二：手動複製安裝

1. 自 [Releases](https://github.com/zpqnzpqn/Amway_ATMOSPHERE/releases) 頁面下載最新版本原始碼。
2. 將 `custom_components/amway_atmosphere` 目錄完整複製至您的 Home Assistant 設定目錄：
   ```text
   config/custom_components/amway_atmosphere/
   ```
3. **重新啟動 Home Assistant**。

---

## ⚙️ 登入與設定步驟 (Configuration)

1. 在 Home Assistant 中前往 **「設定」 $\rightarrow$ 「裝置與服務」 $\rightarrow$ 「新增整合」**。
2. 搜尋並點選 **「Amway Atmosphere」**。
3. 選擇您偏好的連線驗證方式：

### 方式 A：直接輸入 Access Token（最推薦、零密碼風險）
由於安麗官方 App 採用 AppAuth PKCE 機制，最穩定且不需儲存密碼的方式為使用 Access Token：
1. 在您的電腦終端機執行輕量捕獲助手：
   ```bash
   python3 tools/get_token.py --proxy
   ```
2. 依照終端機顯示的指引操作：
   - 將手機連線至相同 Wi-Fi，並在 Wi-Fi 設定中將 HTTP 代理設定為電腦的 IP。
   - 打開手機上的 **Amway Healthy Home** App 並登入或操作開關。
   - 助手偵測到 Token 後會立即印出並自動乾淨關閉代理。
3. 將捕獲到的 **Access Token** 貼入 Home Assistant 設定精靈，點擊 **「傳送」** 即可！

### 方式 B：輸入手機號碼與密碼直接登入
在設定精靈中輸入安麗帳號註冊的手機號碼（支援 `09xxxxxxxx` 或 `+8869xxxxxxxx`）與密碼完成綁定。

### 方式 C：瀏覽器手動換取授權碼
執行 `python3 tools/get_token.py --manual`，在瀏覽器登入後將跳轉網址貼回自動換取 Token。

4. 設定完成後，系統將自動搜尋並建立您名下所有的 Atmosphere Sky 與 Atmosphere Mini 清淨機實體！

---

## 📊 儀表板卡片範例 (Lovelace Cards)

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

### 3. 濾網耗材壽命清單 (Entities Card)
```yaml
type: entities
title: 濾網耗材剩餘壽命
entities:
  - entity: sensor.atmosphere_sky_prefilter_life
    name: 前置濾網壽命
  - entity: sensor.atmosphere_sky_hepa_life
    name: HEPA 濾網壽命
  - entity: sensor.atmosphere_sky_carbon_life
    name: 活性碳氣味濾網壽命
```

---

## 🛠️ 技術架構與實現細節

- **IoT Class**: `cloud_polling`（預設每 30 秒向 Conex API 同步一次最新設備 Shadow 數據）。
- **即時控制**: 發送風速、電源、模式等控制指令時，透過 AWS IoT REST API (SigV4 簽名) 直接向設備 Shadow 發送 `RemoteButton`，並在 1 秒內主動觸發 Coordinator 刷新，反應迅速且操作手感滑順。
- **認證機制**: 採用標準 Gluu OAuth2 IDP (`oxauth/restv1`)，底層自動管理 Access Token 與 Refresh Token，憑證過期時自動進行背景續期，無需頻繁重新登入。
- **地區相容性**: 基於 Amway Global Healthy Home 雲端體系，於台灣地區帳號完整實測通過。

---

## ⚠️ 免責聲明 (Disclaimer)

本專案為社群開源獨立開發，非安麗官方 (Amway Corp.) 出品或提供技術支援。文中所有商標、名稱及標誌均為各自擁有者之財產。
