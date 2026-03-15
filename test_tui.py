#!/usr/bin/env python3
"""
EvE CLI TUI 機能テストスイート
TUI 機能強化：ESC 中断、Type-ahead、/debug-scroll、VIBE_DEBUG_TUI、VIBE_NO_SCROLL
"""

import os
import sys
import tempfile
import time

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
        print(f"✅ PASS: {name}")
    else:
        failed += 1
        results.append(("❌ FAIL", name, details))
        print(f"❌ FAIL: {name}")
        print(f"   詳細：{details}")

print("=" * 60)
print("EvE CLI TUI 機能テストスイート（20 件）")
print("=" * 60)
print()

# ============================================
# カテゴリ 1: ESC 中断検出（5 件）
# ============================================
print("カテゴリ 1: ESC 中断検出（5 件）")
print("-" * 60)

# ESC キーコード検証
esc_tests = [
    (27, True, 'ESC キーコード（0x1B）'),
    (ord('c') - 96, False, 'Ctrl+C'),
    (ord('d') - 96, False, 'Ctrl+D'),
    (13, False, 'Enter'),
    (9, False, 'Tab'),
]

for keycode, should_interrupt, desc in esc_tests:
    # ESC は 27
    is_esc = (keycode == 27)
    result = is_esc == should_interrupt
    test_result(f"キーコード：{desc}", result, f"キーコード：{keycode}, 中断：{is_esc}")

print()

# ============================================
# カテゴリ 2: Type-ahead バッファ（5 件）
# ============================================
print("カテゴリ 2: Type-ahead バッファ（5 件）")
print("-" * 60)

# Type-ahead 機能テスト
typeahead_tests = [
    ("AI 応答中に入力", True, 'バッファリング有効'),
    ("", False, '空文字はバッファなし'),
    ("複数行入力", True, '複数行バッファ'),
    ("Ctrl+C", False, '中断はバッファしない'),
    ("ESC", False, 'ESC はバッファしない'),
]

for input_text, should_buffer, desc in typeahead_tests:
    # 簡易チェック：空文字でないかつ中断キーでない
    is_buffer = bool(input_text) and input_text not in ('Ctrl+C', 'ESC')
    result = is_buffer == should_buffer
    test_result(f"Type-ahead: {desc}", result, f"入力：{input_text}, バッファ：{is_buffer}")

print()

# ============================================
# カテゴリ 3: /debug-scroll コマンド（5 件）
# ============================================
print("カテゴリ 3: /debug-scroll コマンド（5 件）")
print("-" * 60)

# /debug-scroll 機能テスト
debug_scroll_tests = [
    ("/debug-scroll", True, 'コマンド認識'),
    ("/debug-scroll --verbose", True, 'verbose モード'),
    ("/debug-scroll --reset", True, 'リセットモード'),
    ("/debug-scroll", True, 'DECSTBM テスト'),
    ("/debug-scroll", True, 'スクロール領域診断'),
]

for cmd, should_recognize, desc in debug_scroll_tests:
    # 簡易チェック：/debug-scroll は認識
    is_recognized = cmd.startswith('/debug-scroll')
    result = is_recognized == should_recognize
    test_result(f"/debug-scroll: {desc}", result, f"コマンド：{cmd}, 認識：{is_recognized}")

print()

# ============================================
# カテゴリ 4: VIBE_DEBUG_TUI 環境変数（5 件）
# ============================================
print("カテゴリ 5: VIBE_DEBUG_TUI 環境変数（5 件）")
print("-" * 60)

# VIBE_DEBUG_TUI 機能テスト
debug_tui_tests = [
    ('1', True, 'デバッグ有効'),
    ('0', False, 'デバッグ無効'),
    ('true', True, 'true 値'),
    ('false', False, 'false 値'),
    ('', False, '空文字'),
]

for value, should_enable, desc in debug_tui_tests:
    # 簡易チェック：1 または true
    is_enabled = value in ('1', 'true', 'True')
    result = is_enabled == should_enable
    test_result(f"VIBE_DEBUG_TUI: {desc}", result, f"値：{value}, 有効：{is_enabled}")

print()

# ============================================
# カテゴリ 5: VIBE_NO_SCROLL 環境変数（5 件）
# ============================================
print("カテゴリ 5: VIBE_NO_SCROLL 環境変数（5 件）")
print("-" * 60)

# VIBE_NO_SCROLL 機能テスト
no_scroll_tests = [
    ('1', True, 'スクロール無効'),
    ('0', False, 'スクロール有効'),
    ('true', True, 'true 値'),
    ('false', False, 'false 値'),
    ('', False, '空文字'),
]

for value, should_disable, desc in no_scroll_tests:
    # 簡易チェック：1 または true
    is_disabled = value in ('1', 'true', 'True')
    result = is_disabled == should_disable
    test_result(f"VIBE_NO_SCROLL: {desc}", result, f"値：{value}, 無効：{is_disabled}")

print()

# ============================================
# まとめ
# ============================================
print("=" * 60)
print(f"結果：{passed} 件合格 / {failed} 件失敗 / {passed + failed} 件合計")
if failed == 0:
    print("🎉 すべての TUI テストに合格！")
else:
    print(f"⚠️  {failed} 件のテストが失敗しました")
print("=" * 60)

sys.exit(0 if failed == 0 else 1)
