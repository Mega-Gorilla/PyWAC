#!/usr/bin/env python
"""
PyPAC App Audio Recorder - Record audio from a specific application
Usage: python record_app_audio.py [app_name] [duration] [output_file]
Example: python record_app_audio.py firefox 5 firefox_audio.wav
"""

import sys
import os
import time
import wave
import struct
import argparse
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dist'))

def find_app_session(enumerator, app_name):
    """Find audio session for specified application"""
    sessions = enumerator.enumerate_sessions()
    
    # Search for matching process name (case-insensitive)
    app_name_lower = app_name.lower()
    for session in sessions:
        if app_name_lower in session.process_name.lower():
            return session
    
    return None

def save_to_wav(audio_data, filename, sample_rate=48000, channels=2):
    """Save audio data to WAV file"""
    # Convert float32 audio to int16
    audio_int16 = []
    for sample in audio_data:
        # Clip to [-1, 1] range
        sample = max(-1.0, min(1.0, sample))
        # Convert to int16
        audio_int16.append(int(sample * 32767))
    
    # Write WAV file
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        # Pack audio data as bytes
        packed_data = struct.pack('<%dh' % len(audio_int16), *audio_int16)
        wav_file.writeframes(packed_data)

def record_system_audio(duration_seconds=5, output_file="recording.wav"):
    """Record system audio for specified duration"""
    try:
        import pypac
        import numpy as np
    except ImportError as e:
        print(f"[ERROR] Failed to import required modules: {e}")
        print("Please ensure pypac is built and numpy is installed")
        return False
    
    # Start loopback capture
    loopback = pypac.SimpleLoopback()
    
    if not loopback.start():
        print("[ERROR] Failed to start audio capture")
        print("Try running as administrator")
        return False
    
    print(f"[RECORDING] Capturing system audio for {duration_seconds} seconds...")
    
    # Collect audio data
    all_audio = []
    start_time = time.time()
    last_update = 0
    
    while time.time() - start_time < duration_seconds:
        # Get audio buffer
        buffer = loopback.get_buffer()
        
        if len(buffer) > 0:
            all_audio.extend(buffer)
            
            # Show progress
            elapsed = time.time() - start_time
            if elapsed - last_update >= 1.0:
                remaining = duration_seconds - elapsed
                print(f"  [{int(elapsed)}s / {duration_seconds}s] Recording... ({int(remaining)}s remaining)")
                last_update = elapsed
        
        # Small sleep to prevent CPU overuse
        time.sleep(0.01)
    
    # Stop capture
    loopback.stop()
    
    if len(all_audio) == 0:
        print("[WARNING] No audio captured")
        return False
    
    # Save to WAV
    print(f"[SAVING] Writing {len(all_audio)} samples to {output_file}...")
    save_to_wav(all_audio, output_file)
    
    # Calculate file size and duration
    file_size = os.path.getsize(output_file)
    actual_duration = len(all_audio) / (48000 * 2)  # 48kHz, stereo
    
    print(f"[SUCCESS] Audio saved to {output_file}")
    print(f"  Duration: {actual_duration:.2f} seconds")
    print(f"  File size: {file_size / 1024:.2f} KB")
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description='Record audio from a specific application or system',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Record 5s of system audio to recording.wav
  %(prog)s firefox            # Record 5s from Firefox to firefox_recording.wav  
  %(prog)s firefox 10         # Record 10s from Firefox
  %(prog)s firefox 10 out.wav # Record 10s from Firefox to out.wav
  %(prog)s --list             # List all active audio sessions
        """
    )
    
    parser.add_argument('app_name', nargs='?', default=None,
                       help='Application name to record from (partial match supported)')
    parser.add_argument('duration', nargs='?', type=int, default=5,
                       help='Recording duration in seconds (default: 5)')
    parser.add_argument('output', nargs='?', default=None,
                       help='Output WAV filename (default: app_recording.wav)')
    parser.add_argument('--list', '-l', action='store_true',
                       help='List all audio sessions and exit')
    
    args = parser.parse_args()
    
    # Import pypac
    try:
        import pypac
    except ImportError as e:
        print(f"[ERROR] Failed to import pypac: {e}")
        print("Please build the module: python setup.py build_ext --inplace")
        return 1
    
    # List sessions mode
    if args.list:
        enumerator = pypac.SessionEnumerator()
        sessions = enumerator.enumerate_sessions()
        
        print("[AUDIO SESSIONS]")
        active_count = 0
        for session in sessions:
            state = "ACTIVE" if session.state == 1 else "INACTIVE"
            print(f"  [{state}] {session.process_name} (PID: {session.process_id})")
            if session.state == 1:
                active_count += 1
        
        if active_count == 0:
            print("\nNo active audio sessions. Play audio in an application and try again.")
        else:
            print(f"\n{active_count} active session(s) found")
        return 0
    
    # Generate output filename
    if args.output:
        output_file = args.output
    elif args.app_name:
        # Clean app name for filename
        safe_name = "".join(c for c in args.app_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{safe_name}_{timestamp}.wav"
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"recording_{timestamp}.wav"
    
    # Ensure .wav extension
    if not output_file.endswith('.wav'):
        output_file += '.wav'
    
    # Check if specific app was requested
    if args.app_name:
        print(f"[INFO] Looking for application: {args.app_name}")
        
        enumerator = pypac.SessionEnumerator()
        session = find_app_session(enumerator, args.app_name)
        
        if session:
            print(f"[FOUND] {session.process_name} (PID: {session.process_id})")
            
            if session.state != 1:
                print("[WARNING] Application is not currently playing audio")
                print("         Recording system audio instead...")
            else:
                print("[NOTE] PyPAC currently records all system audio")
                print("       Process-specific capture is under development")
        else:
            print(f"[WARNING] Application '{args.app_name}' not found")
            print("          Available applications:")
            
            sessions = enumerator.enumerate_sessions()
            for s in sessions:
                if s.state == 1:
                    print(f"            - {s.process_name}")
            
            print("\n[INFO] Recording all system audio instead...")
    
    # Record audio
    print(f"[CONFIG] Duration: {args.duration} seconds")
    print(f"[CONFIG] Output: {output_file}")
    print("")
    
    success = record_system_audio(args.duration, output_file)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())