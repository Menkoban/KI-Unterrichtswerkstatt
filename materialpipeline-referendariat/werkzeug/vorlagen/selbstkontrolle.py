"""Vorlage Selbstkontroll-Karte A6 quer (abgenommen 2026-10-13, Mischung B/C), Schulkopf nach Profil (schule.*).

Aufruf: python werkzeug/vorlagen/selbstkontrolle.py
Erzeugt vorlagen/Vorlage_selbstkontrolle.docx, docs/stilreferenz/vorlagen/muster/Muster_selbstkontrolle.docx
und die PNG-Vorschau. Vorbild: selbstkontrolle_BC.png / entwurf/selbstkontrolle_BC.html.

Aufbau: Mini-Kopf (Farbstreifen Blau/Grün, kleines Logo, Anlage-Zeile, Titel, LF · LS rechts), „Wozu?“,
Aussagen in Ich-Form mit vierstufiger Skala (jede Stufe über ihrer eigenen Kreis-Spalte), Hinweiszeile;
in der Fußzeile die gestrichelte Falzlinie mit Text, darunter die Ergebnisse um 180° gedreht, KI-Hinweis.
Falz und Ergebnisse stehen in der Fußzeile, damit sie immer am unteren Kartenrand sitzen.
Die gedrehten Ergebnisse sind eine Grafik: Ein um 180° gedrehtes Textfeld (DrawingML rot=10800000)
zeigt LibreOffice nicht kopfüber an. Die Vorlage trägt dort den Platzhalter {{ ergebnisse_bild }};
rendern() zeichnet die Grafik aus „ergebnisse“ (ergebnisbild()) und setzt sie als InlineImage ein.

Daten (Kontext):
  lf, ls, nr, titel, wozu, hinweis, ki_hinweis
  aussagen: Liste von Texten (Ich-Form)
  ergebnisse: Liste von {nr, wert, toleranz}; je zwei nebeneinander
Texte mit Formelzeichen werden über formel() zu RichText (rendern() erledigt das).
"""
import re
import sys
import tempfile
from pathlib import Path

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docxtpl import DocxTemplate, InlineImage
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import schule as s  # noqa: E402
from arbeitsblatt import KI_HINWEIS, als_richtext, bauen, buendig, rahmenlinie, zellabstand  # noqa: E402
from vorlagen_bauen import rahmen, schattieren, tabelle_ohne_rahmen  # noqa: E402

GRAU_TEXT = RGBColor.from_string("4A5563")
RAND = (4, "C9CED6")
SKALA = ("trifft\nzu", "trifft\neher zu", "trifft eher\nnicht zu", "trifft\nnicht zu")
KREIS = 1.2          # Breite einer Kreis-Spalte (cm)
BREITE_ERGEBNIS = 13.2  # Breite der Ergebnisgrafik (cm) = Nutzbreite A6 quer
EMU = 360000
SCHRIFT_DATEI = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"  # metrisch wie Arial
SCHRIFT_FETT = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"


def text_mit_umbruch(p, text, groesse, **kw):
    teile = text.split("\n")
    for i, t in enumerate(teile):
        r = s.lauf(p, t, groesse, **kw)
        if i < len(teile) - 1:
            r.add_break()


def seitenrand_gestrichelt(doc, abstand_pt=7, farbe="8A929E"):
    """Gestrichelte Schnittlinie um die Karte (Seitenrand, gemessen vom Blattrand)."""
    sectPr = doc.sections[0]._sectPr
    b = OxmlElement("w:pgBorders")
    b.set(qn("w:offsetFrom"), "page")
    for seite in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{seite}")
        el.set(qn("w:val"), "dashed"); el.set(qn("w:sz"), "8"); el.set(qn("w:space"), str(abstand_pt))
        el.set(qn("w:color"), farbe)
        b.append(el)
    nach = sectPr.find(qn("w:pgMar"))
    nach.addnext(b)


def minikopf(doc, breite):
    t = doc.add_table(2, 4)
    tabelle_ohne_rahmen(t)
    rest = breite - 0.18 - 1.75 - 2.2
    s.zeilenhoehe(t.rows[0], 0.62)
    s.zeilenhoehe(t.rows[1], 0.38)
    schattieren(t.cell(0, 0), s.BLAU)
    schattieren(t.cell(1, 0), s.GRUEN)
    for z in (t.cell(0, 0), t.cell(1, 0)):
        zellabstand(z, 0, 0, 0, 0)
        s.lauf(s.abstand(z.paragraphs[0]), "", 2)
    logo = t.cell(0, 1).merge(t.cell(1, 1))
    zellabstand(logo, 0, 0, 0, 0)
    s.senkrecht(logo)
    p = s.abstand(logo.paragraphs[0])
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(s.LOGO), width=Cm(1.45))
    mitte = t.cell(0, 2).merge(t.cell(1, 2))
    zellabstand(mitte, 0, 0, 0.1, 0.1)
    s.senkrecht(mitte)
    s.lauf(s.abstand(mitte.paragraphs[0], 0, 0, 1.0), "Anlage {{ nr }} · Selbstkontrolle", 7, farbe=s.RGB_GRAU)
    s.lauf(s.abstand(mitte.add_paragraph(), 0, 0, 1.0), "{{ titel }}", 11, fett=True, farbe=s.RGB_DUNKEL)
    rechts = t.cell(0, 3).merge(t.cell(1, 3))
    zellabstand(rechts, 0, 0, 0.1, 0)
    s.senkrecht(rechts)
    p = s.abstand(rechts.paragraphs[0])
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    s.lauf(p, "LF {{ lf }} · LS {{ ls }}", 7, farbe=s.RGB_GRAU)
    s.feste_breiten(t, [0.18, 1.75, rest, 2.2])
    buendig(t)
    return t


def aussagen(doc, breite):
    t = doc.add_table(4, 5)
    tabelle_ohne_rahmen(t)
    kopf = t.rows[0].cells
    for i, z in enumerate(kopf):
        schattieren(z, s.GRAU_HELL)
        s.zellrand(z, *RAND)
        zellabstand(z, 0.04, 0.04, 0.03 if i else 0.18, 0.03)
        s.senkrecht(z, "center")
        p = s.abstand(z.paragraphs[0], 0, 0, 1.0)
        if i == 0:
            s.lauf(p, "Aussage", 7, farbe=GRAU_TEXT)
        else:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            text_mit_umbruch(p, SKALA[i - 1], 6.3, farbe=GRAU_TEXT)
    s.lauf(s.abstand(t.cell(1, 0).paragraphs[0]), "{%tr for a in aussagen %}", 5)
    s.lauf(s.abstand(t.cell(3, 0).paragraphs[0]), "{%tr endfor %}", 5)
    for i, z in enumerate(t.rows[2].cells):
        s.zellrand(z, *RAND)
        zellabstand(z, 0.05, 0.05, 0.03 if i else 0.18, 0.1 if i == 0 else 0.03)
        s.senkrecht(z, "center")
        p = s.abstand(z.paragraphs[0], 0, 0, 1.1)
        if i == 0:
            s.lauf(p, "{{r a }}", 8.5)
        else:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            s.lauf(p, "◯", 11, farbe=GRAU_TEXT)
    s.zeilenhoehe(t.rows[2], 0.62, genau=False)
    s.feste_breiten(t, [breite - 4 * KREIS] + [KREIS] * 4)
    buendig(t)
    return t


def falzlinie(fuss, breite_seite, rand_lr):
    """Gestrichelte Linie über die ganze Kartenbreite, Text mittig auf der Linie."""
    t = fuss.add_table(2, 3, Cm(breite_seite))
    tabelle_ohne_rahmen(t)
    text_b = 7.2
    aussen = (breite_seite - text_b) / 2
    for zeile in t.rows:
        s.zeilenhoehe(zeile, 0.17)
    for z in (t.cell(0, 0), t.cell(0, 2)):
        rahmenlinie(z, "dashed", bottom=(8, "8A929E"))
    for z in t._cells:
        zellabstand(z, 0, 0, 0, 0)
        s.lauf(s.abstand(z.paragraphs[0]), "", 1).font.size = Pt(1)
    m = t.cell(0, 1).merge(t.cell(1, 1))
    rahmen(m)
    s.senkrecht(m)
    for p in m.paragraphs[1:]:
        m._tc.remove(p._p)
    p = s.abstand(m.paragraphs[0], 0, 0, 1.0)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    s.lauf(p, "✂ hier nach hinten knicken · erst nach der Einschätzung öffnen", 6.3, farbe=s.RGB_GRAU)
    s.feste_breiten(t, [aussen, text_b, aussen])
    buendig(t, -rand_lr + 0.25 + 0.19)
    return t


def _segmente(text):
    """„R_L ≈ 3,2 Ω“ → [(text, tief)], Indizes wie in formel()."""
    teile, pos = [], 0
    for m in re.finditer(r"([A-Za-zΔϑρα])_(\{[^}]+\}|[A-Za-z0-9]+)", text):
        teile.append((text[pos:m.start()] + m.group(1), False))
        teile.append((m.group(2).strip("{}"), True))
        pos = m.end()
    teile.append((text[pos:], False))
    return [t for t in teile if t[0]]


def ergebnisbild(ergebnisse, ziel_png, breite_cm, dpi=300):
    """Ergebnisse als Grafik, um 180° gedreht (Word/LibreOffice drehen Textfelder nicht verlässlich um 180°).

    Zwei Ergebnisse je Zeile; Überschrift „Ergebnisse zum Vergleich“ in Schulblau. Gibt die Höhe in cm zurück.
    """
    px = lambda cm: int(round(cm / 2.54 * dpi))  # noqa: E731
    pt = lambda p: int(round(p / 72 * dpi))  # noqa: E731
    f_norm = ImageFont.truetype(SCHRIFT_DATEI, pt(8.5))
    f_fett = ImageFont.truetype(SCHRIFT_FETT, pt(8.5))
    f_tief = ImageFont.truetype(SCHRIFT_DATEI, pt(6))
    f_kopf = ImageFont.truetype(SCHRIFT_FETT, pt(6.8))
    zeile = pt(8.5 * 1.25)
    paare = [ergebnisse[i:i + 2] for i in range(0, len(ergebnisse), 2)]
    h = pt(6.8 * 1.6) + len(paare) * (2 * zeile + pt(3))
    bild = Image.new("RGB", (px(breite_cm), h), "white")
    d = ImageDraw.Draw(bild)
    x = 0
    for buchst in "ERGEBNISSE ZUM VERGLEICH":
        d.text((x, 0), buchst, font=f_kopf, fill="#" + s.BLAU)
        x += d.textlength(buchst, font=f_kopf) + pt(0.7)
    y = pt(6.8 * 1.6)
    for paar in paare:
        for i, e in enumerate(paar):
            x0 = i * px(breite_cm) // 2
            d.text((x0, y), f"Aufgabe {e['nr']}", font=f_fett, fill="#1B1F24")
            x = x0
            for text, tief in _segmente(f"{e['wert']}  ({e['toleranz']})"):
                f = f_tief if tief else f_norm
                d.text((x, y + zeile + (pt(2.4) if tief else 0)), text, font=f, fill="#1B1F24")
                x += d.textlength(text, font=f)
        y += 2 * zeile + pt(3)
    bild.rotate(180).save(ziel_png, dpi=(dpi, dpi))
    return h / dpi * 2.54


def kartenfuss(doc, breite):
    sec = doc.sections[0]
    f = sec.footer
    f.paragraphs[0].text = ""
    s.abstand(f.paragraphs[0]).paragraph_format.line_spacing = Pt(1)
    falzlinie(f, sec.page_width / EMU - 0.5, sec.left_margin / EMU)
    p = s.abstand(f.add_paragraph(), 5, 3)
    s.lauf(p, "{{ ergebnisse_bild }}", 7, farbe=s.RGB_GRAU)
    t = f.add_table(1, 2, Cm(breite))
    tabelle_ohne_rahmen(t)
    li, re_ = t.rows[0].cells
    for z in (li, re_):
        rahmen(z, top=(4, "C9CED6"))
    zellabstand(li, 0.05, 0, 0, 0.1)
    zellabstand(re_, 0.05, 0, 0.1, 0)
    s.lauf(s.abstand(li.paragraphs[0]), "{{ ki_hinweis }}", 5.8, farbe=s.RGB_GRAU)
    p = s.abstand(re_.paragraphs[0])
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    s.lauf(p, "A6", 5.8, farbe=s.RGB_GRAU)
    s.feste_breiten(t, [breite - 1.0, 1.0])
    buendig(t)
    s.abstand(f.add_paragraph()).paragraph_format.line_spacing = Pt(1)


def vorlage(pfad):
    doc = s.dokument("A6quer")
    sec = doc.sections[0]
    sec.top_margin = Cm(0.7)
    sec.footer_distance = Cm(0.35)
    b = s.nutzbreite(doc)
    seitenrand_gestrichelt(doc)
    minikopf(doc, b)
    p = s.abstand(doc.add_paragraph(), 4, 3, 1.15)
    s.lauf(p, "Wozu? ", 8.3, fett=True, farbe=GRAU_TEXT)
    s.lauf(p, "{{ wozu }}", 8.3, farbe=GRAU_TEXT)
    aussagen(doc, b)
    p = s.abstand(doc.add_paragraph(), 3, 0, 1.1)
    s.lauf(p, "{{ hinweis }}", 7.8, farbe=GRAU_TEXT)
    kartenfuss(doc, b)
    doc.save(pfad)


def rendern(vorlage_pfad, daten, ziel):
    d = dict(daten)
    d["aussagen"] = [als_richtext(a, groesse=8.5) for a in d["aussagen"]]
    t = DocxTemplate(vorlage_pfad)
    with tempfile.TemporaryDirectory() as tmp:
        png = Path(tmp) / "ergebnisse.png"
        ergebnisbild(daten["ergebnisse"], png, BREITE_ERGEBNIS)
        d["ergebnisse_bild"] = InlineImage(t, str(png), width=Cm(BREITE_ERGEBNIS))
        t.render(d)
    t.save(ziel)


def muster_daten():
    r_l = 0.0178 * 90 / 0.5
    dt = r_l / 0.385
    assert f"{r_l:.1f}" == "3.2" and f"{dt:.1f}" == "8.3"
    return {
        "lf": "1", "ls": "3", "nr": "4", "titel": "Leitungswiderstand und Messfehler",
        "wozu": "Bevor Sie dem Kunden antworten, prüfen Sie selbst, ob Ihre Lösung trägt. "
                "Erst einschätzen, dann unten die Ergebnisse vergleichen.",
        "aussagen": [
            "Ich habe die ganze Strecke berechnet, die der Strom durch das Kupfer fließt.",
            "Ich habe die Einheiten bis zum Ergebnis mitgeführt.",
            "Mein Ergebnis erklärt die Beobachtung des Kunden.",
            "Ich kann meinen Rechenweg einer Kollegin in einem Satz erklären.",
        ],
        "hinweis": "Einmal nicht „trifft zu“ angekreuzt? Gehen Sie an die Stelle zurück oder nehmen Sie "
                   "die passende Hilfekarte.",
        "ergebnisse": [
            {"nr": "1", "wert": "R_L ≈ 3,2 Ω", "toleranz": "3,1 … 3,3 Ω"},
            {"nr": "2", "wert": "Δϑ ≈ 8 K", "toleranz": "8,0 … 8,5 K"},
        ],
        "ki_hinweis": KI_HINWEIS,
    }


if __name__ == "__main__":
    bauen("selbstkontrolle", vorlage, muster_daten(), rendern)
