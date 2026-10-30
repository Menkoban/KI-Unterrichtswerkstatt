"""Schaltzeichen-Katalog: Seiten mit Zeichen, Nummer nach EN 60617, deutschem Namen und Quelle.

Aufruf: python katalog.py <praefix oder Liste> <ausgabe.pdf> [png-ordner]
  praefix z. B. "07" (ganzer Teil 7) oder "07-02,07-15" (Abschnitte)
  oder Gruppen der Ergänzung "L,K,F,A,G" (Logik, KOP, FUP, GRAFCET, Gerätesymbole; siehe ergaenzung.csv)
Erzeugt PDF (LuaLaTeX) und PNG je Seite daneben (oder im png-ordner).
"""
import csv
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HIER = Path(__file__).resolve().parent
SPALTEN, ZEILEN = 5, 7
ZELLE_B, ZELLE_H = 3.6, 3.55      # cm
BILD_B, BILD_H = 2.6, 1.9
ANZEIGE = 1.6                      # Katalogmaßstab (Zeichen 1,6-fach)


def eintraege(auswahl):
    praefixe = [p.strip() for p in auswahl.split(",")]
    with open(HIER / "qet" / "symbole.csv", encoding="utf-8") as f:
        return [z for z in csv.DictReader(f, delimiter=";") if any(z["nummer"].startswith(p) for p in praefixe)]


def tex_esc(t):
    for a, b in (("\\", ""), ("&", "\\&"), ("%", "\\%"), ("#", "\\#"), ("_", "\\_"), ("~", "$\\sim$"), ("^", "")):
        t = t.replace(a, b)
    return t


def iec_abgleich():
    """alte Nummer -> (S-Nummer, Status) aus der Recherche (symbolliste.csv)."""
    d = {}
    with open(HIER / "symbolliste.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if r["iec_alt"]:
                d[r["iec_alt"]] = (r["iec_s"], r["status"])
    return d


ABGLEICH = None
FARBE = {"belegt": "green!45!black", "unsicher": "orange!85!black", "offen": "black!50"}


def zelle(i, z):
    global ABGLEICH
    if ABGLEICH is None:
        ABGLEICH = iec_abgleich()
    s_nr, status = ABGLEICH.get(z["nummer"], ("", "nicht abgeglichen"))
    pruef = (f"{s_nr} · " if s_nr else "") + status
    sp, ze = i % SPALTEN, (i // SPALTEN) % ZEILEN
    b, h = float(z["breite"]) or 0.1, float(z["hoehe"]) or 0.1
    s = min(ANZEIGE, BILD_B / b, BILD_H / h)      # einheitlich vergrößert, bei Bedarf verkleinert
    mx, my = float(z["mitte_x"]), float(z["mitte_y"])
    name = tex_esc(z["name_de"])
    if len(name) > 70:
        name = name[:68] + " …"
    x0, y0 = sp * ZELLE_B, -ze * ZELLE_H
    return (f"\\draw[black!15] ({x0:.2f},{y0:.2f}) rectangle ({x0 + ZELLE_B:.2f},{y0 - ZELLE_H:.2f});\n"
            f"\\begin{{scope}}[shift={{({x0 + ZELLE_B / 2:.3f},{y0 - 1.25:.3f})}},scale={s:.3f},"
            f"every node/.append style={{transform shape}}]\n"
            f"\\begin{{scope}}[shift={{({-mx:.3f},{-my:.3f})}}]\\szQ{{{z['nummer']}}}\\end{{scope}}\\end{{scope}}\n"
            f"\\node[font=\\footnotesize\\bfseries] at ({x0 + ZELLE_B / 2:.2f},{y0 - 2.42:.2f}) {{{z['nummer']}}};\n"
            f"\\node[font=\\tiny,text={FARBE.get(status, 'black!50')}] at ({x0 + ZELLE_B / 2:.2f},{y0 - 2.68:.2f}) {{IEC {pruef}}};\n"
            f"\\node[font=\\tiny,align=center,text width={ZELLE_B - 0.3:.2f}cm,anchor=north] "
            f"at ({x0 + ZELLE_B / 2:.2f},{y0 - 2.85:.2f}) {{{name}}};\n")


# ---------------------------------------------------------------------------------------------
# Ergänzung: Gruppen außerhalb von 91_en_60617 (Liste und Belege in ergaenzung.csv)
#   L Logik (IEC 60617-12, aus QET)      \szL{..}  qet_logik/symbole.tex
#   K KOP (IEC 61131-3, tikz-ladder)     \szK{..}  kop_fup/symbole.tex
#   F FUP (IEC 61131-3, eigene Kästen)   \szF{..}  kop_fup/symbole.tex
#   A GRAFCET (DIN EN 60848, grafcet)    \szA{..}  grafcet/symbole.tex
#   G Gerätesymbole (aus QET)            \szG{..}  qet_geraete/symbole.tex
# Aufruf: python katalog.py L,K,F,A,G <ausgabe.pdf> [png-ordner]
# tikz-ladder und ifsym (für grafcet) fehlen in manchen TeX-Installationen: Ordner mit den aus CTAN
# geladenen Dateien in der Umgebungsvariable SZ_CTAN angeben (mehrere mit ":" getrennt).
GRUPPEN = {
    "L": ("Logik nach DIN EN 60617-12", "szL", "qet_logik/symbole.tex"),
    "K": ("Kontaktplan (KOP) nach IEC 61131-3", "szK", "kop_fup/symbole.tex"),
    "F": ("Funktionsplan (FUP) nach IEC 61131-3", "szF", "kop_fup/symbole.tex"),
    "A": ("GRAFCET nach DIN EN 60848", "szA", "grafcet/symbole.tex"),
    "G": ("Gerätesymbole (zusammengesetzt)", "szG", "qet_geraete/symbole.tex"),
}
E_SPALTEN, E_ZEILEN = 4, 5


def ergaenzung_zelle(z):
    befehl = GRUPPEN[z["gruppe"]][1]
    farbe = "black" if z["status"] == "belegt" else "orange!80!black"
    hinweis = f"\\newline\\textit{{{tex_esc(z['hinweis'])}}}" if z["hinweis"] else ""
    return (f"\\szzelle{{\\{befehl}{{{z['schluessel']}}}}}\\par"
            f"{{\\scriptsize\\bfseries\\textbackslash {befehl}\\{{{tex_esc(z['schluessel'])}\\}}}}"
            f"\\hfill{{\\tiny\\color{{{farbe}}}{tex_esc(z['status'])}}}\\par"
            f"{{\\tiny\\raggedright {tex_esc(z['name_de'])}\\newline "
            f"\\textbf{{Beleg:}} {tex_esc(z['beleg'])}\\newline "
            f"\\textbf{{Zeichnung:}} {tex_esc(z['quelle'].replace('qet:', 'QET ')).replace('/', '/\\allowbreak ')}{hinweis}\\par}}")


def ergaenzung(auswahl, ziel, png_ordner=None):
    gruppen = [g.strip() for g in auswahl.split(",")]
    with open(HIER / "ergaenzung.csv", encoding="utf-8") as f:
        liste = [z for z in csv.DictReader(f, delimiter=";") if z["gruppe"] in gruppen]
    dateien = list(dict.fromkeys(GRUPPEN[g][2] for g in gruppen))
    teile = ["\\documentclass{article}\\usepackage[a4paper,margin=1.1cm]{geometry}",
             "\\usepackage{fontspec}\\setmainfont{Liberation Sans}\\usepackage{xcolor,graphicx,array}",
             "\\usepackage{tikz}\\usetikzlibrary{arrows.meta,calc}"]
    if "K" in gruppen:
        teile.append("\\usetikzlibrary{circuits.plc.ladder}")
    if "A" in gruppen:
        teile.append("\\usepackage{grafcet}")
    teile += ["\\input{" + str(HIER / d) + "}" for d in dateien]
    teile += ["\\newsavebox\\szbox",
              "\\newcommand{\\szzelle}[1]{\\sbox\\szbox{\\begin{tikzpicture}[x=1cm,y=1cm]#1\\end{tikzpicture}}%",
              "\\pgfmathsetmacro\\szs{min(" + str(ANZEIGE) + ",3.6cm/max(\\wd\\szbox,1pt),2.3cm/max(\\ht\\szbox+\\dp\\szbox,1pt))}%",
              "\\parbox[c][2.6cm][c]{\\linewidth}{\\centering\\scalebox{\\szs}{\\usebox\\szbox}}}",
              "\\setlength{\\tabcolsep}{3pt}\\renewcommand{\\arraystretch}{1}",
              "\\pagestyle{empty}\\begin{document}"]
    for g in gruppen:
        eintraege_g = [z for z in liste if z["gruppe"] == g]
        seiten = [eintraege_g[i:i + E_SPALTEN * E_ZEILEN] for i in range(0, len(eintraege_g), E_SPALTEN * E_ZEILEN)]
        for n, seite in enumerate(seiten, 1):
            teile.append("\\noindent{\\large\\bfseries Schaltzeichen-Ergänzung " + g + ": " + tex_esc(GRUPPEN[g][0]) +
                         "}\\hfill{\\footnotesize Teil " + str(n) + " von " + str(len(seiten)) + "}\\\\[2pt]")
            teile.append("{\\scriptsize Entwurf zur Prüfung neben den Belegen (Quellen mit URL und Seite: "
                         "quellen\\_ergaenzung.md). Zeichnungen aus QET: QElectroTech-Elementsammlung, CC-BY 3.0; "
                         "KOP: tikz-ladder (CTAN, LPPL); GRAFCET: Paket grafcet (CTAN, LPPL). "
                         "Status „unsicher“: Abweichung zum Beleg, siehe Hinweis.}\\par\\vspace{4pt}")
            teile.append("\\noindent\\begin{tabular}{" + "|p{4.25cm}" * E_SPALTEN + "|}\\hline")
            for r in range(0, len(seite), E_SPALTEN):
                reihe = [ergaenzung_zelle(z) for z in seite[r:r + E_SPALTEN]]
                reihe += [""] * (E_SPALTEN - len(reihe))
                teile.append(" & ".join(reihe) + "\\\\[2pt]\\hline")
            teile.append("\\end{tabular}\\newpage")
    teile.append("\\end{document}")
    return liste, teile


def uebersetzen(teile, ziel, png_ordner):
    umgebung = dict(os.environ)
    zusatz = [p for p in os.environ.get("SZ_CTAN", "").split(":") if p]
    if zusatz:
        umgebung["TEXINPUTS"] = "".join(str(Path(p).resolve()) + "//:" for p in zusatz) + os.environ.get("TEXINPUTS", "")
    with tempfile.TemporaryDirectory() as tmp:
        tex = Path(tmp) / "katalog.tex"
        tex.write_text("\n".join(teile), encoding="utf-8")
        r = subprocess.run(["lualatex", "-interaction=nonstopmode", "katalog.tex"], cwd=tmp, capture_output=True,
                           text=True, env=umgebung)
        pdf = Path(tmp) / "katalog.pdf"
        if not pdf.exists() or r.returncode != 0:
            print(r.stdout[-3000:])
            sys.exit("LaTeX-Fehler")
        ziel.write_bytes(pdf.read_bytes())
    png = Path(png_ordner).resolve() / ziel.stem if png_ordner else ziel.with_suffix("")
    subprocess.run(["pdftoppm", "-png", "-r", "100", str(ziel), str(png)], check=True)


def main(auswahl, ziel, png_ordner=None):
    ziel = Path(ziel).resolve()
    if all(g.strip() in GRUPPEN for g in auswahl.split(",")):
        liste, teile = ergaenzung(auswahl, ziel)
        uebersetzen(teile, ziel, png_ordner)
        print(len(liste), "Zeichen der Ergänzung:", ziel)
        return
    liste = eintraege(auswahl)
    seiten = [liste[i:i + SPALTEN * ZEILEN] for i in range(0, len(liste), SPALTEN * ZEILEN)]
    teile = ["\\documentclass{article}\\usepackage[a4paper,margin=1.2cm]{geometry}",
             "\\usepackage{fontspec}\\setmainfont{Liberation Sans}\\usepackage{tikz}\\usetikzlibrary{arrows.meta}",
             "\\input{" + str(HIER / "qet" / "symbole.tex") + "}",
             "\\pagestyle{empty}\\begin{document}"]
    for n, seite in enumerate(seiten, 1):
        teile.append("\\noindent{\\large\\bfseries Schaltzeichen nach DIN EN 60617 · " + tex_esc(auswahl) +
                     "}\\hfill{\\footnotesize Seite " + str(n) + " von " + str(len(seiten)) + "}\\\\[2pt]")
        teile.append("{\\scriptsize Zeichnung 1:1 übertragen aus der QElectroTech-Elementsammlung (Ordner "
                     "91\\_en\\_60617, CC-BY 3.0); Nummer nach EN 60617. Entwurf zur Prüfung.}\\par\\vspace{4pt}")
        teile.append("\\noindent\\begin{tikzpicture}[x=1cm,y=1cm]")
        teile += [zelle(i, z) for i, z in enumerate(seite)]
        teile.append("\\end{tikzpicture}\\newpage")
    teile.append("\\end{document}")
    with tempfile.TemporaryDirectory() as tmp:
        tex = Path(tmp) / "katalog.tex"
        tex.write_text("\n".join(teile), encoding="utf-8")
        r = subprocess.run(["lualatex", "-interaction=nonstopmode", "katalog.tex"], cwd=tmp, capture_output=True, text=True)
        pdf = Path(tmp) / "katalog.pdf"
        if not pdf.exists():
            print(r.stdout[-3000:])
            sys.exit("LaTeX-Fehler")
        ziel.write_bytes(pdf.read_bytes())
    subprocess.run(["pdftoppm", "-png", "-r", "100", str(ziel), str(ziel.with_suffix(""))], check=True)
    print(len(liste), "Zeichen auf", len(seiten), "Seiten:", ziel)


if __name__ == "__main__":
    main(*sys.argv[1:4])
