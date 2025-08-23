# Windows Audio Capture Library for Python

Windows向けのプロセス単位オーディオキャプチャライブラリです。

## 概要

このプロジェクトは、Windowsでプロセス単位のオーディオキャプチャを実現するためのPython拡張モジュールを提供します。Windows Audio Session APIを使用して、実行中のアプリケーションのオーディオセッションを検出し、システム全体のオーディオをキャプチャすることができます。

## 機能

- **オーディオセッション列挙**: 実行中のアプリケーションのオーディオセッションを検出
- **プロセス情報取得**: プロセス名、PID、音量、ミュート状態などの情報取得
- **シンプルループバック**: システム全体のオーディオをキャプチャ
- **ボリューム制御**: 特定プロセスの音量調整

## モジュール

### `audio_session_capture`
Windows Audio Session APIを使用した安定したオーディオキャプチャ実装

### `process_loopback`  
基本的なWASAPIループバック実装（レガシー）

## 要件

- Windows 10/11
- Python 3.7+
- Visual Studio 2022 (C++開発ツール)
- Windows SDK 10.0.26100.0以降

## インストール

```bash
# 仮想環境のアクティベート
.\.venv\Scripts\Activate.ps1

# 依存関係のインストール
pip install pybind11 numpy

# ビルド
python setup.py build_ext --inplace
```

## 使用例

```python
import audio_session_capture as asc
import numpy as np

# オーディオセッションの列挙
enumerator = asc.SessionEnumerator()
sessions = enumerator.enumerate_sessions()

for session in sessions:
    print(f"{session.process_name} (PID: {session.process_id})")
    print(f"  Volume: {session.volume:.2f}")
    print(f"  Muted: {session.muted}")

# シンプルなループバックキャプチャ
loopback = asc.SimpleLoopback()
if loopback.start():
    # 1秒待機
    import time
    time.sleep(1)
    
    # オーディオデータ取得（numpy配列）
    audio_data = loopback.get_buffer()
    print(f"Captured {len(audio_data)} samples")
    
    loopback.stop()
```

## テスト

```bash
# オーディオセッションのテスト
python tests/test_session_simple.py

# 詳細なテスト
python tests/test_session_capture.py
```

## サンプルコード

`examples/basic_usage.py` に基本的な使用例があります。

```bash
python examples/basic_usage.py
```

## 既知の問題

- Windows 11 24H2でProcess Loopback APIに問題があるため、代替実装（Audio Session API）を使用
- 管理者権限が必要な場合があります

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。