# eve-cli installer for Windows
# Vaporwave Installer / Trilingual: Japanese / English / Chinese
#
# Usage:
#   irm https://raw.githubusercontent.com/NPO-Everyone-Engineer/eve-cli/main/install.ps1 | iex
#   .\install.ps1
#   .\install.ps1 -Model qwen3:8b
#   .\install.ps1 -Lang en

[CmdletBinding()]
param(
    [Alias("model")][string]$Model = "",
    [Alias("lang")][string]$Lang = "",
    [Alias("help")][switch]$Help
)

$ErrorActionPreference = "Continue"
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$TOTAL_STEPS = 7

# ╔══════════════════════════════════════════════════════════════╗
# ║  Vaporwave Colors (ANSI 256-color)                         ║
# ╚══════════════════════════════════════════════════════════════╝

# Enable ANSI escape codes on Windows 10+
$ESC = [char]27
$null = [Console]::Write("")  # force console init
if ($PSVersionTable.PSVersion.Major -ge 7) {
    $PSStyle.OutputRendering = 'Ansi'
}
# Enable VirtualTerminalProcessing for Windows Terminal / conhost
try {
    $k = 'HKCU:\Console'
    if (Test-Path $k) {
        $cur = (Get-ItemProperty $k -Name VirtualTerminalLevel -ErrorAction SilentlyContinue).VirtualTerminalLevel
        if ($cur -ne 1) {
            # We write to console directly; no registry changes needed at runtime.
            # Windows Terminal and modern conhost handle ANSI natively.
        }
    }
} catch {}

function C($code) { "${ESC}[38;5;${code}m" }
function BG($code) { "${ESC}[48;5;${code}m" }

$PINK      = C 198
$HOT_PINK  = C 206
$MAGENTA   = C 165
$PURPLE    = C 141
$CYAN      = C 51
$AQUA      = C 87
$MINT      = C 121
$CORAL     = C 210
$ORANGE    = C 208
$YELLOW    = C 226
$WHITE     = C 255
$GRAY      = C 245
$RED       = C 196
$GREEN     = C 46
$NEON_GREEN= C 118
$BLUE      = C 33

$BG_PINK   = BG 198
$BG_PURPLE = BG 53
$BG_CYAN   = BG 30

$BOLD  = "${ESC}[1m"
$DIM   = "${ESC}[2m"
$BLINK = "${ESC}[5m"
$NC    = "${ESC}[0m"

$GRADIENT_NEON  = @(46,47,48,49,50,51,45,39,33,27,21,57,93,129,165,201,200,199,198,197,196)
$GRADIENT_VAPOR = @(51,87,123,159,195,189,183,177,171,165)

# ╔══════════════════════════════════════════════════════════════╗
# ║  Trilingual Engine                                         ║
# ╚══════════════════════════════════════════════════════════════╝

function Detect-Lang {
    try {
        $culture = (Get-Culture).Name
        if ($culture -match '^ja') { return "ja" }
        if ($culture -match '^zh') { return "zh" }
    } catch {}
    return "en"
}

$script:LANG_CODE = if ($Lang) { $Lang } else { Detect-Lang }

$script:MESSAGES = @{
    # === Japanese ===
    "ja_subtitle"          = "  Vaporwave  AI Coding Environment  "
    "ja_tagline"           = "Network Unnecessary - Totally Free - Local AI Coding"
    "ja_boot1"             = "Vaporwave subsystem initializing..."
    "ja_boot2"             = "Aesthetic modules loading..."
    "ja_boot3"             = "Neon frequency calibrating..."
    "ja_boot4"             = "SYSTEM  ONLINE"
    "ja_step1"             = "SYSTEM  SCAN"
    "ja_step2"             = "MEMORY  ANALYSIS"
    "ja_step3"             = "PACKAGE  INSTALL"
    "ja_step4"             = "AI  MODEL  DOWNLOAD"
    "ja_step5"             = "FILE  DEPLOY"
    "ja_step6"             = "CONFIG  GENERATE"
    "ja_step7"             = "SYSTEM  TEST"
    "ja_hw_scan"           = "Hardware scan in progress..."
    "ja_windows_ok"        = "Windows detected"
    "ja_unsupported_arch"  = "Unsupported architecture"
    "ja_mem_scan"          = "Memory space mapping..."
    "ja_mem_label"         = "System memory"
    "ja_model_best"        = "Best for coding"
    "ja_model_great"       = "Great for coding"
    "ja_model_min"         = "Minimum viable"
    "ja_model_recommend"   = "16GB+ RAM recommended"
    "ja_mem_lack"          = "Insufficient memory"
    "ja_mem_lack_min"      = "Minimum 8GB required"
    "ja_mem_lack_hint1"    = "Close unnecessary apps to free memory"
    "ja_mem_lack_hint2"    = "A PC with 8GB+ RAM is required"
    "ja_manual_model"      = "Manual model"
    "ja_installed"         = "installed"
    "ja_installing"        = "Installing..."
    "ja_install_done"      = "installed"
    "ja_install_fail"      = "install failed"
    "ja_install_fail_hint" = "Please install manually, then re-run this script"
    "ja_no_pkgmgr"         = "No package manager found"
    "ja_python_manual"     = "Install Python from https://www.python.org/downloads/ or Microsoft Store"
    "ja_ollama_manual"     = "Install Ollama from https://ollama.com/download/windows"
    "ja_ollama_starting"   = "Starting Ollama..."
    "ja_ollama_wait"       = "Waiting for Ollama"
    "ja_model_downloading" = "Downloading model..."
    "ja_model_download_hint" = "First download may take several minutes depending on size"
    "ja_model_downloaded"  = "already downloaded"
    "ja_model_dl_done"     = "download complete"
    "ja_file_deploy"       = "Deploying files..."
    "ja_source_local"      = "Source: local"
    "ja_source_github"     = "Source: GitHub"
    "ja_config_gen"        = "Generating config..."
    "ja_config_exists"     = "Config exists -> keeping current settings"
    "ja_config_file"       = "Config file"
    "ja_path_added"        = "PATH added"
    "ja_path_set"          = "PATH: already set"
    "ja_diag"              = "Running system diagnostics..."
    "ja_online"            = "ONLINE"
    "ja_standby"           = "STANDBY (auto-starts on launch)"
    "ja_ready"             = "READY"
    "ja_warning"           = "WARNING"
    "ja_loaded"            = "LOADED"
    "ja_not_loaded"        = "not loaded"
    "ja_path_reopen"       = "Not in PATH (restart terminal to fix)"
    "ja_complete"          = "INSTALL  COMPLETE !!"
    "ja_usage"             = "Usage:"
    "ja_mode_interactive"  = "Interactive mode"
    "ja_mode_oneshot"      = "One-shot"
    "ja_mode_auto"         = "Auto-detect network"
    "ja_settings"          = "Settings:"
    "ja_label_model"       = "Model"
    "ja_label_config"      = "Config"
    "ja_label_command"     = "Command"
    "ja_reopen"            = "Open a new terminal, then run eve-cli"
    "ja_enjoy"             = "  Free AI Coding wo Tanoshimou  "
    "ja_help_usage"        = "Usage: install.ps1 [--model MODEL_NAME] [--lang LANG]"
    "ja_help_model"        = "Specify Ollama model (e.g. qwen3:8b)"
    "ja_help_lang"         = "Language: ja, en, zh"
    "ja_unknown_opt"       = "Unknown option"

    # === English ===
    "en_subtitle"          = "  FREE  AI  CODING  ENVIRONMENT  "
    "en_tagline"           = "No Network - Totally Free - Local AI Coding"
    "en_boot1"             = "Initializing vaporwave subsystem..."
    "en_boot2"             = "Loading aesthetic modules..."
    "en_boot3"             = "Calibrating neon frequencies..."
    "en_boot4"             = "SYSTEM  ONLINE"
    "en_step1"             = "SYSTEM  SCAN"
    "en_step2"             = "MEMORY  ANALYSIS"
    "en_step3"             = "PACKAGE  INSTALL"
    "en_step4"             = "AI  MODEL  DOWNLOAD"
    "en_step5"             = "FILE  DEPLOY"
    "en_step6"             = "CONFIG  GENERATE"
    "en_step7"             = "SYSTEM  TEST"
    "en_hw_scan"           = "Scanning hardware..."
    "en_windows_ok"        = "Windows detected"
    "en_unsupported_arch"  = "Unsupported architecture"
    "en_mem_scan"          = "Mapping memory space..."
    "en_mem_label"         = "System memory"
    "en_model_best"        = "Best for coding"
    "en_model_great"       = "Great for coding"
    "en_model_min"         = "Minimum viable"
    "en_model_recommend"   = "16GB+ RAM recommended"
    "en_mem_lack"          = "Insufficient memory"
    "en_mem_lack_min"      = "Minimum 8GB required"
    "en_mem_lack_hint1"    = "Close unnecessary apps to free memory"
    "en_mem_lack_hint2"    = "A PC with 8GB+ RAM is required"
    "en_manual_model"      = "Manual model"
    "en_installed"         = "installed"
    "en_installing"        = "Installing..."
    "en_install_done"      = "installed"
    "en_install_fail"      = "install failed"
    "en_install_fail_hint" = "Please install manually, then re-run this script"
    "en_no_pkgmgr"         = "No package manager found"
    "en_python_manual"     = "Install Python from https://www.python.org/downloads/ or Microsoft Store"
    "en_ollama_manual"     = "Install Ollama from https://ollama.com/download/windows"
    "en_ollama_starting"   = "Starting Ollama..."
    "en_ollama_wait"       = "Waiting for Ollama"
    "en_model_downloading" = "Downloading model..."
    "en_model_download_hint" = "First download may take several minutes depending on size"
    "en_model_downloaded"  = "already downloaded"
    "en_model_dl_done"     = "download complete"
    "en_file_deploy"       = "Deploying files..."
    "en_source_local"      = "Source: local"
    "en_source_github"     = "Source: GitHub"
    "en_config_gen"        = "Generating config..."
    "en_config_exists"     = "Config exists -> keeping current settings"
    "en_config_file"       = "Config file"
    "en_path_added"        = "PATH added"
    "en_path_set"          = "PATH: already set"
    "en_diag"              = "Running system diagnostics..."
    "en_online"            = "ONLINE"
    "en_standby"           = "STANDBY (auto-starts on launch)"
    "en_ready"             = "READY"
    "en_warning"           = "WARNING"
    "en_loaded"            = "LOADED"
    "en_not_loaded"        = "not loaded"
    "en_path_reopen"       = "Not in PATH (restart terminal to fix)"
    "en_complete"          = "INSTALL  COMPLETE !!"
    "en_usage"             = "Usage:"
    "en_mode_interactive"  = "Interactive mode"
    "en_mode_oneshot"      = "One-shot"
    "en_mode_auto"         = "Auto-detect network"
    "en_settings"          = "Settings:"
    "en_label_model"       = "Model"
    "en_label_config"      = "Config"
    "en_label_command"     = "Command"
    "en_reopen"            = "Open a new terminal, then run eve-cli"
    "en_enjoy"             = "  ENJOY  FREE  AI  CODING  "
    "en_help_usage"        = "Usage: install.ps1 [--model MODEL_NAME] [--lang LANG]"
    "en_help_model"        = "Specify Ollama model (e.g. qwen3:8b)"
    "en_help_lang"         = "Language: ja, en, zh"
    "en_unknown_opt"       = "Unknown option"

    # === Chinese ===
    "zh_subtitle"          = "  Free AI Coding Environment  "
    "zh_tagline"           = "No Network - Totally Free - Local AI Coding"
    "zh_boot1"             = "Initializing vaporwave subsystem..."
    "zh_boot2"             = "Loading aesthetic modules..."
    "zh_boot3"             = "Calibrating neon frequencies..."
    "zh_boot4"             = "SYSTEM  ONLINE"
    "zh_step1"             = "SYSTEM  SCAN"
    "zh_step2"             = "MEMORY  ANALYSIS"
    "zh_step3"             = "PACKAGE  INSTALL"
    "zh_step4"             = "AI  MODEL  DOWNLOAD"
    "zh_step5"             = "FILE  DEPLOY"
    "zh_step6"             = "CONFIG  GENERATE"
    "zh_step7"             = "SYSTEM  TEST"
    "zh_hw_scan"           = "Scanning hardware..."
    "zh_windows_ok"        = "Windows detected"
    "zh_unsupported_arch"  = "Unsupported architecture"
    "zh_mem_scan"          = "Mapping memory space..."
    "zh_mem_label"         = "System memory"
    "zh_model_best"        = "Best for coding"
    "zh_model_great"       = "Great for coding"
    "zh_model_min"         = "Minimum viable"
    "zh_model_recommend"   = "16GB+ RAM recommended"
    "zh_mem_lack"          = "Insufficient memory"
    "zh_mem_lack_min"      = "Minimum 8GB required"
    "zh_mem_lack_hint1"    = "Close unnecessary apps to free memory"
    "zh_mem_lack_hint2"    = "A PC with 8GB+ RAM is required"
    "zh_manual_model"      = "Manual model"
    "zh_installed"         = "installed"
    "zh_installing"        = "Installing..."
    "zh_install_done"      = "installed"
    "zh_install_fail"      = "install failed"
    "zh_install_fail_hint" = "Please install manually, then re-run this script"
    "zh_no_pkgmgr"         = "No package manager found"
    "zh_python_manual"     = "Install Python from https://www.python.org/downloads/ or Microsoft Store"
    "zh_ollama_manual"     = "Install Ollama from https://ollama.com/download/windows"
    "zh_ollama_starting"   = "Starting Ollama..."
    "zh_ollama_wait"       = "Waiting for Ollama"
    "zh_model_downloading" = "Downloading model..."
    "zh_model_download_hint" = "First download may take several minutes depending on size"
    "zh_model_downloaded"  = "already downloaded"
    "zh_model_dl_done"     = "download complete"
    "zh_file_deploy"       = "Deploying files..."
    "zh_source_local"      = "Source: local"
    "zh_source_github"     = "Source: GitHub"
    "zh_config_gen"        = "Generating config..."
    "zh_config_exists"     = "Config exists -> keeping current settings"
    "zh_config_file"       = "Config file"
    "zh_path_added"        = "PATH added"
    "zh_path_set"          = "PATH: already set"
    "zh_diag"              = "Running system diagnostics..."
    "zh_online"            = "ONLINE"
    "zh_standby"           = "STANDBY (auto-starts on launch)"
    "zh_ready"             = "READY"
    "zh_warning"           = "WARNING"
    "zh_loaded"            = "LOADED"
    "zh_not_loaded"        = "not loaded"
    "zh_path_reopen"       = "Not in PATH (restart terminal to fix)"
    "zh_complete"          = "INSTALL  COMPLETE !!"
    "zh_usage"             = "Usage:"
    "zh_mode_interactive"  = "Interactive mode"
    "zh_mode_oneshot"      = "One-shot"
    "zh_mode_auto"         = "Auto-detect network"
    "zh_settings"          = "Settings:"
    "zh_label_model"       = "Model"
    "zh_label_config"      = "Config"
    "zh_label_command"     = "Command"
    "zh_reopen"            = "Open a new terminal, then run eve-cli"
    "zh_enjoy"             = "  Enjoy Free AI Coding  "
    "zh_help_usage"        = "Usage: install.ps1 [--model MODEL_NAME] [--lang LANG]"
    "zh_help_model"        = "Specify Ollama model (e.g. qwen3:8b)"
    "zh_help_lang"         = "Language: ja, en, zh"
    "zh_unknown_opt"       = "Unknown option"
}

function msg($key) {
    $fullKey = "${script:LANG_CODE}_${key}"
    $val = $script:MESSAGES[$fullKey]
    if ($val) { return $val }
    # Fallback to English
    $enKey = "en_${key}"
    $val = $script:MESSAGES[$enKey]
    if ($val) { return $val }
    return $key
}

# ╔══════════════════════════════════════════════════════════════╗
# ║  Animation Engine                                          ║
# ╚══════════════════════════════════════════════════════════════╝

function Rainbow-Text($text) {
    $colors = $GRADIENT_NEON
    $len = $text.Length
    $numColors = $colors.Count
    $result = ""
    for ($i = 0; $i -lt $len; $i++) {
        $ci = $i % $numColors
        $result += "${ESC}[38;5;$($colors[$ci])m$($text[$i])"
    }
    Write-Host "${result}${NC}"
}

function Vapor-Text($text) {
    $colors = $GRADIENT_VAPOR
    $len = $text.Length
    $numColors = $colors.Count
    $result = ""
    for ($i = 0; $i -lt $len; $i++) {
        $ci = [math]::Floor(($i * $numColors / $len)) % $numColors
        $result += "${ESC}[38;5;$($colors[$ci])m$($text[$i])"
    }
    Write-Host "${result}${NC}"
}

function Vaporwave-Progress($msg, $durationSec = 2) {
    $width = 40
    $barChars = @([char]0x2591, [char]0x2592, [char]0x2593, [char]0x2588)  # light/medium/dark/full block
    $sparkles = @("*","o","O","@","#","+","~","=","!","^","&","%")
    $colors = @(198,199,207,213,177,171,165,129,93,57,51,50,49,48,47,46)
    $numColors = $colors.Count
    $steps = [math]::Max(10, [int]($durationSec * 20))

    for ($s = 0; $s -le $steps; $s++) {
        $pct = [math]::Floor($s * 100 / $steps)
        $filled = [math]::Floor($s * $width / $steps)
        $empty = $width - $filled

        $bar = ""
        for ($b = 0; $b -lt $filled; $b++) {
            $ci = [math]::Floor($b * $numColors / $width)
            $bar += "${ESC}[38;5;$($colors[$ci])m$([char]0x2588)"
        }
        if ($filled -lt $width) {
            $animIdx = $s % 4
            $ci = [math]::Floor($filled * $numColors / $width)
            $bar += "${ESC}[38;5;$($colors[$ci])m$($barChars[$animIdx])"
            $empty--
        }
        for ($b = 0; $b -lt $empty; $b++) {
            $bar += "${ESC}[38;5;237m$([char]0x2591)"
        }

        $paddedMsg = $msg.PadRight(30)
        $paddedPct = "$pct".PadLeft(3)
        Write-Host -NoNewline "`r  * ${BOLD}${CYAN}${paddedMsg}${NC} ${MAGENTA}|${NC}${bar}${MAGENTA}|${NC} ${BOLD}${NEON_GREEN}${paddedPct}%${NC} * "
        Start-Sleep -Milliseconds 50
    }
    # Complete line
    $paddedMsg = $msg.PadRight(30)
    $fullBar = ""
    for ($b = 0; $b -lt $width; $b++) {
        $ci = [math]::Floor($b * $numColors / $width)
        $fullBar += "${ESC}[38;5;$($colors[$ci])m$([char]0x2588)"
    }
    Write-Host "`r  + ${BOLD}${GREEN}${paddedMsg}${NC} ${MAGENTA}|${NC}${fullBar}${MAGENTA}|${NC} ${BOLD}${NEON_GREEN}100%${NC} !! "
}

function Step-Header($num, $title) {
    $icons = @(">>","::","[]","{}","<>","%%","##")
    $icon = $icons[$num - 1]
    $colors = @(51,87,123,159,165,171,177)
    $c = $colors[$num - 1]
    Write-Host ""
    Write-Host "  ${ESC}[38;5;${c}m======================================================${NC}"
    Write-Host "  ${icon}  ${ESC}[38;5;${c}m${BOLD}STEP ${num}/${TOTAL_STEPS}${NC}  ${BOLD}${WHITE}${title}${NC}"
    Write-Host "  ${ESC}[38;5;${c}m======================================================${NC}"
}

function Vapor-Success { param([string]$text) Write-Host "  ${NEON_GREEN}|${NC} [OK] ${BOLD}${MINT}${text}${NC}" }
function Vapor-Info    { param([string]$text) Write-Host "  ${CYAN}|${NC} [..] ${AQUA}${text}${NC}" }
function Vapor-Warn    { param([string]$text) Write-Host "  ${ORANGE}|${NC} [!!] ${YELLOW}${text}${NC}" }
function Vapor-Error   { param([string]$text) Write-Host "  ${RED}|${NC} [XX] ${RED}${BOLD}${text}${NC}" }

# ╔══════════════════════════════════════════════════════════════╗
# ║  Utility Functions                                         ║
# ╚══════════════════════════════════════════════════════════════╝

function Find-Command($name) {
    try {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Source }
    } catch {}
    return $null
}

function Find-Ollama {
    # Check PATH first
    $inPath = Find-Command "ollama"
    if ($inPath) { return $inPath }

    # Check common install locations
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe",
        "$env:ProgramFiles\Ollama\ollama.exe",
        "${env:ProgramFiles(x86)}\Ollama\ollama.exe",
        "$env:USERPROFILE\AppData\Local\Ollama\ollama.exe"
    )
    foreach ($p in $candidates) {
        if (Test-Path $p) { return $p }
    }
    return $null
}

function Find-Python {
    # Try py launcher first (recommended on Windows)
    $py = Find-Command "py"
    if ($py) { return "py -3" }

    # Try python3
    $python3 = Find-Command "python3"
    if ($python3) { return "python3" }

    # Try python (check version)
    $python = Find-Command "python"
    if ($python) {
        try {
            $ver = & python --version 2>&1
            if ($ver -match "Python 3") { return "python" }
        } catch {}
    }

    return $null
}

function Test-OllamaRunning {
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
        return ($resp.StatusCode -eq 200)
    } catch {
        return $false
    }
}

function Test-Truthy($value) {
    if ($null -eq $value) { return $false }
    switch ($value.ToString().ToLowerInvariant()) {
        "1" { return $true }
        "true" { return $true }
        "yes" { return $true }
        "on" { return $true }
        default { return $false }
    }
}

function New-TempDownloadPath($suffix = ".tmp") {
    return (Join-Path $env:TEMP ("eve-cli-" + [guid]::NewGuid().ToString("N") + $suffix))
}

function Get-Sha256($path) {
    try {
        return (Get-FileHash -Algorithm SHA256 -Path $path -ErrorAction Stop).Hash.ToLowerInvariant()
    } catch {
        return $null
    }
}

function Verify-Checksum($path, $expectedHash, $label) {
    if ([string]::IsNullOrWhiteSpace($expectedHash)) {
        Vapor-Warn "No checksum provided for $label; skipping verification."
        return $true
    }

    $actualHash = Get-Sha256 $path
    if (-not $actualHash) {
        Vapor-Error "Failed to compute checksum for $label"
        return $false
    }
    if ($actualHash -ne $expectedHash.ToLowerInvariant()) {
        Vapor-Error "Checksum verification failed for $label"
        Vapor-Error "  Expected: $expectedHash"
        Vapor-Error "  Actual:   $actualHash"
        Remove-Item $path -Force -ErrorAction SilentlyContinue
        return $false
    }

    Vapor-Info "Checksum verified for $label"
    return $true
}

function Download-File($url, $dest) {
    try {
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

function Resolve-InstallRef {
    if ($env:EVE_CLI_INSTALL_REF) {
        return $env:EVE_CLI_INSTALL_REF
    }

    try {
        $ProgressPreference = 'SilentlyContinue'
        $resp = Invoke-WebRequest -Uri "https://api.github.com/repos/NPO-Everyone-Engineer/eve-cli/commits/main" -UseBasicParsing -ErrorAction Stop
        $json = $resp.Content | ConvertFrom-Json
        return $json.sha
    } catch {
        return $null
    }
}

function Get-ManifestHash($manifestPath, $name) {
    try {
        $manifest = Get-Content $manifestPath -Encoding UTF8 -Raw | ConvertFrom-Json
        return $manifest.files.$name
    } catch {
        return $null
    }
}

function Download-RepoFileVerified($ref, $manifestPath, $name, $dest) {
    $expectedHash = Get-ManifestHash $manifestPath $name
    if ([string]::IsNullOrWhiteSpace($expectedHash)) {
        Vapor-Error "Checksum entry missing for $name"
        return $false
    }

    $tmpPath = New-TempDownloadPath ".download"
    try {
        $url = "https://raw.githubusercontent.com/NPO-Everyone-Engineer/eve-cli/$ref/$name"
        if (-not (Download-File $url $tmpPath)) {
            return $false
        }
        if (-not (Verify-Checksum $tmpPath $expectedHash $name)) {
            return $false
        }
        Move-Item -Path $tmpPath -Destination $dest -Force
        return $true
    } finally {
        if (Test-Path $tmpPath) {
            Remove-Item $tmpPath -Force -ErrorAction SilentlyContinue
        }
    }
}

function Confirm-UnverifiedRemoteInstaller($label, $url, $checksumEnvName, $allowEnvName) {
    $checksumValue = [System.Environment]::GetEnvironmentVariable($checksumEnvName)
    $allowValue = [System.Environment]::GetEnvironmentVariable($allowEnvName)
    $allowAllValue = [System.Environment]::GetEnvironmentVariable("EVE_CLI_ALLOW_UNVERIFIED_INSTALLERS")

    if (-not [string]::IsNullOrWhiteSpace($checksumValue)) {
        return $true
    }
    if ((Test-Truthy $allowValue) -or (Test-Truthy $allowAllValue)) {
        Vapor-Warn "Proceeding without checksum verification for $label because an override was provided."
        return $true
    }

    Write-Host ""
    Vapor-Warn "Unverified remote installer download detected."
    Write-Host "  $label: $url"
    Write-Host "  Provide checksum via $checksumEnvName=<sha256> to verify the download."
    Write-Host "  Or allow without verification via $allowEnvName=1"
    Write-Host "  Or allow all unverified installers via EVE_CLI_ALLOW_UNVERIFIED_INSTALLERS=1"

    try {
        if ([Console]::IsInputRedirected -or [Console]::IsOutputRedirected) {
            Vapor-Error "Refusing unverified remote installer in non-interactive mode."
            return $false
        }
    } catch {
        # If console state cannot be determined, continue to explicit prompt.
    }

    $reply = Read-Host "  Continue anyway? [y/N]"
    if ($reply -match '^(?i:y|yes)$') {
        return $true
    }

    Vapor-Error "Remote installer download aborted."
    return $false
}

# ╔══════════════════════════════════════════════════════════════╗
# ║  Help                                                      ║
# ╚══════════════════════════════════════════════════════════════╝

if ($Help) {
    Write-Host (msg "help_usage")
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  --model MODEL  $(msg 'help_model')"
    Write-Host "  --lang LANG    $(msg 'help_lang')"
    Write-Host "  --help         Show this help"
    exit 0
}

# ╔══════════════════════════════════════════════════════════════╗
# ║  Title Screen                                              ║
# ╚══════════════════════════════════════════════════════════════╝

Write-Host ""
Write-Host ""

# Animated entrance
for ($i = 0; $i -lt 3; $i++) {
    Write-Host -NoNewline "`r  <*> <+> <o>  "
    Start-Sleep -Milliseconds 150
    Write-Host -NoNewline "`r  <o> <*> <+>  "
    Start-Sleep -Milliseconds 150
    Write-Host -NoNewline "`r  <+> <o> <*>  "
    Start-Sleep -Milliseconds 150
}
Write-Host "`r              "

# Heart bar
$heartBar = "  ${PINK}<3${MAGENTA}<3${PURPLE}<3${CYAN}<3${AQUA}<3${MINT}<3${NEON_GREEN}<3${YELLOW}<3${ORANGE}<3${CORAL}<3${HOT_PINK}<3${PINK}<3${MAGENTA}<3${PURPLE}<3${CYAN}<3${AQUA}<3${NC}"
Write-Host $heartBar
Write-Host ""

# ASCII Logo
Write-Host "${MAGENTA}${BOLD}"
Write-Host "    ███████╗██╗   ██╗███████╗     ██████╗██╗     ██╗"
Write-Host "    ██╔════╝██║   ██║██╔════╝    ██╔════╝██║     ██║"
Write-Host "    █████╗  ██║   ██║█████╗      ██║     ██║     ██║"
Write-Host "    ██╔══╝  ╚██╗ ██╔╝██╔══╝      ██║     ██║     ██║"
Write-Host "    ███████╗ ╚████╔╝ ███████╗    ╚██████╗███████╗██║"
Write-Host "    ╚══════╝  ╚═══╝  ╚══════╝     ╚═════╝╚══════╝╚═╝"
Write-Host "${NC}${CYAN}${BOLD}"
Write-Host "        Everyone.Engineer Coding Agent"
Write-Host "${NC}"
Write-Host $heartBar
Write-Host ""

Vapor-Text "  $(msg 'subtitle')"
Write-Host ""
Rainbow-Text "  ================================================================"
Write-Host "  ${PINK}<3${NC} ${BOLD}${WHITE}$(msg 'tagline')${NC} ${PINK}<3${NC}"
Rainbow-Text "  ================================================================"
Write-Host ""
Start-Sleep -Seconds 1

Write-Host "  ${DIM}${CYAN}$(msg 'boot1')${NC}"
Start-Sleep -Milliseconds 300
Write-Host "  ${DIM}${PURPLE}$(msg 'boot2')${NC}"
Start-Sleep -Milliseconds 300
Write-Host "  ${DIM}${PINK}$(msg 'boot3')${NC}"
Start-Sleep -Milliseconds 300
Write-Host "  ${BOLD}${NEON_GREEN}  >> $(msg 'boot4')${NC}"
Start-Sleep -Milliseconds 500
Write-Host ""

# ╔══════════════════════════════════════════════════════════════╗
# ║  Step 1: System Scan                                       ║
# ╚══════════════════════════════════════════════════════════════╝

Step-Header 1 (msg "step1")

Vaporwave-Progress (msg "hw_scan") 1

$ARCH = $env:PROCESSOR_ARCHITECTURE
Vapor-Info "OS: Windows / Arch: $ARCH"

if ($ARCH -eq "AMD64" -or $ARCH -eq "ARM64") {
    Vapor-Success "$(msg 'windows_ok') ($ARCH)"
} else {
    Vapor-Error "$(msg 'unsupported_arch'): $ARCH"
    Write-Host "  Supported: AMD64, ARM64"
    exit 1
}

# Windows version info
try {
    $osVer = [System.Environment]::OSVersion.Version
    $osBuild = (Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue).Caption
    if ($osBuild) {
        Vapor-Info "Version: $osBuild (Build $($osVer.Build))"
    }
} catch {}

# ╔══════════════════════════════════════════════════════════════╗
# ║  Step 2: Memory Analysis                                   ║
# ╚══════════════════════════════════════════════════════════════╝

Step-Header 2 (msg "step2")

$RAM_BYTES = 0
try {
    $RAM_BYTES = (Get-CimInstance Win32_ComputerSystem -ErrorAction SilentlyContinue).TotalPhysicalMemory
} catch {
    try {
        $RAM_BYTES = (Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory
    } catch {
        Vapor-Warn "Could not detect RAM size, assuming 16GB"
        $RAM_BYTES = 16 * 1073741824
    }
}
$RAM_GB = [math]::Floor($RAM_BYTES / 1073741824)

Vaporwave-Progress (msg "mem_scan") 1

# RAM bar visualization
$RAM_DISPLAY_MAX = 128
$RAM_BAR_WIDTH = 30
$RAM_FILLED = [math]::Min([math]::Floor($RAM_GB * $RAM_BAR_WIDTH / $RAM_DISPLAY_MAX), $RAM_BAR_WIDTH)
$RAM_EMPTY = $RAM_BAR_WIDTH - $RAM_FILLED

$RAM_BAR = ""
for ($i = 0; $i -lt $RAM_FILLED; $i++) { $RAM_BAR += [char]0x2588 }
for ($i = 0; $i -lt $RAM_EMPTY; $i++) { $RAM_BAR += [char]0x2591 }

Write-Host "  ${PURPLE}|${NC} :: ${BOLD}${WHITE}$(msg 'mem_label'): ${NEON_GREEN}${RAM_GB}GB${NC}"
Write-Host "  ${PURPLE}|${NC}    ${CYAN}|${NEON_GREEN}${RAM_BAR}${CYAN}|${NC} ${DIM}${GRAY}(${RAM_GB}/${RAM_DISPLAY_MAX}GB)${NC}"
Write-Host ""

# Model selection
$SIDECAR_MODEL = ""
$MANUAL_MODEL = $Model

if ($MANUAL_MODEL) {
    $MODEL = $MANUAL_MODEL
    Vapor-Info "$(msg 'manual_model'): $MODEL"
} elseif ($RAM_GB -ge 32) {
    $MODEL = "qwen3-coder:30b"
    $SIDECAR_MODEL = "qwen3:8b"
    Write-Host "  ${NEON_GREEN}|${NC} ++ ${BOLD}${YELLOW}*** BEST  MODEL ***${NC}"
    Write-Host "  ${NEON_GREEN}|${NC}    ${BOLD}${WHITE}${MODEL}${NC} ${DIM}(19GB, MoE 3.3B active, $(msg 'model_best'))${NC}"
    Write-Host "  ${NEON_GREEN}|${NC}    ${DIM}+ sidecar: ${SIDECAR_MODEL} (5GB, fast helper)${NC}"
} elseif ($RAM_GB -ge 16) {
    $MODEL = "qwen3:8b"
    $SIDECAR_MODEL = "qwen3:1.7b"
    Write-Host "  ${MINT}|${NC} ** ${BOLD}${CYAN}** GREAT  MODEL **${NC}"
    Write-Host "  ${MINT}|${NC}    ${BOLD}${WHITE}${MODEL}${NC} ${DIM}(5GB, $(msg 'model_great'))${NC}"
    Write-Host "  ${MINT}|${NC}    ${DIM}+ sidecar: ${SIDECAR_MODEL} (1GB, fast helper)${NC}"
} elseif ($RAM_GB -ge 8) {
    $MODEL = "qwen3:1.7b"
    Vapor-Warn "$MODEL ($(msg 'model_min'))"
    Vapor-Warn (msg "model_recommend")
} else {
    Vapor-Error "$(msg 'mem_lack'): ${RAM_GB}GB ($(msg 'mem_lack_min'))"
    Write-Host ""
    Write-Host "  $(msg 'mem_lack_hint1')"
    Write-Host "  $(msg 'mem_lack_hint2')"
    exit 1
}

# ╔══════════════════════════════════════════════════════════════╗
# ║  Step 3: Package Install                                   ║
# ╚══════════════════════════════════════════════════════════════╝

Step-Header 3 (msg "step3")

$hasWinget = $null -ne (Find-Command "winget")

# --- Python ---
$PYTHON_CMD = Find-Python

if ($PYTHON_CMD) {
    try {
        $pyVer = ""
        if ($PYTHON_CMD -eq "py -3") {
            $pyVer = & py -3 --version 2>&1
        } else {
            $pyVer = & $PYTHON_CMD --version 2>&1
        }
        Vapor-Success "Python3 :: $(msg 'installed') ($pyVer)"
    } catch {
        Vapor-Success "Python3 :: $(msg 'installed')"
    }
} else {
    Vapor-Info "Python3 :: $(msg 'installing')"
    $pyInstalled = $false

    if ($hasWinget) {
        Write-Host "  ${DIM}  Attempting: winget install Python.Python.3.12${NC}"
        try {
            $result = & winget install Python.Python.3.12 --accept-source-agreements --accept-package-agreements 2>&1
            # Refresh PATH
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            $PYTHON_CMD = Find-Python
            if ($PYTHON_CMD) {
                $pyInstalled = $true
                Vapor-Success "Python3 :: $(msg 'install_done')"
            }
        } catch {}
    }

    if (-not $pyInstalled) {
        Vapor-Error "Python3 :: $(msg 'install_fail')"
        Vapor-Warn (msg "python_manual")
        Vapor-Warn (msg "install_fail_hint")
    }
}

# --- Ollama ---
$OLLAMA_PATH = Find-Ollama

if ($OLLAMA_PATH) {
    try {
        $ollamaVer = & $OLLAMA_PATH --version 2>&1
        Vapor-Success "Ollama :: $(msg 'installed') ($ollamaVer)"
    } catch {
        Vapor-Success "Ollama :: $(msg 'installed')"
    }
} else {
    Vapor-Info "Ollama :: $(msg 'installing')"
    $ollamaInstalled = $false

    if ($hasWinget) {
        Write-Host "  ${DIM}  Attempting: winget install Ollama.Ollama${NC}"
        try {
            $result = & winget install Ollama.Ollama --accept-source-agreements --accept-package-agreements 2>&1
            # Refresh PATH
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            $OLLAMA_PATH = Find-Ollama
            if ($OLLAMA_PATH) {
                $ollamaInstalled = $true
                Vapor-Success "Ollama :: $(msg 'install_done')"
            }
        } catch {}
    }

    if (-not $ollamaInstalled) {
        # Fallback: direct download
        $setupUrl = "https://ollama.com/download/OllamaSetup.exe"
        $setupPath = Join-Path $env:TEMP "OllamaSetup.exe"
        $setupChecksum = [System.Environment]::GetEnvironmentVariable("EVE_CLI_OLLAMA_SETUP_SHA256")
        Vapor-Info "Downloading OllamaSetup.exe..."

        if ((Confirm-UnverifiedRemoteInstaller "OllamaSetup.exe" $setupUrl "EVE_CLI_OLLAMA_SETUP_SHA256" "EVE_CLI_ALLOW_UNVERIFIED_OLLAMA_SETUP") -and
                (Download-File $setupUrl $setupPath)) {
            if (-not (Verify-Checksum $setupPath $setupChecksum "OllamaSetup.exe")) {
                Vapor-Error "Ollama :: $(msg 'install_fail')"
                Vapor-Warn (msg "ollama_manual")
                Remove-Item $setupPath -Force -ErrorAction SilentlyContinue
                exit 1
            }
            Vapor-Info "Running OllamaSetup.exe (follow the installer prompts)..."
            try {
                Start-Process -FilePath $setupPath -Wait
                # Refresh PATH
                $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
                $OLLAMA_PATH = Find-Ollama
                if ($OLLAMA_PATH) {
                    $ollamaInstalled = $true
                    Vapor-Success "Ollama :: $(msg 'install_done')"
                }
            } catch {
                Vapor-Error "Ollama :: $(msg 'install_fail')"
            }
            Remove-Item $setupPath -Force -ErrorAction SilentlyContinue
        } else {
            Vapor-Error "Ollama :: $(msg 'install_fail')"
            Vapor-Warn (msg "ollama_manual")
            Vapor-Warn (msg "install_fail_hint")
        }
    }
}

# ╔══════════════════════════════════════════════════════════════╗
# ║  Step 4: AI Model Download                                ║
# ╚══════════════════════════════════════════════════════════════╝

Step-Header 4 (msg "step4")

$OLLAMA_PATH = Find-Ollama
if (-not $OLLAMA_PATH) {
    Vapor-Error "Ollama not found. Cannot download models."
    Vapor-Warn "Install Ollama first, then re-run this script."
} else {
    # Start Ollama if not running
    if (-not (Test-OllamaRunning)) {
        Vapor-Info (msg "ollama_starting")
        try {
            Start-Process -FilePath $OLLAMA_PATH -ArgumentList "serve" -WindowStyle Hidden -ErrorAction SilentlyContinue
        } catch {
            Vapor-Warn "Could not start Ollama automatically. Trying alternative..."
            try {
                & $OLLAMA_PATH serve *> $null &
            } catch {}
        }

        # Wait for Ollama to be ready (max 30 seconds)
        $waitSparkles = @("::", "**", ">>", "<<")
        for ($i = 1; $i -le 30; $i++) {
            if (Test-OllamaRunning) { break }
            $si = ($i - 1) % $waitSparkles.Count
            $paddedLabel = (msg "ollama_wait").PadRight(35)
            Write-Host -NoNewline "`r  $($waitSparkles[$si]) ${CYAN}${paddedLabel}${NC} ${DIM}${GRAY}${i}s${NC}  "
            Start-Sleep -Seconds 1
        }
        Write-Host "`r$(' ' * 60)`r" -NoNewline

        if (Test-OllamaRunning) {
            Vapor-Success "Ollama :: $(msg 'online')"
        } else {
            Vapor-Error "Ollama failed to start after 30 seconds."
            Write-Host "  Possible causes:"
            Write-Host "    - Ollama was not installed correctly"
            Write-Host "    - Another process is using port 11434"
            Write-Host "  Try:"
            Write-Host "    ollama serve    (in a separate terminal)"
            Write-Host "  Then re-run this script."
        }
    }

    # Check disk space
    try {
        $drive = (Get-Item $env:USERPROFILE).PSDrive
        $freeGB = [math]::Floor($drive.Free / 1GB)
        if ($freeGB -lt 20) {
            Vapor-Warn "Low disk space: ${freeGB}GB available (20GB+ recommended for model download)"
        }
    } catch {}

    # Download model function
    function Download-Model($modelName, $label) {
        # Check if already downloaded
        try {
            $tagsResp = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
            if ($tagsResp.Content -match [regex]::Escape($modelName)) {
                Vapor-Success "$modelName $(msg 'model_downloaded') :: $label"
                return $true
            }
        } catch {}

        Write-Host ""
        Write-Host "  $heartBar"
        Write-Host "  ${BOLD}${MAGENTA}  >>  ${WHITE}${modelName} ${CYAN}$(msg 'model_downloading') ${label}${NC}"
        Write-Host "  ${DIM}${AQUA}      $(msg 'model_download_hint')${NC}"
        Write-Host "  $heartBar"
        Write-Host ""

        # Pull with retry (up to 3 attempts)
        $pullOk = $false
        for ($attempt = 1; $attempt -le 3; $attempt++) {
            try {
                & $OLLAMA_PATH pull $modelName 2>&1
                if ($LASTEXITCODE -eq 0) {
                    $pullOk = $true
                    break
                }
            } catch {}
            if ($attempt -lt 3) {
                Write-Host "  ${YELLOW}[!!] Download interrupted (attempt ${attempt}/3), retrying in 5s...${NC}"
                Start-Sleep -Seconds 5
            }
        }

        if (-not $pullOk) {
            Write-Host "  ${RED}[!!] Download failed after 3 attempts${NC}"
            Write-Host "  ${DIM}Retry manually: ollama pull ${modelName}${NC}"
            return $false
        }

        # Verify download
        try {
            $tagsResp = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
            if ($tagsResp.Content -match [regex]::Escape($modelName)) {
                Write-Host "  $heartBar"
                Vapor-Success "$modelName $(msg 'model_dl_done') :: $label"
                Write-Host "  $heartBar"
                return $true
            }
        } catch {}

        Vapor-Warn "$modelName $(msg 'install_fail') - ollama pull $modelName"
        return $false
    }

    # Download main model
    if (Test-OllamaRunning) {
        if (-not (Download-Model $MODEL "(main)")) {
            Vapor-Error "Failed to download main model: $MODEL"
            Vapor-Warn "Try manually: ollama pull $MODEL"
        }

        # Download sidecar model if different from main
        if ($SIDECAR_MODEL -and $SIDECAR_MODEL -ne $MODEL) {
            if (-not (Download-Model $SIDECAR_MODEL "(sidecar)")) {
                Vapor-Warn "Sidecar model download failed (non-critical): $SIDECAR_MODEL"
            }
        }
    }
}

# ╔══════════════════════════════════════════════════════════════╗
# ║  Step 5: File Deploy                                       ║
# ╚══════════════════════════════════════════════════════════════╝

Step-Header 5 (msg "step5")

$LIB_DIR = Join-Path $env:USERPROFILE ".local\lib\eve-cli"
$BIN_DIR = Join-Path $env:USERPROFILE ".local\bin"

# Create directories
New-Item -ItemType Directory -Path $LIB_DIR -Force -ErrorAction SilentlyContinue | Out-Null
New-Item -ItemType Directory -Path $BIN_DIR -Force -ErrorAction SilentlyContinue | Out-Null

Vaporwave-Progress (msg "file_deploy") 1.5

# Detect source: local clone or GitHub download
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path -ErrorAction SilentlyContinue
$sourceLocal = $false

if ($SCRIPT_DIR -and (Test-Path (Join-Path $SCRIPT_DIR "eve-coder.py"))) {
    $sourceLocal = $true
    Vapor-Info (msg "source_local")

    Copy-Item (Join-Path $SCRIPT_DIR "eve-coder.py") (Join-Path $LIB_DIR "eve-coder.py") -Force
    if (Test-Path (Join-Path $SCRIPT_DIR "eve-cli.sh")) {
        Copy-Item (Join-Path $SCRIPT_DIR "eve-cli.sh") $LIB_DIR -Force
    }
} else {
    Vapor-Info (msg "source_github")
    $INSTALL_REF = Resolve-InstallRef
    if (-not $INSTALL_REF) {
        Vapor-Error "Failed to resolve an immutable GitHub ref for installer downloads"
        Write-Host "  Re-run from a full checkout, or set EVE_CLI_INSTALL_REF=<commit-sha>."
        exit 1
    }
    $manifestPath = New-TempDownloadPath ".json"
    if (-not (Download-File "https://raw.githubusercontent.com/NPO-Everyone-Engineer/eve-cli/$INSTALL_REF/install-manifest.json" $manifestPath)) {
        Vapor-Error "Failed to download install-manifest.json from GitHub"
        Write-Host "  Ref: $INSTALL_REF"
        exit 1
    }
    Vapor-Info "Verified ref: $INSTALL_REF"

    $dlOk = Download-RepoFileVerified $INSTALL_REF $manifestPath "eve-coder.py" (Join-Path $LIB_DIR "eve-coder.py")
    if (-not $dlOk) {
        Vapor-Error "Failed to download eve-coder.py from GitHub"
        Write-Host "  Check your internet connection or verify install-manifest.json."
        Remove-Item $manifestPath -Force -ErrorAction SilentlyContinue
        exit 1
    }

    $dlOk2 = Download-RepoFileVerified $INSTALL_REF $manifestPath "eve-cli.sh" (Join-Path $LIB_DIR "eve-cli.sh")
    if (-not $dlOk2) {
        Vapor-Error "Failed to download eve-cli.sh from GitHub"
        Write-Host "  Check your internet connection or verify install-manifest.json."
        Remove-Item $manifestPath -Force -ErrorAction SilentlyContinue
        exit 1
    }
    Remove-Item $manifestPath -Force -ErrorAction SilentlyContinue
}

# Create eve-cli.ps1 launcher
$launcherPs1 = Join-Path $BIN_DIR "eve-cli.ps1"
$launcherContent = @'
# eve-cli.ps1 - EvE CLI launcher for Windows
# Auto-generated by install.ps1

$ErrorActionPreference = "Continue"
$CONFIG_FILE = Join-Path $env:USERPROFILE ".config\eve-cli\config"
$LIB_DIR = Join-Path $env:USERPROFILE ".local\lib\eve-cli"
$EVE_CODER = Join-Path $LIB_DIR "eve-coder.py"

# Defaults
$MODEL = ""
$SIDECAR_MODEL = ""
$OLLAMA_HOST = "http://localhost:11434"

# Read config (safe parser)
if (Test-Path $CONFIG_FILE) {
    foreach ($line in Get-Content $CONFIG_FILE -Encoding UTF8) {
        $line = $line.Trim()
        if ($line -match '^#' -or $line -eq '') { continue }
        if ($line -match '^(\w+)=(.*)$') {
            $k = $Matches[1]
            $v = $Matches[2].Trim('"', "'", ' ')
            switch ($k) {
                "MODEL"         { $MODEL = $v }
                "SIDECAR_MODEL" { $SIDECAR_MODEL = $v }
                "OLLAMA_HOST"   { $OLLAMA_HOST = $v }
            }
        }
    }
}

# Find Python
$PY = $null
if (Get-Command "py" -ErrorAction SilentlyContinue) { $PY = "py" }
elseif (Get-Command "python3" -ErrorAction SilentlyContinue) { $PY = "python3" }
elseif (Get-Command "python" -ErrorAction SilentlyContinue) { $PY = "python" }

if (-not $PY) {
    Write-Host "Error: Python 3 not found. Install from https://www.python.org/downloads/"
    exit 1
}

if (-not (Test-Path $EVE_CODER)) {
    Write-Host "Error: eve-coder.py not found at $EVE_CODER"
    Write-Host "Re-run the installer: .\install.ps1"
    exit 1
}

# Build arguments
$pyArgs = @($EVE_CODER)
if ($MODEL) { $pyArgs += "--model"; $pyArgs += $MODEL }
if ($SIDECAR_MODEL) { $pyArgs += "--sidecar-model"; $pyArgs += $SIDECAR_MODEL }
$pyArgs += $args

$env:OLLAMA_HOST = $OLLAMA_HOST

if ($PY -eq "py") {
    & py -3 @pyArgs
} else {
    & $PY @pyArgs
}
'@
Set-Content -Path $launcherPs1 -Value $launcherContent -Encoding UTF8

# Create eve-cli.cmd wrapper (for CMD users)
$launcherCmd = Join-Path $BIN_DIR "eve-cli.cmd"
$cmdContent = @"
@echo off
REM eve-cli.cmd - EvE CLI launcher for Windows (CMD wrapper)
REM Auto-generated by install.ps1
powershell.exe -ExecutionPolicy Bypass -File "%USERPROFILE%\.local\bin\eve-cli.ps1" %*
"@
Set-Content -Path $launcherCmd -Value $cmdContent -Encoding ASCII

Vapor-Success "eve-coder.py -> $LIB_DIR\"
Vapor-Success "eve-cli.ps1  -> $BIN_DIR\"
Vapor-Success "eve-cli.cmd  -> $BIN_DIR\"

# ╔══════════════════════════════════════════════════════════════╗
# ║  Step 6: Config Generate                                   ║
# ╚══════════════════════════════════════════════════════════════╝

Step-Header 6 (msg "step6")

$CONFIG_DIR = Join-Path $env:USERPROFILE ".config\eve-cli"
$CONFIG_FILE = Join-Path $CONFIG_DIR "config"

New-Item -ItemType Directory -Path $CONFIG_DIR -Force -ErrorAction SilentlyContinue | Out-Null

Vaporwave-Progress (msg "config_gen") 1

if (Test-Path $CONFIG_FILE) {
    Vapor-Warn (msg "config_exists")
} else {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $configContent = @"
# eve-cli config
# Auto-generated: $timestamp
# Engine: eve-coder (direct Ollama, no proxy needed)

MODEL="$MODEL"
SIDECAR_MODEL="$SIDECAR_MODEL"
OLLAMA_HOST="http://localhost:11434"
"@
    Set-Content -Path $CONFIG_FILE -Value $configContent -Encoding UTF8
    Vapor-Success "$(msg 'config_file'): $CONFIG_FILE"
}

# Add to User PATH
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$BIN_IN_PATH = $false
if ($userPath -and $userPath.Split(';') -contains $BIN_DIR) {
    $BIN_IN_PATH = $true
}

if (-not $BIN_IN_PATH) {
    try {
        if ($userPath) {
            $newPath = "${BIN_DIR};${userPath}"
        } else {
            $newPath = $BIN_DIR
        }
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        # Also update current session
        $env:Path = "${BIN_DIR};${env:Path}"
        Vapor-Success "$(msg 'path_added') -> User PATH"
    } catch {
        Vapor-Warn "Could not add to PATH automatically."
        Vapor-Warn "Manually add this to your PATH: $BIN_DIR"
    }
} else {
    Vapor-Success (msg "path_set")
}

# ╔══════════════════════════════════════════════════════════════╗
# ║  Step 7: System Test                                       ║
# ╚══════════════════════════════════════════════════════════════╝

Step-Header 7 (msg "step7")

Write-Host ""
Write-Host "  ${CYAN}|${NC} :: ${BOLD}${WHITE}$(msg 'diag')${NC}"
Write-Host ""

# Ollama connectivity
if (Test-OllamaRunning) {
    Vapor-Success "Ollama Server       -> [ON] $(msg 'online')"
} else {
    Vapor-Warn    "Ollama Server       -> [--] $(msg 'standby')"
}

# Python syntax check
$eveCoder = Join-Path $LIB_DIR "eve-coder.py"
if (Test-Path $eveCoder) {
    $PYTHON_CMD = Find-Python
    if ($PYTHON_CMD) {
        $syntaxOk = $false
        try {
            if ($PYTHON_CMD -eq "py -3") {
                $result = & py -3 -c "import ast; ast.parse(open(r'$eveCoder', encoding='utf-8').read())" 2>&1
            } else {
                $result = & $PYTHON_CMD -c "import ast; ast.parse(open(r'$eveCoder', encoding='utf-8').read())" 2>&1
            }
            if ($LASTEXITCODE -eq 0) { $syntaxOk = $true }
        } catch {}
        if ($syntaxOk) {
            Vapor-Success "eve-coder.py       -> [OK] $(msg 'ready')"
        } else {
            Vapor-Warn    "eve-coder.py       -> [!!] $(msg 'warning') (syntax error)"
        }
    } else {
        Vapor-Warn "eve-coder.py       -> [!!] Python not found for syntax check"
    }
} else {
    Vapor-Error "eve-coder.py       -> [XX] File not found!"
}

# Model availability
if (Test-OllamaRunning) {
    try {
        $tagsResp = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        if ($tagsResp.Content -match [regex]::Escape($MODEL)) {
            Vapor-Success "AI Model ($MODEL) -> [OK] $(msg 'loaded')"
        } else {
            Vapor-Warn    "AI Model ($MODEL) -> [--] $(msg 'not_loaded')"
        }

        if ($SIDECAR_MODEL -and $SIDECAR_MODEL -ne $MODEL) {
            if ($tagsResp.Content -match [regex]::Escape($SIDECAR_MODEL)) {
                Vapor-Success "Sidecar  ($SIDECAR_MODEL) -> [OK] $(msg 'loaded')"
            } else {
                Vapor-Warn    "Sidecar  ($SIDECAR_MODEL) -> [--] $(msg 'not_loaded')"
            }
        }
    } catch {
        Vapor-Warn "AI Model ($MODEL) -> [--] Could not check"
    }
} else {
    Vapor-Warn "AI Model ($MODEL) -> [--] Ollama not running"
}

# ╔══════════════════════════════════════════════════════════════╗
# ║  COMPLETE !!                                               ║
# ╚══════════════════════════════════════════════════════════════╝

Write-Host ""
Write-Host ""

# Celebration animation
$frames = @(
    "  ** ## ++ -- oo == oo -- ++ ## **",
    "  ## ** -- ++ == oo == ++ -- ** ##",
    "  ++ -- ** ## oo == oo ## ** -- ++",
    "  -- ++ ## ** == oo == ** ## ++ --"
)
for ($r = 0; $r -lt 3; $r++) {
    foreach ($frame in $frames) {
        Write-Host -NoNewline "`r${frame}"
        Start-Sleep -Milliseconds 100
    }
}
Write-Host ""
Write-Host ""

# Massive completion banner
Write-Host $heartBar
Write-Host ""
Rainbow-Text "    ================================================================"
Write-Host ""
Write-Host "          !!!!  ${BOLD}${MAGENTA}$(msg 'complete')${NC}  !!!!"
Write-Host ""
Rainbow-Text "    ================================================================"
Write-Host ""
Write-Host $heartBar
Write-Host ""

Write-Host ""
Rainbow-Text "    ========================================================="
Write-Host ""
Write-Host "    ${BOLD}${WHITE}>> $(msg 'usage')${NC}"
Write-Host ""
Write-Host "    ${PINK}>${NC} ${BOLD}${CYAN}eve-cli${NC}                     ${DIM}$(msg 'mode_interactive')${NC}"
Write-Host "    ${PINK}>${NC} ${BOLD}${CYAN}eve-cli -p `"...`"${NC}            ${DIM}$(msg 'mode_oneshot')${NC}"
Write-Host "    ${PINK}>${NC} ${BOLD}${CYAN}eve-cli --auto${NC}              ${DIM}$(msg 'mode_auto')${NC}"
Write-Host ""
Rainbow-Text "    ========================================================="
Write-Host ""
Write-Host "    ${BOLD}${WHITE}%% $(msg 'settings')${NC}"
Write-Host "    ${PURPLE}|${NC} $(msg 'label_model'):     ${BOLD}${NEON_GREEN}${MODEL}${NC}"
if ($SIDECAR_MODEL -and $SIDECAR_MODEL -ne $MODEL) {
    Write-Host "    ${PURPLE}|${NC} Sidecar:    ${BOLD}${AQUA}${SIDECAR_MODEL}${NC}"
}
Write-Host "    ${PURPLE}|${NC} $(msg 'label_config'):       ${AQUA}${CONFIG_FILE}${NC}"
Write-Host "    ${PURPLE}|${NC} $(msg 'label_command'):   ${AQUA}${BIN_DIR}\eve-cli.cmd${NC}"
Write-Host ""
Rainbow-Text "    ========================================================="
Write-Host ""
Write-Host "    ${YELLOW}${BOLD}>> $(msg 'reopen') <<${NC}"
Write-Host ""
Write-Host "    ${GREEN}Or run this in the current terminal:${NC}"
Write-Host "    ${BOLD}eve-cli${NC}"
Write-Host ""
Write-Host ""

Vapor-Text "    $(msg 'enjoy')"
Write-Host ""
Write-Host ""
