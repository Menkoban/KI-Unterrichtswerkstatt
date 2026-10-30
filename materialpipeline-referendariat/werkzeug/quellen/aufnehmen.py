"""Quellen aufnehmen (Fahrplan Schritt 3, Lehrkraft 2026-10-15): Foto, Scan oder PDF aus dem Chat ablegen,
durchsuchbar machen (Texterkennung) und in die Quellenkarte eintragen.

    python3 werkzeug/quellen/aufnehmen.py DATEI [DATEI …] --art fachbuch --werk "Europa Tabellenbuch Elektrotechnik"
            --auflage "30. Aufl. 2024" --seite 112 --thema "Schaltzeichen Schütze" --rechte "nur intern"

Ablage:  quellen/<art>/<werk-kürzel>/<werk-kürzel>_S<seite>_<prüfsumme>.<endung>  (+ .txt mit erkanntem Text)
Karte:   quellen/_karte/karte.csv (maschinell) und karte.md (Übersicht zum Lesen)

Regeln: Dateien über 100 MB werden nicht aufgenommen (vorher teilen, CLAUDE.md); doppelte Dateien (gleiche
Prüfsumme) werden erkannt und nicht erneut abgelegt; Fotos vom Tablet (HEIC) werden als JPG abgelegt.
Quellen bleiben im privaten Repo; in eine teilbare Fassung (E11) gehen sie nie.
"""
import argparse
import csv
import datetime
import hashlib
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ARTEN = {"fachbuch": "fachbuecher", "norm": "normen_vorschriften", "hersteller": "hersteller",
         "material": "materialpool"}
SPALTEN = ["id", "datei", "art", "werk", "auflage", "seite", "thema", "rechte", "aufgenommen", "zeichen", "hinweis"]
MAX_MB = 100


def kuerzel(text):
    t = text.lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        t = t.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:40] or "unbekannt"


def pruefsumme(pfad):
    h = hashlib.sha256()
    with open(pfad, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()[:10]


def ocr_bild(pfad):
    e = subprocess.run(["tesseract", str(pfad), "-", "-l", "deu+eng", "--psm", "3"], capture_output=True, text=True)
    if e.returncode:
        raise RuntimeError("Texterkennung fehlgeschlagen: " + e.stderr.strip()[-300:])
    return e.stdout


def text_aus_pdf(pfad):
    """Textschicht des PDF; Seiten ohne Text werden gerendert (300 dpi) und erkannt."""
    import pymupdf as fitz
    teile = []
    with fitz.open(pfad) as doc, tempfile.TemporaryDirectory() as tmp:
        for i, seite in enumerate(doc, 1):
            t = seite.get_text().strip()
            if len(t) < 40:
                bild = Path(tmp) / f"s{i}.png"
                seite.get_pixmap(dpi=300).save(bild)
                t = ocr_bild(bild).strip()
            teile.append(f"--- PDF-Seite {i} ---\n{t}")
    return "\n".join(teile)


def heic_zu_jpg(pfad, ziel):
    from PIL import Image
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
    except ImportError as e:
        raise RuntimeError("HEIC-Foto: pillow-heif fehlt (werkzeug/einrichten.sh ausführen)") from e
    Image.open(pfad).convert("RGB").save(ziel, "JPEG", quality=92)


def eigene_quellen():
    """Ablage der eigenen Quellen: Quellen/ im persönlichen Arbeitsbereich (Aufteilung 2026-10-19)."""
    import sys
    sys.path.insert(0, str(REPO / "werkzeug"))
    import arbeitsbereich
    return arbeitsbereich.quellen()


def karte_lesen(wurzel):
    datei = wurzel / "_karte" / "karte.csv"
    if not datei.exists():
        return []
    with open(datei, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter=";"))


def karte_schreiben(wurzel, eintraege):
    (wurzel / "_karte").mkdir(parents=True, exist_ok=True)
    with open(wurzel / "_karte" / "karte.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=SPALTEN, delimiter=";")
        w.writeheader()
        w.writerows(eintraege)
    md = ["# Quellenkarte", "", "Automatisch erzeugt von werkzeug/quellen/aufnehmen.py. Suche: "
          "`python3 werkzeug/quellen/suche.py BEGRIFF`.", "",
          "| Werk | Auflage | Seite | Thema | Art | Rechte | Datei |", "|---|---|---|---|---|---|---|"]
    for e in sorted(eintraege, key=lambda e: (e["werk"], e["seite"])):
        md.append(f"| {e['werk']} | {e['auflage']} | {e['seite']} | {e['thema']} | {e['art']} | {e['rechte']} | "
                  f"{e['datei']} |")
    (wurzel / "_karte" / "karte.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def aufnehmen(pfad, art, werk, auflage="", seite="", thema="", rechte="nur intern", wurzel=None):
    """Rückgabe: (Eintrag, Meldung). Wirft ValueError bei zu großen oder unbekannten Dateien."""
    pfad = Path(pfad)
    if art not in ARTEN:
        raise ValueError(f"Art {art!r} unbekannt (erlaubt: {', '.join(ARTEN)})")
    if pfad.stat().st_size > MAX_MB * 1024 * 1024:
        raise ValueError(f"{pfad.name} ist größer als {MAX_MB} MB: bitte vorher teilen")
    endung = pfad.suffix.lower()
    if endung not in (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".pdf", ".heic"):
        raise ValueError(f"{pfad.name}: Dateiart {endung} wird nicht aufgenommen")
    kopf = pfad.read_bytes()[:16]
    if endung == ".pdf" and not kopf.startswith(b"%PDF"):
        raise ValueError(f"{pfad.name} ist kein PDF (Inhalt beginnt nicht mit %PDF, z. B. eine Webseite statt der Datei)")
    if endung != ".pdf" and kopf.lstrip().lower().startswith((b"<!doctype", b"<html")):
        raise ValueError(f"{pfad.name} ist eine Webseite, kein Bild")
    pid = pruefsumme(pfad)
    wurzel = wurzel or eigene_quellen()
    eintraege = karte_lesen(wurzel)
    if any(e["id"] == pid for e in eintraege):
        alt = next(e for e in eintraege if e["id"] == pid)
        return alt, f"schon vorhanden: {alt['datei']}"
    kz = kuerzel(werk)
    ordner = wurzel / ARTEN[art] / kz
    ordner.mkdir(parents=True, exist_ok=True)
    name = f"{kz}_S{kuerzel(str(seite)) if seite else 'x'}_{pid}"
    if endung == ".heic":
        ziel = ordner / f"{name}.jpg"
        heic_zu_jpg(pfad, ziel)
    else:
        ziel = ordner / f"{name}{'.jpg' if endung == '.jpeg' else endung}"
        shutil.copyfile(pfad, ziel)
    text = text_aus_pdf(ziel) if ziel.suffix == ".pdf" else ocr_bild(ziel)
    ziel.with_suffix(".txt").write_text(text, encoding="utf-8")
    hinweis = []
    if not seite:
        hinweis.append("Seite unbekannt")
    if not auflage:
        hinweis.append("Auflage unbekannt")
    if len(text.strip()) < 40:
        hinweis.append("kaum Text erkannt (Foto schärfer/heller?)")
    zeichen = [c for c in text if not c.isspace()]
    latein = sum(c.isascii() or c in "äöüÄÖÜß°±µΩ" for c in zeichen)
    if zeichen and latein / len(zeichen) < 0.8:                  # z. B. Datenblatt in Chinesisch statt Deutsch
        hinweis.append("Text überwiegend nicht in Deutsch oder Englisch (Sprachfassung prüfen)")
    eintrag = dict(id=pid, datei=str(ziel.relative_to(wurzel)), art=art, werk=werk, auflage=auflage, seite=str(seite),
                   thema=thema, rechte=rechte, aufgenommen=datetime.date.today().isoformat(),
                   zeichen=str(len(text.strip())), hinweis=", ".join(hinweis))
    karte_schreiben(wurzel, eintraege + [eintrag])
    return eintrag, "aufgenommen" + (f" ({eintrag['hinweis']})" if hinweis else "")


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    a.add_argument("dateien", nargs="+")
    a.add_argument("--art", required=True, choices=list(ARTEN))
    a.add_argument("--werk", required=True)
    a.add_argument("--auflage", default="")
    a.add_argument("--seite", default="")
    a.add_argument("--thema", default="")
    a.add_argument("--rechte", default="nur intern")
    a.add_argument("--wurzel", default=None, help="nur für Tests (sonst Quellen/ im Arbeitsbereich)")
    arg = a.parse_args()
    for d in arg.dateien:
        e, m = aufnehmen(d, arg.art, arg.werk, arg.auflage, arg.seite, arg.thema, arg.rechte, Path(arg.wurzel) if arg.wurzel else None)
        print(f"{Path(d).name}: {m} → {e['datei']} ({e['zeichen']} Zeichen erkannt)")
