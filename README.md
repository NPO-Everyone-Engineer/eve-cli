# EvE CLI — Everyone.Engineer Coding Agent

**EvE CLI** は、AI と一緒にコードを書けるオープンソースのコーディングエージェントです。

[NPO法人 Everyone.Engineer](https://www.everyone.engineer) が提供しています。

> **「プログラミング未経験でも、AI と一緒にコードが書ける」** — それが EvE CLI の目指す世界です。

---

## 30秒で始める

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/NPO-Everyone-Engineer/eve-cli/main/install.sh -o install.sh && bash install.sh
```

```bash
eve-cli
```

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/NPO-Everyone-Engineer/eve-cli/main/install.ps1 | iex
```

```powershell
eve-cli
```

```text
> Hello Worldを作って
```

これだけで、AI がファイル作成・編集・実行まで進めてくれます。

> 詳しい導入手順は [はじめてガイド](docs/getting-started.md) をご覧ください。

---

## はじめての人は、まずこれだけ

EvE CLI はたくさん機能がありますが、最初は次の 4 つだけ覚えれば十分です。

1. `eve-cli` で対話モードを開く
2. 日本語でそのままやりたいことを書く
3. ファイルを見せたいときは `@ファイル名` を付ける
4. 書き込みやコマンド実行の前には確認が出るので、内容を見て許可する

たとえば、こんな使い方ができます。

```text
> Pythonで電卓アプリを作って
> このファイルのバグを直して @src/app.py
> テストを書いて実行して
```

---

## EvE CLI でできること

### コードを書く・直す

- 新しいファイルを作る
- 既存コードの修正を提案して反映する
- テストを追加して実行する
- エラーが出たときに原因を説明し、修正を試す

### 作業を続きから再開する

- セッションを保存して後で再開できます
- プロジェクトごとの会話履歴も扱えます
- ワンショット実行や JSON 出力にも対応しています

### 安全に使う

- ファイル書き込みやコマンド実行の前に確認します
- `/undo` で直前の変更を戻せます
- Git チェックポイントと rollback を使えます

### 少し慣れたら使える機能

- 学習モード（やさしく解説）
- ループモード（完了まで自動で繰り返す）
- **KAIROS** — リポジトリ状態を定期観測して、通知・承認待ちプラン・低リスク自動実行を切り替える proactive supervisor
- **自動 Lint/Test** — ファイル変更のたびに ruff/flake8/eslint + pytest を自動実行・自動修正
- **Repo Map** — プロジェクト構造を AI に注入して大規模コードベースでも正確に編集
- **Thinking モード** — Qwen3.5 の拡張推論で複雑な問題を深く思考
- **Headless モード** — CI/CD パイプラインから非対話で実行（stdin パイプ、`--max-turns`、`--carry-session` 対応）
- **プロジェクトコンテキスト自動学習** — 言語・FW・リンター・テストFW を自動検出してキャッシュ、初回から文脈を理解
- **コードレビュー** — `/review` コマンドでセキュリティ・パフォーマンス・保守性の構造化レビュー
- **Docker サンドボックス** — `--sandbox docker` で Bash コマンドをコンテナ内で安全に実行
- **Extensions** — `eve-cli install <github-url>` でコミュニティ製スキル・MCP 設定を追加
- GitHub 連携
- Hooks / Skills / MCP
- コードインテリジェンス
- ブラウザ操作
- RAG
- **Channels** — Discord・Slack・Webhook から実行中のエージェントにメッセージを送受信
- 日本語 UX（完全対応）

---

## 主な機能

| カテゴリ | 内容 |
|---------|------|
| **AI エージェント** | 複数の内蔵ツール、Plan/Act モード、Agent Teams、サブエージェント、Thinking モード |
| **開発支援** | コミット自動生成、テスト生成、自動 Lint/Test、Repo Map、コードレビュー（`/review`）、GitHub 連携 |
| **CI/CD** | Headless モード（stdin パイプ対応）、JSON 出力、`--max-turns`、`--carry-session`、ループモード |
| **コンテキスト** | プロジェクト自動解析（言語・FW・リンター・テストFW 検出）、キャッシュ、コードインテリジェンス |
| **Proactive** | KAIROS supervisor。heartbeat ごとに状況を観測し、`observe` / `suggest` / `active` モードで通知・承認待ち・低リスク自動実行を制御 |
| **使いやすさ** | 日本語 UX 完全対応、Tab 補完、画像添付、シンタックスハイライト、リッチ diff |
| **カスタマイズ** | メモリ（長期記憶）、Skills、Hooks、MCP、Extensions（`eve-cli install`）、テーマ変更 |
| **Channels** | Discord・Slack・Webhook から実行中のエージェントへ双方向通信。ペアリングコードで安全認証 |
| **安全性** | パーミッション管理、Docker サンドボックス（`--sandbox`）、Git チェックポイント、`/undo` |

> ツールの数や MCP 連携ツールは、設定やバージョンによって増減することがあります。詳しくは [コマンドリファレンス](docs/commands.md) を参照してください。

---

## よく使う起動例

| やりたいこと | コマンド |
|-------------|----------|
| 普通に使う | `eve-cli` |
| モデルを指定する | `eve-cli --model qwen3:8b` |
| 前回の続きから始める | `eve-cli --resume` |
| 1回だけ実行する | `eve-cli -p "テストを書いて実行して"` |
| 自動テスト付きで使う | `eve-cli --autotest` |
| Thinking モードで使う | `eve-cli --think` |
| 学習モードで使う | `eve-cli --learn --level 4` |
| CI/CD で実行する | `eve-cli --headless -p "lint修正して" -y --output-format json` |
| stdin パイプで実行する | `echo "テスト実行" \| eve-cli --headless --output-format json` |
| ターン数制限付き実行 | `eve-cli --headless -p "修正して" --max-turns 5 -y` |
| 完了まで自動で回す | `eve-cli -p "失敗テストを直して ALL_DONE と出して" --loop --done-string ALL_DONE -y` |
| ループで履歴を維持 | `eve-cli -p "修正" --loop --carry-session -y` |
| コードレビューする | 対話モードで `/review` または `/review 123`（PR番号） |
| KAIROS を起動する | `eve-cli` 起動後に `/kairos on` |
| サンドボックスで安全に | `eve-cli --sandbox docker --sandbox-no-network` |
| 拡張機能を追加する | `eve-cli install https://github.com/user/eve-ext-name` |
| Discord から操作する | `eve-cli --channels discord` |

---

## 推奨環境

以下は **現行インストーラーが選ぶ目安** です。必要なら `--model` で手動指定できます。

| 環境 | メモリ | 既定の目安 |
|------|-------|------------|
| Apple Silicon Mac / Linux | 32GB+ | `qwen3-coder:30b` |
| Apple Silicon Mac / Linux | 16GB+ | `qwen3.5:397b-cloud` |
| 省メモリ環境 | 8GB+ | `qwen3.5:32b` |
| 手動で軽いモデルを使いたい | 制限なし | `--model qwen3:8b` など |

```bash
eve-cli --model qwen3:8b
```

> クラウドモデルを使う場合はネットワーク接続が必要です。  
> オフラインで軽いモデルを使いたい場合は、`--model` で明示指定するのが確実です。

---

## config で起動設定を変える

`eve-cli` は起動時に `~/.config/eve-cli/config` を読み込みます。  
毎回同じモデルや設定を使いたい場合は、このファイルを編集してください。

```ini
MODEL=qwen3:8b
SIDECAR_MODEL=qwen3:4b
OLLAMA_HOST=http://localhost:11434
CONTEXT_WINDOW=65536
PROFILE=auto
UI_THEME=normal
```

`--model` のようなコマンドラインオプションは、その回の起動だけ上書きします。  
長く使う設定は `config` に入れておくのがおすすめです。

Ollama Cloud を使う場合は、`OLLAMA_HOST` を `https://ollama.com/api` にし、API キーを環境変数で渡します。

```bash
export OLLAMA_API_KEY=your-ollama-api-key
eve-cli --ollama-host https://ollama.com/api --model qwen3.5:397b-cloud
```

補足:
- `eve-cli` は Ollama の native API を使うため、`OLLAMA_HOST` に `https://ollama.com` と `https://ollama.com/api` のどちらを入れても動くように正規化されます。
- 最近の Ollama docs では `ollama launch pi --model ...` のような統合エージェント導線がありますが、`eve-cli` は引き続き Ollama API に直接つなぐ構成です。

KAIROS を常用する場合は、`~/.config/eve-cli/kairos.json` またはプロジェクト単位の `.eve-cli/kairos.json` に設定を書けます。

```json
{
  "enabled": true,
  "mode": "observe",
  "heartbeat_seconds": 300,
  "active_hours": "workhours",
  "pr_watch": {
    "enabled": true
  },
  "dream": {
    "enabled": true,
    "schedule": "03:00"
  }
}
```

`observe` は通知のみ、`suggest` は承認待ちプランまで、`active` は allowlist にある低リスク操作のみ自動実行します。`/kairos` コマンド一覧は [コマンドリファレンス](docs/commands.md)、設定項目と保存先は [高度な機能](docs/advanced.md) を参照してください。

高度な設定項目は [高度な機能](docs/advanced.md) にまとめています。

---

## どこまで README で分かる？

README は「最初の入口」に絞ってあります。  
詳しい使い方は、次のドキュメントを見ると迷いにくいです。

| ドキュメント | 内容 | 対象 |
|------------|------|------|
| [はじめてガイド](docs/getting-started.md) | インストールから最初の一歩まで | 初心者 |
| [使い方ガイド](docs/usage.md) | 起動オプション、入力方法、権限確認、学習モードなど | 全ユーザー |
| [コマンドリファレンス](docs/commands.md) | スラッシュコマンドと AI ツール一覧 | 全ユーザー |
| [高度な機能](docs/advanced.md) | メモリ、Hooks、Skills、MCP、Agent Teams、環境変数 | 中〜上級者 |
| [トラブルシューティング](docs/troubleshooting.md) | よくある問題と解決策 | 困ったとき |

---

## リポジトリ構成

### ユーザー向けの主要ファイル

| パス | 役割 |
|------|------|
| `eve-coder.py` | EvE CLI のメイン実装です。対話モードやワンショット実行など、エージェント本体の処理を担います。 |
| `eve-cli.sh` | `eve-cli` コマンドの起動スクリプトです。設定読み込み、Ollama の起動確認、`eve-coder.py` の呼び出しを行います。 |
| `install.sh` | 公式インストーラーです。依存確認、モデル導入、CLI 配置まで自動で行います。 |
| `install-manifest.json` | インストーラーが使う検証用のチェックサム一覧です。配布ファイルの整合性確認に使われます。 |

### 開発・保守向け

| パス | 役割 |
|------|------|
| `tests/` | ループ実行、セキュリティ、メモリ互換、並列編集などの回帰テストです。 |
| `dev/` | 開発用スタンドアロンスクリプトです。セキュリティ診断、パフォーマンス検証、アドホックな動作確認に使います。 |
| `scripts/` | リリースや保守に使う補助スクリプトです。現在は `install-manifest.json` 更新用スクリプトを含みます。 |
| `00_Docs/` | 実装メモ、機能提案、作業記録などの内部ドキュメント置き場です。安定版の利用ガイドは `docs/` を参照してください。 |

補足: `.eve-cli/` 配下の `rules/`（パスSスコープルール）、`skills/`、`agents/`、`hooks.json`、`mcp.json` はチーム共有のため git 追跡されます。`channels/`（Bot トークン）や `context/`（キャッシュ）は gitignore されます。詳細は [高度な機能](docs/advanced.md) をご覧ください。

---

## ライセンス

MIT License — [ochyai/vibe-local](https://github.com/ochyai/vibe-local) をベースにしています。

## クレジット

- 原作: [ochyai/vibe-local](https://github.com/ochyai/vibe-local) by Yoichi Ochiai
- フォーク・拡張: [NPO法人 Everyone.Engineer](https://www.everyone.engineer)
