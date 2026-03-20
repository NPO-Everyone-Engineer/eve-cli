import json
import os
import shutil
import tempfile


DEFAULT_TEST_HOOKS = {
    "hooks": [
        {
            "event": "PostToolUse",
            "command": ["sh", "-lc", "test -S /tmp/cmux.sock && cmux notify 'tool finished'"],
            "timeout": 5,
        },
        {
            "event": "Stop",
            "command": ["sh", "-lc", "test -S /tmp/cmux.sock && cmux notify 'session stopped'"],
            "timeout": 5,
        },
    ]
}

DEFAULT_TEST_TRUSTED_HOOKS = {
    "global": {
        "trusted": True,
        "created_for": "test-suite",
    }
}


def create_temp_home_with_hooks():
    temp_home = tempfile.mkdtemp(prefix="eve-cli-home-")
    config_dir = os.path.join(temp_home, ".config", "eve-cli")
    os.makedirs(config_dir, exist_ok=True)

    hooks_path = os.path.join(config_dir, "hooks.json")
    with open(hooks_path, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_TEST_HOOKS, f, ensure_ascii=False, indent=2)

    trusted_hooks_path = os.path.join(config_dir, "trusted_hooks.json")
    with open(trusted_hooks_path, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_TEST_TRUSTED_HOOKS, f, ensure_ascii=False, indent=2)

    return temp_home, config_dir


class HookFixtureMixin:
    @classmethod
    def setUpClass(cls):
        cls._original_home = os.environ.get("HOME")
        cls._temp_home, cls._temp_config_dir = create_temp_home_with_hooks()
        os.environ["HOME"] = cls._temp_home

    @classmethod
    def tearDownClass(cls):
        if cls._original_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = cls._original_home
        shutil.rmtree(cls._temp_home, ignore_errors=True)
