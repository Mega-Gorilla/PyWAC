# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PyWAC (Python Process Audio Capture) is a Windows audio control library that provides both system-wide and process-specific audio capture capabilities. The project successfully implements the Windows Process Loopback API to enable capturing audio from individual applications without mixing (e.g., recording game audio without Discord voice chat).

**Status: Process-specific recording is IMPLEMENTED and FUNCTIONAL**

## Key Technical Context

### Core Problem Being Solved
- Current Python audio libraries (PyAudioWPatch/sounddevice) can only capture system-wide audio
- Windows Process Loopback API (Windows 10 2004+) allows process-specific audio capture
- This requires C++ implementation due to COM interface and async callback requirements

### Architecture

The project implements a C++ extension module using pybind11 that:
1. Uses Windows `ActivateAudioInterfaceAsync` with `AUDIOCLIENT_ACTIVATION_TYPE_PROCESS_LOOPBACK`
2. Implements `IActivateAudioInterfaceCompletionHandler` for async activation
3. Captures audio in a separate thread and buffers it
4. Exposes Python API for process listing and audio capture

## Build Commands

### Build the extension modules
```powershell
# Activate virtual environment and build
powershell -Command ".\.venv\Scripts\Activate.ps1; python setup.py build_ext --inplace"

# Alternative using batch file
.\build.bat
```

### Test the modules
```powershell
# Quick test of basic functionality
powershell -Command ".\.venv\Scripts\Activate.ps1; python examples\quick_test.py"

# Test process-specific recording
powershell -Command ".\.venv\Scripts\Activate.ps1; python examples\process_specific_recording.py"

# Test audio recording from apps
powershell -Command ".\.venv\Scripts\Activate.ps1; python examples\record_app_audio.py"
```

## Development Environment Requirements

- **Windows 10 version 2004 (Build 19041) or later** - Required for Process Loopback API
- **Visual Studio 2022** with C++ development tools
- **Windows SDK 10.0.26100.0** or later (includes audioclientactivationparams.h)
- **Python 3.7+** with virtual environment at `.venv`
- **Dependencies**: pybind11, numpy (installed in venv)

## Module Structure

### Current Modules
- `pywac._pywac_native` - Main module with audio session control and system-wide loopback
- `process_loopback_queue` - **WORKING** Queue-based Process Loopback API implementation
  - Event-driven audio capture with ActivateAudioInterfaceAsync
  - Successfully tested with Spotify and Firefox
  - Captures process-specific audio without mixing
  - Non-destructive queue-based streaming

### Python API Design
```python
import process_loopback_queue as loopback

# List processes (via pywac API)
import pywac
processes = pywac.list_audio_sessions(active_only=True)
# Returns: [{'process_id': 1234, 'process_name': 'Chrome.exe', ...}, ...]

# Stream audio with queue-based capture
capture = loopback.QueueBasedProcessCapture()
capture.set_chunk_size(2400)  # 50ms chunks at 48kHz
capture.start(1234)  # Process ID, or 0 for all system audio

# Poll for chunks
while capture.is_capturing():
    chunks = capture.pop_chunks(max_chunks=10, timeout_ms=10)
    for chunk in chunks:
        if not chunk['silent']:
            audio_data = chunk['data']  # NumPy array
            # Process audio...
            
capture.stop()
```

## Known Issues and Solutions

### Issue: Process Loopback initialization fails
**Symptoms**: `capture.start()` returns False
**Possible causes**:
1. Windows version < 2004
2. Need administrator privileges
3. Target process not producing audio
4. Audio device configuration issues

### Issue: No audio captured
**Symptoms**: `pop_chunks()` returns empty list or silent chunks only
**Solutions**:
1. Ensure audio is playing in target process
2. Check Windows audio mixer settings
3. Verify process has audio sessions active
4. Check chunk['silent'] flag - may indicate no audio activity

## Technical Constraints

### Resolved Issues:
- **GetMixFormat() returns E_NOTIMPL**: Solved by using fixed format (48kHz / 32bit float / stereo)
- **Async activation**: Successfully implemented with IActivateAudioInterfaceCompletionHandler
- **Process isolation**: Confirmed working - no audio mixing between processes

### Current specifications:
- Fixed format: 48kHz / 32bit float / stereo for Process Loopback
- COM threading: COINIT_MULTITHREADED required
- Latency: < 50ms achieved
- Buffer management: Thread-safe with mutex protection

## Reference Implementation

Microsoft's ApplicationLoopback sample is cloned in `windows-classic-samples/Samples/ApplicationLoopback/` for reference. Key files:
- `LoopbackCapture.cpp` - Shows proper ActivateAudioInterfaceAsync usage
- `LoopbackCapture.h` - Interface design pattern

## Future Integration Plan

According to the implementation plan, this module will integrate with LiveCap for real-time transcription:
1. Add process selection dropdown to GUI
2. Switch audio source from system capture to process capture
3. Keep existing VAD/transcription pipeline unchanged