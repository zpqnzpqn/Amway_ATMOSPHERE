# 安麗逸新空氣清淨機 (Amway Atmosphere) Home Assistant 連線與設定指南

本指南專為所有 Home Assistant 使用者設計，協助您在 1 分鐘內順利完成安麗 Atmosphere Sky / Mini 空氣清淨機的綁定與啟用。

---

## 🚀 推薦連線方式一：手機號碼與密碼直接登入（最簡單、免開瀏覽器）

自 `v0.4.0` 起，本整合完整模擬安麗官方 Healthy Home 原生 App 的 OAuth2 + PKCE 鑑權協議。使用者**無需點擊網址、無需跳轉、無需任何抓包工具**，直接在 Home Assistant 介面填入帳號密碼即可完成！

1. 在 Home Assistant 中前往 **「設定」 $\rightarrow$ 「裝置與服務」 $\rightarrow$ 「新增整合」** $\rightarrow$ 搜尋 **Amway Atmosphere**。
2. 直接輸入您的 **手機號碼**（支援 `0912345678` 或 `+886912345678`）與 **密碼**。
3. 國家代碼預設為 `TW`（台灣）。
4. 點選 **「傳送」**，系統將自動完成鑑權交換，並自動取得永久 Refresh Token！
5. 清淨機設備與感測器將立即出現在 Home Assistant！

---

## 💡 進階連線方式三：使用 Token 助手小工具（雙 Token 自動複製）

如果您習慣在終端機操作，亦可使用本專案內建的雙 Token 捕獲工具：

```bash
# 瀏覽器手動換證模式（推薦）
python3 tools/get_token.py --manual
```
工具會自動換取並截獲 `Access Token` 與 `Refresh Token`，並自動拷貝至剪貼簿，直接在「Access Token 或 JSON 負載」欄位貼上即可。

---

---

## 🍏 Apple HomeKit 完美設定教學 (type: air_purifier)

本整合完全相容 Apple HomeKit 原生規範，可將安麗空氣清淨機以 **原生空氣清淨機 (Air Purifier)** 形式橋接至 Apple「家庭」App，並透過獨立感測器與互鎖開關達成極致體驗：

### 1. configuration.yaml 設定範例
在您的 Home Assistant `configuration.yaml` 中，加入 HomeKit 橋接設定：

```yaml
homekit:
  - name: "Amway HomeKit Bridge"
    port: 21064
    mode: bridge
    filter:
      include_entities:
        - fan.atmosphere_sky_air_treatment_system
        - switch.atmosphere_sky_air_treatment_system_auto_mode
        - switch.atmosphere_sky_air_treatment_system_night_mode
        - switch.atmosphere_sky_air_treatment_system_turbo_mode
        - sensor.atmosphere_sky_air_treatment_system_air_quality
        - sensor.atmosphere_sky_air_treatment_system_hepa_filter_life
    entity_config:
      fan.atmosphere_sky_air_treatment_system:
        type: air_purifier
```

### 2. 功能特點
* **Apple 原生空氣清淨機圖標**：不再顯示為電風扇，具備專屬淨化器動畫與自動/手動切換開關。
* **三開關嚴格互鎖**：`Auto Mode`、`Night Mode`、`Turbo Mode` 開關具備單選互鎖特性。手動調整風速滑桿時，三個開關自動全部彈回關閉 (OFF)。
* **Siri 語音極致聲控**：可直接使用 Siri 控制：
  * *「嘿 Siri，打開空氣清淨機的夜間模式」*
  * *「嘿 Siri，將空氣清淨機風速設為 60%」*
* **感測器獨立分類**：空氣品質（1~5級）與濾網壽命可在 HomeKit 作為獨立配件顯示於家庭 App 的「環境」與設備面板中。

---

## ❓ 常見問題 (FAQ)

### Q1：使用 Access Token 連線安全嗎？
**非常安全！**  
使用 Access Token 登入的最大優勢在於：**您完全不需要將您的安麗帳號與登入密碼儲存在 Home Assistant 中**。Token 僅具備讀取與控制設備的專屬權限，不會暴露您的付款或個人敏感資料。

### Q2：Token 會過期嗎？過期了怎麼辦？
官方 Token 有效期約為數個月至一年。若日後 Token 失效導致設備離線，只需重新執行一次 `python3 tools/get_token.py`，並在 Home Assistant 點選該整合的 **「重新認證 (Re-authenticate)」** 貼上最新 Token 即可無縫復原，原有自動化設定與卡片完全不受影響！

### Q3：支援哪些設備型號？
* **Atmosphere Sky™ Air Treatment System**：完整支援 5 段風速、自動/夜間/強效三開關互鎖、前置/HEPA/碳濾網壽命監控、粉塵空氣品質指數。
* **Atmosphere Mini™ Air Treatment System**：完整支援 3 段風速、自動/夜間二開關互鎖、二合一濾網壽命監控。

