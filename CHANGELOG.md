# Changelog

All notable changes to PyWAC (Python Windows Audio Capture) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Unified `AudioData` class for consistent audio data handling
- Comprehensive test suite with 32+ tests
- `AudioData.get_statistics()` method for audio analysis
- `AudioData.to_mono()` and format conversion methods
- Migration guide documentation
- Example test script `test_audiodata.py`

### Changed
- **BREAKING**: All recording functions now return `AudioData` objects instead of `List[float]`
- **BREAKING**: Callbacks now receive `AudioData` objects
- **BREAKING**: Removed `utils.save_to_wav()` - use `AudioData.save()` instead
- Improved error handling for empty audio data
- Refactored `AudioRecorder` to use unified data format

### Deprecated
- `utils.save_to_wav()` - Use `AudioData.save()` instead
- `utils.load_wav()` - Use `AudioData.load()` instead

### Fixed
- Callback recording slow playback issue (was playing at half speed)
- Format inconsistency between C++ and Python layers
- `SessionManager.get_active_sessions()` now correctly returns string list

## [0.2.0] - 2024-12-XX

### Added
- Process-specific audio recording using Windows Process Loopback API
- Gradio demo application with full UI
- Volume control per application
- Async recording with callbacks
- Session management features

### Changed
- Restructured package architecture
- Improved native extension loading

### Fixed
- Thread safety in recording operations
- Memory leaks in native code

## [0.1.0] - 2024-12-XX

### Added
- Initial release
- Basic audio recording functionality
- System-wide audio capture
- WAV file export
- Simple Python API

[Unreleased]: https://github.com/yourusername/pypac/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/yourusername/pypac/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/yourusername/pypac/releases/tag/v0.1.0