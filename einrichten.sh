#!/bin/bash
# Einrichtung für jede KI-App (Claude Code, Codex, Antigravity, Hermes …): persönlichen Arbeitsbereich finden und den
# drei Werkzeugen mitteilen; mit --programme zusätzlich die Programme für Pipeline 2 einrichten (Linux, apt).
# Claude Code ruft das Skript beim Sitzungsstart selbst auf; andere Apps führen es zu Beginn einer Sitzung aus.
#
#     bash einrichten.sh              # Arbeitsbereich finden
#     bash einrichten.sh --programme  # dazu LaTeX, LibreOffice, Python-Pakete (Cloud oder Linux)
cd "$(dirname "$0")" || exit 0
WERKZEUGE="unterrichtspipeline-referendariat materialpipeline-referendariat moodlepipeline-referendariat"

ab=""
for kandidat in ./unterrichtspipeline-referendariat-*/ ../unterrichtspipeline-referendariat-*/; do
  if [ -f "$kandidat/Profil/lehrkraft-profil.json" ] || [ -f "$kandidat/CLAUDE.md" ]; then
    ab="$(cd "$kandidat" && pwd)"
    break
  fi
done
if [ -n "$ab" ]; then
  for w in $WERKZEUGE; do
    [ -f "$w/.arbeitsbereich" ] || echo "$ab" > "$w/.arbeitsbereich"
  done
  echo "Arbeitsbereich: $ab"
  [ -f "$ab/Profil/lehrkraft-profil.json" ] || echo "Noch kein Profil: Einrichtung mit dem Startprompt aus STARTPROMPT.md."
else
  echo "Noch kein Arbeitsbereich gefunden. Für die Einrichtung den Startprompt aus STARTPROMPT.md verwenden."
fi

if [ "${1:-}" = "--programme" ]; then
  (cd materialpipeline-referendariat && bash werkzeug/einrichten.sh) || echo "Einrichtung von Pipeline 2 mit Fehlern."
fi
exit 0
