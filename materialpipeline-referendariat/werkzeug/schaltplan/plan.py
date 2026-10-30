"""Plan-Baukasten: Stromlaufpläne aus einer Beschreibung, die Regeln der Lehrkraft sind fest eingebaut.

Statt Koordinaten beschreibt man Strompfade (oben nach unten). Das Programm ordnet Zeichen, Leitungen,
Bezeichnungen, Betätigungen und Kontaktspiegel nach docs/regeln/schaltplan_checkliste.md an und
prüft die Beschreibung vorher. Zeichen und Maße: werkzeug/schaltzeichen/planzeichen.sty (EPLAN-Proportionen,
Raster 4 mm, A3 1:1).

Fest eingebaut (Nummern = Punkte der Schaltplan-Checkliste):
  21 jede Leitung endet an einem Anschluss (Leitungen werden nur zwischen Anschlusspunkten gezogen)
  22 Betätigung links vom Kontakt, Schaltmesser nach links (Öffner gespiegelt)
  23 Betriebsmittelkennzeichen links, technische Daten darunter
  24 Wirkverbindung nur vom Betätigungszeichen bis zum Schaltmesser desselben Kontakts; jeder Tasterkontakt
     bekommt seine eigene Betätigung (keine Wirklinien über fremde Kontakte)
  25 Taster-Öffner (Aus, Gegentaster) über der Selbsthaltung, Schütz-Verriegelungs-Öffner darunter (Prüfung)
  15 Kontaktspiegel unter jeder Spule, Spalte wird aus der Lage berechnet; keine Querverweise
  10 Verbindungspunkt an jeder Abzweigung
"""
from dataclasses import dataclass, field

# ------------------------------------------------------------------ Maße (mm, A3 1:1)
R = 4.0
KONTAKT = 8.0          # Kontaktlänge 2R
SLOT = 12.0            # Kontakt + 4 mm Leitung
POL = 8.0              # Polabstand
SPALTE0, SPALTE_B = 15.0, 39.5   # Spaltenraster des Blattes
BET_ABSTAND = 8.0      # Betätigung 8 mm links der Kontaktachse (FES S. 16)
# Wirkverbindung zwischen Kontakten desselben Tasters in verschiedenen Pfaden:
#   "gestuft": eine Betätigung am linken Kontakt, Wirklinie gerade – schräg – gerade zu den übrigen Kontakten
#   "einzeln": jeder Kontakt mit eigener Betätigung, keine Wirklinie über die Pfade
WIRKLINIE = "einzeln"   # Lehrkraft 2026-10-13: Wirklinien über die Pfade weglassen


def spalte(x):
    return int((x - SPALTE0) // SPALTE_B)


# ------------------------------------------------------------------ Beschreibung
@dataclass
class K:
    """Kontakt im Steuerstromkreis. art: 'S' Schließer, 'Ö' Öffner; bet: None, 'druck', 'thermisch'."""
    bmk: str
    art: str
    oben: str
    unten: str
    bet: str | None = None    # 'anzug': anzugverzögerter Kontakt eines Zeitrelais (07-05-01/03); 'position': Endschalter
    zusatz: str = ""          # z. B. „Aus“, „Rechts“


@dataclass
class Sich:
    bmk: str
    oben: str = "1"
    unten: str = "2"
    zusatz: str = ""


@dataclass
class Spule:
    bmk: str
    zusatz: str = ""
    art: str = ""             # 'anzug': Zeitrelais mit Ansprechverzögerung (07-15-08)


@dataclass
class Parallel:
    """Selbsthaltung: Zweige nebeneinander; der erste Zweig liegt in der Pfadachse."""
    zweige: list


@dataclass
class Pfad:
    elemente: list


@dataclass
class Steuerung:
    x0: float
    stamm: list                       # gemeinsame Elemente oben (Sicherung, Motorschutz-Öffner, Aus)
    pfade: list                       # je Spule ein Pfad
    pfad_abstand: float = 64.0
    n_x: float | None = None          # Lage der N-Leitung


@dataclass
class Plan:
    titel: str
    untertitel: str
    zusatz: str
    anlage: str = "=VL2"
    ort: str = "+SC1"
    betrieb: str = "Brinkmann Automation"
    betrieb_zusatz: str = "Musterstadt (fiktiver Modellbetrieb)"
    datum: str = "13.10.2026"
    haupt: list = field(default_factory=list)   # TikZ-Zeilen des Hauptstromkreises (aus Bausteinen)
    steuerung: Steuerung | None = None


# ------------------------------------------------------------------ Prüfung der Beschreibung
def pruefen(st: Steuerung):
    fehler = []
    for pf in st.pfade:
        par_gesehen = False
        for e in pf.elemente:
            if isinstance(e, Parallel):
                par_gesehen = True
            elif isinstance(e, K) and e.art == "Ö" and e.bet in ("druck", "thermisch") and par_gesehen:
                fehler.append(f"Regel 25: Taster-Öffner {e.bmk} {e.oben}-{e.unten} muss über der Selbsthaltung stehen")
            elif isinstance(e, K) and e.art == "Ö" and not e.bet and not par_gesehen and any(isinstance(t, Parallel) for t in pf.elemente):
                fehler.append(f"Regel 25: Schütz-Verriegelung {e.bmk} {e.oben}-{e.unten} muss unter der Selbsthaltung stehen")
        if not isinstance(pf.elemente[-1], Spule):
            fehler.append("Pfad endet nicht mit einer Spule")
    if fehler:
        raise ValueError("\n".join(fehler))


# ------------------------------------------------------------------ Zeichnen
class Zeichner:
    def __init__(self):
        self.z = []                    # TikZ-Zeilen
        self.oben = []                 # zuletzt gezeichnet (Klemmen über den Leitungen)
        self.taster = {}               # bmk -> [(x, y, wirkpunkt, kontakt)] für gestufte Wirklinien
        self.stufe = 0
        self.kontakte = []             # (bmk, art, oben, unten, x) für Kontaktspiegel
        self.spulen = {}               # bmk -> (x, y_unten)
        self.n = 0
        self.geo = []                  # Lage der Leitungen und Glieder für die Simulation (werkzeug/simulation)

    def glied(self, typ, bmk, x, y, **daten):
        """Leitendes Glied zwischen (x, y) und (x, y − KONTAKT): kontakt, fest (Sicherung, Bimetall), spule."""
        self.geo.append(dict(typ=typ, bmk=bmk, a=(round(x, 2), round(y, 2)), b=(round(x, 2), round(y - KONTAKT, 2)),
                             **daten))

    def tikz(self, s):
        self.z.append(s)

    def ltg(self, x1, y1, x2, y2):
        if (x1, y1) != (x2, y2):
            self.tikz(f"\\draw[pz] ({x1:.2f},{y1:.2f}) -- ({x2:.2f},{y2:.2f});")
            self.geo.append(dict(typ="ltg", a=(round(x1, 2), round(y1, 2)), b=(round(x2, 2), round(y2, 2))))

    def punkt(self, x, y):
        self.tikz(f"\\pzPunkt{{({x:.2f},{y:.2f})}}")

    def anr(self, x, y, oben, unten, halb=0.0):
        """Anschlussbezeichnungen rechts vom Zeichen (links liegen Messer und Betätigung).
        Abstand 1,2 mm ab Zeichenkante (halb = halbe Zeichenbreite), frei vom Verbindungspunkt (Ø 1,75)."""
        self.tikz(f"\\node[anr,anchor=west] at ({x + halb + 1.2:.2f},{y - 1.4:.2f}) {{{oben}}};")
        self.tikz(f"\\node[anr,anchor=west] at ({x + halb + 1.2:.2f},{y - 6.6:.2f}) {{{unten}}};")

    def wirklinie(self, x1, y1, x2, y2):
        """Wirkverbindung 02-12-01: viele kurze Striche (≈ 1,2 mm) mit kleinen Lücken (halbe Strichlänge),
        an die Länge angepasst, beginnt und endet mit einem Strich (Wunsch der Lehrkraft 2026-10-13)."""
        import math
        L = math.hypot(x2 - x1, y2 - y1)
        n = max(2, round((L + 0.6) / 1.8))                 # Zahl der Striche
        d = L / (n + (n - 1) / 2)
        self.tikz(f"\\draw[pz,line cap=butt,dash pattern=on {d:.3f}mm off {d / 2:.3f}mm] ({x1:.2f},{y1:.2f}) -- ({x2:.2f},{y2:.2f});")

    def bmk(self, x, y, text, zusatz=""):
        """Kennzeichen links (Regel 23); x = rechte Kante des Textes."""
        self.tikz(f"\\node[bmk,anchor=east] at ({x:.2f},{y:.2f}) {{{text}}};")
        if zusatz:
            self.tikz(f"\\node[dat,anchor=north east,align=right] at ({x:.2f},{y - 1.9:.2f}) {{{zusatz}}};")

    def kontakt(self, k: K, x, y):
        self.glied("kontakt", k.bmk, x, y, art=k.art, bet=k.bet or "")
        self.n += 1
        w = f"w{self.n}"
        if k.bet == "position" and k.art == "Ö":           # Endschalter 07-08-02 (Lehrkraft 2026-10-15)
            self.tikz(f"\\pzPositionsOeffner{{{x:.2f}}}{{{y:.2f}}}{{{w}}}")
        elif k.art == "S":
            self.tikz(f"\\pzSchliesser{{{x:.2f}}}{{{y:.2f}}}{{{w}}}")
        else:
            self.tikz(f"\\pzOeffner{{{x:.2f}}}{{{y:.2f}}}{{{w}}}")   # Haken und Messer nach rechts (Lehrkraft 2026-10-13)
        self.anr(x, y, k.oben, k.unten, halb=2.0 if k.art == "Ö" else 0.0)   # Öffner: Haken 2 mm nach rechts
        links = x - 4.5
        if k.bet and WIRKLINIE == "gestuft":
            self.taster.setdefault(k.bmk, []).append((x, y, w, k))
            if len(self.taster[k.bmk]) > 1:      # Betätigung nur am ersten Kontakt, Rest über die Wirklinie
                # Kennzeichen oberhalb der ankommenden Wirklinie (die liegt auf halber Kontakthöhe)
                self.tikz(f"\\node[bmk,anchor=north east,inner sep=0.3mm] at ({links:.2f},{y - 0.5:.2f}) {{{k.bmk}}};")
                self.kontakte.append((k.bmk, k.art, k.oben, k.unten, x))
                return
        if k.bet == "position":                  # Positionsschalter: Kennzeichen am Messer, keine Betätigung links
            links = x - 4.5
        elif k.bet == "anzug":                   # Zeitrelais: Verzögerungszeichen statt Betätigung
            self.tikz(f"\\pzVerzoegerung{{{x:.2f}}}{{{y:.2f}}}{{{-1.111 if k.art == 'S' else 0.667}}}")
            links = x - 5.0
        elif k.bet:
            bx = x - BET_ABSTAND
            if k.bet == "druck":
                self.wirklinie(bx, y - 4, x + (-1.111 if k.art == "S" else 0.667), y - 4)
                self.tikz(f"\\pzDruck{{({bx:.2f},{y - 4:.2f})}}{{1}}")
                links = bx - 1.5
            elif k.bet == "thermisch":
                self.wirklinie(bx + 1.33, y - 4, x + (-1.111 if k.art == "S" else 0.667), y - 4)
                self.tikz(f"\\pzThermBet{{({bx + 1.33:.2f},{y - 4:.2f})}}{{-1}}")
                links = bx - 1.5
        self.bmk(links, y - 2.6, k.bmk, k.zusatz)
        self.kontakte.append((k.bmk, k.art, k.oben, k.unten, x))

    def sicherung(self, s: Sich, x, y):
        self.glied("fest", s.bmk, x, y)
        self.tikz(f"\\pzSicherung{{{x:.2f}}}{{{y:.2f}}}")
        self.anr(x, y, s.oben, s.unten, halb=1.0)
        self.bmk(x - 3, y - 2.6, s.bmk, s.zusatz)

    def spule(self, s: Spule, x, y):
        self.tikz(f"\\pzSpule{'Anzug' if s.art == 'anzug' else ''}{{{x:.2f}}}{{{y:.2f}}}")
        self.tikz(f"\\node[anr,anchor=south west] at ({x + 1.4:.2f},{y - 2.0:.2f}) {{A1}};")
        self.tikz(f"\\node[anr,anchor=north west] at ({x + 1.4:.2f},{y - 6.0:.2f}) {{A2}};")
        self.bmk(x - (7 if s.art == "anzug" else 5), y - 2.6, s.bmk, s.zusatz)
        self.spulen[s.bmk] = (x, y - KONTAKT)
        self.glied("spule", s.bmk, x, y, art=s.art)

    def element(self, e, x, y):
        if isinstance(e, K):
            self.kontakt(e, x, y)
        elif isinstance(e, Sich):
            self.sicherung(e, x, y)
        elif isinstance(e, Spule):
            self.spule(e, x, y)


def wirklinien(zn: Zeichner):
    """Gestufte Wirklinie: vom Schaltmesser waagerecht nach rechts, kurz vor dem Zielkontakt schräg auf dessen
    Höhe, dann waagerecht bis an dessen Schaltmesser (wie in Lehrbüchern)."""
    for bmk, liste in zn.taster.items():
        liste = sorted(liste, key=lambda t: t[0])
        for (x1, y1, w1, _), (x2, y2, w2, _) in zip(liste, liste[1:]):
            ya, yb = y1 - 4, y2 - 4
            if abs(ya - yb) < 0.01:
                zn.tikz(f"\\draw[wv] ({w1}) -- ({w2});")
            else:
                zn.stufe += 1
                xs = x2 - 14 - 5 * (zn.stufe % 2)       # Stufen zweier Taster leicht versetzt
                zn.tikz(f"\\draw[wv] ({w1}) -- ({xs:.2f},{ya:.2f}) -- ({xs + 4:.2f},{yb:.2f}) -- ({w2});")


def hoehe(e):
    """Höhe eines Elements in Slots."""
    if isinstance(e, Parallel):
        return max(sum(hoehe(t) for t in zw) for zw in e.zweige) + 0.5 * (len(e.zweige) - 1)
    return 1


def zeichne_folge(zn: Zeichner, folge, x, y, zweig_abstand=24.0, am_verteiler=False, verteiler_ende=None):
    """Zeichnet Elemente untereinander ab Anschluss (x, y); gibt das untere Ende zurück.
    am_verteiler: der Pfad beginnt an der waagerechten Verteilleitung; ein Parallelzweig am Pfadanfang zweigt dann
    direkt auf ihrer Höhe ab (keine Absenkung, Lehrkraft 2026-10-14)."""
    for n, e in enumerate(folge):
        if isinstance(e, Parallel):
            direkt = am_verteiler and n == 0
            oben = y if direkt else y - 2     # sonst Abzweig 2 mm unter dem oberen Anschluss
            zn.ltg(x, y, x, oben)
            unten_max = []
            for i, zw in enumerate(e.zweige):
                xi = x + i * zweig_abstand
                yi = oben - (i * 6.0 if WIRKLINIE == "gestuft" else 0)  # versetzt nur bei übergreifenden Wirklinien
                if i:
                    zn.ltg(x, oben, xi, oben)
                    zn.ltg(xi, oben, xi, yi)
                    if not direkt:
                        zn.punkt(x, oben)
                    elif verteiler_ende is None or xi < verteiler_ende - 0.01:
                        zn.punkt(xi, oben)            # Abzweig auf der Verteilleitung; am Leitungsende eine Ecke
                ende = zeichne_folge(zn, zw, xi, yi)
                unten_max.append((xi, ende))
            unten = min(u for _, u in unten_max) - 2
            for xi, ende in unten_max:
                zn.ltg(xi, ende, xi, unten)
                if xi != x:
                    zn.ltg(xi, unten, x, unten)
            zn.punkt(x, unten)
            y = unten
        else:
            zn.element(e, x, y)
            y -= KONTAKT
            zn.ltg(x, y, x, y - (SLOT - KONTAKT))
            y -= SLOT - KONTAKT
    return y


def steuerung_zeichnen(zn: Zeichner, st: Steuerung, y_netz_l1, y_netz_n):
    pruefen(st)
    x = st.x0
    y_start = y_netz_l1 - 24                       # unterhalb der PE-Schiene beginnen
    zn.ltg(x, y_netz_l1, x, y_start)
    zn.punkt(x, y_netz_l1)
    y = zeichne_folge(zn, st.stamm, x, y_start)
    xs = [st.x0 + i * st.pfad_abstand for i in range(len(st.pfade))]
    zn.ltg(x, y, xs[-1], y)
    for xi in xs[1:-1]:
        zn.punkt(xi, y)
    if len(xs) > 1:
        zn.punkt(x, y)
    # Alle Pfade gleich hoch: Spulen in einer Reihe; die Verriegelungsöffner und übrigen Schützkontakte am
    # Pfadende (ohne Betätigung) stehen in allen Pfaden auf gleicher Höhe direkt über den Spulen
    # (Lehrkraft 2026-10-14). Die Leitung wird zwischen Pfadkopf und diesem Schwanz verlängert.
    def schwanz(elemente):
        n = 0
        for e in reversed(elemente):
            if isinstance(e, K) and not e.bet:
                n += 1
            else:
                break
        return elemente[:len(elemente) - n], elemente[len(elemente) - n:]
    teile = [schwanz(pf.elemente[:-1]) for pf in st.pfade]
    kopf_h = max(sum(hoehe(e) for e in k) for k, _ in teile)
    schwanz_h = max(len(t) for _, t in teile)
    # Parallelzweig am Pfadanfang zweigt auf der Verteilleitung ab; ragt der letzte Zweig über das Ende hinaus,
    # wird die Verteilleitung verlängert
    breit = [xi + 24.0 for pf, xi in zip(st.pfade, xs) if pf.elemente and isinstance(pf.elemente[0], Parallel)]
    ende_v = max([xs[-1]] + breit)
    if ende_v > xs[-1]:
        zn.ltg(xs[-1], y, ende_v, y)
        zn.punkt(xs[-1], y)                         # der letzte Pfad zweigt jetzt ab (Regel 10)
    enden = []
    for (kopf, rest), pf, xi in zip(teile, st.pfade, xs):
        ye = zeichne_folge(zn, kopf, xi, y, am_verteiler=True, verteiler_ende=ende_v)
        yt = min(ye, y - kopf_h * SLOT - (schwanz_h - len(rest)) * SLOT)
        zn.ltg(xi, ye, xi, yt)
        ye = zeichne_folge(zn, rest, xi, yt)
        ende = zeichne_folge(zn, pf.elemente[-1:], xi, ye)
        enden.append((xi, ende))
    wirklinien(zn)
    yn = min(e for _, e in enden) - 4
    xn = st.n_x or xs[-1] + 40
    for xi, e in enden:
        zn.ltg(xi, e, xi, yn)
    zn.ltg(xs[0], yn, xn, yn)
    for xi in xs[1:]:
        zn.punkt(xi, yn)
    zn.ltg(xn, yn, xn, y_netz_n)
    zn.punkt(xn, y_netz_n)
    return yn


def kontaktspiegel(zn: Zeichner, y):
    """Unter jeder Spule: S | Ö, Anschlüsse und Spalte (aus der Lage berechnet)."""
    for bmk, (x, _) in zn.spulen.items():
        s = [(o, u, cx) for b, a, o, u, cx in zn.kontakte if b == bmk and a == "S"]
        oe = [(o, u, cx) for b, a, o, u, cx in zn.kontakte if b == bmk and a == "Ö"]
        n = max(len(s), len(oe), 1)
        zn.tikz(f"\\begin{{scope}}[shift={{({x:.2f},{y:.2f})}}]")
        zn.tikz(f"\\draw[fein] (-13,0) -- (13,0) (0,0.8) -- (0,{-5 - n * 3.2:.1f});")
        zn.tikz("\\node[anr] at (-6.5,-2.4) {S}; \\node[anr] at (6.5,-2.4) {Ö};")
        for i, (o, u, cx) in enumerate(s, 1):
            zn.tikz(f"\\node[anr,anchor=east] at (-4.5,{-2.4 - i * 3.2:.1f}) {{{o}–{u}}};"
                    f"\\node[anr,anchor=east] at (-0.8,{-2.4 - i * 3.2:.1f}) {{{spalte(cx)}}};")
        for i, (o, u, cx) in enumerate(oe, 1):
            zn.tikz(f"\\node[anr,anchor=east] at (8.5,{-2.4 - i * 3.2:.1f}) {{{o}–{u}}};"
                    f"\\node[anr,anchor=east] at (12.2,{-2.4 - i * 3.2:.1f}) {{{spalte(cx)}}};")
        zn.tikz("\\end{scope}")


# ------------------------------------------------------------------ Blatt
def blatt(p: Plan, inhalt):
    sf = [f"\\node[anchor=west,font=\\fontsize{{12}}{{13}}\\selectfont\\bfseries] at (153,27) {{{p.betrieb}}};",
          f"\\node[anchor=west,font=\\fontsize{{7.5}}{{8}}\\selectfont] at (153,21.5) {{{p.betrieb_zusatz}}};",
          f"\\node[anchor=west,font=\\fontsize{{7.5}}{{8}}\\selectfont] at (153,11) {{Erstellt: {p.datum}}};",
          "\\node[anchor=west,font=\\fontsize{7.5}{8}\\selectfont] at (153,5) {Geprüft: ---};",
          f"\\node[anchor=west,font=\\fontsize{{12}}{{13}}\\selectfont\\bfseries] at (258,27) {{{p.titel}}};",
          f"\\node[anchor=west,font=\\fontsize{{9}}{{10}}\\selectfont] at (258,21) {{{p.untertitel}}};",
          f"\\node[anchor=west,font=\\fontsize{{9}}{{10}}\\selectfont] at (258,9) {{{p.zusatz}}};"]
    for t, w, yy in (("Anlage", p.anlage, 30.6), ("Ort", p.ort, 21.9), ("Blatt", "1 / 1", 13.1), ("Norm", "DIN EN 61082", 4.4)):
        sf.append(f"\\node[anchor=west,font=\\fontsize{{6.5}}{{7}}\\selectfont] at (332,{yy}) {{{t}}};"
                  f"\\node[anchor=east,font=\\fontsize{{9}}{{10}}\\selectfont] at (393,{yy}) {{{w}}};")
    return "\n".join([
        "% Automatisch erzeugt von werkzeug/schaltplan/plan.py – nicht von Hand ändern.",
        "\\documentclass{article}",
        "\\usepackage[paperwidth=420mm,paperheight=297mm,margin=0mm]{geometry}",
        "\\usepackage{fontspec}\\setmainfont{Liberation Sans}",
        "\\usepackage{planzeichen}",
        "\\pagestyle{empty}\\begin{document}\\noindent",
        "\\begin{tikzpicture}[x=1mm,y=1mm]",
        "\\useasboundingbox (0,0) rectangle (420,297);",
        "\\draw[rahmen] (10,5) rectangle (415,292); \\draw[fein] (15,40) rectangle (410,282);",
        "\\foreach \\c in {0,...,9}{\\draw[fein] (15+\\c*39.5,282) -- ++(0,10);"
        " \\node[font=\\fontsize{9}{10}\\selectfont] at (15+\\c*39.5+19.75,287) {\\c};}",
        "\\foreach \\z [count=\\i from 0] in {A,B,C,D,E,F}{\\pgfmathsetmacro{\\yo}{282-\\i*40.333}"
        " \\draw[fein] (10,\\yo) -- (15,\\yo) (410,\\yo) -- (415,\\yo);"
        " \\node[font=\\fontsize{9}{10}\\selectfont] at (12.5,\\yo-20.17) {\\z};"
        " \\node[font=\\fontsize{9}{10}\\selectfont] at (412.5,\\yo-20.17) {\\z};}",
        "\\begin{scope}[shift={(15,5)}]",
        "\\draw[fein] (0,0) rectangle (395,35) (150,0) -- (150,35) (255,0) -- (255,35) (330,0) -- (330,35)"
        " (330,17.5) -- (395,17.5) (330,26.25) -- (395,26.25) (330,8.75) -- (395,8.75) (150,17.5) -- (255,17.5);",
        *sf,
        "\\end{scope}",
        inhalt,
        "\\end{tikzpicture}\\end{document}"])


def netz(zn: Zeichner, x_bis, leiter=("L1", "L2", "L3", "N", "PE"), y0=272, text="3/N/PE AC 400/230 V 50 Hz"):
    ys = {}
    for i, l in enumerate(leiter):
        y = y0 - i * R
        ys[l] = y
        zn.ltg(28, y, x_bis, y)
        zn.tikz(f"\\node[anchor=east,font=\\fontsize{{8}}{{9}}\\selectfont] at (27,{y}) {{{l}}};")
    zn.tikz(f"\\node[anchor=west,font=\\fontsize{{8}}{{9}}\\selectfont] at (20,{y0 + 5.5}) {{{text}}};")
    return ys


# ------------------------------------------------------------------ Schaltfolge aus derselben Beschreibung
def _leitet(folge, betaetigt):
    """Leitet die Reihe aus Kontakten und Parallelzweigen? betaetigt(k) sagt, ob der Kontakt betätigt ist."""
    for e in folge:
        if isinstance(e, Parallel):
            if not any(_leitet(zw, betaetigt) for zw in e.zweige):
                return False
        elif isinstance(e, K):
            if betaetigt(e) != (e.art == "S"):        # Schließer leitet betätigt, Öffner unbetätigt
                return False
    return True


def schaltfolge(st: Steuerung, eingaben, verzoegerung: dict, ende=12.0, dt=0.1):
    """Spielt die gezeichnete Steuerung durch (keine zweite, von Hand geschriebene Logik).
    eingaben(t) → Menge der betätigten Taster und ausgelösten Motorschutz-Kontakte (Kennzeichen);
    verzoegerung: Zeitrelais → Anzugsverzögerung in s. Rückgabe: Liste (t, {Spule: an})."""
    spulen = [pf.elemente[-1].bmk for pf in st.pfade]
    an = {s: False for s in spulen}
    seit = {s: None for s in spulen}
    verlauf, t = [], 0.0
    while t <= ende + 1e-9:
        ein = eingaben(t)

        def betaetigt(k):
            if k.bmk in an:
                if k.bet == "anzug":
                    return an[k.bmk] and seit[k.bmk] is not None and t - seit[k.bmk] >= verzoegerung[k.bmk] - 1e-9
                return an[k.bmk]
            return k.bmk in ein

        for _ in range(20):                       # bis zum stabilen Zustand
            stamm = _leitet(st.stamm, betaetigt)
            neu = {pf.elemente[-1].bmk: stamm and _leitet(pf.elemente[:-1], betaetigt) for pf in st.pfade}
            if neu == an:
                break
            for s in spulen:
                if neu[s] and not an[s]:
                    seit[s] = t
                if not neu[s]:
                    seit[s] = None
            # Schütze ziehen nacheinander an: je Durchlauf nur die erste Änderung übernehmen (keine Gleichzeitigkeit)
            s = next(s for s in spulen if neu[s] != an[s])
            an[s] = neu[s]
        verlauf.append((round(t, 1), dict(an)))
        t += dt
    return verlauf


# ------------------------------------------------------------------ Prüfung: nichts verdeckt (Lehrkraft 2026-10-14)
def ueberdeckungen(zeilen, schrift_mm=None):
    """Sucht Texte, die eine Leitung oder einen anderen Text überdecken. Breite geschätzt (0,55 × Schriftgröße je
    Zeichen), Höhe 0,75 × Schriftgröße; Leitungen aus \\draw[pz]-Strecken. Rückgabe: Liste von Meldungen."""
    import re
    groesse = {"bmk": 9, "anr": 7, "dat": 7.5}
    pt = 0.3528
    texte, linien = [], []
    im_scope = 0
    for z in zeilen:
        if "\\begin{scope}" in z:                    # verschobene Gruppen (Kontaktspiegel): eigene Koordinaten
            im_scope += z.count("\\begin{scope}")
        if im_scope:
            im_scope -= z.count("\\end{scope}")
            continue
        for m in re.finditer(r"\\node\[(\w+)[^\]]*?anchor=([\w ]+)[^\]]*\] at \(([-\d.]+),([-\d.]+)\) \{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", z):
            stil, anker, x, y, text = m.group(1), m.group(2), float(m.group(3)), float(m.group(4)), m.group(5)
            if stil not in groesse:
                continue
            zeilen_t = [re.sub(r"\\[a-z]+(\{[^}]*\})?|[{}$]", "", t).strip() for t in text.split("\\\\")]
            h = groesse[stil] * pt
            b = max(len(t) for t in zeilen_t) * 0.55 * h
            hh = h * 0.75 * len(zeilen_t) + 0.4 * (len(zeilen_t) - 1)
            sep = 0.5
            x0 = {"west": x + sep, "east": x - sep - b}.get(anker.split()[-1], x - b / 2)
            if "north" in anker:
                y1 = y - sep; y0 = y1 - hh
            elif "south" in anker:
                y0 = y + sep; y1 = y0 + hh
            else:
                y0 = y - hh / 2; y1 = y + hh / 2
            if anker in ("west", "east"):
                pass
            texte.append((x0 + 0.2, y0 + 0.2, x0 + b - 0.2, y1 - 0.2, " ".join(zeilen_t)))
        for m in re.finditer(r"\\draw\[pz\] \(([-\d.]+),([-\d.]+)\) -- \(([-\d.]+),([-\d.]+)\)", z):
            linien.append(tuple(map(float, m.groups())))
    meld = []
    for (a0, b0, a1, b1, t) in texte:
        for (x1, y1, x2, y2) in linien:
            if abs(x1 - x2) < 1e-6 and a0 < x1 < a1 and min(y1, y2) < b1 and max(y1, y2) > b0:
                meld.append(f"Text „{t}“ überdeckt eine senkrechte Leitung bei x = {x1:.1f}")
            if abs(y1 - y2) < 1e-6 and b0 < y1 < b1 and min(x1, x2) < a1 and max(x1, x2) > a0:
                meld.append(f"Text „{t}“ überdeckt eine waagerechte Leitung bei y = {y1:.1f}")
    for i, (a0, b0, a1, b1, t) in enumerate(texte):
        for (c0, d0, c1, d1, u) in texte[i + 1:]:
            if a0 < c1 and c0 < a1 and b0 < d1 and d0 < b1:
                meld.append(f"Texte „{t}“ und „{u}“ überdecken sich")
    return list(dict.fromkeys(meld))
