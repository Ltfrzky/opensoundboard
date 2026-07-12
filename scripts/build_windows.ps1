[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$PythonExecutable
)

$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = (Resolve-Path $PythonExecutable).Path
$distRoot = Join-Path $projectRoot "dist"
$artifactDirectory = Join-Path $distRoot "windows\OpenSoundboard"
$version = & $python -c "import tomllib; from pathlib import Path; print(tomllib.loads(Path('pyproject.toml').read_text(encoding='utf-8'))['project']['version'])"

Push-Location $projectRoot
try {
    & $python -m PyInstaller `
        --noconfirm `
        --clean `
        --windowed `
        --onedir `
        --name OpenSoundboard `
        --collect-data app.presentation `
        --collect-all pynput `
        --distpath dist/windows `
        --workpath build/pyinstaller `
        --specpath build/pyinstaller-spec `
        app/main.py
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed with exit code $LASTEXITCODE."
    }

    if (-not (Test-Path -LiteralPath $artifactDirectory)) {
        throw "PyInstaller did not produce $artifactDirectory."
    }

    $archive = Join-Path $distRoot "OpenSoundboard-$version-windows-x64.zip"
    Compress-Archive -LiteralPath $artifactDirectory -DestinationPath $archive -Force
    Write-Output "Built $archive"
}
finally {
    Pop-Location
}
