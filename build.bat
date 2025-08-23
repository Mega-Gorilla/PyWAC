@echo off
echo Building process_loopback module...
call .\.venv\Scripts\activate.bat
python setup.py build_ext --inplace
echo Build complete!