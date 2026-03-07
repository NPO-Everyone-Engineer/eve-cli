# EvE CLI — Everyone.Engineer Coding Agent

**EvE CLI** は、[NPO法人 Everyone.Engineer](https://www.everyone.engineer) が提供するオープンソースのAIコーディングエージェントです。

[ochyai/vibe-local](https://github.com/ochyai/vibe-local) をベースに、ローカルLLMに加えてOllamaクラウドモデルにも対応しています。

## 特徴

- **ローカル + クラウド**: Ollamaのローカルモデルとクラウドモデル（`qwen3.5:397b-cloud` 等）を自由に切り替え
- **自動プロファイル切替**: ネットワーク状態を検知し、オンライン/オフラインで最適なモデルを自動選択
- **ゼロ依存**: Python標準ライブラリのみ、pip install不要
- **16個の内蔵ツール**: Bash実行、ファイル操作、Web取得、サブエージェント、タスク管理など
- **MCP統合**: JSON-RPC 2.0によるツール連携
- **Plan/Actモード**: 読み取り専用 → 実行の段階的遷移
- **Gitチェックポイント**: stashベースのロールバック機能
- **シンタックスハイライト**: コードブロックのキーワード/文字列/コメント色分け（Python, JS/TS, Bash, Go, Rust）
- **カラーdiff表示**: ファイル編集時に変更箇所を赤/緑で表示
- **@file記法**: `@src/main.py` でファイル内容をメッセージに自動添付
- **Tab補完**: スラッシュコマンド、ファイルパス、@fileのTab補完
- **画像添付**: ドラッグ&ドロップ、クリップボード貼り付け、`/image` コマンド（ビジョン対応モデル必要）
- **日本語対応**: 日本語・英語・中国語に対応

## インストール

### ワンライナー（推奨）

```bash
curl -fsSL https://raw.githubusercontent.com/NPO-Everyone-Engineer/eve-cli/main/install.sh | bash
```

これだけで Python・Ollama の確認、モデルのダウンロード、`eve-cli` コマンドのセットアップが自動で行われます。

### 手動インストール

```bash
# リポジトリをクローン
git clone https://github.com/NPO-Everyone-Engineer/eve-cli.git
cd eve-cli

# 実行権限を付与
chmod +x eve-coder.py eve-cli.sh

# パスに追加
ln -s $(pwd)/eve-cli.sh /usr/local/bin/eve-cli
```

### 前提条件

- Python 3.8+
- [Ollama](https://ollama.com/) がインストール・起動済み

## 使い方

```bash
# 対話モード
eve-cli

# ワンショット
eve-cli -p "Hello Worldを作って"

# ローカルモデル指定
eve-cli --model qwen3:8b

# クラウドモデル指定（Ollama有料版）
eve-cli --model qwen3.5:397b-cloud

# 自動許可モード
eve-cli -y

# セッション再開
eve-cli --resume

# プロファイル指定
eve-cli --profile offline    # 常にオフラインモード
eve-cli --profile online     # 常にオンラインモード
eve-cli --profile cafe       # カスタムプロファイル
```

### 入力方法

- **Enter**: 改行（入力を続ける）
- **空のEnter**: メッセージ送信
- **`"""`**: 明示的なマルチラインモード（`"""`で開始・終了）
- **Tab**: ファイルパス・コマンド補完
- **@ファイル名**: ファイル内容を自動添付（例: `@src/main.py を修正して`）
- **ESC**: エージェント実行を中断
- **Ctrl+K**: ローカルモデル ↔ クラウドモデルを即時切り替え

### インタラクティブコマンド

| コマンド | 説明 |
|---------|------|
| `/help` | ヘルプ表示 |
| `/model` | モデル切り替え |
| `/plan` | Planモードに切り替え |
| `/approve` | 計画を承認して実行 |
| `/image` | クリップボードの画像を添付 |
| `/image <path>` | 画像ファイルを添付 |
| `/commit` | Git コミット作成 |
| `/diff` | 変更差分を表示 |
| `/status` | セッション・Git・checkpoint の状態を表示 |
| `/undo` | 直前のファイル変更を元に戻す |
| `/checkpoint` | 非破壊の Git checkpoint を作成 |
| `/checkpoint list` | 保存済み checkpoint 一覧を表示 |
| `/rollback` | チェックポイントに戻す |
| `/compact` | 会話を要約して圧縮 |
| `/watch` | ファイル監視モード |
| `/autotest` | 編集後に構文チェック + テストを自動実行 |
| `/index build` | リポジトリインデックスを構築 |
| `/index search <query>` | シンボルを検索 |
| `/index file <path>` | ファイルのシンボルを表示 |
| `/index status` | インデックスの状態を確認 |
| `/gentest <file.py>` | AI にテストファイルを生成させる |
| `/browser setup` | ブラウザ操作のセットアップ（Playwright MCP） |
| `/browser status` | ブラウザツールの接続状態を確認 |
| `/config` | 現在の設定を表示 |
| `/clear` | 会話クリア |
| `/exit` | 終了 |

### パーミッション

ツール実行時に確認プロンプトが表示されます（`-y` で自動許可）。

| 選択肢 | 説明 |
|--------|------|
| `y` | 今回だけ許可 |
| `a` | このツールを今後すべて許可 |
| `n` / Enter | 拒否 |
| `d` | このツールを今後すべて拒否 |
| `Y` | すべてのツールを自動許可 |

### 安全性・復旧・自動検証

- `Write` / `Edit` / `NotebookEdit` の前に、作業ツリーを汚さない checkpoint を自動作成
- `/rollback` は最新 checkpoint の状態に戻し、checkpoint 作成時点の未追跡ファイルも復元
- `/status` で dirty file 数、最近の変更、checkpoint 数、自動検証コマンドを確認可能
- `/autotest` は Python では既定で `py_compile` を実行し、`tests/` があれば `unittest` を自動検出

## 環境変数

| 変数 | 説明 |
|------|------|
| `EVE_CLI_MODEL` | デフォルトモデル名 |
| `EVE_CLI_SIDECAR_MODEL` | サイドカーモデル名 |
| `EVE_CLI_PROFILE` | 接続プロファイル (`auto`, `online`, `offline`, カスタム名) |
| `EVE_CLI_DEBUG` | デバッグモード (`1` で有効) |
| `OLLAMA_HOST` | Ollamaホスト URL |

### 設定方法

シェルの設定ファイル（`~/.zshrc` または `~/.bashrc`）に追記してください。

```bash
# デフォルトモデルを設定
export EVE_CLI_MODEL="qwen3:8b"

# クラウドモデルを使う場合
export EVE_CLI_MODEL="qwen3.5:397b-cloud"

# サイドカーモデル（サブエージェント用の軽量モデル）
export EVE_CLI_SIDECAR_MODEL="qwen3:4b"

# デバッグモードを有効化
export EVE_CLI_DEBUG=1

# Ollamaのホストを変更（デフォルト: http://localhost:11434）
export OLLAMA_HOST="http://localhost:11434"
```

設定後、ターミナルを再起動するか `source ~/.zshrc` を実行してください。

設定ファイル（`~/.config/eve-cli/config`）でも同様に設定できます。

```
MODEL=qwen3:8b
SIDECAR_MODEL=qwen3:4b
OLLAMA_HOST=http://localhost:11434
EVE_CLI_DEBUG=0

# プロファイル: auto（デフォルト）、online、offline、カスタム名
PROFILE=auto
```

### プロファイル設定

ネットワーク状態に応じたモデル自動切替が設定できます。起動時にインターネット接続を検知し、対応するプロファイルの設定を適用します。

`~/.config/eve-cli/config` にプロファイルセクションを追加:

```ini
# デフォルト: 自動検知
PROFILE=auto

# オンライン時 → クラウドモデルを使用
[profile:online]
MODEL=qwen3.5:397b-cloud
SIDECAR_MODEL=qwen3:8b

# オフライン時 → ローカルモデルにフォールバック
[profile:offline]
MODEL=qwen3:8b
SIDECAR_MODEL=qwen3:4b

# カスタムプロファイル（例: カフェのWi-Fi環境）
[profile:cafe]
MODEL=qwen3:4b
CONTEXT_WINDOW=8192
```

- `PROFILE=auto` — 起動時にネットワーク接続を自動検知し、`online` または `offline` プロファイルを選択
- `PROFILE=online` / `PROFILE=offline` — 常に固定プロファイルを使用
- `PROFILE=<カスタム名>` — 任意のプロファイルを使用
- `--model` オプションはプロファイル設定より優先されます
- フッターに `● ON` / `○ OFF` でネットワーク状態が常時表示されます

## ブラウザ操作（Playwright MCP）

eve-cli からブラウザを操作できます。Webページの表示、スクリーンショット、フォーム入力、クリックなどが可能です。

### セットアップ

```bash
# Node.js が必要（未インストールの場合）
brew install node

# eve-cli 内でセットアップ
eve-cli
> /browser setup
```

セットアップ後、eve-cli を再起動するとブラウザ操作ツールが自動で読み込まれます。

### 使用例

```
> https://example.com を開いてページの内容を教えて
> Google で "EvE CLI" を検索して最初の結果を教えて
> https://example.com のスクリーンショットを撮って
> フォームに名前を入力して送信ボタンを押して
```

### 手動設定

`~/.config/eve-cli/mcp.json` を直接編集することもできます:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}
```

## 推奨環境

| 環境 | メモリ | 推奨モデル |
|------|-------|----------|
| Apple Silicon Mac | 96GB+ | gpt-oss:120b |
| Apple Silicon Mac | 16GB | qwen3:8b |
| Intel/Windows/Linux | 16GB+ | qwen3:8b |
| クラウドモデル利用時 | 制限なし | qwen3.5:397b-cloud |

画像認識を使う場合は、ビジョン対応モデル（`llava`, `llama3.2-vision`, `gemma3` 等）が必要です。

## ライセンス

MIT License — [ochyai/vibe-local](https://github.com/ochyai/vibe-local) をベースにしています。

## クレジット

- 原作: [ochyai/vibe-local](https://github.com/ochyai/vibe-local) by Yoichi Ochiai
- フォーク・拡張: [NPO法人 Everyone.Engineer](https://www.everyone.engineer)
