"""Akten im Arbeitsbereich: Steckbrief je Akte und Übersicht für den Einstieg „Was steht an?“.

Jede Akte hat einen Steckbrief in `.daten/akten/<pfad der akte>.json`:
  {"art": "lernfeld|lernsituation|klasse|schuljahr|stunde|modellbetrieb|ref",
   "titel": "...", "pfad": "<ordner oder datei im arbeitsbereich>",
   "stand": "entwurf|freigegeben", "freigegeben_am": "JJJJ-MM-TT"|null,
   "zuletzt_bearbeitet": "JJJJ-MM-TTTHH:MM", "baut_auf": ["<pfad>", ...],
   "fach": "Elektrotechnik|Mathematik", "notiz": "...", "ruhend": "<Grund>" (optional: Akte bleibt stehen, wird aber
   nicht mehr nachgezogen; keine Warnung „veraltet“, nur ein Hinweis)}

    python akten/akten.py <arbeitsbereich>     # Übersicht: was ist da, Stand, zuletzt bearbeitet, veraltet
"""
import json, sys, pathlib

ARTEN = {"modellbetrieb", "lernfeld", "lernsituation", "schuljahr", "klasse", "stunde", "ref"}
STAENDE = {"entwurf", "freigegeben"}


def steckbriefe(ab):
    ab = pathlib.Path(ab)
    for f in sorted((ab / ".daten" / "akten").rglob("*.json")):
        sb = json.loads(f.read_text(encoding="utf-8"))
        sb["_datei"] = f
        yield sb


def pruefen(ab):
    ab = pathlib.Path(ab)
    alle = list(steckbriefe(ab))
    pfade = {s["pfad"]: s for s in alle}
    befunde = []
    for s in alle:
        if s.get("art") not in ARTEN:
            befunde.append(f"Fehler: {s['pfad']}: unbekannte Art {s.get('art')!r}")
        if s.get("stand") not in STAENDE:
            befunde.append(f"Fehler: {s['pfad']}: unbekannter Stand {s.get('stand')!r}")
        if not (ab / s["pfad"]).exists():
            befunde.append(f"Fehler: {s['pfad']}: Steckbrief ohne Akte im Arbeitsbereich")
        for b in s.get("baut_auf", []):
            if b not in pfade:
                befunde.append(f"Warnung: {s['pfad']}: baut auf {b}, dafür gibt es keinen Steckbrief")
            elif pfade[b]["zuletzt_bearbeitet"] > s["zuletzt_bearbeitet"] and not s.get("ruhend"):  # gleiche Zeit gilt als aktuell
                befunde.append(f"Warnung: {s['pfad']}: veraltet, {b} wurde danach geändert")
        if s.get("ruhend"):
            befunde.append(f"Hinweis: {s['pfad']}: ruht ({s['ruhend']}); wird nicht mehr nachgezogen")
    return befunde


EBENEN = [("modellbetrieb", "Modellbetrieb"), ("lernfeld", "Lernfeld-Akte"), ("lernsituation", "Lernsituations-Akte"),
          ("schuljahr", "Schuljahres-Akte"), ("klasse", "Klassen-Akte"), ("stunde", "Stunden-Akte"), ("ref", "Ref-Akte")]


def uebersicht(ab):
    """Gliedert nach Fach und Ebene (nicht nach Ordnertiefe: Stunden liegen unter Unterricht/, ihre Grundlagen unter
    dem Fach, eine Einrückung nach Pfad stellte sie unter fremde Akten). Stunden mit Klasse aus dem Pfad."""
    alle = list(steckbriefe(ab))
    veraltet = {x.split(":")[1].strip() for x in pruefen(ab) if "veraltet" in x}
    zeilen = []
    for fach in sorted({s.get("fach", "Allgemein") for s in alle}):
        zeilen.append(fach)
        for art, name in EBENEN + [(a, a) for a in sorted({s["art"] for s in alle} - {e for e, _ in EBENEN})]:
            teil = sorted((x for x in alle if x.get("fach", "Allgemein") == fach and x["art"] == art), key=lambda x: x["pfad"])
            if not teil:
                continue
            zeilen.append(f"  {name}")
            for s in teil:
                zeichen = "✓" if s["stand"] == "freigegeben" else "…"
                teile = s["pfad"].split("/")
                vor = f"{teile[2]} · " if art == "stunde" and teile[0] == "Unterricht" and len(teile) > 3 else \
                    f"{teile[1].split('_')[-1]} · " if art in ("lernfeld", "lernsituation") and len(teile) > 2 else ""
                alt = " ⚠ veraltet" if s["pfad"] in veraltet else " (ruht)" if s.get("ruhend") else ""
                zeilen.append(f"    {zeichen} {vor}{s['titel']} ({s['stand']}, zuletzt {s['zuletzt_bearbeitet'][:10]}){alt}")
    letzte = max(alle, key=lambda x: x["zuletzt_bearbeitet"], default=None)
    if letzte:
        zeilen.append(f"\nZuletzt gearbeitet an: {letzte['titel']} ({letzte['zuletzt_bearbeitet'].replace('T', ' ')})")
    return "\n".join(zeilen)


if __name__ == "__main__":
    ab = sys.argv[1]
    print(uebersicht(ab))
    b = pruefen(ab)
    print("\n".join(b) if b else "\nKeine Befunde.")
    sys.exit(1 if any(x.startswith("Fehler") for x in b) else 0)
