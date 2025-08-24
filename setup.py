"""
Setup script for PyPAC - Python Process Audio Capture for Windows
"""

from setuptools import setup, find_packages
from pybind11.setup_helpers import Pybind11Extension, build_ext
import os

# Read the README for long description
def read_long_description():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read version from pypac/__init__.py
def get_version():
    init_path = os.path.join("pypac", "__init__.py")
    if os.path.exists(init_path):
        with open(init_path, "r") as f:
            for line in f:
                if line.startswith("__version__"):
                    return line.split("=")[1].strip().strip('"').strip("'")
    return "0.2.0"

# Define native extensions
ext_modules = [
    Pybind11Extension(
        "pypac._pypac_native",  # Will be imported as pypac._pypac_native
        ["src/audio_session_capture.cpp"],
        include_dirs=[],
        libraries=["ole32", "uuid", "mmdevapi", "psapi"],
        language="c++",
        cxx_std=17,
    ),
    Pybind11Extension(
        "process_loopback_v2",  # Test module for process-specific capture
        ["src/process_loopback_v2.cpp"],
        include_dirs=[],
        libraries=["ole32", "uuid", "mmdevapi", "avrt", "runtimeobject"],
        language="c++",
        cxx_std=17,
    ),
]

setup(
    name="pypac",
    version=get_version(),
    author="PyPAC Contributors",
    author_email="",
    description="Python Process Audio Capture for Windows - High-level audio control library",
    long_description=read_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pypac",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/pypac/issues",
        "Source": "https://github.com/yourusername/pypac",
        "Documentation": "https://github.com/yourusername/pypac#readme",
    },
    
    # Package configuration
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*", "tools", "tools.*"]),
    package_data={
        "pypac": ["py.typed"],  # Include type hints
        "pypac._native": ["*.pyd", "*.so"],  # Include compiled extensions
    },
    include_package_data=True,
    
    # Extensions
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    
    # Dependencies
    install_requires=[
        "numpy>=1.19.0",  # For audio processing
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black",
            "pylint",
            "mypy",
            "sphinx",
        ],
        "examples": [
            "psutil",  # For process debugging
        ],
    },
    
    # Python version requirement
    python_requires=">=3.7",
    
    # Classifiers
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Sound/Audio :: Capture/Recording",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: C++",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Operating System :: Microsoft :: Windows :: Windows 11",
    ],
    
    # Keywords for PyPI
    keywords="audio windows wasapi recording capture volume process loopback",
    
    # Entry points are defined in pyproject.toml
)