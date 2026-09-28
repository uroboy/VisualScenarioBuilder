#!/bin/bash

set -e

# ADBデーモン開始
echo "Starting ADB daemon..."
adb start-server

# 接続されたデバイスを確認
echo "Connected devices:"
adb devices

# 環境変数チェック
if [ -z "$SLACK_BOT_TOKEN" ]; then
    echo "WARNING: SLACK_BOT_TOKEN is not set"
fi

# テストシナリオ実行
if [ -z "$TEST_SCENARIO" ]; then
    echo "No TEST_SCENARIO specified, using default: test_scenario_example.yaml"
    TEST_SCENARIO="test_scenario_example.yaml"
fi

echo "Running test scenario: $TEST_SCENARIO"
python test_framework_main.py

exec "$@"
