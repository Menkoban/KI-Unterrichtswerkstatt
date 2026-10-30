#!/bin/bash
# Sitzungsstart: persönlichen Arbeitsbereich finden und den drei Werkzeugen mitteilen; in Cloud-Sitzungen zusätzlich
# die Programme für Pipeline 2 einrichten (LaTeX, LibreOffice, Python-Pakete). Fehler blockieren die Sitzung nicht.
cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}" || exit 0
WERKZEUGE="unterrichtspipeline-referendariat materialpipeline-referendariat moodlepipeline-referendariat"

ab=""
for kandidat in ./unterrichtspipeline-referendariat-*/ ../unterrichtspipeline-referendariat-*/; do
  if [ -f "$kandidat/Profil/lehrkraft-profil.json" ]; then
    ab="$(cd "$kandidat" && pwd)"
    break
  fi
done
if [ -n "$ab" ]; then
  for w in $WERKZEUGE; do
    [ -f "$w/.arbeitsbereich" ] || echo "$ab" > "$w/.arbeitsbereich"
  done
  echo "Arbeitsbereich: $ab"
else
  echo "Noch kein Arbeitsbereich mit Profil gefunden. Für die Einrichtung den Startprompt aus STARTPROMPT.md verwenden."
fi

if [ "${CLAUDE_CODE_REMOTE:-}" = "true" ]; then
  (cd materialpipeline-referendariat && bash werkzeug/einrichten.sh) || echo "Einrichtung von Pipeline 2 mit Fehlern."
fi
exit 0
