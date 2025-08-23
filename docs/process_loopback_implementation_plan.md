# Process Loopback 実装プラン

## 現在の問題

### 問題1: デバイスレベルでしか音声を取得できない
**現状**: PyAudioWPatch/sounddeviceは「スピーカー全体」の音声しか取得できない
```
Discord + Chrome + Game → [全部混ざる] → LiveCap
```

**影響**: 
- Discordの通話音声がゲーム文字起こしに混入
- システム通知音が文字起こしを妨害
- 複数アプリの音声が分離不可能

### 問題2: Pythonで Process Loopback API を直接呼べない
**現状**: Windows の `AUDIOCLIENT_PROCESS_LOOPBACK_PARAMS` は COM インターフェース
- ctypes では非同期コールバック実装が困難
- 既存のPythonライブラリは存在しない

## 解決アプローチ

### 必要な技術: Windows Process Loopback API
```cpp
// プロセス単位で音声を取得
AUDIOCLIENT_PROCESS_LOOPBACK_PARAMS params;
params.TargetProcessId = chrome_pid;  // Chromeの音声のみ
ActivateAudioInterfaceAsync(...);
```

### 実装方法: C++拡張モジュール (pybind11)

#### なぜC++拡張？
- Windows COM API の直接呼び出しが必要
- 非同期コールバック処理が必須
- リアルタイムオーディオ処理に必要な低レイテンシ

## 開発すべきもの

### 1. C++ コアライブラリ
```cpp
class ProcessLoopbackCapture {
    // 必須機能
    bool StartCapture(DWORD processId);
    vector<float> GetAudioBuffer();
    void StopCapture();
    
    // プロセス管理
    static vector<ProcessInfo> GetAudioProcesses();
};
```

### 2. Python バインディング
```python
# 最終的なPython API
import process_loopback

# プロセス選択
processes = process_loopback.list_audio_processes()
# → [{'pid': 1234, 'name': 'Chrome.exe'}, ...]

# 音声取得
capture = process_loopback.ProcessCapture()
capture.start(pid=1234)
audio_data = capture.get_buffer()  # numpy array
capture.stop()
```

### 3. LiveCap 統合
```python
# src/audio/process_capture.py
class ProcessAudioSource(AudioSource):
    def __init__(self, process_id):
        self.capture = ProcessCapture()
        self.capture.start(process_id)
    
    def read(self):
        return self.capture.get_buffer()
```

## 達成すべき技術要件

### 必須要件
1. **プロセス単位の音声取得**
   - 指定したプロセスIDの音声のみを取得
   - 他のプロセスの音声は混入しない

2. **リアルタイム処理**
   - レイテンシ < 50ms
   - バッファオーバーフローなし

3. **Python インターフェース**
   - NumPy配列として音声データを取得
   - LiveCapの既存パイプラインと統合可能

### 技術的制約
- Windows 10 2004 以降が必須
- 44.1kHz / 16bit / ステレオ 固定（GetMixFormat未実装のため）
- COM STAスレッドでの実行が必要

## 実装ステップ

### Step 1: Windows SDK サンプル動作確認
```bash
# Microsoft サンプルをビルド
git clone https://github.com/microsoft/windows-classic-samples
cd Samples/ApplicationLoopback
# Visual Studio でビルド → 動作確認
```

### Step 2: 最小限のC++実装
```cpp
// minimal_capture.cpp
class MinimalCapture {
    IAudioClient* audioClient;
    IAudioCaptureClient* captureClient;
    
    void StartCapture(DWORD pid) {
        // ActivateAudioInterfaceAsync 呼び出し
        // コールバックで IAudioClient 取得
        // 44.1kHz固定で初期化
    }
};
```

### Step 3: pybind11 バインディング
```cpp
PYBIND11_MODULE(process_loopback, m) {
    py::class_<MinimalCapture>(m, "Capture")
        .def("start", &MinimalCapture::StartCapture)
        .def("get_buffer", [](MinimalCapture& self) {
            return py::array_t<float>(...);
        });
}
```

### Step 4: Python ラッパー
```python
# process_loopback.py
import process_loopback_native

class ProcessCapture:
    def __init__(self):
        self._native = process_loopback_native.Capture()
    
    def start(self, pid):
        self._native.start(pid)
    
    def get_buffer(self):
        return self._native.get_buffer()
```

### Step 5: LiveCap 統合
- GUI にプロセス選択ドロップダウン追加
- audio_source を process_capture に切り替え可能に
- 既存のVAD/転写パイプラインはそのまま使用

## 検証項目

### 動作確認
- [ ] Chrome の音声のみ取得できる
- [ ] Discord を除外できる
- [ ] プロセス終了時にエラーにならない

### パフォーマンス
- [ ] CPU使用率 < 5%
- [ ] メモリ使用量 < 50MB
- [ ] レイテンシ < 50ms

### 統合テスト
- [ ] LiveCap での文字起こし動作
- [ ] GUI からのプロセス選択
- [ ] 長時間動作の安定性

## 既知の課題と回避策

| 課題 | 回避策 |
|------|--------|
| GetMixFormat() が E_NOTIMPL | 44.1kHz/16bit/ステレオ固定 |
| IActivateAudioInterfaceAsyncOperation のリーク | 確実に Release() |
| プロセス終了時のクラッシュ | try-catch とエラーチェック |

## 代替案（開発不要な場合）

### 現状維持: VB-Audio Virtual Cable
- メリット: 開発不要、安定動作
- デメリット: ユーザー設定が複雑、全音声が混ざる

### 簡易版: ApplicationLoopback.exe をラップ
```python
subprocess.run(['ApplicationLoopback.exe', pid, 'output.wav'])
# → リアルタイム性なし、ファイル経由
```

## まとめ

**解決すべき核心的問題**: プロセス単位の音声分離ができない

**解決方法**: Windows Process Loopback API を C++拡張で実装

**最終成果物**: `process_loopback` Pythonモジュール

**達成基準**: 特定プロセスの音声のみをリアルタイムで取得可能