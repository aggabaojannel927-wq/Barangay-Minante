$ErrorActionPreference = "Stop"
$projectPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $projectPython)) {
    throw "Python environment is missing. Run .\setup.ps1 first."
}
& $projectPython -c "import flask, flask_sqlalchemy, sqlalchemy, werkzeug, dotenv, docx"
if ($LASTEXITCODE -ne 0) { throw "Project dependencies are missing. Run .\setup.ps1 first." }
Push-Location (Join-Path $PSScriptRoot "barangay_system")
try {
    & $projectPython app.py
    if ($LASTEXITCODE -ne 0) { throw "The application exited with an error." }
} finally {
    Pop-Location
}
