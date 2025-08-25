# 🎵 PyWAC - Python Process Audio Capture for Windows

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.7+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Version](https://img.shields.io/badge/Version-0.2.0-blue?style=for-the-badge)](https://github.com/Mega-Gorilla/pywac)

**Windows対応のシンプルなオーディオ制御ライブラリ**

[🇬🇧 English](README.en.md) | **🇯🇵 日本語**

</div>

---

## 🚀 3秒でわかるPyWAC

```python
import pywac

# たった1行でオーディオ録音
pywac.record_to_file("output.wav", duration=5)

# 特定アプリの音声だけを録音（Discord音声を除外！）
pywac.record_process("game.exe", "game_only.wav", duration=10)

# アプリの音量を調整
pywac.set_app_volume("spotify", 0.5)

# アクティブなオーディオセッションを確認
active = pywac.get_active_sessions()
print(f"アクティブなセッション: {', '.join(active)}")
# 出力例: アクティブなセッション: Spotify.exe, Chrome.exe
```

**それだけです！** 複雑な設定は不要です。

---

## 📋 Contents

- [Features](#-features)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Demo](#-demo)
- [Usage](#-usage)
- [Examples](#-examples)
- [API Reference](#-api-reference)
- [Development](#-development)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

---

## ✨ Features

### 🎯 主な特徴

- **プロセス別音声録音** - 特定アプリケーションの音声のみを録音（Windows 10 2004+）
- **音量制御** - アプリケーション単位での音量調整・ミュート
- **シンプルなAPI** - 1行のコードで録音開始
- **リアルタイム監視** - 音声セッションの状態をリアルタイムで取得
- **モダンなUI** - Gradioベースの対話型デモアプリケーション
- **Windows 11完全対応** - 最新のWindows Audio APIを活用

### 🔍 なぜPyWACを選ぶ？

| 機能 | PyWAC | PyAudio | sounddevice | PyAudioWPatch |
|------|-------|---------|-------------|---------------|
| プロセス別録音 | ✅ | ❌ | ❌ | ❌ |
| アプリ音量制御 | ✅ | ❌ | ❌ | ❌ |
| Windows 11対応 | ✅ | ⚠️ | ⚠️ | ✅ |
| 簡単なAPI | ✅ | ❌ | ⚠️ | ⚠️ |
| Process Loopback | ✅ | ❌ | ❌ | ❌ |

---

## 📋 Requirements

- **OS**: Windows 10 version 2004 (Build 19041) 以降
- **Python**: 3.7 以降
- **コンパイラ**: Microsoft Visual C++ 14.0 以降（ビルド時のみ）

---

## 📦 Installation

### 方法1: 簡単インストール（推奨）

```bash
# 開発版（現在のインストール方法）
git clone https://github.com/Mega-Gorilla/pywac.git
cd pywac
pip install -e .
```

### 方法2: 手動ビルド（上級者向け）

<details>
<summary>クリックして展開</summary>

#### 前提条件
- Windows 10 (2004以降) または Windows 11
- Python 3.7以上
- Visual Studio 2022（C++開発ツール）
- Windows SDK 10.0.26100.0以降

```bash
# 仮想環境作成
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 依存関係インストール
pip install pybind11 numpy

# ビルド
python setup.py build_ext --inplace
```

</details>

---

## 🚀 Quick Start

### 基本的な使い方

```python
import pywac

# システム音声を録音
pywac.record_to_file("output.wav", duration=5)

# 特定アプリの音声のみ録音
pywac.record_process("spotify", "spotify_only.wav", duration=10)

# アプリの音量を調整
pywac.set_app_volume("firefox", 0.5)  # 50%に設定
```

## 🎮 Demo

### Gradioインタラクティブデモ

PyWACの全機能を体験できる対話型デモアプリケーションを提供しています：

```bash
# デモアプリケーションを起動
python examples/gradio_demo.py
```

ブラウザで `http://localhost:7860` にアクセスしてください。

#### デモの機能

##### 📊 セッション管理
- アクティブな音声セッションをリアルタイム表示
- 各アプリケーションのプロセスID、状態、音量、ミュート状態を確認
- 自動更新機能（5秒間隔）
- ワンクリックで手動更新

##### 🎚️ 音量制御
- ドロップダウンでアプリケーションを選択
- スライダーで音量を調整（0-100%）
- 音量設定ボタンで即座に反映
- 設定結果をステータス表示

##### 🔴 録音機能
3つの録音モードを提供：
- **システム録音**: すべての音声を録音
- **プロセス録音**: 特定アプリの音声のみを録音（Discord等を除外可能）
- **コールバック録音**: リアルタイムモニタリング付き録音
- 録音時間設定（1～60秒）とプリセットボタン（5秒/10秒/30秒）

##### 📈 リアルタイムモニタリング
- 録音中の音声レベルをリアルタイム表示
- RMS値とdBレベルを継続的に更新
- 視覚的なプログレスバー表示

##### 💾 録音管理
- 録音ファイルを自動的にリスト表示（新しい順）
- ワンクリックで録音を再生
- ファイルサイズと録音日時を表示

##### 🎨 モダンなUI
- ダークテーマ対応のモダンなインターフェース
- 3つのタブで機能を整理（セッション管理/録音/音量制御）
- レスポンシブデザイン

### サンプルスクリプト

```bash
# 基本的な使用例
python examples/basic_usage.py

# プロセス別録音のテスト
python examples/record_app_audio.py --list  # 録音可能なアプリをリスト表示
python examples/record_app_audio.py --app spotify --duration 10
```

## 📚 Usage

### 高レベル API (シンプル関数)

```python
import pywac

# システム全体のオーディオ録音
pywac.record_to_file("output.wav", duration=5)

# プロセス固有録音（プロセス名指定）
pywac.record_process("spotify", "spotify_only.wav", duration=10)

# プロセス固有録音（PID指定）
pywac.record_process_id(51716, "spotify_by_pid.wav", duration=10)

# アクティブオーディオセッション取得（プロセス名のリスト）
active = pywac.get_active_sessions()
for app in active:
    print(f"Active: {app}")

# アプリケーション音量制御
pywac.set_app_volume("spotify", 0.5)  # 50%

# セッション情報取得
firefox = pywac.find_audio_session("firefox")
if firefox:
    print(f"Firefox volume: {firefox['volume_percent']}%")

# 全オーディオセッション列挙
sessions = pywac.list_audio_sessions()
for s in sessions:
    print(f"{s['process_name']}: {s['volume_percent']}%")
```

### クラスベース API (詳細制御)

```python
import pywac

# SessionManager による セッション管理
manager = pywac.SessionManager()

# アクティブセッション列挙
active = manager.get_active_sessions()
for session in active:
    print(f"{session.process_name}")
    print(f"  Volume: {session.volume * 100:.0f}%")
    print(f"  Muted: {session.is_muted}")

# セッション検索と制御
discord = manager.find_session("discord")
if discord:
    manager.set_volume("discord", 0.3)  # 30%
    manager.set_mute("discord", True)

# AudioRecorder による詳細録音制御
recorder = pywac.AudioRecorder()
recorder.start(duration=10)

while recorder.is_recording:
    print(f"Recording: {recorder.recording_time:.1f}s "
          f"({recorder.sample_count} samples)")
    time.sleep(1)

audio_data = recorder.stop()
if len(audio_data) > 0:
    pywac.utils.save_to_wav(audio_data, "output.wav")
    print(f"Saved: {len(audio_data)} samples")
```

### ネイティブ API (低レベル制御)

<details>
<summary>詳細を表示</summary>

```python
import pywac._native as native
import numpy as np

# SessionEnumerator による直接セッション制御
enumerator = native.SessionEnumerator()
sessions = enumerator.enumerate_sessions()

for session in sessions:
    if session.state == 1:  # AudioSessionStateActive
        print(f"PID {session.process_id}: {session.process_name}")
        
        # 直接ボリューム制御
        enumerator.set_session_volume(session.process_id, 0.5)
        enumerator.set_session_mute(session.process_id, False)

# SimpleLoopback による低レベル録音
loopback = native.SimpleLoopback()
if loopback.start():
    time.sleep(5)
    
    # NumPy配列として取得
    audio_buffer = loopback.get_buffer()
    
    # 信号処理
    rms = np.sqrt(np.mean(audio_buffer**2))
    peak = np.max(np.abs(audio_buffer))
    
    loopback.stop()
```

</details>

---

## 💡 Examples

### 🎯 プロセス固有録音の使い方

```python
import pywac

# 方法1: 高レベルAPI（動作中！）
def record_specific_app(app_name, output_file, duration=10):
    """特定アプリの音声のみを録音"""
    success = pywac.record_process(app_name, output_file, duration)
    if success:
        print(f"✅ {app_name}の音声のみ録音完了！")
    else:
        print(f"❌ 録音失敗 - {app_name}が音声を再生中か確認してください")

# 方法2: コールバック録音（新機能！）
def record_with_callback_demo():
    """録音完了時にコールバックを実行"""
    def on_recording_complete(audio_data):
        print(f"録音完了: {len(audio_data)} サンプル")
        # 音声解析
        import numpy as np
        audio_array = np.array(audio_data)
        rms = np.sqrt(np.mean(audio_array ** 2))
        db = 20 * np.log10(rms + 1e-10)
        print(f"平均音量: {db:.1f} dB")
        
        # WAVファイルに保存
        pywac.utils.save_to_wav(audio_data, "callback_recording.wav", 48000)
        print("✅ 録音をcallback_recording.wavに保存！")
    
    # 5秒間録音（非同期）
    pywac.record_with_callback(5, on_recording_complete)
    print("録音開始（バックグラウンド）...")
    
    # 録音完了まで待機
    import time
    time.sleep(6)
    print("✅ 処理完了！")

# 使用例：ゲーム音声のみ録音（Discord音声なし）
record_specific_app("game.exe", "game_audio.wav", 30)

# 使用例：ブラウザ音声のみ録音
record_specific_app("firefox", "browser_audio.wav", 15)
```

### 🎮 ゲーム配信用オーディオミキサー

```python
import pywac

class StreamAudioMixer:
    """配信用のオーディオバランス調整"""
    
    def __init__(self):
        self.manager = pywac.SessionManager()
    
    def setup_streaming(self):
        """配信用の音量設定"""
        # ゲーム音を70%
        pywac.set_app_volume("game", 0.7)
        
        # Discord を30%
        pywac.set_app_volume("discord", 0.3)
        
        # Spotify をミュート
        pywac.mute_app("spotify")
        
        print("✅ 配信用オーディオ設定完了！")
    
    def save_all_audio(self, duration=60):
        """システム音声を録音（全アプリの混合音声）"""
        pywac.record_to_file(f"recording_{time.time()}.wav", duration)
    
    def save_game_audio_only(self, game_name="game.exe", duration=60):
        """ゲーム音声のみを録音（Discord音声を除外）"""
        # Process Loopback APIでゲーム音声のみ録音！
        pywac.record_process(game_name, f"game_only_{time.time()}.wav", duration)
        print("✅ ゲーム音声のみ録音完了（Discord音声なし！）")

# 使用例
mixer = StreamAudioMixer()
mixer.setup_streaming()
```

### 📊 リアルタイムオーディオメーター

```python
import pywac
import time

def audio_meter(duration=30):
    """ビジュアルオーディオメーター"""
    recorder = pywac.AudioRecorder()
    recorder.start(duration=duration)
    
    print("🎵 オーディオレベルメーター")
    print("-" * 50)
    
    while recorder.is_recording:
        buffer = recorder.get_buffer()
        if len(buffer) > 0:
            # RMS計算
            rms = pywac.utils.calculate_rms(buffer)
            db = pywac.utils.calculate_db(buffer)
            
            # ビジュアライズ
            bar_length = int(rms * 50)
            bar = "█" * bar_length + "░" * (50 - bar_length)
            
            print(f"\r[{bar}] {db:.1f} dB", end="")
        
        time.sleep(0.1)
    
    recorder.stop()
    print("\n✅ 完了")

# 実行
audio_meter(10)
```

### 🎵 スマート音量調整

```python
import pywac
import schedule

def auto_adjust_volume():
    """時間帯による自動音量調整"""
    import datetime
    
    hour = datetime.datetime.now().hour
    
    if 22 <= hour or hour < 6:
        # 深夜は全体的に音量を下げる
        active = pywac.get_active_sessions()
        for app in active:
            pywac.set_app_volume(app, 0.3)
        print("🌙 深夜モード: 音量30%")
    
    elif 9 <= hour < 17:
        # 仕事時間はビデオ会議アプリを優先
        pywac.set_app_volume("zoom", 1.0)
        pywac.set_app_volume("teams", 1.0)
        pywac.set_app_volume("spotify", 0.2)
        print("💼 仕事モード: 会議優先")
    
    else:
        # 通常時間
        active = pywac.get_active_sessions()
        for app in active:
            pywac.set_app_volume(app, 0.7)
        print("🏠 通常モード: 音量70%")

# スケジュール設定
schedule.every().hour.do(auto_adjust_volume)
```

---

## 📖 API Reference

### 🟢 簡単関数API

| 関数 | 説明 | 例 |
|------|------|-----|
| `record_to_file(filename, duration)` | 音声を録音してファイルに保存 | `pywac.record_to_file("out.wav", 5)` |
| `record_process(name, filename, duration)` | プロセス固有録音 | `pywac.record_process("spotify", "spotify.wav", 10)` |
| `record_process_id(pid, filename, duration)` | PID指定で録音 | `pywac.record_process_id(12345, "out.wav", 10)` |
| `list_audio_sessions()` | 全オーディオセッション取得 | `sessions = pywac.list_audio_sessions()` |
| `list_recordable_processes()` | 録音可能プロセス一覧 | `procs = pywac.list_recordable_processes()` |
| `get_active_sessions()` | アクティブセッション取得 | `sessions = pywac.get_active_sessions()` |
| `set_app_volume(app, volume)` | アプリ音量設定 (0.0-1.0) | `pywac.set_app_volume("chrome", 0.5)` |
| `get_app_volume(app)` | アプリ音量取得 | `vol = pywac.get_app_volume("chrome")` |
| `adjust_volume(app, delta)` | 音量を相対的に調整 | `pywac.adjust_volume("chrome", 0.1)` |
| `mute_app(app)` | アプリをミュート | `pywac.mute_app("spotify")` |
| `unmute_app(app)` | ミュート解除 | `pywac.unmute_app("spotify")` |
| `find_audio_session(app)` | セッション情報取得 | `info = pywac.find_audio_session("firefox")` |
| `record_with_callback(duration, callback)` | コールバック付き録音 | `pywac.record_with_callback(5, on_complete)` |
| `utils.save_to_wav(data, filename, sample_rate)` | WAVファイル保存 | `pywac.utils.save_to_wav(audio_data, "out.wav", 48000)` |

### 🔵 クラスAPI

#### SessionManager

```python
manager = pywac.SessionManager()
```

| メソッド | 説明 |
|---------|------|
| `list_sessions(active_only=False)` | セッション一覧取得 |
| `find_session(app_name)` | アプリ検索 |
| `set_volume(app_name, volume)` | 音量設定 |
| `set_mute(app_name, mute)` | ミュート制御 |
| `get_active_sessions()` | アクティブセッション取得 |

#### AudioRecorder

```python
recorder = pywac.AudioRecorder()
```

| メソッド/プロパティ | 説明 |
|-------------------|------|
| `start(duration=None)` | 録音開始 |
| `stop()` | 録音停止 |
| `record(duration)` | 指定時間録音 |
| `record_to_file(filename, duration)` | ファイルに直接録音 |
| `get_buffer()` | 現在のバッファ取得 |
| `is_recording` | 録音中か確認 |
| `recording_time` | 録音時間取得 |
| `sample_count` | サンプル数取得 |

---

## 🔧 Troubleshooting

### よくある問題

<details>
<summary>❌ ImportError: No module named 'pywac'</summary>

**解決方法:**
```bash
# パッケージをインストール
pip install -e .

# または手動ビルド
python setup.py build_ext --inplace
```
</details>

<details>
<summary>❌ DLL load failed</summary>

**解決方法:**
1. [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe) をインストール
2. Windows を再起動
</details>

<details>
<summary>❌ 音声が録音されない</summary>

**解決方法:**
1. 管理者権限でPowerShellを実行
2. 何かのアプリで音声を再生中か確認
3. Windowsのサウンド設定を確認
</details>

### デバッグモード

```python
# 詳細ログを有効化
import logging
logging.basicConfig(level=logging.DEBUG)

# システム情報を表示
import pywac
print(f"PyWAC Version: {pywac.__version__}")

# オーディオセッション診断
sessions = pywac.list_audio_sessions()
print(f"検出されたセッション: {len(sessions)}")
for s in sessions:
    print(f"  - {s['process_name']} (PID: {s['process_id']})")
```

---

## 🛠️ Development

### ビルド環境

<details>
<summary>必要なツール</summary>

- Visual Studio 2022
- Windows SDK 10.0.26100.0+
- Python 3.7-3.12
- Git

</details>

### 開発セットアップ

```bash
# リポジトリクローン
git clone https://github.com/Mega-Gorilla/pywac.git
cd pywac

# 開発環境構築
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]

# テスト実行
pytest tests/

# コード品質チェック
black pywac/
pylint pywac/
mypy pywac/
```

### アーキテクチャ

```
pywac/
├── pywac/              # Pythonパッケージ
│   ├── __init__.py    # パッケージエントリ
│   ├── api.py         # 高レベルAPI
│   ├── sessions.py    # セッション管理
│   ├── recorder.py    # 録音機能
│   └── utils.py       # ユーティリティ
├── src/               # C++ソース
│   ├── pypac_native.cpp      # メインモジュール
│   └── process_loopback_v2.cpp # Process Loopback実装
├── examples/          # サンプルコード
└── tests/            # テスト
```

### 技術詳細: Process Loopback API

Windows 10 2004 (Build 19041) で導入されたProcess Loopback APIを使用して、プロセス単位の音声キャプチャを実現しています。

#### 実装の特徴

- **API**: `ActivateAudioInterfaceAsync` with `AUDIOCLIENT_ACTIVATION_TYPE_PROCESS_LOOPBACK`
- **フォーマット**: 48kHz / 32bit float / ステレオ（固定）
- **バッファ**: 最大60秒のリングバッファ
- **遅延**: < 50ms
- **スレッドモデル**: COMマルチスレッド (`COINIT_MULTITHREADED`)

#### パフォーマンス

| 操作 | 時間 | 備考 |
|------|------|------|
| セッション列挙 | < 10ms | 5セッション |
| 音量変更 | < 5ms | 即座に反映 |
| 録音開始 | < 50ms | 初期化含む |
| プロセス録音初期化 | < 200ms | COM初期化含む |
| CPU使用率 | < 2% | 録音中 |
| メモリ使用量 | < 50MB | 60秒バッファ |

詳細な技術仕様は[技術調査レポート](docs/PROCESS_LOOPBACK_INVESTIGATION.md)を参照してください。

### コントリビューション

プルリクエスト歓迎です！

1. フォーク
2. フィーチャーブランチ作成 (`git checkout -b feature/amazing`)
3. コミット (`git commit -m 'Add amazing feature'`)
4. プッシュ (`git push origin feature/amazing`)
5. プルリクエスト作成

---

## ✅ 動作確認済み環境

| 環境 | バージョン | 状態 |
|------|-----------|------|
| Windows 11 | 23H2 | ✅ 完全動作 |
| Windows 11 | 24H2 | ⚠️ 一部制限あり |
| Windows 10 | 21H2+ | ✅ 完全動作 |
| Python | 3.7-3.12 | ✅ テスト済み |
| Visual Studio | 2022 | ✅ 推奨 |

### テスト済みアプリケーション

- ✅ **Spotify** - 音量制御、録音
- ✅ **Discord** - 音量制御、ミュート
- ✅ **Chrome/Firefox** - セッション検出、音量制御
- ✅ **Steam** - セッション検出
- ✅ **OBS Studio** - 録音との併用可能

---


## 📄 License

MIT License - 詳細は[LICENSE](LICENSE)参照

## 🙏 Acknowledgments

- [pybind11](https://github.com/pybind/pybind11) - 優れたC++バインディング
- [OBS Studio](https://obsproject.com/) - オーディオキャプチャの参考実装
- Windows Audio APIチーム - 詳細なドキュメント

