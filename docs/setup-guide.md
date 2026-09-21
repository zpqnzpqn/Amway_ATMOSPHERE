# 安麗逸新空氣清淨機 (Amway Atmosphere) Home Assistant 連線與 HomeKit 設定指南

<p align="center">
  <a href="setup-guide_en.md"><b>English</b></a> |
  <a href="setup-guide.md"><b>繁體中文</b></a> |
  <a href="setup-guide_ja.md"><b>日本語</b></a>
</p>

> 🚀 **v1.0.0 首發正式版發行說明 (General Availability)**  
> 本指南專為所有 Home Assistant 與 Apple HomeKit 使用者設計，協助您快速完成安麗 Atmosphere Sky / Mini 空氣清淨機的綁定與啟用。  
> 本版本具備手機密碼直接登入、AWS IoT Shadow 雲端即時雙向控制、HomeKit 原生空氣清淨機與 5 級空氣品質評級對應、實體機身序號同步等完整旗艦功能。

---

> 💡 **事前準備（安裝整合）**：  
> 本整合需先安裝至 Home Assistant。您可以透過 HACS 自訂儲存庫安裝並重啟 HA（若尚未安裝 HACS，請參閱 👉 [**HACS 官方安裝與使用手冊**](https://www.hacs.xyz/docs/use) 完成安裝）；亦可直接下載原始碼手動放入 `config/custom_components/amway_atmosphere/`。

## 🚀 連線登入方式

### 方式一：手機號碼與密碼直接登入（最推薦、免開瀏覽器）

本整合完整實作安麗官方 Healthy Home 原生 App 的 OAuth2 + PKCE 鑑權協議。使用者**無需點擊網址、無需跳轉、無需任何抓包工具**，直接在 Home Assistant 介面填入帳號密碼即可完成：

1. 在 Home Assistant 中前往 **「設定」 $\rightarrow$ 「裝置與服務」 $\rightarrow$ 「新增整合」** $\rightarrow$ 搜尋 **Amway Atmosphere**。
2. 直接輸入您的 **手機號碼**（支援 `0912345678` 或 `+886912345678`）與 **密碼**。
3. 國家代碼預設為 `TW`（台灣）。
4. 點選 **「傳送」**，系統將自動完成鑑權交換，並取得 Refresh Token 進行背景自動續期！
5. 清淨機設備與感測器將立即出現在 Home Assistant！

---

### 方式二：使用 Access Token 直接登入（零密碼風險）

如果您偏好不將個人密碼儲存於 Home Assistant，亦可使用專屬助手工具截取 Token 直接填入：

```bash
python3 tools/get_token.py --proxy
```
依照終端機指引操作手機 App 發送請求，工具獲取 Token 後會自動印出並複製，直接貼入設定畫面即可。

---

## 🍏 Apple HomeKit 完美設定教學 (type: air_purifier)

本整合完全相容 Apple HomeKit 原生規範，可將安麗空氣清淨機以 **原生空氣清淨機 (Air Purifier)** 形式橋接至 Apple「家庭」App，並透過獨立感測器與互鎖開關達成極致體驗：

### 1. 5 項感測器 HomeKit 對應評估表

| 感測器名稱 | 數值範例 | HomeKit 原生支援度 | 對應 HomeKit 類型 / 特徵 | 呈現效果與說明 |
| :--- | :--- | :--- | :--- | :--- |
| **HEPA Filter Life** | 40% | ✅ 原生支援 | 附屬於 `air_purifier` 的 `FilterLifeLevel` 特徵 | 透過清淨機本體綁定後，在「家庭」App 點開清淨機卡片會直接顯示「濾網壽命：40%」，壽命過低時會自動跳出「需要更換濾網」的系統警報。 |
| **Carbon Filter Life** | 13% | ⚠️ 需二選一或取最小值 | 同上（HomeKit 一台清淨機僅能綁定一組 Filter 讀數） | HomeKit 規範一台清淨機僅能有一個 `FilterLifeLevel`。通常建議綁定最快耗盡的濾網（如活性碳 13%），或透過 HA 模板取三者最小值。 |
| **Pre-Filter Life** | 58% | ⚠️ 需二選一或取最小值 | 同上 | 同上說明。 |
| **Air Quality** | good | ✅ 原生支援 | `AirQualitySensor` (空氣品質感測器) | HomeKit 原生支援五段評級（Excellent / Good / Fair / Inferior / Poor）。在家庭 App 中會作為專屬小圖標顯示於房間頂部，顯示「良好」。 |
| **Clean Air Value** | 795 | ❌ 無原生對應 Type | 無 (Apple 無通用數值/CADR 配件) | Apple HomeKit 不允許隨意傳遞無型態的純數字。若強制偽裝成溫度/濕度/PM2.5，會導致讀數單位與分析嚴重失真（例如顯示 795°C 或 795%），**建議留在 Home Assistant 儀表板檢視即可，不納入 HomeKit 橋接**。 |

---

### 2. 🛠️ 最佳 HomeKit 設定範例 (configuration.yaml)

若要讓 Apple 家庭 App 達到最完美的顯示效果，請在 Home Assistant 的 `configuration.yaml` 中使用以下設定（排除不相容的數值感測器，僅橋接相容之清淨機與空氣品質評級）：

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

> 💡 **實體名稱小提示**：若您的實體是以自訂或房間名稱命名（例如 `fan.living_room_atmosphere_sky`），請依您的實際 entity_id 相應替換。

---

### 3. 💡 進階技巧：三層濾網「自動取最低壽命」綁定

由於 Atmosphere Sky 有前置、HEPA、活性碳三層濾網，您可以利用 HA 的 Template Sensor 算出版內壽命最低的那一個濾網：

#### 設定方式 A：寫入 `configuration.yaml`
```yaml
template:
  - sensor:
      - name: "Atmosphere Sky 濾網最低壽命"
        unique_id: atmosphere_sky_lowest_filter_life
        unit_of_measurement: "%"
        state: >
          {{ [
            states('sensor.atmosphere_sky_air_treatment_system_hepa_filter_life') | int(100),
            states('sensor.atmosphere_sky_air_treatment_system_carbon_filter_life') | int(100),
            states('sensor.atmosphere_sky_air_treatment_system_pre_filter_life') | int(100)
          ] | min }}
```

#### 設定方式 B：透過 HA 網頁介面建立（免寫 YAML）
1. 前往 **「設定」 > 「裝置與服務」 > 「輔助程式」**。
2. 點擊 **「+ 建立輔助程式」 > 「樣板」 > 「樣板感測器」**。
3. 名稱填入 `Atmosphere Sky 濾網最低壽命`，狀態樣板貼入上方 Jinja 語法，單位填入 `%` 即可。

接著將 `linked_filter_life_level_sensor` 指向 `sensor.atmosphere_sky_lowest_filter_life`，這樣無論哪一片濾網先耗盡（例如活性碳剩 13%），Apple 家庭 App 都會在第一時間為您推播更換通知！

---

### 4. Apple Home 功能與呈現亮點

* **Apple 原生空氣清淨機圖標**：具備專屬淨化器旋轉動畫，支援開關機與風速百分比調節。
* **原生 Preset Mode 整合**：`Auto`、`Night`、`Turbo` 模式直接內建於清淨機控制項中，無需額外建立獨立開關。
* **濾網壽命原生整合**：透過 `linked_filter_life_level_sensor`，點開家庭 App 清淨機面板即可檢視濾網百分比讀數與耗盡警示。
* **空氣品質評級**：支援 HomeKit 五段評級（極佳、良好、一般、欠佳、極差），顯示於家庭 App 房間頂端。
* **實體機身序號與韌體同步**：自動將安麗實體機身序號及韌體/硬體版本直接對應至 HomeKit `AccessoryInformation` 服務。在 Apple「家庭」App 點選「配件詳細資訊」即可看到真實序號與 Home Assistant 裝置資訊完全一致！*(若更新前已配對，可在 HA 重新載入 HomeKit 橋接器以同步更新快取)*
* **Siri 語音極致聲控**：可直接使用 Siri 控制：
  * *「嘿 Siri，將空氣清淨機設為自動模式」*
  * *「嘿 Siri，將空氣清淨機風速設為 60%」*

---

## ❓ 常見問題 (FAQ)

### Q1：手機密碼登入後，Token 過期會怎麼樣？
**完全無感自動續期！**  
本整合具備自動 Token 續期機制。當 Access Token 即將過期時，整合會在背景自動向安麗 Gluu 授權伺服器使用 Refresh Token 換取最新 Token；即使 Refresh Token 偶發失效，整合亦會使用儲存的密碼憑證自動重新鑑權，絕不影響日常自動化運作。

### Q2：使用 Access Token 連線安全嗎？
**非常安全！**  
使用 Access Token 登入的最大優勢在於：**您完全不需要將您的安麗帳號與登入密碼儲存在 Home Assistant 中**。Token 僅具備讀取與控制設備的專屬權限，不會暴露您的付款或個人敏感資料。

### Q3：支援哪些設備型號？
* **Atmosphere Sky™ Air Treatment System**：完整支援 5 段風速、自動/夜間/強效模式切換、前置/HEPA/活性碳濾網壽命監控、粉塵空氣品質指數。
* **Atmosphere Mini™ Air Treatment System**：完整支援 3 段風速、自動/夜間模式切換、二合一濾網壽命監控。
