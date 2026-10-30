"""Übersichtsschaltplan eines Stromkreisverteilers (einpolig) im Stil der Europa-Lehrmittel.

Vorbild: Fachkunde Elektrotechnik, 35. Aufl., S. 280 (Stromkreisverteiler: Schließer mit Auslösepfeil; LS-Schalter
und RCD einpolig mit Polzahl) und Arbeitsbuch 37566-7 S. 17 (Sammelschiene mit Verbindungspunkt, „F1“ links,
„Typ B16“ rechts). Energiefluss von oben nach unten. Maße in mm auf dem Blatt.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from uebersicht import LW_STRICH, PFEIL_B, PFEIL_L, STRICH, STRICH_WINKEL, Uebersicht, f

SCHALTGLIED = 3.85            # mm Schaltstück (37566-7 S. 17)
SCHALTWINKEL = 30             # Grad zur Senkrechten (Fachkunde S. 280)
PFEIL = 3.4                   # mm Auslösepfeil
SCHIENE = 0.7                 # mm Sammelschiene
R_PUNKT = 0.5                 # mm Verbindungspunkt Ø 1,0


@dataclass
class Abgang:
    kenn: str                 # F1 …
    char: str                 # „B10“
    leiter: str               # Außenleiter „L1“ oder „L1 L2 L3“
    polzahl: int
    adern: int
    leitung: str              # „NYM-J 3 × 1,5“
    ziel: list                # Textzeilen unter dem Abgang


@dataclass
class Gruppe:
    kenn: str                 # RCD „F10“
    text: list                # rechts neben dem Zeichen
    abgaenge: list = field(default_factory=list)


class Verteiler:
    def __init__(self):
        self.t: list[str] = []
        self.u = Uebersicht()                     # Aderzahl-Strich und Putzzeichen wie EI-02

    # ---------- Zeichen ----------
    def schaltglied(self, x, y_unten, rcd=False, pole=1):
        """Schließer mit Auslösepfeil; y_unten = Fußpunkt des Schaltstücks. Gibt (oben, unten) der Lücke zurück."""
        w = math.radians(SCHALTWINKEL)
        bx, by = x - SCHALTGLIED * math.sin(w), y_unten + SCHALTGLIED * math.cos(w)
        oben = y_unten + SCHALTGLIED * math.cos(w) - 0.3
        t = self.t
        t.append(f"\\draw ({f(x)},{f(y_unten)}) -- ({f(bx)},{f(by)});")
        # Auslösepfeil vom Schaltstück nach links unten (Fachkunde: unter ca. 30° zur Waagerechten)
        px, py = x - 0.55 * SCHALTGLIED * math.sin(w), y_unten + 0.55 * SCHALTGLIED * math.cos(w)
        a = math.radians(205)
        ex, ey = px + PFEIL * math.cos(a), py + PFEIL * math.sin(a)
        hx, hy = ex - 1.2 * math.cos(a), ey - 1.2 * math.sin(a)          # Pfeilspitze am Ende (zeigt nach außen)
        nx, ny = -math.sin(a), math.cos(a)
        t.append(f"\\draw ({f(px)},{f(py)}) -- ({f(hx)},{f(hy)});")
        t.append(f"\\fill ({f(ex)},{f(ey)}) -- ({f(hx + 0.45 * nx)},{f(hy + 0.45 * ny)}) -- "
                 f"({f(hx - 0.45 * nx)},{f(hy - 0.45 * ny)}) -- cycle;")
        if rcd:    # Fehlerstromauslöser: Querstrich am Pfeilschaft (Fachkunde S. 280)
            qx, qy = px + 0.55 * PFEIL * math.cos(a), py + 0.55 * PFEIL * math.sin(a)
            t.append(f"\\draw ({f(qx - 0.7 * nx)},{f(qy - 0.7 * ny)}) -- ({f(qx + 0.7 * nx)},{f(qy + 0.7 * ny)});")
        if pole > 1 and not rcd:   # mehrpolig: kurze Striche über dem Schaltstück (Fachkunde S. 280, LS dreipolig)
            for k in range(pole):
                s = 0.62 + 0.09 * k
                sx, sy = x - s * SCHALTGLIED * math.sin(w), y_unten + s * SCHALTGLIED * math.cos(w)
                t.append(f"\\draw[line width={LW_STRICH}mm] ({f(sx - 0.9)},{f(sy - 0.25)}) -- "
                         f"({f(sx + 0.9)},{f(sy + 0.25)});")
        return oben, y_unten

    def schiene(self, x0, x1, y):
        self.t.append(f"\\draw[line width={SCHIENE}mm] ({f(x0)},{f(y)}) -- ({f(x1)},{f(y)});")

    def punkt(self, x, y):
        self.t.append(f"\\fill ({f(x)},{f(y)}) circle ({R_PUNKT});")

    def linie(self, *p):
        self.t.append("\\draw " + " -- ".join(f"({f(x)},{f(y)})" for x, y in p) + ";")

    def text(self, x, y, s, anker="west", stil="bmk"):
        self.t.append(f"\\node[{stil},anchor={anker},align=left] at ({f(x)},{f(y)}) {{{s}}};")

    def adern(self, x, y0, y1, n, ab=6.0):
        self.t += self.u._strich((x, y0), (x, y1), n, ab)

    def putz(self, x, y0, y1, pos, art="UP"):
        self.t += self.u._putz((x, y0), (x, y1), pos, art)

    # ---------- Plan ----------
    def plan(self, einspeisung: dict, gruppen: list[Gruppe], x0=40, abstand=34, y_schiene=232, y_unten=128):
        """Einspeisung von oben auf die Sammelschiene, je Fehlerstrom-Schutzschalter eine Gruppe mit eigener
        Schiene, darunter die Leitungsschutzschalter mit Abgang (Aderzahl, Leitung, Verlegeart, Ziel)."""
        breite = [len(g.abgaenge) * abstand for g in gruppen]
        xg, x = [], x0
        for b in breite:
            xg.append(x)
            x += b + 12
        rechts = x - 12
        # Einspeisung
        xf = x0 + 8
        self.linie((xf, y_schiene + 34), (xf, y_schiene + PFEIL_L))
        self.t.append(f"\\fill ({f(xf - PFEIL_B / 2)},{f(y_schiene + PFEIL_L)}) -- ({f(xf + PFEIL_B / 2)},"
                      f"{f(y_schiene + PFEIL_L)}) -- ({f(xf)},{f(y_schiene + SCHIENE / 2)}) -- cycle;")
        self.adern(xf, y_schiene + 34, y_schiene, einspeisung["adern"], 7)
        self.putz(xf, y_schiene + 34, y_schiene, 14)
        self.text(xf + 2.5, y_schiene + 33, einspeisung["netz"], "north west")
        self.text(xf + 2.5, y_schiene + 24, einspeisung["herkunft"], "north west", "angabe")
        self.schiene(x0, rechts, y_schiene)
        for g, xa, b in zip(gruppen, xg, breite):
            xr = xa + b / 2                                  # RCD mittig über der Gruppe
            y_rcd = y_schiene - 22
            self.punkt(xr, y_schiene)
            oben, unten = self.schaltglied(xr, y_rcd, rcd=True)
            self.linie((xr, y_schiene), (xr, oben))
            ys = y_rcd - 24                                  # Gruppenschiene
            self.linie((xr, unten), (xr, ys))
            self.adern(xr, unten, ys, 4, 9)                  # vierpolig: L1, L2, L3, N
            self.text(xr - 6.0, y_rcd + 2.0, g.kenn, "east")
            self.text(xr + 1.5, y_rcd + 4.2, "\\\\".join(g.text), "north west", "angabe")
            self.schiene(xa, xa + b, ys)
            self.punkt(xr, ys)
            for i, a in enumerate(g.abgaenge):
                xl = xa + abstand * (i + 0.5)
                y_ls = ys - 20
                self.punkt(xl, ys)
                o, u = self.schaltglied(xl, y_ls, pole=a.polzahl)
                self.linie((xl, ys), (xl, o))
                self.text(xl - 0.6, ys - 1.0, a.leiter, "north east", "angabe")
                self.text(xl - 6.0, y_ls + 2.0, a.kenn, "east")
                self.text(xl + 1.2, y_ls + 2.0, a.char, "west")
                self.linie((xl, u), (xl, y_unten))
                self.adern(xl, u, y_unten, a.adern, 8)
                self.putz(xl, u, y_unten, 16)
                self.t.append(f"\\node[angabe,rotate=90,anchor=south east] at ({f(xl - 0.6)},{f(u - 20)}) "
                              f"{{{a.leitung}}};")
                self.text(xl, y_unten - 1.5, "\\\\".join(a.ziel), "north", "ziel")
        return "\n".join(self.t)
