# Visual Scenario Builder

Androidアプリの自動テストシナリオを**ビジュアルに**作成・実行するツール。

<p align="center">
  <strong>画面をクリック → アクション記録 → YAML生成 → 実行</strong>
</p>

## 🎯 主な特徴

### 📺 ライブスクリーンプレビュー
- 接続されたデバイスの画面をリアルタイム表示
- WebSocket でストリーミング更新
- UI要素を自動検出・ハイライト

### 🖱️ インタラクティブ操作
- クリック、テキスト入力、スワイプをGUIで実行
- 要素の Resource ID を自動取得
- 画面の変化をリアルタイムで確認

### 📝 シナリオビルダー
- GUI操作でシナリオを構築
- YAML形式でエクスポート
- テスト実行フレームワークと連携

### 🤝 人間のサポート
- 認証コードなどをSlackで通知
- ユーザー確認後に自動入力
- 複雑な認証フローに対応

## 🏗️ アーキテクチャ

```
┌─────────────────────────────────────────────────┐
│          Visual Scenario Builder                 │
├──────────────────┬──────────────────────────────┤
│                  │                              │
│  React Frontend  │     FastAPI Backend          │
│  (Port 3000)     │     (Port 8000)              │
│                  │                              │
│  • Device List   │  • ADB Control               │
│  • Live Preview  │  • Screen Capture            │
│  • Action Build  │  • UI Analysis               │
│  • Scenario Edit │  • Tap Simulator             │
│                  │  • YAML Generation           │
│                  │                              │
└──────────────────┴──────────────────────────────┘
           ↓              ↓              ↓
      Android Device   adb/screencap   XML Parser
```

## 🚀 クイックスタート

### 1. 前提条件

```bash
# デバイス接続確認
adb devices
```

### 2. Docker で実行

```bash
# ビルド
docker-compose -f docker-compose-vsb.yml build

# 起動
docker-compose -f docker-compose-vsb.yml up

# ブラウザを開く
open http://localhost:3000
```

### 3. ローカル実行（開発用）

**バックエンド:**
```bash
pip install -r backend_requirements.txt
python backend.py
```

**フロントエンド:**
```bash
cd frontend
npm install
npm start
```

## 📱 使い方（5分でマスター）

### ステップ1: デバイス選択
1. 左パネル「デバイス」から接続デバイスを選択
2. ライブスクリーンに画面が表示されます

### ステップ2: 要素をクリック
1. ライブスクリーン内の要素をクリック
2. 要素がハイライト、情報が表示されます

### ステップ3: アクション追加
1. 「アクション追加」パネルでタイプを選択
2. パラメータを入力（テキスト入力の場合）
3. 「+ アクション追加」ボタンをクリック

### ステップ4: エクスポート
1. シナリオ名を入力
2. 「📥 YAML エクスポート」をクリック
3. YAML ファイルが生成されます

### ステップ5: 実行
```bash
python test_framework_main.py --scenario scenarios/my_scenario.yaml
```

## 🎨 UI コンポーネント

### デバイス選択パネル
- デバイス一覧の表示
- リアルタイム更新
- 接続状態の可視化

### ライブスクリーンプレビュー
- 画面のストリーミング表示
- UI要素のハイライト
- 要素情報の表示

### アクションビルダー
- アクションタイプの選択
- パラメータ入力フォーム
- 要素選択の確認

### シナリオエディタ
- アクションリスト表示
- 編集・削除機能
- YAML エクスポート

## 🔧 サポートするアクション

| Type | 説明 | パラメータ |
|------|------|-----------|
| `click` | 要素をタップ | target (resourceId) |
| `input` | テキスト入力 | target, value |
| `wait` | 待機 | duration (秒) |
| `screenshot` | スクリーンショット | image_path |
| `swipe` | スワイプ操作 | x1, y1, x2, y2 |
| `switch_app` | アプリ切り替え | app_name |
| `human_input` | 人間入力待機 | description |

## 📋 生成されるYAMLの例

```yaml
name: "Login Flow"
variables:
  email: "test@example.com"
  password: "password123"

actions:
  - type: click
    target: com.example.app:id/email_field
  
  - type: input
    target: com.example.app:id/email_field
    value: test@example.com
  
  - type: click
    target: com.example.app:id/password_field
  
  - type: input
    target: com.example.app:id/password_field
    value: password123
  
  - type: click
    target: com.example.app:id/login_button
  
  - type: wait
    duration: 3
  
  - type: screenshot
    image_path: login_success.png
```

## 🌐 API エンドポイント

### REST API

```bash
# デバイス一覧取得
GET /api/devices

# デバイス選択
POST /api/devices/{serial}/select

# 画面取得
GET /api/screen

# 画面タップ
POST /api/tap?x=100&y=200

# テキスト入力
POST /api/input?text=hello

# スワイプ
POST /api/swipe?x1=100&y1=200&x2=300&y2=400

# UI要素取得
GET /api/elements

# シナリオ保存
POST /api/scenario/save
```

### WebSocket

```javascript
// リアルタイム画面ストリーミング
ws://localhost:8000/ws/screen
```

## 🐛 トラブルシューティング

### デバイスが表示されない

```bash
# ADB デーモン再起動
adb kill-server
adb start-server

# デバイス確認
adb devices
```

### 画面が更新されない

- ブラウザ開発者ツール（F12）で WebSocket 接続を確認
- バックエンドのログを確認: `docker-compose logs -f backend`
- デバイスのUSB デバッグを有効化

### 要素がハイライトされない

- UIAutomator ツールが機能しているか確認
- `adb shell uiautomator dump /sdcard/dump.xml` で XML 生成テスト

## 📁 ファイル構成

```
.
├── backend.py                    # FastAPI サーバー
├── backend_requirements.txt      # Python 依存
├── Dockerfile.backend            # バックエンド用コンテナ
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # メインコンポーネント
│   │   ├── App.css              # スタイル
│   │   └── index.js             # エントリーポイント
│   ├── package.json             # npm 設定
│   └── Dockerfile               # フロントエンド用コンテナ
│
├── docker-compose-vsb.yml       # Docker Compose 設定
├── VSB_SETUP_GUIDE.md           # 詳細ガイド
└── scenarios/                   # 生成されるYAMLシナリオ
```

## 🔌 統合可能なツール

### 既存フレームワークとの連携

```bash
# 作成したYAMLをテスト実行フレームワークで実行
python test_framework_main.py --scenario scenarios/my_test.yaml
```

### CI/CD パイプライン

```yaml
# GitHub Actions の例
- name: Build Test Scenarios
  run: docker-compose -f docker-compose-vsb.yml up

- name: Run Tests
  run: python test_framework_main.py --scenario scenarios/*.yaml
```

## 📈 次のステップ

- [x] GUI ビルダー実装
- [x] ライブプレビュー
- [x] YAML 生成
- [ ] テスト結果レポート生成
- [ ] パフォーマンス測定
- [ ] 複数シナリオ並行実行
- [ ] スクリーンショット比較

## 💡 活用例

### 例1: ログイン認証テスト
1. アプリ起動 → ログイン画面
2. Email を入力
3. Password を入力
4. ログインボタンクリック
5. 認証コード画像をキャプチャ
6. Slack で確認 → 入力
7. ホーム画面到達を確認

### 例2: 複数アプリ連携テスト
1. App A で登録処理
2. App B に切り替え
3. App B で同じ アカウントでログイン
4. データ同期を確認

### 例3: UI レグレッション テスト
1. 各画面をスクリーンショット
2. 前バージョンと比較
3. 差分を検出

## 📝 ライセンス

MIT License

## 🤝 貢献

改善提案・バグ報告は Issue から。

---

**Happy Test Automation! 🚀**

