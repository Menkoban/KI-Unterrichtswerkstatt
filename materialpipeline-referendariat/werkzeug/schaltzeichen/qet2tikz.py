"""Überträgt Schaltzeichen aus der QElectroTech-Elementsammlung (Ordner 91_en_60617, CC-BY 3.0) unverändert in TikZ.

Die Geometrie wird nicht neu gezeichnet, sondern 1:1 umgerechnet (Maßstab 60 px = 1 cm, y nach oben).
Quelle je Zeichen: Dateiname = EN-60617-Nummer, deutscher Name aus <name lang="de">.

Aufruf (nur als Datenleser, Sammlung liegt außerhalb des Repos):
  python -I qet2tikz.py <pfad/zu/91_en_60617> <ausgabeordner>
Ergebnis: symbole.tex (ein \\szQ{<nummer>}-Befehl je Zeichen), symbole.csv (Nummer, Name, Datei)
"""
import csv
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

KORREKTUREN = []
# Abweichungen der Sammlung von der Norm, belegt durch das IEC-Verzeichnis (symbolliste.csv)
NORMKORREKTUR = {"en_60617_03_02_02": ("ohne_fuellung", "Klemme nach IEC 03-02-02/S00017 als offener Kreis (Sammlung: gefüllt)")}
MASSSTAB = 1 / 60  # cm je px: Kontaktlänge 60 px = 1,0 cm wie im abgenommenen Industriestil


def zahl(v):
    return float(v) if v not in (None, "") else 0.0


def k(x, y):
    return f"({zahl(x) * MASSSTAB:.4f},{-zahl(y) * MASSSTAB:.4f})"


def stil(style):
    s = dict(p.split(":", 1) for p in (style or "").split(";") if ":" in p)
    opt = []
    weight = s.get("line-weight", "normal")
    opt.append({"thin": "line width=0.4pt", "hight": "line width=1.2pt", "eleve": "line width=1.2pt",
                "none": "draw=none"}.get(weight, "line width=0.8pt"))
    ls = s.get("line-style", "normal")
    if ls == "dashed":
        opt.append("dash pattern=on 3pt off 2pt")
    elif ls == "dotted":
        opt.append("dotted")
    elif ls == "dashdotted":
        opt.append("dash pattern=on 3pt off 1.5pt on 0.5pt off 1.5pt")
    fill = s.get("filling", "none")
    if fill not in ("none", "") and not fill.startswith("hor") and not fill.startswith("ver") and not fill.startswith("bdiag") and not fill.startswith("fdiag"):
        opt.append("fill=" + ("black" if fill == "black" else "white" if fill == "white" else "black!50"))
    return ",".join(["line cap=round,line join=round"] + opt)


def tex_text(t):
    t = re.sub(r"\s*/\s*Forme\s*(\d+)", "", t)  # zweisprachige QET-Beschriftung: nur Deutsch
    t = t.replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("#", "\\#").replace("_", "\\_")
    t = t.replace("~", "$\\sim$").replace("^", "")
    return t


def huelle(desc):
    """Umriss (min/max in px) aus allen Zeichenelementen, für die Zentrierung im Katalog."""
    xs, ys = [], []
    for el in desc:
        a = el.attrib
        if el.tag == "line":
            xs += [zahl(a["x1"]), zahl(a["x2"])]; ys += [zahl(a["y1"]), zahl(a["y2"])]
        elif el.tag in ("rect", "ellipse", "arc"):
            x, y = zahl(a.get("x")), zahl(a.get("y"))
            xs += [x, x + zahl(a.get("width"))]; ys += [y, y + zahl(a.get("height"))]
        elif el.tag == "polygon":
            i = 1
            while f"x{i}" in a:
                xs.append(zahl(a[f"x{i}"])); ys.append(zahl(a[f"y{i}"])); i += 1
        elif el.tag == "text":
            txt = re.sub(r"\s*/\s*Forme\s*\d+", "", a.get("text") or "")
            x, y = zahl(a.get("x")), zahl(a.get("y"))
            xs += [x, x + 5.5 * len(txt)]; ys += [y - 9, y]
    if not xs:
        return 0, 0, 0, 0
    return min(xs), max(xs), min(ys), max(ys)


def element_zu_tikz(datei):
    root = ET.parse(datei).getroot()
    desc = root.find("description")
    korr = NORMKORREKTUR.get(Path(datei).stem)
    if korr:
        KORREKTUREN.append((Path(datei).stem, korr[1]))
        if korr[0] == "ohne_fuellung":
            for el in desc:
                if el.get("style"):
                    el.set("style", el.get("style").replace("filling:black", "filling:none"))
    teile = []
    for el in desc:
        tag, a = el.tag, el.attrib
        if tag == "line":
            pfeil = ""
            e1, e2 = a.get("end1", "none"), a.get("end2", "none")
            if e1 != "none" or e2 != "none":
                spitze = {"simple": "Straight Barb", "triangle": "Stealth", "circle": "Circle", "diamond": "Diamond"}
                l, r = spitze.get(e1, ""), spitze.get(e2, "")
                pfeil = f",{{{l}[length=1.5mm]}}-{{{r}[length=1.5mm]}}".replace("{[length=1.5mm]}", "")
            teile.append(f"\\draw[{stil(a.get('style'))}{pfeil}] {k(a['x1'], a['y1'])} -- {k(a['x2'], a['y2'])};")
        elif tag == "rect":
            x, y, w, h = (zahl(a.get(n)) for n in ("x", "y", "width", "height"))
            rx = zahl(a.get("rx"))
            rund = f",rounded corners={rx * MASSSTAB:.3f}cm" if rx else ""
            teile.append(f"\\draw[{stil(a.get('style'))}{rund}] {k(x, y)} rectangle {k(x + w, y + h)};")
        elif tag in ("ellipse", "circle"):
            x, y = zahl(a.get("x")), zahl(a.get("y"))
            w = zahl(a.get("width", a.get("diameter")))
            h = zahl(a.get("height", a.get("diameter")))
            teile.append(f"\\draw[{stil(a.get('style'))}] {k(x + w / 2, y + h / 2)} ellipse "
                         f"[x radius={w / 2 * MASSSTAB:.4f},y radius={h / 2 * MASSSTAB:.4f}];")
        elif tag == "arc":
            x, y, w, h = (zahl(a.get(n)) for n in ("x", "y", "width", "height"))
            start, winkel = zahl(a.get("start")), zahl(a.get("angle"))
            if winkel == 0:  # defektes Element: Bogen ohne Winkel = Vollkreis (protokolliert)
                winkel = 360
                KORREKTUREN.append((Path(datei).stem, "Bogen mit Winkel 0 als Vollkreis gezeichnet"))
            import math
            cx, cy, rx, ry = x + w / 2, y + h / 2, w / 2, h / 2
            sx = cx + rx * math.cos(math.radians(start))
            sy = cy - ry * math.sin(math.radians(start))
            teile.append(f"\\draw[{stil(a.get('style'))}] {k(sx, sy)} arc[start angle={start:.2f},"
                         f"delta angle={winkel:.2f},x radius={rx * MASSSTAB:.4f},y radius={ry * MASSSTAB:.4f}];")
        elif tag == "polygon":
            pkt = []
            i = 1
            while f"x{i}" in a:
                pkt.append(k(a[f"x{i}"], a[f"y{i}"]))
                i += 1
            zu = " -- cycle" if a.get("closed", "true") != "false" else ""
            teile.append(f"\\draw[{stil(a.get('style'))}] " + " -- ".join(pkt) + zu + ";")
        elif tag == "text":
            txt = a.get("text") or (el.findtext("text") or "")
            if txt.strip():
                rot = zahl(a.get("rotation"))
                m = re.search(r",(\d+(?:\.\d+)?),", a.get("font", ",9,"))
                pt = float(m.group(1)) if m else 9
                teile.append(f"\\node[anchor=base west,inner sep=0,font=\\fontsize{{{pt * 0.8:.1f}}}{{{pt:.1f}}}\\selectfont"
                             f",rotate={-rot:.0f}] at {k(a['x'], a['y'])} {{{tex_text(txt)}}};")
        # dynamic_text, terminal: Platzhalter für Beschriftung/Anschlüsse, nicht Teil des Schaltzeichens
    return "\n  ".join(teile)


def name_de(datei):
    s = Path(datei).read_text(encoding="utf-8")
    m = re.search(r'<name lang="de">(.*?)</name>', s, re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def nummer(datei):
    m = re.match(r"en_60617_(\d\d)_(\d\d)_(\d\d)(.*)", Path(datei).stem)
    # Zusatz wie „ex“ (Anwendungsbeispiel, z. B. 11-14-07ex) bleibt Teil der Nummer, sonst überschreibt das
    # Beispiel das Zeichen gleicher Nummer
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}{m.group(4)}" if m else Path(datei).stem


def main(quelle, ziel):
    quelle, ziel = Path(quelle), Path(ziel)
    ziel.mkdir(parents=True, exist_ok=True)
    zeilen, befehle = [], []
    for d in sorted(quelle.rglob("*.elmt")):
        nr = nummer(d)
        try:
            tikz = element_zu_tikz(d)
        except Exception as e:  # defekte Elemente melden, nicht raten
            print("FEHLER", d.name, e)
            continue
        befehle.append(f"\\expandafter\\def\\csname szQ@{nr}\\endcsname{{%\n  {tikz}\n}}")
        ohne_wv = "\n  ".join(z for z in tikz.split("\n  ") if "dash pattern" not in z)
        if ohne_wv != tikz:  # Betätigungszeichen ohne eigene Wirkverbindung (diese zeichnet der Plan durchgehend als 02-12-01)
            befehle.append(f"\\expandafter\\def\\csname szQo@{nr}\\endcsname{{%\n  {ohne_wv}\n}}")
        x0, x1, y0, y1 = huelle(ET.parse(d).getroot().find("description"))
        zeilen.append({"nummer": nr, "name_de": name_de(d), "datei": str(d.relative_to(quelle.parent)),
                       "mitte_x": f"{(x0 + x1) / 2 * MASSSTAB:.3f}", "mitte_y": f"{-(y0 + y1) / 2 * MASSSTAB:.3f}",
                       "breite": f"{(x1 - x0) * MASSSTAB:.3f}", "hoehe": f"{(y1 - y0) * MASSSTAB:.3f}"})
    kopf = ("% Automatisch erzeugt aus der QElectroTech-Elementsammlung (91_en_60617), CC-BY 3.0,\n"
            "% https://github.com/qelectrotech/qelectrotech-elements. Nicht von Hand ändern.\n"
            "\\newcommand{\\szQ}[1]{\\csname szQ@#1\\endcsname}\n"
            "% \\szQo{nr}: dasselbe Zeichen ohne gestrichelte Wirkverbindung (für durchgehende Wirklinien im Plan)\n"
            "\\newcommand{\\szQo}[1]{\\csname szQo@#1\\endcsname}\n")
    (ziel / "symbole.tex").write_text(kopf + "\n".join(befehle) + "\n", encoding="utf-8")
    with open(ziel / "symbole.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["nummer", "name_de", "datei", "mitte_x", "mitte_y", "breite", "hoehe"], delimiter=";")
        w.writeheader()
        w.writerows(zeilen)
    with open(ziel / "korrekturen.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["datei", "korrektur"])
        w.writerows(KORREKTUREN)
    print(len(zeilen), "Zeichen übertragen,", len(KORREKTUREN), "Korrekturen an defekten Quellelementen")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
