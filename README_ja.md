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

アムウェイ（Amway）の空気清浄機 **アトモスフィア スカイ (Atmosphere Sky)** および **アトモスフィア ミニ (Atmosphere Mini)** のための、公式仕様に準拠した Home Assistant カスタムインテグレーションです。公式 *Amway Healthy Home* アプリのクラウド通信プロトコルを解析して構築されており、**Apple HomeKit（ホームアプリ）の空気清浄機および空気質センサー** とのネイティブ連携に対応しています。

---

## ✨ 主な機能

- **🌀 包括的な空気清浄機・ファン制御 (`fan`)**:
  - **Atmosphere Sky**: 5段階の風量調節（20%, 40%, 60%, 80%, 100%）。
  - **Atmosphere Mini**: 3段階の風量調節（33%, 67%, 100%）。
  - **プリセットモード (Preset Modes)**: `自動 (Auto)`、`夜間 (Night)`、`ターボ (Turbo)`（Sky のみ対応）。
  - **電源操作**: 高速な電源オン/オフおよびステータス同期。
- **🍃 Apple HomeKit 5段階 空気質センサー (`sensor`)**:
  - Apple HomeKit ネイティブの `AirQuality` 特性に完全対応：
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
- **🗂️ Apple Home「個別のタイルとして表示」対応**:
  - ホームアプリの **「個別のタイルとして表示 (Show as Separate Tiles)」** に対応し、清浄機本体の操作パネルと空気質センサーを2つの独立したタイルに分割可能。
  - Home Assistant 内でもクリーンで独立したエンティティとして提供され、自由なダッシュボード構築が可能です。

---

## 📱 Apple Home（ホームアプリ）個別タイル設定手順

Home Assistant の **HomeKit Bridge（ホームキットブリッジ）** を介して空気清浄機を同期した場合、デフォルトでは1つのアクセサリタイルにまとめられることがあります。以下の手順で2つの独立したタイルに分割できます：

1. iPhone、iPad、または Mac で **「ホーム (Home)」** アプリを開きます。
2. **「Atmosphere 空気清浄機」** タイルを長押し（またはクリック）します。
3. 右下の **「設定（歯車アイコン）」** をタップします。
4. **「個別のタイルとして表示 (Show as Separate Tiles)」** を選択します。
5. 完了です！ホームアプリ内で自動的に2つのタイルに分割されます：
   - **タイル 1**：空気清浄機の電源、風量スライダー、自動/夜間/ターボモード切替。
   - **タイル 2**：室内の空気質レベル（非常に良い/良い/普通/悪い）とインジケーター。
   それぞれのタイルを異なる部屋やお気に入りに個別に配置できます。

---

## 📦 インストール方法 (Installation)

### 方法 1: HACS カスタムリポジトリ経由（推奨）

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
3. ポップアップ画面にログインリンクが表示されます：
   - リンクをクリックして、ブラウザで公式のアムウェイログインページを開きます。
   - アムウェイアカウントでログインします。
   - ログイン後、ブラウザが以下のような URL にリダイレクトされます：
     ```text
     amwayhealthyhome://loginRedirect?code=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx&state=...
     ```
     *(ブラウザに「ページが見つかりません」または「アプリを開けません」と表示されますが、これは正常な動作です)*。
   - ブラウザのアドレスバーから **URL 全体**（または `code` の値）をコピーします。
   - Home Assistant の入力欄に貼り付けて **「送信」** をクリックします。
4. インテグレーションが自動的に認証を完了し、アカウントに登録されているすべての Atmosphere Sky および Mini デバイスを自動検出します！

---

## 📊 ダッシュボードカード設定例 (Lovelace)

### 1. 空気清浄機コントロールカード (Tile Card)
```yaml
type: tile
entity: fan.atmosphere_sky
name: リビング空気清浄機
features:
  - type: fan-speed
  - type: fan-preset-modes
    style: dropdown
    preset_modes:
      - auto
      - night
      - turbo
```

### 2. 空気質ゲージカード (Gauge Card)
```yaml
type: gauge
entity: sensor.atmosphere_sky_air_quality
name: 室内空気質
needle: true
segments:
  - from: 1
    color: "#4caf50"
    label: 非常に良い
  - from: 2
    color: "#8bc34a"
    label: 良い
  - from: 3
    color: "#ffc107"
    label: 普通
  - from: 4
    color: "#ff9800"
    label: やや悪い
  - from: 5
    color: "#f44336"
    label: 悪い
```

### 3. フィルター残量一覧カード (Entities Card)
```yaml
type: entities
title: フィルター残量
entities:
  - entity: sensor.atmosphere_sky_prefilter_life
    name: プレフィルター残量
  - entity: sensor.atmosphere_sky_hepa_life
    name: HEPA フィルター残量
  - entity: sensor.atmosphere_sky_carbon_life
    name: カーボン脱臭フィルター残量
```

---

## 🛠️ 技術仕様・アーキテクチャ

- **IoT Class**: `cloud_polling`（30秒間隔でクラウド Conex API より Device Shadow 状態をポーリング）。
- **リアルタイム制御**: 風量変更や電源操作は、AWS IoT Device Shadow へ AWS Signature Version 4 (SigV4) 署名付き REST API で `RemoteButton` コマンドを直接発行。発行後1秒以内に即時状態更新を行うことで、遅延のない操作性を実現。
- **認証**: Gluu OAuth2 IDP (`oxauth/restv1`) を採用。Refresh Token によるバックグラウンド自動更新を実装しており、再ログインの手間がありません。
- **対応地域**: グローバル Amway Healthy Home クラウド基盤（台湾地域アカウント実機にて検証済み、日本地域アカウントにも対応可能）。

---

## ⚠️ 免責事項 (Disclaimer)

本プロジェクトはコミュニティによる独立したオープンソース開発であり、アムウェイ社（Amway Corp.）とは一切関係ありません。記載されている商標および製品名は、各所有者に帰属します。
