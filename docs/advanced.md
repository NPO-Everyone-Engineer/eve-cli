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
- [KAIROS（プロアクティブ監督）](#kairosプロアクティブ監督)
- [Channels（外部チャンネル連携）](#channels外部チャンネル連携)
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
MODEL=glm-5:cloud
SIDECAR_MODEL=gemma4:31b-cloud
UTILITY_MODEL=gemma4:31b-cloud
COMPACTION_MODEL=gemma4:31b-cloud
SUBAGENT_MODEL=glm-5:cloud
REVIEW_MODEL=gemma4:31b-cloud
OLLAMA_HOST=https://ollama.com/api
PLAN_MODE_REASONING_EFFORT=high

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

### Hook 環境変数ポリシー

フックに渡す環境変数は config で調整できます。

```ini
HOOK_ENV_POLICY=inherit
HOOK_ENV_INCLUDE=CI,HTTPS_PROXY
HOOK_ENV_EXCLUDE=CI_JOB_TOKEN
HOOK_ENV_SET=TEAM=backend
```

- `HOOK_ENV_POLICY=default`: 既定の安全な allowlist を使う
- `HOOK_ENV_POLICY=inherit`: ほぼ現在の環境を引き継ぐ。ただし secret 系は明示 include しない限り除外
- `HOOK_ENV_INCLUDE`: 追加で渡したい変数
- `HOOK_ENV_EXCLUDE`: 明示的に外したい変数
- `HOOK_ENV_SET`: 固定値を注入

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

### Skill の有効/無効化

Skill が増えて prompt が膨らむ場合は、config で絞れます。

```ini
SKILLS_ENABLE=design*,review
SKILLS_DISABLE=bugfix
```

- `SKILLS_ENABLE`: このパターンに一致する skill だけを読み込む
- `SKILLS_DISABLE`: 一致する skill を除外する
- 判定対象は skill 名、パス、basename

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

### MCP の詳細設定

`mcp.json` では、server 単位で tool の絞り込みや timeout を指定できます。

```json
{
  "mcpServers": {
    "docs": {
      "command": "python3",
      "args": ["scripts/docs_mcp.py"],
      "enabled": true,
      "required": true,
      "enabled_tools": ["read_doc", "search_doc"],
      "disabled_tools": ["delete_doc"],
      "startup_timeout_sec": 20,
      "tool_timeout_sec": 45,
      "env_vars": ["DOCS_API_TOKEN"],
      "env": {"DOCS_MODE": "readonly"}
    }
  }
}
```

- `enabled`: `false` なら読み込まない
- `required`: 起動失敗時に eve-cli 全体を止める
- `enabled_tools` / `disabled_tools`: 公開する MCP tool を絞る
- `startup_timeout_sec`: `initialize` / `tools/list` の待ち時間
- `tool_timeout_sec`: `tools/call` の待ち時間
- `env_vars`: 明示した環境変数だけを子プロセスに渡す
- `env`: 固定値を追加で渡す

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

## KAIROS（プロアクティブ監督）

KAIROS は、EvE CLI のバックグラウンド supervisor です。一定間隔で heartbeat を回し、リポジトリ状態、テスト失敗、PR イベント、保留中 approval などを観測して、通知・提案・低リスク自動実行を切り替えます。

### モード

| モード | 振る舞い |
|-------|----------|
| `observe` | 実行しません。必要があれば通知だけ出します |
| `suggest` | 実行計画は立てますが、実行前に approval queue へ入れます |
| `active` | allowlist に入っている低リスク tool だけ即時実行します |

### 有効化

対話中に手動で起動できます。

```text
> /kairos on
> /kairos status
```

起動時から有効にしたい場合は `kairos.json` に `enabled: true` を入れるか、環境変数 `EVE_CLI_PROACTIVE=1` を付けて起動します。

```bash
EVE_CLI_PROACTIVE=1 eve-cli
```

### 設定ファイル

KAIROS の設定は次の順でマージされます。

1. 内部デフォルト
2. `~/.config/eve-cli/kairos.json`
3. `.eve-cli/kairos.json`
4. 環境変数 `EVE_CLI_PROACTIVE=1`（`enabled` を強制有効化）

設定例:

```json
{
  "enabled": true,
  "mode": "observe",
  "heartbeat_seconds": 300,
  "active_hours": "workhours",
  "allow_proactive_tools": [
    "Read",
    "Glob",
    "Grep",
    "WebFetch",
    "TaskCreate",
    "TaskUpdate",
    "TaskList",
    "TaskGet"
  ],
  "approval_policy": {
    "low": "allow",
    "medium": "prompt",
    "high": "deny"
  },
  "pr_watch": {
    "enabled": true
  },
  "dream": {
    "enabled": true,
    "schedule": "03:00"
  },
  "notification": {
    "cooldown_sec": 300
  }
}
```

主な項目:
- `mode`: `observe` / `suggest` / `active`
- `heartbeat_seconds`: heartbeat 間隔。実装上は 30 秒未満にできません
- `active_hours`: `always` / `workhours` / `custom`
- `allow_proactive_tools`: `active` モードで自動実行してよい tool の allowlist
- `approval_policy`: `low` / `medium` / `high` ごとの扱い
- `dream.schedule`: `autoDream` の実行時刻（ローカル時刻、`HH:MM`）

### PR 監視

`/kairos watch pr add <repo> <num>` で PR を監視できます。GitHub API のポーリングには `EVE_CLI_GITHUB_TOKEN` が必要です。

監視状態はプロジェクト配下に保存されます。

- `.eve-cli/kairos/watchers.json`

### 状態・ログの保存先

KAIROS は state ディレクトリ配下に実行状態を保存します。既定では macOS / Linux で `~/.local/state/eve-cli/kairos/`、`XDG_STATE_HOME` を設定している場合はその配下です。

| パス | 内容 |
|------|------|
| `.../kairos/state.json` | supervisor の状態、last heartbeat、pause 状態 |
| `.../kairos/approvals.json` | approval queue |
| `.../kairos/dedupe.json` | 重複実行の cooldown キャッシュ |
| `.../kairos/audit/YYYY-MM-DD.jsonl` | 監査ログ |
| `.../kairos/dream/YYYY-MM-DD.md` | `autoDream` レポート |

`/kairos log` は `audit/*.jsonl` を読み、`/kairos dream now` は `dream/*.md` を生成します。

---

## Channels（外部チャンネル連携）

Discord・Slack・汎用 Webhook から、**実行中の EvE CLI セッションにメッセージを送受信**できる機能です。
たとえば「Discord でメッセージを送ると、エージェントが作業して結果を Discord に返信する」といった使い方ができます。

### 対応チャンネル

| チャンネル | 方式 | 難易度 |
|-----------|------|--------|
| **Webhook** | HTTP POST で任意のツールから送受信 | 低（アカウント不要） |
| **Discord** | Discord ボットが DM を中継 | 中 |
| **Slack** | Slack アプリが Events API で中継 | 中 |

---

### Webhook（最も簡単）

外部サービスや curl など、任意の HTTP クライアントからメッセージを送れます。

#### 起動

```bash
eve-cli --channels webhook
```

起動すると `http://127.0.0.1:8788/webhook` で待ち受けを開始します。

#### メッセージを送る

別のターミナルで POST するとエージェントが反応します：

```bash
curl -X POST http://127.0.0.1:8788/webhook \
  -H "Content-Type: application/json" \
  -d '{"content": "今のディレクトリのファイルを教えて", "sender_id": "me", "sender_name": "テスト"}'
```

| フィールド | 必須 | 説明 |
|-----------|------|------|
| `content` | 必須 | エージェントに渡すメッセージ |
| `sender_id` | 必須 | 送信者の識別 ID（任意の文字列） |
| `sender_name` | 任意 | ターミナルに表示される名前 |
| `callback_url` | 任意 | 返信を受け取る URL |

#### 送信者を許可する

初期状態では **すべての送信者が拒否**されます。許可するには：

```
> /webhook:allow me
```

`sender_id` に指定した値（上の例では `me`）を許可リストに追加します。

#### API キーで保護する（推奨）

```
> /webhook:configure my-secret-key
```

設定後は、リクエストに `Authorization: Bearer my-secret-key` ヘッダーが必要になります。

---

### Discord

Discord ボットを作成し、DM やチャンネルのメッセージをエージェントに転送します。

#### 事前準備（一度だけ）

1. [Discord Developer Portal](https://discord.com/developers/applications) でアプリを作成
2. 「Bot」タブでボットを作成し、トークンをコピー
3. 「OAuth2 → URL Generator」で `bot` スコープ、`Send Messages` / `Read Message History` 権限を付与してボットをサーバーに招待
4. メッセージを受け取りたいチャンネルの ID をコピー（チャンネルを右クリック → 「ID をコピー」）

> チャンネル ID を表示するには、Discord の設定 → 詳細設定 → 「開発者モード」をオンにしてください。

#### 起動・設定

`--channels discord` で起動し、その後トークンとチャンネル ID を登録します。
登録後はアダプターが**自動で起動**するので、再起動は不要です。

```bash
eve-cli --channels discord
```

```
> /discord:configure ボットトークン チャンネルID
```

複数チャンネルをカンマ区切りで指定できます：

```
> /discord:configure ボットトークン 123456789,987654321
```

設定後、ターミナルに `⚡ Discord adapter started.` と表示されればポーリング開始です。

#### ペアリング（送信者の認証）

初めてメッセージを送ると、ボットが 6 桁のペアリングコードを返信します。
そのコードを EvE CLI で入力すると、その Discord ユーザーが許可されます：

```
> /discord:pair 123456
```

#### アクセスポリシー

| コマンド | 説明 |
|---------|------|
| `/discord:access policy allowlist` | 許可済みユーザーのみ（デフォルト・推奨） |
| `/discord:access policy open` | 全員を許可（開発・テスト用のみ） |

---

### Slack

Slack Events API 経由でメッセージを受信し、エージェントが Slack に返信します。

#### 事前準備（一度だけ）

1. [Slack API](https://api.slack.com/apps) で新しいアプリを作成
2. 「OAuth & Permissions」で `chat:write` スコープを追加し、ワークスペースにインストール
3. 「Bot User OAuth Token」（`xoxb-` で始まる）をコピー
4. 「Basic Information → App Credentials」から「Signing Secret」をコピー
5. 「Event Subscriptions」を有効化し、Request URL に以下を設定：
   - ローカル: `ngrok` 等でポート 8788 を公開してから URL を入力
   - URL 形式: `https://あなたのドメイン/webhook/slack`
6. 「Subscribe to bot events」で `message.channels` または `app_mention` を追加

> ローカル開発に [ngrok](https://ngrok.com/) を使う場合: `ngrok http 8788` で得た URL を Request URL に設定してください。

#### 起動・設定

```bash
eve-cli --channels slack
```

```
> /slack:configure xoxb-ボットトークン 署名シークレット
```

#### 送信者の許可

Slack ユーザー ID（`U` で始まる文字列）を許可します：

```
> /slack:allow U12345678
```

ユーザー ID は Slack のプロフィールページ → 「その他」→ 「メンバー ID をコピー」で確認できます。

---

### 複数チャンネルを同時に使う

```bash
eve-cli --channels discord,slack,webhook
```

---

### 状態の確認・停止

```
> /channels list    # 接続中チャンネルと状態を表示
> /channels stop    # 全チャンネルを停止
```

---

### 仕組みと安全性

- HTTP サーバーは `127.0.0.1`（ローカルホスト）にのみバインドされます。外部に直接公開されません。
- Discord ボットトークンやシークレットは `.eve-cli/channels/{チャンネル名}/.env` に保存され、パーミッション 600（自分のみ読める）に設定されます。
- ホワイトリストにない送信者のメッセージは「Unauthorized sender.」と返信して無視します。
- Slack は HMAC-SHA256 署名検証とタイムスタンプ検証（5 分以内）でリプレイ攻撃を防いでいます。

---

## 環境変数・設定ファイル一覧

### 環境変数

| 変数 | 説明 | 例 |
|------|------|-----|
| `EVE_CLI_MODEL` | デフォルトモデル | `glm-5:cloud` |
| `EVE_CLI_SIDECAR_MODEL` | サイドカーモデル | `gemma4:31b-cloud` |
| `EVE_CLI_UTILITY_MODEL` | helper / utility モデル | `gemma4:31b-cloud` |
| `EVE_CLI_COMPACTION_MODEL` | 会話圧縮モデル | `gemma4:31b-cloud` |
| `EVE_CLI_SUBAGENT_MODEL` | サブエージェントモデル | `glm-5:cloud` |
| `EVE_CLI_REVIEW_MODEL` | Rubber Duck / review モデル | `gemma4:31b-cloud` |
| `EVE_CLI_PROFILE` | 接続プロファイル | `auto` |
| `EVE_CLI_DEBUG` | デバッグモード | `1` |
| `EVE_CLI_MAX_AGENT_STEPS` | AI ステップ上限 | `80` |
| `EVE_CLI_SUBAGENT_DEFAULT_MAX_TURNS` | サブエージェント既定ターン数 | `15` |
| `EVE_CLI_PROMPT_COST_PER_MTOK` | 入力 100 万 tokens あたりの推定コスト（USD） | `0.15` |
| `EVE_CLI_COMPLETION_COST_PER_MTOK` | 出力 100 万 tokens あたりの推定コスト（USD） | `0.60` |
| `EVE_CLI_PLAN_MODE_REASONING_EFFORT` | Plan mode 用の reasoning 強度 | `high` |
| `EVE_CLI_PROACTIVE` | KAIROS を強制有効化 | `1` |
| `EVE_CLI_SHELL_ENV_POLICY` | Bash 実行時の環境変数ポリシー | `inherit` |
| `EVE_CLI_HOOK_ENV_POLICY` | Hook 実行時の環境変数ポリシー | `inherit` |
| `EVE_CLI_NOTIFY_COMMAND` | 通知用コマンド | `python3 ~/.config/eve-cli/notify.py` |
| `EVE_CLI_NOTIFY_ON` | 通知イベント | `stop,error` |
| `EVE_CLI_SKILLS_ENABLE` | 読み込む skill パターン | `design*,review` |
| `EVE_CLI_SKILLS_DISABLE` | 除外する skill パターン | `bugfix` |
| `EVE_CLI_GITHUB_TOKEN` | KAIROS の PR 監視に使う GitHub token | `ghp_...` |
| `OLLAMA_HOST` | Ollama ホスト URL | `http://localhost:11434` / `https://ollama.com/api` |
| `OLLAMA_API_KEY` | Ollama Cloud API キー | `ollama_...` |

### 設定ファイル（~/.config/eve-cli/config）

```ini
MODEL=glm-5:cloud
SIDECAR_MODEL=gemma4:31b-cloud
UTILITY_MODEL=gemma4:31b-cloud
COMPACTION_MODEL=gemma4:31b-cloud
SUBAGENT_MODEL=glm-5:cloud
REVIEW_MODEL=gemma4:31b-cloud
OLLAMA_HOST=https://ollama.com/api
CONTEXT_WINDOW=202752
MAX_TOKENS=4096
TEMPERATURE=0.25
SUBAGENT_DEFAULT_MAX_TURNS=15
PROMPT_COST_PER_MTOK=0.15
COMPLETION_COST_PER_MTOK=0.60
PLAN_MODE_REASONING_EFFORT=high
SHELL_ENV_POLICY=inherit
HOOK_ENV_POLICY=default
NOTIFY_COMMAND=python3 ~/.config/eve-cli/notify.py
NOTIFY_ON=stop,error
SKILLS_ENABLE=design*,review
PROFILE=auto
```

Ollama Cloud を使う場合の例：

```bash
export OLLAMA_API_KEY=your-ollama-api-key
eve-cli --ollama-host https://ollama.com/api --model glm-5:cloud
```

補足:
- `OLLAMA_HOST` は `https://ollama.com` や `https://ollama.com/api` を受け付け、内部で native API 向けに正規化します。
- `eve-cli` は Ollama の native `/api/*` を使うため、OpenAI 互換の `/v1` ではなく Ollama endpoint を指定してください。
- `PROMPT_COST_PER_MTOK` / `COMPLETION_COST_PER_MTOK` は `/usage` の推定コスト計算に使われます。未設定時は `0.0` として扱われます。
- `PLAN_MODE_REASONING_EFFORT` は `none|low|medium|high|max` を受け付け、Plan mode 中だけ thinking budget を上書きします。
- `SUBAGENT_DEFAULT_MAX_TURNS` はサブエージェントの既定ターン数です。現在の hard cap は `20` です。
- `SHELL_ENV_POLICY` / `HOOK_ENV_POLICY` は `default` と `inherit` を受け付けます。
- `NOTIFY_COMMAND` は JSON payload を stdin で受け取る想定です。

### 設定ファイル一覧

| ファイル | 内容 |
|---------|------|
| `~/.config/eve-cli/config` | メイン設定 |
| `~/.config/eve-cli/kairos.json` | KAIROS のグローバル設定 |
| `~/.config/eve-cli/permissions.json` | グローバルなツール許可・拒否・確認（自動保存） |
| `.eve-cli/permissions.json` | プロジェクト単位の approval policy（tool / category / path ルール） |
| `.eve-cli/kairos.json` | KAIROS のプロジェクト設定 |
| `.eve-cli/kairos/watchers.json` | PR 監視対象の保存 |
| `~/.config/eve-cli/memory/memory.json` | 長期メモリ |
| `~/.config/eve-cli/hooks.json` | グローバルフック |
| `~/.config/eve-cli/mcp.json` | MCP サーバー設定 |
| `~/.config/eve-cli/CLAUDE.md` | グローバルプロジェクト指示 |
| `~/.config/eve-cli/skills/*.md` | カスタムスキル |
| `~/.config/eve-cli/trusted_repos.json` | 信頼済みリポジトリ |
| `~/.config/eve-cli/trusted_hooks.json` | 信頼済みフック |
| `~/.local/state/eve-cli/kairos/` | KAIROS の state, approvals, audit, dream レポート |

`permissions.json` は従来の `{ "ToolName": "allow|deny|prompt" }` 形式に加えて、`tools` / `categories` / `paths` を持つ構造化形式も読めます。
`prompt` は明示的な確認ポリシーで、`-y` や Guardian auto-mode より優先されます。
