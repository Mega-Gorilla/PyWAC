# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PyWAC (Python Windows Audio Capture) is a Windows audio control library that provides both system-wide and process-specific audio capture capabilities. It implements the Windows Process Loopback API to enable capturing audio from individual applications without mixing (e.g., recording game audio without Discord voice chat).

**Status: Process-specific recording is IMPLEMENTED and FUNCTIONAL**

## Build Commands

```powershell
# Build extension modules (requires VS 2022 with C++ tools)
.\build.bat
# Or manually:
.\.venv\Scripts\Activate.ps1; python setup.py build_ext --inplace

# Run tests
pytest tests/

# Code quality
black pywac/
pylint pywac/
mypy pywac/
```

## Test Examples

```powershell
# Quick functionality test
python examples\quick_test.py

# Process-specific recording test
python examples\process_specific_recording.py

# Interactive demo (opens at http://localhost:7860)
python examples\gradio_demo.py
```

## Development Environment Requirements

- **Windows 10 version 2004 (Build 19041) or later** - Required for Process Loopback API
- **Visual Studio 2022** with C++ development tools
- **Windows SDK 10.0.26100.0** or later
- **Python 3.8+** with virtual environment at `.venv`
- **Dependencies**: pybind11, numpy

## Architecture

### Layer Structure

```
High-Level API (pywac.api)
    |
    v
Python Classes (SessionManager, AudioRecorder)
    |
    v
Native Extensions (C++ via pybind11)
    |
    v
Windows Audio APIs (WASAPI, Process Loopback)
```

### Native Extensions (C++)

Two separate pybind11 extension modules in `src/`:

1. **`pywac._pywac_native`** (`audio_session_capture.cpp`)
   - Audio session enumeration and control
   - Volume/mute per-application
   - System-wide loopback capture via WASAPI

2. **`process_loopback_queue`** (`process_loopback_queue.cpp`)
   - Process-specific audio capture using Windows Process Loopback API
   - Uses `ActivateAudioInterfaceAsync` with `AUDIOCLIENT_ACTIVATION_TYPE_PROCESS_LOOPBACK`
   - Queue-based streaming with `QueueBasedProcessCapture` class
   - Fixed format: 48kHz / 32bit float / stereo

### Python Package (`pywac/`)

- `api.py` - High-level convenience functions (`record_to_file`, `record_process`, `set_app_volume`, etc.)
- `sessions.py` - `SessionManager` and `AudioSession` classes
- `recorder.py` - `AudioRecorder` and `AsyncAudioRecorder` classes
- `audio_data.py` - `AudioData` container for recorded audio
- `unified_recording.py` - Unified interface for different recording backends

## Key Technical Constraints

- **GetMixFormat() returns E_NOTIMPL** for Process Loopback - use fixed format (48kHz/32bit float/stereo)
- **COM threading**: COINIT_MULTITHREADED required
- **Latency**: < 50ms achieved
- **Buffer management**: Thread-safe with mutex protection

## Python API Quick Reference

```python
import pywac

# System recording
pywac.record_to_file("output.wav", duration=5)

# Process-specific recording
pywac.record_process("spotify", "spotify.wav", duration=10)
pywac.record_process_id(1234, "output.wav", duration=10)

# Volume control
pywac.set_app_volume("chrome", 0.5)
pywac.mute_app("discord")

# Session info
sessions = pywac.list_audio_sessions(active_only=True)
# Returns: [{'process_id': 1234, 'process_name': 'Chrome.exe', 'volume': 1.0, ...}, ...]
```

## Troubleshooting

### Process Loopback initialization fails
1. Windows version < 2004
2. May need administrator privileges
3. Target process not producing audio
4. Audio device configuration issues

### No audio captured
1. Ensure audio is playing in target process
2. Check Windows audio mixer settings
3. Verify process has active audio sessions

## Reference Implementation

Microsoft's ApplicationLoopback sample is in `windows-classic-samples/Samples/ApplicationLoopback/` for reference.
