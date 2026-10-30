"""Vorlage Impulsfolien (PPTX 16:9), Schulname und Logo aus dem Profil (neutral im Werkzeug).

Aufruf: python werkzeug/vorlagen/folien.py
Erzeugt vorlagen/Vorlage_folien.pptx, docs/stilreferenz/vorlagen/muster/Muster_folien.pptx (DS 7)
und die Vorschau docs/stilreferenz/vorlagen/muster/vorschau_folien-N.png.
Vorbild: docs/stilreferenz/vorlagen/folien_3typen.png (Entwurf folien_entwurf.html).

Aufbau
------
Der Folienmaster enthält genau drei Folienlayouts: „Einstieg“, „Ihr Auftrag“, „Sicherung“. In PowerPoint
wählt die Lehrkraft sie über „Neue Folie“. Alles Feste (Typ-Label mit Farbstreifen, Logo, Fußlinie,
Kästen „Sozialform/Unterlagen/Abgabe bis“, Zitatbalken) liegt im Layout und ist auf der Folie nicht
verschiebbar. Alles Veränderliche ist ein Platzhalter mit fester idx-Nummer (siehe PLATZHALTER).

Befüllung (Entscheidung)
------------------------
Befüllt wird über die idx-Nummern der Platzhalter, nicht über Textersetzung:
  * Formatierung (Schrift, Größe, Farbe) steckt im Layout-Platzhalter; der Text erbt sie.
  * Bild oder Tabelle (Einstieg, Sicherung) lassen sich nicht per Textersetzung einsetzen; über den
    Platzhalter kennt das Skript Lage und Größe.
  * Neue Folien entstehen immer aus dem Layout, nie durch Kopieren einer Beispielfolie.
Die drei Beispielfolien in Vorlage_folien.pptx tragen deshalb in jedem Platzhalter „{{ schlüssel }}“:
sichtbar in der Vorschau und zugleich die Namen der Schlüssel für befuellen(). Leere Platzhalter wären
in Vorschau und Bildschirmpräsentation unsichtbar. befuellen() entfernt die Beispielfolien und baut die
gewünschten Folien neu aus den Layouts. Kurzform: siehe muster_daten() und befuellen().
"""
import copy
import subprocess
import sys
import tempfile
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.oxml.ns import qn
from pptx.util import Cm, Emu, Pt

sys.path.insert(0, str(Path(__file__).parent))
import schule as s  # noqa: E402  (Logo und Schulname, Profil schule.*)

WURZEL = Path(__file__).resolve().parents[2]
VORLAGE = WURZEL / "vorlagen" / "Vorlage_folien.pptx"
MUSTER_ORDNER = WURZEL / "docs" / "stilreferenz" / "vorlagen" / "muster"

BLAU, GRUEN = "08349C", "7DDE78"
DUNKEL, GRAU, GRAU_2 = "1B1F24", "5F6670", "4A5563"
LINIE_HELL, LINIE_FUSS, LINIE_VD = "C9CED6", "DDE1E6", "9AA3AD"
HAND_FARBE = "23345E"
SCHRIFT, HAND, SYMBOL = "Arial", "Comic Sans MS", "Segoe UI Symbol"

# Maße nach Entwurf (1280 px Breite = 33,867 cm; 1 px = 0,02646 cm = 0,75 pt)
B, H = Cm(33.867), Cm(19.05)
RAND = 1.27                      # 48 px
NUTZ = 33.867 - 2 * RAND         # 31,33 cm
FUSS_Y = 18.05                   # Fußlinie

# Platzhalter je Layout: Schlüssel -> (idx, Typ, Prompt im leeren Platzhalter)
PLATZHALTER = {
    "Einstieg": {
        "inhalt": (10, "obj", "Impuls einfügen: Bild oder Tabelle (das Problem, ohne Lösung)"),
        "fuss_links": (11, "body", "LF · LS · Titel der Lernsituation"),
        "fuss_rechts": (12, "body", "… sind fiktiv · KI-gestützt erstellt"),
    },
    "Ihr Auftrag": {
        "zitat": (10, "body", "„Auftrag in der Sprache des Betriebs“"),
        "von": (11, "body", "Wer erteilt den Auftrag?"),
        "ergebnis": (12, "body", "Ergebnis: …"),
        "sozialform": (13, "body", "Sozialform"),
        "unterlagen": (14, "body", "Anlagen"),
        "abgabe": (15, "body", "00:00 Uhr"),
        "fuss_links": (16, "body", "LF · LS · Titel der Lernsituation"),
        "fuss_rechts": (17, "body", "KI-gestützt erstellt"),
    },
    "Sicherung": {
        "leitfrage": (10, "body", "Leitfrage eingeben"),
        "tabelle": (11, "tbl", "Tabelle einfügen (Kopfzeile blau, Zeilen leer)"),
        "fuss_links": (12, "body", "LF · LS · Titel der Lernsituation"),
        "fuss_rechts": (13, "body", "KI-gestützt erstellt"),
    },
}

NSMAP = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main",
         "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
         "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}


# ---------------------------------------------------------------- kleine Helfer
def rgb(h):
    return RGBColor.from_string(h)


def _cm(x):
    return int(Cm(x))


def schrift(run, groesse, fett=False, farbe=DUNKEL, name=SCHRIFT, abstand=None):
    f = run.font
    f.size, f.bold, f.name, f.color.rgb = Pt(groesse), fett, name, rgb(farbe)
    if abstand is not None:
        run._r.get_or_add_rPr().set("spc", str(int(abstand * 100)))


def text_mit_fett(absatz, text, groesse, farbe=DUNKEL, name=SCHRIFT):
    """Text mit **fett**-Auszeichnung in Läufe zerlegen."""
    for i, teil in enumerate(text.split("**")):
        if teil:
            r = absatz.add_run(); r.text = teil
            schrift(r, groesse, fett=bool(i % 2), farbe=farbe, name=name)


# ---------------------------------------------------------------- Layout-Bau (XML)
def _sp_platzhalter(sid, name, typ, idx, x, y, b, h, groesse, fett=False, farbe=DUNKEL, ausr="l",
                    anker="t", zeile=None, abstand=None, prompt="", einzug=(0, 0, 0, 0)):
    """Platzhalter-Shape für ein Layout als XML."""
    a, p = NSMAP["a"], NSMAP["p"]
    ln = f'<a:lnSpc><a:spcPct val="{int(zeile * 100000)}"/></a:lnSpc>' if zeile else ""
    spc = f' spc="{int(abstand * 100)}"' if abstand is not None else ""
    l, t, r, u = (_cm(v) for v in einzug)
    xml = f'''<p:sp xmlns:a="{a}" xmlns:p="{p}">
  <p:nvSpPr><p:cNvPr id="{sid}" name="{name}"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>
    <p:nvPr><p:ph type="{typ}" idx="{idx}"{' hasCustomPrompt="1"' if prompt else ''}/></p:nvPr></p:nvSpPr>
  <p:spPr><a:xfrm><a:off x="{_cm(x)}" y="{_cm(y)}"/><a:ext cx="{_cm(b)}" cy="{_cm(h)}"/></a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>
  <p:txBody><a:bodyPr lIns="{l}" tIns="{t}" rIns="{r}" bIns="{u}" anchor="{anker}" wrap="square"><a:normAutofit/></a:bodyPr>
    <a:lstStyle><a:lvl1pPr marL="0" indent="0" algn="{ausr}">{ln}<a:spcBef><a:spcPts val="0"/></a:spcBef><a:buNone/>
      <a:defRPr sz="{int(groesse * 100)}" b="{1 if fett else 0}"{spc}><a:solidFill><a:srgbClr val="{farbe}"/></a:solidFill>
      <a:latin typeface="{SCHRIFT}"/><a:cs typeface="{SCHRIFT}"/></a:defRPr></a:lvl1pPr></a:lstStyle>
    <a:p><a:r><a:rPr lang="de-DE"/><a:t>{prompt}</a:t></a:r></a:p></p:txBody></p:sp>'''
    return etree.fromstring(xml)


def _neues_layout(prs, vorbild, name):
    """Leeres Layout als Kopie von `vorbild` anlegen (eigener Part im selben Master)."""
    from pptx.opc.packuri import PackURI
    from pptx.parts.slide import SlideLayoutPart
    master = prs.slide_master
    vorhandene = {str(p.partname) for p in prs.part.package.iter_parts()}
    i = 1
    while f"/ppt/slideLayouts/slideLayout{i}.xml" in vorhandene:
        i += 1
    xml = copy.deepcopy(vorbild._element)
    part = SlideLayoutPart(PackURI(f"/ppt/slideLayouts/slideLayout{i}.xml"),
                           vorbild.part.content_type, prs.part.package, xml)
    part.relate_to(master.part, RT.SLIDE_MASTER)
    rid = master.part.relate_to(part, RT.SLIDE_LAYOUT)
    lst = master._element.find(qn("p:sldLayoutIdLst"))
    neue_id = max([int(e.get("id")) for e in lst] + [2147483648]) + 1
    e = etree.SubElement(lst, qn("p:sldLayoutId")); e.set("id", str(neue_id)); e.set(qn("r:id"), rid)
    layout = part.slide_layout
    layout._element.cSld.set("name", name)
    layout._element.set("type", "cust"); layout._element.set("preserve", "1")
    sptree = layout._element.cSld.spTree
    for sp in list(sptree)[2:]:
        sptree.remove(sp)
    return layout


def _verschieben(tmp_folie, layout):
    """Alle Shapes einer Hilfsfolie in das Layout verschieben (Bildbeziehungen mitnehmen)."""
    ziel = layout._element.cSld.spTree
    for el in list(tmp_folie.shapes._spTree)[2:]:
        for stil in el.findall(qn("p:style")):   # Designeffekte (Schatten) des Standarddesigns entfernen
            el.remove(stil)
        for blip in el.iter(qn("a:blip")):
            alt = blip.get(qn("r:embed"))
            bildpart = tmp_folie.part.related_part(alt)
            blip.set(qn("r:embed"), layout.part.relate_to(bildpart, RT.IMAGE))
        ziel.append(el)


def _rechteck(folie, x, y, b, h, fuellung=None, linie=None, staerke=1.5):
    s = folie.shapes.add_shape(MSO_SHAPE.RECTANGLE, Cm(x), Cm(y), Cm(b), Cm(h))
    s.shadow.inherit = False
    if fuellung:
        s.fill.solid(); s.fill.fore_color.rgb = rgb(fuellung)
    else:
        s.fill.background()
    if linie:
        s.line.color.rgb = rgb(linie); s.line.width = Pt(staerke)
    else:
        s.line.fill.background()
    return s


def _textfeld(folie, x, y, b, h, text, groesse, fett=False, farbe=DUNKEL, abstand=None, anker=MSO_ANCHOR.TOP):
    tb = folie.shapes.add_textbox(Cm(x), Cm(y), Cm(b), Cm(h))
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anker
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    r = tf.paragraphs[0].add_run(); r.text = text
    schrift(r, groesse, fett, farbe, abstand=abstand)
    return tb


def _rahmen(folie, typ):
    """Kopf (Typ-Label mit Streifen, Logo) und Fußlinie."""
    # Typ-Label: Streifen 8 px, unten 35 % grün; Text 16 px fett, gesperrt
    y_mitte = 1.19
    _rechteck(folie, RAND, y_mitte - 0.28, 0.21, 0.56, fuellung=BLAU)
    _rechteck(folie, RAND, y_mitte - 0.28 + 0.56 * 0.65, 0.21, 0.56 * 0.35, fuellung=GRUEN)
    _textfeld(folie, RAND + 0.21 + 0.32, y_mitte - 0.4, 12, 0.8, typ.upper(), 12, fett=True, farbe=BLAU,
              abstand=1.4, anker=MSO_ANCHOR.MIDDLE)
    logo_h = 1.22; logo_b = logo_h * 900 / 484
    folie.shapes.add_picture(str(s.LOGO), Cm(33.867 - RAND - logo_b), Cm(y_mitte - logo_h / 2), Cm(logo_b), Cm(logo_h))
    linie = folie.shapes.add_connector(1, Cm(RAND), Cm(FUSS_Y), Cm(33.867 - RAND), Cm(FUSS_Y))
    linie.line.color.rgb = rgb(LINIE_FUSS); linie.line.width = Pt(0.75)


def _fuss_platzhalter(ph, sid):
    links, rechts = ph["fuss_links"], ph["fuss_rechts"]
    return [
        _sp_platzhalter(sid, "fuss_links", "body", links[0], RAND, FUSS_Y + 0.12, 17, 0.6, 9, farbe=GRAU,
                        prompt=links[2]),
        _sp_platzhalter(sid + 1, "fuss_rechts", "body", rechts[0], 33.867 - RAND - 14, FUSS_Y + 0.12, 14, 0.6, 9,
                        farbe=GRAU, ausr="r", prompt=rechts[2]),
    ]


# Lage der Inhalte (cm), aus dem Entwurf übernommen
EINSTIEG_FLAECHE = (RAND, 2.6, NUTZ, 15.0)
AUFTRAG = {"balken_y": 5.4, "balken_h": 2.95, "text_x": RAND + 0.26 + 0.63, "kasten_y": 11.9, "kasten_h": 2.75}
SICHERUNG = {"leit_y": 4.1, "tab_y": 5.5, "tab_h": 10.3}


def _layouts_bauen(prs):
    master = prs.slide_master
    vorbild = prs.slide_layouts[6]   # „Leer“
    hilf_layout = prs.slide_layouts[6]
    layouts = {}
    for typ in ("Einstieg", "Ihr Auftrag", "Sicherung"):
        layout = _neues_layout(prs, vorbild, typ)
        tmp = prs.slides.add_slide(hilf_layout)
        _rahmen(tmp, typ)
        ph = PLATZHALTER[typ]
        neu = []
        if typ == "Einstieg":
            x, y, b, h = EINSTIEG_FLAECHE
            neu.append(_sp_platzhalter(20, "inhalt", "obj", ph["inhalt"][0], x, y, b, h, 18, farbe=GRAU,
                                       ausr="ctr", anker="ctr", prompt=ph["inhalt"][2]))
        elif typ == "Ihr Auftrag":
            a = AUFTRAG
            _rechteck(tmp, RAND, a["balken_y"], 0.26, a["balken_h"], fuellung=BLAU)
            kb = (NUTZ - 2 * 0.58) / 3
            for i, (label, key) in enumerate((("Sozialform", "sozialform"), ("Unterlagen", "unterlagen"),
                                              ("Abgabe bis", "abgabe"))):
                kx = RAND + i * (kb + 0.58)
                _rechteck(tmp, kx, a["kasten_y"], kb, a["kasten_h"], linie=BLAU if key == "abgabe" else LINIE_HELL)
                _textfeld(tmp, kx + 0.53, a["kasten_y"] + 0.45, kb - 1, 0.5, label.upper(), 10.5, farbe=GRAU,
                          abstand=1.05)
            neu.append(_sp_platzhalter(20, "zitat", "body", ph["zitat"][0], a["text_x"], a["balken_y"],
                                       NUTZ - (a["text_x"] - RAND), a["balken_h"], 30, fett=True, anker="ctr",
                                       zeile=1.0, prompt=ph["zitat"][2]))
            neu.append(_sp_platzhalter(21, "von", "body", ph["von"][0], a["text_x"], a["balken_y"] + a["balken_h"] + 0.2,
                                       20, 0.8, 15, farbe=GRAU_2, prompt=ph["von"][2]))
            neu.append(_sp_platzhalter(22, "ergebnis", "body", ph["ergebnis"][0], a["text_x"], 10.05, NUTZ - 0.9, 0.9,
                                       16.5, prompt=ph["ergebnis"][2]))
            for i, key in enumerate(("sozialform", "unterlagen", "abgabe")):
                kx = RAND + i * (kb + 0.58)
                zeit = key == "abgabe"
                neu.append(_sp_platzhalter(23 + i, key, "body", ph[key][0], kx + 0.53, a["kasten_y"] + 1.0,
                                           kb - 1.0, 1.55, 33 if zeit else 22.5, fett=True,
                                           farbe=BLAU if zeit else DUNKEL, anker="t", prompt=ph[key][2]))
        else:
            s = SICHERUNG
            neu.append(_sp_platzhalter(20, "leitfrage", "body", ph["leitfrage"][0], RAND, s["leit_y"], NUTZ, 1.2,
                                       25.5, fett=True, anker="b", prompt=ph["leitfrage"][2]))
            neu.append(_sp_platzhalter(21, "tabelle", "tbl", ph["tabelle"][0], RAND, s["tab_y"], NUTZ, s["tab_h"],
                                       16, farbe=GRAU, ausr="ctr", anker="ctr", prompt=ph["tabelle"][2]))
        _verschieben(tmp, layout)
        sptree = layout._element.cSld.spTree
        for el in neu + _fuss_platzhalter(ph, 30):
            sptree.append(el)
        _folie_loeschen(prs, tmp)
        # eindeutige Shape-IDs im Layout
        for n, el in enumerate(sptree.iter(qn("p:cNvPr")), start=2):
            el.set("id", str(n))
        layouts[typ] = layout
    # alle Standardlayouts entfernen
    for lay in list(prs.slide_layouts):
        if lay.name not in layouts:
            prs.slide_layouts.remove(lay)
    _master_schrift(master)
    return layouts


def _master_schrift(master):
    """Designschriften des Masters auf Arial setzen."""
    theme = master.part.part_related_by(RT.THEME)
    root = etree.fromstring(theme.blob)
    for tag in ("a:majorFont", "a:minorFont"):
        for el in root.iter(qn(tag)):
            el.find(qn("a:latin")).set("typeface", SCHRIFT)
    theme._blob = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def _folie_loeschen(prs, folie):
    lst = prs.slides._sldIdLst
    for sld in list(lst):
        if prs.part.related_part(sld.rId) is folie.part:
            prs.part.drop_rel(sld.rId); lst.remove(sld)


# ---------------------------------------------------------------- Tabellen
def _zellrand(zelle, farbe, staerke_pt, seiten="LRTB"):
    tcPr = zelle._tc.get_or_add_tcPr()
    for s in "LRTB":
        alt = tcPr.find(qn(f"a:ln{s}"))
        if alt is not None and s in seiten:
            tcPr.remove(alt)
    vor = tcPr.find(qn("a:solidFill")) if tcPr.find(qn("a:solidFill")) is not None else tcPr.find(qn("a:noFill"))
    for s in seiten:
        ln = etree.SubElement(tcPr, qn(f"a:ln{s}"))
        ln.set("w", str(int(Pt(staerke_pt)))); ln.set("cap", "flat"); ln.set("cmpd", "sng")
        if farbe is None:
            etree.SubElement(ln, qn("a:noFill"))
        else:
            fill = etree.SubElement(ln, qn("a:solidFill"))
            etree.SubElement(fill, qn("a:srgbClr")).set("val", farbe)
        etree.SubElement(ln, qn("a:prstDash")).set("val", "solid")
        if vor is not None:
            vor.addprevious(ln)
    # Reihenfolge lnL, lnR, lnT, lnB sicherstellen
    lines = [tcPr.find(qn(f"a:ln{s}")) for s in "LRTB"]
    for ln in lines:
        if ln is not None:
            tcPr.remove(ln)
    for ln in reversed([x for x in lines if x is not None]):
        tcPr.insert(0, ln)


def _zelle(zelle, fuellung="FFFFFF", innen=(0.42, 0.25, 0.42, 0.2)):
    zelle.fill.solid(); zelle.fill.fore_color.rgb = rgb(fuellung)
    zelle.margin_left, zelle.margin_top, zelle.margin_right, zelle.margin_bottom = (Cm(v) for v in innen)
    zelle.vertical_anchor = MSO_ANCHOR.TOP


def _zelltext(zelle, text, groesse, fett=False, farbe=DUNKEL, name=SCHRIFT, ausr=PP_ALIGN.LEFT, abstand=None):
    tf = zelle.text_frame; tf.word_wrap = True
    zeilen = text.split("\n") if isinstance(text, str) else text
    for i, z in enumerate(zeilen):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = ausr
        for r in list(p.runs):
            r._r.getparent().remove(r._r)
        if abstand is None:
            text_mit_fett(p, z, groesse, farbe, name)
        else:
            r = p.add_run(); r.text = z; schrift(r, groesse, fett, farbe, name, abstand=abstand)
        if fett:
            for r in p.runs:
                r.font.bold = True
    return tf


def _tabelle_ohne_stil(tab):
    tbl = tab._tbl
    tblPr = tbl.tblPr
    for att in ("firstRow", "bandRow", "firstCol", "lastRow", "lastCol", "bandCol"):
        if tblPr.get(att) is not None:
            del tblPr.attrib[att]
    sid = tblPr.find(qn("a:tableStyleId"))
    if sid is None:
        sid = etree.SubElement(tblPr, qn("a:tableStyleId"))
    sid.text = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"   # „Kein Formatvorlage, kein Raster“


def sicherungstabelle(platzhalter, kopf, zeilen=2):
    """Tabelle mit blauer Kopfzeile und leeren Zeilen in den Tabellen-Platzhalter setzen."""
    gf = platzhalter.insert_table(rows=zeilen + 1, cols=len(kopf))
    tab = gf.table; _tabelle_ohne_stil(tab)
    ges = platzhalter.width if hasattr(platzhalter, "width") else gf.width
    anteile = [0.33, 0.34, 0.33] if len(kopf) == 3 else [1 / len(kopf)] * len(kopf)
    for i, a in enumerate(anteile):
        tab.columns[i].width = Emu(int(gf.width * a))
    kopf_h = Cm(1.3)
    tab.rows[0].height = kopf_h
    for r in range(1, zeilen + 1):
        tab.rows[r].height = Emu(int((Cm(SICHERUNG["tab_h"]) - kopf_h) / zeilen))
    for c, t in enumerate(kopf):
        z = tab.cell(0, c); _zelle(z, BLAU, (0.42, 0.25, 0.42, 0.2)); z.vertical_anchor = MSO_ANCHOR.MIDDLE
        _zelltext(z, t, 16.5, fett=True, farbe="FFFFFF")
        _zellrand(z, BLAU, 1.5)
        for r in range(1, zeilen + 1):
            zz = tab.cell(r, c); _zelle(zz); _zelltext(zz, "", 16.5)
            _zellrand(zz, LINIE_HELL, 1.5)
    return tab


def telefonnotiz(folie, platzhalter, d):
    """Vordruck Telefonnotiz als Tabelle in die Einstiegsfläche setzen (vertikal mittig)."""
    breiten = [4.53, 15.45, 4.51, 6.84]
    hoehen = [1.2, 1.15, 1.15, 1.15, 4.75]
    x, y, b, h = EINSTIEG_FLAECHE
    ges_h = sum(hoehen)
    gf = folie.shapes.add_table(5, 4, Cm(x), Cm(y + (h - ges_h) / 2), Cm(sum(breiten)), Cm(ges_h))
    platzhalter._element.getparent().remove(platzhalter._element)
    tab = gf.table; _tabelle_ohne_stil(tab)
    for i, w in enumerate(breiten):
        tab.columns[i].width = Cm(w)
    for i, hh in enumerate(hoehen):
        tab.rows[i].height = Cm(hh)
    tab.cell(0, 0).merge(tab.cell(0, 1)); tab.cell(0, 2).merge(tab.cell(0, 3))
    for r in (1, 2, 3, 4)[1:]:
        tab.cell(r, 1).merge(tab.cell(r, 3))
    for r in range(5):
        for c in range(4):
            z = tab.cell(r, c); _zelle(z, innen=(0.32, 0.18, 0.32, 0.1))
            _zellrand(z, LINIE_VD, 0.75)
    # Kopf
    k = tab.cell(0, 0); k.vertical_anchor = MSO_ANCHOR.MIDDLE
    _zelltext(k, d["titel"], 18, fett=True, abstand=2.5)
    k2 = tab.cell(0, 2); k2.vertical_anchor = MSO_ANCHOR.MIDDLE
    _zelltext(k2, d["betrieb"], 12, ausr=PP_ALIGN.RIGHT)
    for c in range(4):
        _zellrand(tab.cell(0, c), DUNKEL, 1.5, "TB")
    labels = [(1, 0, "Datum / Uhrzeit"), (1, 2, "angenommen von"), (2, 0, "Anrufer"), (3, 0, "Anliegen"), (4, 0, "Notiz")]
    for r, c, t in labels:
        _zelltext(tab.cell(r, c), t, 11, farbe=GRAU_2)
    _zelltext(tab.cell(1, 1), d["datum"], 18)
    _zelltext(tab.cell(1, 3), d["angenommen"], 18)
    _zelltext(tab.cell(2, 1), d["anrufer"], 18)
    p = _zelltext(tab.cell(3, 1), "", 18).paragraphs[0]
    for i, (t, an) in enumerate(d["anliegen"]):
        r = p.add_run(); r.text = ("   " if i else "") + ("☑" if an else "☐") + "\ufe0e\u00a0"
        schrift(r, 18, name=SYMBOL)
        r = p.add_run(); r.text = t; schrift(r, 18)
    tf = _zelltext(tab.cell(4, 1), ["– " + z for z in d["notiz"]], 19, farbe=HAND_FARBE, name=HAND)
    for p in tf.paragraphs:
        p.line_spacing = 1.25
    # Außenrand schwarz 2 px
    for r in range(5):
        _zellrand(tab.cell(r, 0), DUNKEL, 1.5, "L"); _zellrand(tab.cell(r, 3), DUNKEL, 1.5, "R")
    for c in range(4):
        _zellrand(tab.cell(4, c), DUNKEL, 1.5, "B")
    # Rand-Fix: rechte Randzellen in verbundenen Zeilen sitzen in Spalte 1 (Ursprungszelle)
    for r in (2, 3, 4):
        _zellrand(tab.cell(r, 1), DUNKEL, 1.5, "R")
    _zellrand(tab.cell(0, 2), DUNKEL, 1.5, "R")
    _zellrand(tab.cell(0, 0), None, 0, "R"); _zellrand(tab.cell(0, 2), None, 0, "L")
    return tab


# ---------------------------------------------------------------- Befüllung
# Höchstlänge je Feld (Zeichen), damit nichts überläuft (gemessen an der Vorschau, Arial)
GRENZEN = {"zitat": 120, "von": 60, "ergebnis": 100, "sozialform": 22, "unterlagen": 22, "abgabe": 12,
           "leitfrage": 60, "fuss_links": 90, "fuss_rechts": 90}


def _platzhalter(folie, idx):
    for ph in folie.placeholders:
        if ph.placeholder_format.idx == idx:
            return ph
    raise KeyError(idx)


def folie_anlegen(prs, typ, werte):
    """Neue Folie aus dem Layout `typ`; `werte` = {schlüssel: text | callable(folie, platzhalter)}."""
    layout = next(l for l in prs.slide_layouts if l.name == typ)
    folie = prs.slides.add_slide(layout)
    for key, (idx, _, _) in PLATZHALTER[typ].items():
        ph = _platzhalter(folie, idx)
        ph.name = key
        if key not in werte:
            continue
        wert = werte[key]
        if not callable(wert) and len(str(wert).replace("**", "")) > GRENZEN.get(key, 10 ** 6):
            print(f"WARNUNG {typ}/{key}: {len(str(wert))} Zeichen, höchstens {GRENZEN[key]} (läuft über)",
                  file=sys.stderr)
        if callable(wert):
            wert(folie, ph)
        else:
            tf = ph.text_frame
            for i, zeile in enumerate(str(wert).split("\n")):
                p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                for teil_i, teil in enumerate(zeile.split("**")):
                    if teil:
                        r = p.add_run(); r.text = teil
                        if teil_i % 2:
                            r.font.bold = True
    return folie


def befuellen(vorlage, ziel, folien):
    """Vorlage öffnen, Beispielfolien entfernen, `folien` = [(typ, werte), …] aus den Layouts bauen."""
    prs = Presentation(str(vorlage))
    for folie in list(prs.slides):
        _folie_loeschen(prs, folie)
    for typ, werte in folien:
        folie_anlegen(prs, typ, werte)
    prs.save(str(ziel))
    return ziel


# ---------------------------------------------------------------- Vorlage und Muster
def vorlage(pfad=VORLAGE):
    prs = Presentation()
    prs.slide_width, prs.slide_height = B, H
    _layouts_bauen(prs)
    for typ, felder in PLATZHALTER.items():
        werte = {k: "{{ " + k + " }}" for k in felder if k not in ("inhalt", "tabelle")}
        if typ == "Einstieg":
            werte["inhalt"] = "{{ inhalt }}  (Bild oder Tabelle)"
        if typ == "Sicherung":
            werte["tabelle"] = lambda f, ph: sicherungstabelle(ph, ["{{ spalte_1 }}", "{{ spalte_2 }}", "{{ spalte_3 }}"])
        folie_anlegen(prs, typ, werte)
    prs.core_properties.title = "Vorlage Impulsfolien"
    prs.core_properties.author = s.SCHULE["name"].replace(" – ", " ")
    prs.save(str(pfad))
    return pfad


def muster_daten():
    fuss = "LF 1 · LS 3 · Der Temperaturfühler zeigt falsche Werte"
    notiz = {"titel": "TELEFONNOTIZ", "betrieb": "Brinkmann Automation GmbH · Kundendienst",
             "datum": "13.10.2026 · 07:42 Uhr", "angenommen": "K. Lüken",
             "anrufer": "Hr. Ostendorf, Schichtleitung Linie 2 · Nordland Feinkost GmbH",
             "anliegen": [("Störung", True), ("Wartung", False), ("Angebot", False), ("bitte zurückrufen: heute", True)],
             "notiz": ["seit Umbau im Sept. an SG-2 Siegelnähte undicht, 3 Paletten gesperrt",
                       "Steuerung zeigt die ganze Zeit 180 °C = Sollwert",
                       "Prüfthermometer an der Heizbacke: nur ca. 172 °C!",
                       "Folie i. O. laut Hersteller (177 – 183 °C)"]}
    return [
        ("Einstieg", {"inhalt": lambda f, ph: telefonnotiz(f, ph, notiz), "fuss_links": fuss,
                      "fuss_rechts": "Brinkmann Automation und Nordland Feinkost sind fiktiv · KI-gestützt erstellt"}),
        ("Ihr Auftrag", {"zitat": "„Klären Sie die Reklamation und geben Sie dem Kunden eine begründete Empfehlung.“",
                         "von": "Meisterin K. Lüken",
                         "ergebnis": "Ergebnis: **Empfehlung an den Kunden** im Prüfprotokoll (Anlage 5, Seite 2)",
                         "sozialform": "Partnerarbeit", "unterlagen": "Anlage 1 bis 3", "abgabe": "10:15 Uhr",
                         "fuss_links": fuss, "fuss_rechts": "KI-gestützt erstellt"}),
        ("Sicherung", {"leitfrage": "Was sagen wir dem Kunden?",
                       "tabelle": lambda f, ph: sicherungstabelle(ph, ["Ursache", "Beleg (Messung, Rechnung)", "Empfehlung"]),
                       "fuss_links": fuss, "fuss_rechts": "KI-gestützt erstellt"}),
    ]


def vorschau(pptx, praefix, dpi=80):
    pptx = Path(pptx)
    for alt in Path(praefix).parent.glob(Path(praefix).name + "-*.png"):
        alt.unlink()
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", tmp, str(pptx)],
                       check=True, capture_output=True, timeout=180)
        subprocess.run(["pdftoppm", "-png", "-r", str(dpi), str(Path(tmp) / (pptx.stem + ".pdf")), str(praefix)],
                       check=True)
    return sorted(Path(praefix).parent.glob(Path(praefix).name + "-*.png"))


if __name__ == "__main__":
    MUSTER_ORDNER.mkdir(parents=True, exist_ok=True)
    vorlage(VORLAGE)
    muster = befuellen(VORLAGE, MUSTER_ORDNER / "Muster_folien.pptx", muster_daten())
    for png in vorschau(muster, MUSTER_ORDNER / "vorschau_folien"):
        print(png)
    print("fertig")
