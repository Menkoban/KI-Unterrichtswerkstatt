"""Schritt 04: Lernsituation ausarbeiten (Lernsituations-Akte) aus Daten im Arbeitsbereich.

    python lernsituation/ls_ausarbeitung.py <arbeitsbereich> <kurzname>

Daten:    <arbeitsbereich>/.daten/lernsituation/<kurzname>.json
Ergebnis: <ordner>/Lernsituation.docx und Steckbrief. Prüft selbst: Doppelstunden ergeben die
Stunden der Lernsituation, jeder innere Zyklus enthält Planen, alle LK aus der Skizze kommen vor,
Legende vollständig."""
import datetime as dt, json, pathlib, sys
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "akten"))
import steckbrief as sbmod

STUFE = {"Fehler": "F8CBAD", "Warnung": "FFE699", "Hinweis": "C6E0B4"}
PHASEN = ["Informieren", "Planen", "Entscheiden", "Durchführen", "Kontrollieren", "Bewerten"]


def schatten(c, f):
    p = c._tc.get_or_add_tcPr(); s = OxmlElement("w:shd")
    s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), f); p.append(s)


def tabelle(d, kopf, zeilen, breiten, groesse=9.5, faerben=None):
    t = d.add_table(rows=1 if kopf else 0, cols=len(breiten)); t.style = "Table Grid"; t.autofit = False
    if kopf:
        for c, k in zip(t.rows[0].cells, kopf):
            c.text = ""; r = c.paragraphs[0].add_run(k); r.bold = True; r.font.size = Pt(groesse); schatten(c, "D9E2F3")
    for z in zeilen:
        cs = t.add_row().cells
        for i, v in enumerate(z):
            cs[i].text = ""; r = cs[i].paragraphs[0].add_run(str(v)); r.font.size = Pt(groesse)
            if not kopf and i == 0: r.bold = True; schatten(cs[0], "F2F2F2")
        if faerben and faerben(z):
            for c in cs: schatten(c, faerben(z))
    for i, b in enumerate(breiten):
        t.columns[i].width = Cm(b)
        for c in t.columns[i].cells: c.width = Cm(b)
    d.add_paragraph()


def pruefen(s):
    b = []
    std = sum(x.get("std", 2) for x in s["doppelstunden"])
    if std != s["std"]:
        b.append(["Fehler", f"Doppelstunden ergeben {std} Std., die Lernsituation hat {s['std']} Std."])
    for z in s["zyklen"]:
        ph = {p for x in s["doppelstunden"] if x["zyklus"] == z["nr"] for p in x["phasen"]}
        if "Planen" not in ph:
            b.append(["Fehler", f"Zyklus {z['nr']} ohne Planen (Profil: Planen wird nie übersprungen)"])
        fehlt = [p for p in PHASEN if p not in ph]
        if fehlt:
            b.append(["Warnung", f"Zyklus {z['nr']} ohne Phase: {', '.join(fehlt)}"])
    lk = {k for x in s["doppelstunden"] for k in x.get("lk", [])}
    if set(s["lk"]) - lk:
        b.append(["Fehler", "LK der Lernsituation ohne Doppelstunde: " + ", ".join(sorted(set(s["lk"]) - lk))])
    if {z[0] for z in s["lk_legende"]} != set(s["lk"]):
        b.append(["Fehler", "Legende der Lernfeld-Kompetenzen passt nicht zu den LK der Lernsituation"])
    return b


def erzeugen(ab, kurz):
    ab = pathlib.Path(ab)
    s = json.loads((ab / ".daten" / "lernsituation" / f"{kurz}.json").read_text(encoding="utf-8"))
    eigene = pruefen(s)
    d = Document()
    sec = d.sections[0]; sec.orientation = WD_ORIENT.LANDSCAPE; sec.page_width, sec.page_height = Cm(29.7), Cm(21)
    for x in ("left_margin", "right_margin", "top_margin", "bottom_margin"): setattr(sec, x, Cm(1.8))
    st = d.styles["Normal"]; st.font.name = "Arial"; st.font.size = Pt(10.5); st.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    for n in ("Title", "Heading 1"):
        h = d.styles[n]; h.font.name = "Arial"; h.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)
    d.add_heading(f"LS {s['nr']}: {s['titel']}", 0)
    p = d.add_paragraph(f"Lernsituations-Akte · Schritt 04 · {s['lernfeld']} · {s['std']} Std. ({s['std_von_bis']}) · Stand {s['datum']} · {s['stand']}")
    p.runs[0].italic = True
    d.add_heading("Lernsituation", 1)
    tabelle(d, None, [["Kernkompetenz", s["kernkompetenz"]], ["Handlungssituation", s["handlungssituation"]],
                      ["Auftrag", s["auftrag"]], ["Handlungsergebnis", s["handlungsergebnis"]],
                      ["Echte Entscheidung", s["entscheidung"]], ["Lernfeld-Kompetenzen", ", ".join(s["lk"])],
                      ["Bewertung des Handlungsergebnisses", s["bewertung"]]], [5.2, 20.9])
    d.add_heading("Innere vollständige Handlungen (Zyklen)", 1)
    tabelle(d, ["Zyklus", "Leitfrage", "Teilergebnis", "Doppelstunden"],
            [[z["nr"], z["leitfrage"], z["teilergebnis"], z["ds"]] for z in s["zyklen"]], [2, 10.5, 9.6, 4])
    d.add_heading("Doppelstunden", 1)
    tabelle(d, ["DS", "Std.", "Zyklus", "Leitfrage / Thema", "Inhalte", "Teilergebnis", "Phasen", "LK"],
            [[x["ds"], x["std_nr"], x["zyklus"], x["leitfrage"], x["inhalte"], x["teilergebnis"], ", ".join(x["phasen"]), ", ".join(x["lk"])]
             for x in s["doppelstunden"]], [1.0, 1.5, 1.4, 5.0, 6.6, 4.5, 3.9, 2.2], groesse=8.5)
    d.add_heading("Legende: Lernfeld-Kompetenzen dieser Lernsituation", 1)
    tabelle(d, ["LK", "Lernfeld-Kompetenz", "Phase"], s["lk_legende"], [1.8, 20, 4.3], groesse=9)
    d.add_heading("Material, Medien, Bezüge", 1)
    for t in s["hinweise"]: d.add_paragraph(t, style="List Bullet")
    d.add_heading("Prüfbericht", 1)
    tabelle(d, ["Stufe", "Befund"], eigene + s["pruefbericht"], [2.6, 23.5], faerben=lambda z: STUFE[z[0]])
    ziel = ab / s["ordner"] / "Lernsituation.docx"; ziel.parent.mkdir(parents=True, exist_ok=True); d.save(ziel)
    rel = str(ziel.relative_to(ab)); sbp = ab / ".daten" / "akten" / (rel + ".json"); sbp.parent.mkdir(parents=True, exist_ok=True)
    alt = json.loads(sbp.read_text(encoding="utf-8")) if sbp.exists() else {}
    sb = {"art": "lernsituation", "titel": f"LS {s['nr']} {s['titel']}", "pfad": rel, "stand": alt.get("stand", "entwurf"),
          "freigegeben_am": alt.get("freigegeben_am"), "zuletzt_bearbeitet": dt.datetime.now().strftime("%Y-%m-%dT%H:%M"),
          "baut_auf": s["baut_auf"], "fach": s["fach"], "notiz": "Schritt 04"}
    sbmod.schreiben(ab, rel, sb["art"], sb["titel"], sb["baut_auf"], sb["fach"], sb["notiz"], s)
    return ziel, eigene


if __name__ == "__main__":
    z, b = erzeugen(sys.argv[1], sys.argv[2]); print(z); [print(*x) for x in b]
