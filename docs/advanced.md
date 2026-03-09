# EvE CLI — 高度な機能

## 目次

- [メモリ（長期記憶）](#メモリ長期記憶)
- [プロジェクト設定ファイル](#プロジェクト設定ファイル)
- [プロファイル設定（自動切替）](#プロファイル設定自動切替)
- [Hooks（ライフサイクルフック）](#hooksライフサイクルフック)
- [コードインテリジェンス](#コードインテリジェンス)
- [ブラウザ操作（Playwright MCP）](#ブラウザ操作playwright-mcp)
- [Agent Teams（マルチエージェント）](#agent-teamsマルチエージェント)
- [環境変数・設定](#環境変数設定)

---

## メモリ（長期記憶）

セッション間で情報を記憶する機能です。プロジェクトの規約やユーザーの好みを覚えておくことで、毎回説明する手間が省けます。

### メモリの追加

```
> /memory add コミットメッセージは日本語で書く
> /memory add [style] インデントはスペース4つ
> /memory add [project] データベースはPostgreSQLを使用
```

`[カテゴリ]` を付けると整理しやすくなります（省略可）。

### メモリの一覧表示

```
> /memory
  [0] (general) コミットメッセージは日本語で書く
  [1] (style) インデントはスペース4つ
  [2] (project) データベースはPostgreSQLを使用
```

### メモリの検索・削除

```
> /memory search インデント    # キーワード検索
> /memory remove 1             # インデックス1のメモリを削除
> /memory clear                # すべて削除
```

### 仕組み

- メモリは `~/.config/eve-cli/memory/memory.json` に保存
- 起動時に自動でシステムプロンプトに注入されるので、AIが常に覚えています
- 最大100エントリ、各エントリ最大500文字

---

## プロジェクト設定ファイル

プロジェクトごとにAIへの指示を設定できます。チーム全体で共有する規約や、個人の好みを記述します。

### ファイルの優先順位（すべてマージされます）

| ファイル | 用途 | Git管理 |
|---------|------|---------|
| `~/.config/eve-cli/CLAUDE.md` | グローバル設定（全プロジェクト共通） | — |
| `.eve-cli/CLAUDE.md` | チーム共有設定 | する |
| `CLAUDE.md` | プロジェクトルートの設定 | する |
| `CLAUDE.local.md` | 個人設定（自分だけ） | しない（.gitignore推奨） |
| `.eve-coder.json` | 旧形式（後方互換） | する |

### 自動生成

```
> /init
```

プロジェクトの言語・フレームワーク・ビルドコマンドを自動検出し、`.eve-cli/CLAUDE.md` を生成します。

### 設定例

```markdown
# プロジェクトルール

## コーディング規約
- TypeScript を使用
- インデントはスペース2つ
- 関数名は camelCase

## テスト
- Jest を使用
- カバレッジ80%以上を維持

## コミット
- Conventional Commits 形式
- 日本語で記述
```

### 階層的マージ

親ディレクトリからカレントディレクトリまでの全階層を探索し、見つかった設定ファイルをすべてマージします。合計サイズは8KBに制限されます。

### セキュリティ

プロジェクト内の `CLAUDE.md` / `.eve-cli/CLAUDE.md` / `.eve-coder.json` などは、**初回に信頼確認が必要**です。
信頼後にファイル内容が変わった場合は再確認が必要で、状態は `~/.config/eve-cli/trusted_repos.json` に保存されます。

### コンテキスト自動収集

設定ファイルに加えて、起動時に以下の情報を自動収集してAIに提供します:

- **Gitブランチ名** と **直近5コミット**
- **ディレクトリ構造**（主要ファイル/フォルダ一覧）
- **プロジェクト種別**（package.json → Node.js、requirements.txt → Python 等を自動検出）

---

## プロファイル設定（自動切替）

ネットワーク状態に応じてモデルを自動切り替えできます。

### 設定方法

`~/.config/eve-cli/config` にプロファイルセクションを追加:

```ini
# デフォルト: ネットワーク状態を自動検知
PROFILE=auto

# オンライン時 → クラウドモデルを使用（高性能）
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

### 動作

| 設定値 | 動作 |
|--------|------|
| `PROFILE=auto` | 起動時にネットワーク接続を自動検知し、`online` または `offline` プロファイルを選択 |
| `PROFILE=online` | 常にオンラインプロファイルを使用 |
| `PROFILE=offline` | 常にオフラインプロファイルを使用 |
| `PROFILE=<カスタム名>` | 指定したプロファイルを使用 |

- `--model` / `--ollama-host` / `--max-tokens` / `--temperature` / `--context-window` はプロファイル設定より優先されます
- フッターに `● ON` / `○ OFF` でネットワーク状態が常時表示されます

---

## Hooks（ライフサイクルフック）

エージェントのライフサイクルイベントに対して、カスタムシェルコマンドを実行できます。

### 設定ファイル

- `~/.config/eve-cli/hooks.json` （グローバル — 常に信頼）
- `.eve-cli/hooks.json` （プロジェクト単位 — **初回に信頼確認が必要**）

> **セキュリティ警告**: プロジェクトレベルの `.eve-cli/hooks.json` はリポジトリに含まれるファイルです。
> 悪意あるリポジトリがフックを通じて任意のコマンドを実行する可能性があるため、
> 初回読み込み時に内容を表示して明示的な許可を求めます。
> 信頼状態は `~/.config/eve-cli/trusted_hooks.json` にリポジトリごとに保存されます。
> `hooks.json` または参照しているリポジトリ内スクリプトが変更されると信頼は無効化され、再確認が必要になります。

### セキュリティ制限

| 制限 | 内容 |
|------|------|
| **コマンドallowlist** | プロジェクトフックは `echo`, `bash`, `python3`, `node`, `grep` 等の安全なコマンドのみ実行可能 |
| **リポジトリ内スクリプト検証** | フックが参照する repo 内スクリプトもハッシュ検証対象。symlink や repo 外参照は拒否 |
| **SessionStart制限** | プロジェクトフックからの `SessionStart` イベントはデフォルトでブロック |
| **shell=False実行** | シェルインジェクション防止のため、コマンドは配列として安全に実行 |
| **タイムアウト** | フックごとに設定可能（最大30秒） |

### 設定例

```json
{
  "hooks": [
    {"event": "PreToolUse", "command": "echo 'tool check'", "timeout": 5},
    {"event": "PostToolUse", "command": "python3 scripts/log.py"},
    {"event": "Stop", "command": "echo 'done'"}
  ]
}
```

### イベント一覧

| イベント | タイミング | 用途例 |
|---------|-----------|--------|
| `SessionStart` | セッション開始時 | 環境チェック、ログ開始 |
| `PreToolUse` | ツール実行前 | カスタム承認ロジック、ログ |
| `PostToolUse` | ツール実行後 | 結果のログ、通知 |
| `Stop` | セッション終了時 | クリーンアップ |

> **PreToolUse** フックが非ゼロで終了すると、そのツール実行はブロックされます。

### 環境変数

フック実行時に以下の環境変数が設定されます:

| 変数 | 説明 |
|------|------|
| `EVE_HOOK_EVENT` | イベント名 |
| `EVE_HOOK_TOOL_NAME` | ツール名（PreToolUse/PostToolUse時） |
| `EVE_HOOK_SESSION_ID` | セッションID |
| `EVE_HOOK_CWD` | 作業ディレクトリ |

---

## コードインテリジェンス

プロジェクト内の関数・クラス・変数の定義と参照を高速検索できます。

### 対応言語

Python, JavaScript/TypeScript, Go, Rust, Ruby, Java

### 使い方

```
> /index build              # インデックスを構築（初回のみ）
> /index search "handleClick"  # 関数名を検索
> /index file src/app.py    # ファイル内のシンボル一覧
> /index status             # インデックスの状態
```

### 仕組み

- 正規表現ベースのシンボル抽出（高速・依存なし）
- `class`, `def`, `function`, `const`, `struct` 等を自動検出
- AIが自動的に `/index` を使ってコードベースを理解します

---

## ブラウザ操作（Playwright MCP）

EvE CLI からブラウザを操作できます。Webページの表示、スクリーンショット、フォーム入力、クリックなどが可能です。

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

### MCP設定

グローバル設定（`~/.config/eve-cli/mcp.json`）は常に信頼されます:

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

### プロジェクトレベルMCPのセキュリティ

プロジェクト内の `.eve-cli/mcp.json` は**初回に信頼確認が必要**です。

> **なぜ確認が必要？**
> リポジトリに含まれる `mcp.json` は、MCPサーバーとして任意のコマンドを起動できます。
> 悪意あるリポジトリがこれを悪用する可能性があるため、明示的な信頼が必要です。

| セキュリティ制限 | 内容 |
|----------------|------|
| **初回確認** | 内容を表示し、ユーザーの明示的な許可を求める |
| **ハッシュ検証** | ファイル変更時は信頼が無効化され再確認が必要 |
| **コマンドallowlist** | `npx`, `node`, `python3`, `deno` 等の安全なコマンドのみ許可 |
| **リポジトリ単位** | 信頼状態は `~/.config/eve-cli/trusted_repos.json` にリポジトリごとに保存 |

---

## Agent Teams（マルチエージェント）

大きなタスクを複数のAIエージェントに分担させる機能です。

### 使い方

```
> /team このプロジェクトにログイン機能を追加して

# オプション指定
> /team -n "auth-team" -w 3 認証システムの設計・実装・テストを行って
```

### オプション

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `-n <name>` | チーム名 | 自動生成 |
| `-w <count>` | ワーカー（エージェント）数 | 2 |

### 仕組み

1. リーダーエージェントがゴールをサブタスクに分解
2. ワーカーエージェントがそれぞれのタスクを並列で実行
3. 共有タスクストアで進捗を管理
4. 10分のタイムアウトで安全に制限

---

## 環境変数・設定

### 環境変数

| 変数 | 説明 | 例 |
|------|------|-----|
| `EVE_CLI_MODEL` | デフォルトモデル名 | `qwen3:8b` |
| `EVE_CLI_SIDECAR_MODEL` | サイドカーモデル名（要約等に使用） | `qwen3:4b` |
| `EVE_CLI_PROFILE` | 接続プロファイル | `auto`, `online`, `offline` |
| `EVE_CLI_DEBUG` | デバッグモード | `1` で有効 |
| `OLLAMA_HOST` | Ollamaホスト URL | `http://localhost:11434` |

### シェル設定（~/.zshrc または ~/.bashrc）

```bash
# デフォルトモデルを設定
export EVE_CLI_MODEL="qwen3:8b"

# クラウドモデルを使う場合
export EVE_CLI_MODEL="qwen3.5:397b-cloud"

# サイドカーモデル（会話要約用の軽量モデル）
export EVE_CLI_SIDECAR_MODEL="qwen3:4b"

# デバッグモードを有効化
export EVE_CLI_DEBUG=1

# Ollamaのホストを変更（デフォルト: http://localhost:11434）
export OLLAMA_HOST="http://localhost:11434"
```

設定後、ターミナルを再起動するか `source ~/.zshrc` を実行してください。

### 設定ファイル（~/.config/eve-cli/config）

```ini
MODEL=qwen3:8b
SIDECAR_MODEL=qwen3:4b
OLLAMA_HOST=http://localhost:11434
MAX_TOKENS=4096
TEMPERATURE=0.25
CONTEXT_WINDOW=65536

# プロファイル: auto（デフォルト）、online、offline、カスタム名
PROFILE=auto
```

### 設定ファイル一覧

| ファイル | 内容 |
|---------|------|
| `~/.config/eve-cli/config` | メイン設定ファイル |
| `~/.config/eve-cli/permissions.json` | ツール許可・拒否設定（自動保存） |
| `~/.config/eve-cli/memory/memory.json` | 長期メモリ |
| `~/.config/eve-cli/hooks.json` | グローバルフック設定 |
| `~/.config/eve-cli/mcp.json` | MCPサーバー設定 |
| `~/.config/eve-cli/CLAUDE.md` | グローバルプロジェクト指示 |
| `~/.config/eve-cli/skills/*.md` | カスタムスキル |
