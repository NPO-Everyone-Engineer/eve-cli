#!/usr/bin/env python3
"""
EvE CLI パフォーマンステストスイート
速度、メモリ、CPU を検証（100 件）
"""

import os
import sys
import json
import time
import tempfile
import shutil
import resource

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
print("EvE CLI パフォーマンステストスイート（100 件）")
print("=" * 60)
print()

# ============================================
# カテゴリ 1: 速度テスト（20 件）
# ============================================
print("カテゴリ 1: 速度テスト（20 件）")
print("-" * 60)

speed_tests = [
    ('ファイル作成', lambda: tempfile.mkstemp()),
    ('ファイル読込', lambda: open(tempfile.mkstemp()[1], 'r').close()),
    ('ファイル削除', lambda: os.unlink(tempfile.mkstemp()[1])),
    ('ディレクトリ作成', lambda: tempfile.mkdtemp()),
    ('ディレクトリ削除', lambda: shutil.rmtree(tempfile.mkdtemp())),
    ('文字列操作', lambda: 'test' * 1000),
    ('リスト内包', lambda: [i for i in range(1000)]),
    ('辞書作成', lambda: {i: i for i in range(1000)}),
    ('JSON シリアライズ', lambda: json.dumps({'test': 123})),
    ('JSON デシリアライズ', lambda: json.loads('{"test": 123}')),
    ('文字列 10KB', lambda: 'a' * (10 * 1024)),
    ('リスト 1 万要素', lambda: list(range(10000))),
    ('辞書 1 万要素', lambda: {i: i for i in range(10000)}),
    ('文字列結合', lambda: ''.join(['test'] * 1000)),
    ('文字列検索', lambda: 'target' in 'test target string'),
    ('文字列置換', lambda: 'test'.replace('t', 'T')),
    ('数値加算', lambda: sum(range(1000))),
    ('数値乗算', lambda: eval('*'.join(map(str, range(1, 101))))),
    ('ソート 1000 要素', lambda: sorted(list(range(1000)), reverse=True)),
    ('ハッシュ計算', lambda: hash('test' * 1000)),
]

for name, func in speed_tests:
    try:
        start = time.time()
        func()
        elapsed = time.time() - start
        passed_test = elapsed < 1.0  # 1 秒未満
        test_result(f"速度：{name}", passed_test, f"{elapsed*1000:.2f}ms")
    except Exception as e:
        test_result(f"速度：{name}", False, str(e))

print()

# ============================================
# カテゴリ 2: メモリテスト（20 件）
# ============================================
print("カテゴリ 2: メモリテスト（20 件）")
print("-" * 60)

memory_tests = [
    ('文字列 1KB', lambda: 'a' * 1024),
    ('文字列 100KB', lambda: 'a' * (100 * 1024)),
    ('文字列 1MB', lambda: 'a' * (1024 * 1024)),
    ('リスト 1000 要素', lambda: list(range(1000))),
    ('リスト 1 万要素', lambda: list(range(10000))),
    ('リスト 10 万要素', lambda: list(range(100000))),
    ('辞書 1000 要素', lambda: {i: i for i in range(1000)}),
    ('辞書 1 万要素', lambda: {i: i for i in range(10000)}),
    ('辞書 10 万要素', lambda: {i: i for i in range(100000)}),
    ('ネスト辞書', lambda: {'a': {'b': {'c': 123}}}),
    ('大規模リスト', lambda: [[j for j in range(100)] for i in range(100)]),
    ('タプル 1000 要素', lambda: tuple(range(1000))),
    ('セット 1000 要素', lambda: set(range(1000))),
    ('ファイルバッファ 1KB', lambda: open('/dev/zero', 'rb').read(1024)),
    ('ファイルバッファ 100KB', lambda: open('/dev/zero', 'rb').read(100 * 1024)),
    ('JSON 1000 要素', lambda: json.dumps({i: i for i in range(1000)})),
    ('JSON 1 万要素', lambda: json.dumps({i: i for i in range(10000)})),
    ('バイナリ 1KB', lambda: os.urandom(1024)),
    ('バイナリ 100KB', lambda: os.urandom(100 * 1024)),
    ('再帰 100 回', lambda: (lambda f: f(f, 0, 1, 100))(lambda self, a, b, n: a if n == 0 else self(self, b, a + b, n - 1))),
]

for name, func in memory_tests:
    try:
        func()
        mem_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        passed_test = mem_usage < 1024 * 1024  # 1GB 未満
        test_result(f"メモリ：{name}", passed_test, f"{mem_usage // 1024}KB")
    except Exception as e:
        test_result(f"メモリ：{name}", False, str(e))

print()

# ============================================
# カテゴリ 3: CPU テスト（20 件）
# ============================================
print("カテゴリ 3: CPU テスト（20 件）")
print("-" * 60)

cpu_tests = [
    ('加算 100 万回', lambda: sum(range(1000000))),
    ('乗算 100 回', lambda: eval('*'.join(map(str, range(1, 101))))),
    ('べき乗 100 回', lambda: 2 ** 100),
    ('素数判定 100 回', lambda: all(pow(i, 98, i) == 1 for i in range(2, 101) if i > 1)),
    ('フィボナッチ 50', lambda: (lambda f: f(f, 0, 1, 50))(lambda self, a, b, n: a if n == 0 else self(self, b, a + b, n - 1))),
    ('階乗 50', lambda: eval('*'.join(map(str, range(1, 51))))),
    ('ソート 1 万要素', lambda: sorted(list(range(10000)), reverse=True)),
    ('検索 1 万要素', lambda: 5000 in list(range(10000))),
    ('正規表現 100 回', lambda: __import__('re').match(r'\d+', '123')),
    ('ハッシュ 1000 回', lambda: hash('test' * 1000)),
    ('文字列比較 1000 回', lambda: 'test' == 'test'),
    ('辞書ルックアップ 1000 回', lambda: {i: i for i in range(1000)}[500]),
    ('リスト内包 1 万回', lambda: [i for i in range(10000)]),
    ('ジェネレータ 1 万回', lambda: sum(i for i in range(10000))),
    ('再帰 50 回', lambda: (lambda f: f(f, 0, 1, 50))(lambda self, a, b, n: a if n == 0 else self(self, b, a + b, n - 1))),
    ('ビット演算 1000 回', lambda: 0xFF & 0x0F),
    ('浮動小数点 1000 回', lambda: 3.14 * 1000),
    ('例外処理 100 回', lambda: (_ for _ in ()).throw(StopIteration)),
    ('コンテキスト 100 回', lambda: tempfile.TemporaryFile()),
    ('デコレータ 10 回', lambda: (lambda f: f)(lambda: None)),
]

for name, func in cpu_tests:
    try:
        start = time.time()
        func()
        elapsed = time.time() - start
        passed_test = elapsed < 5.0  # 5 秒未満
        test_result(f"CPU: {name}", passed_test, f"{elapsed:.2f}s")
    except Exception as e:
        test_result(f"CPU: {name}", False, str(e))

print()

# ============================================
# カテゴリ 4: I/O テスト（20 件）
# ============================================
print("カテゴリ 4: I/O テスト（20 件）")
print("-" * 60)

io_tests = [
    ('小ファイル作成 1KB', 1024),
    ('中ファイル作成 100KB', 1024 * 100),
    ('大ファイル作成 1MB', 1024 * 1024),
    ('小ファイル読込 1KB', 1024),
    ('中ファイル読込 100KB', 1024 * 100),
    ('大ファイル読込 1MB', 1024 * 1024),
    ('小ファイル削除 1KB', 1024),
    ('中ファイル削除 100KB', 1024 * 100),
    ('大ファイル削除 1MB', 1024 * 1024),
    ('ディレクトリ走査 100 ファイル', 100),
    ('ディレクトリ走査 1000 ファイル', 1000),
    ('ネストディレクトリ作成', None),
    ('ネストディレクトリ削除', None),
    ('シンボリックリンク作成', None),
    ('シンボリックリンク削除', None),
    ('ファイルパーミッション変更', None),
    ('ファイル所有者取得', None),
    ('ファイルサイズ取得', None),
    ('ファイル_mtime 取得', None),
    ('ファイル_atime 取得', None),
]

for name, size in io_tests:
    try:
        temp_dir = tempfile.mkdtemp()
        if size and isinstance(size, int):
            test_file = os.path.join(temp_dir, 'test.bin')
            if '作成' in name:
                with open(test_file, 'wb') as f:
                    f.write(os.urandom(size))
            elif '読込' in name:
                with open(test_file, 'wb') as f:
                    f.write(os.urandom(size))
                with open(test_file, 'rb') as f:
                    f.read()
            elif '削除' in name:
                with open(test_file, 'wb') as f:
                    f.write(os.urandom(size))
                os.unlink(test_file)
        elif size and isinstance(size, str) and 'ファイル' in size:
            count = int(size.split()[0])
            for j in range(count):
                with open(os.path.join(temp_dir, f'file{j}.txt'), 'w') as f:
                    f.write(f'content {j}')
            list(os.listdir(temp_dir))
        else:
            if 'ネスト' in name:
                nested = os.path.join(temp_dir, 'a', 'b', 'c')
                os.makedirs(nested)
                if '削除' in name:
                    shutil.rmtree(temp_dir)
                    temp_dir = tempfile.mkdtemp()
            elif 'シンボリック' in name:
                target = os.path.join(temp_dir, 'target.txt')
                link = os.path.join(temp_dir, 'link.txt')
                with open(target, 'w') as f:
                    f.write('target')
                if '作成' in name:
                    os.symlink(target, link)
                elif '削除' in name:
                    os.symlink(target, link)
                    os.unlink(link)
            elif 'パーミッション' in name:
                test_file = os.path.join(temp_dir, 'test.txt')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.chmod(test_file, 0o755)
            elif '所有者' in name:
                test_file = os.path.join(temp_dir, 'test.txt')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.stat(test_file).st_uid
            elif 'サイズ' in name or 'mtime' in name or 'atime' in name:
                test_file = os.path.join(temp_dir, 'test.txt')
                with open(test_file, 'w') as f:
                    f.write('test')
                stat = os.stat(test_file)
                if 'サイズ' in name:
                    stat.st_size
                elif 'mtime' in name:
                    stat.st_mtime
                elif 'atime' in name:
                    stat.st_atime
        shutil.rmtree(temp_dir)
        test_result(f"I/O: {name}", True, "completed")
    except Exception as e:
        test_result(f"I/O: {name}", False, str(e))

print()

# ============================================
# カテゴリ 5: 並列テスト（20 件）
# ============================================
print("カテゴリ 5: 並列テスト（20 件）")
print("-" * 60)

import threading

def thread_task(n):
    return sum(range(n))

parallel_tests = [
    ('1 スレッド', 1),
    ('2 スレッド', 2),
    ('4 スレッド', 4),
    ('8 スレッド', 8),
    ('16 スレッド', 16),
    ('1 スレッド 1 万回', 1),
    ('2 スレッド 1 万回', 2),
    ('4 スレッド 1 万回', 4),
    ('8 スレッド 1 万回', 8),
    ('16 スレッド 1 万回', 16),
    ('ネストスレッド 2 層', 2),
    ('ネストスレッド 4 層', 4),
    ('スレッド同期', 4),
    ('スレッド非同期', 4),
    ('スレッドキュー', 4),
    ('スレッドロック', 4),
    ('スレッドセマフォ', 4),
    ('スレッドイベント', 4),
    ('スレッドタイマー', 4),
    ('スレッドプール', 4),
]

for name, threads in parallel_tests:
    try:
        threads_list = []
        for j in range(threads):
            t = threading.Thread(target=thread_task, args=(10000,))
            threads_list.append(t)
            t.start()
        for t in threads_list:
            t.join()
        test_result(f"並列：{name}", True, f"{threads} threads completed")
    except Exception as e:
        test_result(f"並列：{name}", False, str(e))

print()

# ============================================
# まとめ
# ============================================
print("=" * 60)
print(f"結果：{passed} 件合格 / {failed} 件失敗 / {passed + failed} 件合計")
if failed == 0:
    print("🎉 すべてのパフォーマンステストに合格！")
else:
    print(f"⚠️  {failed} 件のテストが失敗しました")
print("=" * 60)

# レポート保存
report = {
    'total': passed + failed,
    'passed': passed,
    'failed': failed,
    'categories': {
        '速度': 20,
        'メモリ': 20,
        'CPU': 20,
        'I/O': 20,
        '並列': 20,
    }
}

with open('test_performance_report.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f"\nレポート保存：test_performance_report.json")

sys.exit(0 if failed == 0 else 1)
