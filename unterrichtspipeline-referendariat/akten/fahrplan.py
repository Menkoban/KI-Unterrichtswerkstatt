"""Fahrplan der Personalisierung: aus <arbeitsbereich>/.daten/fahrplan.json eine DOCX für die Lehrkraft.

    python akten/fahrplan.py <arbeitsbereich>   ->  <arbeitsbereich>/Ref/Fahrplan_Personalisierung.docx

Der Fahrplan listet Stufen und Punkte (Weg: planen, fragen, nachbereiten, Probelauf) mit dem, was sie abdecken, und
ihrem Stand. Er ist die Abhakliste bis zum Agent in the Loop (Lehrkraft 2026-10-24); die Werkbank zeigt ihn als Liste.
"""
import json
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor, Cm

ZEICHEN = {"erledigt": "●", "teilweise": "◐", "in Arbeit": "◐", "offen": "○"}


def zaehlen(f):
    punkte = [p for s in f["stufen"] for p in s["punkte"]]
    return sum(p["status"] == "erledigt" for p in punkte), len(punkte)


def breiten(t, cm):
    """Feste Spaltenbreiten (Word und LibreOffice lesen die Gitterspalten, nicht nur die Zellen)."""
    t.autofit = False
    for i, w in enumerate(cm):
        t.columns[i].width = Cm(w)
        for c in t.columns[i].cells:
            c.width = Cm(w)


def stunden(h):
    return ("%g" % h).replace(".", ",") + " h"


def main(ab):
    ab = Path(ab).resolve()
    f = json.loads((ab / ".daten" / "fahrplan.json").read_text(encoding="utf-8"))
    d = Document()
    for s in d.sections:
        s.left_margin = s.right_margin = Cm(2.2)
    st = d.styles["Normal"]
    st.font.name, st.font.size = "Arial", Pt(10.5)
    d.add_heading(f["titel"], 0)
    erl, ges = zaehlen(f)
    d.add_paragraph(f"{f['stand']} · {erl} von {ges} Punkten erledigt")
    d.add_paragraph(f["ziel"])
    if f.get("vorgehen"):
        d.add_heading("So gehen wir vor", 1)
        for i, g in enumerate(f["vorgehen"], 1):
            d.add_paragraph(g, style="List Number")
    d.add_heading("Grundsätze", 1)
    for g in f["grundsaetze"]:
        d.add_paragraph(g, style="List Bullet")
    d.add_paragraph("Fertig, wenn: " + f["fertig_wenn"])
    d.add_heading("Mögliche Bildungsgänge", 1)
    t = d.add_table(rows=1, cols=3)
    t.style = "Light Grid Accent 1"
    for i, k in enumerate(("Bildungsgang", "Fach", "Stand")):
        t.rows[0].cells[i].text = k
    for k in f["kandidaten"]:
        z = t.add_row().cells
        z[0].text, z[1].text, z[2].text = k["bildungsgang"], k["faecher"], k["sicherheit"]
    breiten(t, (7.6, 5.8, 3.2))
    offen = lambda s: sum(p.get("dauer_h", 0) for p in s["punkte"] if p["status"] != "erledigt")
    gesamt = sum(offen(s) for s in f["stufen"])
    if gesamt:
        d.add_heading("Wie lange es dauert", 1)
        t = d.add_table(rows=1, cols=3)
        t.style = "Light Grid Accent 1"
        for i, k in enumerate(("Stufe", "Punkte", "Ihre Zeit (Schätzung)")):
            t.rows[0].cells[i].text = k
        for s in f["stufen"]:
            z = t.add_row().cells
            z[0].text, z[1].text, z[2].text = f"{s['nr']} {s['titel']}", str(len(s["punkte"])), stunden(offen(s))
        z = t.add_row().cells
        z[0].text, z[1].text, z[2].text = "Gesamt", str(ges), stunden(gesamt)
        breiten(t, (10.6, 2.2, 3.8))
        for c in z:
            for r in c.paragraphs[0].runs:
                r.bold = True
        d.add_paragraph(f"Bei 5 Stunden pro Woche sind das etwa {round(gesamt / 5)} Wochen, bei 10 Stunden pro Woche etwa "
                        f"{round(gesamt / 10)} Wochen. Schulferien und Stunden, die ohnehin für den Unterricht geplant werden "
                        "müssen, verkürzen den Weg: Jede echte Stunde zählt als Stichprobe.")
        if f.get("dauer_hinweis"):
            d.add_paragraph(f["dauer_hinweis"]).runs[0].italic = True
    for s in f["stufen"]:
        d.add_heading(f"Stufe {s['nr']}: {s['titel']}", 1)
        d.add_paragraph(s["warum"]).runs[0].italic = True
        t = d.add_table(rows=1, cols=5)
        t.style = "Light Grid Accent 1"
        for i, k in enumerate(("Nr.", "Punkt", "Weg", "Zeit", "Stand")):
            t.rows[0].cells[i].text = k
        for p in s["punkte"]:
            z = t.add_row().cells
            z[0].text = p["id"]
            z[1].text = p["titel"] + ("\nDeckt ab: " + ", ".join(p["deckt"]) if p.get("deckt") else "") + (
                "\n" + p["hinweis"] if p.get("hinweis") else "")
            z[2].text = p["weg"]
            z[3].text = stunden(p.get("dauer_h", 0)) if p["status"] != "erledigt" else "–"
            z[4].text = f"{ZEICHEN.get(p['status'], '○')} {p['status']}"
        breiten(t, (1.4, 9.1, 2.2, 1.5, 2.4))
    fuss = d.add_paragraph("KI-gestützt erstellt; Inhalt mit der Lehrkraft abgestimmt.")
    fuss.runs[0].font.size, fuss.runs[0].font.color.rgb = Pt(8), RGBColor(0x66, 0x66, 0x66)
    fuss.alignment = WD_ALIGN_PARAGRAPH.LEFT
    ziel = ab / "Ref" / "Fahrplan_Personalisierung.docx"
    ziel.parent.mkdir(exist_ok=True)
    d.save(ziel)
    print(ziel.relative_to(ab), f"{erl}/{ges} erledigt")
    return ziel


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
