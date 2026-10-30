"""Einrichtung für jede KI-App und jedes System (Windows, macOS, Linux): persönlichen Arbeitsbereich finden und den drei
Werkzeugen mitteilen; mit --programme unter Linux zusätzlich die Programme für Pipeline 2 (apt).

    python3 einrichten.py              # unter Windows: python einrichten.py
    python3 einrichten.py --programme  # Linux oder Cloud: LaTeX, LibreOffice, Python-Pakete
"""
import platform
import subprocess
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent
WERKZEUGE = ["unterrichtspipeline-referendariat", "materialpipeline-referendariat", "moodlepipeline-referendariat"]


def arbeitsbereich():
    for basis in (WURZEL, WURZEL.parent):
        for kandidat in sorted(basis.glob("unterrichtspipeline-referendariat-*")):
            if (kandidat / "Profil" / "lehrkraft-profil.json").exists() or (kandidat / "CLAUDE.md").exists():
                return kandidat.resolve()
    return None


def main():
    ab = arbeitsbereich()
    if ab:
        for w in WERKZEUGE:
            datei = WURZEL / w / ".arbeitsbereich"
            if not datei.exists():
                datei.write_text(str(ab) + "\n", encoding="utf-8")
        print(f"Arbeitsbereich: {ab}")
        if not (ab / "Profil" / "lehrkraft-profil.json").exists():
            print("Noch kein Profil: Einrichtung mit dem Startprompt aus STARTPROMPT.md.")
    else:
        print("Noch kein Arbeitsbereich gefunden. Für die Einrichtung den Startprompt aus STARTPROMPT.md verwenden.")
    if "--programme" in sys.argv:
        if platform.system() == "Linux":
            subprocess.run(["bash", "werkzeug/einrichten.sh"], cwd=WURZEL / "materialpipeline-referendariat")
        else:
            print("Programme unter Windows und macOS richtet der Startprompt mit Ihnen gemeinsam ein.")


if __name__ == "__main__":
    main()
