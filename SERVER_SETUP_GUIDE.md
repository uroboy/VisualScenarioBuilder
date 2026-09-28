# Visual Scenario Builder - リモートサーバ実行ガイド

このガイドでは、VSB を リモートサーバ上で実行する手順を説明します。

## 前提条件

### サーバ側
- **OS**: Ubuntu 20.04 LTS 以上 / Debian 11 以上
- **CPU**: 2コア以上推奨
- **メモリ**: 4GB 以上
- **ストレージ**: 20GB 以上
- **ネットワーク**: インターネット接続（Docker イメージ取得用）

### インストール必須
- Docker 20.10 以上
- Docker Compose 1.29 以上
- git

### デバイス接続
- Android デバイス（USB接続 or リモート adb）
- USB ケーブル or WiFi 接続

---

## 1. サーバの準備

### 1-1. Docker インストール

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# docker グループに追加（sudo なしで実行可能に）
sudo usermod -aG docker $USER
newgrp docker
```

### 1-2. Docker Compose インストール

```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

### 1-3. git インストール

```bash
sudo apt-get update
sudo apt-get install -y git
```

---

## 2. ファイル配置

### 2-1. リポジトリクローン

```bash
# サーバ上のディレクトリ作成
mkdir -p /home/ubuntu/vsb
cd /home/ubuntu/vsb

# git クローン（または手動でファイルをアップロード）
git clone <repository-url> .
```

### 2-2. 必要なファイルチェック

```bash
ls -la
```

**最小限の必須ファイル：**
```
backend_server.py
frontend/
  - src/
    - App.jsx
    - index.js
  - public/
    - index.html
  - package.json
docker-compose-server.yml
Dockerfile.backend.server
Dockerfile.frontend.server
nginx.conf
.env.server
backend_requirements.txt
```

### 2-3. ディレクトリ構造を作成

```bash
mkdir -p scenarios logs results
chmod -R 755 scenarios logs results
```

---

## 3. 環境設定

### 3-1. `.env.server` を編集

```bash
cp .env.server .env
vi .env  # または nano .env
```

**重要な設定項目：**

```env
# API ホスト（サーバのIPアドレスに変更）
API_HOST=0.0.0.0
API_PORT=8000

# フロントエンドから API へアクセスするURL
# サーバのIPアドレス or ドメイン名に変更
REACT_APP_API_URL=http://192.168.1.100:8000/api

# ADB ホスト
# ローカル接続: localhost
# リモート接続: <デバイスのIPアドレス>
ADB_HOST=localhost
ADB_PORT=5037

# CORS（複数指定可能、本番環境では制限推奨）
ALLOWED_ORIGINS=*

# ログレベル
LOG_LEVEL=INFO
```

### 3-2. ファイアウォール設定

```bash
# UFW 有効化（未設定の場合）
sudo ufw enable

# ポート 3000（フロントエンド）と 8000（API）を許可
sudo ufw allow 3000/tcp
sudo ufw allow 8000/tcp
sudo ufw allow 5037/tcp  # adb

# 確認
sudo ufw status
```

---

## 4. デバイス接続設定

### 4-1. USB接続（ローカル）

```bash
# デバイスをUSBで接続

# adb で接続確認
adb devices

# 出力例:
# List of attached devices
# emulator-5554  device
```

### 4-2. WiFi接続（リモート）

```bash
# デバイス側で「USB デバッグ」を有効化
# Android Settings → Developer Options → USB Debugging

# WiFi 経由で接続
adb connect <device-ip>:5555

# 確認
adb devices

# docker-compose-server.yml で ADB_HOST を設定
# ADB_HOST=<device-ip>
# ADB_PORT=5555
```

### 4-3. リモート adb サーバ（別マシンで adb デーモンが起動している場合）

```bash
# .env.server で設定
ADB_HOST=192.168.1.50  # adb デーモンが起動しているマシンのIP
ADB_PORT=5037
```

---

## 5. Docker Compose 起動

### 5-1. イメージビルド

```bash
cd /home/ubuntu/vsb

# イメージをビルド
docker-compose -f docker-compose-server.yml build

# 出力例:
# Building backend...
# Building frontend...
```

### 5-2. コンテナ起動

```bash
# バックグラウンド起動
docker-compose -f docker-compose-server.yml up -d

# または前景起動（ログを表示）
docker-compose -f docker-compose-server.yml up
```

### 5-3. 起動確認

```bash
# コンテナ状態確認
docker-compose -f docker-compose-server.yml ps

# 出力例:
# NAME                  STATUS
# vsb-backend           Up 2 minutes
# vsb-frontend          Up 2 minutes
```

### 5-4. ログ確認

```bash
# すべてのログ
docker-compose -f docker-compose-server.yml logs

# 特定サービスのログ
docker-compose -f docker-compose-server.yml logs backend
docker-compose -f docker-compose-server.yml logs frontend

# リアルタイムログ
docker-compose -f docker-compose-server.yml logs -f backend
```

---

## 6. アクセス

### 6-1. URL

- **フロントエンド**: `http://<server-ip>:3000`
- **API ドキュメント**: `http://<server-ip>:8000/api/docs`
- **ヘルスチェック**: `http://<server-ip>:8000/health`

### 6-2. 接続テスト

```bash
# ローカルから
curl http://localhost:8000/health
curl http://localhost:3000

# リモートから
curl http://192.168.1.100:8000/health
curl http://192.168.1.100:3000
```

---

## 7. 使用方法

### 7-1. ブラウザでアクセス

```
http://<server-ip>:3000
```

### 7-2. デバイス選択

1. 「Device Selector」でデバイス一覧から選択
2. 「Select」ボタンをクリック

### 7-3. 画面プレビュー

1. 「Screen Preview」にライブ画面が表示される
2. 画面上の要素をクリックすると、要素情報が表示される

### 7-4. アクション記録

1. 「Action Builder」でアクションタイプを選択
2. パラメータを入力
3. 「Add Action」で追加

### 7-5. シナリオ保存

1. 「Scenario Editor」で作成したアクション一覧を確認
2. 「Export as YAML」で保存

---

## 8. トラブルシューティング

### 8-1. ポートが既に使用されている

```bash
# ポート 3000 が使用されているか確認
sudo lsof -i :3000
sudo lsof -i :8000

# 既存プロセスを削除（強制）
sudo kill -9 <PID>

# または docker-compose.yml でポート番号を変更
# ports:
#   - "0.0.0.0:8001:8000"  # 8001 を使用
```

### 8-2. デバイスが接続されない

```bash
# adb デーモン再起動
adb kill-server
adb start-server

# デバイス確認
adb devices

# USB デバッグ有効化を確認
# Settings → Developer Options → USB Debugging (ON)
```

### 8-3. docker イメージビルド失敗

```bash
# キャッシュをクリア
docker-compose -f docker-compose-server.yml down
docker system prune -a

# 再ビルド
docker-compose -f docker-compose-server.yml build --no-cache
```

### 8-4. API が応答しない

```bash
# バックエンド ログ確認
docker-compose -f docker-compose-server.yml logs backend

# ヘルスチェック
curl http://localhost:8000/health

# コンテナ再起動
docker-compose -f docker-compose-server.yml restart backend
```

### 8-5. CORS エラー

```env
# .env.server で CORS を許可
ALLOWED_ORIGINS=*

# または特定オリジンのみ
ALLOWED_ORIGINS=http://192.168.1.100:3000,http://example.com
```

### 8-6. WebSocket 接続エラー

```bash
# nginx.conf で WebSocket サポートが有効か確認
grep "Upgrade\|upgrade" nginx.conf

# ファイアウォールで WebSocket ポートが許可されているか確認
sudo ufw allow 3000/tcp
sudo ufw allow 8000/tcp
```

---

## 9. 本番環境設定（推奨）

### 9-1. HTTPS 設定

```bash
# Let's Encrypt で証明書取得
sudo apt-get install -y certbot

certbot certonly --standalone -d <your-domain>

# nginx.conf で SSL 設定
server {
    listen 443 ssl http2;
    ssl_certificate /etc/letsencrypt/live/<your-domain>/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/<your-domain>/privkey.pem;
    ...
}
```

### 9-2. 認証設定

```bash
# アクセス制限（Basic Auth）
sudo apt-get install -y apache2-utils

htpasswd -c /etc/nginx/.htpasswd user1

# nginx.conf で認証設定
location / {
    auth_basic "Restricted";
    auth_basic_user_file /etc/nginx/.htpasswd;
    ...
}
```

### 9-3. リソース制限

```bash
# Docker メモリ制限（docker-compose.yml）
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 2G
```

---

## 10. バックアップと復元

### 10-1. シナリオバックアップ

```bash
# scenarios ディレクトリをバックアップ
tar -czf scenarios-backup-$(date +%Y%m%d).tar.gz scenarios/

# クラウドストレージへアップロード
scp scenarios-backup-*.tar.gz user@backup-server:/backups/
```

### 10-2. ログバックアップ

```bash
# ログをローテーション
docker-compose -f docker-compose-server.yml logs --tail=1000 > logs/$(date +%Y%m%d_%H%M%S).log
```

---

## 11. 定期メンテナンス

### 11-1. イメージ更新

```bash
# イメージを最新に更新
docker-compose -f docker-compose-server.yml down
docker-compose -f docker-compose-server.yml pull
docker-compose -f docker-compose-server.yml build
docker-compose -f docker-compose-server.yml up -d
```

### 11-2. ディスク容量確認

```bash
# ディスク使用量確認
docker system df

# 未使用イメージ削除
docker image prune -a --force
```

---

## サポート

トラブルが発生した場合：

1. ログを確認
2. `.env` 設定を確認
3. ファイアウォール設定を確認
4. デバイス接続を確認

---

**最終更新**: 2026-09-28
