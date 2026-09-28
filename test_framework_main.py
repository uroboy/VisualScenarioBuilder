"""
Multi-App Test Orchestrator with Slack Integration
複数アプリ対応の自動テストフレームワーク
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable

import uiautomator2 as u2
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import pytesseract
from PIL import Image
import yaml


# ==================== ロギング設定 ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_framework.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ==================== データクラス ====================
class ActionType(Enum):
    CLICK = "click"
    INPUT = "input"
    SCREENSHOT = "screenshot"
    WAIT = "wait"
    HUMAN_INPUT = "human_input"  # Slack経由で人間入力待ち
    IMAGE_RECOGNIZE = "image_recognize"
    NOTIFY = "notify"
    SWITCH_APP = "switch_app"


@dataclass
class TestAction:
    """テストアクション定義"""
    action_type: ActionType
    target: Optional[str] = None
    value: Optional[str] = None
    duration: Optional[float] = None
    image_path: Optional[str] = None
    slack_channel: Optional[str] = None
    timeout: Optional[float] = 300  # デフォルト5分


@dataclass
class TestContext:
    """テスト実行コンテキスト"""
    session_id: str
    current_app: Optional[str] = None
    captured_values: Dict[str, Any] = None
    slack_thread_ts: Optional[str] = None
    start_time: datetime = None
    
    def __post_init__(self):
        if self.captured_values is None:
            self.captured_values = {}
        if self.start_time is None:
            self.start_time = datetime.now()


@dataclass
class HumanInputRequest:
    """人間入力リクエスト"""
    request_id: str
    app_name: str
    description: str
    image_data: Optional[bytes] = None
    expected_field: Optional[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


# ==================== UIオートメーション層 ====================
class UIAutomationEngine:
    """UIAutomation操作をカプセル化"""
    
    def __init__(self, device_id: Optional[str] = None):
        """
        Args:
            device_id: adbデバイスID。Noneの場合は最初に接続されたデバイス
        """
        try:
            self.device = u2.connect(device_id)
            self.device_id = device_id or self.device.serial
            logger.info(f"Device connected: {self.device_id}")
        except Exception as e:
            logger.error(f"Failed to connect to device: {e}")
            raise
    
    def click(self, target: str) -> bool:
        """要素をクリック (resourceId または text で指定可能)"""
        try:
            if target.startswith("text:"):
                self.device(text=target[5:]).click()
            else:
                self.device(resourceId=target).click()
            logger.info(f"Clicked: {target}")
            return True
        except Exception as e:
            logger.error(f"Failed to click {target}: {e}")
            return False
    
    def input_text(self, target: str, text: str) -> bool:
        """テキスト入力"""
        try:
            element = self.device(resourceId=target)
            element.click()
            element.clear_text()
            element.send_keys(text)
            logger.info(f"Input to {target}: {text}")
            return True
        except Exception as e:
            logger.error(f"Failed to input text to {target}: {e}")
            return False
    
    def screenshot(self, filename: str) -> bool:
        """スクリーンショット取得"""
        try:
            self.device.screenshot(filename)
            logger.info(f"Screenshot saved: {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return False
    
    def wait(self, duration: float):
        """待機"""
        time.sleep(duration)
        logger.info(f"Waited {duration} seconds")
    
    def get_current_activity(self) -> str:
        """現在のActivity名を取得"""
        return self.device.current_activity()
    
    def find_element_exists(self, target: str, timeout: float = 10) -> bool:
        """要素が存在するまで待機"""
        try:
            self.device(resourceId=target).wait(timeout=timeout)
            return True
        except Exception:
            return False


# ==================== Slack連携層 ====================
class SlackIntegration:
    """Slack API連携"""
    
    def __init__(self, bot_token: str, default_channel: str):
        self.client = WebClient(token=bot_token)
        self.default_channel = default_channel
        self.pending_requests: Dict[str, HumanInputRequest] = {}
    
    def notify_with_image(self, 
                         channel: str,
                         message: str,
                         image_path: str,
                         request_id: Optional[str] = None) -> Optional[str]:
        """画像付きで通知。スレッドIDを返す"""
        try:
            with open(image_path, 'rb') as f:
                response = self.client.files_upload_v2(
                    channel=channel,
                    file=f,
                    initial_comment=message,
                    filename=Path(image_path).name
                )
            
            thread_ts = response.get('file', {}).get('shares', {}).get('public', [{
                'ts': None
            }])[0]['ts']
            
            # Slackのメッセージスレッドを取得（別途実装）
            logger.info(f"Notified Slack with image: {image_path}")
            return thread_ts
        except SlackApiError as e:
            logger.error(f"Slack API error: {e}")
            return None
    
    def post_to_thread(self, channel: str, thread_ts: str, message: str) -> bool:
        """スレッドにポスト"""
        try:
            self.client.chat_postMessage(
                channel=channel,
                thread_ts=thread_ts,
                text=message
            )
            logger.info(f"Posted to thread: {thread_ts}")
            return True
        except SlackApiError as e:
            logger.error(f"Failed to post to thread: {e}")
            return False
    
    def listen_for_responses(self, 
                            channel: str,
                            thread_ts: str,
                            timeout: float = 300) -> Optional[str]:
        """スレッドの新しいメッセージを待機（タイムアウト付き）"""
        start_time = time.time()
        last_check = float(thread_ts)
        
        while time.time() - start_time < timeout:
            try:
                result = self.client.conversations_replies(
                    channel=channel,
                    ts=thread_ts,
                    limit=10
                )
                
                for msg in result['messages']:
                    msg_ts = float(msg['ts'])
                    # ボット自身のメッセージは除外
                    if msg_ts > last_check and not msg.get('bot_id'):
                        last_check = msg_ts
                        return msg['text']
                
                time.sleep(2)  # ポーリング間隔
            except SlackApiError as e:
                logger.error(f"Error listening for responses: {e}")
        
        logger.warning(f"Timeout waiting for response in thread {thread_ts}")
        return None


# ==================== 画像認識層 ====================
class ImageRecognition:
    """画像からの情報抽出"""
    
    @staticmethod
    def extract_text(image_path: str) -> str:
        """OCR: 画像からテキスト抽出"""
        try:
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img, lang='jpn+eng')
            logger.info(f"Extracted text from {image_path}")
            return text
        except Exception as e:
            logger.error(f"Failed to extract text: {e}")
            return ""
    
    @staticmethod
    def detect_objects(image_path: str, object_type: str) -> List[Dict[str, Any]]:
        """
        物体検出（例: QRコード、テキストボックス）
        実装例：YOLO, OpenCV等を使用
        """
        # プレースホルダー実装
        logger.info(f"Detecting {object_type} in {image_path}")
        return []


# ==================== テスト実行エンジン ====================
class TestExecutionEngine:
    """テスト実行のメインエンジン"""
    
    def __init__(self, 
                 ui_engine: UIAutomationEngine,
                 slack: SlackIntegration,
                 device_config: Dict[str, str]):
        self.ui = ui_engine
        self.slack = slack
        self.device_config = device_config  # アプリパッケージ名のマッピング
        self.context: Optional[TestContext] = None
    
    async def execute_scenario(self, 
                               scenario_path: str,
                               session_id: str) -> bool:
        """シナリオをYAMLから読み込んで実行"""
        self.context = TestContext(session_id=session_id)
        
        try:
            with open(scenario_path, 'r', encoding='utf-8') as f:
                scenario = yaml.safe_load(f)
            
            logger.info(f"Starting scenario: {scenario.get('name')}")
            actions = scenario.get('actions', [])
            
            for idx, action_def in enumerate(actions):
                logger.info(f"Executing action {idx + 1}/{len(actions)}: {action_def}")
                
                action = self._parse_action(action_def)
                success = await self._execute_action(action)
                
                if not success and action_def.get('critical', False):
                    logger.error(f"Critical action failed, aborting")
                    return False
                
                time.sleep(0.5)  # アクション間の待機
            
            logger.info("Scenario completed successfully")
            return True
        
        except Exception as e:
            logger.error(f"Scenario execution failed: {e}")
            return False
    
    def _parse_action(self, action_def: Dict[str, Any]) -> TestAction:
        """辞書からTestActionを生成"""
        action_type = ActionType(action_def['type'])
        return TestAction(
            action_type=action_type,
            target=action_def.get('target'),
            value=action_def.get('value'),
            duration=action_def.get('duration'),
            image_path=action_def.get('image_path'),
            slack_channel=action_def.get('slack_channel'),
            timeout=action_def.get('timeout', 300)
        )
    
    async def _execute_action(self, action: TestAction) -> bool:
        """アクションを実行"""
        try:
            if action.action_type == ActionType.CLICK:
                return self.ui.click(action.target)
            
            elif action.action_type == ActionType.INPUT:
                return self.ui.input_text(action.target, action.value)
            
            elif action.action_type == ActionType.SCREENSHOT:
                return self.ui.screenshot(action.image_path or f"screen_{int(time.time())}.png")
            
            elif action.action_type == ActionType.WAIT:
                self.ui.wait(action.duration)
                return True
            
            elif action.action_type == ActionType.SWITCH_APP:
                # アプリ切り替え実装
                package = self.device_config.get(action.target)
                if package:
                    self.ui.device.app_start(package)
                    self.context.current_app = action.target
                    return True
                return False
            
            elif action.action_type == ActionType.SCREENSHOT:
                # スクリーンショット + 画像認識 + Slack通知
                screenshot_path = action.image_path or f"capture_{int(time.time())}.png"
                self.ui.screenshot(screenshot_path)
                
                # 画像をSlackで通知して人間入力を待つ
                if action.slack_channel:
                    return await self._handle_human_input(
                        channel=action.slack_channel,
                        image_path=screenshot_path,
                        target_field=action.target,
                        timeout=action.timeout
                    )
                return True
            
            elif action.action_type == ActionType.HUMAN_INPUT:
                # Slack経由で人間入力を待機
                return await self._handle_human_input(
                    channel=action.slack_channel,
                    description=action.value,
                    target_field=action.target,
                    timeout=action.timeout
                )
            
            else:
                logger.warning(f"Unknown action type: {action.action_type}")
                return False
        
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return False
    
    async def _handle_human_input(self,
                                  channel: str,
                                  image_path: Optional[str] = None,
                                  description: Optional[str] = None,
                                  target_field: Optional[str] = None,
                                  timeout: float = 300) -> bool:
        """Slack経由で人間からの入力を待機して取得"""
        request_id = f"req_{int(time.time())}"
        
        # メッセージ作成
        message = f":information_source: **Manual Input Required**\n"
        if description:
            message += f"説明: {description}\n"
        message += f"Request ID: {request_id}"
        
        # 画像があれば添付
        thread_ts = None
        if image_path:
            thread_ts = self.slack.notify_with_image(
                channel=channel,
                message=message,
                image_path=image_path,
                request_id=request_id
            )
        else:
            # テキストのみ
            response = self.slack.client.chat_postMessage(
                channel=channel,
                text=message
            )
            thread_ts = response['ts']
        
        if not thread_ts:
            logger.error("Failed to notify Slack")
            return False
        
        # ユーザーの応答を待機
        response_text = self.slack.listen_for_responses(
            channel=channel,
            thread_ts=thread_ts,
            timeout=timeout
        )
        
        if response_text:
            # 取得した応答をアプリに入力
            if target_field:
                self.context.captured_values[target_field] = response_text
                return self.ui.input_text(target_field, response_text)
            else:
                self.context.captured_values[request_id] = response_text
                return True
        
        return False


# ==================== メイン実行 ====================
async def main():
    """使用例"""
    import os
    
    # 環境変数から取得
    SLACK_TOKEN = os.getenv('SLACK_BOT_TOKEN')
    SLACK_CHANNEL = os.getenv('SLACK_CHANNEL', '#test-automation')
    
    if not SLACK_TOKEN:
        logger.error("SLACK_BOT_TOKEN environment variable not set")
        return
    
    # エンジン初期化
    ui_engine = UIAutomationEngine()
    slack = SlackIntegration(SLACK_TOKEN, SLACK_CHANNEL)
    
    device_config = {
        "app1": "com.example.app1",
        "app2": "com.example.app2"
    }
    
    executor = TestExecutionEngine(ui_engine, slack, device_config)
    
    # シナリオ実行
    success = await executor.execute_scenario(
        scenario_path='test_scenario.yaml',
        session_id='test_001'
    )
    
    print(f"Test result: {'PASSED' if success else 'FAILED'}")


if __name__ == '__main__':
    asyncio.run(main())
