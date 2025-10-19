<#
Simple PowerShell helper to create a virtual environment and install requirements.

Usage (from repo root):
  .\scripts\setup_env.ps1

#>
param(
    [string]$VenvPath = ".\.venv",
    [string]$PythonExe = "python"
)

Write-Host "Creating venv at $VenvPath using $PythonExe"
$PythonExe -m venv $VenvPath

Write-Host "Activating venv"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
. "$VenvPath\Scripts\Activate.ps1"

Write-Host "Upgrading pip"
pip install --upgrade pip

if (Test-Path requirements.txt) {
    Write-Host "Installing requirements.txt"
    pip install -r requirements.txt
} else {
    Write-Host "No requirements.txt found"
}

Write-Host "Done. Activate the venv with: . $VenvPath\\Scripts\\Activate.ps1"
