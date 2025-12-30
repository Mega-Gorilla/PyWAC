# Changelog

All notable changes to PyWAC (Python Windows Audio Capture) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2024-12-30

### Added
- Thread-safe singleton pattern for `SessionManager`
- `refresh_sessions()` function to re-enumerate audio sessions
- Migration guide: `docs/migrations/v1.0.0-module-rename.md`
- Test suite: `tests/test_import_structure.py`

### Changed
- **BREAKING**: Native module renamed from `pywac._pywac_native` to `pywac.core`
- **BREAKING**: Native module renamed from `process_loopback_queue` to `pywac.capture`
- **BREAKING**: Removed `pywac/_native/` directory (no longer needed)
- Made `pywac.core` and `pywac.capture` public APIs
- Simplified import statements throughout the codebase
- Updated all documentation, examples, and tools to use new module names

### Deprecated
- `find_app()` - Use `find_audio_session()` instead
- `get_active_apps()` - Use `get_active_sessions()` instead

### Migration
See [`docs/migrations/v1.0.0-module-rename.md`](docs/migrations/v1.0.0-module-rename.md) for detailed migration instructions.

## [0.4.1] - 2024-12-26

### Added
- **Event-driven audio capture** using WASAPI SetEventHandle API
- Automatic fallback to polling mode for compatibility
- Event metrics tracking (`event_signals`, `timeouts`)
- Performance mode detection in metrics API

### Changed
- **Performance**: CPU usage reduced from 3-5% to < 1% in event-driven mode
- **Performance**: Eliminated polling in C++ capture thread when events are available
- **Efficiency**: 100% event efficiency achieved (499 events, 0 timeouts)
- Capture thread now reports mode (event-driven or polling)

### Fixed
- Unnecessary CPU usage from 1ms polling in capture loop
- WaitForMultipleObjects now properly handles audio events

## [0.4.0] - 2024-12-26

### Added
- **Queue-based architecture** for GIL-safe audio capture
- `process_loopback_queue` C++ module with thread-safe queue
- `QueueBasedStreamingCapture` class with adaptive polling
- `capture_process_audio()` convenience function
- Comprehensive performance metrics API
- Batch processing support for efficiency
- Migration guide for v0.4.0
- Test suite for queue-based implementation

### Changed
- **BREAKING**: Module reorganization - use `process_loopback_queue` instead of `process_loopback_v2`
- **BREAKING**: New streaming interface with `QueueBasedStreamingCapture`
- **Performance**: CPU usage reduced from 30-100% to < 5%
- **Performance**: Consistent 10ms latency (was variable)
- **Reliability**: Zero data loss with bounded queue (was destructive reads)

### Deprecated
- `process_loopback_v2` - Use `process_loopback_queue` instead
- `process_loopback_v3` - Has GIL issues, use queue-based approach

### Fixed
- **Critical**: GIL management crashes in callback-based approach
- **Critical**: High CPU usage from polling architecture
- **Critical**: Data loss from destructive buffer reads
- Thread state issues with C++ to Python callbacks
- Memory inefficiency in polling implementation

## [0.3.0] - 2024-12-25

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

[Unreleased]: https://github.com/Mega-Gorilla/pywac/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Mega-Gorilla/pywac/compare/v0.4.1...v1.0.0
[0.4.1]: https://github.com/Mega-Gorilla/pywac/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/Mega-Gorilla/pywac/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/Mega-Gorilla/pywac/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/Mega-Gorilla/pywac/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Mega-Gorilla/pywac/releases/tag/v0.1.0