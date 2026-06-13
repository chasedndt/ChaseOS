param(
    [string]$VaultRoot = ".",
    [string]$SignThumbprint = "",
    [ValidateSet("CurrentUser", "LocalMachine")]
    [string]$SignStoreLocation = "CurrentUser",
    [string]$TimestampServer = ""
)

$ErrorActionPreference = "Stop"

# Source-only scaffold for the future ChaseOS-Installer.exe build lane.
# Reuse the existing installer lane if possible before introducing a separate helper.
# No PyInstaller command is run by Settings; this script must be invoked
# explicitly in a future signed-build verification pass.
$ResolvedVaultRoot = (Resolve-Path -LiteralPath $VaultRoot).Path
$SpecFile = Join-Path $ResolvedVaultRoot "runtime\studio\shell\ChaseOS-Installer.spec"
$DistPath = Join-Path $ResolvedVaultRoot "dist\studio"
$WorkPath = Join-Path $ResolvedVaultRoot "build\studio-installer"
$InstallerDistPath = Join-Path $ResolvedVaultRoot "build\studio-installer-dist"
$InstallerBuildOutput = Join-Path $InstallerDistPath "ChaseOS-Installer.exe"
$ExpectedOutput = Join-Path $DistPath "ChaseOS-Installer.exe"
$StudioPath = Join-Path $DistPath "ChaseOS-Studio.exe"

if (-not (Test-Path -LiteralPath $SpecFile -PathType Leaf)) {
    throw "Missing ChaseOS-Installer.spec at $SpecFile"
}

if (-not (Test-Path -LiteralPath $DistPath -PathType Container)) {
    New-Item -ItemType Directory -Path $DistPath | Out-Null
}

$StudioHashBefore = $null
if (Test-Path -LiteralPath $StudioPath -PathType Leaf) {
    $StudioHashBefore = (Get-FileHash -Algorithm SHA256 -LiteralPath $StudioPath).Hash
}

Push-Location $ResolvedVaultRoot
try {
    $PyInstallerExe = @((Get-Command pyinstaller -CommandType Application -ErrorAction Stop))[0].Source
    & $PyInstallerExe $SpecFile --distpath $InstallerDistPath --workpath $WorkPath --noconfirm
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed while building ChaseOS-Installer.exe."
    }
    if (-not (Test-Path -LiteralPath $InstallerBuildOutput -PathType Leaf)) {
        throw "Expected ChaseOS-Installer.exe was not created at $InstallerBuildOutput"
    }
    Copy-Item -LiteralPath $InstallerBuildOutput -Destination $ExpectedOutput -Force
    if (-not (Test-Path -LiteralPath $ExpectedOutput -PathType Leaf)) {
        throw "Expected ChaseOS-Installer.exe was not created at $ExpectedOutput"
    }
    if ($null -ne $StudioHashBefore) {
        if (-not (Test-Path -LiteralPath $StudioPath -PathType Leaf)) {
            throw "ChaseOS-Studio.exe disappeared during installer build at $StudioPath"
        }
        $StudioHashAfter = (Get-FileHash -Algorithm SHA256 -LiteralPath $StudioPath).Hash
        if ($StudioHashAfter -ne $StudioHashBefore) {
            throw "ChaseOS-Studio.exe hash changed during installer build at $StudioPath"
        }
    }
    elseif (Test-Path -LiteralPath $StudioPath -PathType Leaf) {
        throw "ChaseOS-Studio.exe was unexpectedly created during installer build at $StudioPath"
    }
    if ($SignThumbprint -ne "") {
        $CleanThumbprint = ($SignThumbprint -replace '\s', '').ToUpperInvariant()
        $CertPath = "Cert:\$SignStoreLocation\My\$CleanThumbprint"
        $Cert = Get-Item -LiteralPath $CertPath -ErrorAction SilentlyContinue
        if ($null -eq $Cert) {
            throw "Code-signing certificate not found at $CertPath"
        }
        if (-not $Cert.HasPrivateKey) {
            throw "Certificate $CleanThumbprint has no private key available for signing."
        }
        $SignArgs = @{
            FilePath = $ExpectedOutput
            Certificate = $Cert
        }
        if ($TimestampServer -ne "") {
            $SignArgs["TimestampServer"] = $TimestampServer
        }
        $Signature = Set-AuthenticodeSignature @SignArgs
        if ($Signature.Status -ne "Valid") {
            throw "Signing failed or produced invalid signature: $($Signature.Status) - $($Signature.StatusMessage)"
        }
        Write-Output "Built and signed $ExpectedOutput"
        Write-Output "Signature: $($Signature.Status)"
        Write-Output "Thumbprint: $CleanThumbprint"
    }
    else {
        $Signature = Get-AuthenticodeSignature -LiteralPath $ExpectedOutput
        Write-Output "Built $ExpectedOutput"
        Write-Output "Signature: $($Signature.Status)"
        if ($Signature.Status -eq "NotSigned") {
            Write-Output "Signing skipped: use -SignThumbprint with an existing trusted code-signing certificate for release distribution."
        }
    }
}
finally {
    Pop-Location
}
