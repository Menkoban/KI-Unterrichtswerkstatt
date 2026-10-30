"""Beispiel-Themenkurs (fiktiv) bauen und prüfen.

    python3 beispiel.py [--ziel ausgabe/beispiel.mbz]

Legt neben der .mbz den Ordner `beispiel_dateien/` (Bilder, Simulation,
Druckvorlage) und `beispiel.json` an, baut die Sicherung und lässt die zehn
Prüfer laufen. Rückgabe 1, wenn ein Prüfer einen Fehler meldet.
"""
from __future__ import annotations

import json
import struct
import sys
import zipfile
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bauen  # noqa: E402
import pruefen  # noqa: E402

BLAU, GRUEN = (8, 52, 156), (125, 222, 120)
MEDAILLEN = [("Grün", (60, 170, 70), 1, 50), ("Bronze", (176, 116, 60), 50, 81),
             ("Silber", (170, 170, 175), 81, 92), ("Gold", (222, 180, 40), 92, None)]


def png(breite: int, hoehe: int, grund, kreis=None) -> bytes:
    """Einfaches PNG ohne Fremdbibliothek: Fläche, optional ein Kreis."""
    zeilen = bytearray()
    for y in range(hoehe):
        zeilen.append(0)
        for x_ in range(breite):
            farbe = grund
            if kreis and (x_ - breite / 2) ** 2 + (y - hoehe / 2) ** 2 < (min(breite, hoehe) / 2.4) ** 2:
                farbe = kreis
            zeilen += bytes(farbe)

    def block(art, daten):
        return (struct.pack(">I", len(daten)) + art + daten
                + struct.pack(">I", zlib.crc32(art + daten) & 0xFFFFFFFF))
    return (b"\x89PNG\r\n\x1a\n" + block(b"IHDR", struct.pack(">IIBBBBB", breite, hoehe, 8, 2, 0, 0, 0))
            + block(b"IDAT", zlib.compress(bytes(zeilen))) + block(b"IEND", b""))


def docx(pfad: Path, text: str) -> None:
    """Kleinste gültige Word-Datei (Platzhalter für eine Druckvorlage)."""
    w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    with zipfile.ZipFile(pfad, "w") as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
        z.writestr("_rels/.rels",
                   '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        z.writestr("word/document.xml", f'<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="{w}">'
                   f"<w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>")


SIMULATION = """<!doctype html><html lang="de"><head><meta charset="utf-8">
<title>Werte-Labor Leistung</title><style>body{font:16px sans-serif;color:#08349C;margin:16px}
input{width:100%}</style></head><body><h1>Werte-Labor: Leistung und Strom</h1>
<label for="p">Leistung des Geräts: <span id="pw">2000</span> W</label>
<input id="p" type="range" min="100" max="3500" step="50" value="2000">
<p>Strom bei 230 V: <strong id="i"></strong> A</p>
<script>const p=document.getElementById('p');function neu(){document.getElementById('pw').textContent=p.value;
document.getElementById('i').textContent=(p.value/230).toFixed(2).replace('.',',');}p.oninput=neu;neu();</script>
</body></html>"""


def dateien_anlegen(wurzel: Path) -> None:
    (wurzel / "bilder").mkdir(parents=True, exist_ok=True)
    (wurzel / "abzeichen").mkdir(exist_ok=True)
    (wurzel / "lehrkraft").mkdir(exist_ok=True)
    (wurzel / "bilder/haus_schuette.png").write_bytes(png(160, 100, (235, 240, 250), BLAU))
    (wurzel / "bilder/verteiler.png").write_bytes(png(200, 120, (245, 245, 245), GRUEN))
    (wurzel / "bilder/kurs.png").write_bytes(png(120, 80, BLAU, GRUEN))
    (wurzel / "werte_labor.html").write_text(SIMULATION, encoding="utf-8")
    for name, farbe, _, _ in MEDAILLEN:
        (wurzel / f"abzeichen/{dateiname(name)}.png").write_bytes(png(100, 100, (255, 255, 255), farbe))
    docx(wurzel / "lehrkraft/Anlage_1_Arbeitsblatt.docx", "Arbeitsblatt Leistung im Haus Schütte")
    docx(wurzel / "lehrkraft/Anlage_2_Messprotokoll.docx", "Messprotokoll Haus Schütte")


def dateiname(medaille: str) -> str:
    return medaille.lower().replace("ü", "ue")


def fragen() -> list[dict]:
    t = ["Schulform:BS", "Lernfeld:LF01", "Leitbegriff:Leistung", "Thema:Stromhof"]
    return [
        {"typ": "multichoice", "name": "F01 Leistung", "idnummer": "LS01-F01", "tags": t,
         "text": "<p>Der Wasserkocher von Frau Schütte hat 2000 W. Was gibt diese Angabe an?</p>",
         "antworten": [
             {"text": "die elektrische Leistung", "richtig": True, "feedback": "Richtig."},
             {"text": "die Spannung", "feedback": "Die Spannung wird in Volt angegeben."},
             {"text": "den Strom", "feedback": "Der Strom wird in Ampere angegeben."}]},
        {"typ": "truefalse", "name": "F02 Spannung", "idnummer": "LS01-F02", "tags": t,
         "text": "<p>Im Haus Schütte beträgt die Spannung an der Steckdose 230 V.</p>",
         "richtig": True, "feedback_falsch": "Im Niederspannungsnetz sind es 230 V."},
        {"typ": "shortanswer", "name": "F03 Einheit", "idnummer": "LS01-F03", "tags": t,
         "text": "<p>Nennen Sie die Einheit der elektrischen Leistung (Wort).</p>",
         "antworten": [{"text": "Watt", "anteil": 100}]},
        {"typ": "numerical", "name": "F04 Leistung rechnen", "idnummer": "LS01-F04", "tags": t,
         "text": "<p>Ein Gerät nimmt bei 230 V einen Strom von 10 A auf. Berechnen Sie die "
                 "Leistung in W.</p>", "antworten": [{"wert": 2300, "toleranz": 0}]},
        {"typ": "calculated", "name": "F05 Strom rechnen", "idnummer": "LS01-F05", "tags": t,
         "text": "<p>Ein Heizlüfter hat {P} W bei {U} V. Berechnen Sie den Strom in A.</p>",
         "formel": "{P}/{U}", "toleranz": 0.01, "nachkommastellen": 2, "plausibel": [0.1, 20],
         "variablen": [{"name": "P", "min": 500, "max": 3000},
                       {"name": "U", "min": 230, "max": 230}]},
        {"typ": "match", "name": "F06 Größen", "idnummer": "LS01-F06", "tags": t,
         "text": "<p>Ordnen Sie jeder Größe ihre Einheit zu.</p>",
         "paare": [{"frage": "Spannung", "antwort": "V"}, {"frage": "Strom", "antwort": "A"},
                   {"frage": "Leistung", "antwort": "W"}], "ablenker": ["Hz"]},
        {"typ": "ddwtos", "name": "F07 Lückentext", "idnummer": "LS01-F07", "tags": t,
         "text": "<p>Die Leistung ist das Produkt aus [[1]] und [[2]].</p>",
         "woerter": [{"text": "Spannung"}, {"text": "Strom"}, {"text": "Widerstand"}]},
        {"typ": "gapselect", "name": "F08 Auswahl", "idnummer": "LS01-F08", "tags": t,
         "text": "<p>Bei gleicher Spannung braucht ein Gerät mit mehr Leistung [[1]] Strom.</p>",
         "auswahl": [{"text": "mehr"}, {"text": "weniger"}]},
        {"typ": "ordering", "name": "F09 Sicherheitsregeln", "idnummer": "LS01-F09", "tags": t,
         "text": "<p>Bringen Sie die fünf Sicherheitsregeln in die richtige Reihenfolge.</p>",
         "elemente": ["Freischalten", "Gegen Wiedereinschalten sichern",
                      "Spannungsfreiheit feststellen", "Erden und kurzschließen",
                      "Benachbarte, unter Spannung stehende Teile abdecken"]},
        {"typ": "ddmarker", "name": "F10 Verteiler", "idnummer": "LS01-F10", "tags": t,
         "text": "<p>Markieren Sie im Bild den Fehlerstrom-Schutzschalter.</p>",
         "bild": "bilder/verteiler.png", "markierungen": [{"text": "RCD"}],
         "zonen": [{"form": "circle", "koordinaten": "100,60;30", "markierung": 1}]},
        {"typ": "ddimageortext", "name": "F11 Haus", "idnummer": "LS01-F11", "tags": t,
         "text": "<p>Ziehen Sie die Begriffe an die richtige Stelle im Haus.</p>",
         "bild": "bilder/haus_schuette.png",
         "ziehobjekte": [{"text": "Zählerschrank"}, {"text": "Küche"}],
         "zonen": [{"x": 20, "y": 20, "objekt": 1}, {"x": 100, "y": 60, "objekt": 2}]},
    ]


def kursdefinition() -> dict:
    medaillen = [{"typ": "page", "name": f"Ihre Medaille: {n}", "medaille": n,
                  "inhalt": f"<p>Herzlichen Glückwunsch zur Medaille {n}.</p>"
                            f'<p><img src="{dateiname(n)}.png" alt="Medaille {n}"></p>',
                  "dateien": [f"abzeichen/{dateiname(n)}.png"],
                  "voraussetzung": {"aktivitaet": "Abschlusstest", "min": lo,
                                    **({"max": hi} if hi else {})}}
                 for n, _, lo, hi in MEDAILLEN]
    return {
        "kurs": {"vollname": "EG1 · LF 1 · LS 1 Der Stromhof und das Haus Schütte",
                 "kurzname": "EG1-LF01-LS01", "format": "tiles", "abschlussverfolgung": True,
                 "ki_hinweis": "Erstellt von Alex Muster mit Hilfe von künstlicher Intelligenz",
                 "beschreibung": "<p>Familie Schütte lässt ihr Haus am Stromhof modernisieren. "
                                 "Sie planen mit Brinkmann Automation die Elektroinstallation.</p>",
                 "kursbild": "bilder/kurs.png"},
        "gruppen": ["Team A", "Team B", "Team C", "Team D"],
        "abschnitte": [
            {"name": "1 · Einstieg: Der Auftrag im Haus Schütte", "sichtbar": True,
             "zusammenfassung": "<p>Worum es geht: Familie Schütte meldet ein Problem. Sie "
                                "schätzen zuerst sich selbst ein.</p>",
             "aktivitaeten": [
                 {"typ": "page", "name": "Handlungssituation: Haus Schütte", "tags": ["Einstieg"],
                  "inhalt": '<p>Frau Schütte ruft an: „Wenn Wasserkocher und Heizlüfter laufen, '
                            'fliegt die Sicherung.“</p><p><img src="haus_schuette.png" '
                            'alt="Skizze des Hauses Schütte mit Küche und Zählerschrank"></p>'
                            "<p>Schätzen Sie danach in der „Selbsteinschätzung vorher“ ein, "
                            "was Sie schon können.</p>",
                  "dateien": ["bilder/haus_schuette.png"]},
                 {"typ": "feedback", "name": "Selbsteinschätzung vorher", "anonym": False,
                  "tags": ["Selbsteinschätzung"],
                  "elemente": [{"typ": "likert", "frage": "Ich kann die Leistung eines Geräts berechnen."},
                               {"typ": "likert", "frage": "Ich kann erklären, warum eine Sicherung auslöst."},
                               {"typ": "text", "frage": "Das möchte ich klären …"}]},
                 {"typ": "url", "name": "Erklärvideo: Elektrische Leistung", "anzeige": "neues_fenster",
                  "adresse": "https://www.example.org/video/leistung", "tags": ["Video"]},
                 # Abgabe des Einstiegs (Prüfer 8): zählt nicht für Sterne und Medaille
                 {"typ": "quiz", "name": "Eingangstest: Was wissen Sie schon?", "sterne": 0, "versuche": 1,
                  "abschluss": "note", "tags": ["Eingangstest"],
                  "fragen": [{"typ": "truefalse", "name": "Eingang 1", "richtig": False,
                              "text": "<p>Eine Sicherung schützt vor allem das Gerät.</p>"}]}]},
            {"name": "2 · Erarbeitung: Leistung und Strom", "sichtbar": False,
             "zusammenfassung": "<p>Sie informieren sich, probieren im Werte-Labor aus und "
                                "geben im Team ein Messprotokoll ab.</p>",
             "aktivitaeten": [
                 {"typ": "page", "name": "Infoblatt: Leistung im Haushalt", "tags": ["Infoblatt"],
                  "inhalt": "<h3>1 Leistung</h3><p>Die Leistung P ist das Produkt aus Spannung U "
                            'und Strom I.</p><p><img src="verteiler.png" alt="Abb. 1: '
                            'Stromkreisverteiler (eigene Darstellung)"></p>',
                  "dateien": ["bilder/verteiler.png"]},
                 {"typ": "resource", "name": "Simulation: Werte-Labor", "datei": "werte_labor.html",
                  "tags": ["Simulation"]},
                 {"typ": "label", "name": "Hinweis Teamarbeit",
                  "text": "<p>Arbeiten Sie im Team. Eine Person lädt das Ergebnis hoch.</p>"},
                 {"typ": "assign", "name": "Auftrag: Messprotokoll Haus Schütte",
                  "beschreibung": "<p>Laden Sie Ihr ausgefülltes Messprotokoll als Foto oder Datei hoch.</p>",
                  "abgabe": ["datei"], "gruppenabgabe": True, "tags": ["Auftrag"],
                  "bewertungsraster": [
                      {"kriterium": "Messwerte", "beschreibung": "vollständig und mit Einheit", "punkte": 6},
                      {"kriterium": "Rechnung", "beschreibung": "Leistung richtig berechnet", "punkte": 4}]},
                 {"typ": "data", "name": "Gerätesammlung Haus Schütte", "tags": ["Datenbank"],
                  "beschreibung": "<p>Tragen Sie jedes Gerät, das Sie im Haus Schütte finden, mit "
                                  "seiner Leistung ein. Die Einträge aller Teams stehen in einer "
                                  "Tabelle.</p>",
                  "felder": [{"name": "Gerät", "typ": "text", "pflicht": True,
                              "beschreibung": "z. B. Wasserkocher in der Küche"},
                             {"name": "Leistung in W", "typ": "number", "pflicht": True,
                              "beschreibung": "vom Typenschild"},
                             {"name": "Bemerkung", "typ": "textarea"}],
                  "abschluss": "eintraege", "eintraege_fuer_abschluss": 1},
                 {"typ": "assign", "name": "Auftrag: Skizze Zählerschrank", "bewertung": "keine",
                  "beschreibung": "<p>Laden Sie ein Foto Ihrer Skizze des Zählerschranks hoch.</p>",
                  "abgabe": ["datei"], "gruppenabgabe": True, "abschluss": "abgabe",
                  "tags": ["Auftrag"]}]},
            {"name": "3 · Rückblick", "sichtbar": False,
             "zusammenfassung": "<p>Sie prüfen Ihr Wissen im Abschlusstest. Holen Sie hier Ihre "
                                "Medaille ab.</p>",
             "aktivitaeten": [
                 {"typ": "page", "name": "So geht der Abschlusstest",
                  "inhalt": "<p>Der „Abschlusstest“ hat genau einen Versuch. Danach sehen Sie "
                            "Ihre Medaille. Begriffe stehen im „Glossar Stromhof“.</p>"},
                 {"typ": "quiz", "name": "Abschlusstest", "versuche": 1, "punkte": 10,
                  "bestehensgrenze_prozent": 50, "vollbild": True, "glossar_aus": True,
                  "abschluss": "bestanden_oder_versuche", "tags": ["Abschlusstest"],
                  "beschreibung": "<p>Sie haben einen Versuch.</p>", "fragen": fragen()},
                 {"typ": "glossary", "name": "Glossar Stromhof", "kategorien":
                  ["Begriffe", "Unsere Musterlösungen"], "freigabe_noetig": True,
                  "eintraege": [
                      {"begriff": "Leistung", "kategorie": "Begriffe",
                       "definition": "<p>Wie viel Energie ein Gerät je Sekunde umsetzt (Watt).</p>"},
                      {"begriff": "Fehlerstrom-Schutzschalter", "kategorie": "Begriffe",
                       "definition": "<p>Schaltet ab, wenn Strom über einen falschen Weg fließt.</p>",
                       "bild": "bilder/verteiler.png", "bild_alt": "Verteiler mit RCD"}]},
                 *medaillen]},
            {"name": "Material für Lehrkräfte", "lehrkraft": True, "sichtbar": False,
             "aktivitaeten": [
                 {"typ": "folder", "name": "Druckvorlagen LS 1",
                  "dateien": ["lehrkraft/Anlage_1_Arbeitsblatt.docx",
                              "lehrkraft/Anlage_2_Messprotokoll.docx"]},
                 {"typ": "page", "name": "Erwartungshorizont Messprotokoll", "markierungen": ["loesung"],
                  "sichtbar": False, "inhalt": "<p>P = 230 V · 10 A = 2300 W</p>"}]},
        ],
        "abzeichen": [{"name": f"Medaille {n}: LS 1 Der Stromhof",
                       "beschreibung": f"Medaille {n} im Themenkurs LS 1 Der Stromhof und das Haus Schütte.",
                       "bild": f"abzeichen/{dateiname(n)}.png", "aktivitaet": f"Ihre Medaille: {n}"}
                      for n, _, _, _ in MEDAILLEN],
    }


def main(ziel: Path) -> int:
    wurzel = ziel.parent / "beispiel_dateien"
    dateien_anlegen(wurzel)
    kurs = kursdefinition()
    (ziel.parent / "beispiel.json").write_text(json.dumps(kurs, ensure_ascii=False, indent=1),
                                               encoding="utf-8")
    bauen.baue(kurs, wurzel, ziel)
    befunde = pruefen.pruefe(ziel, kurs)
    print(f"Gebaut: {ziel}\n" + pruefen.bericht(befunde))
    return 1 if any(b.stufe == pruefen.FEHLER for b in befunde) else 0


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ziel", type=Path, default=Path("ausgabe/beispiel.mbz"))
    sys.exit(main(ap.parse_args().ziel.resolve()))
