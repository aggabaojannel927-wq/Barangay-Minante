$ErrorActionPreference = "Stop"
$projectPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $projectPython)) {
    python -m venv (Join-Path $PSScriptRoot ".venv")
    if ($LASTEXITCODE -ne 0) { throw "Could not create the Python environment." }
}

& $projectPython -m ensurepip --upgrade
if ($LASTEXITCODE -ne 0) { throw "Could not initialize pip in the Python environment." }
& $projectPython -m pip install -r (Join-Path $PSScriptRoot "barangay_system\requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "Could not install the project dependencies." }
& $projectPython -m pip check
if ($LASTEXITCODE -ne 0) { throw "The installed dependencies are incompatible." }
Write-Host "Setup complete. Start the application with .\run.ps1"
