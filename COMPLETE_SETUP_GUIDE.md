# Visual Scenario Builder - 完全セットアップガイド

AndroidアプリのテストシナリオをビジュアルGUIで構築・実行するフレームワークです。

## 📋 概要

このVisual Scenario Builderは以下を実現します：

✅ **ライブスクリーン表示** - 接続デバイスの画面をリアルタイムプレビュー  
✅ **UI要素の自動検出** - タップ可能な要素をハイライト表示  
✅ **インタラクティブ操作** - 画面クリックで操作を記録  
✅ **シナリオ自動生成** - YAML形式でエクスポート  
✅ **Slack連携** - 認証コード等を人間に確認させる  
✅ **複数アプリ対応** - アプリ間の切り替え処理をサポート

## 🏗️ システムアーキテクチャ

```
┌────────────────────────────────────────────────────────────┐
│                  Web ブラウザ (Port 3000)                   │
│                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Device Panel │  │ Live Preview │  │  Scenario    │   │
│  │  (選択)      │  │  (画面表示)  │  │  Editor      │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │        React.js フロントエンド                         │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬─────────────────────────────────┘
                         │ HTTP/WebSocket
┌────────────────────────────────────────────────────────────┐
│              FastAPI バックエンド (Port 8000)              │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  • Device Manager (adb制御)                          │  │
│  │  • Screen Capture (screencap)                        │  │
│  │  • UI Analysis (XML パース)                          │  │
│  │  • Tap Simulator (タップ実行)                        │  │
│  │  • YAML Generator (シナリオ生成)                     │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬─────────────────────────────────┘
                         │ adb shell
┌────────────────────────────────────────────────────────────┐
│           Android デバイス (USB接続 or 無線)              │
│                                                            │
│  • screencap (画面キャプチャ)                              │
│  • uiautomator dump (UI階層解析)                          │
│  • input tap/text/swipe (タップ/入力/ジェスチャー)        │
└────────────────────────────────────────────────────────────┘
```

## 📁 完全なファイル一覧

```
visual-scenario-builder/
│
├── 【バックエンド】
├── backend.py                    ★ FastAPI メインサーバー
├── backend_requirements.txt       ★ Python依存パッケージ
├── Dockerfile.backend            ★ バックエンド用Docker
│
├── 【フロントエンド】
├── frontend_package.json         → frontend/package.json
├── frontend_App.jsx              → frontend/src/App.jsx
├── frontend_App.css              → frontend/src/App.css
├── frontend_index.js             → frontend/src/index.js
├── frontend_index.html           → frontend/public/index.html
├── Dockerfile.frontend           → frontend/Dockerfile
│
├── 【Docker設定】
├── docker-compose-vsb.yml        ★ Docker Compose設定
│
├── 【テストフレームワーク】
├── test_framework_main.py        ★ 実行エンジン
├── test_utils.py                 ★ ユーティリティ
├── requirements.txt              ★ テスト用依存パッケージ
│
├── 【ドキュメント】
├── VSB_README.md                 ★ 概要・使い方
├── VSB_SETUP_GUIDE.md            ★ 詳細セットアップ
├── COMPLETE_SETUP_GUIDE.md       ★ このファイル
│
├── 【セットアップ】
├── setup.sh                      ★ 自動セットアップスクリプト
├── .env.example                  環境変数テンプレート
│
├── 【出力ディレクトリ】
├── scenarios/                    生成されるYAMLシナリオ
├── logs/                         テスト実行ログ
└── frontend/                     フロントエンドディレクトリ
    ├── src/
    ├── public/
    └── package.json
```

## 🚀 インストール・セットアップ

### 方法 1: 自動セットアップスクリプト（推奨）

```bash
# リポジトリ取得
cd visual-scenario-builder

# セットアップスクリプト実行
chmod +x setup.sh
./setup.sh
```

このスクリプトが自動的に以下を行います：
- 前提条件チェック
- ディレクトリ構造作成
- ファイル配置
- Docker イメージビルド
- コンテナ起動
- ブラウザ自動オープン

### 方法 2: 手動セットアップ

#### 前提条件

```bash
# インストール確認
docker --version
docker-compose --version
adb version

# デバイス接続
adb devices
```

#### 手順

**1. ディレクトリ構造作成**
```bash
mkdir -p frontend/{src,public}
mkdir -p scenarios logs
```

**2. フロントエンドファイルを配置**
```bash
# ファイルを対応するディレクトリにコピー
cp frontend_package.json frontend/package.json
cp frontend_App.jsx frontend/src/App.jsx
cp frontend_App.css frontend/src/App.css
cp frontend_index.js frontend/src/index.js
cp frontend_index.html frontend/public/index.html
```

**3. Docker イメージをビルド**
```bash
docker-compose -f docker-compose-vsb.yml build
```

**4. コンテナを起動**
```bash
docker-compose -f docker-compose-vsb.yml up
```

**5. ブラウザで開く**
```
http://localhost:3000
```

## 🎮 実際の使い方

### シナリオ作成フロー

```
1. デバイス選択
   └─ 左パネル「デバイス」からデバイスをクリック
   └─ ライブスクリーンに画面が表示

2. 要素をクリック
   └─ ライブスクリーン内の要素をクリック
   └─ 要素がハイライト表示
   └─ Resource ID やテキストが表示

3. アクションを追加
   └─ 「アクション追加」パネルで操作内容を選択
   └─ 「+ アクション追加」をクリック

4. シナリオをビルド
   └─ 手順 2-3 を繰り返す

5. YAMLをエクスポート
   └─ シナリオ名を入力
   └─ 「📥 YAML エクスポート」をクリック
   └─ scenarios/ に YAML ファイルが保存

6. テストを実行
   └─ python test_framework_main.py --scenario scenarios/xxx.yaml
```

### 実例：ログイン認証テスト

```
【構築】
① デバイスを選択 → ログイン画面が表示
② "Email" フィールドをクリック
③ アクション: input → "test@example.com"
④ "Password" フィールドをクリック
⑤ アクション: input → "password123"
⑥ "ログイン" ボタンをクリック
⑦ アクション: click（自動選択）
⑧ アクション: wait → 3秒
⑨ 認証コード画面をスクリーンショット
⑩ シナリオ名：「Login Test」
⑪ YAML エクスポート

【実行】
$ python test_framework_main.py --scenario scenarios/login_test.yaml
```

## 📊 生成されるYAML

UI操作から自動生成されたYAMLの例：

```yaml
name: "Login Test"
variables: {}

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

## 🔄 テスト実行パイプライン

### ローカル実行

```bash
# YAML で実行
python test_framework_main.py --scenario scenarios/my_test.yaml

# ログで確認
tail -f logs/test_framework.log

# 結果確認
cat results/test_001_result.json | jq .
```

### CI/CD 統合

**GitHub Actions の例：**

```yaml
name: Android App Tests

on:
  schedule:
    - cron: '0 9 * * 1-5'  # 平日 9:00

jobs:
  build-scenarios:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker image
        run: docker-compose -f docker-compose-vsb.yml build
      
      - name: Run test scenarios
        run: |
          docker-compose -f docker-compose-vsb.yml up -d
          sleep 10
          python test_framework_main.py --scenario scenarios/*.yaml
      
      - name: Upload results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results
          path: results/
```

## 🔧 トラブルシューティング

### デバイスが見つからない

```bash
# ADB デーモン再起動
adb kill-server
adb start-server

# 接続確認
adb devices -l

# USB デバッグを確認
adb shell "getprop ro.debuggable"
```

### 画面が表示されない

```bash
# バックエンドのログ確認
docker-compose -f docker-compose-vsb.yml logs backend

# WebSocket 接続確認
curl http://localhost:8000/health

# screencap テスト
adb shell screencap -p > /dev/null && echo "OK"
```

### UI要素が検出されない

```bash
# UI階層をダンプテスト
adb shell uiautomator dump /sdcard/dump.xml
adb pull /sdcard/dump.xml
cat dump.xml | head -50

# Resource ID を確認
grep resource-id dump.xml | head -10
```

### React アプリが起動しない

```bash
# フロントエンドのログ確認
docker-compose -f docker-compose-vsb.yml logs frontend

# npm キャッシュをクリア
cd frontend && npm ci --legacy-peer-deps

# 再起動
docker-compose -f docker-compose-vsb.yml restart frontend
```

## 📋 サポートするアクション完全リスト

| アクション | 説明 | パラメータ | 例 |
|----------|------|----------|-----|
| `click` | 要素をタップ | target (resourceId) | `target: "com.app:id/button"` |
| `input` | テキスト入力 | target, value | `value: "test@example.com"` |
| `wait` | 待機 | duration | `duration: 3` |
| `screenshot` | スクリーンショット | image_path | `image_path: "result.png"` |
| `swipe` | スワイプ | x1, y1, x2, y2 | 画面のスクロール |
| `switch_app` | アプリ切り替え | target | `target: "com.another.app"` |
| `human_input` | Slack で確認 | description, timeout | 認証コード確認 |

## 🌐 API リファレンス

### REST エンドポイント

```
GET  /api/devices              デバイス一覧取得
POST /api/devices/{s}/select   デバイス選択
GET  /api/screen               現在の画面取得
POST /api/tap                  画面をタップ
POST /api/input                テキスト入力
POST /api/swipe                スワイプ
GET  /api/elements             UI要素一覧
POST /api/scenario/save        シナリオ保存
```

### WebSocket

```
ws://localhost:8000/ws/screen  リアルタイム画面ストリーミング
```

## 📈 パフォーマンスチューニング

### 画面更新間隔の調整

`backend.py` の WebSocket コード:
```python
await asyncio.sleep(1)  # 1秒ごとに更新
```

を変更して最適化可能。

### UI要素検出の最適化

不要なノード層を除外することで高速化。

## 📚 参考リンク

- [FastAPI ドキュメント](https://fastapi.tiangolo.com/)
- [React ドキュメント](https://ja.react.dev/)
- [UIAutomator 公式ドキュメント](https://developer.android.com/training/testing/ui-automator)
- [adb シェルコマンド](https://developer.android.com/studio/command-line/adb?hl=ja)

## ✅ チェックリスト

セットアップ時：
- [ ] Docker & Docker Compose インストール
- [ ] adb インストール＆PATH設定
- [ ] Android デバイス USB接続
- [ ] USB デバッグ有効化
- [ ] `setup.sh` 実行 または 手動セットアップ

初回使用時：
- [ ] `http://localhost:3000` にアクセス
- [ ] デバイスが「デバイス」パネルに表示される
- [ ] 「ライブスクリーン」に画面が表示される
- [ ] 要素をクリックしてハイライトされる

シナリオ作成時：
- [ ] 各操作を順番に実行
- [ ] シナリオ名を入力
- [ ] YAML をエクスポート
- [ ] scenarios/ に YAML ファイルが生成される

テスト実行時：
- [ ] `test_framework_main.py` で実行
- [ ] ログを確認
- [ ] 結果をチェック

## 💬 サポート

### よくある質問

**Q: デバイスが複数ある場合は？**  
A: 「デバイス」パネルから選択するだけ。複数デバイス同時テストも対応予定。

**Q: Slack 連携が必要ない場合は？**  
A: 「human_input」アクション以外を使えば不要です。

**Q: カスタムアクションを追加できますか？**  
A: `backend.py` と `test_framework_main.py` を拡張して追加可能。

**Q: すでに YAML を持っていますが？**  
A: 直接 `test_framework_main.py` で実行可能。ビルダーは不要。

### コンタクト＆フィードバック

改善提案やバグ報告は Issue で。

---

**Happy Testing! 🚀**

