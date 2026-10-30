#!/bin/bash
# Einrichtung des Werkzeugkastens (Pipeline 2): installiert nur, was fehlt; mehrfach ausführbar, ohne Rückfragen.
#   bash werkzeug/einrichten.sh            Abhängigkeiten prüfen und nachinstallieren
#   bash werkzeug/einrichten.sh --probe    danach alle Stilreferenzen neu bauen und prüfen (werkzeug/probelauf.py)
set -euo pipefail
HIER="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Systempakete: LuaLaTeX mit TikZ, pgfplots, circuitikz, unicode-math, Deutsch; Schrift Liberation Sans;
# poppler (pdftoppm) für PNG-Vorschauen; LibreOffice für DOCX/PPTX-Vorschauen
APT_PAKETE=(texlive-luatex texlive-latex-base texlive-latex-recommended texlive-latex-extra texlive-pictures
            texlive-science texlive-lang-german texlive-fonts-recommended fonts-liberation poppler-utils
            libreoffice-writer libreoffice-impress libreoffice-calc libreoffice-math tesseract-ocr tesseract-ocr-deu)
fehlt=()
for p in "${APT_PAKETE[@]}"; do
  dpkg -s "$p" >/dev/null 2>&1 || fehlt+=("$p")
done
if [ ${#fehlt[@]} -gt 0 ]; then
  echo "Installiere Systempakete: ${fehlt[*]}"
  SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
  $SUDO apt-get update -qq
  DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y -qq --no-install-recommends "${fehlt[@]}"
else
  echo "Systempakete vollständig."
fi

# Python-Pakete (lcapy ohne Abhängigkeiten, die nötigen stehen einzeln in der Liste)
PIP="python3 -m pip install -q --disable-pip-version-check"
python3 -m pip --version >/dev/null 2>&1 || { echo "pip fehlt"; exit 1; }
$PIP -r "$HIER/vorlagen/anforderungen.txt" 2>/dev/null || $PIP --break-system-packages -r "$HIER/vorlagen/anforderungen.txt"
python3 -c "import lcapy" 2>/dev/null || $PIP --no-deps lcapy 2>/dev/null || $PIP --break-system-packages --no-deps lcapy

# Kontrolle: Werkzeuge, LaTeX-Pakete, Schrift, Python-Module
for b in lualatex pdftoppm pdftocairo soffice node; do command -v "$b" >/dev/null || { echo "FEHLT: $b"; exit 1; }; done
for s in pgfplots.sty circuitikz.sty unicode-math.sty fontspec.sty ngerman.sty bm.sty; do
  kpsewhich "$s" >/dev/null || { echo "FEHLT: LaTeX-Paket $s"; exit 1; }
done
fc-list : family | grep "Liberation Sans" >/dev/null || { echo "FEHLT: Schrift Liberation Sans"; exit 1; }
tesseract --list-langs 2>/dev/null | grep -x deu >/dev/null || { echo "FEHLT: Texterkennung Deutsch (tesseract-ocr-deu)"; exit 1; }
python3 - <<'PY'
import importlib.util, sys
fehlt = [m for m in ("docx", "docxtpl", "docxcompose", "pptx", "openpyxl", "PIL", "pint", "lcapy", "sympy", "numpy",
                     "scipy", "networkx", "pymupdf", "lxml", "playwright", "pillow_heif", "edge_tts") if importlib.util.find_spec(m) is None]
if fehlt:
    sys.exit("FEHLT: Python-Module " + ", ".join(fehlt))
print("Werkzeugkasten eingerichtet.")
PY

if [ "${1:-}" = "--probe" ]; then
  python3 "$HIER/probelauf.py"
fi
