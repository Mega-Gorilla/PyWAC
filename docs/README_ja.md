# PyWAC ドキュメント

PyWACドキュメントディレクトリへようこそ。このフォルダには、すべての技術ドキュメント、移行ガイド、およびアーキテクチャ情報が含まれています。

## 📚 ドキュメント構造

### コアドキュメント
- [`API_Reference.md`](./API_Reference.md) - 完全なAPIリファレンス（v0.4.1対応）
- [`Process_Loopback_API_Research.md`](./Process_Loopback_API_Research.md) - Windows Process Loopback API調査
- [`v0.4.1_implementation_summary.md`](./v0.4.1_implementation_summary.md) - **最新** イベント駆動実装サマリー

### 移行ガイド
- [`migrations/`](./migrations/) - バージョン固有の移行ガイド
  - [`v0.4.1-event-driven.md`](./migrations/v0.4.1-event-driven.md) - イベント駆動実装（最新）
  - [`v0.4.0-queue-architecture.md`](./migrations/v0.4.0-queue-architecture.md) - キューアーキテクチャ移行
  - [`v0.3.0-audiodata.md`](./migrations/v0.3.0-audiodata.md) - AudioDataクラス導入

### プロジェクト管理
- [`Version_Management_Strategy.md`](./Version_Management_Strategy.md) - バージョン管理戦略
- [`Documentation_Structure.md`](./Documentation_Structure.md) - ドキュメント構成

## 🔄 バージョン管理

### 現在のバージョン: 0.4.1（イベント駆動キャプチャ）

**v0.4.1の主な変更点:**
- ✅ **WASAPIイベント駆動**でCPU使用率 < 1%を実現
- ✅ SetEventHandle APIで完全なゼロポーリング
- ✅ 自動フォールバックで100%の互換性維持
- ✅ イベント効率100%（499イベント、0タイムアウト）
- ✅ Process Loopback APIとの完全な統合

**v0.4.0の改善点:**
- ✅ キューベースアーキテクチャがGIL問題を解決
- ✅ スレッドセーフキューでデータ損失ゼロ
- ✅ Spotify、Chrome等で本番対応

バージョン固有のドキュメント：
- 使用しているバージョンのgitタグを確認
- 移行ガイドは`docs/migrations/`にあります
- 破壊的変更は[`CHANGELOG.md`](../CHANGELOG.md)に記載

## 🚨 重要：アーキテクチャの変更

**v0.4.0は問題のあるポーリングとコールバックアプローチを置き換えるキューベースアーキテクチャを導入:**

```python
# 古い (v0.3.x) - 高CPU使用率
import process_loopback_v2 as loopback
capture = loopback.ProcessCapture()
# 30-100%のCPU使用率でポーリング

# 新しい (v0.4.0) - 効率的なキューベース
from pywac.queue_streaming import QueueBasedStreamingCapture
capture = QueueBasedStreamingCapture(process_id=pid)
# アダプティブポーリングで < 5%のCPU使用率
```

移行の詳細は[`migrations/v0.4.0-queue-architecture.md`](./migrations/v0.4.0-queue-architecture.md)を参照してください。

## 📝 更新ノートの場所

更新ノートとリリース情報は次のように管理されています：

1. **CHANGELOG.md**（ルート） - ユーザー向けの変更
2. **GitHubリリース** - バイナリ付きの詳細なリリースノート
3. **移行ガイド** - ステップバイステップのアップグレード手順
4. **APIドキュメント** - バージョン固有のAPI変更

## 🚀 クイックリンク

### 開始方法
- [最新APIリファレンス](./API_リファレンス.md)
- [キュー実装概要](./キューベース実装サマリー.md)

### 移行
- [v0.3.xからv0.4.0への移行](./migrations/v0.4.0-queue-architecture.md)
- [v0.2.xからv0.3.0への移行](./migrations/v0.3.0-audiodata.md)

### 技術的深掘り
- [キューアーキテクチャ設計](./queue_based_implementation_plan.md)
- [問題解決レポート](./v0.4.0_problem_resolution.md)
- [元の問題分析](./pywac_dataflow_and_issues.md)

## 📊 パフォーマンスメトリクス（v0.4.1）

イベント駆動実装の成果：
- **CPU使用率**: < 1%（v0.4.0では3-5%、v0.3.xでは30-100%）
- **レイテンシ**: 一定の~10ms
- **データ損失**: 0%（ドロップされたチャンクなし）
- **イベント効率**: 100%（完全なイベント駆動）
- **メモリ**: 有界キューで最小限のオーバーヘッド
- **スレッド安全性**: 完全なGIL準拠

Spotifyキャプチャの実例：
```
録音時間: 5.02秒
総チャンク数: 499
ドロップされたチャンク: 0
効率: 1.04 chunks/poll
CPU使用率: < 5%
```

## 📦 モジュール概要

### コアモジュール（v0.4.0）
- `process_loopback_queue` - C++キューベースキャプチャ（推奨）
- `pywac.queue_streaming` - Pythonストリーミングインターフェース
- `pywac.audio_data` - 統一オーディオデータコンテナ

### 非推奨モジュール
- `process_loopback_v2` - ポーリングベース（高CPU使用率）
- `process_loopback_v3` - コールバックベース（GIL問題）

## 🔍 情報の検索

- **パフォーマンス問題**: [`キューベース実装サマリー.md`](./キューベース実装サマリー.md)を参照
- **API変更**: [`API_リファレンス.md`](./API_リファレンス.md)を確認
- **移行ヘルプ**: [`migrations/`](./migrations/)を参照
- **使用例**: `examples/`とテストファイルを確認
- **技術詳細**: アーキテクチャドキュメントを読む

## 🐛 既知の問題と解決策

### v0.3.x以前
- ❌ 高CPU使用率（30-100%） - v0.4.0で修正
- ❌ コールバックでのGILクラッシュ - v0.4.0で修正
- ❌ ポーリングでのデータ損失 - v0.4.0で修正

### v0.4.0
- ✅ すべての主要な問題が解決済み
- ✅ 本番対応の実装
- ✅ 実際のアプリケーションでテスト済み

## 📈 バージョン履歴

- **v0.4.1** - イベント駆動実装、< 1% CPU、SetEventHandle統合
- **v0.4.0** - キューベースアーキテクチャ、< 5% CPU、GILセーフ
- **v0.3.0** - AudioDataクラス、統一フォーマット処理
- **v0.2.0** - Process Loopback API実装
- **v0.1.0** - WASAPIサポート付き初期リリース