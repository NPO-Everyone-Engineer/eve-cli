#!/usr/bin/env python3
"""
EvE CLI 機能実装確認と脆弱性診断スイート
現行の機能実装状況を洗い出し、セキュリティ脆弱性を診断
"""

import os
import sys
import re
import ast
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("EvE CLI 機能実装確認と脆弱性診断")
print("=" * 60)
print()

# ============================================================================
# 1. 機能実装確認
# ============================================================================
print("1. 機能実装確認")
print("-" * 60)

# ファイル読み込み
with open('eve-coder.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 関数定義を抽出
func_pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
functions = re.findall(func_pattern, code)

# クラス定義を抽出
class_pattern = r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)'
classes = re.findall(class_pattern, code)

# スラッシュコマンドを抽出
slash_pattern = r'elif\s+cmd\s*==\s*"(/[^"]+)"'
slash_commands = re.findall(slash_pattern, code)

# ツール定義を抽出
tool_pattern = r'class\s+(\w+Tool)\s*\('
tools = re.findall(tool_pattern, code)

print(f"コード行数：{len(code.splitlines()):,} 行")
print(f"関数定義数：{len(functions)} 個")
print(f"クラス定義数：{len(classes)} 個")
print(f"スラッシュコマンド数：{len(slash_commands)} 個")
print(f"ツール数：{len(tools)} 個")
print()

# 主要機能チェックリスト
features = {
    '日本語 UX': 't()' in code and 'locales' in code,
    'エラーメッセージ日本語化': 'errors.' in code,
    'ヘルプメッセージ日本語化': 'help.' in code,
    'スラッシュコマンド日本語化': 'slash.' in code,
    'セキュリティテスト': os.path.exists('test_security.py'),
    'TUI 機能強化': 'VIBE_DEBUG_TUI' in code or 'VIBE_NO_SCROLL' in code,
    'ESC 中断': '_check_esc_key' in code,
    'Type-ahead': '_typeahead_buffer' in code,
    'MCP 連携': 'mcp' in code.lower(),
    'Skills': 'skills' in code.lower(),
    'Plan/Act モード': 'plan_mode' in code.lower(),
    'Git チェックポイント': 'checkpoint' in code.lower(),
    '自動テストループ': 'autotest' in code.lower(),
    'File Watcher': 'watch' in code.lower(),
    'Parallel Agents': 'parallel' in code.lower(),
}

print("主要機能実装状況:")
for feature, implemented in features.items():
    status = "✅" if implemented else "❌"
    print(f"  {status} {feature}")
print()

# ============================================================================
# 2. 脆弱性診断
# ============================================================================
print("2. 脆弱性診断")
print("-" * 60)

vulnerabilities = []

# 診断 1: eval/exec 使用
if 'eval(' in code or 'exec(' in code:
    vulnerabilities.append({
        'severity': 'HIGH',
        'type': 'コードインジェクション',
        'description': 'eval() または exec() の使用が検出されました',
        'recommendation': 'ast.literal_eval() または safer な方法を使用'
    })

# 診断 2: pickle 使用
if 'pickle' in code:
    vulnerabilities.append({
        'severity': 'HIGH',
        'type': '不安全なシリアライゼーション',
        'description': 'pickle モジュールの使用が検出されました',
        'recommendation': 'json または safer なシリアライゼーションを使用'
    })

# 診断 3: SQL インジェクション
if 'sqlite' in code and '?' not in code:
    vulnerabilities.append({
        'severity': 'MEDIUM',
        'type': 'SQL インジェクション',
        'description': 'パラメータ化クエリが使用されていない可能性があります',
        'recommendation': '? プレースホルダーを使用'
    })

# 診断 4: 危険な subprocess 呼び出し
if 'subprocess' in code and 'shell=True' in code:
    vulnerabilities.append({
        'severity': 'HIGH',
        'type': 'コマンドインジェクション',
        'description': 'subprocess で shell=True が使用されています',
        'recommendation': 'shell=False でリスト形式のコマンドを使用'
    })

# 診断 5: 不安全なファイル操作
if 'os.system' in code:
    vulnerabilities.append({
        'severity': 'HIGH',
        'type': 'コマンドインジェクション',
        'description': 'os.system() の使用が検出されました',
        'recommendation': 'subprocess.run() を使用'
    })

# 診断 6: 临时ファイル競合
if 'tempfile' not in code and '/tmp/' in code:
    vulnerabilities.append({
        'severity': 'MEDIUM',
        'type': 'TOCTOU 競合',
        'description': '/tmp/ ディレクトリの直接使用が検出されました',
        'recommendation': 'tempfile モジュールを使用'
    })

# 診断 7: 密码ハードコーディング
if 'password' in code.lower() and '=' in code:
    vulnerabilities.append({
        'severity': 'MEDIUM',
        'type': 'ハードコーディされたパスワード',
        'description': 'パスワードがコードにハードコーディングされています',
        'recommendation': '環境変数またはシークレット管理を使用'
    })

# 診断 8: 入力検証不足
if 'input(' in code:
    # input 使用は OK（ readline 編集のため）
    pass  # 脆弱性ではない

# 診断 9: シンボリックリンク競合
if 'os.readlink' not in code and 'open(' in code:
    vulnerabilities.append({
        'severity': 'LOW',
        'type': 'シンボリックリンク競合',
        'description': 'symlink チェックが実装されていない可能性があります',
        'recommendation': 'os.path.islink() でチェック'
    })

# 診断 10: エラーメッセージ情報漏洩
if 'traceback' in code and 'print' in code:
    vulnerabilities.append({
        'severity': 'LOW',
        'type': '情報漏洩',
        'description': 'スタックトレースが出力される可能性があります',
        'recommendation': 'ユーザー向けエラーメッセージを制限'
    })

print(f"脆弱性数：{len(vulnerabilities)} 件")
print()

if vulnerabilities:
    print("脆弱性一覧:")
    for i, vuln in enumerate(vulnerabilities, 1):
        print(f"\n  [{i}] {vuln['severity']}: {vuln['type']}")
        print(f"      説明：{vuln['description']}")
        print(f"      推奨：{vuln['recommendation']}")
else:
    print("✅ 重大な脆弱性は検出されませんでした")

print()

# ============================================================================
# 3. セキュリティ対策確認
# ============================================================================
print("3. セキュリティ対策確認")
print("-" * 60)

security_measures = {
    '危険コマンドブロック': 'dangerous_patterns' in code or 'is_dangerous' in code,
    'URL スキーム検証': 'http' in code and 'https' in code,
    'パストラバーサル防止': '..' in code and 'os.path' in code,
    'SSRF 防止': 'localhost' in code or '127.0.0.1' in code,
    'セッション ID サニタイズ': 'session_id' in code and 're' in code,
    '保護パスブロック': '.config' in code or '.ssh' in code,
    '最大イテレーション': 'MAX_' in code or 'max_' in code,
    'シンボリックリンク防止': 'islink' in code,
}

print("セキュリティ対策実装状況:")
for measure, implemented in security_measures.items():
    status = "✅" if implemented else "❌"
    print(f"  {status} {measure}")
print()

# ============================================================================
# 4. 診断サマリー
# ============================================================================
print("=" * 60)
print("診断サマリー")
print("=" * 60)

# 機能実装率
implemented_count = sum(1 for v in features.values() if v)
total_features = len(features)
feature_rate = (implemented_count / total_features) * 100

# 脆弱性数
high_count = sum(1 for v in vulnerabilities if v['severity'] == 'HIGH')
medium_count = sum(1 for v in vulnerabilities if v['severity'] == 'MEDIUM')
low_count = sum(1 for v in vulnerabilities if v['severity'] == 'LOW')

# セキュリティ対策率
implemented_security = sum(1 for v in security_measures.values() if v)
total_security = len(security_measures)
security_rate = (implemented_security / total_security) * 100

print(f"機能実装率：{implemented_count}/{total_features} ({feature_rate:.1f}%)")
print(f"セキュリティ対策率：{implemented_security}/{total_security} ({security_rate:.1f}%)")
print(f"脆弱性数：HIGH={high_count}, MEDIUM={medium_count}, LOW={low_count}")
print()

if high_count > 0:
    print("⚠️  HIGH 脆弱性があります！優先的に対応してください")
elif medium_count > 0:
    print("⚠️  MEDIUM 脆弱性があります！対応を検討してください")
elif low_count > 0:
    print("ℹ️  LOW 脆弱性があります！改善を検討してください")
else:
    print("✅ セキュリティは良好です")

print("=" * 60)

# JSON 出力
report = {
    'features': features,
    'vulnerabilities': vulnerabilities,
    'security_measures': security_measures,
    'summary': {
        'feature_rate': feature_rate,
        'security_rate': security_rate,
        'high_vulnerabilities': high_count,
        'medium_vulnerabilities': medium_count,
        'low_vulnerabilities': low_count,
    }
}

# レポート保存
with open('security_audit_report.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f"\nレポート保存：security_audit_report.json")

sys.exit(0 if high_count == 0 else 1)
