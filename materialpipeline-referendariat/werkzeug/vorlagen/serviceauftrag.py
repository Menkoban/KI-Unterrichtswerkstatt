"""Vorlage Serviceauftrag (Handlungssituation als Betriebsdokument).

Seite 1: Kopf nach Variante C, Titelzeile mit Namensfeld, optional Wozu, blaue Linie, Handlungssituation als
ruhiger Fließtext (Einstieg Optik B, kein Farbkasten), Formular „SERVICEAUFTRAG“ (Auftragsdaten,
Störungsmeldung, Vorgeschichte, Arbeitsauftrag), erste Vermutung auf freien Linien.
Seite 2: Abbildung der Anlage mit Quelle (optional, `abbildung` als InlineImage) und Formular
„Rückmeldung Techniker“ (Schalter `rueckmeldung`; aus, wenn ein Servicebericht beiliegt).

Der Arbeitsauftrag bleibt neutral (Ursache ermitteln, belegen, Empfehlung geben) und nimmt keine
Methode vorweg (Leitlinie problemorientierter Einstieg).

Aufruf: python werkzeug/vorlagen/serviceauftrag.py
Erzeugt vorlagen/Vorlage_serviceauftrag.docx, docs/stilreferenz/vorlagen/muster/Muster_serviceauftrag.docx
und die Vorschau vorschau_serviceauftrag-N.png.
"""
import sys
from pathlib import Path

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docxtpl import InlineImage

sys.path.insert(0, str(Path(__file__).parent))
import schule as s  # noqa: E402
import messprotokoll as mp  # noqa: E402  Formular-Bausteine
from servicebericht import linien_schleife  # noqa: E402
from vorlagen_bauen import rahmen, schattieren  # noqa: E402

ABB = mp.WURZEL / "docs" / "stilreferenz" / "vorlagen" / "entwurf" / "ts_ohne_leitungsdaten.png"
PRIO_FARBE = "C8452B"


def steuerabsatz(ziel, tag):
    """Absatz nur mit einem {%p … %}-Tag (verschwindet beim Rendern)."""
    p = s.abstand(ziel.add_paragraph())
    s.lauf(p, tag, 7)
    return p


def lauf_schattiert(p, text, groesse, fill, farbe=s.WEISS, fett=True):
    r = s.lauf(p, text, groesse, fett=fett, farbe=farbe)
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), fill)
    r._r.get_or_add_rPr().append(shd)
    return r


def abschnitt(zelle, titel, text, kursiv=False, fett=False):
    mp.bereichstitel(zelle, titel, farbe=s.RGB_DUNKEL, groesse=7.5, vor=4, nach=2)
    p = s.abstand(zelle.add_paragraph(), 0, 3, 1.2)
    s.lauf(p, text, 9.5, fett=fett, kursiv=kursiv, farbe=s.RGB_DUNKEL)
    return p


def vorlage(pfad):
    doc = s.dokument("A4")
    b = s.nutzbreite(doc)
    innen = b - 0.6
    s.kopf(doc)
    s.fusszeile(doc, links=mp.fusstext(), quellen=None)

    # ---------------- Seite 1
    s.titelzeile(doc, schild="Anlage {{ nr }} · Handlungssituation", titel="{{ titel }}")
    steuerabsatz(doc, "{%p if wozu %}")
    s.wozu(doc, linie=False)
    steuerabsatz(doc, "{%p endif %}")
    p = s.abstand(doc.add_paragraph(), 4, 0)
    p.paragraph_format.line_spacing = Pt(2)
    s.absatzlinie(p, (16, s.BLAU))
    p = s.abstand(doc.add_paragraph(), 8, 2)
    r = s.kapitaelchen(s.lauf(p, "Handlungssituation", 8, fett=True, farbe=s.RGB_BLAU))
    mp.gesperrt(r, 16)
    p = s.abstand(doc.add_paragraph(), 0, 10, 1.4)
    s.lauf(p, "{{ situation }}", 10.5, farbe=s.RGB_DUNKEL)

    f = mp.formular(doc, b, 5, trenner={1: mp.RAND, 2: mp.DUENN, 3: mp.DUENN, 4: mp.DUENN})
    mp.formularkopf(f.cell(0, 0), "{{ betrieb }}", "SERVICEAUFTRAG", innen, links_klein="{{ betrieb_zeile }}",
                    fill=mp.KOPF_FILL, rechts_gross=True)
    z = f.cell(1, 0)
    s.zellabstand(z, 0, 0, 0, 0)
    a = mp.datentabelle(z, None, 5, 4, hoehe=0.62)
    zeilen = (("Auftrags-Nr.", "{{ auftrag_nr }}", None, "Erstellt", "{{ erstellt }}", None),
              ("Auftragsart", "{{ auftragsart }}", None, "Priorität", None, None),
              ("Kunde", "{{ kunde }}", "{{ kunde_zusatz }}", "Einsatzort", "{{ einsatzort }}", "{{ einsatzort_zusatz }}"),
              ("Anlage", "{{ anlage }}", "{{ anlage_zusatz }}", "Ansprechpartner", "{{ ansprechpartner }}",
               "{{ ansprechpartner_zusatz }}"))
    for i, (l1, w1, k1, l2, w2, k2) in enumerate(zeilen):
        c = a.rows[i].cells
        mp.label(c[0], l1)
        mp.zelle_fuellen(c[1], w1, 9.5, fett=(i == 0), klein=k1)
        mp.label(c[2], l2)
        if w2 is None:   # Priorität als Kennzeichen
            mp.zelle_fuellen(c[3], "", 9.5)
            p = c[3].paragraphs[0]
            lauf_schattiert(p, " {{ prioritaet }} ", 9, PRIO_FARBE)
            s.lauf(p, " {{ prioritaet_zusatz }}", 9.5, farbe=s.RGB_DUNKEL)
        else:
            mp.zelle_fuellen(c[3], w2, 9.5, klein=k2)
    letzte = a.rows[4].cells
    mp.label(letzte[0], "Techniker/in")
    w = letzte[1].merge(letzte[3])
    for p in w.paragraphs[1:]:
        p._p.getparent().remove(p._p)
    mp.zelle_fuellen(w, "Service-Team: ", 9.5)
    s.lauf(w.paragraphs[0], "{{ techniker }}", 9.5, kursiv=True)
    s.feste_breiten(a, [2.9, 6.6, 2.9, b - 12.4])
    mp.knapp(z.paragraphs[0]); mp.knapp(z.paragraphs[-1])
    abschnitt(f.cell(2, 0), "Störungsmeldung (Angabe des Kunden)", "„{{ meldung }}“", kursiv=True)
    abschnitt(f.cell(3, 0), "Vorgeschichte (aus der Anlagenakte)", "{{ vorgeschichte }}")
    abschnitt(f.cell(4, 0), "Arbeitsauftrag", "{{ arbeitsauftrag }}", fett=True)

    p = s.abstand(doc.add_paragraph(), 14, 0)
    r = s.kapitaelchen(s.lauf(p, "{{ vermutung_titel }}", 8, fett=True, farbe=s.RGB_DUNKEL))
    mp.gesperrt(r, 16)
    # Linien als Schleife direkt im Dokument (über eine Hilfszelle gebaut, dann herausgelöst)
    hilfs = doc.add_table(1, 1)
    linien_schleife(hilfs.cell(0, 0), "vermutung_zeilen or 4", b, 0.85)
    inner = hilfs.cell(0, 0).tables[0]._tbl
    hilfs._tbl.addprevious(inner)
    hilfs._tbl.getparent().remove(hilfs._tbl)

    # ---------------- Seite 2
    mp.seitenumbruch(doc)
    s.titelzeile(doc, schild="Anlage {{ nr }} · Handlungssituation", titel="Serviceauftrag {{ auftrag_nr }}, Seite 2",
                 namensfeld=False, titelgroesse=14)
    steuerabsatz(doc, "{%p if abbildung %}")
    t = doc.add_table(1, 1)
    c = t.cell(0, 0)
    s.zellrand(c, 4, "E1E4E8")
    s.zellabstand(c, 0.25, 0.2, 0.3, 0.3)
    p = s.abstand(c.paragraphs[0])
    p.alignment = 1
    s.lauf(p, "{{ abbildung }}", 9)
    s.feste_breiten(t, [b])
    p = s.abstand(doc.add_paragraph(), 3, 6)
    s.lauf(p, "{{ abbildung_unterschrift }}", 8, farbe=mp.RGB_LABEL)
    steuerabsatz(doc, "{%p endif %}")

    steuerabsatz(doc, "{%p if rueckmeldung %}")
    f = mp.formular(doc, b, 6, trenner={1: mp.RAND, 2: mp.DUENN, 3: mp.DUENN, 4: mp.DUENN})
    mp.formularkopf(f.cell(0, 0), "Rückmeldung Techniker", "{{ auftrag_nr }}", innen,
                    links_klein="vom Service-Team auszufüllen", fill=mp.KOPF_FILL)
    k = f.cell(0, 0).tables[0]
    r = k.cell(0, 1).paragraphs[0].runs[0]
    r.font.size = Pt(11); r.bold = True
    mp.gesperrt(r, 30)
    for i, (titel, n) in enumerate((("Befund / Ursache", 3), ("Durchgeführte Arbeiten und Messwerte", 3),
                                    ("Empfehlung an den Kunden", 2)), start=1):
        z = f.cell(i, 0)
        mp.bereichstitel(z, titel, farbe=s.RGB_DUNKEL, groesse=7.5, vor=4, nach=0)
        mp.linien(z, n, innen, 0.68)
    z = f.cell(4, 0)
    s.zellabstand(z, 0, 0, 0, 0)
    az = mp.datentabelle(z, None, 3, 6, hoehe=0.55)
    for c, txt in zip(az.rows[0].cells, ("Datum", "Techniker/in", "von", "bis", "Std.", "Material")):
        mp.th(c, txt, ausrichtung=1)
    s.feste_breiten(az, [3.2, 4.4, 2.1, 1.8, 2.2, b - 13.7])
    mp.knapp(z.paragraphs[0]); mp.knapp(z.paragraphs[-1])
    z = f.cell(5, 0)
    mp.unterschriften(z, ("Unterschrift Techniker/in", "Unterschrift Kunde"), innen, luecke=1.2, vor=0.8)
    steuerabsatz(doc, "{%p endif %}")
    doc.save(pfad)


def muster_daten():
    return {**mp.GEMEINSAM,
            "nr": "1", "titel": "Störung an der Siegelstation", "wozu": "",
            "situation": "Sie arbeiten als Elektronikerin oder Elektroniker im Kundendienst der Brinkmann Automation "
                         "GmbH in Musterstadt. Heute früh hat Ihnen Meisterin Kerstin Lüken den folgenden Serviceauftrag "
                         "zugeteilt: Bei Ihrem Stammkunden Nordland Feinkost sind seit einem Umbau Siegelnähte "
                         "undicht. Sie sollen die Ursache finden und so belegen, dass der Kunde sie nachvollziehen kann.",
            "erstellt": "13.10.2026, 07:42 Uhr · K. Lüken",
            "auftragsart": "Störungsbeseitigung",
            "prioritaet": "1 – hoch", "prioritaet_zusatz": "Reaktion < 4 h",
            "kunde": "Nordland Feinkost GmbH", "kunde_zusatz": "Kd.-Nr. 10473 · Wartungsvertrag WV-118",
            "einsatzort": "Werk Musterstadt, Halle 3,", "einsatzort_zusatz": "Verpackungslinie 2",
            "anlage": "Siegelstation SG-2", "anlage_zusatz": "Equipment-Nr. 4711-SG2",
            "ansprechpartner": "Schichtleitung Linie 2", "ansprechpartner_zusatz": "Tel. 0591 000-24 (intern)",
            "techniker": "Ihre Namen",
            "meldung": "Seit dem Umbau im September sind an der SG-2 immer wieder Siegelnähte undicht, 3 Paletten "
                       "gesperrt. Die Steuerung zeigt die ganze Zeit 180 °C = Sollwert, unser Prüfthermometer an der "
                       "Heizbacke nur ca. 172 °C. Folie laut Hersteller i. O.",
            "vorgeschichte": "Umbau Linie 2 im September 2026 durch Fremdfirma (Elektro Sandkamp). "
                             "Steuerung und Parameter unverändert. Einzelheiten: Anlagenakte SG-2.",
            "arbeitsauftrag": "Ursache der Störung ermitteln, belegen und dem Kunden eine Empfehlung geben.",
            "vermutung_titel": "Unsere erste Vermutung (vor der Untersuchung)", "vermutung_zeilen": 4,
            "abbildung_unterschrift": "Abb. 1: Siegelstation SG-2 der Verpackungslinie 2 (eigene Darstellung)",
            "rueckmeldung": True,
            "quellen": "Abb. 1 eigene Darstellung",
            "datei": "Anlage 1 · Handlungssituation · Brinkmann Automation, Nordland Feinkost und Elektro Sandkamp sind fiktiv."}


if __name__ == "__main__":
    mp.bauen("serviceauftrag", vorlage, muster_daten(),
             render_extra=lambda tpl: {"abbildung": InlineImage(tpl, str(ABB), width=Cm(16.4))})
