# Proposal #003: インポート構造とAPI設計のリファクタリング

**ステータス**: 提案中
**関連Issue**: [#3](https://github.com/Mega-Gorilla/PyWAC/issues/3)
**作成日**: 2024-12-26
**対象バージョン**: v0.5.0（Phase 1）, v1.0.0（Phase 2）

---

## 概要

PyWACのインポート構造とAPI設計を改善し、技術的負債を解消する。エンドユーザー向けAPIは維持しつつ、内部構造を簡素化する。

---

## 背景

### 現状の問題

PyWACは機能的には良好に動作するが、内部構造にいくつかの技術的負債がある：

1. ネイティブモジュールの命名が不整合
2. 不要なフォールバックコードが残存
3. グローバルシングルトンがスレッドセーフでない
4. 非推奨関数に警告がない
5. 用語（process/app/session）が混在

### 影響を受けるファイル

```
pywac/
├── __init__.py           # sys.path操作
├── _native/
│   └── __init__.py       # 複雑なフォールバック
├── api.py                # グローバルシングルトン、非推奨関数
├── unified_recording.py  # process_loopback_queue インポート
└── setup.py              # モジュール命名
```

---

## 提案する変更

### Phase 1: 内部改善（v0.5.0）

#### 1.1 ネイティブモジュール名の統一

**現状**:
```python
# setup.py
Pybind11Extension("pywac._pywac_native", ...)      # 名前空間内
Pybind11Extension("process_loopback_queue", ...)   # トップレベル（問題）
```

**変更後**:
```python
# setup.py
Pybind11Extension("pywac._pywac_native", ...)
Pybind11Extension("pywac._process_loopback", ...)  # 名前空間内に移動
```

**移行戦略**:
- 新しいモジュール名でビルド
- `api.py`, `unified_recording.py` のインポート文を更新
- 古い`process_loopback_queue`は非推奨として一時的に維持（v1.0.0で削除）

#### 1.2 `_native/__init__.py` の簡素化

**現状** (52行):
```python
try:
    from .. import _pywac_native as _pypac_module
except:
    try:
        from . import pypac as _pypac_module  # 存在しない
    except:
        try:
            import pypac as _pypac_module  # 存在しない
        except:
            # dist/ から探す...
```

**変更後** (約15行):
```python
"""Native extension wrapper for PyWAC."""

try:
    from .. import _pywac_native
    SessionEnumerator = _pywac_native.SessionEnumerator
    SimpleLoopback = _pywac_native.SimpleLoopback
except ImportError as e:
    raise ImportError(
        "Failed to load PyWAC native extension. "
        "Please build with: python setup.py build_ext --inplace"
    ) from e

__all__ = ['SessionEnumerator', 'SimpleLoopback']
```

#### 1.3 グローバルシングルトンの改善

**現状**:
```python
_global_session_manager = None

def _get_session_manager():
    global _global_session_manager
    if _global_session_manager is None:
        _global_session_manager = SessionManager()
    return _global_session_manager
```

**変更後**:
```python
import threading

_lock = threading.Lock()
_global_session_manager = None

def _get_session_manager() -> SessionManager:
    """Get or create thread-safe global SessionManager instance."""
    global _global_session_manager
    if _global_session_manager is None:
        with _lock:
            if _global_session_manager is None:  # Double-check locking
                _global_session_manager = SessionManager()
    return _global_session_manager

def refresh_sessions() -> None:
    """Refresh the global session manager (re-enumerate sessions)."""
    global _global_session_manager
    with _lock:
        _global_session_manager = SessionManager()
```

#### 1.4 非推奨関数への警告追加

**変更後**:
```python
import warnings

def find_app(app_name: str) -> Optional[Dict[str, Any]]:
    """
    Deprecated: Use find_audio_session() instead.

    Find an application by name and return its audio session info.
    """
    warnings.warn(
        "find_app() is deprecated, use find_audio_session() instead",
        DeprecationWarning,
        stacklevel=2
    )
    return find_audio_session(app_name)

def get_active_apps() -> List[str]:
    """
    Deprecated: Use get_active_sessions() instead.

    Get list of applications currently playing audio.
    """
    warnings.warn(
        "get_active_apps() is deprecated, use get_active_sessions() instead",
        DeprecationWarning,
        stacklevel=2
    )
    return get_active_sessions()
```

#### 1.5 `__init__.py` の `sys.path` 操作削除

**現状**:
```python
_native_path = os.path.join(os.path.dirname(__file__), '_native')
if os.path.exists(_native_path):
    sys.path.insert(0, _native_path)
```

**変更後**: 削除（1.2の簡素化により不要になる）

---

### Phase 2: API統一（v1.0.0）

#### 2.1 用語の統一

「session」に統一を推奨：

| 現在の関数 | 新しい関数 | 非推奨 |
|-----------|-----------|--------|
| `record_process()` | `record_session()` | v1.0.0で削除 |
| `record_process_id()` | `record_session_by_pid()` | v1.0.0で削除 |
| `set_app_volume()` | `set_session_volume()` | v2.0.0で削除 |
| `get_app_volume()` | `get_session_volume()` | v2.0.0で削除 |
| `mute_app()` | `mute_session()` | v2.0.0で削除 |
| `unmute_app()` | `unmute_session()` | v2.0.0で削除 |

**注**: Phase 2は破壊的変更を含むため、十分な移行期間を設ける。

#### 2.2 非推奨関数の削除

v1.0.0で削除：
- `find_app()` → `find_audio_session()`
- `get_active_apps()` → `get_active_sessions()`

---

## 実装計画

### Phase 1 タスク一覧

| # | タスク | ファイル | 破壊的変更 |
|---|--------|----------|-----------|
| 1 | `process_loopback_queue` を `pywac._process_loopback` にリネーム | `setup.py` | なし |
| 2 | インポート文を更新 | `api.py`, `unified_recording.py` | なし |
| 3 | `_native/__init__.py` を簡素化 | `pywac/_native/__init__.py` | なし |
| 4 | グローバルシングルトンをスレッドセーフ化 | `api.py` | なし |
| 5 | `refresh_sessions()` 関数を追加 | `api.py`, `__init__.py` | なし |
| 6 | 非推奨警告を追加 | `api.py` | なし |
| 7 | `sys.path` 操作を削除 | `pywac/__init__.py` | なし |
| 8 | テストを追加・更新 | `tests/` | なし |
| 9 | ドキュメントを更新 | `docs/` | なし |

### テスト計画

```python
# tests/test_import_structure.py

def test_import_pywac():
    """Test that pywac can be imported cleanly."""
    import pywac
    assert hasattr(pywac, 'record_to_file')
    assert hasattr(pywac, 'SessionManager')

def test_native_module_import():
    """Test that native modules are in correct namespace."""
    from pywac import _pywac_native
    from pywac import _process_loopback
    assert hasattr(_pywac_native, 'SessionEnumerator')
    assert hasattr(_process_loopback, 'QueueBasedProcessCapture')

def test_deprecated_function_warning():
    """Test that deprecated functions emit warnings."""
    import warnings
    import pywac

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        pywac.find_app("test")
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)

def test_thread_safety():
    """Test that global singletons are thread-safe."""
    import threading
    import pywac

    results = []
    def get_manager():
        results.append(id(pywac._get_session_manager()))

    threads = [threading.Thread(target=get_manager) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # All threads should get the same instance
    assert len(set(results)) == 1
```

---

## 互換性

### 後方互換性

Phase 1は完全に後方互換：
- すべての公開APIは変更なし
- 既存のコードは修正不要で動作
- 非推奨警告は `DeprecationWarning`（デフォルトで非表示）

### 前方互換性

Phase 2への移行を容易にするため：
- 非推奨関数には警告を追加
- 新しい関数名を先行して導入（エイリアスとして）
- 移行ガイドを提供

---

## リスク評価

| リスク | 影響度 | 発生確率 | 対策 |
|--------|--------|----------|------|
| ビルド失敗 | 高 | 低 | CI/CDでテスト |
| インポートエラー | 高 | 低 | 段階的移行、フォールバック |
| パフォーマンス低下 | 中 | 低 | ベンチマーク |
| ドキュメント不整合 | 低 | 中 | レビュープロセス |

---

## タイムライン

```
Phase 1 (v0.5.0)
├── 実装
├── テスト
├── ドキュメント更新
└── リリース

Phase 2 (v1.0.0)
├── 新API導入（エイリアス）
├── 移行期間
├── 非推奨関数削除
└── リリース
```

---

## 参考資料

- [Issue #3: インポート構造とAPI設計の改善](https://github.com/Mega-Gorilla/PyWAC/issues/3)
- [Python Packaging User Guide](https://packaging.python.org/)
- [PEP 387 - Backwards Compatibility Policy](https://peps.python.org/pep-0387/)
- [Semantic Versioning 2.0.0](https://semver.org/)
