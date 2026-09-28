# Visual Scenario Builder - サーバ実行版 引き継ぎチェックリスト

このファイルで、サーバ実行用にアップデートされた全ファイルを確認できます。

---

## ✅ 新規作成ファイル（サーバ実行対応）

### Docker 設定

- [x] **`docker-compose-server.yml`**
  - リモートアクセス対応（0.0.0.0 バインディング）
  - CORS 設定対応
  - リモート adb 接続サポート
  - 新規

- [x] **`Dockerfile.backend.server`**
  - Python 3.11 slim ベース
  - adb, tesseract 等を含む
  - ヘルスチェック実装
  - 新規

- [x] **`Dockerfile.frontend.server`**
  - Node 20 alpine でビルド
  - NGINX でサーブ
  - リバースプロキシ対応
  - 新規

- [x] **`nginx.conf`**
  - リバースプロキシ設定
  - WebSocket サポート
  - API プロキシ設定
  - 新規

### バックエンド

- [x] **`backend_server.py`**
  - FastAPI 実装（前のバージョンから改善）
  - リモート adb 接続サポート
  - CORS ミドルウェア
  - WebSocket ストリーミング
  - ヘルスチェックエンドポイント
  - 起動情報ログ
  - 置換版（backend.py に置き換え）

### 環境設定

- [x] **`.env.server`**
  - サーバ実行用テンプレート
  - API_HOST=0.0.0.0
  - REACT_APP_API_URL 設定
  - ADB_HOST/ADB_PORT 設定
  - ALLOWED_ORIGINS（CORS）
  - LOG_LEVEL 設定
  - 新規

### ドキュメント

- [x] **`SERVER_SETUP_GUIDE.md`**
  - 詳細なセットアップ手順
  - 前提条件チェック
  - トラブルシューティング
  - 本番環境設定
  - バックアップ・復元手順
  - 新規

- [x] **`QUICK_START_SERVER.md`**
  - 5分クイックスタート
  - ステップバイステップガイド
  - よく使うコマンド集
  - トラブルシューティング簡易版
  - 新規

- [x] **`HANDOVER_CHECKLIST.md`**
  - このファイル
  - 引き継ぎ用チェックリスト
  - 新規

### セットアップ自動化

- [x] **`setup-server.sh`**
  - 自動セットアップスクリプト
  - システム環境チェック
  - 依存パッケージのインストール
  - ディレクトリ作成
  - ファイアウォール設定
  - Docker ビルド・起動
  - ヘルスチェック
  - 新規

---

## 📋 既存ファイル（互換性確認）

### Part 1: テストフレームワーク

以下は既存のまま使用可能：

- [x] **`test_framework_main.py`**
  - 変更不要（ローカル実行用）
  - サーバで実行可能

- [x] **`test_utils.py`**
  - 変更不要
  - サーバで実行可能

- [x] **`test_scenario_example.yaml`**
  - 変更不要
  - サーバで生成可能

- [x] **`requirements.txt`**
  - 変更不要
  - Part 1 用

- [x] **`docker-compose.yml`**
  - そのまま保持（ローカル実行用）
  - 新しい `docker-compose-server.yml` と併用可

- [x] **`Dockerfile`**
  - そのまま保持（ローカル実行用）
  - 新しい `Dockerfile.backend.server` と併用可

### Part 2: Visual Scenario Builder（ローカル版）

以下の既存ファイルは置き換え推奨：

- [ ] **`backend.py`** → `backend_server.py` に置き換え
- [ ] **`.env.example`** → `.env.server` を使用
- [ ] **`Dockerfile.backend`** → `Dockerfile.backend.server` に置き換え
- [ ] **`Dockerfile.frontend`** → `Dockerfile.frontend.server` に置き換え

既存ファイルをバックアップしたい場合：

```bash
mkdir -p backup_local
mv backend.py backup_local/
mv Dockerfile.backend backup_local/
mv Dockerfile.frontend backup_local/
mv docker-compose-vsb.yml backup_local/
```

---

## 🔄 使い分け

### ローカル開発時

```bash
# Part 1 のみ実行
docker-compose -f docker-compose.yml up

# または Part 2 のみ
docker-compose -f docker-compose-vsb.yml up
```

### サーバ実行時

```bash
# サーバ統合版
docker-compose -f docker-compose-server.yml up -d
```

---

## 📦 引き継ぎパッケージ内容

サーバへ転送すべきファイル：

```
vsb/
├── backend_server.py .................... FastAPI バックエンド（新）
├── docker-compose-server.yml ............ Docker Compose 設定（新）
├── Dockerfile.backend.server ............ バックエンド Docker（新）
├── Dockerfile.frontend.server ........... フロントエンド Docker（新）
├── nginx.conf ........................... NGINX リバースプロキシ（新）
├── setup-server.sh ...................... 自動セットアップ（新）
├── .env.server .......................... 環境設定テンプレート（新）
├── backend_requirements.txt ............. Python 依存（既存）
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── index.js
│   ├── public/
│   │   └── index.html
│   └── package.json
│
├── SERVER_SETUP_GUIDE.md ................ 詳細ガイド（新）
├── QUICK_START_SERVER.md ............... クイックスタート（新）
├── HANDOVER_CHECKLIST.md ............... このファイル（新）
│
├── test_framework_main.py .............. テストフレームワーク（既存）
├── test_utils.py ....................... ユーティリティ（既存）
├── test_scenario_example.yaml .......... シナリオ例（既存）
├── requirements.txt .................... Python 依存（既存）
│
├── README.md ........................... 概要（既存）
└── SETUP_GUIDE.md ...................... セットアップ（既存）
```

### 最小限のセットアップに必要なファイル

```
backend_server.py
docker-compose-server.yml
Dockerfile.backend.server
Dockerfile.frontend.server
nginx.conf
setup-server.sh
.env.server
backend_requirements.txt
frontend/（src/public 含む）
```

---

## 🚀 セットアップ手順サマリー

### 1. ファイル転送

```bash
# ローカルマシンから
scp -r vsb/ user@server-ip:/home/user/

# または git
git clone <url> /home/user/vsb
cd /home/user/vsb
```

### 2. 自動セットアップ

```bash
chmod +x setup-server.sh
./setup-server.sh
```

### 3. アクセス

```
http://<server-ip>:3000
```

### 4. デバイス接続

```bash
adb devices
```

---

## ✨ 新機能（サーバ実行対応版）

### ✅ リモートアクセス
- 0.0.0.0 バインディング
- IP アドレスでアクセス可能
- CORS 設定完備

### ✅ リモート adb 接続
- ローカルデバイス（USB）
- WiFi デバイス
- リモート adb サーバ対応

### ✅ 本番環境対応
- NGINX リバースプロキシ
- WebSocket サポート
- ヘルスチェック
- ロギング
- リソース制限対応

### ✅ 自動セットアップ
- ワンコマンドでセットアップ
- 依存パッケージ自動インストール
- ファイアウォール自動設定
- ヘルスチェック実装

### ✅ ドキュメント
- 詳細セットアップガイド
- クイックスタート
- トラブルシューティング
- 本番環境設定ガイド

---

## 🔧 トラブルシューティング

### ファイルが見当たらない

```bash
# ファイルリスト確認
ls -la

# ファイルが足りない場合は、以下から取得：
git status
git pull
```

### スクリプト実行権限エラー

```bash
chmod +x setup-server.sh
./setup-server.sh
```

### Docker エラー

```bash
# Docker グループに追加
sudo usermod -aG docker $USER

# グループ変更を反映
newgrp docker

# または新しいシェルセッションを開く
exit
ssh user@server-ip
```

---

## 📝 修正が必要な箇所

設定ファイルを環境に合わせて修正してください：

### 1. `.env` ファイル

```bash
cp .env.server .env
```

以下を編集：

```env
# サーバのIP アドレスに変更
REACT_APP_API_URL=http://192.168.1.100:8000/api

# デバイス接続先を指定
ADB_HOST=localhost  # またはデバイスのIP
ADB_PORT=5037
```

### 2. 本番環境（推奨）

```bash
# HTTPS 有効化
certbot certonly --standalone -d example.com

# ファイアウォール強化
sudo ufw allow 22/tcp
sudo ufw allow 443/tcp
sudo ufw deny incoming
```

---

## 📞 サポート

問題が発生した場合：

1. **QUICK_START_SERVER.md** → トラブルシューティング セクション
2. **SERVER_SETUP_GUIDE.md** → 詳細なガイド
3. ログ確認 → `docker-compose -f docker-compose-server.yml logs -f`

---

## ✅ チェックリスト（実行前）

セットアップ前に以下を確認してください：

- [ ] Linux サーバを準備した
- [ ] Docker がインストールされている
- [ ] docker-compose がインストールされている
- [ ] git がインストールされている
- [ ] ファイアウォール設定確認（または disable）
- [ ] Android デバイスを用意した
- [ ] USB ケーブル or WiFi 接続が可能
- [ ] SSH でサーバにアクセスできる

---

## ✅ チェックリスト（セットアップ後）

セットアップが完了したら以下を確認：

- [ ] `setup-server.sh` が成功した
- [ ] Docker コンテナが起動している（`docker ps`）
- [ ] ブラウザで `http://<server-ip>:3000` にアクセスできる
- [ ] `http://<server-ip>:8000/health` が応答する
- [ ] `adb devices` でデバイスが表示される
- [ ] フロントエンドでデバイスを選択できる
- [ ] 画面プレビューが表示される

---

## 🎉 完了！

ここまで来たら、サーバでの VSB 実行は完了です！

次は：
1. **シナリオ作成** → Web UI で画面アクション記録
2. **YAML エクスポート** → シナリオを保存
3. **テスト実行** → Part 1 フレームワークで自動実行

---

**最終更新**: 2026-09-28  
**バージョン**: Server Edition v1.0
