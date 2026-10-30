"""Findet den Arbeitsbereich der Lehrkraft. Reihenfolge:
1. Umgebungsvariable UPR_ARBEITSBEREICH
2. Datei `.arbeitsbereich` im Werkzeug (eine Zeile mit dem Pfad; nicht im Git)
3. genau ein Nachbarordner `unterrichtspipeline-referendariat-*` mit `Profil/lehrkraft-profil.json`
Sonst Abbruch mit klarer Meldung, nie raten."""
import os, pathlib

WERKZEUG = pathlib.Path(__file__).resolve().parents[1]


def finden():
    if os.environ.get("UPR_ARBEITSBEREICH"):
        p = pathlib.Path(os.environ["UPR_ARBEITSBEREICH"])
        if not p.is_dir():
            raise SystemExit(f"UPR_ARBEITSBEREICH zeigt auf {p}, den Ordner gibt es nicht.")
        return p
    datei = WERKZEUG / ".arbeitsbereich"
    if datei.exists():
        p = pathlib.Path(datei.read_text(encoding="utf-8").strip())
        if not p.is_dir():
            raise SystemExit(f".arbeitsbereich zeigt auf {p}, den Ordner gibt es nicht.")
        return p
    kandidaten = [d for d in WERKZEUG.parent.glob(WERKZEUG.name + "-*") if (d / "Profil" / "lehrkraft-profil.json").exists()]
    if len(kandidaten) == 1:
        return kandidaten[0]
    if not kandidaten:
        raise SystemExit("Kein Arbeitsbereich gefunden. Pfad in UPR_ARBEITSBEREICH oder .arbeitsbereich eintragen.")
    raise SystemExit("Mehrere Arbeitsbereiche gefunden: " + ", ".join(map(str, kandidaten)) + ". Bitte einen festlegen.")


if __name__ == "__main__":
    print(finden())
