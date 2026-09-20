# 安麗逸新空氣清淨機 (Amway Atmosphere) Home Assistant 連線與設定指南

本指南專為所有 Home Assistant 使用者設計，協助您在 1 分鐘內順利完成安麗 Atmosphere Sky / Mini 空氣清淨機的綁定與啟用。

---

## ⚠️ 重要先備知識：為什麼不能在一般網頁登入？

當您在電腦瀏覽器點開安麗登入頁面時，常會看到一個**綠色的登入畫面（oxAuth / Gluu）**且輸入帳密必定失敗。  
這是因為：
* 安麗官方雲端伺服器設有 App 驗證防護，只允許官方手機應用程式（Amway Healthy Home App）正常通過認證。
* 任何透過一般電腦瀏覽器開啟的請求，都會被伺服器導向內部的工程維護頁面（綠色畫面），該頁面**完全沒有台灣消費者的帳號密碼資料庫**。

因此，**請不要使用電腦瀏覽器手動登入**。我們提供了專屬的輕量小工具，只需 3 個步驟即可秒取 Token！

---

## 🚀 推薦連線方式：使用 Token 助手快速取得（100% 成功）

### 步驟 1：在電腦終端機啟動小工具
開啟終端機（Terminal），執行：
```bash
python3 tools/get_token.py
```
終端機將會自動偵測您的電腦 IP，並開啟常駐監聽：
```text
本機 IP 位址:  10.0.1.99
代理伺服器連接埠: 8080
```

### 步驟 2：手機設定 Wi-Fi 代理
1. 確保您的手機與電腦處於**同一個 Wi-Fi 網路**。
2. 打開手機的 **Wi-Fi 設定** $\rightarrow$ 點選已連線 Wi-Fi 旁邊的 **「ⓘ」**。
3. 滑到最下方找到 **「設定代理伺服器」** $\rightarrow$ 選擇 **「手動」**：
   - **伺服器**：填入剛才終端機顯示的電腦 IP（如 `10.0.1.99`）
   - **連接埠**：填入 `8080`
   - 點擊右上角 **「儲存」**。

### 步驟 3：在手機 App 觸發連線
1. 打開手機上的 **Amway Healthy Home** App。
2. 進入空氣清淨機頁面或切換開關。
3. 此時電腦終端機會**立刻自動捕獲 Token，並自動複製到電腦剪貼簿**！
4. **手機復原**：將手機 Wi-Fi 中的「設定代理伺服器」切換回 **「關閉」** 即可。

### 步驟 4：貼入 Home Assistant 完成綁定
1. 在 Home Assistant 中前往 **「設定」 $\rightarrow$ 「裝置與服務」 $\rightarrow$ 「新增整合」** $\rightarrow$ 搜尋 **Amway Atmosphere**。
2. 將剛才複製的 Token 貼入第一欄 **「Access Token（推薦，免帳密）」**。
3. 點選 **「傳送」**，完成！您的清淨機實體、風速控制與三道濾網數據將立刻出現在 Home Assistant！

---

## 📱 備用方式：輸入手機號碼與密碼

若您暫時無法執行電腦腳本，您也可以在 Home Assistant 的設定介面直接輸入：
* **手機號碼**：支援台灣手機格式（例如 `0912345678` 或 `+886912345678`）
* **密碼**：您的安麗官方帳號密碼
* **國家/地區代碼**：預設為 `TW`

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

