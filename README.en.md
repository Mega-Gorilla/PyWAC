# PyPAC - Python Process Audio Capture for Windows

[![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/)
[![Windows](https://img.shields.io/badge/platform-Windows%2010%2F11-blue.svg)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Process-level audio capture library for Windows

**English** | [日本語](README.md)

## 🎯 Overview

PyPAC is a Python extension module that enables process-specific audio capture on Windows. Using the Windows Audio Session API, it aims to isolate and capture audio from specific applications.

### Why PyPAC?

- **Problem**: Existing Python audio libraries (PyAudioWPatch, sounddevice, etc.) can only capture system-wide audio
- **Solution**: Isolate audio by application, preventing unwanted audio mixing
- **Use Cases**: Game streaming audio separation, app-specific recording, audio analysis

## ✨ Key Features

| Feature | Status | Description |
|---------|--------|-------------|
| Audio Session Enumeration | ✅ Implemented | Detect audio sessions of running apps |
| Process Information | ✅ Implemented | Get process name, PID, volume, mute state |
| System Loopback | ✅ Implemented | Capture system-wide audio |
| Volume Control | ✅ Implemented | Adjust specific process volume |
| Process-Specific Capture | 🚧 In Development | Limited on Windows 11 24H2 |

## 🏗️ Architecture

```
pypac/
├── audio_session_capture     # Main module
│   ├── SessionEnumerator    # Session management class
│   └── SimpleLoopback       # System recording class
└── process_loopback         # Legacy API (reference implementation)
```

### Technology Stack
- **C++17**: Core implementation
- **Windows Audio Session API**: Audio session management
- **WASAPI**: Windows Audio Session API Interface
- **pybind11**: Python bindings

## 📦 Installation

### Prerequisites

| Requirement | Version |
|-------------|---------|
| Windows | 10 (2004+) / 11 |
| Python | 3.7+ |
| Visual Studio | 2022 (C++ development tools) |
| Windows SDK | 10.0.26100.0 or later |

### Setup Instructions

```powershell
# 1. Clone the repository
git clone https://github.com/yourusername/pypac.git
cd pypac

# 2. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install pybind11 numpy

# 4. Build
python setup.py build_ext --inplace

# 5. Verify
python examples/demo_audio_capture.py
```

## 🚀 Quick Start

### Basic Usage

```python
import pypac
import numpy as np

# Enumerate audio sessions
enumerator = pypac.SessionEnumerator()
sessions = enumerator.enumerate_sessions()

for session in sessions:
    if session.state == 1:  # Active
        print(f"🔊 {session.process_name} (PID: {session.process_id})")
        print(f"   Volume: {session.volume:.0%}")
        print(f"   Muted: {'Yes' if session.muted else 'No'}")

# System-wide recording
loopback = pypac.SimpleLoopback()
if loopback.start():
    import time
    time.sleep(3)  # Record for 3 seconds
    
    audio_data = loopback.get_buffer()
    print(f"Recording complete: {len(audio_data)} samples")
    
    loopback.stop()
```

## 📖 API Reference

### SessionEnumerator Class

| Method | Description | Returns |
|--------|-------------|---------|
| `enumerate_sessions()` | Get all audio sessions | `List[SessionInfo]` |
| `set_session_volume(pid, volume)` | Set process volume (0.0-1.0) | `bool` |
| `set_session_mute(pid, mute)` | Set process mute state | `bool` |

### SessionInfo Structure

| Property | Type | Description |
|----------|------|-------------|
| `process_name` | `str` | Process name |
| `process_id` | `int` | Process ID |
| `state` | `int` | 0:Inactive, 1:Active, 2:Expired |
| `volume` | `float` | Volume level (0.0-1.0) |
| `muted` | `bool` | Mute state |

### SimpleLoopback Class

| Method | Description | Returns |
|--------|-------------|---------|
| `start()` | Start capture | `bool` (success/failure) |
| `stop()` | Stop capture | `None` |
| `get_buffer()` | Get audio data | `numpy.ndarray[float32]` |

## 💡 Practical Examples

### Adjust Application Volume

```python
def adjust_app_volume(app_name: str, volume_percent: int) -> bool:
    """Adjust specific application volume"""
    enumerator = pypac.SessionEnumerator()
    sessions = enumerator.enumerate_sessions()
    
    for session in sessions:
        if app_name.lower() in session.process_name.lower():
            success = enumerator.set_session_volume(
                session.process_id, 
                volume_percent / 100.0
            )
            if success:
                print(f"✅ Set {session.process_name} volume to {volume_percent}%")
                return True
    
    print(f"❌ {app_name} not found")
    return False

# Examples
adjust_app_volume("Discord", 50)  # Set Discord to 50%
adjust_app_volume("chrome", 80)   # Set Chrome to 80%
```

### Audio Level Meter

```python
def show_audio_meter(duration_seconds: int = 10):
    """Real-time audio level meter"""
    loopback = pypac.SimpleLoopback()
    
    if not loopback.start():
        print("❌ Failed to start capture")
        return
    
    print("🎵 Audio Level Meter (Ctrl+C to stop)")
    print("-" * 50)
    
    import time
    for i in range(duration_seconds):
        time.sleep(1)
        buffer = loopback.get_buffer()
        
        if len(buffer) > 0:
            # Calculate RMS
            rms = np.sqrt(np.mean(buffer**2))
            db = 20 * np.log10(rms + 1e-10)
            
            # Visualize
            meter_width = 40
            normalized = min(1.0, max(0.0, (db + 60) / 60))
            filled = int(normalized * meter_width)
            meter = "█" * filled + "░" * (meter_width - filled)
            
            print(f"\r[{meter}] {db:+6.1f} dB", end="")
    
    loopback.stop()
    print("\n✅ Recording complete")
```

## 🔧 Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `ImportError: DLL load failed` | Missing VC++ Redistributable | Install [VC++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe) |
| No audio captured | Admin rights required | Run PowerShell as Administrator |
| Sessions not showing | App not outputting audio | Play audio in target app |
| Build error `error C2039` | Windows SDK version mismatch | Install latest SDK via Visual Studio Installer |

### Debug Mode

```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check COM initialization
import ctypes
hr = ctypes.windll.ole32.CoInitializeEx(None, 0x0)
print(f"COM initialization: 0x{hr:08X}")
```

## 🔄 Known Limitations

### Windows 11 24H2 Issues
- **Process Loopback API** doesn't work properly (heap corruption error 0xc0000374)
- Using **Audio Session API** as an alternative
- Process-specific capture currently in development

### Performance Specifications
| Item | Value |
|------|-------|
| Buffer Size | 480 samples (10ms @ 48kHz) |
| Sample Rate | 48,000 Hz |
| Bit Depth | 32-bit float |
| Latency | ~10-20ms |
| CPU Usage | Typically 1-3% |

## 🤝 Contributing

Pull requests are welcome!

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Create a Pull Request

### Development Environment

```powershell
# Install in development mode
pip install -e .

# Run tests
python -m pytest tests/

# Code quality checks
python -m pylint src/
python -m black src/
```

## 📚 Related Resources

- [Windows Audio Session API (WASAPI)](https://docs.microsoft.com/en-us/windows/win32/coreaudio/wasapi)
- [Core Audio APIs](https://docs.microsoft.com/en-us/windows/win32/coreaudio/core-audio-apis-in-windows-vista)
- [pybind11 Documentation](https://pybind11.readthedocs.io/)
- [OBS Studio win-capture-audio](https://github.com/bozbez/win-capture-audio) - Implementation reference

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [OBS Studio](https://obsproject.com/) - win-capture-audio implementation approach
- [pybind11](https://github.com/pybind/pybind11) - Excellent C++/Python bindings
- Windows Audio API Team - Detailed documentation and samples

## 📝 Changelog

### v0.2.0 (2024-01-XX)
- 🎉 Complete migration to Audio Session API
- 🐛 Improved stability on Windows 11 24H2
- 📁 Improved project structure
- 📚 Comprehensive documentation added

### v0.1.0 (2024-01-XX)
- 🚀 Initial release
- 🔬 Process Loopback API implementation (experimental)
- 🎵 Basic audio capture functionality

---

<div align="center">

**[⬆ Back to Top](#pypac---python-process-audio-capture-for-windows)**

Made with ❤️ for Windows Audio Development

</div>