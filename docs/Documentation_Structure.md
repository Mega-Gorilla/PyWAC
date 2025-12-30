# PyWAC ドキュメント構造

## 📁 ドキュメント構成

```
pywac/
├── ルートドキュメント
│   ├── README.md              # プロジェクト概要（日本語）
│   ├── README.en.md           # プロジェクト概要（英語）
│   ├── CHANGELOG.md           # バージョン履歴
│   ├── RELEASE_NOTES.md       # 現在のリリース詳細
│   ├── VERSION               # バージョン番号
│   ├── CLAUDE.md             # AIアシスタント指示
│   └── THIRDPARTY.md         # サードパーティライセンス
│
├── docs/                     # 技術ドキュメント
│   ├── README_ja.md          # ドキュメントインデックス（日本語）
│   ├── API_REFERENCE.md      # APIドキュメント
│   ├── API_CLARIFICATION.md  # API設計の補足説明
│   ├── Documentation_Structure.md    # このファイル
│   ├── Version_Management_Strategy.md  # バージョン戦略
│   ├── v0.4.1_implementation_summary.md  # イベント駆動実装サマリー
│   ├── v0.4.2_unified_recording.md   # 統一録音API実装
│   │
│   ├── architecture/         # アーキテクチャ設計
│   │   └── (将来のアーキテクチャドキュメント)
│   │
│   ├── proposals/            # 改善・リファクタリング提案
│   │   └── 003-import-structure-refactoring.md  # インポート構造改善
│   │
│   ├── research/             # 技術調査・分析
│   │   ├── Process_Loopback_API_Research.md  # Windows API調査
│   │   └── recording_api_analysis.md         # 録音API分析
│   │
│   └── migrations/           # 移行ガイド
│       ├── v0.3.0-audiodata.md
│       ├── v0.4.0-queue-architecture.md
│       └── v0.4.1-event-driven.md
│
├── examples/                 # 使用例
│   ├── basic_usage.py
│   ├── gradio_demo.py
│   ├── quick_test.py
│   └── test_audiodata.py
│
└── tests/                    # テストファイル
    ├── test_audio_data.py
    └── test_examples.py
```

## 📝 ドキュメントの目的

### ルートレベル
- **README.md/README.en.md** - ユーザー向けプロジェクトドキュメント
- **CHANGELOG.md** - すべてのユーザー向け変更を追跡
- **RELEASE_NOTES.md** - 現在のバージョンの詳細ノート
- **VERSION** - バージョン番号の唯一の情報源
- **CLAUDE.md** - AIアシスタント用の指示
- **THIRDPARTY.md** - 依存関係のライセンス情報

### docs/ ディレクトリ
- **README_ja.md** - ドキュメントハブとナビゲーション
- **API_REFERENCE.md** - 完全なAPIドキュメント
- **API_CLARIFICATION.md** - API設計の補足説明
- **Documentation_Structure.md** - このファイル、ドキュメント構成の説明
- **Version_Management_Strategy.md** - バージョンとリリースの管理方法

### docs/architecture/
- アーキテクチャ設計ドキュメント
- システム構成図、設計判断の記録

### docs/proposals/
- 改善・リファクタリング提案
- 番号付きでトラッキング（例: `003-import-structure-refactoring.md`）
- 関連Issueへのリンクを含む

### docs/research/
- **Process_Loopback_API_Research.md** - Windows APIの技術的深掘り
- **recording_api_analysis.md** - 録音API分析
- 技術調査・分析結果

### docs/migrations/
- バージョン固有の移行ガイド

## 🎯 ドキュメントガイドライン

### いつドキュメントを作成するか
- **新機能**: API_REFERENCE.mdを更新し、例を追加
- **破壊的変更**: docs/migrations/に移行ガイドを作成
- **バグ修正**: CHANGELOG.mdを更新
- **技術調査**: docs/research/に追加
- **リファクタリング提案**: docs/proposals/に提案書を作成（Issue連携）
- **アーキテクチャ決定**: docs/architecture/に記録

### いつドキュメントを作成しないか
- 内部リファクタリング（APIに影響しない限り）
- 一時的な修正や回避策
- ユーザー向けでない実験的機能

## 🔄 更新プロセス

1. **開発中**
   - CHANGELOG.md（未リリースセクション）を更新
   - 必要に応じて例を追加/更新
   - 新機能のAPIリファレンスを更新

2. **リリース前**
   - CHANGELOG.mdの未リリースをバージョンセクションに移動
   - RELEASE_NOTES.mdを更新
   - 破壊的変更がある場合は移行ガイドを作成
   - VERSIONファイルを更新

3. **リリース後**
   - gitでタグ付け
   - GitHubリリースを作成
   - 必要に応じて古いリリースノートをアーカイブ

## ✅ ドキュメントチェックリスト

各変更について確認：
- [ ] ユーザーに影響するか？ → CHANGELOG.mdを更新
- [ ] 新しいAPIか？ → API_リファレンス.mdを更新
- [ ] 破壊的変更か？ → 移行ガイドを作成
- [ ] 例が必要か？ → examples/に追加
- [ ] ユーザーはテスト方法を知るべきか？ → テストを追加

## 🚫 ドキュメント化しないもの

- ユーザーが必要としない実装詳細
- 内部クラス構造（パブリックAPIでない限り）
- 一時的な回避策
- デバッグコードやログ
- パフォーマンス最適化（ユーザーに見えない限り）

## 📌 主要原則

1. **ユーザー重視**: ドキュメントは開発者ではなくユーザーのため
2. **実行可能**: 例と移行手順を含める
3. **バージョン管理**: ドキュメントをコードと同期させる
4. **発見可能**: 明確な構造と相互参照
5. **保守可能**: 古いドキュメントを削除、蓄積させない