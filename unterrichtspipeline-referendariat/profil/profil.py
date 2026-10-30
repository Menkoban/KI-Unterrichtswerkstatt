"""Lehrkraft-Profil: Vorlage (Werkzeug) + persönliche Werte (Arbeitsbereich).

    python profil/profil.py <arbeitsbereich>            # prüfen und Lehrkraft-Profil.docx erzeugen
    python profil/profil.py <arbeitsbereich> --pruefen  # nur prüfen

Skills lesen das Profil nur über lade(); persönliche Werte gewinnen gegen den Standard.
"""
import json, sys, pathlib

VORLAGE = pathlib.Path(__file__).with_name("vorlage.json")
WERTE = pathlib.Path("Profil") / "lehrkraft-profil.json"
TYPEN = {"ja_nein": bool, "zahl": (int, float), "text": str, "liste": list, "auswahl": str}


def vorlage():
    return json.loads(VORLAGE.read_text(encoding="utf-8"))["einstellungen"]


def pruefen(werte):
    """Gibt eine Liste von Befunden zurück (leer = in Ordnung)."""
    v = {e["id"]: e for e in vorlage()}
    befunde = []
    for k, w in werte.get("werte", {}).items():
        if k not in v:
            befunde.append(f"Fehler: unbekannte Einstellung '{k}' (Tippfehler oder fehlt in der Vorlage)")
            continue
        e = v[k]
        if not isinstance(w, TYPEN[e["typ"]]) or (e["typ"] == "zahl" and isinstance(w, bool)):
            befunde.append(f"Fehler: '{k}' erwartet {e['typ']}, steht aber {w!r}")
        elif e["typ"] == "auswahl" and w not in e["optionen"]:
            befunde.append(f"Fehler: '{k}' = {w!r} ist keine der Optionen {e['optionen']}")
    for k in werte.get("herkunft", {}):
        if k not in werte.get("werte", {}):
            befunde.append(f"Hinweis: Herkunft für '{k}' ohne Wert")
    return befunde


def lade(arbeitsbereich):
    """Zusammengeführtes Profil {id: wert}; bricht bei Fehlern ab."""
    pfad = pathlib.Path(arbeitsbereich) / WERTE
    werte = json.loads(pfad.read_text(encoding="utf-8")) if pfad.exists() else {"werte": {}}
    fehler = [b for b in pruefen(werte) if b.startswith("Fehler")]
    if fehler:
        raise ValueError("Profil fehlerhaft:\n" + "\n".join(fehler))
    profil = {e["id"]: e["standard"] for e in vorlage()}
    profil.update(werte["werte"])
    return profil


def docx(arbeitsbereich):
    from docx import Document
    from docx.shared import Pt, Cm, RGBColor
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    ab = pathlib.Path(arbeitsbereich)
    werte = json.loads((ab / WERTE).read_text(encoding="utf-8"))
    profil = lade(ab)

    def schatten(c, f):
        p = c._tc.get_or_add_tcPr(); s = OxmlElement("w:shd")
        s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), f); p.append(s)

    def zeigen(w):
        if isinstance(w, bool): return "ja" if w else "nein"
        if isinstance(w, list): return ", ".join(map(str, w)) or "(leer)"
        return str(w).replace("_", " ").replace("fuer", "für").replace("fuehr", "führ") if w != "" else "(leer)"

    d = Document()
    s = d.sections[0]; s.page_width, s.page_height = Cm(21), Cm(29.7)
    for m in ("left_margin", "right_margin", "top_margin", "bottom_margin"): setattr(s, m, Cm(2))
    st = d.styles["Normal"]; st.font.name = "Arial"; st.font.size = Pt(10)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    d.add_heading("Lehrkraft-Profil", 0)
    p = d.add_paragraph("Automatisch erzeugt aus Profil/lehrkraft-profil.json und der Profil-Vorlage des Werkzeugs. "
                        "Nicht von Hand bearbeiten; Änderungen über Claude oder die Nachbereitung. "
                        "Grau hinterlegt: eigener Wert weicht vom Standard ab.")
    p.runs[0].italic = True
    gruppen = []
    for e in vorlage():
        if e["gruppe"] not in gruppen: gruppen.append(e["gruppe"])
    for g in gruppen:
        d.add_heading(g, 1)
        t = d.add_table(rows=1, cols=4); t.style = "Table Grid"
        for c, k in zip(t.rows[0].cells, ("Einstellung", "Dein Wert", "Standard", "Herkunft")):
            c.text = ""; c.paragraphs[0].add_run(k).bold = True; schatten(c, "D9E2F3")
        for e in (x for x in vorlage() if x["gruppe"] == g):
            r = t.add_row().cells
            r[0].text = ""; r[0].paragraphs[0].add_run(e["titel"]).bold = True
            if e["erklaerung"]:
                q = r[0].add_paragraph(e["erklaerung"]); q.runs[0].font.size = Pt(8.5)
                q.runs[0].font.color.rgb = RGBColor(0x55, 0x5F, 0x70)
            r[1].text = zeigen(profil[e["id"]]); r[2].text = zeigen(e["standard"])
            r[3].text = werte.get("herkunft", {}).get(e["id"], "")
            if e["id"] in werte["werte"] and werte["werte"][e["id"]] != e["standard"]:
                schatten(r[1], "EDEDED")
        t.autofit = False
        for i, b in enumerate((5.6, 4.2, 3.2, 4.0)):
            t.columns[i].width = Cm(b)
            for c in t.columns[i].cells: c.width = Cm(b)
    ziel = ab / "Profil" / "Lehrkraft-Profil.docx"
    d.save(ziel)
    return ziel


if __name__ == "__main__":
    ab = pathlib.Path(sys.argv[1])
    werte = json.loads((ab / WERTE).read_text(encoding="utf-8"))
    befunde = pruefen(werte)
    for b in befunde: print(b)
    if any(b.startswith("Fehler") for b in befunde): sys.exit(1)
    if "--pruefen" not in sys.argv: print(docx(ab))
    print("Profil in Ordnung:", len(werte["werte"]), "eigene Werte")
