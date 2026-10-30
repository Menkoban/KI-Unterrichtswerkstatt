"""Installationsplan im Grundriss (DIN EN 60617-11), Maßstab 1:50 auf A3.

Alle Maße sind gemessen, nicht geschätzt: docs/recherche/2026-10-14_installationsplaene.md (P1 Planungsbüro,
P3 Lehrbuch). Zeichen kommen 1:1 aus der Bibliothek (werkzeug/schaltzeichen/qet/symbole.tex), proportional auf
Schalterkreis Ø 3,77 mm vergrößert (P1); Strichstärke der Elektrozeichen 0,25 mm (P1).

Regeln (Installationsplan-Checkliste, docs/regeln/installationsplan_checkliste.md):
- Grundriss grau (Wände 0,38 mm mittelgrau, gefüllt; Ausbau 0,25 mm hellgrau), Elektro rot, Texte schwarz.
- Steckdose: Anschlussstrich senkrecht zur Wand, endet an der Wandinnenseite, Halbkreis öffnet zum Raum.
- Schalter: Kreis frei im Raum, Rand 3 mm von der Wand, Hebel zeigt von der Wand weg.
- Industrie (Standard): keine Leitungen, Stromkreisbezeichnung an jedem Gerät; Lehrbuch: Leitungen mit Leiterzahl.

Koordinaten des Grundrisses in Metern (Rohbau-Innenmaße), Zeichnung in mm auf dem Blatt.
"""
from __future__ import annotations

import math
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

HIER = Path(__file__).resolve().parent
SYMBOLE = HIER.parent / "schaltzeichen" / "qet" / "symbole.tex"

M = 1000 / 50                 # 1:50 → 20 mm je Meter
QET = 11.31                   # mm je Bibliothekseinheit: Kreis 0,333 → Ø 3,77 mm (P1)
LW_ELEKTRO = 0.25             # mm (P1)
R_DOSE = 1.5                  # mm Abzweigdose (P3: Ø 3,0 mm)
STRICH_GRUNDRISS = 2.4        # mm Leiterzahl-Strich im Grundriss (kürzer als 3,77 mm im Übersichtsschaltplan P3,
                              # damit er in Leitungsbündeln mit 5 cm Spurabstand keine Nachbarleitung schneidet)
LW_WAND = 0.38                # mm (P1)
LW_AUSBAU = 0.25              # mm (P1)
ABSTAND_SCHALTER = 3.0        # mm Kreisrand bis Wand (P1)
R_SCHALTER = 0.1667 * QET     # 1,885 mm
SCHRIFT = 2.4                 # mm Versalhöhe Stromkreis (P1: 3,0 mm auf A0; auf A3 verkleinert, siehe Checkliste)

# Gestalt nach Bibliothek (11-13-04, 11-14-01/05/06/07, 11-15-03), Proportionen nach P1 gemessen (wie planzeichen.sty
# beim Stromlaufplan): Die Bibliothek hat Hebel 1,5 × Kreis unter 60°, die Hebel ragten dann in die Wand.
HEBEL = 4.46                  # mm ab Kreisrand (P1)
HEBEL_WINKEL = 45             # Grad (P1)
HAKEN = 2.10                  # mm, rechtwinklig zum Hebel, nach außen (Bibliothek: gleiche Seite)
SD_STRICH = 2.33              # mm Anschlussstrich Steckdose (P1)
SD_QUER = 3.73                # mm Querstrich Schutzkontakt (P1); zweifach 7,49 mm
SD_R = 3.77 / 2               # mm Halbkreis (P1)
LEUCHTE_R = 3.6 / 2           # mm Leuchtenauslass als Kreuz 3,6 × 3,6 mm (P1; Lehrbuch P3 und RWE ebenfalls Kreuz)
HEBEL_JE_ART = {"aus": (45,), "serie": (45, 135), "wechsel": (45, 225), "kreuz": (45, 135, 225, 315)}


def _putz_abschnitt(ab, mindest=0.35):
    """Letzter Abschnitt (vom Leitungsende her), der lang genug für das Putzzeichen ist."""
    for i in range(len(ab) - 1, -1, -1):
        if math.dist(*ab[i]) >= mindest:
            return i
    return max(range(len(ab)), key=lambda j: math.dist(*ab[j]))


def _schneiden(p1, p2, p3, p4) -> bool:
    def kreuz(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    d1, d2 = kreuz(p3, p4, p1), kreuz(p3, p4, p2)
    d3, d4 = kreuz(p1, p2, p3), kreuz(p1, p2, p4)
    return (d1 * d2 < 0) and (d3 * d4 < 0)


def _abstand(a, b, p1, p2) -> float:
    """Kleinster Abstand der Endpunkte des Strichs zur Strecke a–b (m)."""
    def punkt(p, a, b):
        ax, ay = a; bx, by = b
        l2 = (bx - ax) ** 2 + (by - ay) ** 2
        t = 0 if l2 == 0 else max(0, min(1, ((p[0] - ax) * (bx - ax) + (p[1] - ay) * (by - ay)) / l2))
        return math.dist(p, (ax + t * (bx - ax), ay + t * (by - ay)))
    return min(punkt(p1, a, b), punkt(p2, a, b))


def anker_zu(dx, dy) -> str:
    """Anker eines Textknotens, der um (dx, dy) vom Zeichen versetzt steht (zeigt zurück zum Zeichen)."""
    w = math.degrees(math.atan2(dy, dx)) % 360
    namen = ["west", "south west", "south", "south east", "east", "north east", "north", "north west"]
    return namen[int(((w + 22.5) % 360) // 45)]


def schalter_tikz(typ: str, dreh: float = 0) -> str:
    """Schalter, Kreismitte im Ursprung, Wand unten (Hebel zeigen nach oben vom Raum aus gesehen weg von der Wand).
    dreh: Drehung, mit der das Zeichen auf dem Blatt steht. Die Haken zeigen in Blattlage immer waagerecht nach
    außen (obere Haken nach außen-unten, untere nach außen-oben), wie Bibliothek 11-14-07 (EN 60617-11), Europa
    32690-3 S. 15/18, etz Stuttgart und Elektricks; ein gedrehter Kreuzschalter sieht damit aus wie in der Norm
    (Korrektur der Lehrkraft 2026-10-14)."""
    teile = [f"\\draw[fill=white] (0,0) circle ({R_SCHALTER:.3f});"]
    if typ == "taster":
        return teile[0] + f"\\draw (0,0) circle ({R_SCHALTER / 2:.3f});"
    for w in HEBEL_JE_ART[typ]:
        a = math.radians(w)
        x0, y0 = R_SCHALTER * math.cos(a), R_SCHALTER * math.sin(a)
        x1, y1 = (R_SCHALTER + HEBEL) * math.cos(a), (R_SCHALTER + HEBEL) * math.sin(a)
        # Haken zeigt in Blattlage waagerecht nach außen (wie in der Bibliothek)
        ab = a + math.radians(dreh)
        h = a - math.pi / 2 if math.cos(ab - math.pi / 2) * math.cos(ab) > 0 else a + math.pi / 2
        x2, y2 = x1 + HAKEN * math.cos(h), y1 + HAKEN * math.sin(h)
        teile.append(f"\\draw ({x0:.3f},{y0:.3f}) -- ({x1:.3f},{y1:.3f}) -- ({x2:.3f},{y2:.3f});")
    return "".join(teile)


def steckdose_tikz(anzahl=1) -> str:
    """Schutzkontaktsteckdose, Anschluss an der Wand im Ursprung, Wand oben, Halbkreis öffnet zum Raum.
    Mehrfachsteckdose (Bibliothek 11-13-02, Lehrbuch P3): dasselbe Zeichen mit Schrägstrich und Anzahl."""
    t = [f"\\draw (0,0) -- (0,{-SD_STRICH:.3f}) ({-SD_QUER / 2:.3f},{-SD_STRICH:.3f}) -- ({SD_QUER / 2:.3f},{-SD_STRICH:.3f});",
         f"\\draw ({SD_R:.3f},{-SD_STRICH - SD_R:.3f}) arc[start angle=0,end angle=180,radius={SD_R:.3f}];"]
    if anzahl > 1:
        # Schrägstrich durch den Halbkreis nahe der Spitze, zum Raum geneigt (Lehrbuch P3); Länge wie Bibliothek
        x0, y0 = schraeg_mehrfach()
        t.append(f"\\draw ({x0[0]:.3f},{x0[1]:.3f}) -- ({y0[0]:.3f},{y0[1]:.3f});")
    return "".join(t)


def schraeg_mehrfach():
    """Anfang und Ende des Schrägstrichs der Mehrfachsteckdose (Wand oben, Halbkreismitte bei y = −2,33 − r)."""
    mx, my = 0.0, -SD_STRICH - SD_R
    w = math.radians(15)
    px, py = mx + SD_R * math.cos(w), my + SD_R * math.sin(w)       # Schnittpunkt mit dem Halbkreis
    h = 0.236 * 11.31 / 2                                            # Länge 2,67 mm (Bibliothek 11-13-02)
    d = math.radians(-45)
    return (px - h * math.cos(d), py - h * math.sin(d)), (px + h * math.cos(d), py + h * math.sin(d))


HERD = 6.0                    # mm Quadrat Herdanschluss (P1), Punkte Ø 1,48 mm bei 1,5 / 4,5 mm (P1; RWE gleich)
UV_L, UV_T = 7.03, 1.91       # mm Unterverteiler, Rechteck diagonal halb gefüllt (P1)


def herd_tikz() -> str:
    """Herdanschluss (P1, RWE): Quadrat an der Wand (Wand oben), zwei Punkte zur Wand, einer zum Raum."""
    h = HERD
    t = [f"\\draw[fill=white] ({-h / 2:.3f},0) rectangle ({h / 2:.3f},{-h:.3f});"]
    for x, y in ((-1.5, -1.5), (1.5, -1.5), (0, -4.5)):
        t.append(f"\\fill ({x:.3f},{y:.3f}) circle (0.74);")
    return "".join(t)


def verteiler_tikz() -> str:
    """Unterverteiler (P1): Rechteck 7,03 × 1,91 mm an der Wand (Wand oben), Hälfte an der Wand gefüllt."""
    l, d = UV_L / 2, UV_T
    return (f"\\fill ({-l:.3f},{-d:.3f}) -- ({-l:.3f},0) -- ({l:.3f},0) -- cycle;"
            f"\\draw ({-l:.3f},0) rectangle ({l:.3f},{-d:.3f}) ({-l:.3f},{-d:.3f}) -- ({l:.3f},0);")


def leuchte_tikz() -> str:
    """Leuchtenauslass (Bibliothek 11-15-01, ohne Anschlussstrich): Kreuz 3,6 × 3,6 mm (P1)."""
    k = LEUCHTE_R
    return f"\\draw ({-k:.3f},{-k:.3f}) -- ({k:.3f},{k:.3f}) ({-k:.3f},{k:.3f}) -- ({k:.3f},{-k:.3f});"


# Lage des Geräts zur Wand: Wand liegt "oben", "unten", "links" oder "rechts" vom Gerät
NORMALE = {"oben": (0, 1), "unten": (0, -1), "links": (-1, 0), "rechts": (1, 0)}
# Drehung der Bibliothekszeichen: Steckdose zeigt in der Bibliothek mit dem Anschluss nach oben,
# Schalterhebel nach rechts oben (zeigt also von einer Wand unten weg)
DREH_STECKDOSE = {"oben": 0, "unten": 180, "links": 90, "rechts": -90}
DREH_SCHALTER = {"unten": 0, "oben": 180, "links": -90, "rechts": 90}

SCHALTER = {"aus": "11-14-01", "serie": "11-14-05", "wechsel": "11-14-06", "kreuz": "11-14-07", "taster": "11-14-10"}
STECKDOSE = "11-13-04"        # Schutzkontaktsteckdose
LEUCHTE = "11-15-03"
DOSE = "11-12-05"             # Anschlussdose (Geräteanschluss, z. B. Herd)
VERTEILER = "11-12-07"


def bibliothek(nummern) -> str:
    """Bibliotheksmakros der benötigten Zeichen, Strichstärke und Farbe für den Plan gesetzt (nicht von Hand)."""
    text = SYMBOLE.read_text(encoding="utf-8")
    teile = []
    for nr in sorted(set(nummern)):
        m = re.search(rf"\\expandafter\\def\\csname szQ@{re.escape(nr)}\\endcsname\{{%\n(.*?)\n\}}", text, re.S)
        if not m:
            raise KeyError(f"Zeichen {nr} fehlt in der Bibliothek")
        rumpf = m.group(1).replace("line width=0.8pt", "line width=\\elLW").replace(",fill=black", ",fill")
        teile.append(f"\\expandafter\\def\\csname el@{nr}\\endcsname{{%\n{rumpf}\n}}")
    return "\n".join(teile)


@dataclass
class Geraet:
    art: str                  # steckdose | steckdose2 | schalter | leuchte | dose | verteiler
    x: float                  # m, Punkt an der Wandinnenseite (Wandgeräte) bzw. Lage (Deckenleuchte)
    y: float
    wand: str = ""
    typ: str = ""             # Schalterart oder Zeichennummer
    stromkreis: str = ""      # z. B. "F2"
    kenn: str = ""            # Kennbuchstaben (A, KS, GS …) oder Zuordnung Schalter–Leuchte (a, b …)
    text_seite: int = 1       # Schalter: +1 links oberhalb, −1 rechts daneben
    text_lage: tuple | None = None   # (dx, dy) in mm vom Zeichenmittelpunkt, überschreibt die Regel
    vor: float = 0.0          # m vor der Wand (Lehrbuch: Gerät sitzt auf seiner Leitung, Fachkunde S. 102)


@dataclass
class Plan:
    titel: str
    ox: float = 75.0          # mm, Lage des Nullpunkts auf dem Blatt
    oy: float = 85.0
    waende: list = field(default_factory=list)       # (x0, y0, x1, y1) in m
    oeffnungen: list = field(default_factory=list)   # (art, x0, y0, x1, y1, anschlag)
    raeume: list = field(default_factory=list)       # (name, x0, y0, x1, y1)
    geraete: list = field(default_factory=list)
    leitungen: list = field(default_factory=list)    # Lehrbuch: (punkte in m, leiterzahl, beschriftung)
    putz: list = field(default_factory=list)         # Verlegeart je Leitung: (punkte, "AP"/"IP"/"UP", abschnitt)
    tikz: list = field(default_factory=list)
    nummern: list = field(default_factory=list)

    # ---------- Umrechnung ----------
    def p(self, x, y):
        return self.ox + x * M, self.oy + y * M

    def c(self, x, y):
        a, b = self.p(x, y)
        return f"({a:.2f},{b:.2f})"

    # ---------- Grundriss ----------
    def wand(self, x0, y0, x1, y1):
        self.waende.append((x0, y0, x1, y1))

    def tuer(self, x0, y0, x1, y1, angel, aufschlag):
        """Türöffnung im Wandstück (x0..x1, y0..y1); angel = Ecke des Bands (x, y) an der Raumseite,
        aufschlag = Richtung, in die das Blatt aufgeht ("oben", "unten", "links", "rechts")."""
        self.oeffnungen.append(("tuer", x0, y0, x1, y1, (angel, aufschlag)))

    def fenster(self, x0, y0, x1, y1):
        self.oeffnungen.append(("fenster", x0, y0, x1, y1, None))

    def raum(self, name, x0, y0, x1, y1, lage=None):
        """Raumstempel (Name, Fläche); lage = (x, y) in m, sonst unter der Raummitte."""
        self.raeume.append((name, x0, y0, x1, y1, lage))

    def geraet(self, *a, **k):
        g = Geraet(*a, **k)
        self.geraete.append(g)
        return g

    def leitung(self, punkte, leiterzahl=3, strich=None, pos=0.5, ziffer=0, putz=None, putz_abschnitt=None):
        """Leitung als Linienzug (m). Leiterzahl einschließlich PE; strich = Index des Abschnitts für den
        Leiterzahl-Strich (sonst der längste)."""
        self.leitungen.append((punkte, leiterzahl, strich, pos, ziffer))
        if putz:
            self.putz.append((punkte, putz, putz_abschnitt))

    # ---------- Zeichnen ----------
    def _grundriss(self):
        t = self.tikz
        for x0, y0, x1, y1 in self.waende:
            t.append(f"\\fill[wandfuell] {self.c(x0, y0)} rectangle {self.c(x1, y1)};")
        for art, x0, y0, x1, y1, z in self.oeffnungen:
            t.append(f"\\fill[white] {self.c(x0, y0)} rectangle {self.c(x1, y1)};")
        # Wandkanten: Umriss je Wandstück; über Öffnungen weiß abgedeckt, dann Laibungen gezeichnet
        for x0, y0, x1, y1 in self.waende:
            t.append(f"\\draw[wand] {self.c(x0, y0)} rectangle {self.c(x1, y1)};")
        for art, x0, y0, x1, y1, z in self.oeffnungen:
            senkrecht = (x1 - x0) < (y1 - y0)            # Öffnung in einer senkrechten Wand
            (a0, b0), (a1, b1) = self.p(x0, y0), self.p(x1, y1)
            if senkrecht:
                a0, a1 = a0 - 0.3, a1 + 0.3
            else:
                b0, b1 = b0 - 0.3, b1 + 0.3
            t.append(f"\\fill[white] ({a0:.2f},{b0:.2f}) rectangle ({a1:.2f},{b1:.2f});")
            senkrecht = (x1 - x0) < (y1 - y0)            # Öffnung in einer senkrechten Wand
            if senkrecht:
                t.append(f"\\draw[wand] {self.c(x0, y0)} -- {self.c(x1, y0)} {self.c(x0, y1)} -- {self.c(x1, y1)};")
            else:
                t.append(f"\\draw[wand] {self.c(x0, y0)} -- {self.c(x0, y1)} {self.c(x1, y0)} -- {self.c(x1, y1)};")
            if art == "fenster":
                for f in (0.35, 0.65):
                    if senkrecht:
                        xm = x0 + (x1 - x0) * f
                        t.append(f"\\draw[ausbau] {self.c(xm, y0)} -- {self.c(xm, y1)};")
                    else:
                        ym = y0 + (y1 - y0) * f
                        t.append(f"\\draw[ausbau] {self.c(x0, ym)} -- {self.c(x1, ym)};")
            else:
                (ax, ay), auf = z
                breite = (y1 - y0) if senkrecht else (x1 - x0)
                dx, dy = NORMALE[auf]
                ex, ey = ax + dx * breite, ay + dy * breite
                # Ende des Bogens: anderes Ende der Öffnung auf der Raumseite
                if senkrecht:
                    gx, gy = ax, (y1 if abs(ay - y0) < 1e-6 else y0)
                else:
                    gx, gy = (x1 if abs(ax - x0) < 1e-6 else x0), ay
                t.append(f"\\draw[ausbau] {self.c(ax, ay)} -- {self.c(ex, ey)};")
                r = breite * M
                a0 = math.degrees(math.atan2(ey - ay, ex - ax))
                a1 = math.degrees(math.atan2(gy - ay, gx - ax))
                d = (a1 - a0 + 540) % 360 - 180
                t.append(f"\\draw[ausbau] {self.c(ex, ey)} arc[start angle={a0:.1f},"
                         f"delta angle={d:.1f},radius={r:.2f}];")
        for name, x0, y0, x1, y1, lage in self.raeume:
            fl = (x1 - x0) * (y1 - y0)
            lx, ly = lage or ((x0 + x1) / 2, (y0 + y1) / 2 - 0.7)
            fl_text = f"{fl:.2f}".replace(".", ",")
            t.append(f"\\node[raum] at {self.c(lx, ly)} {{{name}\\\\{fl_text}\\,m²}};")

    def _zeichen(self, nr, px, py, dreh):
        self.nummern.append(nr)
        return (f"\\begin{{scope}}[shift={{({px:.2f},{py:.2f})}},rotate={dreh},x={QET}mm,y={QET}mm]"
                f"\\csname el@{nr}\\endcsname\\end{{scope}}")

    def _geraete(self):
        t = self.tikz
        t.append("\\begin{scope}[elektro]")
        for g in self.geraete:
            px, py = self.p(g.x, g.y)
            if g.vor and g.wand:
                nx, ny = NORMALE[g.wand]
                px, py = px - nx * g.vor * M, py - ny * g.vor * M
            if g.art in ("steckdose", "steckdose2"):
                d = DREH_STECKDOSE[g.wand]
                n = 2 if g.art == "steckdose2" else 1
                t.append(f"\\begin{{scope}}[shift={{({px:.2f},{py:.2f})}},rotate={d},line width={LW_ELEKTRO}mm]"
                         f"{steckdose_tikz(n)}\\end{{scope}}")
                if n > 1:                                  # Anzahl am äußeren Strichende (aufrecht)
                    rad = math.radians(d)
                    (_, _), (ex, ey) = schraeg_mehrfach()
                    ax, ay = ex * math.cos(rad) - ey * math.sin(rad), ex * math.sin(rad) + ey * math.cos(rad)
                    dx, dy = math.cos(rad - math.pi / 4), math.sin(rad - math.pi / 4)
                    t.append(f"\\node[lz,anchor={anker_zu(dx, dy)}] at ({px + ax:.2f},{py + ay:.2f}) {{{n}}};")
                tiefe = SD_STRICH + SD_R
            elif g.art == "schalter":
                nx, ny = NORMALE[g.wand]
                a = ABSTAND_SCHALTER + R_SCHALTER
                cx, cy = px - nx * a, py - ny * a
                d = DREH_SCHALTER[g.wand]
                t.append(f"\\begin{{scope}}[shift={{({cx:.2f},{cy:.2f})}},rotate={d},line width={LW_ELEKTRO}mm]"
                         f"{schalter_tikz(g.typ, d)}\\end{{scope}}")
                tiefe = a + R_SCHALTER
            elif g.art == "dose":
                nx, ny = NORMALE[g.wand]
                a = ABSTAND_SCHALTER + R_SCHALTER
                cx, cy = px - nx * a, py - ny * a
                t.append(f"\\begin{{scope}}[shift={{({cx:.2f},{cy:.2f})}},x={QET}mm,y={QET}mm]"
                         f"\\begin{{scope}}[shift={{(0.1667,-0.1667)}}]\\csname el@{DOSE}\\endcsname"
                         "\\end{scope}\\end{scope}")
                self.nummern.append(DOSE)
                tiefe = a + R_SCHALTER
            elif g.art == "abzweig":
                # Abzweigdose als leerer Kreis Ø 3,0 mm (Fachkunde S. 102, Europa-Aufgabensammlung; P3 gemessen)
                t.append(f"\\draw[fill=white,line width={LW_ELEKTRO}mm] ({px:.2f},{py:.2f}) circle ({R_DOSE:.3f});")
                tiefe = 0
            elif g.art == "leuchte":
                t.append(f"\\begin{{scope}}[shift={{({px:.2f},{py:.2f})}},line width={LW_ELEKTRO}mm]"
                         f"{leuchte_tikz()}\\end{{scope}}")
                tiefe = 0
            elif g.art == "verteiler":
                d = DREH_STECKDOSE[g.wand]
                t.append(f"\\begin{{scope}}[shift={{({px:.2f},{py:.2f})}},rotate={d},line width={LW_ELEKTRO}mm]"
                         f"{verteiler_tikz()}\\end{{scope}}")
                tiefe = UV_T
            elif g.art == "herd":
                d = DREH_STECKDOSE[g.wand]
                t.append(f"\\begin{{scope}}[shift={{({px:.2f},{py:.2f})}},rotate={d},line width={LW_ELEKTRO}mm]"
                         f"{herd_tikz()}\\end{{scope}}")
                tiefe = HERD
            self._beschriftung(g, px, py, tiefe)
        t.append("\\end{scope}")

    def _beschriftung(self, g, px, py, tiefe):
        """Steckdosen, Dosen, Verteiler: Text vor dem Zeichen zur Raumseite. Schalter: Text neben dem Kreis auf der
        Seite gegenüber dem Hebel. Leuchten: rechts daneben."""
        text = " ".join(s for s in (g.stromkreis, g.kenn) if s)
        if not text:
            return
        if g.text_lage:
            nx, ny = NORMALE.get(g.wand, (0, 0))
            a = ABSTAND_SCHALTER + R_SCHALTER if g.art in ("schalter", "dose") else 0
            dx, dy = g.text_lage[:2]
            anker = g.text_lage[2] if len(g.text_lage) > 2 else anker_zu(dx, dy)
            self.tikz.append(f"\\node[sk,anchor={anker}] at ({px - nx * a + dx:.2f},"
                             f"{py - ny * a + dy:.2f}) {{{text}}};")
            return
        if g.art in ("leuchte", "abzweig"):
            self.tikz.append(f"\\node[sk,anchor=west] at ({px + LEUCHTE_R + 1.0:.2f},{py:.2f}) {{{text}}};")
            return
        nx, ny = NORMALE[g.wand]
        if g.art == "schalter":
            a = ABSTAND_SCHALTER + R_SCHALTER
            cx, cy = px - nx * a, py - ny * a
            # im Bibliothekszeichen (Wand unten): Text links oberhalb des Kreises, zwischen den Hebeln;
            # beim Kreuzschalter links außerhalb der Haken; text_seite = −1 spiegelt nach rechts unten
            if g.typ == "kreuz":
                lx, ly = -(R_SCHALTER + (HEBEL + HAKEN) * math.cos(math.radians(45)) + 0.6), 0.0
            else:
                lx, ly = -(R_SCHALTER + 0.4), R_SCHALTER + 0.4
            if g.text_seite < 0 and g.typ != "kreuz":   # rechts neben den Kreis, auf Mittenhöhe (frei bei Aus/Wechsel)
                lx, ly = R_SCHALTER + 1.0, -0.3
            elif g.text_seite < 0:
                lx = -lx
            d = math.radians(DREH_SCHALTER[g.wand])
            ux, uy = lx * math.cos(d) - ly * math.sin(d), lx * math.sin(d) + ly * math.cos(d)
            mx, my = cx + ux, cy + uy
            anker = anker_zu(ux, uy)
        else:
            mx, my = px - nx * (tiefe + 0.8), py - ny * (tiefe + 0.8)
            if g.art == "steckdose2":                  # Platz für die Anzahl rechts neben dem Halbkreis
                d = math.radians(DREH_STECKDOSE[g.wand])
                mx, my = mx - 2.5 * math.cos(d), my - 2.5 * math.sin(d)
            anker = {(0, 1): "north", (0, -1): "south", (-1, 0): "west", (1, 0): "east"}[(nx, ny)]
        self.tikz.append(f"\\node[sk,anchor={anker}] at ({mx:.2f},{my:.2f}) {{{text}}};")

    def _geraetepunkte(self):
        """Mittelpunkte der Geräte in m (für das Freihalten von Leiterzahl und Putzzeichen)."""
        tiefe = {"schalter": 0.244, "dose": 0.244, "steckdose": 0.15, "steckdose2": 0.15, "herd": 0.15,
                 "verteiler": 0.05}
        pkt = []
        for g in self.geraete:
            if g.wand:
                nx, ny = NORMALE[g.wand]
                d = g.vor + tiefe.get(g.art, 0)
                pkt.append((g.x - nx * d, g.y - ny * d))
            else:
                pkt.append((g.x, g.y))
        return pkt

    def _platz(self, punkte, seitlich, marken, geraete, abstand_geraet=0.28, abstand_marke=0.22, raumseite=None):
        """Freie Lage (Abschnitt, Anteil) für ein Zeichen auf der Leitung, vom Leitungsende her gesucht."""
        andere = [seg for pk, *_ in self.leitungen if pk is not punkte for seg in zip(pk, pk[1:])]
        ab = list(zip(punkte, punkte[1:]))
        for i in range(len(ab) - 1, -1, -1):
            (xa, ya), (xb, yb) = ab[i]
            if math.dist((xa, ya), (xb, yb)) < 0.4:
                continue
            for pos in (0.5, 0.35, 0.65, 0.25, 0.75, 0.15, 0.85):
                c = (xa + (xb - xa) * pos, ya + (yb - ya) * pos)
                if any(math.dist(c, q) < abstand_geraet for q in geraete):
                    continue
                if any(math.dist(c, q) < abstand_marke for q in marken):
                    continue
                if raumseite is None:
                    if any(_abstand(a, b, c, c) < seitlich for a, b in andere):
                        continue
                else:                                         # Schraffur liegt raumseitig: nur dort frei halten
                    l = math.dist((xa, ya), (xb, yb))
                    nx, ny = -(yb - ya) / l, (xb - xa) / l
                    if self._raumseite(c, nx, ny) < 0:
                        nx, ny = -nx, -ny
                    probe = [(c[0] + nx * raumseite * f + (xb - xa) / l * d, c[1] + ny * raumseite * f + (yb - ya) / l * d)
                             for f in (0.4, 0.8, 1.0) for d in (-0.07, 0, 0.07)]
                    if any(_abstand(a, b, q, q) < 0.02 for a, b in andere for q in probe):
                        continue
                return i, pos
        return None

    def _leitungen(self):
        t = self.tikz
        geraete = self._geraetepunkte()
        marken = []
        putz = {id(pk): art for pk, art, _ in self.putz}
        for punkte, n, strich, pos, ziffer in self.leitungen:
            pfad = " -- ".join(self.c(x, y) for x, y in punkte)
            t.append(f"\\draw[elektro,line width={LW_ELEKTRO}mm] {pfad};")
            abschnitte = list(zip(punkte, punkte[1:]))
            # Putzzeichen (Verlegeart) einmal je Leitung
            if id(punkte) in putz:
                lage = self._platz(punkte, 0.07, marken, geraete, raumseite=0.11)
                if lage:
                    i, ps = lage
                    (xa, ya), (xb, yb) = abschnitte[i]
                    c = (xa + (xb - xa) * ps, ya + (yb - ya) * ps)
                    marken.append(c)
                    self._putzzeichen_bei(abschnitte[i], ps, putz[id(punkte)])
            if n is None:
                continue
            # Leiterzahl: schräger Strich 2,4 mm unter 36° zur Leitung mit Ziffer
            if strich is None:
                lage = self._platz(punkte, 0.045, marken, geraete)
                strich, pos = lage if lage else (max(range(len(abschnitte)), key=lambda j: math.dist(*abschnitte[j])), 0.5)
            (xa, ya), (xb, yb) = abschnitte[strich]
            marken.append((xa + (xb - xa) * pos, ya + (yb - ya) * pos))
            mx, my = self.p(xa + (xb - xa) * pos, ya + (yb - ya) * pos)
            w = math.atan2(yb - ya, xb - xa) + math.radians(36)
            if math.cos(w) < -1e-6 or (abs(math.cos(w)) < 1e-6 and math.sin(w) < 0):
                w += math.pi                                  # Ziffer immer rechts oben am Strich
            h = STRICH_GRUNDRISS / 2
            if ziffer == 0:
                ziffer = self._ziffer_seite(punkte, xa + (xb - xa) * pos, ya + (yb - ya) * pos, w)
            t.append(f"\\draw[elektro,line width={LW_ELEKTRO}mm] ({mx - h * math.cos(w):.2f},{my - h * math.sin(w):.2f})"
                     f" -- ({mx + h * math.cos(w):.2f},{my + h * math.sin(w):.2f});")
            ex, ey = mx + ziffer * h * math.cos(w), my + ziffer * h * math.sin(w)
            t.append(f"\\node[lz,anchor={anker_zu(ziffer * math.cos(w), ziffer * math.sin(w))}] at ({ex:.2f},{ey:.2f}) {{{n}}};")

    def _raumseite(self, c, nx, ny):
        """+1, wenn (nx, ny) von Punkt c zur Raumseite zeigt (erste Seite, die aus der Wand herausführt), sonst −1."""
        for d in (0.1, 0.2, 0.3, 0.4):
            a = self._wandabstand(c[0] + nx * d, c[1] + ny * d)
            b = self._wandabstand(c[0] - nx * d, c[1] - ny * d)
            if a != b:
                return 1 if a > b else -1
        return 1

    def _wandabstand(self, x, y):
        """Abstand eines Punktes (m) zur nächsten Wand (0 innerhalb einer Wand)."""
        best = 9.9
        for x0, y0, x1, y1 in self.waende:
            dx = max(x0 - x, 0, x - x1)
            dy = max(y0 - y, 0, y - y1)
            best = min(best, math.hypot(dx, dy))
        return best

    def _putzzeichen_bei(self, segment, pos, art):
        """Putzzeichen (Fachkunde S. 681, etz S. 1): drei Schrägstriche mit Deckstrich. Unter Putz: Schraffur zur
        Raumseite der Leitung (Putz liegt zwischen Leitung und Raum); auf Putz: zur Wandseite; im Putz: Leitung
        mittig durch die Schraffur."""
        t = self.tikz
        if True:
            (xa, ya), (xb, yb) = segment
            l = math.dist((xa, ya), (xb, yb))
            ux, uy = (xb - xa) / l, (yb - ya) / l
            nx, ny = -uy, ux
            mx, my = xa + (xb - xa) * pos, ya + (yb - ya) * pos
            raum = self._raumseite((mx, my), nx, ny)
            seite = {"UP": raum, "AP": -raum, "IP": raum}[art]
            nx, ny = nx * seite, ny * seite
            cx, cy = self.p(mx, my)
            a0 = {"UP": 0.35, "AP": 0.35, "IP": -0.6}[art]       # mm Abstand Schraffur ↔ Leitung
            hoehe, breite = 1.2, 2.4
            teile = []
            for k in (-0.8, 0.0, 0.8):
                bx, by = cx + ux * k, cy + uy * k
                x0, y0 = bx + nx * a0 - ux * 0.35, by + ny * a0 - uy * 0.35
                x1, y1 = bx + nx * (a0 + hoehe) + ux * 0.35, by + ny * (a0 + hoehe) + uy * 0.35
                teile.append(f"({x0:.2f},{y0:.2f}) -- ({x1:.2f},{y1:.2f})")
            dx0, dy0 = cx - ux * breite / 2 + nx * (a0 + hoehe), cy - uy * breite / 2 + ny * (a0 + hoehe)
            dx1, dy1 = cx + ux * breite / 2 + nx * (a0 + hoehe), cy + uy * breite / 2 + ny * (a0 + hoehe)
            teile.append(f"({dx0:.2f},{dy0:.2f}) -- ({dx1:.2f},{dy1:.2f})")
            t.append(f"\\draw[elektro,line width={LW_ELEKTRO}mm] " + " ".join(teile) + ";")

    def _freie_strichlage(self, punkte, n):
        """Sucht einen Abschnitt und eine Lage, an der der Leiterzahl-Strich keine andere Leitung schneidet."""
        h = STRICH_GRUNDRISS / 2 / M                         # halbe Strichlänge in m
        andere = [seg for pk, *_ in self.leitungen if pk is not punkte for seg in zip(pk, pk[1:])]
        # Putzzeichen derselben Leitung freihalten (liegt bei 30 % des längsten Abschnitts)
        for pk, _, idx in self.putz:
            if pk is punkte:
                ab = list(zip(pk, pk[1:]))
                i = idx if idx is not None else _putz_abschnitt(ab)
                (xa, ya), (xb, yb) = ab[i]
                cx, cy = xa + (xb - xa) * 0.3, ya + (yb - ya) * 0.3
                andere.append(((cx - 0.08, cy - 0.08), (cx + 0.08, cy + 0.08)))
                andere.append(((cx - 0.08, cy + 0.08), (cx + 0.08, cy - 0.08)))
        abschnitte = list(zip(punkte, punkte[1:]))
        reihenfolge = list(range(len(abschnitte) - 1, -1, -1))      # vom Leitungsende her (dort läuft sie allein)
        for i in reihenfolge:
            (xa, ya), (xb, yb) = abschnitte[i]
            if math.dist((xa, ya), (xb, yb)) < 2.2 * h:
                continue
            w = math.atan2(yb - ya, xb - xa) + math.radians(36)
            for pos in (0.5, 0.35, 0.65, 0.25, 0.75, 0.15, 0.85):
                mx, my = xa + (xb - xa) * pos, ya + (yb - ya) * pos
                p1 = (mx - h * math.cos(w), my - h * math.sin(w))
                p2 = (mx + h * math.cos(w), my + h * math.sin(w))
                if not any(_schneiden(p1, p2, a, b) or _abstand(a, b, p1, p2) < 0.012 for a, b in andere):
                    z = self._ziffer_seite(punkte, mx, my, w, pruefen=True)
                    if z:
                        return i, pos
        return reihenfolge[0], 0.5

    def _ziffer_seite(self, punkte, mx, my, w, pruefen=False):
        """+1/−1: an welchem Strichende die Ziffer frei steht (Abstand zu anderen Leitungen); 0 wenn keines."""
        h = STRICH_GRUNDRISS / 2 / M
        andere = [seg for pk, *_ in self.leitungen if pk is not punkte for seg in zip(pk, pk[1:])]
        beste, abst = 0, 0.0
        for z in (1, -1):
            zx, zy = mx + z * (h + 0.05) * math.cos(w), my + z * (h + 0.05) * math.sin(w)
            d = min((_abstand(a, b, (zx, zy), (zx, zy)) for a, b in andere), default=1)
            if d > abst:
                beste, abst = z, d
        if pruefen:
            return beste if abst > 0.05 else 0
        return beste or 1

    # ---------- Blatt ----------
    def blatt(self, legende, hinweise, schriftfeld, lehrbuch=False):
        self.tikz = []
        self._grundriss()
        if lehrbuch:
            self._leitungen()
        self._geraete()
        plan = "\n".join(self.tikz)
        rand = []
        # A3 quer, Rahmen: Heftrand 20 mm links, sonst 5 mm (P1)
        rand.append("\\draw[rahmen] (20,5) rectangle (415,292);")
        sx = 415 - 95
        rand.append(f"\\draw[rahmen] ({sx},5) -- ({sx},292);")
        # Legende: Zeichen in Plangröße links, Text rechts (P1)
        y = 284
        rand.append(f"\\node[kopf,anchor=north west] at ({sx + 4},{y + 4}) {{Legende}};")
        y -= 9
        self.tikz = []
        for eintrag in legende:
            art, typ, text = eintrag
            g = Geraet(art, 0, 0, "unten" if art in ("schalter", "dose") else "oben", typ)
            # Anschlusspunkt so legen, dass das Zeichen mittig auf der Textzeile steht
            if art == "putz":                                 # Putzzeichen wie Fachkunde S. 681
                gesammelt, self.tikz = self.tikz, []
                self.waende_alt, self.waende = self.waende, [(0, -9, 99, -8)]   # Wand „unten“ für die Raumseite
                ox, oy = self.ox, self.oy
                self.ox, self.oy = 0, 0
                self._putzzeichen_bei((((sx + 6) / M, (y - 1.2) / M), ((sx + 18) / M, (y - 1.2) / M)), 0.5, typ)
                self.waende = self.waende_alt
                self.ox, self.oy = ox, oy
                rand.append(f"\\draw[elektro,line width={LW_ELEKTRO}mm] ({sx + 6},{y - 1.2}) -- ({sx + 18},{y - 1.2});")
                rand += self.tikz
                self.tikz = gesammelt
                rand.append(f"\\node[leg,anchor=west] at ({sx + 24},{y}) {{{text}}};")
                y -= 10
                continue
            if art == "leitung":
                rand.append(f"\\draw[elektro,line width={LW_ELEKTRO}mm] ({sx + 6},{y}) -- ({sx + 18},{y}) "
                            f"({sx + 12 - 1.525:.2f},{y - 1.108:.2f}) -- ({sx + 12 + 1.525:.2f},{y + 1.108:.2f});"
                            f"\\node[lz,anchor=south west] at ({sx + 13.6:.2f},{y + 1.0:.2f}) {{3}};")
                rand.append(f"\\node[leg,anchor=west] at ({sx + 24},{y}) {{{text}}};")
                y -= 10
                continue
            dy = {"abzweig": 0, "steckdose": 2.1, "steckdose2": 2.1, "schalter": -4.9, "dose": -4.9, "leuchte": 0,
                  "verteiler": 1.0, "herd": 3.0}[art]
            if typ in ("wechsel", "kreuz"):
                y -= 2
            self.ox, self.oy = sx + 12, y + dy
            self._geraete_einzeln(g)
            rand.append(f"\\node[leg,anchor=west] at ({sx + 24},{y}) {{{text}}};")
            y -= 13 if typ in ("wechsel", "kreuz") or art in ("leuchte", "herd", "steckdose2") else 10
        rand += self.tikz
        y -= 2
        rand.append(f"\\node[kopf,anchor=north west] at ({sx + 4},{y}) {{Hinweise}};")
        rand.append(f"\\node[leg,anchor=north west,text width=86mm,align=left] at ({sx + 4},{y - 6}) "
                    f"{{{hinweise}}};")
        rand.append(self._schriftfeld(sx, schriftfeld))
        return plan, "\n".join(rand)

    def _geraete_einzeln(self, g):
        alt = self.geraete
        self.geraete = [g]
        self._geraete()
        self.geraete = alt

    def _schriftfeld(self, sx, f):
        zeilen = [("Bauherr", f["bauherr"]), ("Bauvorhaben", f["bauvorhaben"]), ("Planinhalt", f["planinhalt"]),
                  ("Fachplanung", f["fachplanung"]), ("Gewerk", f["gewerk"])]
        zw = [("Maßstab", f["massstab"]), ("Format", f["format"]), ("Datum", f["datum"]),
              ("Erstellt", f["erstellt"]), ("Plan-Nr.", f["plannr"]), ("Stand", f["stand"])]
        h = 7.0
        y0 = 13                       # darunter eine eigene Zeile für Quelle und KI-Hinweis
        teile = []
        hoehe = h * (len(zeilen) + len(zw) // 2) + 2
        teile.append(f"\\draw[rahmen] ({sx},{y0 + hoehe:.1f}) -- (415,{y0 + hoehe:.1f});")
        y = y0 + hoehe
        for k, v in zeilen:
            y -= h
            teile.append(f"\\draw[fein] ({sx},{y:.1f}) -- (415,{y:.1f});")
            teile.append(f"\\node[feld,anchor=north west] at ({sx + 1.5},{y + h - 0.6:.1f}) {{{k}}};")
            teile.append(f"\\node[eintrag,anchor=south west] at ({sx + 1.5},{y + 0.6:.1f}) {{{v}}};")
        for i in range(0, len(zw), 2):
            y -= h
            teile.append(f"\\draw[fein] ({sx},{y:.1f}) -- (415,{y:.1f}) ({sx + 47.5},{y:.1f}) -- ({sx + 47.5},{y + h:.1f});")
            for j, (k, v) in enumerate(zw[i:i + 2]):
                xx = sx + 1.5 + j * 47.5
                teile.append(f"\\node[feld,anchor=north west] at ({xx},{y + h - 0.6:.1f}) {{{k}}};")
                teile.append(f"\\node[eintrag,anchor=south west] at ({xx},{y + 0.6:.1f}) {{{v}}};")
        teile.append(f"\\node[fuss,anchor=south west,text width=91mm] at ({sx + 1.5},6.2) {{{f['fuss']}}};")
        return "\n".join(teile)

    def tex(self, legende, hinweise, schriftfeld, lehrbuch=False):
        plan, rand = self.blatt(legende, hinweise, schriftfeld, lehrbuch)
        return TEX.replace("%BIBLIOTHEK%", bibliothek(self.nummern)).replace("%PLAN%", plan).replace("%RAND%", rand)

    def bauen(self, ziel: Path, *a, dpi=200, **k):
        ziel = Path(ziel)
        ziel.with_suffix(".tex").write_text(self.tex(*a, **k), encoding="utf-8")
        r = subprocess.run(["lualatex", "-interaction=nonstopmode", "-halt-on-error", ziel.with_suffix(".tex").name],
                           cwd=ziel.parent, capture_output=True, text=True)
        if r.returncode:
            print(r.stdout[-3000:])
            raise SystemExit("LuaLaTeX-Fehler")
        for e in (".aux", ".log"):
            ziel.with_suffix(e).unlink(missing_ok=True)
        subprocess.run(["pdftoppm", "-png", "-r", str(dpi), "-singlefile", ziel.with_suffix(".pdf").name, ziel.name],
                       cwd=ziel.parent, check=True)
        return ziel.with_suffix(".png")


TEX = r"""\documentclass{article}
\usepackage[a3paper,landscape,margin=0mm]{geometry}
\usepackage{fontspec}\setmainfont{Liberation Sans}
\usepackage[ngerman]{babel}
\usepackage{tikz}
\pagestyle{empty}
\definecolor{elektrorot}{RGB}{220,0,0}
\newcommand{\elLW}{0.25mm}
\tikzset{
 wand/.style={line width=0.38mm,black!50},
 wandfuell/.style={fill=black!22},
 ausbau/.style={line width=0.25mm,black!35},
 elektro/.style={elektrorot},
 rahmen/.style={line width=0.5mm},
 fein/.style={line width=0.18mm},
 sk/.style={font=\fontsize{9.5}{10}\selectfont,inner sep=0.5mm,black},
 lz/.style={font=\fontsize{7.5}{8}\selectfont,inner sep=0.4mm,elektrorot},
 dat/.style={font=\fontsize{7}{8}\selectfont,inner sep=0.3mm,black},
 raum/.style={font=\fontsize{8}{9.5}\selectfont,align=center,black!60},
 kopf/.style={font=\bfseries\fontsize{10}{12}\selectfont},
 leg/.style={font=\fontsize{8}{10}\selectfont},
 feld/.style={font=\fontsize{5.5}{6.5}\selectfont,black!70,inner sep=0},
 eintrag/.style={font=\fontsize{8.5}{10}\selectfont,inner sep=0},
 fuss/.style={font=\fontsize{5.5}{6.5}\selectfont,inner sep=0,align=left},
}
%BIBLIOTHEK%
\begin{document}\noindent
\begin{tikzpicture}[x=1mm,y=1mm,line cap=round,line join=round]
\useasboundingbox (0,0) rectangle (420,297);
%PLAN%
%RAND%
\end{tikzpicture}
\end{document}
"""
