# Multi-App Test Framework セットアップガイド

複数のAndroidアプリを連携させて自動テストを実行し、Slackで人間のサポートを受けながら進めるフレームワークです。

## 前提条件

- Docker / Docker Compose
- Android デバイス（実機またはエミュレータ）
- Slack ワークスペース＆ Bot Token
- Python 3.11+（ローカル実行の場合）

## セットアップ手順

### 1. Slack Bot 設定

Slack API コンソール (https://api.slack.com/apps) で新しいアプリを作成:

```
1. Create New App → From Scratch
2. App name: "Test Automation Bot"
3. Workspace を選択

4. OAuth & Permissions (左メニュー):
   - Scopes > Bot Token Scopes に以下を追加:
     - chat:write
     - files:write
     - channels:read
     - channels:manage
     - conversations.history:read

5. Install to Workspace
6. Bot User OAuth Token をコピー → SLACK_BOT_TOKEN
```

### 2. テスト用チャンネル作成

Slack で新しいチャンネルを作成: `#test-automation`

### 3. ローカルセットアップ（Docker）

```bash
# リポジトリクローン/ファイル配置
mkdir -p ~/test-framework && cd ~/test-framework
# 上記で作成したファイルを配置

# .env ファイル作成
cat > .env << EOF
SLACK_BOT_TOKEN=xoxb-your-token-here
SLACK_CHANNEL=#test-automation
DEVICE_ID=emulator-5554  # または実機のシリアル番号
EOF

# Docker Compose ファイル作成
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  test-framework:
    build: .
    environment:
      SLACK_BOT_TOKEN: ${SLACK_BOT_TOKEN}
      SLACK_CHANNEL: ${SLACK_CHANNEL}
      DEVICE_ID: ${DEVICE_ID}
      TEST_SCENARIO: test_scenario_example.yaml
    volumes:
      - /dev/bus/usb:/dev/bus/usb
      - ./test_scenario_example.yaml:/app/test_scenario_example.yaml
      - ./logs:/app/logs
      - ./screenshots:/app/screenshots
    network_mode: "host"
    privileged: true
EOF

# ビルド＆実行
docker-compose build
docker-compose run test-framework
```

### 4. ローカル実行（Python 直接実行）

```bash
# 依存パッケージインストール
pip install -r requirements.txt

# ADB デバイス接続確認
adb devices

# 環境変数設定
export SLACK_BOT_TOKEN="xoxb-your-token"
export SLACK_CHANNEL="#test-automation"

# テスト実行
python test_framework_main.py
```

## テストシナリオの定義

### YAML フォーマット

```yaml
name: "Test Name"
description: "Description"

variables:
  email: "test@example.com"
  password: "secret"

actions:
  - type: "switch_app"
    target: "app1"
    
  - type: "input"
    target: "com.example.app:id/field_id"
    value: "${email}"
    
  - type: "click"
    target: "com.example.app:id/button_id"
    
  - type: "human_input"
    slack_channel: "#test-automation"
    target: "com.example.app:id/auth_field"
    description: "Please enter the code sent to your email"
    timeout: 600
    
  - type: "screenshot"
    image_path: "result.png"
```

### アクションタイプ一覧

| Type | 説明 | パラメータ |
|------|------|-----------|
| `click` | 要素をクリック | `target` (resourceId or "text:...") |
| `input` | テキスト入力 | `target`, `value` |
| `screenshot` | スクリーンショット | `image_path` |
| `wait` | 待機 | `duration` (秒) |
| `switch_app` | アプリ切り替え | `target` (app1, app2 など) |
| `human_input` | 人間入力を待つ | `slack_channel`, `target`, `description`, `timeout` |
| `notify` | Slack通知 | `slack_channel`, `message` |

## 実装例：認証フロー

### シナリオ例 1: SMS コード認証

```yaml
name: "SMS Authentication"

variables:
  phone: "+81-90-xxxx-xxxx"

actions:
  - type: "input"
    target: "com.app:id/phone_field"
    value: "${phone}"
  
  - type: "click"
    target: "com.app:id/send_sms_button"
  
  - type: "wait"
    duration: 2
  
  - type: "human_input"
    slack_channel: "#test-automation"
    target: "com.app:id/sms_code_field"
    description: "SMS コードが送信されました。スレッドで入力してください"
    timeout: 300
  
  - type: "click"
    target: "com.app:id/verify_button"
```

### Python での拡張実装

```python
from test_framework_main import TestExecutionEngine, UIAutomationEngine, SlackIntegration

# カスタムテストクラス
class AuthenticationTest(TestExecutionEngine):
    async def extract_otp_from_email(self, email: str) -> str:
        """メールからOTP抽出（例）"""
        # メールクライアント連携、正規表現での抽出など
        pass
    
    async def validate_auth_result(self) -> bool:
        """認証成功を検証"""
        activity = self.ui.get_current_activity()
        return "authenticated" in activity.lower()
```

## デバッグ＆トラブルシューティング

### ADB デバイス未検出

```bash
# ADB デーモン再起動
adb kill-server
adb start-server

# デバイスの再認識
adb devices

# USB 接続確認（Linux）
lsusb
```

### Slack 通知が来ない

```bash
# Bot Token 確認
echo $SLACK_BOT_TOKEN

# チャンネル権限確認
# Slack App > OAuth & Permissions > Scopes を確認
```

### UIAutomator2 で要素が見つからない

```python
# デバッグモード: 現在のUI階層を出力
device.dump_hierarchy()

# スクリーンショットで要素を視認
device.screenshot('debug.png')

# resourceId の取得例
# adb shell uiautomator dump /sdcard/dump.xml
# cat /sdcard/dump.xml | grep -i "resource-id"
```

### タイムアウト設定

```yaml
- type: "human_input"
  slack_channel: "#test-automation"
  target: "com.app:id/field"
  description: "入力待機"
  timeout: 900  # 15分に延長
```

## ベストプラクティス

### 1. アクション間の待機を挿入

```yaml
- type: "click"
  target: "com.app:id/button"

- type: "wait"
  duration: 2  # 画面遷移待ち

- type: "screenshot"
  image_path: "next_screen.png"
```

### 2. Critical フラグで重要なステップをマーク

```yaml
- type: "click"
  target: "com.app:id/submit"
  critical: true  # ここで失敗したら即中止
```

### 3. エラーハンドリング

```python
# Python コードでの例
try:
    success = await executor.execute_scenario('scenario.yaml', 'session_001')
except Exception as e:
    logger.error(f"Test failed: {e}")
    # アラート送信、ログ保存など
```

### 4. ログとスクリーンショットの保存

```bash
# ディレクトリ構造
test-framework/
├── logs/                    # テスト実行ログ
├── screenshots/             # キャプチャ画像
├── scenarios/               # テストシナリオ YAML
│   ├── auth_flow.yaml
│   ├── multi_app_flow.yaml
│   └── edge_cases.yaml
└── results/                 # テスト結果
```

## CI/CD 統合（GitHub Actions 例）

```yaml
name: Automated App Testing

on:
  schedule:
    - cron: '0 9 * * 1-5'  # 平日 9:00 実行

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker
        uses: docker/setup-buildx-action@v2
      
      - name: Build and run tests
        env:
          SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
          SLACK_CHANNEL: ${{ secrets.SLACK_CHANNEL }}
        run: docker-compose up --build
      
      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: |
            logs/
            screenshots/
```

## トラブル対応

| 問題 | 原因 | 解決策 |
|------|------|--------|
| "Element not found" | resourceId が変更 | UI Automator Viewer で新しい ID を確認 |
| Slack 通知失敗 | Token 無効化 | Workspace 再認証 |
| デバイス切断 | USB ケーブル抜け | ケーブル再接続、`adb devices` で確認 |
| タイムアウト | ネットワーク遅延 | timeout 値を増加、待機を延長 |

## 次のステップ

- [x] 基本フレームワーク実装
- [ ] CI/CD パイプライン統合
- [ ] 詳細なレポート生成
- [ ] パフォーマンス測定
- [ ] 複数デバイス並行実行

---

質問や問題がある場合は、ログを確認してください:
```bash
tail -f test_framework.log
```
