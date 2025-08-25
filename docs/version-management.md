# Version Management Strategy for PyWAC

## 📋 Overview

This document outlines the version management and documentation strategy for PyWAC.

## 🏗️ Repository Structure

```
pypac/
├── CHANGELOG.md           # User-facing changelog (Keep a Changelog format)
├── RELEASE_NOTES.md       # Detailed release notes for current version
├── VERSION               # Current version number
├── docs/
│   ├── README.md         # Documentation index
│   ├── migrations/       # Version-specific migration guides
│   │   ├── v0.3.0-audiodata.md
│   │   └── v0.4.0-xxx.md
│   ├── archive/          # Historical/deprecated docs
│   └── API_REFERENCE.md  # Current API documentation
└── .github/
    └── release-template.md  # Template for GitHub releases

```

## 🔢 Versioning Strategy

### Semantic Versioning
We follow [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH** (e.g., 0.3.0)
- **MAJOR**: Breaking API changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Version Locations
1. `VERSION` file - Single source of truth
2. `setup.py` - Read from VERSION file
3. `pywac/__init__.py` - `__version__` attribute
4. Git tags - `v0.3.0` format

## 📝 Documentation Management

### 1. CHANGELOG.md
- **Format**: [Keep a Changelog](https://keepachangelog.com/)
- **Sections**: Added, Changed, Deprecated, Removed, Fixed, Security
- **Audience**: All users
- **Update**: Every commit that affects users

### 2. Migration Guides
- **Location**: `docs/migrations/v{VERSION}-{feature}.md`
- **Format**: Step-by-step instructions
- **Content**:
  - Breaking changes
  - Before/after code examples
  - Automated migration scripts (if applicable)

### 3. Release Notes
- **RELEASE_NOTES.md**: Current version details
- **GitHub Releases**: Per-version archives
- **Content**:
  - Summary of changes
  - Breaking changes highlight
  - Migration guide links
  - Contributor acknowledgments

### 4. API Documentation
- **Location**: `docs/API_REFERENCE.md`
- **Versioned**: Tagged with releases
- **Generated**: Consider using tools like Sphinx

## 🚀 Release Process

### 1. Pre-release
```bash
# Update version
echo "0.3.0" > VERSION

# Update CHANGELOG.md
# Move Unreleased to new version section

# Create migration guide if needed
touch docs/migrations/v0.3.0-feature.md

# Update RELEASE_NOTES.md
```

### 2. Release
```bash
# Commit changes
git add -A
git commit -m "chore: Release v0.3.0"

# Create tag
git tag -a v0.3.0 -m "Release v0.3.0"

# Push
git push origin main --tags
```

### 3. Post-release
1. Create GitHub Release using `.github/release-template.md`
2. Attach built wheels/packages
3. Announce on project channels

## 🔄 Update Notes Best Practices

### DO:
- ✅ Keep CHANGELOG.md updated with every user-facing change
- ✅ Create migration guides for breaking changes
- ✅ Use clear, concise language
- ✅ Include code examples in migration guides
- ✅ Link between related documents

### DON'T:
- ❌ Mix internal changes with user-facing changes
- ❌ Use technical jargon without explanation
- ❌ Forget to update VERSION file
- ❌ Skip migration guides for breaking changes

## 📚 Documentation Workflow

### For Breaking Changes:
1. Update `CHANGELOG.md` - Add to Unreleased/Changed
2. Create migration guide in `docs/migrations/`
3. Update API documentation
4. Add deprecation warnings in code

### For New Features:
1. Update `CHANGELOG.md` - Add to Unreleased/Added
2. Update API documentation
3. Add usage examples
4. Update README if significant

### For Bug Fixes:
1. Update `CHANGELOG.md` - Add to Unreleased/Fixed
2. Add test case
3. Update documentation if behavior changed

## 🏷️ Git Tag Convention

```bash
# Release tags
v0.3.0          # Stable release
v0.3.0-rc.1     # Release candidate
v0.3.0-beta.1   # Beta release
v0.3.0-alpha.1  # Alpha release

# Feature branches
feature/audio-data
fix/callback-recording
docs/migration-guide
```

## 📊 Version History Tracking

### Tools:
- **git-cliff**: Generate changelog from commits
- **standard-version**: Automated versioning
- **release-please**: Google's release automation

### Commit Convention:
```
feat: Add new feature
fix: Fix bug
docs: Update documentation
chore: Maintenance task
refactor: Code refactoring
test: Add tests
BREAKING CHANGE: Description
```

## 🔍 Finding Version Information

Users can find version information:
1. **Current version**: `pywac.__version__`
2. **Changelog**: `CHANGELOG.md`
3. **Migration guides**: `docs/migrations/`
4. **Release notes**: GitHub Releases page
5. **API changes**: API documentation

## 💡 Examples

### Creating a Migration Guide:
```markdown
# Migration Guide: v0.3.0 - AudioData

## Overview
Version 0.3.0 introduces AudioData class...

## Breaking Changes

### 1. Recording Functions
**Before (v0.2.x):**
\```python
audio_data = pywac.record_audio(3)  # List[float]
\```

**After (v0.3.0):**
\```python
audio = pywac.record_audio(3)  # AudioData
\```

## Migration Steps
1. Update import statements
2. Replace save_to_wav calls
3. Update callback functions
```

This strategy ensures clear, organized version management that helps users understand changes and migrate smoothly between versions.