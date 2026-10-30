# -*- coding: utf-8 -*-
"""setup_laptop.py: Einrichtung auf einem neuen Rechner.

Die Skills der Unterrichtspipeline liegen im Werkzeug unter .claude/skills und arbeiten mit den
Skripten des Werkzeugs (Pfade relativ zur Projektwurzel). Sie werden deshalb nicht mehr global
kopiert; Claude Code findet sie, wenn die Sitzung in der Wurzel dieses Repositorys startet.

Das Skript
  1. prüft die Python-Pakete (python-docx, docxcompose),
  2. merkt sich auf Wunsch den Pfad zum persönlichen Arbeitsbereich (Datei .arbeitsbereich),
  3. findet alte, global kopierte Skills der ersten Fassung (~/.claude/skills,
     ~/.gemini/config/skills) und verschiebt sie nach Rückfrage in einen Sicherungsordner
     daneben, damit sie die neuen Skills nicht überdecken. Gelöscht wird nichts.

    python setup_laptop.py [<pfad zum arbeitsbereich>]
"""
import datetime as dt, shutil, sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent
ARCHIV = WURZEL / "archiv" / "skills_fassung1"  # fehlt in der öffentlichen Fassung
ALTE = {p.name for p in ARCHIV.iterdir() if p.is_dir()} if ARCHIV.is_dir() else set()


def pakete():
    fehlt = []
    for mod, name in {"docx": "python-docx", "docxcompose": "docxcompose"}.items():
        try:
            __import__(mod); print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} fehlt"); fehlt.append(name)
    if fehlt:
        print(f"\n  Bitte installieren: pip install {' '.join(fehlt)}")


def arbeitsbereich(pfad):
    p = Path(pfad).expanduser().resolve()
    if not (p / "Profil" / "lehrkraft-profil.json").exists():
        print(f"  ✗ {p} ist kein Arbeitsbereich (Profil/lehrkraft-profil.json fehlt)"); return
    (WURZEL / ".arbeitsbereich").write_text(str(p), encoding="utf-8")
    print(f"  ✓ Arbeitsbereich gemerkt: {p}")


def alte_skills():
    for ziel in (Path.home() / ".claude" / "skills", Path.home() / ".gemini" / "config" / "skills"):
        if not ziel.is_dir():
            continue
        treffer = [p for p in ziel.iterdir() if p.is_dir() and p.name in ALTE]
        if not treffer:
            continue
        print(f"\n  Alte Skills der ersten Fassung in {ziel}: {', '.join(p.name for p in treffer)}")
        if input("  In einen Sicherungsordner daneben verschieben? [j/N] ").strip().lower() != "j":
            continue
        sicherung = ziel.parent / f"skills_alt_{dt.date.today():%Y-%m-%d}"
        sicherung.mkdir(exist_ok=True)
        for p in treffer:
            shutil.move(str(p), str(sicherung / p.name)); print(f"  → {p.name} nach {sicherung}")


if __name__ == "__main__":
    print("Unterrichtspipeline: Einrichtung\n\nPython-Pakete:")
    pakete()
    if len(sys.argv) > 1:
        print("\nArbeitsbereich:"); arbeitsbereich(sys.argv[1])
    alte_skills()
    print("\nFertig. Sitzungen in der Wurzel dieses Repositorys starten:", WURZEL)
