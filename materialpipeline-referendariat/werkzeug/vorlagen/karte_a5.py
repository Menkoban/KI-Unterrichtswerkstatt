"""Vorlage Karte A5 quer (Lehrkraft 2026-10-13, A): ein Design, drei Typen.

Eine Vorlage mit Typ-Schalter: `karten` ist eine Liste, jede Karte füllt eine Seite A5 quer;
`k.typ` wählt die Bausteine:
  "station"  Nummernfeld, Titel, Wozu, Anstoß (Zitat), Ihr Auftrag, Am Ende haben Sie,
             Leiste Sozialform/Zeit/Unterlagen
  "rolle"    Rollenkarte: Ihre Lage, Das wollen Sie wissen (Liste), So verhalten Sie sich
  "info"     Informationskarte: ein Dokument aus dem Informationspool (Rahmen mit Kopf und Feldern)
Gemeinsam: Mini-Kopf mit Farbstreifen (Blau, unten Grün), Logo rechts, „Wozu?“, Fußzeile mit
Fiktiv- und KI-Hinweis, gestrichelte Schnittkante (Seitenrahmen).

Eine Vorlage statt drei, weil gemischte Kartensätze (z. B. vier Stationen und eine Rollenkarte)
so in einer Datei gedruckt werden; die Typen sind als Tabellenzeilen mit {%tr if %} geschaltet,
das bleibt in Word sauber (keine Abschnittswechsel, keine Textfelder). Die Karte ist eine
Tabelle mit festen Zeilenhöhen; der Inhalt muss in sein Feld passen (sonst abgeschnitten).

Kontext: karten[{typ, nr, typ_label, titel, wozu, zitat, zitat_quelle, auftrag, ergebnis,
sozialform, zeit, unterlagen, lage, wissen[…], verhalten, dok{titel, info, zeilen[{label, wert}]},
fuss, ki}]. Werte mit Zeilenumbruch (dok.zeilen.wert) als RichText (material_bausteine.rt).

Aufruf: python werkzeug/vorlagen/karte_a5.py
Erzeugt vorlagen/Vorlage_karte_a5.docx, Muster_karte_a5.docx und vorschau_karte_a5-N.png.
"""
import sys
from pathlib import Path

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor

sys.path.insert(0, str(Path(__file__).parent))
import material_bausteine as mb  # noqa: E402
import schule as s  # noqa: E402
from vorlagen_bauen import rahmen, schattieren, tabelle_ohne_rahmen  # noqa: E402

MITTEL = RGBColor.from_string(mb.MITTEL)
# feste Höhen (cm); Summe bleibt knapp unter der Satzspiegelhöhe 13,0 cm
H_KOPF, H_WOZU, H_LEISTE, H_FUSS = 1.85, 1.0, 1.25, 0.55
H_GESAMT = 12.65
H_INHALT_STATION = H_GESAMT - H_KOPF - H_WOZU - H_LEISTE - H_FUSS
H_INHALT = H_GESAMT - H_KOPF - H_WOZU - H_FUSS


def tagzeile(t, i, text):
    z = t.cell(i, 0)
    s.lauf(s.abstand(z.paragraphs[0]), text, 2)


def kopf(zelle, b, mit_nummer):
    """Mini-Kopf: Farbstreifen, [Nummernfeld], Typ und Titel, Logo."""
    spalten = [0.28, 0.35] + ([1.75, 0.4] if mit_nummer else []) + [b - 0.63 - (2.15 if mit_nummer else 0) - 2.7, 2.7]
    n = mb.zell_tabelle(zelle, 1, len(spalten))
    tabelle_ohne_rahmen(n)
    s.zeilenhoehe(n.rows[0], 1.75)
    zellen = n.rows[0].cells
    for z in zellen:
        s.zellabstand(z, 0, 0, 0, 0)
        s.senkrecht(z, "center")
    # Farbstreifen: zwei schattierte Absätze fester Höhe (Blau oben, Grün unten)
    st = zellen[0]
    s.senkrecht(st, "top")
    for i, (farbe, hoehe) in enumerate(((s.BLAU, 1.15), (s.GRUEN, 0.6))):
        q = s.abstand(st.paragraphs[0] if i == 0 else st.add_paragraph())
        q.paragraph_format.line_spacing = Cm(hoehe)
        q.paragraph_format.line_spacing_rule = 4  # genau
        mb.p_schatten(q, farbe)
        s.lauf(q, "", 2)
    zellen = zellen[1:]
    j = 1
    if mit_nummer:
        nr = zellen[j]
        blau = (24, s.BLAU)
        rahmen(nr, top=blau, bottom=blau, left=blau, right=blau)
        p = s.abstand(nr.paragraphs[0]); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        s.lauf(p, "{{ k.nr }}", 30, fett=True, farbe=s.RGB_BLAU)
        j += 2
    tz = zellen[j]
    s.zellabstand(tz, 0, 0, 0.05, 0.1)
    p = s.abstand(tz.paragraphs[0], 0, 1)
    mb.r_sperren(s.kapitaelchen(s.lauf(p, "{{ k.typ_label }}", 8, fett=True, farbe=s.RGB_BLAU)), 24)
    s.lauf(s.abstand(tz.add_paragraph(), 0, 0, 1.0), "{{ k.titel }}", 18, fett=True, farbe=s.RGB_DUNKEL)
    lg = zellen[j + 1]
    p = s.abstand(lg.paragraphs[0]); p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p.add_run().add_picture(str(s.LOGO), width=Cm(2.5))
    s.feste_breiten(n, spalten)
    mb.schlussabsatz(zelle)
    zelle._tc.remove(zelle.paragraphs[0]._p)


def bh(zelle, text, vor=7):
    return mb.label(zelle, text, farbe=RGBColor.from_string("2B3440"), groesse=7.5, vor=vor, nach=1, sperren=14)


def fliess(zelle, text, groesse=12.5, vor=0, nach=0):
    p = s.abstand(zelle.add_paragraph(), vor, nach, 1.3)
    s.lauf(p, text, groesse, farbe=s.RGB_DUNKEL)
    return p


def inhalt_station(z):
    mb.tag(z, "{%p if k.zitat %}")
    p = s.abstand(z.add_paragraph(), 4, 4, 1.3)
    p.paragraph_format.left_indent = Cm(0.45)
    mb.p_rahmen(p, space=10, left=(36, s.GRUEN))
    s.lauf(p, "{{ k.zitat }}", 12, kursiv=True, farbe=s.RGB_DUNKEL)
    s.lauf(p, "{% if k.zitat_quelle %} – {{ k.zitat_quelle }}{% endif %}", 9, farbe=s.RGB_GRAU)
    mb.tag(z, "{%p endif %}")
    bh(z, "Ihr Auftrag")
    fliess(z, "{{ k.auftrag }}")
    bh(z, "Am Ende haben Sie", vor=10)
    fliess(z, "{{ k.ergebnis }}")


def inhalt_rolle(z):
    bh(z, "Ihre Lage", vor=6)
    fliess(z, "{{ k.lage }}")
    bh(z, "Das wollen Sie wissen")
    mb.tag(z, "{%p for w in k.wissen %}")
    p = fliess(z, "•\t{{ w }}")
    p.paragraph_format.left_indent = Cm(0.55); p.paragraph_format.first_line_indent = Cm(-0.55)
    mb.tab_stopp(p, 0.55, "left")
    mb.tag(z, "{%p endfor %}")
    bh(z, "So verhalten Sie sich")
    fliess(z, "{{ k.verhalten }}")


def inhalt_info(z, b):
    mb.text_absatz(z, "", 2, zeile=Pt(8))
    d = mb.zell_tabelle(z, 4, 2)
    tabelle_ohne_rahmen(d)
    dunkel = (12, mb.DUNKEL)
    breiten = [4.9, b - 4.9]
    k = d.cell(0, 0).merge(d.cell(0, 1))
    rahmen(k, top=dunkel, left=dunkel, right=dunkel)
    s.zellabstand(k, 0.25, 0.05, 0.4, 0.4)
    p = s.abstand(k.paragraphs[0], 0, 0)
    mb.p_rahmen(p, space=3, bottom=(4, "9AA3AD"))
    mb.tab_stopp(p, b - 0.8)
    s.lauf(p, "{{ k.dok.titel }}", 11, fett=True, farbe=s.RGB_DUNKEL)
    s.lauf(p, "\t{{ k.dok.info }}", 8.5, farbe=s.RGB_DUNKEL)
    for i, txt in ((1, "{%tr for x in k.dok.zeilen %}"), (3, "{%tr endfor %}")):
        c = d.cell(i, 0).merge(d.cell(i, 1))
        s.lauf(s.abstand(c.paragraphs[0]), txt, 2)
    for j, txt in enumerate(("{{ x.label }}", "{{r x.wert }}")):
        c = d.cell(2, j)
        rahmen(c, left=dunkel if j == 0 else None, right=dunkel if j == 1 else None)
        s.zellabstand(c, 0.06, 0.06, 0.4 if j == 0 else 0.1, 0.4 if j == 1 else 0.1)
        s.lauf(s.abstand(c.paragraphs[0], 0, 0, 1.3), txt, 11, farbe=MITTEL if j == 0 else s.RGB_DUNKEL)
    # Abschlusszeile mit unterem Rahmen
    r = d.add_row()
    c = r.cells[0].merge(r.cells[1])
    rahmen(c, bottom=dunkel, left=dunkel, right=dunkel)
    mb.schlussabsatz(c, 4)
    s.zeilenhoehe(r, 0.25)
    s.feste_breiten(d, breiten)
    mb.schlussabsatz(z)


def leiste(zelle, b):
    n = mb.zell_tabelle(zelle, 1, 5)
    tabelle_ohne_rahmen(n)
    luecke = 0.4
    breite = (b - 2 * luecke) / 3
    grau = (12, "C9CED6")
    for j, (lab, wert) in zip((0, 2, 4), (("Sozialform", "{{ k.sozialform }}"), ("Zeit", "{{ k.zeit }}"),
                                          ("Unterlagen", "{{ k.unterlagen }}"))):
        c = n.cell(0, j)
        rahmen(c, top=grau, bottom=grau, left=grau, right=grau)
        s.zellabstand(c, 0.08, 0.08, 0.25, 0.2)
        p = s.abstand(c.paragraphs[0])
        mb.r_sperren(s.kapitaelchen(s.lauf(p, lab, 6.5, farbe=s.RGB_GRAU)), 14)
        s.lauf(s.abstand(c.add_paragraph()), wert, 10, farbe=s.RGB_DUNKEL)
    s.feste_breiten(n, [breite, luecke, breite, luecke, breite])
    mb.schlussabsatz(zelle)
    zelle._tc.remove(zelle.paragraphs[0]._p)


def vorlage():
    doc = s.dokument("A5quer")
    mb.seitenrand_gestrichelt(doc)
    b = s.nutzbreite(doc)
    mb.tag(doc, "{%p for k in karten %}")
    mb.tag(doc, "{%p if not loop.first %}")
    mb.seitenumbruch(doc)
    mb.tag(doc, "{%p endif %}")
    plan = ["{%tr if k.typ == 'station' %}", "kopf_nr", "{%tr else %}", "kopf", "{%tr endif %}",
            "wozu",
            "{%tr if k.typ == 'station' %}", "station", "{%tr elif k.typ == 'rolle' %}", "rolle",
            "{%tr else %}", "info", "{%tr endif %}",
            "{%tr if k.typ == 'station' %}", "leiste", "{%tr endif %}",
            "fuss"]
    t = doc.add_table(len(plan), 1)
    tabelle_ohne_rahmen(t)
    for i, was in enumerate(plan):
        z = t.cell(i, 0)
        s.zellabstand(z, 0, 0, 0, 0)
        if was.startswith("{%"):
            tagzeile(t, i, was)
            continue
        zeile = t.rows[i]
        s.senkrecht(z, "top")
        if was in ("kopf_nr", "kopf"):
            s.zeilenhoehe(zeile, H_KOPF)
            kopf(z, b, was == "kopf_nr")
        elif was == "wozu":
            s.zeilenhoehe(zeile, H_WOZU)
            p = s.abstand(z.paragraphs[0], 5, 0, 1.15)
            s.lauf(p, "Wozu? ", 9, fett=True, farbe=MITTEL)
            s.lauf(p, "{{ k.wozu }}", 9, farbe=MITTEL)
        elif was in ("station", "rolle", "info"):
            s.zeilenhoehe(zeile, H_INHALT_STATION if was == "station" else H_INHALT)
            z._tc.remove(z.paragraphs[0]._p)
            {"station": inhalt_station, "rolle": inhalt_rolle}.get(was, lambda c: inhalt_info(c, b))(z)
            mb.schlussabsatz(z)
        elif was == "leiste":
            s.zeilenhoehe(zeile, H_LEISTE)
            s.senkrecht(z, "bottom")
            leiste(z, b)
        elif was == "fuss":
            s.zeilenhoehe(zeile, H_FUSS)
            s.senkrecht(z, "bottom")
            p = s.abstand(z.paragraphs[0])
            mb.p_rahmen(p, space=2, top=(4, "C9CED6"))
            mb.tab_stopp(p, b)
            s.lauf(p, "{{ k.fuss }}\t{{ k.ki }}", 6.5, farbe=s.RGB_GRAU)
    s.feste_breiten(t, [b])
    mb.tag(doc, "{%p endfor %}")
    mb.schlussabsatz(doc)
    return doc


def muster_daten(tpl):
    ki = "KI-gestützt erstellt · A5"
    return {"karten": [
        {"typ": "station", "nr": "2", "typ_label": "Station", "titel": "Spurensuche an der Anlage",
         "wozu": "An dieser Station sammeln Sie Belege, mit denen Sie die Reklamation erklären können.",
         "zitat": "„Die Anzeige sagt 180 °C, das Thermometer sagt 172 °C. Einer von beiden hat unrecht – und ich will "
                  "wissen, warum.“",
         "zitat_quelle": "Hr. Ostendorf, Nordland Feinkost",
         "auftrag": "Prüfen Sie Ihre Vermutung an der Anlage. Halten Sie fest, wie Sie vorgegangen sind, was Sie "
                    "herausgefunden haben und was noch offen ist.",
         "ergebnis": "einen Beleg, den Sie dem Kunden zeigen können.",
         "sozialform": "Gruppe (3 Personen)", "zeit": "20 Minuten", "unterlagen": "Anlagenakte, Anlage 2",
         "fuss": "LF 1 · LS 3 · Brinkmann Automation und Nordland Feinkost sind fiktiv", "ki": ki},
        {"typ": "rolle", "typ_label": "Rollenkarte · Kunde", "titel": "Herr Ostendorf, Schichtleitung Linie 2",
         "wozu": "Sie spielen den Kunden beim Rückruf. Ihre Mitschülerin oder Ihr Mitschüler erklärt Ihnen als "
                 "Technikerin oder Techniker das Ergebnis.",
         "lage": "Drei Paletten sind gesperrt, die Qualitätssicherung macht Druck. Von Elektrotechnik verstehen Sie "
                 "wenig, von Ihrer Linie sehr viel.",
         "wissen": ["Ist die Steuerung kaputt, oder war es die Fremdfirma beim Umbau?",
                    "Was kostet die Lösung, und wann läuft die Linie wieder sicher?"],
         "verhalten": "Fragen Sie nach, wenn Fachbegriffe fallen („Was heißt das für mich?“). Geben Sie sich erst "
                      "zufrieden, wenn Sie eine klare Empfehlung bekommen.",
         "fuss": "LF 1 · LS 3 · Rolle fiktiv", "ki": ki},
        {"typ": "info", "typ_label": "Information · Anlagenakte SG-2", "titel": "Auszug: Umbau Linie 2",
         "wozu": "Ein Dokument aus der Anlagenakte. Entscheiden Sie selbst, ob es für Ihren Auftrag wichtig ist.",
         "dok": {"titel": "Änderungsnachweis Nr. 3", "info": "Elektro Sandkamp · 18.09.2026",
                 "zeilen": [{"label": a, "wert": mb.rt(w, 11)} for a, w in (
                     ("Anlage", "Siegelstation SG-2, Linie 2"),
                     ("Grund", "Neuaufstellung der Linie, Schaltschrank in Nebenraum verlegt"),
                     ("Geänderte Betriebsmittel", "-B1 Temperaturfühler: Leitung neu verlegt, 45 m, Cu 2 × 0,5 mm²\n"
                                                  "-X2 Klemmleiste im Schaltschrank neu"),
                     ("Parameter Steuerung", "unverändert übernommen"),
                     ("Funktionsprüfung", "Anlage läuft, Anzeige plausibel · gez. Sandkamp"))]},
         "fuss": "LF 1 · LS 3 · Elektro Sandkamp, Brinkmann Automation und Nordland Feinkost sind fiktiv", "ki": ki},
    ]}


if __name__ == "__main__":
    mb.bauen("karte_a5", vorlage, muster_daten)
