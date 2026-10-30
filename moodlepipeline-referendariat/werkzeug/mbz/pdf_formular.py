"""Ausfüllbares PDF aus einer Word-Datei.

    pdf = docx_zu_pdf(docx, ziel)     # Word (pywin32), sonst LibreOffice
    n = formular_felder(pdf)          # Textfelder auf Schreibzeilen und leere Tabellenzellen

Ein Feld liegt über jeder Schreibzeile (mindestens fünf `_` hintereinander, ganze Breite der Unterstriche),
über jeder gezeichneten waagerechten Linie ab 60 pt (Word: Linie oder Absatzrahmen unten; nicht auf
Tabellen- oder Kastenrändern, nicht gestrichelt, nicht unter oder durch Text) und über jeder leeren
Tabellenzelle, die mindestens 18 pt hoch ist. Was schon ein Feld hat, bekommt kein zweites.
Feldnamen `feld_<seite>_<nr>`, Schrift Helvetica 11. Ohne Felder bleibt die Datei unverändert.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ZELLE_MIN_HOEHE = 18.0      # pt; flachere leere Zellen sind Abstandshalter
MEHRZEILIG_AB = 30.0        # pt; höhere Felder brechen um
SCHRIFT, GROESSE = "Helv", 11
LINIE_MIN_LAENGE = 60.0     # pt; kürzere Striche sind Schmuck oder Kästchen
LINIE_MAX_DICKE = 3.0       # pt; dickere „Linien“ sind Flächen
LINIE_FELD_HOEHE = 14.0     # pt; eine Zeile Helvetica 11
RAND_TOLERANZ = 3.0         # pt; so nah an einem Zellen- oder Kastenrand gilt eine Linie als Rahmen


def _lies(pfad: Path) -> bytes:
    import docx_seite
    return docx_seite._lies(pfad)


def _soffice() -> str | None:
    gefunden = shutil.which("soffice") or shutil.which("soffice.exe")
    if gefunden:
        return gefunden
    for basis in (os.environ.get("ProgramFiles", r"C:\Program Files"),
                  os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")):
        kandidat = Path(basis) / "LibreOffice" / "program" / "soffice.exe"
        if kandidat.is_file():
            return str(kandidat)
    return None


def _mit_word(quelle: Path, ziel: Path) -> bool:
    try:
        import pythoncom
        import win32com.client
    except ImportError:
        return False
    pythoncom.CoInitialize()
    try:
        try:
            word = win32com.client.DispatchEx("Word.Application")
        except Exception:     # Word nicht installiert
            return False
        try:
            word.Visible = False
            word.DisplayAlerts = 0
            dok = word.Documents.Open(str(quelle), ReadOnly=True, AddToRecentFiles=False)
            try:
                dok.SaveAs2(str(ziel), FileFormat=17)    # wdFormatPDF
            finally:
                dok.Close(False)
        finally:
            word.Quit()
        return True
    finally:
        pythoncom.CoUninitialize()


def docx_zu_pdf(docx: Path, ziel: Path) -> Path:
    """DOCX als PDF nach `ziel`. Word arbeitet auf einer Kopie unter kurzem Pfad (lange Kursordnerpfade
    und Umlaute vertragen sich nicht mit Word)."""
    ziel = Path(ziel).resolve()
    ziel.parent.mkdir(parents=True, exist_ok=True)
    arbeit = Path(tempfile.mkdtemp(prefix="docx_pdf_"))
    try:
        quelle = arbeit / "quelle.docx"
        quelle.write_bytes(_lies(Path(docx)))
        aus = arbeit / "quelle.pdf"
        if not _mit_word(quelle, aus):
            soffice = _soffice()
            if soffice is None:
                raise RuntimeError("Weder Word noch LibreOffice gefunden – das PDF zu "
                                   f"{Path(docx).name} lässt sich nicht erzeugen.")
            subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(arbeit), str(quelle)],
                           check=True, capture_output=True, timeout=180)
        if not aus.is_file():
            raise RuntimeError(f"Umwandlung in PDF ohne Ergebnis: {Path(docx).name}")
        shutil.move(str(aus), str(ziel))
        return ziel
    finally:
        shutil.rmtree(arbeit, ignore_errors=True)


def _schreibzeilen(seite) -> list:
    """Rechtecke der Folgen aus ≥5 `_` (ganze Breite der Unterstriche, Höhe der Zeile)."""
    import pymupdf
    rechtecke = []
    for block in seite.get_text("rawdict")["blocks"]:
        for zeile in block.get("lines", []):
            lauf = []
            zeichen = [z for span in zeile["spans"] for z in span["chars"]] + [None]
            for z in zeichen:
                if z is not None and z["c"] == "_":
                    lauf.append(z)
                    continue
                if len(lauf) >= 5:
                    r = pymupdf.Rect(lauf[0]["bbox"])
                    for u in lauf[1:]:
                        r |= pymupdf.Rect(u["bbox"])
                    rechtecke.append(r)
                lauf = []
    return rechtecke


def _zellen(seite) -> list:
    """Alle Zellen aller erkannten Tabellen."""
    import pymupdf
    try:
        tabellen = seite.find_tables().tables
    except Exception:       # Tabellenerkennung scheitert an manchen Zeichnungen
        return []
    return [pymupdf.Rect(zelle) for tabelle in tabellen for zeile in tabelle.rows
            for zelle in zeile.cells if zelle is not None]


def _leere_zellen(seite, zellen) -> list:
    rechtecke = []
    for r in zellen:
        if r.height < ZELLE_MIN_HOEHE or r.width < 10:
            continue
        if seite.get_text("text", clip=r).strip():
            continue
        rechtecke.append(r + (2, 2, -2, -2))       # nicht auf den Rahmenlinien
    return rechtecke


def _gestrichelt(zeichnung) -> bool:
    striche = (zeichnung.get("dashes") or "").strip()
    return striche.startswith("[") and striche[1:striche.find("]")].strip() != ""


def _linien(seite):
    """Waagerechte Striche (Linie oder flaches Rechteck) und senkrechte Kanten aller Zeichnungen."""
    import pymupdf
    waagerecht, senkrecht = [], []
    for zeichnung in seite.get_drawings():
        gestrichelt = _gestrichelt(zeichnung)
        for element in zeichnung["items"]:
            if element[0] == "l":
                r = pymupdf.Rect(element[1], element[2]).normalize()
            elif element[0] == "re":
                r = pymupdf.Rect(element[1]).normalize()
                if r.width > LINIE_MAX_DICKE and r.height > LINIE_MAX_DICKE:
                    if "s" in (zeichnung.get("type") or ""):        # Kastenrand: beide Seiten senkrecht
                        senkrecht += [pymupdf.Rect(r.x0, r.y0, r.x0, r.y1), pymupdf.Rect(r.x1, r.y0, r.x1, r.y1)]
                    continue
            else:
                continue
            if r.height <= LINIE_MAX_DICKE and r.width > r.height:
                if not gestrichelt:
                    waagerecht.append(r)
            elif r.width <= LINIE_MAX_DICKE:
                senkrecht.append(r)
    return waagerecht, senkrecht


def _abstand(a0, a1, wert) -> float:
    return 0.0 if a0 <= wert <= a1 else min(abs(a0 - wert), abs(a1 - wert))


def _auf_zellenrand(linie, zellen) -> bool:
    for z in zellen:
        if linie.x1 < z.x0 - RAND_TOLERANZ or linie.x0 > z.x1 + RAND_TOLERANZ:
            continue
        if min(_abstand(linie.y0, linie.y1, z.y0), _abstand(linie.y0, linie.y1, z.y1)) <= RAND_TOLERANZ:
            return True
    return False


def _an_senkrechter(linie, senkrecht) -> bool:
    """Ein Ende stößt an eine senkrechte Kante: Kasten- oder Rahmenlinie."""
    for k in senkrecht:
        if _abstand(k.y0 - RAND_TOLERANZ, k.y1 + RAND_TOLERANZ, linie.y0) > 0:
            continue
        mitte = (k.x0 + k.x1) / 2
        if min(abs(linie.x0 - mitte), abs(linie.x1 - mitte)) <= RAND_TOLERANZ:
            return True
    return False


def _ueberdeckt(r, vorhanden) -> bool:
    for q in vorhanden:
        schnitt = r & q
        if not schnitt.is_empty and schnitt.get_area() > 0.3 * min(r.get_area(), q.get_area()):
            return True
    return False


def _gezeichnete_zeilen(seite, zellen, vorhanden) -> list:
    """Felder über gezeichneten Schreiblinien, ohne Rahmen, Unterstreichungen und Doppelte."""
    import pymupdf
    waagerecht, senkrecht = _linien(seite)
    woerter = [pymupdf.Rect(w[:4]) for w in seite.get_text("words")]
    rechtecke = []
    for linie in sorted(waagerecht, key=lambda r: (r.y0, r.x0)):
        if linie.width < LINIE_MIN_LAENGE:
            continue
        if _auf_zellenrand(linie, zellen) or _an_senkrechter(linie, senkrecht):
            continue
        streifen = pymupdf.Rect(linie.x0, linie.y0 - 12, linie.x1, linie.y1 + 2)
        if any(w.intersects(streifen) for w in woerter):        # Unterstreichung, Trennlinie durch Text
            continue
        feld = pymupdf.Rect(linie.x0, linie.y0 - LINIE_FELD_HOEHE, linie.x1, linie.y0)
        if _ueberdeckt(feld, vorhanden + rechtecke):
            continue
        rechtecke.append(feld)
    return rechtecke


def formular_felder(pdf: Path) -> int:
    """Textfelder einsetzen und in place speichern; Zahl der Felder zurück (0: Datei unverändert)."""
    import pymupdf
    pdf = Path(pdf)
    dok = pymupdf.open(stream=pdf.read_bytes(), filetype="pdf")
    zahl = 0
    try:
        for nr_seite, seite in enumerate(dok, start=1):
            zellen = _zellen(seite)
            rechtecke = _schreibzeilen(seite) + _leere_zellen(seite, zellen)
            rechtecke += _gezeichnete_zeilen(seite, zellen, rechtecke)
            rechtecke.sort(key=lambda r: (round(r.y0), r.x0))
            for nr, r in enumerate(rechtecke, start=1):
                w = pymupdf.Widget()
                w.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
                w.field_name = f"feld_{nr_seite}_{nr}"
                w.rect = r
                w.text_font, w.text_fontsize = SCHRIFT, GROESSE
                if r.height >= MEHRZEILIG_AB:
                    w.field_flags |= pymupdf.PDF_TX_FIELD_IS_MULTILINE
                seite.add_widget(w)
                zahl += 1
        if zahl:
            daten = dok.tobytes(garbage=3, deflate=True)
    finally:
        dok.close()
    if zahl:
        pdf.write_bytes(daten)
    return zahl
