"""Modellbetrieb je Beruf/Fachrichtung (Schritt 02): erzeugt das DOCX aus den Daten im Arbeitsbereich.

    python modellbetrieb/modellbetrieb.py <arbeitsbereich> <kurzname>

Daten:    <arbeitsbereich>/.daten/modellbetrieb/<kurzname>.json
Ergebnis: <arbeitsbereich>/<fach>/<beruf>/Modellbetrieb_<Name>.docx und Steckbrief."""
import datetime as dt, json, pathlib, sys
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "akten"))
import steckbrief as sbmod

STUFE = {"Fehler": "F8CBAD", "Warnung": "FFE699", "Hinweis": "C6E0B4"}


def schatten(c, f):
    p = c._tc.get_or_add_tcPr(); s = OxmlElement("w:shd")
    s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), f); p.append(s)


def tabelle(d, kopf, zeilen, breiten, faerben=None):
    t = d.add_table(rows=1 if kopf else 0, cols=len(breiten)); t.style = "Table Grid"; t.autofit = False
    if kopf:
        for c, k in zip(t.rows[0].cells, kopf):
            c.text = ""; c.paragraphs[0].add_run(k).bold = True; schatten(c, "D9E2F3")
    for z in zeilen:
        cs = t.add_row().cells
        for i, v in enumerate(z): cs[i].text = str(v)
        if not kopf: cs[0].paragraphs[0].runs[0].bold = True; schatten(cs[0], "F2F2F2")
        if faerben and faerben(z): schatten(cs[0], faerben(z))
    for i, b in enumerate(breiten):
        t.columns[i].width = Cm(b)
        for c in t.columns[i].cells: c.width = Cm(b)
    d.add_paragraph()


def erzeugen(ab, kurz):
    ab = pathlib.Path(ab)
    m = json.loads((ab / ".daten" / "modellbetrieb" / f"{kurz}.json").read_text(encoding="utf-8"))
    d = Document()
    s = d.sections[0]; s.page_width, s.page_height = Cm(21), Cm(29.7)
    for x in ("left_margin", "right_margin", "top_margin", "bottom_margin"): setattr(s, x, Cm(2))
    st = d.styles["Normal"]; st.font.name = "Arial"; st.font.size = Pt(10.5); st.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    for n in ("Title", "Heading 1"):
        h = d.styles[n]; h.font.name = "Arial"; h.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)
    d.add_heading(f"Modellbetrieb {m['name']}", 0)
    p = d.add_paragraph(f"{m['beruf']} · gilt für alle Lernfelder · Stand {m['datum']} · {m['stand']}"); p.runs[0].italic = True
    d.add_paragraph("Alle Personen, Firmen und Aufträge sind frei erfunden. Ähnlichkeiten mit echten Betrieben sind nicht "
                    "beabsichtigt; die Namen wurden per Websuche geprüft (siehe Prüfbericht).")
    d.add_heading("1. Steckbrief", 1); tabelle(d, None, m["steckbrief"], [4, 13])
    d.add_heading("2. Personen", 1); tabelle(d, ["Rolle", "Name", "Was die Person in den Lernsituationen tut"], m["personen"], [3.5, 4.3, 9.2])
    d.add_heading("3. Rolle der Lernenden", 1)
    for t in m["rolle"]: d.add_paragraph(t)
    d.add_heading("4. Stammkunden", 1); tabelle(d, ["Kunde", "Art", "Was dort wiederkehrt"], m["kunden"], [4.3, 3.7, 9])
    d.add_heading("5. Der Betrieb wächst mit", 1); tabelle(d, ["Ausbildungsjahr", "Typische Aufträge"], m["wachsen"], [3.5, 13.5])
    d.add_heading("6. Übergeordnete Handlungssituation je Lernfeld", 1)
    for t in m["handlungssituation"]: d.add_paragraph(t)
    d.add_heading("7. Wiederkehrende Elemente", 1)
    for t in m["elemente"]: d.add_paragraph(t)
    d.add_heading("8. Regeln für alle Lernsituationen", 1)
    for t in m["regeln"]: d.add_paragraph(t, style="List Bullet")
    d.add_heading("Prüfbericht", 1)
    tabelle(d, ["Stufe", "Befund"], m["pruefbericht"], [2.6, 14.4], faerben=lambda z: STUFE[z[0]])
    ziel = ab / m["ordner"] / f"Modellbetrieb_{m['dateiname']}.docx"; ziel.parent.mkdir(parents=True, exist_ok=True); d.save(ziel)
    rel = str(ziel.relative_to(ab)); sbp = ab / ".daten" / "akten" / (rel + ".json"); sbp.parent.mkdir(parents=True, exist_ok=True)
    alt = json.loads(sbp.read_text(encoding="utf-8")) if sbp.exists() else {}
    sb = {"art": "modellbetrieb", "titel": f"Modellbetrieb {m['name']}", "pfad": rel, "stand": alt.get("stand", "entwurf"),
          "freigegeben_am": alt.get("freigegeben_am"), "zuletzt_bearbeitet": dt.datetime.now().strftime("%Y-%m-%dT%H:%M"),
          "baut_auf": [], "fach": m["fach"], "notiz": f"Schritt 02; {m['beruf']}"}
    sbmod.schreiben(ab, rel, sb["art"], sb["titel"], sb["baut_auf"], sb["fach"], sb["notiz"], m)
    return ziel


if __name__ == "__main__":
    print(erzeugen(sys.argv[1], sys.argv[2]))
