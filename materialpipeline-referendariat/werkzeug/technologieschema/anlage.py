"""Bausteine für Technologieschemata von Bandanlagen im Stil der Stilreferenz Siegelstation (Baustein 5):
TikZ, Schrägbild mit Tiefe, Graustufen, Positionsnummern mit Legende.

Eine Szene zeichnet nur, was ruht. Was sich bewegt oder bedient wird, legt die Simulation darüber; dafür schreibt
die Szene die Lage dieser Teile mit (szene.lage, in cm im Bild). Genutzt von foerderband.py (Stern-Dreieck) und
pendelband.py (Wendeschütz mit Endschaltern).
"""
import subprocess

DX, DY = 0.45, 0.3                       # Schrägbild-Tiefe je Einheit (wie Siegelstation)

PRAEAMBEL = r"""\documentclass[border=0mm]{standalone}
\usepackage[T1]{fontenc}\usepackage{helvet}\renewcommand{\familydefault}{\sfdefault}
\usepackage{tikz}
\usetikzlibrary{arrows.meta,shadings,patterns,calc,shadows.blur}
\definecolor{stahl}{HTML}{C9CED6}\definecolor{stahlh}{HTML}{E7EAEE}\definecolor{stahld}{HTML}{8A929E}
\definecolor{band}{HTML}{33373D}\definecolor{dunkel}{HTML}{1F3A5F}\definecolor{ral}{HTML}{D7DBE0}
\definecolor{motor}{HTML}{6E7F96}\definecolor{karton}{HTML}{C8975A}\definecolor{gruen}{HTML}{2E7D32}\definecolor{rot}{HTML}{C62828}
\tikzset{
 k/.style={line width=0.8pt,draw=black,line join=round},
 kf/.style={line width=0.5pt,draw=black,line join=round},
 nr/.style={circle,draw=black,fill=white,line width=0.7pt,inner sep=1pt,font=\bfseries\footnotesize,minimum size=5mm},
 hl/.style={line width=0.45pt,-{Circle[length=2pt]}},
 bmk/.style={font=\scriptsize\bfseries},
 schraube/.style={fill=stahld,draw=black,line width=0.3pt},
}
\def\dx{0.45}\def\dy{0.3}
% Quader: x y Breite Höhe Tiefe Farbe
\newcommand{\quader}[6]{%
 \fill[#6!75!black,draw=black,line width=0.8pt,line join=round] (#1+#3,#2) -- ++(#5*\dx,#5*\dy) -- ++(0,#4) -- ++(-#5*\dx,-#5*\dy) -- cycle;
 \fill[#6!45!white,draw=black,line width=0.8pt,line join=round] (#1,#2+#4) -- ++(#5*\dx,#5*\dy) -- ++(#3,0) -- ++(-#5*\dx,-#5*\dy) -- cycle;
 \shade[top color=#6!85!white,bottom color=#6,draw=black,line width=0.8pt] (#1,#2) rectangle ++(#3,#4);
 \draw[k] (#1,#2) rectangle ++(#3,#4);}
"""


def f(v):
    return f"{v:.3f}".rstrip("0").rstrip(".")


class Szene:
    def __init__(self, box, band=dict(x0=0.4, x1=12.8, y=2.27, tiefe=1.6, h=0.5), praeambel=""):
        self.box, self.b, self.praeambel = box, band, praeambel
        self.z, self.lage, self.nummern = [], {}, []

    def a(self, s):
        self.z.append(s)

    # ------------------------------------------------------------ Teile
    def boden(self):
        a = self.a
        a(r"\fill[black!6] (-1,-0.05) -- (24.2,-0.05) -- (24.9,0.45) -- (-0.3,0.45) -- cycle;")
        a(r"\draw[line width=1pt] (-1,-0.05) -- (24.2,-0.05);")
        a(r"\fill[pattern=north east lines,pattern color=black!30] (-1,-0.4) rectangle (24.2,-0.05);")

    def band(self, beweglich, fuesse=(0.8, 6.4, 11.9)):
        """Gestell, Gurt (Oberfläche, Seite) und Trommeln; beweglich=False ohne Gurtlinien."""
        a, b = self.a, self.b
        x0, x1, yb, t, hb = b["x0"], b["x1"], b["y"], b["tiefe"], b["h"]
        for x in fuesse:
            a(rf"\quader{{{f(x)}}}{{-0.05}}{{0.3}}{{{f(yb - hb - 0.27)}}}{{0.6}}{{stahl}}")
        a(rf"\quader{{{f(x0 - 0.15)}}}{{{f(yb - hb - 0.27)}}}{{{f(x1 - x0 + 0.3)}}}{{0.22}}{{{f(t)}}}{{stahl}}")
        a(rf"\fill[band!70!white,draw=black,line width=0.8pt] ({f(x0)},{f(yb)}) -- ++({f(t * DX)},{f(t * DY)}) -- ({f(x1 + t * DX)},{f(yb + t * DY)}) -- ({f(x1)},{f(yb)}) -- cycle;")
        if beweglich:
            for x in [x0 + 0.8 * i for i in range(1, 16)]:
                a(rf"\draw[white!55!band,line width=0.4pt] ({f(x)},{f(yb)}) -- ++({f(t * DX)},{f(t * DY)});")
        a(rf"\shade[top color=band!80!white,bottom color=band,draw=black,line width=0.8pt,rounded corners=2pt] ({f(x0)},{f(yb - hb)}) rectangle ({f(x1)},{f(yb)});")
        r = hb / 2
        for name, x in (("umlenk", x0), ("antrieb", x1)):
            a(rf"\draw[k,fill=stahld] ({f(x)},{f(yb - r)}) circle ({f(r)});")
            self.lage[name] = (x, yb - r, r)
        self.lage["band"] = dict(x0=x0, x1=x1, y=yb, tiefe=t, dx=DX, dy=DY)
        self.lage["box"] = self.box

    def karton(self, x, b=1.1, h=0.75, t=0.9):
        """Paket bzw. Kiste als Quader auf dem Gurt, etwas hinter der Vorderkante."""
        self.a(rf"\quader{{{f(x + 0.12)}}}{{{f(self.b['y'] + 0.12)}}}{{{f(b)}}}{{{f(h)}}}{{{f(t)}}}{{karton}}")

    def antrieb(self):
        """Welle, Stirnradgetriebe, Drehstrommotor mit Klemmenkasten auf Konsole, rechts an der Antriebstrommel."""
        a, x1 = self.a, self.b["x1"]
        ym = self.b["y"] - self.b["h"] / 2
        a(rf"\draw[k,fill=stahl] ({f(x1)},{f(ym - 0.07)}) rectangle ({f(x1 + 0.55)},{f(ym + 0.07)});")
        a(rf"\quader{{13.3}}{{0.95}}{{0.95}}{{1.45}}{{1.0}}{{stahl}}")                      # Getriebe
        a(r"\quader{13.1}{-0.05}{3.3}{0.95}{1.0}{stahl}")                                 # Konsole
        a(r"\shade[top color=motor!55,bottom color=motor!95!black,draw=black,line width=0.8pt] (14.25,1.15) rectangle (16.5,2.35);")
        for x in (14.55, 14.85, 15.15, 15.45, 15.75, 16.05):
            a(rf"\draw[motor!40!black,line width=0.5pt] ({f(x)},1.18) -- ({f(x)},2.32);")    # Kühlrippen
        a(r"\fill[motor!80!black,draw=black,line width=0.8pt] (16.5,1.15) -- ++(0.45,0.3) -- ++(0,1.2) -- ++(-0.45,-0.3) -- cycle;")
        a(r"\shade[top color=stahlh,bottom color=stahl,draw=black,line width=0.8pt] (16.5,1.2) rectangle (17.05,2.3);")   # Lüfterhaube
        for y in (1.35, 1.55, 1.75, 1.95, 2.15):
            a(rf"\draw[stahld,line width=0.6pt] (16.6,{f(y)}) -- (16.95,{f(y)});")
        a(r"\quader{14.75}{2.35}{0.9}{0.45}{0.7}{motor}")                                  # Klemmenkasten
        a(r"\draw[k,fill=stahld] (15.6,2.45) rectangle (15.75,2.65);")
        self.lage["motor"] = (15.2, 1.75)
        self.lage["klemmkasten"] = (15.2, 2.58)
        self.lage["anzeige"] = (14.75, 0.45)              # Schild für Betriebsart auf der Konsole

    def kabelkanal(self):
        a = self.a
        a(r"\draw[k,fill=stahl!70] (16.3,0.15) -- (19.6,0.15) -- (19.6,0.35) -- (16.3,0.35) -- cycle;")
        a(r"\draw[dunkel,line width=1.6pt,line cap=round] (15.75,2.55) -- (15.95,2.55) -- (15.95,3.0) -- (17.3,3.0) -- (17.3,0.25) -- (19.6,0.25);")
        a(r"\draw[dunkel,line width=1.2pt,line cap=round] (18.35,2.8) -- (18.35,0.3) -- (19.6,0.3);")

    def bedienkasten(self, taster, text, x0=17.6, breite=1.5):
        """taster: [(Kennzeichen, Farbe, Aufschrift, x)] auf einem Kasten auf Säule."""
        a = self.a
        a(r"\quader{18.25}{-0.05}{0.2}{2.85}{0.4}{stahl}")
        a(rf"\quader{{{f(x0)}}}{{2.8}}{{{f(breite)}}}{{1.25}}{{0.5}}{{ral}}")
        lage, y = {}, 3.5
        for bmk, farbe, sym, x in taster:
            lage[bmk] = (x, y)
            a(rf"\draw[k,fill=black!70] ({f(x)},{f(y)}) circle (0.24);")
            a(rf"\draw[kf,fill={farbe}] ({f(x)},{f(y)}) circle (0.18);")
            a(rf"\node[white,font=\scriptsize\bfseries] at ({f(x)},{f(y)}) {{{sym}}};")
            a(rf"\node[bmk,anchor=north] at ({f(x)},{f(y - 0.28)}) {{{bmk}}};")
        self.lage["taster"] = lage
        a(rf"\node[font=\tiny] at ({f(x0 + breite / 2)},3.8) {{{text}}};")

    def schaltschrank(self):
        a = self.a
        a(r"\quader{19.6}{-0.05}{4.3}{6.9}{1.0}{ral}")
        a(r"\draw[k,fill=white] (19.85,0.25) rectangle (23.65,6.6);")
        for y in (5.35, 3.6, 1.95):
            a(rf"\draw[line width=1.2pt,stahld] (20.0,{f(y)}) -- (23.5,{f(y)});")        # Hutschienen

    def geraet(self, bmk, x, y, b, h, text="", farbe="stahlh"):
        a = self.a
        a(rf"\shade[top color={farbe},bottom color=stahl,draw=black,line width=0.5pt] ({f(x)},{f(y)}) rectangle ++({f(b)},{f(h)});")
        a(rf"\draw[kf,fill=stahld!60] ({f(x + 0.05)},{f(y + h - 0.12)}) rectangle ++({f(b - 0.1)},0.08) ({f(x + 0.05)},{f(y + 0.04)}) rectangle ++({f(b - 0.1)},0.08);")
        a(rf"\node[bmk,anchor=north] at ({f(x + b / 2)},{f(y - 0.03)}) {{{bmk}}};")
        if text:
            a(rf"\node[font=\tiny,anchor=north] at ({f(x + b / 2)},{f(y - 0.3)}) {{{text}}};")
        self.lage.setdefault("geraete", {})[bmk] = (x, y, b, h)

    def klemmen_und_zufuehrung(self):
        a = self.a
        a(r"\foreach \x in {21.3,21.45,...,23.3}{\draw[kf,fill=stahlh] (\x,1.62) rectangle ++(0.12,0.45);}")
        a(r"\node[bmk,anchor=north] at (22.35,1.57) {-X1};")
        a(r"\draw[dunkel,line width=1.6pt] (22.75,0.25) -- (22.75,1.62); \draw[dunkel,line width=1.2pt] (23.05,0.25) -- (23.05,1.62);")
        a(r"\node[font=\small\itshape,anchor=west] at (20.2,7.5) {Schaltschrank +SC1};")

    # ------------------------------------------------------------ Beschriftung
    def nummer(self, n, z, text):
        self.nummern.append((n, z, text))

    def beschriften(self, titel):
        a = self.a
        for i, ((xn, yn), (xz, yz), _) in enumerate(self.nummern, 1):
            a(rf"\node[nr] (n{i}) at ({f(xn)},{f(yn)}) {{{i}}}; \draw[hl] (n{i}) -- ({f(xz)},{f(yz)});")
        a(rf"\node[font=\small\itshape,anchor=west] at (-0.8,7.9) {{{titel}}};")
        zeilen = [rf"\textbf{{{i}}} & {t_}" for i, (_, _, t_) in enumerate(self.nummern, 1)]
        spalten = [zeilen[i:i + 4] for i in range(0, len(zeilen), 4)]          # spaltenweise wie Siegelstation
        tab = "\\\\\n".join(" & ".join(spalten[j][i] if i < len(spalten[j]) else "&" for j in range(len(spalten)))
                            for i in range(max(len(s) for s in spalten)))
        a(r"\node[anchor=north west,font=\footnotesize,align=left] at (-0.8,-0.75){%" + "\n"
          r"\begin{tabular}{@{}r@{\,}l@{\qquad}r@{\,}l@{\qquad}r@{\,}l@{}}" + "\n" + tab +
          "\n\\end{tabular}};")

    # ------------------------------------------------------------ Ausgabe
    def tex(self):
        b = self.box
        return "\n".join([PRAEAMBEL + self.praeambel, r"\begin{document}", r"\begin{tikzpicture}[x=1cm,y=1cm]",
                          rf"\useasboundingbox ({b[0]},{b[1]}) rectangle ({b[2]},{b[3]});", *self.z,
                          r"\end{tikzpicture}", r"\end{document}"])


def bauen(tex, ziel):
    """TeX schreiben, mit pdflatex setzen, PNG-Vorschau (150 dpi)."""
    ziel.with_suffix(".tex").write_text(tex, encoding="utf-8")
    e = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", ziel.with_suffix(".tex").name],
                       cwd=ziel.parent, capture_output=True, text=True)
    for s in (".aux", ".log"):
        ziel.with_suffix(s).unlink(missing_ok=True)
    if e.returncode:
        raise SystemExit("pdflatex-Fehler:\n" + e.stdout[-3000:])
    subprocess.run(["pdftoppm", "-png", "-r", "150", "-singlefile", ziel.with_suffix(".pdf").name, ziel.name],
                   cwd=ziel.parent, check=True)
    return ziel
