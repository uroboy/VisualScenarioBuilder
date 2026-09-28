"""
Visual Scenario Builder - FastAPI Backend
デバイス制御、画面キャプチャ、UI要素識別
"""

import asyncio
import base64
import json
import logging
import os
import shutil
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict

from fastapi import FastAPI, WebSocket, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse
import aiofiles
import cv2
import numpy as np
from PIL import Image
import xml.etree.ElementTree as ET

from test_utils import TestResultManager
from report_generator import HTMLReportGenerator

# ==================== ロギング ====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Visual Scenario Builder API")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== データクラス ====================
@dataclass
class Device:
    serial: str
    name: str
    connected: bool
    model: Optional[str] = None
    android_version: Optional[str] = None


@dataclass
class UIElement:
    """UI要素情報"""
    id: str
    resource_id: str
    class_name: str
    text: str
    bounds: Dict[str, int]  # x1, y1, x2, y2
    clickable: bool
    depth: int


# ==================== Android SDK パス解決 ====================
ANDROID_SDK_ROOT = os.getenv('ANDROID_SDK_ROOT') or os.getenv('ANDROID_HOME') or os.path.expanduser('~/android-sdk')


def _sdk_tool(*relative_path: str) -> str:
    """SDK配下のツールパスを解決。見つからなければPATH上のコマンド名にフォールバック"""
    candidate = os.path.join(ANDROID_SDK_ROOT, *relative_path)
    if os.path.exists(candidate):
        return candidate
    return shutil.which(relative_path[-1]) or relative_path[-1]


EMULATOR_BIN = _sdk_tool('emulator', 'emulator')
AVDMANAGER_BIN = _sdk_tool('cmdline-tools', 'latest', 'bin', 'avdmanager')
ADB_BIN = shutil.which('adb') or _sdk_tool('platform-tools', 'adb')
XVFB_RUN_BIN = shutil.which('xvfb-run')


# ==================== Android仮想デバイス(AVD)管理 ====================
class EmulatorManager:
    """AVDの一覧取得・起動・停止（KVMなど実行環境に依存）"""

    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}

    def list_avds(self) -> List[str]:
        """作成済みAVD名の一覧"""
        try:
            result = subprocess.run(
                [EMULATOR_BIN, '-list-avds'],
                capture_output=True, text=True, timeout=10
            )
            return [line.strip() for line in result.stdout.splitlines() if line.strip()]
        except Exception as e:
            logger.error(f"Failed to list AVDs: {e}")
            return []

    def start_avd(self, name: str) -> Dict[str, Any]:
        """AVDをヘッドレス起動（起動完了はadb devicesで別途確認が必要）"""
        existing = self.processes.get(name)
        if existing and existing.poll() is None:
            return {"success": False, "error": f"'{name}' はすでに起動処理中です"}

        cmd = [
            EMULATOR_BIN, '-avd', name,
            '-no-window', '-no-audio', '-no-boot-anim',
            '-gpu', 'swiftshader_indirect',
            '-accel', 'auto',
        ]
        if XVFB_RUN_BIN:
            # ヘッドレスLinuxではSwiftShaderがX11ライブラリのロードを試みてクラッシュするため、
            # 仮想ディスプレイ(Xvfb)の下で起動する（-no-window指定でも必要）
            cmd = [XVFB_RUN_BIN, '-a'] + cmd
        else:
            logger.warning("xvfb-run not found - emulator may crash on a headless Linux host without a display")

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,  # 呼び出し元プロセスのセッション終了に巻き込まれないようにする
            )
            self.processes[name] = proc
            logger.info(f"Starting emulator '{name}' (pid={proc.pid})")
            return {"success": True, "pid": proc.pid}
        except FileNotFoundError:
            logger.error(f"emulator binary not found at {EMULATOR_BIN}")
            return {"success": False, "error": "emulator コマンドが見つかりません（Android SDKが未インストール）"}
        except Exception as e:
            logger.error(f"Failed to start AVD '{name}': {e}")
            return {"success": False, "error": str(e)}

    def stop(self, serial: str) -> bool:
        """稼働中のエミュレータをシリアル指定で停止"""
        try:
            subprocess.run([ADB_BIN, '-s', serial, 'emu', 'kill'], timeout=5, capture_output=True)
            return True
        except Exception as e:
            logger.error(f"Failed to stop emulator {serial}: {e}")
            return False

    def process_status(self) -> Dict[str, Dict[str, Any]]:
        """起動を試みたAVDプロセスの生死状態（終了コードも含める）"""
        status = {}
        for name, proc in self.processes.items():
            returncode = proc.poll()
            if returncode is None:
                status[name] = {"state": "running"}
            elif returncode == 0:
                status[name] = {"state": "exited", "returncode": returncode}
            else:
                status[name] = {"state": "crashed", "returncode": returncode}
        return status


# ==================== デバイス管理 ====================
class DeviceManager:
    """ADB デバイス管理"""
    
    def __init__(self):
        self.devices: Dict[str, Device] = {}
        self.selected_device: Optional[str] = None
    
    def refresh_devices(self) -> List[Device]:
        """接続デバイスを更新"""
        try:
            result = subprocess.run(
                ['adb', 'devices', '-l'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            self.devices = {}
            for line in result.stdout.strip().split('\n')[1:]:
                if not line.strip():
                    continue
                
                parts = line.split()
                if len(parts) >= 2:
                    serial = parts[0]
                    status = parts[1]
                    
                    if status == 'device':
                        device = Device(
                            serial=serial,
                            name=self._get_device_name(serial),
                            connected=True,
                            model=self._get_device_prop(serial, 'ro.product.model'),
                            android_version=self._get_device_prop(serial, 'ro.build.version.release')
                        )
                        self.devices[serial] = device
            
            logger.info(f"Found {len(self.devices)} devices")
            return list(self.devices.values())
        
        except Exception as e:
            logger.error(f"Failed to refresh devices: {e}")
            return []
    
    def _get_device_name(self, serial: str) -> str:
        """デバイス名取得"""
        try:
            result = subprocess.run(
                ['adb', '-s', serial, 'shell', 'getprop', 'ro.product.model'],
                capture_output=True,
                text=True,
                timeout=3
            )
            return result.stdout.strip() or serial
        except:
            return serial
    
    def _get_device_prop(self, serial: str, prop: str) -> Optional[str]:
        """デバイスプロパティ取得"""
        try:
            result = subprocess.run(
                ['adb', '-s', serial, 'shell', 'getprop', prop],
                capture_output=True,
                text=True,
                timeout=3
            )
            return result.stdout.strip() or None
        except:
            return None
    
    def select_device(self, serial: str) -> bool:
        """デバイス選択"""
        if serial in self.devices:
            self.selected_device = serial
            logger.info(f"Selected device: {serial}")
            return True
        return False


# ==================== 画面キャプチャと要素解析 ====================
class ScreenCapture:
    """画面キャプチャと要素識別"""
    
    def __init__(self, device_serial: str):
        self.device_serial = device_serial
        self.last_screenshot_path: Optional[str] = None
        self.ui_elements: List[UIElement] = []
    
    def capture_screen(self) -> Optional[bytes]:
        """スクリーンショット取得"""
        try:
            # adb screencap で画像取得
            result = subprocess.run(
                ['adb', '-s', self.device_serial, 'exec-out', 'screencap', '-p'],
                capture_output=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                logger.error(f"screencap failed: {result.stderr.decode()}")
                return None
        
        except Exception as e:
            logger.error(f"Failed to capture screen: {e}")
            return None
    
    def capture_and_analyze(self) -> Dict[str, Any]:
        """スクリーンショット取得 + UI要素解析"""
        screenshot_bytes = self.capture_screen()
        if not screenshot_bytes:
            return {"success": False, "error": "Failed to capture screen"}
        
        # Base64エンコード
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        
        # UI要素を取得
        ui_elements = self._analyze_ui_elements()
        
        return {
            "success": True,
            "screenshot": f"data:image/png;base64,{screenshot_base64}",
            "elements": [asdict(elem) for elem in ui_elements],
            "timestamp": datetime.now().isoformat()
        }
    
    def _analyze_ui_elements(self) -> List[UIElement]:
        """UI階層をダンプして要素を抽出"""
        try:
            # UI階層を /sdcard にダンプ
            subprocess.run(
                ['adb', '-s', self.device_serial, 'shell', 'uiautomator', 'dump', '/sdcard/dump.xml'],
                timeout=5,
                capture_output=True
            )
            
            # ダンプファイルをローカルに取得
            dump_path = '/tmp/dump.xml'
            subprocess.run(
                ['adb', '-s', self.device_serial, 'pull', '/sdcard/dump.xml', dump_path],
                timeout=5,
                capture_output=True
            )
            
            # XMLを解析
            return self._parse_ui_hierarchy(dump_path)
        
        except Exception as e:
            logger.error(f"Failed to analyze UI elements: {e}")
            return []
    
    def _parse_ui_hierarchy(self, xml_path: str) -> List[UIElement]:
        """UI階層XMLを解析"""
        elements = []
        
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            def parse_node(node, depth=0):
                # 属性を取得
                attribs = node.attrib
                
                # bounds をパース
                bounds_str = attribs.get('bounds', '')
                bounds = self._parse_bounds(bounds_str)
                
                if bounds:
                    element = UIElement(
                        id=f"elem_{len(elements)}",
                        resource_id=attribs.get('resource-id', ''),
                        class_name=attribs.get('class', ''),
                        text=attribs.get('text', ''),
                        bounds=bounds,
                        clickable=attribs.get('clickable', 'false').lower() == 'true',
                        depth=depth
                    )
                    elements.append(element)
                
                # 子ノードを再帰処理
                for child in node:
                    parse_node(child, depth + 1)
            
            parse_node(root)
            logger.info(f"Found {len(elements)} UI elements")
            self.ui_elements = elements
            return elements
        
        except Exception as e:
            logger.error(f"Failed to parse UI hierarchy: {e}")
            return []
    
    @staticmethod
    def _parse_bounds(bounds_str: str) -> Optional[Dict[str, int]]:
        """bounds 文字列を解析 "[x1,y1][x2,y2]" """
        try:
            if not bounds_str:
                return None
            
            # "[100,200][300,400]" -> [[100,200],[300,400]]
            bounds_str = bounds_str.replace('[', '').replace(']', ',')
            coords = [int(x) for x in bounds_str.split(',') if x]
            
            if len(coords) == 4:
                return {
                    'x1': coords[0],
                    'y1': coords[1],
                    'x2': coords[2],
                    'y2': coords[3]
                }
        except:
            pass
        
        return None


# ==================== タップシミュレーション ====================
class TapSimulator:
    """タップとジェスチャーのシミュレーション"""
    
    def __init__(self, device_serial: str):
        self.device_serial = device_serial
    
    def tap(self, x: int, y: int) -> bool:
        """指定座標をタップ"""
        try:
            subprocess.run(
                ['adb', '-s', self.device_serial, 'shell', 'input', 'tap', str(x), str(y)],
                timeout=5,
                capture_output=True
            )
            logger.info(f"Tapped at ({x}, {y})")
            return True
        except Exception as e:
            logger.error(f"Failed to tap: {e}")
            return False
    
    def long_press(self, x: int, y: int, duration: int = 1000) -> bool:
        """長押し"""
        try:
            subprocess.run(
                ['adb', '-s', self.device_serial, 'shell', 'input', 'swipe',
                 str(x), str(y), str(x), str(y), str(duration)],
                timeout=5,
                capture_output=True
            )
            logger.info(f"Long pressed at ({x}, {y}) for {duration}ms")
            return True
        except Exception as e:
            logger.error(f"Failed to long press: {e}")
            return False
    
    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 500) -> bool:
        """スワイプ"""
        try:
            subprocess.run(
                ['adb', '-s', self.device_serial, 'shell', 'input', 'swipe',
                 str(x1), str(y1), str(x2), str(y2), str(duration)],
                timeout=5,
                capture_output=True
            )
            logger.info(f"Swiped from ({x1}, {y1}) to ({x2}, {y2})")
            return True
        except Exception as e:
            logger.error(f"Failed to swipe: {e}")
            return False
    
    def input_text(self, text: str) -> bool:
        """テキスト入力"""
        try:
            # 特殊文字をエスケープ
            escaped_text = text.replace('"', '\\"')
            subprocess.run(
                ['adb', '-s', self.device_serial, 'shell', 'input', 'text', escaped_text],
                timeout=5,
                capture_output=True
            )
            logger.info(f"Input text: {text}")
            return True
        except Exception as e:
            logger.error(f"Failed to input text: {e}")
            return False


# ==================== グローバルインスタンス ====================
device_manager = DeviceManager()
emulator_manager = EmulatorManager()
screen_capture_map: Dict[str, ScreenCapture] = {}
tap_simulator_map: Dict[str, TapSimulator] = {}
scenario_runs: Dict[str, Dict[str, Any]] = {}

# ==================== REST API エンドポイント ====================

@app.get("/api/devices")
async def get_devices():
    """接続デバイス一覧"""
    devices = device_manager.refresh_devices()
    return {
        "devices": [asdict(d) for d in devices],
        "selected": device_manager.selected_device
    }


@app.post("/api/devices/{serial}/select")
async def select_device(serial: str):
    """デバイスを選択"""
    if device_manager.select_device(serial):
        # 初期化
        screen_capture_map[serial] = ScreenCapture(serial)
        tap_simulator_map[serial] = TapSimulator(serial)
        return {"success": True, "serial": serial}
    else:
        raise HTTPException(status_code=404, detail="Device not found")


@app.get("/api/screen")
async def get_screen():
    """現在の画面を取得"""
    serial = device_manager.selected_device
    if not serial:
        raise HTTPException(status_code=400, detail="No device selected")
    
    if serial not in screen_capture_map:
        screen_capture_map[serial] = ScreenCapture(serial)
    
    capture = screen_capture_map[serial]
    result = capture.capture_and_analyze()
    
    return result


@app.post("/api/tap")
async def tap(x: int, y: int):
    """画面をタップ"""
    serial = device_manager.selected_device
    if not serial:
        raise HTTPException(status_code=400, detail="No device selected")
    
    if serial not in tap_simulator_map:
        tap_simulator_map[serial] = TapSimulator(serial)
    
    simulator = tap_simulator_map[serial]
    success = simulator.tap(x, y)
    
    # タップ後の画面を取得
    await asyncio.sleep(0.5)
    if serial not in screen_capture_map:
        screen_capture_map[serial] = ScreenCapture(serial)
    
    capture = screen_capture_map[serial]
    result = capture.capture_and_analyze()
    
    return {
        "tap_success": success,
        **result
    }


@app.post("/api/input")
async def input_text(text: str):
    """テキスト入力"""
    serial = device_manager.selected_device
    if not serial:
        raise HTTPException(status_code=400, detail="No device selected")
    
    if serial not in tap_simulator_map:
        tap_simulator_map[serial] = TapSimulator(serial)
    
    simulator = tap_simulator_map[serial]
    success = simulator.input_text(text)
    
    # 入力後の画面を取得
    await asyncio.sleep(0.3)
    if serial not in screen_capture_map:
        screen_capture_map[serial] = ScreenCapture(serial)
    
    capture = screen_capture_map[serial]
    result = capture.capture_and_analyze()
    
    return {
        "input_success": success,
        **result
    }


@app.post("/api/swipe")
async def swipe(x1: int, y1: int, x2: int, y2: int, duration: int = 500):
    """スワイプ"""
    serial = device_manager.selected_device
    if not serial:
        raise HTTPException(status_code=400, detail="No device selected")
    
    if serial not in tap_simulator_map:
        tap_simulator_map[serial] = TapSimulator(serial)
    
    simulator = tap_simulator_map[serial]
    success = simulator.swipe(x1, y1, x2, y2, duration)
    
    await asyncio.sleep(0.5)
    if serial not in screen_capture_map:
        screen_capture_map[serial] = ScreenCapture(serial)
    
    capture = screen_capture_map[serial]
    result = capture.capture_and_analyze()
    
    return {
        "swipe_success": success,
        **result
    }


@app.get("/api/elements")
async def get_elements():
    """現在の画面のUI要素を取得"""
    serial = device_manager.selected_device
    if not serial:
        raise HTTPException(status_code=400, detail="No device selected")
    
    if serial not in screen_capture_map:
        screen_capture_map[serial] = ScreenCapture(serial)
    
    capture = screen_capture_map[serial]
    elements = capture._analyze_ui_elements()
    
    return {
        "elements": [asdict(elem) for elem in elements],
        "count": len(elements)
    }


@app.post("/api/scenario/save")
async def save_scenario(scenario: Dict[str, Any]):
    """シナリオをYAMLで保存"""
    import yaml
    
    try:
        scenarios_dir = Path("./scenarios")
        scenarios_dir.mkdir(exist_ok=True)
        
        filename = scenario.get('name', 'scenario').replace(' ', '_')
        filepath = scenarios_dir / f"{filename}.yaml"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(scenario, f, allow_unicode=True, default_flow_style=False)
        
        logger.info(f"Scenario saved: {filepath}")
        return {"success": True, "path": str(filepath)}
    
    except Exception as e:
        logger.error(f"Failed to save scenario: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _execute_scenario(run_id: str, serial: str, scenario_name: str, actions: List[Dict[str, Any]]):
    """バックグラウンドでシナリオを1ステップずつ実行し、scenario_runs[run_id] に進捗を書き込む"""
    simulator = tap_simulator_map[serial]
    capture = screen_capture_map[serial]
    run = scenario_runs[run_id]
    start_time = time.time()
    error_message: Optional[str] = None

    for idx, action in enumerate(actions):
        action_type = action.get('type')
        step: Dict[str, Any] = {"index": idx, "type": action_type}

        try:
            if action_type == 'click':
                x, y = action.get('x'), action.get('y')
                if x is None or y is None:
                    step["success"] = False
                    step["message"] = "座標情報がありません（要素をクリックして追加したアクションのみ実行できます）"
                else:
                    step["success"] = simulator.tap(int(x), int(y))

            elif action_type == 'input':
                x, y = action.get('x'), action.get('y')
                if x is not None and y is not None:
                    simulator.tap(int(x), int(y))
                    await asyncio.sleep(0.3)
                step["success"] = simulator.input_text(action.get('value') or '')

            elif action_type == 'swipe':
                required = ['x1', 'y1', 'x2', 'y2']
                if any(action.get(k) is None for k in required):
                    step["success"] = False
                    step["message"] = "スワイプ座標情報がありません"
                else:
                    step["success"] = simulator.swipe(
                        int(action['x1']), int(action['y1']),
                        int(action['x2']), int(action['y2'])
                    )

            elif action_type == 'wait':
                await asyncio.sleep(float(action.get('duration') or 1))
                step["success"] = True

            elif action_type == 'screenshot':
                step["success"] = True  # 実際のキャプチャは下の共通処理で行う

            else:
                step["success"] = False
                step["message"] = f"このアプリでは未対応のアクションタイプです: {action_type}"

            await asyncio.sleep(0.3)  # アクション間の待機

        except Exception as e:
            step["success"] = False
            step["message"] = str(e)

        # ステップ実行のたびに画面を取得し、進捗としてすぐ参照できるようにする
        try:
            shot = capture.capture_and_analyze()
            if shot.get("success"):
                step["screenshot"] = shot["screenshot"]
                run["screenshot"] = shot["screenshot"]
                run["elements"] = shot.get("elements", [])
        except Exception as e:
            logger.error(f"Failed to capture screen after step {idx}: {e}")

        run["steps"].append(step)
        run["current"] = idx

        if not step["success"] and action.get('critical'):
            error_message = f"ステップ{idx + 1}（{action_type}）で失敗したため中断しました"
            break

    passed = len(run["steps"]) > 0 and all(s["success"] for s in run["steps"])
    execution_time = time.time() - start_time

    result_manager = TestResultManager("./results")
    result_manager.save_test_result(
        session_id=run_id,
        scenario_name=scenario_name,
        passed=passed,
        execution_time=execution_time,
        context={"steps": run["steps"]},
        error=error_message
    )

    run["status"] = "done"
    run["success"] = passed
    run["execution_time"] = execution_time
    run["error"] = error_message


@app.post("/api/scenario/run")
async def run_scenario(scenario: Dict[str, Any]):
    """シナリオの実行をバックグラウンドで開始する（進捗は /api/scenario/run/{run_id}/status で取得）"""
    serial = device_manager.selected_device
    if not serial:
        raise HTTPException(status_code=400, detail="No device selected")

    if serial not in tap_simulator_map:
        tap_simulator_map[serial] = TapSimulator(serial)
    if serial not in screen_capture_map:
        screen_capture_map[serial] = ScreenCapture(serial)

    scenario_name = scenario.get('name', 'Unnamed Scenario')
    actions = scenario.get('actions', [])
    run_id = f"ui_{int(time.time() * 1000)}"

    scenario_runs[run_id] = {
        "status": "running",
        "current": -1,
        "total": len(actions),
        "steps": [],
        "screenshot": None,
        "elements": [],
        "scenario_name": scenario_name,
    }

    asyncio.create_task(_execute_scenario(run_id, serial, scenario_name, actions))

    return {"run_id": run_id, "status": "running", "total": len(actions)}


@app.get("/api/scenario/run/{run_id}/status")
async def get_scenario_run_status(run_id: str):
    """実行中/完了したシナリオ実行の進捗を取得する"""
    run = scenario_runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


# ==================== テスト結果レポート ====================
@app.get("/api/reports/summary")
async def get_reports_summary():
    """テスト結果のサマリー（JSON）を取得"""
    result_manager = TestResultManager("./results")
    return result_manager.generate_summary_report()


@app.get("/api/reports/html", response_class=HTMLResponse)
async def get_reports_html():
    """テスト結果レポート（HTML）を取得"""
    generator = HTMLReportGenerator("./results")
    return generator.render_html()


# ==================== Android仮想デバイス(AVD) ====================
@app.get("/api/emulator/avds")
async def list_avds():
    """作成済みAVD一覧"""
    return {"avds": emulator_manager.list_avds(), "status": emulator_manager.process_status()}


@app.post("/api/emulator/{name}/start")
async def start_emulator(name: str):
    """AVDをヘッドレスで起動（起動完了までは数分〜要求環境によってはそれ以上かかる）"""
    result = emulator_manager.start_avd(name)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "起動に失敗しました"))
    return result


@app.post("/api/emulator/stop")
async def stop_emulator(serial: str):
    """稼働中のエミュレータを停止"""
    success = emulator_manager.stop(serial)
    return {"success": success}


# ==================== WebSocket（リアルタイム更新） ====================
@app.websocket("/api/ws/screen")
async def websocket_screen(websocket: WebSocket):
    """リアルタイム画面ストリーミング"""
    await websocket.accept()
    
    try:
        while True:
            serial = device_manager.selected_device
            if not serial:
                await websocket.send_json({"error": "No device selected"})
                await asyncio.sleep(1)
                continue
            
            if serial not in screen_capture_map:
                screen_capture_map[serial] = ScreenCapture(serial)
            
            capture = screen_capture_map[serial]
            result = capture.capture_and_analyze()
            
            await websocket.send_json(result)
            await asyncio.sleep(1)  # 1秒ごとに更新
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()


# ==================== ヘルスチェック ====================
@app.get("/health")
async def health():
    """ヘルスチェック"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
