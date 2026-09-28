# Visual Scenario Builder - リモートサーバ クイックスタート

**最短 5 分でセットアップ完了！**

---

## 前置き

このガイドは、Linux サーバ上で VSB をすぐに実行したい方向けです。
詳細な設定については `SERVER_SETUP_GUIDE.md` をご覧ください。

---

## ステップ 1: サーバにログイン

```bash
ssh user@server-ip
```

---

## ステップ 2: ファイルをサーバに転送

**ローカルマシンから：**

```bash
# リポジトリ全体をアップロード
scp -r /path/to/vsb user@server-ip:/home/user/vsb

# または git でクローン
ssh user@server-ip
git clone <repository-url> ~/vsb
cd ~/vsb
```

---

## ステップ 3: 自動セットアップ実行

**サーバ上：**

```bash
cd ~/vsb

# スクリプトに実行権限を付与
chmod +x setup-server.sh

# セットアップ実行
./setup-server.sh
```

**入力プロンプト：**
- "Enable UFW?" → `y` （推奨）
- "Start containers now?" → `y` 

セットアップスクリプトが自動的に以下を実行します：
- ✅ 依存パッケージのインストール
- ✅ ディレクトリ作成
- ✅ ファイアウォール設定
- ✅ Docker イメージビルド
- ✅ コンテナ起動

---

## ステップ 4: アクセス確認

セットアップ完了後、ブラウザで以下にアクセス：

```
http://<server-ip>:3000
```

**例：**
```
http://192.168.1.100:3000
```

---

## ステップ 5: デバイス接続

### USB接続の場合

```bash
# サーバで実行
adb devices

# 出力例:
# emulator-5554  device
```

### WiFi接続の場合

```bash
# デバイス側で「USB デバッグ」を有効化
# Settings → Developer Options → USB Debugging → ON

# サーバで実行
adb connect <device-ip>:5555
```

---

## トラブルシューティング

### ① ポート 3000 が既に使用されている

```bash
# ポートを確認
sudo lsof -i :3000

# 既存プロセスを停止
sudo kill -9 <PID>

# または別のポート使用
# .env で PORT=3001 に変更
```

### ② デバイスが接続されない

```bash
# adb を再起動
adb kill-server
adb start-server
adb devices
```

### ③ Docker コンテナが起動しない

```bash
# ログ確認
docker-compose -f docker-compose-server.yml logs

# コンテナ再起動
docker-compose -f docker-compose-server.yml restart
```

---

## よく使うコマンド

```bash
# コンテナ起動
docker-compose -f docker-compose-server.yml up -d

# コンテナ停止
docker-compose -f docker-compose-server.yml stop

# ログ表示（リアルタイム）
docker-compose -f docker-compose-server.yml logs -f backend

# コンテナ状態確認
docker-compose -f docker-compose-server.yml ps

# コンテナ削除（再構築時）
docker-compose -f docker-compose-server.yml down
```

---

## 設定ファイル

セットアップ後、以下ファイルを編集して動作をカスタマイズ可能：

### `.env` ファイル

```env
# API アクセスURL（ブラウザから API へアクセスする場合のURL）
REACT_APP_API_URL=http://192.168.1.100:8000/api

# ADB 接続先（ローカルの場合は localhost）
ADB_HOST=localhost
ADB_PORT=5037

# CORS 許可オリジン
ALLOWED_ORIGINS=*
```

編集後、コンテナを再起動：

```bash
docker-compose -f docker-compose-server.yml restart
```

---

## 本番環境への推奨設定

### ① HTTPS 有効化

```bash
# Let's Encrypt 証明書取得
sudo apt-get install -y certbot
certbot certonly --standalone -d example.com
```

### ② ファイアウォール強化

```bash
# SSH のみ許可
sudo ufw allow 22/tcp
sudo ufw allow 3000/tcp
sudo ufw allow 8000/tcp
sudo ufw enable
```

### ③ リソース制限

Docker Compose で CPU/メモリ制限を設定：

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 2G
```

---

## ファイル構成

セットアップ後の標準ディレクトリ構成：

```
/home/user/vsb/
├── backend_server.py          # FastAPI バックエンド
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── index.js
│   ├── public/
│   │   └── index.html
│   └── package.json
├── docker-compose-server.yml  # メイン設定
├── Dockerfile.backend.server  # バックエンド Docker
├── Dockerfile.frontend.server # フロントエンド Docker
├── nginx.conf                 # NGINX 設定
├── .env                       # 環境変数（セットアップで作成）
├── scenarios/                 # 保存されたシナリオ
├── logs/                      # ログファイル
└── results/                   # テスト結果
```

---

## ネクストステップ

1. **シナリオ作成**: ブラウザで画面をクリックしてアクションを記録
2. **YAML エクスポート**: 作成したシナリオを YAML で保存
3. **テスト実行**: Part 1 のテストフレームワークで自動実行

詳細は `SERVER_SETUP_GUIDE.md` をご覧ください。

---

## サポート

問題が発生した場合：

1. **ログ確認**
   ```bash
   docker-compose -f docker-compose-server.yml logs backend
   docker-compose -f docker-compose-server.yml logs frontend
   ```

2. **ヘルスチェック**
   ```bash
   curl http://localhost:8000/health
   ```

3. **ファイアウォール確認**
   ```bash
   sudo ufw status
   ```

4. **Docker 再構築**
   ```bash
   docker-compose -f docker-compose-server.yml down
   docker-compose -f docker-compose-server.yml build --no-cache
   docker-compose -f docker-compose-server.yml up -d
   ```

---

**準備完了！ハッピーテスト！🚀**
