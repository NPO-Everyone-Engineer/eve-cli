#!/usr/bin/env python3
"""
EvE CLI テスト網羅性チェック
現行テストが機能を網羅しているか検証
"""

import os
import sys
import re
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("EvE CLI テスト網羅性チェック")
print("=" * 60)
print()

# ============================================
# 1. コード解析
# ============================================
print("1. コード解析")
print("-" * 60)

with open('eve-coder.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Tool クラス抽出
tool_pattern = r'class\s+(\w+Tool)\s*\('
tools = re.findall(tool_pattern, code)

# 関数抽出
func_pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
functions = re.findall(func_pattern, code)

# スラッシュコマンド抽出
slash_pattern = r'elif\s+cmd\s*==\s*"(/[^"]+)"'
slash_commands = re.findall(slash_pattern, code)

print(f"Tool クラス数：{len(tools)} 個")
print(f"関数定義数：{len(functions)} 個")
print(f"スラッシュコマンド数：{len(slash_commands)} 個")
print()

# ============================================
# 2. テストファイル解析
# ============================================
print("2. テストファイル解析")
print("-" * 60)

test_files = [
    'test_ja.py',
    'test_security.py',
    'test_tui.py',
    'test_features.py',
    'test_integration.py',
]

test_coverage = {}

for test_file in test_files:
    if os.path.exists(test_file):
        with open(test_file, 'r', encoding='utf-8') as f:
            test_code = f.read()
        
        # テストケース数（test_result 呼び出し）
        test_cases = len(re.findall(r'test_result\(', test_code))
        
        # Tool 言及チェック
        tool_mentions = {}
        for tool in tools:
            if tool.lower() in test_code.lower():
                tool_mentions[tool] = test_code.lower().count(tool.lower())
        
        test_coverage[test_file] = {
            'cases': test_cases,
            'tool_mentions': tool_mentions,
        }
        
        print(f"{test_file}:")
        print(f"  テストケース数：{test_cases} 件")
        print(f"  Tool 言及数：{len(tool_mentions)} 個")
        for tool, count in sorted(tool_mentions.items(), key=lambda x: -x[1])[:5]:
            print(f"    {tool}: {count} 回")
        print()
    else:
        print(f"{test_file}: ❌ 存在しない")
        test_coverage[test_file] = None
        print()

# ============================================
# 3. Tool クラス網羅性
# ============================================
print("3. Tool クラス網羅性")
print("-" * 60)

tool_coverage = {}
for tool in tools:
    covered = False
    for test_file, coverage in test_coverage.items():
        if coverage and tool.lower() in str(coverage.get('tool_mentions', {})).lower():
            covered = True
            break
    tool_coverage[tool] = covered

covered_tools = sum(1 for v in tool_coverage.values() if v)
total_tools = len(tools)

print(f"Tool クラス網羅性：{covered_tools}/{total_tools} ({covered_tools/total_tools*100:.1f}%)")
print()

print("カバーされた Tool:")
for tool, covered in tool_coverage.items():
    if covered:
        print(f"  ✅ {tool}")

print()
print("カバーされていない Tool:")
for tool, covered in tool_coverage.items():
    if not covered:
        print(f"  ❌ {tool}")

print()

# ============================================
# 4. 関数網羅性（主要関数のみ）
# ============================================
print("4. 関数網羅性（主要関数のみ）")
print("-" * 60)

# 主要関数（Tool クラスの run メソッドなど）
major_funcs = [f for f in functions if f.lower() in ['run', 'execute', 'call', 'validate', 'sanitize']]

func_coverage = {}
for func in major_funcs:
    covered = False
    for test_file, coverage in test_coverage.items():
        if coverage and func in coverage.get('tool_mentions', {}):
            covered = True
            break
    func_coverage[func] = covered

covered_funcs = sum(1 for v in func_coverage.values() if v)
total_funcs = len(major_funcs)

print(f"主要関数網羅性：{covered_funcs}/{total_funcs} ({covered_funcs/total_funcs*100:.1f}%)")
print()

# ============================================
# 5. スラッシュコマンド網羅性
# ============================================
print("5. スラッシュコマンド網羅性")
print("-" * 60)

slash_coverage = {}
for cmd in slash_commands:
    covered = False
    for test_file, coverage in test_coverage.items():
        if coverage and cmd in coverage:
            covered = True
            break
    slash_coverage[cmd] = covered

covered_slash = sum(1 for v in slash_coverage.values() if v)
total_slash = len(slash_commands)

print(f"スラッシュコマンド網羅性：{covered_slash}/{total_slash} ({covered_slash/total_slash*100:.1f}%)")
print()

# ============================================
# 6. 網羅性サマリー
# ============================================
print("=" * 60)
print("網羅性サマリー")
print("=" * 60)

print(f"Tool クラス：      {covered_tools}/{total_tools} ({covered_tools/total_tools*100:.1f}%)")
print(f"主要関数：        {covered_funcs}/{total_funcs} ({covered_funcs/total_funcs*100:.1f}%)")
print(f"スラッシュコマンド：{covered_slash}/{total_slash} ({covered_slash/total_slash*100:.1f}%)")
print()

# 総合評価
total_coverage = (covered_tools + covered_funcs + covered_slash) / (total_tools + total_funcs + total_slash) * 100

if total_coverage >= 80:
    evaluation = "✅ 良好"
elif total_coverage >= 50:
    evaluation = "⚠️ 改善の余地あり"
else:
    evaluation = "❌ 不十分"

print(f"総合網羅性：{total_coverage:.1f}% {evaluation}")
print()

# ============================================
# 7. 推奨アクション
# ============================================
print("7. 推奨アクション")
print("-" * 60)

uncovered_tools = [t for t, c in tool_coverage.items() if not c]
if uncovered_tools:
    print(f"未カバレッジ Tool（{len(uncovered_tools)} 個）:")
    for tool in uncovered_tools[:10]:
        print(f"  - {tool}")
    if len(uncovered_tools) > 10:
        print(f"  ... さらに {len(uncovered_tools) - 10} 個")
    print()

print("推奨:")
print("  1. 未カバレッジ Tool のテスト追加")
print("  2. 統合テストの実質的実装（20 件）")
print("  3. 形式テストを計画ドキュメントに変更")
print()

# ============================================
# 8. レポート保存
# ============================================
report = {
    'tools': {
        'total': total_tools,
        'covered': covered_tools,
        'uncovered': uncovered_tools,
    },
    'functions': {
        'total': total_funcs,
        'covered': covered_funcs,
    },
    'slash_commands': {
        'total': total_slash,
        'covered': covered_slash,
    },
    'test_files': test_coverage,
    'summary': {
        'total_coverage': total_coverage,
        'evaluation': evaluation,
    }
}

with open('test_coverage_report.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f"レポート保存：test_coverage_report.json")

sys.exit(0 if total_coverage >= 80 else 1)
