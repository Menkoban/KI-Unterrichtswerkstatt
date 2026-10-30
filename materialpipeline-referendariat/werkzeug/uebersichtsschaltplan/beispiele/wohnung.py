"""Probe Übersichtsschaltplan zur Wohnung, je Stromkreis ein zusammenhängender Strang (Lehrkraft 2026-10-14).

Verschaltung und Aderzahlen kommen aus werkzeug/installationsplan/beispiele/wohnung_netz.py, derselben Quelle wie der
Installationsplan EI-01. Aufbau wie Europa 32690-3 S. 15: Einspeisung von links in die erste Abzweigdose, Dosen
untereinander verbunden, Leuchten darüber, Schalter und Steckdosen darunter. Nie schräge Linien.
Raumgrenzen gestrichelt mit Raumname. Geräte ohne Dose bekommen die Einspeisung von oben (S. 9).

    python3 werkzeug/uebersichtsschaltplan/beispiele/wohnung.py
Ausgabe: docs/stilreferenz/uebersichtsschaltplan_wohnung_a3.{tex,pdf,png}
"""
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent))
sys.path.insert(0, str(HIER.parents[1] / "installationsplan" / "beispiele"))
from uebersicht import PFEIL_B, PFEIL_L, Element, Leitung, Uebersicht  # noqa: E402
from wohnung_netz import n as NETZ  # noqa: E402

ZIEL = HIER.parents[2] / "docs" / "stilreferenz" / "uebersichtsschaltplan_wohnung_a3"
LICHT, UNTEN, BUS = 5, -7, -5           # Rasterzeilen: Leuchten, Schalter/Steckdosen, Durchschleifen
NYM15, NYM25 = "NYM-J Cu 1,5", "NYM-J Cu 2,5"
MITTE = 999                             # Aderzahl-Strich in der Mitte einer Dose-Dose-Verbindung (Europa S. 15)

u = Uebersicht()
E: dict[str, Element] = {}
GEZEICHNET: set = set()


def setze(fd, art, kenn, gx, gy, *a, **k):
    E[kenn] = getattr(fd, art)(kenn, gx, gy, *a, **k)
    return E[kenn]


def ltg(fd, a, b, ueber=(), **k):
    """Leitung a–b; Aderzahl aus der Verschaltung. Start an einem Element oder an einem Knotenpunkt (gx, gy)."""
    von = k.pop("von", E[a])
    fd.leitung(von, list(ueber), E[b], NETZ.adern(a, b), **k)
    GEZEICHNET.add(frozenset((a, b)))


def zuleitung(fd, ziel, start, sk, leitung, **k):
    fd.einspeisung(E[ziel], start, sk, leitung, adern=NETZ.adern("UV", ziel), **k)
    GEZEICHNET.add(frozenset(("UV", ziel)))


def raeume(fd, grenzen, namen):
    """Gestrichelte Raumgrenzen (Raster-x) und Raumnamen (Raster-x der Mitte)."""
    for gx in grenzen:
        x, _ = fd.p(gx, 0)
        fd.roh.append(f"\\draw[raumgrenze] ({x},{fd.unten + 3}) -- ({x},{fd.oben - 9});")
    for gx, name in namen:
        x, _ = fd.p(gx, 0)
        fd.roh.append(f"\\node[raumname,anchor=north] at ({x},{fd.oben - 9}) {{{name}}};")


# ---------- F1 Beleuchtung: UV → X13 (Küche) → X10 → X11 → X12 (Flur) → X14 → X15 (Wohnzimmer) ----------
f1 = u.feld("Stromkreis F1 – Beleuchtung", 25, 290, 238, 192, oben=286)
for kenn, gx in (("X13", 11), ("X10", 18), ("X11", 24), ("X12", 30), ("X14", 39), ("X15", 46)):
    setze(f1, "dose", kenn, gx, 0)
for kenn, gx in (("E2", 11), ("E1", 30), ("E3", 46)):
    setze(f1, "leuchte", kenn, gx, LICHT)
for kenn, gx, typ in (("Q4", 11, "aus"), ("Q3", 18, "wechsel"), ("Q2", 24, "kreuz"), ("Q1", 30, "wechsel"),
                      ("Q5", 39, "wechsel"), ("Q6", 46, "wechsel")):
    setze(f1, "schalter", kenn, gx, UNTEN, typ)
zuleitung(f1, "X13", 1, "F1", NYM15)
for a, b in (("X13", "X10"), ("X10", "X11"), ("X11", "X12"), ("X12", "X14"), ("X14", "X15")):
    ltg(f1, a, b, ab=MITTE)
for a, b in (("X13", "E2"), ("X13", "Q4"), ("X10", "Q3"), ("X11", "Q2"), ("X12", "E1"), ("X12", "Q1"),
             ("X14", "Q5"), ("X15", "E3"), ("X15", "Q6")):
    ltg(f1, a, b)
raeume(f1, (14.5, 34.5), ((7, "Küche"), (24, "Flur"), (42.5, "Wohnzimmer")))

# ---------- F2 Steckdosen: UV → X16 → X1; X16 → X6 → X7 → X9 → X8 (durchgeschleift) ----------
f2 = u.feld("Stromkreis F2 – Steckdosen Flur und Wohnzimmer", 25, 150, 148, 102, oben=188)
setze(f2, "dose", "X16", 11, 0)
setze(f2, "steckdose", "X1", 11, UNTEN)
for kenn, gx in (("X6", 16), ("X7", 20), ("X9", 24), ("X8", 28)):
    setze(f2, "steckdose", kenn, gx, UNTEN, 2)
zuleitung(f2, "X16", 1, "F2", NYM25)
ltg(f2, "X16", "X1")
ltg(f2, "X16", "X6", [(16, 0)])
for a, b in (("X6", "X7"), ("X7", "X9"), ("X9", "X8")):
    ga, gb = (E[a].x - f2.x0) / 5, (E[b].x - f2.x0) / 5
    ltg(f2, a, b, [(gb, BUS)], von=f2.knoten_bei(ga, BUS), segment=0, ab=MITTE)
raeume(f2, (13.5,), ((7, "Flur"), (22, "Wohnzimmer")))

# ---------- F3–F6 Küche: Arbeitsfläche durchgeschleift, Einzelstromkreise ohne Dose ----------
f3 = u.feld("Stromkreise F3–F6 – Küche", 180, 135, 148, 102, oben=188)
setze(f3, "steckdose", "X3", 4, UNTEN, 2, zweck="Arbeits-\\\\fläche")
setze(f3, "steckdose", "X4", 8, UNTEN, 2, zweck="Arbeits-\\\\fläche")
setze(f3, "steckdose", "X2", 13, UNTEN, zweck="Kühlschrank")
setze(f3, "steckdose", "X5", 17, UNTEN, zweck="Geschirr-\\\\spüler")
setze(f3, "herd", "E4", 22, UNTEN + 0.4, zweck="Elektroherd")
for kenn, sk in (("X3", "F3"), ("X2", "F4"), ("X5", "F5")):
    zuleitung(f3, kenn, LICHT, sk, NYM15, richtung="oben")
zuleitung(f3, "E4", LICHT, "F6", NYM25, richtung="oben", text="L1/L2/L3/N/PE")
ltg(f3, "X3", "X4", [(8, BUS)], von=f3.knoten_bei(4, BUS), segment=0, ab=MITTE)

fehlt = {frozenset(k) for k in NETZ.kanten} - GEZEICHNET
if fehlt:
    raise SystemExit(f"Leitungen aus der Verschaltung nicht gezeichnet: {sorted(map(sorted, fehlt))}")

# ---------- Zeichenerklärung: vier Spalten, Zeichen und Text auf gleicher Mittellinie ----------
lg = u.feld("Zeichenerklärung", 25, 290, 80, 38, oben=97)
SP = (3, 15, 27, 41)                     # Spalten (Raster) der Zeichen; Text 3 Raster rechts davon
for (sp, gy), (art, a, text) in zip(((s, r) for s in SP[:3] for r in (0, -3, -6)), (
        ("dose", (), "Abzweigdose"), ("leuchte", (), "Leuchte"), ("herd", (), "Herdanschluss"),
        ("schalter", ("aus",), "Ausschalter"), ("schalter", ("wechsel",), "Wechselschalter"),
        ("schalter", ("kreuz",), "Kreuzschalter"),
        ("steckdose", (), "Schutzkontaktsteckdose"), ("steckdose", (2,), "Doppelsteckdose"),
        ("knoten", (), "Verbindungspunkt (Knotenpunkt)"))):
    dy = {"steckdose": 0.25, "herd": 0.6}.get(art, 0)
    if art == "knoten":
        lg.knoten_bei(sp, gy)
    else:
        getattr(lg, art)("", sp, gy + dy, *a)
    lg.text(sp + 3, gy, text)
x, y = lg.p(SP[3] - 2, 0)                # Einspeisung
lg.roh.append(f"\\draw ({x},{y}) -- ({x + 10},{y}); \\fill ({x + 10 - PFEIL_L},{y - PFEIL_B / 2}) -- "
              f"({x + 10 - PFEIL_L},{y + PFEIL_B / 2}) -- ({x + 10},{y}) -- cycle;")
lg.text(SP[3] + 3, 0, "Einspeisung vom Unterverteiler")
x, y = lg.p(SP[3] - 2, -3)               # Aderzahl
lg.leitungen.append(Leitung([(x, y), (x + 10, y)], 3, 0, 5, Element("legende", "", x + 10, y)))
lg.text(SP[3] + 3, -3, "Leitung mit Aderzahl (einschl. PE)")
x, y = lg.p(SP[3] - 2, -6)               # Verlegeart
lg.roh.append(f"\\draw ({x},{y}) -- ({x + 10},{y});")
lg.roh += u._putz((x, y), (x + 10, y), 5, "UP")
lg.text(SP[3] + 3, -6, "Leitung unter Putz")

HINWEISE = (r"Übersichtsschaltplan zum Installationsplan EI-01 (gleiche Kennzeichen und Verschaltung): "
            r"Q Schalter, E Leuchten und Herd, X Dosen und Steckdosen.\\[1mm]"
            r"Je Stromkreis eine Zuleitung vom Unterverteiler UV; danach sind die Abzweigdosen untereinander "
            r"verbunden. Gestrichelt: Raumgrenzen.\\[1mm]"
            r"Aderzahl an jeder Leitung einschließlich Schutzleiter, auch wo das Betriebsmittel keinen braucht; "
            r"berechnet aus der Verschaltung.\\[1mm]"
            r"An jeder Einspeisung: Stromkreis, Leitungsangabe und Verlegeart. Alle Leitungen NYM-J unter Putz, "
            r"Cu 1,5\,mm²; F2 und Herd Cu 2,5\,mm² (Spannungsfall). F2 in der unteren, übrige in der oberen "
            r"Installationszone.\\[1mm]"
            r"X3/X4 und X6–X9 durchgeschleift: Abzweig an der Steckdose mit Verbindungspunkt.\\[1mm]"
            r"Netz TN-S ab Zählerplatz, 3/N/PE AC 400/230\,V 50\,Hz. Bemessungsströme, Fehlerstrom-Schutzschalter "
            r"und Leitungslängen siehe Verteiler-Übersichtsschaltplan.")
SCHRIFTFELD = {
    "bauherr": "Familie Hinrichs, Musterstadt (fiktiv)",
    "bauvorhaben": "Sanierung Wohnung 2. OG",
    "planinhalt": "Übersichtsschaltplan Installation",
    "fachplanung": "Brinkmann Automation (fiktiver Modellbetrieb)",
    "gewerk": "Elektro",
    "massstab": "ohne", "format": "A3", "datum": "14.10.2026", "erstellt": "BA",
    "plannr": "EI-02", "stand": "Probe",
    "fuss": r"Eigene Darstellung nach dem Vorbild von Tapken, H.: Schalten, Steuern und Automatisieren – "
            r"Aufgabensammlung. 3. Aufl., Haan-Gruiten: Europa-Lehrmittel 2025, S. 6–20. "
            r"Zeichen nach DIN EN 60617-11. Erstellt mit KI-Unterstützung.",
}

if __name__ == "__main__":
    for m in NETZ.pruefen():
        print(*m, sep=": ")
    print(u.bauen(ZIEL, HINWEISE, SCHRIFTFELD))
