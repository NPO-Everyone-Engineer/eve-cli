# `/delegate` 機能実装指示書

## 概要

cmux.dev や tmux 環境で複数パネルを立ち上げている場合に、
現在の eve-cli から**別パネルで動いている eve-cli（または他の CLI）にタスクを委譲**できる機能。

`tmux send-keys` を使い、指定パネルへ入力を送り込む方式。
実装コストが小さく、cmux.dev での複数エージェント並列運用に最も近い体験を提供する。

---

## ユースケース

```
# 右パネルの eve-cli にレビューを依頼
/delegate right PRの差分をレビューして問題点を報告して

# パネルIDを直接指定してタスクを送る
/delegate %3 テストを全件実行して失敗があれば修正して

# 別モデルで動いている eve-cli にクロスレビューさせる
/delegate %5 このコードを別の視点でレビューして
```

---

## 参考にする既存コード

| 箇所 | 行番号（目安） | 参考にする点 |
|---|---|---|
| `_notify()` 関数 | ~134行 | `tmux display-message` の実装パターン |
| `/watch` ハンドラ | ~9064行 | スラッシュコマンド登録の参考 |
| `_slash_commands` リスト | ~6382行 | 補完リストへの追加場所 |
| `/help` 表示 | ~7463行 | ヘルプ文字列の追記場所 |

---

## 実装仕様

### 1. ユーティリティ関数 `tmux_send_task()` を追加

**配置場所:** `_tmux_notify` の定義直後（約 165 行付近）

```python
def tmux_send_task(pane: str, task: str) -> tuple[bool, str]:
    """
    Send a task string to another tmux pane running eve-cli.

    pane: tmux pane target (e.g. "right", "left", "%3", "1.2")
    task: the text to type into the target pane
    Returns: (success: bool, message: str)
    """
    if not os.environ.get("TMUX"):
        return False, "Not inside a tmux session"

    # Resolve shorthand directions to tmux pane targets
    direction_map = {
        "right": "{right-of}",
        "left":  "{left-of}",
        "up":    "{up-of}",
        "down":  "{down-of}",
        "next":  "{next}",
        "prev":  "{previous}",
    }
    target = direction_map.get(pane.lower(), pane)

    try:
        # Verify the target pane exists
        check = subprocess.run(
            ["tmux", "display-message", "-p", "-t", target, "#{pane_id}"],
            capture_output=True, text=True, timeout=3
        )
        if check.returncode != 0:
            return False, f"Pane '{pane}' not found"

        pane_id = check.stdout.strip()

        # Send the task text followed by Enter
        subprocess.run(
            ["tmux", "send-keys", "-t", pane_id, task, "Enter"],
            check=True, timeout=3
        )
        return True, pane_id

    except subprocess.TimeoutExpired:
        return False, "tmux command timed out"
    except subprocess.CalledProcessError as e:
        return False, str(e)
```

---

### 2. `/delegate` スラッシュコマンドハンドラを追加

**配置場所:** `/loop` ハンドラの直後（loop 実装後）、または `/watch` ハンドラの直後

**コマンド形式:**

| コマンド | 動作 |
|---|---|
| `/delegate <pane> <task>` | 指定パネルにタスクを送信 |
| `/delegate list` | 現在の tmux パネル一覧を表示 |
| `/delegate right <task>` | 右パネルに送信（方向指定） |
| `/delegate left <task>` | 左パネルに送信 |
| `/delegate %3 <task>` | パネルID直接指定 |

**ハンドラ実装例:**

```python
elif cmd == "/delegate" or user_input.startswith("/delegate "):
    args = user_input[len("/delegate"):].strip()

    if not os.environ.get("TMUX"):
        print(f"  {C.YELLOW}⚠ Not inside a tmux session.{C.RESET}")
        print(f"  {C.DIM}Run eve-cli inside tmux (e.g. cmux.dev) to use /delegate.{C.RESET}")
        continue

    if args in ("list", "ls", ""):
        # Show available panes
        result = subprocess.run(
            ["tmux", "list-panes", "-a",
             "-F", "#{pane_id} #{window_name} #{pane_current_command} [#{pane_width}x#{pane_height}]"],
            capture_output=True, text=True
        )
        print(f"  {C.BOLD}Available tmux panes:{C.RESET}")
        for line in result.stdout.strip().splitlines():
            print(f"    {line}")
        print(f"\n  {C.DIM}Usage: /delegate <pane-id or direction> <task>{C.RESET}")
        print(f"  {C.DIM}Directions: right, left, up, down, next, prev{C.RESET}")
    else:
        parts = args.split(None, 1)
        if len(parts) < 2:
            print(f"  {C.YELLOW}Usage: /delegate <pane> <task description>{C.RESET}")
            print(f"  {C.DIM}Example: /delegate right テストを実行して{C.RESET}")
        else:
            pane, task = parts[0], parts[1]
            ok, info = tmux_send_task(pane, task)
            if ok:
                print(f"  {C.GREEN}✓ Delegated to pane {info}{C.RESET}")
                print(f"  {C.DIM}Task: {task}{C.RESET}")
            else:
                print(f"  {C.RED}✗ Failed: {info}{C.RESET}")
                print(f"  {C.DIM}Use /delegate list to see available panes.{C.RESET}")
    continue
```

---

### 3. スラッシュコマンド補完リストに追加

`_slash_commands` リスト（6382 行付近）に追加する：

```python
"/delegate",
```

---

### 4. `/help` 表示に追加

`/loop` と `/watch` の説明が並んでいる箇所（約 7463 行付近）に追記する：

```
{_c198}/delegate{C.RESET}          別の tmux パネルにタスクを委譲 (cmux.dev 対応)
```

---

## 動作確認シナリオ

### シナリオ 1: パネル一覧確認

```
/delegate list
```

→ 現在の tmux セッション内の全パネル一覧が表示される。

### シナリオ 2: 右パネルにタスクを送る

```
/delegate right git diff HEAD~1 を確認してレビューコメントをまとめて
```

→ 右パネルの eve-cli にテキストが入力され、Enter が送信される。

### シナリオ 3: パネルID直接指定

```
/delegate %3 このPRの実装をレビューして問題点があれば列挙して
```

→ `%3` パネルにタスクが送信される。

### シナリオ 4: tmux 外での実行

```
/delegate right something
```

→ `⚠ Not inside a tmux session.` と警告が表示され、何も送信しない。

---

## 発展アイデア（実装対象外・将来の拡張）

- `/delegate all <task>` — 全パネルに同じタスクをブロードキャスト
- `/delegate %3 --wait <task>` — 相手パネルの完了を待って結果を受け取る
- パネル名（`window_name`）での指定対応
- 複数モデルに並列クロスレビューさせる `/review --multi` との統合

---

## 注意事項

- `tmux send-keys` は対象パネルに**そのまま文字を送り込む**ため、相手が eve-cli 以外（bash など）でも動作する。意図しないコマンド実行に注意。
- 長いタスク文字列は tmux のバッファ制限（デフォルト 2MB）内に収まる範囲で使用する。
- `TMUX` 環境変数が未設定の場合（SSH 直接接続など）は機能しない。
