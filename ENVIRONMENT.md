Recommended environment
=======================

Python
------
- Empfohlene Version: Python 3.11.x (funktioniert auch mit 3.8+; 3.11 empfohlen)
- Wenn Du pyenv verwendest, lege die Datei `.python-version` (im Repo-Root) auf `3.11.10` oder eine gewünschte 3.11.x-Version.

Virtual environment
-------------------
- Erstelle ein virtuelles Environment im Repo (empfohlen `.venv`) und aktiviere es.
- Nutze die mitgelieferten Skripte:
  - Windows / PowerShell: `scripts/setup_env.ps1`
  - macOS / Linux: `scripts/setup_env.sh`

Dependencies
------------
- Alle Python-Abhängigkeiten sind in `requirements.txt` (z. B. `googletrans`).
- Nach Aktivierung der venv: `pip install -r requirements.txt`.

Locale / Encoding
-----------------
- Windows PowerShell verwendet UTF-8 mit `utf-8-sig` in den Skripten – falls Probleme auftreten, setze die Konsole auf UTF-8:
  - PowerShell (temporär): `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8`

Notes
-----
- `googletrans` ist inoffiziell; bei Bedarf auf eine offizielle API umstellen.
