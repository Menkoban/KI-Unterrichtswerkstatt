"""Vorlage Servicebericht (Bericht an den Kunden als Formular des Betriebs, Variante A).

Kopf nach Variante C, Titelzeile mit Namensfeld, Wozu, Formular „SERVICEBERICHT“: Auftragsdaten,
Befund, Ursache mit Beleg, durchgeführte Arbeiten, Empfehlung, Material, Status, Anlagen,
Unterschriften. Die Überschriften geben Struktur, keinen Inhalt.

Die Abschnitte stehen als Schleife `abschnitte` (Titel, Zeilenzahl) in der Vorlage; ohne Angabe gelten
die Standardabschnitte aus ABSCHNITTE.

Aufruf: python werkzeug/vorlagen/servicebericht.py
Erzeugt vorlagen/Vorlage_servicebericht.docx, docs/stilreferenz/vorlagen/muster/Muster_servicebericht.docx
und die Vorschau vorschau_servicebericht-N.png.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import schule as s  # noqa: E402
import messprotokoll as mp  # noqa: E402  Formular-Bausteine
from vorlagen_bauen import rahmen, tabelle_ohne_rahmen  # noqa: E402

def linien_schleife(zelle, anzahl, breite, hoehe=0.6):
    """Schreiblinien als Zeilenschleife: anzahl ist ein Jinja-Ausdruck (z. B. „ab.zeilen or 3“)."""
    t = zelle.add_table(3, 1)
    tabelle_ohne_rahmen(t)
    for i, zeile in enumerate(t.rows):
        c = zeile.cells[0]
        s.zellabstand(c, 0, 0, 0, 0)
        p = s.abstand(c.paragraphs[0])
        if i == 0:
            s.lauf(p, "{%%tr for _ in range(%s) %%}" % anzahl, 2)
        elif i == 2:
            s.lauf(p, "{%tr endfor %}", 2)
        else:
            s.zeilenhoehe(zeile, hoehe)
            rahmen(c, bottom=(4, mp.FLINIE))
    s.feste_breiten(t, [breite])
    mp.knapp(zelle.paragraphs[-1])
    return t


ABSCHNITTE = [
    {"titel": "Befund (was wurde festgestellt?)", "zeilen": 3},
    {"titel": "Ursache (mit Beleg: Messung, Rechnung, Unterlage)", "zeilen": 4},
    {"titel": "Durchgeführte Arbeiten", "zeilen": 3},
    {"titel": "Empfehlung an den Kunden", "zeilen": 4},
    {"titel": "Material / Ersatzteile", "zeilen": 2},
]

STATUS = ["Störung behoben", "provisorisch behoben", "offen, Angebot folgt"]
ANLAGEN = ["Prüfprotokoll", "Fotos", "Datenblatt"]
# Standardwerte als Jinja-Literale ohne geschweifte Klammern (docxtpl-Tags vertragen keine „}“)
STANDARD_ABSCHNITTE = "[" + ", ".join('dict(titel="%s", zeilen=%d)' % (a["titel"], a["zeilen"]) for a in ABSCHNITTE) + "]"
STANDARD_STATUS = "[" + ", ".join('"%s"' % o for o in STATUS) + "]"
STANDARD_ANLAGEN = "[" + ", ".join('"%s"' % o for o in ANLAGEN) + "]"


def ankreuzzeile(zelle, titel, optionen_platzhalter, groesse=8.5, fett_titel=True, farbe=None):
    p = mp.absatz_in(zelle)
    s.abstand(p, 3, 3)
    s.lauf(p, titel + " ", groesse, fett=fett_titel, farbe=farbe or s.RGB_DUNKEL)
    s.lauf(p, optionen_platzhalter, groesse, farbe=farbe or s.RGB_DUNKEL)
    return p


def vorlage(pfad):
    doc = s.dokument("A4")
    b = s.nutzbreite(doc)
    innen = b - 0.6
    s.kopf(doc)
    s.fusszeile(doc, links=mp.fusstext(), quellen=None)
    s.titelzeile(doc, schild="Anlage {{ nr }} · Servicebericht", titel="{{ titel }}")
    s.wozu(doc)

    # Formular: Kopf | Auftragsdaten | Schleife Abschnitte | Status | Anlagen | Unterschriften
    f = mp.formular(doc, b, 8, trenner={1: mp.RAND, 2: mp.RAND, 3: mp.DUENN, 4: mp.DUENN, 5: mp.DUENN,
                                         6: mp.DUENN, 7: None})
    mp.formularkopf(f.cell(0, 0), "{{ betrieb }}", "SERVICEBERICHT", innen, links_klein="{{ betrieb_zeile }}",
                    fill=mp.KOPF_FILL, rechts_gross=True)
    # Auftragsdaten ohne Innenabstand des Rahmens (Tabelle bündig)
    z = f.cell(1, 0)
    s.zellabstand(z, 0, 0, 0, 0)
    a = mp.datentabelle(z, None, 3, 4, hoehe=0.6)
    for i, (l1, w1, l2, w2) in enumerate((
            ("Auftrags-Nr.", "{{ auftrag_nr }}", "Kunde", "{{ kunde }}"),
            ("Anlage", "{{ anlage }}", "Techniker/in", "{{ techniker or '' }}"),
            ("Einsatz am", "{{ einsatz_am or '' }}", "Arbeitszeit", "von ______ bis ______ Uhr"))):
        c = a.rows[i].cells
        mp.label(c[0], l1); mp.zelle_fuellen(c[1], w1, fett=(i == 0)); mp.label(c[2], l2); mp.zelle_fuellen(c[3], w2)
    s.feste_breiten(a, [2.9, 6.1, 2.9, b - 11.9])
    mp.knapp(z.paragraphs[0]); mp.knapp(z.paragraphs[-1])

    # Abschnitte als Schleife (je Zeile der Formulartabelle ein Abschnitt)
    s.lauf(s.abstand(f.cell(2, 0).paragraphs[0]),
           "{%tr for ab in (abschnitte or " + STANDARD_ABSCHNITTE + ") %}", 7)
    z = f.cell(3, 0)
    mp.bereichstitel(z, "{{ ab.titel }}", farbe=s.RGB_DUNKEL, groesse=7, vor=4, nach=0)
    linien_schleife(z, "ab.zeilen or 3", innen)
    s.lauf(s.abstand(f.cell(4, 0).paragraphs[0]), "{%tr endfor %}", 7)

    z = f.cell(5, 0)
    ankreuzzeile(z, "Status:", "{% for o in status_optionen or " + STANDARD_STATUS + " %}☐ {{ o }}    {% endfor %}")
    z = f.cell(6, 0)
    ankreuzzeile(z, "Anlagen:", "{% for o in anlagen_optionen or " + STANDARD_ANLAGEN + " %}☐ {{ o }}    {% endfor %}",
                 groesse=7.5, fett_titel=False, farbe=mp.RGB_LABEL)
    z = f.cell(7, 0)
    mp.unterschriften(z, ("Ort, Datum", "Techniker/in", "Kunde (Abnahme)"), innen, vor=0.75)
    doc.save(pfad)




def muster_daten():
    return {**mp.GEMEINSAM,
            "nr": "6", "titel": "Bericht an den Kunden",
            "wozu": "Sie schließen den Serviceauftrag ab und dokumentieren Ergebnis und Empfehlung für den Kunden, "
                    "so wie im Betrieb üblich.",
            "kunde": "Nordland Feinkost GmbH, Werk Musterstadt",
            "anlage": "Siegelstation SG-2 · Equipment-Nr. 4711-SG2",
            "techniker": "", "einsatz_am": "",
            "datei": "Anlage 6 · Servicebericht · Brinkmann Automation und Nordland Feinkost sind fiktiv."}


if __name__ == "__main__":
    mp.bauen("servicebericht", vorlage, muster_daten())
