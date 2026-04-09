#!/usr/bin/env python3
"""
EvE CLI 実統合スモークハーネス。

旧来の擬似 PASS リストではなく、実際の unittest スイートを少数精鋭で実行する。
"""

import os

from harness import SMOKE_GROUPS, run_groups


os.environ["LANG"] = "ja_JP.UTF-8"
os.environ["LC_ALL"] = "ja_JP.UTF-8"


if __name__ == "__main__":
    raise SystemExit(run_groups("EvE CLI 実統合スモークハーネス", SMOKE_GROUPS))
