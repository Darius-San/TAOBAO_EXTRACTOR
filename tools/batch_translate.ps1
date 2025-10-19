<#
.SYNOPSIS
  Batch-translate all CSV files in input directory using tools/translate_all_progress.py

.DESCRIPTION
  Runs the existing Python translator for every CSV found in the input directory and writes
  outputs into the output directory. Writes a log file and prints a summary.

.PARAMETER InputDir
  Directory that contains input CSV files (default: .\input_csv)

.PARAMETER OutputDir
  Directory where translated CSV files will be written (default: .\final_output)

.PARAMETER WriteInterval
  Passed to the Python script as --write-interval (default: 10)

.PARAMETER PythonExe
  Python executable to use (default: python). Use full path to a specific interpreter if needed.

.PARAMETER UseVenv
  If set, attempt to activate .venv\Scripts\Activate.ps1 before running translations.

EXAMPLE
  # From repository root
  .\tools\batch_translate.ps1 -InputDir .\input_csv -OutputDir .\final_output -WriteInterval 10

#>
param(
    [string]$InputDir = ".\input_csv",
    [string]$OutputDir = ".\final_output",
    [int]$WriteInterval = 10,
    [string]$PythonExe = "python",
    [switch]$UseVenv
)

Set-StrictMode -Version Latest

try {
    $inPath = Resolve-Path -Path $InputDir -ErrorAction Stop
} catch {
    Write-Error "Input directory not found: $InputDir"
    exit 1
}

if (-not (Test-Path -Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

$logFile = Join-Path $OutputDir "batch_translate.log"
"Batch translate started: $(Get-Date -Format u)" | Out-File -FilePath $logFile -Encoding utf8

if ($UseVenv) {
    $activate = Join-Path ".\.venv\Scripts" "Activate.ps1"
    if (Test-Path $activate) {
        Write-Host "Activating virtualenv: $activate"
        . $activate
    } else {
        Write-Warning "Requested .venv activation but $activate not found. Continuing with $PythonExe"
    }
}

$files = @(Get-ChildItem -Path $inPath -Filter *.csv -File -ErrorAction SilentlyContinue)
if ($files.Count -eq 0) {
  Write-Host "No CSV files found in $inPath"
  exit 0
}

$summary = @()
foreach ($f in $files) {
  $inFile = $f.FullName
  $outName = $f.BaseName + "_no_chinese.csv"
  $outFile = Join-Path $OutputDir $outName

  Write-Host "Translating: $($f.Name) -> $outName"
  Add-Content $logFile "$(Get-Date -Format u) START $inFile -> $outFile"

  try {
    # Use the call operator so PowerShell handles quoting correctly for paths with spaces
    & $PythonExe "tools\translate_all_progress.py" -i $inFile -o $outFile --write-interval $WriteInterval
    $exit = $LASTEXITCODE
  } catch {
    $exit = 1
    Add-Content $logFile "$(Get-Date -Format u) ERROR $inFile : $_"
  }

  if ($exit -eq 0) {
    Write-Host "  OK"
    Add-Content $logFile "$(Get-Date -Format u) DONE $inFile -> $outFile"
    $summary += [pscustomobject]@{file=$f.Name; status='OK'; out=$outFile}
  } else {
    Write-Host "  FAILED (exit $exit)"
    Add-Content $logFile "$(Get-Date -Format u) FAILED $inFile Exit:$exit"
    $summary += [pscustomobject]@{file=$f.Name; status='FAILED'; out=$outFile; exit=$exit}
  }
}

Write-Host "`nSummary:`n"
foreach ($s in $summary) {
  Write-Host ("{0,-40} {1,-8} {2}" -f $s.file, $s.status, $s.out)
}

Write-Host "`nLog: $logFile"
Write-Host "Done."
