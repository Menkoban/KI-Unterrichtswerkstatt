"""Technologieschema Pendelförderband mit Wendeschützschaltung und Endschaltern (Lehrkraft 2026-10-15: A).

Eine Kiste fährt auf dem Gurt nach rechts bis zur Endlage rechts (-B1) und nach links bis zur Endlage links (-B2).
Die Endschalter (Rollenhebel) stehen hinter dem Gurt; ihr Hebel ragt in die Bahn der Kiste. Bausteine aus
anlage.py; Kiste, Gurt, Trommeln, Hebel, Taster und Schaltstellung legt die Simulation darüber.
Die Betriebsmittel entsprechen genau dem Stromlaufplan schaltplan_wendeschuetz_a3 (gleiche Kennzeichen).

    python3 werkzeug/technologieschema/pendelband.py
Ausgabe: docs/stilreferenz/technologieschema_pendelband.{tex,pdf,png}
"""
import math
from pathlib import Path

from anlage import DX, DY, Szene, bauen as setzen, f

HIER = Path(__file__).resolve().parent
REPO = HIER.parents[1]
ZIEL = REPO / "docs" / "stilreferenz" / "technologieschema_pendelband"
BOX = (-1.2, -2.5, 24.8, 8.3)
LAGE = {}
KISTE = dict(b=1.3, h=0.85, t=0.9, start=5.6)
HEBEL = dict(r=0.1, tiefe=0.6, hoehe=0.45)   # Rollenradius; Rolle in Gurttiefe 0,6 und 0,45 über dem Gurt (Mitte Kiste)


def endschalter(s, bmk, x_r, seite):
    """Rollenhebel-Endschalter auf einer Säule an der Hinterkante des Gurts, Hebel nach vorn in die Bahn der Kiste.
    x_r: x der Rolle in der Vorderebene; seite = +1 Endlage rechts (Kiste kommt von links), -1 Endlage links.
    Rückgabe: Drehpunkt und Rollenmitte (Bildkoordinaten) und x der Kistenflanke, bei der die Rolle berührt."""
    b, r = s.b, HEBEL["r"]
    rolle = (x_r + HEBEL["tiefe"] * DX, b["y"] + HEBEL["tiefe"] * DY + HEBEL["hoehe"])
    dreh = (rolle[0] + 0.3 * seite, rolle[1] + 0.8)
    yf = b["y"] + b["tiefe"] * DY                                      # Hinterkante des Gurts
    xf = dreh[0]
    s.a(rf"\quader{{{f(xf - 0.06)}}}{{{f(yf)}}}{{0.12}}{{{f(dreh[1] - yf)}}}{{0.15}}{{stahl}}")
    s.a(rf"\quader{{{f(xf - 0.28)}}}{{{f(dreh[1])}}}{{0.56}}{{0.6}}{{0.3}}{{ral}}")
    s.a(rf"\node[bmk,anchor=south] at ({f(xf)},{f(dreh[1] + 0.67)}) {{{bmk}}};")
    return dict(dreh=[round(v, 3) for v in dreh], rolle=[round(v, 3) for v in rolle], seite=seite,
                kontakt=round(x_r - seite * r, 3))


def hebel_tikz(e):
    (xd, yd), (xr, yr) = e["dreh"], e["rolle"]
    return (rf"\draw[line width=1.4pt,stahld!60!black] ({f(xd)},{f(yd)}) -- ({f(xr)},{f(yr)});"
            rf"\draw[k,fill=black!70] ({f(xr)},{f(yr)}) circle ({f(HEBEL['r'])});"
            rf"\fill[schraube] ({f(xd)},{f(yd)}) circle (0.05);")


def szene(beweglich=True):
    s = Szene(BOX, praeambel=r"\usepackage{amssymb}" + "\n")
    s.boden()
    s.band(beweglich)
    b = s.b
    s.lage["massstab"] = 2.0
    s.lage["kiste"] = dict(KISTE, y=b["y"] + 0.12)
    s.lage["hebel"] = HEBEL
    # Endschalter hinter dem Gurt: Rolle in der Bahn der Kiste
    s.lage["endschalter"] = {"-B2": endschalter(s, "-B2", 1.6, -1), "-B1": endschalter(s, "-B1", 11.6, +1)}
    if beweglich:
        s.karton(KISTE["start"], KISTE["b"], KISTE["h"], KISTE["t"])
        for e in s.lage["endschalter"].values():
            s.a(hebel_tikz(e))
    s.a(r"\draw[{Stealth[length=3mm]}-{Stealth[length=3mm]},line width=1pt] (1.4,0.95)--(3.6,0.95) node[midway,below=1pt,font=\scriptsize]{rechts / links};")
    s.antrieb()
    s.kabelkanal()
    s.bedienkasten([("-S2", "gruen", r"$\blacktriangleright$", 17.85), ("-S3", "gruen", r"$\blacktriangleleft$", 18.45),
                    ("-S1", "rot", "0", 19.05)], "Pendelband -M1", x0=17.5, breite=1.85)
    s.schaltschrank()
    s.geraet("-F1", 20.1, 4.95, 1.15, 0.75, "3 × 16 A gG")
    s.geraet("-F3", 21.45, 4.95, 0.4, 0.75, "2 A")
    s.geraet("-Q1", 20.1, 3.1, 0.75, 0.95, "Rechtslauf")
    s.geraet("-Q2", 20.95, 3.1, 0.75, 0.95, "Linkslauf")
    s.geraet("-F2", 20.1, 1.5, 0.75, 0.75, "3,3 A")
    s.klemmen_und_zufuehrung()
    x0, x1, ym = b["x0"], b["x1"], b["y"] - b["h"] / 2
    for z, ziel, text in (
            ((4.0, 0.85), (4.0, 1.9), "Förderband (Gurt)"),
            ((-0.3, 3.0), (x0, ym), "Umlenktrommel"),
            ((11.2, 0.85), (x1 - 0.12, ym - 0.1), "Antriebstrommel"),
            ((13.0, 3.5), (13.8, 2.3), "Stirnradgetriebe"),
            ((14.6, 4.0), (15.0, 2.15), "Drehstrommotor -M1, 1,5 kW, 400 V"),
            ((16.2, 3.6), (15.45, 2.75), "Klemmenkasten (U1, V1, W1, PE)"),
            ((16.9, 4.8), (17.52, 3.3), "Bedienkasten: -S2 Rechts, -S3 Links, -S1 Aus"),
            ((13.1, 5.2), (12.15, 4.0), "Endschalter -B1 (Endlage rechts)"),
            ((0.4, 5.2), (1.6, 4.0), "Endschalter -B2 (Endlage links)"),
            ((18.9, 1.0), (19.25, 0.33), "Motor- und Steuerleitung im Kabelkanal"),
            ((24.25, 4.6), (23.3, 4.0), "Schaltschrank +SC1 (Wendeschütze, Schutzgeräte)"),
            ((7.6, 5.0), (6.9, 3.6), "Kiste (Fördergut)")):
        s.nummer(z, ziel, text)
    s.beschriften("Brinkmann Automation, Versand: Pendelförderband mit Wendeschützschaltung und Endschaltern")
    LAGE.clear()
    LAGE.update(s.lage)
    return s


def tex(beweglich=True):
    return szene(beweglich).tex()


def bauen(ZIEL=ZIEL, beweglich=True):
    return setzen(tex(beweglich), ZIEL)


if __name__ == "__main__":
    print(bauen().with_suffix(".png"))
