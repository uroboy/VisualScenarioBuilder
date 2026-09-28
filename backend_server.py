"""
Visual Scenario Builder - FastAPI Backend (リモートサーバ対応版)
リモートadb接続、CORS設定、セキュリティ対応
"""

import asyncio
import base64
import json
import logging
import os
import subprocess
import threading
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

# ==================== 環境変数 ====================
ADB_HOST = os.getenv('ADB_HOST', 'localhost')
ADB_PORT = os.getenv('ADB_PORT', '5037')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', '8000'))
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '*').split(',')
RESULTS_DIR = os.getenv('RESULTS_DIR', './results')

# ==================== ロギング ====================
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Visual Scenario Builder API",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

# ==================== CORS設定（リモートアクセス対応） ====================
logger.info(f"Allowed origins: {ALLOWED_ORIGINS}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# ==================== データクラス ====================
@dataclass
class Device:
    serial: str
    name: str
    connected: bool
    model: Optional[str] = None
    android_version: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None


@dataclass
class UIElement:
    """UI要素情報"""
    id: str
    resource_id: str
    class_name: str
    text: str
    bounds: Dict[str, int]
    clickable: bool
    depth: int


# ==================== デバイス管理（リモートadb対応） ====================
class DeviceManager:
    """ADB デバイス管理（ローカル/リモート対応）"""
    
    def __init__(self, adb_host: str = 'localhost', adb_port: int = 5037):
        self.devices: Dict[str, Device] = {}
        self.selected_device: Optional[str] = None
        self.adb_host = adb_host
        self.adb_port = adb_port
        
        logger.info(f"DeviceManager initialized: {adb_host}:{adb_port}")
    
    def refresh_devices(self) -> List[Device]:
        """接続デバイスを更新"""
        try:
            # リモートadb接続の場合
            if self.adb_host != 'localhost' and self.adb_host != '127.0.0.1':
                self._connect_remote_adb()
            
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
                            android_version=self._get_device_prop(serial, 'ro.build.version.release'),
                            host=self.adb_host,
                            port=self.adb_port
                        )
                        self.devices[serial] = device
                        logger.info(f"Device found: {serial} ({device.name})")
            
            logger.info(f"Found {len(self.devices)} devices")
            return list(self.devices.values())
        
        except Exception as e:
            logger.error(f"Failed to refresh devices: {e}")
            return []
    
    def _connect_remote_adb(self):
        """リモートadbに接続"""
        try:
            # すでに接続されているか確認
            result = subprocess.run(
                ['adb', 'devices'],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            if f"{self.adb_host}:{self.adb_port}" not in result.stdout:
                logger.info(f"Connecting to remote adb: {self.adb_host}:{self.adb_port}")
                subprocess.run(
                    ['adb', 'connect', f"{self.adb_host}:{self.adb_port}"],
                    capture_output=True,
                    timeout=10
                )
        except Exception as e:
            logger.warning(f"Failed to connect remote adb: {e}")
    
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
        self.ui_elements: List[UIElement] = []
    
    def capture_screen(self) -> Optional[bytes]:
        """スクリーンショット取得"""
        try:
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
        
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
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
            subprocess.run(
                ['adb', '-s', self.device_serial, 'shell', 'uiautomator', 'dump', '/sdcard/dump.xml'],
                timeout=5,
                capture_output=True
            )
            
            dump_path = f'/tmp/dump_{self.device_serial}.xml'
            subprocess.run(
                ['adb', '-s', self.device_serial, 'pull', '/sdcard/dump.xml', dump_path],
                timeout=5,
                capture_output=True
            )
            
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
                attribs = node.attrib
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
        """bounds 文字列を解析"""
        try:
            if not bounds_str:
                return None
            
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
            logger.info(f"Tapped at ({x}, {y}) on {self.device_serial}")
            return True
        except Exception as e:
            logger.error(f"Failed to tap: {e}")
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
            logger.info(f"Swiped on {self.device_serial}: ({x1}, {y1}) → ({x2}, {y2})")
            return True
        except Exception as e:
            logger.error(f"Failed to swipe: {e}")
            return False
    
    def input_text(self, text: str) -> bool:
        """テキスト入力"""
        try:
            escaped_text = text.replace('"', '\\"')
            subprocess.run(
                ['adb', '-s', self.device_serial, 'shell', 'input', 'text', escaped_text],
                timeout=5,
                capture_output=True
            )
            logger.info(f"Input text on {self.device_serial}: {text}")
            return True
        except Exception as e:
            logger.error(f"Failed to input text: {e}")
            return False


# ==================== グローバルインスタンス ====================
device_manager = DeviceManager(ADB_HOST, int(ADB_PORT))
screen_capture_map: Dict[str, ScreenCapture] = {}
tap_simulator_map: Dict[str, TapSimulator] = {}

# ==================== REST API エンドポイント ====================

@app.get("/health")
async def health():
    """ヘルスチェック"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "adb_host": ADB_HOST,
        "adb_port": ADB_PORT
    }


@app.get("/api/devices")
async def get_devices():
    """接続デバイス一覧"""
    devices = device_manager.refresh_devices()
    return {
        "devices": [asdict(d) for d in devices],
        "selected": device_manager.selected_device,
        "adb_host": ADB_HOST,
        "adb_port": ADB_PORT
    }


@app.post("/api/devices/{serial}/select")
async def select_device(serial: str):
    """デバイスを選択"""
    if device_manager.select_device(serial):
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


# ==================== テスト結果レポート ====================
@app.get("/api/reports/summary")
async def get_reports_summary():
    """テスト結果のサマリー（JSON）を取得"""
    result_manager = TestResultManager(RESULTS_DIR)
    return result_manager.generate_summary_report()


@app.get("/api/reports/html", response_class=HTMLResponse)
async def get_reports_html():
    """テスト結果レポート（HTML）を取得"""
    generator = HTMLReportGenerator(RESULTS_DIR)
    return generator.render_html()


# ==================== WebSocket（リアルタイム更新） ====================
@app.websocket("/ws/screen")
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
            await asyncio.sleep(1)
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()


# ==================== 起動情報ログ ====================
@app.on_event("startup")
async def startup_event():
    """アプリ起動時"""
    logger.info("="*50)
    logger.info("Visual Scenario Builder Backend Started")
    logger.info("="*50)
    logger.info(f"API Host: {API_HOST}:{API_PORT}")
    logger.info(f"ADB Host: {ADB_HOST}:{ADB_PORT}")
    logger.info(f"CORS Origins: {ALLOWED_ORIGINS}")
    logger.info(f"Log Level: {LOG_LEVEL}")
    logger.info("="*50)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        log_level=LOG_LEVEL.lower()
    )
