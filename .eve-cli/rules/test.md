---
paths:
  - tests/
  - eve-coder.py
---
# テスト規約（eve-coder.py / tests/）

## インポートパターン（全テストで統一）
```python
import importlib.util, os, sys, tempfile, shutil, unittest
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPT_DIR)
spec = importlib.util.spec_from_file_location(
    "eve_coder", os.path.join(SCRIPT_DIR, "eve-coder.py"))
eve_coder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eve_coder)
MyClass = eve_coder.MyClass
```

## ファイル・クラス命名
- ファイル: `tests/test_{対象クラスをスネークケース}.py`
- クラス: `Test{ClassName}{Scenario}`（例: `TestMemoryPersistence`）

## setUp / tearDown（状態を持つクラス）
```python
def setUp(self):
    self.tmpdir = tempfile.mkdtemp()
def tearDown(self):
    shutil.rmtree(self.tmpdir, ignore_errors=True)
```

## 必須テストケース（クラスごとに揃える）
1. **初期状態** — デフォルト値・ディレクトリ生成が正しい
2. **正常系** — 基本操作が期待値を返す
3. **境界値** — 上限・下限・空文字・None 入力
4. **永続化** — 保存 → 再ロードで値が一致する
5. **エラー耐性** — ファイル破損・不正入力でクラッシュしない

## 設計品質を検証するテスト観点
- バックグラウンド処理が本体ループを止めない
- append-only データが通常手段で上書きできない
- 高リスク操作が policy 判定を通過しない
- 再インスタンス化後に state が復元される
- symlink を渡したとき安全に拒否する

## 実行
```bash
python3 -m pytest tests/ -v           # 全テスト
python3 -m pytest tests/test_foo.py   # 単一ファイル
python3 -m pytest tests/ -k "Memory"  # 絞り込み
```
