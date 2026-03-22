---
description: "ユーザーがコードレビュー・品質チェックを依頼したとき、または /review コマンドを使用したとき（例: 「レビューして」「セキュリティチェックして」「PR前に確認して」）"
allowed-tools: [Read, Glob, Grep, Bash]
---
# コードレビュー (Code Review)

## 概要
コードを包括的にレビューし、テストカバレッジ・型安全性・エラーハンドリングを含む品質チェックを実行します。

## 使用方法
```
/custom review [ファイル名またはディレクトリ]
```

## レビュー手順（必ずこの順序で実行）

### Phase 1: テストカバレッジ検査
1. `Glob("src/**/*.py")` or `Glob("**/*.py")` でソースファイル一覧を取得
2. `Glob("tests/test_*.py")` でテストファイル一覧を取得
3. **テストが存在しないモジュールを検出**して報告
4. 各テストファイルを Read し、正常系・異常系・エッジケースが揃っているか確認

### Phase 2: エラーハンドリング検査
1. `Grep("json.loads|json.load")` → try/except で囲まれているか確認
2. `Grep("requests\.|httpx\.|urllib\.|urlopen")` → 外部 API 呼び出しに例外処理があるか
3. `Grep("\.get\(")` → 戻り値が None になりうる箇所で None チェックがあるか
4. `Grep("open\(")` → encoding="utf-8" が指定されているか

### Phase 3: 型安全性検査
1. `Grep("async def")` → async 関数が await で呼ばれているか（同期呼び出ししていないか）
2. `Grep("def.*->")` → 戻り値型ヒントと実際の return 値が一致しているか
3. `Grep("Optional\[|None")` → Optional な値に対する None チェックがあるか

### Phase 4: セキュリティ検査
1. `Grep("/Users/|/home/|C:\\\\Users")` → ハードコードされた絶対パスがないか
2. `Grep("api_key|password|secret|token")` → シークレットのハードコード
3. `Grep("eval\(|exec\(")` → 危険な動的実行
4. `Grep("subprocess.*shell=True")` → シェルインジェクションリスク

### Phase 5: モック一貫性検査（テストファイルのみ）
1. `Read("tests/conftest.py")` が存在する場合、共有フィクスチャを確認
2. 各テストファイルで conftest.py と重複するフィクスチャ（FakeSession 等）がないか
3. 外部 HTTP 呼び出しのモックが一貫しているか

## 出力形式

| 深刻度 | カテゴリ | ファイル:行 | 問題 | 修正案 |
|--------|---------|-----------|------|--------|

- **Critical**: セキュリティ脆弱性、データ損失リスク
- **High**: テスト欠如、None チェック漏れ、async/sync 不一致
- **Medium**: エラーハンドリング不足、encoding 指定漏れ
- **Low**: コードスタイル、命名規則

## Gotchas
- eve-coder.py 固有: symlink チェック必須、OLLAMA_HOST の localhost 制限、ゼロ依存
- Python 3.8+ 互換性: match/case (3.10+) は使用不可
- encoding="utf-8", errors="replace" の漏れは High 扱い
