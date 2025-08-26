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
│   ├── API_REFERENCE.md      # API documentation (v0.4.0 updated)
│   ├── PROCESS_LOOPBACK_INVESTIGATION.md  # Technical research
│   ├── STRUCTURE.md          # This file
│   ├── version-management.md # Version strategy
│   ├── pywac_dataflow_and_issues.md  # Original problem analysis
│   ├── implementation_analysis.md     # Feature inventory & problems
│   ├── technical_deep_dive.md         # Architecture analysis
│   ├── callback_architecture_plan.md  # Callback approach (GIL issues)
│   ├── queue_based_implementation_plan.md  # Queue solution design
│   ├── queue_implementation_summary.md     # Final implementation results
│   └── migrations/           # Migration guides
│       ├── v0.3.0-audiodata.md
│       └── v0.4.0-queue-architecture.md  # Queue migration guide
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
- **API_REFERENCE.md** - Complete API documentation (v0.4.0: queue-based architecture)
- **PROCESS_LOOPBACK_INVESTIGATION.md** - Technical deep-dive on Windows API
- **STRUCTURE.md** - This file, explaining documentation organization
- **version-management.md** - How we manage versions and releases

#### Implementation Documentation (v0.4.0)
- **pywac_dataflow_and_issues.md** - Original polling architecture problems
- **implementation_analysis.md** - Comprehensive feature inventory
- **technical_deep_dive.md** - Performance analysis and measurements
- **callback_architecture_plan.md** - Initial callback approach (encountered GIL issues)
- **queue_based_implementation_plan.md** - Queue-based solution design
- **queue_implementation_summary.md** - Final implementation results and metrics

#### Migration Guides
- **migrations/v0.3.0-audiodata.md** - AudioData class introduction
- **migrations/v0.4.0-queue-architecture.md** - Queue-based architecture migration

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