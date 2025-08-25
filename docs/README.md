# PyWAC Documentation

Welcome to the PyWAC documentation directory. This folder contains all technical documentation, migration guides, and architectural information.

## 📚 Documentation Structure

### Core Documentation
- [`API_REFERENCE.md`](./API_REFERENCE.md) - Complete API reference
- [`ARCHITECTURE.md`](./ARCHITECTURE.md) - System architecture and design decisions
- [`BUILD_GUIDE.md`](./BUILD_GUIDE.md) - Building from source instructions

### Migration Guides
- [`migrations/`](./migrations/) - Version-specific migration guides
  - [`v0.3.0-audiodata.md`](./migrations/v0.3.0-audiodata.md) - AudioData migration guide

### Development
- [`CONTRIBUTING.md`](./CONTRIBUTING.md) - Contribution guidelines
- [`TESTING.md`](./TESTING.md) - Testing guidelines and strategies

### Archives
- [`archive/`](./archive/) - Deprecated documentation and historical notes

## 🔄 Version Management

### Current Version: 0.3.0 (Unreleased)

For version-specific documentation:
- Check the git tag for the version you're using
- Migration guides are in `docs/migrations/`
- Breaking changes are documented in [`CHANGELOG.md`](../CHANGELOG.md)

## 📝 Update Notes Location

Update notes and release information are managed as follows:

1. **CHANGELOG.md** (root) - User-facing changes
2. **GitHub Releases** - Detailed release notes with binaries
3. **Migration Guides** - Step-by-step upgrade instructions
4. **API Documentation** - Version-specific API changes

## 🚀 Quick Links

- [Latest API Reference](./API_REFERENCE.md)
- [Migration from v0.2.x](./migrations/v0.3.0-audiodata.md)
- [Building from Source](./BUILD_GUIDE.md)
- [Contributing](./CONTRIBUTING.md)

## 📦 Documentation Versions

Documentation is versioned alongside the code:
- Documentation for each release is tagged with the release version
- `main` branch contains documentation for the latest development version
- Release branches contain stable documentation

## 🔍 Finding Information

- **API Changes**: Check `CHANGELOG.md` and migration guides
- **Usage Examples**: See `examples/` directory
- **Technical Details**: Read architecture documentation
- **Troubleshooting**: Check FAQ and known issues in release notes