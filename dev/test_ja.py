#!/usr/bin/env python3
"""
EvE CLI 日本語 UX テストスクリプト
"""

import os
import sys

# 日本語環境を強制
os.environ['LANG'] = 'ja_JP.UTF-8'
os.environ['LC_ALL'] = 'ja_JP.UTF-8'

# eve-coder.py から関数をインポート
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 最小限のインポート
import json

# 翻訳システムを初期化
_LANG = None
_LOCALES = {}

def _detect_language():
    import locale
    env_lang = os.environ.get('EVE_CLI_LANG')
    if env_lang:
        return 'ja' if env_lang.lower().startswith('ja') else 'en'
    for var in ['LC_ALL', 'LC_MESSAGES', 'LANG']:
        lang = os.environ.get(var, '')
        if lang:
            if lang.startswith('ja') or 'JP' in lang:
                return 'ja'
            elif lang.startswith('en') or lang.startswith('C'):
                return 'en'
    try:
        lang = locale.getdefaultlocale()[0] or ''
        if lang.startswith('ja'):
            return 'ja'
        return 'en'
    except Exception:
        return 'en'

def _load_locales(lang='ja'):
    global _LOCALES
    if _LOCALES:
        return _LOCALES
    script_dir = os.path.dirname(os.path.abspath(__file__))
    locale_file = os.path.join(script_dir, 'locales', f'{lang}.json')
    try:
        if os.path.exists(locale_file):
            with open(locale_file, 'r', encoding='utf-8') as f:
                _LOCALES = json.load(f)
        else:
            _LOCALES = {}
    except Exception:
        _LOCALES = {}
    return _LOCALES

def set_language(lang):
    global _LANG
    _LANG = lang
    _LOCALES.clear()
    if lang == 'ja':
        _load_locales('ja')

def get_language():
    global _LANG
    if _LANG is None:
        _LANG = _detect_language()
    return _LANG

def t(key, default=None, **kwargs):
    lang = get_language()
    if lang != 'ja':
        return default or key
    locales = _load_locales('ja')
    parts = key.split('.')
    value = locales
    for part in parts:
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return default or key
    if isinstance(value, str) and kwargs:
        try:
            value = value.format(**kwargs)
        except KeyError:
            pass
    return value

# 初期化
set_language(get_language())

# テスト実行
print("=" * 60)
print("EvE CLI 日本語 UX テスト")
print("=" * 60)
print(f"検出された言語：{get_language()}")
print()

# テストケース
test_cases = [
    # エラーメッセージ（11 件）
    ('errors.invalid_max_steps', {}),
    ('errors.invalid_loop_hours', {}),
    ('errors.path_not_exist', {'path': '/tmp/nonexistent'}),
    ('errors.model_not_found', {'model': 'qwen3:8b'}),
    ('errors.command_timeout', {'timeout_s': 30}),
    ('errors.max_loop_hours_capped', {}),
    ('errors.mcp_server_start_failed', {'name': 'test-server', 'e': 'file not found'}),
    ('errors.sidecar_call_failed', {'e': 'timeout'}),
    ('errors.session_load_failed', {'error': 'permission denied'}),
    ('errors.url_redirect_blocked_scheme', {'scheme': 'ftp'}),
    ('errors.git_diff_failed', {}),
    
    # 警告メッセージ（6 件）
    ('warnings.ollama_host_not_localhost', {'hostname': '192.168.1.100'}),
    ('warnings.file_read_failed', {'fname': 'test.txt', 'error': 'permission denied'}),
    ('warnings.session_path_escape', {}),
    ('warnings.hook_command_blocked', {'base_cmd': 'rm -rf /'}),
    ('warnings.trusted_repo_changed', {'scope': 'global'}),
    ('warnings.test_syntax_error', {}),
    
    # 情報メッセージ（1 件）
    ('info.session_resumed', {}),
    
    # プロンプト（1 件）
    ('prompts.confirm_write', {'path': './test.txt'}),
    
    # ヘルプメッセージ（10 件）
    ('help.description', {}),
    ('help.prompt', {}),
    ('help.model', {}),
    ('help.max_agent_steps', {'default': 100, 'max': 200}),
    ('help.loop', {}),
    ('help.rag', {}),
    ('help.rag_model', {}),
    ('help.max_parallel_files', {}),
    ('help.level', {}),
    ('help.theme', {}),
    
    # スラッシュコマンド - Usage（10 件）
    ('slash.cleared', {}),
    ('slash.git_usage', {}),
    ('slash.pr_usage', {}),
    ('slash.learn_usage', {}),
    ('slash.gentest_usage', {}),
    ('slash.image_usage', {}),
    ('slash.index_search_usage', {}),
    ('slash.memory_add_usage', {}),
    ('slash.custom_usage', {}),
    ('slash.team_usage', {}),
    
    # スラッシュコマンド - 出力メッセージ（15 件）
    ('slash.session_saved', {'session_id': '20260315_200000_abc123'}),
    ('slash.session_forked', {'old_id': 'orig', 'fork_id': 'fork'}),
    ('slash.fork_preserved', {}),
    ('slash.compacted', {'before': 1000, 'after': 500}),
    ('slash.already_compact', {'after': 500, 'msgs': 10}),
    ('slash.yes_enabled', {}),
    ('slash.no_disabled', {}),
    ('slash.tokens_messages', {}),
    ('slash.diff_staged', {}),
    ('slash.commit_clean', {}),
    ('slash.commit_stage_prompt', {}),
    ('slash.commit_staged', {}),
    ('slash.checkpoint_none', {}),
    ('slash.checkpoint_list_title', {}),
    ('slash.checkpoint_saved', {}),
]

print("テスト結果:")
print("-" * 60)

all_passed = True
for key, kwargs in test_cases:
    result = t(key, default=f"[EN] {key}")
    
    # プレースホルダーを除去してチェック
    result_clean = result.replace('{before}', '').replace('{after}', '').replace('{msgs}', '')
    result_clean = result_clean.replace('{session_id}', '').replace('{old_id}', '').replace('{fork_id}', '')
    result_clean = result_clean.replace('{len}', '').replace('{path}', '').replace('{model}', '')
    result_clean = result_clean.replace('{error}', '').replace('{e}', '').replace('{timeout_s}', '')
    result_clean = result_clean.replace('{name}', '').replace('{hostname}', '').replace('{fname}', '')
    result_clean = result_clean.replace('{base_cmd}', '').replace('{scope}', '').replace('{default}', '')
    result_clean = result_clean.replace('{max}', '')
    
    # 日本語チェック：日本語文字（ひらがな・カタカナ・漢字）が含まれていれば OK
    import re
    ja_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]')
    is_ja = bool(ja_pattern.search(result_clean))
    
    if get_language() == 'ja' and is_ja:
        status = "✅ PASS"
    else:
        status = "❌ FAIL"
        all_passed = False
    
    print(f"{status}: {key}")
    print(f"  → {result}")
    print()

print("=" * 60)
if all_passed:
    print("🎉 すべてのテストに合格！")
else:
    print("⚠️  一部のテストが失敗しました")
print("=" * 60)

sys.exit(0 if all_passed else 1)
