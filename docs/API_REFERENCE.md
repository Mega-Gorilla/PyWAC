# PyWAC API リファレンス

## コア関数

### オーディオ録音

#### `record_audio(duration: float) -> AudioData`
指定した時間だけシステム全体のオーディオを録音します。

**パラメータ:**
- `duration`: 録音時間（秒）

**戻り値:**
- 録音されたオーディオを含む`AudioData`オブジェクト

**例:**
```python
audio_data = pywac.record_audio(5)  # 5秒間録音
audio_data.save("output.wav")
```

---

#### `record_to_file(filename: str, duration: float) -> bool`
システム全体のオーディオを直接WAVファイルに録音します。

**パラメータ:**
- `filename`: 出力WAVファイル名
- `duration`: 録音時間（秒）

**戻り値:**
- 成功時はTrue

**例:**
```python
pywac.record_to_file("output.wav", 10)  # 10秒間録音
```

---

#### `record_process(process_name: str, filename: str, duration: float) -> bool`
特定のプロセスからのみオーディオを録音します（Windows 10 2004以降）。

**パラメータ:**
- `process_name`: プロセス名または部分名
- `filename`: 出力WAVファイル名
- `duration`: 録音時間（秒）

**戻り値:**
- 成功時はTrue、失敗時はFalse

**必要要件:**
- Windows 10 バージョン2004（ビルド19041）以降
- Process Loopback APIサポート

**例:**
```python
pywac.record_process("spotify", "spotify_audio.wav", 10)
```

---

#### `record_process_id(pid: int, filename: str, duration: float) -> bool`
PIDで特定のプロセスからオーディオを録音します（Windows 10 2004以降）。

**パラメータ:**
- `pid`: プロセスID（0でシステム全体の録音）
- `filename`: 出力WAVファイル名
- `duration`: 録音時間（秒）

**戻り値:**
- 成功時はTrue、失敗時はFalse

**例:**
```python
pywac.record_process_id(12345, "app_audio.wav", 10)
```

---

### セッション管理

#### `list_audio_sessions(active_only: bool = False) -> List[Dict[str, Any]]`
すべてのオーディオセッションを一覧表示します。

**パラメータ:**
- `active_only`: Trueの場合、アクティブなセッションのみを返す

**戻り値:**
- セッション情報の辞書のリスト

**例:**
```python
sessions = pywac.list_audio_sessions()
for session in sessions:
    print(f"{session['process_name']}: {session['volume_percent']}%")
```

---

#### `list_recordable_processes() -> List[Dict[str, Any]]`
録音可能なすべてのプロセス（オーディオセッションを持つ）を一覧表示します。

**戻り値:**
- 'pid'と'name'キーを持つプロセス情報辞書のリスト

**例:**
```python
processes = pywac.list_recordable_processes()
for proc in processes:
    print(f"{proc['name']} (PID: {proc['pid']})")
```

---

#### `find_audio_session(app_name: str) -> Optional[Dict[str, Any]]`
アプリケーション名でオーディオセッションを検索します。

**パラメータ:**
- `app_name`: アプリケーションの名前または部分名

**戻り値:**
- セッション情報辞書、見つからない場合はNone

**例:**
```python
info = pywac.find_audio_session("firefox")
if info:
    print(f"Firefoxは{'アクティブ' if info['is_active'] else '非アクティブ'}です")
```

---

#### `get_active_sessions() -> List[str]`
現在オーディオを再生しているプロセス名のリストを取得します。

**戻り値:**
- アクティブなオーディオセッションを持つプロセス名のリスト

**例:**
```python
active = pywac.get_active_sessions()
print(f"アクティブなセッション: {', '.join(active)}")
```

---

### ボリューム制御

#### `set_app_volume(app_name: str, volume: float) -> bool`
アプリケーションのボリュームを設定します。

**パラメータ:**
- `app_name`: アプリケーションの名前または部分名
- `volume`: ボリュームレベル（0.0〜1.0）

**戻り値:**
- 成功時はTrue、失敗時はFalse

**例:**
```python
pywac.set_app_volume("firefox", 0.5)  # Firefoxを50%に設定
```

---

#### `get_app_volume(app_name: str) -> Optional[float]`
アプリケーションの現在のボリュームを取得します。

**パラメータ:**
- `app_name`: アプリケーションの名前または部分名

**戻り値:**
- ボリュームレベル（0.0〜1.0）、アプリが見つからない場合はNone

**例:**
```python
volume = pywac.get_app_volume("firefox")
print(f"Firefoxのボリューム: {volume * 100:.0f}%")
```

---

#### `adjust_volume(app_name: str, delta: float) -> Optional[float]`
アプリケーションのボリュームをデルタ値で調整します。

**パラメータ:**
- `app_name`: アプリケーションの名前または部分名
- `delta`: ボリューム変更量（-1.0〜1.0）

**戻り値:**
- 新しいボリュームレベル、アプリが見つからない場合はNone

**例:**
```python
new_volume = pywac.adjust_volume("spotify", 0.1)  # 10%増加
```

---

#### `mute_app(app_name: str) -> bool`
アプリケーションをミュートします。

**パラメータ:**
- `app_name`: アプリケーションの名前または部分名

**戻り値:**
- 成功時はTrue、失敗時はFalse

**例:**
```python
pywac.mute_app("discord")
```

---

#### `unmute_app(app_name: str) -> bool`
アプリケーションのミュートを解除します。

**パラメータ:**
- `app_name`: アプリケーションの名前または部分名

**戻り値:**
- 成功時はTrue、失敗時はFalse

**例:**
```python
pywac.unmute_app("discord")
```

---

## クラス

### AudioData
統一されたオーディオデータコンテナ（v0.3.0以降）。

#### コンストラクタ
```python
AudioData(samples: np.ndarray, sample_rate: int = 48000, channels: int = 2)
```

#### プロパティ
- `samples`: オーディオサンプルのNumPy配列
- `sample_rate`: サンプルレート（Hz）
- `channels`: チャンネル数
- `num_frames`: オーディオフレーム数
- `duration`: 秒単位の期間
- `dtype`: サンプルのデータ型

#### メソッド
- `save(filename: str) -> None`: WAVファイルに保存
- `to_mono() -> AudioData`: モノラルに変換
- `resample(target_rate: int) -> AudioData`: オーディオをリサンプリング
- `normalize(peak: float = 1.0) -> AudioData`: オーディオを正規化
- `get_statistics() -> Dict`: オーディオ統計（RMS、ピークなど）を取得
- `@classmethod create_empty() -> AudioData`: 空のAudioDataを作成

---

### QueueBasedStreamingCapture
アダプティブポーリングによる高性能ストリーミングオーディオキャプチャ（v0.4.0以降）。

#### コンストラクタ
```python
QueueBasedStreamingCapture(
    process_id: int = 0,
    chunk_duration: float = 0.01,
    on_audio: Optional[Callable[[AudioData], None]] = None,
    queue_size: int = 1000,
    batch_size: int = 10
)
```

#### パラメータ
- `process_id`: キャプチャするプロセスID（0でシステム全体）
- `chunk_duration`: 各チャンクの秒単位の期間（デフォルト：10ms）
- `on_audio`: ストリーミングオーディオチャンク用のコールバック
- `queue_size`: C++での最大キューサイズ
- `batch_size`: 一度にポップするチャンク数

#### メソッド
- `start() -> bool`: オーディオキャプチャを開始
- `stop() -> AudioData`: キャプチャを停止し、蓄積されたオーディオを返す
- `get_metrics() -> Dict`: パフォーマンスメトリクスを取得

#### 例
```python
from pywac.queue_streaming import QueueBasedStreamingCapture

def on_audio_chunk(audio: AudioData):
    print(f"{audio.duration:.3f}秒のオーディオを受信")

capture = QueueBasedStreamingCapture(
    process_id=spotify_pid,
    on_audio=on_audio_chunk
)

if capture.start():
    time.sleep(5)
    audio = capture.stop()
    audio.save("captured.wav")
```

---

### AudioRecorder
オーディオ録音用の高レベルインターフェース。

#### コンストラクタ
```python
AudioRecorder(sample_rate: int = 48000, channels: int = 2)
```

#### メソッド
- `start(duration: Optional[float] = None) -> bool`: 録音開始
- `stop() -> AudioData`: 録音停止し、オーディオデータを返す
- `record(duration: float) -> AudioData`: 指定時間録音（ブロッキング）
- `record_to_file(filename: str, duration: float) -> bool`: ファイルに直接録音
- `save(filename: Optional[str] = None) -> str`: 現在の録音をファイルに保存

#### プロパティ
- `is_recording`: 現在録音中かチェック
- `recording_time`: 現在の録音時間を秒単位で取得
- `sample_count`: 現在の録音サンプル数を取得

---

### SessionManager
オーディオセッション管理用の高レベルインターフェース。

#### メソッド
- `list_sessions(active_only: bool = False) -> List[AudioSession]`: すべてのセッションを一覧表示
- `find_session(app_name: str) -> Optional[AudioSession]`: 名前でセッションを検索
- `set_volume(app_name: str, volume: float) -> bool`: ボリュームを設定
- `get_volume(app_name: str) -> Optional[float]`: ボリュームを取得
- `set_mute(app_name: str, mute: bool) -> bool`: ミュート状態を設定

---

### AudioSession
Windowsプロセスのオーディオセッションを表します。

#### プロパティ
- `process_id`: プロセスID
- `process_name`: プロセス名
- `state`: セッション状態（0: 非アクティブ、1: アクティブ、2: 期限切れ）
- `volume`: ボリュームレベル（0.0〜1.0）
- `is_active`: アクティブにオーディオを再生しているかチェック
- `is_muted`: ミュートされているかチェック

---

## 低レベルモジュール

### pywac.capture
プロセス固有オーディオキャプチャ用のネイティブモジュール（v1.0.0以降）。
SetEventHandle APIを使用してゼロポーリングを実現。

#### 関数
- `list_audio_processes() -> List[ProcessInfo]`: オーディオを生成する可能性のあるプロセスを一覧表示
  
#### クラス

##### QueueBasedProcessCapture
低レベルのキューベースキャプチャインターフェース。

**メソッド:**
- `start(process_id: int) -> bool`: キャプチャ開始
- `stop() -> None`: キャプチャ停止
- `set_chunk_size(frames: int) -> None`: チャンクサイズ設定（開始前）
- `pop_chunks(max_chunks: int = 10, timeout_ms: int = 10) -> List[Dict]`: キューからチャンクをポップ
- `pop_chunk(timeout_ms: int = 10) -> Optional[Dict]`: 単一チャンクをポップ
- `queue_size() -> int`: 現在のキューサイズを取得
- `is_capturing() -> bool`: 現在キャプチャ中かチェック
- `get_metrics() -> Dict`: パフォーマンスメトリクスを取得

**チャンク辞書フォーマット:**
```python
{
    "data": np.ndarray,      # オーディオサンプル (frames, 2)
    "silent": bool,           # チャンクが無音かどうか
    "timestamp": int          # エポックからのマイクロ秒
}
```

---

### 注意事項
- v1.0.0以降、`pywac.capture`が公式APIです
- 以前のバージョン（process_loopback_v2, process_loopback_v3）は非推奨です

---

## ユーティリティ関数

### `save_to_wav(audio_data: AudioData, filename: str) -> None`
AudioDataをWAVファイルに保存。

### `capture_process_audio(process_id: int = 0, duration: float = 5.0, on_audio: Optional[Callable] = None) -> AudioData`
シンプルなオーディオキャプチャ用の便利関数。

**パラメータ:**
- `process_id`: プロセスID（0でシステム全体）
- `duration`: キャプチャする秒数
- `on_audio`: ストリーミング用のオプションコールバック

**戻り値:**
- キャプチャされたオーディオを含む`AudioData`オブジェクト

**例:**
```python
from pywac.queue_streaming import capture_process_audio

# シンプルなキャプチャ
audio = capture_process_audio(spotify_pid, duration=10)
audio.save("spotify_10s.wav")

# ストリーミングコールバック付き
def on_chunk(audio):
    print(f"RMS: {audio.get_statistics()['rms_db']:.1f} dB")

audio = capture_process_audio(0, duration=5, on_audio=on_chunk)
```

---

## パフォーマンスメトリクス

キューベース実装は詳細なメトリクスを提供します：

```python
capture = QueueBasedStreamingCapture(process_id=0)
capture.start()
time.sleep(5)
audio = capture.stop()

metrics = capture.get_metrics()
print(f"総チャンク数: {metrics['total_chunks']}")
print(f"ドロップされたチャンク: {metrics['dropped_chunks']}")
print(f"ポーリング効率: {metrics['efficiency']:.2f} chunks/poll")
print(f"現在の間隔: {metrics['current_interval_ms']:.1f}ms")
```

典型的なメトリクス（v0.4.1）:
- CPU使用率: < 1%（イベント駆動モード）
- ポーリング間隔: イベント駆動（SetEventHandle使用時）
- レイテンシ: ~10ms
- ドロップ率: 0%
- イベント効率: 100%（イベント駆動モード）

---

## 移行ガイド

### v0.3.x から v0.4.x へ

1. **AudioData戻り値型**: 関数はリストの代わりに`AudioData`オブジェクトを返すようになりました：
```python
# 古い (v0.3.x以前)
samples = pywac.record_audio(5)
save_to_wav(samples, "output.wav")

# 新しい (v0.4.x)
audio = pywac.record_audio(5)
audio.save("output.wav")
```

2. **プロセスキャプチャ**: キューベース実装を使用：
```python
# 新しい (v0.4.0以降)
from pywac.queue_streaming import QueueBasedStreamingCapture
capture = QueueBasedStreamingCapture(process_id=pid)

# または低レベルAPI
from pywac import capture
cap = capture.QueueBasedProcessCapture()
```

3. **ストリーミング**: 新しいコールバックインターフェース：
```python
# 新しいコールバック付きストリーミング
def on_audio(audio: AudioData):
    stats = audio.get_statistics()
    print(f"RMS: {stats['rms_db']:.1f} dB")

capture = QueueBasedStreamingCapture(
    process_id=0,
    on_audio=on_audio
)
```

---

## Unified Recording API (v0.4.2+)

### `pywac.unified_recording.record()`
統一録音関数 - すべての録音モードをサポートする単一のコア関数。

```python
def record(
    duration: float,
    target: Optional[Union[str, int]] = None,
    output_file: Optional[str] = None,
    on_complete: Optional[Callable[[AudioData], None]] = None,
    fallback_enabled: bool = True
) -> Union[AudioData, bool, None]
```

**パラメータ:**
- `duration`: 録音時間（秒）
- `target`: None（システム全体）、プロセス名（str）、またはPID（int）
- `output_file`: 指定した場合、ファイルに保存してboolを返す
- `on_complete`: 指定した場合、非同期実行してコールバックを呼び出す
- `fallback_enabled`: True の場合、失敗時にネイティブレコーダーにフォールバック

**戻り値:**
- コールバック指定時: None（非同期実行）
- ファイル名指定時: bool（成功/失敗）
- それ以外: AudioDataオブジェクト

**例:**
```python
from pywac.unified_recording import record

# システム録音
audio = record(5)

# プロセス録音
audio = record(5, target="firefox")
success = record(5, target="spotify", output_file="spotify.wav")

# 非同期録音
record(5, on_complete=lambda audio: audio.save("async.wav"))
```

### `pywac.unified_recording.Recorder`
クリーンなクラスベースの録音インターフェース。

```python
# Firefoxのレコーダーを作成
recorder = Recorder(target="firefox")

if recorder.is_available():
    # 同期録音
    audio = recorder.record(5)
    
    # ファイルへ直接録音
    recorder.record_to_file(5, "firefox.wav")
    
    # 非同期録音
    recorder.record_async(5, callback_function)
```

---

## バージョン履歴

- **v0.4.2**: 統一録音API、すべての録音モードを単一関数に統合
- **v0.4.1**: イベント駆動キャプチャ（SetEventHandle）、CPU使用率 < 1%
- **v0.4.0**: キューベースアーキテクチャ、GIL問題解決、CPU使用率 < 5%
- **v0.3.0**: AudioDataクラス、統一フォーマット処理
- **v0.2.0**: Process Loopback API実装
- **v0.1.0**: WASAPI サポートを含む初期リリース