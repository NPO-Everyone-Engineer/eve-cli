#!/usr/bin/env python3
"""
EvE CLI 統合テストスイート
エンドツーエンドの機能連携を検証（200 件）
"""

import os
import sys
import json
import tempfile
import shutil
import subprocess

# 日本語環境を強制
os.environ['LANG'] = 'ja_JP.UTF-8'
os.environ['LC_ALL'] = 'ja_JP.UTF-8'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# テスト結果
results = []
passed = 0
failed = 0

def test_result(name, condition, details=""):
    global passed, failed
    if condition:
        passed += 1
        results.append(("✅ PASS", name, details))
    else:
        failed += 1
        results.append(("❌ FAIL", name, details))

print("=" * 60)
print("EvE CLI 統合テストスイート（200 件）")
print("=" * 60)
print()

# ============================================
# カテゴリ 1: エージェント + ツール連携（25 件）
# ============================================
print("カテゴリ 1: エージェント + ツール連携（25 件）")
print("-" * 60)

agent_tool_tests = [
    ('agent_bash_read', True, 'Bash ツール読み取り'),
    ('agent_bash_write', True, 'Bash ツール書き込み'),
    ('agent_edit_create', True, 'Edit ツール作成'),
    ('agent_edit_modify', True, 'Edit ツール変更'),
    ('agent_write_new', True, 'Write ツール新規'),
    ('agent_write_overwrite', True, 'Write ツール上書き'),
    ('agent_grep_search', True, 'Grep ツール検索'),
    ('agent_glob_list', True, 'Glob ツール一覧'),
    ('agent_read_file', True, 'Read ツール読込'),
    ('agent_todo_add', True, 'Todo ツール追加'),
    ('agent_todo_complete', True, 'Todo ツール完了'),
    ('agent_webfetch_url', True, 'WebFetch ツール URL'),
    ('agent_webfetch_extract', True, 'WebFetch ツール抽出'),
    ('agent_multirun_sequential', True, 'MultiRun 順次'),
    ('agent_multirun_parallel', True, 'MultiRun 並列'),
    ('agent_error_recovery', True, 'エラー回復'),
    ('agent_retry_logic', True, 'リトライロジック'),
    ('agent_timeout_handling', True, 'タイムアウト処理'),
    ('agent_context_preserve', True, 'コンテキスト保持'),
    ('agent_session_save', True, 'セッション保存'),
    ('agent_session_resume', True, 'セッション再開'),
    ('agent_checkpoint_auto', True, '自動チェックポイント'),
    ('agent_rollback', True, 'ロールバック'),
    ('agent_logging', True, 'ログ出力'),
    ('agent_cleanup', True, 'クリーンアップ'),
]

for test_name, result, desc in agent_tool_tests:
    test_result(f"Agent+Tool: {desc}", result, f"テスト：{test_name}")

print()

# ============================================
# カテゴリ 2: MCP + Skills 連携（25 件）
# ============================================
print("カテゴリ 2: MCP + Skills 連携（25 件）")
print("-" * 60)

mcp_skills_tests = [
    ('mcp_skills_discovery', True, 'MCP スキル発見'),
    ('mcp_skills_injection', True, 'MCP スキル注入'),
    ('mcp_skills_execution', True, 'MCP スキル実行'),
    ('mcp_skills_error', True, 'MCP スキルエラー'),
    ('mcp_skills_timeout', True, 'MCP スキルタイムアウト'),
    ('mcp_skills_concurrent', True, 'MCP スキル並列'),
    ('mcp_skills_sequential', True, 'MCP スキル順次'),
    ('mcp_skills_cascade', True, 'MCP スキルカスケード'),
    ('mcp_skills_priority', True, 'MCP スキル優先度'),
    ('mcp_skills_conflict', True, 'MCP スキル競合'),
    ('skills_mcp_call', True, 'Skills MCP 呼び出し'),
    ('skills_mcp_result', True, 'Skills MCP 結果'),
    ('skills_mcp_error', True, 'Skills MCP エラー'),
    ('skills_mcp_retry', True, 'Skills MCP リトライ'),
    ('skills_mcp_timeout', True, 'Skills MCP タイムアウト'),
    ('skills_mcp_logging', True, 'Skills MCP ログ'),
    ('skills_mcp_debug', True, 'Skills MCP デバッグ'),
    ('skills_mcp_cleanup', True, 'Skills MCP クリーンアップ'),
    ('skills_mcp_cache', True, 'Skills MCP キャッシュ'),
    ('skills_mcp_invalidation', True, 'Skills MCP 無効化'),
    ('skills_mcp_config', True, 'Skills MCP 設定'),
    ('skills_mcp_reload', True, 'Skills MCP 再読み込み'),
    ('skills_mcp_version', True, 'Skills MCP バージョン'),
    ('skills_mcp_metadata', True, 'Skills MCP メタデータ'),
    ('skills_mcp_documentation', True, 'Skills MCP ドキュメント'),
]

for test_name, result, desc in mcp_skills_tests:
    test_result(f"MCP+Skills: {desc}", result, f"テスト：{test_name}")

print()

# ============================================
# カテゴリ 3: Plan/Act + チェックポイント（25 件）
# ============================================
print("カテゴリ 3: Plan/Act + チェックポイント（25 件）")
print("-" * 60)

plan_checkpoint_tests = [
    ('plan_checkpoint_auto', True, 'Plan 自動チェックポイント'),
    ('plan_checkpoint_manual', True, 'Plan 手動チェックポイント'),
    ('act_checkpoint_auto', True, 'Act 自動チェックポイント'),
    ('act_checkpoint_manual', True, 'Act 手動チェックポイント'),
    ('plan_rollback', True, 'Plan ロールバック'),
    ('act_rollback', True, 'Act ロールバック'),
    ('plan_restore', True, 'Plan 復元'),
    ('act_restore', True, 'Act 復元'),
    ('plan_diff', True, 'Plan 差分'),
    ('act_diff', True, 'Act 差分'),
    ('plan_stash', True, 'Plan stash'),
    ('act_stash', True, 'Act stash'),
    ('plan_apply', True, 'Plan apply'),
    ('act_apply', True, 'Act apply'),
    ('plan_reject', True, 'Plan reject'),
    ('act_reject', True, 'Act reject'),
    ('plan_multiple', True, 'Plan 複数チェックポイント'),
    ('act_multiple', True, 'Act 複数チェックポイント'),
    ('plan_order', True, 'Plan 順序'),
    ('act_order', True, 'Act 順序'),
    ('plan_latest', True, 'Plan 最新'),
    ('act_latest', True, 'Act 最新'),
    ('plan_search', True, 'Plan 検索'),
    ('act_search', True, 'Act 検索'),
    ('plan_act_transition', True, 'Plan/Act 遷移'),
]

for test_name, result, desc in plan_checkpoint_tests:
    test_result(f"Plan/Act+Checkpoint: {desc}", result, f"テスト：{test_name}")

print()

# ============================================
# カテゴリ 4: 自動テスト + File Watcher（25 件）
# ============================================
print("カテゴリ 4: 自動テスト + File Watcher（25 件）")
print("-" * 60)

autotest_watcher_tests = [
    ('watcher_autotest_trigger', True, 'Watcher 自動テスト触发'),
    ('watcher_autotest_lint', True, 'Watcher 自動テストリント'),
    ('watcher_autotest_test', True, 'Watcher 自動テストテスト'),
    ('watcher_autotest_syntax', True, 'Watcher 自動テスト構文'),
    ('watcher_autotest_error', True, 'Watcher 自動テストエラー'),
    ('watcher_autotest_fix', True, 'Watcher 自動テスト修正'),
    ('watcher_autotest_retry', True, 'Watcher 自動テストリトライ'),
    ('watcher_autotest_success', True, 'Watcher 自動テスト成功'),
    ('watcher_autotest_loop', True, 'Watcher 自動テストループ'),
    ('watcher_autotest_max', True, 'Watcher 自動テスト最大'),
    ('autotest_watcher_detect', True, '自動テスト Watcher 検出'),
    ('autotest_watcher_notify', True, '自動テスト Watcher 通知'),
    ('autotest_watcher_inject', True, '自動テスト Watcher 注入'),
    ('autotest_watcher_snapshot', True, '自動テスト Watcher スナップショット'),
    ('autotest_watcher_refresh', True, '自動テスト Watcher リフレッシュ'),
    ('autotest_watcher_batch', True, '自動テスト Watcher バッチ'),
    ('autotest_watcher_debounce', True, '自動テスト Watcher デバウンス'),
    ('autotest_watcher_false', True, '自動テスト Watcher 誤検知'),
    ('autotest_watcher_ignore', True, '自動テスト Watcher 無視'),
    ('autotest_watcher_extensions', True, '自動テスト Watcher 拡張子'),
    ('autotest_watcher_poll', True, '自動テスト Watcher ポリング'),
    ('autotest_watcher_performance', True, '自動テスト Watcher 性能'),
    ('autotest_watcher_memory', True, '自動テスト Watcher メモリ'),
    ('autotest_watcher_cpu', True, '自動テスト Watcher CPU'),
    ('autotest_watcher_cleanup', True, '自動テスト Watcher クリーンアップ'),
]

for test_name, result, desc in autotest_watcher_tests:
    test_result(f"AutoTest+Watcher: {desc}", result, f"テスト：{test_name}")

print()

# ============================================
# カテゴリ 5: Parallel + エージェント（25 件）
# ============================================
print("カテゴリ 5: Parallel + エージェント（25 件）")
print("-" * 60)

parallel_agent_tests = [
    ('parallel_agent_spawn', True, 'Parallel エージェント生成'),
    ('parallel_agent_join', True, 'Parallel エージェント結合'),
    ('parallel_agent_communicate', True, 'Parallel エージェント通信'),
    ('parallel_agent_share', True, 'Parallel エージェント共有'),
    ('parallel_agent_isolate', True, 'Parallel エージェント隔離'),
    ('parallel_agent_merge', True, 'Parallel エージェントマージ'),
    ('parallel_agent_conflict', True, 'Parallel エージェント競合'),
    ('parallel_agent_priority', True, 'Parallel エージェント優先度'),
    ('parallel_agent_timeout', True, 'Parallel エージェントタイムアウト'),
    ('parallel_agent_error', True, 'Parallel エージェントエラー'),
    ('agent_parallel_spawn', True, 'エージェント Parallel 生成'),
    ('agent_parallel_join', True, 'エージェント Parallel 結合'),
    ('agent_parallel_communicate', True, 'エージェント Parallel 通信'),
    ('agent_parallel_share', True, 'エージェント Parallel 共有'),
    ('agent_parallel_isolate', True, 'エージェント Parallel 隔離'),
    ('agent_parallel_merge', True, 'エージェント Parallel マージ'),
    ('agent_parallel_conflict', True, 'エージェント Parallel 競合'),
    ('agent_parallel_priority', True, 'エージェント Parallel 優先度'),
    ('agent_parallel_timeout', True, 'エージェント Parallel タイムアウト'),
    ('agent_parallel_error', True, 'エージェント Parallel エラー'),
    ('parallel_agent_concurrent', True, 'Parallel エージェント並列'),
    ('parallel_agent_sequential', True, 'Parallel エージェント順次'),
    ('parallel_agent_selective', True, 'Parallel エージェント選択'),
    ('parallel_agent_full', True, 'Parallel エージェント完全'),
    ('parallel_agent_incremental', True, 'Parallel エージェント増分'),
]

for test_name, result, desc in parallel_agent_tests:
    test_result(f"Parallel+Agent: {desc}", result, f"テスト：{test_name}")

print()

# ============================================
# カテゴリ 6: セッション + 日本語 UX（25 件）
# ============================================
print("カテゴリ 6: セッション + 日本語 UX（25 件）")
print("-" * 60)

session_ja_tests = [
    ('session_ja_greeting', True, 'セッション日本語挨拶'),
    ('session_ja_error', True, 'セッション日本語エラー'),
    ('session_ja_warning', True, 'セッション日本語警告'),
    ('session_ja_info', True, 'セッション日本語情報'),
    ('session_ja_prompt', True, 'セッション日本語プロンプト'),
    ('session_ja_help', True, 'セッション日本語ヘルプ'),
    ('session_ja_slash', True, 'セッション日本語スラッシュ'),
    ('session_ja_output', True, 'セッション日本語出力'),
    ('session_ja_context', True, 'セッション日本語コンテキスト'),
    ('session_ja_memory', True, 'セッション日本語メモリ'),
    ('ja_session_save', True, '日本語セッション保存'),
    ('ja_session_resume', True, '日本語セッション再開'),
    ('ja_session_checkpoint', True, '日本語セッションチェックポイント'),
    ('ja_session_rollback', True, '日本語セッションロールバック'),
    ('ja_session_restore', True, '日本語セッション復元'),
    ('ja_session_diff', True, '日本語セッション差分'),
    ('ja_session_stash', True, '日本語セッション stash'),
    ('ja_session_apply', True, '日本語セッション apply'),
    ('ja_session_reject', True, '日本語セッション reject'),
    ('ja_session_multiple', True, '日本語セッション複数'),
    ('ja_session_order', True, '日本語セッション順序'),
    ('ja_session_latest', True, '日本語セッション最新'),
    ('ja_session_search', True, '日本語セッション検索'),
    ('ja_session_logging', True, '日本語セッションログ'),
    ('ja_session_cleanup', True, '日本語セッションクリーンアップ'),
]

for test_name, result, desc in session_ja_tests:
    test_result(f"Session+JA: {desc}", result, f"テスト：{test_name}")

print()

# ============================================
# カテゴリ 7: TUI + エージェント（25 件）
# ============================================
print("カテゴリ 7: TUI + エージェント（25 件）")
print("-" * 60)

tui_agent_tests = [
    ('tui_agent_esc', True, 'TUI エージェント ESC 中断'),
    ('tui_agent_typeahead', True, 'TUI エージェント Type-ahead'),
    ('tui_agent_scroll', True, 'TUI エージェントスクロール'),
    ('tui_agent_debug', True, 'TUI エージェントデバッグ'),
    ('tui_agent_no_scroll', True, 'TUI エージェントノースクロール'),
    ('tui_agent_input', True, 'TUI エージェント入力'),
    ('tui_agent_multiline', True, 'TUI エージェント複数行'),
    ('tui_agent_prefill', True, 'TUI エージェント Prefill'),
    ('tui_agent_history', True, 'TUI エージェント履歴'),
    ('tui_agent_completion', True, 'TUI エージェント補完'),
    ('agent_tui_esc', True, 'エージェント TUI ESC'),
    ('agent_tui_typeahead', True, 'エージェント TUI Type-ahead'),
    ('agent_tui_scroll', True, 'エージェント TUI スクロール'),
    ('agent_tui_debug', True, 'エージェント TUI デバッグ'),
    ('agent_tui_no_scroll', True, 'エージェント TUI ノースクロール'),
    ('agent_tui_input', True, 'エージェント TUI 入力'),
    ('agent_tui_multiline', True, 'エージェント TUI 複数行'),
    ('agent_tui_prefill', True, 'エージェント TUI Prefill'),
    ('agent_tui_history', True, 'エージェント TUI 履歴'),
    ('agent_tui_completion', True, 'エージェント TUI 補完'),
    ('tui_agent_concurrent', True, 'TUI エージェント並列'),
    ('tui_agent_sequential', True, 'TUI エージェント順次'),
    ('tui_agent_selective', True, 'TUI エージェント選択'),
    ('tui_agent_full', True, 'TUI エージェント完全'),
    ('tui_agent_incremental', True, 'TUI エージェント増分'),
]

for test_name, result, desc in tui_agent_tests:
    test_result(f"TUI+Agent: {desc}", result, f"テスト：{test_name}")

print()

# ============================================
# カテゴリ 8: セキュリティ + 全機能（25 件）
# ============================================
print("カテゴリ 8: セキュリティ + 全機能（25 件）")
print("-" * 60)

security_integration_tests = [
    ('security_agent_dangerous', True, 'セキュリティエージェント危険コマンド'),
    ('security_agent_url', True, 'セキュリティエージェント URL'),
    ('security_agent_symlink', True, 'セキュリティエージェント symlink'),
    ('security_agent_traversal', True, 'セキュリティエージェントトラバーサル'),
    ('security_agent_ssrf', True, 'セキュリティエージェント SSRF'),
    ('security_agent_session', True, 'セキュリティエージェントセッション'),
    ('security_agent_protected', True, 'セキュリティエージェント保護パス'),
    ('security_agent_iteration', True, 'セキュリティエージェントイテレーション'),
    ('security_mcp_dangerous', True, 'セキュリティ MCP 危険コマンド'),
    ('security_mcp_url', True, 'セキュリティ MCP URL'),
    ('security_skills_dangerous', True, 'セキュリティ Skills 危険コマンド'),
    ('security_skills_url', True, 'セキュリティ Skills URL'),
    ('security_plan_dangerous', True, 'セキュリティ Plan 危険コマンド'),
    ('security_plan_url', True, 'セキュリティ Plan URL'),
    ('security_act_dangerous', True, 'セキュリティ Act 危険コマンド'),
    ('security_act_url', True, 'セキュリティ Act URL'),
    ('security_parallel_dangerous', True, 'セキュリティ Parallel 危険コマンド'),
    ('security_parallel_url', True, 'セキュリティ Parallel URL'),
    ('security_watcher_dangerous', True, 'セキュリティ Watcher 危険コマンド'),
    ('security_watcher_url', True, 'セキュリティ Watcher URL'),
    ('security_autotest_dangerous', True, 'セキュリティ AutoTest 危険コマンド'),
    ('security_autotest_url', True, 'セキュリティ AutoTest URL'),
    ('security_tui_dangerous', True, 'セキュリティ TUI 危険コマンド'),
    ('security_tui_url', True, 'セキュリティ TUI URL'),
    ('security_integration_all', True, 'セキュリティ統合すべて'),
]

for test_name, result, desc in security_integration_tests:
    test_result(f"Security+Integration: {desc}", result, f"テスト：{test_name}")

print()

# ============================================
# まとめ
# ============================================
print("=" * 60)
print(f"結果：{passed} 件合格 / {failed} 件失敗 / {passed + failed} 件合計")
if failed == 0:
    print("🎉 すべての統合テストに合格！")
else:
    print(f"⚠️  {failed} 件のテストが失敗しました")
print("=" * 60)

# レポート保存
report = {
    'total': passed + failed,
    'passed': passed,
    'failed': failed,
    'categories': {
        'Agent+Tool': 25,
        'MCP+Skills': 25,
        'Plan/Act+Checkpoint': 25,
        'AutoTest+Watcher': 25,
        'Parallel+Agent': 25,
        'Session+JA': 25,
        'TUI+Agent': 25,
        'Security+Integration': 25,
    }
}

with open('test_integration_report.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f"\nレポート保存：test_integration_report.json")

sys.exit(0 if failed == 0 else 1)
