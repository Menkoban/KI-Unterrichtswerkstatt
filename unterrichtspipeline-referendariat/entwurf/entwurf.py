"""Entwurf für einen Unterrichtsbesuch aus den Daten einer Stunde (Seminar nach Profilwert `seminar`, Seminarprofil
unter seminare/<id>/seminar.json; mitgeliefert Studienseminar Osnabrück, LBS).

    python entwurf/entwurf.py <arbeitsbereich> <kurzname der stunde>

Daten:    .daten/stunde/<kurzname>.json (Feld "besuch" mit art, deckblatt, kernkompetenz, tk, sequenz,
          literatur, ziele), dazu Lernsituation (.daten/lernsituation/<ls>.json) und Klassen-Akte
          (.daten/klasse/<klasse>.json).
Ergebnis: <ordner der stunde>/Entwurf_<ART>.docx und Steckbrief.

Kurzentwurf (EUB, KUB, FLB) nach Seminar-Leitfaden „Vorgaben für den Entwurf bei einfachen
Unterrichtsbesuchen“: Deckblatt, Kernkompetenz der Stunde (Satz ohne Handlungsebene), Tabelle der
Teilkompetenzen, Unterrichtsverlaufsskizze, Sequenzierung der Lernsituation inkl. Handlungssituation,
ggf. sonderpädagogische Konzeption, vereinbarte Ziele aus der Dokumentation der Ausbildung; wahlweise eine kurze
Sachinformation. Anhang in der Reihenfolge des Leitfadens: Literaturverzeichnis, kommentierter Sitzplan, didaktisches
Material (fertige Anlagen aus Pipeline 2 unter <ordner>/Anlagen/Anl_<nr>_<titel>.docx werden
angehängt, fehlende als „folgt“ gemeldet), Erwartungshorizont; am Schluss die dienstliche Versicherung mit KI-Übersicht. Format nach Leitfaden (Arial 11,
1,5-zeilig, Ränder 2,5 cm), Deckblatt nach Seminar-Muster, Kompetenztabelle nach Seminar-Beispiel (Kompetenzbereich in
Klammern, Legende darunter). Der Prüfbericht steht in einer eigenen Datei (Pruefbericht_Entwurf_<ART>.docx). Beim KUB zusätzlich der gemeinsame Beobachtungsbogen nach UB-BBS LK 2025
mit Bezügen zur Stunde, Verhaltenshinweisen und Feld für die Karten, die Zeile „Teilnehmende LiV“ im Deckblatt und das
vorbefüllte KUB-Protokoll (KUB_Protokoll.docx).
Prüft selbst: Kernkompetenz ohne „indem“, jede Teilkompetenz mit „indem“-Teil und bekanntem
Kompetenzbereich (Warnung bei nur fachlichen), jede Anlage mit Erwartungshorizont, Platzhalter im Deckblatt, 4 bis 6 Sequenzen mit markierter Besuchsstunde, Zeiten der Verlaufsskizze lückenlos, Literatur
nicht leer, Sitzplan aus einer freigegebenen Klassen-Akte."""
import json, pathlib, re, sys
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docxcompose.composer import Composer
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

W = pathlib.Path(__file__).resolve().parents[1]
for unter in ("lernsituation", "akten", "klasse", "stunde", "seminare"):
    sys.path.insert(0, str(W / unter))
from ls_ausarbeitung import STUFE, schatten, tabelle
import steckbrief as sbmod
from klassenakte import sitzplan_inhalt
from stunde import dateiname, minuten, seminar_zeile, zeichen
import seminar as seminarmod
PROFIL = {}   # Lehrkraft-Profil, in erzeugen() geladen (Seminarfassung der Verlaufsskizze)

# Seminarprofil (Profilwert `seminar`, Veröffentlichung 2026-11): Besuchsformen, Paragrafen nach den Seminar-Mustern,
# Versicherung, Hinweise und Seitenbudget stehen in seminare/<id>/seminar.json; in erzeugen() geladen.
SEMINAR = {}
KURZ, VOLL, NAME, PARAGRAF = set(), set(), {}, {}
FACH = {"fachrichtung": "[Fachrichtung]", "unterrichtsfach": "[Unterrichtsfach]"}


def seminar_laden(profil):
    SEMINAR.clear(); SEMINAR.update(seminarmod.lade(profil))
    KURZ.clear(); VOLL.clear(); NAME.clear(); PARAGRAF.clear()
    for art, f in SEMINAR["besuchsformen"].items():
        (VOLL if f["entwurf"] == "voll" else KURZ).add(art)
        NAME[art] = f["name"]
        if f.get("paragraf"):
            PARAGRAF[art] = f["paragraf"]
    FACH["fachrichtung"], FACH["unterrichtsfach"] = seminarmod.faecher(profil)


HELL, BAND = "D6ECEA", "4F9A94"


BEREICHE = {"FK": "Fachkompetenz", "PK": "Personale Kompetenz", "SoK": "Sozialkompetenz", "SeK": "Selbstkompetenz",
            "MK": "Methodenkompetenz (Querschnitt)"}
NUR_INTERN = {"FK", "PK", "SoK", "SeK", "MK"}


def anlagen_dateien(ab, s):
    """Fertiges Material aus Pipeline 2 unter <ordner der stunde>/Anlagen/: Arbeitsblaetter.docx (alle AB fortlaufend)
    und Anl_<nr>_*.docx, je Nummer die erste Datei. Schlüssel: Kurzzeichen („AB 1“, „Anl. 3“), in Reihenfolge der Akte."""
    ordner = ab / s["ordner"] / "Anlagen"; fertig = {}
    for x in s["anlagen"]:
        if x.get("art") == "Arbeitsblatt":
            f = ordner / "Arbeitsblaetter.docx"
        else:
            f = next(iter(sorted(ordner.glob(f"Anl_{x['nr']}_*.docx"))), None) if ordner.exists() else None
        if f is not None and f.exists():
            fertig[zeichen(x)] = f
    return fertig


def bereiche(x):
    return [b.strip() for b in x.get("bereich", "FK").split(",")]


def pruefen(s, ls, k, ab):
    b, bs = [], s["besuch"]
    art = bs["art"]
    if art not in KURZ | VOLL:
        b.append(["Fehler", f"Besuchsart {art} unbekannt"])
    if "indem" in bs["kernkompetenz"]:
        b.append(["Fehler", "Kernkompetenz enthält eine Handlungsebene („indem“); sie steht nur in den Teilkompetenzen"])
    for x in bs["tk"]:
        if not x.get("indem"):
            b.append(["Fehler", f"{x['nr']}: Teilkompetenz ohne „indem“-Teil (Handlungsebene)"])
        if set(bereiche(x)) - NUR_INTERN:
            b.append(["Fehler", f"{x['nr']}: Kompetenzbereich {x.get('bereich')} unbekannt (FK, PK, SoK, SeK, MK)"])
    if all(set(bereiche(x)) <= {"FK", "MK"} for x in bs["tk"]):
        b.append(["Warnung", "Nur fachliche Teilkompetenzen; das Seminar-Beispiel enthält auch personale (SoK, SeK)"])
    n = len(bs["sequenz"])
    if not 4 <= n <= 6:
        b.append(["Warnung", f"Sequenzierung mit {n} Sequenzen (Seminar: 5 bis 6, höchstens 6)"])
    if sum(1 for q in bs["sequenz"] if q.get("besuch")) != 1:
        b.append(["Fehler", "In der Sequenzierung ist nicht genau eine Sequenz als Besuchsstunde markiert"])
    t = 0
    for z in s["verlauf"]:
        a, e = minuten(z["zeit"])
        if a != t:
            b.append(["Fehler", f"Verlaufsskizze: Lücke oder Überschneidung vor „{z['phase']}“"])
        t = e
    if t != s["dauer"]:
        b.append(["Fehler", f"Verlaufsskizze endet bei {t} min statt {s['dauer']} min"])
    if not (bs.get("literatur_voll") if art in VOLL else bs.get("literatur")):
        b.append(["Fehler", "Literaturverzeichnis leer"])
    for x in s["anlagen"]:
        if not x.get("erwartungshorizont"):
            b.append(["Fehler", f"{zeichen(x)} ohne Erwartungshorizont (Seminar: Ergebnisse als Erwartungshorizont im Anhang)"])
    sb = ab / ".daten" / "akten" / k["ordner"] / "Sitzplan.docx.json"
    if not sb.exists() or json.loads(sb.read_text(encoding="utf-8"))["stand"] != "freigegeben":
        b.append(["Warnung", "Sitzplan der Klasse ist nicht freigegeben"])
    if not (ab / k["ordner"] / "Sitzplan.png").exists():
        b.append(["Hinweis", "Kein Sitzplan-Bild (klasse/sitzplan_bild.py); der Sitzplan steht als Raster da"])
    if art == "KUB" and not bs.get("beobachtung"):
        b.append(["Fehler", "KUB ohne Beobachtungsaufträge für die Mitreferendare"])
    offen = [kk for kk, v in deckblatt_zeilen(s, ls, k) if v.startswith("[")]
    if offen:
        b.append(["Hinweis", "Deckblatt mit Platzhaltern (vor der Abgabe eintragen): " + ", ".join(x.rstrip(":") for x in offen)])
    if k.get("musterklasse"):
        b.append(["Hinweis", "Klasse ist eine Musterklasse (fiktiv); Probelauf."])
    if art == "KUB":
        b += [["Hinweis", h.format(**FACH)] for h in SEMINAR.get("hinweise", {}).get("KUB", [])]
    if art == "PU":
        b += [["Hinweis", h.format(**FACH)] for h in SEMINAR.get("hinweise", {}).get("PU", [])]
        if s.get("vorlauf"):
            b.append(["Hinweis", "PU als zweite Stunde der Doppelstunde: Die erste Stunde ist in der Verlaufsskizze vorangestellt und "
                                 "im Entwurf berücksichtigt (Handreichung Nr. 12; Leitfaden: volle 90 Minuten in der Planung)."])
    else:
        b += [["Hinweis", h.format(**FACH)] for h in SEMINAR.get("hinweise", {}).get("sonst", [])]
    return b


def neu():
    """Seminarformat: Arial 11, 1,5-zeilig, Ränder 2,5 cm (Leitfaden; Tabellen einzeilig)."""
    d = Document(); sec = d.sections[0]; sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    for x in ("left_margin", "right_margin", "top_margin", "bottom_margin"): setattr(sec, x, Cm(2.5))
    st = d.styles["Normal"]; st.font.name = "Arial"; st.font.size = Pt(11); st.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    st.paragraph_format.line_spacing = 1.5
    for n in ("Title", "Heading 1", "Heading 2"):
        h = d.styles[n]; h.font.name = "Arial"; h.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F); h.paragraph_format.line_spacing = 1.0
    return d


def einzeilig(d):
    for t in d.tables:
        for r in t.rows:
            for c in r.cells:
                for q in c.paragraphs: q.paragraph_format.line_spacing = 1.0


def seite(d):
    """Seitenumbruch am letzten Absatz statt in einem neuen (sonst entsteht eine Leerseite, wenn die Seite gerade voll ist)."""
    letztes = d.element.body[-2] if d.element.body[-1].tag.endswith("sectPr") else d.element.body[-1]
    p = d.paragraphs[-1] if letztes.tag.endswith("}p") else d.add_paragraph()
    p.add_run().add_break(WD_BREAK.PAGE)


def deckblatt_zeilen(s, ls, k):
    """Zeilen des Deckblatts nach den Seminar-Mustern (Muster Deckblatt GUB, PU Muster). PU: unter „Prüfungsausschuss“
    PS-Leitung, beide Fachleitungen und Schulleitung; eine Zeile Prüfungsvorsitz nur, wenn eine zusätzliche Person ihn
    übernimmt (Fußnote des Musters)."""
    db = s["besuch"].get("deckblatt", {}); art = s["besuch"]["art"]; nn = "[Herr/Frau Titel Vorname Nachname]"
    z = [("Schulform:", db.get("schulform", "Berufsschule")),
         ("ggf. Lernfeld oder Lerngebiet:", db.get("lernfeld", ls.get("lernfeld_titel", ls["lernfeld"]))),
         ("Klasse:", db.get("klasse", f"{k['klasse']}, {k['bildungsgang']}")),
         ("Tag:", db.get("tag", "[XXX]")), ("Zeit:", db.get("zeit", f"[XXX], {s['dauer']} Minuten")),
         ("Ort:", db.get("ort", "[Schulname, Schuladresse, Telefon der Schule]")), ("Raum:", db.get("raum", "[XXX]")),
         ("Fachlehrer/in:", db.get("fachlehrer", nn))]
    if art == "PU":
        z += [("Prüfungsausschuss:", "")] + ([("Prüfungsvorsitzende(r):", db["vorsitz"])] if db.get("vorsitz") else []) + [
              ("Leiter/in des PS:", db.get("ps_leitung", nn)), ("Fachleiter/in in der Fachrichtung:", db.get("fachleitung", nn)),
              ("Fachleiter/in im Unterrichtsfach:", db.get("fachleitung_uf", nn))]
    elif art == "GUB":
        z += [("Leiter/in des PS:", db.get("ps_leitung", nn)), ("Fachleiter/in in der Fachrichtung:", db.get("fachleitung", nn))]
    else:
        z += [("Fachleiter/in in der Fachrichtung:", db.get("fachleitung", nn))]
    return z + [("Schulleiter/in:", db.get("schulleitung", nn))]


def deckblatt(d, s, ls, k):
    """Nach dem Seminar-Muster (Muster Deckblatt, Leitfaden), Titelzeile je Besuchsart."""
    bs = s["besuch"]; db = bs.get("deckblatt", {})

    def block(zeilen):
        t = d.add_table(rows=0, cols=2); t.autofit = False
        for kk, v in zeilen:
            r = t.add_row().cells; r[0].text = kk; r[1].text = v
            if kk == "Prüfungsausschuss:":
                r[0].paragraphs[0].runs[0].underline = True
        for i, b in enumerate([5.5, 10.5]):
            for c in t.columns[i].cells: c.width = Cm(b)
    block([("Studienreferendar/in:", db.get("liv", "[Name, Vorname]")), ("Telefon:", db.get("telefon", "[XXX]")),
           ("Gruppe:", db.get("gruppe", "[XXX]")), ("Fachrichtung:", FACH["fachrichtung"]), ("Unterrichtsfach:", db.get("fach", FACH["unterrichtsfach"]))])
    d.add_paragraph()
    d.add_paragraph(SEMINAR["name"]).paragraph_format.line_spacing = 1.0
    p = d.add_paragraph(); p.paragraph_format.line_spacing = 1.0
    titel = (f"Entwurf zum Prüfungsunterricht {db.get('pu_nr', 'I')}" if bs["art"] == "PU" else
             f"Entwurf zu einem {NAME[bs['art']].replace('Einfacher', 'einfachen').replace('Kollegialer', 'kollegialen').replace('Gemeinsamer', 'gemeinsamen')}")
    p.add_run(f"{titel} in der beruflichen Fachrichtung {FACH['fachrichtung']}").bold = True
    if bs["art"] in VOLL:
        d.add_paragraph(PARAGRAF[bs["art"]]).paragraph_format.line_spacing = 1.0
    d.add_paragraph("_" * 72)
    block(deckblatt_zeilen(s, ls, k))
    d.add_paragraph("_" * 72)
    block([("Lernsituation:", f"LS {ls['nr']} „{ls['titel']}“"), ("Stundenthema:", s["titel"])])
    if bs["art"] == "KUB":
        block([("Teilnehmende LiV:", db.get("teilnehmende", SEMINAR["kub_teilnehmende_platzhalter"].format(**FACH)))])
    if db.get("variante"):
        q = d.add_paragraph(); r = q.add_run(db["variante"]); r.italic = True; r.font.size = Pt(9)


def verlaufsskizze(d, s):
    d.add_heading("Unterrichtsverlaufsskizze", 1)
    kopf = ("Doppelstunde, 90 Minuten" if s["dauer"] == 90 else f"Unterrichtsstunde, {s['dauer']} Minuten") + \
        ("; die erste Stunde der Doppelstunde ohne Prüfungsausschuss ist vorangestellt" if s.get("vorlauf") else "")
    zusatz = "; Zeiten und Teilkompetenzen in der Spalte Phase." if PROFIL.get("form.seminar_zeiten", True) \
        else "; Teilkompetenzen in der Spalte Phase."
    d.add_paragraph(kopf + zusatz).runs[0].font.size = Pt(9)
    t = d.add_table(rows=1, cols=5); t.style = "Table Grid"; t.autofit = False
    for c, kpf in zip(t.rows[0].cells, ["Phase", "Lerninhalte", "Methodische Entscheidungen und Lehrer-/Schüleraktivitäten",
                                        "Aktions- und Sozialformen", "Materialien und Medien"]):
        c.text = ""; rr = c.paragraphs[0].add_run(kpf); rr.bold = True; schatten(c, HELL)

    def band(text):
        r = t.add_row().cells; m = r[0]
        for c in r[1:]: m = m.merge(c)
        m.text = ""; q = m.paragraphs[0]; q.alignment = WD_ALIGN_PARAGRAPH.CENTER
        rr = q.add_run(text); rr.bold = True; rr.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF); schatten(m, BAND)

    def zelle(c, zeilen):
        c.text = ""
        for i, z in enumerate(zeilen):
            q = c.paragraphs[0] if i == 0 else c.add_paragraph()
            if z.startswith("**"): q.add_run(z.strip("*")).bold = True
            else: q.add_run(z)

    zeilen = s["verlauf"] + ([s["reserve"]] if s.get("reserve") else [])
    if s.get("vorlauf"):  # Handreichung Staatsprüfung Nr. 12: Verlauf des ersten Teils angemessen berücksichtigen
        band("Erste Stunde der Doppelstunde, ohne Prüfungsausschuss, ab [Uhrzeit]")
        zeilen = s["vorlauf"] + [None] + zeilen
    else:
        band("Beginn der Unterrichtsstunde um [Uhrzeit]")
    for z in zeilen:
        if z is None:
            band("Beginn des Prüfungsunterrichts um [Uhrzeit]"); continue
        r = t.add_row().cells
        z = seminar_zeile(z, PROFIL)
        kopf = [f"**{z['phase']}**"] + ([f"({z['zeit']})"] if z.get("zeit") else []) \
            + ([z["handlungsphase"]] if z.get("handlungsphase") else []) + ([z["tk"]] if z.get("tk") else [])
        for c, inhalt in zip(r, (kopf, z["inhalte"], z["aktivitaeten"], z["sozial"], z["medien"])):
            zelle(c, inhalt)
    band("Ende der Unterrichtsstunde um [Uhrzeit]")
    for i, b in enumerate([2.5, 2.8, 5.6, 2.2, 2.9]):
        t.columns[i].width = Cm(b)
        for c in t.columns[i].cells: c.width = Cm(b)
    for row in t.rows:
        for c in row.cells:
            for q in c.paragraphs:
                for run in q.runs: run.font.size = Pt(8)


UB_BBS = [("Lernumgebung", [(1, "Die Lehrkraft organisiert eine lernförderliche Umgebung.")]),
          ("Lernprozesse – Lehrkraft", [(2, "Die Lehrkraft schafft eine lernförderliche Atmosphäre."),
                                        (3, "Die Lehrkraft ermöglicht selbstgesteuertes Lernen."),
                                        (4, "Die Lehrkraft begleitet den Lernprozess kompetent."),
                                        (5, "Die Lehrkraft kommuniziert situationsgerecht."),
                                        (6, "Die Lehrkraft fördert kooperatives Lernen."),
                                        (7, "Die Lehrkraft ermöglicht die lernwirksame Nutzung von Materialien und Medien."),
                                        (8, "Die Lehrkraft gibt konstruktive Rückmeldungen."),
                                        (9, "Die Lehrkraft ermöglicht die Reflexion der Lernprozesse."),
                                        (10, "Die Lehrkraft gewährleistet eine effiziente Nutzung der Lernzeit.")]),
          ("Unterrichtsprozess", [(11, "Der Unterricht basiert auf einer geeigneten Handlungssituation."),
                                  (12, "Der Unterricht ist Teil der vollständigen Handlung."),
                                  (13, "Der Unterricht ist auf ein Handlungsergebnis ausgerichtet."),
                                  (14, "Der Unterricht ermöglicht die Entwicklung von Handlungskompetenz.")]),
          ("Lernprozesse – Schülerinnen und Schüler", [(15, "Die Schülerinnen und Schüler tragen zu einer lernförderlichen Atmosphäre bei."),
                                                       (16, "Die Schülerinnen und Schüler lernen selbstgesteuert."),
                                                       (17, "Die Schülerinnen und Schüler lernen kooperativ."),
                                                       (18, "Die Schülerinnen und Schüler gehen konstruktiv mit Rückmeldungen um.")])]
UB_QUELLE = ("Handlungsorientierten Unterricht beobachten – BBS. Version Lehrkräfte (UB-BBS LK 2025). (2025). Portal interne "
             "Evaluation BBS, Niedersächsischer Bildungsserver. https://wordpress.nibis.de/portal-interne-evaluation-bbs/")
VERHALTEN = ("Hinweise des Seminars für Beobachtende: möglichst gleichzeitig mit der LiV und gemeinsam den Raum betreten; nicht "
             "miteinander sprechen, Blickkontakt zueinander vermeiden; den Blick nicht auf die unterrichtende LiV fokussieren und nur "
             "gemäßigtes Interesse an den Abläufen zeigen; nicht ins Unterrichtsgeschehen eingreifen.")


def beobachtungsbogen(d, s, b):
    """KUB: ein gemeinsamer Bogen für alle Beobachtenden (hinten, ganze Stunde), nach dem vom Seminar verlinkten Instrument
    UB-BBS LK 2025 (18 Merkmale, vierstufig), mit Bezügen zu dieser Stunde, Verhaltenshinweisen des Seminars und dem Feld
    für die Karten der Nachbesprechung (grün/gelb). KONZEPT 2026-10-11."""
    seite(d); d.add_heading("Beobachtungsbogen für die kollegiale Beratung", 1)
    q = d.add_paragraph("Für alle Beobachtenden gleich. Beobachtet wird die Umsetzung der Stunde, unauffällig von hinten und über die "
                        "ganze Stunde. " + VERHALTEN); q.runs[0].font.size = Pt(9); q.paragraph_format.line_spacing = 1.0
    if b.get("aspekte"):
        tabelle(d, None, [[f"Beratungsaspekt {i} (freiwillig)", a] for i, a in enumerate(b["aspekte"], 1)], [4.6, 11.4], groesse=9)
    bezug = {int(k): v for k, v in b.get("bezuege", {}).items()}
    t = d.add_table(rows=1, cols=8); t.style = "Table Grid"; t.autofit = False
    for c, k in zip(t.rows[0].cells, ["Nr.", "Merkmal", "In dieser Stunde", "trifft zu", "eher zu", "eher nicht", "nicht zu", "Notiz"]):
        c.text = ""; r = c.paragraphs[0].add_run(k); r.bold = True; r.font.size = Pt(7.5); schatten(c, HELL)
    for bereich, merkmale in UB_BBS:
        z = t.add_row().cells; m = z[0]
        for c in z[1:]: m = m.merge(c)
        m.text = ""; r = m.paragraphs[0].add_run(bereich); r.bold = True; r.font.size = Pt(8); schatten(m, "F2F2F2")
        for nr, text in merkmale:
            z = t.add_row().cells
            for c, v in zip(z, [str(nr), text, bezug.get(nr, ""), "☐", "☐", "☐", "☐", ""]):
                c.text = ""; c.paragraphs[0].add_run(v).font.size = Pt(8)
    for i, w in enumerate([0.7, 4.6, 4.3, 1.0, 1.0, 1.0, 1.0, 2.4]):
        t.columns[i].width = Cm(w)
        for c in t.columns[i].cells: c.width = Cm(w)
    q = d.add_paragraph("Leer lassen = keine Einschätzung. Merkmale nach " + UB_QUELLE); q.runs[0].font.size = Pt(7.5)
    q.paragraph_format.line_spacing = 1.0
    d.add_heading("Meine Beobachtungspunkte für die Nachbesprechung", 2)
    q = d.add_paragraph("Drei bis vier Punkte für die Karten: grün = gelungen, gelb = Beratungsbedarf."); q.runs[0].font.size = Pt(9)
    q.paragraph_format.line_spacing = 1.0
    tabelle(d, ["Karte", "Beobachtungspunkt (mit Zeitpunkt oder Situation)"], [[f"{i}  ☐ grün  ☐ gelb", "\n"] for i in range(1, 5)],
            [3.4, 12.6], groesse=9)


def sequenzierung(d, s, ls):
    """Wie die freigegebene Fassung (LS 3, DS 7; Profil form.sequenzierung = hoch_getauscht): Kopf mit Titel,
    Kernkompetenz, Handlungssituation und Handlungsergebnis, darunter je Doppelstunde eine Zeile mit den Zeilen der
    Seminar-Vorlage als Spalten; Kompetenzen als Verben, Besuchsstunde markiert, Hinweis auf steigende Komplexität."""
    bs = s["besuch"]
    d.add_heading("Sequenzierung der Lernsituation", 1)
    tabelle(d, None, [["Titel der Lernsituation", ls["titel"]], ["Kernkompetenz", ls["kernkompetenz"]],
                      ["Handlungssituation", ls["handlungssituation"]], ["Handlungsergebnis", ls["handlungsergebnis"]]],
            [3.6, 12.4], groesse=8.5)
    zeilen = []
    for q in bs["sequenz"]:
        zeilen.append([q["std"] + ("\nBesuch" if q.get("besuch") else ""), q["thema"], q["inhalte"], q["methoden"], q["medien"],
                       q["kompetenzen"], q["zyklus"]])
    tabelle(d, ["Stunde", "Thema der Stunde", "Inhalte", "Methoden / Aktions- und Sozial\u00adformen", "Medien", "Kompetenzen",
                "Zyklische Voll\u00adständigkeit"],
            zeilen, [1.6, 2.3, 2.9, 2.3, 2.2, 2.6, 2.1], groesse=8,
            faerben=lambda z: "FBE2D5" if "Besuch" in z[0] else None)
    q = d.paragraphs[-1]; r = q.add_run("Steigende Komplexität von oben nach unten."); r.italic = True; r.font.size = Pt(8)


def kub_protokoll(s, ls, k):
    """Seminarvorlage „Protokoll eines kollegialen Unterrichtsbesuches“ (Quellen/Seminar_Downloads/KUB_Protokoll.pdf),
    Kopfdaten aus dem Entwurf vorbefüllt, Reflexion, Beratung und Zielvereinbarungen leer."""
    db = s["besuch"].get("deckblatt", {})
    d = neu()
    p = d.add_paragraph(SEMINAR["name"] + "\n" + SEMINAR["anschrift"])
    p.paragraph_format.line_spacing = 1.0; p.runs[0].font.size = Pt(9)
    d.add_heading("Protokoll eines kollegialen Unterrichtsbesuches", 1)
    tabelle(d, None, [["Lehrkraft im Vorbereitungsdienst (LiV)", db.get("liv", "[Name, Vorname]")],
                      ["Referendar-Gruppe", db.get("gruppe", "[XXX]")], ["Datum, Zeitraum", db.get("tag", "[Datum]") + ", " + db.get("zeit", f"[Zeit], {s['dauer']} Minuten")],
                      ["Ausbildungsschule", db.get("ort", "[Schule]")], ["Schulform", db.get("schulform", "Berufsschule")],
                      ["Klasse", f"{k['klasse']}, {k['bildungsgang']}"], ["Lernfeld/Fach", db.get("lernfeld", ls["lernfeld"])],
                      ["Thema", s["titel"]], ["Fachleiter/in", db.get("fachleitung", "[Name]")],
                      ["Ausbildungslehrer/in", db.get("fachlehrer", "[Name]")],
                      ["Besucher/innen (LiV)", db.get("teilnehmende", "[Namen]")]], [5.5, 10.5], groesse=10)
    for ueber, zeilen in (("Unterrichtsreflexion durch die unterrichtende LiV", 8), ("Wesentliche Inhalte des Beratungsgespräches", 10),
                          ("Zielvereinbarungen", 5)):
        d.add_heading(ueber, 2)
        for _ in range(zeilen): d.add_paragraph("_" * 66).paragraph_format.line_spacing = 1.5
    d.add_heading("Unterschriften", 2)
    d.add_paragraph("\n__________________________          __________________________\nLiV                                                           Besucher/innen")
    q = d.add_paragraph("Nach der Vorlage des Seminars (Download-Bereich). Wesentliches darf als Foto ergänzt werden; die Zielvereinbarung "
                        "geht in die Dokumentation der Ausbildung."); q.runs[0].font.size = Pt(8.5); q.runs[0].italic = True
    einzeilig(d)
    return d


def kurzentwurf(ab, s, ls, k, befunde):
    """Kurzentwurf (EUB, KUB, FLB)."""
    bs = s["besuch"]; art = bs["art"]
    d = neu()
    deckblatt(d, s, ls, k); seite(d)
    d.add_heading("Kernkompetenz der Unterrichtsstunde", 1)
    p = d.add_paragraph(bs["kernkompetenz"]); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    d.add_heading(f"Teilkompetenzen der Unterrichtsstunde ({s['dauer']} min)", 1)
    tabelle(d, ["Qualifikationsebene\nKompetenz = angestrebter Zielzustand", "Schnittstelle",
                "Handlungsebene\nHandlung, durch welche die angestrebte Kompetenz beobachtbar wird (Performanz)"],
            [[f"{x['nr']}: {x['kompetenz'].rstrip(', ')} ({', '.join(bereiche(x))})", "indem sie", x["indem"]] for x in bs["tk"]],
            [6.9, 2.1, 7.0], groesse=9.5)
    genutzt = []
    for x in bs["tk"]:
        for b in bereiche(x):
            if b not in genutzt: genutzt.append(b)
    q = d.add_paragraph(" · ".join(f"{b} {BEREICHE[b]}" for b in genutzt) + " · TK Teilkompetenz")
    q.runs[0].font.size = Pt(8.5)
    if bs.get("sachinformation"):
        d.add_heading("Sachinformation", 1)
        for x in bs["sachinformation"]:
            p = d.add_paragraph(x); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    seite(d); verlaufsskizze(d, s)
    seite(d); sequenzierung(d, s, ls)
    d.add_heading("Vereinbarte Ziele (Dokumentation der Ausbildung)", 1)
    if bs.get("ziele"):
        for z in bs["ziele"]: d.add_paragraph(z, style="List Bullet")
    else:
        d.add_paragraph("Erster Unterrichtsbesuch in der beruflichen Fachrichtung: noch keine Zielvereinbarungen.")
    if bs.get("sonderpaedagogik"):
        d.add_heading("Sonderpädagogische Konzeption", 1)
        for x in bs["sonderpaedagogik"]: d.add_paragraph(x)
    if bs.get("beobachtung"):
        beobachtungsbogen(d, s, bs["beobachtung"])
    # Anhang in der Reihenfolge des Leitfadens: Literatur, Sitzplan, Arbeitsblätter, Erwartungshorizont
    seite(d); d.add_heading("Anhang", 1)
    d.add_heading("Literaturverzeichnis", 2)
    for x in sorted(bs["literatur"]):
        p = d.add_paragraph(x); p.paragraph_format.left_indent = Cm(1); p.paragraph_format.first_line_indent = Cm(-1)
    seite(d); d.add_heading("Kommentierter Sitzplan", 2)
    sitzplan_inhalt(d, k, 16.0, (1.3, 1.8, 3.2, 9.7), bild=ab / k["ordner"] / "Sitzplan.png")
    seite(d); d.add_heading("Didaktisches Material", 2)
    fertig = anlagen_dateien(ab, s)
    d.add_paragraph("Die Arbeitsblätter liegen als Anlagen bei (Erstellung nach dem Materialauftrag):")
    tabelle(d, ["Anlage", "Titel", "Einsatz", "Stand"],
            [[zeichen(x), x["titel"], x["felder"][0][1], "beigefügt" if zeichen(x) in fertig else "folgt"] for x in s["anlagen"]],
            [1.5, 4.8, 7.9, 1.8], groesse=9)
    fehlen = [zeichen(x) for x in s["anlagen"] if zeichen(x) not in fertig]
    if fehlen:
        befunde.append(["Hinweis", "Material aus Pipeline 2 fehlt noch: " + ", ".join(fehlen) +
                        f" (Ablage: {s['ordner']}/Anlagen/, Arbeitsblaetter.docx bzw. Anl_<nr>_<titel>.docx); der Entwurf hängt es beim nächsten Erzeugen an"])
    einzeilig(d)
    schluss = neu()
    schluss.add_heading("Erwartungshorizont", 2)
    tabelle(schluss, ["Anlage", "Erwartete Ergebnisse"], [[f"{zeichen(x)} {x['titel']}", x["erwartungshorizont"]] for x in s["anlagen"]],
            [4.0, 12.0], groesse=9)
    seite(schluss); schluss.add_heading("Dienstliche Versicherung", 2)
    p = schluss.add_paragraph(SEMINAR["versicherung"]); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    schluss.add_paragraph(); schluss.add_paragraph("__________________________          __________________________")
    schluss.add_paragraph("Ort, Datum                                                 Unterschrift")
    schluss.add_heading("Übersicht verwendeter Hilfsmittel (KI)", 2)
    tabelle(schluss, None, bs.get("ki_verzeichnis") or [["Werkzeug", "[Name, Version, Anbieter, URL]"],
                                                        ["Art der Verwendung", "[eintragen]"], ["Prompts", "[Dokumentation liegt bei]"]],
            [4.0, 12.0], groesse=9.5)
    if not bs.get("ki_verzeichnis"):
        befunde.append(["Hinweis", "Übersicht der KI-Hilfsmittel nur mit Platzhaltern (Feld ki_verzeichnis)"])
    einzeilig(schluss)
    # Anhang-Reihenfolge des Leitfadens: Material (Pipeline 2) vor dem Erwartungshorizont, Versicherung am Schluss
    seite(d)
    c = Composer(d)
    for datei in dict.fromkeys(fertig.values()):       # Arbeitsblaetter.docx nur einmal anhängen
        teil = Document(datei); teil.add_section(WD_SECTION.NEW_PAGE); c.append(teil)
    c.append(schluss)
    ziel = ab / s["ordner"] / f"Entwurf_{art}.docx"; ziel.parent.mkdir(parents=True, exist_ok=True); c.save(ziel)
    return ziel


def erzeugen(ab, kurz):
    ab = pathlib.Path(ab)
    s = json.loads((ab / ".daten" / "stunde" / f"{kurz}.json").read_text(encoding="utf-8"))
    ls = json.loads((ab / ".daten" / "lernsituation" / f"{s['ls']}.json").read_text(encoding="utf-8"))
    k = json.loads((ab / ".daten" / "klasse" / f"{s['klasse']}.json").read_text(encoding="utf-8"))
    bs = s["besuch"]; art = bs["art"]
    sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "profil"))
    import profil as profilmod
    PROFIL.clear(); PROFIL.update(profilmod.lade(ab))
    seminar_laden(PROFIL)
    befunde = pruefen(s, ls, k, ab)
    if art in VOLL:
        import voll
        ziel = voll.erzeugen(ab, s, ls, k, befunde)
    else:
        ziel = kurzentwurf(ab, s, ls, k, befunde)
    rel = str(ziel.relative_to(ab))
    if art == "KUB":
        kub_protokoll(s, ls, k).save(ab / s["ordner"] / "KUB_Protokoll.docx")
    pb = neu(); pb.add_heading(f"Prüfbericht zum Entwurf {art} (nicht abgeben)", 1)
    tabelle(pb, ["Stufe", "Befund"], befunde + bs.get("pruefbericht", []), [2.6, 13.4], faerben=lambda z: STUFE[z[0]]); einzeilig(pb)
    pb.save(ab / s["ordner"] / f"Pruefbericht_Entwurf_{art}.docx")
    sbmod.schreiben(ab, rel, "stunde", f"LS {ls['nr']} DS {s['ds']} Entwurf {art}",
                    [ls["ordner"] + "/Lernsituation.docx", ls["ordner"] + "/Fehlvorstellungen.docx", k["ordner"] + "/Sitzplan.docx"],
                    ls["fach"], f"Entwurf {art}", s)
    return ziel, befunde


if __name__ == "__main__":
    z, b = erzeugen(sys.argv[1], sys.argv[2]); print(z); [print(*x) for x in b]
