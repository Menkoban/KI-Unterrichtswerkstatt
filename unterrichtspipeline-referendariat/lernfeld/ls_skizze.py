"""Schritt 02: Lernsituationen-Skizze eines Lernfelds aus Daten im Arbeitsbereich.

    python lernfeld/ls_skizze.py <arbeitsbereich> <kurzname>

Daten:    <arbeitsbereich>/.daten/ls_skizze/<kurzname>.json
Ergebnis: <ordner>/Lernsituationen_Skizze.docx und Steckbrief. Prüft selbst: Stundensumme =
Zeitrichtwert, jede LK mindestens einmal. Geplant wird ohne Kalender (KONZEPT 5b); Grenzen wie
Ferien prüft es nur, wenn die Lehrkraft sie in den Daten ausdrücklich setzt (`grenzen`)."""
import datetime as dt, json, pathlib, sys
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "akten"))
import steckbrief as sbmod

STUFE = {"Fehler": "F8CBAD", "Warnung": "FFE699", "Hinweis": "C6E0B4"}


def schatten(c, f):
    p = c._tc.get_or_add_tcPr(); s = OxmlElement("w:shd")
    s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), f); p.append(s)


def tabelle(d, kopf, zeilen, breiten, groesse=9.5, faerben=None):
    t = d.add_table(rows=1, cols=len(kopf)); t.style = "Table Grid"; t.autofit = False
    for c, k in zip(t.rows[0].cells, kopf):
        c.text = ""; r = c.paragraphs[0].add_run(k); r.bold = True; r.font.size = Pt(groesse); schatten(c, "D9E2F3")
    for z in zeilen:
        cs = t.add_row().cells
        for i, v in enumerate(z):
            cs[i].text = ""; r = cs[i].paragraphs[0].add_run(str(v)); r.font.size = Pt(groesse)
        if faerben and faerben(z):
            for c in cs: schatten(c, faerben(z))
    for i, b in enumerate(breiten):
        t.columns[i].width = Cm(b)
        for c in t.columns[i].cells: c.width = Cm(b)
    d.add_paragraph()


def pruefen(s):
    befunde = []
    summe = sum(x["std"] for x in s["ablauf"])
    if summe != s["zeitrichtwert"]:
        befunde.append(["Fehler", f"Stundensumme {summe} ≠ Zeitrichtwert {s['zeitrichtwert']}"])
    lk = {k for x in s["ablauf"] for k in x.get("lk", [])}
    fehlend = [k for k in s["lk_alle"] if k not in lk]
    leg = {z[0] for z in s.get("lk_legende", [])}
    if leg != set(s["lk_alle"]):
        befunde.append(["Fehler", "Legende der Lernfeld-Kompetenzen fehlt oder ist unvollständig"])
    if fehlend:
        befunde.append(["Fehler", "Lernfeld-Kompetenzen ohne Lernsituation: " + ", ".join(fehlend)])
    kum = 0
    grenzen = {g["nach_std"]: g["was"] for g in s.get("grenzen", [])}
    for x in s["ablauf"]:
        a, kum = kum + 1, kum + x["std"]
        for g, was in grenzen.items():
            if a <= g < kum:
                befunde.append(["Warnung", f"{x['titel']} läuft über {was} (nach Std. {g})"])
    return befunde


def erzeugen(ab, kurz):
    ab = pathlib.Path(ab)
    s = json.loads((ab / ".daten" / "ls_skizze" / f"{kurz}.json").read_text(encoding="utf-8"))
    eigene = pruefen(s)
    d = Document()
    sec = d.sections[0]; sec.orientation = WD_ORIENT.LANDSCAPE
    sec.page_width, sec.page_height = Cm(29.7), Cm(21)
    for x in ("left_margin", "right_margin", "top_margin", "bottom_margin"): setattr(sec, x, Cm(1.8))
    st = d.styles["Normal"]; st.font.name = "Arial"; st.font.size = Pt(10.5); st.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    for n in ("Title", "Heading 1"):
        h = d.styles[n]; h.font.name = "Arial"; h.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)
    d.add_heading(s["titel"], 0)
    p = d.add_paragraph(f"Lernfeld-Akte · Schritt 02 · Stand {s['datum']} · {s['stand']}"); p.runs[0].italic = True
    d.add_heading("Eckdaten", 1)
    tabelle(d, ["Merkmal", "Angabe"], s["meta"], [5, 21.1])
    d.add_heading("Leitlinie", 1)
    for t in s["leitlinie"]: d.add_paragraph(t)
    d.add_heading("Übergeordnete Handlungssituation", 1)
    d.add_paragraph(s["handlungssituation"])
    d.add_heading("Lernsituationen in zeitlicher Folge", 1).paragraph_format.page_break_before = True
    zeilen, kum = [], 0
    for x in s["ablauf"]:
        a, kum = kum + 1, kum + x["std"]
        zeilen.append([x["nr"], x["titel"], x.get("situation", ""), x.get("ergebnis", ""), x.get("entscheidung", ""),
                       ", ".join(x.get("lk", [])), x["std"], f"{a}–{kum}"])
        for g in s.get("grenzen", []):
            if g["nach_std"] == kum:
                zeilen.append(["", g["was"], "", "", "", "", "", ""])
    tabelle(d, ["LS", "Titel", "Handlungssituation", "Handlungsergebnis", "Echte Entscheidung", "LK", "Std.", "Std. von–bis"],
            zeilen, [1.0, 3.6, 7.2, 5.0, 4.3, 2.0, 1.1, 1.9], groesse=8.5,
            faerben=lambda z: "F2F2F2" if z[0] == "" else None)
    d.add_heading("Legende: Lernfeld-Kompetenzen (aus der curricularen Analyse)", 1)
    tabelle(d, ["LK", "Lernfeld-Kompetenz", "Phase", "Kompetenzbereich"], s["lk_legende"], [1.8, 17.3, 3.2, 3.8], groesse=9)
    d.add_heading("Inhaltsschwerpunkte und mathematische Grundlagen", 1)
    tabelle(d, ["LS", "Inhaltsschwerpunkt (Pflicht-Inhaltskatalog)", "Eingeführte mathematische Grundlage", "Lernort Betrieb (ARP)"],
            [[x["nr"], x.get("inhalt", ""), x.get("mathe", ""), x.get("arp", "")] for x in s["ablauf"] if x["nr"] not in ("", "–")],
            [1.0, 11.0, 7.5, 6.6], groesse=9)
    d.add_heading("Abdeckung und Abgrenzung", 1)
    for t in s["abdeckung"]: d.add_paragraph(t, style="List Bullet")
    d.add_heading("Prüfbericht", 1)
    tabelle(d, ["Stufe", "Befund"], eigene + s["pruefbericht"], [2.6, 23.5], faerben=lambda z: STUFE[z[0]])
    ziel = ab / s["ordner"] / "Lernsituationen_Skizze.docx"; ziel.parent.mkdir(parents=True, exist_ok=True); d.save(ziel)
    rel = str(ziel.relative_to(ab)); sbp = ab / ".daten" / "akten" / (rel + ".json"); sbp.parent.mkdir(parents=True, exist_ok=True)
    alt = json.loads(sbp.read_text(encoding="utf-8")) if sbp.exists() else {}
    sb = {"art": "lernfeld", "titel": s["kurztitel"], "pfad": rel, "stand": alt.get("stand", "entwurf"),
          "freigegeben_am": alt.get("freigegeben_am"), "zuletzt_bearbeitet": dt.datetime.now().strftime("%Y-%m-%dT%H:%M"),
          "baut_auf": s["baut_auf"], "fach": s["fach"], "notiz": "Schritt 02"}
    sbmod.schreiben(ab, rel, sb["art"], sb["titel"], sb["baut_auf"], sb["fach"], sb["notiz"], s)
    return ziel, eigene


if __name__ == "__main__":
    z, b = erzeugen(sys.argv[1], sys.argv[2]); print(z); [print(*x) for x in b]
