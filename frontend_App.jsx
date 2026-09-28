/*
Visual Scenario Builder - React Frontend
アプリケーションのUIコンポーネント
*/

import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE = 'http://localhost:8000/api';

// ==================== デバイス選択コンポーネント ====================
function DeviceSelector({ onDeviceSelect }) {
  const [devices, setDevices] = useState([]);
  const [selectedDevice, setSelectedDevice] = useState(null);

  useEffect(() => {
    refreshDevices();
  }, []);

  const refreshDevices = async () => {
    try {
      const response = await axios.get(`${API_BASE}/devices`);
      setDevices(response.data.devices);
      setSelectedDevice(response.data.selected);
    } catch (error) {
      console.error('Failed to fetch devices:', error);
    }
  };

  const handleSelectDevice = async (serial) => {
    try {
      const response = await axios.post(`${API_BASE}/devices/${serial}/select`);
      setSelectedDevice(serial);
      onDeviceSelect(serial);
    } catch (error) {
      console.error('Failed to select device:', error);
    }
  };

  return (
    <div className="device-selector">
      <h3>デバイス</h3>
      <button onClick={refreshDevices} className="btn-refresh">⟳ 更新</button>
      
      {devices.length === 0 ? (
        <p className="no-devices">デバイスが接続されていません</p>
      ) : (
        <div className="device-list">
          {devices.map((device) => (
            <div
              key={device.serial}
              className={`device-item ${selectedDevice === device.serial ? 'selected' : ''}`}
              onClick={() => handleSelectDevice(device.serial)}
            >
              <div className="device-name">
                {device.name}
                {selectedDevice === device.serial && ' ✓'}
              </div>
              <div className="device-info">
                {device.model} · Android {device.android_version}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ==================== 画面プレビューコンポーネント ====================
function ScreenPreview({ selectedDevice, onElementClick, onTap }) {
  const [screenshot, setScreenshot] = useState(null);
  const [elements, setElements] = useState([]);
  const [highlightedElement, setHighlightedElement] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const canvasRef = useRef(null);
  const wsRef = useRef(null);

  useEffect(() => {
    if (selectedDevice) {
      startScreenStream();
    }
  }, [selectedDevice]);

  const startScreenStream = () => {
    if (wsRef.current) {
      wsRef.current.close();
    }

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${wsProtocol}//${window.location.host}/ws/screen`);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsStreaming(true);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.screenshot) {
        setScreenshot(data.screenshot);
        if (data.elements) {
          setElements(data.elements);
        }
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      setIsStreaming(false);
    };

    wsRef.current = ws;
  };

  const handleCanvasClick = async (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const x = Math.round((e.clientX - rect.left) * (1920 / rect.width)); // 画面解像度に合わせる
    const y = Math.round((e.clientY - rect.top) * (1080 / rect.height));

    // タップ検出の可視化
    const clickedElement = elements.find((elem) => {
      return x >= elem.bounds.x1 && x <= elem.bounds.x2 &&
             y >= elem.bounds.y1 && y <= elem.bounds.y2;
    });

    if (clickedElement) {
      setHighlightedElement(clickedElement.id);
      onElementClick(clickedElement);
    }

    // タップ実行
    try {
      const response = await axios.post(`${API_BASE}/tap?x=${x}&y=${y}`);
      setScreenshot(response.data.screenshot);
      if (response.data.elements) {
        setElements(response.data.elements);
      }
    } catch (error) {
      console.error('Failed to tap:', error);
    }
  };

  const drawElements = (ctx) => {
    if (!elements || elements.length === 0) return;

    elements.forEach((elem) => {
      if (!elem.clickable) return;

      const x = elem.bounds.x1;
      const y = elem.bounds.y1;
      const w = elem.bounds.x2 - elem.bounds.x1;
      const h = elem.bounds.y2 - elem.bounds.y1;

      // 枠線を描画
      if (highlightedElement === elem.id) {
        ctx.strokeStyle = '#ff6b6b';
        ctx.lineWidth = 3;
      } else {
        ctx.strokeStyle = 'rgba(52, 168, 224, 0.5)';
        ctx.lineWidth = 1;
      }

      ctx.strokeRect(x, y, w, h);

      // ラベルを描画
      if (elem.text) {
        ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
        ctx.fillRect(x, y - 20, w, 20);
        ctx.fillStyle = '#fff';
        ctx.font = '12px Arial';
        ctx.fillText(elem.text.substring(0, 20), x + 3, y - 5);
      }
    });
  };

  return (
    <div className="screen-preview">
      <div className="preview-header">
        <h3>ライブスクリーン</h3>
        <div className="status">
          <span className={`indicator ${isStreaming ? 'active' : ''}`}></span>
          {isStreaming ? 'ストリーミング中' : 'オフライン'}
        </div>
      </div>

      <div className="preview-container">
        {screenshot ? (
          <div className="canvas-wrapper">
            <img
              src={screenshot}
              alt="device screen"
              className="screenshot-image"
              onClick={handleCanvasClick}
            />
            <canvas
              ref={canvasRef}
              className="element-overlay"
              width={1920}
              height={1080}
              onClick={handleCanvasClick}
            />
          </div>
        ) : (
          <div className="loading">
            スクリーンショット読み込み中...
          </div>
        )}
      </div>

      <div className="element-info">
        {highlightedElement && elements.find(e => e.id === highlightedElement) && (
          (() => {
            const elem = elements.find(e => e.id === highlightedElement);
            return (
              <div className="info-box">
                <p><strong>Resource ID:</strong> {elem.resource_id}</p>
                <p><strong>Text:</strong> {elem.text}</p>
                <p><strong>Class:</strong> {elem.class_name}</p>
                <p><strong>Clickable:</strong> {elem.clickable ? 'Yes' : 'No'}</p>
                <p><strong>Bounds:</strong> ({elem.bounds.x1}, {elem.bounds.y1}) - ({elem.bounds.x2}, {elem.bounds.y2})</p>
              </div>
            );
          })()
        )}
      </div>
    </div>
  );
}

// ==================== アクション作成コンポーネント ====================
function ActionBuilder({ selectedElement, onAddAction }) {
  const [actionType, setActionType] = useState('click');
  const [inputValue, setInputValue] = useState('');
  const [duration, setDuration] = useState(1);

  const handleAddAction = () => {
    const action = {
      type: actionType,
      target: selectedElement?.resource_id,
      value: inputValue,
      duration: duration,
      timestamp: new Date().toISOString()
    };

    onAddAction(action);
    setInputValue('');
  };

  return (
    <div className="action-builder">
      <h3>アクション追加</h3>

      <div className="form-group">
        <label>アクションタイプ</label>
        <select value={actionType} onChange={(e) => setActionType(e.target.value)}>
          <option value="click">クリック</option>
          <option value="input">入力</option>
          <option value="wait">待機</option>
          <option value="screenshot">スクリーンショット</option>
          <option value="swipe">スワイプ</option>
          <option value="switch_app">アプリ切り替え</option>
          <option value="human_input">人間入力待ち</option>
        </select>
      </div>

      {actionType === 'input' && (
        <div className="form-group">
          <label>入力テキスト</label>
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="入力内容"
          />
        </div>
      )}

      {actionType === 'wait' && (
        <div className="form-group">
          <label>待機時間（秒）</label>
          <input
            type="number"
            min="0.1"
            step="0.1"
            value={duration}
            onChange={(e) => setDuration(parseFloat(e.target.value))}
          />
        </div>
      )}

      {selectedElement ? (
        <div className="selected-element-info">
          <p>対象要素: <strong>{selectedElement.resource_id || selectedElement.text}</strong></p>
        </div>
      ) : (
        <div className="no-element-info">
          <p>画面内の要素をクリックして選択</p>
        </div>
      )}

      <button
        onClick={handleAddAction}
        disabled={!selectedElement && actionType !== 'wait' && actionType !== 'switch_app'}
        className="btn-add-action"
      >
        + アクション追加
      </button>
    </div>
  );
}

// ==================== シナリオエディタコンポーネント ====================
function ScenarioEditor({ actions, onDeleteAction, onExport }) {
  const [scenarioName, setScenarioName] = useState('My Scenario');

  return (
    <div className="scenario-editor">
      <div className="scenario-header">
        <h3>シナリオ</h3>
        <input
          type="text"
          value={scenarioName}
          onChange={(e) => setScenarioName(e.target.value)}
          placeholder="シナリオ名"
          className="scenario-name-input"
        />
      </div>

      <div className="actions-list">
        {actions.length === 0 ? (
          <p className="empty-message">アクションが追加されていません</p>
        ) : (
          actions.map((action, index) => (
            <div key={index} className="action-item">
              <div className="action-number">{index + 1}</div>
              <div className="action-content">
                <div className="action-type">{action.type}</div>
                <div className="action-details">
                  {action.target && <span>{action.target}</span>}
                  {action.value && <span>{action.value}</span>}
                  {action.duration && <span>{action.duration}s</span>}
                </div>
              </div>
              <button
                onClick={() => onDeleteAction(index)}
                className="btn-delete"
              >
                ×
              </button>
            </div>
          ))
        )}
      </div>

      <button
        onClick={() => onExport(scenarioName, actions)}
        disabled={actions.length === 0}
        className="btn-export"
      >
        📥 YAML エクスポート
      </button>
    </div>
  );
}

// ==================== メインアプリケーション ====================
function App() {
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [selectedElement, setSelectedElement] = useState(null);
  const [actions, setActions] = useState([]);

  const handleAddAction = (action) => {
    setActions([...actions, action]);
  };

  const handleDeleteAction = (index) => {
    setActions(actions.filter((_, i) => i !== index));
  };

  const handleExport = async (scenarioName, actions) => {
    const scenario = {
      name: scenarioName,
      variables: {},
      actions: actions.map((a) => ({
        type: a.type,
        target: a.target,
        value: a.value,
        duration: a.duration
      }))
    };

    try {
      const response = await axios.post(`${API_BASE}/scenario/save`, scenario);
      alert(`Saved: ${response.data.path}`);
    } catch (error) {
      console.error('Failed to save scenario:', error);
      alert('シナリオの保存に失敗しました');
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Visual Scenario Builder</h1>
        <p>Androidアプリの自動テストシナリオをビジュアルで構築</p>
      </header>

      <div className="app-container">
        <div className="sidebar">
          <DeviceSelector onDeviceSelect={setSelectedDevice} />
          <ActionBuilder selectedElement={selectedElement} onAddAction={handleAddAction} />
        </div>

        <div className="main-content">
          {selectedDevice ? (
            <ScreenPreview
              selectedDevice={selectedDevice}
              onElementClick={setSelectedElement}
            />
          ) : (
            <div className="no-device-placeholder">
              <p>デバイスを選択してください</p>
            </div>
          )}
        </div>

        <div className="sidebar">
          <ScenarioEditor
            actions={actions}
            onDeleteAction={handleDeleteAction}
            onExport={handleExport}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
