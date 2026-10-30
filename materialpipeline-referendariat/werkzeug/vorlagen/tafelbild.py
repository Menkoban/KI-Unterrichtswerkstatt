"""Vorlage Tafelbild-Plan (A4 quer): was wann wohin an Tafel oder Whiteboard kommt.

Schmaler Kopf (Farbstreifen, „LF · LS · DS · Tafelbild-Plan“, Leitfrage groß, Logo), Wozu, Tafel mit grauem
Rahmen in drei Feldern (links Problem, Mitte Erarbeitung/Sicherung mit Leitfrage, rechts Begriffe/Merkbild),
Legende der Phasen und Farben, Fuß.

Felder als Schleifen: `links`, `mitte`, `rechts` sind Listen von Einträgen mit
  phase (1 … 9, Nummer im blauen Kreis), text (str oder RichText für farbige Teile),
  art ("magnet" = angeheftetes Blatt, sonst Tafelanschrieb), farbe (Hex, ganze Zeile),
  platzhalter (Text im gestrichelten Feld; leer = kein Feld), hoehe (Feldhöhe in cm).

Aufruf: python werkzeug/vorlagen/tafelbild.py
Erzeugt vorlagen/Vorlage_tafelbild.docx, docs/stilreferenz/vorlagen/muster/Muster_tafelbild.docx
und die Vorschau vorschau_tafelbild-N.png.
"""
import sys
from pathlib import Path

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docxtpl import RichText

sys.path.insert(0, str(Path(__file__).parent))
import schule as s  # noqa: E402
import messprotokoll as mp  # noqa: E402  gemeinsame Bausteine
from vorlagen_bauen import rahmen, schattieren, tabelle_ohne_rahmen  # noqa: E402

TAFEL_RAND, TAFEL_FLAECHE, TRENNER = "7B8794", "FBFCFD", "C9CED6"
KREISE = "❶❷❸❹❺❻❼❽❾"
RGB_FELD = RGBColor.from_string("7B8794")
TAFEL_HOEHE = 14.8


def kreis(p, ausdruck, groesse=16):
    """Phasennummer als weiße Ziffer im blauen Kreis (Zeichen ❶ …)."""
    r = s.lauf(p, "{{ '%s'[%s - 1] if %s else '' }}" % (KREISE, ausdruck, ausdruck), groesse, farbe=s.RGB_BLAU)
    r.font.name = "Segoe UI Symbol"
    r._r.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Segoe UI Symbol")
    r._r.rPr.rFonts.set(qn("w:cs"), "Segoe UI Symbol")
    return r


def farbe_jinja(r, ausdruck):
    """Schriftfarbe aus einem Jinja-Ausdruck (z. B. e.farbe)."""
    r.font.color.rgb = s.RGB_DUNKEL
    r._r.rPr.find(qn("w:color")).set(qn("w:val"), "{{ %s }}" % ausdruck)
    return r


def steuer(zelle, tag):
    p = s.abstand(zelle.add_paragraph())
    s.lauf(p, tag, 7)
    return p


def feldname(zelle, text, vor=0):
    p = s.abstand(mp.absatz_in(zelle), vor, 6)
    r = s.kapitaelchen(s.lauf(p, text, 7.5, farbe=RGB_FELD))
    mp.gesperrt(r, 24)
    return p


def eintraege(zelle, liste, breite):
    """Schleife über die Einträge eines Tafelfelds."""
    steuer(zelle, "{%%p for e in (%s or []) %%}" % liste)
    steuer(zelle, "{%p if e.art == 'magnet' %}")
    p = s.abstand(zelle.add_paragraph(), 0, 10)
    kreis(p, "e.phase")
    s.lauf(p, " ", 10)
    r = s.lauf(p, " {{ e.text }} ", 9.5, farbe=s.RGB_DUNKEL)
    shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), "FFF4D6")
    r._r.get_or_add_rPr().append(shd)
    bdr = OxmlElement("w:bdr"); bdr.set(qn("w:val"), "single"); bdr.set(qn("w:sz"), "4"); bdr.set(qn("w:space"), "0")
    bdr.set(qn("w:color"), "E0B84A")
    r._r.rPr.insert(0, bdr)
    # Tafelanschrieb: Text als str (eine Farbe, e.farbe) oder RichText (mehrfarbig, {{r … }})
    for zweig, tag in (("{%p elif e.text is string %}", "{{ e.text }}"), ("{%p else %}", "{{r e.text }}")):
        steuer(zelle, zweig)
        p = s.abstand(zelle.add_paragraph(), 0, 3, 1.15)
        kreis(p, "e.phase")
        s.lauf(p, " ", 13)
        r = s.lauf(p, tag, 14)
        if tag == "{{ e.text }}":
            farbe_jinja(r, "e.farbe or '1B1F24'")
    steuer(zelle, "{%p endif %}")
    steuer(zelle, "{%p if e.platzhalter %}")
    t = zelle.add_table(1, 1)
    c = t.cell(0, 0)
    tcPr = c._tc.get_or_add_tcPr()
    b = OxmlElement("w:tcBorders")
    for seite in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{seite}")
        el.set(qn("w:val"), "dashed"); el.set(qn("w:sz"), "8"); el.set(qn("w:color"), "9AA3AD")
        b.append(el)
    tcPr.append(b)
    s.zellabstand(c, 0.15, 0.1, 0.18, 0.18)
    s.lauf(s.abstand(c.paragraphs[0]), "{{ e.platzhalter }}", 9, farbe=RGB_FELD)
    s.zeilenhoehe(t.rows[0], 3.0)
    t.rows[0]._tr.trPr.find(qn("w:trHeight")).set(qn("w:val"), "{{ ((e.hoehe or 3) * 567)|int }}")
    s.feste_breiten(t, [breite])
    p = s.abstand(zelle.add_paragraph(), 0, 0)
    p.paragraph_format.line_spacing = Pt(10)
    steuer(zelle, "{%p endif %}")
    steuer(zelle, "{%p endfor %}")


def kopfblock(doc, b):
    t = doc.add_table(2, 3)
    tabelle_ohne_rahmen(t)
    schattieren(t.cell(0, 0), s.BLAU)
    schattieren(t.cell(1, 0), s.GRUEN)
    for z in (t.cell(0, 0), t.cell(1, 0)):
        s.zellabstand(z, 0, 0, 0, 0)
        mp.knapp(z.paragraphs[0])
    s.zeilenhoehe(t.rows[0], 0.85, genau=False)
    s.zeilenhoehe(t.rows[1], 0.45, genau=False)
    text = t.cell(0, 1).merge(t.cell(1, 1))
    s.zellabstand(text, 0, 0, 0.3, 0)
    s.senkrecht(text, "center")
    p = s.abstand(text.paragraphs[0])
    s.lauf(p, "LF {{ lf }} · LS {{ ls }} · DS {{ ds }}  ·  Tafelbild-Plan", 9, farbe=mp.RGB_LABEL)
    p = s.abstand(text.add_paragraph(), 0, 0, 1.0)
    s.lauf(p, "{{ leitfrage }}", 17, fett=True, farbe=s.RGB_DUNKEL)
    logo = t.cell(0, 2).merge(t.cell(1, 2))
    s.senkrecht(logo, "center")
    s.zellabstand(logo, 0, 0, 0, 0)
    p = s.abstand(logo.paragraphs[0])
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p.add_run().add_picture(str(s.LOGO), width=Cm(2.6))
    s.feste_breiten(t, [0.25, b - 3.25, 3.0])


def fuss(doc, b):
    f = doc.sections[0].footer
    f.paragraphs[0].text = ""
    t = f.add_table(1, 2, Cm(b))
    tabelle_ohne_rahmen(t)
    li, re = t.rows[0].cells
    for z in (li, re):
        rahmen(z, top=(4, TRENNER))
        s.zellabstand(z, 0.06, 0, 0, 0)
    s.lauf(s.abstand(li.paragraphs[0]), mp.fusstext(), 7, farbe=s.RGB_GRAU)
    p = s.abstand(re.paragraphs[0])
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    s.lauf(p, "{{ ki_hinweis }}", 7, farbe=s.RGB_GRAU, kursiv=True)
    s.feste_breiten(t, [b * 0.5, b * 0.5])


def vorlage(pfad):
    doc = s.dokument("A4quer")
    b = s.nutzbreite(doc)
    fuss(doc, b)
    kopfblock(doc, b)
    s.wozu(doc, linie=False)

    # Tafel: drei Felder 1 : 1,35 : 1
    anteile = (1, 1.35, 1)
    breiten = [b * a / sum(anteile) for a in anteile]
    t = doc.add_table(1, 3)
    s.zeilenhoehe(t.rows[0], TAFEL_HOEHE)
    dick = (60, TAFEL_RAND)
    zellen = t.rows[0].cells
    for i, c in enumerate(zellen):
        tcPr = c._tc.get_or_add_tcPr()
        bo = OxmlElement("w:tcBorders")
        for seite in ("top", "left", "bottom", "right"):
            el = OxmlElement(f"w:{seite}")
            aussen = seite in ("top", "bottom") or (seite == "left" and i == 0) or (seite == "right" and i == 2)
            if aussen:
                el.set(qn("w:val"), "single"); el.set(qn("w:sz"), str(dick[0])); el.set(qn("w:color"), dick[1])
            else:
                el.set(qn("w:val"), "dashed"); el.set(qn("w:sz"), "12"); el.set(qn("w:color"), TRENNER)
            bo.append(el)
        tcPr.append(bo)
        schattieren(c, TAFEL_FLAECHE)
        s.zellabstand(c, 0.3, 0.2, 0.4, 0.4)
        s.senkrecht(c, "top")
    innen = [w - 0.8 for w in breiten]
    links, mitte, rechts = zellen
    feldname(links, "{{ feld_links or 'links · Problem' }}")
    eintraege(links, "links", innen[0])
    p = s.abstand(mp.absatz_in(mitte), 0, 4)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = s.lauf(p, "{{ leitfrage }}", 16, fett=True, farbe=s.RGB_DUNKEL)
    r.underline = True
    feldname(mitte, "{{ feld_mitte or 'Mitte · Erarbeitung und Sicherung' }}")
    eintraege(mitte, "mitte", innen[1])
    feldname(rechts, "{{ feld_rechts or 'rechts · Fachbegriffe und Merkbild' }}")
    eintraege(rechts, "rechts", innen[2])
    s.feste_breiten(t, breiten)

    # Legende
    p = s.abstand(doc.add_paragraph(), 6, 0)
    s.lauf(p, "{% for ph in (phasen or []) %}", 9)
    r = s.lauf(p, "{{ '%s'[loop.index0] }}" % KREISE, 14, farbe=s.RGB_BLAU)
    r.font.name = "Segoe UI Symbol"
    s.lauf(p, " {{ ph }}      ", 9, farbe=mp.RGB_LABEL)
    s.lauf(p, "{% endfor %}", 9)
    s.lauf(p, "{% if farben %}Farben: {% endif %}", 9, farbe=mp.RGB_LABEL)
    s.lauf(p, "{% for fa in (farben or []) %}", 9)
    r = s.lauf(p, "{{ fa.name }}", 9, fett=True)
    farbe_jinja(r, "fa.farbe")
    s.lauf(p, " {{ fa.bedeutung }}{% if not loop.last %} · {% endif %}", 9, farbe=mp.RGB_LABEL)
    s.lauf(p, "{% endfor %}", 9)
    doc.save(pfad)


def muster_daten():
    rt = RichText()
    rt.add("Anzeige: ", size=28, color="1B1F24")
    rt.add("180 °C", size=28, color="08349C")
    rt.add("\n")
    rt.add("Thermometer: ", size=28, color="1B1F24")
    rt.add("≈ 172 °C", size=28, color="C62828")
    return {**mp.GEMEINSAM,
            "wozu": "Planung der Tafel bzw. des Whiteboards: was wann wohin kommt. Die Nummern zeigen die Phase, "
                    "in der etwas angeschrieben oder angeheftet wird.",
            "links": [
                {"phase": 1, "art": "magnet", "text": "Telefonnotiz (Ausdruck A4, angeheftet)"},
                {"phase": 1, "text": rt},
                {"phase": 1, "text": "Unsere Vermutungen:", "platzhalter": "Zurufe der Klasse sammeln, nicht bewerten",
                 "hoehe": 6.6}],
            "mitte": [
                {"phase": 2, "text": "Plan der Gruppen:",
                 "platzhalter": "je Gruppe ein Stichwort (Messen? Rechnen? Datenblatt?)", "hoehe": 3.0},
                {"phase": 4, "text": "Ursache  →  Beleg  →  Empfehlung",
                 "platzhalter": "Ergebnisse der Gruppen, gemeinsam geordnet (gleiche Struktur wie Folie „Sicherung“)",
                 "hoehe": 6.2}],
            "rechts": [
                {"phase": 3, "text": "Begriffe, die fallen:",
                 "platzhalter": "z. B. Leitungswiderstand, Zweileiterschaltung", "hoehe": 3.9},
                {"phase": 5, "text": "Merksatz:",
                 "platzhalter": "von den Lernenden formuliert, an der Tafel festgehalten", "hoehe": 3.3},
                {"phase": 5, "text": "Ausblick: Wie setzen wir die Empfehlung um?", "farbe": "2E7D32"}],
            "phasen": ["Einstieg", "Planung", "Erarbeitung", "Sicherung", "Abschluss"],
            "farben": [{"name": "blau", "farbe": "08349C", "bedeutung": "Anzeige/Steuerung"},
                       {"name": "rot", "farbe": "C62828", "bedeutung": "Messung"},
                       {"name": "grün", "farbe": "2E7D32", "bedeutung": "Ergebnis"}],
            "datei": "Tafelbild-Plan · Brinkmann Automation und Nordland Feinkost sind fiktiv."}


if __name__ == "__main__":
    mp.bauen("tafelbild", vorlage, muster_daten())
