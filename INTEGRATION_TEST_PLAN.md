# 統合テスト計画（200 件）

## 概要

EvE CLI の統合テストシナリオ 200 件を列挙。
機能連携、エンドツーエンドの動作を検証。

## 方針

- **自動化**: 重要なシナリオ 20 件のみ自動化（test_integration_real.py）
- **手動 QA**: 残りの 180 件は手動で検証
- **優先度**: A（必須）→ B（重要）→ C（改善）

---

## カテゴリ 1: エージェント + ツール連携（25 件）

### 自動化（5 件）

| ID | テスト名 | 優先度 | 内容 | 自動化 |
|----|----------|--------|------|--------|
| AT-001 | agent_bash_read | A | Bash ツール読み取り | ✅ |
| AT-002 | agent_bash_write | A | Bash ツール書き込み | ✅ |
| AT-003 | agent_edit_create | A | Edit ツール作成 | ✅ |
| AT-004 | agent_write_new | A | Write ツール新規 | ✅ |
| AT-005 | agent_read_file | A | Read ツール読込 | ✅ |

### 手動（20 件）

| ID | テスト名 | 優先度 | 内容 |
|----|----------|--------|------|
| AT-006 | agent_edit_modify | B | Edit ツール変更 |
| AT-007 | agent_write_overwrite | B | Write ツール上書き |
| AT-008 | agent_grep_search | B | Grep ツール検索 |
| AT-009 | agent_glob_list | C | Glob ツール一覧 |
| AT-010 | agent_todo_add | C | Todo ツール追加 |
| AT-011 | agent_todo_complete | C | Todo ツール完了 |
| AT-012 | agent_webfetch_url | B | WebFetch ツール URL |
| AT-013 | agent_webfetch_extract | B | WebFetch ツール抽出 |
| AT-014 | agent_multirun_sequential | B | MultiRun 順次 |
| AT-015 | agent_multirun_parallel | B | MultiRun 並列 |
| AT-016 | agent_error_recovery | A | エラー回復 |
| AT-017 | agent_retry_logic | A | リトライロジック |
| AT-018 | agent_timeout_handling | A | タイムアウト処理 |
| AT-019 | agent_context_preserve | B | コンテキスト保持 |
| AT-020 | agent_session_save | A | セッション保存 |
| AT-021 | agent_session_resume | A | セッション再開 |
| AT-022 | agent_checkpoint_auto | B | 自動チェックポイント |
| AT-023 | agent_rollback | A | ロールバック |
| AT-024 | agent_logging | C | ログ出力 |
| AT-025 | agent_cleanup | C | クリーンアップ |

---

## カテゴリ 2: MCP + Skills 連携（25 件）

### 自動化（5 件）

| ID | テスト名 | 優先度 | 内容 | 自動化 |
|----|----------|--------|------|--------|
| MS-001 | mcp_skills_discovery | A | MCP スキル発見 | ✅ |
| MS-002 | mcp_skills_injection | A | MCP スキル注入 | ✅ |
| MS-003 | mcp_skills_execution | A | MCP スキル実行 | ✅ |
| MS-004 | mcp_skills_error | A | MCP スキルエラー | ✅ |
| MS-005 | mcp_skills_timeout | A | MCP スキルタイムアウト | ✅ |

### 手動（20 件）

| ID | テスト名 | 優先度 | 内容 |
|----|----------|--------|------|
| MS-006 | mcp_skills_concurrent | B | MCP スキル並列 |
| MS-007 | mcp_skills_sequential | B | MCP スキル順次 |
| MS-008 | mcp_skills_cascade | B | MCP スキルカスケード |
| MS-009 | mcp_skills_priority | B | MCP スキル優先度 |
| MS-010 | mcp_skills_conflict | B | MCP スキル競合 |
| MS-011 | skills_mcp_call | A | Skills MCP 呼び出し |
| MS-012 | skills_mcp_result | A | Skills MCP 結果 |
| MS-013 | skills_mcp_error | A | Skills MCP エラー |
| MS-014 | skills_mcp_retry | B | Skills MCP リトライ |
| MS-015 | skills_mcp_timeout | B | Skills MCP タイムアウト |
| MS-016 | skills_mcp_logging | C | Skills MCP ログ |
| MS-017 | skills_mcp_debug | C | Skills MCP デバッグ |
| MS-018 | skills_mcp_cleanup | C | Skills MCP クリーンアップ |
| MS-019 | skills_mcp_cache | B | Skills MCP キャッシュ |
| MS-020 | skills_mcp_invalidation | B | Skills MCP 無効化 |
| MS-021 | skills_mcp_config | B | Skills MCP 設定 |
| MS-022 | skills_mcp_reload | B | Skills MCP 再読み込み |
| MS-023 | skills_mcp_version | C | Skills MCP バージョン |
| MS-024 | skills_mcp_metadata | C | Skills MCP メタデータ |
| MS-025 | skills_mcp_documentation | C | Skills MCP ドキュメント |

---

## カテゴリ 3: Plan/Act + チェックポイント（25 件）

### 自動化（5 件）

| ID | テスト名 | 優先度 | 内容 | 自動化 |
|----|----------|--------|------|--------|
| PC-001 | plan_checkpoint_auto | A | Plan 自動チェックポイント | ✅ |
| PC-002 | act_checkpoint_auto | A | Act 自動チェックポイント | ✅ |
| PC-003 | plan_rollback | A | Plan ロールバック | ✅ |
| PC-004 | act_rollback | A | Act ロールバック | ✅ |
| PC-005 | plan_act_transition | A | Plan/Act 遷移 | ✅ |

### 手動（20 件）

| ID | テスト名 | 優先度 | 内容 |
|----|----------|--------|------|
| PC-006 | plan_checkpoint_manual | B | Plan 手動チェックポイント |
| PC-007 | act_checkpoint_manual | B | Act 手動チェックポイント |
| PC-008 | plan_restore | B | Plan 復元 |
| PC-009 | act_restore | B | Act 復元 |
| PC-010 | plan_diff | B | Plan 差分 |
| PC-011 | act_diff | B | Act 差分 |
| PC-012 | plan_stash | C | Plan stash |
| PC-013 | act_stash | C | Act stash |
| PC-014 | plan_apply | B | Plan apply |
| PC-015 | act_apply | B | Act apply |
| PC-016 | plan_reject | C | Plan reject |
| PC-017 | act_reject | C | Act reject |
| PC-018 | plan_multiple | B | Plan 複数チェックポイント |
| PC-019 | act_multiple | B | Act 複数チェックポイント |
| PC-020 | plan_order | C | Plan 順序 |
| PC-021 | act_order | C | Act 順序 |
| PC-022 | plan_latest | B | Plan 最新 |
| PC-023 | act_latest | B | Act 最新 |
| PC-024 | plan_search | C | Plan 検索 |
| PC-025 | act_search | C | Act 検索 |

---

## カテゴリ 4: 自動テスト + File Watcher（25 件）

### 自動化（5 件）

| ID | テスト名 | 優先度 | 内容 | 自動化 |
|----|----------|--------|------|--------|
| AW-001 | watcher_autotest_trigger | A | Watcher 自動テスト触发 | ✅ |
| AW-002 | watcher_autotest_lint | A | Watcher 自動テストリント | ✅ |
| AW-003 | watcher_autotest_test | A | Watcher 自動テストテスト | ✅ |
| AW-004 | watcher_autotest_error | A | Watcher 自動テストエラー | ✅ |
| AW-005 | watcher_autotest_fix | A | Watcher 自動テスト修正 | ✅ |

### 手動（20 件）

| ID | テスト名 | 優先度 | 内容 |
|----|----------|--------|------|
| AW-006 | watcher_autotest_syntax | B | Watcher 自動テスト構文 |
| AW-007 | watcher_autotest_retry | B | Watcher 自動テストリトライ |
| AW-008 | watcher_autotest_success | B | Watcher 自動テスト成功 |
| AW-009 | watcher_autotest_loop | B | Watcher 自動テストループ |
| AW-010 | watcher_autotest_max | B | Watcher 自動テスト最大 |
| AW-011 | autotest_watcher_detect | A | 自動テスト Watcher 検出 |
| AW-012 | autotest_watcher_notify | A | 自動テスト Watcher 通知 |
| AW-013 | autotest_watcher_inject | A | 自動テスト Watcher 注入 |
| AW-014 | autotest_watcher_snapshot | B | 自動テスト Watcher スナップショット |
| AW-015 | autotest_watcher_refresh | B | 自動テスト Watcher リフレッシュ |
| AW-016 | autotest_watcher_batch | C | 自動テスト Watcher バッチ |
| AW-017 | autotest_watcher_debounce | C | 自動テスト Watcher デバウンス |
| AW-018 | autotest_watcher_false | C | 自動テスト Watcher 誤検知 |
| AW-019 | autotest_watcher_ignore | C | 自動テスト Watcher 無視 |
| AW-020 | autotest_watcher_extensions | B | 自動テスト Watcher 拡張子 |
| AW-021 | autotest_watcher_poll | B | 自動テスト Watcher ポリング |
| AW-022 | autotest_watcher_performance | C | 自動テスト Watcher 性能 |
| AW-023 | autotest_watcher_memory | C | 自動テスト Watcher メモリ |
| AW-024 | autotest_watcher_cpu | C | 自動テスト Watcher CPU |
| AW-025 | autotest_watcher_cleanup | C | 自動テスト Watcher クリーンアップ |

---

## カテゴリ 5: Parallel + エージェント（25 件）

### 自動化（5 件）

| ID | テスト名 | 優先度 | 内容 | 自動化 |
|----|----------|--------|------|--------|
| PA-001 | parallel_agent_spawn | A | Parallel エージェント生成 | ✅ |
| PA-002 | parallel_agent_join | A | Parallel エージェント結合 | ✅ |
| PA-003 | parallel_agent_timeout | A | Parallel エージェントタイムアウト | ✅ |
| PA-004 | parallel_agent_error | A | Parallel エージェントエラー | ✅ |
| PA-005 | parallel_agent_concurrent | A | Parallel エージェント並列 | ✅ |

### 手動（20 件）

| ID | テスト名 | 優先度 | 内容 |
|----|----------|--------|------|
| PA-006 | parallel_agent_communicate | B | Parallel エージェント通信 |
| PA-007 | parallel_agent_share | B | Parallel エージェント共有 |
| PA-008 | parallel_agent_isolate | B | Parallel エージェント隔離 |
| PA-009 | parallel_agent_merge | B | Parallel エージェントマージ |
| PA-010 | parallel_agent_conflict | B | Parallel エージェント競合 |
| PA-011 | parallel_agent_priority | B | Parallel エージェント優先度 |
| PA-012 | parallel_agent_retry | B | Parallel エージェントリトライ |
| PA-013 | parallel_agent_cancel | B | Parallel エージェントキャンセル |
| PA-014 | parallel_agent_progress | C | Parallel エージェント進捗 |
| PA-015 | parallel_agent_logging | C | Parallel エージェントログ |
| PA-016 | agent_parallel_spawn | A | エージェント Parallel 生成 |
| PA-017 | agent_parallel_join | A | エージェント Parallel 結合 |
| PA-018 | agent_parallel_communicate | B | エージェント Parallel 通信 |
| PA-019 | agent_parallel_share | B | エージェント Parallel 共有 |
| PA-020 | agent_parallel_isolate | B | エージェント Parallel 隔離 |
| PA-021 | agent_parallel_merge | B | エージェント Parallel マージ |
| PA-022 | agent_parallel_conflict | B | エージェント Parallel 競合 |
| PA-023 | agent_parallel_priority | B | エージェント Parallel 優先度 |
| PA-024 | agent_parallel_timeout | A | エージェント Parallel タイムアウト |
| PA-025 | agent_parallel_error | A | エージェント Parallel エラー |

---

## カテゴリ 6: セッション + 日本語 UX（25 件）

### 自動化（5 件）

| ID | テスト名 | 優先度 | 内容 | 自動化 |
|----|----------|--------|------|--------|
| SJ-001 | session_ja_greeting | A | セッション日本語挨拶 | ✅ |
| SJ-002 | session_ja_error | A | セッション日本語エラー | ✅ |
| SJ-003 | session_ja_warning | A | セッション日本語警告 | ✅ |
| SJ-004 | session_ja_info | A | セッション日本語情報 | ✅ |
| SJ-005 | session_ja_prompt | A | セッション日本語プロンプト | ✅ |

### 手動（20 件）

| ID | テスト名 | 優先度 | 内容 |
|----|----------|--------|------|
| SJ-006 | session_ja_help | B | セッション日本語ヘルプ |
| SJ-007 | session_ja_slash | B | セッション日本語スラッシュ |
| SJ-008 | session_ja_output | B | セッション日本語出力 |
| SJ-009 | session_ja_context | B | セッション日本語コンテキスト |
| SJ-010 | session_ja_memory | B | セッション日本語メモリ |
| SJ-011 | ja_session_save | A | 日本語セッション保存 |
| SJ-012 | ja_session_resume | A | 日本語セッション再開 |
| SJ-013 | ja_session_checkpoint | B | 日本語セッションチェックポイント |
| SJ-014 | ja_session_rollback | A | 日本語セッションロールバック |
| SJ-015 | ja_session_restore | B | 日本語セッション復元 |
| SJ-016 | ja_session_diff | B | 日本語セッション差分 |
| SJ-017 | ja_session_stash | C | 日本語セッション stash |
| SJ-018 | ja_session_apply | B | 日本語セッション apply |
| SJ-019 | ja_session_reject | C | 日本語セッション reject |
| SJ-020 | ja_session_multiple | C | 日本語セッション複数 |
| SJ-021 | ja_session_order | C | 日本語セッション順序 |
| SJ-022 | ja_session_latest | B | 日本語セッション最新 |
| SJ-023 | ja_session_search | C | 日本語セッション検索 |
| SJ-024 | ja_session_logging | C | 日本語セッションログ |
| SJ-025 | ja_session_cleanup | C | 日本語セッションクリーンアップ |

---

## カテゴリ 7: TUI + エージェント（25 件）

### 自動化（5 件）

| ID | テスト名 | 優先度 | 内容 | 自動化 |
|----|----------|--------|------|--------|
| TA-001 | tui_agent_esc | A | TUI エージェント ESC 中断 | ✅ |
| TA-002 | tui_agent_typeahead | A | TUI エージェント Type-ahead | ✅ |
| TA-003 | tui_agent_scroll | A | TUI エージェントスクロール | ✅ |
| TA-004 | tui_agent_input | A | TUI エージェント入力 | ✅ |
| TA-005 | tui_agent_multiline | A | TUI エージェント複数行 | ✅ |

### 手動（20 件）

| ID | テスト名 | 優先度 | 内容 |
|----|----------|--------|------|
| TA-006 | tui_agent_debug | B | TUI エージェントデバッグ |
| TA-007 | tui_agent_no_scroll | B | TUI エージェントノースクロール |
| TA-008 | tui_agent_prefill | B | TUI エージェント Prefill |
| TA-009 | tui_agent_history | C | TUI エージェント履歴 |
| TA-010 | tui_agent_completion | C | TUI エージェント補完 |
| TA-011 | agent_tui_esc | A | エージェント TUI ESC |
| TA-012 | agent_tui_typeahead | A | エージェント TUI Type-ahead |
| TA-013 | agent_tui_scroll | A | エージェント TUI スクロール |
| TA-014 | agent_tui_debug | B | エージェント TUI デバッグ |
| TA-015 | agent_tui_no_scroll | B | エージェント TUI ノースクロール |
| TA-016 | agent_tui_input | A | エージェント TUI 入力 |
| TA-017 | agent_tui_multiline | A | エージェント TUI 複数行 |
| TA-018 | agent_tui_prefill | B | エージェント TUI Prefill |
| TA-019 | agent_tui_history | C | エージェント TUI 履歴 |
| TA-020 | agent_tui_completion | C | エージェント TUI 補完 |
| TA-021 | tui_agent_concurrent | B | TUI エージェント並列 |
| TA-022 | tui_agent_sequential | B | TUI エージェント順次 |
| TA-023 | tui_agent_selective | C | TUI エージェント選択 |
| TA-024 | tui_agent_full | C | TUI エージェント完全 |
| TA-025 | tui_agent_incremental | C | TUI エージェント増分 |

---

## カテゴリ 8: セキュリティ + 全機能（25 件）

### 自動化（5 件）

| ID | テスト名 | 優先度 | 内容 | 自動化 |
|----|----------|--------|------|--------|
| SI-001 | security_agent_dangerous | A | セキュリティエージェント危険コマンド | ✅ |
| SI-002 | security_agent_url | A | セキュリティエージェント URL | ✅ |
| SI-003 | security_agent_symlink | A | セキュリティエージェント symlink | ✅ |
| SI-004 | security_agent_traversal | A | セキュリティエージェントトラバーサル | ✅ |
| SI-005 | security_agent_ssrf | A | セキュリティエージェント SSRF | ✅ |

### 手動（20 件）

| ID | テスト名 | 優先度 | 内容 |
|----|----------|--------|------|
| SI-006 | security_agent_session | B | セキュリティエージェントセッション |
| SI-007 | security_agent_protected | B | セキュリティエージェント保護パス |
| SI-008 | security_agent_iteration | B | セキュリティエージェントイテレーション |
| SI-009 | security_mcp_dangerous | B | セキュリティ MCP 危険コマンド |
| SI-010 | security_mcp_url | B | セキュリティ MCP URL |
| SI-011 | security_skills_dangerous | B | セキュリティ Skills 危険コマンド |
| SI-012 | security_skills_url | B | セキュリティ Skills URL |
| SI-013 | security_plan_dangerous | B | セキュリティ Plan 危険コマンド |
| SI-014 | security_plan_url | B | セキュリティ Plan URL |
| SI-015 | security_act_dangerous | B | セキュリティ Act 危険コマンド |
| SI-016 | security_act_url | B | セキュリティ Act URL |
| SI-017 | security_parallel_dangerous | C | セキュリティ Parallel 危険コマンド |
| SI-018 | security_parallel_url | C | セキュリティ Parallel URL |
| SI-019 | security_watcher_dangerous | C | セキュリティ Watcher 危険コマンド |
| SI-020 | security_watcher_url | C | セキュリティ Watcher URL |
| SI-021 | security_autotest_dangerous | C | セキュリティ AutoTest 危険コマンド |
| SI-022 | security_autotest_url | C | セキュリティ AutoTest URL |
| SI-023 | security_tui_dangerous | C | セキュリティ TUI 危険コマンド |
| SI-024 | security_tui_url | C | セキュリティ TUI URL |
| SI-025 | security_integration_all | A | セキュリティ統合すべて |

---

## 自動化計画（20 件）

### 優先度 A（15 件）

```
AT-001, AT-002, AT-003, AT-004, AT-005（エージェント + ツール）
MS-001, MS-002, MS-003, MS-004, MS-005（MCP + Skills）
PC-001, PC-002, PC-003, PC-004, PC-005（Plan/Act + チェックポイント）
```

### 優先度 B（5 件）

```
SJ-001, SJ-002, SJ-003, SJ-004, SJ-005（セッション + 日本語 UX）
```

---

## 手動 QA 計画（180 件）

### 実施方針

1. **テスター**: 開発チーム（手動でシナリオ実行）
2. **記録**: テスト結果を Issue で管理
3. **頻度**: リリース前（v2.6.0）
4. **カバレッジ**: 180 件すべて

### 優先度別実施順序

1. **優先度 A**（50 件）：必須機能
2. **優先度 B**（80 件）：重要機能
3. **優先度 C**（50 件）：改善機能

---

## 次回ステップ

1. **実質テスト 20 件実装**（test_integration_real.py）
2. **形式テスト削除**（test_features.py, test_integration.py）
3. **手動 QA 開始**（180 件）

---

## 更新履歴

- 2026-03-16: 初版作成（200 件列挙）
- 2026-03-16: 自動化方針決定（20 件）
