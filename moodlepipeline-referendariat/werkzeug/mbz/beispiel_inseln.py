"""Beispiel-Themenkurs (fiktiv) mit zwei Übungsinseln und „Mein Lernpfad“ bauen und prüfen.

    python3 beispiel_inseln.py [--ziel ausgabe/beispiel_inseln.mbz]

Grundlage ist der Beispielkurs (beispiel.py): Kachel 2 bekommt nach dem Messprotokoll die Insel 1 „Leistung und
Strom“ und einen Stern „selbst gelöst“; eine neue Kachel 3 hat eine Abgabe und danach die Insel 2 „Widerstand“.
Kursschalter: Sternzähler und Lernpfad an. Rückgabe 1, wenn ein Prüfer einen Fehler meldet.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bauen  # noqa: E402
import beispiel  # noqa: E402
import pruefen  # noqa: E402
import sterne  # noqa: E402

MESSPROTOKOLL = "Auftrag: Messprotokoll Haus Schütte"
ABGABE_3 = "Auftrag: Widerstand der Heizmatte"


def rechenfrage(name: str, text: str, formel: str, variablen: list[dict], plausibel: list) -> dict:
    return {"typ": "calculated", "name": name, "text": text, "formel": formel, "toleranz": 0.02,
            "nachkommastellen": 2, "plausibel": plausibel, "variablen": variablen}


def _fragen_leistung(stufe: str, n: int, kennung: str) -> list[dict]:
    """n berechnete Fragen zu P = U · I je Stufe (Zahlen nach Stufe)."""
    bereich = {"Grundlagen": (100, 1000, 0), "Standard": (300, 2500, 0), "Vertiefung": (150, 3600, 0)}[stufe]
    aus = []
    for i in range(1, n + 1):
        if stufe == "Vertiefung":
            aus.append(rechenfrage(f"{kennung} {i}", "<p>Eine Heizmatte hat {R} Ω an 230 V. Welche Leistung in W "
                                   "nimmt sie auf?</p>", "230*230/{R}", [{"name": "R", "min": 20, "max": 120}],
                                   [400, 2700]))
        else:
            aus.append(rechenfrage(f"{kennung} {i}", "<p>Ein Gerät nimmt {P} W an 230 V auf. Berechnen Sie den "
                                   "Strom in A.</p>", "{P}/230",
                                   [{"name": "P", "min": bereich[0], "max": bereich[1]}], [0.3, 12]))
    return aus


def _fragen_widerstand(stufe: str, n: int, kennung: str) -> list[dict]:
    lo, hi = {"Grundlagen": (1, 10), "Standard": (0.5, 16), "Vertiefung": (0.1, 16)}[stufe]
    return [rechenfrage(f"{kennung} {i}", "<p>Durch einen Widerstand fließen {I} A bei 230 V. Berechnen Sie den "
                        "Widerstand in Ω.</p>", "230/{I}", [{"name": "I", "min": lo, "max": hi, "nachkommastellen": 1}],
                        [10, 2500]) for i in range(1, n + 1)]


def insel(nr: int, name: str, fragen, voraussetzung: list) -> dict:
    return {"typ": "insel", "nr": nr, "name": name, "voraussetzung": voraussetzung,
            "stufen": {s: {"uebung": {"fragen": fragen(s, 2, f"I{nr} {s} Üben"),
                                      **({"verhalten": "interactive"} if s == "Grundlagen" else {})},
                           "kurztest": {"fragen": fragen(s, 3, f"I{nr} {s} Kurztest")}}
                       for s in ("Grundlagen", "Standard", "Vertiefung")}}


def kursdefinition() -> dict:
    k = copy.deepcopy(beispiel.kursdefinition())
    k["kurs"].update(vollname="EG1 · LF 1 · LS 9 Beispiel mit Übungsinseln", kurzname="EG1-LF01-LS09",
                     sternzaehler=True, lernpfad=True, schulfarben=["#08349C", "#7DDE78"])
    ab2 = k["abschnitte"][1]
    hilfe = sterne.hilfekarte("Hilfe zum Messprotokoll", "<p>Welche Größen stehen auf dem Typenschild?</p>")
    i = next(j for j, a in enumerate(ab2["aktivitaeten"]) if a["name"] == MESSPROTOKOLL)
    ab2["aktivitaeten"][i + 1:i + 1] = [
        hilfe,
        insel(1, "Insel 1: Leistung und Strom", _fragen_leistung,
              [{"abschluss": MESSPROTOKOLL, "zustand": "abgeschlossen"}]),
        sterne.stern_aktivitaet(ab2, MESSPROTOKOLL, [hilfe["name"]])]
    k["abschnitte"].insert(2, {
        "name": "3 · Übung: Widerstand der Heizmatte", "sichtbar": False,
        "zusammenfassung": "<p>Familie Schütte will wissen, welchen Widerstand die Heizmatte hat. Rechnen Sie es "
                           "aus und üben Sie danach auf Ihrer Stufe.</p>",
        "aktivitaeten": [
            {"typ": "assign", "name": ABGABE_3, "bewertung": "keine", "abgabe": ["onlinetext"],
             "abschluss": "abgabe",
             "beschreibung": "<p>Berechnen Sie den Widerstand der Heizmatte mit Rechenweg.</p>"},
            insel(2, "Insel 2: Widerstand", _fragen_widerstand,
                  [{"abschluss": ABGABE_3, "zustand": "abgeschlossen"}])]})
    sterne.idnummern(k["abschnitte"])          # wie allgemein.anwenden: stern-k<n>, hilfe-k<n>-s<m>
    return k


def main(ziel: Path) -> int:
    wurzel = ziel.parent / "beispiel_dateien"
    beispiel.dateien_anlegen(wurzel)
    kurs = kursdefinition()
    bauen.baue(kurs, wurzel, ziel)
    (ziel.parent / "beispiel_inseln.json").write_text(json.dumps(kurs, ensure_ascii=False, indent=1),
                                                       encoding="utf-8")
    befunde = pruefen.pruefe(ziel, kurs)
    print(pruefen.bericht(befunde))
    return 1 if any(b.stufe == pruefen.FEHLER for b in befunde) else 0


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ziel", type=Path, default=Path("ausgabe/beispiel_inseln.mbz"))
    a = ap.parse_args()
    a.ziel.parent.mkdir(parents=True, exist_ok=True)
    sys.exit(main(a.ziel))
