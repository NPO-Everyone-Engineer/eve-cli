#!/usr/bin/env python3
"""
EvE CLI 契約テストハーネス。

カテゴリ別に実テスト群を回し、どの面が壊れたかを素早く切り分ける。
"""

import os

from harness import CONTRACT_GROUPS, run_groups


os.environ["LANG"] = "ja_JP.UTF-8"
os.environ["LC_ALL"] = "ja_JP.UTF-8"


if __name__ == "__main__":
    raise SystemExit(run_groups("EvE CLI 契約テストハーネス", CONTRACT_GROUPS))
