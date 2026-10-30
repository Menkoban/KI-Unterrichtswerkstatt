"""Kursplan eines Themenkurses als DOCX (Entscheidung Punkt 2, Lehrkraft 2026-10-19).

Der Kursplan wächst im Grilling nach jeder Antwort mit; offene Punkte sind markiert. Gegliedert wie der Themenkurs:
Einstieg, Abschnitte mit Aktivitäten und didaktischer Begründung, Rückblick, Lehrkraftbereich, Bewertungsaufwand.

    python3 werkzeug/kursplan.py <kursplan.json> <ziel.docx>

Format kursplan.json:
    {"kurs": {"name": …, "kurzname": …, "klasse": …, "lf": …, "ls": …, "stand": "JJJJ-MM-TT"},
     "kernkompetenz": …, "handlungssituation": …,
     "abschnitte": [{"name": …, "worum": …, "phasen": ["Informieren", "Planen"],
                     "aktivitaeten": [{"art": "Seite|Test|Aufgabe|…", "titel": …, "aus": "DS 2, Anl. 3",
                                       "tk": …, "phase": …, "warum": …, "fv": …, "zeit": 10,
                                       "sozialform": …, "offen": false}]}],
     "bewertungsaufwand": [ … ], "offene_punkte": [ … ], "nur_fuer_klasse": [ … ]}
"""
import json
import sys
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

BLAU, GRAU, ROT = RGBColor(0x08, 0x34, 0x9C), RGBColor(0x5F, 0x66, 0x70), RGBColor(0xB0, 0x3A, 0x2E)
SPALTEN = [("Aktivität", 4.2), ("aus", 2.0), ("Teilkompetenz · Phase", 4.6), ("Warum diese Aktivität", 8.0),
           ("Fehlvorstellung", 2.6), ("min", 1.1), ("Sozialform", 2.4)]


def _lauf(p, text, groesse=10, fett=False, farbe=None, kursiv=False):
    r = p.add_run(text)
    r.font.size, r.font.bold, r.font.italic, r.font.name = Pt(groesse), fett, kursiv, "Arial"
    if farbe is not None:
        r.font.color.rgb = farbe
    return r


def _schatten(zelle, farbe):
    s = OxmlElement("w:shd"); s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), farbe)
    zelle._tc.get_or_add_tcPr().append(s)


def _ueberschrift(doc, text, groesse=13):
    p = doc.add_paragraph()
    p.paragraph_format.space_before, p.paragraph_format.space_after = Pt(10), Pt(3)
    _lauf(p, text, groesse, fett=True, farbe=BLAU)


def _absatz(doc, text, groesse=10, farbe=None, kursiv=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(3)
    _lauf(p, text, groesse, farbe=farbe, kursiv=kursiv)
    return p


def _tabelle(doc, aktivitaeten):
    t = doc.add_table(rows=1, cols=len(SPALTEN))
    t.style = "Table Grid"
    t.autofit = False                                    # feste Spaltenbreiten, auch in LibreOffice (Gitter setzen)
    for i, (_kopf, breite) in enumerate(SPALTEN):
        t.columns[i].width = Cm(breite)
    for i, (kopf, breite) in enumerate(SPALTEN):
        z = t.rows[0].cells[i]
        z.width = Cm(breite)
        _schatten(z, "E8EEF8")
        _lauf(z.paragraphs[0], kopf, 9, fett=True)
    for a in aktivitaeten:
        zeile = t.add_row().cells
        werte = [f"{a.get('art', '')}: {a.get('titel', '')}", a.get("aus", ""),
                 " · ".join(x for x in (a.get("tk", ""), a.get("phase", "")) if x), a.get("warum", ""),
                 a.get("fv", ""), str(a.get("zeit", "")), a.get("sozialform", "")]
        for i, w in enumerate(werte):
            zeile[i].width = Cm(SPALTEN[i][1])
            _lauf(zeile[i].paragraphs[0], w, 9, fett=(i == 0))
            if a.get("offen"):
                _schatten(zeile[i], "FDEBD3")
    return t


def baue(plan, ziel):
    doc = Document()
    sec = doc.sections[0]
    sec.orientation = WD_ORIENT.LANDSCAPE
    sec.page_width, sec.page_height = Cm(29.7), Cm(21.0)
    for rand in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(sec, rand, Cm(1.5))
    k = plan["kurs"]
    p = doc.add_paragraph()
    _lauf(p, "Kursplan", 9, farbe=GRAU)
    p = doc.add_paragraph()
    _lauf(p, k["name"], 18, fett=True)
    _absatz(doc, f"Kurzname {k.get('kurzname', '')} · Stand {k.get('stand', '')} · offene Punkte orange markiert",
            9, GRAU)
    if plan.get("kernkompetenz"):
        _ueberschrift(doc, "Kernkompetenz", 11)
        _absatz(doc, plan["kernkompetenz"])
    if plan.get("handlungssituation"):
        _ueberschrift(doc, "Handlungssituation", 11)
        _absatz(doc, plan["handlungssituation"])
    summe = 0
    for nr, ab in enumerate(plan.get("abschnitte", []), 1):
        _ueberschrift(doc, ab["name"])
        if ab.get("phasen"):
            _absatz(doc, "Phasen der vollständigen Handlung: " + " · ".join(ab["phasen"]), 9, BLAU)
        if ab.get("worum"):
            _absatz(doc, ab["worum"], kursiv=True)
        if ab.get("aktivitaeten"):
            _tabelle(doc, ab["aktivitaeten"])
            summe += sum(int(a.get("zeit") or 0) for a in ab["aktivitaeten"])
    _absatz(doc, f"Lernzeit der Aktivitäten zusammen: {summe} min", 9, GRAU)
    st = plan.get("sterne")
    if st:                                                   # Sternegewichtung (Freigabe im Kursplan)
        _ueberschrift(doc, f"Sterne (möglich: {st.get('moeglich', '?')})", 11)
        for name, zahl in st.get("tests", {}).items():
            _absatz(doc, f"• {name}: {zahl}")
        for k in ("selbst_geloest", "warum"):
            if st.get(k):
                _absatz(doc, "• " + st[k], kursiv=k == "warum")
    for titel, schluessel, farbe in (("Bewertungsaufwand für die Lehrkraft", "bewertungsaufwand", None),
                                     ("Nur für diese Klasse (nicht weitergeben)", "nur_fuer_klasse", None),
                                     ("Offene Punkte", "offene_punkte", ROT)):
        if plan.get(schluessel):
            _ueberschrift(doc, titel, 11)
            for zeile in plan[schluessel]:
                _absatz(doc, "• " + zeile, farbe=farbe)   # keine Gedankenstriche
    doc.save(ziel)
    return Path(ziel)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    print(baue(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")), sys.argv[2]))
