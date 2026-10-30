"""Vorlage Messprotokoll (Prüfprotokoll des Betriebs, Variante A, zweiseitig).

Seite 1: Kopf nach Variante C, Titelzeile mit Namensfeld, Wozu, Rahmen „PRÜFPROTOKOLL“ mit Auftrag,
verwendeten Messgeräten und großem Kästchenfeld für den Messaufbau.
Seite 2: schmale Fortsetzungszeile (eigene Kopfzeile für Folgeseiten), Messwerttabelle, Ergebnis und
Empfehlung, Unterschriften.

Schalter `messpunkte_vorgegeben`: True druckt die Messpunkte aus `messpunkte` vor (Routineprüfung nach
festem Prüfplan), False lässt die Tabelle leer mit dem Hinweis „Messpunkte selbst festlegen“.
Leere Zeilen werden bis `zeilen_min` (Standard 8) aufgefüllt.

Die Formular-Bausteine (formular, raender, datentabelle, unterschriften …) nutzen auch
servicebericht.py und serviceauftrag.py.

Aufruf: python werkzeug/vorlagen/messprotokoll.py
Erzeugt vorlagen/Vorlage_messprotokoll.docx, docs/stilreferenz/vorlagen/muster/Muster_messprotokoll.docx
und die Vorschau vorschau_messprotokoll-N.png.
"""
import sys
from pathlib import Path

from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docxtpl import DocxTemplate

sys.path.insert(0, str(Path(__file__).parent))
import schule as s  # noqa: E402
from vorlagen_bauen import rahmen, schattieren, tabelle_ohne_rahmen  # noqa: E402

WURZEL = s.WURZEL
VORLAGEN = WURZEL / "vorlagen"
MUSTER = WURZEL / "docs" / "stilreferenz" / "vorlagen" / "muster"

DUNKEL = "1B1F24"
FLINIE = "9AA3AD"           # Linien im Formular
LABEL_FILL = "F7F8FA"        # Feldbezeichnung
KOPF_FILL = "EDEFF2"         # Tabellenkopf, Formularkopf
RGB_LABEL = RGBColor.from_string("4A5563")
RAND = (12, DUNKEL)          # 1,5 pt Formularrahmen
DUENN = (4, FLINIE)


# ---------------------------------------------------------------- Formular-Bausteine
def knapp(p, pt=1):
    """Leerer Absatz nahezu ohne Höhe (z. B. der Pflichtabsatz hinter einer verschachtelten Tabelle)."""
    s.abstand(p)
    p.paragraph_format.line_spacing = Pt(pt)
    r = p.add_run("")
    r.font.size = Pt(1)
    return p


def absatz_in(zelle):
    """Letzten leeren Absatz der Zelle weiterverwenden, sonst neuen anlegen."""
    p = zelle.paragraphs[-1]
    if not p.runs and not p.text and p._p.getnext() is None:
        return p
    return zelle.add_paragraph()


def bereichstitel(zelle, text, farbe=s.RGB_BLAU, groesse=7.5, vor=6, nach=2):
    """Kleine Überschrift in Großbuchstaben mit Sperrung (wie .h / .bh im Entwurf)."""
    p = s.abstand(absatz_in(zelle), vor, nach)
    r = s.kapitaelchen(s.lauf(p, text, groesse, fett=True, farbe=farbe))
    sp = OxmlElement("w:spacing"); sp.set(qn("w:val"), "14")
    r._r.get_or_add_rPr().append(sp)
    return p


def gesperrt(r, wert=40):
    sp = OxmlElement("w:spacing"); sp.set(qn("w:val"), str(wert))
    r._r.get_or_add_rPr().append(sp)
    return r


def formular(ziel, breite, zeilen, trenner=None, innen=0.3, oben=0.05, unten=0.12):
    """Einspaltige Rahmentabelle (schwarzer Rand 1,5 pt). trenner: {zeilenindex: (staerke, farbe)}
    für die Linie über dieser Zeile. Gibt die Tabelle zurück."""
    trenner = trenner or {}
    t = ziel.add_table(zeilen, 1)
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    n = len(t.rows)
    for i, zeile in enumerate(t.rows):
        z = zeile.cells[0]
        rahmen(z, top=RAND if i == 0 else trenner.get(i),
               bottom=RAND if i == n - 1 else None, left=RAND, right=RAND)
        s.zellabstand(z, oben, unten, innen, innen)
        s.abstand(z.paragraphs[0])
    s.feste_breiten(t, [breite])
    return t


def formularkopf(zelle, links, rechts, breite, links_klein=None, fill=None, rechts_gross=False):
    """Kopf eines Formulars: links Bezeichnung (groß gesperrt) bzw. Firma, rechts Zusatz."""
    if fill:
        schattieren(zelle, fill)
    t = zelle.add_table(1, 2)
    tabelle_ohne_rahmen(t)
    a, b = t.rows[0].cells
    for z in (a, b):
        s.zellabstand(z, 0.02, 0.02, 0, 0)
        s.senkrecht(z, "center")
    p = s.abstand(a.paragraphs[0])
    if links_klein is None:          # „PRÜFPROTOKOLL“ links groß
        gesperrt(s.lauf(p, links, 12, fett=True, farbe=s.RGB_DUNKEL), 40)
    else:                            # Firma links, Formularname rechts groß
        s.lauf(p, links, 9.5, fett=True, farbe=s.RGB_DUNKEL)
        s.lauf(s.abstand(a.add_paragraph()), links_klein, 7, farbe=RGB_LABEL)
    p = s.abstand(b.paragraphs[0])
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    if rechts_gross:
        gesperrt(s.lauf(p, rechts, 13, fett=True, farbe=s.RGB_DUNKEL), 40)
    else:
        s.lauf(p, rechts, 8.5, farbe=s.RGB_DUNKEL)
    knapp(zelle.paragraphs[0])
    s.feste_breiten(t, [breite * 0.5, breite * 0.5] if rechts_gross or links_klein else [breite * 0.42, breite * 0.58])
    knapp(zelle.paragraphs[-1])
    return t


def datentabelle(ziel, breiten, zeilen, spalten=None, hoehe=0.62):
    t = ziel.add_table(zeilen, spalten or len(breiten))
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    for zeile in t.rows:
        s.zeilenhoehe(zeile, hoehe, genau=False)
        for z in zeile.cells:
            s.zellrand(z, 4, FLINIE)
    return t


def zelle_fuellen(z, text, groesse=8.5, fett=False, farbe=None, kursiv=False, fill=None, klein=None,
                  ausrichtung=None):
    """Zelltext mit Innenabstand; optional zweite kleine graue Zeile (klein)."""
    if fill:
        schattieren(z, fill)
    s.zellabstand(z, 0.08, 0.06, 0.15, 0.15)
    p = s.abstand(z.paragraphs[0])
    if ausrichtung is not None:
        p.alignment = ausrichtung
    s.lauf(p, text, groesse, fett=fett, farbe=farbe, kursiv=kursiv)
    if klein:
        s.lauf(s.abstand(z.add_paragraph()), klein, 7, farbe=RGB_LABEL)
    return p


def label(z, text):
    return zelle_fuellen(z, text, 7.5, farbe=RGB_LABEL, fill=LABEL_FILL)


def th(z, text, ausrichtung=None):
    return zelle_fuellen(z, text, 7.5, farbe=RGBColor.from_string("2B3440"), fill=KOPF_FILL, ausrichtung=ausrichtung)


def unterschriften(zelle, texte, breite, luecke=0.8, vor=0.9):
    """Unterschriftszeilen: Linie oben, Bezeichnung darunter."""
    p = absatz_in(zelle)
    s.abstand(p).paragraph_format.line_spacing = Cm(vor)
    n = len(texte)
    w = (breite - luecke * (n - 1)) / n
    t = zelle.add_table(1, 2 * n - 1)
    tabelle_ohne_rahmen(t)
    breiten = []
    for i, z in enumerate(t.rows[0].cells):
        s.zellabstand(z, 0.03, 0, 0, 0)
        if i % 2 == 0:
            rahmen(z, top=(8, DUNKEL))  # 1 pt: bei 0,75 pt rendern Linien je nach Lage ungleich dick
            s.lauf(s.abstand(z.paragraphs[0]), texte[i // 2], 7, farbe=RGB_LABEL)
            breiten.append(w)
        else:
            s.zellabstand(z, 0, 0, 0, 0)
            breiten.append(luecke)
    s.feste_breiten(t, breiten)
    knapp(zelle.paragraphs[-1])
    return t


def kaestchen_feld(zelle, breite, hoehe, raster=0.5):
    t = s.kaestchen(zelle, breite, hoehe, raster)
    knapp(zelle.paragraphs[-1])
    return t


def linien(zelle, anzahl, breite, hoehe=0.7):
    t = s.schreiblinien(zelle, anzahl, hoehe, breite)
    for zeile in t.rows:
        rahmen(zeile.cells[0], bottom=(4, FLINIE))
        s.zellabstand(zeile.cells[0], 0, 0, 0, 0)
    knapp(zelle.paragraphs[-1])
    return t


def kopfreferenz_umbenennen(doc, art="header", von="default", nach="first"):
    """Benennt die vorhandene Kopf-/Fußzeilen-Referenz um (default → first), damit der nächste
    Zugriff auf sec.header bzw. sec.footer eine neue Standard-Kopfzeile für die Folgeseiten anlegt."""
    sectPr = doc.sections[0]._sectPr
    for ref in sectPr.findall(qn(f"w:{art}Reference")):
        if ref.get(qn("w:type")) == von:
            ref.set(qn("w:type"), nach)


def kopf_nur_erste_seite(doc, folgekopf, fuss):
    """Seite 1: voller Schulkopf (schule.kopf) in first_page_header; Folgeseiten: folgekopf(doc).
    Fußzeile gleich auf allen Seiten (fuss(doc) wird zweimal aufgerufen)."""
    sec = doc.sections[0]
    sec.different_first_page_header_footer = True
    s.kopf(doc)
    kopfreferenz_umbenennen(doc, "header")
    folgekopf(doc)
    fuss(doc)
    kopfreferenz_umbenennen(doc, "footer")
    fuss(doc)


def seitenumbruch(doc):
    p = s.abstand(doc.add_paragraph())
    p.paragraph_format.line_spacing = Pt(1)
    p.add_run().add_break(WD_BREAK.PAGE)
    return p


def fusstext(links="{{ datei }}"):
    """Fußzeilentext; Quellen nur, wenn angegeben."""
    return links + "{% if quellen %} · Quellen: {{ quellen }}{% endif %}"


GEMEINSAM = {
    "beruf": "Elektroniker/in, Fachrichtung Automatisierungs- und Systemtechnik",
    "lf": "1", "lf_titel": "Elektrotechnische Systeme analysieren und Funktionen prüfen",
    "ls": "3", "ls_titel": "Der Temperaturfühler zeigt falsche Werte",
    "ds": "7", "leitfrage": "Können wir den Fehler beweisen?",
    "betrieb": "Brinkmann Automation GmbH",
    "betrieb_zeile": "Elektro- und Automatisierungstechnik · Musterstraße 1 · 12345 Musterstadt",
    "auftrag_nr": "SA-26-02417",
    "ki_hinweis": "KI-gestützt erstellt; Werkzeug, Version und Datum siehe KI-Verzeichnis.",
    "quellen": "",
}


REIHENFOLGE = {
    "rPr": "rStyle rFonts b bCs i iCs caps smallCaps strike dstrike outline shadow emboss imprint noProof snapToGrid "
           "vanish webHidden color spacing w kern position sz szCs highlight u effect bdr shd fitText vertAlign rtl "
           "cs em lang eastAsianLayout specVanish oMath",
    "pPr": "pStyle keepNext keepLines pageBreakBefore framePr widowControl numPr suppressLineNumbers pBdr shd tabs "
           "suppressAutoHyphens kinsoku wordWrap overflowPunct topLinePunct autoSpaceDE autoSpaceDN bidi "
           "adjustRightInd snapToGrid spacing ind contextualSpacing mirrorIndents suppressOverlap jc textDirection "
           "textAlignment textboxTightWrap outlineLvl divId cnfStyle rPr sectPr pPrChange",
    "tcPr": "cnfStyle tcW gridSpan hMerge vMerge tcBorders shd noWrap tcMar textDirection tcFitText vAlign hideMark",
    "tblPr": "tblStyle tblpPr tblOverlap bidiVisual tblStyleRowBandSize tblStyleColBandSize tblW jc tblCellSpacing "
             "tblInd tblBorders shd tblLayout tblCellMar tblLook",
    "trPr": "cnfStyle divId gridBefore gridAfter wBefore wAfter cantSplit trHeight tblHeader tblCellSpacing jc hidden",
}


def schema_ordnen(pfad):
    """Ordnet die Kindelemente von rPr, pPr, tcPr, tblPr, trPr nach dem WordprocessingML-Schema und entfernt
    Doppelte (das zuletzt gesetzte gilt). Word ist hier strenger als LibreOffice."""
    from docx import Document
    doc = Document(pfad)
    w = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    for part in doc.part.package.iter_parts():
        el = getattr(part, "_element", None)
        if el is None:
            continue
        for tag, folge in REIHENFOLGE.items():
            rang = {w + n: i for i, n in enumerate(folge.split())}
            for knoten in el.iter(w + tag):
                kinder = list(knoten)
                letzte = {}
                for k in kinder:
                    letzte[k.tag] = k
                for k in kinder:
                    knoten.remove(k)
                behalten = [k for k in kinder if letzte[k.tag] is k]
                behalten.sort(key=lambda k: rang.get(k.tag, 999))
                for k in behalten:
                    knoten.append(k)
    doc.save(pfad)


def bauen(name, vorlage_fn, daten, render_extra=None):
    """Baut Vorlage, Muster und Vorschau einer Materialart."""
    VORLAGEN.mkdir(parents=True, exist_ok=True)
    MUSTER.mkdir(parents=True, exist_ok=True)
    v = VORLAGEN / f"Vorlage_{name}.docx"
    vorlage_fn(v)
    schema_ordnen(v)
    tpl = DocxTemplate(v)
    kontext = dict(daten)
    if render_extra:
        kontext.update(render_extra(tpl))
    tpl.render(kontext, autoescape=True)
    m = MUSTER / f"Muster_{name}.docx"
    tpl.save(m)
    for alt in MUSTER.glob(f"vorschau_{name}-*.png"):
        alt.unlink()
    pngs = s.vorschau(m, MUSTER / f"vorschau_{name}")
    print(v.relative_to(WURZEL), m.relative_to(WURZEL), [p.name for p in pngs])
    return pngs


# ---------------------------------------------------------------- Messprotokoll
def folgekopf(doc):
    """Schmale Kopfzeile ab Seite 2: blauer Strich, Anlage · Titel · Fortsetzung, rechts Name."""
    b = s.nutzbreite(doc)
    k = doc.sections[0].header
    k.paragraphs[0].text = ""
    t = k.add_table(1, 3, Cm(b))
    tabelle_ohne_rahmen(t)
    st, mi, re = t.rows[0].cells
    schattieren(st, s.BLAU)
    s.zellabstand(st, 0, 0, 0, 0)
    knapp(st.paragraphs[0])
    for z in (mi, re):
        s.zellabstand(z, 0.06, 0.06, 0.25, 0)
        s.senkrecht(z, "center")
    p = s.abstand(mi.paragraphs[0])
    s.lauf(p, "Anlage {{ nr }} · {{ titel }}", 8.5, fett=True, farbe=s.RGB_DUNKEL)
    s.lauf(p, "  ·  Fortsetzung", 8.5, farbe=RGB_LABEL)
    p = s.abstand(re.paragraphs[0])
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    s.lauf(p, "Name: ", 8.5, farbe=RGB_LABEL)
    s.lauf(p, "_" * 26, 8.5, farbe=RGBColor.from_string("8A929E"))
    s.feste_breiten(t, [0.16, b - 6.66, 6.5])
    s.leer(k, 8)


def vorlage(pfad):
    doc = s.dokument("A4")
    b = s.nutzbreite(doc)
    innen = b - 0.6
    kopf_nur_erste_seite(doc, folgekopf, lambda d: s.fusszeile(d, links=fusstext(), quellen=None))

    s.titelzeile(doc, schild="Anlage {{ nr }} · Messprotokoll", titel="{{ titel }}")
    s.wozu(doc)

    # ---------- Seite 1: Rahmen mit Auftrag, Messgeräten, Messaufbau
    f = formular(doc, b, 2, trenner={1: RAND})
    formularkopf(f.cell(0, 0), "PRÜFPROTOKOLL", "{{ betrieb }} · {{ formular }}", innen)
    z = f.cell(1, 0)
    bereichstitel(z, "Auftrag")
    a = datentabelle(z, None, 2, 4)
    for i, (l1, w1, l2, w2) in enumerate((("Auftrag-Nr.", "{{ auftrag_nr }}", "Kunde / Standort", "{{ kunde }}"),
                                         ("Anlage / BMK", "{{ anlage }}", "Prüfgrund", "{{ pruefgrund }}"))):
        c = a.rows[i].cells
        label(c[0], l1); zelle_fuellen(c[1], w1); label(c[2], l2); zelle_fuellen(c[3], w2)
    s.feste_breiten(a, [3.0, 4.6, 3.0, innen - 10.6])
    bereichstitel(z, "Verwendete Messgeräte", vor=8)
    g = datentabelle(z, None, 4, 4)
    for c, txt in zip(g.rows[0].cells, ("Messgerät", "Hersteller / Typ", "Inventar-Nr.", "kalibriert bis")):
        th(c, txt)
    zelle_fuellen(g.cell(1, 0), "{%tr for m in (messgeraete or []) + [none] * ((geraete_min or 2) - (messgeraete or [])|length) %}", 7)
    for c, key in zip(g.rows[2].cells, ("geraet", "typ", "inventar", "kalibriert")):
        zelle_fuellen(c, "{{ m.%s or '' }}" % key)
    zelle_fuellen(g.cell(3, 0), "{%tr endfor %}", 7)
    s.feste_breiten(g, [3.8, 5.1, 4.2, innen - 13.1])
    bereichstitel(z, "Messaufbau (Skizze mit Messpunkten und Messgeräten)", vor=8)
    kaestchen_feld(z, innen, 14.9, raster=innen / 35)
    knapp(z.paragraphs[-1])

    seitenumbruch(doc)

    # ---------- Seite 2: Messwerte, Ergebnis, Unterschriften
    f = formular(doc, b, 2, trenner={1: RAND})
    formularkopf(f.cell(0, 0), "PRÜFPROTOKOLL", "Auftrag {{ auftrag_nr }} · {{ anlage_kurz }}", innen)
    z = f.cell(1, 0)
    bereichstitel(z, "Messwerte")
    p = s.abstand(z.add_paragraph(), 0, 3)
    s.lauf(p, "{%p if not messpunkte_vorgegeben %}", 7)
    p = s.abstand(z.add_paragraph(), 0, 3)
    s.lauf(p, "Messpunkte selbst festlegen: ", 8, fett=True, farbe=s.RGB_DUNKEL)
    s.lauf(p, "{{ hinweis_messpunkte or 'Tragen Sie ein, was Sie wo messen, und legen Sie den Sollwert fest.' }}", 8,
           farbe=RGB_LABEL)
    p = s.abstand(z.add_paragraph(), 0, 3)
    s.lauf(p, "{%p endif %}", 7)
    m = datentabelle(z, None, 4, 6, hoehe=0.82)
    kb = ("Nr.", "Messgröße / Messpunkt", "Einheit", "Sollwert", "Istwert", "Bewertung")
    for c, txt in zip(m.rows[0].cells, kb):
        th(c, txt)
    s.zeilenhoehe(m.rows[0], 0.62, genau=False)
    zelle_fuellen(m.cell(1, 0), "{%tr for mp in (messpunkte if messpunkte_vorgegeben else []) + [none] * "
                                "((zeilen_min or 8) - (messpunkte if messpunkte_vorgegeben else [])|length) %}", 7)
    c = m.rows[2].cells
    zelle_fuellen(c[0], "{{ loop.index }}")
    zelle_fuellen(c[1], "{{ mp.groesse or '' }}")
    zelle_fuellen(c[2], "{{ mp.einheit or '' }}")
    zelle_fuellen(c[3], "{{ mp.soll or '' }}")
    zelle_fuellen(c[4], "{{ mp.ist or '' }}")
    zelle_fuellen(c[5], "☐ i. O.    ☐ n. i. O.")
    zelle_fuellen(m.cell(3, 0), "{%tr endfor %}", 7)
    s.feste_breiten(m, [0.9, innen - 10.2, 1.5, 2.4, 2.4, 3.0])
    bereichstitel(z, "Ergebnis und Empfehlung", vor=10)
    linien(z, 10, innen, 0.78)
    unterschriften(z, ("Ort, Datum", "Prüfer/in", "Kunde (Kenntnisnahme)"), innen)
    doc.save(pfad)


def muster_daten():
    return {**GEMEINSAM,
            "nr": "5", "titel": "Messprotokoll Siegelstation SG-2",
            "wozu": "Sie halten Ihre Messungen so fest, wie es der Betrieb für den Kunden verlangt.",
            "formular": "Kundendienst · FB-07",
            "kunde": "Nordland Feinkost, Werk Musterstadt, Linie 2",
            "anlage": "Siegelstation SG-2 · -B1", "anlage_kurz": "Siegelstation SG-2",
            "pruefgrund": "Reklamation Siegeltemperatur",
            "messgeraete": [], "geraete_min": 2,
            "messpunkte_vorgegeben": True,
            "messpunkte": [
                {"groesse": "Temperatur Heizbacke (Prüfthermometer)", "einheit": "°C"},
                {"groesse": "Temperatur Anzeige Steuerung", "einheit": "°C"},
                {"groesse": "Widerstand an Klemme X2 (mit Leitung)", "einheit": "Ω"},
                {"groesse": "Widerstand direkt am Fühler (ohne Leitung)", "einheit": "Ω"}],
            "zeilen_min": 8,
            "datei": "Anlage 5 · Messprotokoll · Brinkmann Automation und Nordland Feinkost sind fiktiv."}


if __name__ == "__main__":
    bauen("messprotokoll", vorlage, muster_daten())
