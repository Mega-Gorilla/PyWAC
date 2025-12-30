# Release Notes

## Version 1.0.0 (2024-12-30)

### 🎯 Public API Release - Module Renaming

PyWAC v1.0.0 marks the transition to stable public APIs with cleaner module names. This is a **breaking change** release that establishes the foundation for future development.

### 🚨 Breaking Changes

#### Native Module Renaming

| Old Name (v0.4.x) | New Name (v1.0.0) |
|-------------------|-------------------|
| `pywac._pywac_native` | `pywac.core` |
| `process_loopback_queue` | `pywac.capture` |

#### Migration Required

```python
# Old (v0.4.x)
import process_loopback_queue as loopback
cap = loopback.QueueBasedProcessCapture()

# New (v1.0.0)
from pywac import capture
cap = capture.QueueBasedProcessCapture()
```

### ✨ What's New

- **Public APIs**: `pywac.core` and `pywac.capture` are now official public APIs
- **Singleton SessionManager**: Thread-safe session management with automatic initialization
- **`refresh_sessions()`**: New function to re-enumerate audio sessions without restarting
- **Simplified Imports**: No more `sys.path` manipulation needed

### 📦 Module Overview (v1.0.0)

| Module | Description |
|--------|-------------|
| `pywac.core` | Session enumeration, system loopback capture |
| `pywac.capture` | Process-specific audio capture |
| `pywac.audio_data` | Unified audio data container |

### ⚠️ Deprecation Warnings

The following functions now emit deprecation warnings:
- `find_app()` - Use `find_audio_session()` instead
- `get_active_apps()` - Use `get_active_sessions()` instead

### 🔄 Compatibility

- **Not compatible** with v0.4.x import statements
- All functionality preserved, only import paths changed
- See migration guide for upgrade instructions

### 📚 Migration Guide

See [`docs/migrations/v1.0.0-module-rename.md`](docs/migrations/v1.0.0-module-rename.md) for detailed migration instructions.

---

## Version 0.4.1 (2024-12-26)

### 🚀 Event-Driven Capture - Ultimate Performance

PyWAC v0.4.1 implements true event-driven audio capture using WASAPI's SetEventHandle API, achieving < 1% CPU usage - the theoretical minimum for audio capture on Windows.

### 🎯 Key Achievement

**SetEventHandle works perfectly with Process Loopback API!**

After extensive testing, we've confirmed that Windows' event-driven audio notification system works flawlessly with Process Loopback, enabling zero-polling capture.

### 📊 Performance Breakthrough

| Metric | v0.4.0 | v0.4.1 | Improvement |
|--------|---------|---------|------------|
| CPU Usage | 3-5% | < 1% | **80% reduction** |
| Polling | 1ms interval | Event-driven | **Eliminated** |
| Efficiency | Adaptive | 100% events | **Optimal** |
| Latency | 10ms | 10ms | Maintained |

### ✨ What's New

- **Event-Driven Capture**: Uses `WaitForSingleObject` instead of polling
- **SetEventHandle Integration**: Proper WASAPI event notifications
- **Automatic Fallback**: Seamless fallback to polling if events unavailable
- **Event Metrics**: Track event signals and timeouts
- **Mode Detection**: Reports whether running in event-driven or polling mode

### 🔧 Technical Details

The capture thread now:
1. Attempts to initialize with `AUDCLNT_STREAMFLAGS_EVENTCALLBACK`
2. Calls `SetEventHandle()` to register for audio events
3. Uses `WaitForMultipleObjects()` for efficient waiting
4. Falls back to 1ms polling only if events fail

### 📈 Real-World Results

Testing with Edge WebView2 and Steam:
- **499 event signals in 5 seconds**
- **0 timeouts**
- **100% event efficiency**
- **< 1% CPU usage**

### 🔄 Compatibility

- **100% API compatible** with v0.4.0
- No code changes required
- Automatic optimization on supported systems

---

## Version 0.4.0 (2024-12-26)

### 🎉 Queue-Based Architecture - Major Performance Release

PyWAC v0.4.0 features a completely redesigned queue-based architecture that resolves critical performance and stability issues. This release represents a major step forward in making PyWAC production-ready.

### 🚀 Key Highlights

- **95% CPU Usage Reduction**: From 30-100% down to < 5%
- **Zero Data Loss**: Thread-safe queue eliminates dropped audio
- **GIL-Safe**: No more crashes from Python/C++ interaction
- **Consistent Latency**: Stable 10ms response time
- **Production Ready**: Successfully tested with Spotify, Chrome, Discord

### 📊 Performance Improvements

#### Before (v0.3.x)
- CPU Usage: 30-100% (constant polling)
- Data Loss: Frequent (destructive reads)
- Stability: GIL crashes with callbacks
- Latency: Variable 50-100ms

#### After (v0.4.0)
- CPU Usage: < 5% (adaptive polling)
- Data Loss: 0% (thread-safe queue)
- Stability: Rock solid
- Latency: Consistent 10ms

### 🚨 Breaking Changes

1. **Module Reorganization**
   ```python
   # Old (v0.3.x)
   import process_loopback_v2 as loopback
   
   # New (v0.4.0)
   import process_loopback_queue as loopback
   ```

2. **New Streaming Interface**
   ```python
   # New (v0.4.0)
   from pywac.queue_streaming import QueueBasedStreamingCapture
   
   capture = QueueBasedStreamingCapture(
       process_id=spotify_pid,
       on_audio=callback_func
   )
   ```

### ✨ New Features

- **QueueBasedStreamingCapture**: High-level streaming API
- **Adaptive Polling**: Automatically adjusts 1-20ms based on load
- **Batch Processing**: Process multiple chunks efficiently
- **Performance Metrics**: Detailed metrics API
- **Zero-Copy**: Direct numpy array creation from C++

### 🐛 Fixed Issues

- **Critical**: GIL management crashes in callback approach
- **Critical**: High CPU usage from polling architecture
- **Critical**: Data loss from destructive buffer reads
- Thread state issues with C++ to Python callbacks
- Memory inefficiency in polling implementation

### 📚 Migration Guide

See [`docs/migrations/v0.4.0-queue-architecture.md`](docs/migrations/v0.4.0-queue-architecture.md) for detailed migration instructions.

---

## Version 0.3.0 (2024-12-25)

### 🎯 Major Changes

#### AudioData - Unified Audio Format
This release introduces the `AudioData` class, a unified format for handling audio throughout PyWAC. This is a **breaking change** that significantly improves the library's consistency and usability.

### 🚨 Breaking Changes

1. **Recording Functions Return AudioData**
   ```python
   # Old (v0.2.x)
   audio_data = pywac.record_audio(3)  # Returns List[float]
   
   # New (v0.3.0)
   audio = pywac.record_audio(3)  # Returns AudioData object
   ```

2. **Callback Functions Receive AudioData**
   ```python
   # Old (v0.2.x)
   def callback(audio_data: List[float]):
       pywac.utils.save_to_wav(audio_data, "file.wav", 48000)
   
   # New (v0.3.0)
   def callback(audio: AudioData):
       audio.save("file.wav")
   ```

3. **Direct Save Methods**
   ```python
   # Old (v0.2.x)
   pywac.utils.save_to_wav(audio_data, "file.wav", 48000)
   
   # New (v0.3.0)
   audio.save("file.wav")
   ```

### ✨ New Features

- **AudioData Class**: Unified audio data container with metadata
- **Format Conversions**: Built-in methods for float32/int16, mono/stereo
- **Audio Statistics**: Calculate RMS, peak levels, and dB values
- **Improved Type Safety**: Clear types instead of ambiguous lists

### 🐛 Bug Fixes

- Fixed callback recording playing at half speed
- Fixed format inconsistency between C++ and Python layers
- Fixed `SessionManager.get_active_sessions()` return type

### 📚 Migration Guide

See [`docs/migrations/v0.3.0-audiodata.md`](docs/migrations/v0.3.0-audiodata.md) for detailed migration instructions.

### 🧪 Testing

- Added comprehensive test suite (32+ tests)
- All examples updated and tested
- Test coverage for all major components

---

## Version 0.2.0

### ✨ Features
- Process-specific audio recording (Windows 10 2004+)
- Gradio demo application
- Volume control per application
- Async recording with callbacks

### 🐛 Bug Fixes
- Thread safety improvements
- Memory leak fixes

---

## Version 0.1.0

### 🎉 Initial Release
- Basic audio recording
- System-wide audio capture
- WAV file export
- Simple Python API