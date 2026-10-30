#!/bin/bash
# Sitzungsstart (nur Cloud-Sitzungen): Werkzeugkasten einrichten und beim Neustart einmal zur Probe bauen.
set -euo pipefail
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi
cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}"

# Quelle des Starts (startup, resume, clear, compact); der Probelauf nur beim echten Start
quelle="$(cat 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin).get("source",""))' 2>/dev/null || true)"

bash werkzeug/einrichten.sh
if [ "$quelle" = "startup" ] || [ -z "$quelle" ]; then
  # Fehler im Probelauf blockieren die Sitzung nicht, stehen aber im Bericht zu Beginn
  python3 werkzeug/probelauf.py || echo "Probelauf mit Fehlern: siehe Bericht oben."
fi
