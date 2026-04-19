#!/usr/bin/env python3
"""
EvE CLI 回帰ハーネス。

リポジトリ内の unittest discover 対象をそのまま実行し、全体回帰を見る。
"""

import os

from harness import run_discovery


os.environ["LANG"] = "ja_JP.UTF-8"
os.environ["LC_ALL"] = "ja_JP.UTF-8"


if __name__ == "__main__":
    raise SystemExit(run_discovery("EvE CLI 回帰ハーネス"))
