# eve-cli.ps1
# ローカルLLM (Ollama) で eve-coder を起動するスクリプト (Windows PowerShell / pwsh)
# Python + Ollama だけで動作 — Node.js不要、Claude Code不要、プロキシ不要
#
# NOTE: This project is NOT affiliated with, endorsed by, or associated with Anthropic.
#
# 使い方:
#   .\eve-cli.ps1                      # インタラクティブモード
#   .\eve-cli.ps1 -p "質問"            # ワンショット
#   .\eve-cli.ps1 --auto               # ネットワーク状況で自動判定
#   .\eve-cli.ps1 --model qwen3:8b     # モデル手動指定
#   .\eve-cli.ps1 -y                   # パーミッション確認スキップ (自己責任)
#   .\eve-cli.ps1 --debug              # デバッグモード

# --- UTF-8 エンコーディング修正 ---
# Windows コンソールを UTF-8 に強制設定
try { chcp 65001 | Out-Null } catch {}
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding  = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

$ErrorActionPreference = "Continue"

# --- ディレクトリ初期化 ---
$STATE_DIR = Join-Path $env:LOCALAPPDATA "eve-cli"
$CONFIG_DIR = Join-Path $env:USERPROFILE ".config\eve-cli"
$CONFIG_FILE = Join-Path $CONFIG_DIR "config"
$LIB_DIR = Join-Path $env:USERPROFILE ".local\lib\eve-cli"
$EVE_CODER_SCRIPT = Join-Path $LIB_DIR "eve-coder.py"

# ステートディレクトリの作成
if (-not (Test-Path $STATE_DIR)) {
    try { New-Item -ItemType Directory -Path $STATE_DIR -Force | Out-Null } catch {}
}

# --- デフォルト値 ---
$MODEL = ""
$SIDECAR_MODEL = ""
$OLLAMA_HOST = "http://localhost:11434"
$EVE_CLI_DEBUG = "0"
$UI_THEME = ""

# --- 設定読み込み (安全なパーサー) ---
# [C1 fix] dot-sourcing ではなく regex で既知キーのみ安全に読む
if (Test-Path $CONFIG_FILE) {
    $configLines = Get-Content -Path $CONFIG_FILE -Encoding UTF8 -ErrorAction SilentlyContinue
    foreach ($line in $configLines) {
        # Skip comments and blank lines
        if ($line -match '^\s*#' -or $line -match '^\s*$') { continue }

        # Parse KEY=VALUE (strip quotes, inline comments)
        if ($line -match '^(MODEL|SIDECAR_MODEL|OLLAMA_HOST|EVE_CLI_DEBUG|UI_THEME)\s*=\s*(.*)$') {
            $key = $Matches[1]
            $val = $Matches[2].Trim()
            # Remove surrounding quotes (single or double)
            $val = $val -replace "^[`"']", '' -replace "[`"']\s*$", ''
            # Remove inline comments (space + #)
            $val = $val -replace '\s+#.*$', ''
            $val = $val.Trim()

            if ($val -ne "") {
                switch ($key) {
                    "MODEL"          { $MODEL = $val }
                    "SIDECAR_MODEL"  { $SIDECAR_MODEL = $val }
                    "OLLAMA_HOST"    { $OLLAMA_HOST = $val }
                    "EVE_CLI_DEBUG"  { $EVE_CLI_DEBUG = $val }
                    "UI_THEME"       { $UI_THEME = $val }
                }
            }
        }
    }
}

# --- [SEC] OLLAMA_HOST 検証 - localhost のみ許可 (SSRF防止) ---
# Strict regex: @-credential injection を拒否 (e.g. http://localhost:11434@attacker.com)
$hostValid = $false
if ($OLLAMA_HOST -match '^http://(localhost|127\.0\.0\.1|\[::1\]):\d{1,5}(/.*)?$') {
    if ($OLLAMA_HOST -notmatch '@') {
        $hostValid = $true
    }
}
if (-not $hostValid) {
    Write-Host "Warning: OLLAMA_HOST='$OLLAMA_HOST' is not localhost. Resetting to localhost for security." -ForegroundColor Yellow
    Write-Host "  OLLAMA_HOST='$OLLAMA_HOST' はlocalhostではありません。セキュリティのためlocalhostにリセットします。" -ForegroundColor Yellow
    $OLLAMA_HOST = "http://localhost:11434"
}

# --- Python 検出 ---
# py -3 → python3 → python の順に試行。Python 3 であることを検証。
$PYTHON_CMD = $null

# Try py -3 (Windows py launcher)
try {
    $pyVer = & py -3 --version 2>&1
    if ($LASTEXITCODE -eq 0 -and $pyVer -match 'Python 3') {
        $PYTHON_CMD = "py"
    }
} catch {}

# Try python3
if (-not $PYTHON_CMD) {
    try {
        $pyVer = & python3 --version 2>&1
        if ($LASTEXITCODE -eq 0 -and $pyVer -match 'Python 3') {
            $PYTHON_CMD = "python3"
        }
    } catch {}
}

# Try python
if (-not $PYTHON_CMD) {
    try {
        $pyVer = & python --version 2>&1
        if ($LASTEXITCODE -eq 0 -and $pyVer -match 'Python 3') {
            $PYTHON_CMD = "python"
        }
    } catch {}
}

if (-not $PYTHON_CMD) {
    Write-Host "Error: Python 3 が見つかりません / Python 3 not found" -ForegroundColor Red
    Write-Host ""
    Write-Host "インストール方法 / Install:"
    Write-Host "  Windows: https://www.python.org/downloads/"
    Write-Host "  winget:  winget install Python.Python.3.12"
    Write-Host "  scoop:   scoop install python"
    exit 1
}

# Helper: Build Python invocation args (handles py -3 vs python3/python)
# Usage: $baseArgs = Get-PythonBaseArgs; & $PYTHON_CMD @baseArgs -c "script"
function Get-PythonBaseArgs {
    if ($PYTHON_CMD -eq "py") { return @("-3") }
    return @()
}

# --- eve-coder.py の探索 ---
if (-not (Test-Path $EVE_CODER_SCRIPT)) {
    $scriptDir = $PSScriptRoot
    $localCandidate = Join-Path $scriptDir "eve-coder.py"
    if ($scriptDir -and (Test-Path $localCandidate)) {
        $EVE_CODER_SCRIPT = $localCandidate
    } else {
        Write-Host "Error: eve-coder.py が見つかりません / eve-coder.py not found" -ForegroundColor Red
        Write-Host "  install.sh を実行するか、eve-coder.py を同じディレクトリに置いてください"
        Write-Host "  Run install.sh or place eve-coder.py in the same directory as this script."
        exit 1
    }
}

# --- Ollama 起動確認・起動関数 ---
function Test-OllamaRunning {
    try {
        $null = Invoke-WebRequest -Uri "$OLLAMA_HOST/api/tags" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

function Ensure-Ollama {
    if (Test-OllamaRunning) {
        return $true
    }

    # ollama コマンドの存在確認
    $ollamaCmd = Get-Command ollama -ErrorAction SilentlyContinue
    if (-not $ollamaCmd) {
        Write-Host "Error: ollama コマンドが見つかりません / ollama command not found" -ForegroundColor Red
        Write-Host ""
        Write-Host "インストール方法 / Install:"
        Write-Host "  Windows: https://ollama.com/download"
        Write-Host "  winget:  winget install Ollama.Ollama"
        return $false
    }

    Write-Host "  ollama を起動中... / Starting ollama..." -ForegroundColor Cyan
    try {
        Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden -ErrorAction Stop
    } catch {
        Write-Host "Error: ollama serve の起動に失敗しました / Failed to start ollama serve" -ForegroundColor Red
        return $false
    }

    # 最大30秒待機 (2秒×15回)
    for ($i = 1; $i -le 15; $i++) {
        $elapsed = $i * 2
        Write-Host "`r  ollama 起動待ち... / Waiting for ollama... ${elapsed}s " -NoNewline
        Start-Sleep -Seconds 2
        if (Test-OllamaRunning) {
            Write-Host ""
            Write-Host "  ollama 起動完了 / ollama started successfully" -ForegroundColor Green
            return $true
        }
    }
    Write-Host ""
    Write-Host "Error: ollama が起動できませんでした / Failed to start ollama" -ForegroundColor Red
    Write-Host ""
    Write-Host "対処法 / Troubleshooting:"
    Write-Host "  Ollama アプリを手動で起動してください"
    Write-Host "  Start the Ollama application manually."
    return $false
}

# --- ネットワーク接続チェック ---
function Test-NetworkAvailable {
    try {
        $null = Invoke-WebRequest -Uri "https://api.anthropic.com/" -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

# --- 引数パース ---
# Manual parsing to avoid PS parameter binding conflicts
$AUTO_MODE = $false
$YES_FLAG = $false
$EXTRA_ARGS = @()

$argList = $args
$i = 0
while ($i -lt $argList.Count) {
    $arg = [string]$argList[$i]
    switch -Exact ($arg) {
        "--auto" {
            $AUTO_MODE = $true
            $i++
        }
        "--model" {
            if ($i + 1 -ge $argList.Count) {
                Write-Host "Error: --model requires an argument" -ForegroundColor Red
                exit 1
            }
            $MODEL = [string]$argList[$i + 1]
            $i += 2
        }
        "-m" {
            if ($i + 1 -ge $argList.Count) {
                Write-Host "Error: -m requires an argument" -ForegroundColor Red
                exit 1
            }
            $MODEL = [string]$argList[$i + 1]
            $i += 2
        }
        "--theme" {
            if ($i + 1 -ge $argList.Count) {
                Write-Host "Error: --theme requires an argument" -ForegroundColor Red
                exit 1
            }
            $UI_THEME = [string]$argList[$i + 1]
            $i += 2
        }
        "-y" {
            $YES_FLAG = $true
            $i++
        }
        "--yes" {
            $YES_FLAG = $true
            $i++
        }
        "--dangerously-skip-permissions" {
            $YES_FLAG = $true
            $i++
        }
        "--debug" {
            $EVE_CLI_DEBUG = "1"
            $i++
        }
        "--resume" {
            $EXTRA_ARGS += $arg
            $i++
        }
        "-p" {
            # -p takes next arg as prompt
            if ($i + 1 -ge $argList.Count) {
                Write-Host "Error: -p requires an argument" -ForegroundColor Red
                exit 1
            }
            $EXTRA_ARGS += $arg
            $EXTRA_ARGS += [string]$argList[$i + 1]
            $i += 2
        }
        default {
            $EXTRA_ARGS += $arg
            $i++
        }
    }
}

# --- 環境変数を保存 (cleanup用) ---
$origOllamaHost = $env:OLLAMA_HOST
$origEveModel = $env:EVE_CLI_MODEL
$origEveSidecar = $env:EVE_CLI_SIDECAR_MODEL
$origEveDebug = $env:EVE_CLI_DEBUG
$origPythonIOEnc = $env:PYTHONIOENCODING
$origPythonUTF8 = $env:PYTHONUTF8

try {
    # --- 自動判定モード ---
    if ($AUTO_MODE) {
        if (Test-NetworkAvailable) {
            # claude CLI の存在確認
            $claudeCmd = Get-Command claude -ErrorAction SilentlyContinue
            if ($claudeCmd) {
                Write-Host "  ネットワーク接続あり + Claude Code あり → Claude Code を起動" -ForegroundColor Cyan
                Write-Host "  Network available + Claude Code found -> Launching Claude Code"
                $claudeArgs = @()
                if ($YES_FLAG) { $claudeArgs += "--dangerously-skip-permissions" }
                $claudeArgs += $EXTRA_ARGS
                & claude @claudeArgs
                exit $LASTEXITCODE
            }
            Write-Host "  ネットワーク接続あり (Claude Code なし) → ローカルモードで起動" -ForegroundColor Cyan
            Write-Host "  Network available (no Claude Code) -> Starting in local mode"
        } else {
            Write-Host "  ネットワーク接続なし → ローカルモード" -ForegroundColor Cyan
            Write-Host "  No network -> Local mode"
        }
    }

    # --- ローカルモードで起動 ---
    if (-not (Ensure-Ollama)) {
        Write-Host ""
        Write-Host "ollama が起動できないため終了します。 / Exiting: ollama could not be started." -ForegroundColor Red
        exit 1
    }

    # --- モデル引数を組み立て ---
    $MODEL_ARGS = @()
    if ($MODEL -ne "") {
        $MODEL_ARGS += "--model"
        $MODEL_ARGS += $MODEL
    }

    # --- モデルがロード済みか確認 (モデルが指定されている場合のみ) ---
    if ($MODEL -ne "") {
        $modelFound = $false
        try {
            $apiResponse = Invoke-WebRequest -Uri "$OLLAMA_HOST/api/tags" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
            $apiJson = $apiResponse.Content

            if ($apiJson) {
                # [SEC] Pass MODEL via env var, not interpolation (prevents injection)
                $env:TARGET_MODEL = $MODEL
                # Safer approach: pipe JSON via stdin, use env var for model name
                $pipeScript = @"
import sys, json, os
try:
    d = json.load(sys.stdin)
    names = [m['name'].strip() for m in d.get('models', [])]
    want = os.environ.get('TARGET_MODEL', '').strip()
    found = want in names or want + ':latest' in names
    found = found or any(n.startswith(want + ':') or n.startswith(want + '-') or n == want for n in names)
    want_base = want.split(':')[0] if ':' in want else want
    found = found or any(n.split(':')[0] == want_base for n in names)
    sys.exit(0 if found else 1)
except:
    sys.exit(1)
"@
                $pyBase = Get-PythonBaseArgs
                $apiJson | & $PYTHON_CMD @pyBase -c $pipeScript 2>$null
                if ($LASTEXITCODE -eq 0) {
                    $modelFound = $true
                } else {
                    # Fallback: simple string match
                    if ($apiJson -match [regex]::Escape($MODEL)) {
                        $modelFound = $true
                    }
                }
                Remove-Item Env:TARGET_MODEL -ErrorAction SilentlyContinue
            }
        } catch {}

        if (-not $modelFound) {
            Write-Host "Error: AIモデル $MODEL がまだダウンロードされていません" -ForegroundColor Red
            Write-Host "  AI model '$MODEL' is not downloaded yet."
            Write-Host ""
            Write-Host "ダウンロードするには、以下のコマンドを貼り付けてEnterを押してください:"
            Write-Host "  ollama pull `"$MODEL`""
            Write-Host ""
            Write-Host "(数分～数十分かかります。完了後に再度 eve-cli を実行してください)"
            Write-Host "  (This may take a few minutes. Run eve-cli again after it completes.)"
            Write-Host ""
            Write-Host "インストール済みモデル / Installed models:"
            try {
                $listScript = @"
import sys, json
try:
    data = json.load(sys.stdin)
    for m in data.get('models', []):
        print(f"  - {m['name']}")
except:
    pass
"@
                $listResponse = Invoke-WebRequest -Uri "$OLLAMA_HOST/api/tags" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
                $pyBase = Get-PythonBaseArgs
                $listResponse.Content | & $PYTHON_CMD @pyBase -c $listScript 2>$null
            } catch {
                Write-Host "  (一覧取得失敗 / Failed to list models)"
            }
            exit 1
        }
    }

    # --- パーミッション確認 ---
    $PERM_ARGS = @()

    if ($YES_FLAG) {
        $PERM_ARGS += "-y"
    } else {
        Write-Host ""
        Write-Host "============================================"
        Write-Host "  パーミッション確認 / Permission Check" -ForegroundColor Yellow
        Write-Host "============================================"
        Write-Host ""
        Write-Host " eve-cli はツール自動許可モード (-y) で起動できます。"
        Write-Host ""
        Write-Host " This means the AI can execute commands, read/write"
        Write-Host " files, and modify your system WITHOUT asking."
        Write-Host ""
        Write-Host " ローカルLLMはクラウドAIより精度が低いため、"
        Write-Host " 意図しない操作が実行される可能性があります。"
        Write-Host ""
        Write-Host "--------------------------------------------"
        Write-Host " [y] 自動許可モード (Auto-approve all tools)"
        Write-Host " [N] 通常モード (Ask before each tool use)"
        Write-Host "--------------------------------------------"
        Write-Host ""
        Write-Host " 続行しますか？ / Continue? [y/N]: " -NoNewline

        try {
            $reply = $Host.UI.ReadLine()
        } catch {
            $reply = "n"
        }
        Write-Host ""

        if ($reply -match '^(y|yes|はい|是)$') {
            $PERM_ARGS += "-y"
            Write-Host " → 自動許可モードで起動します / Starting in auto-approve mode" -ForegroundColor Green
        } else {
            Write-Host " → 通常モード (毎回確認) で起動します / Starting in normal mode" -ForegroundColor Cyan
        }
    }

    # --- デバッグ引数 ---
    $DEBUG_ARGS = @()
    if ($EVE_CLI_DEBUG -eq "1" -or $EVE_CLI_DEBUG -eq "true") {
        $DEBUG_ARGS += "--debug"
    }

    # --- テーマ引数 ---
    $THEME_ARGS = @()
    if ($UI_THEME -ne "") {
        $THEME_ARGS += "--theme"
        $THEME_ARGS += $UI_THEME
    }

    # --- 起動バナー ---
    Write-Host ""
    Write-Host "============================================"
    Write-Host "  eve-cli (eve-coder)" -ForegroundColor Cyan
    if ($MODEL -ne "") {
        Write-Host " Model: $MODEL"
    } else {
        Write-Host " Model: (auto-detect)"
    }
    Write-Host " Ollama: $OLLAMA_HOST"
    Write-Host " Engine: eve-coder.py (direct, no proxy)"
    Write-Host "============================================"
    Write-Host ""

    # --- 環境変数を設定 ---
    $env:OLLAMA_HOST = $OLLAMA_HOST
    $env:EVE_CLI_MODEL = $MODEL
    $env:EVE_CLI_SIDECAR_MODEL = $SIDECAR_MODEL
    $env:EVE_CLI_DEBUG = $EVE_CLI_DEBUG

    # --- Python 実行引数の組み立て ---
    $pythonArgs = Get-PythonBaseArgs
    $pythonArgs += $EVE_CODER_SCRIPT
    $pythonArgs += $MODEL_ARGS
    $pythonArgs += $PERM_ARGS
    $pythonArgs += $DEBUG_ARGS
    $pythonArgs += $THEME_ARGS
    $pythonArgs += $EXTRA_ARGS

    # --- 実行 ---
    & $PYTHON_CMD @pythonArgs
    exit $LASTEXITCODE

} finally {
    # --- 環境変数クリーンアップ ---
    # 元の値に復元 (null なら削除)
    if ($null -eq $origOllamaHost)  { Remove-Item Env:OLLAMA_HOST -ErrorAction SilentlyContinue }
    else { $env:OLLAMA_HOST = $origOllamaHost }

    if ($null -eq $origEveModel) { Remove-Item Env:EVE_CLI_MODEL -ErrorAction SilentlyContinue }
    else { $env:EVE_CLI_MODEL = $origEveModel }

    if ($null -eq $origEveSidecar) { Remove-Item Env:EVE_CLI_SIDECAR_MODEL -ErrorAction SilentlyContinue }
    else { $env:EVE_CLI_SIDECAR_MODEL = $origEveSidecar }

    if ($null -eq $origEveDebug) { Remove-Item Env:EVE_CLI_DEBUG -ErrorAction SilentlyContinue }
    else { $env:EVE_CLI_DEBUG = $origEveDebug }

    if ($null -eq $origPythonIOEnc) { Remove-Item Env:PYTHONIOENCODING -ErrorAction SilentlyContinue }
    else { $env:PYTHONIOENCODING = $origPythonIOEnc }

    if ($null -eq $origPythonUTF8) { Remove-Item Env:PYTHONUTF8 -ErrorAction SilentlyContinue }
    else { $env:PYTHONUTF8 = $origPythonUTF8 }
}
