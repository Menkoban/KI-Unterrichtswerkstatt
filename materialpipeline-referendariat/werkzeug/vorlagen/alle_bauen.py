"""Baut alle abgenommenen Vorlagen, Muster und Vorschauen neu und prüft sie.

Aufruf: python werkzeug/vorlagen/alle_bauen.py
1. Startet jedes Vorlagen-Skript (Vorlage → Muster mit DS-7-Inhalt → PNG-Vorschau).
2. Ordnet in allen DOCX die XML-Eigenschaften so, wie Word es verlangt (LibreOffice ist nachsichtiger).
3. Prüft die Muster nach den automatischen Punkten der Prüf-Checkliste (docs/regeln/pruefcheckliste.md).
"""
import re
import subprocess
import sys
import zipfile
from pathlib import Path

HIER = Path(__file__).resolve().parent
WURZEL = HIER.parents[1]
sys.path.insert(0, str(HIER))
from messprotokoll import REIHENFOLGE, schema_ordnen  # noqa: E402

SKRIPTE = ["arbeitsblatt", "hilfekarten", "erwartungshorizont", "selbstkontrolle", "einstieg", "infoblatt",
           "karte_a5", "messprotokoll", "servicebericht", "serviceauftrag", "tafelbild", "folien"]
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def reihenfolge_fehler(pfad):
    from docx import Document
    doc = Document(pfad)
    fehler = 0
    for part in doc.part.package.iter_parts():
        el = getattr(part, "_element", None)
        if el is None:
            continue
        for tag, folge in REIHENFOLGE.items():
            rang = {W + n: i for i, n in enumerate(folge.split())}
            for knoten in el.iter(W + tag):
                r = [rang.get(k.tag, 999) for k in knoten]
                fehler += r != sorted(r) or len({k.tag for k in knoten}) != len(r)
    return fehler


def offene_platzhalter(pfad):
    with zipfile.ZipFile(pfad) as z:
        text = " ".join(z.read(n).decode("utf-8", "ignore") for n in z.namelist() if n.endswith(".xml"))
    return re.findall(r"\{\{[^}]*\}\}|\{%[^%]*%\}", re.sub(r"<[^>]+>", "", text))


WARNWOERTER = ["gegeben:", "gesucht:", "rechnerisch und messtechnisch", "berechnen sie zuerst", "gehen sie so vor"]
OHNE_WOZU = ("einstieg", "serviceauftrag", "schneidekarten", "folien")   # Schneidekarten: Stimm-, Bild-, Rollenkarten
SEITEN = {"arbeitsblatt": 1, "hilfekarten": 1, "erwartungshorizont": 1, "selbstkontrolle": 1, "einstieg": 2,
          "infoblatt": 1, "datenblatt": 1, "karte_a5": 3, "messprotokoll": 2, "servicebericht": 1,
          "serviceauftrag": 2, "tafelbild": 1}  # erwarteter Umfang der Muster (S1: kein Überlauf)  # Handlungssituation: Ausnahme (Lehrkraft 2026-10-13)


def text(pfad):
    with zipfile.ZipFile(pfad) as z:
        roh = " ".join(z.read(n).decode("utf-8", "ignore") for n in z.namelist()
                       if n.startswith(("word/", "ppt/slides/", "ppt/notesSlides/")) and n.endswith(".xml"))
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", roh))


def pruefen(pfad, art=None):
    """Automatische Prüfpunkte der Checkliste (docs/regeln/pruefcheckliste.md) für ein fertiges Dokument.

    Gestaltung nach schule.STIL: neutral für Muster, nach schule.persoenlich() wie im Lehrkraft-Profil.
    art: Materialart (z. B. "infoblatt"); ohne Angabe aus dem Namen Muster_<art>.docx.
    """
    import material_bausteine as mb
    import schule as s
    t, tl = text(pfad), text(pfad).lower()
    art = art or pfad.stem.removeprefix("Muster_")
    befunde = []
    if pfad.suffix == ".docx" and offene_platzhalter(pfad):
        befunde.append("A1 offene Platzhalter")
    if "ki-gestützt" not in tl:
        befunde.append("A3 KI-Fußnote fehlt")
    ohne_wozu = OHNE_WOZU + (() if s.STIL["infoblatt_wozu"] else ("infoblatt",))
    if art not in ohne_wozu and "wozu?" not in tl:
        befunde.append("A6 Wozu-Zeile fehlt")
    if s.STIL["keine_gedankenstriche"]:
        for stelle in mb.gedankenstriche(pfad):
            befunde.append(f"Gedankenstrich (Profil): „…{stelle}…“")
    for w in WARNWOERTER:
        if w in tl:
            befunde.append(f"A7/A8 Warnwort „{w}“")
    soll = SEITEN.get(art) if pfad.stem.startswith("Muster_") else None   # nur für Muster mit Vorschau
    ist = len(list(pfad.parent.glob(f"vorschau_{art}-*.png")))
    if soll and ist != soll:
        befunde.append(f"S1 {ist} statt {soll} Seite(n)")
    if ("brinkmann" in tl or "nordland" in tl) and "fiktiv" not in tl:
        befunde.append("A10 Kennzeichnung fiktiv fehlt")
    return befunde


def main():
    for name in SKRIPTE:
        print(f"· {name}")
        subprocess.run([sys.executable, str(HIER / f"{name}.py")], check=True, cwd=WURZEL)
    dateien = sorted((WURZEL / "vorlagen").glob("Vorlage_*.docx")) + \
        sorted((WURZEL / "docs/stilreferenz/vorlagen/muster").glob("Muster_*.docx"))
    probleme = 0
    for d in dateien:
        schema_ordnen(d)
        f = reihenfolge_fehler(d)
        befunde = pruefen(d) if d.name.startswith("Muster_") else []
        if f:
            befunde.append(f"A2 Reihenfolge ({f} Stellen)")
        if befunde:
            probleme += 1
            print(f"BEFUND {d.name}: " + "; ".join(befunde))
    print(f"{len(dateien)} DOCX geprüft, {probleme} mit Problemen")
    return probleme


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
