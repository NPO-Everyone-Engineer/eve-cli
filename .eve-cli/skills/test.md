---
description: "ユーザーがテスト生成・テスト作成を依頼したとき、または /test コマンドを使用したとき（例: 「テストを書いて」「テストを追加して」「カバレッジを上げて」）"
allowed-tools: [Read, Write, Glob, Grep, Bash]
---
# テスト生成 (Test Generation)

## 概要
指定されたファイルの包括的なユニットテストを自動生成します。

## 使用方法
```
/custom test <ファイル名>
```

## 生成手順（必ずこの順序で実行）

### Step 1: 既存テスト環境の把握
1. `Read("tests/conftest.py")` が存在するなら必ず読む → 共有フィクスチャを再利用
2. `Glob("tests/test_*.py")` で既存テストのスタイルを確認（クラスベース vs 関数ベース）
3. 既存テストで使われているモックパターン（FakeSession 等）を把握

### Step 2: 対象ファイルの分析
1. `Read` で対象ファイルを読む
2. 全パブリック関数/メソッドをリストアップ
3. 外部依存（import）を特定 → モック対象を決定
4. 入力パラメータの型と None になりうる箇所を確認

### Step 3: テスト生成ルール

#### 必須テストケース（各関数/メソッドに対して）
| カテゴリ | 最低数 | 内容 |
|---------|-------|------|
| 正常系 | 1+ | 基本的な動作確認、期待される入出力 |
| 異常系 | 1+ | None入力、空文字、不正型、例外発生 |
| エッジケース | 1+ | 境界値、空リスト、Unicode文字、大量データ |

#### モック一貫性ルール（必須）
- **conftest.py に既存フィクスチャがあれば必ず再利用する**（重複作成禁止）
- **外部 HTTP 呼び出し**: モジュールレベルで `unittest.mock.patch` を使用
- **LLM 呼び出し**: レスポンスを固定文字列でモック
- **DB 操作**: インメモリ DB またはモックを使用
- **ファイル I/O**: `tmp_path` フィクスチャまたは `tempfile` を使用
- **時間依存**: `unittest.mock.patch("time.time", return_value=...)` でモック

```python
# WRONG: テストごとに FakeSession を定義
class TestFoo:
    class FakeSession:  # ← conftest.py と重複！
        pass

# RIGHT: conftest.py のフィクスチャを使う
class TestFoo:
    def test_something(self, fake_session):  # ← conftest.py から
        ...
```

#### エラーハンドリングのテスト
```python
# 外部 API モックのテンプレート
@patch("src.extractor.httpx.post")
def test_api_failure_handling(self, mock_post):
    """外部 API が失敗した場合のフォールバック動作"""
    mock_post.side_effect = httpx.HTTPError("Connection refused")
    result = extractor.extract(data)
    assert result == fallback_value  # エラー時もクラッシュしない

# None 入力のテスト
def test_none_input(self):
    """None が渡された場合に適切にハンドリングする"""
    result = process(None)
    assert result == "" or result is None  # クラッシュしない

# JSON パース失敗のテスト
@patch("src.extractor.llm_call")
def test_invalid_json_response(self, mock_llm):
    """LLM が不正な JSON を返した場合"""
    mock_llm.return_value = "not valid json {{"
    result = extractor.extract(data)
    assert result is not None  # フォールバック値が返る
```

### Step 4: 検証
1. `Bash("python3 -m pytest tests/test_{name}.py -v")` でテスト実行
2. 全テスト PASS を確認
3. 失敗があれば修正して再実行

## 出力先
- デフォルト: `tests/test_<filename>.py`
- `tests/` ディレクトリがない場合は自動作成
- `tests/__init__.py` がない場合は自動作成
- 既存ファイルがある場合は上書き確認

## Gotchas
- eve-coder.py のテストは単体インポートが困難（単一ファイル＋副作用）
- テスト対象コード自体はゼロ依存だが、テストコードで外部ライブラリ（pytest, mock）は OK
- macOS の readline は libedit のため、readline 関連テストは OS 依存に注意
