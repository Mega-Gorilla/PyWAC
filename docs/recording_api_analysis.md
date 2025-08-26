# PyWAC録音API統合可能性分析

## 現在の実装状況

### 1. システム録音 (`record_audio`)
```python
def record_audio(duration: float) -> AudioData
```
- **対象**: システム全体の音声
- **実行方式**: 同期（ブロッキング）
- **戻り値**: AudioDataオブジェクト
- **実装**: 
  - PID=0でprocess_loopback_queueを使用
  - 失敗時はnative recorderにフォールバック

### 2. プロセス録音 (`record_process/record_process_id`)
```python
def record_process(process_name: str, filename: str, duration: float) -> bool
def record_process_id(pid: int, filename: str, duration: float) -> bool
```
- **対象**: 特定プロセスの音声
- **実行方式**: 同期（ブロッキング）
- **戻り値**: bool（成功/失敗）
- **実装**: 
  - process_loopback_queueモジュール使用
  - ファイルに直接保存

### 3. コールバック録音 (`record_with_callback`)
```python
def record_with_callback(duration: float, callback) -> None
```
- **対象**: システム全体の音声
- **実行方式**: 非同期（ノンブロッキング）
- **戻り値**: なし（コールバックでAudioDataを受け取る）
- **実装**: 
  - AsyncAudioRecorderを使用
  - 別スレッドで`record_audio`を実行
  - 完了時にコールバック呼び出し

## 重複と問題点

### 発見された重複

1. **システム録音とコールバック録音の重複**
   - 両方ともシステム全体の音声を録音
   - 違いは同期/非同期の実行方式のみ
   - コールバック録音は内部で`record_audio`を呼んでいるだけ

2. **PID=0の扱いの不一致**
   - `record_process_id(0, ...)` はシステム録音として動作
   - しかし別のAPIとして分離されている

3. **戻り値の不一致**
   - システム録音: AudioDataを返す
   - プロセス録音: boolを返す（ファイルに保存）
   - この違いは必然的ではない

## 統合提案

### 提案1: 統一録音API
```python
def record(
    duration: float,
    process: Optional[Union[str, int]] = None,  # None=システム全体、str=プロセス名、int=PID
    filename: Optional[str] = None,              # 指定時はファイルに保存
    callback: Optional[Callable] = None,         # 指定時は非同期実行
) -> Union[AudioData, bool, None]:
    """
    統一された録音インターフェース
    
    Args:
        duration: 録音時間（秒）
        process: None（システム全体）、プロセス名、またはPID
        filename: 保存先ファイル名（省略時はAudioDataを返す）
        callback: コールバック関数（指定時は非同期実行）
    
    Returns:
        - callback指定時: None（コールバックでAudioDataを受け取る）
        - filename指定時: bool（成功/失敗）
        - それ以外: AudioData
    """
```

### 提案2: 2つのAPIに簡素化
```python
# 同期録音API（システム/プロセス両対応）
def record(
    duration: float,
    process: Optional[Union[str, int]] = None,
    filename: Optional[str] = None
) -> Union[AudioData, bool]:
    """同期録音（システム全体またはプロセス指定）"""
    
# 非同期録音API（システム/プロセス両対応）
def record_async(
    duration: float,
    callback: Callable,
    process: Optional[Union[str, int]] = None
) -> None:
    """非同期録音（コールバック付き）"""
```

### 提案3: クラスベースの統一インターフェース
```python
class UnifiedRecorder:
    def __init__(self, process: Optional[Union[str, int]] = None):
        """
        Args:
            process: None（システム全体）、プロセス名、またはPID
        """
        self.process = process
    
    def record(self, duration: float) -> AudioData:
        """同期録音"""
        
    def record_to_file(self, duration: float, filename: str) -> bool:
        """ファイルに直接録音"""
        
    def record_async(self, duration: float, callback: Callable) -> None:
        """非同期録音"""
```

## 推奨事項

### 短期的改善（後方互換性維持）

1. **内部実装の統一**
   - すべての録音メソッドが同じ基底実装を使用するよう統一
   - 現在の`record_with_callback`のように、他のメソッドも基底メソッドのラッパーにする

2. **新しい統一APIの追加**
   ```python
   # 既存APIは維持しつつ、新しい統一APIを追加
   def record_universal(duration, process=None, filename=None, callback=None):
       # 統一実装
   ```

### 長期的改善（メジャーバージョンアップ時）

1. **APIの簡素化**
   - 提案2の2つのAPI（同期/非同期）に整理
   - プロセス指定は両方でオプションパラメータとして対応

2. **一貫性のある戻り値**
   - すべての同期メソッドがAudioDataを返す
   - ファイル保存は`audio_data.save()`で統一

## 結論

**はい、統合すべきです。** 現在の3つの録音モードは以下の理由で統合可能です：

1. **システム録音とコールバック録音の違いは同期/非同期のみ**
   - これは単一のパラメータで制御可能

2. **プロセス録音もPID=0でシステム録音になる**
   - プロセス指定はオプションパラメータで対応可能

3. **実装の重複が多い**
   - 基底実装を共有することでコード削減可能

### 最小限の変更で最大の効果

```python
# 即座に実装可能な改善
def record_audio(duration: float, process_id: int = 0, async_callback: Optional[Callable] = None) -> Optional[AudioData]:
    """
    統合された録音関数
    
    Args:
        duration: 録音時間
        process_id: 0=システム全体、その他=特定プロセス
        async_callback: 指定時は非同期実行
    """
    if async_callback:
        # 非同期実行
        thread = threading.Thread(
            target=lambda: async_callback(_record_core(duration, process_id))
        )
        thread.start()
        return None
    else:
        # 同期実行
        return _record_core(duration, process_id)
```

これにより、コードの重複を削減し、APIの一貫性を向上させることができます。