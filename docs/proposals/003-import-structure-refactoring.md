# Proposal #003: インポート構造とAPI設計のリファクタリング

**ステータス**: 提案中
**関連Issue**: [#3](https://github.com/Mega-Gorilla/PyWAC/issues/3)
**作成日**: 2024-12-26
**更新日**: 2024-12-30
**対象バージョン**: v1.0.0（Phase 1 - 破壊的変更）, v2.0.0（Phase 2）

---

## 概要

PyWACのインポート構造とAPI設計を改善し、技術的負債を解消する。

**主な変更点:**
- ネイティブモジュールを機能ベースのシンプルな名前に変更
- `pywac._pywac_native` → `pywac.core`（公開API）
- `process_loopback_queue` → `pywac.capture`（公開API）
- アンダースコアを削除し、低レベルAPIとして正式にサポート

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
├── __init__.py           # sys.path操作、公開API定義
├── _native/              # 削除予定
│   └── __init__.py       # 複雑なフォールバック
├── api.py                # グローバルシングルトン、非推奨関数
├── sessions.py           # _native インポート
├── recorder.py           # _native インポート
├── unified_recording.py  # process_loopback_queue インポート
└── setup.py              # モジュール命名
```

### v1.0.0 後の構造

```
pywac/
├── __init__.py           # 公開API定義
├── api.py                # 高レベルAPI関数
├── sessions.py           # SessionManager（pywac.core使用）
├── recorder.py           # AudioRecorder（pywac.core使用）
├── unified_recording.py  # 統一録音（pywac.capture使用）
├── audio_data.py         # AudioDataクラス
├── utils.py              # ユーティリティ
├── core.cpython-xxx.pyd  # ネイティブ: SessionEnumerator, SimpleLoopback
└── capture.cpython-xxx.pyd # ネイティブ: QueueBasedProcessCapture
```

---

## 提案する変更

### Phase 1: 内部改善（v1.0.0 - 破壊的変更）

> **注意**: `process_loopback_queue` および `pywac._pywac_native` を直接インポートしているコードは修正が必要です。
> 詳細は[移行ガイド](#移行ガイド)を参照してください。

#### 1.1 ネイティブモジュール名の統一と公開API化

**現状の問題**:
```python
# setup.py（現在）
Pybind11Extension("pywac._pywac_native", ...)      # 冗長な命名、内部扱い
Pybind11Extension("process_loopback_queue", ...)   # 名前空間外、不整合
```

**変更後**:
```python
# setup.py（v1.0.0）
Pybind11Extension("pywac.core", ...)      # セッション列挙、システムループバック
Pybind11Extension("pywac.capture", ...)   # プロセス固有キャプチャ
```

**命名の根拠**:

| モジュール | 機能 | 含まれるクラス |
|-----------|------|---------------|
| `pywac.core` | コア機能（セッション管理、システム録音） | `SessionEnumerator`, `SimpleLoopback` |
| `pywac.capture` | プロセス固有キャプチャ | `QueueBasedProcessCapture` |

**設計方針**:
- **アンダースコアなし**: 公開APIとして正式サポート
- **機能ベース命名**: 役割が明確
- **安定性保証**: 破壊的変更時はメジャーバージョンアップ

#### 1.2 `_native/` ディレクトリの削除

**現状**: `pywac/_native/__init__.py` に複雑なフォールバックロジック（52行）

**変更後**: ディレクトリごと削除

**理由**:
- `pywac.core` が直接 `SessionEnumerator`, `SimpleLoopback` を提供
- ラッパー層が不要になる
- インポートがシンプルに

```python
# 変更前（複雑）
from pywac._native import SessionEnumerator  # ラッパー経由

# 変更後（シンプル）
from pywac.core import SessionEnumerator     # 直接アクセス
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

### Phase 2: API統一（v2.0.0）

#### 2.1 用語の統一

「session」に統一を推奨：

| 現在の関数 | 新しい関数 | 非推奨 |
|-----------|-----------|--------|
| `record_process()` | `record_session()` | v2.0.0で削除 |
| `record_process_id()` | `record_session_by_pid()` | v2.0.0で削除 |
| `set_app_volume()` | `set_session_volume()` | v2.0.0で削除 |
| `get_app_volume()` | `get_session_volume()` | v2.0.0で削除 |
| `mute_app()` | `mute_session()` | v2.0.0で削除 |
| `unmute_app()` | `unmute_session()` | v2.0.0で削除 |

**注**: Phase 2は破壊的変更を含むため、十分な移行期間を設ける。

#### 2.2 非推奨関数の削除

v2.0.0で削除：
- `find_app()` → `find_audio_session()`
- `get_active_apps()` → `get_active_sessions()`

---

## 実装計画

### Phase 1 タスク一覧

| # | タスク | ファイル | 破壊的変更 |
|---|--------|----------|-----------|
| 1 | `pywac._pywac_native` を `pywac.core` にリネーム | `setup.py` | **あり** |
| 2 | `process_loopback_queue` を `pywac.capture` にリネーム | `setup.py` | **あり** |
| 3 | `pywac/_native/` ディレクトリを削除 | `pywac/_native/` | **あり** |
| 4 | `pyproject.toml` のパッケージ設定を更新 | `pyproject.toml` | なし |
| 5 | インポート文を更新 | `api.py`, `unified_recording.py`, `sessions.py`, `recorder.py` | なし |
| 6 | グローバルシングルトンをスレッドセーフ化 | `api.py` | なし |
| 7 | `refresh_sessions()` 関数を追加 | `api.py`, `__init__.py` | なし |
| 8 | 非推奨警告を追加 | `api.py` | なし |
| 9 | `sys.path` 操作を削除 | `pywac/__init__.py` | なし |
| 10 | テストを追加・更新 | `tests/` | なし |
| 11 | ドキュメントを更新 | `docs/` | なし |
| 12 | 移行ガイドを作成 | `docs/migrations/` | なし |

### pyproject.toml の更新

```toml
[tool.setuptools]
packages = ["pywac"]  # "pywac._native" を削除

[tool.setuptools.package-data]
pywac = [
    "*.pyd",      # Windows: core.pyd, capture.pyd
    "*.so",       # Linux: core.so, capture.so
]
```

**変更点:**
- `pywac._native` をパッケージリストから削除
- `package-data` でネイティブ拡張（`.pyd`, `.so`）を含める

### テスト計画

```python
# tests/test_import_structure.py

import pytest

# ネイティブ拡張が利用可能かチェック
def _native_available():
    try:
        from pywac import core, capture
        return True
    except ImportError:
        return False

requires_native = pytest.mark.skipif(
    not _native_available(),
    reason="Native extensions not built. Run: python setup.py build_ext --inplace"
)


def test_import_pywac():
    """Test that pywac can be imported cleanly."""
    import pywac
    assert hasattr(pywac, 'record_to_file')
    assert hasattr(pywac, 'SessionManager')


@requires_native
def test_core_module_import():
    """Test that pywac.core is accessible as public API."""
    from pywac import core
    assert hasattr(core, 'SessionEnumerator')
    assert hasattr(core, 'SimpleLoopback')


@requires_native
def test_capture_module_import():
    """Test that pywac.capture is accessible as public API."""
    from pywac import capture
    assert hasattr(capture, 'QueueBasedProcessCapture')


@requires_native
def test_low_level_api_usage():
    """Test that low-level APIs work correctly."""
    from pywac.core import SessionEnumerator
    from pywac.capture import QueueBasedProcessCapture

    # セッション列挙
    enumerator = SessionEnumerator()
    sessions = enumerator.enumerate_sessions()
    assert isinstance(sessions, list)

    # キャプチャインスタンス生成
    cap = QueueBasedProcessCapture()
    assert cap is not None


@requires_native
def test_deprecated_function_warning():
    """Test that deprecated functions emit warnings."""
    import warnings
    import pywac

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        pywac.find_app("test")
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)

@requires_native
def test_thread_safety():
    """Test that global singletons are thread-safe."""
    import threading
    from pywac import api

    results = []
    def get_manager():
        results.append(id(api._get_session_manager()))

    threads = [threading.Thread(target=get_manager) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # All threads should get the same instance
    assert len(set(results)) == 1


@requires_native
def test_refresh_sessions():
    """Test that refresh_sessions() is exposed as public API."""
    import pywac
    assert hasattr(pywac, 'refresh_sessions')
    pywac.refresh_sessions()
```

**テストスキップ条件:**
- `requires_native`: ネイティブ拡張がビルドされていない場合はスキップ

> **注**: PyWACはWindows専用ライブラリのため、プラットフォーム判定は不要です。

---

## 互換性

### 破壊的変更（Phase 1）

Phase 1は以下の破壊的変更を含む：

| 変更前 | 変更後 | 影響 |
|--------|--------|------|
| `pywac._pywac_native` | `pywac.core` | 直接インポートしているコードの修正が必要 |
| `process_loopback_queue` | `pywac.capture` | 直接インポートしているコードの修正が必要 |
| `pywac/_native/` | 削除 | `pywac._native` からのインポートが動作しなくなる |

**高レベルAPI（`pywac.record_process()` など）には影響なし。**

### 後方互換性が維持される部分

- `pywac` パッケージの高レベルAPI（`record_to_file`, `record_process`, `set_app_volume` など）
- `pywac.SessionManager`, `pywac.AudioRecorder` クラス
- `pywac.AudioData` クラス

### 新しい公開API

v1.0.0で以下の低レベルAPIが公開APIとして追加：

```python
# 低レベルAPI（公開、安定性保証）
from pywac.core import SessionEnumerator, SimpleLoopback
from pywac.capture import QueueBasedProcessCapture
```

---

## 移行ガイド

### `process_loopback_queue` からの移行

**変更前（v0.4.x）:**
```python
import process_loopback_queue
capture = process_loopback_queue.QueueBasedProcessCapture()
```

**変更後（v1.0.0）:**
```python
from pywac.capture import QueueBasedProcessCapture
capture = QueueBasedProcessCapture()
```

### `pywac._pywac_native` からの移行

**変更前（v0.4.x）:**
```python
from pywac._native import SessionEnumerator
# または
from pywac import _pywac_native
enumerator = _pywac_native.SessionEnumerator()
```

**変更後（v1.0.0）:**
```python
from pywac.core import SessionEnumerator
enumerator = SessionEnumerator()
```

### 高レベルAPIの使用（推奨）

低レベルAPIが不要な場合は、高レベルAPIの使用を推奨：

```python
import pywac

# プロセス固有の録音（推奨）
pywac.record_process("spotify", "output.wav", duration=10)

# セッション一覧取得（推奨）
sessions = pywac.list_audio_sessions()
```

### 移行チェックリスト

- [ ] `import process_loopback_queue` を `from pywac.capture import ...` に変更
- [ ] `from pywac._native import ...` を `from pywac.core import ...` に変更
- [ ] `from pywac import _pywac_native` を `from pywac import core` に変更
- [ ] テストを実行して動作確認

---

## リスク評価

| リスク | 影響度 | 発生確率 | 対策 |
|--------|--------|----------|------|
| 低レベルAPI直接利用者への影響 | 高 | 低〜中 | 移行ガイド提供、リリースノートで周知 |
| ビルド失敗 | 高 | 低 | CI/CDでテスト |
| インポートエラー | 高 | 低 | 明確なエラーメッセージ |
| 公開API増加による保守負担 | 中 | 中 | ドキュメント整備、テスト拡充 |
| ドキュメント不整合 | 低 | 中 | レビュープロセス |

---

## タイムライン

```
Phase 1 (v1.0.0) - メジャーバージョンアップ
├── 破壊的変更の実装
│   ├── pywac._pywac_native → pywac.core
│   ├── process_loopback_queue → pywac.capture
│   └── pywac/_native/ ディレクトリ削除
├── 低レベルAPI公開（pywac.core, pywac.capture）
├── 内部改善（スレッドセーフ化、コード簡素化）
├── 移行ガイド作成
├── テスト
└── リリース

Phase 2 (v2.0.0)
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
