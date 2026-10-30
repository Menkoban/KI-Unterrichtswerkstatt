"""Baut die Hausvorlagen (DOCX mit docxtpl-Platzhaltern, PPTX, XLSX) und je ein Muster.

Aufruf:  python werkzeug/vorlagen/vorlagen_bauen.py <ausgabeordner>
Ergebnis: <ausgabe>/vorlagen/*  (Vorlagen mit Platzhaltern)
          <ausgabe>/muster/*    (dieselben Vorlagen mit Beispielinhalt aus LF 1, LS 3, DS 7)

Schulfarbe, Schulname und Bildungsgang stehen in STIL und lassen sich zentral ändern.
"""
import sys
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docxtpl import DocxTemplate

STIL = {
    "schule": "BBS Musterstadt",
    "bildungsgang": "Elektroniker/in für Betriebstechnik",
    "farbe": "00677F",       # Schulfarbe (Petrol), zentral änderbar
    "farbe_hell": "E3EFF2",
    "grau": "5F6670",
    "schrift": "Arial",
}
FARBE = RGBColor.from_string(STIL["farbe"])
GRAU = RGBColor.from_string(STIL["grau"])


# ---------------------------------------------------------------- Hilfsfunktionen
def schattieren(zelle, farbe):
    tcPr = zelle._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), farbe)
    tcPr.append(shd)


def rahmen(zelle, **seiten):
    """seiten: top/bottom/left/right = (staerke_achtelpunkt, farbe) oder None für keinen Rahmen"""
    tcPr = zelle._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for seite in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{seite}")
        wert = seiten.get(seite)
        if wert is None:
            el.set(qn("w:val"), "nil")
        else:
            el.set(qn("w:val"), "single"); el.set(qn("w:sz"), str(wert[0])); el.set(qn("w:color"), wert[1])
        borders.append(el)
    tcPr.append(borders)


def tabelle_ohne_rahmen(tab):
    for zeile in tab.rows:
        for z in zeile.cells:
            rahmen(z)


def spaltenbreiten(tab, breiten_cm):
    tab.autofit = False
    for zeile in tab.rows:
        for z, b in zip(zeile.cells, breiten_cm):
            z.width = Cm(b)


def absatz(ziel, text="", groesse=None, fett=False, farbe=None, ausrichtung=None, abstand_nach=None, kursiv=False):
    p = ziel.add_paragraph() if hasattr(ziel, "add_paragraph") else ziel
    if text:
        r = p.add_run(text)
        r.bold = fett; r.italic = kursiv
        if groesse: r.font.size = Pt(groesse)
        if farbe is not None: r.font.color.rgb = farbe
    if ausrichtung is not None: p.alignment = ausrichtung
    if abstand_nach is not None: p.paragraph_format.space_after = Pt(abstand_nach)
    return p


def zelltext(zelle, text, groesse=9, fett=False, farbe=None, ausrichtung=None):
    p = zelle.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    return absatz(p, text, groesse, fett, farbe, ausrichtung)


def feld(absatz_, code):
    """Fügt ein Word-Feld ein (z. B. PAGE, NUMPAGES)."""
    r = absatz_.add_run()
    for typ, inhalt in (("begin", None), ("instr", code), ("separate", None), ("end", None)):
        if typ == "instr":
            el = OxmlElement("w:instrText"); el.set(qn("xml:space"), "preserve"); el.text = f" {code} "
        else:
            el = OxmlElement("w:fldChar"); el.set(qn("w:fldCharType"), typ)
        r._r.append(el)
    r.font.size = Pt(8); r.font.color.rgb = GRAU


def grunddokument(quer=False, a5=False):
    doc = Document()
    sec = doc.sections[0]
    if a5:
        sec.page_width, sec.page_height = Cm(21.0), Cm(14.8)
        sec.orientation = WD_ORIENT.LANDSCAPE
    elif quer:
        sec.orientation = WD_ORIENT.LANDSCAPE
        sec.page_width, sec.page_height = sec.page_height, sec.page_width
    for s in ("left_margin", "right_margin"):
        setattr(sec, s, Cm(2.0))
    sec.top_margin, sec.bottom_margin = Cm(1.6), Cm(1.6)
    sec.header_distance, sec.footer_distance = Cm(0.8), Cm(0.8)
    st = doc.styles["Normal"]
    st.font.name = STIL["schrift"]; st.font.size = Pt(11)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), STIL["schrift"])
    st.paragraph_format.space_after = Pt(4); st.paragraph_format.line_spacing = 1.15
    return doc


def kopfzeile(doc, mit_namensfeld=True, lehrkraft=False):
    sec = doc.sections[0]
    breite = (sec.page_width - sec.left_margin - sec.right_margin) / 360000  # in cm
    kopf = sec.header
    kopf.paragraphs[0].text = ""
    t = kopf.add_table(1, 3, Cm(breite))
    tabelle_ohne_rahmen(t)
    spaltenbreiten(t, [3.0, breite - 7.0, 4.0])
    logo, mitte, rechts = t.rows[0].cells
    # Logo-Platzhalter
    rahmen(logo, top=(6, "BFC5CC"), bottom=(6, "BFC5CC"), left=(6, "BFC5CC"), right=(6, "BFC5CC"))
    zelltext(logo, "Schullogo", 8, farbe=GRAU, ausrichtung=WD_ALIGN_PARAGRAPH.CENTER)
    zelltext(mitte, "{{ schule }}", 10, fett=True, farbe=FARBE)
    absatz(mitte, "{{ bildungsgang }}", 8, farbe=GRAU, abstand_nach=0)
    zelltext(rechts, "LF {{ lf }}  ·  LS {{ ls }}", 9, fett=True, ausrichtung=WD_ALIGN_PARAGRAPH.RIGHT)
    absatz(rechts, "{{ lf_titel }}", 7, farbe=GRAU, ausrichtung=WD_ALIGN_PARAGRAPH.RIGHT, abstand_nach=0)
    if lehrkraft:
        absatz(rechts, "NUR FÜR DIE LEHRKRAFT", 7, fett=True, farbe=RGBColor(0xB0, 0x00, 0x20),
               ausrichtung=WD_ALIGN_PARAGRAPH.RIGHT, abstand_nach=0)
    # farbige Linie
    for z in t.rows[0].cells[1:]:
        rahmen(z, bottom=(12, STIL["farbe"]))
    rahmen(logo, top=(6, "BFC5CC"), bottom=(12, STIL["farbe"]), left=(6, "BFC5CC"), right=(6, "BFC5CC"))
    if mit_namensfeld:
        n = kopf.add_table(1, 3, Cm(breite))
        tabelle_ohne_rahmen(n)
        spaltenbreiten(n, [breite - 8.0, 4.0, 4.0])
        for z, txt in zip(n.rows[0].cells, ("Name:", "Klasse:", "Datum:")):
            zelltext(z, txt, 9, farbe=GRAU)
            rahmen(z, bottom=(4, "8A929E"))
    kopf.add_paragraph().paragraph_format.space_after = Pt(0)


def fusszeile(doc, mit_quelle=True):
    sec = doc.sections[0]
    breite = (sec.page_width - sec.left_margin - sec.right_margin) / 360000
    fuss = sec.footer
    fuss.paragraphs[0].text = ""
    t = fuss.add_table(1, 2, Cm(breite))
    tabelle_ohne_rahmen(t)
    spaltenbreiten(t, [breite - 3.0, 3.0])
    links, rechts = t.rows[0].cells
    for z in (links, rechts):
        rahmen(z, top=(4, "BFC5CC"))
    zelltext(links, "{{ datei }}", 7, farbe=GRAU)
    if mit_quelle:
        absatz(links, "Quellen: {{ quellen }}", 7, farbe=GRAU, abstand_nach=0)
    absatz(links, "{{ ki_hinweis }}", 6.5, farbe=GRAU, abstand_nach=0, kursiv=True)
    p = zelltext(rechts, "Seite ", 8, farbe=GRAU, ausrichtung=WD_ALIGN_PARAGRAPH.RIGHT)
    feld(p, "PAGE"); r = p.add_run(" von "); r.font.size = Pt(8); r.font.color.rgb = GRAU; feld(p, "NUMPAGES")


def titelband(doc, titel_platzhalter="{{ titel }}", zusatz="Anlage {{ nr }}"):
    t = doc.add_table(1, 2)
    tabelle_ohne_rahmen(t)
    sec = doc.sections[0]
    breite = (sec.page_width - sec.left_margin - sec.right_margin) / 360000
    spaltenbreiten(t, [breite - 3.0, 3.0])
    a, b = t.rows[0].cells
    schattieren(a, STIL["farbe"]); schattieren(b, STIL["farbe"])
    zelltext(a, titel_platzhalter, 14, fett=True, farbe=RGBColor(0xFF, 0xFF, 0xFF))
    zelltext(b, zusatz, 9, farbe=RGBColor(0xFF, 0xFF, 0xFF), ausrichtung=WD_ALIGN_PARAGRAPH.RIGHT)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def kasten(doc, ueberschrift, inhalt_platzhalter, farbe_hell=True):
    t = doc.add_table(1, 1)
    z = t.rows[0].cells[0]
    rahmen(z, left=(24, STIL["farbe"]))
    if farbe_hell:
        schattieren(z, STIL["farbe_hell"])
    zelltext(z, ueberschrift, 9, fett=True, farbe=FARBE)
    absatz(z, inhalt_platzhalter, 10.5, abstand_nach=2)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def linien(doc, anzahl):
    for _ in range(anzahl):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0); p.paragraph_format.line_spacing = 1.6
        pPr = p._p.get_or_add_pPr(); b = OxmlElement("w:pBdr"); u = OxmlElement("w:bottom")
        u.set(qn("w:val"), "single"); u.set(qn("w:sz"), "4"); u.set(qn("w:color"), "BFC5CC"); b.append(u); pPr.append(b)


# ---------------------------------------------------------------- DOCX-Vorlagen
def vorlage_arbeitsblatt(pfad):
    doc = grunddokument(); kopfzeile(doc); fusszeile(doc); titelband(doc)
    kasten(doc, "Situation", "{{ situation }}")
    absatz(doc, "Auftrag", 11, fett=True, farbe=FARBE, abstand_nach=2)
    absatz(doc, "{%p for a in aufgaben %}")
    absatz(doc, "{{ a.nr }}  {{ a.text }}", 11, abstand_nach=2)
    absatz(doc, "{%p if a.gegeben %}")
    g = doc.add_table(2, 2); g.style = "Table Grid"
    zelltext(g.cell(0, 0), "gegeben", 9, fett=True); zelltext(g.cell(0, 1), "gesucht", 9, fett=True)
    schattieren(g.cell(0, 0), STIL["farbe_hell"]); schattieren(g.cell(0, 1), STIL["farbe_hell"])
    zelltext(g.cell(1, 0), "{{ a.gegeben }}", 10); zelltext(g.cell(1, 1), "{{ a.gesucht }}", 10)
    absatz(doc, "{%p endif %}")
    absatz(doc, "Lösung:", 9, farbe=GRAU, abstand_nach=0)
    lt = doc.add_table(3, 1)
    zelltext(lt.cell(0, 0), "{%tr for z in range(a.zeilen) %}", 8)
    z = lt.cell(1, 0); zelltext(z, " ", 11)
    rahmen(z, bottom=(4, "BFC5CC")); lt.rows[1].height = Cm(0.9)
    zelltext(lt.cell(2, 0), "{%tr endfor %}", 8)
    absatz(doc, "{%p endfor %}")
    kasten(doc, "Selbstkontrolle", "☐ Einheiten geprüft   ☐ Ergebnis plausibel   ☐ Rechenweg nachvollziehbar")
    doc.save(pfad)


def vorlage_infoblatt(pfad):
    doc = grunddokument(); kopfzeile(doc, mit_namensfeld=False); fusszeile(doc)
    titelband(doc, zusatz="Infoblatt {{ nr }}")
    absatz(doc, "{%p for b in bloecke %}")
    absatz(doc, "{{ b.ueberschrift }}", 12, fett=True, farbe=FARBE, abstand_nach=2)
    absatz(doc, "{{ b.text }}", 11)
    absatz(doc, "{%p endfor %}")
    kasten(doc, "Merke", "{{ merke }}")
    doc.save(pfad)


def vorlage_erwartungshorizont(pfad):
    doc = grunddokument(); kopfzeile(doc, mit_namensfeld=False, lehrkraft=True); fusszeile(doc)
    titelband(doc, "Erwartungshorizont: {{ titel }}", "zu Anlage {{ nr }}")
    t = doc.add_table(3, 3); t.style = "Table Grid"
    spaltenbreiten(t, [2.0, 10.0, 5.0])
    for z, txt in zip(t.rows[0].cells, ("Aufgabe", "Erwartete Lösung (gerechnet)", "Typische Fehler / Hinweise")):
        zelltext(z, txt, 9, fett=True, farbe=RGBColor(0xFF, 0xFF, 0xFF)); schattieren(z, STIL["farbe"])
    zelltext(t.cell(1, 0), "{%tr for e in erwartungen %}", 8)
    zelltext(t.cell(2, 0), "{{ e.nr }}", 10, fett=True)
    zelltext(t.cell(2, 1), "{{ e.loesung }}", 10)
    zelltext(t.cell(2, 2), "{{ e.fehler }}", 9)
    end = t.add_row(); zelltext(end.cells[0], "{%tr endfor %}", 8)
    doc.add_paragraph()
    kasten(doc, "Prüfung der Rechnung", "{{ pruefung }}", farbe_hell=False)
    doc.save(pfad)


def vorlage_hilfekarten(pfad):
    """A4 mit 8 Karten (2 × 4, je ca. A7) zum Ausschneiden; Schnittlinien gestrichelt."""
    doc = grunddokument(); fusszeile(doc, mit_quelle=False)
    absatz(doc, "Hilfekarten zu Anlage {{ nr }}: {{ titel }}", 11, fett=True, farbe=FARBE, abstand_nach=2)
    absatz(doc, "Entlang der gestrichelten Linien ausschneiden. Erst Karte 1 nehmen, dann 2, dann 3.", 8, farbe=GRAU)
    t = doc.add_table(2, 2)
    spaltenbreiten(t, [8.5, 8.5])
    zelltext(t.cell(0, 0), "{%tr for paar in kartenpaare %}", 8)
    for i, z in enumerate(t.rows[1].cells):
        s = "paar[0]" if i == 0 else "paar[1]"
        rahmen(z, top=(6, "8A929E"), bottom=(6, "8A929E"), left=(6, "8A929E"), right=(6, "8A929E"))
        zelltext(z, "{{ %s.kopf }}" % s, 9, fett=True, farbe=FARBE)
        absatz(z, "{{ %s.text }}" % s, 10.5)
        for _ in range(2):
            absatz(z, "", 6)
    end = t.add_row(); zelltext(end.cells[0], "{%tr endfor %}", 8)
    # Schnittlinien gestrichelt
    for zeile in t.rows[1:2]:
        for z in zeile.cells:
            tcPr = z._tc.get_or_add_tcPr(); b = OxmlElement("w:tcBorders")
            for seite in ("top", "left", "bottom", "right"):
                el = OxmlElement(f"w:{seite}"); el.set(qn("w:val"), "dashed"); el.set(qn("w:sz"), "6"); el.set(qn("w:color"), "8A929E"); b.append(el)
            tcPr.append(b)
    doc.save(pfad)


def vorlage_protokoll(pfad):
    doc = grunddokument(quer=True); kopfzeile(doc); fusszeile(doc)
    titelband(doc, zusatz="Messprotokoll {{ nr }}")
    kasten(doc, "Messaufgabe", "{{ aufgabe }}")
    absatz(doc, "Messgeräte: {{ geraete }}", 10, abstand_nach=4)
    # feste Tabelle mit bis zu 6 Spalten; Kopf aus den Daten, leere Spalten bleiben leer
    t = doc.add_table(5, 6); t.style = "Table Grid"
    for i, z in enumerate(t.rows[0].cells):
        zelltext(z, "{{ spalten[%d] if spalten|length > %d else '' }}" % (i, i), 9, fett=True)
        schattieren(z, STIL["farbe_hell"])
    for zeile in t.rows[1:]:
        zeile.height = Cm(1.0)
    doc.add_paragraph()
    absatz(doc, "Auswertung:", 10, fett=True, farbe=FARBE, abstand_nach=0)
    linien(doc, 4)
    doc.save(pfad)


def vorlage_karte_a5(pfad):
    """Karte A5 quer (Checkliste, Rollenkarte, Merkkarte) mit farbigem Rand."""
    doc = grunddokument(a5=True)
    sec = doc.sections[0]
    for s in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(sec, s, Cm(1.2))
    t = doc.add_table(1, 1)
    z = t.rows[0].cells[0]
    rahmen(z, top=(36, "F2B705"), bottom=(36, "F2B705"), left=(36, "F2B705"), right=(36, "F2B705"))
    zelltext(z, "{{ titel }}", 16, fett=True, farbe=FARBE)
    absatz(z, "{{ untertitel }}", 9, farbe=GRAU)
    absatz(z, "{%p for p in punkte %}")
    absatz(z, "☐  {{ p }}", 13, abstand_nach=4)
    absatz(z, "{%p endfor %}")
    absatz(z, "{{ schule }} · LF {{ lf }} · LS {{ ls }} · {{ datei }}", 7, farbe=GRAU)
    doc.save(pfad)


def vorlage_ticket(pfad):
    """Betriebsdokument des Modellbetriebs (Service-Ticket) innerhalb der Schulvorlage."""
    doc = grunddokument(); kopfzeile(doc); fusszeile(doc)
    titelband(doc, zusatz="Anlage {{ nr }}")
    t = doc.add_table(1, 2); tabelle_ohne_rahmen(t); spaltenbreiten(t, [11.0, 6.0])
    a, b = t.rows[0].cells
    schattieren(a, "1F3A5F"); schattieren(b, "1F3A5F")
    zelltext(a, "{{ betrieb }}", 13, fett=True, farbe=RGBColor(0xFF, 0xFF, 0xFF))
    absatz(a, "Service-Ticket", 9, farbe=RGBColor(0xDD, 0xE3, 0xEA), abstand_nach=0)
    zelltext(b, "{{ ticket_nr }}", 16, fett=True, farbe=RGBColor(0xFF, 0xFF, 0xFF), ausrichtung=WD_ALIGN_PARAGRAPH.RIGHT)
    d = doc.add_table(2, 2); d.style = "Table Grid"; spaltenbreiten(d, [4.0, 13.0])
    zelltext(d.cell(0, 0), "{%tr for f in felder %}", 8)
    zelltext(d.cell(1, 0), "{{ f[0] }}", 9, fett=True); schattieren(d.cell(1, 0), "EEF1F5")
    zelltext(d.cell(1, 1), "{{ f[1] }}", 10)
    end = d.add_row(); zelltext(end.cells[0], "{%tr endfor %}", 8)
    doc.add_paragraph()
    kasten(doc, "Meldung des Kunden", "„{{ meldung }}“")
    kasten(doc, "Technische Notiz", "{{ notiz }}", farbe_hell=False)
    kasten(doc, "Auftrag", "{{ auftrag }}")
    absatz(doc, "{{ unterschrift }}", 10, kursiv=True, ausrichtung=WD_ALIGN_PARAGRAPH.RIGHT)
    doc.save(pfad)


# ---------------------------------------------------------------- PPTX und XLSX
def vorlage_folien(pfad, muster=None):
    from pptx import Presentation
    from pptx.util import Cm as PCm, Pt as PPt
    from pptx.dml.color import RGBColor as PRGB
    from pptx.enum.shapes import MSO_SHAPE
    farbe = PRGB.from_string(STIL["farbe"]); grau = PRGB.from_string(STIL["grau"])
    prs = Presentation(); prs.slide_width, prs.slide_height = PCm(33.867), PCm(19.05)
    leer = prs.slide_layouts[6]
    m = muster or {}

    def rahmen_folie(titel):
        f = prs.slides.add_slide(leer)
        band = f.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, PCm(2.2))
        band.fill.solid(); band.fill.fore_color.rgb = farbe; band.line.fill.background()
        tb = f.shapes.add_textbox(PCm(1.2), PCm(0.35), PCm(26), PCm(1.6)).text_frame
        tb.text = titel; r = tb.paragraphs[0].runs[0]; r.font.size = PPt(28); r.font.bold = True
        r.font.color.rgb = PRGB(0xFF, 0xFF, 0xFF); r.font.name = STIL["schrift"]
        logo = f.shapes.add_shape(MSO_SHAPE.RECTANGLE, PCm(29.6), PCm(0.3), PCm(3.6), PCm(1.6))
        logo.fill.solid(); logo.fill.fore_color.rgb = PRGB(0xFF, 0xFF, 0xFF); logo.line.color.rgb = PRGB(0xBF, 0xC5, 0xCC)
        logo.text_frame.text = "Schullogo"; lr = logo.text_frame.paragraphs[0].runs[0]; lr.font.size = PPt(11); lr.font.color.rgb = grau
        fuss = f.shapes.add_textbox(PCm(1.2), PCm(18.0), PCm(31), PCm(0.8)).text_frame
        fuss.text = f"{STIL['schule']} · LF {m.get('lf','{{ lf }}')} · LS {m.get('ls','{{ ls }}')} · KI-gestützt erstellt (siehe KI-Verzeichnis)"
        fr = fuss.paragraphs[0].runs[0]; fr.font.size = PPt(10); fr.font.color.rgb = grau
        return f

    # 1 Titelfolie
    f = rahmen_folie(m.get("titel", "{{ titel }}"))
    tb = f.shapes.add_textbox(PCm(1.2), PCm(6.5), PCm(31), PCm(5)).text_frame; tb.word_wrap = True
    tb.text = m.get("leitfrage", "{{ leitfrage }}"); r = tb.paragraphs[0].runs[0]; r.font.size = PPt(40); r.font.bold = True; r.font.color.rgb = farbe
    # 2 Fahrplan
    f = rahmen_folie("Fahrplan der Stunde")
    phasen = m.get("phasen", [("Phase 1", "10 min"), ("Phase 2", "20 min"), ("Phase 3", "20 min"), ("Phase 4", "15 min")])
    breite = 30.6 / len(phasen)
    for i, (name, zeit) in enumerate(phasen):
        k = f.shapes.add_shape(MSO_SHAPE.CHEVRON if i else MSO_SHAPE.PENTAGON, PCm(1.2 + i * breite), PCm(7.5), PCm(breite - 0.2), PCm(3.2))
        aktiv = i == m.get("aktiv", 0)
        k.fill.solid(); k.fill.fore_color.rgb = farbe if aktiv else PRGB.from_string(STIL["farbe_hell"])
        k.line.fill.background()
        tf = k.text_frame; tf.word_wrap = False; tf.text = name; tf.add_paragraph().text = zeit
        for p in tf.paragraphs:
            for r in p.runs:
                r.font.size = PPt(15); r.font.bold = True
                r.font.color.rgb = PRGB(0xFF, 0xFF, 0xFF) if aktiv else farbe
    # 3 Inhalt
    f = rahmen_folie(m.get("inhalt_titel", "{{ inhalt_titel }}"))
    tb = f.shapes.add_textbox(PCm(1.2), PCm(3.2), PCm(31), PCm(13)).text_frame; tb.word_wrap = True
    punkte = m.get("punkte", ["{{ punkt_1 }}", "{{ punkt_2 }}", "{{ punkt_3 }}"])
    tb.text = "• " + punkte[0]
    for pkt in punkte[1:]:
        tb.add_paragraph().text = "• " + pkt
    for p in tb.paragraphs:
        for r in p.runs:
            r.font.size = PPt(26)
    # 4 Merkbild
    f = rahmen_folie("Merke")
    k = f.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, PCm(3), PCm(5), PCm(27.8), PCm(9))
    k.fill.solid(); k.fill.fore_color.rgb = PRGB.from_string(STIL["farbe_hell"]); k.line.color.rgb = farbe; k.line.width = PPt(3)
    tf = k.text_frame; tf.word_wrap = True; tf.text = m.get("merke", "{{ merke }}")
    for r in tf.paragraphs[0].runs:
        r.font.size = PPt(30); r.font.bold = True; r.font.color.rgb = farbe
    prs.save(pfad)


def vorlage_tabelle(pfad, muster=None):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    wb = Workbook(); ws = wb.active; ws.title = "Messprotokoll"
    m = muster or {}
    farbe = PatternFill("solid", fgColor=STIL["farbe"]); hell = PatternFill("solid", fgColor=STIL["farbe_hell"])
    duenn = Side(style="thin", color="8A929E"); rand = Border(top=duenn, bottom=duenn, left=duenn, right=duenn)
    ws.merge_cells("A1:F1"); ws["A1"] = f"{STIL['schule']}  ·  LF {m.get('lf','{{ lf }}')}  ·  LS {m.get('ls','{{ ls }}')}"
    ws["A1"].font = Font(name="Arial", bold=True, color="FFFFFF", size=11); ws["A1"].fill = farbe
    ws.merge_cells("A2:F2"); ws["A2"] = m.get("titel", "{{ titel }}")
    ws["A2"].font = Font(name="Arial", bold=True, size=14, color=STIL["farbe"])
    for zelle, txt in (("A3", "Name:"), ("C3", "Klasse:"), ("E3", "Datum:")):
        ws[zelle] = txt; ws[zelle].font = Font(name="Arial", size=9, color=STIL["grau"])
    spalten = m.get("spalten", ["Messung", "Größe 1", "Größe 2", "Rechnung", "Abweichung in %"])
    for i, s in enumerate(spalten, start=1):
        c = ws.cell(5, i, s); c.font = Font(name="Arial", bold=True, size=10); c.fill = hell; c.border = rand
        c.alignment = Alignment(wrap_text=True, vertical="center")
    zeilen = m.get("zeilen", [[f"{n}", None, None, None, None] for n in (1, 2, 3)])
    for r, werte in enumerate(zeilen, start=6):
        for c, w in enumerate(werte, start=1):
            zelle = ws.cell(r, c, w); zelle.border = rand; zelle.font = Font(name="Arial", size=10)
    for i, b in enumerate([16, 18, 18, 18, 18, 18], start=1):
        ws.column_dimensions[chr(64 + i)].width = b
    ws.row_dimensions[5].height = 32
    ws["A11"] = "KI-gestützt erstellt (siehe KI-Verzeichnis)"; ws["A11"].font = Font(name="Arial", size=8, italic=True, color=STIL["grau"])
    wb.save(pfad)


# ---------------------------------------------------------------- Musterinhalt (DS 7)
GEMEINSAM = {**{k: STIL[k] for k in ("schule", "bildungsgang")},
             "lf": "1", "ls": "3", "lf_titel": "Elektrotechnische Systeme analysieren und Funktionen prüfen",
             "ki_hinweis": "KI-gestützt erstellt; Werkzeug, Version und Datum siehe KI-Verzeichnis.",
             "quellen": "eigene Darstellung; Werte nach Tabellenbuch Elektrotechnik"}
RL = 0.0178 * 90 / 0.5
DT = RL / 0.385


def muster_daten():
    k = lambda x, n: f"{x:.{n}f}".replace(".", ",")
    return {
        "arbeitsblatt": {**GEMEINSAM, "nr": 4, "titel": "Leitungswiderstand und Messfehler",
            "datei": "Anl_4_Leitungswiderstand.docx",
            "situation": "Nordland Feinkost meldet: Seit dem Umbau zeigt die Steuerung der Siegelstation rund 8 °C zu viel an. "
                         "Der Pt100 sitzt jetzt 45 m entfernt (Zuleitung 2 × 0,5 mm², Kupfer).",
            "aufgaben": [
                {"nr": "a)", "text": "Berechnen Sie den Widerstand der Zuleitung.",
                 "gegeben": "l = 45 m (einfach), A = 0,5 mm², ρ = 0,0178 Ω·mm²/m", "gesucht": "R_L in Ω", "zeilen": 4},
                {"nr": "b)", "text": "Berechnen Sie, um wie viel Kelvin die Steuerung deshalb zu viel anzeigt.",
                 "gegeben": "Steigung Pt100: 0,385 Ω/K", "gesucht": "Δϑ in K", "zeilen": 3}]},
        "infoblatt": {**GEMEINSAM, "nr": 2, "titel": "Zweileiterschaltung beim Pt100", "datei": "Info_2_Zweileiterschaltung.docx",
            "bloecke": [{"ueberschrift": "Wie misst die Steuerung?", "text": "Die Steuerung schickt einen kleinen Messstrom durch den Pt100 und misst die Spannung. Daraus berechnet sie den Widerstand und daraus die Temperatur."},
                        {"ueberschrift": "Warum stört die Leitung?", "text": "Bei der Zweileiterschaltung fließt der Messstrom auch durch Hin- und Rückleiter. Die Steuerung misst deshalb R_Pt + R_L und kann beides nicht unterscheiden."}],
            "merke": "Jedes Ohm Leitungswiderstand täuscht beim Pt100 etwa 2,6 K mehr Temperatur vor."},
        "erwartungshorizont": {**GEMEINSAM, "nr": 4, "titel": "Leitungswiderstand und Messfehler", "datei": "EH_4_Leitungswiderstand.docx",
            "erwartungen": [
                {"nr": "a)", "loesung": f"l_ges = 2 · 45 m = 90 m;  R_L = 0,0178 Ω·mm²/m · 90 m / 0,5 mm² = {k(RL, 2)} Ω ≈ 3,2 Ω",
                 "fehler": "nur 45 m gerechnet (1,6 Ω); mm² in m² umgerechnet"},
                {"nr": "b)", "loesung": f"Δϑ = 3,2 Ω / 0,385 Ω/K = {k(DT, 1)} K", "fehler": "Kehrwert gebildet (0,12 K)"}],
            "pruefung": f"Nachgerechnet mit Einheiten (Pint): R_L = {k(RL, 3)} Ω, Δϑ = {k(DT, 2)} K. Übereinstimmung mit dem Materialauftrag."},
        "hilfekarten": {**GEMEINSAM, "nr": 4, "titel": "Leitungswiderstand und Messfehler", "datei": "HK_4_Leitungswiderstand.docx",
            "kartenpaare": [
                [{"kopf": "Hilfe 1 · Tipp (a)", "text": "Der Strom fließt zum Fühler hin und wieder zurück. Wie lang ist der ganze Weg?"},
                 {"kopf": "Hilfe 1 · Tipp (b)", "text": "Die Steuerung rechnet jeden zusätzlichen Widerstand in Temperatur um. Wie viel Ω entspricht 1 K?"}],
                [{"kopf": "Hilfe 2 · Ansatz (a)", "text": "R = ρ · l / A mit l = 2 · 45 m. A in mm², ρ in Ω·mm²/m einsetzen."},
                 {"kopf": "Hilfe 2 · Ansatz (b)", "text": "Δϑ = R_L / 0,385 Ω/K"}],
                [{"kopf": "Hilfe 3 · Lösungsweg (a)", "text": f"R_L = 0,0178 · 90 / 0,5 Ω = {k(RL, 2)} Ω"},
                 {"kopf": "Hilfe 3 · Lösungsweg (b)", "text": f"Δϑ = {k(RL, 2)} Ω / 0,385 Ω/K = {k(DT, 1)} K"}]]},
        "protokoll": {**GEMEINSAM, "nr": 5, "titel": "Messung an der Leitungsnachbildung", "datei": "Anl_5_Messprotokoll.docx",
            "aufgabe": "Messen Sie den Widerstand der Leitungsnachbildung und die Anzeige der Pt100-Auswertung ohne und mit Nachbildung.",
            "geraete": "Multimeter mit Nullabgleich (REL), Pt100-Auswertung, Leitungsnachbildung 3,3 Ω",
            "spalten": ["R_L gemessen", "R_L berechnet", "Anzeige ohne Leitung", "Anzeige mit Leitung", "Differenz in K", "Abweichung und Grund"]},
        "karte": {**GEMEINSAM, "titel": "Checkliste Sicherheit", "untertitel": "Vor jeder Messung abhaken (abwischbar)",
            "datei": "Anl_7_Checkliste_Sicherheit.docx",
            "punkte": ["Versorgung der Auswertung ausgeschaltet?", "Spannungsfreiheit mit dem Multimeter geprüft?",
                       "Messbereich Ω gewählt?", "Leitungen und Klemmen unbeschädigt?", "Nach der Messung abgebaut und weggeräumt?"]},
        "ticket": {**GEMEINSAM, "nr": 1, "titel": "Service-Ticket #2417", "datei": "Anl_1_Service_Ticket.docx",
            "betrieb": "Brinkmann Automation GmbH", "ticket_nr": "#2417",
            "felder": [["Datum", "13.10.2026"], ["Priorität", "hoch"], ["Kunde", "Nordland Feinkost GmbH"],
                       ["Anlage", "Verpackungslinie 2, Siegelstation"], ["Ansprechpartner", "Schichtleitung Linie 2"]],
            "meldung": "Seit dem Umbau zeigt die Steuerung rund 8 °C mehr an als vorher. Die Siegelnähte sind teilweise undicht.",
            "notiz": "Pt100 wurde beim Umbau 45 m entfernt neu montiert, Zuleitung 2 × 0,5 mm².",
            "auftrag": "Finden Sie die Ursache und weisen Sie sie rechnerisch und messtechnisch nach.",
            "unterschrift": "Kerstin Lüken, Meisterin"},
    }


def kartenpaare_fuer_vorlage():
    return [[{"kopf": "{{ Karte }}", "text": "{{ Text }}"}] * 2]


def main(ausgabe: Path):
    v, mu = ausgabe / "vorlagen", ausgabe / "muster"
    v.mkdir(parents=True, exist_ok=True); mu.mkdir(parents=True, exist_ok=True)
    bauer = {"arbeitsblatt": vorlage_arbeitsblatt, "infoblatt": vorlage_infoblatt,
             "erwartungshorizont": vorlage_erwartungshorizont, "hilfekarten": vorlage_hilfekarten,
             "protokoll": vorlage_protokoll, "karte": vorlage_karte_a5, "ticket": vorlage_ticket}
    daten = muster_daten()
    for name, f in bauer.items():
        pfad = v / f"Vorlage_{name}.docx"
        f(pfad)
        tpl = DocxTemplate(pfad); tpl.render(daten[name]); tpl.save(mu / f"Muster_{name}.docx")
    vorlage_folien(v / "Vorlage_folien.pptx")
    vorlage_folien(mu / "Muster_folien.pptx", {"lf": "1", "ls": "3", "titel": "Service-Ticket #2417",
        "leitfrage": "Können wir den Fehler beweisen?",
        "phasen": [("Vermuten", "10 min"), ("Planen", "10 min"), ("Rechnen", "20 min"), ("Messen", "25 min"), ("Nachweis", "15 min")],
        "aktiv": 2, "inhalt_titel": "Was misst die Steuerung wirklich?",
        "punkte": ["Die Steuerung misst R_Pt + R_L", "Zuleitung 2 × 45 m, 0,5 mm² → R_L ≈ 3,2 Ω", "3,2 Ω entsprechen ≈ 8,3 K"],
        "merke": "Bei der Zweileiterschaltung geht der Leitungswiderstand voll in die Temperaturanzeige ein."})
    vorlage_tabelle(v / "Vorlage_tabelle.xlsx")
    vorlage_tabelle(mu / "Muster_tabelle.xlsx", {"lf": "1", "ls": "3", "titel": "Messprotokoll Leitungsnachbildung",
        "spalten": ["Messung", "R_L gemessen in Ω", "R_L berechnet in Ω", "Anzeige ohne Leitung in °C", "Anzeige mit Leitung in °C", "Differenz in K"],
        "zeilen": [["1", None, 3.2, None, None, None], ["2", None, 3.2, None, None, None], ["3", None, 3.2, None, None, None]]})
    print("fertig:", sorted(p.name for p in v.iterdir()))


if __name__ == "__main__":
    # Abgelöst (2026-10-13): Die Vorlagen entstehen jetzt einzeln je Materialart, siehe alle_bauen.py.
    # Dieses Modul liefert nur noch Hilfsfunktionen (und vorlage_tabelle für XLSX).
    sys.exit("Abgelöst: python werkzeug/vorlagen/alle_bauen.py verwenden.")
