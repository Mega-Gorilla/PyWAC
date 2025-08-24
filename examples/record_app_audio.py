#!/usr/bin/env python
"""
PyPAC App Audio Recorder - Record audio from a specific application using package API
Usage: python record_app_audio.py [app_name] [duration] [output_file]
Example: python record_app_audio.py firefox 5 firefox_audio.wav
"""

import pypac
import sys
import os
import time
import argparse
from datetime import datetime

def find_app_session(app_name):
    """Find audio session for specified application using package API"""
    sessions = pypac.list_audio_sessions()
    
    # Search for matching process name (case-insensitive)
    app_name_lower = app_name.lower()
    for session in sessions:
        if app_name_lower in session['process_name'].lower():
            return session
    
    return None

def record_system_audio(duration_seconds=5, output_file="recording.wav"):
    """Record system audio for specified duration using package API"""
    
    print(f"[RECORDING] Capturing system audio for {duration_seconds} seconds...")
    
    # Use the high-level API to record directly to file
    success = pypac.record_to_file(output_file, duration_seconds)
    
    if not success:
        print("[ERROR] Failed to record audio")
        print("Try running as administrator or check if audio is playing")
        return False
    
    # Check file was created and get info
    if os.path.exists(output_file):
        file_size = os.path.getsize(output_file)
        print(f"[SUCCESS] Audio saved to {output_file}")
        print(f"  Duration: {duration_seconds} seconds")
        print(f"  File size: {file_size / 1024:.2f} KB")
        return True
    else:
        print("[ERROR] Recording file was not created")
        return False

def record_with_progress(duration_seconds=5, output_file="recording.wav"):
    """Record audio with progress display using AudioRecorder class"""
    
    recorder = pypac.AudioRecorder()
    
    print(f"[RECORDING] Capturing system audio for {duration_seconds} seconds...")
    
    # Start recording
    if not recorder.start(duration=duration_seconds):
        print("[ERROR] Failed to start recording")
        print("Try running as administrator")
        return False
    
    # Show progress
    last_update = 0
    while recorder.is_recording:
        elapsed = recorder.recording_time
        samples = recorder.sample_count
        
        if elapsed - last_update >= 1.0:
            remaining = duration_seconds - elapsed
            progress = int((elapsed / duration_seconds) * 30)
            bar = "#" * progress + "-" * (30 - progress)
            print(f"  [{bar}] {elapsed:.0f}s / {duration_seconds}s ({samples:,} samples)", end='\r')
            last_update = elapsed
        
        time.sleep(0.1)
    
    print()  # New line after progress
    
    # Stop and save
    audio_data = recorder.stop()
    
    if len(audio_data) == 0:
        print("[WARNING] No audio captured")
        return False
    
    # Save to file
    print(f"[SAVING] Writing {len(audio_data):,} samples to {output_file}...")
    saved_file = recorder.save(output_file)
    
    if saved_file and os.path.exists(saved_file):
        file_size = os.path.getsize(saved_file)
        actual_duration = len(audio_data) / (48000 * 2)  # 48kHz, stereo
        
        print(f"[SUCCESS] Audio saved to {saved_file}")
        print(f"  Duration: {actual_duration:.2f} seconds")
        print(f"  File size: {file_size / 1024:.2f} KB")
        return True
    
    return False

def select_process_interactive():
    """Let user select a process interactively from available processes"""
    try:
        # Get recordable processes
        processes = pypac.list_recordable_processes()
        
        if not processes:
            print("[WARNING] No recordable processes found")
            return None, None
        
        print("\n[SELECT PROCESS TO RECORD]")
        print("-" * 40)
        print("  0. Record ALL system audio")
        
        for i, proc in enumerate(processes, 1):
            # Check if process is active
            sessions = pypac.list_audio_sessions()
            is_active = any(s['process_id'] == proc['pid'] and s['is_active'] for s in sessions)
            status = "[ACTIVE]" if is_active else "[INACTIVE]"
            print(f"  {i}. {proc['name']} (PID: {proc['pid']}) {status}")
        
        print("-" * 40)
        
        while True:
            try:
                choice = input(f"Enter choice (0-{len(processes)}) or 'q' to quit: ").strip()
                
                if choice.lower() == 'q':
                    return None, None
                
                choice_num = int(choice)
                
                if choice_num == 0:
                    return "system", None
                elif 1 <= choice_num <= len(processes):
                    selected = processes[choice_num - 1]
                    return selected['name'], selected['pid']
                else:
                    print(f"[ERROR] Please enter a number between 0 and {len(processes)}")
                    
            except ValueError:
                print("[ERROR] Please enter a valid number or 'q' to quit")
                
    except Exception as e:
        print(f"[ERROR] Failed to get process list: {e}")
        return None, None

def main():
    parser = argparse.ArgumentParser(
        description='Record audio from a specific application or system using PyPAC',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Interactive mode - select process from menu
  %(prog)s --interactive      # Interactive mode - select process from menu
  %(prog)s firefox            # Record 5s from Firefox to firefox_recording.wav  
  %(prog)s firefox 10         # Record 10s from Firefox
  %(prog)s firefox 10 out.wav # Record 10s from Firefox to out.wav
  %(prog)s --list             # List all active audio sessions
  %(prog)s --progress         # Show recording progress bar
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
    parser.add_argument('--progress', '-p', action='store_true',
                       help='Show progress bar during recording')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Interactive mode - select process from menu')
    
    args = parser.parse_args()
    
    # Print version
    print(f"PyPAC Audio Recorder v{pypac.__version__}")
    print("=" * 60)
    
    # List sessions mode
    if args.list:
        sessions = pypac.list_audio_sessions()
        
        print("[AUDIO SESSIONS]")
        active_count = 0
        for session in sessions:
            state = "ACTIVE" if session['is_active'] else "INACTIVE"
            vol_info = f"Vol: {session['volume_percent']:.0f}%"
            mute_info = "[MUTED]" if session['is_muted'] else ""
            print(f"  [{state}] {session['process_name']} (PID: {session['process_id']}) {vol_info} {mute_info}")
            if session['is_active']:
                active_count += 1
        
        # Show active sessions summary
        active_sessions = pypac.get_active_sessions()
        if active_sessions:
            print(f"\n{len(active_sessions)} active session(s): {', '.join(active_sessions)}")
        else:
            print("\nNo active audio sessions. Play audio in an application and try again.")
        return 0
    
    # Interactive mode - select process from menu
    if args.interactive or (args.app_name is None and not args.output):
        print("[INTERACTIVE MODE]")
        app_name, pid = select_process_interactive()
        
        if app_name is None:
            print("\n[INFO] Recording cancelled")
            return 0
        
        # Set app_name for further processing
        if app_name == "system":
            args.app_name = None  # Will record system audio
            print("\n[INFO] Recording ALL system audio")
        else:
            args.app_name = app_name
            print(f"\n[INFO] Selected: {app_name} (PID: {pid})")
    
    # Create recordings directory if it doesn't exist
    from pathlib import Path
    script_dir = Path(__file__).parent
    recordings_dir = script_dir / "recordings"
    recordings_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate output filename
    if args.output:
        # If output path is provided, use it as-is or place in recordings dir
        output_path = Path(args.output)
        if output_path.is_absolute():
            output_file = str(output_path)
        else:
            output_file = str(recordings_dir / output_path)
    elif args.app_name:
        # Clean app name for filename
        safe_name = "".join(c for c in args.app_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name.replace('.exe', '').replace(' ', '_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = str(recordings_dir / f"{safe_name}_{timestamp}.wav")
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = str(recordings_dir / f"recording_{timestamp}.wav")
    
    # Ensure .wav extension
    if not output_file.endswith('.wav'):
        output_file += '.wav'
    
    # Check if specific app was requested
    if args.app_name:
        print(f"[INFO] Looking for application: {args.app_name}")
        
        session = find_app_session(args.app_name)
        
        if session:
            print(f"[FOUND] {session['process_name']} (PID: {session['process_id']})")
            
            if not session['is_active']:
                print("[WARNING] Application is not currently playing audio")
                print("         Recording system audio instead...")
            else:
                # Try process-specific recording
                print("[INFO] Attempting process-specific recording...")
                success = pypac.record_process(args.app_name, output_file, args.duration)
                if success:
                    print(f"[SUCCESS] Process-specific audio saved to {output_file}")
                    return 0
                else:
                    print("[FALLBACK] Recording system audio instead...")
        else:
            print(f"[WARNING] Application '{args.app_name}' not found")
            
            # Show available sessions
            active_sessions = pypac.get_active_sessions()
            if active_sessions:
                print("          Available sessions:")
                for session in active_sessions:
                    print(f"            - {session}")
            else:
                print("          No applications currently playing audio")
            
            print("\n[INFO] Recording all system audio instead...")
    
    # Record audio
    print(f"[CONFIG] Duration: {args.duration} seconds")
    print(f"[CONFIG] Output: {output_file}")
    if not Path(output_file).is_absolute():
        print(f"[CONFIG] Recording directory: {recordings_dir}")
    print("")
    
    # Use progress recording if requested
    if args.progress:
        success = record_with_progress(args.duration, output_file)
    else:
        success = record_system_audio(args.duration, output_file)
    
    return 0 if success else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except ImportError as e:
        print("=" * 60)
        print("ERROR: Failed to import pypac module")
        print("=" * 60)
        print(f"Details: {e}")
        print("\nPlease install the package:")
        print("  pip install -e .")
        print("\nOr build the module:")
        print("  python setup.py build_ext --inplace")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[INFO] Recording cancelled by user")
        sys.exit(0)