"""Vorlage Arbeitsblatt (abgenommen 2026-10-13), Schulkopf nach Profil (schule.*).

Aufruf: python werkzeug/vorlagen/arbeitsblatt.py
Erzeugt vorlagen/Vorlage_arbeitsblatt.docx (docxtpl-Platzhalter),
docs/stilreferenz/vorlagen/muster/Muster_arbeitsblatt.docx (DS 7) und die PNG-Vorschau.

Gestaltung nach docs/regeln/stilregeln.md und dem Vorbild arbeitsblatt_seite.png:
Kopf Variante C, Schild „Anlage n · Arbeitsblatt“, Titel, Namensblock, „Wozu?“-Zeile,
Situation als Kasten, Aufgaben in einer Schleife. Kein gegeben/gesucht, keine Kennzeile, kein Ziel.

Daten (Kontext):
  beruf, lf, lf_titel, ls, ls_titel, nr, titel, wozu, situation, quellen, ki_hinweis
  aufgaben: Liste von {nr, operator, text, zeilen (Kästchenzeilen, mind. 8), rechenfeld (Standard ja),
            antwortsatz (ja/nein), skizzenfeld (ja/nein)}
Felder mit Formelzeichen (situation, a.text) werden über formel() zu RichText:
  „R_L“ → R mit tiefgestelltem L, „l_{ges}“ für mehrere Zeichen, „**fett**“, Zeilenumbruch „\\n“.
rendern() erledigt das automatisch.
"""
import re
import sys
from pathlib import Path

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor
from docxtpl import DocxTemplate, RichText

sys.path.insert(0, str(Path(__file__).parent))
import schule as s  # noqa: E402
from vorlagen_bauen import rahmen, schattieren  # noqa: E402

VORLAGEN = s.WURZEL / "vorlagen"
MUSTER = s.WURZEL / "docs" / "stilreferenz" / "vorlagen" / "muster"
GRUEN_HELL, GRUEN_DUNKEL = "EEF9EE", "2E7D32"
RGB_GRUEN_DUNKEL = RGBColor.from_string(GRUEN_DUNKEL)
KI_HINWEIS = "KI-gestützt erstellt; Werkzeug, Version und Datum siehe KI-Verzeichnis."


# ---------------------------------------------------------------- gemeinsame Hilfen (auch für Hilfekarten,
# Erwartungshorizont, Selbstkontrolle)
def formel(text, groesse=10.5, farbe=None, fett=False, schrift="Arial"):
    """Text → RichText mit echten Indizes: R_L, l_{ges}; **fett**; \\n als Zeilenumbruch."""
    rt = RichText()
    farbe = farbe if farbe is None or isinstance(farbe, str) else str(farbe)
    opt = dict(size=int(groesse * 2), font=schrift, color=farbe)

    def teil(t, b=False, sub=False):
        if t:
            rt.add(t, bold=fett or b, subscript=sub, **opt)

    def normal(t, b=False):
        pos = 0
        for m in re.finditer(r"([A-Za-zΔϑρα])_(\{[^}]+\}|[A-Za-z0-9]+)", t):
            teil(t[pos:m.start()] + m.group(1), b)
            teil(m.group(2).strip("{}"), b, True)
            pos = m.end()
        teil(t[pos:], b)

    pos = 0
    for m in re.finditer(r"\*\*(.+?)\*\*", text):
        normal(text[pos:m.start()])
        normal(m.group(1), True)
        pos = m.end()
    normal(text[pos:])
    return rt


def als_richtext(wert, **kw):
    return wert if isinstance(wert, RichText) else formel(str(wert), **kw)


def zellabstand(zelle, oben=0.05, unten=0.05, links=0.15, rechts=0.15):
    """Innenabstand der Zelle (Word: start/end, LibreOffice: left/right)."""
    tcPr = zelle._tc.get_or_add_tcPr()
    mar = OxmlElement("w:tcMar")
    for seite, wert in (("top", oben), ("left", links), ("start", links), ("bottom", unten),
                        ("right", rechts), ("end", rechts)):
        el = OxmlElement(f"w:{seite}")
        el.set(qn("w:w"), str(int(wert * 567))); el.set(qn("w:type"), "dxa")
        mar.append(el)
    tcPr.append(mar)


def rahmenlinie(zelle, art="dashed", **seiten):
    """Wie rahmen(), aber mit Linienart (dashed, dotted …): seiten=(staerke, farbe) oder None."""
    tcPr = zelle._tc.get_or_add_tcPr()
    alt = tcPr.find(qn("w:tcBorders"))
    if alt is not None:
        tcPr.remove(alt)
    b = OxmlElement("w:tcBorders")
    for seite in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{seite}")
        wert = seiten.get(seite)
        if wert is None:
            el.set(qn("w:val"), "nil")
        else:
            el.set(qn("w:val"), art); el.set(qn("w:sz"), str(wert[0])); el.set(qn("w:color"), wert[1])
        b.append(el)
    tcPr.append(b)


def buendig(tab, cm=0.19):
    """Tabelle bündig zum Satzspiegel (tblInd), statt um den Zellabstand nach links versetzt."""
    tblPr = tab._tbl.tblPr
    alt = tblPr.find(qn("w:tblInd"))
    if alt is not None:
        tblPr.remove(alt)
    ind = OxmlElement("w:tblInd"); ind.set(qn("w:w"), str(int(cm * 567))); ind.set(qn("w:type"), "dxa")
    nach = [tblPr.find(qn(f"w:{n}")) for n in ("tblBorders", "shd", "tblLayout", "tblCellMar", "tblLook")]
    nach = [n for n in nach if n is not None]
    if nach:
        nach[0].addprevious(ind)
    else:
        tblPr.append(ind)
    return tab


def tag(ziel, text):
    """Absatz nur für einen Jinja-Absatz-Tag ({%p … %}), klein und ohne Abstand."""
    p = s.abstand(ziel.add_paragraph())
    s.lauf(p, text, 6)
    return p


def kasten(doc, titel, inhalt, fuellung=s.BLAU_HELL, randfarbe=s.BLAU, titelfarbe=s.RGB_BLAU,
           breite=None, groesse=10.5, titel_im_text=False):
    """Hinweis-/Situationskasten: farbige Fläche, dicker Balken links."""
    breite = breite or s.nutzbreite(doc)
    t = doc.add_table(1, 1)
    z = t.cell(0, 0)
    schattieren(z, fuellung)
    rahmen(z, left=(36, randfarbe))
    zellabstand(z, 0.2, 0.2, 0.45, 0.3)
    p = s.abstand(z.paragraphs[0], 0, 1, 1.25)
    s.lauf(p, titel + (" " if titel_im_text else ""), groesse if titel_im_text else 9.5, fett=True, farbe=titelfarbe)
    if not titel_im_text:
        p = s.abstand(z.add_paragraph(), 0, 0, 1.3)
    s.lauf(p, inhalt, groesse)
    s.feste_breiten(t, [breite])
    buendig(t)
    return t


def fuss(doc, links, quellen="{{ quellen }}", ki="{{ ki_hinweis }}", bedingt=True):
    """Fußzeile wie im Vorbild: Datei, Quellen (nur wenn vorhanden), KI-Hinweis; rechts Seite x von y."""
    t = buendig(s.fusszeile(doc, links=links, quellen=None, ki=None))
    li, re_ = t.rows[0].cells
    zellabstand(li, 0.08, 0, 0, 0.1)
    zellabstand(re_, 0.08, 0, 0.1, 0)
    if quellen:
        if bedingt:
            tag(li, "{%p if quellen %}")
        s.lauf(s.abstand(li.add_paragraph()), "Quellen: " + quellen, 7, farbe=s.RGB_GRAU)
        if bedingt:
            tag(li, "{%p endif %}")
    if ki:
        s.lauf(s.abstand(li.add_paragraph()), ki, 6.5, farbe=s.RGB_GRAU, kursiv=True)
    return t


def titel(doc, schild, titeltext="{{ titel }}", namensfeld=True, titelgroesse=18):
    """schule.titelzeile, bündig zum Satzspiegel (Titel links, Namensblock rechts auf Kante)."""
    t = buendig(s.titelzeile(doc, schild, titeltext, namensfeld=namensfeld, titelgroesse=titelgroesse))
    zellen = t.rows[0].cells
    zellabstand(zellen[0], 0, 0, 0, 0.15)
    if namensfeld:
        zellabstand(zellen[1], 0, 0, 0.15, 0)
    return t


def schild_farbe(titel_tabelle, farbe):
    """Färbt das Anlage-Schild der Titelzeile um (z. B. grau beim Erwartungshorizont)."""
    for shd in titel_tabelle._tbl.iter(qn("w:shd")):
        if shd.getparent().tag == qn("w:rPr"):
            shd.set(qn("w:fill"), farbe)


def bauen(name, vorlage_fn, daten, rendern_fn):
    """Vorlage, Muster und Vorschau einer Materialart erzeugen."""
    VORLAGEN.mkdir(exist_ok=True); MUSTER.mkdir(parents=True, exist_ok=True)
    v = VORLAGEN / f"Vorlage_{name}.docx"
    vorlage_fn(v)
    m = MUSTER / f"Muster_{name}.docx"
    rendern_fn(v, daten, m)
    for alt in MUSTER.glob(f"vorschau_{name}-*.png"):
        alt.unlink()
    pngs = s.vorschau(m, MUSTER / f"vorschau_{name}")
    print(v, m, *pngs, sep="\n")
    return pngs


# ---------------------------------------------------------------- Arbeitsblatt
def rechenfeld(doc, breite=18.0, raster=0.5):
    """Kästchenraster 5 mm; Zeilenzahl aus a.zeilen (mindestens 8) per {%tr for %}."""
    spalten = int(breite / raster)
    t = doc.add_table(3, spalten)
    t.autofit = False
    for i, zeile in enumerate(t.rows):
        s.zeilenhoehe(zeile, raster, genau=(i == 1))
        for z in zeile.cells:
            s.zellrand(z, 2, "C9D3E6")
            zellabstand(z, 0, 0, 0, 0)
            p = s.abstand(z.paragraphs[0])
            p.paragraph_format.line_spacing = Pt(2)
    s.lauf(t.cell(0, 0).paragraphs[0], "{%tr for z in range([a.zeilen|default(8), 8]|max) %}", 5)
    s.lauf(t.cell(2, 0).paragraphs[0], "{%tr endfor %}", 5)
    s.feste_breiten(t, [raster] * spalten)
    buendig(t)
    return t


def vorlage(pfad):
    doc = s.dokument("A4")
    b = s.nutzbreite(doc)
    buendig(s.kopf(doc))
    fuss(doc, "Anlage {{ nr }} · {{ titel }} {%- if fiktiv %} · {{ fiktiv }}{% endif %}")
    titel(doc, "Anlage {{ nr }} · Arbeitsblatt")
    s.wozu(doc)
    kasten(doc, "Situation", "{{r situation }}", breite=b)
    tag(doc, "{%p for a in aufgaben %}")
    p = s.abstand(doc.add_paragraph(), 12, 1)
    s.lauf(p, "Aufgabe {{ a.nr }}  ", 11, fett=True, farbe=s.RGB_BLAU)
    s.lauf(p, "{{ a.operator }} ", 11, fett=True)
    s.lauf(p, "{{r a.text }}", 11)
    tag(doc, "{%p if a.rechenfeld|default(true) %}")
    s.lauf(s.abstand(doc.add_paragraph(), 2, 2), "Rechnung:", 8.5, farbe=s.RGB_GRAU)
    rechenfeld(doc, b)
    tag(doc, "{%p endif %}")
    tag(doc, "{%p if a.skizzenfeld %}")
    s.lauf(s.abstand(doc.add_paragraph(), 2, 2), "Skizze:", 8.5, farbe=s.RGB_GRAU)
    sk = doc.add_table(1, 1)
    s.zellrand(sk.cell(0, 0), 4, "C9D3E6")
    s.zeilenhoehe(sk.rows[0], 6.0)
    s.feste_breiten(sk, [b]); buendig(sk)
    tag(doc, "{%p endif %}")
    tag(doc, "{%p if a.antwortsatz %}")
    s.lauf(s.abstand(doc.add_paragraph(), 5, 0), "Antwortsatz:", 8.5, farbe=s.RGB_GRAU)
    buendig(s.schreiblinien(doc, 2, 0.85, b))
    tag(doc, "{%p endif %}")
    tag(doc, "{%p endfor %}")
    doc.save(pfad)


def rendern(vorlage_pfad, daten, ziel):
    d = dict(daten)
    d["situation"] = als_richtext(d["situation"], groesse=10.5)
    d["aufgaben"] = [dict(a, text=als_richtext(a["text"], groesse=11)) for a in d["aufgaben"]]
    t = DocxTemplate(vorlage_pfad)
    t.render(d)
    t.save(ziel)


def kopfdaten():
    return {
        "beruf": "Elektroniker/in, Fachrichtung Automatisierungs- und Systemtechnik",
        "lf": "1", "lf_titel": "Elektrotechnische Systeme analysieren und Funktionen prüfen",
        "ls": "3", "ls_titel": "Der Temperaturfühler zeigt falsche Werte",
        "nr": "4", "titel": "Leitungswiderstand und Messfehler",
        "fiktiv": "Nordland Feinkost und Brinkmann Automation sind fiktiv.",
        "ki_hinweis": KI_HINWEIS,
    }


def muster_daten():
    return dict(kopfdaten(), **{
        "wozu": "Sie klären rechnerisch, ob die neue Zuleitung die Abweichung erklären kann, "
                "damit Meisterin Lüken dem Kunden eine belastbare Antwort geben kann.",
        "situation": "Nordland Feinkost meldet: „Seit dem Umbau zeigt die Steuerung der Siegelstation rund 8 °C "
                     "mehr an.“ Der Pt100 wurde 45 m entfernt neu montiert (Zuleitung 2 × 0,5 mm², Kupfer). "
                     "Meisterin Lüken möchte wissen, ob die Leitung der Grund ist.",
        "aufgaben": [
            {"nr": "1", "operator": "Berechnen Sie", "text": "den Widerstand der Zuleitung (Hin- und Rückleiter).",
             "zeilen": 12, "antwortsatz": False},
            {"nr": "2", "operator": "Berechnen Sie", "text": "um wie viel Kelvin die Steuerung deshalb zu viel anzeigt.",
             "zeilen": 12, "antwortsatz": True},
        ],
        "quellen": "eigene Darstellung; Stoffwerte nach Tabellenbuch Elektrotechnik (Europa-Lehrmittel)",
    })


if __name__ == "__main__":
    bauen("arbeitsblatt", vorlage, muster_daten(), rendern)
