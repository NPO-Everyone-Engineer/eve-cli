---
description: "ユーザーが新機能のスケルトン生成を依頼したとき、または /scaffold コマンドを使用したとき（例: 「新しいAPIエンドポイントを作って」「新モジュール追加して」「機能のテンプレート作って」）"
allowed-tools: [Read, Write, Glob, Grep, Bash]
---
# スキャフォールド (Scaffold)

## 概要
新機能のスケルトン（ソースファイル + テスト + スキーマ）を一括生成します。
テスト漏れや構造の不整合を防ぎます。

## 使用方法
```
/custom scaffold <モジュール名> [フレームワーク]
```

## 生成手順（必ずこの順序で実行）

### Step 1: プロジェクト構造の把握
1. `Glob("**/**.py")` でプロジェクト構造を確認
2. 既存の命名規約、ディレクトリ構造を把握
3. `Read("tests/conftest.py")` があれば共有フィクスチャを確認

### Step 2: フレームワーク検出
プロジェクトのフレームワークを自動検出:

| 検出ファイル | フレームワーク | 生成テンプレート |
|-------------|-------------|----------------|
| `requirements.txt` に `fastapi` | FastAPI | route + Pydantic model + test |
| `requirements.txt` に `flask` | Flask | blueprint + test |
| `requirements.txt` に `django` | Django | view + model + serializer + test |
| `package.json` | Node.js | module + test |
| なし | Plain Python | module + test |

### Step 3: ファイル一括生成

**FastAPI の場合:**
```
src/{name}.py         — route 定義 + エラーハンドリング
src/schemas/{name}.py — Pydantic model (request/response)
tests/test_{name}.py  — 正常系 + 異常系 + エッジケース
```

**Plain Python の場合:**
```
src/{name}.py         — クラス/関数定義 + docstring + 型ヒント
tests/test_{name}.py  — 正常系 + 異常系 + エッジケース
```

### Step 4: テスト生成ルール（必須）
生成するテストには以下を必ず含める:
- **正常系**: 基本的な動作確認（最低1ケース）
- **異常系**: None入力、空文字、不正型（最低1ケース）
- **エッジケース**: 境界値、大量データ、Unicode（最低1ケース）
- **外部依存**: LLM, DB, HTTP API は `unittest.mock.patch` でモック
- **conftest.py**: 既存フィクスチャがあれば再利用（重複作成しない）

### Step 5: 検証
1. `Bash("python3 -c \"import py_compile; py_compile.compile('src/{name}.py', doraise=True)\"")` で構文チェック
2. `Bash("python3 -m pytest tests/test_{name}.py -v")` でテスト実行
3. 全テスト PASS を確認

## エラーハンドリングテンプレート

生成するコードには以下のパターンを必ず適用:

```python
# 外部 API 呼び出し
try:
    response = httpx.post(url, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
except (httpx.HTTPError, json.JSONDecodeError) as e:
    logger.error(f"API call failed: {e}")
    return fallback_value

# ユーザー入力
text = (request.get("text") or "").strip()
if not text:
    raise ValueError("Input text is required")

# LLM レスポンス
try:
    result = json.loads(llm_response)
except json.JSONDecodeError:
    logger.warning("Failed to parse LLM response, using fallback")
    result = {"error": "parse_failed"}
```

## 使用例

```bash
# FastAPI エンドポイントを作成
/custom scaffold user_profile fastapi

# Plain Python モジュールを作成
/custom scaffold data_processor

# 既存プロジェクト構造に合わせて自動検出
/custom scaffold notification
```
