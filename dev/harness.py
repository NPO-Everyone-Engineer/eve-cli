#!/usr/bin/env python3
"""
Utilities for running the real unittest-based EvE CLI harness suites.
"""

from __future__ import annotations

import os
import sys
import time
import unittest


DEV_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(DEV_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


SMOKE_GROUPS = (
    (
        "Verifier / Watcher",
        (
            "tests.test_autotest_runner",
            "tests.test_file_watcher",
        ),
    ),
    (
        "Agent / Parallel",
        (
            "tests.test_subagent_scaling",
            "tests.test_parallel_files",
        ),
    ),
    (
        "Safety / Proactive",
        (
            "tests.test_action_executor",
            "tests.test_security_hardening",
        ),
    ),
)

CONTRACT_GROUPS = (
    (
        "Tools / MultiEdit",
        (
            "tests.test_tools",
            "tests.test_parallel_files",
        ),
    ),
    (
        "Verifier Pipeline",
        (
            "tests.test_autotest_runner",
            "tests.test_file_watcher",
            "tests.test_runtime_controls",
        ),
    ),
    (
        "Agent Contracts",
        (
            "tests.test_subagent_scaling",
            "tests.test_session",
        ),
    ),
    (
        "Security / Config",
        (
            "tests.test_action_executor",
            "tests.test_security_hardening",
            "tests.test_permission_mgr",
            "tests.test_config",
        ),
    ),
)


def _print_header(title):
    print("=" * 72)
    print(title)
    print("=" * 72)
    print()


def _load_module_suite(module_names):
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    for module_name in module_names:
        suite.addTests(loader.loadTestsFromName(module_name))
    return suite


def _run_suite(label, suite, verbosity=1):
    print(f"[{label}]")
    start = time.time()
    result = unittest.TextTestRunner(verbosity=verbosity, buffer=True).run(suite)
    elapsed = time.time() - start
    failures = len(result.failures) + len(result.errors)
    status = "PASS" if result.wasSuccessful() else "FAIL"
    print(
        f"{status}: {result.testsRun} tests, "
        f"{failures} failures/errors, "
        f"{len(result.skipped)} skipped, "
        f"{elapsed:.2f}s"
    )
    print()
    return result


def run_groups(title, groups, verbosity=1):
    _print_header(title)
    overall_ok = True
    total_run = 0
    total_failures = 0
    total_skipped = 0
    total_elapsed = 0.0

    for label, module_names in groups:
        start = time.time()
        suite = _load_module_suite(module_names)
        result = _run_suite(label, suite, verbosity=verbosity)
        total_elapsed += time.time() - start
        total_run += result.testsRun
        total_failures += len(result.failures) + len(result.errors)
        total_skipped += len(result.skipped)
        overall_ok = overall_ok and result.wasSuccessful()

    print("-" * 72)
    print(
        f"TOTAL: {total_run} tests, {total_failures} failures/errors, "
        f"{total_skipped} skipped, {total_elapsed:.2f}s"
    )
    return 0 if overall_ok else 1


def run_discovery(title, start_dir="tests", pattern="test*.py", verbosity=1):
    _print_header(title)
    loader = unittest.defaultTestLoader
    suite = loader.discover(
        start_dir=os.path.join(ROOT_DIR, start_dir),
        pattern=pattern,
        top_level_dir=ROOT_DIR,
    )
    result = _run_suite(f"discover:{start_dir}", suite, verbosity=verbosity)
    return 0 if result.wasSuccessful() else 1
