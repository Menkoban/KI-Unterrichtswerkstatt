"""Arbeitsbereich und Profil der Lehrkraft für Pipeline 3 (Aufteilung wie Pipeline 1 und 2, Lehrkraft 2026-10-21).

Das Werkzeug (dieses Repo) enthält nur Allgemeines. Kursplan, Bauskripte, fertige Kurse und das Profil
liegen im **gemeinsamen** persönlichen Arbeitsbereich aller Pipelines.

Arbeitsbereich finden, in dieser Reihenfolge:
1. Umgebungsvariable UPR_ARBEITSBEREICH (dieselbe wie in Pipeline 1)
2. Datei `.arbeitsbereich` in diesem Werkzeug (eine Zeile mit dem Pfad; nicht im Git)
3. genau ein Nachbarordner `unterrichtspipeline-referendariat-*` mit `Profil/lehrkraft-profil.json`
Sonst Abbruch mit klarer Meldung, nie raten.

Profil: eine Datei `Profil/lehrkraft-profil.json`; Vorlage und Prüfung kommen aus dem Werkzeug von Pipeline 1
(`profil/profil.py`, Gruppe „Moodle“), gefunden über UPR_WERKZEUG oder den Nachbarordner
`unterrichtspipeline-referendariat`.

    python3 werkzeug/arbeitsbereich.py            # Pfade und Material-Einstellungen anzeigen
"""
import importlib.util
import os
from pathlib import Path

WERKZEUG = Path(__file__).resolve().parents[1]


def finden():
    if os.environ.get("UPR_ARBEITSBEREICH"):
        p = Path(os.environ["UPR_ARBEITSBEREICH"])
        if not p.is_dir():
            raise SystemExit(f"UPR_ARBEITSBEREICH zeigt auf {p}, den Ordner gibt es nicht.")
        return p
    datei = WERKZEUG / ".arbeitsbereich"
    if datei.exists():
        p = Path(datei.read_text(encoding="utf-8").strip())
        if not p.is_dir():
            raise SystemExit(f".arbeitsbereich zeigt auf {p}, den Ordner gibt es nicht.")
        return p
    kandidaten = [d for d in WERKZEUG.parent.glob("unterrichtspipeline-referendariat-*")
                  if (d / "Profil" / "lehrkraft-profil.json").exists()]
    if len(kandidaten) == 1:
        return kandidaten[0]
    if not kandidaten:
        raise SystemExit("Kein Arbeitsbereich gefunden. Pfad in UPR_ARBEITSBEREICH oder .arbeitsbereich eintragen.")
    raise SystemExit("Mehrere Arbeitsbereiche gefunden: " + ", ".join(map(str, kandidaten)) + ". Bitte einen festlegen.")


def werkzeug_pipeline1():
    p = Path(os.environ.get("UPR_WERKZEUG") or WERKZEUG.parent / "unterrichtspipeline-referendariat")
    if not (p / "profil" / "profil.py").exists():
        raise SystemExit(f"Werkzeug von Pipeline 1 nicht gefunden ({p}); Pfad in UPR_WERKZEUG eintragen.")
    return p


def profil(arbeitsbereich=None):
    """Zusammengeführtes Profil {id: wert} (Standard der Vorlage, darüber die eigenen Werte)."""
    pfad = werkzeug_pipeline1() / "profil" / "profil.py"
    spec = importlib.util.spec_from_file_location("upr_profil", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul.lade(arbeitsbereich or finden())


def quellen(arbeitsbereich=None):
    """Eigene Quellen (Fachbücher, Normen, Hersteller, Materialpool) mit Quellenkarte."""
    return Path(arbeitsbereich or finden()) / "Quellen"


def lernfeld(fach, beruf, lf, arbeitsbereich=None):
    """Lernfeld-Ordner im Arbeitsbereich, z. B. lernfeld("Elektrotechnik", "Elektroniker_EG", "LF01")."""
    basis = Path(arbeitsbereich or finden()) / fach / beruf
    treffer = sorted(basis.glob(f"{lf}_*")) or sorted(basis.glob(lf))
    if not treffer:
        raise SystemExit(f"Lernfeld {lf} nicht gefunden unter {basis}.")
    return treffer[0]


def bibliothek(fach, beruf, lf, arbeitsbereich=None):
    """Bibliothek je Lernfeld: Material, das über eine Lernsituation hinaus trägt."""
    return lernfeld(fach, beruf, lf, arbeitsbereich) / "Bibliothek"


def moodle(fach, beruf, lf, ls, arbeitsbereich=None):
    """Kursplan, Bauskripte und fertige .mbz einer Lernsituation: <LF>/<LS>/Moodle/ (neben dem Material)."""
    return material(fach, beruf, lf, ls, arbeitsbereich).parent / "Moodle"


def material(fach, beruf, lf, ls, arbeitsbereich=None):
    """Bauskripte, Fotos und Ausgaben einer Lernsituation: <LF>/<LS>/Material/<DS>/."""
    basis = lernfeld(fach, beruf, lf, arbeitsbereich)
    treffer = sorted(basis.glob(f"{ls}_*")) or sorted(basis.glob(ls))
    if not treffer:
        raise SystemExit(f"Lernsituation {ls} nicht gefunden unter {basis}.")
    return treffer[0] / "Material"


if __name__ == "__main__":
    ab = finden()
    print("Arbeitsbereich:", ab)
    print("Quellen:       ", quellen(ab))
    for k, v in sorted(profil(ab).items()):
        if k.startswith(("moodle.", "lehrkraft.")) or k in ("ansprache", "rolle_lernende"):
            print(f"  {k} = {v}")
