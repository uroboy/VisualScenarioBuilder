# Visual Scenario Builder - リモートサーバ引き継ぎパッケージ

**生成日時**: 2026-09-28  
**セッション**: Android自動テストフレームワーク + Visual Scenario Builder サーバ実行対応版完成

---

## 📋 **このドキュメント について**

このファイルは、Claude エージェントが動作する開発用サーバへの **完全な引き継ぎガイド** です。
サーバ上で新しい Claude セッションを開いた際、このファイルを参考にしてセットアップが完了します。

---

## 🎯 **セッションの成果**

### **作成されたシステム**

#### **Part 1: マルチアプリテストフレームワーク**
- 外部Android アプリの自動テスト
- 複数アプリ連携操作対応
- Slack統合（画像認証コード通知・人間入力待機）
- 再利用可能な YAML ベースシナリオ定義

#### **Part 2: Visual Scenario Builder（ローカル版）**
- Web UI でシナリオ作成
- ライブ画面プレビュー（WebSocket）
- 要素認識・GUI操作記録
- YAML エクスポート

#### **Part 2 ビルド改修: サーバ実行対応版**
- Docker 化（バックエンド+フロントエンド）
- リモート adb 接続対応
- CORS 完備
- NGINX リバースプロキシ
- 自動セットアップスクリプト
- 詳細ドキュメント

---

## 📦 **引き継ぎファイル一覧**

### **🆕 新規作成ファイル（サーバ実行対応）**

```
【バックエンド】
✓ backend_server.py
  - FastAPI 実装
  - リモート adb 接続対応
  - CORS ミドルウェア
  - WebSocket ストリーミング
  - ヘルスチェック

【Docker 設定】
✓ docker-compose-server.yml
  - 0.0.0.0 バインディング（全インターフェース）
  - リモート adb サーバ接続対応
  - ボリュームマウント（scenarios, logs, results）
  - ネットワーク設定

✓ Dockerfile.backend.server
  - Python 3.11 slim ベース
  - adb, tesseract-ocr インストール
  - ヘルスチェック実装

✓ Dockerfile.frontend.server
  - Node 20 alpine でビルド
  - NGINX でサーブ
  - リバースプロキシ対応

✓ nginx.conf
  - API リバースプロキシ
  - WebSocket サポート
  - CORS ヘッダー設定

【環境設定】
✓ .env.server
  - API_HOST, API_PORT
  - REACT_APP_API_URL（ブラウザから API へアクセス）
  - ADB_HOST, ADB_PORT（デバイス接続）
  - ALLOWED_ORIGINS（CORS）
  - LOG_LEVEL

【セットアップ自動化】
✓ setup-server.sh
  - システム環境チェック
  - 依存パッケージ自動インストール
  - ディレクトリ作成
  - ファイアウォール設定
  - Docker ビルド・起動
  - ヘルスチェック

【ドキュメント】
✓ SERVER_SETUP_GUIDE.md
  - 詳細なセットアップ手順（全14セクション）
  - トラブルシューティング
  - 本番環境設定ガイド
  - バックアップ・復元手順

✓ QUICK_START_SERVER.md
  - 5分でセットアップ
  - ステップバイステップ
  - よく使うコマンド集

✓ HANDOVER_CHECKLIST.md
  - 引き継ぎ用チェックリスト
  - ファイル構成確認
  - セットアップ前後のチェック

✓ TRANSFER_PACKAGE.md
  - このファイル
  - 完全な引き継ぎガイド
```

### **既存ファイル（互換性保持）**

```
【Part 1: テストフレームワーク】
- test_framework_main.py
- test_utils.py
- test_scenario_example.yaml
- requirements.txt
- docker-compose.yml（ローカル用）
- Dockerfile（ローカル用）
- README.md, SETUP_GUIDE.md

【Part 2: React フロントエンド】
- frontend/src/App.jsx
- frontend/src/App.css
- frontend/src/index.js
- frontend/public/index.html
- frontend/package.json

【その他】
- backend_requirements.txt
```

---

## 🚀 **開発サーバへのデプロイ手順**

### **ステップ 1: ファイル転送**

**ローカルマシンから開発サーバへ：**

```bash
# 方法 A: scp で転送
scp -r /path/to/vsb user@dev-server:/home/user/vsb

# 方法 B: git で転送
git clone <repository-url> /home/user/vsb
cd /home/user/vsb

# 方法 C: このファイルから直接
# サーバで以下を実行して、下記ファイルをアップロード
```

### **ステップ 2: 自動セットアップ（推奨）**

**開発サーバ上で実行：**

```bash
cd /home/user/vsb

# セットアップスクリプトに実行権限を付与
chmod +x setup-server.sh

# 自動セットアップ開始
./setup-server.sh
```

**スクリプトが自動的に以下を実行します：**
- ✅ システム環境チェック（OS, 依存パッケージ）
- ✅ Docker, Docker Compose インストール
- ✅ ディレクトリ作成（scenarios, logs, results, frontend）
- ✅ 環境変数ファイル（.env）作成
- ✅ ファイアウォール設定
- ✅ Docker イメージビルド
- ✅ コンテナ起動
- ✅ ヘルスチェック

### **ステップ 3: 手動セットアップ（オプション）**

自動スクリプトが失敗した場合：

```bash
# イメージをビルド
docker-compose -f docker-compose-server.yml build

# コンテナを起動
docker-compose -f docker-compose-server.yml up -d

# 起動確認
docker-compose -f docker-compose-server.yml ps

# ログ確認
docker-compose -f docker-compose-server.yml logs backend
```

---

## ⚙️ **環境設定（重要）**

### **`.env` ファイルを編集**

```bash
cp .env.server .env
vi .env  # エディタで開く
```

### **設定項目：**

```env
# ===== API 設定 =====
# バックエンドがリッスンするホスト（0.0.0.0 = 全インターフェース）
API_HOST=0.0.0.0
API_PORT=8000

# フロントエンドから API へアクセスするURL
# ⚠️ サーバのIPアドレスに変更してください
REACT_APP_API_URL=http://192.168.1.100:8000/api

# ===== ADB 設定（Android デバイス接続） =====
# ローカル USB 接続の場合
ADB_HOST=localhost
ADB_PORT=5037

# WiFi 接続の場合
# ADB_HOST=192.168.1.50      # デバイスのIPアドレス
# ADB_PORT=5555

# リモート adb サーバの場合
# ADB_HOST=adb-server-ip
# ADB_PORT=5037

# ===== CORS 設定 =====
# 本番環境では * を使わず、明示的にオリジンを指定してください
ALLOWED_ORIGINS=*

# ===== ログレベル =====
LOG_LEVEL=INFO
# 選択肢: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

---

## 🌐 **アクセス方法**

セットアップ後、以下の URL でアクセス可能：

| 用途 | URL |
|------|-----|
| **フロントエンド** | `http://<server-ip>:3000` |
| **API ドキュメント** | `http://<server-ip>:8000/api/docs` |
| **ヘルスチェック** | `http://<server-ip>:8000/health` |

### **例:**

```
http://192.168.1.100:3000    # フロントエンド
http://192.168.1.100:8000/api/docs  # Swagger UI
```

---

## ✅ **セットアップ後のチェック**

セットアップが完了したら、以下を確認：

### **1. Docker コンテナ確認**

```bash
docker-compose -f docker-compose-server.yml ps

# 出力例:
# NAME                STATUS
# vsb-backend         Up 2 minutes
# vsb-frontend        Up 1 minute
```

### **2. API ヘルスチェック**

```bash
curl http://localhost:8000/health

# 出力例:
# {"status":"ok","timestamp":"2026-09-28T...","adb_host":"localhost","adb_port":5037}
```

### **3. adb デバイス確認**

```bash
adb devices

# 出力例:
# List of attached devices
# emulator-5554  device
```

### **4. ブラウザアクセス**

```
http://<server-ip>:3000
```

- デバイスセレクタにデバイスが表示される
- 画面プレビューがライブ更新される
- アクションを記録できる

---

## 📊 **よく使うコマンド**

### **コンテナ管理**

```bash
# コンテナ起動
docker-compose -f docker-compose-server.yml up -d

# コンテナ停止
docker-compose -f docker-compose-server.yml stop

# コンテナ再起動
docker-compose -f docker-compose-server.yml restart

# コンテナ削除（再構築時）
docker-compose -f docker-compose-server.yml down

# コンテナ状態確認
docker-compose -f docker-compose-server.yml ps
```

### **ログ確認**

```bash
# 全ログ表示
docker-compose -f docker-compose-server.yml logs

# 特定サービスのログ
docker-compose -f docker-compose-server.yml logs backend
docker-compose -f docker-compose-server.yml logs frontend

# リアルタイムログ
docker-compose -f docker-compose-server.yml logs -f backend
```

### **トラブルシューティング**

```bash
# API が応答しているか確認
curl -i http://localhost:8000/health

# Docker コンテナ内でシェルを実行
docker-compose -f docker-compose-server.yml exec backend bash

# Docker イメージを再ビルド（キャッシュなし）
docker-compose -f docker-compose-server.yml build --no-cache
```

---

## 🔧 **トラブルシューティング**

### **❌ ポート 3000/8000 が既に使用されている**

```bash
# 使用中のプロセスを確認
sudo lsof -i :3000
sudo lsof -i :8000

# プロセスを停止
sudo kill -9 <PID>

# または docker-compose.yml でポート番号を変更
```

### **❌ デバイスが接続されない**

```bash
# adb デーモンを再起動
adb kill-server
adb start-server

# デバイス確認
adb devices

# Android 設定確認
# Settings → Developer Options → USB Debugging → ON
```

### **❌ Docker イメージビルド失敗**

```bash
# Docker キャッシュをクリア
docker system prune -a

# 再ビルド
docker-compose -f docker-compose-server.yml build --no-cache
docker-compose -f docker-compose-server.yml up -d
```

### **❌ API が応答しない**

```bash
# ログ確認
docker-compose -f docker-compose-server.yml logs backend

# ヘルスチェック
curl http://localhost:8000/health

# コンテナ再起動
docker-compose -f docker-compose-server.yml restart backend
```

---

## 📚 **詳細ドキュメント**

以下のドキュメントを参照してください：

| ドキュメント | 内容 |
|-------------|------|
| **QUICK_START_SERVER.md** | 5分クイックスタート（最もシンプル） |
| **SERVER_SETUP_GUIDE.md** | 詳細なセットアップ（トラブルシューティング含む） |
| **HANDOVER_CHECKLIST.md** | ファイル引き継ぎチェックリスト |
| **README.md** | Part 1 テストフレームワーク概要 |
| **SETUP_GUIDE.md** | Part 1 セットアップガイド |
| **VSB_README.md** | Part 2 Visual Scenario Builder 概要 |
| **VSB_SETUP_GUIDE.md** | Part 2 VSB セットアップ |

---

## 🎯 **次のステップ**

### **1. シナリオ作成**

```
ブラウザで http://<server-ip>:3000 にアクセス
  ↓
デバイスを選択
  ↓
画面プレビューでアクションを記録
  ↓
「Export as YAML」でシナリオを保存
```

### **2. テスト実行**

Part 1 テストフレームワークで YAML シナリオを実行：

```bash
python test_framework_main.py \
  --scenario scenarios/my-scenario.yaml \
  --slack_token xoxb-... \
  --slack_channel #test-automation \
  --device_id emulator-5554
```

### **3. 本番環境対応**

```bash
# HTTPS 有効化
# ファイアウォール強化
# リソース制限
# バックアップ設定
```

詳細は `SERVER_SETUP_GUIDE.md` の「本番環境設定」を参照。

---

## 🔐 **セキュリティ推奨事項**

### **本番環境での設定**

1. **HTTPS 有効化**
   ```bash
   certbot certonly --standalone -d your-domain.com
   ```

2. **CORS 制限**
   ```env
   ALLOWED_ORIGINS=https://your-domain.com
   ```

3. **ファイアウォール設定**
   ```bash
   sudo ufw allow 22/tcp      # SSH
   sudo ufw allow 80/tcp      # HTTP
   sudo ufw allow 443/tcp     # HTTPS
   sudo ufw deny incoming
   ```

4. **API 認証（推奨）**
   - Basic Auth の実装
   - API キー ベースの認証

---

## 📝 **ファイルリスト（完全）**

### **転送すべきファイル**

```bash
# 最小限のセット
backend_server.py
docker-compose-server.yml
Dockerfile.backend.server
Dockerfile.frontend.server
nginx.conf
setup-server.sh
.env.server
backend_requirements.txt
frontend/

# 推奨（ドキュメント）
SERVER_SETUP_GUIDE.md
QUICK_START_SERVER.md
HANDOVER_CHECKLIST.md
TRANSFER_PACKAGE.md

# オプション（Part 1 テストフレームワーク）
test_framework_main.py
test_utils.py
requirements.txt
SETUP_GUIDE.md
```

### **転送コマンド（まとめ）**

```bash
# ローカルマシンから実行
scp -r ~/vsb user@dev-server:/home/user/

# または git
git clone <url> /home/user/vsb
```

---

## ✨ **この引き継ぎパッケージの特徴**

✅ **完全自動化** - `setup-server.sh` で全て完了  
✅ **環境対応** - ローカル/WiFi/リモート adb に対応  
✅ **ドキュメント豊富** - 詳細ガイド、クイックスタート、チェックリスト  
✅ **本番対応** - HTTPS, CORS, リソース制限, バックアップ対応  
✅ **トラブルシューティング** - 一般的な問題と解決方法を網羅  

---

## 📞 **問題が発生した場合**

1. **QUICK_START_SERVER.md** → トラブルシューティング セクション確認
2. **SERVER_SETUP_GUIDE.md** → 詳細なトラブルシューティング
3. ログ確認 → `docker-compose -f docker-compose-server.yml logs -f`
4. ファイアウォール確認 → `sudo ufw status`

---

## 🎉 **準備完了！**

このファイルをサーバに転送して、`setup-server.sh` を実行するだけで、
完全な Visual Scenario Builder サーバ実行版がセットアップされます。

**Happy Testing! 🚀**

---

**パッケージ情報**  
生成日: 2026-09-28  
バージョン: Visual Scenario Builder Server Edition v1.0  
対応環境: Linux (Ubuntu 20.04+, Debian 11+)  
必須: Docker 20.10+, Docker Compose 1.29+
