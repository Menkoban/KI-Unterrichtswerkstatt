"""Schritte 05 und 06 (Klassenteil): Klassen-Akte aus Daten im Arbeitsbereich.

    python klasse/klassenakte.py <arbeitsbereich> <kurzname>

Daten:    <arbeitsbereich>/.daten/klasse/<kurzname>.json
Ergebnis: im Klassenordner Bedingungsfeld.docx (Gliederung nach Seminar-Leitfaden 1.1 bis 1.5 mit
Konsequenz je Bedingung und drei Personas), Lernausgangslage.docx (allgemeiner Teil je Bereich) und
Sitzplan.docx (kommentierter Sitzplan mit Bild aus dem Sitzplan-Studio, Anhang), je mit Steckbrief; dazu
Sitzplan.png.
Prüft selbst: nur Kürzel (S01 …), Anzahl = Zahl der Lernenden, Vorbildung und Niveaus summieren
sich auf die Anzahl, jede Bedingung mit Konsequenz, drei Personas mit vorhandenem Kürzel, jeder
Platz nur einmal belegt, Musterklasse als fiktiv gekennzeichnet, Lernausgangslage nur mit Quelle."""
import json, pathlib, re, sys
from collections import Counter
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "lernsituation"))
from ls_ausarbeitung import STUFE, schatten, tabelle
sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "akten"))
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import steckbrief as sbmod

NIVEAU_FARBE = {"Beginner": "D9EAD3", "Könner": "D6E4F5", "Experte": "E6DAF0"}


def pruefen(k):
    b = []
    ls = k["lernende"]
    for x in ls:
        if not re.fullmatch(r"S\d{2}", x["k"]):
            b.append(["Fehler", f"Kürzel {x['k']!r}: nur S01, S02 … (keine Namen)"])
    if k["daten"]["anzahl"] != len(ls):
        b.append(["Fehler", f"Anzahl {k['daten']['anzahl']}, aber {len(ls)} Lernende eingetragen"])
    vb = Counter(x["vorbildung"] for x in ls)
    if dict(vb) != {a: n for a, n in k["daten"]["vorbildung"].items() if n}:
        b.append(["Fehler", f"Vorbildung in den Daten {k['daten']['vorbildung']} passt nicht zu den Lernenden {dict(vb)}"])
    nv = Counter(x["niveau"] for x in ls)
    b.append(["Hinweis", "Niveaus: " + ", ".join(f"{n} {a}" for a, n in nv.items())])
    for a in k["abschnitte"]:
        for bed, kon in a["bedingungen"]:
            if not kon.strip():
                b.append(["Fehler", f"{a['nr']}: Bedingung ohne Konsequenz: {bed[:50]}"])
    kz = {x["k"] for x in ls}
    if len(k["personas"]) != 3:
        b.append(["Warnung", f"{len(k['personas'])} Personas (vorgesehen: drei)"])
    for p in k["personas"]:
        if p["k"] not in kz:
            b.append(["Fehler", f"Persona {p['name']}: Kürzel {p['k']} gibt es nicht"])
    plaetze = [tuple(x["platz"]) for x in ls]
    doppelt = [p for p, n in Counter(plaetze).items() if n > 1]
    if doppelt:
        b.append(["Fehler", f"Plätze doppelt belegt: {doppelt}"])
    r = k["raum"]
    for p in plaetze:
        if not (1 <= p[0] <= r["reihen"] and 1 <= p[1] <= r["plaetze_je_reihe"]):
            b.append(["Fehler", f"Platz {p} liegt außerhalb des Raums"])
    for x in ls:
        for art, n in x.get("noten", {}).items():
            if n not in ("1", "2", "3", "4", "5", "6") and not re.fullmatch(r"[1-6][+-]?|[1-5],[0-9]", str(n)):
                b.append(["Fehler", f"{x['k']}: Note {art} {n!r} ist keine Schulnote (1 bis 6)"])
    if k.get("musterklasse"):
        b.append(["Hinweis", "Musterklasse: alle Angaben sind fiktiv und dienen dem Probelauf; sie werden durch die echte Klasse ersetzt."])
    for z in k["lernausgangslage"]:
        if z["stand"] != "unbekannt" and not z.get("quelle"):
            b.append(["Fehler", f"Lernausgangslage „{z['bereich']}“ ohne Quelle"])
    return b


def neu(quer=False):
    d = Document(); sec = d.sections[0]
    if quer:
        sec.orientation = WD_ORIENT.LANDSCAPE; sec.page_width, sec.page_height = Cm(29.7), Cm(21)
    else:
        sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    for x in ("left_margin", "right_margin", "top_margin", "bottom_margin"): setattr(sec, x, Cm(2.0))
    st = d.styles["Normal"]; st.font.name = "Arial"; st.font.size = Pt(10.5); st.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    for n in ("Title", "Heading 1", "Heading 2"):
        h = d.styles[n]; h.font.name = "Arial"; h.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)
    return d


def kopf(d, k, titel, schritt):
    d.add_heading(f"{titel}: {k['klasse']}", 0)
    p = d.add_paragraph(f"Klassen-Akte · {schritt} · {k['bildungsgang']} · Schuljahr {k['schuljahr']} · Stand {k['datum']} · {k['stand']}")
    p.runs[0].italic = True
    if k.get("musterklasse"):
        p = d.add_paragraph(); r = p.add_run("Musterklasse (fiktiv) für den Probelauf der Pipeline; keine echten Lernenden."); r.bold = True


def bedingungsfeld(k, befunde):
    d = neu(); kopf(d, k, "Bedingungsfeld", "Schritt 05")
    dd = k["daten"]
    d.add_heading("1.1 Daten zur Klasse (Anhang I)", 1)
    vb = ", ".join(f"{n} {a}" for a, n in dd["vorbildung"].items() if n)
    tabelle(d, None, [["Bildungsgang, Beruf", k["bildungsgang"]], ["Ausbildungsjahr, Organisation", dd["organisation"]],
                      ["Lernende", f"{dd['anzahl']} ({dd['geschlecht']})"], ["Alter", dd["alter"]],
                      ["Höchster Schulabschluss", vb], ["Sprache", dd["sprache"]],
                      ["Ausbildungsbetriebe", dd["betriebe"]], ["Besonderheiten", dd.get("besonderheiten", "–")]], [5.0, 12.0])
    for a in k["abschnitte"]:
        d.add_heading(f"{a['nr']} {a['titel']}", 1)
        for t in a.get("text", []):
            p = d.add_paragraph(t); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        tabelle(d, ["Bedingung", "Konsequenz für die Planung"], a["bedingungen"], [8.5, 8.5], groesse=9.5)
    d.add_heading("Schlüssel-Lernende (Personas)", 1)
    d.add_paragraph("Drei Lernende, an denen Differenzierung, Sitzplan und Antizipation geprüft werden.")
    tabelle(d, ["Persona", "Kürzel", "Profil", "Niveau", "Was hilft"],
            [[p["name"], p["k"], p["profil"], p["niveau"], p["hilft"]] for p in k["personas"]], [2.5, 1.4, 7.0, 1.8, 4.3], groesse=9)
    d.add_heading("Prüfbericht", 1)
    tabelle(d, ["Stufe", "Befund"], befunde + k["pruefbericht"], [2.6, 14.4], faerben=lambda z: STUFE[z[0]])
    return d


def lernausgangslage(k):
    d = neu(); kopf(d, k, "Lernausgangslage", "Schritt 06 (allgemeiner Teil)")
    for t in k["lernausgangslage_text"]:
        p = d.add_paragraph(t); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    tabelle(d, ["Bereich", "Stand", "Quelle", "Konsequenz"],
            [[z["bereich"], z["stand"], z.get("quelle") or "–", z["konsequenz"]] for z in k["lernausgangslage"]], [4.0, 4.5, 3.5, 5.0], groesse=9)
    return d


def sitzplan(k, bild=None):
    d = neu(quer=True); kopf(d, k, "Kommentierter Sitzplan", "Anhang zum Entwurf")
    sitzplan_inhalt(d, k, 25.7, bild=bild)
    return d


def sitzplan_inhalt(d, k, gesamtbreite, kommentar_breiten=(1.6, 2.2, 4.5, 17.4), bild=None):
    """Raumplan plus Kommentartabelle; auch für Entwürfe (Hochformat: 17 cm). Liegt ein Bild aus dem
    Sitzplan-Studio vor (sitzplan_bild.py), steht es statt des Rasters da."""
    r = k["raum"]
    d.add_paragraph(r["beschreibung"])
    if bild and pathlib.Path(bild).exists():
        breite = min(gesamtbreite, 17.0)
        p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(bild), width=Cm(breite))
        d.add_paragraph("Ring: grün Beginner · blau Könner · violett Experte. Zahl am Rand: Persona 1, 2, 3. Punkt: orange "
                        "Deutsch als Zweitsprache, rot Unterstützungsbedarf. Kürzel statt Namen; die Namen trägt die Lehrkraft "
                        "nur lokal für die Abgabe ein (Datenschutz). Bild aus dem Sitzplan-Studio.").runs[0].font.size = Pt(9)
        kommentare(d, k, kommentar_breiten)
        return
    p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("Tafel · Beamer · Lehrertisch"); run.bold = True
    platz = {tuple(x["platz"]): x for x in k["lernende"]}
    t = d.add_table(rows=r["reihen"], cols=r["plaetze_je_reihe"]); t.style = "Table Grid"; t.autofit = False
    breite = gesamtbreite / r["plaetze_je_reihe"]
    for i in range(r["reihen"]):
        for j in range(r["plaetze_je_reihe"]):
            c = t.cell(i, j); c.width = Cm(breite); c.text = ""
            x = platz.get((i + 1, j + 1))
            if not x:
                c.paragraphs[0].add_run("frei").font.size = Pt(8); continue
            q = c.paragraphs[0]; rr = q.add_run(f"{x['k']}  "); rr.bold = True; rr.font.size = Pt(9)
            q.add_run(x["niveau"]).font.size = Pt(8)
            for z in (x["kurz"],):
                c.add_paragraph().add_run(z).font.size = Pt(7.5)
            schatten(c, NIVEAU_FARBE[x["niveau"]])
    d.add_paragraph()
    d.add_paragraph("Farben: grün Beginner · blau Könner · violett Experte. Kürzel statt Namen; die Namen trägt die Lehrkraft "
                    "nur lokal für die Abgabe ein (Datenschutz).")
    kommentare(d, k, kommentar_breiten)


def kommentare(d, k, breiten):
    """Kommentartabelle; mit Leistungsangaben (Leitfaden: schriftliche und sonstige Leistungen), sobald Noten vorliegen."""
    d.add_heading("Kommentare zu den Lernenden", 1)
    if any(x.get("noten") for x in k["lernende"]):
        b = list(breiten); b = b[:3] + [1.5, 1.5, b[3] - 3.0]
        tabelle(d, ["Kürzel", "Niveau", "Vorbildung", "Note schriftlich", "Note sonstige", "Kommentar"],
                [[x["k"], x["niveau"], x["vorbildung"], x.get("noten", {}).get("schriftlich", "–"),
                  x.get("noten", {}).get("sonstige", "–"), x["kommentar"]] for x in k["lernende"]], b, groesse=8.5)
        q = d.add_paragraph(k.get("noten_hinweis", "Noten: schriftlich aus Klassenarbeiten und Tests, sonstige aus Mitarbeit, "
                                                    "Protokollen und Teamarbeit."))
        q.runs[0].font.size = Pt(8.5)
    else:
        tabelle(d, ["Kürzel", "Niveau", "Vorbildung", "Kommentar"],
                [[x["k"], x["niveau"], x["vorbildung"], x["kommentar"]] for x in k["lernende"]], list(breiten), groesse=8.5)


def erzeugen(ab, kurz):
    ab = pathlib.Path(ab)
    k = json.loads((ab / ".daten" / "klasse" / f"{kurz}.json").read_text(encoding="utf-8"))
    befunde = pruefen(k)
    ordner = ab / k["ordner"]; ordner.mkdir(parents=True, exist_ok=True)
    ziele = []
    try:
        from sitzplan_bild import erzeugen as bild_erzeugen
        bild = bild_erzeugen(ab, kurz)
    except (Exception, SystemExit) as e:
        bild = None; befunde.append(["Hinweis", f"Sitzplan ohne Bild aus dem Sitzplan-Studio (Raster statt Bild): {e}"])
    for name, dok, schritt in (("Bedingungsfeld.docx", bedingungsfeld(k, befunde), "Schritt 05"),
                               ("Lernausgangslage.docx", lernausgangslage(k), "Schritt 06 (Klasse)"),
                               ("Sitzplan.docx", sitzplan(k, bild), "Schritt 05 (Sitzplan)")):
        z = ordner / name; dok.save(z); ziele.append(z)
        sbmod.schreiben(ab, str(z.relative_to(ab)), "klasse", f"{k['klasse']} {name[:-5]}", [], "Elektrotechnik", schritt, k)
    return ziele, befunde


if __name__ == "__main__":
    z, b = erzeugen(sys.argv[1], sys.argv[2]); [print(x) for x in z]; [print(*x) for x in b]
