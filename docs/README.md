# PyWAC Documentation

Welcome to the PyWAC documentation directory. This folder contains all technical documentation, migration guides, and architectural information.

## 📚 Documentation Structure

### Core Documentation
- [`API_REFERENCE.md`](./API_REFERENCE.md) - Complete API reference (v0.4.0 updated)
- [`PROCESS_LOOPBACK_INVESTIGATION.md`](./PROCESS_LOOPBACK_INVESTIGATION.md) - Windows Process Loopback API research

### Architecture Documentation (v0.4.0)
- [`queue_implementation_summary.md`](./queue_implementation_summary.md) - **Start here!** Queue-based architecture overview
- [`pywac_dataflow_and_issues.md`](./pywac_dataflow_and_issues.md) - Original problem analysis
- [`implementation_analysis.md`](./implementation_analysis.md) - Comprehensive feature inventory
- [`technical_deep_dive.md`](./technical_deep_dive.md) - Performance analysis
- [`queue_based_implementation_plan.md`](./queue_based_implementation_plan.md) - Queue solution design
- [`callback_architecture_plan.md`](./callback_architecture_plan.md) - Initial callback approach (has GIL issues)

### Migration Guides
- [`migrations/`](./migrations/) - Version-specific migration guides
  - [`v0.4.0-queue-architecture.md`](./migrations/v0.4.0-queue-architecture.md) - **Queue architecture migration** (Latest)
  - [`v0.3.0-audiodata.md`](./migrations/v0.3.0-audiodata.md) - AudioData class introduction

### Development
- [`version-management.md`](./version-management.md) - Version management strategy
- [`STRUCTURE.md`](./STRUCTURE.md) - Documentation organization

## 🔄 Version Management

### Current Version: 0.4.0 (Queue-Based Architecture)

**Major Changes in v0.4.0:**
- ✅ Queue-based architecture resolves GIL issues
- ✅ CPU usage reduced to < 5% (from 30-100%)
- ✅ Zero data loss with thread-safe queue
- ✅ Adaptive polling for optimal performance
- ✅ Production-ready with Spotify, Chrome, etc.

For version-specific documentation:
- Check the git tag for the version you're using
- Migration guides are in `docs/migrations/`
- Breaking changes are documented in [`CHANGELOG.md`](../CHANGELOG.md)

## 🚨 Important: Architecture Change

**v0.4.0 introduces a queue-based architecture that replaces the problematic polling and callback approaches:**

```python
# Old (v0.3.x) - High CPU usage
import process_loopback_v2 as loopback
capture = loopback.ProcessCapture()
# Polling with 30-100% CPU usage

# New (v0.4.0) - Efficient queue-based
from pywac.queue_streaming import QueueBasedStreamingCapture
capture = QueueBasedStreamingCapture(process_id=pid)
# < 5% CPU usage with adaptive polling
```

See [`migrations/v0.4.0-queue-architecture.md`](./migrations/v0.4.0-queue-architecture.md) for migration details.

## 📝 Update Notes Location

Update notes and release information are managed as follows:

1. **CHANGELOG.md** (root) - User-facing changes
2. **GitHub Releases** - Detailed release notes with binaries
3. **Migration Guides** - Step-by-step upgrade instructions
4. **API Documentation** - Version-specific API changes

## 🚀 Quick Links

### Getting Started
- [Latest API Reference](./API_REFERENCE.md)
- [Queue Implementation Overview](./queue_implementation_summary.md)

### Migration
- [Migration from v0.3.x to v0.4.0](./migrations/v0.4.0-queue-architecture.md)
- [Migration from v0.2.x to v0.3.0](./migrations/v0.3.0-audiodata.md)

### Technical Deep-Dives
- [Queue Architecture Design](./queue_based_implementation_plan.md)
- [Performance Analysis](./technical_deep_dive.md)
- [Problem Analysis](./pywac_dataflow_and_issues.md)

## 📊 Performance Metrics (v0.4.0)

The queue-based implementation achieves:
- **CPU Usage**: < 5% (was 30-100%)
- **Latency**: ~10ms consistent
- **Data Loss**: 0% (zero dropped chunks)
- **Memory**: Minimal overhead with bounded queue
- **Thread Safety**: Full GIL compliance

Example performance from Spotify capture:
```
Duration: 5.02 seconds
Total chunks: 499
Dropped chunks: 0
Efficiency: 1.04 chunks/poll
CPU usage: < 5%
```

## 📦 Module Overview

### Core Modules (v0.4.0)
- `process_loopback_queue` - C++ queue-based capture (recommended)
- `pywac.queue_streaming` - Python streaming interface
- `pywac.audio_data` - Unified audio data container

### Deprecated Modules
- `process_loopback_v2` - Polling-based (high CPU usage)
- `process_loopback_v3` - Callback-based (GIL issues)

## 🔍 Finding Information

- **Performance Issues**: See [`queue_implementation_summary.md`](./queue_implementation_summary.md)
- **API Changes**: Check [`API_REFERENCE.md`](./API_REFERENCE.md)
- **Migration Help**: See [`migrations/`](./migrations/)
- **Usage Examples**: Check `examples/` and test files
- **Technical Details**: Read architecture documentation

## 🐛 Known Issues and Solutions

### v0.3.x and Earlier
- ❌ High CPU usage (30-100%) - Fixed in v0.4.0
- ❌ GIL crashes with callbacks - Fixed in v0.4.0
- ❌ Data loss with polling - Fixed in v0.4.0

### v0.4.0
- ✅ All major issues resolved
- ✅ Production-ready implementation
- ✅ Tested with real applications

## 📈 Version History

- **v0.4.0** - Queue-based architecture, < 5% CPU, GIL-safe
- **v0.3.0** - AudioData class, unified format handling
- **v0.2.0** - Process Loopback API implementation
- **v0.1.0** - Initial WASAPI support