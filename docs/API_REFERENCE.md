# PyPAC API Reference

## Core Functions

### Audio Recording

#### `record_audio(duration: float) -> List[float]`
Record system-wide audio for a specified duration.

**Parameters:**
- `duration`: Recording duration in seconds

**Returns:**
- List of audio samples (float32)

**Example:**
```python
audio_data = pypac.record_audio(5)  # Record 5 seconds
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
pypac.record_to_file("output.wav", 10)  # Record 10 seconds
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
pypac.record_process("spotify", "spotify_audio.wav", 10)
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
pypac.record_process_id(12345, "app_audio.wav", 10)
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
sessions = pypac.list_audio_sessions()
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
processes = pypac.list_recordable_processes()
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
info = pypac.find_audio_session("firefox")
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
active = pypac.get_active_sessions()
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
pypac.set_app_volume("firefox", 0.5)  # Set Firefox to 50%
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
volume = pypac.get_app_volume("firefox")
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
new_volume = pypac.adjust_volume("spotify", 0.1)  # Increase by 10%
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
pypac.mute_app("discord")
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
pypac.unmute_app("discord")
```

---

## Classes

### AudioRecorder
High-level interface for audio recording.

#### Constructor
```python
AudioRecorder(sample_rate: int = 48000, channels: int = 2)
```

#### Methods

- `start(duration: Optional[float] = None) -> bool`: Start recording
- `stop() -> List[float]`: Stop recording and return audio data
- `record(duration: float) -> List[float]`: Record for specified duration (blocking)
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

## Utility Functions

### `save_to_wav(audio_data, filename, sample_rate=48000, channels=2)`
Save audio data to WAV file.

### `convert_float32_to_int16(audio_data)`
Convert float32 audio to int16 format.

---

## Deprecated Functions

The following functions are deprecated but maintained for backward compatibility:

- `find_app()` → Use `find_audio_session()` instead
- `get_active_apps()` → Use `get_active_sessions()` instead