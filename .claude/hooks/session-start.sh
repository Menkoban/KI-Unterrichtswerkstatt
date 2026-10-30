#!/bin/bash
# Sitzungsstart in Claude Code: gemeinsame Einrichtung (einrichten.sh); in Cloud-Sitzungen mit den Programmen.
cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}" || exit 0
if [ "${CLAUDE_CODE_REMOTE:-}" = "true" ]; then
  bash einrichten.sh --programme
else
  bash einrichten.sh
fi
exit 0
