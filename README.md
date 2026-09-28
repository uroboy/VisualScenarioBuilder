# Multi-App Test Framework with Slack Integration

複数のAndroidアプリを自動で操作し、認証コードなどの確認が必要な場面でSlackを通じて人間のサポートを受けながらテストを進めるフレームワークです。

## 🎯 概要

このフレームワークでできること：

✅ **複数アプリの自動制御**
- UIAutomator2による要素の特定・操作
- アプリ間の切り替え

✅ **人間のサポートが必要な場面への対応**
- 画像認証・SMS確認などをSlackで通知
- スレッド内で入力内容を受け取り自動入力

✅ **完全に再利用可能な設計**
- YAML定義でシナリオを記述
- Pythonコードでも動的に構築可能
- Docker環境で一貫性を確保

✅ **詳細なログと結果管理**
- 全操作をログに記録
- テスト結果をJSON形式で保存
- スクリーンショットを自動キャプチャ

## 📁 ディレクトリ構成

```
test-framework/
├── test_framework_main.py          # メインフレームワーク
├── test_utils.py                   # ユーティリティ関数
├── test_scenario_example.yaml      # シナリオ定義例
├── Dockerfile                      # コンテナ定義
├── docker-compose.yml              # 環境構成
├── requirements.txt                # Python依存パッケージ
├── entrypoint.sh                   # Docker エントリーポイント
├── SETUP_GUIDE.md                  # 詳細セットアップガイド
├── .env.example                    # 環境変数テンプレート
│
├── scenarios/                      # テストシナリオディレクトリ
│   ├── auth_flow.yaml
│   ├── multi_app_flow.yaml
│   └── edge_cases.yaml
│
├── logs/                           # テスト実行ログ
├── screenshots/                    # キャプチャ画像
└── results/                        # テスト結果JSON

```

## 🚀 クイックスタート

### 1. 環境設定

```bash
# リポジトリをクローン/ダウンロード
cd test-framework

# 環境変数設定ファイルを作成
cp .env.example .env

# .env を編集してSlack Tokenを設定
# SLACK_BOT_TOKEN=xoxb-...
nano .env
```

### 2. Slack Bot 設定（初回のみ）

詳細は [SETUP_GUIDE.md](./SETUP_GUIDE.md) の「Slack Bot 設定」参照

### 3. Docker で実行

```bash
# ビルド
docker-compose build

# テスト実行
docker-compose run test-framework

# バックグラウンド実行
docker-compose up -d
```

### 4. ローカル実行（Docker なし）

```bash
# 依存パッケージインストール
pip install -r requirements.txt

# ADB デバイス接続確認
adb devices

# 環境変数設定
export SLACK_BOT_TOKEN="xoxb-..."
export SLACK_CHANNEL="#test-automation"

# テスト実行
python test_framework_main.py
```

## 📝 テストシナリオの定義

### 基本的なYAML形式

```yaml
name: "My Test Scenario"
description: "テストの説明"

variables:
  email: "test@example.com"
  password: "password123"

actions:
  - type: "switch_app"
    target: "app1"
  
  - type: "wait"
    duration: 2
  
  - type: "input"
    target: "com.example.app:id/email_field"
    value: "${email}"
  
  - type: "click"
    target: "com.example.app:id/login_button"
    critical: true
  
  - type: "wait"
    duration: 3
  
  # 画像をSlackで通知して人間入力を待つ
  - type: "human_input"
    slack_channel: "#test-automation"
    target: "com.example.app:id/auth_code_field"
    description: "メールに送信されたコードを入力してください"
    timeout: 600  # 10分
  
  - type: "click"
    target: "com.example.app:id/verify_button"
    critical: true
  
  - type: "screenshot"
    image_path: "final_result.png"
```

### Pythonコードでシナリオを構築

```python
from test_utils import ScenarioBuilder

scenario = (ScenarioBuilder("My Scenario")
    .add_variable('email', 'test@example.com')
    .add_switch_app('app1')
    .add_wait(2)
    .add_input('com.example.app:id/email', '${email}')
    .add_click('com.example.app:id/login_button', critical=True)
    .add_human_input(
        slack_channel='#test-automation',
        target='com.example.app:id/code_field',
        description='確認コードを入力'
    )
    .add_screenshot('result.png')
)

# YAML として保存
scenario.save('my_scenario.yaml')

# または Pythonコードで直接実行
# ...実装中...
```

## 🔧 アクションタイプ

| Type | 説明 | 例 |
|------|------|-----|
| `click` | 要素をクリック | `target: "com.app:id/button"` |
| `input` | テキスト入力 | `target: "...", value: "text"` |
| `screenshot` | スクリーンショット取得 | `image_path: "screen.png"` |
| `wait` | 待機 | `duration: 2` |
| `switch_app` | アプリ切り替え | `target: "app1"` |
| `human_input` | 人間入力を待つ | `slack_channel: "..."` |
| `notify` | Slack 通知 | `slack_channel: "..."` |

## 💡 実装例

### 例1: SMS 認証フロー

```yaml
name: "SMS Authentication"

variables:
  phone: "+81-90-1234-5678"

actions:
  - type: "input"
    target: "com.app:id/phone_field"
    value: "${phone}"
  
  - type: "click"
    target: "com.app:id/send_sms_button"
  
  - type: "wait"
    duration: 2
  
  # SMS コードを人間が入力
  - type: "human_input"
    slack_channel: "#test-automation"
    target: "com.app:id/sms_code_field"
    description: "SMSで送信されたコードをスレッドに入力してください"
    timeout: 300
  
  - type: "click"
    target: "com.app:id/verify_button"
```

### 例2: 複数アプリ連携

```yaml
name: "Multi-App Integration"

actions:
  # App1 でログイン
  - type: "switch_app"
    target: "app1"
  
  - type: "input"
    target: "com.app1:id/username"
    value: "user@example.com"
  
  - type: "click"
    target: "com.app1:id/login_button"
    critical: true
  
  - type: "wait"
    duration: 3
  
  # App2 に切り替えて処理
  - type: "switch_app"
    target: "app2"
  
  - type: "screenshot"
    image_path: "app2_result.png"
  
  - type: "click"
    target: "com.app2:id/process_button"
  
  - type: "screenshot"
    image_path: "final_result.png"
```

## 📊 テスト結果

テスト実行後、以下が自動保存されます：

```bash
logs/
├── test_framework.log          # 実行ログ

screenshots/
├── screen_<timestamp>.png      # キャプチャ画像
└── ...

results/
├── test_001_result.json        # テスト結果
└── summary_report.json         # サマリー
```

### 結果JSON形式

```json
{
  "session_id": "test_001",
  "scenario_name": "SMS Authentication",
  "passed": true,
  "execution_time": 45.2,
  "timestamp": "2024-12-01T09:30:45",
  "context": {
    "captured_values": {
      "phone_field": "+81-90-1234-5678",
      "sms_code_field": "123456"
    }
  },
  "error": null
}
```

## 🐛 デバッグ

### ログの確認

```bash
# リアルタイムログ表示
tail -f logs/test_framework.log

# エラーのみ抽出
grep ERROR logs/test_framework.log
```

### UIAutomator デバッグ

```bash
# デバイスのUI階層をダンプ
adb shell uiautomator dump /sdcard/dump.xml

# 取得したファイルを確認
adb pull /sdcard/dump.xml

# 要素IDを検索
grep resource-id dump.xml | head -20
```

### デバイス接続確認

```bash
# 接続デバイス一覧
adb devices

# デバイス情報確認
adb shell getprop

# 現在のActivity確認
adb shell dumpsys window | grep mCurrentFocus
```

## 🔄 CI/CD 統合

GitHub Actions での実行例：

```yaml
name: Automated Tests
on:
  schedule:
    - cron: '0 9 * * 1-5'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        env:
          SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
        run: docker-compose up --build
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: results/
```

## 📚 さらに詳しく

- [詳細セットアップガイド](./SETUP_GUIDE.md) - Slackの設定方法、トラブルシューティング
- [test_framework_main.py](./test_framework_main.py) - フレームワークの全実装
- [test_utils.py](./test_utils.py) - ユーティリティと拡張機能

## ⚙️ カスタマイズ

### 新しいアクションタイプを追加

```python
# test_framework_main.py の TestExecutionEngine._execute_action() に追加

elif action.action_type == ActionType.CUSTOM_ACTION:
    # カスタム実装
    return await self._handle_custom_action(action)

async def _handle_custom_action(self, action: TestAction) -> bool:
    # 実装
    pass
```

### 外部ツールとの連携

```python
# Gmail, Microsoft Teams など他のサービスとも連携可能
# SlackIntegration と同じ形式で実装
```

## 📋 チェックリスト

セットアップ時：
- [ ] Slack Bot を作成
- [ ] Bot Token を `.env` に設定
- [ ] デバイスを USB 接続
- [ ] `adb devices` で認識確認
- [ ] Docker をインストール
- [ ] `docker-compose build` でビルド

テスト実行時：
- [ ] シナリオファイル（YAML）を準備
- [ ] テスト対象アプリをインストール
- [ ] resourceId を確認（UIAutomator Viewer）
- [ ] `docker-compose run test-framework`

## 🤝 貢献

改善提案やバグ報告はお気軽に。

## 📄 ライセンス

MIT License

---

**サポート**

質問や問題がある場合：
1. ログ（`logs/test_framework.log`）を確認
2. [SETUP_GUIDE.md](./SETUP_GUIDE.md) のトラブルシューティング参照
3. デバイスが正しく接続されているか確認（`adb devices`）
