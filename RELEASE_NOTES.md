# Release Notes

## Version 0.3.0 (Unreleased)

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