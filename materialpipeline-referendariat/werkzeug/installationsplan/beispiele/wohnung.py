"""Probe Installationsplan: Wohnung mit Flur, Küche, Wohnzimmer (Entscheidung 2026-10-14, B).

    cd werkzeug/installationsplan && python3 beispiele/wohnung.py
Ausgabe: docs/stilreferenz/installationsplan_wohnung_a3.{tex,pdf,png}
"""
import math
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent))
from grundriss import Plan  # noqa: E402
from wohnung_netz import n as NETZ  # noqa: E402  (Aderzahl aus der Verschaltung)

ZIEL = HIER.parents[2] / "docs" / "stilreferenz" / "installationsplan_wohnung_a3"

p = Plan("Wohnung")
# Rohbau: Außenwände 30 cm, Innenwände 11,5 cm; Innenmaß 8,50 m × 6,00 m
p.wand(-0.3, -0.3, 8.8, 0)
p.wand(-0.3, 6.0, 8.8, 6.3)
p.wand(-0.3, 0, 0, 6.0)
p.wand(8.5, 0, 8.8, 6.0)
p.wand(3.4, 0, 3.64, 6.0)                                # tragende Innenwand 24 cm
p.wand(0, 2.9, 3.4, 3.015)
p.tuer(0.6, -0.3, 1.61, 0, (0.6, 0), "oben")             # Wohnungstür
p.tuer(2.2, 2.9, 3.085, 3.015, (3.085, 3.015), "oben")    # Küche
p.tuer(3.4, 1.9, 3.64, 2.785, (3.64, 2.785), "rechts")  # Wohnzimmer
p.tuer(8.5, 3.5, 8.8, 4.51, (8.5, 4.51), "links")         # Balkontür
p.fenster(-0.3, 4.0, 0, 5.26)                             # Küche
p.fenster(4.8, 6.0, 6.81, 6.3)                            # Wohnzimmer
p.fenster(8.5, 1.0, 8.8, 2.26)
p.raum("Flur", 0, 0, 3.4, 2.9, lage=(2.7, 2.15))
p.raum("Küche", 0, 3.015, 3.4, 6.0, lage=(2.4, 4.15))
p.raum("Wohnzimmer", 3.64, 0, 8.5, 6.0, lage=(6.0, 4.4))

# Flur: Kreuzschaltung (Wohnungstür, Wohnzimmertür, Küchentür)
p.geraet("leuchte", 1.7, 1.45, stromkreis="E1")
p.geraet("schalter", 2.0, 0, "unten", "wechsel", "Q1", text_seite=-1)
p.geraet("schalter", 3.4, 1.65, "rechts", "kreuz", "Q2")
p.geraet("schalter", 1.85, 2.9, "oben", "wechsel", "Q3")
p.geraet("steckdose", 0, 1.85, "links", stromkreis="X1")
p.geraet("verteiler", 0, 2.2, "links", kenn="UV", text_lage=(-0.6, 0, "east"))
# Küche: Ausschaltung, Arbeitssteckdosen, Geräte
p.geraet("schalter", 1.95, 3.015, "unten", "aus", "Q4")
p.geraet("leuchte", 1.7, 4.5, stromkreis="E2")
p.geraet("steckdose2", 0.7, 6.0, "oben", stromkreis="X3")
p.geraet("herd", 2.65, 6.0, "oben", stromkreis="E4", text_lage=(0, -7.0, "north"))
p.geraet("steckdose2", 1.65, 6.0, "oben", stromkreis="X4")
p.geraet("steckdose", 3.4, 4.6, "rechts", stromkreis="X5")
p.geraet("steckdose", 0, 3.8, "links", stromkreis="X2", text_lage=(8.5, 0))
# Wohnzimmer: Wechselschaltung (Tür, Balkontür), Steckdosen
p.geraet("schalter", 3.64, 1.65, "links", "wechsel", "Q5")
p.geraet("schalter", 8.5, 3.2, "rechts", "wechsel", "Q6", text_seite=1)
p.geraet("leuchte", 6.0, 3.0, stromkreis="E3")
p.geraet("steckdose2", 4.6, 0, "unten", stromkreis="X6")
p.geraet("steckdose2", 7.4, 0, "unten", stromkreis="X7")
p.geraet("steckdose2", 4.2, 6.0, "oben", stromkreis="X8")
p.geraet("steckdose2", 7.6, 6.0, "oben", stromkreis="X9")

LEGENDE = [
    ("steckdose", "", "Schutzkontaktsteckdose"),
    ("steckdose2", "", "Schutzkontaktsteckdose, zweifach"),
    ("schalter", "aus", "Ausschalter"),
    ("schalter", "wechsel", "Wechselschalter"),
    ("schalter", "kreuz", "Kreuzschalter"),
    ("leuchte", "", "Leuchtenauslass (Leuchte)"),
    ("herd", "", "Herdanschluss"),
    ("verteiler", "", "Unterverteiler"),
]
HINWEISE = (r"Installation unter Putz. Höhen über fertigem Fußboden: Steckdosen 0,30\,m, Schalter 1,05\,m, "
            r"Arbeitssteckdosen Küche 1,15\,m, Unterkante Unterverteiler 1,25\,m.\\[1mm]"
            r"Leitungsführung in den Installationszonen nach DIN 18015-3.\\[1mm]"
            r"Gerätekennzeichen nach DIN EN IEC 81346-2 (wie Europa-Lehrbuch): Q Schalter, E Leuchten und Herd, "
            r"X Steckdosen und Dosen. X2 Kühlschrank, X3/X4 Arbeitssteckdosen, X5 Geschirrspüler. "
            r"Stromkreise: siehe Übersichtsschaltplan.")
SCHRIFTFELD = {
    "bauherr": "Familie Hinrichs, Musterstadt (fiktiv)",
    "bauvorhaben": "Sanierung Wohnung 2. OG",
    "planinhalt": "Grundriss Elektroinstallation",
    "fachplanung": "Brinkmann Automation (fiktiver Modellbetrieb)",
    "gewerk": "Elektro",
    "massstab": "1:50", "format": "A3", "datum": "14.10.2026", "erstellt": "BA",
    "plannr": "EI-01", "stand": "Probe",
    "fuss": r"Eigene Darstellung. Zeichen nach DIN EN 60617-11 aus der QElectroTech-Elementsammlung "
            r"(CC BY 3.0). Erstellt mit KI-Unterstützung.",
}



def leitungen_auf_putz(p):
    """Lehrbuch-Fassung auf Putz (Fachkunde S. 102, Regel 14c): Leitungen raumseitig vor der Wand (Spuren 13, 18,
    23, 28, 33 cm), Geräte sitzen auf ihrer Leitung, Abzweigdosen auf der Spur. Gleiche Verschaltung und Aderzahl wie
    unter Putz (wohnung_netz.py). Wer früher abzweigt, liegt weiter vorn; Leitungen dahinter laufen hinter den
    Geräten vorbei. Drei Kreuzungen im Wohnzimmer (F1 obere, F2 untere Installationszone)."""
    o = lambda k: 0.08 + 0.05 * k            # Spur vor der Wand, k = 1 (wandnah) … 5   # noqa: E731
    FT = lambda k: 2.9 - o(k)                # Flur oben                 # noqa: E731
    FR = lambda k: 3.4 - o(k)                # Flur rechts               # noqa: E731
    KB = lambda k: 3.015 + o(k)              # Küche unten               # noqa: E731
    KT = lambda k: 6.0 - o(k)                # Küche oben                # noqa: E731
    KR = lambda k: 3.4 - o(k)                # Küche rechts              # noqa: E731
    WL = lambda k: 3.64 + o(k)               # Wohnzimmer links          # noqa: E731
    WT = lambda k: 6.0 - o(k)                # Wohnzimmer oben           # noqa: E731
    WR = lambda k: 8.5 - o(k)                # Wohnzimmer rechts         # noqa: E731
    g = {x.stromkreis: x for x in p.geraete}
    for bmk, k in (("X1", 3), ("X2", 4), ("X3", 3), ("X4", 3), ("E4", 2), ("X5", 1), ("Q1", 5), ("Q2", 5),
                   ("Q3", 3), ("Q4", 5), ("Q5", 5), ("Q6", 5), ("X6", 4), ("X7", 4), ("X8", 4), ("X9", 4)):
        g[bmk].vor = o(k)
    g["E1"].text_lage = (-2.6, 0, "east")
    g["Q4"].text_seite = -1
    g["Q2"].text_lage = (-7.2, 0, "east")       # links neben den Haken, frei von X11
    r = 0.075
    D = {"X13": (1.45, KB(5)), "X10": (1.45, FT(3)), "X11": (FR(3), 1.35), "X12": (2.4, o(5)),
         "X14": (WL(3), 1.35), "X15": (WR(2), 2.6), "X16": (o(1), 1.45)}
    lage = {"X13": (-1.2, 1.2, "south east"), "X10": (-1.2, -1.2, "north east"), "X11": (-1.2, -1.2, "north east"),
            "X12": (1.2, 1.2, "south west"), "X14": (1.2, -1.2, "north west"), "X15": (-1.2, -1.2, "north east"),
            "X16": (1.2, -1.2, "north west")}
    for k, d in D.items():
        p.geraet("abzweig", *d, stromkreis=k, text_lage=lage[k])

    def oben(k, dx=0):
        return D[k][0] + dx, D[k][1] + math.sqrt(r * r - dx * dx)

    def unten(k, dx=0):
        return D[k][0] + dx, D[k][1] - math.sqrt(r * r - dx * dx)

    def links(k, dy=0):
        return D[k][0] - math.sqrt(r * r - dy * dy), D[k][1] + dy

    def rechts(k, dy=0):
        return D[k][0] + math.sqrt(r * r - dy * dy), D[k][1] + dy

    def ltg(a, b, punkte):
        p.leitung(punkte, NETZ.adern(a, b), putz="AP")
        KANTEN["AP"].append((a, b))

    U = 0.096                                # Raumkante des Unterverteilers
    # F1 Beleuchtung: UV → X13 → X10 → X11 → X12 → X14 → X15
    ltg("UV", "X13", [(U, 2.20), (o(5), 2.20), (o(5), KB(5)), links("X13")])
    ltg("X13", "X10", [unten("X13"), oben("X10")])
    ltg("X13", "Q4", [rechts("X13"), (1.95, KB(5)), (1.95, KB(5) + 0.15)])
    ltg("X13", "E2", [oben("X13"), (1.45, 4.5), (1.7, 4.5)])
    ltg("X10", "Q3", [rechts("X10"), (1.85, FT(3)), (1.85, FT(3) - 0.15)])
    ltg("X10", "X11", [oben("X10", 0.05), (1.50, FT(1)), (FR(1), FT(1)), (FR(1), 1.40), rechts("X11", 0.05)])
    ltg("X11", "Q2", [oben("X11"), (FR(3), 1.65), (FR(5) - 0.15, 1.65)])   # vorn, Hebel frei von FR(1)
    ltg("X11", "X12", [unten("X11"), (FR(3), o(5)), rechts("X12")])
    ltg("X12", "Q1", [links("X12"), (2.0, o(5)), (2.0, o(5) + 0.15)])
    ltg("X12", "E1", [oben("X12"), (2.4, 1.45), (1.7, 1.45)])
    ltg("X12", "X14", [unten("X12"), (2.4, o(3)), (WL(1), o(3)), (WL(1), 1.35), links("X14")])
    ltg("X14", "Q5", [oben("X14"), (WL(3), 1.65), (WL(5) + 0.15, 1.65)])
    ltg("X14", "X15", [unten("X14"), (WL(3), o(2)), (WR(2), o(2)), unten("X15")])
    ltg("X15", "Q6", [oben("X15"), (WR(2), 3.2), (WR(5), 3.2), (WR(5) - 0.15, 3.2)])
    ltg("X15", "E3", [links("X15"), (6.0, 2.6), (6.0, 3.0)])
    # F2 Steckdosen: UV → X16 → X1; X16 → X6 → X7 → X9 → X8 (durchgeschleift, auf der Spur)
    ltg("UV", "X16", [(U, 2.08), (o(1), 2.08), oben("X16")])
    ltg("X16", "X1", [rechts("X16", 0.04), (o(3), D["X16"][1] + 0.04), (o(3), 1.85)])
    ltg("X16", "X6", [unten("X16"), (o(1), o(1)), (4.0, o(1)), (4.0, o(4)), (4.6, o(4))])
    ltg("X6", "X7", [(4.6, o(4)), (7.4, o(4))])
    ltg("X7", "X9", [(7.4, o(4)), (WR(4), o(4)), (WR(4), WT(4)), (7.6, WT(4))])
    ltg("X9", "X8", [(7.6, WT(4)), (4.2, WT(4))])
    # F3–F6 Küche (Spuren am Unterverteiler: nach oben startet die vordere Spur tiefer)
    ltg("UV", "X3", [(U, 2.28), (o(3), 2.28), (o(3), KT(3)), (0.7, KT(3))])
    ltg("X3", "X4", [(0.7, KT(3)), (1.65, KT(3))])
    ltg("UV", "X2", [(U, 2.24), (o(4), 2.24), (o(4), 3.8)])
    ltg("UV", "E4", [(U, 2.32), (o(2), 2.32), (o(2), KT(2)), (2.65, KT(2))])
    ltg("UV", "X5", [(U, 2.36), (o(1), 2.36), (o(1), KT(1)), (KR(1), KT(1)), (KR(1), 4.6)])


KANTEN: dict = {"UP": [], "AP": []}         # gezeichnete Leitungen je Fassung (Plansatz-Prüfung)
STRECKEN: dict = {}                          # (von, nach) → Linienzug im Grundriss (m), Unterputz-Fassung


def leitungen_unter_putz(p):
    """Lehrbuch-Fassung unter Putz (Regeln 14–17, 14a, 14c, 18): Leitungen in den Wänden, je Stromkreis eine Zuleitung
    vom Unterverteiler, danach Abzweigdosen untereinander verbunden (Verschaltung und Aderzahl aus wohnung_netz.py).
    Dosen im Raum 12 cm vor der Wand, Abgänge rechtwinklig in die Wand; Leuchten rechtwinklig in den Raum.
    Spuren: Außenwände 5 cm Teilung, Wand Flur/Küche drei Spuren, Wand zum Wohnzimmer je zwei Spuren pro Seite."""
    next(g for g in p.geraete if g.kenn == "UV").text_lage = (0.4, 4.0, "south west")   # Wand ist belegt
    g = {x.stromkreis: x for x in p.geraete}
    g["E1"].text_lage = (-2.6, 0, "east")      # Zuleitung kommt von rechts
    g["Q4"].text_seite = -1                    # links läuft die Leitung zu E2
    L = lambda k: -0.05 * k                  # linke Außenwand          # noqa: E731
    B = lambda k: -0.05 * k                  # untere Außenwand         # noqa: E731
    T = lambda k: 6.0 + 0.05 * k             # obere Außenwand          # noqa: E731
    Rw = lambda k: 8.5 + 0.05 * k            # rechte Außenwand         # noqa: E731
    H1, H2, H3 = 2.925, 2.9575, 2.99         # Wand Flur/Küche 2,90–3,015
    VF1, VF2, VW2, VW1 = 3.45, 3.50, 3.54, 3.59   # Wand 3,40–3,64 (Flur bzw. Küche … Wohnzimmer)
    r = 0.075                                # Abzweigdose Ø 3,0 mm
    D = {"X13": (1.45, 3.28), "X10": (1.45, 2.64), "X11": (3.28, 0.80), "X12": (2.5, 0.12),
         "X14": (3.76, 0.80), "X15": (8.38, 2.60), "X16": (0.12, 1.50)}
    lage = {"X13": (-1.2, 0, "east"), "X10": (-1.2, 0, "east"), "X11": (-1.2, -1.2, "north east"),
            "X12": (1.2, 1.2, "south west"), "X14": (1.2, -1.2, "north west"), "X15": (-1.2, -1.2, "north east"),
            "X16": (1.2, -1.2, "north west")}
    for k, d in D.items():
        p.geraet("abzweig", *d, stromkreis=k, text_lage=lage[k])

    def oben(k, dx):
        return D[k][0] + dx, D[k][1] + math.sqrt(r * r - dx * dx)

    def unten(k, dx):
        return D[k][0] + dx, D[k][1] - math.sqrt(r * r - dx * dx)

    def links(k, dy):
        return D[k][0] - math.sqrt(r * r - dy * dy), D[k][1] + dy

    def rechts(k, dy):
        return D[k][0] + math.sqrt(r * r - dy * dy), D[k][1] + dy

    def ltg(a, b, punkte):
        p.leitung(punkte, NETZ.adern(a, b), putz="UP")
        KANTEN["UP"].append((a, b))
        STRECKEN[(a, b)] = punkte                # Grundrisslänge für den Spannungsfall (Verteilerplan)

    # F1 Beleuchtung: UV → X13 → X10 → X11 → X12 → X14 → X15
    x = D["X10"][0]                          # X10 und X13 übereinander, Abgänge in die Wand Flur/Küche
    ltg("UV", "X13", [(0, 2.36), (L(1), 2.36), (L(1), H3), (x - 0.06, H3), unten("X13", -0.06)])
    ltg("X13", "X10", [unten("X13", -0.02), oben("X10", -0.02)])
    ltg("X13", "Q4", [unten("X13", 0.06), (x + 0.06, H3), (1.95, H3), (1.95, 3.165)])
    ltg("X13", "E2", [oben("X13", 0), (x, 4.5), (1.7, 4.5)])
    y = D["X11"][1]                          # X11 und X14 auf gleicher Höhe beiderseits der Wand
    ltg("X10", "Q3", [oben("X10", 0.06), (x + 0.06, H1), (1.85, H1), (1.85, 2.75)])
    ltg("X10", "X11", [oben("X10", 0.02), (x + 0.02, H2), (VF2, H2), (VF2, y + 0.02), rechts("X11", 0.02)])
    ltg("X11", "Q2", [rechts("X11", 0.06), (VF1, y + 0.06), (VF1, 1.65), (3.25, 1.65)])
    ltg("X11", "X12", [rechts("X11", -0.06), (VF1, y - 0.06), (VF1, B(1)), (2.55, B(1)), unten("X12", 0.05)])
    ltg("X12", "Q1", [unten("X12", -0.05), (2.45, B(1)), (2.0, B(1)), (2.0, 0.15)])
    ltg("X12", "E1", [oben("X12", 0), (2.5, 1.45), (1.7, 1.45)])
    ltg("X12", "X14", [unten("X12", 0), (2.5, B(2)), (VW2, B(2)), (VW2, y - 0.06), links("X14", -0.06)])
    ltg("X14", "Q5", [links("X14", 0.06), (VW1, y + 0.06), (VW1, 1.65), (3.79, 1.65)])
    # Wohnzimmerlicht über die Außenwände (kürzer als um den Raum; Spannungsfall, Entscheidung A 2026-10-14).
    # Kreuzt F2 zweimal im Grundriss: F1 liegt in der oberen, F2 in der unteren Installationszone
    ltg("X14", "X15", [unten("X14", 0), (D["X14"][0], B(4)), (Rw(4), B(4)), (Rw(4), 2.56), rechts("X15", -0.04)])
    ltg("X15", "Q6", [rechts("X15", 0.04), (Rw(1), 2.64), (Rw(1), 3.2), (8.35, 3.2)])
    ltg("X15", "E3", [links("X15", 0), (6.0, 2.6), (6.0, 3.0)])
    # F2 Steckdosen Flur/Wohnzimmer: UV → X16 → X1; X16 → X6 → X7 → X9 → X8 (durchgeschleift)
    ltg("UV", "X16", [(0, 2.08), (L(2), 2.08), (L(2), 1.50), links("X16", 0)])
    ltg("X16", "X1", [links("X16", 0.05), (L(1), 1.55), (L(1), 1.85), (0, 1.85)])
    ltg("X16", "X6", [links("X16", -0.05), (L(3), 1.45), (L(3), B(3)), (4.56, B(3)), (4.56, 0)])
    ltg("X6", "X7", [(4.64, 0), (4.64, B(3)), (7.36, B(3)), (7.36, 0)])
    ltg("X7", "X9", [(7.44, 0), (7.44, B(3)), (Rw(3), B(3)), (Rw(3), T(1)), (7.64, T(1)), (7.64, 6.0)])
    ltg("X9", "X8", [(7.56, 6.0), (7.56, T(1)), (4.2, T(1)), (4.2, 6.0)])
    # F3 Arbeitsfläche (durchgeschleift), F4 Kühlschrank, F5 Geschirrspüler, F6 Herd
    ltg("UV", "X3", [(0, 2.28), (L(3), 2.28), (L(3), T(1)), (0.66, T(1)), (0.66, 6.0)])
    ltg("X3", "X4", [(0.74, 6.0), (0.74, T(1)), (1.65, T(1)), (1.65, 6.0)])
    ltg("UV", "X2", [(0, 2.32), (L(2), 2.32), (L(2), 3.8), (0, 3.8)])
    ltg("UV", "E4", [(0, 2.24), (L(4), 2.24), (L(4), T(2)), (2.65, T(2)), (2.65, 6.0)])
    ltg("UV", "X5", [(0, 2.20), (L(5), 2.20), (L(5), T(3)), (VF1, T(3)), (VF1, 4.6), (3.4, 4.6)])


if __name__ == "__main__":
    aufputz = "--aufputz" in sys.argv
    lehrbuch = "--lehrbuch" in sys.argv or aufputz
    if lehrbuch:
        (leitungen_auf_putz if aufputz else leitungen_unter_putz)(p)
        LEGENDE = LEGENDE[:6] + [("herd", "", "Herdanschluss"), ("abzweig", "", "Abzweigdose"),
                                 ("leitung", "", "Leitung mit Leiterzahl (einschl. PE)"),
                                 ("putz", "AP" if aufputz else "UP", "Leitung auf Putz" if aufputz else "Leitung unter Putz"),
                                 ("verteiler", "", "Unterverteiler")]
        HINWEISE = HINWEISE.replace("Stromkreise: siehe Übersichtsschaltplan.",
                                    r"X10–X16 Abzweigdosen. Je Stromkreis eine Zuleitung vom Unterverteiler. Stromkreise: siehe Übersichtsschaltplan.\\[1mm]" +
                                    ("Alle Leitungen auf Putz" if aufputz else "Alle Leitungen NYM-J unter Putz, Cu 1,5 mm², F2 und Herd 2,5 mm²") +
                                    " (Putzzeichen, wo Platz ist); Leiterzahl einschließlich Schutzleiter. "
                                    "Steckdosen F2 in der unteren, übrige Leitungen in der oberen Installationszone; "
                                    "Kreuzung ohne Punkt: keine Verbindung.")
    if aufputz:
        HINWEISE = HINWEISE.replace("Installation unter Putz.", "Installation auf Putz.")
    ziel = ZIEL.with_name(ZIEL.name + ("_aufputz" if aufputz else "_lehrbuch" if lehrbuch else ""))
    print(p.bauen(ziel, LEGENDE, HINWEISE, SCHRIFTFELD, lehrbuch=lehrbuch))
