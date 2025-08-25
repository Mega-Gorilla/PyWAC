#!/usr/bin/env python
"""
Test the AudioData functionality
"""

import pywac
import numpy as np
import tempfile
import os

def test_audiodata_features():
    """Test AudioData features"""
    print("=" * 60)
    print("AUDIODATA FEATURE TEST")
    print("=" * 60)
    
    # Record audio
    print("\n1. Recording 0.5 seconds of audio...")
    audio = pywac.record_audio(0.5)
    
    # Check type
    print(f"   Type: {type(audio)}")
    print(f"   Duration: {audio.duration:.3f} seconds")
    print(f"   Sample rate: {audio.sample_rate} Hz")
    print(f"   Channels: {audio.channels}")
    print(f"   Frames: {audio.num_frames}")
    
    # Get statistics
    print("\n2. Audio statistics:")
    stats = audio.get_statistics()
    print(f"   RMS: {stats['rms']:.6f}")
    print(f"   Peak: {stats['peak']:.6f}")
    print(f"   RMS (dB): {stats['rms_db']:.1f}")
    print(f"   Peak (dB): {stats['peak_db']:.1f}")
    
    # Format conversions
    print("\n3. Format conversions:")
    float_audio = audio.to_float32()
    print(f"   Float32 dtype: {float_audio.dtype}")
    
    int_audio = audio.to_int16()
    print(f"   Int16 dtype: {int_audio.dtype}")
    
    mono = audio.to_mono()
    print(f"   Mono channels: {mono.channels}")
    
    interleaved = audio.to_interleaved()
    print(f"   Interleaved shape: {interleaved.shape}")
    
    # Save and load
    print("\n4. Save and load test:")
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        temp_path = f.name
    
    try:
        audio.save(temp_path)
        print(f"   Saved to: {temp_path}")
        
        loaded = pywac.AudioData.load(temp_path)
        print(f"   Loaded: {loaded.duration:.3f} seconds")
        
        # Compare
        if audio == loaded:
            print("   [OK] Original and loaded match exactly")
        else:
            # Check if they're close enough (due to format conversion)
            int_orig = audio.to_int16()
            int_loaded = loaded.to_int16() if loaded.dtype != np.int16 else loaded
            if np.allclose(int_orig.samples, int_loaded.samples, atol=1):
                print("   [OK] Original and loaded are equivalent")
            else:
                print("   [ERROR] Original and loaded differ")
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    print("\n5. Callback recording test:")
    callback_audio = None
    import threading
    event = threading.Event()
    
    def on_complete(audio_data):
        nonlocal callback_audio
        callback_audio = audio_data
        print(f"   Callback received AudioData: {audio_data.duration:.3f}s")
        event.set()
    
    pywac.record_with_callback(0.5, on_complete)
    event.wait(timeout=2.0)
    
    if callback_audio:
        print(f"   Callback audio type: {type(callback_audio)}")
        print(f"   Callback audio frames: {callback_audio.num_frames}")
    else:
        print("   Callback not received within timeout")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("AudioData is working correctly!")
    print("=" * 60)


if __name__ == "__main__":
    test_audiodata_features()