"""Check DLL dependencies"""
import os
import sys
import ctypes

print("Checking pywac module dependencies...")
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

# Check if running in venv
in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
print(f"Running in virtual environment: {in_venv}")

# Add parent directory to path (where .pyd files are)
parent_path = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, parent_path)
print(f"\nModule path: {parent_path}")

# List .pyd files in parent and pywac directories
print("\n.pyd files found:")
import glob
pyd_files = glob.glob(os.path.join(parent_path, '*.pyd'))
pyd_files.extend(glob.glob(os.path.join(parent_path, 'pywac', '*.pyd')))

for filepath in pyd_files:
    size = os.path.getsize(filepath)
    filename = os.path.basename(filepath)
    print(f"  - {filename} ({size:,} bytes)")

# Try to load the module
print("\nTrying to import pywac...")
try:
    import pywac
    print("[SUCCESS] pywac imported successfully!")
except ImportError as e:
    print(f"[FAILED] Import error: {e}")
    
    # Try to load .pyd files as DLL directly to check dependencies
    print("\nTrying to load .pyd files directly...")
    for pyd_path in pyd_files[:2]:  # Test first 2 files
        filename = os.path.basename(pyd_path)
        print(f"\nLoading {filename}...")
        try:
            dll = ctypes.CDLL(pyd_path)
            print(f"  [SUCCESS] {filename} loaded with ctypes")
        except Exception as e2:
            print(f"  [FAILED] DLL load error: {e2}")
            if "specified module could not be found" in str(e2):
                print("  This usually means missing dependencies like:")
                print("    - Visual C++ Redistributable")
                print("    - Windows SDK libraries")
                print("    - Python development files")