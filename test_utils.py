"""
Test Framework ユーティリティ関数と拡張クラス
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import asdict

logger = logging.getLogger(__name__)


# ==================== テスト結果管理 ====================
class TestResultManager:
    """テスト結果の記録と分析"""
    
    def __init__(self, results_dir: str = "./results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
    
    def save_test_result(self, 
                        session_id: str,
                        scenario_name: str,
                        passed: bool,
                        execution_time: float,
                        context: Dict[str, Any],
                        error: Optional[str] = None):
        """テスト結果をJSON形式で保存"""
        result = {
            "session_id": session_id,
            "scenario_name": scenario_name,
            "passed": passed,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "error": error
        }
        
        result_file = self.results_dir / f"{session_id}_result.json"
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Result saved: {result_file}")
        return result_file
    
    def generate_summary_report(self, 
                               results_dir: Optional[str] = None) -> Dict[str, Any]:
        """全テスト結果のサマリーレポート生成"""
        search_dir = Path(results_dir) if results_dir else self.results_dir
        
        results = []
        for result_file in search_dir.glob("*_result.json"):
            with open(result_file, 'r') as f:
                results.append(json.load(f))
        
        if not results:
            return {"total": 0, "passed": 0, "failed": 0, "summary": []}
        
        summary = {
            "total": len(results),
            "passed": sum(1 for r in results if r["passed"]),
            "failed": sum(1 for r in results if not r["passed"]),
            "pass_rate": sum(1 for r in results if r["passed"]) / len(results) * 100,
            "average_execution_time": sum(r["execution_time"] for r in results) / len(results),
            "results": results
        }
        
        return summary


# ==================== Slack ユーティリティ ====================
class SlackNotificationHelper:
    """Slack 通知ユーティリティ"""
    
    @staticmethod
    def format_test_report_message(test_result: Dict[str, Any]) -> str:
        """テスト結果をSlack用フォーマットに変換"""
        status_emoji = "✅" if test_result["passed"] else "❌"
        
        message = f"""{status_emoji} **Test Result**

*Scenario:* {test_result['scenario_name']}
*Status:* {'PASSED' if test_result['passed'] else 'FAILED'}
*Execution Time:* {test_result['execution_time']:.2f}s
*Timestamp:* {test_result['timestamp']}
*Session ID:* {test_result['session_id']}"""
        
        if test_result.get('error'):
            message += f"\n*Error:* ```{test_result['error']}```"
        
        return message
    
    @staticmethod
    def format_captured_values_message(context: Dict[str, Any]) -> str:
        """キャプチャ値をSlack用フォーマットに変換"""
        message = "*Captured Values:*\n"
        for key, value in context.get('captured_values', {}).items():
            message += f"• `{key}`: {value}\n"
        return message


# ==================== デバイス管理 ====================
class DeviceManager:
    """複数デバイスの管理"""
    
    def __init__(self):
        import subprocess
        self.devices = {}
    
    def list_devices(self) -> List[Dict[str, str]]:
        """接続されたデバイス一覧取得"""
        import subprocess
        
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')[1:]  # ヘッダースキップ
        
        devices = []
        for line in lines:
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    devices.append({
                        'serial': parts[0],
                        'status': parts[1]
                    })
        
        return devices
    
    def get_device_info(self, serial: str) -> Dict[str, str]:
        """デバイス情報取得"""
        import subprocess
        
        info = {}
        props = ['ro.build.version.sdk', 'ro.product.model', 'ro.product.brand']
        
        for prop in props:
            result = subprocess.run(
                ['adb', '-s', serial, 'shell', 'getprop', prop],
                capture_output=True, text=True
            )
            info[prop] = result.stdout.strip()
        
        return info


# ==================== シナリオビルダー ====================
class ScenarioBuilder:
    """YAML をPythonコードで構築するヘルパー"""
    
    def __init__(self, name: str):
        self.scenario = {
            'name': name,
            'variables': {},
            'actions': []
        }
    
    def add_variable(self, key: str, value: str) -> 'ScenarioBuilder':
        """変数を追加"""
        self.scenario['variables'][key] = value
        return self
    
    def add_action(self, 
                   action_type: str,
                   target: Optional[str] = None,
                   value: Optional[str] = None,
                   **kwargs) -> 'ScenarioBuilder':
        """アクションを追加"""
        action = {
            'type': action_type,
            'target': target,
            'value': value,
            **kwargs
        }
        # None 値を除去
        action = {k: v for k, v in action.items() if v is not None}
        self.scenario['actions'].append(action)
        return self
    
    def add_input(self, target: str, value: str, critical: bool = False) -> 'ScenarioBuilder':
        """入力アクション追加"""
        return self.add_action('input', target=target, value=value, critical=critical)
    
    def add_click(self, target: str, critical: bool = False) -> 'ScenarioBuilder':
        """クリックアクション追加"""
        return self.add_action('click', target=target, critical=critical)
    
    def add_wait(self, duration: float) -> 'ScenarioBuilder':
        """待機アクション追加"""
        return self.add_action('wait', duration=duration)
    
    def add_screenshot(self, image_path: str) -> 'ScenarioBuilder':
        """スクリーンショットアクション追加"""
        return self.add_action('screenshot', image_path=image_path)
    
    def add_human_input(self, 
                       slack_channel: str,
                       target: str,
                       description: str,
                       timeout: float = 300) -> 'ScenarioBuilder':
        """人間入力アクション追加"""
        return self.add_action(
            'human_input',
            slack_channel=slack_channel,
            target=target,
            description=description,
            timeout=timeout
        )
    
    def add_switch_app(self, app: str) -> 'ScenarioBuilder':
        """アプリ切り替えアクション追加"""
        return self.add_action('switch_app', target=app)
    
    def build_yaml(self) -> str:
        """YAMLフォーマットで出力"""
        import yaml
        return yaml.dump(self.scenario, allow_unicode=True, default_flow_style=False)
    
    def save(self, filepath: str):
        """YAML ファイルに保存"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.build_yaml())
        logger.info(f"Scenario saved: {filepath}")


# ==================== ログ分析 ====================
class LogAnalyzer:
    """テスト実行ログの分析"""
    
    @staticmethod
    def extract_failures(log_file: str) -> List[Dict[str, str]]:
        """ログからエラーを抽出"""
        failures = []
        
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines):
            if 'ERROR' in line:
                failures.append({
                    'line_number': i + 1,
                    'message': line.strip(),
                    'context': lines[max(0, i-2):min(len(lines), i+3)]
                })
        
        return failures
    
    @staticmethod
    def generate_execution_timeline(log_file: str) -> List[Dict[str, str]]:
        """実行タイムラインを生成"""
        timeline = []
        
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if 'Executing action' in line or 'completed' in line or 'failed' in line:
                    # タイムスタンプとメッセージを抽出
                    parts = line.split(' - ', 1)
                    if len(parts) == 2:
                        timestamp, message = parts
                        timeline.append({
                            'timestamp': timestamp,
                            'message': message.strip()
                        })
        
        return timeline


# ==================== 使用例 ====================
if __name__ == '__main__':
    # シナリオをPythonコードで構築
    builder = ScenarioBuilder("Python-Built Scenario")
    
    scenario = (builder
        .add_variable('email', 'test@example.com')
        .add_variable('password', 'secret123')
        .add_switch_app('app1')
        .add_wait(2)
        .add_screenshot('initial_screen.png')
        .add_input('com.example.app:id/email', '${email}')
        .add_input('com.example.app:id/password', '${password}')
        .add_click('com.example.app:id/login_button', critical=True)
        .add_wait(3)
        .add_screenshot('auth_screen.png')
        .add_human_input(
            slack_channel='#test-automation',
            target='com.example.app:id/code_field',
            description='画面のコードを入力してください',
            timeout=600
        )
        .add_click('com.example.app:id/verify_button', critical=True)
        .add_screenshot('final_screen.png')
    )
    
    # YAML保存
    scenario.save('generated_scenario.yaml')
    
    # テスト結果管理の例
    result_manager = TestResultManager()
    result_manager.save_test_result(
        session_id='test_001',
        scenario_name='Python-Built Scenario',
        passed=True,
        execution_time=45.2,
        context={'email': 'test@example.com'},
        error=None
    )
    
    # サマリーレポート
    summary = result_manager.generate_summary_report()
    print(json.dumps(summary, indent=2, ensure_ascii=False))
