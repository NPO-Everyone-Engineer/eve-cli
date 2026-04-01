---
paths:
  - eve-coder.py
---
# 設計・実装ルール（eve-coder.py）

## 作業前に必ず行うこと
- CLAUDE.md のセクション構成表で挿入位置を確認する
- 変更対象を Read で読んでから設計・編集する
- `python3 -m pytest tests/ -v` でグリーンを確認してから着手する

## 設計フロー
新機能は既存クラスを変更せず新規クラスとして追加する
依存関係の順に配置する（依存先クラスを先に書く）
複雑な機能は「仕様確認 → テスト作成 → 実装」の順で進める

## コーディング制約
- ゼロ依存: Python 標準ライブラリのみ。pip install 禁止
- Python 3.8+ 互換: `match/case` 禁止、walrus `:=` は可
- エンコーディング: `open(..., encoding="utf-8", errors="replace")` を徹底
- パス操作: `os.path.islink()` で symlink チェック必須
- セキュリティ: OLLAMA_HOST は localhost のみ / シェルインジェクション防止

## 必須パターン（状態の永続化）
```python
# アトミック書き込み（EvolutionEngine._save と同じパターン）
tmp = path + ".tmp"
with open(tmp, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
os.replace(tmp, path)
```

## バックグラウンドスレッド
例外は必ずキャッチし、本体の対話ループに波及させない

## バージョン更新（変更時に必須）
テスト成功後に `__version__`（274行目付近）をインクリメント
バグ修正=PATCH / 新機能=MINOR / 破壊的変更=MAJOR
反映: `cp eve-coder.py ~/.local/lib/eve-cli/eve-coder.py`

## よく使う既存クラス（行番号）
- `Memory(14136)` — `add(content, category)` で記憶追加
- `EvolutionEngine(14268)` — 統計・insight 記録
- `ChannelManager(12393)` — Discord/Slack/Webhook 通知
- `ToolRegistry(12679)` / `PermissionMgr(13065)` — ツール実行・承認
- `AutoTestRunner(10971)` / `FileWatcher(11230)`
