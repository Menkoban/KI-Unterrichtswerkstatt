"""Gemeinsame Bausteine der abgenommenen Vorlagen (Schulname, Logo und Modellbetrieb aus dem Profil, neutral
im Werkzeug: BBS Musterstadt, Platzhalter-Logo, Musterbetrieb).

Kopf nach Variante C, Titelzeile mit Anlage-Schild und Namensblock, „Wozu?“-Zeile, Fußzeile.
Alle Vorlagen in diesem Ordner bauen darauf auf; Gestaltung siehe docs/regeln/stilregeln.md
und die Muster in docs/stilreferenz/vorlagen/.
"""
import subprocess
import re
import sys
import tempfile
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

sys.path.insert(0, str(Path(__file__).parent))
from vorlagen_bauen import absatz, rahmen, schattieren, spaltenbreiten, tabelle_ohne_rahmen, zelltext  # noqa: E402,F401

WURZEL = Path(__file__).resolve().parents[2]
LOGO_NEUTRAL = WURZEL / "vorlagen" / "logo" / "Schullogo_Muster.png"
LOGO = LOGO_NEUTRAL

# Schule und Modellbetrieb (Profil schule.name, schule.ort, schule.logo, modellbetrieb.name; Veröffentlichung 2026-11).
# Neutral für Werkzeug, Vorlagen und Muster; aus dem Profil über persoenlich() und für jedes Bauskript, das im
# Arbeitsbereich liegt (auch ältere ohne persoenlich()), siehe _bauskript_im_arbeitsbereich() am Ende.
SCHULE = {"name": "BBS Musterstadt", "ort": "Musterstadt", "betrieb": "Musterbetrieb GmbH"}
NEUTRAL = dict(SCHULE)

# Gestaltung, die zur Lehrkraft gehört (Profil, Gruppe „Material“). Hier die neutralen Standardwerte für
# Werkzeug, Vorlagen und Muster; Bauskripte im Arbeitsbereich rufen zuerst persoenlich() auf.
STIL = {"kopf_zentriert": False, "abbildungen_zentriert": False, "infoblatt_wozu": True,
        "keine_gedankenstriche": False, "zeit_auf_arbeitsblatt": True, "aufgaben_kaestchen": False, "flattersatz": False,
        "merkkasten": "blau", "merkkasten_schueler": "lueckenformel", "formeln_als_bruch": False, "fassung": "gesamt",
        "sozialform_symbol": True, "freigabe_einschalten": "fragen", "freigabefeld_auf_blatt": True}


def persoenlich():
    """Übernimmt die Gestaltung aus dem Lehrkraft-Profil in STIL und gibt das ganze Profil zurück."""
    sys.path.insert(0, str(WURZEL / "werkzeug"))
    import arbeitsbereich
    werte = arbeitsbereich.profil()
    schule_aus_profil(werte, arbeitsbereich.finden())
    STIL.update(kopf_zentriert=werte["material.kopf_zentriert"],
                abbildungen_zentriert=werte["material.abbildungen_zentriert"],
                infoblatt_wozu=werte["material.infoblatt_wozu"],
                keine_gedankenstriche=werte["form.keine_gedankenstriche"],
                zeit_auf_arbeitsblatt=werte.get("material.zeit_auf_arbeitsblatt", True),
                aufgaben_kaestchen=werte.get("material.aufgaben_kaestchen", False),
                flattersatz=werte.get("material.flattersatz", False),
                merkkasten=werte.get("material.merkkasten", "blau"),
                merkkasten_schueler=werte.get("material.merkkasten_schueler", "lueckenformel"),
                formeln_als_bruch=werte.get("material.formeln_als_bruch", False),
                # Sozialform-Symbol an den Aufgaben bleibt auch bei freier Sozialform (Lehrkraft 2026-10-27: „das durftest
                # du eigentlich“; Wegfall zurückgenommen)
                sozialform_symbol=werte.get("material.sozialform_symbol", True),
                freigabe_einschalten=werte.get("ruesten.freigabe_einschalten", "fragen"),
                # Freigabe mündlich (Lehrkraft 2026-10-27): kein Freigabefeld auf dem Blatt, die Regel bleibt
                freigabefeld_auf_blatt=werte.get("material.freigabefeld_auf_blatt", True))
    return werte


def schule_aus_profil(werte, arbeitsbereich):
    """Schulname, Ort, Logo und Modellbetrieb aus dem Profil; fehlende Werte bleiben neutral."""
    global LOGO
    SCHULE.update(name=werte.get("schule.name") or SCHULE["name"], ort=werte.get("schule.ort") or SCHULE["ort"],
                  betrieb=werte.get("modellbetrieb.name") or SCHULE["betrieb"])
    logo = werte.get("schule.logo")
    if logo and (Path(arbeitsbereich) / logo).exists():
        LOGO = Path(arbeitsbereich) / logo


def werkzeugvorlage(pfad, vorlage_fn):
    """Ältere Bauskripte im Arbeitsbereich nutzen die neutrale Werkzeug-Vorlage (vorlagen/Vorlage_*.docx) direkt: dann
    dieselbe Vorlage mit Schule und Logo aus dem Profil neu bauen (Gestaltung STIL wie bisher). Sonst der Pfad selbst."""
    pfad = Path(pfad)
    if pfad.resolve().parent != (WURZEL / "vorlagen").resolve() or (SCHULE == NEUTRAL and LOGO == LOGO_NEUTRAL):
        return pfad
    ziel = Path(tempfile.mkdtemp()) / pfad.name
    vorlage_fn(ziel)
    from messprotokoll import schema_ordnen
    schema_ordnen(ziel)
    return ziel


def _bauskript_im_arbeitsbereich():
    """Liegt das gestartete Skript im Arbeitsbereich, gelten Schule, Logo und Modellbetrieb aus dem Profil, auch ohne
    persoenlich() (so bleiben ältere Bauskripte gleich). Skripte im Werkzeug und Tests bleiben neutral."""
    try:
        sys.path.insert(0, str(WURZEL / "werkzeug"))
        import arbeitsbereich
        ab = arbeitsbereich.finden().resolve()
        if ab in Path(sys.argv[0]).resolve().parents:
            schule_aus_profil(arbeitsbereich.profil(ab), ab)
    except (SystemExit, Exception):   # kein oder mehrdeutiger Arbeitsbereich: neutral
        pass

BLAU, GRUEN = "08349C", "7DDE78"
BLAU_HELL, GRAU_HELL = "E8EEF8", "F7F8FA"
LINIE, LINIE_HELL = "8A929E", "C9CED6"
SCHRIFT = "Arial"
RGB_BLAU = RGBColor.from_string(BLAU)
RGB_GRAU = RGBColor.from_string("5F6670")
RGB_DUNKEL = RGBColor.from_string("1B1F24")
WEISS = RGBColor(0xFF, 0xFF, 0xFF)

FORMATE = {  # Breite, Höhe, Rand links/rechts, Rand oben/unten (cm)
    "A4": (21.0, 29.7, 1.5, 1.2),
    "A4quer": (29.7, 21.0, 1.5, 1.2),
    "A5quer": (21.0, 14.8, 1.2, 0.9),
    "A6quer": (14.8, 10.5, 0.8, 0.6),
}


# ---------------------------------------------------------------- Grundlagen
def dokument(fmt="A4"):
    b, h, rand_lr, rand_ou = FORMATE[fmt]
    doc = Document()
    sec = doc.sections[0]
    sec.orientation = WD_ORIENT.LANDSCAPE if b > h else WD_ORIENT.PORTRAIT
    sec.page_width, sec.page_height = Cm(b), Cm(h)
    sec.left_margin = sec.right_margin = Cm(rand_lr)
    sec.top_margin = sec.bottom_margin = Cm(rand_ou)
    sec.header_distance = sec.footer_distance = Cm(rand_ou * 0.6)
    st = doc.styles["Normal"]
    st.font.name = SCHRIFT
    st.font.size = Pt(11)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), SCHRIFT)
    st.paragraph_format.space_after = Pt(3)
    st.paragraph_format.line_spacing = 1.15
    return doc


def nutzbreite(doc):
    sec = doc.sections[0]
    return (sec.page_width - sec.left_margin - sec.right_margin) / 360000


EINHEITEN = ("kWh", "Wh", "kW", "mW", "W", "kΩ", "MΩ", "Ω", "mA", "µA", "kA", "A", "mV", "kV", "V", "mm²", "mm", "cm",
             "km", "m³", "m²", "m", "°C", "K", "Hz", "%", "ms", "min", "h", "s", "kJ", "J", "kg", "g", "€", "ct", "l")
_ZAHL_EINHEIT = re.compile(r"(?<=\d) (?=(?:" + "|".join(re.escape(e) for e in EINHEITEN) + r")(?![\w²³]))")


def einheit_fest(text):
    """Geschütztes Leerzeichen zwischen Zahl und Einheit („47 Ω“ bricht nicht um; Sichtprüfung LS 4, 2026-10-27)."""
    return _ZAHL_EINHEIT.sub("\u00a0", text) if text else text


def lauf(p, text, groesse=None, fett=False, farbe=None, kursiv=False, hoch=False, tief=False):
    r = p.add_run(einheit_fest(text))
    r.bold, r.italic = fett, kursiv
    if groesse:
        r.font.size = Pt(groesse)
    if farbe is not None:
        r.font.color.rgb = farbe
    r.font.superscript, r.font.subscript = hoch, tief
    return r


def abstand(p, vor=0, nach=0, zeile=None):
    pf = p.paragraph_format
    pf.space_before, pf.space_after = Pt(vor), Pt(nach)
    if zeile:
        pf.line_spacing = zeile
    return p


def leer(ziel, hoehe_pt=4):
    p = ziel.add_paragraph()
    abstand(p)
    p.paragraph_format.line_spacing = Pt(hoehe_pt)
    return p


def zellrand(zelle, staerke=4, farbe=LINIE):
    rahmen(zelle, top=(staerke, farbe), bottom=(staerke, farbe), left=(staerke, farbe), right=(staerke, farbe))


def tabellenrand(tab, staerke=4, farbe=LINIE):
    for zeile in tab.rows:
        for z in zeile.cells:
            zellrand(z, staerke, farbe)


def feste_breiten(tab, breiten_cm):
    """Feste Spaltenbreiten (tblLayout fixed, tblGrid, tcW), auch nach verbundenen Zellen."""
    tblPr = tab._tbl.tblPr
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
    w = tblPr.find(qn("w:tblW"))
    if w is None:
        w = OxmlElement("w:tblW"); tblPr.append(w)
    w.set(qn("w:w"), str(int(sum(breiten_cm) * 567))); w.set(qn("w:type"), "dxa")
    grid = tab._tbl.tblGrid
    for gc, b in zip(grid.findall(qn("w:gridCol")), breiten_cm):
        gc.set(qn("w:w"), str(int(b * 567)))
    for tr in tab._tbl.tr_lst:
        i = 0
        for tc in tr.tc_lst:
            span = tc.grid_span
            tcPr = tc.get_or_add_tcPr()
            tcW = tcPr.find(qn("w:tcW"))
            if tcW is None:
                tcW = OxmlElement("w:tcW"); tcPr.insert(0, tcW)
            tcW.set(qn("w:w"), str(int(sum(breiten_cm[i:i + span]) * 567))); tcW.set(qn("w:type"), "dxa")
            i += span


def feld(p, code, groesse=7, farbe=None):
    """Word-Feld (PAGE, NUMPAGES) mit eigener Schriftgröße je Lauf."""
    for typ in ("begin", "instr", "separate", "text", "end"):
        r = p.add_run("1" if typ == "text" else None)
        r.font.size = Pt(groesse)
        if farbe is not None:
            r.font.color.rgb = farbe
        if typ == "instr":
            el = OxmlElement("w:instrText"); el.set(qn("xml:space"), "preserve"); el.text = f" {code} "
            r._r.append(el)
        elif typ != "text":
            el = OxmlElement("w:fldChar"); el.set(qn("w:fldCharType"), typ)
            r._r.append(el)


def kapitaelchen(r):
    """Großbuchstaben per Schriftattribut (Platzhalter bleiben unverändert)."""
    el = OxmlElement("w:caps"); r._r.get_or_add_rPr().append(el)
    return r


def zeilenhoehe(zeile, cm, genau=True):
    trPr = zeile._tr.get_or_add_trPr()
    h = OxmlElement("w:trHeight")
    h.set(qn("w:val"), str(int(cm * 567)))
    h.set(qn("w:hRule"), "exact" if genau else "atLeast")
    trPr.append(h)


def zellabstand(zelle, oben=0.05, unten=0.05, links=0.15, rechts=0.15):
    tcPr = zelle._tc.get_or_add_tcPr()
    mar = OxmlElement("w:tcMar")
    for seite, wert in (("top", oben), ("bottom", unten), ("start", links), ("end", rechts)):
        el = OxmlElement(f"w:{seite}")
        el.set(qn("w:w"), str(int(wert * 567)))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tcPr.append(mar)


def senkrecht(zelle, wo="center"):
    tcPr = zelle._tc.get_or_add_tcPr()
    v = OxmlElement("w:vAlign")
    v.set(qn("w:val"), wo)
    tcPr.append(v)


def absatzlinie(p, unten=(4, LINIE_HELL), oben=None):
    pPr = p._p.get_or_add_pPr()
    b = OxmlElement("w:pBdr")
    for seite, wert in (("top", oben), ("bottom", unten)):
        if wert:
            el = OxmlElement(f"w:{seite}")
            el.set(qn("w:val"), "single")
            el.set(qn("w:sz"), str(wert[0]))
            el.set(qn("w:space"), "1")
            el.set(qn("w:color"), wert[1])
            b.append(el)
    pPr.append(b)


def schreiblinien(ziel, anzahl, hoehe_cm=0.8, breite_cm=18.0):
    """Schreiblinien als Tabelle mit fester Zeilenhöhe (gleichmäßig in Word und LibreOffice)."""
    t = ziel.add_table(anzahl, 1)
    tabelle_ohne_rahmen(t)
    for zeile in t.rows:
        zeilenhoehe(zeile, hoehe_cm)
        rahmen(zeile.cells[0], bottom=(4, "9AA3AD"))
        abstand(zeile.cells[0].paragraphs[0])
    feste_breiten(t, [breite_cm])
    return t


def kaestchen(ziel, breite_cm, hoehe_cm, raster=0.5):
    """Kästchenraster (Rechenpapier) als Tabelle, Raster in cm."""
    spalten, zeilen = int(breite_cm / raster), int(hoehe_cm / raster)
    t = ziel.add_table(zeilen, spalten)
    t.autofit = False
    for zeile in t.rows:
        zeilenhoehe(zeile, raster)
        for z in zeile.cells:
            z.width = Cm(raster)
            zellrand(z, 2, "C9D3E6")
            zellabstand(z, 0, 0, 0, 0)
            p = abstand(z.paragraphs[0])
            p.paragraph_format.line_spacing = Pt(2)
    feste_breiten(t, [raster] * spalten)
    return t


# ---------------------------------------------------------------- Kopf, Titel, Fuß
def kopf(doc, beruf="{{ beruf }}", lf="Lernfeld {{ lf }}", lf_titel="{{ lf_titel }}",
         ls="Lernsituation {{ ls }}", ls_titel="{{ ls_titel }}"):
    """Kopf nach Variante C: Farbstreifen (Blau, unten Grün), Logo, Schule · Beruf, Felder LF und LS."""
    b = nutzbreite(doc)
    k = doc.sections[0].header
    k.paragraphs[0].text = ""
    t = k.add_table(2, 4, Cm(b))
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    tabelle_ohne_rahmen(t)
    rest = b - 0.28 - 3.6
    zeilenhoehe(t.rows[0], 0.75, genau=False)
    zeilenhoehe(t.rows[1], 0.95, genau=False)
    streifen_o, streifen_u = t.cell(0, 0), t.cell(1, 0)
    schattieren(streifen_o, BLAU)
    schattieren(streifen_u, GRUEN)
    for z in (streifen_o, streifen_u):
        lauf(abstand(z.paragraphs[0]), "", 2)
    logo = t.cell(0, 1).merge(t.cell(1, 1))
    senkrecht(logo)
    p = abstand(logo.paragraphs[0])
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(LOGO), width=Cm(3.0))
    # Schule links, Beruf rechts über der Lernsituation zentriert: bricht der Beruf um, steht die zweite Zeile
    # mittig darunter (Korrektur der Lehrkraft 2026-10-20)
    schule_z, beruf_z = t.cell(0, 2), t.cell(0, 3)
    for z in (schule_z, beruf_z):
        senkrecht(z, "top")       # Schule und Beruf auf gleicher Höhe (erste Zeile)
    mitte = STIL["kopf_zentriert"]   # Profil material.kopf_zentriert
    p = abstand(schule_z.paragraphs[0])
    if mitte:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    lauf(p, SCHULE["name"], 9, fett=True, farbe=RGB_BLAU)   # Profil schule.name
    p = abstand(beruf_z.paragraphs[0])
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    lauf(p, beruf, 9, farbe=RGB_GRAU)
    for z, kl, titel in ((t.cell(1, 2), lf, lf_titel), (t.cell(1, 3), ls, ls_titel)):
        senkrecht(z, "top")
        p = abstand(z.paragraphs[0])
        if mitte:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        kapitaelchen(lauf(p, kl, 6.5, farbe=RGB_GRAU))
        p = abstand(z.add_paragraph())
        if mitte:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        lauf(p, titel, 8.5)
    # Rahmen: außen hellgrau, Trennlinien innen
    for (zi, si) in ((0, 1), (1, 1), (0, 2), (0, 3), (1, 2), (1, 3)):
        z = t.cell(zi, si)
        rahmen(z, top=(4, "C3C9D1"), bottom=(4, "C3C9D1"), left=(4, "C3C9D1"), right=(4, "C3C9D1"))
    feste_breiten(t, [0.28, 3.6, rest / 2, rest / 2])
    leer(k, 6)
    return t


def titelzeile(doc, schild="Anlage {{ nr }} · Arbeitsblatt", titel="{{ titel }}", namensfeld=True, titelgroesse=18):
    """Links Schild (Schulblau) und Titel groß, rechts Name, Klasse, Datum als Schreiblinien."""
    b = nutzbreite(doc)
    t = doc.add_table(1, 2 if namensfeld else 1)
    tabelle_ohne_rahmen(t)
    a = t.cell(0, 0)
    senkrecht(a, "bottom")
    p = abstand(a.paragraphs[0], 0, 2)
    r = lauf(p, f" {schild} ", 8, farbe=WEISS)
    schatten = OxmlElement("w:shd")
    schatten.set(qn("w:val"), "clear"); schatten.set(qn("w:color"), "auto"); schatten.set(qn("w:fill"), BLAU)
    r._r.get_or_add_rPr().append(schatten)
    p = abstand(a.add_paragraph(), 0, 0, 1.0)
    lauf(p, titel, titelgroesse, fett=True, farbe=RGB_DUNKEL)
    if namensfeld:
        n = t.cell(0, 1)
        nb = n.add_table(3, 1)
        tabelle_ohne_rahmen(nb)
        for zeile, txt in zip(nb.rows, ("Name", "Klasse", "Datum")):
            zeilenhoehe(zeile, 0.62)
            c = zeile.cells[0]
            rahmen(c, bottom=(4, LINIE))
            senkrecht(c, "bottom")
            lauf(abstand(c.paragraphs[0]), txt, 8, farbe=RGB_GRAU)
        abstand(n.paragraphs[0]).paragraph_format.line_spacing = Pt(1)
        feste_breiten(nb, [5.4])
    feste_breiten(t, [b - 5.6, 5.6] if namensfeld else [b])
    return t


def wozu(doc, text="{{ wozu }}", linie=True):
    p = abstand(doc.add_paragraph(), 3, 6)
    lauf(p, "Wozu? ", 9, fett=True, farbe=RGBColor.from_string("4A5563"))
    lauf(p, text, 9, farbe=RGBColor.from_string("4A5563"))
    if linie:
        absatzlinie(p, (4, LINIE_HELL))
    return p


def fusszeile(doc, links="{{ datei }}", quellen="{{ quellen }}", ki="{{ ki_hinweis }}", seiten=True):
    b = nutzbreite(doc)
    f = doc.sections[0].footer
    f.paragraphs[0].text = ""
    t = f.add_table(1, 2, Cm(b))
    tabelle_ohne_rahmen(t)
    feste_breiten(t, [b - 2.6, 2.6])
    li, re = t.rows[0].cells
    for z in (li, re):
        rahmen(z, top=(4, "BFC5CC"))
    p = abstand(li.paragraphs[0])
    lauf(p, links, 7, farbe=RGB_GRAU)
    if quellen:
        lauf(p, " · Quellen: " + quellen, 7, farbe=RGB_GRAU)
    if ki:
        lauf(abstand(li.add_paragraph()), ki, 6.5, farbe=RGB_GRAU, kursiv=True)
    if seiten:
        p = abstand(re.paragraphs[0])
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        lauf(p, "Seite ", 7, farbe=RGB_GRAU)
        feld(p, "PAGE", 7, RGB_GRAU)
        lauf(p, " von ", 7, farbe=RGB_GRAU)
        feld(p, "NUMPAGES", 7, RGB_GRAU)
    return t


def ueberschrift(ziel, text, farbe=RGB_BLAU, groesse=8, vor=8, nach=2):
    """Kleine Überschrift in Großbuchstaben (z. B. „MESSWERTE“)."""
    p = abstand(ziel.add_paragraph(), vor, nach)
    r = kapitaelchen(lauf(p, text, groesse, fett=True, farbe=farbe))
    sp = OxmlElement("w:spacing"); sp.set(qn("w:val"), "12")
    r._r.get_or_add_rPr().append(sp)
    return p


# ---------------------------------------------------------------- Vorschau
def vorschau(docx, ziel_png_praefix, dpi=110):
    """DOCX/PPTX → PDF (LibreOffice) → PNG je Seite. Gibt die Liste der PNG-Dateien zurück."""
    docx = Path(docx)
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", tmp, str(docx)],
                       check=True, capture_output=True, timeout=180)
        pdf = Path(tmp) / (docx.stem + ".pdf")
        subprocess.run(["pdftoppm", "-png", "-r", str(dpi), str(pdf), str(ziel_png_praefix)], check=True)
    return sorted(Path(ziel_png_praefix).parent.glob(Path(ziel_png_praefix).name + "*.png"))


_bauskript_im_arbeitsbereich()
