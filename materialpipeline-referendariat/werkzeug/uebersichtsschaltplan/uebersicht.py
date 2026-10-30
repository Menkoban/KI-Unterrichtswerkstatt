"""Übersichtsschaltplan (einpolig) der Installation je Raum im Stil der Europa-Aufgabensammlung 32690-3.

Alle Maße gemessen: docs/recherche/2026-10-14_uebersichtsschaltplan.md (Europa 32690-3 S. 6–20, 33951-8 S. 20,
37566-7 S. 17). Regeln: docs/regeln/uebersichtsschaltplan_checkliste.md.

Aufbau wie Europa 32690-3 S. 15–20: Abzweigdosen in einer Reihe, Einspeisung von links, Leuchten darüber, Schalter
und Steckdosen darunter. Jede Leitung trägt ihre Aderzahl (einschließlich Schutzleiter), auch die Einspeisung
(33951-8). Die Einspeisung trägt zusätzlich Stromkreis, Leitungsangabe und Verlegeart (33951-8: „NYM-J Cu 1,5“ mit
Putzzeichen). Abzweige außerhalb von Dosen bekommen einen Verbindungspunkt (Knotenpunkt).

Koordinaten je Feld in Rasterschritten (5 mm), Ursprung auf der Dosenreihe, x nach rechts, y nach oben.
"""
from __future__ import annotations

import math
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent / "installationsplan"))
from grundriss import Plan  # noqa: E402  (Schriftfeld wie beim Installationsplan)

RASTER = 5.0                  # mm (Europa: Karoraster 5 mm)
LW = 0.25                     # mm Leitungen und Zeichen
LW_STRICH = 0.20              # mm Aderzahl-Strich
R_DOSE = 1.5                  # mm Abzweigdose Ø 3,0 (S. 6/7)
R_KNOTEN = 0.5                # mm Verbindungspunkt Ø 1,0 (37566-7 S. 17)
R_SCHALTER = 2.0              # mm Ø 4,0
HEBEL = 3.8                   # mm ab Kreisrand (bis 5,8 mm ab Mitte)
HEBEL_WINKEL = 58             # Grad zur Waagerechten
HAKEN = 2.13                  # mm
LEUCHTE = 2.0                 # mm halbe Kreuzbreite (4 × 4 mm)
SD_QUER = 4.0                 # mm Schutzkontaktstrich
SD_R = 2.0                    # mm Halbkreis 4,0 × 2,0
MEHRFACH = 1.83               # mm Schrägstrich der Mehrfachsteckdose
MEHRFACH_WINKEL = 42          # Grad
HERD = 6.0                    # mm wie im Grundriss (kein Europa-Übersichtsplan mit Herd gefunden)
STRICH = 3.77                 # mm Aderzahl-Strich
STRICH_WINKEL = 37            # Grad zur Waagerechten, auf allen Leitungen gleich
STRICH_ABSTAND = 10.0         # mm Mitte des Strichs hinter Dose bzw. Ecke
PFEIL_L, PFEIL_B = 3.12, 2.12  # mm gefülltes Dreieck
PUTZ_H, PUTZ_T, PUTZ_B = 1.4, 1.0, 3.2   # mm Putzzeichen: Strichhöhe, Teilung, Deckstrich (Fachkunde S. 681, etz S. 1)
HEBEL_JE_ART = {"aus": (HEBEL_WINKEL,), "serie": (HEBEL_WINKEL, 180 - HEBEL_WINKEL),
                "wechsel": (HEBEL_WINKEL, 180 + HEBEL_WINKEL),
                "kreuz": (HEBEL_WINKEL, 180 - HEBEL_WINKEL, 180 + HEBEL_WINKEL, 360 - HEBEL_WINKEL)}
# Aderzahl einschließlich PE vom Abzweig zum Gerät (Europa 32690-3 S. 17: „mit einem Schutzleiter, auch wenn dieser
# für das Betriebsmittel nicht erforderlich ist“)
ADERN_SOLL = {"aus": 3, "serie": 4, "wechsel": 4, "kreuz": 5, "leuchte": 3, "steckdose": 3, "herd": 5}


def f(z):
    return f"{z:.3f}"


@dataclass
class Element:
    art: str
    kenn: str
    x: float                  # mm absolut
    y: float
    typ: str = ""
    anzahl: int = 1
    zweck: str = ""

    def anschluss(self):
        return self.x, self.y + (R_SCHALTER if self.art == "schalter" else 0.0)

    def soll(self):
        return ADERN_SOLL.get(self.typ) or ADERN_SOLL.get(self.art)


@dataclass
class Leitung:
    punkte: list
    adern: int | None
    segment: int = -1         # Abschnitt mit dem Aderzahl-Strich
    ab: float = STRICH_ABSTAND
    ziel: Element | None = None


@dataclass
class Einspeisung:
    ziel: Element
    richtung: str             # "links" (Europa S. 6–20) oder "oben" (S. 9, 18/19; Geräte ohne Dose)
    start: float              # mm, x (links) bzw. y (oben) des Leitungsanfangs
    adern: int
    stromkreis: str
    leitung: str
    putz: str = "UP"
    text: str = "L/N/PE"

    def punkte(self):
        z = self.ziel
        if self.richtung == "links":
            return [(self.start, z.y), (z.x - (R_DOSE if z.art == "dose" else 0), z.y)]
        oben = {"dose": R_DOSE, "schalter": 2 * R_SCHALTER}.get(z.art, 0.0)
        return [(z.x, self.start), (z.x, z.y + oben)]


@dataclass
class Feld:
    titel: str
    x0: float                 # mm, linke Kante
    breite: float
    y0: float                 # mm, Dosenreihe
    unten: float              # mm, Unterkante des Rahmens
    oben: float = 0.0         # mm, Oberkante (Standard y0 + 45)
    elemente: list = field(default_factory=list)
    leitungen: list = field(default_factory=list)
    einspeisungen: list = field(default_factory=list)
    knoten: list = field(default_factory=list)
    roh: list = field(default_factory=list)

    def __post_init__(self):
        self.oben = self.oben or self.y0 + 45

    def p(self, gx, gy):
        return self.x0 + gx * RASTER, self.y0 + gy * RASTER

    def _neu(self, art, kenn, gx, gy, **k):
        e = Element(art, kenn, *self.p(gx, gy), **k)
        self.elemente.append(e)
        return e

    def dose(self, kenn, gx, gy=0):
        return self._neu("dose", kenn, gx, gy)

    def schalter(self, kenn, gx, gy, typ):
        return self._neu("schalter", kenn, gx, gy, typ=typ)

    def leuchte(self, kenn, gx, gy):
        return self._neu("leuchte", kenn, gx, gy)

    def steckdose(self, kenn, gx, gy, anzahl=1, zweck=""):
        return self._neu("steckdose", kenn, gx, gy, anzahl=anzahl, zweck=zweck)

    def herd(self, kenn, gx, gy, zweck=""):
        return self._neu("herd", kenn, gx, gy, typ="herd", zweck=zweck)

    def text(self, gx, gy, s, anker="west"):
        x, y = self.p(gx, gy)
        self.roh.append(f"\\node[leg,align=left,anchor={anker}] at ({f(x)},{f(y)}) {{{s}}};")

    def einspeisung(self, ziel, start_g, stromkreis, leitung, adern=3, richtung="links", **k):
        """start_g: Rasterwert x (links) bzw. y (oben) des Leitungsanfangs."""
        s = self.x0 + start_g * RASTER if richtung == "links" else self.y0 + start_g * RASTER
        self.einspeisungen.append(Einspeisung(ziel, richtung, s, adern, stromkreis, leitung, **k))

    def knoten_bei(self, gx, gy):
        self.knoten.append(self.p(gx, gy))
        return gx, gy

    def leitung(self, von, ueber, nach: Element, adern, segment=-1, ab=STRICH_ABSTAND):
        """Leitung von einem Element oder Rasterpunkt über Eckpunkte (Raster) zu einem Element."""
        start = (von.x, von.y) if isinstance(von, Element) else self.p(*von)
        pkt = [start] + [self.p(*q) for q in ueber] + [nach.anschluss()]
        self.leitungen.append(Leitung(pkt, adern, segment, ab, nach))


class Uebersicht:
    def __init__(self):
        self.felder: list[Feld] = []

    def feld(self, titel, x0, breite, y0, unten, oben=0.0):
        fd = Feld(titel, x0, breite, y0, unten, oben)
        self.felder.append(fd)
        return fd

    # ---------- Zeichen ----------
    def _schalter(self, e):
        r = R_SCHALTER
        t = []
        for w in HEBEL_JE_ART[e.typ]:
            a = math.radians(w)
            x0, y0 = e.x + r * math.cos(a), e.y + r * math.sin(a)
            x1, y1 = e.x + (r + HEBEL) * math.cos(a), e.y + (r + HEBEL) * math.sin(a)
            h = a - math.pi / 2 if math.cos(a - math.pi / 2) * math.cos(a) > 0 else a + math.pi / 2
            t.append(f"\\draw ({f(x0)},{f(y0)}) -- ({f(x1)},{f(y1)}) -- ({f(x1 + HAKEN * math.cos(h))},"
                     f"{f(y1 + HAKEN * math.sin(h))});")
        t.append(f"\\draw[fill=white] ({f(e.x)},{f(e.y)}) circle ({r});")
        t.append(f"\\node[bmk,anchor=east] at ({f(e.x - r - 0.6)},{f(e.y)}) {{{e.kenn}}};")
        return t

    def _leuchte(self, e):
        k = LEUCHTE
        return [f"\\draw ({f(e.x - k)},{f(e.y - k)}) -- ({f(e.x + k)},{f(e.y + k)}) "
                f"({f(e.x - k)},{f(e.y + k)}) -- ({f(e.x + k)},{f(e.y - k)});",
                f"\\node[bmk,anchor=east] at ({f(e.x - k - 0.6)},{f(e.y + 0.6)}) {{{e.kenn}}};"]

    def _steckdose(self, e):
        q, r = SD_QUER / 2, SD_R
        t = [f"\\draw ({f(e.x - q)},{f(e.y)}) -- ({f(e.x + q)},{f(e.y)});",
             f"\\draw ({f(e.x + r)},{f(e.y - r)}) arc[start angle=0,end angle=180,radius={r}];"]
        if e.anzahl > 1:
            # Schrägstrich rechts am Halbkreis unter 42°, Anzahl rechts oben (S. 19)
            a = math.radians(20)
            px, py = e.x + r * math.cos(a), e.y - r + r * math.sin(a)
            w = math.radians(MEHRFACH_WINKEL)
            h = MEHRFACH / 2
            t.append(f"\\draw ({f(px - h * math.cos(w))},{f(py - h * math.sin(w))}) -- "
                     f"({f(px + h * math.cos(w))},{f(py + h * math.sin(w))});")
            t.append(f"\\node[bmk,anchor=south west] at ({f(px + 0.9)},{f(py + 0.2)}) {{{e.anzahl}}};")
        t.append(f"\\node[bmk,anchor=east] at ({f(e.x - q - 0.6)},{f(e.y - r / 2)}) {{{e.kenn}}};")
        if e.zweck:
            t.append(f"\\node[zweck,anchor=north] at ({f(e.x)},{f(e.y - r - 1.2)}) {{{e.zweck}}};")
        return t

    def _herd(self, e):
        h = HERD
        t = [f"\\draw[fill=white] ({f(e.x - h / 2)},{f(e.y)}) rectangle ({f(e.x + h / 2)},{f(e.y - h)});"]
        for dx, dy in ((-1.5, -1.5), (1.5, -1.5), (0, -4.5)):
            t.append(f"\\fill ({f(e.x + dx)},{f(e.y + dy)}) circle (0.74);")
        t.append(f"\\node[bmk,anchor=east] at ({f(e.x - h / 2 - 0.6)},{f(e.y - h / 2)}) {{{e.kenn}}};")
        if e.zweck:
            t.append(f"\\node[zweck,anchor=north] at ({f(e.x)},{f(e.y - h - 1.2)}) {{{e.zweck}}};")
        return t

    def _dose(self, e):
        return [f"\\draw[fill=white] ({f(e.x)},{f(e.y)}) circle ({R_DOSE});",
                f"\\node[bmk,anchor=south east] at ({f(e.x - 0.4)},{f(e.y + 0.9)}) {{{e.kenn}}};"]

    def _strich(self, a, b, adern, ab):
        """Aderzahl-Strich (37°) auf dem Abschnitt a–b, Mitte ab mm hinter a, Ziffer rechts oben."""
        d = math.dist(a, b)
        t = min(ab, d / 2) / d
        mx, my = a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])
        w = math.radians(STRICH_WINKEL)
        h = STRICH / 2
        ex, ey = mx + h * math.cos(w), my + h * math.sin(w)
        return [f"\\draw[line width={LW_STRICH}mm] ({f(mx - h * math.cos(w))},{f(my - h * math.sin(w))}) -- "
                f"({f(ex)},{f(ey)});",
                f"\\node[bmk,anchor=south west,inner sep=0.3mm] at ({f(ex - 0.3)},{f(ey - 1.6)}) {{{adern}}};"]

    def _putz(self, a, b, pos, art):
        """Putzzeichen: drei Schrägstriche mit Deckstrich. Unter Putz: Zeichen über der Leitung (Leitung liegt unter
        der Schraffur), auf Putz: darunter mit Abstand, im Putz: Leitung durch die Striche (Fachkunde S. 681).
        „Über“ heißt in Leserichtung: bei senkrechten Leitungen links (Text von rechts lesbar, DIN EN 61082-1)."""
        d = math.dist(a, b)
        ux, uy = (b[0] - a[0]) / d, (b[1] - a[1]) / d
        nx, ny = (-1.0, 0.0) if abs(uy) > 0.5 else (0.0, 1.0)
        cx, cy = a[0] + ux * pos, a[1] + uy * pos
        a0 = {"UP": 0.0, "AP": -(0.6 + PUTZ_H), "IP": -PUTZ_H / 2}[art]
        # Schrägstriche immer gleich geneigt wie „///“ in Leserichtung
        sx, sy = (1.0, 0.0) if abs(uy) <= 0.5 else (0.0, 1.0)   # um 90° gedreht
        teile = []
        for k in (-PUTZ_T, 0.0, PUTZ_T):
            bx, by = cx + sx * k, cy + sy * k
            teile.append(f"({f(bx + nx * a0 - sx * 0.4)},{f(by + ny * a0 - sy * 0.4)}) -- "
                         f"({f(bx + nx * (a0 + PUTZ_H) + sx * 0.4)},{f(by + ny * (a0 + PUTZ_H) + sy * 0.4)})")
        o = a0 + PUTZ_H
        teile.append(f"({f(cx - sx * PUTZ_B / 2 + nx * o)},{f(cy - sy * PUTZ_B / 2 + ny * o)}) -- "
                     f"({f(cx + sx * PUTZ_B / 2 + nx * o)},{f(cy + sy * PUTZ_B / 2 + ny * o)})")
        return ["\\draw[line width=0.2mm] " + " ".join(teile) + ";"]

    def _einspeisung(self, e: Einspeisung):
        (sx, sy), (zx, zy) = e.punkte()
        b = PFEIL_B / 2
        t = [f"\\draw ({f(sx)},{f(sy)}) -- ({f(zx)},{f(zy)});"]
        angabe = f"{e.stromkreis}\\enspace {e.leitung}"
        if e.richtung == "links":
            t.append(f"\\fill ({f(zx - PFEIL_L)},{f(zy - b)}) -- ({f(zx - PFEIL_L)},{f(zy + b)}) -- ({f(zx)},{f(zy)}) -- cycle;")
            t.append(f"\\node[bmk,anchor=south west] at ({f(sx)},{f(sy + 0.6)}) {{{e.text}}};")
            # oben: „L/N/PE“, Aderzahl, Putzzeichen hintereinander; unten: Stromkreis und Leitung hinter dem Strich
            t += self._strich((sx, sy), (zx, zy), e.adern, 14.0)
            t += self._putz((sx, sy), (zx, zy), 22.0, e.putz)
            t.append(f"\\node[angabe,anchor=north west] at ({f(sx + 17.0)},{f(sy - 0.8)}) {{{angabe}}};")
        else:
            t.append(f"\\fill ({f(zx - b)},{f(zy + PFEIL_L)}) -- ({f(zx + b)},{f(zy + PFEIL_L)}) -- ({f(zx)},{f(zy)}) -- cycle;")
            t.append(f"\\node[bmk,anchor=south] at ({f(sx)},{f(sy + 0.6)}) {{{e.text}}};")
            t += self._strich((sx, sy), (zx, zy), e.adern, 6.0)
            t += self._putz((sx, sy), (zx, zy), 13.0, e.putz)
            t.append(f"\\node[angabe,rotate=90,anchor=south east] at ({f(sx - 0.6)},{f(sy - 17.0)}) {{{angabe}}};")
        return t

    # ---------- Prüfung ----------
    def _alle_abschnitte(self, fd):
        ab = []
        for l in fd.leitungen:
            ab += [(l.ziel.kenn or "Legende", s) for s in zip(l.punkte, l.punkte[1:])]
        for e in fd.einspeisungen:
            ab.append((f"Einspeisung {e.ziel.kenn}", tuple(e.punkte())))
        return ab

    def pruefen(self):
        """Fehler/Warnung/Hinweis: Aderzahl überall und je Gerät, Kreuzungen, Knotenpunkte, rechtwinklige Führung."""
        meld = []
        for fd in self.felder:
            for l in fd.leitungen:
                z = l.ziel
                if l.adern is None:
                    meld.append(("Fehler", f"{fd.titel}: Leitung zu {z.kenn} ohne Aderzahl"))
                elif z.soll() and l.adern != z.soll():
                    meld.append(("Fehler", f"{fd.titel}: {z.kenn} hat Aderzahl {l.adern}, erwartet {z.soll()}"))
                for (x1, y1), (x2, y2) in zip(l.punkte, l.punkte[1:]):
                    if abs(x1 - x2) > 1e-6 and abs(y1 - y2) > 1e-6:      # Lehrkraft 2026-10-14: nie schräg
                        meld.append(("Fehler", f"{fd.titel}: schräger Abschnitt zu {z.kenn}"))
            for e in fd.einspeisungen:
                soll = 3 if e.ziel.art == "dose" else e.ziel.soll()
                if e.adern != soll:
                    meld.append(("Fehler", f"{fd.titel}: Einspeisung {e.ziel.kenn} mit {e.adern} Adern, erwartet {soll}"))
            segs = self._alle_abschnitte(fd)
            for i, (k1, s1) in enumerate(segs):
                for k2, s2 in segs[i + 1:]:
                    if _schneiden(*s1, *s2):
                        meld.append(("Fehler", f"{fd.titel}: Leitungen zu {k1} und {k2} kreuzen sich"))
            # Abzweigdose mit mehr als vier Anschlüssen ist ohne schräge Abgänge nicht darstellbar
            for el in fd.elemente:
                if el.art == "dose":
                    zahl = sum(math.dist((el.x, el.y), q) < R_DOSE + 0.01 for l in fd.leitungen
                               for q in (l.punkte[0], l.punkte[-1])) + sum(e.ziel is el for e in fd.einspeisungen)
                    if zahl > 4:
                        meld.append(("Fehler", f"{fd.titel}: {el.kenn} hat {zahl} Anschlüsse (höchstens vier)"))
            # Treffen sich außerhalb einer Dose drei oder mehr Leitungsäste, ist ein Verbindungspunkt nötig
            dosen = [(e.x, e.y) for e in fd.elemente if e.art == "dose"]
            ende = [q for _, (a, b) in segs for q in (a, b)]
            for pkt in dict.fromkeys((round(x, 3), round(y, 3)) for x, y in ende):
                if any(math.dist(pkt, d) < R_DOSE + 0.01 for d in dosen):
                    continue
                grad = sum(math.dist(pkt, q) < 0.01 for q in ende) + 2 * sum(_auf_innen(pkt, a, b) for _, (a, b) in segs)
                if grad >= 3 and not any(math.dist(pkt, kn) < 0.01 for kn in fd.knoten):
                    meld.append(("Fehler", f"{fd.titel}: Abzweig bei {pkt} ohne Verbindungspunkt"))
        return meld

    # ---------- Blatt ----------
    def blatt(self, hinweise, schriftfeld):
        t = []
        for fd in self.felder:
            t.append(f"\\draw[fein] ({fd.x0},{fd.unten}) rectangle ({fd.x0 + fd.breite},{fd.oben});")
            t.append(f"\\node[kopf,anchor=north west] at ({fd.x0 + 3},{fd.oben - 3}) {{{fd.titel}}};")
            t += fd.roh
            for l in fd.leitungen:
                t.append("\\draw " + " -- ".join(f"({f(x)},{f(y)})" for x, y in l.punkte) + ";")
            for e in fd.einspeisungen:
                t += self._einspeisung(e)
            for el in fd.elemente:
                t += getattr(self, "_" + el.art)(el)
            for l in fd.leitungen:
                if l.adern is not None:
                    s = l.segment % (len(l.punkte) - 1)
                    t += self._strich(l.punkte[s], l.punkte[s + 1], l.adern, l.ab)
            for x, y in fd.knoten:
                t.append(f"\\fill ({f(x)},{f(y)}) circle ({R_KNOTEN});")
        sx = 415 - 95
        rand = ["\\draw[rahmen] (20,5) rectangle (415,292);", f"\\draw[rahmen] ({sx},5) -- ({sx},292);",
                f"\\node[kopf,anchor=north west] at ({sx + 4},288) {{Hinweise}};",
                f"\\node[leg,anchor=north west,text width=86mm,align=left] at ({sx + 4},281) {{{hinweise}}};",
                Plan._schriftfeld(None, sx, schriftfeld)]
        return "\n".join(t), "\n".join(rand)

    def bauen(self, ziel: Path, hinweise, schriftfeld, dpi=200):
        meld = list(dict.fromkeys(self.pruefen()))
        for m in meld:
            print(*m, sep=": ")
        if any(s == "Fehler" for s, _ in meld):
            raise SystemExit("Prüfung mit Fehlern")
        plan, rand = self.blatt(hinweise, schriftfeld)
        ziel = Path(ziel)
        ziel.with_suffix(".tex").write_text(TEX.replace("%PLAN%", plan).replace("%RAND%", rand), encoding="utf-8")
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


def _schneiden(p1, p2, p3, p4) -> bool:
    def kreuz(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    d1, d2 = kreuz(p3, p4, p1), kreuz(p3, p4, p2)
    d3, d4 = kreuz(p1, p2, p3), kreuz(p1, p2, p4)
    return (d1 * d2 < -1e-9) and (d3 * d4 < -1e-9)


def _auf_innen(p, a, b) -> bool:
    """Liegt p auf der Strecke a–b, aber nicht an deren Enden?"""
    if min(math.dist(p, a), math.dist(p, b)) < 0.01:
        return False
    return abs(math.dist(a, p) + math.dist(p, b) - math.dist(a, b)) < 1e-6


TEX = r"""\documentclass{article}
\usepackage[a3paper,landscape,margin=0mm]{geometry}
\usepackage{fontspec}\setmainfont{Liberation Sans}
\usepackage[ngerman]{babel}
\usepackage{tikz}
\pagestyle{empty}
\tikzset{
 rahmen/.style={line width=0.5mm},
 fein/.style={line width=0.18mm,black!40},
 raumgrenze/.style={line width=0.18mm,black!35,dash pattern=on 2mm off 1.2mm},
 raumname/.style={font=\fontsize{8}{9.5}\selectfont,black!55,inner sep=0.5mm},
 bmk/.style={font=\fontsize{9}{10}\selectfont,inner sep=0.4mm},
 angabe/.style={font=\fontsize{7.5}{9}\selectfont,inner sep=0.3mm},
 zweck/.style={font=\fontsize{7}{8}\selectfont,inner sep=0.3mm,align=center},
 kopf/.style={font=\bfseries\fontsize{10}{12}\selectfont},
 leg/.style={font=\fontsize{8}{10}\selectfont},
 feld/.style={font=\fontsize{5.5}{6.5}\selectfont,black!70,inner sep=0},
 eintrag/.style={font=\fontsize{8.5}{10}\selectfont,inner sep=0},
 fuss/.style={font=\fontsize{5.5}{6.5}\selectfont,inner sep=0,align=left},
}
\begin{document}\noindent
\begin{tikzpicture}[x=1mm,y=1mm,line cap=round,line join=round,line width=0.25mm]
\useasboundingbox (0,0) rectangle (420,297);
%PLAN%
%RAND%
\end{tikzpicture}
\end{document}
"""
