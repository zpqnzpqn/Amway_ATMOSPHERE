# アムウェイ アトモスフィア (Amway Atmosphere) Home Assistant 接続 & Apple HomeKit 設定ガイド

<p align="center">
  <a href="setup-guide_en.md"><b>English</b></a> |
  <a href="setup-guide.md"><b>繁體中文</b></a> |
  <a href="setup-guide_ja.md"><b>日本語</b></a>
</p>

> 🚀 **v1.0.0 正式リリース版 (General Availability)**  
> 本ガイドは、Home Assistant および Apple HomeKit ユーザー向けに、アムウェイ Atmosphere Sky / Mini 空気清浄機の連携、設定、自動化をスムーズに行うための完全マニュアルです。  
> 携帯電話番号とパスワードによる直接認証、AWS IoT Device Shadow によるリアルタイム双方向クラウド制御、Apple HomeKit ネイティブ空気清浄機＆5段階空気質センサー連携、実機シリアル番号同期など、充実した機能を備えています。

---

> 💡 **事前準備（インテグレーションのインストール）**：  
> 本インテグレーションをご利用いただくには、事前に Home Assistant へインストールする必要があります。HACS のカスタムリポジトリから追加して HA を再起動するか（HACS が未インストールの場合は 👉 [**HACS 公式導入・利用マニュアル**](https://www.hacs.xyz/docs/use) を参照してください）、GitHub よりソースコードを直接ダウンロードして `config/custom_components/amway_atmosphere/` に配置してください。

## 🚀 接続・ログイン方法

### 方法 1: 携帯電話番号とパスワードによる直接ログイン（推奨・ブラウザ不要）

本インテグレーションは、アムウェイ公式「Healthy Home」アプリの OAuth2 + PKCE 認証プロトコルを完全に実装しています。**認証用URLのクリックやブラウザ遷移、パケットキャプチャツールは一切不要**です。Home Assistant の設定画面から直接完了できます：

1. Home Assistant で **「設定」 $\rightarrow$ 「デバイスとサービス」 $\rightarrow$ 「統合を追加」** を開き、**Amway Atmosphere** を検索します。
2. 登録済みの **携帯電話番号**（例: `09012345678` や `+886912345678`）と **パスワード** を入力します。
3. 国コードを選択します（台湾: `TW`、日本登録の場合は該当の国コード）。
4. **「送信」** をクリックすると、バックグラウンドで安全にトークン交換が行われ、自動更新が有効になります。
5. 空気清浄機および各センサーが即座に Home Assistant に登録されます！

---

### 方法 2: Access Token の直接入力（パスワード非保持・高セキュリティ）

Home Assistant 内にパスワードを保存したくない場合は、付属のヘルパーツールを使用してトークンを取得し、直接入力することができます：

```bash
python3 tools/get_token.py --proxy
```
ターミナルの案内に従いスマートフォンアプリを操作すると、ツールが自動的にトークンを抽出・コピーします。設定ダイアログにそのまま貼り付けてください。

---

## 🍏 Apple HomeKit 設定ガイド (type: air_purifier)

本インテグレーションは Apple HomeKit の仕様に完全対応しており、アムウェイ空気清浄機を **ネイティブの空気清浄機 (Air Purifier)** アクセサリとして Apple「ホーム」アプリへブリッジできます：

### 1. 5大センサー HomeKit 対応評価一覧表

| センサー名 | サンプル値 | HomeKit ネイティブ対応 | HomeKit 種別 / 特性 | 表示効果および詳細説明 |
| :--- | :--- | :--- | :--- | :--- |
| **HEPA Filter Life** | 40% | ✅ ネイティブ対応 | `air_purifier` に従属する `FilterLifeLevel` 特性 | 清浄機本体に紐付けることで、ホームアプリの清浄機カード内に「フィルター残量：40%」と直接表示されます。寿命低下時には自動的に「フィルター交換の必要あり」というシステム通知が届きます。 |
| **Carbon Filter Life** | 13% | ⚠️ 選択または最小値算出 | 同上（HomeKit 仕様上、清浄機1台につきフィルター読取値は1つ） | HomeKit 規格では1台の空気清浄機につき `FilterLifeLevel` は1つのみ保持可能です。最も早く消費されるフィルター（例：カーボン脱臭 13%）を割り当てるか、HAのテンプレートで3層の最小値を算出することを推奨します。 |
| **Pre-Filter Life** | 58% | ⚠️ 選択または最小値算出 | 同上 | 同上。 |
| **PM2.5 / Air Quality** | 18 µg/m³ | ✅ ネイティブ対応 | `AirQualitySensor` (空気質センサー) | HomeKit は `linked_pm25_sensor` で数値型の PM2.5 濃度を紐付けることで5段階評価を判定します。ホームアプリ内の部屋上部に「空気質：良好」アイコンが表示されます。 |
| **Clean Air Value** | 795 | ❌ 非対応（型なし数値） | なし（Apple HomeKit に汎用数値/CADR用アクセサリ型は存在しません） | Apple HomeKit は型のない純粋な数値を許可していません。無理に温度や湿度、PM2.5として偽装すると単位や解析が著しく乱れます（例：795°C や 795% 表示）。**Home Assistant のダッシュボードでの確認に留め、HomeKit にはブリッジしないことを強く推奨します。** |

---

### 2. 🛠️ 推奨 HomeKit ブリッジ設定 (configuration.yaml / packages)

Apple「ホーム」アプリで最も美しく安定した表示を実現するため（部屋上部の「空気質：良好」アイコン表示、フィルター寿命警告、Auto/Night/Turbo プリセット連動）、専用の HomeKit ブリッジを設定することをお勧めします：

```yaml
homekit:
  - name: "Amway HomeKit Bridge"
    port: 21065
    mode: bridge
    filter:
      include_entities:
        - fan.atmosphere_sky
    entity_config:
      fan.atmosphere_sky:
        type: air_purifier
        linked_filter_life_level_sensor: sensor.atmosphere_sky_lowest_filter_life
        linked_pm25_sensor: sensor.atmosphere_sky_pm2_5
```

> 💡 **注意事項とエンティティ設定**：
> 1. **重複タイルの防止（重要）**：`filter.include_entities` には空気清浄機本体 `fan.atmosphere_sky` のみを指定してください。`sensor.atmosphere_sky_pm2_5` は `include_entities` に含めないでください。`linked_pm25_sensor` の設定により、PM2.5 サービスは清浄機アクセサリに直接統合され、ホームアプリの部屋上部に円形「空気質：良好」アイコンが表示されます。個別に登録すると重複したセンサーカードが生成されてしまいます。
> 2. **エンティティ名の置換**: お使いの環境の実際の `entity_id`（例: `fan.<device_name>`）に置き換えてください。テンプレート名にドット（`PM2.5`）が含まれる場合、Home Assistant はアンダースコア（`sensor.atmosphere_sky_pm2_5`）に変換します。

---

### 3. 💡 応用テクニック：3層フィルター「自動最小寿命」センサーの作成

Atmosphere Sky にはプレフィルター、HEPA、カーボン脱臭の3層フィルターが搭載されています。HA のテンプレートセンサーを使用して最も寿命の短い値を自動算出できます：

#### 設定方法 A: `configuration.yaml` に記述
```yaml
template:
  - sensor:
      - name: "Atmosphere Sky フィルター最低寿命"
        unique_id: atmosphere_sky_lowest_filter_life
        unit_of_measurement: "%"
        state: >
          {{ [
            states('sensor.atmosphere_sky_air_treatment_system_hepa_filter_life') | int(100),
            states('sensor.atmosphere_sky_air_treatment_system_carbon_filter_life') | int(100),
            states('sensor.atmosphere_sky_air_treatment_system_pre_filter_life') | int(100)
          ] | min }}
```

#### 設定方法 B: HA Web 管理画面から作成（YAML 編集不要）
1. **「設定」 $\rightarrow$ 「デバイスとサービス」 $\rightarrow$ 「ヘルパー」** を開きます。
2. **「+ ヘルパーを作成」 $\rightarrow$ 「テンプレート」 $\rightarrow$ 「センサーのテンプレート化」** を選択します。
3. 名前に `Atmosphere Sky フィルター最低寿命` と入力し、状態テンプレートに上記の Jinja 式を貼り付け、単位に `%` を設定します。

作成後、HomeKit 設定の `linked_filter_life_level_sensor` に `sensor.atmosphere_sky_lowest_filter_life` を指定します。いずれかのフィルターが残り少なくなった場合（例：活性炭フィルターが13%）、Apple ホームアプリが即座に警告と交換通知を発行します！

---

### 4. Apple Home 機能の特長と連携体験

* **ネイティブ空気清浄機アイコン**: 清浄機の回転アニメーション表示、電源ON/OFF、風量（パーセント）調整に対応。
* **プリセットモード内蔵**: `自動 (Auto)`、`夜間 (Night)`、`ターボ (Turbo)` モードを空気清浄機コントロール内に統合。余計なスイッチを別途作る必要がありません。
* **フィルター残量表示**: `linked_filter_life_level_sensor` との連携により、ホームアプリ内で残量確認および交換推奨通知が有効になります。
* **5段階空気質評価**: HomeKit 標準の空気質評価（非常に良い・良い・普通・やや悪い・悪い）として部屋上部にすっきりと表示。
* **実機シリアル番号とファームウェアの同期**: 本体の実機シリアル番号およびバージョン情報を HomeKit の `AccessoryInformation` に完全反映。Apple ホームアプリの「アクセサリの詳細」で Home Assistant と全く同一の実機情報が確認できます。*(更新前にペアリング済みの場合は、HAでHomeKitブリッジを再読み込みすることで同期されます)*
* **Siri 音声操作**:
  * *「Hey Siri、空気清浄機を自動モードにして」*
  * *「Hey Siri、空気清浄機の風量を60%にして」*

---

## ❓ よくある質問 (FAQ)

### Q1: 電話番号ログイン後、トークンが切れた場合はどうなりますか？
**バックグラウンドで完全自動更新されます！**  
本インテグレーションにはトークンの自動更新機能が組み込まれています。Access Token の有効期限が近づくと、裏で自動的に Refresh Token を使ってアムウェイの Gluu 認可サーバーから新しいトークンを取得します。一時的な通信エラー等が発生した場合でも、保存された資格情報を用いてサイレントに再認証が行われます。

### Q2: Access Token でのログインは安全ですか？
**非常に安全です！**  
Access Token によるログインの最大の利点は、**Home Assistant 内にアカウントのパスワードが一切保存されない**点です。Token はデバイスの制御・状態取得にのみ限定された権限を持ち、決済情報や個人情報へのアクセス権はありません。

### Q3: 対応している機種は何ですか？
* **Atmosphere Sky™ 空気清浄機**: 5段階風量調節、自動/夜間/ターボモード、プレ/HEPA/カーボン各フィルター寿命監視、粒子空気質指数に対応。
* **Atmosphere Mini™ 空気清浄機**: 3段階風量調節、自動/夜間モード、2-in-1 フィルター寿命監視に対応。
