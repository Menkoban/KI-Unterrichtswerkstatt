"""Vorlage Einstieg (problemorientiert), zwei Seiten, Optik B (Lehrkraft 2026-10-13).

Seite 1: Handlungssituation als Fließtext unter blauer Linie, Betriebsdokument als schwarz
umrandeter Vordruck (Felder, Ankreuzfelder, Notiz in Handschrift), Auftrag im blau umrandeten
Kasten mit Pfeil, erste Vermutung auf freien Linien.
Seite 2 (optional, Schalter `akte`): Auszug aus Unterlagen (Anlagenakte) als Folge von
Dokumenten mit Text, Tabelle und Stempel, darunter optional eine Abbildung mit Quelle.

Aufruf: python werkzeug/vorlagen/einstieg.py
Erzeugt vorlagen/Vorlage_einstieg.docx, docs/stilreferenz/vorlagen/muster/Muster_einstieg.docx
und die Vorschau vorschau_einstieg-N.png.

Kontext (Auszug): nr, titel, situation_label, situation, vordruck{titel, absender, l1, w1, l2, w2,
zeilen[{label, wert}], kreuz_label, kreuze[{text, an}], notiz_label, notiz[…]}, auftrag_label,
auftrag, unterlagen, vermutung_frage, akte (bool), akte_titel, dokumente[{titel, info, stempel,
text[…], tabelle (Subdoc über material_bausteine.tabelle)}], abb (InlineImage), abb_text,
datei, quellen, ki_hinweis sowie Kopf (beruf, lf, lf_titel, ls, ls_titel).
"""
import sys
from pathlib import Path

from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor
from docxtpl import InlineImage

sys.path.insert(0, str(Path(__file__).parent))
import material_bausteine as mb  # noqa: E402
import schule as s  # noqa: E402
from vorlagen_bauen import rahmen, schattieren, tabelle_ohne_rahmen  # noqa: E402

TINTE = RGBColor.from_string("23345E")
SCHWARZ = "1B1F24"
FELDLINIE = "9AA3AD"


def vordruck(doc, b):
    """Schwarz umrandeter Vordruck (Telefonnotiz, Störmeldung …)."""
    t = doc.add_table(6, 4)
    tabelle_ohne_rahmen(t)
    breiten = [2.5, 8.6, 2.9, b - 14.0]
    aussen = (12, SCHWARZ)
    innen = (4, FELDLINIE)
    # Zeile 0: Titel und Absender
    k = t.cell(0, 0).merge(t.cell(0, 3))
    rahmen(k, top=aussen, left=aussen, right=aussen, bottom=aussen)
    s.zellabstand(k, 0.12, 0.1, 0.25, 0.25)
    p = s.abstand(k.paragraphs[0])
    mb.tab_stopp(p, b - 0.5)
    mb.r_sperren(s.lauf(p, "{{ vordruck.titel }}", 13, fett=True, farbe=s.RGB_DUNKEL), 50)
    s.lauf(p, "\t{{ vordruck.absender }}", 8.5, farbe=s.RGB_DUNKEL)
    # Zeile 1: zwei Felder nebeneinander
    for j, txt in enumerate(("{{ vordruck.l1 }}", "{{ vordruck.w1 }}", "{{ vordruck.l2 }}", "{{ vordruck.w2 }}")):
        z = t.cell(1, j)
        rahmen(z, left=aussen if j == 0 else innen, right=aussen if j == 3 else innen, bottom=innen)
        s.zellabstand(z, 0.07, 0.07, 0.25, 0.2)
        ist_label = j in (0, 2)
        s.lauf(s.abstand(z.paragraphs[0]), txt, 7.5 if ist_label else 10,
               farbe=RGBColor.from_string(mb.MITTEL) if ist_label else s.RGB_DUNKEL)
    # Zeile 2: Schleife über weitere Felder (Anrufer …)
    zeilen = [(2, "{%tr for f in vordruck.zeilen %}", None), (3, "{{ f.label }}", "{{ f.wert }}"),
              (4, "{%tr endfor %}", None)]
    for i, links, rechts in zeilen:
        a = t.cell(i, 0)
        w = t.cell(i, 1).merge(t.cell(i, 3))
        if rechts is None:
            s.lauf(s.abstand(a.paragraphs[0]), links, 2)
            continue
        for z, txt, lab in ((a, links, True), (w, rechts, False)):
            rahmen(z, left=aussen if lab else innen, right=None if lab else aussen, bottom=innen)
            s.zellabstand(z, 0.07, 0.07, 0.25, 0.2)
            s.lauf(s.abstand(z.paragraphs[0]), txt, 7.5 if lab else 10,
                   farbe=RGBColor.from_string(mb.MITTEL) if lab else s.RGB_DUNKEL)
        rahmen(w, left=innen, right=aussen, bottom=innen)
    # Zeile 5: Ankreuzfelder; danach Notiz (zusätzliche Zeile)
    a = t.cell(5, 0); w = t.cell(5, 1).merge(t.cell(5, 3))
    rahmen(a, left=aussen, right=innen, bottom=innen); rahmen(w, left=innen, right=aussen, bottom=innen)
    for z in (a, w):
        s.zellabstand(z, 0.07, 0.07, 0.25, 0.2)
    s.lauf(s.abstand(a.paragraphs[0]), "{{ vordruck.kreuz_label }}", 7.5, farbe=RGBColor.from_string(mb.MITTEL))
    p = s.abstand(w.paragraphs[0])
    s.lauf(p, "{% for k in vordruck.kreuze %}", 10)
    s.lauf(p, "{% if k.an %}", 10)
    mb.r_symbol(p.add_run(), "F0FE", 11)
    s.lauf(p, "{% else %}", 10)
    mb.r_symbol(p.add_run(), "F0A8", 11)
    s.lauf(p, "{% endif %}", 10)
    s.lauf(p, " {{ k.text }}{% if not loop.last %}    {% endif %}{% endfor %}", 10)
    zeile = t.add_row()
    a = zeile.cells[0]; w = zeile.cells[1].merge(zeile.cells[3])
    rahmen(a, left=aussen, right=innen, bottom=aussen); rahmen(w, left=innen, right=aussen, bottom=aussen)
    s.zellabstand(a, 0.1, 0.1, 0.25, 0.2); s.zellabstand(w, 0.1, 0.15, 0.25, 0.25)
    s.lauf(s.abstand(a.paragraphs[0]), "{{ vordruck.notiz_label }}", 7.5, farbe=RGBColor.from_string(mb.MITTEL))
    s.abstand(w.paragraphs[0])
    s.lauf(w.paragraphs[0], "{%p for n in vordruck.notiz %}", 2)
    p = s.abstand(w.add_paragraph(), 0, 1, 1.15)
    mb.r_schrift(s.lauf(p, "– {{ n }}", 10.5, farbe=TINTE), mb.HAND)
    mb.tag(w, "{%p endfor %}")
    mb.schlussabsatz(w)
    s.feste_breiten(t, breiten)
    return t


def auftragskasten(doc, b):
    t = doc.add_table(1, 2)
    tabelle_ohne_rahmen(t)
    pf, inh = t.rows[0].cells
    blau = (16, s.BLAU)
    rahmen(pf, top=blau, bottom=blau, left=blau, right=None)
    rahmen(inh, top=blau, bottom=blau, left=None, right=blau)
    s.senkrecht(pf, "center"); s.senkrecht(inh, "center")
    s.zellabstand(pf, 0.15, 0.15, 0.3, 0.1); s.zellabstand(inh, 0.22, 0.22, 0.1, 0.3)
    p = s.abstand(pf.paragraphs[0]); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    s.lauf(p, "→", 22, fett=True, farbe=s.RGB_BLAU)
    p = s.abstand(inh.paragraphs[0])
    mb.r_sperren(s.kapitaelchen(s.lauf(p, "{{ auftrag_label }}", 7.5, fett=True, farbe=s.RGB_BLAU)), 16)
    p = s.abstand(inh.add_paragraph(), 1, 1, 1.05)
    s.lauf(p, "{{ auftrag }}", 11, fett=True, farbe=s.RGB_DUNKEL)
    p = s.abstand(inh.add_paragraph())
    s.lauf(p, "{% if unterlagen %}Unterlagen: {{ unterlagen }}{% endif %}", 9, farbe=RGBColor.from_string(mb.MITTEL))
    s.feste_breiten(t, [1.3, b - 1.3])
    return t


def akte(doc, b):
    """Rahmen mit den Dokumenten aus der Akte; jede Zeile ein Dokument."""
    t = doc.add_table(3, 1)
    tabelle_ohne_rahmen(t)
    rand = (12, mb.MITTEL)
    s.lauf(s.abstand(t.cell(0, 0).paragraphs[0]), "{%tr for d in dokumente %}", 2)
    s.lauf(s.abstand(t.cell(2, 0).paragraphs[0]), "{%tr endfor %}", 2)
    z = t.cell(1, 0)
    rahmen(z, top=rand, bottom=rand, left=rand, right=rand)
    s.zellabstand(z, 0.18, 0.2, 0.3, 0.3)
    p = s.abstand(z.paragraphs[0], 0, 3)
    mb.tab_stopp(p, b - 0.62)
    s.lauf(p, "{{ d.titel }}", 9.5, fett=True, farbe=s.RGB_DUNKEL)
    s.lauf(p, "\t{{ d.info }}", 7.5, farbe=s.RGB_GRAU)
    s.lauf(p, "{% if d.stempel %}  {% endif %}", 7.5)
    r = s.lauf(p, "{% if d.stempel %} {{ d.stempel }} {% endif %}", 8, fett=True, farbe=RGBColor.from_string("7A2E2E"))
    mb.r_rahmen(r, 12, "7A2E2E")
    mb.tag(z, "{%p for x in d.text %}")
    s.lauf(s.abstand(z.add_paragraph(), 0, 0, 1.1), "{{ x }}", 9)
    mb.tag(z, "{%p endfor %}")
    mb.tag(z, "{%p if d.tabelle %}")
    s.lauf(s.abstand(z.add_paragraph()), "{{p d.tabelle }}", 9)
    mb.tag(z, "{%p endif %}")
    mb.schlussabsatz(z, 2)
    s.feste_breiten(t, [b])
    return t


def vorlage():
    doc = s.dokument("A4")
    mb.schriftersatz(doc)
    b = s.nutzbreite(doc)
    s.kopf(doc)
    s.fusszeile(doc, links="{{ datei }}{% if quellen %} · Quellen: {{ quellen }}{% endif %}", quellen=None)
    # ---------------- Seite 1
    s.titelzeile(doc, schild="Anlage {{ nr }} · Handlungssituation", titel="{{ titel }}", titelgroesse=19)
    mb.text_absatz(doc, "", 6, zeile=Pt(10))
    sit = doc.add_table(1, 1)
    tabelle_ohne_rahmen(sit)
    z = sit.cell(0, 0)
    rahmen(z, top=(16, s.BLAU))
    s.zellabstand(z, 0.2, 0.1, 0.19, 0.19)
    z.paragraphs[0].text = ""
    p = mb.label(z, "{{ situation_label }}", vor=0, nach=2)
    z._tc.remove(z.paragraphs[0]._p)
    p = s.abstand(z.add_paragraph(), 0, 0, 1.45)
    s.lauf(p, "{{ situation }}", 11, farbe=s.RGB_DUNKEL)
    s.feste_breiten(sit, [b])
    mb.text_absatz(doc, "", 6, zeile=Pt(10))
    vordruck(doc, b)
    mb.text_absatz(doc, "", 6, zeile=Pt(12))
    auftragskasten(doc, b)
    mb.label(doc, "{{ vermutung_frage }}", farbe=s.RGB_DUNKEL, vor=10, nach=4)
    s.schreiblinien(doc, 4, 0.85, b)
    mb.schlussabsatz(doc)
    # ---------------- Seite 2: Auszug aus der Akte (optional)
    mb.tag(doc, "{%p if akte %}")
    mb.seitenumbruch(doc)
    s.titelzeile(doc, schild="Anlage {{ nr }} · Informationen", titel="{{ akte_titel }}", namensfeld=False,
                 titelgroesse=17)
    mb.text_absatz(doc, "", 6, zeile=Pt(8))
    akte(doc, b)
    mb.tag(doc, "{%p if abb %}")
    p = mb.text_absatz(doc, "", vor=8, nach=0, ausr="mitte")
    s.lauf(p, "{{ abb }}", 9)
    p = mb.text_absatz(doc, "{{ abb_text }}", 8, farbe=s.RGB_GRAU, vor=3)
    p.paragraph_format.left_indent = Cm(0)
    mb.tag(doc, "{%p endif %}")
    mb.tag(doc, "{%p endif %}")
    return doc


def muster_daten(tpl):
    tab = mb.tabelle
    stamm = tab(tpl, None, [
        ["Baujahr", "2019", "Heizleistung Backe", "4 × 400 W Heizpatronen"],
        ["Temperaturregelung", "Kompaktsteuerung im Schaltschrank +SC1, Pt100-Eingang (2-/3-/4-Leiter wählbar)",
         "Sollwert Siegeltemperatur", "180 °C"],
        ["Druckluft Zylinder", "6 bar", "Taktzeit", "3 s"],
        ["Wartungsintervall", "halbjährlich (zuletzt 03/2026, ohne Befund)", "Folie", "PET/PE, 60 µm"]],
        [3.0, 8.2, 3.3, 2.88], groesse=8.5, zeilenkopf=True)
    leitung = tab(tpl, ["Kabel", "von", "nach", "Typ", "Länge", "Bemerkung"], [
        ["-W12", "Fühler -B1 (Heizbacke)", "+SC1 -X3:5/6", "LIYY 2 × 0,5 mm²", "45 m", "neu 09/2026"],
        ["-W13", "Heizpatronen -E1…E4", "+SC1 -X2", "ÖLFLEX 4G1,5", "45 m", "neu 09/2026"],
        ["-W14", "Zylinder -MM1", "Ventilinsel", "Pneumatikschlauch 8 mm", "3 m", "unverändert"]],
        [1.5, 4.4, 2.8, 4.8, 1.5, 2.38], groesse=8.5)
    datenblatt = tab(tpl, None, [
        ["Messelement", "Pt100, R_{0} = 100 Ω bei 0 °C", "Kennlinie (vereinfacht)", "R = 100 Ω · (1 + 0,00385 K^{−1} · ϑ)"],
        ["Grenzabweichung Klasse B", "± (0,3 + 0,005 · |ϑ|) K", "Messbereich", "−50 … +400 °C"],
        ["Anschluss", "2-Leiter (Standard), 3- und 4-Leiter auf Anfrage", "empfohlener Messstrom", "≤ 1 mA"]],
        [3.6, 6.0, 3.6, 4.18], groesse=8.5, zeilenkopf=True)
    return {
        "beruf": "Elektroniker/in, Fachrichtung Automatisierungs- und Systemtechnik",
        "lf": "1", "lf_titel": "Elektrotechnische Systeme analysieren und Funktionen prüfen",
        "ls": "3", "ls_titel": "Der Temperaturfühler zeigt falsche Werte",
        "nr": "1", "titel": "Reklamation an der Siegelstation",
        "situation_label": "Handlungssituation",
        "situation": "Sie arbeiten als Elektronikerin oder Elektroniker im Kundendienst der Brinkmann Automation GmbH "
                     "in Musterstadt. Montagmorgen, 7:45 Uhr: Meisterin Kerstin Lüken legt Ihnen eine Telefonnotiz auf den "
                     "Tisch. „Nordland Feinkost ist unser wichtigster Kunde. Kümmern Sie sich darum, ich brauche bis "
                     "heute Mittag eine Antwort für den Kunden.“",
        "vordruck": {
            "titel": "TELEFONNOTIZ", "absender": "Brinkmann Automation GmbH · Kundendienst",
            "l1": "Datum / Uhrzeit", "w1": "13.10.2026 · 07:42 Uhr", "l2": "angenommen von", "w2": "K. Lüken",
            "zeilen": [{"label": "Anrufer",
                        "wert": "Hr. Ostendorf, Schichtleitung Linie 2 · Nordland Feinkost GmbH, Werk Musterstadt"}],
            "kreuz_label": "Anliegen",
            "kreuze": [{"text": "Störung", "an": True}, {"text": "Wartung", "an": False},
                       {"text": "Angebot", "an": False}, {"text": "bitte zurückrufen: heute", "an": True}],
            "notiz_label": "Notiz",
            "notiz": ["seit Umbau im Sept. an Siegelstation SG-2 immer wieder Siegelnähte undicht, QS hat 3 Paletten gesperrt",
                      "Steuerung zeigt die ganze Zeit 180 °C = Sollwert („alles im grünen Bereich“)",
                      "Kollege hat mit Prüfthermometer an der Heizbacke gemessen: nur ca. 172 °C!",
                      "Folie i. O. laut Hersteller (Siegelfenster 177 – 183 °C)",
                      "Kunde verärgert"]},
        "auftrag_label": "Auftrag der Meisterin",
        "auftrag": "„Klären Sie die Reklamation und geben Sie dem Kunden eine begründete Empfehlung.“",
        "unterlagen": "Auszug aus der Anlagenakte SG-2 (Seite 2)",
        "vermutung_frage": "Was ist hier eigentlich das Problem? Unsere erste Vermutung",
        "akte": True, "akte_titel": "Auszug aus der Anlagenakte SG-2",
        "dokumente": [
            {"titel": "Anlagenstammblatt Siegelstation SG-2",
             "info": "Nordland Feinkost GmbH · Equipment-Nr. 4711-SG2 · Wartungsvertrag WV-118", "stempel": "",
             "text": [], "tabelle": stamm},
            {"titel": "Umbauprotokoll (Auszug)", "info": "Elektro Sandkamp GmbH, Meppen · 22.09.2026",
             "stempel": "ERLEDIGT", "tabelle": None,
             "text": ["1. Verpackungslinie 2 um 40 m verlängert, Siegelstation SG-2 an neuen Platz versetzt.",
                      "2. Pt100-Einschraubfühler der Heizbacke weiterverwendet, neu angeschlossen.",
                      "3. Neue Zuleitung Fühler ↔ Schaltschrank verlegt (siehe Leitungsliste), Anschluss wie vorher "
                      "in Zweileitertechnik.",
                      "4. Funktionsprüfung: Heizung schaltet, Anzeige plausibel. Keine Parameteränderung an der Steuerung."]},
            {"titel": "Leitungsliste (Auszug)", "info": "Stand nach Umbau", "stempel": "", "text": [],
             "tabelle": leitung},
            {"titel": "Datenblatt Temperaturfühler -B1 (Auszug)",
             "info": "Einschraubfühler Pt100, Klasse B nach DIN EN 60751", "stempel": "", "text": [],
             "tabelle": datenblatt}],
        "abb": InlineImage(tpl, str(mb.ENTWURF / "ts_neutral.png"), width=Cm(13.6)),
        "abb_text": "Abb. 1: Siegelstation SG-2 nach dem Umbau (eigene Darstellung)",
        "datei": "Anlage 1 · Handlungssituation · Brinkmann Automation, Nordland Feinkost und Elektro Sandkamp sind fiktiv.",
        "quellen": "",
        "ki_hinweis": "KI-gestützt erstellt; Werkzeug, Version und Datum siehe KI-Verzeichnis.",
    }


if __name__ == "__main__":
    mb.bauen("einstieg", vorlage, muster_daten)
