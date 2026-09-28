#!/bin/bash

# ==================== Visual Scenario Builder - Server Setup Script ====================
# このスクリプトは、リモートサーバ上で VSB を自動セットアップします。

set -e  # エラーで終了

# ==================== カラー定義 ====================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

# ==================== ユーティリティ関数 ====================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if command -v $1 &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# ==================== 初期化 ====================

clear
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║ Visual Scenario Builder - Server Setup                     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

log_info "Starting setup process..."
SETUP_TIME=$(date '+%Y-%m-%d %H:%M:%S')
log_info "Setup started at: $SETUP_TIME"
echo ""

# ==================== 環境チェック ====================

log_info "Checking system environment..."

# OS チェック
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    log_success "OS: Linux"
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        log_info "Distribution: $PRETTY_NAME"
    fi
else
    log_error "This script requires Linux. Current OS: $OSTYPE"
    exit 1
fi

# ==================== 依存パッケージチェック ====================

log_info "Checking dependencies..."

MISSING_DEPS=()

if ! check_command git; then
    MISSING_DEPS+=("git")
fi

if ! check_command docker; then
    MISSING_DEPS+=("docker")
fi

if ! check_command docker-compose; then
    MISSING_DEPS+=("docker-compose")
fi

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    log_warning "Missing dependencies: ${MISSING_DEPS[*]}"
    echo ""
    
    if grep -q "Ubuntu\|Debian" /etc/os-release; then
        log_info "Installing missing packages..."
        
        if [[ " ${MISSING_DEPS[*]} " =~ " git " ]]; then
            log_info "Installing git..."
            sudo apt-get update
            sudo apt-get install -y git
        fi
        
        if [[ " ${MISSING_DEPS[*]} " =~ " docker " ]]; then
            log_info "Installing Docker..."
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo usermod -aG docker $USER
            log_warning "Please log out and log in again for docker group to take effect"
        fi
        
        if [[ " ${MISSING_DEPS[*]} " =~ " docker-compose " ]]; then
            log_info "Installing Docker Compose..."
            sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" \
                -o /usr/local/bin/docker-compose
            sudo chmod +x /usr/local/bin/docker-compose
        fi
    else
        log_error "Please install missing dependencies manually"
        exit 1
    fi
fi

# ==================== 出力ディレクトリ作成 ====================

log_info "Creating directories..."

mkdir -p scenarios logs results frontend/{src,public}
chmod -R 755 scenarios logs results
log_success "Directories created"

# ==================== 環境設定ファイル ====================

log_info "Setting up configuration files..."

if [ ! -f .env ]; then
    if [ -f .env.server ]; then
        cp .env.server .env
        log_success ".env created from .env.server"
    else
        log_warning ".env.server not found, skipping .env creation"
    fi
else
    log_warning ".env already exists, skipping"
fi

# ==================== ファイアウォール設定 ====================

log_info "Checking firewall..."

if check_command ufw; then
    log_info "UFW detected"
    
    UFW_STATUS=$(sudo ufw status | grep -i "status" || echo "")
    if [[ $UFW_STATUS == *"inactive"* ]]; then
        log_warning "UFW is inactive"
        read -p "Enable UFW? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo ufw enable
            log_success "UFW enabled"
        fi
    fi
    
    log_info "Allowing required ports..."
    sudo ufw allow 3000/tcp
    sudo ufw allow 8000/tcp
    sudo ufw allow 5037/tcp
    log_success "Ports allowed"
else
    log_warning "UFW not installed, please configure firewall manually"
    log_warning "Allow ports: 3000 (frontend), 8000 (api), 5037 (adb)"
fi

# ==================== Docker イメージビルド ====================

log_info "Building Docker images..."

if [ -f docker-compose-server.yml ]; then
    docker-compose -f docker-compose-server.yml build
    log_success "Docker images built"
else
    log_error "docker-compose-server.yml not found"
    exit 1
fi

# ==================== 起動前チェック ====================

log_info "Pre-startup checks..."

# adb チェック
if check_command adb; then
    log_info "Checking ADB devices..."
    ADB_COUNT=$(adb devices | wc -l)
    if [ $ADB_COUNT -gt 2 ]; then
        log_success "ADB device(s) detected"
        adb devices
    else
        log_warning "No ADB devices detected"
        log_info "Connect Android device via USB and enable USB Debugging"
    fi
fi

# ==================== コンテナ起動 ====================

log_info "Starting containers..."
read -p "Start containers now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker-compose -f docker-compose-server.yml up -d
    log_success "Containers started"
    
    # 起動待機
    log_info "Waiting for services to start..."
    sleep 5
    
    # ヘルスチェック
    log_info "Running health checks..."
    
    BACKEND_HEALTH=$(curl -s http://localhost:8000/health || echo "FAILED")
    if echo "$BACKEND_HEALTH" | grep -q "status"; then
        log_success "Backend is healthy"
    else
        log_warning "Backend health check failed, check logs"
    fi
    
    docker-compose -f docker-compose-server.yml ps
fi

# ==================== セットアップ完了 ====================

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║ Setup Complete!                                           ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# サーバIP取得
SERVER_IP=$(hostname -I | awk '{print $1}')

log_info "Access URLs:"
echo ""
echo -e "  ${YELLOW}Frontend:${NC}      http://$SERVER_IP:3000"
echo -e "  ${YELLOW}API Docs:${NC}      http://$SERVER_IP:8000/api/docs"
echo -e "  ${YELLOW}Health Check:${NC}  http://$SERVER_IP:8000/health"
echo ""

log_info "Useful commands:"
echo ""
echo "  # View logs"
echo "  docker-compose -f docker-compose-server.yml logs -f"
echo ""
echo "  # Stop containers"
echo "  docker-compose -f docker-compose-server.yml stop"
echo ""
echo "  # Restart containers"
echo "  docker-compose -f docker-compose-server.yml restart"
echo ""
echo "  # View container status"
echo "  docker-compose -f docker-compose-server.yml ps"
echo ""

log_success "Setup completed at $(date '+%Y-%m-%d %H:%M:%S')"
log_info "See SERVER_SETUP_GUIDE.md for detailed documentation"
echo ""
