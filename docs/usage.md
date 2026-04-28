# 使い方ガイド

EvE CLI の機能と使い方を詳しく解説します。

> 初めての方は先に [はじめてガイド](getting-started.md) をご覧ください。

---

## 目次

- [起動オプション](#起動オプション)
- [入力方法](#入力方法)
- [パーミッション（実行許可）](#パーミッション実行許可)
- [安全性・復旧機能](#安全性復旧機能)
- [診断・可視化コマンド](#診断可視化コマンド)
- [コミットメッセージ自動生成](#コミットメッセージ自動生成)
- [テスト生成](#テスト生成)
- [GitHub 連携](#github-連携)
- [ループモード](#ループモード)
- [学習モード](#学習モード)
- [エラー自動修復](#エラー自動修復)
- [自動コンパクション](#自動コンパクション)

---

## 起動オプション

### 対話モード（基本）

```bash
eve-cli
```

起動すると対話画面が表示されます。日本語で自由に話しかけてください。

### ワンショットモード

```bash
eve-cli -p "Hello Worldを作って"
```

1 回だけ質問して結果を受け取ります。CI/CD スクリプトでも使えます。

### よく使うオプション

| オプション | 説明 | 例 |
|-----------|------|-----|
| `--model <名前>` | 使用モデルを指定 | `--model qwen3.5:14b` |
| `-p "<指示>"` | ワンショットモードで実行 | `-p "バグを直して"` |
| `-y` | 自動許可モード（毎回の確認をスキップ） | |
| `--resume` | セッションを再開（候補が複数あればピッカー表示） | |
| `--continue` | 最新セッションを即時再開（ピッカーをスキップ） | |
| `--session-id <id>` | 特定セッションを ID で指定再開 | |
| `--list-sessions` | 保存済みセッション一覧（cwd / preview 付き） | |
| `--profile <名前>` | 接続プロファイルを指定 | `--profile offline` |
| `--output-format json` | 出力を JSON 形式に | |
| `--learn` | 学習モードで起動 | |
| `--learn --level <1-5>` | 学習モードの難易度を指定 | `--learn --level 3` |
| `--loop` | ループモードで実行 | |
| `--max-agent-steps <N>` | AI の内部ステップ上限（既定: 50） | `--max-agent-steps 80` |
| `--think` / `--no-think` | Thinking モード（Qwen3 推論）の ON/OFF | `--think` |
| `--autotest` | 自動 Lint/Test を有効にして起動 | |
| `--headless` | CI/CD 向けヘッドレスモード（`-p` 必須） | |

### サイドカーモデルの指定

会話の自動圧縮など内部処理に使う軽量モデルを、環境変数で設定できます：

```bash
EVE_CLI_SIDECAR_MODEL=qwen3-coder-next:cloud eve-cli
```

---

## 入力方法

| 操作 | 説明 |
|------|------|
| **Enter** | 改行（入力を続ける） |
| **空 Enter** | メッセージ送信（何も入力せず Enter） |
| **`"""`** | マルチラインモード（`"""` で開始・終了） |
| **Tab** | ファイルパス・コマンドの自動補完 |
| **@ファイル名** | ファイル内容を自動添付（例: `@src/main.py を修正して`） |
| **ESC** | AI の実行を中断 |

### 画像を添付する

ビジョン対応モデル（`llava`, `llama3.2-vision`, `gemma3` 等）が必要です。

```
> /image                          # クリップボードの画像を添付
> /image ~/Desktop/screenshot.png  # ファイルパスで指定
> (ターミナルに画像をドラッグ&ドロップ)
```

---

## パーミッション（実行許可）

EvE CLI はファイル書き込みやコマンド実行の前に必ず確認を求めます。

### 確認画面の選択肢

| キー | 意味 |
|------|------|
| `y` | **今回だけ**許可 |
| `a` | このツールを**今後すべて**許可 |
| `p` | このツールを**今後も毎回確認** |
| `n` / Enter | **拒否**（デフォルト） |
| `d` | このツールを**今後すべて**拒否 |
| `Y` | **すべてのツール**を自動許可（`-y` モードと同じ） |

### 知っておくと便利なこと

- `a` や `d` の設定は `~/.config/eve-cli/permissions.json` に保存され、次回も有効
- `p` を選ぶと、そのツールは三値ポリシーの `prompt` として保存され、`-y` や Guardian auto-mode より優先して毎回確認されます
- **安全のため** `Bash`・`Write`・`Edit`・`ApplyPatch`・`MultiEdit`・`NotebookEdit` は永続的な自動許可ができません（毎回確認）
- 危険なコマンド（`sudo`、`rm` 等）は赤色でハイライト表示されます
- `--auto-mode` では Guardian が `low / medium / high` リスクを評価し、`low` は自動許可、`medium` は確認、`high` は自動拒否します

---

## 安全性・復旧機能

### 自動チェックポイント

ファイルを変更する前に、作業状態を自動バックアップします（Git の stash を使用）。

### 元に戻す方法

| コマンド | 説明 |
|---------|------|
| `/undo` | 直前のファイル変更だけ元に戻す |
| `/rollback` | チェックポイントの状態に戻す |
| `/checkpoint list` | 保存済みチェックポイント一覧を表示 |
| `/status` | セッション・Git・チェックポイントの状態を確認 |

### リッチ diff プレビュー

ファイル編集時に、変更前後の差分が色付きで表示されます：
- 赤色（`-`）: 削除される行
- 緑色（`+`）: 追加される行

### patch 形式の編集

大きめの変更や複数 hunk の修正では、`ApplyPatch` ツールが unified diff をまとめて適用します。
`Edit` の文字列置換よりも、大きな差分や複数ファイル変更に向いています。

---

## 診断・可視化コマンド

設定や routing の状況を確認したいときは、以下の診断コマンドを使えます。

| コマンド | 説明 |
|---------|------|
| `/doctor` | 設定、接続状態、trust 状態、runtime 概要をまとめて表示 |
| `/tool-pool` | 現在利用可能なツールと permission 状態を表示 |
| `/command-graph` | 直近の routing snapshot と候補ツールを表示 |
| `/command-graph <依頼文>` | 指定した依頼文に対する想定 routing を表示 |
| `/bootstrap-graph` | モデル接続、MCP、hooks、channels など起動パイプラインの状態を表示 |
| `/usage` | セッションをまたいだ token 集計と推定 cost を表示 |
| `/debug setup` | `/doctor` のエイリアス |
| `/debug route` | 直近の routing snapshot を簡易表示 |

### 使いどころ

- `モデルに繋がらない` とき: `/doctor`
- `なぜそのツールを使ったか見たい` とき: `/command-graph`
- `どのツールが今 blocked か確認したい` とき: `/tool-pool`
- `hooks / MCP / channel の読込状態を見たい` とき: `/bootstrap-graph`
- `トークン消費と概算費用を見たい` とき: `/usage`

`/doctor` には approval stack と直近の Guardian risk 判定も表示されます。

---

## ストリーミング中の入力キュー

AI が応答をストリーミングしている間に次の入力をタイプすると、入力はキューに積まれます。
改行まで入力した内容は次のターンでそのまま送信され、途中までの入力は次の prompt に prefill されます。

`/usage` の cost は、`PROMPT_COST_PER_MTOK` / `COMPLETION_COST_PER_MTOK` または
`EVE_CLI_PROMPT_COST_PER_MTOK` / `EVE_CLI_COMPLETION_COST_PER_MTOK` に設定した単価を元に計算されます。

---

## コミットメッセージ自動生成

```
> /commit
```

AI が差分を分析して [Conventional Commits](https://www.conventionalcommits.org/) 形式のメッセージを提案します。

**流れ：**

1. `git diff --cached` で差分を取得
2. 直近のコミットスタイルを参照
3. AI がメッセージを生成
4. 確認画面で承認・編集

```
> /commit

  Generated commit message:
  feat(auth): ログイン画面にパスワードリセット機能を追加

  [y] Commit  [e] Edit  [n] Cancel
```

---

## テスト生成

```
> /gentest src/calculator.py
```

AI が指定ファイルのユニットテストを自動生成します。

**自動で行われること：**
- ソースファイルの読み込みと分析
- 既存テストのスタイルを踏襲
- エッジケース・エラーケースを含む包括的なテスト生成
- `tests/` ディレクトリと `__init__.py` の自動作成
- 構文チェックの自動実行

---

## GitHub 連携

[GitHub CLI (`gh`)](https://cli.github.com/) がインストール済みで `gh auth login` が完了していれば使えます。

```
> /pr                  # PR 一覧を表示
> /pr create           # 新しい PR を作成
> /pr 42               # PR #42 の詳細を表示
> /pr checks 42        # CI チェック状況を確認
> /pr merge 42         # PR をマージ
> /gh issue list       # Issue 一覧
```

---

## ヘッドレスモード（CI/CD）

CI/CD パイプラインや自動化スクリプトから EvE CLI を実行するためのモードです。

```bash
# 基本的な使い方
eve-cli --headless -p "READMEのタイポを修正して" -y --output-format json

# GitHub Actions で使う場合
eve-cli --headless -p "lint エラーを修正して" -y --autotest
```

| 動作 | 説明 |
|------|------|
| TUI 無効化 | スピナー・スクロールリージョン・色を無効 |
| CI 自動検出 | `CI=true` や `GITHUB_ACTIONS` 環境変数で自動有効化 |
| 終了コード | `0`=成功, `1`=エラー, `2`=タイムアウト, `3`=ループ上限到達 |
| `-p` 必須 | 対話モードは不可（プロンプトが必要） |

### 出力フォーマット

| `--output-format` | 用途 | 形式 |
|---|---|---|
| `text` (default) | 人間が読む | プレーンテキスト |
| `json` | CI 結果を 1 つの JSON にまとめる | 最後に 1 つのオブジェクト |
| `stream-json` | リアルタイム監視・パイプ処理 | JSONL（イベント 1 行 = 1 JSON） |

#### `stream-json` のイベントスキーマ

各イベントは `type` フィールドで種類を判別します。`session_start` で始まり `done` で終わります。

```json
{"type":"session_start","model":"...","session_id":"...","prompt":"...","timestamp":...}
{"type":"tool_call","tool":"Bash","params":{...},"timestamp":...}
{"type":"tool_result","tool":"Bash","output":"...","is_error":false,"timestamp":...}
{"type":"assistant","content":"...","timestamp":...}
{"type":"done","stop_reason":"completed","stop_detail":"","exit_code":0,"duration_ms":1234,"token_usage":{"input":100,"output":50,"total":150},"timestamp":...}
```

**stop_reason** の値: `completed` / `assistant_final` / `max_iterations` / `tool_loop` / `interrupted` / `error`

#### `json` モードの最終出力

```json
{
  "role": "assistant",
  "content": "...",
  "model": "...",
  "session_id": "...",
  "tool_calls": 3,
  "stop_reason": "completed",
  "stop_detail": "",
  "duration_ms": 1234,
  "token_usage": {"input": 100, "output": 50, "total": 150},
  "events": [...],
  "exit_code": 0
}
```

#### CI 連携例（GitHub Actions）

```yaml
- name: Run AI fix
  run: |
    eve-cli --headless -p "lint エラーを修正" -y \
      --output-format stream-json \
    | tee result.jsonl
    # 最後の done イベントから exit_code を取得
    EXIT=$(tail -1 result.jsonl | jq -r .exit_code)
    exit "$EXIT"
```

---

## 自動 Lint/Test

ファイル変更のたびに lint と test を自動実行し、失敗したら AI が自動修正します。

```bash
# 起動時に有効化
eve-cli --autotest

# セッション中にトグル
/autotest
```

### 自動検出されるツール

| 種別 | 検出順序（優先度順） |
|------|---------------------|
| **Lint (Python)** | ruff → flake8 → py_compile |
| **Lint (Node.js)** | eslint |
| **Test (Python)** | pytest → unittest |
| **Test (Node.js)** | npm test |

---

## Repo Map（コード構造マップ）

プロジェクト全体のクラス・関数構造を生成し、AI のコンテキストに注入します。

```
/map
```

AI が「どのファイルにどんなクラス/関数があるか」を正確に把握するため、大規模プロジェクトでの編集精度が向上します。

---

## ループモード

AI が完了するまでプロンプトを自動再実行します。長時間の自律タスクに便利です。

```bash
eve-cli -p "pytest を実行して失敗があれば修正してください。全テスト通過したら ALL_DONE と出力してください" --loop --max-loop-iterations 5 --done-string "ALL_DONE" -y
```

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `--loop` | ループモードを有効化（`-p` と併用必須） | ― |
| `--max-loop-iterations N` | 最大再実行回数 | 5 |
| `--done-string TEXT` | 完了シグナル文字列 | `"DONE"` |
| `--max-loop-hours N` | 最大実行時間（時間、最大 72h） | なし |

**注意点：**
- `--loop` は `-p` と併用した場合のみ有効
- 各反復で会話履歴は引き継がれないが、ファイル変更は保持される
- 完了判定は AI の最終テキスト応答のみ（ツール出力は対象外）

---

## 学習モード

AI がコードやエラーを対話的に解説する機能です。プログラミング学習に最適です。

### 起動方法

```bash
eve-cli --learn
eve-cli --learn --level 3
```

### 難易度レベル

| レベル | スタイル | 対象 |
|--------|---------|------|
| 1 | 超簡潔 | 経験者・要点だけ知りたい |
| 2 | 簡潔 | 中級者 |
| 3 | 標準（デフォルト） | 一般的な解説 |
| 4 | 詳細 | 初心者・理由も含めて詳しく |
| 5 | 超詳細 | 超初心者・背景知識から丁寧に |

### 何が起きるか

**コード生成後：** 自動的に「なぜこう書くの？」セクションが表示されます。

**エラー発生時：** 自動的に「なぜエラーが起きたの？」と原因・修正方法を説明します。

### 操作

| キー | 説明 |
|------|------|
| `y` | わかった（次に進む） |
| `?` | もっと詳しく |
| `s` | スキップ |
| `n` | 解説なしで続ける |

### コマンド

```
/learn              # オン/オフ切替
/learn on           # オン
/learn off          # オフ
/learn level 4      # レベル変更
/learn auto on      # エラー自動解説オン
/learn auto off     # エラー自動解説オフ
```

---

## エラー自動修復

コマンドやテストが失敗すると、AI が自動でエラーを分析し修正を試みます。

**仕組み：**
1. `Bash`・`Edit`・`Write` がエラーを返すと発動
2. AI がエラー内容を分析
3. 次のステップで修正を実行
4. 同じエラーに対する自動修復は最大 2 回まで（無限ループ防止）

---

## 自動コンパクション

長い会話のコンテキスト上限を自動で管理します。

**仕組み：**
- トークン使用量がコンテキストウィンドウの 80% を超えると自動発動
- 古い会話を AI が要約・圧縮
- 直近 4 メッセージは完全に保持
- 5 イテレーションごとにチェック

手動で圧縮したい場合：

```
> /compact
```
