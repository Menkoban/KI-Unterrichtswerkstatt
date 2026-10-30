"""Schritt 03 Jahresplanung: erzeugt die Schuljahres-Akte als DOCX aus den Planungsdaten.

    python jahresplanung/jahresplanung.py <arbeitsbereich> <name>      # z. B. 2026-27_EG1

Planungsdaten: <arbeitsbereich>/.daten/jahresplanung/<name>.json
Ergebnis:      <arbeitsbereich>/Unterricht/<fach>/<name>/Jahresplanung.docx und Steckbrief.
"""
import datetime as dt, json, pathlib, sys
from collections import Counter
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import kalender as K
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "akten"))
import steckbrief as sbmod

HIER = pathlib.Path(__file__).parent
WT = ["Mo", "Di", "Mi", "Do", "Fr"]


def schatten(c, f):
    p = c._tc.get_or_add_tcPr(); s = OxmlElement("w:shd")
    s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), f); p.append(s)


def tabelle(d, kopf, zeilen, breiten, groesse=9, kopffarbe="D9E2F3", faerben=None):
    t = d.add_table(rows=1, cols=len(kopf)); t.style = "Table Grid"; t.autofit = False
    for c, k in zip(t.rows[0].cells, kopf):
        c.text = ""; r = c.paragraphs[0].add_run(k); r.bold = True; r.font.size = Pt(groesse); schatten(c, kopffarbe)
    for z in zeilen:
        cs = t.add_row().cells
        for i, v in enumerate(z):
            cs[i].text = ""; r = cs[i].paragraphs[0].add_run(str(v)); r.font.size = Pt(groesse)
        if faerben:
            f = faerben(z)
            if f:
                for c in cs: schatten(c, f)
    for i, b in enumerate(breiten):
        t.columns[i].width = Cm(b)
        for c in t.columns[i].cells: c.width = Cm(b)
    d.add_paragraph()
    return t


def datum(d):
    return d.strftime("%d.%m.%Y")


def erzeugen(ab, name):
    ab = pathlib.Path(ab)
    p = json.loads((ab / ".daten" / "jahresplanung" / f"{name}.json").read_text(encoding="utf-8"))
    k = K.laden(HIER / p["kalender"])
    w = K.wochen(k)
    je_tag = Counter(dd.weekday() for x in w for dd in x["schultage"])
    min_tage = min(je_tag.values())

    d = Document()
    s = d.sections[0]; s.page_width, s.page_height = Cm(21), Cm(29.7)
    for m in ("left_margin", "right_margin", "top_margin", "bottom_margin"): setattr(s, m, Cm(2))
    st = d.styles["Normal"]; st.font.name = "Arial"; st.font.size = Pt(10.5)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    for n in ("Title", "Heading 1", "Heading 2"):
        h = d.styles[n]; h.font.name = "Arial"; h.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)
    d.add_heading(f"Jahresplanung {p['schuljahr']}", 0)
    q = d.add_paragraph(); r = q.add_run(f"Schuljahres-Akte · Stand: {p['stand']} · {p['datum']}"); r.italic = True

    d.add_heading("1 Eckdaten", 1)
    tabelle(d, ["Merkmal", "Angabe"], [
        ["Klasse", p["klasse"]], ["Bildungsgang", p["bildungsgang"]], ["Ausbildungsjahr", p["ausbildungsjahr"]],
        ["Organisationsform", p["organisationsform"]], ["Berufsschultage", p["berufsschultage"]],
        ["Schuljahr", f"{datum(k['_start'])} bis {datum(k['_ende'])}"],
        ["Rahmenlehrplan", p["rahmenlehrplan"]], ["Schulplanung", p["schulplanung"]],
    ], [4.5, 12.5], groesse=10)

    d.add_heading("2 Kalender", 1)
    q = d.add_paragraph(f"Quelle der Ferien: {k['quelle']}, abgerufen {k['abgerufen']}. Gesetzliche Feiertage nach dem "
                        "Niedersächsischen Feiertagsgesetz berechnet.")
    q.runs[0].font.size = Pt(9)
    zeilen = [[n, datum(a), datum(b)] for n, a, b in k["_ferien"]]
    zeilen += [[f"{n} (Feiertag)", datum(dd), ""] for dd, n in sorted(k["_feiertage"].items()) if dd.weekday() < 5
               and not any(a <= dd <= b for _, a, b in k["_ferien"])]
    tabelle(d, ["Ferien und unterrichtsfreie Tage", "von", "bis"], zeilen, [9, 4, 4])
    voll = sum(1 for x in w if len(x["schultage"]) == 5); teil = sum(1 for x in w if 0 < len(x["schultage"]) < 5)
    d.add_paragraph(f"Unterrichtswochen: {voll} volle und {teil} angebrochene Wochen. Schultage je Wochentag: "
                    + ", ".join(f"{WT[i]} {je_tag[i]}" for i in range(5))
                    + f". Wer einen festen Wochentag hat, kommt also auf {min(je_tag.values())} bis {max(je_tag.values())} Termine im Jahr.")

    d.add_heading("3 Lernfelder des Schuljahres", 1)
    sp = p.get("stundenplan")  # {"lf_std_woche": {"1": 2, ...}, "wochentage": {"1": ["Mo"]}}, erst wenn bekannt
    zeilen = [[f"LF {lf['nr']}", lf["titel"], lf["zeitrichtwert"], lf["lehrkraft"]] for lf in p["lernfelder"]]
    tabelle(d, ["LF", "Titel", "Zeitrichtwert (Std.)", "unterrichtet"], zeilen, [1.2, 10.5, 2.6, 2.7],
            faerben=lambda z: "E3F4E8" if z[3] == "ich" else None)
    d.add_paragraph(f"Zusammen {sum(lf['zeitrichtwert'] for lf in p['lernfelder'])} Std. im Schuljahr. Grün: Lernfelder, "
                    "die du selbst unterrichtest. Sie werden auf der Ebene des Lernfelds chronologisch durchgeplant "
                    "(Lernsituationen, dann Unterrichtseinheiten). Die übrigen bleiben Blöcke mit Zeitrichtwert.")

    d.add_heading("4 Zeitlicher Ablauf", 1)
    for lf in (x for x in p["lernfelder"] if x["lehrkraft"] == "ich"):
        d.add_paragraph(f"LF {lf['nr']}: {lf['zeitrichtwert']} Std., chronologisch geplant von Stunde 1 bis "
                        f"{lf['zeitrichtwert']}. Reihenfolge und Umfang der Lernsituationen legt die Lernfeld-Akte fest.",
                        style="List Bullet")
    if not sp:
        d.add_paragraph("Zuordnung zu Kalenderwochen und Wochentagen: folgt, sobald der Stundenplan bekannt ist "
                        "(Stunden je Lernfeld und Woche, Wochentage). Dann rechnet die Pipeline aus dem Kalender, "
                        "wann welche Stunde liegt und ob die Zeitrichtwerte in die verfügbaren Termine passen.")
    else:
        d.add_paragraph(f"Stundenplan: {sp.get('quelle', 'Angabe der Lehrkraft')}. Zuordnung der Stunden zu den Terminen:")
        tag_nr = {t: i for i, t in enumerate(WT)}
        for lf in (x for x in p["lernfelder"] if x["lehrkraft"] == "ich"):
            plan = sp["lernfelder"][str(lf["nr"])]          # [{"tag": "Mo", "std": 2}, ...] oder {"std_woche": 8} (Tage offen)
            if isinstance(plan, dict):                       # epochal/wochenweise, Wochentage noch offen
                gesamt, zeilen = 0, []
                for x in w:
                    if gesamt >= lf["zeitrichtwert"] or not x["schultage"]:
                        if x["schultage"] == [] and 0 < gesamt < lf["zeitrichtwert"]:
                            zeilen.append([x["kw"], datum(x["montag"]), "–", "; ".join(sorted({g for _, g in x["frei"]})) or "keine Schule", gesamt])
                        continue
                    if len(x["schultage"]) < 5:
                        grund = "; ".join(sorted({g for _, g in x["frei"]})) or ("erste Schulwoche" if gesamt == 0 else "letzte Schulwoche")
                        zeilen.append([x["kw"], datum(x["montag"]), "?", f"angebrochen ({grund}); zählt erst, wenn die Wochentage feststehen", gesamt])
                        continue
                    std = min(plan["std_woche"], lf["zeitrichtwert"] - gesamt); von = gesamt + 1; gesamt += std
                    zeilen.append([x["kw"], datum(x["montag"]), std, f"Std. {von}–{gesamt}", gesamt])
                letzte = next(z for z in reversed(zeilen) if isinstance(z[2], int))
                erste = next(z for z in zeilen if isinstance(z[2], int))
                d.add_heading(f"LF {lf['nr']}: epochal, {plan['std_woche']} Std. je Woche, Std. 1 bis {lf['zeitrichtwert']} "
                              f"von KW {erste[0]} (ab {erste[1]}) bis KW {letzte[0]} (Woche ab {letzte[1]})", 2)
                tabelle(d, ["KW", "Woche ab", "Std.", "Inhalt", "kumuliert"], zeilen, [1.2, 2.6, 1.2, 9.6, 2.2], groesse=8.5,
                        faerben=lambda z: "F2F2F2" if z[2] == "–" else ("FFF3E0" if z[2] == "?" else None))
                continue
            termine = []
            for x in w:
                for e in plan:
                    dd = next((t for t in x["schultage"] if t.weekday() == tag_nr[e["tag"]]), None)
                    if dd: termine.append((dd, e["std"]))
            gesamt, zeilen, bis = 0, [], 0
            for dd, std in sorted(termine):
                von = gesamt + 1; gesamt += std
                zeilen.append([x2 for x2 in (datum(dd), WT[dd.weekday()], f"Std. {von}–{gesamt}" if std > 1 else f"Std. {von}")])
            d.add_heading(f"LF {lf['nr']}: {gesamt} Std. verfügbar bei {lf['zeitrichtwert']} Std. Zeitrichtwert "
                          f"({gesamt - lf['zeitrichtwert']:+d})", 2)
            tabelle(d, ["Datum", "Tag", "Stunden"], zeilen, [4, 2, 4], groesse=8.5)

    d.add_heading("5 Querbezüge und Abweichungen", 1)
    for t in p["querbezuege"] + p["abweichungen"]:
        d.add_paragraph(t, style="List Bullet")

    d.add_heading("Prüfbericht", 1)
    farbe = {"Fehler": "F8CBAD", "Warnung": "FFE699", "Hinweis": "C6E0B4"}
    t = tabelle(d, ["Stufe", "Befund"], [[a, b] for a, b in p["pruefbericht"]], [2.6, 14.4], groesse=9.5,
                faerben=lambda z: farbe[z[0]])

    ziel = ab / "Unterricht" / p["fach"] / name / "Jahresplanung.docx"
    ziel.parent.mkdir(parents=True, exist_ok=True)
    d.save(ziel)
    rel = str(ziel.relative_to(ab))
    sb = {"art": "schuljahr", "titel": f"Jahresplanung {p['schuljahr']} {p.get('klasse_kurz', p['klasse'])}", "pfad": rel,
          "stand": "entwurf", "freigegeben_am": None, "zuletzt_bearbeitet": dt.datetime.now().strftime("%Y-%m-%dT%H:%M"),
          "baut_auf": [], "fach": p["fach"], "notiz": "Schritt 03; " + p["schulplanung"]}
    sbp = ab / ".daten" / "akten" / (rel + ".json"); sbp.parent.mkdir(parents=True, exist_ok=True)
    alt = json.loads(sbp.read_text(encoding="utf-8")) if sbp.exists() else {}
    if alt.get("stand") == "freigegeben":
        sb["stand"], sb["freigegeben_am"] = "freigegeben", alt["freigegeben_am"]
    sbmod.schreiben(ab, rel, sb["art"], sb["titel"], sb["baut_auf"], sb["fach"], sb["notiz"], p)
    return ziel


if __name__ == "__main__":
    print(erzeugen(sys.argv[1], sys.argv[2]))
