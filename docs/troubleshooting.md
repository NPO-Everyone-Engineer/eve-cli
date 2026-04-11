# トラブルシューティング

EvE CLI でよくある問題と、その解決策をまとめています。

---

## 目次

- [インストールで困ったとき](#インストールで困ったとき)
- [起動で困ったとき](#起動で困ったとき)
- [使用中に困ったとき](#使用中に困ったとき)
- [モデル・パフォーマンス](#モデルパフォーマンス)
- [それでも解決しないとき](#それでも解決しないとき)

---

## インストールで困ったとき

### 「Python が見つからない」と表示される

```bash
python3 --version
```

バージョンが表示されない場合、Python がインストールされていません。

**Mac の場合：**

```bash
xcode-select --install
```

これで Apple の開発者ツールとともに Python 3 がインストールされます。

**Linux（Ubuntu/Debian）の場合：**

```bash
sudo apt update && sudo apt install python3
```

### 「Ollama が見つからない」と表示される

Ollama をインストールしてください：

- **Mac**: [ollama.com](https://ollama.com/) からアプリをダウンロード
- **Linux**: `curl -fsSL https://ollama.com/install.sh | sh`

インストール後、Ollama が起動していることを確認：

```bash
ollama --version
```

### `eve-cli` コマンドが見つからない

インストーラーが PATH に追加したパスが反映されていない可能性があります。

```bash
source ~/.zshrc
```

または新しいターミナルを開いてください。それでもダメな場合：

```bash
ls ~/.local/bin/eve-cli
```

ファイルが存在するなら、PATH に追加してください：

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

---

## 起動で困ったとき

### 「Ollama に接続できない」エラー

Ollama が起動しているか確認してください：

```bash
ollama list
```

エラーが出る場合は Ollama を起動します：

- **Mac**: アプリケーションフォルダから Ollama を起動
- **Linux**: `ollama serve &`

Ollama Cloud を使っている場合は、ローカル起動ではなく接続先を確認してください：

```bash
echo $OLLAMA_API_KEY
eve-cli --ollama-host https://ollama.com/api --model glm-5:cloud
```

`OLLAMA_HOST=https://ollama.com/api` と API キーが正しいかを確認してください。

### 「モデルが見つからない」エラー

指定したモデルがダウンロード済みか確認：

```bash
ollama list
```

一覧にない場合はダウンロード：

```bash
ollama pull qwen3.5:9b
```

Ollama Cloud を使っている場合は `pull` ではなく、モデル名・契約・接続先を確認してください。

### 起動が異常に遅い

初回起動時はモデルの読み込みに時間がかかります（30秒〜数分）。2回目以降は高速になります。

メモリが不足している場合も遅くなります。PC のメモリに合ったモデルを選んでください：

| メモリ | 推奨モデル |
|-------|----------|
| 8GB | `qwen3.5:9b` |
| 16GB | `qwen3.5:14b` |
| 32GB+ | `qwen3.5:32b` |

---

## 使用中に困ったとき

### AI の応答が途中で切れる

コンテキストウィンドウが一杯になっている可能性があります：

```
> /compact
```

会話を圧縮して続行できます。または `/clear` で新しい会話を始めてください。

コーディング用途では `CONTEXT_WINDOW=65536` 以上がおすすめです。

### ファイルを間違って変更された

すぐに元に戻せます：

```
> /undo
```

より前の状態に戻したい場合：

```
> /rollback
```

### 「パーミッションが拒否されました」と表示される

ツールの実行を誤って拒否設定にした可能性があります。パーミッション設定をリセット：

```bash
rm ~/.config/eve-cli/permissions.json
```

次回起動時に再度確認が表示されます。

### 画像を送れない

画像認識にはビジョン対応モデルが必要です：

```bash
ollama pull gemma3
eve-cli --model gemma3
```

対応モデル例: `llava`, `llama3.2-vision`, `gemma3`

### Tab 補完が効かない

Mac の場合、libedit と readline の互換性問題の可能性があります。これは既知の制限です。基本的な補完（ファイルパス、スラッシュコマンド）は動作します。

---

## モデル・パフォーマンス

### AI の回答品質が低い

より大きなモデルに切り替えてみてください：

```
> /model qwen3.5:14b
```

または、指示をより具体的に書いてみてください。「いい感じにして」より「関数 `calculate()` の引数チェックを追加して」の方が良い結果が得られます。

### メモリ不足で PC が重くなる

モデルがメモリを多く使っている可能性があります。軽量モデルに切り替えてください：

```bash
eve-cli --model qwen3.5:9b
```

使っていない Ollama モデルを削除してメモリを解放することもできます：

```bash
ollama list
ollama rm 使わないモデル名
```

### クラウドモデルを使いたい

Ollama Cloud を使う場合は、ホストと API キーを設定してください：

```bash
export OLLAMA_API_KEY=your-ollama-api-key
eve-cli --ollama-host https://ollama.com/api --model glm-5:cloud
```

ネットワーク接続が必要です。プロファイル機能でオンライン/オフラインの自動切替もできます。詳しくは [高度な機能](advanced.md) を参照してください。

---

## それでも解決しないとき

### デバッグモードで詳細を確認

```bash
EVE_CLI_DEBUG=1 eve-cli
```

詳細なログが表示され、問題の特定に役立ちます。

### GitHub で報告

解決しない問題は、GitHub Issue で報告してください：

- [https://github.com/NPO-Everyone-Engineer/eve-cli/issues](https://github.com/NPO-Everyone-Engineer/eve-cli/issues)

報告時に以下の情報を含めると助かります：

- OS とバージョン（`uname -a`）
- Python バージョン（`python3 --version`）
- Ollama バージョン（`ollama --version`）
- EvE CLI バージョン（`eve-cli --version`）
- エラーメッセージの全文
- 再現手順
