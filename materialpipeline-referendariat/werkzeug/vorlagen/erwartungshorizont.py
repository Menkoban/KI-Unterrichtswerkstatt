"""Vorlage Erwartungshorizont (abgenommen 2026-10-13), Schulkopf nach Profil (schule.*).

Aufruf: python werkzeug/vorlagen/erwartungshorizont.py
Erzeugt vorlagen/Vorlage_erwartungshorizont.docx, docs/stilreferenz/vorlagen/muster/Muster_erwartungshorizont.docx
und die PNG-Vorschau. Vorbild: erwartungshorizont_entwurf.png / entwurf/erwartungshorizont.html.

Kopf wie Arbeitsblatt, graues Schild „Erwartungshorizont zu Anlage n“, kein Vermerk „Nur für die Lehrkraft“.
Tabelle je Aufgabe: erwartete Lösung gerechnet (Ergebnis hervorgehoben), Antwortsatz ja/nein mit Muster,
anerkannte andere Wege und Rundung (immer), typische Fehler mit Reaktion. Darunter „Bezug zum Fall“ und
„Rechenprüfung“. Kompetenzbezug (TK, AFB) nur per Schalter: Liste „kompetenzbezug“ leer = aus.

Daten (Kontext):
  beruf, lf, lf_titel, ls, ls_titel, nr, titel, ki_hinweis, quellen (optional), bezug, rechenpruefung
  aufgaben: Liste von {nr, loesung, ergebnis, antwortsatz ("" = kein Antwortsatz verlangt),
            alternativen, rundung ("" = ohne Rundung), zwischenergebnis (Standard ja; nein = kein Hinweis
            „Kein Antwortsatz verlangt“), fehler: Liste von Texten}
  kopf_loesung: Spaltenkopf (Standard „Erwartete Lösung (gerechnet)“, ohne Rechnung z. B. „Erwartete Lösung“);
  rechenpruefung "" = Kasten entfällt (Anlage ohne Zahlen)
  kompetenzbezug: [] oder Liste von {aufgabe, tk, afb}
Texte mit Formelzeichen und **fett** werden über formel() zu RichText (rendern() erledigt das).
"""
import re
import sys
from pathlib import Path

from docx.enum.text import WD_TAB_ALIGNMENT
from docx.shared import Cm
from docxtpl import DocxTemplate

sys.path.insert(0, str(Path(__file__).parent))
import schule as s  # noqa: E402
from arbeitsblatt import (GRUEN_HELL, RGB_GRUEN_DUNKEL, als_richtext, bauen, buendig, formel, fuss,  # noqa: E402
                          kasten, kopfdaten, schild_farbe, tag, titel, zellabstand)
from vorlagen_bauen import rahmen, schattieren, tabelle_ohne_rahmen  # noqa: E402

TRENN = (6, "C3C9D1")
BREITEN = [2.0, 9.3, 6.7]


def ergebnis(text, groesse=10.5):
    """Ergebnis hervorgehoben: fett, hellblau hinterlegt, blau umrandet (Zeichenrahmen)."""
    rt = formel(text, groesse, fett=True)
    zusatz = ('<w:bdr w:val="single" w:sz="6" w:space="1" w:color="08349C"/>'
              '<w:shd w:val="clear" w:color="auto" w:fill="E8EEF8"/>')
    rt.xml = re.sub(r"<w:rPr>", "<w:rPr>" + zusatz, rt.xml)
    return rt


def aufzaehlung(p, einzug=0.4):
    pf = p.paragraph_format
    pf.left_indent, pf.first_line_indent = Cm(einzug), Cm(-einzug)
    pf.tab_stops.add_tab_stop(Cm(einzug), WD_TAB_ALIGNMENT.LEFT)
    return p


def tabelle_aufgaben(doc, breite):
    t = doc.add_table(4, 3)
    tabelle_ohne_rahmen(t)
    for z, txt in zip(t.rows[0].cells, ("Aufgabe", "{{ kopf_loesung|default('Erwartete Lösung (gerechnet)') }}", "Typische Fehler und Reaktion")):
        schattieren(z, s.BLAU)
        zellabstand(z, 0.12, 0.12, 0.2, 0.2)
        s.lauf(s.abstand(z.paragraphs[0]), txt, 9.5, fett=True, farbe=s.WEISS)
    s.lauf(s.abstand(t.cell(1, 0).paragraphs[0]), "{%tr for a in aufgaben %}", 6)
    s.lauf(s.abstand(t.cell(3, 0).paragraphs[0]), "{%tr endfor %}", 6)
    nr, loe, feh = t.rows[2].cells
    for z in (nr, loe, feh):
        rahmen(z, bottom=TRENN)
        zellabstand(z, 0.2, 0.25, 0.2, 0.2)
    s.lauf(s.abstand(nr.paragraphs[0]), "{{ a.nr }}", 10.5, fett=True, farbe=s.RGB_BLAU)
    # Lösung
    s.lauf(s.abstand(loe.paragraphs[0], 0, 2, 1.35), "{{r a.loesung }}", 10.5)
    s.lauf(s.abstand(loe.add_paragraph(), 2, 3, 1.2), "{{r a.ergebnis }}", 10.5)
    tag(loe, "{%p if a.antwortsatz %}")
    p = s.abstand(loe.add_paragraph(), 0, 2, 1.3)
    s.lauf(p, "Antwortsatz (sinngemäß): „{{ a.antwortsatz }}“", 10)
    tag(loe, "{%p elif a.zwischenergebnis|default(true) %}")
    s.lauf(s.abstand(loe.add_paragraph(), 0, 2, 1.3), "Kein Antwortsatz verlangt (Zwischenergebnis).", 9,
           farbe=s.RGB_GRAU)
    tag(loe, "{%p endif %}")
    tag(loe, "{%p if a.alternativen or a.rundung %}")          # leeres „Auch richtig:“ nicht zeigen
    p = s.abstand(loe.add_paragraph(), 0, 0, 1.3)
    s.lauf(p, "{% if a.alternativen %}Auch richtig: ", 9, fett=True, farbe=s.RGB_GRAU)
    s.lauf(p, "{{ a.alternativen }} {% endif %}", 9, farbe=s.RGB_GRAU)
    s.lauf(p, "{% if a.rundung %}Rundung: ", 9, fett=True, farbe=s.RGB_GRAU)
    s.lauf(p, "{{ a.rundung }}{% endif %}", 9, farbe=s.RGB_GRAU)
    tag(loe, "{%p endif %}")
    # Fehler
    tag(feh, "{%p for f in a.fehler %}")
    p = aufzaehlung(s.abstand(feh.add_paragraph(), 0, 3, 1.3))
    s.lauf(p, "•\t", 10)
    s.lauf(p, "{{r f }}", 10)
    tag(feh, "{%p endfor %}")
    feh._tc.remove(feh.paragraphs[0]._p)  # leeren ersten Absatz entfernen
    s.feste_breiten(t, BREITEN)
    buendig(t)
    return t


def kompetenzbezug(doc, breite):
    """Nur per Schalter: erscheint, wenn die Liste kompetenzbezug nicht leer ist."""
    tag(doc, "{%p if kompetenzbezug %}")
    s.ueberschrift(doc, "Kompetenzbezug", vor=12, nach=3)
    t = doc.add_table(4, 3)
    tabelle_ohne_rahmen(t)
    for z, txt in zip(t.rows[0].cells, ("Aufgabe", "Teilkompetenz (TK)", "AFB")):
        schattieren(z, s.BLAU_HELL)
        zellabstand(z, 0.08, 0.08, 0.2, 0.2)
        s.lauf(s.abstand(z.paragraphs[0]), txt, 9, fett=True, farbe=s.RGB_BLAU)
    s.lauf(s.abstand(t.cell(1, 0).paragraphs[0]), "{%tr for k in kompetenzbezug %}", 6)
    s.lauf(s.abstand(t.cell(3, 0).paragraphs[0]), "{%tr endfor %}", 6)
    for z, txt in zip(t.rows[2].cells, ("{{ k.aufgabe }}", "{{ k.tk }}", "{{ k.afb }}")):
        rahmen(z, bottom=TRENN)
        zellabstand(z, 0.08, 0.08, 0.2, 0.2)
        s.lauf(s.abstand(z.paragraphs[0], 0, 0, 1.25), txt, 9.5)
    s.feste_breiten(t, [BREITEN[0], breite - BREITEN[0] - 3.4, 3.4])
    buendig(t)
    tag(doc, "{%p endif %}")


def vorlage(pfad):
    doc = s.dokument("A4")
    b = s.nutzbreite(doc)
    buendig(s.kopf(doc))
    fuss(doc, "Erwartungshorizont zu {{ art|default('Anlage') }} {{ nr }} · {{ titel }} {%- if fiktiv %} · {{ fiktiv }}{% endif %}")
    s.leer(doc, 8)
    schild_farbe(titel(doc, "Erwartungshorizont zu {{ art|default('Anlage') }} {{ nr }}", namensfeld=False), "5F6670")
    s.wozu(doc)
    tabelle_aufgaben(doc, b)
    s.leer(doc, 12)
    kasten(doc, "Bezug zum Fall:", "{{r bezug }}", fuellung=GRUEN_HELL, randfarbe=s.GRUEN,
           titelfarbe=RGB_GRUEN_DUNKEL, breite=b, groesse=10, titel_im_text=True)
    tag(doc, "{%p if rechenpruefung %}")
    s.leer(doc, 8)
    kasten(doc, "Rechenprüfung:", "{{r rechenpruefung }}", breite=b, groesse=10, titel_im_text=True)
    tag(doc, "{%p endif %}")
    kompetenzbezug(doc, b)
    doc.save(pfad)


def rendern(vorlage_pfad, daten, ziel):
    d = dict(daten)
    d["bezug"] = als_richtext(d["bezug"], groesse=10)
    d["rechenpruefung"] = als_richtext(d["rechenpruefung"], groesse=10) if d.get("rechenpruefung") else ""
    d.setdefault("kompetenzbezug", [])
    d["aufgaben"] = [dict(a, loesung=als_richtext(a["loesung"], groesse=10.5),
                          ergebnis=a["ergebnis"] if not isinstance(a["ergebnis"], str) else ergebnis(a["ergebnis"]),
                          fehler=[als_richtext(f, groesse=10) for f in a["fehler"]])
                     for a in d["aufgaben"]]
    t = DocxTemplate(s.werkzeugvorlage(vorlage_pfad, vorlage))   # Schule und Logo aus dem Profil (ältere Bauskripte)
    t.render(d)
    t.save(ziel)
    _leere_zellen_fuellen(ziel)


def _leere_zellen_fuellen(ziel):
    """Eine leere Liste (z. B. keine typischen Fehler) entfernt mit {%p for %} den einzigen Absatz der Zelle;
    eine Zelle ohne Absatz ist ungültig und verschiebt in Word und LibreOffice die Spalten."""
    from docx import Document
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    doc = Document(ziel)
    leer = [tc for tc in doc.element.body.iter(qn("w:tc")) if tc.find(qn("w:p")) is None]
    for tc in leer:
        tc.append(OxmlElement("w:p"))
    if leer:
        doc.save(ziel)


def zahl(x, stellen):
    return f"{x:.{stellen}f}".replace(".", ",")


def muster_daten():
    r_l = 0.0178 * 90 / 0.5          # 3,204 Ω
    dt = r_l / 0.385                 # 8,32 K
    r_f = 0.0178 * 45 / 0.5          # Fehler: nur einfache Länge, 1,60 Ω
    assert f"{r_l:.2f}" == "3.20" and f"{dt:.1f}" == "8.3" and f"{r_f / 0.385:.2f}" == "4.16"
    return dict(kopfdaten(), **{
        "wozu": "Grundlage für Besprechung und Rückmeldung: erwartete Lösungen, anerkannte andere Wege und typische Fehler.",
        "quellen": "",
        "aufgaben": [
            {"nr": "1",
             "loesung": "Länge Hin- und Rückleiter: l_{ges} = 2 · 45 m = 90 m\n"
                        "R_L = ρ · l_{ges} / A = 0,0178 Ω·mm²/m · 90 m / 0,5 mm²",
             "ergebnis": "R_L = 3,20 Ω ≈ 3,2 Ω",
             "antwortsatz": "",
             "alternativen": "je Leiter 1,60 Ω rechnen und verdoppeln.",
             "rundung": "eine Nachkommastelle genügt (3,2 Ω).",
             "fehler": [
                 "**nur 45 m** gerechnet → 1,60 Ω. Reaktion: Hilfekarte 1, Stromweg am Schaltbild nachfahren lassen.",
                 "**mm² in m² umgerechnet** → Ergebnis um 10⁶ falsch. Reaktion: Einheit von ρ zeigen, "
                 "mm² kürzt sich.",
                 "**durch ρ statt A geteilt**. Reaktion: Formel im Tabellenbuch nachschlagen lassen."]},
            {"nr": "2",
             "loesung": "Δϑ = R_L / 0,385 Ω/K = 3,20 Ω / 0,385 Ω/K",
             "ergebnis": "Δϑ = 8,3 K",
             "antwortsatz": "Die Zuleitung erhöht den gemessenen Widerstand um 3,2 Ω; die Steuerung zeigt deshalb "
                            "etwa 8 K zu viel an. Das erklärt die Meldung des Kunden.",
             "alternativen": "über die Kennlinie: 100 Ω + 3,2 Ω entsprechen etwa 8 K; "
                             "Rechnung mit 3,2 Ω ergibt ebenfalls 8,3 K.",
             "rundung": "8 K bis 8,5 K; Angabe „rund 8 K“ genügt im Antwortsatz.",
             "fehler": [
                 "**Kehrwert** gebildet (0,12 K). Reaktion: Einheitenkontrolle, Ω muss sich kürzen.",
                 "**Folgefehler aus 1** (4,2 K bei 1,6 Ω). Reaktion: als Folgefehler werten, Rechenweg richtig."]},
        ],
        "bezug": "Der berechnete Fehler (8,3 K) passt zur Kundenmeldung „rund 8 °C mehr“. Die Messung in Anlage 5 "
                 "mit der Nachbildung 3,3 Ω (E12) liefert erwartungsgemäß etwa 8,6 K; die Abweichung zur Rechnung "
                 "erklärt sich aus E-Reihe und Toleranz.",
        "rechenpruefung": f"Alle Werte mit Einheiten nachgerechnet: R_L = {zahl(r_l, 3)} Ω; Δϑ = {zahl(dt, 2)} K; "
                          f"Fehlerwerte {zahl(r_f, 2)} Ω / {zahl(r_f / 0.385, 2)} K. "
                          "Übereinstimmung mit dem Materialauftrag.",
        "kompetenzbezug": [],
    })


def muster_mit_kompetenzbezug():
    d = muster_daten()
    d["kompetenzbezug"] = [
        {"aufgabe": "1", "tk": "Sie berechnen den Widerstand einer Zuleitung aus Länge, Querschnitt und Werkstoff.",
         "afb": "II"},
        {"aufgabe": "2", "tk": "Sie beurteilen den Einfluss des Leitungswiderstands auf die Temperaturmessung.",
         "afb": "II–III"},
    ]
    return d


if __name__ == "__main__":
    bauen("erwartungshorizont", vorlage, muster_daten(), rendern)
