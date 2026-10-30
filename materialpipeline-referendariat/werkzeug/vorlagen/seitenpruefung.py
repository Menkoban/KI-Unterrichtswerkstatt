"""Seitenprüfung eines fertigen Arbeitsblatt-Dokuments am PDF (Lehrkraft 2026-10-25, Prüfcheckliste L27).

    python3 werkzeug/vorlagen/seitenpruefung.py <datei.docx> [...]

Setzt die DOCX mit LibreOffice als PDF und meldet jede Seite, auf der ein Aufgabenkasten (Profil
material.aufgaben_kaestchen, Hintergrund EAF0FA) das Letzte vor der Fußzeile ist: Dann steht die Aufgabe allein unten
und ihr Bearbeitungsteil beginnt erst auf der nächsten Seite. Aufgaben ohne eigenen Bearbeitungsteil (etwa „Ergänzen
Sie Ihre Karte“) melden sich auch; die Meldung ist darum ein Hinweis zum Ansehen, kein Fehler.

Platz nach Bedarf (Lehrkraft 2026-10-27, Prüfcheckliste L30): gemeldet wird auch eine Seite, deren unteres Drittel
leer ist, außer sie ist die letzte Seite eines AB (die nächste Seite beginnt mit „AB n ·“) oder die letzte Seite.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

KASTEN = (234, 240, 250)


def _ist_kasten(p):
    return abs(p[0] - KASTEN[0]) < 6 and abs(p[1] - KASTEN[1]) < 6 and abs(p[2] - KASTEN[2]) < 5


def seitenenden(docx, dpi=40):
    """Liste von (Seite, Hinweis) für Aufgaben, die allein unten auf einer Seite stehen."""
    befunde = []
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", d, str(docx)],
                       capture_output=True, timeout=300)
        pdf = Path(d) / (Path(docx).stem + ".pdf")
        if not pdf.exists():
            return [(0, "PDF nicht erzeugt, Seitenprüfung übersprungen")]
        subprocess.run(["pdftoppm", "-r", str(dpi), "-png", str(pdf), str(Path(d) / "s")], check=True, capture_output=True)
        for bild in sorted(Path(d).glob("s-*.png"), key=lambda f: int(f.stem.split("-")[1])):
            im = Image.open(bild).convert("RGB"); w, h = im.size; px = im.load()
            oben, unten = int(h * 0.1), int(h * 0.92)            # ohne Kopf und Fußzeile
            kasten = [y for y in range(oben, unten)
                      if sum(1 for x in range(0, w, 3) if _ist_kasten(px[x, y])) > w / 12]
            inhalt = [y for y in range(oben, unten)
                      if any(sum(px[x, y]) < 720 for x in range(int(w * 0.05), int(w * 0.95), 2))]
            nr = int(bild.stem.split("-")[1])
            if kasten and inhalt and max(inhalt) - max(kasten) < 12:
                befunde.append((nr, "Aufgabe steht allein unten; Bearbeitungsteil auf der nächsten Seite?"))
            frei = (unten - (max(inhalt) if inhalt else oben)) / (unten - oben)
            if frei > 1 / 3 and not _letzte_seite_eines_ab(pdf, nr):
                befunde.append((nr, f"unten {frei:.0%} frei; Platz nach Bedarf (Seitenumbruch, Felder zu groß?)"))
    return befunde


def _letzte_seite_eines_ab(pdf, nr):
    """Wahr, wenn die nächste Seite mit einem neuen AB beginnt („AB n ·“) oder es keine nächste Seite gibt."""
    r = subprocess.run(["pdftotext", "-f", str(nr + 1), "-l", str(nr + 1), str(pdf), "-"], capture_output=True,
                       text=True)
    if not r.stdout.strip():
        return True
    return bool(re.search(r"^\s*(AB \d+ ·|Quellenverzeichnis|Meilenstein \d)", r.stdout, re.M))


if __name__ == "__main__":
    for datei in sys.argv[1:]:
        for seite, text in seitenenden(datei):
            print(f"{Path(datei).name} Seite {seite}: {text}")
