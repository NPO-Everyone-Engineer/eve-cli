# EvE CLI — Everyone.Engineer Coding Agent

**EvE CLI** は、[NPO法人 Everyone.Engineer](https://www.everyone.engineer) が提供するオープンソースのAIコーディングエージェントです。

[ochyai/vibe-local](https://github.com/ochyai/vibe-local) をベースに、ローカルLLMに加えてOllamaクラウドモデルにも対応しています。

> **「プログラミング未経験でも、AIと一緒にコードが書ける」** — それが EvE CLI の目指す世界です。

**バージョン**: 2.3.0

---

## 目次

- [特徴](#特徴)
- [クイックスタート](#クイックスタート)
- [インストール](#インストール)
- [基本的な使い方](#基本的な使い方)
- [推奨環境](#推奨環境)
- [ドキュメント](#ドキュメント)
- [ライセンス](#ライセンス)
- [クレジット](#クレジット)

---

## 特徴

### 基本機能

- **ローカル + クラウド**: Ollamaのローカルモデル（`qwen3.5:9b` 等）とクラウドモデル（`qwen3.5:397b-cloud`）を自由に切り替え
- **自動プロファイル切替**: ネットワーク状態を検知し、オンライン/オフラインで最適なモデルを自動選択
- **ゼロ依存**: Python標準ライブラリのみ使用。pip install は一切不要
- **日本語対応**: 日本語・英語・中国語でやり取り可能

### AIエージェント機能

- **18個の内蔵ツール**: Bash実行、ファイル操作、マルチファイル一括編集、Web取得、サブエージェント、タスク管理など
- **Plan/Actモード**: まず計画を立て（Plan）、承認後に実行（Act）する安全な段階的遷移
- **Agent Teams**: 複数のAIエージェントがチームを組んで大きなタスクを分担処理
- **Extended Thinking**: AIの思考過程を表示（対応モデルのみ）
- **エラー自動修復**: コマンドやテストが失敗した場合、AIが自動で原因を分析して修正を試みる
- **自動コンパクション**: 会話が長くなると自動で要約・圧縮して、コンテキスト上限を超えないように管理
- **ループモード**: AI が完了シグナルを出力するまでプロンプトを自動再実行（`--loop` フラグ）
- **学習モード**: コードやエラーの解説を AI が対話的に説明（`--learn` フラグ・難易度調整可能）

### 開発支援

- **コンテキスト自動収集**: 起動時にgit履歴、ディレクトリ構造、プロジェクト種別を自動検出してAIに提供
- **コミットメッセージ自動生成**: `/commit` で差分からConventional Commits形式のメッセージをAIが自動提案
- **テスト自動生成**: `/gentest` で指定ファイルのユニットテストをAIが自動生成
- **コードインテリジェンス**: 関数定義・参照の検索、シンボルインデックス（Python, JS/TS, Go, Rust, Ruby, Java対応）
- **GitHub連携**: `/pr` でプルリクエスト作成・管理、`/gh` でGitHub CLIコマンド実行

### UX（使いやすさ）

- **Gitチェックポイント**: ファイル変更前に自動バックアップ。いつでも `/rollback` で元に戻せる
- **シンタックスハイライト**: コードブロックのキーワード/文字列/コメントを色分け表示
- **リッチdiffプレビュー**: ファイル編集時に変更箇所を赤/緑で詳細に表示
- **@file記法**: `@src/main.py` でファイル内容をメッセージに自動添付
- **Tab補完**: スラッシュコマンド、ファイルパス、@fileの自動補完
- **画像添付**: ドラッグ&ドロップ、クリップボード貼り付け、`/image` コマンド
- **MCP統合**: JSON-RPC 2.0によるツール連携（Playwright等）
- **メモリ（長期記憶）**: プロジェクト規約やユーザーの好みをセッション跨ぎで記憶
- **パーミッション永続化**: ツールの許可・拒否設定をファイルに保存し、次回起動時も有効
- **レスポンスキャッシュ**: 同じ問い合わせに対する応答をキャッシュして高速化

---

## クイックスタート

初めての方は、以下の3ステップで始められます。

### ステップ1: インストール

```bash
curl -fsSL https://raw.githubusercontent.com/NPO-Everyone-Engineer/eve-cli/main/install.sh -o install.sh
bash install.sh
```

### ステップ2: 起動

```bash
eve-cli
```

### ステップ3: 話しかける

```
> Hello Worldを作って
```

これだけです！ AIが自動でファイルを作成し、実行まで行います。

---

## インストール

### ダウンロードして実行（推奨）

```bash
curl -fsSL https://raw.githubusercontent.com/NPO-Everyone-Engineer/eve-cli/main/install.sh -o install.sh
bash install.sh
```

これだけで以下が自動で行われます:

1. Python 3.8+ の確認
2. Ollama のインストール確認
3. 推奨モデルのダウンロード
4. `eve-cli` コマンドのセットアップ

### 手動インストール

```bash
# リポジトリをクローン
git clone https://github.com/NPO-Everyone-Engineer/eve-cli.git
cd eve-cli

# 実行権限を付与
chmod +x eve-coder.py eve-cli.sh

# パスに追加（どこからでも実行可能に）
ln -s $(pwd)/eve-cli.sh /usr/local/bin/eve-cli
```

### 前提条件

| ソフトウェア | バージョン | 説明 |
|------------|-----------|------|
| Python | 3.8以上 | macOS/Linuxには通常プリインストール |
| [Ollama](https://ollama.com/) | 最新版 | AIモデルを動かすためのエンジン |

> **Ollamaって何？**
> Ollamaは、AIモデルをあなたのPC上で動かすためのソフトウェアです。[ollama.com](https://ollama.com/) からインストールできます。

---

## 基本的な使い方

### 対話モード（一番よく使う）

```bash
eve-cli
```

起動すると対話画面が表示されます。日本語で自由に話しかけてください。

```
> Pythonで電卓アプリを作って
> このファイルのバグを直して @src/app.py
> テストを書いて実行して
```

### ワンショットモード（1回だけ質問）

```bash
eve-cli -p "Hello Worldを作って"
```

結果だけ受け取りたい場合に便利です。CI/CD スクリプトでも使えます。

### 学習モード（コード解説）

```bash
# 学習モードで起動（難易度レベル 1-5）
eve-cli --learn
eve-cli --learn --level 3

# 対話中に解説レベルを変更
> /learn level 4
```

### Skills（カスタムコマンド）

```bash
# コード解説
/custom explain src/main.py

# コードレビュー
/custom review src/

# テスト生成
/custom test calculator.py
```

### よく使うオプション

```bash
# ローカルモデルを指定して起動（標準）
eve-cli --model qwen3.5:9b

# ローカルモデル（高性能・メモリ16GB以上）
eve-cli --model qwen3.5:14b

# クラウドモデルを使う（最高性能・Ollama有料版）
eve-cli --model qwen3.5:397b-cloud

# サイドカーモデルを設定（会話要約・コンパクション用の軽量モデル）
EVE_CLI_SIDECAR_MODEL=qwen3.5:3b eve-cli

# 自動許可モード（毎回の確認をスキップ）
eve-cli -y

# 前回のセッションを再開
eve-cli --resume

# プロファイル指定（ネットワーク環境に合わせて）
eve-cli --profile offline
eve-cli --profile online

# 出力形式を指定（スクリプト連携用）
eve-cli -p "バージョンを教えて" --output-format json

# 学習モードで起動（コードの解説を受けながら開発）
eve-cli --learn
eve-cli --learn --level 3  # 難易度調整（1-5）
```

---

## 推奨環境

| 環境 | メモリ | 推奨モデル | 備考 |
|------|-------|----------|------|
| Apple Silicon Mac | 96GB+ | gpt-oss:120b | 最高性能 |
| Apple Silicon Mac | 16GB | qwen3:8b | 標準的 |
| Intel/Windows/Linux | 16GB+ | qwen3:8b | 標準的 |
| クラウドモデル利用時 | 制限なし | qwen3.5:397b-cloud | Ollama有料版 |

> **画像認識**を使う場合は、ビジョン対応モデル（`llava`, `llama3.2-vision`, `gemma3` 等）が必要です。

---

## ドキュメント

詳細な情報は以下のドキュメントを参照してください。

| ドキュメント | 内容 |
|------------|------|
| [使い方ガイド](docs/usage.md) | 入力方法・コマンド一覧・ツール・パーミッション・安全性・テスト生成・GitHub連携など |
| [高度な機能](docs/advanced.md) | メモリ・プロジェクト設定・プロファイル・Hooks・MCP・Agent Teams・環境変数など |

---

## ライセンス

MIT License — [ochyai/vibe-local](https://github.com/ochyai/vibe-local) をベースにしています。

## クレジット

- 原作: [ochyai/vibe-local](https://github.com/ochyai/vibe-local) by Yoichi Ochiai
- フォーク・拡張: [NPO法人 Everyone.Engineer](https://www.everyone.engineer)
