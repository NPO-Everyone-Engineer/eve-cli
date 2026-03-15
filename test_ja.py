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
    # エラーメッセージ
    ('errors.invalid_max_steps', {}),
    ('errors.invalid_loop_hours', {}),
    ('errors.path_not_exist', {'path': '/tmp/nonexistent'}),
    ('errors.model_not_found', {'model': 'qwen3:8b'}),
    ('errors.command_timeout', {'timeout_s': 30}),
    ('errors.max_loop_hours_capped', {}),
    ('errors.mcp_server_start_failed', {'name': 'test-server', 'e': 'file not found'}),
    ('errors.sidecar_call_failed', {'e': 'timeout'}),
    
    # 警告メッセージ
    ('warnings.ollama_host_not_localhost', {'hostname': '192.168.1.100'}),
    ('warnings.file_read_failed', {'fname': 'test.txt', 'error': 'permission denied'}),
    
    # 情報メッセージ
    ('info.session_resumed', {}),
    
    # プロンプト
    ('prompts.confirm_write', {'path': './test.txt'}),
]

print("テスト結果:")
print("-" * 60)

all_passed = True
for key, kwargs in test_cases:
    result = t(key, default=f"[EN] {key}")
    
    # 日本語チェック：キーワードが含まれていれば OK
    ja_keywords = ['エラー', '警告', 'デバッグ', 'セッション', 'ファイル', 'サーバー', 'モデル', 'コマンド', 'パス', '許可', '読め', '返し', '起動', '呼び出し']
    is_ja = any(kw in result for kw in ja_keywords)
    
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
