# PyPAC Examples

このディレクトリには、PyPACライブラリの使用例が含まれています。

## 📂 ファイル一覧

| ファイル | 説明 | 主な機能 |
|----------|------|----------|
| `demo_audio_capture.py` | 全機能の包括的なデモ | セッション列挙、録音、音量制御 |
| `quick_test.py` | モジュールの簡単な動作確認 | インポートテスト、基本的なセッション列挙 |
| `volume_controller.py` | インタラクティブな音量コントローラー | アプリ選択、音量調整、ミュート切替 |

## 🚀 実行方法

### 仮想環境を使用する場合（推奨）
```powershell
# 仮想環境から実行
.\.venv\Scripts\python.exe examples\demo_audio_capture.py
```

### システムPythonを使用する場合
```powershell
# distフォルダにpypac.pydが必要
python examples\quick_test.py
```

## 📋 前提条件

1. **ビルド済みモジュール**: `dist/pypac.pyd`が存在すること
2. **Python 3.7+**: 64ビット版が必要
3. **Windows 10/11**: Process Audio APIのサポート
4. **Visual C++ Redistributable**: [ダウンロード](https://aka.ms/vs/17/release/vc_redist.x64.exe)

## ⚠️ トラブルシューティング

### ImportError: DLL load failed
Visual C++ Redistributableをインストールしてください。

### No audio sessions found
- アプリケーションで音声を再生してください
- 管理者権限で実行してみてください

### 診断スクリプト
問題が解決しない場合は、診断スクリプトを実行してください：
```powershell
python pypac_check.py
```