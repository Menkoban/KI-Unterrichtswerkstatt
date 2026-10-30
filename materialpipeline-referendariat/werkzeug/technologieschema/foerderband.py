"""Technologieschema Förderband mit Stern-Dreieck-Antrieb (Fassung 3 der Simulation, Lehrkraft 2026-10-15: A).

Stil wie die Stilreferenz Siegelstation (Baustein 5), Bausteine aus anlage.py. Gezeichnet wird nur, was ruht; Pakete,
Gurt, Trommeln, Taster und Schaltstellung legt die Simulation darüber (LAGE, in cm im Bild).
Die Betriebsmittel entsprechen genau dem Stromlaufplan schaltplan_sterndreieck_a3 (gleiche Kennzeichen).

    python3 werkzeug/technologieschema/foerderband.py
Ausgabe: docs/stilreferenz/technologieschema_foerderband.{tex,pdf,png}
"""
from pathlib import Path

from anlage import Szene, bauen as setzen

HIER = Path(__file__).resolve().parent
REPO = HIER.parents[1]
ZIEL = REPO / "docs" / "stilreferenz" / "technologieschema_foerderband"
BOX = (-1.2, -2.5, 24.8, 8.3)            # Bildausschnitt (cm), fest, damit die Simulation die Lage umrechnen kann
PAKETE_START = (1.2, 4.0, 6.8, 9.6)
LAGE = {}


def szene(beweglich=True):
    """beweglich=False: ohne Pakete und Gurtlinien (die zeichnet die Simulation selbst)."""
    s = Szene(BOX)
    s.boden()
    s.band(beweglich)
    b = s.b
    s.lage["massstab"] = 2.0                       # cm im Bild je m Gurtweg (Band ≈ 6,2 m lang)
    s.lage["anzeige"] = (14.75, 0.45)
    s.lage["paket"] = dict(b=1.1, h=0.75, t=0.9, start=0.4, laenge=11.2, y=b["y"] + 0.12, x=PAKETE_START)
    if beweglich:
        for x in PAKETE_START:
            s.karton(x)
    s.a(r"\draw[-{Stealth[length=3mm]},line width=1pt] (1.4,0.95)--(3.2,0.95) node[midway,below=1pt,font=\scriptsize]{Förderrichtung};")
    s.antrieb()
    s.kabelkanal()
    s.bedienkasten([("-S2", "gruen", "I", 18.0), ("-S1", "rot", "0", 18.7)], "Förderband -M1")
    s.schaltschrank()
    # oben: Sicherungen; Mitte: Schütze und Zeitrelais; unten: Motorschutzrelais und Klemmen
    s.geraet("-F1", 20.1, 4.95, 1.15, 0.75, "3 × 25 A gG")
    s.geraet("-F3", 21.45, 4.95, 0.4, 0.75, "2 A")
    for bmk, x, text in (("-Q1", 20.1, "Netz"), ("-Q2", 20.95, "Stern"), ("-Q3", 21.8, "Dreieck")):
        s.geraet(bmk, x, 3.1, 0.75, 0.95, text)
    s.geraet("-K1", 22.7, 3.1, 0.55, 0.95, "10 s")
    s.a(r"\draw[kf,fill=white] (22.97,3.62) circle (0.13); \draw[line width=0.6pt] (22.97,3.62) -- ++(60:0.11);")
    s.geraet("-F2", 20.1, 1.5, 0.75, 0.75, "8,5 A")
    s.klemmen_und_zufuehrung()
    x0, x1, ym = b["x0"], b["x1"], b["y"] - b["h"] / 2
    for z, ziel, text in (
            ((4.6, 0.85), (4.6, 1.9), "Förderband (Gurt)"),
            ((-0.3, 3.0), (x0, ym), "Umlenktrommel"),
            ((11.2, 0.85), (x1 - 0.12, ym - 0.1), "Antriebstrommel"),
            ((13.0, 3.5), (13.8, 2.3), "Stirnradgetriebe"),
            ((14.6, 4.0), (15.0, 2.15), "Drehstrommotor -M1, 7,5 kW, 400 V $\\Delta$"),
            ((16.2, 3.6), (15.45, 2.75), "Klemmenkasten (6 Anschlüsse + PE)"),
            ((17.0, 4.8), (17.62, 3.3), "Bedienkasten mit -S2 Ein, -S1 Aus"),
            ((18.9, 1.0), (19.25, 0.33), "Motorleitung und Steuerleitung im Kabelkanal"),
            ((24.25, 4.6), (23.3, 4.0), "Schaltschrank +SC1 (Schütze, Zeitrelais, Schutzgeräte)"),
            ((8.3, 4.3), (7.6, 3.5), "Paket (Fördergut)")):
        s.nummer(z, ziel, text)
    s.beschriften("Brinkmann Automation, Versand: Förderband mit Stern-Dreieck-Anlauf")
    LAGE.clear()
    LAGE.update(s.lage)
    return s


def tex(beweglich=True):
    return szene(beweglich).tex()


def bauen(ZIEL=ZIEL, beweglich=True):
    return setzen(tex(beweglich), ZIEL)


if __name__ == "__main__":
    print(bauen().with_suffix(".png"))
