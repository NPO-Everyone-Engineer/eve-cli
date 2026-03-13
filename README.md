# EvE CLI — Everyone.Engineer Coding Agent

**EvE CLI** は、AIと一緒にコードが書けるオープンソースのコーディングエージェントです。

[NPO法人 Everyone.Engineer](https://www.everyone.engineer) が提供しています。

> **「プログラミング未経験でも、AIと一緒にコードが書ける」** — それが EvE CLI の目指す世界です。

**バージョン**: 2.4.2

---

## 30秒で始める

```bash
curl -fsSL https://raw.githubusercontent.com/NPO-Everyone-Engineer/eve-cli/main/install.sh -o install.sh && bash install.sh
```

```bash
eve-cli
```

```
> Hello Worldを作って
```

これだけです。AIが自動でファイルを作成し、実行まで行います。

> 詳しいインストール手順は [はじめてガイド](docs/getting-started.md) をご覧ください。

---

## 特徴

### AI がコードを書いてくれる

日本語で「こういうアプリを作って」と伝えるだけで、AIがファイルの作成・編集・実行をすべて行います。

```
> Pythonで電卓アプリを作って
> このファイルのバグを直して @src/app.py
> テストを書いて実行して
```

### ネット不要・完全無料

[Ollama](https://ollama.com/) を使って、あなたのPC上でAIが動きます。クラウドAPIの契約は不要です。ネットがつながる環境ならクラウドモデルも使えます。

### インストールかんたん

Python の `pip install` は不要。インストーラーが Ollama のセットアップからモデルのダウンロードまですべて自動で行います。

### 安全設計

ファイルの書き込みやコマンド実行の前に必ず確認を求めます。自動バックアップ機能で、いつでも元に戻せます。

---

## 主な機能

| カテゴリ | 機能 |
|---------|------|
| **AI エージェント** | 18個の内蔵ツール、Plan/Act モード、Agent Teams、エラー自動修復 |
| **開発支援** | コミットメッセージ自動生成、テスト自動生成、GitHub 連携、コードインテリジェンス |
| **使いやすさ** | 日本語対応、Tab 補完、画像添付、シンタックスハイライト、リッチ diff |
| **カスタマイズ** | メモリ（長期記憶）、Skills、Hooks、MCP 統合、プロファイル自動切替 |
| **安全性** | パーミッション管理、Git チェックポイント、自動バックアップ |

---

## 推奨環境

| 環境 | メモリ | 推奨モデル |
|------|-------|----------|
| Apple Silicon Mac | 32GB+ | `qwen3.5:32b` |
| Apple Silicon Mac / Linux | 16GB | `qwen3.5:14b` |
| 省メモリ環境 | 8GB | `qwen3.5:9b` |
| クラウドモデル | 制限なし | `qwen3.5:397b-cloud` |

```bash
eve-cli --model qwen3.5:14b
```

### config で起動設定を変更する

`eve-cli` は起動時に `~/.config/eve-cli/config` を読み込みます。メインモデル、サイドカーモデル、Ollama の接続先を固定したい場合は、このファイルを編集してください。

```ini
MODEL=qwen3.5:14b
SIDECAR_MODEL=qwen3:4b
OLLAMA_HOST=http://localhost:11434
```

`--model` オプションはその回のメインモデルだけを切り替えます。サイドカーも含めて普段の設定を変えたいときは、`config` を使うのが確実です。ほかの設定項目は [高度な機能](docs/advanced.md) にまとめています。

---

## ドキュメント

| ドキュメント | 内容 | 対象 |
|------------|------|------|
| [はじめてガイド](docs/getting-started.md) | インストールから最初の一歩まで | 初心者 |
| [使い方ガイド](docs/usage.md) | 入力方法・機能の詳しい使い方 | 全ユーザー |
| [コマンドリファレンス](docs/commands.md) | スラッシュコマンド・ツール一覧 | 全ユーザー |
| [高度な機能](docs/advanced.md) | メモリ・Hooks・MCP・Agent Teams・環境変数 | 中〜上級者 |
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
| `scripts/` | リリースや保守に使う補助スクリプトです。現在は `install-manifest.json` 更新用スクリプトを含みます。 |
| `00_Docs/` | 実装メモ、機能提案、作業記録などの内部ドキュメント置き場です。安定版の利用ガイドは `docs/` を参照してください。 |

補足: `.eve-cli/` のようなローカル設定や Skills / Hooks / MCP 連携の詳細は、[高度な機能](docs/advanced.md) にまとめています。

---

## ライセンス

MIT License — [ochyai/vibe-local](https://github.com/ochyai/vibe-local) をベースにしています。

## クレジット

- 原作: [ochyai/vibe-local](https://github.com/ochyai/vibe-local) by Yoichi Ochiai
- フォーク・拡張: [NPO法人 Everyone.Engineer](https://www.everyone.engineer)
