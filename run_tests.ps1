# Run tests script
# Usage: .\run_tests.ps1      

Push-Location $PSScriptRoot
$env:PYTHONPATH = $PWD

Write-Host "Running tests in virtual environment..." -ForegroundColor Cyan
& ".\.venv\Scripts\python.exe" -m pytest $args

Pop-Location
