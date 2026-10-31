"""Probekurs für das Klassen-Dashboard mit gestuften Aufgaben (6 Kacheln), zwei Meilensteinen und Dashboard.

    python3 probe_stufenkurs.py <ziel.mbz>
"""
import copy
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bauen  # noqa: E402
import dashboard  # noqa: E402
import pruefen  # noqa: E402
import stufen  # noqa: E402

M1 = {"id": "m1", "kurz": "Meilenstein 1", "titel": "Meilenstein 1 · Fehler eingrenzen", "kriterien": [
    {"name": "Fehlerbild und Vermutungen", "stufen": ["Fehlerbild fehlt; keine Vermutung", "eine Vermutung ohne Begründung",
                                                     "mehrere Vermutungen, teils begründet", "mehrere Vermutungen, jede begründet"]},
    {"name": "Eigener Prüfplan", "stufen": ["kein Plan", "Schritte ohne begründete Reihenfolge",
                                           "begründete Reihenfolge mit Messmitteln", "mit Sollwerten und Gegenprobe"]},
    {"name": "Sicher gearbeitet", "stufen": ["Regeln missachtet", "nur nach Hinweis", "selbstständig eingehalten",
                                            "eingehalten und im Plan ausgewiesen"]}]}
M2 = {"id": "m2", "kurz": "Meilenstein 2", "titel": "Meilenstein 2 · Ursache belegen und Kundschaft informieren", "kriterien": [
    {"name": "Messen und Auswerten", "stufen": ["Messwerte fehlen", "Auswertung lückenhaft", "mit Sollwerten verglichen", "Abweichungen beurteilt"]},
    {"name": "Ursache belegt", "stufen": ["keine Ursache", "genannt, ohne Beleg", "mit Messwerten belegt", "andere Vermutungen ausgeschlossen"]},
    {"name": "Information für die Kundschaft", "stufen": ["fehlt oder unverständlich", "verständlich, fachlich lückenhaft",
                                                         "verständlich, fachlich richtig", "alle Fragen beantwortet, Lösung begründet"]}]}


def kurs():
    def aufg(t):
        return {"thema": t, "fragen": [{"typ": "truefalse", "name": t, "text": "<p>Stimmt das?</p>", "richtig": True}]}
    abschnitte = []
    for n in range(1, 7):
        akts = [{"typ": "label", "name": f"Auftrag {n}", "text": "<p>Ihr Auftrag in dieser Kachel.</p>"},
                {"typ": "stufen", "kachel": n, "titel": f"Kachel {n}",
                 "aufgaben": {s: [aufg(f"{s} {n} a"), aufg(f"{s} {n} b")] for s in stufen.STUFEN}}]
        if n == 3:
            akts.append(dashboard.selbsteinschaetzung(M1))
        if n == 6:
            akts.append(dashboard.selbsteinschaetzung(M2))
        abschnitte.append({"name": f"{n} · Kachel {n}", "aktivitaeten": akts})
    k = {"kurs": {"vollname": "Probe Klassen-Dashboard mit Stufen", "kurzname": "KD-STUFEN", "beschreibung": "<p>Probe</p>",
                  "ki_hinweis": "mit Hilfe von künstlicher Intelligenz", "format": "tiles", "ursache": {"keine": True}},
         "abschnitte": abschnitte}
    stufen.einsetzen(k)
    k["abschnitte"].append({"name": "Material für Lehrkräfte", "lehrkraft": True, "sichtbar": False,
                            "aktivitaeten": [
                                {"typ": "resource", "name": "Lernstand-Dashboard", "datei": "lehrkraft/lernstand-dashboard.html",
                                 "anzeige": "eingebettet", "sichtbar": False, "abschluss": "keine"},
                                dashboard.dashboard_aktivitaet([M1, M2], 2, k, name=dashboard.DATEN_NAME)]})
    return k


LERNSTAND = {"kurs": "Probe Klassen-Dashboard mit Stufen", "kurzname": "KD-STUFEN",
             "medaillen": [{"name": "Gold", "ab": 92}, {"name": "Silber", "ab": 81}, {"name": "Bronze", "ab": 50},
                           {"name": "Grün", "ab": 1}],
             "stern_tests": [], "hilfekarten": [], "testpaare": [], "sterne_max": 3, "fehlvorstellungen": [],
             "tests": [], "feedbacks": []}


if __name__ == "__main__":
    ziel = Path(sys.argv[1])
    with tempfile.TemporaryDirectory() as t:
        stufen.dateien_anlegen(Path(t))
        k = kurs()
        (Path(t) / "lehrkraft").mkdir(exist_ok=True)
        (Path(t) / "lehrkraft" / "lernstand-dashboard.html").write_text(
            dashboard.lernstand_datei(LERNSTAND, [M1, M2], 2, k), encoding="utf-8")
        bauen.baue(copy.deepcopy(k), Path(t), ziel)
        befunde = pruefen.pruefe(ziel, k)
        print(pruefen.bericht([b for b in befunde if b.stufe == pruefen.FEHLER]) if any(b.stufe == pruefen.FEHLER for b in befunde)
              else "Keine Fehler (" + str(len(befunde)) + " Hinweise)")
