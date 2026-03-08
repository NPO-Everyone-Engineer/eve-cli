# `/loop` 機能実装依頼プロンプト

## タスク: eve-cli に `/loop` コマンドを実装する

### 概要

Claude Code v2.0.22 の `/loop` 機能と同等の「継続的自律実行モード」を
`eve-coder.py` に実装する。

ユーザーが `/loop <タスク説明>` を入力すると、AI が指定したタスクを
定期的に実行し続ける（監視 → 検知 → 修正 → 再監視のサイクル）。

---

## 参考にする既存コード（実装前に必ず読むこと）

| クラス / 箇所 | 行番号（目安） | 参考にする点 |
|---|---|---|
| `AutoTestRunner` クラス | ~5066行 | バックグラウンドスレッドの参考実装 |
| `FileWatcher` クラス | ~5119行 | `_poll_loop` / `threading.Event` の使い方 |
| `/autotest` ハンドラ | ~9052行 | スラッシュコマンド登録の参考 |
| `Agent._run_impl()` | ~7658行 | エージェント実行の呼び出し方 |
| `_slash_commands` リスト | ~6382行 | 補完リストへの追加場所 |

---

## 実装仕様

### 1. `LoopMode` クラスを新規追加

**配置場所:** `FileWatcher` クラスの直後（約 5245 行付近）

```python
class LoopMode:
    """Continuously re-runs an agent task on a fixed interval."""

    DEFAULT_INTERVAL = 60          # seconds between iterations
    MAX_DURATION_SECONDS = 259200  # 3 days hard cap
    MAX_ITERATIONS = 4320          # 3 days / 60sec

    def __init__(self):
        self.enabled = False
        self.task = ""
        self.interval = self.DEFAULT_INTERVAL
        self.iteration_count = 0
        self._stop_event = threading.Event()
        self._thread = None
        self._agent_ref = None   # weak reference to Agent instance
        self._start_time = None
        self._lock = threading.Lock()
        self.last_result = ""

    def start(self, task: str, agent, interval: int = None):
        """Start loop mode with the given task and agent reference."""
        ...  # 実装する

    def stop(self):
        """Stop loop mode."""
        ...  # 実装する

    def _loop_body(self):
        """Background thread: repeatedly calls agent.run(self.task)."""
        ...  # 実装する

    def status_line(self) -> str:
        """Return a one-line status string for display."""
        ...  # 実装する
```

**`_loop_body` の動作:**

1. `_stop_event.wait(self.interval)` でインターバル待機
2. 経過時間が `MAX_DURATION_SECONDS` 超か `iteration_count >= MAX_ITERATIONS` なら自動停止
3. `self._agent_ref.run(self.task)` を呼び出す
4. 実行前に `[Loop #N]` のラベルをターミナルに出力する
5. 例外はキャッチしてログ出力し、ループを継続する

---

### 2. `Agent.__init__` に `LoopMode` を追加

既存の `self.file_watcher = FileWatcher(...)` の直後に追加する。

```python
self.loop_mode = LoopMode()
```

---

### 3. `/loop` スラッシュコマンドハンドラを追加

**配置場所:** `/watch` ハンドラ（約 9064 行付近）の直後

**コマンド形式:**

| コマンド | 動作 |
|---|---|
| `/loop <タスク説明>` | デフォルト 60 秒間隔でループ開始 |
| `/loop <N> <タスク説明>` | N 秒間隔でループ開始（例: `/loop 30 PRを監視して...`） |
| `/loop stop` | ループ停止 |
| `/loop status` | 現在の状態を表示 |

**ハンドラの実装例:**

```python
elif cmd == "/loop" or user_input.startswith("/loop "):
    args = user_input[len("/loop"):].strip()
    if args in ("stop", "off"):
        agent.loop_mode.stop()
        print(f"  Loop mode: {C.RED}OFF{C.RESET}")
    elif args in ("status", ""):
        if agent.loop_mode.enabled:
            print(f"  {agent.loop_mode.status_line()}")
        else:
            print(f"  Loop mode is not running.")
            print(f"  Usage: /loop [interval_sec] <task description>")
    else:
        # parse optional leading integer as interval
        parts = args.split(None, 1)
        interval = LoopMode.DEFAULT_INTERVAL
        task = args
        if parts[0].isdigit():
            interval = int(parts[0])
            task = parts[1] if len(parts) > 1 else ""
        if not task:
            print(f"  {C.YELLOW}Usage: /loop [interval_sec] <task description>{C.RESET}")
        else:
            agent.loop_mode.start(task, agent, interval=interval)
            print(f"  Loop mode: {C.GREEN}ON{C.RESET}")
            print(f"  {C.DIM}Task: {task}{C.RESET}")
            print(f"  {C.DIM}Interval: {interval}s | Max: 3 days{C.RESET}")
    continue
```

---

### 4. スラッシュコマンド補完リストに追加

`_slash_commands` リスト（6382 行付近）に `"/loop"` を追加する。

---

### 5. `/help` 表示に追加

`/autotest` と `/watch` の説明が並んでいる箇所（約 7463 行付近）に追記する。

```
{_c198}/loop{C.RESET}              Continuously re-run a task (監視→修正→再監視)
```

---

### 6. プログラム終了時のクリーンアップ

既存の `atexit` / シグナルハンドラが実行されている箇所を探し、
`agent.loop_mode.stop()` が呼ばれるようにする。

---

## 動作確認シナリオ

実装後、以下のコマンドで動作を確認すること。

**シナリオ 1: 基本動作**

```
/loop 10 git statusを確認して、uncommittedな変更があればdiff内容を要約して
```

→ 10 秒ごとにエージェントが実行され、`[Loop #1]`, `[Loop #2]` のように
  カウントが表示されることを確認する。

**シナリオ 2: 状態確認と停止**

```
/loop status
/loop stop
```

→ 状態表示と停止が正しく機能することを確認する。

---

## 注意事項

- `agent.run()` はメインスレッドの TUI に書き込むため、バックグラウンドスレッドから
  呼ぶ際は `threading.Lock` で保護すること
- `_stop_event.wait(interval)` を使うことで、停止要求に即座に反応できるようにする
- ループ中に `/loop stop` が入力されたとき、実行中の `agent.run()` が
  完了するまで待ってから停止する（強制終了しない）
- `LoopMode` は `Agent` への参照を `weakref` で持ち、循環参照を避けること
- ループの各実行は新しいユーザーメッセージとして `Session` に追加される
  （セッション履歴にループの全実行記録が残る）
