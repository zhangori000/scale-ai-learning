param(
    [string]$WheelDir = ".\\wheelhouse"
)

$ErrorActionPreference = "Stop"

if (!(Test-Path $WheelDir)) {
    New-Item -ItemType Directory -Path $WheelDir | Out-Null
}

Write-Host "Downloading wheels to $WheelDir ..."
python -m pip download -r requirements.txt -d $WheelDir
Write-Host "Done. You can install offline using:"
Write-Host "python -m pip install --no-index --find-links `"$WheelDir`" -r requirements.txt"
