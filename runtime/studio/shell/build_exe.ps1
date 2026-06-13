# build_exe.ps1 — Build ChaseOS-Studio.exe from vault root
#
# Usage (from any directory):
#   powershell -ExecutionPolicy Bypass -File "C:\path\to\vault\runtime\studio\shell\build_exe.ps1"
#
# Or from the vault root:
#   .\runtime\studio\shell\build_exe.ps1 [-VaultRoot "C:\path\to\vault"] [-Dev] [-Console]
#
# Output: dist\studio\ChaseOS-Studio.exe

param(
    [string]$VaultRoot = "",
    [switch]$Dev,       # keep console window + debug symbols
    [switch]$Console,    # force console=True even in non-Dev build
    [switch]$Clean,      # force PyInstaller to refresh bundled frontend/runtime assets
    [switch]$NoShortcut, # build executable only; do not mutate Desktop shortcuts
    [string]$SignThumbprint = "",
    [ValidateSet("CurrentUser", "LocalMachine")]
    [string]$SignStoreLocation = "CurrentUser",
    [string]$TimestampServer = ""
)

$ErrorActionPreference = 'Stop'
# Note: $PSNativeCommandUseErrorActionPreference intentionally NOT set —
# PyInstaller writes progress to stderr; treating that as a fatal error breaks the build.

# ── Resolve vault root ────────────────────────────────────────────────────────
if ($VaultRoot -eq "") {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $VaultRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $ScriptDir))
}
$VaultRoot = (Resolve-Path $VaultRoot).Path

if (-not (Test-Path "$VaultRoot\CLAUDE.md") -and -not (Test-Path "$VaultRoot\runtime")) {
    Write-Error "Not a ChaseOS vault: $VaultRoot"
    exit 1
}

Write-Host "==> ChaseOS Studio .exe builder"
Write-Host "    Vault root : $VaultRoot"

# ── Activate venv ────────────────────────────────────────────────────────────
$VenvActivate = "$VaultRoot\.venv\Scripts\Activate.ps1"
if (-not (Test-Path $VenvActivate)) {
    Write-Error "No .venv found at $VaultRoot\.venv. Run: python -m venv .venv && pip install -e ."
    exit 1
}

Write-Host "==> Activating venv..."
. $VenvActivate

# ── Ensure PyInstaller is installed ──────────────────────────────────────────
$piVer = python -c "import PyInstaller; print(PyInstaller.__version__)" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "==> Installing PyInstaller..."
    pip install "pyinstaller>=6.0" --quiet
}
else {
    Write-Host "    PyInstaller $piVer"
}

# ── Ensure PyQt6 stack is installed (pywebview Qt backend) ───────────────────
# pythonnet/winforms unavailable on Python 3.14.x; Qt backend used instead.
$qt6Check = python -c "from PyQt6 import QtCore; from PyQt6 import QtWebEngineWidgets; import qtpy" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "==> Installing PyQt6 + PyQt6-WebEngine + qtpy (pywebview Qt backend)..."
    pip install PyQt6 PyQt6-WebEngine qtpy --quiet
}
else {
    Write-Host "    PyQt6 + WebEngine + qtpy: OK"
}

# ── Run PyInstaller ───────────────────────────────────────────────────────────
Push-Location $VaultRoot

$SpecFile = "runtime\studio\shell\ChaseOS-Studio.spec"
$DistPath = "dist\studio"
$StudioDistPath = "build\studio-dist"
$WorkPath = "build\studio"
$LogFile  = "build\studio-build.log"
$FinalDistPath = Join-Path $VaultRoot $DistPath
$StudioBuildOutput = Join-Path $VaultRoot (Join-Path $StudioDistPath "ChaseOS-Studio.exe")
$ExpectedOutput = Join-Path $FinalDistPath "ChaseOS-Studio.exe"
$InstallerPath = Join-Path $FinalDistPath "ChaseOS-Installer.exe"

New-Item -ItemType Directory -Force -Path "build" | Out-Null
New-Item -ItemType Directory -Force -Path $WorkPath | Out-Null
New-Item -ItemType Directory -Force -Path $StudioDistPath | Out-Null
New-Item -ItemType Directory -Force -Path $FinalDistPath | Out-Null

$InstallerHashBefore = $null
if (Test-Path -LiteralPath $InstallerPath -PathType Leaf) {
    $InstallerHashBefore = (Get-FileHash -Algorithm SHA256 -LiteralPath $InstallerPath).Hash
}

Write-Host "==> Running PyInstaller..."
$piArgs = @(
    $SpecFile,
    "--distpath", $StudioDistPath,
    "--workpath", $WorkPath,
    "--noconfirm"
)

if ($Dev -or $Console) {
    $piArgs += "--debug", "all"
}

if ($Clean) {
    $piArgs += "--clean"
}

# PyInstaller writes progress to stderr. Redirect all streams to the build log
# while keeping the native process in this shell so PowerShell waits for the
# real exit code and does not fail on INFO/WARNING stderr records.
Remove-Item -Force -ErrorAction SilentlyContinue $LogFile
$PyInstallerExe = @((Get-Command pyinstaller -CommandType Application -ErrorAction Stop))[0].Source
$ErrorActionPreference = 'Continue'
& $PyInstallerExe @piArgs *> $LogFile
$piBuildExit = $LASTEXITCODE
$ErrorActionPreference = 'Stop'

if (Test-Path -LiteralPath $LogFile -PathType Leaf) {
    Get-Content -LiteralPath $LogFile | Select-Object -Last 80 | ForEach-Object { Write-Host $_ }
}

if ($piBuildExit -ne 0) {
    Write-Error "PyInstaller failed (exit $piBuildExit). Check $LogFile for details."
    Pop-Location
    exit 1
}

if (-not (Test-Path -LiteralPath $StudioBuildOutput -PathType Leaf)) {
    Write-Error "Build claimed success but exe not found at $StudioBuildOutput"
    Pop-Location
    exit 1
}

Copy-Item -LiteralPath $StudioBuildOutput -Destination $ExpectedOutput -Force

if ($null -ne $InstallerHashBefore) {
    if (-not (Test-Path -LiteralPath $InstallerPath -PathType Leaf)) {
        Write-Error "ChaseOS-Installer.exe disappeared during Studio build at $InstallerPath"
        Pop-Location
        exit 1
    }
    $InstallerHashAfter = (Get-FileHash -Algorithm SHA256 -LiteralPath $InstallerPath).Hash
    if ($InstallerHashAfter -ne $InstallerHashBefore) {
        Write-Error "ChaseOS-Installer.exe hash changed during Studio build at $InstallerPath"
        Pop-Location
        exit 1
    }
}
elseif (Test-Path -LiteralPath $InstallerPath -PathType Leaf) {
    Write-Error "ChaseOS-Installer.exe was unexpectedly created during Studio build at $InstallerPath"
    Pop-Location
    exit 1
}

Pop-Location

# ── Report ────────────────────────────────────────────────────────────────────
$ExePath = $ExpectedOutput
if (Test-Path $ExePath) {
    $SizeMB = [math]::Round((Get-Item $ExePath).Length / 1MB, 1)
    Write-Host ""
    Write-Host "==> Build complete!" -ForegroundColor Green
    Write-Host "    Output : $ExePath"
    Write-Host "    Size   : ${SizeMB} MB"
}
else {
    Write-Error "Build claimed success but exe not found at $ExePath"
    exit 1
}

# ── Create / update desktop shortcut (source launcher — always reflects live code) ──
if ($SignThumbprint -ne "") {
    Write-Host "==> Signing executable..."
    $CleanThumbprint = ($SignThumbprint -replace '\s', '').ToUpperInvariant()
    $CertPath = "Cert:\$SignStoreLocation\My\$CleanThumbprint"
    $Cert = Get-Item -LiteralPath $CertPath -ErrorAction SilentlyContinue
    if ($null -eq $Cert) {
        Write-Error "Code-signing certificate not found at $CertPath"
        exit 1
    }
    if (-not $Cert.HasPrivateKey) {
        Write-Error "Certificate $CleanThumbprint has no private key available for signing."
        exit 1
    }

    $SignArgs = @{
        FilePath = $ExePath
        Certificate = $Cert
    }
    if ($TimestampServer -ne "") {
        $SignArgs["TimestampServer"] = $TimestampServer
    }
    $Signature = Set-AuthenticodeSignature @SignArgs
    if ($Signature.Status -ne "Valid") {
        Write-Error "Signing failed or produced invalid signature: $($Signature.Status) - $($Signature.StatusMessage)"
        exit 1
    }
    Write-Host "    Signature : $($Signature.Status)" -ForegroundColor Green
    Write-Host "    Thumbprint: $CleanThumbprint"
}
else {
    $Signature = Get-AuthenticodeSignature -LiteralPath $ExePath
    if ($Signature.Status -eq "NotSigned") {
        Write-Host "==> Signing skipped: executable is unsigned. Use -SignThumbprint with an existing trusted code-signing certificate for release/native host-policy proof." -ForegroundColor Yellow
    }
    else {
        Write-Host "==> Signature status: $($Signature.Status)"
    }
}

if ($NoShortcut) {
    Write-Host "==> Desktop shortcut update skipped (-NoShortcut)."
}
else {
Write-Host "==> Creating desktop shortcut..."
$Desktop    = [System.Environment]::GetFolderPath("Desktop")
$LnkPath    = "$Desktop\ChaseOS Studio.lnk"
$BatLauncher = "$VaultRoot\runtime\studio\shell\launch_studio.bat"
$WshShell   = New-Object -ComObject WScript.Shell
$Shortcut   = $WshShell.CreateShortcut($LnkPath)
$Shortcut.TargetPath       = "C:\Windows\System32\cmd.exe"
$Shortcut.Arguments        = "/c `"$BatLauncher`""
$Shortcut.WorkingDirectory = $VaultRoot
$Shortcut.Description      = "ChaseOS Studio"
$Shortcut.WindowStyle      = 7   # minimised cmd window — Studio window appears normally
$Shortcut.IconLocation     = "$ExePath,0"   # use fresh exe for icon
$Shortcut.Save()

# Notify Windows shell to refresh icon cache
$code = @'
[System.Runtime.InteropServices.DllImport("shell32.dll")]
public static extern void SHChangeNotify(int wEventId, int uFlags, IntPtr dwItem1, IntPtr dwItem2);
'@
Add-Type -MemberDefinition $code -Name WinAPI -Namespace Shell -ErrorAction SilentlyContinue
try { [Shell.WinAPI]::SHChangeNotify(0x8000000, 0, [IntPtr]::Zero, [IntPtr]::Zero) } catch {}

Write-Host "    Shortcut : $LnkPath" -ForegroundColor Green
Write-Host "    Target   : launch_studio.bat (always runs live source code)"
Write-Host ""
Write-Host "    Double-click 'ChaseOS Studio' on your desktop to launch."
}
