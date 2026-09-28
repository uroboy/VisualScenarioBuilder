#!/bin/bash

# Visual Scenario Builder - クイックスタート
# このスクリプトで環境構築と起動が自動化されます

set -e

echo "========================================="
echo "Visual Scenario Builder - Setup"
echo "========================================="
echo ""

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ==================== 前提条件チェック ====================
echo -e "${YELLOW}前提条件をチェック中...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker がインストールされていません${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose がインストールされていません${NC}"
    exit 1
fi

if ! command -v adb &> /dev/null; then
    echo -e "${RED}❌ adb がインストールされていません${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker, Docker Compose, adb がインストール済みです${NC}"
echo ""

# ==================== デバイス接続確認 ====================
echo -e "${YELLOW}Android デバイス接続確認中...${NC}"

device_count=$(adb devices | grep -c "device$" || true)

if [ "$device_count" -eq 0 ]; then
    echo -e "${YELLOW}⚠ デバイスが接続されていません${NC}"
    echo "  USB でデバイスを接続してください"
    echo "  接続後: adb devices"
    read -p "続行しますか？ (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓ $device_count 個のデバイスが接続されています${NC}"
    adb devices
    echo ""
fi

# ==================== ディレクトリ構成を作成 ====================
echo -e "${YELLOW}ディレクトリ構造を作成中...${NC}"

mkdir -p scenarios
mkdir -p frontend/src
mkdir -p frontend/public
mkdir -p logs

echo -e "${GREEN}✓ ディレクトリを作成しました${NC}"
echo ""

# ==================== フロントエンド ファイル配置 ====================
echo -e "${YELLOW}フロントエンド ファイルを配置中...${NC}"

# package.json
if [ ! -f "frontend/package.json" ]; then
    cp frontend_package.json frontend/package.json
    echo "  ✓ package.json をコピーしました"
fi

# App.jsx
if [ ! -f "frontend/src/App.jsx" ]; then
    cp frontend_App.jsx frontend/src/App.jsx
    echo "  ✓ App.jsx をコピーしました"
fi

# App.css
if [ ! -f "frontend/src/App.css" ]; then
    cp frontend_App.css frontend/src/App.css
    echo "  ✓ App.css をコピーしました"
fi

# index.js
if [ ! -f "frontend/src/index.js" ]; then
    cp frontend_index.js frontend/src/index.js
    echo "  ✓ index.js をコピーしました"
fi

# index.html
if [ ! -f "frontend/public/index.html" ]; then
    cp frontend_index.html frontend/public/index.html
    echo "  ✓ index.html をコピーしました"
fi

echo ""

# ==================== Docker イメージをビルド ====================
echo -e "${YELLOW}Docker イメージをビルド中（初回のみ時間がかかります）...${NC}"

docker-compose -f docker-compose-vsb.yml build

echo -e "${GREEN}✓ Docker イメージをビルドしました${NC}"
echo ""

# ==================== コンテナを起動 ====================
echo -e "${YELLOW}コンテナを起動中...${NC}"

docker-compose -f docker-compose-vsb.yml up &

# バックエンドの起動を待つ
sleep 5

if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✓ バックエンド (FastAPI) が起動しました${NC}"
else
    echo -e "${YELLOW}⚠ バックエンドの起動に時間がかかっています...${NC}"
fi

sleep 10

# フロントエンドの起動を待つ
if curl -s http://localhost:3000 > /dev/null; then
    echo -e "${GREEN}✓ フロントエンド (React) が起動しました${NC}"
else
    echo -e "${YELLOW}⚠ フロントエンドの起動に時間がかかっています...${NC}"
fi

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}✓ セットアップが完了しました！${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""

# ==================== ブラウザを開く ====================
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000
elif command -v open &> /dev/null; then
    open http://localhost:3000
else
    echo -e "${YELLOW}ブラウザで以下のURLを開いてください:${NC}"
    echo "  http://localhost:3000"
fi

echo ""
echo -e "${YELLOW}ログの確認:${NC}"
echo "  docker-compose -f docker-compose-vsb.yml logs -f"
echo ""
echo -e "${YELLOW}停止:${NC}"
echo "  docker-compose -f docker-compose-vsb.yml down"
echo ""
echo -e "${YELLOW}詳細はこちらを参照:${NC}"
echo "  VSB_SETUP_GUIDE.md"
echo ""
