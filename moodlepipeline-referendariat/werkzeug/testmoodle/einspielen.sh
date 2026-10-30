#!/bin/bash
# Live-Restore einer Sicherung in ein lokales Moodle 5.1.6 mit Kachelformat (Kurzform für Linux und Cloud).
#   werkzeug/testmoodle/einspielen.sh <kurs.mbz> [test-ordner]
# Eigentliches Werkzeug, auch für Windows und macOS: werkzeug/testmoodle/testmoodle.py (einrichten, einspielen,
# pruefen, ansehen, stoppen). Ohne Kachelformat prüfen: KACHELN=0 mit neuem Test-Ordner.
set -euo pipefail
HIER=$(dirname "$(realpath "$0")")
python3 "$HIER/testmoodle.py" einspielen "$1" ${2:+--ordner "$2"}
