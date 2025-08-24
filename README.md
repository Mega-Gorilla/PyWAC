# 🎵 PyPAC - Python Process Audio Capture for Windows

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.7+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Version](https://img.shields.io/badge/Version-0.2.0-blue?style=for-the-badge)](https://github.com/yourusername/pypac)

**Windowsで最もシンプルなオーディオ制御ライブラリ**

[🇬🇧 English](README.en.md) | **🇯🇵 日本語**

</div>

---

## 🚀 3秒でわかるPyPAC

```python
import pypac

# たった1行でオーディオ録音
pypac.record_to_file("output.wav", duration=5)

# アプリの音量を調整
pypac.set_app_volume("spotify", 0.5)

# 実行中のオーディオセッションを確認
apps = pypac.get_active_apps()
print(f"音声再生中: {', '.join(apps)}")
# 出力例: 音声再生中: Spotify.exe, Chrome.exe
```

**それだけです！** 複雑な設定は不要です。

---

## 📖 目次

- [なぜPyPACが必要か？](#-なぜpypacが必要か)
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

## 🤔 なぜPyPACが必要か？

### 既存ライブラリの問題点

| ライブラリ | 問題 |
|-----------|------|
| PyAudio | Windowsの最新APIに非対応 |
| sounddevice | プロセス単位の制御不可 |
| PyAudioWPatch | システム全体の音声のみ |
| OBS win-capture-audio | GUIアプリ専用、Python非対応 |

### PyPACの解決策

| 機能 | PyPAC | 他のライブラリ |
|------|-------|--------------|
| プロセス別音量制御 | ✅ | ❌ |
| **アプリ単位の録音** | **✅ 完全実装** | ❌ |
| 簡単なAPI | ✅ 1行で実行 | ❌ 複雑な設定 |
| Windows 11対応 | ✅ | ⚠️ 限定的 |
| Process Loopback API | ✅ | ❌ |

---

## ✨ 主な機能

<div align="center">

| 機能 | 状態 | 簡単さ |
|------|------|--------|
| 🎙️ システムオーディオ録音 | ✅ 完成 | ⭐ |
| 🎚️ アプリ別音量制御 | ✅ 完成 | ⭐ |
| 📊 オーディオセッション一覧 | ✅ 完成 | ⭐ |
| 🔇 アプリ別ミュート | ✅ 完成 | ⭐ |
| 🎯 プロセス固有録音 | ✅ 完成 | ⭐⭐ |
| 📈 リアルタイム解析 | ✅ 完成 | ⭐⭐ |

</div>

### 🎯 プロセス固有録音が完全動作！

Windows Process Loopback APIを使用して、**特定のアプリケーションの音声のみを録音**できるようになりました！

**動作確認済みアプリ:**
- ✅ Spotify - 音楽のみを録音（Discord音声を除外）
- ✅ Firefox/Chrome - ブラウザ音声のみを録音
- ✅ ゲーム - ゲーム音声のみを録音（ボイスチャット除外）

**必要環境:** Windows 10 2004 (Build 19041) 以降

詳細は[技術調査レポート](docs/PROCESS_LOOPBACK_INVESTIGATION.md)をご覧ください。

---

## 📦 インストール

### 方法1: 簡単インストール（推奨）

```bash
# PyPIから（準備中）
pip install pypac

# または開発版
git clone https://github.com/yourusername/pypac.git
cd pypac
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

## 🎯 使い方

### Level 1: 超簡単 - 関数API

**最も簡単な方法** - 初心者向け

```python
import pypac

# 📝 5秒間録音して保存（システム全体）
pypac.record_to_file("my_recording.wav", duration=5)

# 🎯 特定アプリの音声のみ録音（NEW!）
pypac.record_process("spotify", "spotify_only.wav", duration=10)

# 🔊 アクティブなアプリを確認
apps = pypac.get_active_apps()
print(f"音声再生中: {apps}")

# 🎚️ Spotifyの音量を50%に
pypac.set_app_volume("spotify", 0.5)

# 🔍 Firefoxの情報を取得
firefox = pypac.find_app("firefox")
if firefox:
    print(f"Firefox音量: {firefox['volume_percent']}%")

# 📊 全セッションをリスト
sessions = pypac.list_audio_sessions()
for s in sessions:
    print(f"{s['process_name']}: {s['volume_percent']}%")
# 出力例:
# firefox.exe: 50%
# spotify.exe: 100%
# discord.exe: 75%
```

### Level 2: 柔軟 - クラスAPI

**より細かい制御** - 中級者向け

```python
import pypac

# セッション管理
manager = pypac.SessionManager()

# アクティブなセッションを取得
active = manager.get_active_sessions()
for session in active:
    print(f"🎵 {session.process_name}")
    print(f"   音量: {session.volume * 100:.0f}%")
    print(f"   ミュート: {session.is_muted}")

# 特定アプリを検索して制御
discord = manager.find_session("discord")
if discord:
    manager.set_volume("discord", 0.3)  # 30%に設定
    manager.mute_session("discord", True)  # ミュート

# オーディオ録音（詳細制御）
recorder = pypac.AudioRecorder()
recorder.start(duration=10)

while recorder.is_recording:
    print(f"録音中... {recorder.recording_time:.1f}秒 "
          f"({recorder.sample_count} サンプル)")
    time.sleep(1)

audio_data = recorder.stop()
if len(audio_data) > 0:
    pypac.utils.save_to_wav(audio_data, "detailed_recording.wav")
    print(f"録音保存: {len(audio_data)} サンプル")
```

### Level 3: 完全制御 - ネイティブAPI

**最大限の制御** - 上級者向け

<details>
<summary>クリックして展開</summary>

```python
import pypac._native as native
import numpy as np

# 低レベルセッション列挙
enumerator = native.SessionEnumerator()
sessions = enumerator.enumerate_sessions()

for session in sessions:
    if session.state == 1:  # AudioSessionStateActive
        print(f"PID {session.process_id}: {session.process_name}")
        
        # 直接ボリューム制御
        enumerator.set_session_volume(session.process_id, 0.5)
        enumerator.set_session_mute(session.process_id, False)

# 低レベルループバック録音
loopback = native.SimpleLoopback()
if loopback.start():
    time.sleep(5)
    
    # NumPy配列として取得
    audio_buffer = loopback.get_buffer()
    
    # カスタム処理
    rms = np.sqrt(np.mean(audio_buffer**2))
    peak = np.max(np.abs(audio_buffer))
    
    loopback.stop()
```

</details>

---

## 💡 実用例

### 🎮 ゲーム配信用オーディオミキサー

```python
import pypac

class StreamAudioMixer:
    """配信用のオーディオバランス調整"""
    
    def __init__(self):
        self.manager = pypac.SessionManager()
    
    def setup_streaming(self):
        """配信用の音量設定"""
        # ゲーム音を70%
        pypac.set_app_volume("game", 0.7)
        
        # Discord を30%
        pypac.set_app_volume("discord", 0.3)
        
        # Spotify をミュート
        pypac.mute_app("spotify")
        
        print("✅ 配信用オーディオ設定完了！")
    
    def save_all_audio(self, duration=60):
        """システム音声を録音（全アプリの混合音声）"""
        pypac.record_to_file(f"recording_{time.time()}.wav", duration)
    
    def save_game_audio_only(self, game_name="game.exe", duration=60):
        """ゲーム音声のみを録音（Discord音声を除外）"""
        # Process Loopback APIでゲーム音声のみ録音！
        pypac.record_process(game_name, f"game_only_{time.time()}.wav", duration)
        print("✅ ゲーム音声のみ録音完了（Discord音声なし！）")

# 使用例
mixer = StreamAudioMixer()
mixer.setup_streaming()
```

### 📊 リアルタイムオーディオメーター

```python
import pypac
import time

def audio_meter(duration=30):
    """ビジュアルオーディオメーター"""
    recorder = pypac.AudioRecorder()
    recorder.start(duration=duration)
    
    print("🎵 オーディオレベルメーター")
    print("-" * 50)
    
    while recorder.is_recording:
        buffer = recorder.get_buffer()
        if len(buffer) > 0:
            # RMS計算
            rms = pypac.utils.calculate_rms(buffer)
            db = pypac.utils.calculate_db(buffer)
            
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
import pypac
import schedule

def auto_adjust_volume():
    """時間帯による自動音量調整"""
    import datetime
    
    hour = datetime.datetime.now().hour
    
    if 22 <= hour or hour < 6:
        # 深夜は全体的に音量を下げる
        for app in pypac.get_active_apps():
            pypac.set_app_volume(app, 0.3)
        print("🌙 深夜モード: 音量30%")
    
    elif 9 <= hour < 17:
        # 仕事時間はビデオ会議アプリを優先
        pypac.set_app_volume("zoom", 1.0)
        pypac.set_app_volume("teams", 1.0)
        pypac.set_app_volume("spotify", 0.2)
        print("💼 仕事モード: 会議優先")
    
    else:
        # 通常時間
        for app in pypac.get_active_apps():
            pypac.set_app_volume(app, 0.7)
        print("🏠 通常モード: 音量70%")

# スケジュール設定
schedule.every().hour.do(auto_adjust_volume)
```

---

## 📚 APIリファレンス

### 🟢 簡単関数API

| 関数 | 説明 | 例 |
|------|------|-----|
| `record_to_file(filename, duration)` | 音声を録音してファイルに保存 | `pypac.record_to_file("out.wav", 5)` |
| `list_audio_sessions()` | 全オーディオセッション取得 | `sessions = pypac.list_audio_sessions()` |
| `get_active_apps()` | アクティブなアプリ名リスト | `apps = pypac.get_active_apps()` |
| `set_app_volume(app, volume)` | アプリ音量設定 (0.0-1.0) | `pypac.set_app_volume("chrome", 0.5)` |
| `get_app_volume(app)` | アプリ音量取得 | `vol = pypac.get_app_volume("chrome")` |
| `mute_app(app)` | アプリをミュート | `pypac.mute_app("spotify")` |
| `unmute_app(app)` | ミュート解除 | `pypac.unmute_app("spotify")` |
| `find_app(app)` | アプリ情報取得 | `info = pypac.find_app("firefox")` |

### 🔵 クラスAPI

#### SessionManager

```python
manager = pypac.SessionManager()
```

| メソッド | 説明 |
|---------|------|
| `list_sessions(active_only=False)` | セッション一覧取得 |
| `find_session(app_name)` | アプリ検索 |
| `set_volume(app_name, volume)` | 音量設定 |
| `mute_session(app_name, mute)` | ミュート制御 |
| `get_active_sessions()` | アクティブセッション取得 |

#### AudioRecorder

```python
recorder = pypac.AudioRecorder()
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
<summary>❌ ImportError: No module named 'pypac'</summary>

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
import pypac
print(f"PyPAC Version: {pypac.__version__}")

# オーディオセッション診断
sessions = pypac.list_audio_sessions()
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
git clone https://github.com/yourusername/pypac.git
cd pypac

# 開発環境構築
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]

# テスト実行
pytest tests/

# コード品質チェック
black pypac/
pylint pypac/
mypy pypac/
```

### アーキテクチャ

```
pypac/
├── pypac/              # Pythonパッケージ
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

## 📄 ライセンス

MIT License - 詳細は[LICENSE](LICENSE)参照

## 🙏 謝辞

- [pybind11](https://github.com/pybind/pybind11) - 優れたC++バインディング
- [OBS Studio](https://obsproject.com/) - オーディオキャプチャの参考実装
- Windows Audio APIチーム - 詳細なドキュメント

