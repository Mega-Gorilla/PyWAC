# PyWAC Documentation Structure

## 📁 Documentation Organization

```
pypac/
├── Root Documentation
│   ├── README.md              # Project overview (Japanese)
│   ├── README.en.md           # Project overview (English)
│   ├── CHANGELOG.md           # Version history
│   ├── RELEASE_NOTES.md       # Current release details
│   ├── VERSION               # Version number
│   ├── CLAUDE.md             # AI assistant instructions
│   └── THIRDPARTY.md         # Third-party licenses
│
├── docs/                     # Technical documentation
│   ├── README.md             # Documentation index
│   ├── API_REFERENCE.md      # API documentation
│   ├── PROCESS_LOOPBACK_INVESTIGATION.md  # Technical research
│   ├── STRUCTURE.md          # This file
│   ├── version-management.md # Version strategy
│   └── migrations/           # Migration guides
│       └── v0.3.0-audiodata.md
│
├── examples/                 # Usage examples
│   ├── basic_usage.py
│   ├── gradio_demo.py
│   ├── quick_test.py
│   └── test_audiodata.py
│
└── tests/                    # Test files
    ├── test_audio_data.py
    └── test_examples.py
```

## 📝 Document Purposes

### Root Level
- **README.md/README.en.md** - User-facing project documentation
- **CHANGELOG.md** - Track all user-facing changes
- **RELEASE_NOTES.md** - Detailed notes for current version
- **VERSION** - Single source of truth for version number
- **CLAUDE.md** - Instructions for AI assistants
- **THIRDPARTY.md** - License information for dependencies

### docs/ Directory
- **README.md** - Documentation hub and navigation
- **API_REFERENCE.md** - Complete API documentation
- **PROCESS_LOOPBACK_INVESTIGATION.md** - Technical deep-dive on Windows API
- **STRUCTURE.md** - This file, explaining documentation organization
- **version-management.md** - How we manage versions and releases
- **migrations/** - Version-specific migration guides

## 🎯 Documentation Guidelines

### When to Create Documentation
- **New Feature**: Update API_REFERENCE.md and add examples
- **Breaking Change**: Create migration guide in docs/migrations/
- **Bug Fix**: Update CHANGELOG.md
- **Research**: Add to docs/ with descriptive filename

### When NOT to Create Documentation
- Internal refactoring (unless it affects API)
- Temporary fixes or workarounds
- Experimental features not ready for users

## 🔄 Update Process

1. **During Development**
   - Update CHANGELOG.md (Unreleased section)
   - Add/update examples if needed
   - Update API_REFERENCE.md for new features

2. **Before Release**
   - Move Unreleased to version section in CHANGELOG.md
   - Update RELEASE_NOTES.md
   - Create migration guide if breaking changes
   - Update VERSION file

3. **After Release**
   - Tag in git
   - Create GitHub release
   - Archive old release notes if needed

## ✅ Documentation Checklist

For each change, ask:
- [ ] Does this affect users? → Update CHANGELOG.md
- [ ] Is this a new API? → Update API_REFERENCE.md
- [ ] Is this breaking? → Create migration guide
- [ ] Does this need an example? → Add to examples/
- [ ] Should users know how to test this? → Add tests

## 🚫 What NOT to Document

- Implementation details users don't need
- Internal class structures (unless public API)
- Temporary workarounds
- Debug code or logging
- Performance optimizations (unless user-visible)

## 📌 Key Principles

1. **User-Focused**: Documentation is for users, not developers
2. **Actionable**: Include examples and migration steps
3. **Versioned**: Keep documentation in sync with code
4. **Discoverable**: Clear structure and cross-references
5. **Maintainable**: Remove outdated docs, don't accumulate