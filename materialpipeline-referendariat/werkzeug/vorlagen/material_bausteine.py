"""Zusätzliche Bausteine für Einstieg, Infoblatt/Datenblatt und Karte A5.

Ergänzt schule.py (wird nicht verändert): Absatz- und Zeichenrahmen, Text mit Indizes
(R_{L}, 10^{−3}, **fett**) als RichText oder direkt in einen Absatz, Tabellen als Subdoc
für variable Tabellen in Vorlagen, Schemaordnung der XML-Eigenschaften (Word ist dort
streng) und ein gemeinsamer Bauablauf Vorlage → Muster → Vorschau.
"""
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docxtpl import DocxTemplate, RichText

sys.path.insert(0, str(Path(__file__).parent))
import schule as s  # noqa: E402
from vorlagen_bauen import rahmen, schattieren, tabelle_ohne_rahmen  # noqa: E402

WURZEL = s.WURZEL
MUSTER = WURZEL / "docs" / "stilreferenz" / "vorlagen" / "muster"
ENTWURF = WURZEL / "docs" / "stilreferenz" / "vorlagen" / "entwurf"
VORLAGEN = WURZEL / "vorlagen"
HAND = "Segoe Print"            # Handschrift (Windows); Ersatz siehe schriftersatz()
HAND_ERSATZ = "Comic Sans MS"
SYMBOL = "Segoe UI Symbol"      # Ankreuzfelder, Warnzeichen
DUNKEL, MITTEL = "1B1F24", "4A5563"
RGB_MITTEL = RGBColor.from_string(MITTEL)
UMBRUCH_MARKE = "[[SEITENUMBRUCH]]"


def persoenliche_vorlage(name, vorlage_fn):
    """Baut eine Vorlage mit der Gestaltung aus dem Lehrkraft-Profil in den Arbeitsbereich.

    Die Vorlagen in vorlagen/ (Werkzeug) bleiben neutral. Bauskripte im Arbeitsbereich nutzen diese
    Funktion statt WURZEL / "vorlagen" / ...; sie ruft schule.persoenlich() selbst auf.
    """
    s.persoenlich()
    import arbeitsbereich
    ziel = arbeitsbereich.finden() / ".daten" / "vorlagen" / f"Vorlage_{name}.docx"
    ziel.parent.mkdir(parents=True, exist_ok=True)
    doc = vorlage_fn()
    ordnen(doc)
    doc.save(ziel)
    return ziel


def gedankenstriche(pfad):
    """Fundstellen von Halbgeviert- und Geviertstrichen im Text (Profil form.keine_gedankenstriche)."""
    import zipfile
    with zipfile.ZipFile(pfad) as z:
        roh = " ".join(z.read(n).decode("utf-8", "ignore") for n in z.namelist()
                       if n.startswith(("word/", "ppt/slides/", "ppt/notesSlides/")) and n.endswith(".xml"))
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", roh)).replace(s.SCHULE["name"], "")   # Schulname: Eigenname, vom Gedankenstrich-Verbot ausgenommen
    return [text[max(m.start() - 25, 0):m.end() + 25] for m in re.finditer("[–—]", text)]


def seitenumbrueche_aufloesen(pfad):
    """Teilt die einzeilige Layout-Tabelle (Hauptspalte | Lücke | Randspalte) an jeder UMBRUCH_MARKE.

    Ein Umbruch in einer Tabellenzelle wird von Word und LibreOffice nicht zuverlässig umgesetzt.
    Darum: Tabelle kopieren, im Original alles ab der Marke löschen, in der Kopie alles vor der Marke
    und die Randspalte leeren, dazwischen ein Absatz mit echtem Seitenumbruch auf Dokumentebene.
    """
    from copy import deepcopy
    doc = Document(pfad)
    body = doc.element.body

    def marke_in(tc):
        return next((p for p in tc.findall(qn("w:p")) if UMBRUCH_MARKE in "".join(p.itertext())), None)

    def leerer_absatz():
        return OxmlElement("w:p")

    while True:
        fund = None
        for tbl in body.findall(qn("w:tbl")):
            tr = tbl.find(qn("w:tr"))
            if tr is None:
                continue
            for i, tc in enumerate(tr.findall(qn("w:tc"))):
                if marke_in(tc) is not None:
                    fund = (tbl, i)
                    break
            if fund:
                break
        if not fund:
            break
        tbl, i = fund
        kopie = deepcopy(tbl)
        tc = tbl.find(qn("w:tr")).findall(qn("w:tc"))[i]
        marke = marke_in(tc)
        weg = False
        for kind in list(tc):
            if kind is marke:
                weg = True
            if weg:
                tc.remove(kind)
        tc.append(leerer_absatz())
        # Folgeseite: nur die Spalte mit der Marke bleibt, über die volle Breite (Randspalte ist dort leer)
        tr2 = kopie.find(qn("w:tr"))
        for j, tc2 in enumerate(tr2.findall(qn("w:tc"))):
            if j == i:
                marke2 = marke_in(tc2)
                for kind in list(tc2):
                    if kind.tag == qn("w:tcPr"):
                        continue
                    tc2.remove(kind)
                    if kind is marke2:
                        break
                behalten = tc2
            else:
                tr2.remove(tc2)
        raster = kopie.find(qn("w:tblGrid"))
        breite = sum(int(g.get(qn("w:w"))) for g in raster.findall(qn("w:gridCol")))
        for g in raster.findall(qn("w:gridCol")):
            raster.remove(g)
        spalte = OxmlElement("w:gridCol")
        spalte.set(qn("w:w"), str(breite))
        raster.append(spalte)
        tcw = behalten.find(qn("w:tcPr")).find(qn("w:tcW"))
        tcw.set(qn("w:w"), str(breite))
        tcw.set(qn("w:type"), "dxa")
        umbruch = OxmlElement("w:p")
        ppr = OxmlElement("w:pPr")
        abst = OxmlElement("w:spacing")
        abst.set(qn("w:before"), "0"); abst.set(qn("w:after"), "0")
        abst.set(qn("w:line"), "20"); abst.set(qn("w:lineRule"), "exact")
        ppr.append(abst)
        umbruch.append(ppr)
        r = OxmlElement("w:r")
        br = OxmlElement("w:br")
        br.set(qn("w:type"), "page")
        r.append(br)
        umbruch.append(r)
        tbl.addnext(umbruch)
        umbruch.addnext(kopie)
    doc.save(pfad)


# ---------------------------------------------------------------- Rahmen, Schrift
def p_rahmen(p, space=1, **seiten):
    """Absatzrahmen: top/bottom/left/right = (Stärke Achtelpunkt, Farbe[, Linienart])."""
    pPr = p._p.get_or_add_pPr()
    alt = pPr.find(qn("w:pBdr"))
    if alt is not None:
        pPr.remove(alt)
    b = OxmlElement("w:pBdr")
    for seite in ("top", "left", "bottom", "right"):
        wert = seiten.get(seite)
        if wert:
            el = OxmlElement(f"w:{seite}")
            el.set(qn("w:val"), wert[2] if len(wert) > 2 else "single")
            el.set(qn("w:sz"), str(wert[0]))
            el.set(qn("w:space"), str(space))
            el.set(qn("w:color"), wert[1])
            b.append(el)
    pPr.append(b)
    return p


def p_schatten(p, farbe):
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), farbe)
    pPr.append(shd)


def r_rahmen(r, staerke=8, farbe=DUNKEL):
    rPr = r._r.get_or_add_rPr()
    b = OxmlElement("w:bdr")
    b.set(qn("w:val"), "single"); b.set(qn("w:sz"), str(staerke)); b.set(qn("w:space"), "1"); b.set(qn("w:color"), farbe)
    rPr.append(b)
    return r


def r_schrift(r, name):
    rPr = r._r.get_or_add_rPr()
    f = rPr.find(qn("w:rFonts"))
    if f is None:
        f = OxmlElement("w:rFonts"); rPr.append(f)
    for a in ("ascii", "hAnsi", "cs", "eastAsia"):
        f.set(qn(f"w:{a}"), name)
    return r


def r_symbol(r, code, groesse=10, schrift="Wingdings"):
    """Symbolzeichen (w:sym), z. B. Wingdings F0FE = Kästchen mit Haken, F0A8 = leeres Kästchen."""
    r.font.size = Pt(groesse)
    el = OxmlElement("w:sym"); el.set(qn("w:font"), schrift); el.set(qn("w:char"), code)
    r._r.append(el)
    return r


def r_sperren(r, twips=20):
    sp = OxmlElement("w:spacing"); sp.set(qn("w:val"), str(twips))
    r._r.get_or_add_rPr().append(sp)
    return r


def schriftersatz(doc, name=HAND, ersatz=HAND_ERSATZ, familie="script"):
    """Trägt die Handschrift mit Ersatzschrift in die Schriftentabelle ein (w:altName)."""
    ft = None
    for rel in doc.part.rels.values():
        if rel.reltype.endswith("/fontTable"):
            ft = rel.target_part
    if ft is None:
        return
    from lxml import etree
    root = etree.fromstring(ft.blob)
    el = etree.SubElement(root, qn("w:font")); el.set(qn("w:name"), name)
    for tag, val in (("altName", ersatz), ("family", familie), ("pitch", "variable")):
        x = etree.SubElement(el, qn(f"w:{tag}")); x.set(qn("w:val"), val)
    ft._blob = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def zeile_nicht_teilen(zeile):
    el = OxmlElement("w:cantSplit"); zeile._tr.get_or_add_trPr().append(el)


def tab_stopp(p, cm, art="right"):
    from docx.enum.text import WD_TAB_ALIGNMENT
    p.paragraph_format.tab_stops.add_tab_stop(Cm(cm), WD_TAB_ALIGNMENT.RIGHT if art == "right" else WD_TAB_ALIGNMENT.LEFT)


def text_absatz(ziel, text="", groesse=9, fett=False, farbe=None, vor=0, nach=0, zeile=None, ausr=None, kursiv=False):
    p = s.abstand(ziel.add_paragraph(), vor, nach, zeile)
    if text:
        s.lauf(p, text, groesse, fett=fett, farbe=farbe, kursiv=kursiv)
    if ausr:
        p.alignment = {"mitte": WD_ALIGN_PARAGRAPH.CENTER, "rechts": WD_ALIGN_PARAGRAPH.RIGHT,
                       "block": WD_ALIGN_PARAGRAPH.JUSTIFY}[ausr]
    return p


def zell_tabelle(zelle, zeilen, spalten):
    """Tabelle in einer Zelle, ohne den leeren Absatz, den python-docx dahinter anhängt."""
    n = zelle.add_table(zeilen, spalten)
    folge = n._tbl.getnext()
    if folge is not None and folge.tag == qn("w:p") and len(folge) == 0:
        folge.getparent().remove(folge)
    return n


def tag(ziel, text):
    """Absatz mit Jinja-Steueranweisung ({%p … %}); wird beim Füllen entfernt."""
    p = s.abstand(ziel.add_paragraph())
    s.lauf(p, text, 2)
    return p


def schlussabsatz(zelle_oder_doc, hoehe=1):
    """Winziger Abschlussabsatz: eine Zelle darf in Word nicht mit einer Tabelle enden."""
    p = s.abstand(zelle_oder_doc.add_paragraph())
    p.paragraph_format.line_spacing = Pt(hoehe)
    r = s.lauf(p, "", hoehe)
    return p


def label(ziel, text, farbe=s.RGB_BLAU, groesse=7.5, vor=6, nach=1, sperren=16):
    """Bezeichnung in Großbuchstaben, gesperrt (wie .bh/.sk im Entwurf)."""
    p = s.abstand(ziel.add_paragraph(), vor, nach)
    r = s.kapitaelchen(s.lauf(p, text, groesse, fett=True, farbe=farbe))
    r_sperren(r, sperren)
    return p


# ---------------------------------------------------------------- Text mit Indizes
_MUSTER = re.compile(r"\*\*(.+?)\*\*|_\{(.+?)\}|\^\{(.+?)\}")


def _teile(text):
    """Zerlegt 'R_{L} = ρ · l / A, **fett**, 10^{−3}' in (text, art)."""
    pos = 0
    for m in _MUSTER.finditer(text):
        if m.start() > pos:
            yield text[pos:m.start()], ""
        if m.group(1) is not None:
            yield m.group(1), "fett"
        elif m.group(2) is not None:
            yield m.group(2), "tief"
        else:
            yield m.group(3), "hoch"
        pos = m.end()
    if pos < len(text):
        yield text[pos:], ""


def rt(text, groesse=9, farbe=None, fett=False, kursiv=False, font=None):
    """RichText mit _{tief}, ^{hoch} und **fett** (für {{r … }} in Vorlagen)."""
    r = RichText()
    for t, art in _teile(text):
        r.add(t, size=int(groesse * 2), color=farbe, bold=fett or art == "fett", italic=kursiv,
              subscript=art == "tief", superscript=art == "hoch", font=font)
    return r


def runs(p, text, groesse=9, farbe=None, fett=False, kursiv=False):
    """Wie rt(), aber direkt in einen python-docx-Absatz (für Subdoc-Tabellen)."""
    for t, art in _teile(text):
        s.lauf(p, t, groesse, fett=fett or art == "fett", farbe=farbe, kursiv=kursiv,
               tief=art == "tief", hoch=art == "hoch")
    return p


# ---------------------------------------------------------------- Tabellen als Subdoc
def tabelle(tpl, kopf, zeilen, breiten, groesse=8, ausr="links", zeilenkopf=False, linie="C9CED6",
            kopf_fuellung="F2F4F7", kopf_farbe=s.RGBColor.from_string(MITTEL), mono=False, zellen_oben=0.06,
            zentriert=None):
    """Tabelle für {{p … }}: kopf (Liste oder None), zeilen (Liste von Listen), Breiten in cm.

    zeilenkopf=True: erste Spalte jeder Zeile grau hinterlegt (Schlüssel-Wert-Tabellen);
    bei 4 Spalten wird auch Spalte 3 als Schlüssel behandelt (zweispaltige Stammblätter).
    zentriert: Tabelle auf der Seite zentriert statt linksbündig; None = Profil material.abbildungen_zentriert.
    """
    sd = tpl.new_subdoc()
    alle = ([kopf] if kopf else []) + zeilen
    t = sd.add_table(len(alle), len(breiten))
    tabelle_ohne_rahmen(t)
    if s.STIL["abbildungen_zentriert"] if zentriert is None else zentriert:
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, werte in enumerate(alle):
        for j, w in enumerate(werte):
            z = t.cell(i, j)
            s.zellrand(z, 4, linie)
            s.zellabstand(z, zellen_oben, zellen_oben, 0.14, 0.14)
            ist_kopf = (kopf and i == 0) or (zeilenkopf and (j == 0 or (len(breiten) == 4 and j == 2)))
            if ist_kopf:
                schattieren(z, kopf_fuellung)
            s.senkrecht(z, "center")
            p = s.abstand(z.paragraphs[0], 0, 0, 1.05)
            if ausr == "mitte" and not (zeilenkopf and j == 0):
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            runs(p, str(w), groesse, farbe=kopf_farbe if ist_kopf else None)
            if mono and not ist_kopf:
                for r in p.runs:
                    r_schrift(r, "Courier New")
    s.feste_breiten(t, breiten)
    return sd


# ---------------------------------------------------------------- Seitenumbruch
def seitenumbruch(doc):
    from docx.enum.text import WD_BREAK
    p = s.abstand(doc.add_paragraph())
    p.paragraph_format.line_spacing = Pt(1)
    r = s.lauf(p, "", 1)
    r.add_break(WD_BREAK.PAGE)
    return p


def seitenrand_gestrichelt(doc, farbe="8A929E", abstand_pt=14):
    """Gestrichelte Schnittkante als Seitenrahmen (Abstand vom Blattrand)."""
    sectPr = doc.sections[0]._sectPr
    pb = OxmlElement("w:pgBorders")
    pb.set(qn("w:offsetFrom"), "page")
    for seite in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{seite}")
        el.set(qn("w:val"), "dashed"); el.set(qn("w:sz"), "8"); el.set(qn("w:space"), str(abstand_pt))
        el.set(qn("w:color"), farbe)
        pb.append(el)
    # Reihenfolge im sectPr: … pgSz, pgMar, paperSrc, pgBorders, lnNumType, pgNumType, cols …
    mar = sectPr.find(qn("w:pgMar"))
    mar.addnext(pb)


# ---------------------------------------------------------------- Schemaordnung
_ORDNUNG = {
    "pPr": "pStyle keepNext keepLines pageBreakBefore framePr widowControl numPr suppressLineNumbers pBdr shd tabs "
           "suppressAutoHyphens kinsoku wordWrap overflowPunct topLinePunct autoSpaceDE autoSpaceDN bidi "
           "adjustRightInd snapToGrid spacing ind contextualSpacing mirrorIndents suppressOverlap jc textDirection "
           "textAlignment textboxTightWrap outlineLvl divId cnfStyle rPr sectPr pPrChange",
    "rPr": "rStyle rFonts b bCs i iCs caps smallCaps strike dstrike outline shadow emboss imprint noProof snapToGrid "
           "vanish webHidden color spacing w kern position sz szCs highlight u effect bdr shd fitText vertAlign rtl "
           "cs em lang eastAsianLayout specVanish oMath",
    "tcPr": "cnfStyle tcW gridSpan hMerge vMerge tcBorders shd noWrap tcMar textDirection tcFitText vAlign hideMark",
    "tblPr": "tblStyle tblpPr tblOverlap bidiVisual tblStyleRowBandSize tblStyleColBandSize tblW jc tblCellSpacing "
             "tblInd tblBorders shd tblLayout tblCellMar tblLook",
    "trPr": "cnfStyle divId gridBefore gridAfter wBefore wAfter cantSplit trHeight tblHeader tblCellSpacing jc hidden",
}
_ORDNUNG = {qn(f"w:{k}"): {qn(f"w:{n}"): i for i, n in enumerate(v.split())} for k, v in _ORDNUNG.items()}


def _ordne_element(el):
    rang = _ORDNUNG[el.tag]
    kinder = list(el)
    # Doppelte Eigenschaften: die zuletzt gesetzte gilt
    gesehen, behalten = set(), []
    for k in reversed(kinder):
        if k.tag in rang and k.tag in gesehen:
            el.remove(k); continue
        gesehen.add(k.tag); behalten.append(k)
    behalten.reverse()
    behalten.sort(key=lambda k: rang.get(k.tag, 999))
    for k in behalten:
        el.remove(k)
    for k in behalten:
        el.append(k)


def ordnen(doc):
    """Bringt pPr/rPr/tcPr/tblPr/trPr-Kinder in Schemareihenfolge (Word öffnet sonst ggf. nicht)."""
    teile = [doc.element]
    for sec in doc.sections:
        for hf in (sec.header, sec.footer):
            teile.append(hf._element)
    for wurzel in teile:
        for tagname in _ORDNUNG:
            for el in wurzel.iter(tagname):
                _ordne_element(el)


# ---------------------------------------------------------------- Bauablauf
def bauen(name, vorlage_fn, daten_fn, vorlage_datei=None):
    """Vorlage bauen, Muster füllen, Vorschau rendern. daten_fn(tpl) liefert den Kontext."""
    VORLAGEN.mkdir(exist_ok=True); MUSTER.mkdir(parents=True, exist_ok=True)
    v = VORLAGEN / (vorlage_datei or f"Vorlage_{name}.docx")
    doc = vorlage_fn()
    ordnen(doc)
    doc.save(v)
    tpl = DocxTemplate(v)
    tpl.render(daten_fn(tpl), autoescape=True)
    m = MUSTER / f"Muster_{name}.docx"
    tpl.save(m)
    d = Document(m); ordnen(d); d.save(m)
    teile = [d.element.xml] + [hf._element.xml for sec in d.sections for hf in (sec.header, sec.footer)]
    rest = sum(x.count("{{") + x.count("{%") + x.count("{#") for x in teile)
    for alt in MUSTER.glob(f"vorschau_{name}-*.png"):
        alt.unlink()
    pngs = s.vorschau(m, MUSTER / f"vorschau_{name}")
    print(f"{v.name} · {m.name} · {len(pngs)} Seite(n) · offene Platzhalter: {rest}")
    return v, m, pngs
