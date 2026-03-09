---
description: Generate unit tests
allowed-tools: [Read, Write, Glob]
---
# テスト生成 (Test Generation)

## 概要
指定されたファイルの包括的なユニットテストを自動生成します。

## 使用方法
```
/custom test <ファイル名>
```

## 生成されるテスト

### 1. 通常ケース (Normal Cases)
- 基本的な機能の動作確認
- 期待される入力に対する正常な出力

### 2. エッジケース (Edge Cases)
- 境界値テスト
- 最小値/最大値
- 空の入力
- null/undefined 値

### 3. エラーケース (Error Cases)
- 無効な入力
- 予期せぬデータ型
- リソース不足
- ネットワークエラー

## 要件

- **テストフレームワーク**: プロジェクトで使用されているフレームワークに従う
  - Python: unittest, pytest
  - JavaScript: Jest, Mocha
  - Go: testing パッケージ
  - その他：プロジェクトの規約に従う

- **ドキュメント**: 各テストに docstring/comment を含む

- **スタイル**: 既存のテストファイルのスタイルを踏襲

- **カバレッジ**: できるだけ多くのコードパスをカバー

## 出力形式

```python
# 例：Python の場合
import unittest
from src.calculator import Calculator

class TestCalculator(unittest.TestCase):
    """Calculator クラスのユニットテスト"""
    
    def setUp(self):
        """各テスト前のセットアップ"""
        self.calc = Calculator()
    
    def test_add_normal(self):
        """通常の加算テスト"""
        result = self.calc.add(2, 3)
        self.assertEqual(result, 5)
    
    def test_add_edge_case_zero(self):
        """エッジケース：0 の加算"""
        result = self.calc.add(0, 0)
        self.assertEqual(result, 0)
    
    def test_add_error_negative(self):
        """エラーケース：負の数の入力"""
        with self.assertRaises(ValueError):
            self.calc.add(-1, 5)

if __name__ == '__main__':
    unittest.main()
```

## 使用例

```bash
# ファイルのテストを生成
/custom test src/calculator.py

# 複数のファイル（個別に実行）
/custom test src/auth.py
/custom test src/api.py
```

## 自動実行

テスト生成後、以下のコマンドで実行可能：

```bash
# Python の場合
python -m pytest tests/test_calculator.py

# または
python -m unittest tests/test_calculator.py
```

## ヒント

- 既存のテストディレクトリ構造を自動的に作成
- 依存関係がある場合はモックを使用
- 時間依存のテストは現在時刻をモック化
- データベース操作はインメモリ DB またはトランザクションを使用

## 出力先

- デフォルト：`tests/test_<filename>.py`
- 既存ファイルがある場合は上書き確認
- `tests/` ディレクトリがない場合は自動作成
