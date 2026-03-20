# 高度な機能

EvE CLI のカスタマイズや高度な設定について解説します。

> 基本的な使い方は [使い方ガイド](usage.md) をご覧ください。

---

## 目次

- [メモリ（長期記憶）](#メモリ長期記憶)
- [プロジェクト設定ファイル](#プロジェクト設定ファイル)
- [プロファイル（ネットワーク自動切替）](#プロファイルネットワーク自動切替)
- [Hooks（ライフサイクルフック）](#hooksライフサイクルフック)
- [Skills（カスタムスキル）](#skillsカスタムスキル)
- [コードインテリジェンス](#コードインテリジェンス)
- [ブラウザ操作（MCP）](#ブラウザ操作mcp)
- [Agent Teams](#agent-teams)
- [環境変数・設定ファイル一覧](#環境変数設定ファイル一覧)

---

## メモリ（長期記憶）

セッション間で情報を記憶する機能です。プロジェクトの規約やユーザーの好みを覚えておけます。

### 基本操作

```
> /memory add コミットメッセージは日本語で書く
> /memory add [style] インデントはスペース4つ
> /memory                         # 一覧表示
> /memory search インデント        # 検索
> /memory remove 1                # 削除
> /memory clear                   # 全削除
```

`[カテゴリ]` を付けると整理しやすくなります（省略可）。

### 仕組み

- 保存先: `~/.config/eve-cli/memory/memory.json`
- 起動時にシステムプロンプトに自動注入
- 最大 100 エントリ、各エントリ最大 500 文字

---

## プロジェクト設定ファイル

プロジェクトごとに AI への指示を設定できます。

### 設定ファイルの種類（すべてマージされます）

| ファイル | 用途 | Git 管理 |
|---------|------|---------|
| `~/.config/eve-cli/CLAUDE.md` | グローバル（全プロジェクト共通） | ― |
| `.eve-cli/CLAUDE.md` | チーム共有設定 | する |
| `CLAUDE.md` | プロジェクトルート | する |
| `CLAUDE.local.md` | 個人設定（自分だけ） | しない |
| `.eve-coder.json` | 旧形式（後方互換） | する |

### 自動生成

```
> /init
```

プロジェクトの言語・フレームワーク・ビルドコマンドを自動検出して `.eve-cli/CLAUDE.md` を生成します。

### 設定例

```markdown
# プロジェクトルール

## コーディング規約
- TypeScript を使用
- インデントはスペース 2 つ
- 関数名は camelCase

## テスト
- Jest を使用
- カバレッジ 80% 以上を維持

## コミット
- Conventional Commits 形式
- 日本語で記述
```

### セキュリティ

プロジェクト内の設定ファイル（`CLAUDE.md` / `.eve-cli/CLAUDE.md` / `.eve-coder.json`）は、初回に信頼確認が必要です。ファイル内容が変わると再確認されます。

---

## プロファイル（ネットワーク自動切替）

ネットワーク状態に応じてモデルを自動切り替えできます。

### 設定方法

`~/.config/eve-cli/config` にプロファイルセクションを追加：

```ini
PROFILE=auto

[profile:online]
MODEL=qwen3.5:397b-cloud
SIDECAR_MODEL=qwen3:8b

[profile:offline]
MODEL=qwen3:8b
SIDECAR_MODEL=qwen3:4b
```

### 動作

| 設定 | 動作 |
|------|------|
| `auto` | ネットワーク接続を自動検知して切替 |
| `online` | 常にオンライン設定を使用 |
| `offline` | 常にオフライン設定を使用 |
| カスタム名 | 指定したプロファイルを使用 |

コマンドラインオプション（`--model` 等）はプロファイル設定より優先されます。

---

## Hooks（ライフサイクルフック）

エージェントのイベントに対してカスタムコマンドを実行できます。

### 設定ファイル

| ファイル | 用途 | 信頼確認 |
|---------|------|---------|
| `~/.config/eve-cli/hooks.json` | グローバル | 不要（常に信頼） |
| `.eve-cli/hooks.json` | プロジェクト | 初回に必要 |

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
| `SessionStart` | セッション開始時 | 環境チェック |
| `PreToolUse` | ツール実行前 | カスタム承認、ログ |
| `PostToolUse` | ツール実行後 | 結果のログ、通知 |
| `Stop` | セッション終了時 | クリーンアップ |

`PreToolUse` フックが非ゼロで終了すると、そのツール実行はブロックされます。

### フック実行時の環境変数

| 変数 | 説明 |
|------|------|
| `EVE_HOOK_EVENT` | イベント名 |
| `EVE_HOOK_TOOL_NAME` | ツール名 |
| `EVE_HOOK_SESSION_ID` | セッション ID |
| `EVE_HOOK_CWD` | 作業ディレクトリ |

### セキュリティ制限

- プロジェクトフックは allowlist のコマンドのみ実行可能（`echo`, `bash`, `python3`, `node` 等）
- リポジトリ内スクリプトはハッシュ検証対象
- symlink やリポジトリ外への参照は拒否
- タイムアウト: 最大 30 秒

---

## Skills（カスタムスキル）

特定のタスクに特化した AI への指示セットを再利用可能な形で定義できます。

### 標準 Skills

| Skill | 説明 | 使い方 |
|-------|------|--------|
| `explain` | コードの仕組みを解説 | `/custom explain src/main.py` |
| `review` | コードレビュー | `/custom review src/` |
| `test` | テスト自動生成 | `/custom test calculator.py` |
| `learn` | 学習モード | `eve-cli --learn` |

### 保存場所

| ディレクトリ | 用途 | Git 管理 |
|-------------|------|---------|
| `~/.config/eve-cli/skills/` | グローバル（全プロジェクト共通） | ― |
| `.eve-cli/skills/` | チーム共有 | する |
| `skills/` | プロジェクトルート | する |

### カスタム Skill の作り方

`.md` ファイルとして保存します：

```markdown
---
description: API ドキュメント生成
allowed-tools: [Read, Write, Glob]
---
# API ドキュメント生成

指定されたファイルから API ドキュメントを生成します。

## 要件
- Markdown 形式
- 各関数の説明、引数、戻り値を含む

## 出力先
docs/api/<filename>.md
```

### 変数展開

| 変数 | 説明 |
|------|------|
| `$ARGUMENTS` | コマンドの全引数 |
| `$0` | Skill 名 |
| `$1`, `$2`, ... | 位置引数 |
| `$SKILL_DIR` | Skill ディレクトリのパス |
| `$CWD` | 現在の作業ディレクトリ |

---

## コードインテリジェンス

プロジェクト内の関数・クラス・変数を高速検索できます。

```
> /index build              # インデックスを構築（初回のみ）
> /index search "handleClick"  # 関数名を検索
> /index file src/app.py    # ファイル内のシンボル一覧
```

対応言語: Python, JavaScript/TypeScript, Go, Rust, Ruby, Java

正規表現ベースのシンボル抽出で、外部依存なしに高速動作します。

---

## ブラウザ操作（MCP）

[Playwright MCP](https://github.com/anthropics/mcp) を使って、EvE CLI からブラウザを操作できます。

### セットアップ

```bash
brew install node
eve-cli
> /browser setup
```

セットアップ後、再起動するとブラウザ操作ツールが自動で読み込まれます。

### 使い方

```
> https://example.com を開いてページの内容を教えて
> Google で "EvE CLI" を検索して最初の結果を教えて
> フォームに名前を入力して送信ボタンを押して
```

### MCP 設定ファイル

| ファイル | 用途 | 信頼確認 |
|---------|------|---------|
| `~/.config/eve-cli/mcp.json` | グローバル | 不要 |
| `.eve-cli/mcp.json` | プロジェクト | 初回に必要 |

プロジェクトレベルの MCP 設定は、リポジトリに含まれるファイルのためセキュリティ確認が必要です。

---

## Agent Teams

複数の AI エージェントに大きなタスクを分担させる機能です。

### 使い方

```
> /team このプロジェクトにログイン機能を追加して
> /team -n "auth-team" -w 3 認証の設計・実装・テストを行って
```

### 仕組み

1. リーダーエージェントがゴールをサブタスクに分解
2. ワーカーエージェントが並列で実行
3. 共有タスクストアで進捗を管理
4. 10 分のタイムアウトで安全に制限

---

## 環境変数・設定ファイル一覧

### 環境変数

| 変数 | 説明 | 例 |
|------|------|-----|
| `EVE_CLI_MODEL` | デフォルトモデル | `qwen3:8b` |
| `EVE_CLI_SIDECAR_MODEL` | サイドカーモデル | `qwen3:4b` |
| `EVE_CLI_PROFILE` | 接続プロファイル | `auto` |
| `EVE_CLI_DEBUG` | デバッグモード | `1` |
| `EVE_CLI_MAX_AGENT_STEPS` | AI ステップ上限 | `80` |
| `OLLAMA_HOST` | Ollama ホスト URL | `http://localhost:11434` |

### 設定ファイル（~/.config/eve-cli/config）

```ini
MODEL=qwen3:8b
SIDECAR_MODEL=qwen3:4b
OLLAMA_HOST=http://localhost:11434
MAX_TOKENS=4096
TEMPERATURE=0.25
CONTEXT_WINDOW=65536
PROFILE=auto
```

### 設定ファイル一覧

| ファイル | 内容 |
|---------|------|
| `~/.config/eve-cli/config` | メイン設定 |
| `~/.config/eve-cli/permissions.json` | グローバルなツール許可・拒否（自動保存） |
| `.eve-cli/permissions.json` | プロジェクト単位の approval policy（tool / category / path ルール） |
| `~/.config/eve-cli/memory/memory.json` | 長期メモリ |
| `~/.config/eve-cli/hooks.json` | グローバルフック |
| `~/.config/eve-cli/mcp.json` | MCP サーバー設定 |
| `~/.config/eve-cli/CLAUDE.md` | グローバルプロジェクト指示 |
| `~/.config/eve-cli/skills/*.md` | カスタムスキル |
| `~/.config/eve-cli/trusted_repos.json` | 信頼済みリポジトリ |
| `~/.config/eve-cli/trusted_hooks.json` | 信頼済みフック |

`permissions.json` は従来の `{ "ToolName": "allow|deny" }` 形式に加えて、`tools` / `categories` / `paths` を持つ構造化形式も読めます。
