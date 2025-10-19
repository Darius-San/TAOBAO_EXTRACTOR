#!/usr/bin/env bash
set -euo pipefail

VENV_PATH=".venv"
PYTHON=${PYTHON:-python3}

echo "Creating venv at $VENV_PATH using $PYTHON"
$PYTHON -m venv "$VENV_PATH"
echo "Activating venv"
source "$VENV_PATH/bin/activate"
echo "Upgrading pip"
pip install --upgrade pip
if [ -f requirements.txt ]; then
  echo "Installing requirements.txt"
  pip install -r requirements.txt
else
  echo "No requirements.txt found"
fi
echo "Done. Activate with: source $VENV_PATH/bin/activate"
