# はじめてガイド

EvE CLI を初めて使う方のための、ステップバイステップガイドです。

---

## 必要なもの

| 必要なもの | 説明 |
|-----------|------|
| **Mac または Linux** | Windows は Git Bash / WSL 経由で対応 |
| **Python 3.8 以上** | Mac / Linux には最初から入っていることが多い |
| **Ollama** | AI モデルを動かすエンジン（インストーラーが案内します） |

### Python が入っているか確認する

```bash
python3 --version
```

`Python 3.8.x` 以上が表示されれば OK です。表示されない場合は [python.org](https://www.python.org/downloads/) からインストールしてください。

### Ollama とは？

Ollama は、ローカルモデルとクラウドモデルの両方を扱える AI 実行基盤です。EvE CLI は Ollama の API を通じて AI を利用します。

- 公式サイト: [ollama.com](https://ollama.com/)
- 無料で使えます
- インストーラーが自動でダウンロードを案内します

---

## インストール

### 方法 1: ワンライナーインストール（推奨）

```bash
curl -fsSL https://raw.githubusercontent.com/NPO-Everyone-Engineer/eve-cli/main/install.sh -o install.sh && bash install.sh
```

インストーラーが以下を自動で行います：

1. Python のバージョン確認
2. Ollama のインストール確認（未インストールなら案内を表示）
3. AI モデルのダウンロード（初回は数分かかります）
4. `eve-cli` コマンドのセットアップ

> インストーラーは日本語・英語・中国語に対応しています。システムの言語設定を自動検出します。

### 方法 2: 手動インストール

```bash
git clone https://github.com/NPO-Everyone-Engineer/eve-cli.git
cd eve-cli
chmod +x eve-coder.py eve-cli.sh
ln -s $(pwd)/eve-cli.sh /usr/local/bin/eve-cli
```

手動の場合は、別途 [Ollama のインストール](https://ollama.com/) が必要です。ローカルモデルを使うなら AI モデルのダウンロードも行ってください：

```bash
ollama pull qwen3.5:9b
```

Ollama Cloud を使う場合は、ローカルにモデルを pull しなくても構いません。API キーを設定して `OLLAMA_HOST` を切り替えます：

```bash
export OLLAMA_API_KEY=your-ollama-api-key
eve-cli --ollama-host https://ollama.com/api --model glm-5:cloud
```

---

## 起動してみよう

```bash
eve-cli
```

バナーが表示されたら準備完了です。`>` プロンプトに日本語で話しかけてください。

---

## 最初にやってみること

### 1. あいさつしてみる

```
> こんにちは！何ができるの？
```

AI が自己紹介と、できることの一覧を教えてくれます。

### 2. 簡単なプログラムを作ってもらう

```
> Hello World を表示する Python スクリプトを作って
```

AI がファイルを作成し、実行まで行います。途中で「このファイルを作成していいですか？」と確認が入るので、`y` を押して許可してください。

### 3. ファイルの中身を聞いてみる

```
> @hello.py このファイルの内容を説明して
```

`@ファイル名` と書くと、そのファイルの内容を AI に自動で渡せます。

### 4. 間違いを直してもらう

```
> @hello.py にバグがあるので直して
```

AI がファイルを読み、問題を見つけて修正します。

---

## 覚えておきたい基本操作

| 操作 | やり方 |
|------|--------|
| メッセージを送信 | 入力して **空 Enter**（何も入力せず Enter） |
| 改行する | **Enter** |
| ファイルを添付 | `@ファイル名`（例: `@src/app.py`） |
| AI を途中で止める | **ESC** キー |
| コマンドを使う | `/` で始まる（例: `/help`） |
| 終了する | `/exit` または Ctrl+D |

---

## よく使うコマンド

| コマンド | 説明 |
|---------|------|
| `/help` | ヘルプを表示 |
| `/clear` | 会話をリセット |
| `/commit` | AI がコミットメッセージを作成してコミット |
| `/undo` | 直前のファイル変更を元に戻す |
| `/status` | セッション情報を表示 |

全コマンドの一覧は [コマンドリファレンス](commands.md) をご覧ください。

---

## モデルの選び方

PC のメモリ（RAM）に合わせてモデルを選んでください。

| メモリ | おすすめモデル | 特徴 |
|-------|-------------|------|
| 8GB | `qwen3.5:9b` | 軽量。動作は少し遅め |
| 16GB | `qwen3.5:14b` | バランスが良い。多くの人におすすめ |
| 32GB+ | `qwen3.5:32b` | 高性能。複雑なタスクにも対応 |

```bash
eve-cli --model qwen3.5:14b
```

メモリの確認方法：
- **Mac**: 左上の Apple メニュー → 「この Mac について」
- **Linux**: `free -h` コマンド

コーディング用途では、`CONTEXT_WINDOW=65536` 以上を推奨します。EvE CLI の既定値も 64K に合わせています。

---

## うまくいかないとき

[トラブルシューティング](troubleshooting.md) に、よくある問題と解決策をまとめています。

---

## 次のステップ

- [使い方ガイド](usage.md) — 入力方法や機能の詳しい使い方
- [コマンドリファレンス](commands.md) — 全コマンド・ツールの一覧
- [高度な機能](advanced.md) — メモリ、Hooks、MCP などのカスタマイズ
