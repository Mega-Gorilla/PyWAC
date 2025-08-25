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

## 📖 目次

- [なぜPyWACが必要か？](#-なぜpywacが必要か)
- [主な機能](#-主な機能)
- [インストール](#-インストール)
- [使い方](#-使い方)
  - [Level 1: 超簡単 - 関数API](#level-1-超簡単---関数api)
  - [Level 2: 柔軟 - クラスAPI](#level-2-柔軟---クラスapi)
  - [Level 3: 完全制御 - ネイティブAPI](#level-3-完全制御---ネイティブapi)
- [実用例](#-実用例)
- [APIリファレンス](#-apiリファレンス)
- [トラブルシューティング](#-トラブルシューティング)
- [開発者向け](#-開発者向け)

---

## 🤔 なぜPyWACが必要か？

### 既存ライブラリの問題点

| ライブラリ | 問題 |
|-----------|------|
| PyAudio | Windowsの最新APIに非対応 |
| sounddevice | プロセス単位の制御不可 |
| PyAudioWPatch | システム全体の音声のみ |
| OBS win-capture-audio | GUIアプリ専用、Python非対応 |

### PyWACの解決策

| 機能 | PyWAC | 他のライブラリ |
|------|-------|--------------|
| プロセス別音量制御 | ✅ | ❌ |
| **アプリ単位の録音** | ✅ | ❌ |
| 簡単なAPI | ✅ 1行で実行 | ❌ 複雑な設定 |
| Windows 11対応 | ✅ | ⚠️ 限定的 |
| Process Loopback API | ✅ | ❌ |

---

## 主要機能

### Process Loopback API による プロセス固有録音 ✅

Windows 10 2004 (Build 19041) 以降で利用可能な Process Loopback API を使用し、特定プロセスの音声ストリームを分離してキャプチャする機能を実装しました。これにより、ゲーム音声とボイスチャット音声を分離して録音することが可能です。

**技術仕様:**
- Windows Audio Session API (WASAPI) を使用したオーディオセッション管理
- `ActivateAudioInterfaceAsync` による非同期オーディオインターフェース初期化
- `AUDIOCLIENT_ACTIVATION_TYPE_PROCESS_LOOPBACK` によるプロセス固有キャプチャ
- `PROCESS_LOOPBACK_MODE_INCLUDE_TARGET_PROCESS_TREE` で対象プロセスの音声を録音
- 48kHz / 32bit float / ステレオ の固定フォーマット（`GetMixFormat()` が E_NOTIMPL を返すため）
- 最大60秒のバッファリング対応

**実装詳細:**
- C++17 による低レベル実装（`src/process_loopback_v2.cpp`）
- pybind11 を使用した Python バインディング
- COM マルチスレッド環境での動作（`COINIT_MULTITHREADED`）

詳細な技術仕様は [技術調査レポート](docs/PROCESS_LOOPBACK_INVESTIGATION.md) を参照してください。

---

## 📦 インストール

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

## API 使用方法

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

## 💡 実用例

### 🎯 プロセス固有録音の使い方（目玉機能！）

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

## 📚 APIリファレンス

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

## 🔧 トラブルシューティング

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

## 📊 パフォーマンス

### 実測値（Windows 11 環境）

| 操作 | 時間 | 備考 |
|------|------|------|
| セッション列挙 | < 10ms | 5セッション |
| 音量変更 | < 5ms | 即座に反映 |
| 録音開始 | < 50ms | 初期化含む |
| 1秒録音のサンプル数 | 約96,000 | 48kHz×2ch |
| メモリ使用量 | < 50MB | 通常使用時 |

### システム要件

| 最小要件 | 推奨要件 |
|---------|---------|
| Windows 10 2004 | Windows 11 |
| 4GB RAM | 8GB RAM |
| Python 3.7 | Python 3.10+ |

---

## 🛠️ 開発者向け

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
│   └── audio_session_capture.cpp
├── examples/          # サンプルコード
└── tests/            # テスト
```

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

## 🎮 Gradio デモアプリケーション

PyWACの全機能を試せる統合デモアプリを用意しています：

```bash
# Gradioデモを起動
python examples/gradio_demo.py
```

### デモの機能：
- 📊 **セッション管理**: リアルタイムで音声セッションを監視・制御
- 🎚️ **音量制御**: 各アプリの音量をGUIで調整
- 🔴 **録音機能**: システム/プロセス/コールバック録音をサポート
- 📈 **モニタリング**: 録音中の音声レベルをリアルタイム表示
- 🌙 **ダークテーマ**: 目に優しいモダンなUI

---

## 📄 ライセンス

MIT License - 詳細は[LICENSE](LICENSE)参照

## 🙏 謝辞

- [pybind11](https://github.com/pybind/pybind11) - 優れたC++バインディング
- [OBS Studio](https://obsproject.com/) - オーディオキャプチャの参考実装
- Windows Audio APIチーム - 詳細なドキュメント

