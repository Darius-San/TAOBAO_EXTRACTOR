# Taobao HTML Data Extractor 🛒

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/yourusername/taobao-extractor/graphs/commit-activity)

A Python tool to extract and translate Taobao purchase data from HTML files into English CSV/Markdown format.

## Features

- 🔄 Extracts product data from Taobao HTML purchase history
- 🌍 Translates Chinese product names to English (47+ translations)
- 🎨 Translates color classifications to English (59+ translations)  
- 🏪 Maps products to appropriate English seller names (25+ sellers)
- 📅 Assigns realistic purchase dates based on order ID patterns
- 📊 Exports to both CSV and Markdown formats
- ✅ Complete Unicode handling for Chinese characters

## Installation

## TAOBAO_EXTRACTOR — Minimaler Workflow (Deutsch)

Dieses Repository ist auf ein kleines, praktisches Werkzeug reduziert:

- `scripts/taobao_export_json.user.js` — Tampermonkey Userscript: exportiert Bestellungen von der Taobao-Bestellseite (verwendet eingebettetes JSON).
- `data/input.html` — Beispiel / gespeicherte Taobao-Bestellseite (enthält das eingebettete JSON).
- `input_csv/` — Ordner, in den Du die vom Userscript erzeugten CSV-Dateien legst.
- `final_output/` — Ordner für die finalen, ins Englische übersetzten CSV-Dateien.
- `tools/` — kleine Python-Skripte zum Übersetzen / Finalisieren (progress-enabled).

Ziel: einfacher Ablauf — Seite exportieren → CSV in `input_csv/` legen → übersetzen → finales CSV in `final_output/`.

## Easy install (one command)

Wenn Du das Repo gerade heruntergeladen hast und schnell loslegen willst, gibt es zwei kleine Helfer:

- Windows / PowerShell (einfach ausführen im Repo-Root):

```powershell
.\scripts\setup_env.ps1
```

- macOS / Linux (bash):

```bash
./scripts/setup_env.sh
```

Beide Skripte erzeugen ein virtuelles Environment `.venv` und installieren die Abhängigkeiten aus `requirements.txt` (sofern vorhanden). Du kannst danach die venv aktivieren und wie gewohnt die Tools verwenden.

## Schnellstart (PowerShell)

Voraussetzungen:
- Windows mit installiertem Python 3.8+ (empfohlen 3.11+)
- (Optional) virtuelles Environment für Python
- Für automatische Übersetzung: `googletrans==4.0.0-rc1` (oder eine andere Übersetzungs-API Deiner Wahl)

Beispielschritte (PowerShell):

1) (Optional) Virtuelle Umgebung anlegen und aktivieren

```powershell
# im Repo-Root
python -m venv .venv
# PowerShell: eventuell ExecutionPolicy erlauben, dann aktivieren
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force; .\.venv\Scripts\Activate.ps1
```

2) Abhängigkeit (googletrans) installieren

```powershell
pip install googletrans==4.0.0-rc1
```

3) CSV exportieren mit Tampermonkey

- Tampermonkey installieren (Browser-Erweiterung).
- Neu-Skript anlegen und den Inhalt von `scripts/taobao_export_json.user.js` einfügen.
- Hinweis zu lokalen HTML-Dateien: Das Userscript ist standardmäßig auf `https://buyertrade.taobao.com/*` gesetzt. Wenn Du `data/input.html` lokal öffnest, musst Du entweder
	- das `@match` in der Script-Header-Zeile temporär anpassen (z. B. `@match file:///*`), oder
	- in Tampermonkey eine `Include`-Regel hinzufügen, die lokale Dateien erlaubt.
- Öffne die Bestellseite (oder `data/input.html`) im Browser, klicke die neu eingeblendete Schaltfläche „导出 (JSON)“ — die CSV-Datei wird heruntergeladen.

4) Exportierte CSV in `input_csv/` ablegen

Kopiere oder verschiebe die Datei, z. B. `input_csv\\taobao_orders.csv`.

5) Automatische Übersetzung (alle chinesischen Zellen)

```powershell
python tools/translate_all_progress.py -i "input_csv\\taobao_orders.csv" -o "final_output\\taobao_orders_no_chinese.csv" --write-interval 10
```

Erläuterung:
- `--write-interval 10` schreibt alle 10 Zeilen eine Zwischenversion, so dass Du Fortschritt siehst und das Skript im Notfall fortsetzen kannst.
- Falls `googletrans` in Deiner (virtuellen) Umgebung Probleme macht, kannst Du das Skript mit einem globalen Python laufen lassen, in dem `googletrans` bereits installiert ist.

6) Finalisieren (Spalten umbenennen / chinesische Spalten ersetzen)

```powershell
python tools/finalize_translated_csv.py -i "final_output\\taobao_orders_no_chinese.csv" -o "final_output\\taobao_orders_final.csv"
```

Dieses Skript kopiert die `_en`-Spalten (sofern vorhanden) über die Originalspalten und schreibt eine finale, auf Englisch benannte CSV-Datei.

## Felder / Format

Die vom Userscript erzeugte CSV hat (aktuell) die Spalten:

- `订单号` (order id)
- `商品名称` (title; ggf. mehrere Artikel durch `||` getrennt)
- `商品链接` (erste Artikel-URL)
- `单价` (unit price; evtl. leer)
- `数量` (quantity)
- `实付款` (paid)
- `状态` (status)
- `快递单号` (tracking number; evtl. leer)

Nach der Übersetzung / Finalisierung werden die Spalten in der finalen CSV auf Englisch benannt (z. B. `order_id`, `title`, `item_url`, `unit_price`, `quantity`, `paid`, `status`, `tracking_number`).

## Hinweise & Troubleshooting

- Lokale HTML-Datei: Browser-Sicherheitsregeln können das Laden lokaler Dateien einschränken. Wenn das Userscript nicht ausgelöst wird, prüfe die `@match`/`@include`-Regeln in Tampermonkey.
- `googletrans` ist ein inoffizieller Client; bei vielen oder sehr langen Texten können Übersetzungsfehler auftreten. In diesem Fall:
	- Das Skript versucht mehrfach, fehlgeschlagene Übersetzungen erneut.
	- Fehlschläge werden protokolliert; die Originaltexte bleiben erhalten und können manuell geprüft werden.
- Wenn Du eine produktive/skalierbare Lösung benötigst, empfehle ich eine offizielle API (Google Cloud Translate, DeepL, etc.) — die Skripte können angepasst werden.

## Was im Repo enthalten ist

- `scripts/taobao_export_json.user.js` — Tampermonkey exporter
- `data/input.html` — Beispiel / gespeicherte Bestellseite
- `input_csv/` — Platz für rohe Exporte
- `final_output/` — Endergebnisse nach Übersetzung
- `tools/translate_all_progress.py` — Übersetzt alle chinesischen Zellen mit Fortschritt/Interims-Speicher
- `tools/finalize_translated_csv.py` — Finalisiert und benennt Spalten um

## Nächste Schritte (optional)

- Soll ich die Änderungen direkt commiten und pushen? Sag kurz Bescheid, dann führe ich `git add`/`git commit` für Dich aus.

Viel Erfolg — wenn Du möchtest, kann ich die README noch weiter vereinfachen oder Beispielbefehle für andere Shells (cmd, bash) ergänzen.
This repository has been reduced to a minimal example project that contains:
