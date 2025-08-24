"""
PyPAC Volume Controller - Interactive volume control for running applications
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dist'))

def main():
    try:
        import pypac
    except ImportError as e:
        print(f"Error: {e}")
        print("Please build the module: python setup.py build_ext --inplace")
        return
    
    print("=" * 60)
    print("PYPAC VOLUME CONTROLLER")
    print("=" * 60)
    
    # Get sessions
    enumerator = pypac.SessionEnumerator()
    sessions = enumerator.enumerate_sessions()
    
    # Filter active sessions
    active_sessions = [s for s in sessions if s.state == 1]
    
    if not active_sessions:
        print("No active audio sessions found.")
        print("Please play audio in an application and try again.")
        return
    
    # Display sessions
    print("\nActive Audio Sessions:")
    for i, session in enumerate(active_sessions, 1):
        mute_status = "[MUTED]" if session.muted else f"[VOL: {session.volume:.0%}]"
        print(f"{i}. {session.process_name} - {mute_status}")
    
    # User selection
    print("\nSelect an application to control (number):")
    try:
        choice = int(input("> ")) - 1
        if 0 <= choice < len(active_sessions):
            selected = active_sessions[choice]
            
            print(f"\nControlling: {selected.process_name}")
            print("Enter new volume (0-100) or 'm' to toggle mute:")
            
            action = input("> ").strip().lower()
            
            if action == 'm':
                # Toggle mute
                new_mute = not selected.muted
                if enumerator.set_session_mute(selected.process_id, new_mute):
                    print(f"[OK] {'Muted' if new_mute else 'Unmuted'} {selected.process_name}")
                else:
                    print("[ERROR] Failed to change mute state")
            else:
                # Set volume
                try:
                    volume = int(action)
                    if 0 <= volume <= 100:
                        if enumerator.set_session_volume(selected.process_id, volume / 100):
                            print(f"[OK] Set {selected.process_name} volume to {volume}%")
                        else:
                            print("[ERROR] Failed to change volume")
                    else:
                        print("[ERROR] Volume must be between 0 and 100")
                except ValueError:
                    print("[ERROR] Invalid input")
        else:
            print("[ERROR] Invalid selection")
    except (ValueError, EOFError):
        print("[ERROR] Invalid input")

if __name__ == "__main__":
    main()