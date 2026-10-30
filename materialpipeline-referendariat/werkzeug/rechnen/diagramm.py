"""Diagramme im Stil der abgenommenen Pt100-Kennlinie (docs/stilreferenz/kennlinie_pt100.tex):
pgfplots, Liberation Sans, Achsenzahlen serifenlos mit Komma, Gitter fein, Achsbeschriftung „Größe Zeichen in Einheit“.

Kurven werden aus Python-Funktionen abgetastet, also aus derselben Rechnung wie die Lösung (Rechenprüfer);
Diagramm und Erwartungshorizont können so nicht auseinanderlaufen.

    d = Diagramm(Achse("Temperatur", "ϑ", "°C", 0, 250, 50), Achse("Widerstand", "R", "Ω", 95, 200, 20))
    d.kurve(lambda t: 100 * (1 + 0.00385 * t), "Pt100 allein")
    d.messwerte([(0, 100.1), (50, 119.3)], "Messung")
    d.ablesen(180, f)                       # gepunktete Ablesehilfe x → Kurve → y-Achse
    d.massband(180, 188.3, 103, "8,3 K")
    d.bauen(ziel)                           # .tex, .pdf, .png (300 dpi, für Word) und Vorschau

Mit leer=True entsteht nur das beschriftete Raster, damit die Lernenden selbst eintragen.
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

FARBEN = {"dunkel": "1F3A5F", "heiss": "E4572E", "gruen": "2E7D4F", "grau": "6B6B6B", "gelb": "D9A62E"}
REIHE = ["dunkel", "heiss", "gruen", "grau"]


def fz(zeichen: str) -> str:
    """Formelzeichen in Mathe-Schreibweise: R_L → $R_\\mathrm{L}$, ϑ → $ϑ$ (Indizes aufrecht, DIN 1338)."""
    if not zeichen:
        return ""
    s = re.sub(r"_\{?([^}]+)\}?", lambda m: rf"_\mathrm{{{m.group(1)}}}", zeichen)
    return f"${s}$"


def tex_text(s: str) -> str:
    s = s.replace("Ω", r"\Ohm{}").replace("%", r"\%")
    return re.sub(r"(\w+)_\{?([^} ]+)\}?", lambda m: fz(f"{m.group(1)}_{m.group(2)}"), s)


def zahl(x: float) -> str:
    return f"{x:g}".replace(".", "{,}")


@dataclass
class Achse:
    groesse: str
    zeichen: str
    einheit: str
    von: float
    bis: float
    schritt: float | None = None
    log: bool = False

    def beschriftung(self):
        e = tex_text(self.einheit)
        return f"{self.groesse} {fz(self.zeichen)} in {e}".strip()


@dataclass
class Diagramm:
    x: Achse
    y: Achse
    breite_cm: float = 12
    hoehe_cm: float = 7.5
    leer: bool = False
    legende: str = "north west"
    _teile: list[str] = field(default_factory=list)
    _farbe: int = 0

    def _naechste(self, farbe):
        if farbe:
            return farbe
        f = REIHE[self._farbe % len(REIHE)]
        self._farbe += 1
        return f

    def kurve(self, f, name="", farbe=None, gestrichelt=False, punkte=101, von=None, bis=None):
        a, b = von if von is not None else self.x.von, bis if bis is not None else self.x.bis
        xs = [a + (b - a) * i / (punkte - 1) for i in range(punkte)]
        koord = " ".join(f"({x:.6g},{f(x):.6g})" for x in xs)
        stil = f"{self._naechste(farbe)},line width=1.4pt" + (",dashed" if gestrichelt else "")
        self._teile.append(f"\\addplot[{stil},no marks] coordinates {{{koord}}};"
                           + (f"\\addlegendentry{{{tex_text(name)}}}" if name else ""))
        return self

    def messwerte(self, punkte, name="", farbe=None, verbinden=False):
        koord = " ".join(f"({x:.6g},{y:.6g})" for x, y in punkte)
        c = self._naechste(farbe)
        stil = f"{c},mark=*,mark size=1.8pt,line width=0.9pt" + ("" if verbinden else ",only marks")
        self._teile.append(f"\\addplot[{stil}] coordinates {{{koord}}};"
                           + (f"\\addlegendentry{{{tex_text(name)}}}" if name else ""))
        return self

    def ablesen(self, x, f, text_x="", text_y="", farbe="dunkel"):
        """Gepunktete Ablesehilfe von der x-Achse zur Kurve und weiter zur y-Achse."""
        y = f(x)
        self._teile.append(
            f"\\draw[black!60,dotted,line width=0.8pt] (axis cs:{x:.6g},{self.y.von:.6g}) -- (axis cs:{x:.6g},{y:.6g})"
            f" -- (axis cs:{self.x.von:.6g},{y:.6g});\\fill[{farbe}] (axis cs:{x:.6g},{y:.6g}) circle (1.8pt);")
        if text_x:
            self.notiz(x, self.y.von, text_x, "south west")
        if text_y:
            self.notiz(self.x.von, y, text_y, "south west")
        return y

    def massband(self, x1, x2, y, text, seite="right"):
        """Maßpfeil zwischen x1 und x2; Beschriftung rechts daneben (bei kurzen Strecken lesbar) oder "above"."""
        lage = "midway,above" if seite == "above" else "pos=1,right=0.8mm"
        self._teile.append(
            f"\\draw[{{Stealth[length=1.3mm,width=1.3mm]}}-{{Stealth[length=1.3mm,width=1.3mm]}},line width=0.6pt] "
            f"(axis cs:{x1:.6g},{y:.6g}) -- (axis cs:{x2:.6g},{y:.6g}) node[{lage},font=\\footnotesize,fill=white,"
            f"inner sep=1pt]{{{tex_text(text)}}};")
        return self

    def notiz(self, x, y, text, anker="west"):
        self._teile.append(f"\\node[font=\\footnotesize,anchor={anker},fill=white,inner sep=1pt] "
                           f"at (axis cs:{x:.6g},{y:.6g}) {{{tex_text(text)}}};")
        return self

    def tex(self) -> str:
        x, y = self.x, self.y
        opt = [f"width={self.breite_cm}cm", f"height={self.hoehe_cm}cm", "scale only axis",
               f"xmin={x.von:g}", f"xmax={x.bis:g}", f"ymin={y.von:g}", f"ymax={y.bis:g}",
               f"xlabel={{{x.beschriftung()}}}", f"ylabel={{{y.beschriftung()}}}",
               "grid=both", "grid style={black!15}", "minor tick num=4", "minor grid style={black!6}",
               "axis lines=left", "tick style={black}", "/pgf/number format/use comma",
               "/pgf/number format/1000 sep={\\,}", "every axis label/.style={font=\\small}",
               "tick label style={font=\\small}", "legend cell align=left",
               f"legend style={{draw=none,fill=white,font=\\footnotesize,at={{{self._anker()}}},"
               f"anchor={self.legende}}}"]
        for a, n in ((x, "x"), (y, "y")):
            if a.schritt:
                opt.append(f"{n}tick distance={a.schritt:g}")
            if a.log:
                opt.append(f"{n}mode=log")
            else:
                # Achsenzahlen serifenlos (Textmodus statt Mathe-Schrift); nur auf linearen Achsen,
                # auf Log-Achsen übernimmt "log ticks with fixed point" die Formatierung (s. u.).
                opt.append(f"{n}ticklabel={{\\pgfmathprintnumber[assume math mode=true]{{\\tick}}}}")
        if x.log or y.log:
            # Feste (nicht-wissenschaftliche) Zahlen auch auf der Log-Achse, mit Komma (s. o.).
            opt.append("log ticks with fixed point")
        if self.leer:
            opt += ["minor tick num=9", "minor grid style={black!10}", "grid style={black!30}"]
        inhalt = "" if self.leer else "\n".join(self._teile)
        farben = "".join(f"\\definecolor{{{k}}}{{HTML}}{{{v}}}" for k, v in FARBEN.items())
        return (
            "\\documentclass[border=3mm]{standalone}\n"
            "\\usepackage{pgfplots}\\pgfplotsset{compat=1.18}\n"
            "\\usepackage{fontspec}\\setmainfont{Liberation Sans}\n"
            "\\usepackage{unicode-math}\\setmathfont{TeX Gyre DejaVu Math}\\newcommand{\\Ohm}{Ω}\n"
            "\\usetikzlibrary{arrows.meta}\n" + farben + "\n"
            "\\begin{document}\\begin{tikzpicture}\n"
            f"\\begin{{axis}}[{','.join(opt)}]\n{inhalt}\n\\end{{axis}}\n"
            "\\end{tikzpicture}\\end{document}\n")

    def _anker(self):
        return {"north west": "(0.02,0.98)", "north east": "(0.98,0.98)", "south east": "(0.98,0.02)",
                "south west": "(0.02,0.02)"}[self.legende]

    def bauen(self, ziel: Path, dpi=300) -> Path:
        """Schreibt ziel.tex, übersetzt mit LuaLaTeX, erzeugt ziel.pdf und ziel.png (für Word)."""
        ziel = Path(ziel)
        ziel.parent.mkdir(parents=True, exist_ok=True)
        ziel.with_suffix(".tex").write_text(self.tex(), encoding="utf-8")
        subprocess.run(["lualatex", "-interaction=nonstopmode", "-halt-on-error", ziel.with_suffix(".tex").name],
                       cwd=ziel.parent, check=True, capture_output=True)
        for endung in (".aux", ".log"):
            ziel.with_suffix(endung).unlink(missing_ok=True)
        subprocess.run(["pdftoppm", "-png", "-r", str(dpi), "-singlefile", ziel.with_suffix(".pdf").name, ziel.name],
                       cwd=ziel.parent, check=True)
        return ziel.with_suffix(".png")
