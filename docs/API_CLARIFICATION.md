# PyWAC API 明確化ドキュメント

## 録音APIの使い分け

### 1. バッチ録音（固定時間の録音）

#### UnifiedRecorder（推奨）
```python
from pywac import UnifiedRecorder

# システム全体の録音
recorder = UnifiedRecorder()
audio_data = recorder.record(duration=5.0)  # 5秒間録音

# 特定プロセスの録音
recorder = UnifiedRecorder(target="spotify")
audio_data = recorder.record(duration=10.0)

# ファイルに直接録音
success = recorder.record_to_file(duration=5.0, filename="output.wav")

# 非同期録音（コールバック付き）
def on_complete(audio_data):
    print(f"録音完了: {audio_data.duration}秒")
    audio_data.save("async_recording.wav")

recorder.record_async(duration=5.0, callback=on_complete)
```

**注意**: UnifiedRecorderには以下のメソッドは**存在しません**：
- ❌ `start_recording()` - 存在しない
- ❌ `stop_recording()` - 存在しない
- ❌ `get_buffer()` - 存在しない

### 2. リアルタイムストリーミング録音（連続録音）

#### QueueBasedProcessCapture（低レベルAPI）
```python
from pywac import capture

# リアルタイムストリーミング用
capture = capture.QueueBasedProcessCapture()
capture.set_chunk_size(2400)  # 50ms chunks at 48kHz

# 録音開始（非ブロッキング）
if capture.start(process_id):  # PID指定、0でシステム全体
    # 連続的にチャンクを取得
    while capture.is_capturing():
        chunks = capture.pop_chunks(max_chunks=10, timeout_ms=10)
        for chunk in chunks:
            if not chunk['silent']:
                audio_data = chunk['data']  # NumPy array
                # リアルタイム処理...
                process_audio(audio_data)
    
    capture.stop()
```

#### gradio_demo.pyでの実装例
```python
# リアルタイム録音の正しい実装
class RecordingManager:
    def start_realtime_recording(self, duration: int, process_id: int = 0):
        """リアルタイム録音開始"""
        # QueueBasedProcessCaptureを使用（UnifiedRecorderではない！）
        self.realtime_capture = capture.QueueBasedProcessCapture()
        self.realtime_capture.set_chunk_size(int(48000 * 0.05))  # 50ms chunks
        
        if self.realtime_capture.start(process_id):
            # ポーリングスレッド開始
            self.polling_thread = threading.Thread(
                target=self._realtime_polling_loop,
                daemon=True
            )
            self.polling_thread.start()
```

## APIの使い分けガイドライン

### UnifiedRecorderを使うべき場合：
- ✅ 固定時間の録音が必要
- ✅ 録音完了後に一括でデータを処理
- ✅ シンプルなAPI が必要
- ✅ 高レベルの抽象化が必要

### QueueBasedProcessCaptureを使うべき場合：
- ✅ リアルタイムストリーミングが必要
- ✅ 連続的な録音が必要
- ✅ チャンク単位での処理が必要
- ✅ 低遅延が重要
- ✅ 循環バッファでの実装が必要

## よくある間違い

### ❌ 間違い1: UnifiedRecorderでリアルタイムストリーミング
```python
# 間違い - UnifiedRecorderはバッチ録音用
recorder = UnifiedRecorder()
recorder.start_recording()  # このメソッドは存在しない！
while True:
    buffer = recorder.get_buffer()  # このメソッドも存在しない！
```

### ✅ 正しい実装: QueueBasedProcessCaptureを使用
```python
# 正しい - リアルタイムにはQueueBasedProcessCapture
capture = capture.QueueBasedProcessCapture()
capture.start(process_id)
while capture.is_capturing():
    chunks = capture.pop_chunks()
    # チャンクを処理...
```

### ❌ 間違い2: SimpleLoopbackでプロセス固有録音
```python
# 間違い - SimpleLoopbackはシステム全体のみ
loopback = native.SimpleLoopback()
loopback.start(process_id=1234)  # process_idパラメータは存在しない！
```

### ✅ 正しい実装: プロセス固有にはQueueBasedProcessCapture
```python
# 正しい - プロセス固有録音
capture = capture.QueueBasedProcessCapture()
capture.start(1234)  # プロセスID指定
```

## まとめ

| 用途 | 推奨API | メソッド |
|------|---------|----------|
| 固定時間のシステム録音 | UnifiedRecorder | `record()` |
| 固定時間のプロセス録音 | UnifiedRecorder | `record()` |
| リアルタイムストリーミング | QueueBasedProcessCapture | `start()` + `pop_chunks()` |
| 低レベルシステム録音 | SimpleLoopback | `start()` + `get_buffer()` |

## 将来の改善提案

1. **ストリーミング対応のUnifiedRecorder**
   ```python
   # 将来的な実装案
   class StreamingRecorder(UnifiedRecorder):
       def start_streaming(self) -> None:
           """ストリーミング開始"""
       
       def get_chunk(self, timeout_ms: int = 10) -> Optional[AudioData]:
           """次のチャンクを取得"""
       
       def stop_streaming(self) -> None:
           """ストリーミング停止"""
   ```

2. **統一されたファクトリーメソッド**
   ```python
   # 用途に応じて適切な実装を返す
   def create_recorder(mode="batch", target=None):
       if mode == "batch":
           return UnifiedRecorder(target)
       elif mode == "streaming":
           return StreamingRecorder(target)  # 将来実装
   ```

このドキュメントは2024年1月時点のPyWAC v0.4.2の実装に基づいています。