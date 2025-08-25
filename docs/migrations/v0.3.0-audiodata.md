# AudioData Migration Guide

## Overview

PyWAC has been updated to use a unified `AudioData` class for all audio operations. This provides a consistent, type-safe interface for audio data throughout the library.

## What's Changed

### Old API (Deprecated)
```python
# Recording returned List[float] or numpy array
audio_data = pywac.record_audio(3)  # Returns list of float samples
pywac.utils.save_to_wav(audio_data, "output.wav", 48000)

# Callback received list of floats
def on_complete(audio_data):
    print(f"Recorded {len(audio_data)} samples")
    pywac.utils.save_to_wav(audio_data, "output.wav", 48000)
```

### New API (Current)
```python
# Recording returns AudioData object
audio = pywac.record_audio(3)  # Returns AudioData object
print(f"Recorded {audio.duration:.1f} seconds")
print(f"Sample rate: {audio.sample_rate}Hz")
audio.save("output.wav")  # Direct save method

# Callback receives AudioData object
def on_complete(audio):
    print(f"Recorded {audio.duration:.1f} seconds")
    stats = audio.get_statistics()
    print(f"RMS: {stats['rms_db']:.1f} dB")
    audio.save("output.wav")
```

## AudioData Class Features

### Core Properties
```python
audio = pywac.record_audio(5)

# Properties
audio.samples       # numpy array of samples
audio.sample_rate   # Sample rate in Hz (e.g., 48000)
audio.channels      # Number of channels (1=mono, 2=stereo)
audio.num_frames    # Number of audio frames
audio.duration      # Duration in seconds
audio.dtype         # Data type of samples
```

### Format Conversions
```python
# Convert between data types
audio_float32 = audio.to_float32()  # Convert to float32 (-1.0 to 1.0)
audio_int16 = audio.to_int16()      # Convert to int16 for WAV

# Channel conversions
mono_audio = audio.to_mono()        # Convert stereo to mono

# Format conversions
interleaved = audio.to_interleaved()  # Get interleaved array [L,R,L,R,...]
```

### Audio Analysis
```python
# Get comprehensive statistics
stats = audio.get_statistics()
print(f"Duration: {stats['duration']:.2f} seconds")
print(f"RMS Level: {stats['rms_db']:.1f} dB")
print(f"Peak Level: {stats['peak_db']:.1f} dB")
print(f"RMS Value: {stats['rms']:.4f}")
print(f"Peak Value: {stats['peak']:.4f}")
```

### File I/O
```python
# Save to WAV file
audio.save("output.wav")

# Load from WAV file
loaded_audio = AudioData.load("input.wav")

# Create from interleaved data
data = [0.1, -0.1, 0.2, -0.2]  # L,R,L,R
audio = AudioData.from_interleaved(data, sample_rate=48000, channels=2)
```

## Migration Examples

### Example 1: Basic Recording
```python
# Before
audio_data = pywac.record_audio(5)
if len(audio_data) > 0:
    pywac.utils.save_to_wav(audio_data, "output.wav", 48000)

# After
audio = pywac.record_audio(5)
if audio.num_frames > 0:
    audio.save("output.wav")
```

### Example 2: Callback Recording
```python
# Before
def on_complete(audio_data):
    samples = len(audio_data)
    pywac.utils.save_to_wav(audio_data, "callback.wav", 48000)

# After
def on_complete(audio):
    print(f"Duration: {audio.duration:.1f}s")
    audio.save("callback.wav")
```

### Example 3: Audio Processing
```python
# Before
import numpy as np
audio_data = pywac.record_audio(3)
audio_array = np.array(audio_data, dtype=np.float32)
rms = np.sqrt(np.mean(audio_array ** 2))
db = 20 * np.log10(rms + 1e-10)

# After
audio = pywac.record_audio(3)
stats = audio.get_statistics()
db = stats['rms_db']
```

### Example 4: Using AudioRecorder Class
```python
recorder = pywac.AudioRecorder()
recorder.start(duration=5)

# Wait or do other work
time.sleep(5)

# Stop and get AudioData
audio = recorder.stop()  # Returns AudioData object
print(f"Recorded {audio.duration:.1f} seconds")
audio.save("recording.wav")
```

## Benefits of AudioData

1. **Type Safety**: Clear types instead of ambiguous List[float]
2. **Convenience Methods**: Built-in save, load, and conversion methods
3. **Metadata Preservation**: Sample rate and channel info always available
4. **Format Flexibility**: Easy conversion between formats
5. **Audio Analysis**: Built-in statistics calculation
6. **Consistency**: Same format across entire library

## Backward Compatibility

This update removes backward compatibility since the library is new (1 day old). All functions now return `AudioData` objects instead of lists or numpy arrays.

## Complete API Reference

### Recording Functions
- `record_audio(duration) -> AudioData`
- `record_to_file(filename, duration) -> bool`
- `record_process(process_name, filename, duration) -> bool`
- `record_with_callback(duration, callback) -> None`

### AudioData Methods
- `save(filename) -> None`
- `load(filename) -> AudioData` (class method)
- `from_interleaved(data, sample_rate, channels) -> AudioData` (class method)
- `to_float32() -> AudioData`
- `to_int16() -> AudioData`
- `to_mono() -> AudioData`
- `to_interleaved() -> np.ndarray`
- `get_statistics() -> dict`

## Testing

Run the test suite to verify AudioData functionality:

```bash
python -m unittest tests.test_audio_data -v
```

All 10 tests should pass, covering:
- Creation from samples and interleaved data
- Format conversions (float32, int16)
- Channel operations (mono, stereo)
- File I/O (save, load)
- Statistics calculation
- Empty audio handling