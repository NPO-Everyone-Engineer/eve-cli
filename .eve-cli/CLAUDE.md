# EvECLI

## Project Overview
- **Language**: Unknown
- **Repository**: git@github.com:NPO-Everyone-Engineer/eve-cli.git
- **Main branch**: main

## Directory Structure
```
.eve-cli/
00_Docs/
CODE_QUALITY_REPORT.md
INTEGRATION_TEST_PLAN.md
LICENSE
README.md
TEST_QUALITY_REPORT.md
dev/
docs/
eve-cli.cmd
eve-cli.ps1
eve-cli.sh
eve-coder.py
install-manifest.json
install.cmd
install.ps1
install.sh
locales/
scripts/
tests/
```

## Instructions for AI
- Follow existing code style and conventions
- Write tests for new features
- Use absolute paths for file operations
- Prefer project-local skills when they match the task:
  - `design` for planning and impact analysis before implementation
  - `implement` for careful changes with tests
  - `bugfix` for root-cause debugging and regression prevention
  - `refactor` for behavior-preserving cleanup
  - `review-lite` for fast risk-focused review

## Design Quality Rules — CRITICAL

### 実装前の準備（必須）
- 対象ファイル・呼び出し元・テストの最低 3 箇所を Read してから実装を開始する
- 既存の命名規則・エラーハンドリング・インデントを把握し、それに合わせる
- 2 ファイル以上を変更するタスクは計画を簡潔に述べてから着手する

### 関数設計
- 1 関数 = 1 責務。関数名だけで動作が分かること
- 関数は 30 行以内を目安。超える場合はヘルパーに分割
- 引数は 5 個以内。超える場合は dict でまとめる
- 略語を避ける: `cfg` → `config`, `msg` → `message`
- bool 変数は `is_`, `has_`, `can_` で始める

### 段階的実装（一度に書きすぎない）
- 50 行以上を一度に書かない。骨格 → 肉付け → エッジケースの 3 段階で進める
- 各段階で構文チェック or 動作確認してから次に進む
- 大きな変更を一括で Write せず、Edit で段階的に組み立てる

### エッジケースの事前列挙
- 実装前に「壊れるケース」を 3 つ以上挙げる
- 最低限: 空入力, None, 境界値(0, 負数, 最大値), Unicode, 長大な入力
- 列挙したケースのハンドリングを実装に含める

### 検証（完了前に必ず実行）
- `python3 -c "import py_compile; py_compile.compile('eve-coder.py', doraise=True)"`
- `python3 -m pytest tests/ -v`（または `python3 -m unittest discover -s tests -v`）
- 変更したファイルを Read で再確認

## EvE CLI 固有ルール
- **ゼロ依存**: Python 標準ライブラリのみ。pip install 禁止
- **単一ファイル**: eve-coder.py に全機能を収める
- **Python 3.8+ 互換**: match/case (3.10+) 使用不可
- **エンコーディング**: ファイル操作は常に `encoding="utf-8", errors="replace"`
- **セキュリティ**: パス操作では symlink チェック、OLLAMA_HOST は localhost のみ

## Design Quality Rules

### Before Writing Code
- ALWAYS read the target file and related files (callers, tests) BEFORE editing
- Identify existing patterns, naming conventions, and error handling style
- For tasks touching 2+ files: state your plan before implementing

### Implementation Standards
- One function = one responsibility. Keep functions under 30 lines
- Use clear, descriptive names: `validate_user_input()` not `proc(d)`
- Do NOT write more than 50 lines at once. Build incrementally:
  skeleton → flesh out → edge cases, verifying at each step
- Before implementing, list 3+ edge cases that could break the code
  (empty input, None, boundary values, Unicode, large data)

### After Writing Code
- Run syntax check / linter before reporting completion
- Run tests if available; write tests for new features
- Re-read modified files to confirm correctness
