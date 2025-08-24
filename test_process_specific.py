"""
Test script for process-specific audio recording
Tests with Spotify and Firefox that are currently playing audio
"""
import time
import wave
import numpy as np
import process_loopback_v2 as loopback

def save_audio(data, filename, sample_rate=48000, channels=2):
    """Save audio data to WAV file"""
    if len(data) == 0:
        print(f"No audio data to save for {filename}")
        return
    
    # Convert float32 to int16
    audio_int16 = (data * 32767).astype(np.int16)
    
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())
    
    print(f"Saved {len(data) / sample_rate:.2f} seconds of audio to {filename}")

def test_process_capture(pid, name, duration=5):
    """Test capturing audio from a specific process"""
    print(f"\nTesting process-specific capture for {name} (PID: {pid})")
    print("=" * 60)
    
    capture = loopback.ProcessCapture()
    
    print(f"Starting capture for PID {pid}...")
    success = capture.start(pid)
    
    if not success:
        print(f"Failed to start capture for {name}")
        return False
    
    print(f"Recording for {duration} seconds...")
    time.sleep(duration)
    
    # Get captured audio
    audio_data = capture.get_buffer()
    print(f"Captured {len(audio_data)} samples")
    
    # Stop capture
    capture.stop()
    
    # Save to file
    if len(audio_data) > 0:
        filename = f"capture_{name.lower().replace('.exe', '')}_{pid}.wav"
        save_audio(audio_data, filename)
        
        # Calculate RMS to check if there's actual audio
        rms = np.sqrt(np.mean(audio_data**2))
        print(f"Audio RMS level: {rms:.6f}")
        
        if rms > 0.0001:
            print(f"SUCCESS: Captured audio from {name}")
            return True
        else:
            print(f"WARNING: Captured data but audio seems silent")
            return False
    else:
        print(f"FAILED: No audio captured from {name}")
        return False

def main():
    print("Process-Specific Audio Capture Test")
    print("=" * 60)
    
    # List current audio sessions
    print("\nListing current audio processes...")
    processes = loopback.list_audio_processes()
    
    if not processes:
        print("No audio processes found!")
        return
    
    print(f"Found {len(processes)} audio processes:")
    for proc in processes:
        print(f"  - {proc.name} (PID: {proc.pid})")
    
    # Test with known PIDs from user's system
    test_cases = [
        (51716, "Spotify.exe"),  # Spotify playing audio
        (93656, "firefox.exe"),  # Firefox playing audio
        (0, "System-wide")       # All system audio
    ]
    
    results = []
    
    for pid, name in test_cases:
        # Check if process is in the list (except system-wide)
        if pid != 0:
            found = any(p.pid == pid for p in processes)
            if not found:
                print(f"\nWarning: {name} (PID: {pid}) not found in audio processes")
                print("Process might not be playing audio right now")
        
        result = test_process_capture(pid, name, duration=3)
        results.append((name, result))
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY:")
    print("=" * 60)
    
    for name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"  {name}: {status}")
    
    # Check if process-specific recording works
    process_specific_works = any(success for name, success in results if name != "System-wide")
    
    if process_specific_works:
        print("\nCONCLUSION: Process-specific recording IS WORKING!")
    else:
        print("\nCONCLUSION: Process-specific recording is NOT working.")
        print("Only system-wide recording appears to be functional.")

if __name__ == "__main__":
    main()