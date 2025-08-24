#!/usr/bin/env python
"""
Process-Specific Audio Recording Example
Records audio from a specific application only (Windows 10 2004+)

This example demonstrates the NEW process-specific recording feature using 
Windows Process Loopback API. It can record audio from a single application
without mixing audio from other sources.

Usage:
    python process_specific_recording.py           # Interactive mode
    python process_specific_recording.py spotify   # Record from Spotify
    python process_specific_recording.py firefox 10 # Record Firefox for 10 seconds
"""

import sys
import time
import wave
import numpy as np

try:
    import process_loopback_v2 as loopback
except ImportError:
    print("Error: process_loopback_v2 module not found!")
    print("Please build the module first:")
    print("  python setup.py build_ext --inplace")
    sys.exit(1)

def save_audio_to_wav(audio_data, filename, sample_rate=48000, channels=2):
    """Save audio data to WAV file"""
    if len(audio_data) == 0:
        print(f"No audio data to save")
        return False
    
    # Convert float32 to int16
    audio_int16 = (audio_data * 32767).astype(np.int16)
    
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())
    
    duration = len(audio_data) / (sample_rate * channels)
    file_size = audio_int16.nbytes
    
    print(f"[SUCCESS] Saved {duration:.2f} seconds of audio to {filename}")
    print(f"          File size: {file_size / 1024:.2f} KB")
    print(f"          Sample rate: {sample_rate} Hz")
    print(f"          Channels: {channels}")
    
    return True

def list_audio_processes():
    """List all processes with audio sessions"""
    print("\n[AUDIO PROCESSES]")
    print("-" * 60)
    
    processes = loopback.list_audio_processes()
    
    if not processes:
        print("No audio processes found!")
        print("Make sure applications are playing audio and try again.")
        return None
    
    print(f"Found {len(processes)} process(es) with audio sessions:\n")
    
    for i, proc in enumerate(processes, 1):
        print(f"  {i}. {proc.name} (PID: {proc.pid})")
    
    return processes

def select_process_interactive(processes):
    """Let user select a process interactively"""
    while True:
        print("\nSelect a process to record from:")
        print("  0. Record ALL system audio")
        for i, proc in enumerate(processes, 1):
            print(f"  {i}. {proc.name}")
        
        try:
            choice = input("\nEnter choice (0-{}): ".format(len(processes)))
            choice = int(choice)
            
            if choice == 0:
                return 0, "System-wide"
            elif 1 <= choice <= len(processes):
                selected = processes[choice - 1]
                return selected.pid, selected.name
            else:
                print("Invalid choice. Please try again.")
        except (ValueError, KeyboardInterrupt):
            print("\nCancelled.")
            return None, None

def find_process_by_name(processes, name):
    """Find process by name (case-insensitive partial match)"""
    name_lower = name.lower()
    
    for proc in processes:
        if name_lower in proc.name.lower():
            return proc.pid, proc.name
    
    return None, None

def record_process_audio(pid, process_name, duration=5):
    """Record audio from a specific process"""
    print("\n" + "=" * 60)
    print(f"PROCESS-SPECIFIC AUDIO RECORDING")
    print("=" * 60)
    
    if pid == 0:
        print(f"Target: ALL SYSTEM AUDIO")
    else:
        print(f"Target: {process_name} (PID: {pid})")
    
    print(f"Duration: {duration} seconds")
    print("-" * 60)
    
    # Create capture instance
    capture = loopback.ProcessCapture()
    
    # Start capturing
    print(f"\n[STARTING] Initializing audio capture...")
    
    success = capture.start(pid)
    
    if not success:
        print("[ERROR] Failed to start audio capture!")
        print("\nPossible reasons:")
        print("  1. Windows version < 2004 (Build 19041)")
        print("  2. Process not producing audio")
        print("  3. Audio device configuration issues")
        print("  4. Need administrator privileges")
        return False
    
    print("[RECORDING] Capturing audio...")
    
    # Show progress
    start_time = time.time()
    last_update = 0
    
    while time.time() - start_time < duration:
        elapsed = time.time() - start_time
        
        if elapsed - last_update >= 0.5:
            # Get current buffer to show activity
            buffer = capture.get_buffer()
            activity = "*" if len(buffer) > 0 else " "
            
            remaining = duration - elapsed
            progress = int((elapsed / duration) * 30)
            bar = "█" * progress + "░" * (30 - progress)
            
            print(f"  [{bar}] {elapsed:.1f}s / {duration}s {activity}", end='\r')
            last_update = elapsed
        
        time.sleep(0.1)
    
    print(f"\n\n[STOPPING] Finalizing capture...")
    
    # Get captured audio
    audio_data = capture.get_buffer()
    
    # Stop capture
    capture.stop()
    
    if len(audio_data) == 0:
        print("[WARNING] No audio was captured!")
        print("          Make sure the application is playing audio.")
        return False
    
    # Generate filename
    if pid == 0:
        filename = f"system_audio_{int(time.time())}.wav"
    else:
        safe_name = process_name.replace('.exe', '').replace('.', '_')
        filename = f"{safe_name}_{pid}_{int(time.time())}.wav"
    
    # Save to file
    print(f"\n[SAVING] Writing audio to {filename}...")
    
    if save_audio_to_wav(audio_data, filename):
        # Calculate and show audio statistics
        rms = np.sqrt(np.mean(audio_data**2))
        peak = np.max(np.abs(audio_data))
        
        print(f"\n[STATISTICS]")
        print(f"  Samples captured: {len(audio_data):,}")
        print(f"  RMS level: {rms:.6f}")
        print(f"  Peak level: {peak:.6f}")
        print(f"  Dynamic range: {20 * np.log10(peak/rms if rms > 0 else 1):.1f} dB")
        
        return True
    
    return False

def main():
    print("\n" + "=" * 60)
    print("PYPAC PROCESS-SPECIFIC AUDIO RECORDER")
    print("Windows Process Loopback API Demo")
    print("=" * 60)
    
    # Get command line arguments
    args = sys.argv[1:]
    
    # List available processes
    processes = loopback.list_audio_processes()
    
    if not processes and len(args) == 0:
        print("\nNo audio processes found!")
        print("Please start playing audio in an application and try again.")
        return 1
    
    # Determine target process
    if len(args) == 0:
        # Interactive mode
        if processes:
            list_audio_processes()
            pid, name = select_process_interactive(processes)
            if pid is None:
                return 0
        else:
            print("Recording system-wide audio (no specific processes found)")
            pid, name = 0, "System-wide"
        duration = 5
        
    elif len(args) >= 1:
        # Command line mode
        app_name = args[0]
        duration = int(args[1]) if len(args) > 1 else 5
        
        # Find process by name
        if processes:
            pid, name = find_process_by_name(processes, app_name)
            
            if pid is None:
                print(f"\n[WARNING] Process '{app_name}' not found!")
                print("\nAvailable processes:")
                for proc in processes:
                    print(f"  - {proc.name}")
                
                print(f"\nRecording system-wide audio instead...")
                pid, name = 0, "System-wide"
        else:
            print(f"[INFO] No specific processes found, recording system-wide")
            pid, name = 0, "System-wide"
    
    # Validate duration
    if duration < 1:
        duration = 1
    elif duration > 300:
        duration = 300
        print(f"[INFO] Duration limited to {duration} seconds")
    
    # Record audio
    success = record_process_audio(pid, name, duration)
    
    if success:
        print("\n" + "=" * 60)
        print("Recording completed successfully!")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("Recording failed. See error messages above.")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Recording stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)