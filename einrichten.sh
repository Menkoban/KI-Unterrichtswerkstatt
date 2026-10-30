#!/bin/bash
# Kurzform von einrichten.py für Linux, macOS und die Cloud (Claude Code ruft sie beim Sitzungsstart auf).
cd "$(dirname "$0")" || exit 0
python3 einrichten.py "$@" || true
