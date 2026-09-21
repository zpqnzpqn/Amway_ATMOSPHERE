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

專為 **Amway Atmosphere Sky** 與 **Amway Atmosphere Mini** 空氣清淨機打造的 Home Assistant 官方級自訂整合元件（Custom Integration）。基於最新版 *Amway Healthy Home* 雲端通訊協議逆向工程實作，具備 AWS IoT Device Shadow 即時雙向控制，並與 **Apple HomeKit 空氣清淨機與五段空氣品質** 達成原生級橋接。

---

> 🚀 **版本發行說明 (Release v1.0.0 - 首發正式版)**  
> 本版本為正式發行版本（General Availability），所有核心功能皆經真機實測與 38 項全自動化單元測試驗證通過：
> - 支援手機號碼 + 密碼直接登入，底層自動完成 Gluu PKCE 授權換取 Token，並具備背景無感自動續期機制。
> - 完整支援 Atmosphere Sky（5 段風速、三層濾網、Turbo 模式）與 Atmosphere Mini（3 段風速、二合一濾網）。
> - 風扇與模式控制原生內建於清淨機實體（Fan Entity），自動清理舊版冗餘開關。
> - 獨家動態 HomeKit 序號同步鉤子，將安麗實體機身序號與韌體版本 100% 同步至 Apple「家庭」App 序號欄位。
> - 新手設定步驟請參閱 👉 [**新手快速連線與 HomeKit 設定指南**](docs/setup-guide.md)

---

## ✨ 主要功能特點

- **🌀 原生清淨機與風扇控制實體 (`fan`)**:
  - **Atmosphere Sky**: 5 段獨立風速調節（20%、40%、60%、80%、100%）。
  - **Atmosphere Mini**: 3 段獨立風速調節（33%、67%、100%）。
  - **內建預設模式 (Preset Modes)**: 支援 `Auto (自動)`、`Night (夜間)`、`Turbo (強效 / 極速)`，免去傳統外掛獨立開關的雜亂。
  - **秒級雲端控制**: 透過 AWS IoT REST API (SigV4 簽名) 直接向 Device Shadow 發送指令，操作毫秒級響應。
- **🍃 Apple HomeKit 原生 5 級空氣品質感測器 (`sensor`)**:
  - 完美對應 Apple HomeKit 原生 `AirQuality` 特徵數值（顯示於房間頂部圖標）：
    - `1`: 極佳 (Excellent)
    - `2`: 良好 (Good)
    - `3`: 一般 (Fair)
    - `4`: 欠佳 (Inferior)
    - `5`: 極差 (Poor)
- **🛡️ 多重濾網壽命追蹤感測器 (`sensor`)**:
  - 前置濾網壽命 (`0–100%`)
  - HEPA 濾網壽命 (`0–100%`)
  - 活性碳氣味濾網壽命 (`0–100%`，僅 Sky 支援)
- **📱 Apple Home 實體機身序號與配件資訊完美對應**:
  - 自動將安麗實體機身序號與韌體/硬體版本帶入 HomeKit，告別 HA 預設顯示的隨機實體名稱。
- **🗂️ Apple Home (家庭 App) 多張卡片支援 (顯示為個別標籤頁)**:
  - 支援 Apple Home 的 **「顯示為個別標籤頁 (Show as Separate Tiles)」**，將設備拆解為「清淨機控制」和「室內空氣品質」兩張獨立卡片。

---

## 📦 安裝步驟 (Installation)

### 方法一：透過 HACS 安裝（推薦）

> 💡 **尚未安裝 HACS？** 請先參閱 👉 [**HACS 官方安裝與使用手冊**](https://www.hacs.xyz/docs/use) 完成 Home Assistant 社群商店之建置；或直接使用下方 **方法二** 手動複製安裝（完全無需 HACS）。

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
3. 提供兩種便利的連線驗證方式：
   - **方式 A：手機號碼與密碼直接登入（最便利）**：
     輸入安麗帳號註冊的手機號碼（例如 `0912345678` 或 `+886912345678`）與登入密碼，整合將自動完成雲端認證與 Token 續期。
   - **方式 B：直接輸入 Access Token（零密碼風險）**：
     若您偏好不將帳密儲存於 HA 中，可執行專屬助手工具 `python3 tools/get_token.py --proxy` 取得 Token 後直接貼入。
4. 設定完成後，系統將自動搜尋並建立名下所有清淨機設備與感測器！

---

## 🍏 Apple HomeKit 完美設定範例

若要讓 Apple 家庭 App 達到原生空氣清淨機的極致體驗，請在 `configuration.yaml` 中配置：

```yaml
homekit:
  - name: "Amway HomeKit Bridge"
    port: 21064
    mode: bridge
    filter:
      include_entities:
        - fan.atmosphere_sky_air_treatment_system # 或您的 fan.<device_name>
        - sensor.atmosphere_sky_air_treatment_system_air_quality
    entity_config:
      fan.atmosphere_sky_air_treatment_system:
        type: air_purifier
        # 將清淨機內建的濾網百分比與耗盡警報綁定至最低濾網壽命
        linked_filter_life_level_sensor: sensor.atmosphere_sky_lowest_filter_life
```

> 💡 **5 項感測器 HomeKit 對應評估表與濾網自動最低壽命綁定教學**，請參閱 👉 [**Apple HomeKit 完整設定教學**](docs/setup-guide.md#-apple-homekit-完美設定教學-type-air_purifier)

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
    label: 極佳
  - from: 2
    color: "#8bc34a"
    label: 良好
  - from: 3
    color: "#ffc107"
    label: 一般
  - from: 4
    color: "#ff9800"
    label: 欠佳
  - from: 5
    color: "#f44336"
    label: 極差
```

---

## 🛠️ 技術架構與實現細節

- **IoT Class**: `cloud_polling`（預設每 30 秒向 Conex API 同步一次最新設備 Shadow 數據）。
- **即時控制**: 發送風速、電源、模式等控制指令時，透過 AWS IoT REST API (SigV4 簽名) 直接向設備 Shadow 發送 `RemoteButton`，並在 1 秒內主動觸發 Coordinator 刷新，操作手感毫無延遲。
- **認證機制**: 採用標準 Gluu OAuth2 IDP (`oxauth/restv1`)，底層自動管理 Access Token 與 Refresh Token，憑證過期時自動進行背景續期，無需頻繁重新登入。
- **地區相容性**: 基於 Amway Global Healthy Home 雲端體系，於台灣地區帳號完整實測通過。

---

## ⚠️ 免責聲明 (Disclaimer)

本專案為社群獨立開發之開源軟體，非安麗官方（Amway Corp.）官方出品或贊助產品。所有商標、產品名稱均屬於原權利人所有。
