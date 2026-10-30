"""Planungsmappe: fasst die Akten einer Planung zu einem DOCX zusammen (zum Zeigen, etwa im Gespräch mit der Schule).

    python mappe/planungsmappe.py <arbeitsbereich> <kurzname>

Daten:    <arbeitsbereich>/.daten/mappe/<kurzname>.json mit Titel, Einführung (Absätze), Übersichtstabellen
          und der Liste der Dokumente (Pfade im Arbeitsbereich, DOCX oder Markdown).
Ergebnis: <ziel> (DOCX) und Steckbrief. Jedes Dokument beginnt auf einer neuen Seite und behält sein
Format (hoch oder quer); mit "format" lässt sich ein Dokument quer oder hoch setzen (ein Wechsel von quer
zurück nach hoch wird in manchen Programmen eine Seite zu früh angezeigt). Markdown-Akten werden als einfache Word-Abschnitte übernommen.
Prüft selbst: alle Dokumente vorhanden, Stand jedes Dokuments laut Steckbrief (nur freigegebene
ohne Hinweis)."""
import copy, datetime as dt, json, pathlib, re, sys
from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docxcompose.composer import Composer

sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "lernsituation"))
from ls_ausarbeitung import schatten, tabelle
sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "akten"))
import steckbrief as sbmod


def stil(d):
    st = d.styles["Normal"]; st.font.name = "Arial"; st.font.size = Pt(11); st.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    for n in ("Title", "Heading 1", "Heading 2"):
        h = d.styles[n]; h.font.name = "Arial"; h.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)


def seite(sec, quer):
    if quer:
        sec.orientation = WD_ORIENT.LANDSCAPE; sec.page_width, sec.page_height = Cm(29.7), Cm(21)
    else:
        sec.orientation = WD_ORIENT.PORTRAIT; sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    for x in ("left_margin", "right_margin", "top_margin", "bottom_margin"): setattr(sec, x, Cm(2.0))


def aus_markdown(pfad):
    """Einfache Umsetzung einer Markdown-Akte (Überschriften, Tabellen, Listen, Absätze) in ein DOCX."""
    d = Document(); stil(d); seite(d.sections[0], False)
    zeilen = pfad.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(zeilen):
        z = zeilen[i].rstrip()
        if z.startswith(">"):
            i += 1; continue
        if z.startswith("|"):
            block = []
            while i < len(zeilen) and zeilen[i].startswith("|"):
                block.append([c.strip().replace("**", "") for c in zeilen[i].strip().strip("|").split("|")]); i += 1
            block = [b for b in block if not re.fullmatch(r"[-: ]+", "".join(b))]
            n = len(block[0]); breite = 17.0 / n
            tabelle(d, block[0], block[1:], [breite] * n, groesse=8.5)
            continue
        if z.startswith("#"):
            stufe = len(z) - len(z.lstrip("#"))
            d.add_heading(z.lstrip("#").strip(), 0 if stufe == 1 else min(stufe - 1, 2))
        elif z.startswith("- "):
            d.add_paragraph(z[2:].replace("**", ""), style="List Bullet")
        elif z.strip():
            text = z.replace("**", "")
            while i + 1 < len(zeilen) and zeilen[i + 1].strip() and not zeilen[i + 1].startswith(("#", "|", "- ", ">")):
                i += 1; text += " " + zeilen[i].strip().replace("**", "")
            d.add_paragraph(text)
        i += 1
    return d


def stand(ab, rel):
    p = ab / ".daten" / "akten" / (rel + ".json")
    if not p.exists():
        return "ohne Steckbrief"
    s = json.loads(p.read_text(encoding="utf-8"))
    return s["stand"] + (f" am {s['freigegeben_am'][:10]}" if s.get("freigegeben_am") else "")


def erzeugen(ab, kurz):
    ab = pathlib.Path(ab)
    m = json.loads((ab / ".daten" / "mappe" / f"{kurz}.json").read_text(encoding="utf-8"))
    befunde = []
    d = Document(); stil(d); seite(d.sections[0], False)
    t = d.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for _ in range(4): d.add_paragraph()
    r = d.add_paragraph().add_run(m["titel"]); r.bold = True; r.font.size = Pt(24); r.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)
    r = d.add_paragraph().add_run(m["untertitel"]); r.font.size = Pt(14)
    d.add_paragraph()
    for z in m["deckblatt"]:
        d.add_paragraph(z)
    d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    for abschnitt in m["einfuehrung"]:
        d.add_heading(abschnitt["ueberschrift"], 1)
        for a in abschnitt.get("absaetze", []):
            p = d.add_paragraph(a); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        if abschnitt.get("tabelle"):
            tb = abschnitt["tabelle"]
            tabelle(d, tb["kopf"], tb["zeilen"], tb["breiten"], groesse=9)
    d.add_heading("Inhalt der Mappe", 1)
    zeilen = []
    for n, x in enumerate(m["dokumente"], 1):
        pfad = ab / x["pfad"]
        if not pfad.exists():
            befunde.append(["Fehler", f"Dokument fehlt: {x['pfad']}"]); continue
        st = stand(ab, x["pfad"])
        if not st.startswith("freigegeben"):
            befunde.append(["Hinweis", f"{x['titel']}: Stand {st}"])
        zeilen.append([str(n), x["schritt"], x["titel"], st])
    tabelle(d, ["Teil", "Schritt", "Dokument", "Stand"], zeilen, [1.2, 2.3, 9.5, 4.0], groesse=9)
    if m.get("ki_hinweis"):
        p = d.add_paragraph(); p.add_run("Hinweis zur KI-Unterstützung: ").bold = True; p.add_run(m["ki_hinweis"])
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    # Jedes Dokument wird mit einem eigenen Abschnittsende angehängt, damit es sein Format (hoch oder quer)
    # behält; das letzte bestimmt das Format des Schlussabschnitts.
    d.add_section(WD_SECTION.NEW_PAGE)
    c = Composer(d)
    vorhanden = [x for x in m["dokumente"] if (ab / x["pfad"]).exists()]
    for k, x in enumerate(vorhanden):
        pfad = ab / x["pfad"]
        teil = aus_markdown(pfad) if pfad.suffix == ".md" else Document(pfad)
        if x.get("format") in ("quer", "hoch"):
            for sec in teil.sections: seite(sec, x["format"] == "quer")
        quer = teil.sections[-1].orientation == WD_ORIENT.LANDSCAPE
        if k < len(vorhanden) - 1:
            teil.add_section(WD_SECTION.NEW_PAGE)
        c.append(teil)
        if k == len(vorhanden) - 1:
            seite(c.doc.sections[-1], quer)
    ziel = ab / m["ziel"]; ziel.parent.mkdir(parents=True, exist_ok=True); c.save(ziel)
    rel = str(ziel.relative_to(ab)); sbp = ab / ".daten" / "akten" / (rel + ".json"); sbp.parent.mkdir(parents=True, exist_ok=True)
    alt = json.loads(sbp.read_text(encoding="utf-8")) if sbp.exists() else {}
    sb = {"art": m.get("art", "lernfeld"), "titel": m["titel"], "pfad": rel, "stand": alt.get("stand", "entwurf"),
          "freigegeben_am": alt.get("freigegeben_am"), "zuletzt_bearbeitet": dt.datetime.now().strftime("%Y-%m-%dT%H:%M"),
          "baut_auf": [x["pfad"] for x in m["dokumente"]], "fach": m["fach"], "notiz": "Planungsmappe (Zusammenstellung)"}
    sbmod.schreiben(ab, rel, sb["art"], sb["titel"], sb["baut_auf"], sb["fach"], sb["notiz"], m)
    return ziel, befunde


if __name__ == "__main__":
    z, b = erzeugen(sys.argv[1], sys.argv[2]); print(z); [print(*x) for x in b]
