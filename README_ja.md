# Amway Atmosphere for Home Assistant & Apple HomeKit (日本語)

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

アムウェイ（Amway）の空気清浄機 **アトモスフィア スカイ (Atmosphere Sky)** および **アトモスフィア ミニ (Atmosphere Mini)** のための、公式仕様に準拠した Home Assistant カスタムインテグレーションです。公式 *Amway Healthy Home* アプリのクラウド通信プロトコルを解析して構築されており、**AWS IoT Device Shadow 双方向リアルタイム制御** および **Apple HomeKit（ホームアプリ）ネイティブ空気清浄機・5段階空気質連携** に対応しています。

---

> 🚀 **リリースノート (Release v1.0.0 - 正式リリース版)**  
> 本バージョンは最初の公式安定版（General Availability）であり、実機テストおよび38項目の自動ユニットテストに完全合格しています：
> - 携帯電話番号とパスワードによる直接ログインに対応。バックグラウンドで Gluu PKCE 認証およびトークン自動更新を行います。
> - Atmosphere Sky（5段階風量、3層フィルター、ターボモード）および Atmosphere Mini（3段階風量、2-in-1 フィルター）に完全対応。
> - 空気清浄機本体（Fan エンティティ）にプリセットモード（自動、夜間、ターボ）を統合し、不要なスイッチを自動クリーンアップ。
> - デバイスの実機シリアル番号およびファームウェアバージョンを Apple HomeKit のアクセサリ情報へ自動同期。
> - 詳細なセットアップ手順については 👉 [**セットアップ・HomeKit ガイド**](docs/setup-guide_ja.md) をご参照ください。

---

## ✨ 主な機能

- **🌀 ネイティブ空気清浄機・ファン制御 (`fan`)**:
  - **Atmosphere Sky**: 5段階の風量調節（20%, 40%, 60%, 80%, 100%）。
  - **Atmosphere Mini**: 3段階の風量調節（33%, 67%, 100%）。
  - **内蔵プリセットモード (Preset Modes)**: `自動 (Auto)`、`夜間 (Night)`、`ターボ (Turbo)`（Sky のみ）。
  - **即時クラウド制御**: AWS IoT REST API (SigV4 署名) を介して Device Shadow へ直接コマンド送信し、1秒以内に状態を同期。
- **🍃 Apple HomeKit 5段階 空気質センサー (`sensor`)**:
  - Apple HomeKit ネイティブの `AirQuality` 特性に完全対応（ホームアプリの部屋上部アイコンに表示）：
    - `1`: 非常に良い (Excellent)
    - `2`: 良い (Good)
    - `3`: 普通 (Fair)
    - `4`: やや悪い (Inferior)
    - `5`: 悪い (Poor)
  - 数値型 **クリーンエア供給値 (Clean Air Value)** センサー (`cleanAirVal`)。
- **🛡️ フィルター寿命トラッキング (`sensor`)**:
  - プレフィルター残量 (`0–100%`)
  - HEPA フィルター残量 (`0–100%`)
  - カーボン脱臭フィルター残量 (`0–100%`、Sky のみ)
- **📱 Apple Home 実機シリアル番号同期**:
  - アムウェイ本体の実機シリアル番号およびファームウェア/ハードウェアバージョンを Apple HomeKit のアクセサリ情報へ正確に反映。
- **🗂️ Apple Home「個別のタイルとして表示」対応**:
  - ホームアプリ内で清浄機操作パネルと空気質センサーを2つの独立したタイルに分割可能。

---

## 📦 インストール方法 (Installation)

### 方法 1: HACS カスタムリポジトリ経由（推奨）

> 💡 **HACS が未インストールの場合は？** 公式ドキュメント 👉 [**HACS 公式導入・利用マニュアル**](https://www.hacs.xyz/docs/use) を参照して事前に HACS をセットアップするか、下記 **方法 2** の手動インストール（HACS 不要）をご利用ください。

1. Home Assistant のサイドバーから **HACS** を開きます。
2. 右上のメニューアイコン（縦の3点 `...`）$\rightarrow$ **「カスタムレポジトリ (Custom repositories)」** をクリックします。
3. リポジトリ URL に以下を入力します：
   ```text
   https://github.com/zpqnzpqn/Amway_ATMOSPHERE
   ```
4. カテゴリに **「Integration (インテグレーション)」** を選択し、**「追加 (Add)」** をクリックします。
5. リストから **「Amway Atmosphere」** を検索し、**「ダウンロード」** を選択します。
6. **Home Assistant を再起動** します。

### 方法 2: 手動インストール

1. [Releases](https://github.com/zpqnzpqn/Amway_ATMOSPHERE/releases) ページから最新リリースのソースコードをダウンロードします。
2. `custom_components/amway_atmosphere` ディレクトリを Home Assistant の設定ディレクトリにコピーします：
   ```text
   config/custom_components/amway_atmosphere/
   ```
3. **Home Assistant を再起動** します。

---

## ⚙️ 設定手順 (Configuration)

1. Home Assistant で **「設定」 $\rightarrow$ 「デバイスとサービス」 $\rightarrow$ 「統合を追加」** を開きます。
2. **「Amway Atmosphere」** を検索して選択します。
3. 認証方法を選択します：
   - **方法 A：電話番号とパスワードによる直接ログイン（推奨）**：
     登録済みの電話番号（例：`090xxxxxxxx` や `+8869xxxxxxxx`）とパスワードを入力します。自動的にトークンが取得され、期限切れ時もバックグラウンドで自動更新されます。
   - **方法 B：Access Token の直接入力**：
     パスワード保存を避けたい場合は、付属ツール `python3 tools/get_token.py --proxy` でトークンを取得して貼り付けます。
4. 設定完了後、すべてのアトモスフィアデバイスおよびセンサーが自動的に登録されます！

---

## 🍏 Apple HomeKit 設定例 (configuration.yaml)

Apple「ホーム」アプリで空気清浄機として最大限に活用する場合（部屋上部の「空気質：良好」アイコン表示、フィルター寿命警告、Auto/Night/Turbo プリセット連動）、専用の HomeKit ブリッジを設定することをお勧めします（`configuration.yaml` または `packages/amway_atmosphere.yaml`）：

```yaml
# ==============================================================================
# Amway Atmosphere Sky - HomeKit & Template Sensors Package
# ==============================================================================

template:
  # 1. 3層フィルター（プレ、HEPA、カーボン）の最低残量を算出するテンプレート
  - sensor:
      - name: "Atmosphere Sky フィルター最低寿命"
        unique_id: atmosphere_sky_lowest_filter_life
        unit_of_measurement: "%"
        state: >
          {{ [
            states('sensor.atmosphere_sky_hepa_filter_life') | int(100),
            states('sensor.atmosphere_sky_carbon_filter_life') | int(100),
            states('sensor.atmosphere_sky_pre_filter_life') | int(100)
          ] | min }}

  # 2. Apple HomeKit 用 PM2.5 数値センサーへのマッピング (µg/m³)
  # 備考：HomeKit の「空気質」円形アイコンは数値の PM2.5 濃度を必要とします
  - sensor:
      - name: "Atmosphere Sky PM2.5"
        unique_id: atmosphere_sky_pm25
        device_class: pm25
        state_class: measurement
        unit_of_measurement: "µg/m³"
        state: >
          {% set level = state_attr('sensor.atmosphere_sky_air_quality', 'dust_level') | int(2) %}
          {% if level == 1 %}5
          {% elif level == 2 %}18
          {% elif level == 3 %}45
          {% elif level == 4 %}80
          {% elif level == 5 %}150
          {% else %}18
          {% endif %}

# 3. 独立した Apple HomeKit ブリッジ
# 備考：デフォルト（21064）と競合しないよう 21065 などのポートを指定します
homekit:
  - name: "Amway HomeKit Bridge"
    port: 21065
    mode: bridge
    filter:
      include_entities:
        - fan.atmosphere_sky
        - sensor.atmosphere_sky_pm2_5
    entity_config:
      fan.atmosphere_sky:
        type: air_purifier
        linked_filter_life_level_sensor: sensor.atmosphere_sky_lowest_filter_life
        linked_pm25_sensor: sensor.atmosphere_sky_pm2_5
```

> 💡 **注意事項とヒント**：
> 1. **エンティティ ID の置換**：ご使用の環境の実際のエンティティ名（例：`fan.<device_name>`）に適宜置き換えてください。テンプレート名にドット（`PM2.5`）が含まれる場合、Home Assistant はアンダースコア（`sensor.atmosphere_sky_pm2_5`）に変換します。
> 2. **空気質アイコンの表示**：Apple HomeKit で部屋の上部に「空気質：良好」アイコンを表示するには、数値型の `linked_pm25_sensor` の紐付けが必要です。
> 3. 5大センサーの HomeKit 対応状況および詳細解説については、👉 [**セットアップ・HomeKit ガイド**](docs/setup-guide_ja.md#-apple-homekit-設定ガイド-type-air_purifier) をご参照ください。

---

## 📊 ダッシュボード設定例 (Lovelace Dashboard)

以下の YAML を Home Assistant ダッシュボード（手動カードまたは垂直スタック）に貼り付けるだけで、清浄機本体の操作、空気質、および各フィルターの残量を一括監視できるダッシュボードが完成します：

```yaml
type: vertical-stack
cards:
  # 1. 空気清浄機メイン操作カード（プリセットモード・風量調整）
  - type: tile
    entity: fan.atmosphere_sky
    name: Atmosphere Sky
    icon: mdi:air-purifier
    features:
      - type: fan-preset-modes
        style: dropdown
        preset_modes:
          - Auto
          - Night
          - Turbo
      - type: fan-speed

  # 2. 空気質およびフィルター重要警告
  - type: horizontal-stack
    cards:
      # 空気質評価
      - type: tile
        entity: sensor.atmosphere_sky_air_quality
        name: 空気質
        icon: mdi:leaf

      # CADR クリーンエア供給値
      - type: tile
        entity: sensor.atmosphere_sky_clean_air_value
        name: 供給値 (CADR)
        icon: mdi:weather-windy

      # 最低フィルター残量（テンプレートセンサー連携）
      - type: gauge
        entity: sensor.atmosphere_sky_low_filter_life
        name: フィルター最低寿命
        min: 0
        max: 100
        needle: true
        segments:
          - from: 0
            color: "#f44336"
          - from: 20
            color: "#ff9800"
          - from: 50
            color: "#4caf50"

  # 3. 3層フィルター個別残量トラッキング
  - type: horizontal-stack
    cards:
      # プレフィルター (Pre-Filter)
      - type: gauge
        entity: sensor.atmosphere_sky_pre_filter_life
        name: プレフィルター
        min: 0
        max: 100
        needle: true
        segments:
          - from: 0
            color: "#f44336"
          - from: 20
            color: "#ff9800"
          - from: 50
            color: "#4caf50"

      # HEPA フィルター
      - type: gauge
        entity: sensor.atmosphere_sky_hepa_filter_life
        name: HEPA フィルター
        min: 0
        max: 100
        needle: true
        segments:
          - from: 0
            color: "#f44336"
          - from: 20
            color: "#ff9800"
          - from: 50
            color: "#4caf50"

      # カーボン脱臭フィルター (Carbon Filter)
      - type: gauge
        entity: sensor.atmosphere_sky_carbon_filter_life
        name: 活性炭フィルター
        min: 0
        max: 100
        needle: true
        segments:
          - from: 0
            color: "#f44336"
          - from: 20
            color: "#ff9800"
          - from: 50
            color: "#4caf50"
```

---

## 🛠️ 技術仕様・アーキテクチャ

- **IoT Class**: `cloud_polling`（30秒間隔でクラウド Conex API より Device Shadow 状態を同期）。
- **リアルタイム制御**: AWS IoT Device Shadow へ SigV4 署名付き REST API で `RemoteButton` コマンドを直接発行。発行後1秒以内に即時状態更新を行うことで、遅延のない操作性を実現。
- **認証**: Gluu OAuth2 IDP (`oxauth/restv1`) を採用。Refresh Token によるバックグラウンド自動更新を実装。
- **対応地域**: グローバル Amway Healthy Home クラウド基盤。

---

## ⚠️ 免責事項 (Disclaimer)

本プロジェクトはコミュニティによる独立したオープンソース開発であり、アムウェイ社（Amway Corp.）とは一切関係ありません。記載されている商標および製品名は、各所有者に帰属します。
