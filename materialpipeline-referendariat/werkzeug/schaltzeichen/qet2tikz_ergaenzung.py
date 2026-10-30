"""Ergänzung zu qet2tikz.py: überträgt einzelne QElectroTech-Elemente außerhalb von 91_en_60617.

Welche Elemente übertragen werden, steht in ergaenzung.csv (Spalte quelle = "qet:<pfad in der Sammlung>").
Die Umrechnung ist dieselbe wie in qet2tikz.py (element_zu_tikz, huelle, name_de werden unverändert
wiederverwendet); nur die Auswahl und die Befehlsnamen sind neu:
  Gruppe L (Logik, IEC 60617-12)  -> qet_logik/symbole.tex,   Befehl \\szL{und2}
  Gruppe G (Gerätesymbole)        -> qet_geraete/symbole.tex, Befehl \\szG{ls_1p}

Aufruf (nur als Datenleser, Sammlung liegt außerhalb des Repos):
  python -I qet2tikz_ergaenzung.py <pfad/zu/qelectrotech-elements>
"""
import csv
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HIER))  # bei python -I fehlt der Skriptordner im Suchpfad
import qet2tikz as q  # noqa: E402

ZIELE = {"L": ("qet_logik", "szL"), "G": ("qet_geraete", "szG")}


def main(sammlung):
    sammlung = Path(sammlung)
    with open(HIER / "ergaenzung.csv", encoding="utf-8") as f:
        zeilen = [z for z in csv.DictReader(f, delimiter=";") if z["quelle"].startswith("qet:")]
    for gruppe, (ordner, befehl) in ZIELE.items():
        ziel = HIER / ordner
        ziel.mkdir(exist_ok=True)
        q.KORREKTUREN.clear()
        befehle, tabelle = [], []
        for z in (z for z in zeilen if z["gruppe"] == gruppe):
            datei = sammlung / z["quelle"][4:]
            tikz = q.element_zu_tikz(datei)
            x0, x1, y0, y1 = q.huelle(ET.parse(datei).getroot().find("description"))
            befehle.append(f"\\expandafter\\def\\csname {befehl}@{z['schluessel']}\\endcsname{{%\n  {tikz}\n}}")
            tabelle.append({"schluessel": z["schluessel"], "name_qet": q.name_de(datei), "datei": z["quelle"][4:],
                            "mitte_x": f"{(x0 + x1) / 2 * q.MASSSTAB:.3f}", "mitte_y": f"{-(y0 + y1) / 2 * q.MASSSTAB:.3f}",
                            "breite": f"{(x1 - x0) * q.MASSSTAB:.3f}", "hoehe": f"{(y1 - y0) * q.MASSSTAB:.3f}"})
        kopf = ("% Automatisch erzeugt aus der QElectroTech-Elementsammlung, CC-BY 3.0,\n"
                "% https://github.com/qelectrotech/qelectrotech-elements. Nicht von Hand ändern.\n"
                "% Auswahl und Belege: ../ergaenzung.csv, Erzeugung: ../qet2tikz_ergaenzung.py\n"
                f"\\providecommand{{\\{befehl}}}[1]{{\\csname {befehl}@#1\\endcsname}}\n")
        (ziel / "symbole.tex").write_text(kopf + "\n".join(befehle) + "\n", encoding="utf-8")
        with open(ziel / "symbole.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(tabelle[0]), delimiter=";")
            w.writeheader()
            w.writerows(tabelle)
        print(gruppe, len(tabelle), "Zeichen übertragen nach", ordner, "| Korrekturen:", q.KORREKTUREN or "keine")


if __name__ == "__main__":
    main(sys.argv[1])
