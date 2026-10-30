"""Voller Entwurf für GUB und PU (Seminarprofil nach Profilwert `seminar`, mitgeliefert Osnabrück LBS), aufgerufen von entwurf.py.

Aufbau nach Leitfaden und KONZEPT (Aufbau GUB/PU-Entwurf mit Seitenbudget): Deckblatt nach Seminar-Muster,
Inhaltsverzeichnis mit Seitenzahlen und Abkürzungsverzeichnis (römisch), Kap. 1 bis 3 (arabisch, höchstens sechs
Textseiten: 1,5 · 0,5 · 0,5 · 1,5 · 1 · 1), Literaturverzeichnis (APA 7, nur zitierte Werke), Anhang I
(Verlaufsskizze, Kompetenztabelle, Sequenzierung, Daten zur Klasse, kommentierter Sitzplan, sonderpädagogische
Konzeption) und Anhang II (didaktisches Material mit den Anlagen aus Pipeline 2, Erwartungshorizont, dienstliche
Versicherung, KI-Übersicht). Zwei Durchläufe: Der erste Satz liefert über LibreOffice die Seitenzahlen fürs
Inhaltsverzeichnis und misst die Kapitellängen; der zweite baut mit den Seitenzahlen.

Daten: im Feld "besuch" der Stunde zusätzlich "kapitel" (k1: Liste [Titel, Text], k21, k22, k23, k24, k3: Listen von
Absätzen) und "literatur" als Liste [Kurzzitat, Eintrag]; das Kurzzitat muss im Text vorkommen, sonst Fehler."""
import pathlib, re, subprocess, tempfile
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from docxcompose.composer import Composer

import entwurf as E

# Seitenbudget aus dem Seminarprofil (seminare/<id>/seminar.json), gesetzt in erzeugen()
BUDGET, HOECHSTENS = [], 6.0
VERZEICHNIS = ["1 Analyse des Bedingungsfeldes", "2 Didaktisch-methodische Konzeption", "2.1 Analyse der curricularen Vorgaben",
               "2.2 Angestrebte Kompetenzen", "2.3 Analyse der Thematik, ihrer Komplexität und ihre fachliche Begründung",
               "2.4 Auswahl- und Reduktionsentscheidungen", "3 Gestaltung der Verlaufsstruktur", "Literaturverzeichnis",
               "Anhang I", "Unterrichtsverlaufsskizze", "Kompetenztabelle", "Sequenzierung der Lernsituation",
               "Daten zur Klasse", "Kommentierter Sitzplan", "Sonderpädagogische Konzeption", "Anhang II",
               "Didaktisches Material", "Erwartungshorizont", "Dienstliche Versicherung", "Übersicht verwendeter Hilfsmittel (KI)"]
HAUPT = {"1 Analyse des Bedingungsfeldes", "2 Didaktisch-methodische Konzeption", "3 Gestaltung der Verlaufsstruktur",
         "Literaturverzeichnis", "Anhang I", "Anhang II"}


def verzeichnis(bs):
    """Einträge des Inhaltsverzeichnisses; der letzte Teil von Anhang I richtet sich nach den Daten."""
    v = [e for e in VERZEICHNIS if e != "Sonderpädagogische Konzeption" or bs.get("sonderpaedagogik")]
    if bs.get("heterogenitaet"):
        v.insert(v.index("Anhang II"), "Heterogenität der Lerngruppe")
    return v


ABKUERZUNGEN = [("AB", "Arbeitsblatt"), ("Anl.", "Anlage"), ("DQR", "Deutscher Qualifikationsrahmen"), ("DS", "Doppelstunde"), ("FK", "Fachkompetenz"),
                ("GUB", "Gemeinsamer Unterrichtsbesuch"), ("LF", "Lernfeld"), ("LiV", "Lehrkraft im Vorbereitungsdienst"),
                ("LK", "Lernfeld-Kompetenz"), ("LS", "Lernsituation"), ("MK", "Methodenkompetenz"), ("PK", "Personale Kompetenz"),
                ("PU", "Prüfungsunterricht"), ("SeK", "Selbstkompetenz"), ("SoK", "Sozialkompetenz"), ("S01 …", "Kürzel der Lernenden"),
                ("TK", "Teilkompetenz")]


def seitenzahl(sec, fmt, start=None):
    pg = sec._sectPr.find(qn("w:pgNumType"))
    if pg is None:
        pg = OxmlElement("w:pgNumType"); sec._sectPr.append(pg)
    pg.set(qn("w:fmt"), fmt)
    if start is not None: pg.set(qn("w:start"), str(start))
    sec.footer.is_linked_to_previous = False
    p = sec.footer.paragraphs[0]; p.text = ""; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run()
    for typ, txt in (("begin", None), (None, " PAGE "), ("end", None)):
        if typ:
            f = OxmlElement("w:fldChar"); f.set(qn("w:fldCharType"), typ); r._r.append(f)
        else:
            it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = txt; r._r.append(it)


def absatz(d, t):
    p = d.add_paragraph(t); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return p


def bauen(ab, s, ls, k, seiten=None):
    bs = s["besuch"]; kap = bs["kapitel"]
    d = E.neu()
    E.deckblatt(d, s, ls, k)
    sec = d.add_section(WD_SECTION.NEW_PAGE); seitenzahl(sec, "upperRoman", 2)
    d.add_heading("Inhaltsverzeichnis", 1)
    for e in verzeichnis(bs):
        p = d.add_paragraph(); p.paragraph_format.tab_stops.add_tab_stop(Cm(16), alignment=2, leader=1)
        einr = e.startswith("2.") or e not in HAUPT
        if einr: p.paragraph_format.left_indent = Cm(0.8)
        r = p.add_run(e); r.bold = not einr
        p.add_run("\t" + str((seiten or {}).get(e, "")))
    E.seite(d); d.add_heading("Abkürzungsverzeichnis", 1)  # eigene Seite III (Seminar: Seitenanzahl/Nummerierung)
    for a, b in sorted(ABKUERZUNGEN + [tuple(x) for x in bs.get("abkuerzungen", [])], key=lambda x: x[0].lower()):
        p = d.add_paragraph(); p.paragraph_format.tab_stops.add_tab_stop(Cm(3)); p.paragraph_format.line_spacing = 1.15
        p.add_run(a).bold = True; p.add_run("\t" + b)
    # Hauptteil
    sec = d.add_section(WD_SECTION.NEW_PAGE); seitenzahl(sec, "decimal", 1)
    d.add_heading("1 Analyse des Bedingungsfeldes", 1)
    for titel, text in kap["k1"]:
        p = d.add_paragraph(); p.add_run(titel).bold = True; p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.keep_with_next = True
        absatz(d, text)
    d.add_heading("2 Didaktisch-methodische Konzeption", 1)
    for nr, titel in (("k21", "2.1 Analyse der curricularen Vorgaben"), ("k22", "2.2 Angestrebte Kompetenzen"),
                      ("k23", "2.3 Analyse der Thematik, ihrer Komplexität und ihre fachliche Begründung"),
                      ("k24", "2.4 Auswahl- und Reduktionsentscheidungen")):
        d.add_heading(titel, 2)
        for t in kap[nr]:
            absatz(d, t)
    d.add_heading("3 Gestaltung der Verlaufsstruktur", 1)
    for t in kap["k3"]:
        absatz(d, t)
    E.seite(d); d.add_heading("Literaturverzeichnis", 1)
    for _, eintrag in sorted(bs["literatur_voll"], key=lambda x: x[1].lower()):
        p = d.add_paragraph(eintrag); p.paragraph_format.left_indent = Cm(1); p.paragraph_format.first_line_indent = Cm(-1)
        p.paragraph_format.line_spacing = 1.15; p.paragraph_format.space_after = Pt(4)
    # Anhang I
    sec = d.add_section(WD_SECTION.NEW_PAGE); seitenzahl(sec, "upperRoman", 4)
    d.add_heading("Anhang I", 1)
    E.verlaufsskizze(d, s)
    E.seite(d); d.add_heading("Kompetenztabelle", 1)
    p = d.add_paragraph(); p.add_run("Kernkompetenz der Unterrichtsstunde: ").bold = True; p.add_run(bs["kernkompetenz"])
    E.tabelle(d, ["Qualifikationsebene\nKompetenz = angestrebter Zielzustand", "Schnittstelle",
                  "Handlungsebene\nHandlung, durch welche die angestrebte Kompetenz beobachtbar wird (Performanz)"],
              [[f"{x['nr']}: {x['kompetenz'].rstrip(', ')} ({', '.join(E.bereiche(x))})", "indem sie", x["indem"]] for x in bs["tk"]],
              [6.9, 2.1, 7.0], groesse=9.5)
    genutzt = list(dict.fromkeys(b for x in bs["tk"] for b in E.bereiche(x)))
    d.add_paragraph(" · ".join(f"{b} {E.BEREICHE[b]}" for b in genutzt) + " · TK Teilkompetenz").runs[0].font.size = Pt(8.5)
    E.seite(d); E.sequenzierung(d, s, ls)
    E.seite(d); d.add_heading("Daten zur Klasse", 1)
    dd = k["daten"]
    E.tabelle(d, None, [["Bildungsgang, Beruf", k["bildungsgang"]], ["Ausbildungsjahr, Organisation", dd["organisation"]],
                        ["Lernende", f"{dd['anzahl']} ({dd['geschlecht']})"], ["Alter", dd["alter"]],
                        ["Höchster Schulabschluss", ", ".join(f"{n} {a}" for a, n in dd["vorbildung"].items() if n)],
                        ["Sprache", dd["sprache"]], ["Ausbildungsbetriebe", dd["betriebe"]],
                        ["Besonderheiten", dd.get("besonderheiten", "–")]], [5.0, 11.0], groesse=9.5)
    E.seite(d); d.add_heading("Kommentierter Sitzplan", 1)
    E.sitzplan_inhalt(d, k, 16.0, (1.3, 1.8, 3.2, 9.7), bild=ab / k["ordner"] / "Sitzplan.png")
    if bs.get("sonderpaedagogik"):
        E.seite(d); d.add_heading("Sonderpädagogische Konzeption", 1)
        for titel, text in bs["sonderpaedagogik"]:
            p = d.add_paragraph(); p.add_run(titel).bold = True
            absatz(d, text)
    if bs.get("heterogenitaet"):  # statt einer Konzeption für Einzelne (Lehrkraft, PU 2026-10-12)
        E.seite(d); d.add_heading("Heterogenität der Lerngruppe", 1)
        h = bs["heterogenitaet"]
        E.tabelle(d, h["kopf"], h["zeilen"], h.get("breiten", [2.0, 3.6, 4.4, 4.6, 1.4]), groesse=9)
    # Anhang II
    E.seite(d); d.add_heading("Anhang II", 1)
    d.add_heading("Didaktisches Material", 2)
    fertig = E.anlagen_dateien(ab, s)
    E.tabelle(d, ["Anlage", "Titel", "Einsatz", "Stand"],
              [[E.zeichen(x), x["titel"], x["felder"][0][1], "beigefügt" if E.zeichen(x) in fertig else "folgt"] for x in s["anlagen"]],
              [1.5, 4.8, 7.9, 1.8], groesse=9)
    E.einzeilig(d)
    schluss = E.neu()
    schluss.add_heading("Erwartungshorizont", 2)
    E.tabelle(schluss, ["Anlage", "Erwartete Ergebnisse"], [[f"{E.zeichen(x)} {x['titel']}", x["erwartungshorizont"]] for x in s["anlagen"]],
              [4.0, 12.0], groesse=9)
    E.seite(schluss); schluss.add_heading("Dienstliche Versicherung", 2)
    absatz(schluss, E.SEMINAR["versicherung"])
    schluss.add_paragraph(); schluss.add_paragraph("__________________________          __________________________")
    schluss.add_paragraph("Ort, Datum                                                 Unterschrift")
    schluss.add_heading("Übersicht verwendeter Hilfsmittel (KI)", 2)
    E.tabelle(schluss, None, bs.get("ki_verzeichnis") or [["Werkzeug", "[Name, Version, Anbieter, URL]"]], [4.0, 12.0], groesse=9.5)
    E.einzeilig(schluss)
    E.seite(d)
    c = Composer(d)
    for datei in dict.fromkeys(fertig.values()):       # Arbeitsblaetter.docx nur einmal anhängen
        teil = Document(datei); teil.add_section(WD_SECTION.NEW_PAGE); c.append(teil)
    c.append(schluss)
    return c, fertig


def pdf(pfad, ordner):
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(ordner), str(pfad)],
                   check=True, capture_output=True, timeout=240)
    return pathlib.Path(ordner) / (pfad.stem + ".pdf")


def roemisch(n):
    out = ""
    for w, z in ((40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        while n >= w: out += z; n -= w
    return out


def vermessen(pdfpfad):
    """Seitenzahlen für das Inhaltsverzeichnis und Kapitellängen im Satz (Seiten, Nutzhöhe bei 2,5 cm Rand)."""
    import pdfplumber
    with pdfplumber.open(str(pdfpfad)) as p:
        H = p.pages[0].height; rand = 2.5 / 2.54 * 72; nutz = H - 2 * rand
        zeilen = [[(ln["text"].strip(), ln["top"], ln["bottom"]) for ln in pg.extract_text_lines()] for pg in p.pages]
    haupt = next(i for i, z in enumerate(zeilen) if any(t == "1 Analyse des Bedingungsfeldes" for t, *_ in z)
                 and not any(t.startswith("Inhaltsverzeichnis") for t, *_ in z))
    anh = next(i for i, z in enumerate(zeilen) if i > haupt and any(t == "Anhang I" for t, *_ in z))
    seiten, pos = {}, {}
    for e in VERZEICHNIS + ["Heterogenität der Lerngruppe"]:
        for i in range(haupt, len(zeilen)):
            treffer = [(t, top) for t, top, _ in zeilen[i] if t == e or (e.startswith("2.3") and t.startswith("2.3 Analyse der Thematik"))]
            if treffer:
                seiten[e] = i - haupt + 1 if i < anh else roemisch(4 + i - anh)
                pos[e] = (i, treffer[0][1]); break
    lit = pos.get("Literaturverzeichnis")
    letzte = None
    for i in range(haupt, lit[0]):
        body = [b for t, top, b in zeilen[i] if b < H - rand - 5]
        if body: letzte = (i, max(body))
    def laenge(a, b): return round((b[0] - a[0]) + (b[1] - a[1]) / nutz, 2)
    kap_pos = [pos[e if not e.startswith("2.3") else VERZEICHNIS[4]] for e, _ in BUDGET]
    messung = []
    for j, (name, soll) in enumerate(BUDGET):
        ende = kap_pos[j + 1] if j + 1 < len(BUDGET) else letzte
        if name.startswith("1 "):  # Kap. 1 endet am Kopf von Kap. 2
            ende = pos["2 Didaktisch-methodische Konzeption"]
        messung.append((name, laenge(kap_pos[j], ende), soll))
    summe = laenge(kap_pos[0], letzte)
    return seiten, messung, summe, len(zeilen)


def pruefen(s, bs, messung, summe):
    b = []
    text = " ".join(t for _, t in bs["kapitel"]["k1"]) + " " + " ".join(
        t for n in ("k21", "k22", "k23", "k24", "k3") for t in bs["kapitel"][n]) + " " + " ".join(
        t for _, t in bs.get("sonderpaedagogik", [])) + " " + " ".join(
        " ".join(z) for z in bs.get("heterogenitaet", {}).get("zeilen", []))
    for kurz, eintrag in bs["literatur_voll"]:
        if kurz not in text:
            b.append(["Fehler", f"Literatur nicht zitiert (Kurzzitat „{kurz}“ fehlt im Text): {eintrag[:60]}"])
    for zitat in set(re.findall(r"\(([A-ZÄÖÜ][^()]*?\d{4}[a-z]?)(?:, S\. [^)]*)?\)", text)):
        for teil in zitat.split(";"):
            teil = re.sub(r"^vgl\. ", "", teil.strip()); teil = re.sub(r", S\. .*$", "", teil)
            if not any(kurz in teil or teil in kurz for kurz, _ in bs["literatur_voll"]):
                b.append(["Warnung", f"Zitat ohne Eintrag im Literaturverzeichnis: ({teil})"])
    for name, ist, soll in messung:
        if abs(ist - soll) > 0.1 * soll + 0.05:
            b.append(["Warnung", f"{name}: {ist:.2f} Seiten statt {soll:.1f} (Budget der Lehrkraft, ± 10 %)"])
        else:
            b.append(["Hinweis", f"{name}: {ist:.2f} Seiten (Budget {soll:.1f})"])
    if summe > HOECHSTENS:
        b.append(["Fehler", f"Kap. 1 bis 3 umfassen {summe:.2f} Seiten; das Seminar erlaubt höchstens {HOECHSTENS:g} Textseiten"])
    else:
        b.append(["Hinweis", f"Kap. 1 bis 3 zusammen {summe:.2f} Seiten (höchstens {HOECHSTENS:g})"])
    if "–" in text:
        b.append(["Warnung", "Gedankenstrich im Fließtext (Profil: keine Gedankenstriche)"])
    return b


def erzeugen(ab, s, ls, k, befunde):
    global HOECHSTENS
    # Seminarprofil auch in diesem Modul laden (entwurf.py läuft als Skript, hier ist es ein eigenes Modul E; PROFIL
    # bleibt dabei leer wie bisher, siehe KONZEPT 2026-11)
    import profil as profilmod
    E.seminar_laden(profilmod.lade(ab))
    BUDGET[:] = [tuple(x) for x in E.SEMINAR["seitenbudget"]["kapitel"]]
    HOECHSTENS = E.SEMINAR["seitenbudget"]["hoechstens"]
    ziel = ab / s["ordner"] / f"Entwurf_{s['besuch']['art']}.docx"; ziel.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        c, fertig = bauen(ab, s, ls, k); c.save(ziel)
        seiten, messung, summe, n = vermessen(pdf(ziel, tmp))
        c, fertig = bauen(ab, s, ls, k, seiten); c.save(ziel)
        seiten2, messung, summe, n = vermessen(pdf(ziel, tmp))
    fehlen = [E.zeichen(x) for x in s["anlagen"] if E.zeichen(x) not in fertig]
    if fehlen:
        befunde.append(["Hinweis", "Material aus Pipeline 2 fehlt noch: " + ", ".join(fehlen)])
    befunde += pruefen(s, s["besuch"], messung, summe)
    befunde.append(["Hinweis", f"Entwurf mit {n} Seiten; Inhaltsverzeichnis mit Seitenzahlen aus dem Satz (LibreOffice; in Word "
                               "kann der Umbruch leicht abweichen)"])
    return ziel
