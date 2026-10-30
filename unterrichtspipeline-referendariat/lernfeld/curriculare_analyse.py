"""Schritt 01: Curriculare Analyse eines Lernfelds aus Daten im Arbeitsbereich.

    python lernfeld/curriculare_analyse.py <arbeitsbereich> <kurzname>

Daten:    <arbeitsbereich>/.daten/curriculare_analyse/<kurzname>.json
Ergebnis: <ordner>/Curriculare_Analyse.docx und Steckbrief. Prüft selbst: Quelle genannt,
LK lückenlos nummeriert, jede LK mit Phase, AFB und Kompetenzbereich, alle Phasen der
vollständigen Handlung vertreten, Inhaltskatalog mit Pflichtteil, Abgrenzung zu Nachbar-
Lernfeldern, Lernort Betrieb aus der Liste der Entsprechungen."""
import datetime as dt, json, pathlib, sys
from docx import Document
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "lernsituation"))
from ls_ausarbeitung import STUFE, tabelle
sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "akten"))
import steckbrief as sbmod

PHASEN = ["Informieren", "Planen", "Entscheiden", "Ausführen", "Kontrollieren", "Bewerten"]


def pruefen(s):
    b = []
    if not any(k == "Quelle" for k, _ in s["meta"]):
        b.append(["Fehler", "Quelle des Rahmenlehrplans fehlt in den Eckdaten"])
    for i, x in enumerate(s["lk"], 1):
        if x[0] != f"LK-{i:02d}":
            b.append(["Fehler", f"LK-Nummer {x[0]} an Stelle {i} (lückenlos LK-01 …)"])
        if not all(x[2:5]):
            b.append(["Fehler", f"{x[0]}: Phase, AFB oder Kompetenzbereich fehlt"])
    ph = " ".join(x[2] for x in s["lk"])
    fehlt = [p for p in PHASEN if p not in ph]
    if fehlt:
        b.append(["Warnung", "Phasen der vollständigen Handlung ohne LK: " + ", ".join(fehlt)])
    if not s["inhaltskatalog"].get("pflicht"):
        b.append(["Fehler", "Inhaltskatalog ohne Pflichtteil"])
    if not s.get("abgrenzung"):
        b.append(["Fehler", "Abgrenzung zu Nachbar-Lernfeldern fehlt"])
    if not s.get("lernort"):
        b.append(["Warnung", "Lernort Betrieb (Liste der Entsprechungen) fehlt"])
    return b


def erzeugen(ab, kurz):
    ab = pathlib.Path(ab)
    s = json.loads((ab / ".daten" / "curriculare_analyse" / f"{kurz}.json").read_text(encoding="utf-8"))
    eigene = pruefen(s)
    d = Document()
    sec = d.sections[0]; sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    for x in ("left_margin", "right_margin", "top_margin", "bottom_margin"): setattr(sec, x, Cm(2.0))
    st = d.styles["Normal"]; st.font.name = "Arial"; st.font.size = Pt(10.5); st.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    for n in ("Title", "Heading 1", "Heading 2"):
        h = d.styles[n]; h.font.name = "Arial"; h.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)
    d.add_heading(s["titel"], 0)
    p = d.add_paragraph(f"Lernfeld-Akte · Schritt 01 · Stand {s['datum']} · {s['stand']}"); p.runs[0].italic = True
    d.add_heading("Eckdaten", 1)
    tabelle(d, None, s["meta"], [4.5, 12.5])
    p = d.add_paragraph(); p.add_run("Kernkompetenz (Lehrplan): ").bold = True; p.add_run(s["kernkompetenz"])
    d.add_heading("Lernfeld-Kompetenzen (LK)", 1)
    d.add_paragraph(s["lk_hinweis"])
    tabelle(d, ["Nr.", "Lernfeld-Kompetenz (nah am Lehrplan)", "Phase", "AFB", "Kompetenz"], s["lk"], [1.5, 9.5, 2.4, 1.3, 2.3], groesse=9)
    tabelle(d, ["Kürzel", "Bedeutung"], s["kuerzel_legende"], [2.5, 14.5], groesse=9)
    d.add_heading("Inhalte aus dem Lehrplantext", 1)
    for t in s["inhalte_lehrplan"]: d.add_paragraph(t, style="List Bullet")
    d.add_heading("Inhaltskatalog (Konkretisierung durch die Lehrkraft)", 1)
    d.add_paragraph(s["inhaltskatalog"]["hinweis"])
    d.add_heading("Pflicht (Fundamentum)", 2)
    tabelle(d, ["Bereich", "Inhalte"], s["inhaltskatalog"]["pflicht"], [4.0, 13.0], groesse=9)
    for teil, ueber in (("optional", "Optional (Additum, Präferenz der Lehrkraft)"), ("verschoben", "Verschoben")):
        if s["inhaltskatalog"].get(teil):
            d.add_heading(ueber, 2)
            for t in s["inhaltskatalog"][teil]: d.add_paragraph(t, style="List Bullet")
    d.add_heading("Abgrenzung zu Nachbar-Lernfeldern", 1)
    tabelle(d, ["Lernfeld", "Gehört dorthin, nicht in dieses Lernfeld"], s["abgrenzung"], [5.0, 12.0], groesse=9)
    d.add_heading("Querschnittsthemen", 1)
    d.add_paragraph(s["querschnitt"])
    d.add_heading("Lernort Betrieb (Liste der Entsprechungen)", 1)
    tabelle(d, ["ARP-Abschnitt", "Position (gekürzt)"], s["lernort"], [5.0, 12.0], groesse=9)
    d.add_heading("Prüfbericht", 1)
    tabelle(d, ["Stufe", "Befund"], eigene + s["pruefbericht"], [2.6, 14.4], faerben=lambda z: STUFE[z[0]])
    ziel = ab / s["ordner"] / "Curriculare_Analyse.docx"; ziel.parent.mkdir(parents=True, exist_ok=True); d.save(ziel)
    rel = str(ziel.relative_to(ab)); sbp = ab / ".daten" / "akten" / (rel + ".json"); sbp.parent.mkdir(parents=True, exist_ok=True)
    alt = json.loads(sbp.read_text(encoding="utf-8")) if sbp.exists() else s.get("steckbrief_vorher", {})
    sb = {"art": "lernfeld", "titel": s["kurztitel"], "pfad": rel, "stand": alt.get("stand", "entwurf"),
          "freigegeben_am": alt.get("freigegeben_am"), "zuletzt_bearbeitet": dt.datetime.now().strftime("%Y-%m-%dT%H:%M"),
          "baut_auf": s.get("baut_auf", []), "fach": s["fach"], "notiz": "Schritt 01"}
    sbmod.schreiben(ab, rel, sb["art"], sb["titel"], sb["baut_auf"], sb["fach"], sb["notiz"], s, vorher=s.get("steckbrief_vorher"))
    return ziel, eigene


if __name__ == "__main__":
    z, b = erzeugen(sys.argv[1], sys.argv[2]); print(z); [print(*x) for x in b]
