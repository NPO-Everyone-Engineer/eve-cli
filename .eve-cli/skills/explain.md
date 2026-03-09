---
description: Explain how code works
allowed-tools: [Read, Glob, Grep]
---
# コード解説 (Code Explain)

## 概要
コードの仕組みを詳細に解説します。

## 使用方法
```
/custom explain <ファイル名またはコード>
```

## 解説内容

以下の項目を段階的に解説します：

1. **実行フロー**: メインの実行流れ
2. **主要関数/クラス**: 使用されている重要な関数とクラス
3. **データ構造**: 使用されているデータ構造
4. **デザインパターン**: 適用されているデザインパターン

## 出力形式

- 初心者でも理解できる簡単な言葉を使用
- 段階的にロジックを分解
- 具体的なコード例を示す

## 使用例

```bash
# ファイルの解説を依頼
/custom explain src/main.py

# 特定の機能について解説
/custom explain 認証機能の仕組み
```

## 対象ファイル

- Python (.py)
- JavaScript/TypeScript (.js, .ts)
- Go (.go)
- Rust (.rs)
- Ruby (.rb)
- Java (.java)

## ヒント

- 特定の行範囲を指定するとより詳細な解説が可能
- 複数のファイルをまたぐ解説も可能
- エラーメッセージと一緒に依頼すると原因解説も受けられる
