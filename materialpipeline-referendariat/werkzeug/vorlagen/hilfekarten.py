"""Vorlage Hilfekarten (abgenommen 2026-10-13), Schulkopf nach Profil (schule.*).

Aufruf: python werkzeug/vorlagen/hilfekarten.py
Erzeugt vorlagen/Vorlage_hilfekarten.docx, docs/stilreferenz/vorlagen/muster/Muster_hilfekarten.docx
und die PNG-Vorschau. Vorbild: hilfekarten_entwurf.png / entwurf/hilfekarten.html.

A4-Bogen: Kopf wie Arbeitsblatt, Schild „Anlage n · Hilfekarten“ ohne Namensfeld, grüner Hinweis zur
Nutzung, Karten mit gestrichelten Schnittlinien: eine Spalte je Aufgabe, eine Zeile je Stufe
(Tipp, Ansatz, Lösungsweg) mit Stufenpunkten ●○○.

Daten (Kontext):
  beruf, lf, lf_titel, ls, ls_titel, nr, titel, quellen (optional), ki_hinweis
  stufen: Liste von {nr (1–3), name, karten: Liste von {aufgabe, text}}; je Stufe eine Karte pro Aufgabe.
k.text mit Formelzeichen und **fett** wird über formel() zu RichText (rendern() erledigt das).
"""
import sys
from pathlib import Path

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt
from docxtpl import DocxTemplate

sys.path.insert(0, str(Path(__file__).parent))
import schule as s  # noqa: E402
from arbeitsblatt import (GRUEN_HELL, RGB_GRUEN_DUNKEL, als_richtext, bauen, buendig,  # noqa: E402
                          fuss, kopfdaten, rahmenlinie, titel, zellabstand)
from vorlagen_bauen import rahmen, schattieren, tabelle_ohne_rahmen  # noqa: E402

SCHNITT = (12, "8A929E")


def ohne_zellbreite(tab):
    """tcW entfernen: Spaltenbreiten kommen aus tblGrid (docxtpl passt sie bei {%tc for %} an)."""
    for tc in tab._tbl.iter(qn("w:tc")):
        w = tc.tcPr.find(qn("w:tcW")) if tc.tcPr is not None else None
        if w is not None:
            tc.tcPr.remove(w)


def tabellenbreite(tab, cm=None, prozent=None, fest=True):
    tblPr = tab._tbl.tblPr
    w = tblPr.find(qn("w:tblW"))
    if w is None:
        w = OxmlElement("w:tblW"); tblPr.append(w)
    if prozent:
        w.set(qn("w:w"), str(int(prozent * 50))); w.set(qn("w:type"), "pct")
    else:
        w.set(qn("w:w"), str(int(cm * 567))); w.set(qn("w:type"), "dxa")
    if fest:
        lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed")
        w.addnext(lay)


def raster(tab, breiten_cm):
    for gc, b in zip(tab._tbl.tblGrid.findall(qn("w:gridCol")), breiten_cm):
        gc.set(qn("w:w"), str(int(b * 567)))


def hinweis(doc, breite):
    """Grüner Hinweiskasten zur Nutzung der Karten (fester Wortlaut, abgenommen)."""
    t = doc.add_table(1, 2)
    links, rechts = t.rows[0].cells
    for z in (links, rechts):
        schattieren(z, GRUEN_HELL)
    rahmen(links, left=(36, s.GRUEN))
    rahmen(rechts)
    zellabstand(links, 0.2, 0.2, 0.35, 0.05)
    zellabstand(rechts, 0.2, 0.2, 0.15, 0.3)
    s.senkrecht(links)
    s.lauf(s.abstand(links.paragraphs[0]), "💡", 12)
    p = s.abstand(rechts.paragraphs[0], 0, 0, 1.25)
    s.lauf(p, "So nutzen Sie die Hilfekarten: ", 10, fett=True, farbe=RGB_GRUEN_DUNKEL)
    s.lauf(p, "Versuchen Sie es zuerst allein. Kommen Sie nicht weiter, nehmen Sie ", 10)
    s.lauf(p, "Karte 1 (Tipp)", 10, fett=True, farbe=RGB_GRUEN_DUNKEL)
    s.lauf(p, ". Reicht das nicht, Karte 2 (Ansatz), erst zuletzt Karte 3 (Lösungsweg). "
              "Jede Karte gilt nur für ihre Aufgabe.", 10)
    s.feste_breiten(t, [1.0, breite - 1.0])
    buendig(t)
    return t


def karten(doc, breite, hoehe_cm=6.0):
    """Kartenraster: {%tr for st in stufen %} Zeilen, {%tc for k in st.karten %} Spalten."""
    t = doc.add_table(3, 3)
    tabelle_ohne_rahmen(t)
    t.autofit = False
    for i in (0, 2):
        for z in t.rows[i].cells:
            s.abstand(z.paragraphs[0])
    s.lauf(t.cell(0, 0).paragraphs[0], "{%tr for st in stufen %}", 6)
    s.lauf(t.cell(2, 0).paragraphs[0], "{%tr endfor %}", 6)
    s.lauf(s.abstand(t.cell(1, 0).paragraphs[0]), "{%tc for k in st.karten %}", 6)
    s.lauf(s.abstand(t.cell(1, 2).paragraphs[0]), "{%tc endfor %}", 6)
    s.zeilenhoehe(t.rows[1], hoehe_cm)
    z = t.cell(1, 1)
    rahmenlinie(z, "dashed", top=SCHNITT, bottom=SCHNITT, left=SCHNITT, right=SCHNITT)
    zellabstand(z, 0.3, 0.2, 0.4, 0.4)
    # Kopfzeile der Karte: links Stufe, rechts Aufgabe (innere Tabelle über 100 % Breite)
    innen = z.add_table(1, 2)
    tabelle_ohne_rahmen(innen)
    ohne_zellbreite(innen)
    tabellenbreite(innen, prozent=100, fest=False)
    a, b = innen.rows[0].cells
    raster(innen, [6.0, 2.0])
    for zelle, anteil in ((a, 75), (b, 25)):
        tcW = OxmlElement("w:tcW"); tcW.set(qn("w:w"), str(anteil * 50)); tcW.set(qn("w:type"), "pct")
        zelle._tc.get_or_add_tcPr().insert(0, tcW)
        zellabstand(zelle, 0, 0, 0, 0)
    s.senkrecht(a, "bottom"); s.senkrecht(b, "bottom")
    s.lauf(s.abstand(a.paragraphs[0]), "Hilfe {{ st.nr }} · {{ st.name }}", 12.5, fett=True, farbe=s.RGB_BLAU)
    p = s.abstand(b.paragraphs[0])
    p.alignment = 2  # rechts
    s.lauf(p, "Aufgabe {{ k.aufgabe }}", 8.5, farbe=s.RGB_GRAU)
    s.abstand(z.paragraphs[0]).paragraph_format.line_spacing = Pt(1)
    # Stufenpunkte und Text
    p = s.abstand(z.paragraphs[-1], 3, 5)
    r = s.lauf(p, "{{ '●' * st.nr }}{{ '○' * (3 - st.nr) }}", 12, farbe=s.RGB_BLAU)
    sp = OxmlElement("w:spacing"); sp.set(qn("w:val"), "50"); r._r.get_or_add_rPr().append(sp)
    s.lauf(s.abstand(z.add_paragraph(), 0, 0, 1.4), "{{r k.text }}", 10.5)
    tabellenbreite(t, cm=breite)
    raster(t, [breite / 3] * 3)
    ohne_zellbreite(t)
    buendig(t)
    return t


def vorlage(pfad):
    doc = s.dokument("A4")
    b = s.nutzbreite(doc)
    buendig(s.kopf(doc))
    fuss(doc, "Anlage {{ nr }} · Hilfekarten · {{ titel }} {%- if fiktiv %} · {{ fiktiv }}{% endif %}")
    s.leer(doc, 8)
    titel(doc, "Anlage {{ nr }} · Hilfekarten", "Hilfekarten zu „{{ titel }}“", namensfeld=False)
    s.wozu(doc)
    hinweis(doc, b)
    p = s.abstand(doc.add_paragraph(), 5, 6)
    s.lauf(p, "✂ entlang der gestrichelten Linien ausschneiden", 8.5, farbe=s.RGB_GRAU)
    karten(doc, b)
    doc.save(pfad)


def rendern(vorlage_pfad, daten, ziel):
    d = dict(daten)
    d["stufen"] = [dict(st, nr=int(st["nr"]),
                        karten=[dict(k, text=als_richtext(k["text"], groesse=10.5)) for k in st["karten"]])
                   for st in d["stufen"]]
    t = DocxTemplate(vorlage_pfad)
    t.render(d)
    t.save(ziel)


def muster_daten():
    return dict(kopfdaten(), **{
        "wozu": "Hilfe, wenn Sie allein nicht weiterkommen: so viel wie nötig, so wenig wie möglich.",
        "quellen": "Stoffwerte nach Tabellenbuch Elektrotechnik (Europa-Lehrmittel)",
        "stufen": [
            {"nr": 1, "name": "Tipp", "karten": [
                {"aufgabe": "1", "text": "Der Strom fließt vom Pt100-Eingang zum Fühler hin **und wieder zurück**. "
                                         "Wie lang ist der ganze Weg, den der Strom durch Kupfer zurücklegt?"},
                {"aufgabe": "2", "text": "Die Steuerung kann nicht unterscheiden, ob ein Ohm vom Pt100 oder von der "
                                         "Leitung kommt. Wie viel Ohm bedeutet beim Pt100 ein Kelvin?"}]},
            {"nr": 2, "name": "Ansatz", "karten": [
                {"aufgabe": "1", "text": "R_L = ρ · l_{ges} / A  mit  l_{ges} = 2 · 45 m\n"
                                         "Setzen Sie ρ in Ω·mm²/m und A in mm² ein. Dann kürzen sich mm² und m."},
                {"aufgabe": "2", "text": "Δϑ = R_L / Steigung  mit  Steigung = 0,385 Ω/K\n"
                                         "Achten Sie darauf, dass sich Ω kürzt und K übrig bleibt."}]},
            {"nr": 3, "name": "Lösungsweg", "karten": [
                {"aufgabe": "1", "text": "l_{ges} = 2 · 45 m = 90 m\n"
                                         "R_L = 0,0178 Ω·mm²/m · 90 m / 0,5 mm²\n"
                                         "R_L = 3,20 Ω ≈ **3,2 Ω**"},
                {"aufgabe": "2", "text": "Δϑ = 3,20 Ω / 0,385 Ω/K\n"
                                         "Δϑ = 8,3 K\n"
                                         "Die Steuerung zeigt **rund 8 K zu viel** an."}]},
        ],
    })


if __name__ == "__main__":
    bauen("hilfekarten", vorlage, muster_daten(), rendern)
