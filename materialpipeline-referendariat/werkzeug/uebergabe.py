"""Beschreibungsdatei für die Übergabe an Pipeline 3 (docs/schnittstellen/uebergabe_pipeline3.md).

schreiben(stundenordner, stunde, anlagen, hinweise=()) prüft die Pflichtfelder und schreibt
<stundenordner>/Anlagen/uebergabe.json.
"""
import json
from pathlib import Path

PFLICHT = ("nr", "datei", "art", "titel", "phase", "sichtbar_fuer")
PHASEN = {"Einstieg", "Planung", "Erarbeitung", "Sicherung", "Abschluss"}
SICHTBAR = {"lernende", "lehrkraft"}
MOODLE = {"datei", "ordner", "seite", "aufgabe", "test", "h5p", "keine"}


def pruefen(anlagen, ordner):
    fehler = []
    nummern = {a.get("nr") for a in anlagen}
    for a in anlagen:
        for f in PFLICHT:
            if f not in a and not (f in ("titel", "phase") and a.get("sichtbar_fuer") == "lehrkraft"):
                fehler.append(f"Anlage {a.get('nr')}: Feld {f} fehlt")
        if a.get("phase") and a["phase"] not in PHASEN:
            fehler.append(f"Anlage {a['nr']}: unbekannte Phase {a['phase']}")
        if a.get("sichtbar_fuer") not in SICHTBAR:
            fehler.append(f"Anlage {a.get('nr')}: sichtbar_fuer muss lernende oder lehrkraft sein")
        if a.get("moodle", "datei") not in MOODLE:
            fehler.append(f"Anlage {a['nr']}: unbekannter Moodle-Vorschlag {a['moodle']}")
        if a.get("gehoert_zu") and a["gehoert_zu"] not in nummern:
            fehler.append(f"Anlage {a['nr']}: gehoert_zu verweist auf fehlende Anlage {a['gehoert_zu']}")
        if a.get("art") == "erwartungshorizont" and a.get("sichtbar_fuer") != "lehrkraft":
            fehler.append(f"Anlage {a['nr']}: Erwartungshorizont muss lehrkraft sein")
        if ordner and not (Path(ordner) / a.get("datei", "")).exists():
            fehler.append(f"Anlage {a.get('nr')}: Datei {a.get('datei')} fehlt im Ordner")
    return fehler


def schreiben(stundenordner, stunde, anlagen, hinweise=(), materialauftrag="../Materialauftrag.docx"):
    ordner = Path(stundenordner) / "Anlagen"
    fehler = pruefen(anlagen, ordner)
    if fehler:
        raise ValueError("Übergabe unvollständig:\n" + "\n".join(fehler))
    daten = {"stunde": stunde, "materialauftrag": materialauftrag,
             "anlagen": sorted(anlagen, key=lambda a: a["nr"]), "hinweise": list(hinweise)}
    ziel = ordner / "uebergabe.json"
    ziel.write_text(json.dumps(daten, ensure_ascii=False, indent=2), encoding="utf-8")
    return ziel
