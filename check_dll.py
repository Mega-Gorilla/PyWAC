"""Check DLL dependencies"""
import os
import sys
import ctypes

print("Checking pypac module dependencies...")
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

# Check if running in venv
in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
print(f"Running in virtual environment: {in_venv}")

# Add dist to path
dist_path = os.path.join(os.path.dirname(__file__), 'dist')
sys.path.insert(0, dist_path)
print(f"\nDist path: {dist_path}")

# List files in dist
print("\nFiles in dist:")
for file in os.listdir(dist_path):
    if file.endswith('.pyd'):
        filepath = os.path.join(dist_path, file)
        size = os.path.getsize(filepath)
        print(f"  - {file} ({size:,} bytes)")

# Try to load the module
print("\nTrying to import pypac...")
try:
    import pypac
    print("[SUCCESS] pypac imported successfully!")
except ImportError as e:
    print(f"[FAILED] Import error: {e}")
    
    # Try to load as DLL directly
    pyd_path = os.path.join(dist_path, "pypac.pyd")
    if os.path.exists(pyd_path):
        print(f"\nTrying to load {pyd_path} as DLL...")
        try:
            dll = ctypes.CDLL(pyd_path)
            print("[SUCCESS] DLL loaded with ctypes")
        except Exception as e2:
            print(f"[FAILED] DLL load error: {e2}")
            print("\nThis usually means missing dependencies like:")
            print("  - Visual C++ Redistributable")
            print("  - Windows SDK libraries")
            print("  - Python development files")