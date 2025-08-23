from setuptools import setup, Extension
from pybind11.setup_helpers import Pybind11Extension, build_ext

ext_modules = [
    Pybind11Extension(
        "process_loopback",
        ["src/process_loopback.cpp"],
        include_dirs=[],
        libraries=["ole32", "uuid"],
        language="c++",
        cxx_std=17,
    ),
    Pybind11Extension(
        "audio_session_capture",
        ["src/audio_session_capture.cpp"],
        include_dirs=[],
        libraries=["ole32", "uuid", "mmdevapi", "psapi"],
        language="c++",
        cxx_std=17,
    ),
]

setup(
    name="process_loopback",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    python_requires=">=3.7",
)