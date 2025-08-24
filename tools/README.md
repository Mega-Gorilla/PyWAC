# PyPAC Developer Tools

このディレクトリには、PyPACの開発・デバッグ用ツールが含まれています。

## 🔧 ツール一覧

| ツール | 説明 | 用途 |
|--------|------|------|
| `pypac_check.py` | 包括的な環境診断ツール | モジュールが動作しない場合の原因調査 |
| `check_dll.py` | DLL依存関係チェッカー | DLLロードエラーの診断 |
| `test_pypac.py` | シンプルな動作確認スクリプト | モジュールの基本的な動作確認 |
| `debug_processes.py` | プロセス名検出デバッガー | プロセス名が正しく取得できない場合の調査 |

## 📋 使用方法

### 環境診断を実行
```powershell
python tools/pypac_check.py
```
このツールは以下をチェックします：
- Python環境（バージョン、アーキテクチャ）
- 必要な依存関係（pybind11、numpy）
- Visual C++ Redistributable
- モジュールファイルの存在
- インポートテスト

### DLL問題の調査
```powershell
python tools/check_dll.py
```
DLLロードエラーが発生した場合に使用します。

### プロセス名の問題を調査
```powershell
# psutilをインストール（オプション）
pip install psutil

# デバッグツールを実行
python tools/debug_processes.py
```
プロセス名が"Unknown"と表示される場合の原因を特定します。

## 🐛 一般的な問題と解決方法

### ImportError: DLL load failed
1. `pypac_check.py`を実行して環境を確認
2. Visual C++ Redistributableをインストール
3. Python 64ビット版を使用していることを確認

### プロセス名がUnknownと表示される
1. `debug_processes.py`を実行して詳細を確認
2. 管理者権限で実行してみる
3. C++コードの`GetProcessName`関数を確認

## 📝 開発者向けメモ

これらのツールは主に以下の場面で使用されます：
- 新しい環境でのセットアップ時
- ユーザーから問題報告があった際の調査
- PyPACの新機能開発時のデバッグ
- CI/CD環境での動作確認

## ⚠️ 注意事項

- これらのツールは開発・デバッグ目的のみ
- エンドユーザーには通常必要ありません
- `debug_processes.py`はpsutilを使用する場合、追加インストールが必要