# EvE CLI - クイックスタート

**バージョン**: v2.6.0（開発中）  
**最終更新**: 2026-03-16

---

## インストール

### 要件
- Python 3.8+
- Ollama（ローカル LLM）
- Git

### インストール手順

```bash
# 1. リポジトリクローン
git clone https://github.com/NPO-Everyone-Engineer/eve-cli.git
cd eve-cli

# 2. Ollama インストール（macOS）
brew install ollama

# 3. モデルダウンロード
ollama pull qwen2.5-coder:7b

# 4. 実行
python3 eve-coder.py --help
```

---

## 基本使用法

### 1. 対話モード

```bash
# 対話モード起動
python3 eve-coder.py

# スラッシュコマンド一覧
/help
```

### 2. ワンショットモード

```bash
# 単発プロンプト
python3 eve-coder.py -p "ファイルを作成して"

# モデル指定
python3 eve-coder.py -m qwen2.5-coder:7b -p "コードを書く"
```

### 3. ループモード

```bash
# ループモード（完了文字列で終了）
python3 eve-coder.py --loop "DONE"
```

---

## スラッシュコマンド

### セッション管理

| コマンド | 説明 |
|----------|------|
| `/session` | セッション保存 |
| `/fork` | セッションフォーク |
| `/compact` | メッセージ圧縮 |
| `/clear` | 画面クリア |

### モデル管理

| コマンド | 説明 |
|----------|------|
| `/model` | モデル表示 |
| `/models` | モデル一覧 |
| `/status` | ステータス表示 |

### Git 連携

| コマンド | 説明 |
|----------|------|
| `/git` | Git コマンド |
| `/pr` | プルリクエスト |
| `/checkpoint` | チェックポイント保存 |
| `/rollback` | ロールバック |

### 開発ツール

| コマンド | 説明 |
|----------|------|
| `/gentest` | テスト生成 |
| `/review` | コードレビュー |
| `/test` | テスト実行 |
| `/debug` | デバッグモード |

### その他

| コマンド | 説明 |
|----------|------|
| `/help` | ヘルプ表示 |
| `/tokens` | トークン数表示 |
| `/memory` | 記憶管理 |
| `/learn` | 学習モード |

---

## ツール一覧

### 19 Tool クラス

| Tool | 説明 |
|------|------|
| **BashTool** | コマンド実行 |
| **ReadTool** | ファイル読込 |
| **WriteTool** | ファイル書き込み |
| **EditTool** | ファイル編集 |
| **MultiEditTool** | 複数ファイル編集 |
| **GlobTool** | ファイル検索 |
| **GrepTool** | テキスト検索 |
| **WebFetchTool** | Web ページ取得 |
| **WebSearchTool** | Web 検索 |
| **NotebookEditTool** | Jupyter 編集 |
| **TaskCreateTool** | タスク作成 |
| **TaskListTool** | タスク一覧 |
| **TaskGetTool** | タスク取得 |
| **TaskUpdateTool** | タスク更新 |
| **AskUserQuestionTool** | ユーザー質問 |
| **AskUserQuestionBatchTool** | バッチ質問 |
| **SubAgentTool** | サブエージェント |
| **MCPTool** | MCP 呼び出し |
| **ParallelAgentTool** | 並列エージェント |

---

## 設定オプション

### コマンドライン

| オプション | 説明 | デフォルト |
|------------|------|------------|
| `-m, --model` | Ollama モデル | qwen2.5-coder:7b |
| `-p, --prompt` | ワンショットプロンプト | - |
| `--max-agent-steps` | 最大 AI ステップ | 100 |
| `--max-loop-hours` | 最大ループ時間 | 24 |
| `--timeout` | タイムアウト（秒） | 300 |
| `--rag` | RAG モード | false |
| `--verbose` | 詳細出力 | false |
| `--quiet` | 最小出力 | false |
| `--debug` | デバッグモード | false |

---

## 日本語 UX

### エラーメッセージ

すべて日本語化済み：
```
エラー：--max-agent-steps は 1 以上である必要があります
エラー：パス '{path}' が存在しません
エラー：モデル '{model}' が見つかりません
```

### 警告メッセージ

```
警告：OLLAMA_HOST '{hostname}' は localhost ではありません
警告：ファイル {fname} の読み込みに失敗しました
```

### ヘルプメッセージ

```
EvE CLI — Everyone.Engineer コーディングエージェント
使用方法：python3 eve-coder.py [オプション]
```

---

## テスト

### テスト実行

```bash
# 日本語 UX テスト
python3 test_ja.py

# セキュリティテスト
python3 test_security.py

# TUI テスト
python3 test_tui.py

# Tool テスト
python3 test_tools.py

# パフォーマンステスト
python3 test_performance.py

# 回帰テスト
python3 test_regression.py
```

### テスト進捗

- **日本語 UX**: 53 件 ✅
- **セキュリティ**: 100 件 ✅
- **TUI**: 25 件 ✅
- **実質統合**: 25 件 ✅
- **Tool**: 15 件 ✅
- **パフォーマンス**: 100 件 ✅
- **回帰**: 147 件 ✅
- **合計**: 465/800 件（58%）

---

## トラブルシューティング

### よくあるエラー

#### モデルが見つからない

```bash
# モデルダウンロード
ollama pull qwen2.5-coder:7b
```

#### パーミッションエラー

```bash
# 実行権限付与
chmod +x eve-coder.py
```

#### Ollama 接続エラー

```bash
# Ollama 起動
ollama serve
```

---

## 貢献ガイド

### 開発フロー

1. フォーク
2. ブランチ作成
3. 機能実装
4. テスト作成
5. テスト実行
6. プルリクエスト

### テスト義務化

- 全てのコード変更時にテスト実行
- テストなしでコミットしない
- 既存テストが全て PASS することを確認

---

## 連絡先

- **GitHub**: https://github.com/NPO-Everyone-Engineer/eve-cli
- **Everyone.Engineer**: https://www.everyone.engineer/
- **Discord**: #一般 チャンネル

---

**ドキュメントは更新中です。最新情報は Issue を確認ください。**
