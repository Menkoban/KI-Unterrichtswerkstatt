"""Schritt 06: Lernausgangslage und Fehlvorstellungen einer Lernsituation aus Daten im Arbeitsbereich.

    python lernsituation/fehlvorstellungen.py <arbeitsbereich> <kurzname>

Daten:    <arbeitsbereich>/.daten/fehlvorstellungen/<kurzname>.json; die Lernsituation steht in
          .daten/lernsituation/<ls>.json (Feld "ls").
Ergebnis: <ordner der LS>/Fehlvorstellungen.docx und Steckbrief. Prüft selbst: Herkunft aus der
erlaubten Liste, Forschung mit Literatur, KI-Vermutungen bestätigt, Doppelstunden gibt es in der
Lernsituation, A- und B-Einträge mit Aufdecken und Aufgreifen, nicht zu viele A-Einträge,
Lernausgangslage nur mit Quelle (sonst „unbekannt“). Eine KI-Vermutung braucht einen Bezug
(verwandte Theorie, Fach- oder Praxisquelle); reine KI-Vermutungen ohne Bezug werden nicht
aufgenommen (Lehrkraft 2026-10-11)."""
import datetime as dt, json, pathlib, sys
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from ls_ausarbeitung import STUFE, tabelle
sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "akten"))
import steckbrief as sbmod

HERKUNFT = ["Forschung", "Erfahrung der Lehrkraft", "eigene Beobachtung", "KI-Vermutung"]
PRIO = {"A": "im Unterricht gezielt aufgreifen (Vorhersagen – Prüfen – Erklären)",
        "B": "über Diagnose-Item und Hilfekarte abfangen", "C": "nur im Blick behalten"}


def pruefen(f, ls):
    b, ds = [], {x["ds"] for x in ls["doppelstunden"]}
    offen = []
    for x in f["fv"]:
        h = x["herkunft"]
        if h["art"] not in HERKUNFT:
            b.append(["Fehler", f"{x['nr']}: Herkunft „{h['art']}“ nicht erlaubt ({', '.join(HERKUNFT)})"])
        if h["art"] == "Forschung" and not h.get("literatur"):
            b.append(["Warnung", f"{x['nr']}: Herkunft Forschung ohne Literaturangabe"])
        if h["art"] == "KI-Vermutung" and not h.get("bezug"):
            b.append(["Fehler", f"{x['nr']}: reine KI-Vermutung ohne Bezug; wird nicht aufgenommen (Lehrkraft 2026-10-11)"])
        if h["art"] == "KI-Vermutung" and not x.get("bestaetigt"):
            offen.append(x["nr"])
        if x["prio"] not in PRIO:
            b.append(["Fehler", f"{x['nr']}: Priorität {x['prio']} unbekannt"])
        if x["prio"] in "AB" and not (x.get("aufdecken") and x.get("aufgreifen")):
            b.append(["Fehler", f"{x['nr']}: Priorität {x['prio']} ohne Aufdecken oder Aufgreifen"])
        falsch = [d for d in x["ds"] if d not in ds]
        if falsch:
            b.append(["Fehler", f"{x['nr']}: DS {', '.join(falsch)} gibt es in LS {ls['nr']} nicht"])
    if offen:
        b.append(["Warnung", "KI-Vermutungen noch nicht bestätigt: " + ", ".join(offen)
                  + ". Sie gehen erst nach Bestätigung durch die Lehrkraft in einen Entwurf."])
    a = sum(x["prio"] == "A" for x in f["fv"])
    if a > max(2, len(ds) // 2 + 1):
        b.append(["Warnung", f"{a} Einträge mit Priorität A bei {len(ds)} Doppelstunden; zu viele zum aktiven Aufgreifen"])
    for z in f["lernausgangslage"]:
        if z["stand"] != "unbekannt" and not z.get("quelle"):
            b.append(["Fehler", f"Lernausgangslage „{z['inhalt']}“: Einschätzung ohne Quelle (sonst „unbekannt“)"])
    return b


def erzeugen(ab, kurz):
    ab = pathlib.Path(ab)
    f = json.loads((ab / ".daten" / "fehlvorstellungen" / f"{kurz}.json").read_text(encoding="utf-8"))
    ls = json.loads((ab / ".daten" / "lernsituation" / f"{f['ls']}.json").read_text(encoding="utf-8"))
    eigene = pruefen(f, ls)
    d = Document()
    sec = d.sections[0]; sec.orientation = WD_ORIENT.LANDSCAPE; sec.page_width, sec.page_height = Cm(29.7), Cm(21)
    for x in ("left_margin", "right_margin", "top_margin", "bottom_margin"): setattr(sec, x, Cm(1.8))
    st = d.styles["Normal"]; st.font.name = "Arial"; st.font.size = Pt(10.5); st.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    for n in ("Title", "Heading 1", "Heading 2"):
        h = d.styles[n]; h.font.name = "Arial"; h.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)
    d.add_heading(f"LS {ls['nr']}: Lernausgangslage und Fehlvorstellungen", 0)
    p = d.add_paragraph(f"Lernsituations-Akte · Schritt 06 · {ls['lernfeld']} · LS {ls['nr']} „{ls['titel']}“ · "
                        f"Stand {f['datum']} · {f['stand']}")
    p.runs[0].italic = True
    d.add_heading("Worum es geht", 1)
    for t in f["einleitung"]: d.add_paragraph(t)
    tabelle(d, ["Herkunft", "Bedeutung"], [[h, t] for h, t in f.get("herkunft_legende", [
        ["Forschung", "in der fachdidaktischen Literatur beschrieben, mit Literaturangabe"],
        ["Erfahrung der Lehrkraft", "aus eigener Unterrichtserfahrung"],
        ["eigene Beobachtung", "aus Nachbereitungen, mit Datum und Klasse"],
        ["KI-Vermutung", "plausibel, aber unbelegt; muss von der Lehrkraft bestätigt werden"]])], [5.2, 20.9])
    tabelle(d, ["Priorität", "Bedeutung"], [[k, v] for k, v in PRIO.items()], [5.2, 20.9])
    d.add_heading("Lernausgangslage je Inhalt", 1)
    d.add_paragraph(f["lernausgangslage_text"])
    tabelle(d, ["Inhalt", "Stand", "Quelle", "Diagnose (Moodle)"],
            [[z["inhalt"], z["stand"], z.get("quelle") or "–", z["diagnose"]] for z in f["lernausgangslage"]],
            [7.0, 3.0, 5.0, 11.1], groesse=9)
    d.add_heading("Übersicht der Fehlvorstellungen", 1)
    tabelle(d, ["Nr.", "Fehlvorstellung", "Herkunft", "DS", "Prio"],
            [[x["nr"], x["name"], x["herkunft"]["art"] + ("" if x["herkunft"]["art"] != "KI-Vermutung" else
              (", bestätigt" if x.get("bestaetigt") else ", zu bestätigen")), ", ".join(x["ds"]), x["prio"]] for x in f["fv"]],
            [1.6, 13.5, 5.5, 3.0, 2.5], groesse=9)
    d.add_heading("Die Fehlvorstellungen im Einzelnen", 1)
    for x in f["fv"]:
        d.add_heading(f"{x['nr']} · {x['name']}", 2)
        h = x["herkunft"]
        herk = h["art"] + (f": {h['literatur']}" if h.get("literatur") else "") + (f"; Bezug: {h['bezug']}" if h.get("bezug") else "") \
            + (f" ({h['notiz']})" if h.get("notiz") else "")
        tabelle(d, None, [["Typische Äußerung", x["aeusserung"]], ["Worum es geht", x["kern"]], ["Herkunft", herk],
                          ["Wo in der LS", f"DS {', '.join(x['ds'])} · Priorität {x['prio']}"],
                          ["Aufdecken (Moodle-Quiz)", x.get("aufdecken", "–")], ["Aufgreifen", x.get("aufgreifen", "–")]],
                [5.2, 20.9], groesse=9.5)
    if f.get("nicht_aufgenommen"):
        d.add_heading("Bewusst nicht aufgenommen", 1)
        for t in f["nicht_aufgenommen"]: d.add_paragraph(t, style="List Bullet")
    if f.get("literatur"):
        d.add_heading("Literatur", 1)
        for t in f["literatur"]: d.add_paragraph(t)
    d.add_heading("Prüfbericht", 1)
    tabelle(d, ["Stufe", "Befund"], eigene + f["pruefbericht"], [2.6, 23.5], faerben=lambda z: STUFE[z[0]])
    ziel = ab / ls["ordner"] / "Fehlvorstellungen.docx"; ziel.parent.mkdir(parents=True, exist_ok=True); d.save(ziel)
    rel = str(ziel.relative_to(ab)); sbp = ab / ".daten" / "akten" / (rel + ".json"); sbp.parent.mkdir(parents=True, exist_ok=True)
    alt = json.loads(sbp.read_text(encoding="utf-8")) if sbp.exists() else {}
    sb = {"art": "lernsituation", "titel": f"LS {ls['nr']} Fehlvorstellungen", "pfad": rel, "stand": alt.get("stand", "entwurf"),
          "freigegeben_am": alt.get("freigegeben_am"), "zuletzt_bearbeitet": dt.datetime.now().strftime("%Y-%m-%dT%H:%M"),
          "baut_auf": [ls["ordner"] + "/Lernsituation.docx"], "fach": ls["fach"], "notiz": "Schritt 06"}
    sbmod.schreiben(ab, rel, sb["art"], sb["titel"], sb["baut_auf"], sb["fach"], sb["notiz"], f)
    return ziel, eigene


if __name__ == "__main__":
    z, b = erzeugen(sys.argv[1], sys.argv[2]); print(z); [print(*x) for x in b]
