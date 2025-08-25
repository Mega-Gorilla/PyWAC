# PyWAC - Python Process Audio Capture for Windows

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.7+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Version](https://img.shields.io/badge/Version-0.2.0-blue?style=for-the-badge)](https://github.com/Mega-Gorilla/pywac)

**The Simplest Audio Control Library for Windows**

**English** | [Japanese](README.md)

</div>

---

## Quick Start in 3 Seconds

```python
import pywac

# Record audio with just one line
pywac.record_to_file("output.wav", duration=5)

# Record specific app audio only (exclude Discord voice!)
pywac.record_process("game.exe", "game_only.wav", duration=10)

# Adjust app volume
pywac.set_app_volume("spotify", 0.5)

# Check active audio sessions
active = pywac.get_active_sessions()
print(f"Active sessions: {', '.join(active)}")
# Output: Active sessions: Spotify.exe, Chrome.exe
```

**That's it!** No complex configuration needed.

---

## 📋 Contents

- [Features](#-features)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Demo](#-demo)
- [Usage](#-usage)
- [Examples](#-examples)
- [API Reference](#-api-reference)
- [Development](#-development)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

---

## ✨ Features

### 🎯 Main Features

- **Process-specific audio recording** - Record audio from specific applications only (Windows 10 2004+)
- **Volume control** - Per-application volume adjustment and muting
- **Simple API** - Start recording with just one line of code
- **Real-time monitoring** - Get audio session status in real-time
- **Modern UI** - Interactive Gradio-based demo application
- **Full Windows 11 support** - Leverages the latest Windows Audio APIs

### 🔍 Why Choose PyWAC?

| Feature | PyWAC | PyAudio | sounddevice | PyAudioWPatch |
|---------|-------|---------|-------------|---------------|
| Process-specific recording | ✅ | ❌ | ❌ | ❌ |
| App volume control | ✅ | ❌ | ❌ | ❌ |
| Windows 11 support | ✅ | ⚠️ | ⚠️ | ✅ |
| Simple API | ✅ | ❌ | ⚠️ | ⚠️ |
| Process Loopback | ✅ | ❌ | ❌ | ❌ |

---

## 📋 Requirements

- **OS**: Windows 10 version 2004 (Build 19041) or later
- **Python**: 3.7 or later
- **Compiler**: Microsoft Visual C++ 14.0 or later (for building only)

---

## 📦 Installation

### Method 1: Easy Install (Recommended)

```bash
# Development version (current installation method)
git clone https://github.com/Mega-Gorilla/pywac.git
cd pywac
pip install -e .
```

### Method 2: Manual Build (Advanced)

<details>
<summary>Click to expand</summary>

#### Prerequisites
- Windows 10 (2004 or later) or Windows 11
- Python 3.7+
- Visual Studio 2022 (C++ development tools)
- Windows SDK 10.0.26100.0 or later

```bash
# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install pybind11 numpy

# Build
python setup.py build_ext --inplace
```

</details>

---

## 🚀 Quick Start

### Basic Usage

```python
import pywac

# Record system audio
pywac.record_to_file("output.wav", duration=5)

# Record specific app audio only
pywac.record_process("spotify", "spotify_only.wav", duration=10)

# Adjust app volume
pywac.set_app_volume("firefox", 0.5)  # Set to 50%
```

## 🎮 Demo

### Gradio Interactive Demo

PyWAC includes a comprehensive interactive demo application showcasing all features:

```bash
# Launch the demo application
python examples/gradio_demo.py
```

Open your browser and navigate to `http://localhost:7860`.

#### Demo Features

##### 📊 Session Management
- View active audio sessions in real-time
- Monitor process IDs, states, volume levels, and mute status
- Auto-refresh feature (5-second interval)
- Manual refresh with one click

##### 🎚️ Volume Control
- Select application from dropdown
- Adjust volume with slider (0-100%)
- Set volume button for instant application
- Status display for feedback

##### 🔴 Recording Features
Three recording modes available:
- **System Recording**: Capture all system audio
- **Process Recording**: Record specific app audio only (exclude Discord, etc.)
- **Callback Recording**: Record with real-time monitoring
- Duration settings (1-60 seconds) with preset buttons (5s/10s/30s)

##### 📈 Real-time Monitoring
- View audio levels during recording
- Continuous RMS and dB level updates
- Visual progress bar display

##### 💾 Recording Management
- Auto-list recordings (newest first)
- One-click playback
- Display file size and recording time

##### 🎨 Modern UI
- Dark theme support
- Three organized tabs (Session Management/Recording/Volume Control)
- Responsive design

### Sample Scripts

```bash
# Basic usage examples
python examples/basic_usage.py

# Test process-specific recording
python examples/record_app_audio.py --list  # List recordable apps
python examples/record_app_audio.py --app spotify --duration 10
```

## 📚 Usage

### High-Level API (Simple Functions)

```python
import pywac

# System-wide audio recording
pywac.record_to_file("output.wav", duration=5)

# Process-specific recording (by name)
pywac.record_process("spotify", "spotify_only.wav", duration=10)

# Process-specific recording (by PID)
pywac.record_process_id(51716, "spotify_by_pid.wav", duration=10)

# Get active audio sessions (list of process names)
active = pywac.get_active_sessions()
for app in active:
    print(f"Active: {app}")

# Application volume control
pywac.set_app_volume("spotify", 0.5)  # 50%

# Session information retrieval
firefox = pywac.find_audio_session("firefox")
if firefox:
    print(f"Firefox volume: {firefox['volume_percent']}%")

# Enumerate all audio sessions
sessions = pywac.list_audio_sessions()
for s in sessions:
    print(f"{s['process_name']}: {s['volume_percent']}%")
```

### Class-Based API (Detailed Control)

```python
import pywac

# Session management via SessionManager
manager = pywac.SessionManager()

# Enumerate active sessions
active = manager.get_active_sessions()
for session in active:
    print(f"{session.process_name}")
    print(f"  Volume: {session.volume * 100:.0f}%")
    print(f"  Muted: {session.is_muted}")

# Session search and control
discord = manager.find_session("discord")
if discord:
    manager.set_volume("discord", 0.3)  # 30%
    manager.set_mute("discord", True)

# Detailed recording control via AudioRecorder
recorder = pywac.AudioRecorder()
recorder.start(duration=10)

while recorder.is_recording:
    print(f"Recording: {recorder.recording_time:.1f}s "
          f"({recorder.sample_count} samples)")
    time.sleep(1)

audio_data = recorder.stop()
if len(audio_data) > 0:
    pywac.utils.save_to_wav(audio_data, "output.wav")
    print(f"Saved: {len(audio_data)} samples")
```

### Native API (Low-Level Control)

<details>
<summary>Show details</summary>

```python
import pywac._native as native
import numpy as np

# Direct session control via SessionEnumerator
enumerator = native.SessionEnumerator()
sessions = enumerator.enumerate_sessions()

for session in sessions:
    if session.state == 1:  # AudioSessionStateActive
        print(f"PID {session.process_id}: {session.process_name}")
        
        # Direct volume control
        enumerator.set_session_volume(session.process_id, 0.5)
        enumerator.set_session_mute(session.process_id, False)

# Low-level recording via SimpleLoopback
loopback = native.SimpleLoopback()
if loopback.start():
    time.sleep(5)
    
    # Get as NumPy array
    audio_buffer = loopback.get_buffer()
    
    # Signal processing
    rms = np.sqrt(np.mean(audio_buffer**2))
    peak = np.max(np.abs(audio_buffer))
    
    loopback.stop()
```

</details>

---

## 💡 Examples

### 🎯 Process-Specific Recording (Key Feature!)

```python
import pywac

# Method 1: High-level API (working!)
def record_specific_app(app_name, output_file, duration=10):
    """Record audio from specific app only"""
    success = pywac.record_process(app_name, output_file, duration)
    if success:
        print(f"✅ {app_name} audio recorded successfully!")
    else:
        print(f"❌ Recording failed - Check if {app_name} is playing audio")

# Method 2: Callback recording (new feature!)
def record_with_callback_demo():
    """Record with callback on completion"""
    def on_recording_complete(audio_data):
        print(f"Recording complete: {len(audio_data)} samples")
        # Analyze audio
        import numpy as np
        audio_array = np.array(audio_data)
        rms = np.sqrt(np.mean(audio_array ** 2))
        db = 20 * np.log10(rms + 1e-10)
        print(f"Average volume: {db:.1f} dB")
        
        # Save to WAV file
        pywac.utils.save_to_wav(audio_data, "callback_recording.wav", 48000)
        print("✅ Recording saved to callback_recording.wav!")
    
    # Record for 5 seconds (asynchronously)
    pywac.record_with_callback(5, on_recording_complete)
    print("Recording started (background)...")
    
    # Wait for completion
    import time
    time.sleep(6)
    print("✅ Process complete!")

# Example: Record game audio only (no Discord voice)
record_specific_app("game.exe", "game_audio.wav", 30)

# Example: Record browser audio only
record_specific_app("firefox", "browser_audio.wav", 15)
```

### Game Streaming Audio Mixer

```python
import pywac
import time

class StreamAudioMixer:
    """Audio balance adjustment for streaming"""
    
    def __init__(self):
        self.manager = pywac.SessionManager()
    
    def setup_streaming(self):
        """Setup audio for streaming"""
        # Game audio at 70%
        pywac.set_app_volume("game", 0.7)
        
        # Discord at 30%
        pywac.set_app_volume("discord", 0.3)
        
        # Mute Spotify (via SessionManager)
        manager = pywac.SessionManager()
        manager.set_mute("spotify", True)
        
        print("Streaming audio setup complete!")
    
    def save_game_audio_only(self, game_name="game.exe", duration=60):
        """Record game audio only (exclude Discord voice)"""
        # Process Loopback API records game audio only!
        pywac.record_process(game_name, f"game_only_{time.time()}.wav", duration)
        print("Game audio recorded successfully (no Discord voice!)")

# Usage
mixer = StreamAudioMixer()
mixer.setup_streaming()
mixer.save_game_audio_only()
```

### Real-time Audio Meter

```python
import pywac
import time

def audio_meter(duration=30):
    """Visual audio meter"""
    recorder = pywac.AudioRecorder()
    recorder.start(duration=duration)
    
    print("Audio Level Meter")
    print("-" * 50)
    
    while recorder.is_recording:
        buffer = recorder.get_buffer()
        if len(buffer) > 0:
            # Calculate RMS
            rms = pywac.utils.calculate_rms(buffer)
            db = pywac.utils.calculate_db(buffer)
            
            # Visualize
            bar_length = int(rms * 50)
            bar = "█" * bar_length + "░" * (50 - bar_length)
            
            print(f"\r[{bar}] {db:.1f} dB", end="")
        
        time.sleep(0.1)
    
    recorder.stop()
    print("\nComplete")

# Run
audio_meter(10)
```

---

## 📖 API Reference

### Simple Function API

#### Recording Functions

| Function | Description | Example |
|----------|-------------|---------|
| `record_to_file(filename, duration)` | Record audio to file | `pywac.record_to_file("out.wav", 5)` |
| `record_process(app, filename, duration)` | Record specific app audio | `pywac.record_process("spotify", "spotify.wav", 10)` |
| `record_process_id(pid, filename, duration)` | Record by process ID | `pywac.record_process_id(1234, "app.wav", 10)` |
| `record_with_callback(duration, callback)` | Record with callback | See callback recording example |
| `list_audio_sessions()` | Get all audio sessions | `sessions = pywac.list_audio_sessions()` |
| `get_active_sessions()` | List active app names | `apps = pywac.get_active_sessions()` |
| `set_app_volume(app, volume)` | Set app volume (0.0-1.0) | `pywac.set_app_volume("chrome", 0.5)` |
| `mute_app(app)` | Mute app | `manager = pywac.SessionManager(); manager.set_mute("spotify", True)` |
| `find_audio_session(app)` | Get app info | `info = pywac.find_audio_session("firefox")` |

#### Session Management Functions

| Function | Description | Example |
|----------|-------------|---------|  
| `get_active_sessions()` | List active audio session names | `sessions = pywac.get_active_sessions()` |
| `list_audio_sessions()` | Get detailed session information | `sessions = pywac.list_audio_sessions()` |
| `find_audio_session(app_name)` | Find session by name | `session = pywac.find_audio_session("spotify")` |
| `set_app_volume(app, volume)` | Set app volume (0.0-1.0) | `pywac.set_app_volume("chrome", 0.5)` |
| `mute_app(app_name)` | Mute application | `manager = pywac.SessionManager(); manager.set_mute("discord", True)` |
| `unmute_app(app_name)` | Unmute application | `manager = pywac.SessionManager(); manager.set_mute("discord", False)` |

#### Utility Functions

| Function | Description | Example |
|----------|-------------|---------|  
| `save_to_wav(data, filename, sample_rate)` | Save audio to WAV | `pywac.utils.save_to_wav(audio_data, "out.wav", 48000)` |
| `calculate_rms(audio_buffer)` | Calculate RMS value | `rms = pywac.calculate_rms(buffer)` |
| `calculate_db(audio_buffer)` | Calculate dB level | `db = pywac.calculate_db(buffer)` |

### Callback Recording

```python
import pywac

def audio_callback(audio_data):
    """Called when recording completes"""
    if audio_data:
        print(f"Recorded {len(audio_data)} samples")
        
        # Process audio
        rms = pywac.calculate_rms(audio_data)
        db = pywac.calculate_db(audio_data)
        print(f"Audio level: {db:.1f} dB")
        
        # Save to file
        pywac.utils.save_to_wav(audio_data, "callback_recording.wav", 48000)
        print("Audio saved!")

# Record with callback
pywac.record_with_callback(duration=5, callback=audio_callback)
print("Recording in progress...")
```

---


## 🔧 Troubleshooting

### Common Issues

<details>
<summary>ImportError: No module named 'pywac'</summary>

**Solution:**
```bash
# Install package
pip install -e .

# Or manual build
python setup.py build_ext --inplace
```
</details>

<details>
<summary>DLL load failed</summary>

**Solution:**
1. Install [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
2. Restart Windows
</details>

<details>
<summary>No audio recorded</summary>

**Solution:**
1. Run PowerShell as administrator
2. Check if audio is playing in any app
3. Verify Windows sound settings
</details>

---


## 🛠️ Development

### Build Environment

- Visual Studio 2022
- Windows SDK 10.0.26100.0+
- Python 3.7-3.12
- Git

### Development Setup

```bash
# Clone repository
git clone https://github.com/Mega-Gorilla/pywac.git
cd pywac

# Setup development environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]

# Run tests
pytest tests/

# Code quality checks
black pywac/
pylint pywac/
mypy pywac/
```

### Architecture

```
pywac/
├── pywac/              # Python package
│   ├── __init__.py    # Package entry
│   ├── api.py         # High-level API
│   ├── sessions.py    # Session management
│   ├── recorder.py    # Recording features
│   └── utils.py       # Utilities
├── src/               # C++ source
│   ├── pypac_native.cpp      # Main module
│   └── process_loopback_v2.cpp # Process Loopback implementation
├── examples/          # Sample code
└── tests/            # Tests
```

### Technical Details: Process Loopback API

PyWAC uses the Process Loopback API introduced in Windows 10 2004 (Build 19041) to enable process-specific audio capture.

#### Implementation Features

- **API**: `ActivateAudioInterfaceAsync` with `AUDIOCLIENT_ACTIVATION_TYPE_PROCESS_LOOPBACK`
- **Format**: 48kHz / 32-bit float / stereo (fixed)
- **Buffer**: Up to 60 seconds ring buffer
- **Latency**: < 50ms
- **Threading**: COM multithreaded (`COINIT_MULTITHREADED`)

#### Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Session enumeration | < 10ms | 5 sessions |
| Volume change | < 5ms | Instant |
| Recording start | < 50ms | Including init |
| Process recording init | < 200ms | Including COM init |
| CPU usage | < 2% | During recording |
| Memory usage | < 50MB | 60-second buffer |

For detailed technical specifications, see the [Technical Investigation Report](docs/PROCESS_LOOPBACK_INVESTIGATION.md).

---

## ✅ Tested Environments

| Environment | Version | Status |
|-------------|---------|--------|
| Windows 11 | 23H2 | ✅ Fully working |
| Windows 10 | 21H2+ | ✅ Fully working |
| Python | 3.7-3.12 | ✅ Tested |
| Visual Studio | 2022 | ✅ Recommended |

### Tested Applications

- ✅ **Spotify** - Volume control, process-specific recording
- ✅ **Discord** - Volume control, mute
- ✅ **Chrome/Firefox** - Session detection, volume control, process-specific recording
- ✅ **Games** - Process-specific recording
- ✅ **OBS Studio** - Compatible with recording

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

## 🙏 Acknowledgments

- [pybind11](https://github.com/pybind/pybind11) - Excellent C++ bindings
- [OBS Studio](https://obsproject.com/) - Audio capture reference implementation
- Windows Audio API team - Detailed documentation
- Microsoft ApplicationLoopback sample - Process Loopback API reference