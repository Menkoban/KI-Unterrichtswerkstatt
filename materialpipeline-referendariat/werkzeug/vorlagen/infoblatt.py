"""Vorlagen Infoblatt (Fachbuch-Auszug, Standard) und Herstellerdatenblatt (Ergänzung).

Infoblatt (Lehrkraft 2026-10-13): Schild „Anlage n · Information“, Titel, „Wozu?“, ohne Namensfeld;
nummerierte Abschnitte (Schleife) mit Text, optionaler Formel, optionaler Abbildung und/oder
Tabelle (nebeneinander, wenn beides), jeweils mit Nummer und Quelle; Randspalte mit grüner Linie
(Begriffe, Formelzeichen, Norm, Weiterlesen …, ebenfalls Schleife).
Datenblatt: Herstellerunterlage eines fiktiven Herstellers im schwarzen Rahmen mit dunklem Kopf,
technischen Daten, Anschlussbild, Bestellschlüssel, Tabelle, Hinweisen und Warnhinweis.

Aufruf: python werkzeug/vorlagen/infoblatt.py
Erzeugt vorlagen/Vorlage_infoblatt.docx und vorlagen/Vorlage_datenblatt.docx, dazu Muster und
Vorschau in docs/stilreferenz/vorlagen/muster/.

Kontext Infoblatt: nr, titel, abschnitte[{nr, titel, absaetze[RichText], formel (RichText
oder ""), symbol (optional, kleines InlineImage rechts neben dem Titel), abb (InlineImage oder None), abb_text, tabelle (Subdoc über material_bausteine.tabelle
oder None), tab_text, absaetze_nach[RichText] (optional, Text unter Abbildung/Tabelle), neue_seite
(optional, Abschnitt beginnt auf neuer Seite; nach dem Füllen material_bausteine.seitenumbrueche_aufloesen()
aufrufen)}], rand[{titel, zeilen[RichText]}], datei, quellen, ki_hinweis, Kopf.
Absätze über fliesstext("…"), Formeln und Randzeilen über material_bausteine.rt("R_{ϑ} = …").
Kontext Datenblatt: nr, titel, wozu, hersteller, hersteller_zusatz, db_kopf[Zeilen], typ, untertitel,
daten[[Merkmal, Wert(RichText)]], anschlussbild (InlineImage oder None), anschluss_text,
bestellschluessel (Subdoc oder None), bestell_text, tabelle_titel, tabelle (Subdoc oder None),
hinweise[…], warnung, db_fuss_links, db_fuss_rechts, datei, quellen, ki_hinweis, Kopf.
"""
import sys
from pathlib import Path

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor
from docxtpl import InlineImage

sys.path.insert(0, str(Path(__file__).parent))
import material_bausteine as mb  # noqa: E402
import schule as s  # noqa: E402
from vorlagen_bauen import rahmen, schattieren, tabelle_ohne_rahmen  # noqa: E402

MITTEL = RGBColor.from_string(mb.MITTEL)
HAUPT, LUECKE = 13.5, 0.5          # Breite Hauptspalte, Abstand zur Randspalte (cm)
FUSS = "{{ datei }}{% if quellen %} · Quellen: {{ quellen }}{% endif %}"


def grundgeruest(titel_groesse=17):
    doc = s.dokument("A4")
    s.kopf(doc)
    s.fusszeile(doc, links=FUSS, quellen=None)
    s.titelzeile(doc, schild="Anlage {{ nr }} · Information", titel="{{ titel }}", namensfeld=False,
                 titelgroesse=titel_groesse)
    if s.STIL["infoblatt_wozu"]:   # Profil material.infoblatt_wozu
        p = s.wozu(doc)
        p.paragraph_format.space_after = Pt(6)
    return doc


def satz():
    """Fließtext im Blocksatz oder linksbündig (Profil material.flattersatz; leichter lesbar bei LRS und DaZ)."""
    return None if s.STIL["flattersatz"] else "block"


def mittig():
    """Ausrichtung allein stehender Abbildungen und Tabellen (Profil material.abbildungen_zentriert)."""
    return "mitte" if s.STIL["abbildungen_zentriert"] else None


# ================================================================ Infoblatt
def bildunterschrift(ziel, text, vor=1, nach=3, ausr=None):
    return mb.text_absatz(ziel, text, 7.5, farbe=s.RGB_GRAU, vor=vor, nach=nach, ausr=ausr)


def vorlage_infoblatt():
    doc = grundgeruest()
    b = s.nutzbreite(doc)
    rand = b - HAUPT - LUECKE
    t = doc.add_table(1, 3)
    tabelle_ohne_rahmen(t)
    haupt, _, rspalte = t.rows[0].cells
    for z in t.rows[0].cells:
        s.zellabstand(z, 0, 0, 0.19 if z is haupt else 0, 0)
    # ---- Hauptspalte: Abschnitte
    s.lauf(s.abstand(haupt.paragraphs[0]), "{%p for a in abschnitte %}", 2)
    # Seitenumbruch in einer Tabellenzelle setzen Word und LibreOffice nicht zuverlässig um; die Marke
    # wird nach dem Füllen von mb.seitenumbrueche_aufloesen() in einen echten Umbruch übersetzt.
    mb.tag(haupt, "{%p if a.neue_seite %}")
    s.lauf(s.abstand(haupt.add_paragraph()), mb.UMBRUCH_MARKE, 2)
    mb.tag(haupt, "{%p endif %}")
    p = s.abstand(haupt.add_paragraph(), 5, 1)
    mb.tab_stopp(p, 0.75, "left")
    s.lauf(p, "{{ a.nr }}\t{{ a.titel }}", 10.5, fett=True, farbe=s.RGB_BLAU)
    s.lauf(p, "{% if a.symbol %}   {{ a.symbol }}{% endif %}", 10.5)      # optionales Symbol (InlineImage, ~0,5 cm)
    mb.tag(haupt, "{%p for x in a.absaetze %}")
    p = mb.text_absatz(haupt, "", nach=3, zeile=1.18, ausr=satz())
    s.lauf(p, "{{r x }}", 9)
    mb.tag(haupt, "{%p endfor %}")
    mb.tag(haupt, "{%p if a.formel %}")
    p = mb.text_absatz(haupt, "", vor=1, nach=5, ausr="mitte")
    s.lauf(p, "{{r a.formel }}", 10)
    mb.tag(haupt, "{%p endif %}")
    # Abbildung und Tabelle nebeneinander
    mb.tag(haupt, "{%p if a.abb and a.tabelle %}")
    n = mb.zell_tabelle(haupt, 1, 3)
    tabelle_ohne_rahmen(n)
    links, _, rechts = n.rows[0].cells
    for z in n.rows[0].cells:
        s.zellabstand(z, 0, 0, 0, 0)
    s.lauf(s.abstand(links.paragraphs[0]), "{{ a.abb }}", 9)
    bildunterschrift(links, "{{ a.abb_text }}")
    p = mb.text_absatz(rechts, "", vor=2, nach=2)
    rechts._tc.remove(rechts.paragraphs[0]._p)
    s.lauf(p, "{{ a.tab_text }}", 8, fett=True, farbe=s.RGB_DUNKEL)
    s.lauf(mb.text_absatz(rechts), "{{p a.tabelle }}", 9)
    mb.schlussabsatz(rechts)
    s.feste_breiten(n, [7.7, 0.5, HAUPT - 0.19 - 8.2])
    mb.tag(haupt, "{%p elif a.abb %}")
    p = mb.text_absatz(haupt, "", vor=4, ausr=mittig())
    s.lauf(p, "{{ a.abb }}", 9)
    bildunterschrift(haupt, "{{ a.abb_text }}", ausr=mittig())
    mb.tag(haupt, "{%p elif a.tabelle %}")
    mb.text_absatz(haupt, "{{ a.tab_text }}", 8, fett=True, farbe=s.RGB_DUNKEL, vor=4, nach=2, ausr=mittig())
    s.lauf(mb.text_absatz(haupt), "{{p a.tabelle }}", 9)
    mb.tag(haupt, "{%p endif %}")
    # Text unter Abbildung bzw. Tabelle (z. B. Erläuterung, die den Abschnitt abschließt)
    mb.tag(haupt, "{%p for x in a.absaetze_nach %}")
    p = mb.text_absatz(haupt, "", vor=2, nach=3, zeile=1.18, ausr=satz())
    s.lauf(p, "{{r x }}", 9)
    mb.tag(haupt, "{%p endfor %}")
    mb.tag(haupt, "{%p endfor %}")
    mb.schlussabsatz(haupt)
    # ---- Randspalte: Blöcke mit grüner Linie
    s.lauf(s.abstand(rspalte.paragraphs[0]), "{%p for r in rand %}", 2)
    gruen = (18, s.GRUEN)
    p = s.abstand(rspalte.add_paragraph(), 10, 0, 1.3)
    p.paragraph_format.left_indent = Cm(0.3)
    mb.p_rahmen(p, space=6, left=gruen)
    s.lauf(p, "{{ r.titel }}", 8, fett=True, farbe=s.RGB_DUNKEL)
    mb.tag(rspalte, "{%p for z in r.zeilen %}")
    p = s.abstand(rspalte.add_paragraph(), 0, 0, 1.3)
    p.paragraph_format.left_indent = Cm(0.3)
    mb.p_rahmen(p, space=6, left=gruen)
    s.lauf(p, "{{r z }}", 7.5)
    mb.tag(rspalte, "{%p endfor %}")
    mb.tag(rspalte, "{%p endfor %}")
    mb.schlussabsatz(rspalte)
    s.feste_breiten(t, [HAUPT, LUECKE, rand])
    mb.schlussabsatz(doc)
    return doc


def fliesstext(text):
    """Absatz für das Infoblatt (8,5 pt wie im Entwurf; **fett**, _{tief}, ^{hoch})."""
    return mb.rt(text, 8.5)


def daten_infoblatt(tpl):
    rt = fliesstext
    tab1 = mb.tabelle(tpl, ["ϑ in °C", "R in Ω"],
                      [["−50", "80,31"], ["0", "100,00"], ["50", "119,40"], ["100", "138,51"],
                       ["150", "157,33"], ["200", "175,86"], ["250", "194,10"]],
                      [2.6, 2.6], groesse=8.5, ausr="mitte", linie="9AA3AD")
    grau = "4A5563"
    return {
        **kopfdaten(),
        "nr": "2", "titel": "Widerstandsthermometer Pt100",
        "wozu": "Nachschlagen: Aufbau, Kennwerte und Anschlussarten von Pt100-Fühlern. Nutzen Sie nur, was Sie "
                "für Ihren Auftrag brauchen.",
        "abschnitte": [
            {"nr": "1", "titel": "Aufbau und Wirkungsweise",
             "absaetze": [rt("Ein Pt100 ist ein Messwiderstand aus Platin. Bei 0 °C hat er einen Widerstand von genau "
                             "100 Ω. Mit steigender Temperatur nimmt sein Widerstand zu (Kaltleiterverhalten). Der "
                             "Zusammenhang ist in DIN EN IEC 60751 festgelegt und über den genutzten Bereich nahezu "
                             "linear."),
                          rt("Für überschlägige Rechnungen genügt der mittlere Temperaturbeiwert zwischen 0 °C und "
                             "100 °C:")],
             "formel": mb.rt("R_{ϑ} = R_{0} · (1 + α · Δϑ)     mit   R_{0} = 100 Ω,  α = 3,85 · 10^{−3} 1/K", 10),
             "abb": InlineImage(tpl, str(mb.ENTWURF / "infoblatt_abb-1.png"), width=Cm(7.4)),
             "abb_text": "Abb. 1: Kennlinie Pt100 (eigene Darstellung, Werte nach DIN EN IEC 60751)",
             "tabelle": tab1, "tab_text": "Tab. 1: Grundwerte Pt100"},
            {"nr": "2", "titel": "Genauigkeitsklassen",
             "absaetze": [rt("Die Norm legt zulässige Grenzabweichungen fest: Klasse A ± (0,15 + 0,002 · |ϑ|) K, "
                             "Klasse B ± (0,30 + 0,005 · |ϑ|) K, mit ϑ in °C. Diese Werte gelten für den "
                             "Messwiderstand allein, nicht für Leitung und Auswertung.")],
             "formel": "", "abb": None, "tabelle": None},
            {"nr": "3", "titel": "Anschlussarten",
             "absaetze": [rt("Das Auswertegerät (Messumformer, Analogeingang der Steuerung) misst den Widerstand des "
                             "gesamten angeschlossenen Stromkreises und rechnet ihn in eine Temperatur um. Je nach "
                             "Anzahl der Adern unterscheidet man drei Schaltungen:"),
                          rt("**Zweileiterschaltung:** Messwiderstand und beide Adern der Anschlussleitung liegen in "
                             "Reihe. **Dreileiterschaltung:** Über eine dritte Ader erfasst das Gerät den "
                             "Leitungswiderstand und gleicht ihn aus, sofern alle Adern gleich sind. "
                             "**Vierleiterschaltung:** Ein Aderpaar führt den Messstrom, das andere misst die Spannung "
                             "direkt am Fühler.")],
             "formel": "",
             "abb": InlineImage(tpl, str(mb.ENTWURF / "infoblatt_abb-2.png"), width=Cm(11.0)),
             "abb_text": "Abb. 2: Anschlussarten von Widerstandsthermometern (eigene Darstellung)",
             "tabelle": None},
            {"nr": "4", "titel": "Widerstand von Leitungen",
             "absaetze": [rt("Der Widerstand eines Leiters hängt von Werkstoff, Länge und Querschnitt ab:  "
                             "R = ρ · l / A.  Spezifischer Widerstand von Kupfer bei 20 °C: ρ_{Cu} = 0,0178 Ω · mm²/m; "
                             "weitere Werkstoffe siehe Tabellenbuch.")],
             "formel": "", "abb": None, "tabelle": None}],
        "rand": [
            {"titel": "Begriffe", "zeilen": [mb.rt(x, 7.5, grau) for x in
                                             ("Pt = Platin", "100 = Nennwiderstand in Ω bei 0 °C", "Ebenso: Pt500, Pt1000")]},
            {"titel": "Formelzeichen", "zeilen": [mb.rt(x, 7.5, grau) for x in (
                "R_{ϑ} Widerstand bei ϑ", "R_{0} Widerstand bei 0 °C", "α Temperaturbeiwert", "Δϑ Temperaturdifferenz",
                "ρ spezifischer Widerstand", "l Leiterlänge", "A Leiterquerschnitt")]},
            {"titel": "Norm", "zeilen": [mb.rt("DIN EN IEC 60751: Industrielle Platin-Widerstandsthermometer und "
                                            "Platin-Temperatursensoren", 7.5, grau)]},
            {"titel": "Weiterlesen", "zeilen": [mb.rt("Tabellenbuch Elektrotechnik, Abschnitt Temperaturmessung", 7.5, grau)]}],
        "datei": "Anlage 2 · Information · Widerstandsthermometer Pt100",
        "quellen": "eigene Darstellung; Grundwerte und Grenzabweichungen nach DIN EN IEC 60751",
        "ki_hinweis": "KI-gestützt erstellt; Werkzeug, Version und Datum siehe KI-Verzeichnis.",
    }


# ================================================================ Datenblatt
DB_LINIE, DB_DUNKEL = "9AA3AD", "2B3440"


def db_ueberschrift(ziel, text, vor=4):
    p = mb.label(ziel, text, farbe=s.RGB_DUNKEL, groesse=7.5, vor=vor, nach=3, sperren=12)
    mb.p_rahmen(p, space=1, bottom=(6, mb.DUNKEL))
    return p


def vorlage_datenblatt():
    doc = grundgeruest()
    b = s.nutzbreite(doc)
    aussen = (12, mb.DUNKEL)
    innen = (4, DB_LINIE)
    links_b = 9.4
    t = doc.add_table(6, 1)
    tabelle_ohne_rahmen(t)
    zellen = [r.cells[0] for r in t.rows]
    for i, z in enumerate(zellen):
        rahmen(z, left=aussen, right=aussen, top=aussen if i == 0 else innen, bottom=aussen if i == 5 else innen)
        s.zellabstand(z, 0.15, 0.2, 0.3, 0.3)
    # 0: dunkler Kopf mit Hersteller und Datenblattnummer
    k = zellen[0]
    schattieren(k, DB_DUNKEL)
    s.zellabstand(k, 0.15, 0.15, 0.3, 0.3)
    n = mb.zell_tabelle(k, 1, 2)
    tabelle_ohne_rahmen(n)
    a, r = n.rows[0].cells
    s.senkrecht(a); s.senkrecht(r)
    p = s.abstand(a.paragraphs[0])
    mb.r_sperren(s.lauf(p, "{{ hersteller }} ", 13, fett=True, farbe=s.WEISS), 16)
    mb.r_sperren(s.lauf(p, "{{ hersteller_zusatz }}", 13, fett=True, farbe=RGBColor.from_string("F2B33D")), 16)
    p = s.abstand(r.paragraphs[0]); p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    s.lauf(p, "{%p for z in db_kopf %}", 2)
    p = s.abstand(r.add_paragraph()); p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    s.lauf(p, "{{ z }}", 7.5, farbe=s.WEISS)
    mb.tag(r, "{%p endfor %}")
    s.feste_breiten(n, [(b - 0.6) * 0.55, (b - 0.6) * 0.45])
    s.abstand(k.paragraphs[0]).paragraph_format.line_spacing = Pt(1)
    k.paragraphs[0].runs or s.lauf(k.paragraphs[0], "", 1)
    k._tc.remove(k.paragraphs[0]._p)
    mb.schlussabsatz(k)
    # 1: Typ und Untertitel
    z = zellen[1]
    s.lauf(s.abstand(z.paragraphs[0], 0, 0, 1.05), "{{ typ }}", 14, fett=True, farbe=s.RGB_DUNKEL)
    s.lauf(s.abstand(z.add_paragraph()), "{{ untertitel }}", 9, farbe=MITTEL)
    # 2: technische Daten | Anschlussbild, Bestellschlüssel
    z = zellen[2]
    s.zellabstand(z, 0, 0, 0, 0)
    n = mb.zell_tabelle(z, 1, 2)
    tabelle_ohne_rahmen(n)
    li, re = n.rows[0].cells
    rahmen(li, right=innen)
    s.zellabstand(li, 0.1, 0.2, 0.3, 0.3); s.zellabstand(re, 0.1, 0.2, 0.3, 0.3)
    li._tc.remove(li.paragraphs[0]._p)
    db_ueberschrift(li, "Technische Daten")
    d = mb.zell_tabelle(li, 3, 2)
    tabelle_ohne_rahmen(d)
    s.lauf(s.abstand(d.cell(0, 0).paragraphs[0]), "{%tr for x in daten %}", 2)
    s.lauf(s.abstand(d.cell(2, 0).paragraphs[0]), "{%tr endfor %}", 2)
    for j, txt in enumerate(("{{ x[0] }}", "{{r x[1] }}")):
        c = d.cell(1, j)
        rahmen(c, bottom=(4, "DDE1E6"))
        s.zellabstand(c, 0.05, 0.05, 0.1, 0.1)
        s.lauf(s.abstand(c.paragraphs[0], 0, 0, 1.05), txt, 8.5, farbe=MITTEL if j == 0 else None)
    s.feste_breiten(d, [3.6, links_b - 0.8 - 3.6])
    mb.schlussabsatz(li)
    re._tc.remove(re.paragraphs[0]._p)
    mb.tag(re, "{%p if anschlussbild %}")
    db_ueberschrift(re, "Anschlussbild")
    p = mb.text_absatz(re, "", vor=6, nach=4, ausr="mitte")
    s.lauf(p, "{{ anschlussbild }}", 8)
    mb.text_absatz(re, "{{ anschluss_text }}", 8, farbe=MITTEL, nach=4)
    mb.tag(re, "{%p endif %}")
    mb.tag(re, "{%p if bestellschluessel %}")
    db_ueberschrift(re, "Bestellschlüssel", vor=6)
    s.lauf(mb.text_absatz(re), "{{p bestellschluessel }}", 8)
    mb.text_absatz(re, "{{ bestell_text }}", 8, farbe=MITTEL, vor=3)
    mb.tag(re, "{%p endif %}")
    mb.schlussabsatz(re)
    s.feste_breiten(n, [links_b, b - links_b])
    mb.schlussabsatz(z)
    z._tc.remove(z.paragraphs[0]._p)
    # 3: Tabelle (optional)
    z = zellen[3]
    z._tc.remove(z.paragraphs[0]._p)
    mb.tag(z, "{%p if tabelle %}")
    db_ueberschrift(z, "{{ tabelle_titel }}")
    s.lauf(mb.text_absatz(z), "{{p tabelle }}", 8)
    mb.tag(z, "{%p endif %}")
    mb.schlussabsatz(z)
    # 4: Hinweise und Warnung
    z = zellen[4]
    z._tc.remove(z.paragraphs[0]._p)
    db_ueberschrift(z, "Montage- und Anschlusshinweise")
    mb.tag(z, "{%p for h in hinweise %}")
    p = mb.text_absatz(z, "", nach=1, zeile=1.3)
    p.paragraph_format.left_indent = Cm(0.5); p.paragraph_format.first_line_indent = Cm(-0.5)
    mb.tab_stopp(p, 0.5, "left")
    s.lauf(p, "•\t{{ h }}", 9)
    mb.tag(z, "{%p endfor %}")
    mb.tag(z, "{%p if warnung %}")
    mb.text_absatz(z, "", 2, zeile=Pt(4))
    w = mb.zell_tabelle(z, 1, 2)
    tabelle_ohne_rahmen(w)
    gelb = (6, "E0B84A")
    wa, wb = w.rows[0].cells
    rahmen(wa, top=gelb, bottom=gelb, left=gelb); rahmen(wb, top=gelb, bottom=gelb, right=gelb)
    for c in (wa, wb):
        schattieren(c, "FFF4D6"); s.zellabstand(c, 0.1, 0.1, 0.2, 0.2)
    s.senkrecht(wa, "center")
    p = s.abstand(wa.paragraphs[0]); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    mb.r_schrift(s.lauf(p, "⚠", 12, fett=True), mb.SYMBOL)
    s.lauf(s.abstand(wb.paragraphs[0], 0, 0, 1.1), "{{ warnung }}", 9)
    s.feste_breiten(w, [0.9, b - 0.6 - 0.9])
    mb.schlussabsatz(z)
    mb.tag(z, "{%p endif %}")
    mb.schlussabsatz(z)
    # 5: Fuß des Datenblatts
    z = zellen[5]
    s.zellabstand(z, 0.08, 0.08, 0.3, 0.3)
    p = s.abstand(z.paragraphs[0])
    mb.tab_stopp(p, b - 0.6)
    s.lauf(p, "{{ db_fuss_links }}\t{{ db_fuss_rechts }}", 7, farbe=MITTEL)
    s.feste_breiten(t, [b])
    mb.schlussabsatz(doc)
    return doc


def daten_datenblatt(tpl):
    rt = mb.rt
    bestell = mb.tabelle(tpl, None, [["HS-ET 100", "-", "B", "-", "2L", "-", "2,5"],
                                     ["Typ", "", "Klasse", "", "Schaltung", "", "Leitung in m"]],
                         [2.25, 0.45, 1.3, 0.45, 1.3, 0.45, 1.8], groesse=8, linie="9AA3AD", zellen_oben=0.03)
    # zweite Zeile klein und grau, erste Zeile Schreibmaschinenschrift
    sd_tab = bestell.subdocx.tables[0]
    for c in sd_tab.rows[0].cells:
        for r in c.paragraphs[0].runs:
            mb.r_schrift(r, "Courier New"); r.font.size = Pt(9)
    for c in sd_tab.rows[1].cells:
        for r in c.paragraphs[0].runs:
            r.font.size = Pt(6.5); r.font.color.rgb = MITTEL
    gw = mb.tabelle(tpl, None, [
        ["Temperatur in °C", "−50", "0", "50", "100", "150", "200", "250"],
        ["Widerstand in Ω", "80,31", "100,00", "119,40", "138,51", "157,33", "175,86", "194,10"],
        ["Grenzabw. Klasse B in K", "± 0,55", "± 0,30", "± 0,55", "± 0,80", "± 1,05", "± 1,30", "± 1,55"]],
        [3.9] + [(18 - 0.6 - 3.9) / 7] * 7, groesse=8.5, ausr="mitte", zeilenkopf=True, linie="9AA3AD",
        kopf_farbe=s.RGB_DUNKEL)
    return {
        **kopfdaten(),
        "nr": "3", "titel": "Datenblatt des eingebauten Temperaturfühlers",
        "wozu": "Herstellerunterlage zum Fühler an der Siegelstation SG-2, so wie sie in der Anlagenakte liegt.",
        "hersteller": "HASETAL", "hersteller_zusatz": "SENSORIK",
        "db_kopf": ["Datenblatt DB 41.20 · Ausgabe 03/2025", "Seite 1 von 1"],
        "typ": "Einschraub-Widerstandsthermometer HS-ET 100",
        "untertitel": "mit Anschlussleitung, für Heizplatten, Siegel- und Schweißwerkzeuge",
        "daten": [[k, rt(v, 8.5)] for k, v in (
            ("Messelement", "1 × Pt100 nach DIN EN IEC 60751"),
            ("Genauigkeitsklasse", "B (Option: A)"),
            ("Messbereich", "−50 … +250 °C"),
            ("Schaltung", "2-Leiter (Standard), 3- oder 4-Leiter auf Bestellung"),
            ("Schutzrohr", "Ø 6 mm, Edelstahl 1.4571, Einbaulänge 50 mm"),
            ("Prozessanschluss", "Einschraubgewinde G 1/4"),
            ("Anschlussleitung", "Silikon, 2 × 0,5 mm² Cu (bei 2-Leiter), Länge 2,5 m, offene Enden mit Aderendhülsen"),
            ("Ansprechzeit", "t_{0,5} ≈ 3 s, t_{0,9} ≈ 9 s (in Wasser, 0,4 m/s)"),
            ("Messstrom", "empfohlen 0,3 … 1 mA"),
            ("Schutzart", "IP65"))],
        "anschlussbild": InlineImage(tpl, str(mb.ENTWURF / "infoblatt_abb-3.png"), width=Cm(7.8)),
        "anschluss_text": "Aderfarben nach DIN EN IEC 60751: rt = rot, ws = weiß",
        "bestellschluessel": bestell,
        "bestell_text": "Geliefert für Brinkmann Automation, Auftrag 24-1187",
        "tabelle_titel": "Grundwerte und Grenzabweichung (Auszug aus DIN EN IEC 60751)",
        "tabelle": gw,
        "hinweise": [
            "Fühler mit Wärmeleitpaste vollständig in die Bohrung der Heizbacke einschrauben, Anzugsmoment max. 10 Nm.",
            "Anschlussleitung zugentlastet und getrennt von Leistungsleitungen verlegen.",
            "Verlängerungen der Anschlussleitung bauseits mit Klemmen; Leitung und Querschnitt nach Anforderung der "
            "Messung wählen.",
            "Bei Zweileiterschaltung geht der Widerstand der Anschlussleitung in das Messergebnis ein. Der Abgleich "
            "erfolgt im Auswertegerät."],
        "warnung": "Die angegebene Genauigkeitsklasse gilt nur für das Messelement. Abweichungen durch Leitung, "
                   "Klemmstellen und Auswertung sind nicht enthalten.",
        "db_fuss_links": "Hasetal Sensorik GmbH · Technische Änderungen vorbehalten",
        "db_fuss_rechts": "DB 41.20 · 03/2025",
        "datei": "Anlage 3 · Information · Datenblatt HS-ET 100 · Hasetal Sensorik, Brinkmann Automation und "
                 "Nordland Feinkost sind fiktiv",
        "quellen": "Abbildungen eigene Darstellung; Grundwerte nach DIN EN IEC 60751",
        "ki_hinweis": "KI-gestützt erstellt; Werkzeug, Version und Datum siehe KI-Verzeichnis.",
    }


def kopfdaten():
    return {"beruf": "Elektroniker/in, Fachrichtung Automatisierungs- und Systemtechnik",
            "lf": "1", "lf_titel": "Elektrotechnische Systeme analysieren und Funktionen prüfen",
            "ls": "3", "ls_titel": "Der Temperaturfühler zeigt falsche Werte"}


if __name__ == "__main__":
    mb.bauen("infoblatt", vorlage_infoblatt, daten_infoblatt)
    mb.bauen("datenblatt", vorlage_datenblatt, daten_datenblatt)
