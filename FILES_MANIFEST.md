# Visual Scenario Builder - ファイルマニフェスト

**このドキュメント内のファイル内容は、サーバ上のセッションからコピー&ペースト、または base64 デコードで復元できます。**

---

## 📥 **サーバ上での復元方法**

### **方法 1: Claude との会話でファイル内容をコピー**

サーバの Claude セッションで：

```
「/home/claude 配下のすべてのファイルをセッション内容から復元してください」
```

と指示すれば、各ファイルを復元できます。

### **方法 2: ファイル内容を一覧表示**

以下、各ファイルの一覧と参照方法を示します。

---

## 📋 **必須ファイルリスト**

| ファイル | 用途 | サイズ | 復元方法 |
|---------|------|--------|---------|
| `docker-compose-server.yml` | Docker Compose 設定 | ~4KB | コピペ |
| `backend_server.py` | FastAPI バックエンド | ~15KB | コピペ |
| `Dockerfile.backend.server` | バックエンド Docker | ~1KB | コピペ |
| `Dockerfile.frontend.server` | フロントエンド Docker | ~0.5KB | コピペ |
| `nginx.conf` | NGINX リバースプロキシ | ~2KB | コピペ |
| `.env.server` | 環境設定テンプレート | ~1KB | コピペ |
| `setup-server.sh` | 自動セットアップ | ~7KB | コピペ |
| `backend_requirements.txt` | Python 依存 | ~0.5KB | コピペ |

### **ドキュメント**

| ファイル | 用途 |
|---------|------|
| `QUICK_START_SERVER.md` | 5分クイックスタート |
| `SERVER_SETUP_GUIDE.md` | 詳細セットアップ |
| `HANDOVER_CHECKLIST.md` | チェックリスト |

---

## 🔄 **復元スクリプト（サーバ上で実行）**

サーバの Claude セッションで以下を実行すれば、全ファイルが復元されます：

```bash
# サーバ上で
cd /home/user/vsb

# 以下を Claude に指示
# 「このセッションから、/home/claude の全ファイルを復元してください」
```

Claude が以下を提供します：
1. 各ファイルの内容
2. `cat > filename << 'EOF'` 形式のコマンド
3. 自動復元スクリプト

---

## 📦 **別の方法：このセッションから直接ダウンロード**

**ローカルマシンから、サーバへ直接転送：**

```bash
# ローカルマシン
cd /home/claude

# サーバへ一括転送
rsync -avz . user@dev-server:/home/user/vsb/

# または scp
scp -r . user@dev-server:/home/user/vsb/
```

---

## ✅ **推奨手順**

### **最もシンプル：GitHub 経由**

1. このマシンで git リポジトリを作成
2. GitHub にプッシュ
3. サーバで `git clone`

```bash
# ローカル（このマシン）
cd /home/claude
git init && git add . && git commit -m "VSB Server Edition"
git remote add origin https://github.com/your-account/vsb.git
git push -u origin main

# サーバ上
git clone https://github.com/your-account/vsb.git /home/user/vsb
cd /home/user/vsb
chmod +x setup-server.sh
./setup-server.sh
```

### **次点：Claude セッション経由**

1. サーバの Claude セッションを新規開始
2. 「前のセッションから VSB ファイルを復元してください」と指示
3. Claude が全ファイルを提供
4. コピペで復元

---

## 🎯 **最終推奨**

✅ **GitHub リポジトリが最も確実です** 

- バージョン管理可能
- サーバから直接 `git clone`
- CI/CD パイプラインにも対応

---

**このマニフェストを基に、好きな方法を選んでください。**
