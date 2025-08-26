# PyWAC API Reference

## Core Functions

### Audio Recording

#### `record_audio(duration: float) -> AudioData`
Record system-wide audio for a specified duration.

**Parameters:**
- `duration`: Recording duration in seconds

**Returns:**
- `AudioData` object containing the recorded audio

**Example:**
```python
audio_data = pywac.record_audio(5)  # Record 5 seconds
audio_data.save("output.wav")
```

---

#### `record_to_file(filename: str, duration: float) -> bool`
Record system-wide audio directly to a WAV file.

**Parameters:**
- `filename`: Output WAV filename
- `duration`: Recording duration in seconds

**Returns:**
- True if successful

**Example:**
```python
pywac.record_to_file("output.wav", 10)  # Record 10 seconds
```

---

#### `record_process(process_name: str, filename: str, duration: float) -> bool`
Record audio from a specific process only (Windows 10 2004+).

**Parameters:**
- `process_name`: Name or partial name of the process
- `filename`: Output WAV filename
- `duration`: Recording duration in seconds

**Returns:**
- True if successful, False otherwise

**Requirements:**
- Windows 10 version 2004 (Build 19041) or later
- Process Loopback API support

**Example:**
```python
pywac.record_process("spotify", "spotify_audio.wav", 10)
```

---

#### `record_process_id(pid: int, filename: str, duration: float) -> bool`
Record audio from a specific process by PID (Windows 10 2004+).

**Parameters:**
- `pid`: Process ID (use 0 for system-wide recording)
- `filename`: Output WAV filename
- `duration`: Recording duration in seconds

**Returns:**
- True if successful, False otherwise

**Example:**
```python
pywac.record_process_id(12345, "app_audio.wav", 10)
```

---

### Session Management

#### `list_audio_sessions(active_only: bool = False) -> List[Dict[str, Any]]`
List all audio sessions.

**Parameters:**
- `active_only`: If True, only return active sessions

**Returns:**
- List of session information dictionaries

**Example:**
```python
sessions = pywac.list_audio_sessions()
for session in sessions:
    print(f"{session['process_name']}: {session['volume_percent']}%")
```

---

#### `list_recordable_processes() -> List[Dict[str, Any]]`
List all processes that can be recorded (have audio sessions).

**Returns:**
- List of process information dictionaries with 'pid' and 'name' keys

**Example:**
```python
processes = pywac.list_recordable_processes()
for proc in processes:
    print(f"{proc['name']} (PID: {proc['pid']})")
```

---

#### `find_audio_session(app_name: str) -> Optional[Dict[str, Any]]`
Find an audio session by application name.

**Parameters:**
- `app_name`: Name or partial name of the application

**Returns:**
- Session information dictionary, or None if not found

**Example:**
```python
info = pywac.find_audio_session("firefox")
if info:
    print(f"Firefox is {'active' if info['is_active'] else 'inactive'}")
```

---

#### `get_active_sessions() -> List[str]`
Get list of process names currently playing audio.

**Returns:**
- List of process names with active audio sessions

**Example:**
```python
active = pywac.get_active_sessions()
print(f"Active sessions: {', '.join(active)}")
```

---

### Volume Control

#### `set_app_volume(app_name: str, volume: float) -> bool`
Set the volume for an application.

**Parameters:**
- `app_name`: Name or partial name of the application
- `volume`: Volume level (0.0 to 1.0)

**Returns:**
- True if successful, False otherwise

**Example:**
```python
pywac.set_app_volume("firefox", 0.5)  # Set Firefox to 50%
```

---

#### `get_app_volume(app_name: str) -> Optional[float]`
Get the current volume for an application.

**Parameters:**
- `app_name`: Name or partial name of the application

**Returns:**
- Volume level (0.0 to 1.0), or None if app not found

**Example:**
```python
volume = pywac.get_app_volume("firefox")
print(f"Firefox volume: {volume * 100:.0f}%")
```

---

#### `adjust_volume(app_name: str, delta: float) -> Optional[float]`
Adjust an application's volume by a delta value.

**Parameters:**
- `app_name`: Name or partial name of the application
- `delta`: Volume change (-1.0 to 1.0)

**Returns:**
- New volume level, or None if app not found

**Example:**
```python
new_volume = pywac.adjust_volume("spotify", 0.1)  # Increase by 10%
```

---

#### `mute_app(app_name: str) -> bool`
Mute an application.

**Parameters:**
- `app_name`: Name or partial name of the application

**Returns:**
- True if successful, False otherwise

**Example:**
```python
pywac.mute_app("discord")
```

---

#### `unmute_app(app_name: str) -> bool`
Unmute an application.

**Parameters:**
- `app_name`: Name or partial name of the application

**Returns:**
- True if successful, False otherwise

**Example:**
```python
pywac.unmute_app("discord")
```

---

## Classes

### AudioData
Unified audio data container (v0.3.0+).

#### Constructor
```python
AudioData(samples: np.ndarray, sample_rate: int = 48000, channels: int = 2)
```

#### Properties
- `samples`: NumPy array of audio samples
- `sample_rate`: Sample rate in Hz
- `channels`: Number of channels
- `num_frames`: Number of audio frames
- `duration`: Duration in seconds
- `dtype`: Data type of samples

#### Methods
- `save(filename: str) -> None`: Save to WAV file
- `to_mono() -> AudioData`: Convert to mono
- `resample(target_rate: int) -> AudioData`: Resample audio
- `normalize(peak: float = 1.0) -> AudioData`: Normalize audio
- `get_statistics() -> Dict`: Get audio statistics (RMS, peak, etc.)
- `@classmethod create_empty() -> AudioData`: Create empty AudioData

---

### QueueBasedStreamingCapture
High-performance streaming audio capture with adaptive polling (v0.4.0+).

#### Constructor
```python
QueueBasedStreamingCapture(
    process_id: int = 0,
    chunk_duration: float = 0.01,
    on_audio: Optional[Callable[[AudioData], None]] = None,
    queue_size: int = 1000,
    batch_size: int = 10
)
```

#### Parameters
- `process_id`: Process ID to capture (0 for system-wide)
- `chunk_duration`: Duration of each chunk in seconds (default: 10ms)
- `on_audio`: Callback for streaming audio chunks
- `queue_size`: Maximum queue size in C++
- `batch_size`: Number of chunks to pop at once

#### Methods
- `start() -> bool`: Start audio capture
- `stop() -> AudioData`: Stop capture and return accumulated audio
- `get_metrics() -> Dict`: Get performance metrics

#### Example
```python
from pywac.queue_streaming import QueueBasedStreamingCapture

def on_audio_chunk(audio: AudioData):
    print(f"Received {audio.duration:.3f}s of audio")

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
High-level interface for audio recording.

#### Constructor
```python
AudioRecorder(sample_rate: int = 48000, channels: int = 2)
```

#### Methods
- `start(duration: Optional[float] = None) -> bool`: Start recording
- `stop() -> AudioData`: Stop recording and return audio data
- `record(duration: float) -> AudioData`: Record for specified duration (blocking)
- `record_to_file(filename: str, duration: float) -> bool`: Record directly to file
- `save(filename: Optional[str] = None) -> str`: Save current recording to file

#### Properties
- `is_recording`: Check if currently recording
- `recording_time`: Get current recording time in seconds
- `sample_count`: Get current number of recorded samples

---

### SessionManager
High-level interface for managing audio sessions.

#### Methods
- `list_sessions(active_only: bool = False) -> List[AudioSession]`: List all sessions
- `find_session(app_name: str) -> Optional[AudioSession]`: Find session by name
- `set_volume(app_name: str, volume: float) -> bool`: Set volume
- `get_volume(app_name: str) -> Optional[float]`: Get volume
- `set_mute(app_name: str, mute: bool) -> bool`: Set mute state

---

### AudioSession
Represents an audio session for a Windows process.

#### Properties
- `process_id`: Process ID
- `process_name`: Process name
- `state`: Session state (0: Inactive, 1: Active, 2: Expired)
- `volume`: Volume level (0.0 to 1.0)
- `is_active`: Check if actively playing audio
- `is_muted`: Check if muted

---

## Low-Level Modules

### process_loopback_queue
C++ module for queue-based process audio capture (v0.4.0+).

#### Functions
- `list_audio_processes() -> List[ProcessInfo]`: List processes that might produce audio
  
#### Classes

##### QueueBasedProcessCapture
Low-level queue-based capture interface.

**Methods:**
- `start(process_id: int) -> bool`: Start capturing
- `stop() -> None`: Stop capturing
- `set_chunk_size(frames: int) -> None`: Set chunk size (before start)
- `pop_chunks(max_chunks: int = 10, timeout_ms: int = 10) -> List[Dict]`: Pop chunks from queue
- `pop_chunk(timeout_ms: int = 10) -> Optional[Dict]`: Pop single chunk
- `queue_size() -> int`: Get current queue size
- `is_capturing() -> bool`: Check if currently capturing
- `get_metrics() -> Dict`: Get performance metrics

**Chunk Dictionary Format:**
```python
{
    "data": np.ndarray,      # Audio samples (frames, 2)
    "silent": bool,           # Whether chunk is silent
    "timestamp": int          # Microseconds since epoch
}
```

---

### process_loopback_v2 (Deprecated)
Polling-based process capture. Use `process_loopback_queue` instead.

### process_loopback_v3 (Experimental)
Callback-based capture. Has GIL issues - use `process_loopback_queue` instead.

---

## Utility Functions

### `save_to_wav(audio_data: AudioData, filename: str) -> None`
Save AudioData to WAV file.

### `capture_process_audio(process_id: int = 0, duration: float = 5.0, on_audio: Optional[Callable] = None) -> AudioData`
Convenience function for simple audio capture.

**Parameters:**
- `process_id`: Process ID (0 for system-wide)
- `duration`: Duration to capture in seconds
- `on_audio`: Optional callback for streaming

**Returns:**
- `AudioData` object with captured audio

**Example:**
```python
from pywac.queue_streaming import capture_process_audio

# Simple capture
audio = capture_process_audio(spotify_pid, duration=10)
audio.save("spotify_10s.wav")

# With streaming callback
def on_chunk(audio):
    print(f"RMS: {audio.get_statistics()['rms_db']:.1f} dB")

audio = capture_process_audio(0, duration=5, on_audio=on_chunk)
```

---

## Performance Metrics

The queue-based implementation provides detailed metrics:

```python
capture = QueueBasedStreamingCapture(process_id=0)
capture.start()
time.sleep(5)
audio = capture.stop()

metrics = capture.get_metrics()
print(f"Total chunks: {metrics['total_chunks']}")
print(f"Dropped chunks: {metrics['dropped_chunks']}")
print(f"Poll efficiency: {metrics['efficiency']:.2f} chunks/poll")
print(f"Current interval: {metrics['current_interval_ms']:.1f}ms")
```

Typical metrics:
- CPU usage: < 5%
- Polling interval: 1-20ms (adaptive)
- Latency: ~10ms
- Drop rate: 0%

---

## Migration Guide

### From v0.2.x to v0.4.x

1. **AudioData Return Type**: Functions now return `AudioData` objects instead of lists:
```python
# Old (v0.2.x)
samples = pywac.record_audio(5)
save_to_wav(samples, "output.wav")

# New (v0.4.x)
audio = pywac.record_audio(5)
audio.save("output.wav")
```

2. **Process Capture**: Use queue-based implementation:
```python
# Old (polling)
import process_loopback_v2 as loopback
capture = loopback.ProcessCapture()

# New (queue-based)
from pywac.queue_streaming import QueueBasedStreamingCapture
capture = QueueBasedStreamingCapture(process_id=pid)
```

3. **Streaming**: New callback interface:
```python
# New streaming with callbacks
def on_audio(audio: AudioData):
    stats = audio.get_statistics()
    print(f"RMS: {stats['rms_db']:.1f} dB")

capture = QueueBasedStreamingCapture(
    process_id=0,
    on_audio=on_audio
)
```

---

## Version History

- **v0.4.0**: Queue-based architecture, resolved GIL issues, < 5% CPU usage
- **v0.3.0**: AudioData class, unified format handling
- **v0.2.0**: Process Loopback API implementation
- **v0.1.0**: Initial release with WASAPI support