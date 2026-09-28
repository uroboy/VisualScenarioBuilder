# Visual Scenario Builder - セットアップガイド

ビジュアルシナリオビルダーで、画面操作を記録しながらテストシナリオを作成できます。

## 🎯 機能概要

✨ **ライブプレビュー**
- 接続されたAndroidデバイスの画面をリアルタイムで表示
- WebSocketでストリーミング更新

✨ **インタラクティブ要素認識**
- UI要素を自動検出・ハイライト表示
- クリック可能な要素をビジュアルに操作

✨ **シナリオビルダー**
- 画面クリックで操作を記録
- テキスト入力、待機などのアクション追加
- YAMLファイルとしてエクスポート

✨ **リアルタイム実行**
- シナリオを即座にテスト実行
- 画面更新を動的に確認

## 📋 システム要件

- Docker & Docker Compose
- Android デバイス（USB接続 or adb接続）
- Chrome / Firefox など最新ブラウザ

## 🚀 クイックスタート

### 1. ディレクトリ構成

```
visual-scenario-builder/
├── backend.py                  # FastAPI サーバー
├── backend_requirements.txt    # Python依存
├── Dockerfile.backend          # バックエンド用コンテナ
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.js
│   │   └── index.css
│   ├── public/
│   │   └── index.html
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose-vsb.yml
└── scenarios/                  # 生成されたYAMLシナリオ
```

### 2. セットアップ

```bash
# リポジトリをクローン/ダウンロード
cd visual-scenario-builder

# デバイス接続確認
adb devices

# Docker イメージをビルド
docker-compose -f docker-compose-vsb.yml build

# コンテナを起動
docker-compose -f docker-compose-vsb.yml up
```

### 3. ブラウザで開く

```
http://localhost:3000
```

## 💡 使い方

### ステップ 1: デバイスを選択

1. **デバイス リスト** パネルで接続デバイスを表示
2. 左側の「⟳ 更新」ボタンでデバイス一覧を更新
3. デバイスをクリックして選択
4. **ライブスクリーン** に画面が表示されます

### ステップ 2: 要素をクリックして操作を記録

1. **ライブスクリーン** 内の要素をクリック
2. クリックした要素がハイライト表示される
3. 要素情報（Resource ID、テキストなど）が下に表示

### ステップ 3: アクションを追加

**アクション追加** パネル:

- **アクションタイプを選択**
  - `click` - 要素をクリック
  - `input` - テキスト入力
  - `wait` - 秒単位で待機
  - `screenshot` - スクリーンショット取得
  - `swipe` - スワイプジェスチャー
  - `switch_app` - 別アプリに切り替え
  - `human_input` - Slack経由の人間入力

- **パラメータ入力**（アクションタイプによって変わる）
  - `input`: 入力するテキスト
  - `wait`: 待機秒数

- **「+ アクション追加」をクリック**

### ステップ 4: シナリオをエクスポート

**シナリオ** パネル:

1. シナリオ名を入力（例：`Login Test`）
2. アクション一覧を確認
3. **「📥 YAML エクスポート」** をクリック
4. YAML ファイルが `scenarios/` に保存されます

### ステップ 5: シナリオを実行

エクスポートしたYAMLファイルは、以下のコマンドで実行できます：

```bash
python test_framework_main.py --scenario scenarios/login_test.yaml
```

## 🎮 インタラクティブ操作ガイド

### 画面内での操作

| 操作 | 動作 |
|------|------|
| **クリック** | 要素をクリック＆選択 |
| **ダブルクリック** | テキスト入力モード開始 |
| **ドラッグ** | スワイプ操作（実装予定） |

### UI要素の情報表示

クリックした要素の情報が表示されます：

```
Resource ID: com.example.app:id/login_button
Text: ログイン
Class: android.widget.Button
Clickable: Yes
Bounds: (100, 200) - (300, 250)
```

## 🔧 高度な使い方

### 条件付きアクション（Slack経由）

```
1. 認証画像が表示される画面をスクリーンショット
2. アクションタイプで「human_input」を選択
3. Slack に画像を通知
4. ユーザーがスレッドで回答
5. 回答をアプリに自動入力
```

### 複数アプリの連携

```
1. App1 で操作完了
2. アクションで「switch_app」を選択
3. App2 の名前を指定
4. App2 で新しい操作を続ける
```

### テキスト入力の自動化

```yaml
# エクスポートされたYAML
actions:
  - type: input
    target: com.example.app:id/email_field
    value: test@example.com
  
  - type: input
    target: com.example.app:id/password_field
    value: password123
```

## 📱 デバイス接続のトラブルシューティング

### デバイスが表示されない

```bash
# ADB デーモン再起動
adb kill-server
adb start-server

# デバイス再接続
adb devices

# デバイス情報確認
adb devices -l
```

### USB接続トラブル

```bash
# USB デバイス一覧を確認（Linux）
lsusb

# デバイス認可確認（Android）
adb shell "getprop ro.secure"

# デバッグモード有効確認
adb shell "getprop ro.debuggable"
```

### 画面キャプチャエラー

```bash
# screencap テスト
adb shell screencap -p > /dev/null

# UI ダンプテスト
adb shell uiautomator dump /sdcard/dump.xml
```

## 🐛 デバッグモード

バックエンドログの確認：

```bash
# Docker コンテナのログを表示
docker-compose -f docker-compose-vsb.yml logs -f backend

# フロントエンドログ
docker-compose -f docker-compose-vsb.yml logs -f frontend
```

ブラウザの開発者ツール：
- F12 キーで開く
- **Console** タブでAPI エラーを確認
- **Network** タブでリクエスト/レスポンスを確認

## 📊 生成されたYAMLの例

```yaml
name: "Login Test"
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

## 🔄 ワークフロー例

### 例1：ログイン認証テスト

```
1. アプリを起動 → ログイン画面に到達
2. メールフィールドをクリック
3. メールアドレスを入力
4. パスワードフィールドをクリック
5. パスワードを入力
6. ログインボタンをクリック
7. 認証コード画像をスクリーンショット
8. 「human_input」で Slack 通知
9. ユーザーが確認コードを入力
10. 結果をスクリーンショット
11. YAML エクスポート
```

### 例2：複数アプリ連携

```
1. App1 で登録処理完了
2. App2 に切り替え
3. App2 で同じアカウントでログイン
4. データ同期を確認
5. YAML エクスポート
```

## 📈 次のステップ

- [ ] CI/CD パイプラインへの統合
- [ ] テスト結果の可視化
- [ ] 複数シナリオの並行実行
- [ ] パフォーマンス測定
- [ ] スクリーンショット比較

## 💬 サポート

問題が発生した場合：

1. **ログを確認**
   ```bash
   docker-compose -f docker-compose-vsb.yml logs
   ```

2. **デバイス接続を確認**
   ```bash
   adb devices
   ```

3. **ブラウザのコンソールを確認**
   - F12 > Console タブ

4. **API 接続テスト**
   ```bash
   curl http://localhost:8000/health
   ```

---

楽しいテスト自動化を！
