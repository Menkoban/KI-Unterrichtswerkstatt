"""Schritte 13 und 14 einer Alltagsstunde: Verlaufsskizze und Materialauftrag aus Daten im Arbeitsbereich.

    python stunde/stunde.py <arbeitsbereich> <kurzname>

Daten:    <arbeitsbereich>/.daten/stunde/<kurzname>.json; die Lernsituation steht in
          .daten/lernsituation/<ls>.json (Feld "ls").
Ergebnis: <ordner>/Verlaufsskizze.docx und <ordner>/Materialauftrag.docx, je mit Steckbrief.
Prüft selbst: Zeiten lückenlos von 0 bis zur Dauer, jede Anlage der Verlaufsskizze hat einen
Steckbrief im Materialauftrag und umgekehrt, jede Anlage mit den Pflichtfeldern (Zweck, Inhalt und Wortlaut,
Aufbau und Layout, Hilfen, Moodle, Quellen, Abnahmekriterien) und Erwartungshorizont oder dem Vermerk,
dass keiner nötig ist, Doppelstunde und Phasen passen zur Lernsituation, Annahmen offen genannt,
wenn keine Klassen-Akte vorliegt. Geplant wird ohne Kalender; das Datum kommt bei der zeitlichen
Zuordnung in den Ordnernamen (KONZEPT 5b)."""
import datetime as dt, json, pathlib, re, sys
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "lernsituation"))
from ls_ausarbeitung import STUFE, schatten, tabelle
sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "akten"))
import steckbrief as sbmod

HELL, BAND = "D6ECEA", "4F9A94"


PFLICHTFELDER = ["Zweck, Phase, TK", "Inhalt und Wortlaut", "Aufbau und Layout", "Hilfen", "Moodle",
                 "Werkzeug (Vorschlag)", "Quellen", "Abnahmekriterien"]


# Bestand vor der Niveau-Entscheidung (Lehrkraft 2026-10-13: Beginner, Könner, Experte gestrichen, ein Niveau)
ALT = {"Niveaus und Hilfen": "Hilfen"}


# Problemorientierter Einstieg (Lehrkraft 2026-10-13): Formulierungen, die Methode oder Lösungsweg vorgeben
VORWEG = {r"gegeben\s*:": "gegeben", r"gesucht\s*:": "gesucht", r"rechnerisch und messtechnisch": "rechnerisch und messtechnisch",
          r"berechnen Sie zuerst": "berechnen Sie zuerst", r"gehen Sie so vor": "gehen Sie so vor"}


def minuten(z):
    a, b = (int(x) for x in re.findall(r"\d+", z)[:2])
    return a, b



def zeichen(x):
    """Kurzzeichen: „AB 2“ für Arbeitsblätter (Profil material.arbeitsblaetter_fortlaufend, Feld art), sonst „Anl. 3“."""
    return f"AB {x['nr']}" if x.get("art") == "Arbeitsblatt" else f"Anl. {x['nr']}"


def dateiname(x):
    """Arbeitsblätter stehen fortlaufend in einem Dokument (wie ein Fachbuch), Anlagen je eine Datei."""
    if x.get("art") == "Arbeitsblatt":
        return "Arbeitsblaetter.docx"
    return f"Anl_{x['nr']}_{x.get('kurz', re.sub(r'[^A-Za-z0-9]+', '_', x['titel'])[:30])}.docx"

NIVEAUWOERTER = r"\b(Beginner\w*|Könner\w*|Expert\w*|drei Fassungen|drei Stufen|Stufenband|Niveaustufe\w*)"
GEDANKENSTRICH = r"\s[–—]\s|—"


def profil_befunde(s, profil):
    """Steckbriefe und Verlauf gegen das Lehrkraft-Profil prüfen (Korrektur 2026-10-23: Fehler fielen erst beim
    Materialbau auf). Zeitspannen wie „0–5 min“ sind Bis-Striche und bleiben erlaubt."""
    b = []
    stellen = [(zeichen(x), k, v) for x in s["anlagen"] for k, v in x["felder"] + [["Titel", x["titel"]]]]
    stellen += [(f"Verlauf {z.get('zeit', '')}", "Aktivitäten", " ".join(z.get("aktivitaeten", [])))
                for z in s.get("vorlauf", []) + s["verlauf"]]
    if profil.get("form.keine_gedankenstriche"):
        for wo, feld, text in stellen:
            if feld in ("Inhalt und Wortlaut", "Titel") and re.search(GEDANKENSTRICH, text):
                b.append(["Warnung", f"{wo}, {feld}: Gedankenstrich im Wortlaut (Profil form.keine_gedankenstriche)"])
    if profil.get("material.ein_niveau"):
        for wo, feld, text in stellen:
            treffer = sorted(set(m.group(1) for m in re.finditer(NIVEAUWOERTER, text)))
            if treffer:
                b.append(["Warnung", f"{wo}, {feld}: Niveaustufen ({', '.join(treffer)}); Profil material.ein_niveau: "
                                     "ein Blatt für alle, Stützen als Hilfekarte, Erweiterung als Zusatz für Schnelle"])
    if profil.get("material.beamer_zeigt_arbeitsblatt"):
        for x in s["anlagen"]:
            if x.get("art") != "Arbeitsblatt" and re.search(r"Tafelbild|Tafeltabelle|Tafelfassung|Abstimmungsfolie", x["titel"]):
                b.append(["Warnung", f"{zeichen(x)} „{x['titel']}“: wiederholt vermutlich das Arbeitsblatt; Profil "
                                     "material.beamer_zeigt_arbeitsblatt: nur Neues als Folie (z. B. Strichliste)"])
    if profil.get("hausaufgaben") == "keine":
        for wo, feld, text in stellen:
            if re.search(r"(?<!keine )(?<!ohne )Hausaufgabe", text):
                b.append(["Fehler", f"{wo}, {feld}: Hausaufgabe geplant; Profil hausaufgaben: keine"])
    praxis = re.compile(r"\bmessen\b|Messplatz|Messplätze|Übungsplatz|Station|aufbau|Versuch", re.I)
    ruesten = re.compile(r"Einweis|Aufbau|Abbau|aufbau|abbau|vorbereitet|Rüst", re.I)
    zeilen = s.get("vorlauf", []) + s["verlauf"]
    texte = [" ".join(z.get("aktivitaeten", []) + z.get("medien", [])) + " " + z.get("phase", "") for z in zeilen]
    # Labor- und Rüstprüfung gehört zum Fachpaket Elektrotechnik (Profil fach.elektrotechnik, Veröffentlichung 2026-11)
    if profil.get("fach.elektrotechnik") and any(praxis.search(t) for t in texte) \
            and not any(ruesten.search(t) for t in texte):
        b.append(["Warnung", "Verlauf: praktische Phase ohne Einweisung, Aufbau oder Abbau; Rüstzeiten mitplanen "
                             "(ARBEITSWEISE, Lehrkraft 2026-10-25)"])
    if profil.get("methoden.vielfalt") == "gering" and s.get("typ", "Alltagsstunde") == "Alltagsstunde":
        aufwendig = re.compile(r"Gruppenpuzzle|Experten|Rotation|Kreuz|Galerie|Stationen|Fishbowl|Placemat|Kugellager", re.I)
        for z in zeilen:
            t = " ".join(z.get("aktivitaeten", []) + z.get("sozial", []))
            if aufwendig.search(t):
                b.append(["Warnung", f"Verlauf {z.get('zeit', '')}: aufwendige Methode; Profil methoden.vielfalt gering: "
                                     "einfache, wiederkehrende Sozialformen"])
    if profil.get("material.schriftliche_hilfen") is False:
        for x in s["anlagen"]:
            if re.search(r"Hilfekarte|Hilfskarte|Tippkarte", x["titel"]):
                b.append(["Warnung", f"{zeichen(x)} „{x['titel']}“: schriftliche Hilfe geplant; Profil "
                                     "material.schriftliche_hilfen aus: Hilfe persönlich, Impulse im Erwartungshorizont"])
    if profil.get("material.wortspeicher_als_anlage") is False:
        for x in s["anlagen"]:
            if re.search(r"Wortspeicher|Wortliste|Glossar", x["titel"]):
                b.append(["Warnung", f"{zeichen(x)} „{x['titel']}“: Wortspeicher als Anlage geplant; Profil "
                                     "material.wortspeicher_als_anlage aus: Fachwörter nur als Glossar in Moodle"])
    if profil.get("lernsituation.sicherung_merkkasten") == "tafel_ende_ds" and s.get("arbeitsplan") \
            and not any("Sicherung" in z.get("phase", "") for z in zeilen):
        b.append(["Warnung", "Kurzskizze ohne Phase „Sicherung der Merkkästen“ (Profil lernsituation.sicherung_merkkasten: "
                             "an der Tafel am Ende der DS, etwa 5 min)"])
    if profil.get("material.sprachaufnahmen") == "vermeiden":
        for wo, feld, text in stellen:
            if re.search(r"\b(Audio\w*|Sprachaufnahme\w*|Sprachnachricht\w*|Hördatei\w*)", text):
                b.append(["Warnung", f"{wo}, {feld}: Sprachaufnahme geplant (Profil material.sprachaufnahmen: vermeiden)"])
    return b


def pruefen(s, ls):
    b = []
    bestand = s.get("datum", "") < "2026-10-13"  # vor der Leitlinie freigegeben: nur Hinweis
    t = 0
    for z in s["verlauf"]:
        a, e = minuten(z["zeit"])
        if a != t:
            b.append(["Fehler", f"Lücke oder Überschneidung vor „{z['phase']}“ ({t} → {a} min)"])
        t = e
    r = s.get("reserve") or {}
    if re.match(r"\d+\s*–\s*\d+", r.get("zeit", "")):           # Reserve mit festen Minuten (Profil-Zeitbudget)
        ra, re_ = minuten(r["zeit"])
        if ra != t:
            b.append(["Fehler", f"Lücke oder Überschneidung vor der didaktischen Reserve ({t} → {ra} min)"])
        t = re_
    if t != s["dauer"]:
        b.append(["Fehler", f"Verlauf endet bei {t} min, die Stunde hat {s['dauer']} min"])
    if r and any("reserve" in z["phase"].lower() for z in s["verlauf"]):
        b.append(["Fehler", "Didaktische Reserve doppelt: als Phase im Verlauf und als eigener Block; nur einmal führen "
                            "(Block „reserve“ mit Minuten und Inhalten für Zeitnot und Zeitüberschuss)"])
    genannt = {f"{a} {n}" for z in s.get("vorlauf", []) + s["verlauf"] for m in z["medien"] for a, n in re.findall(r"(Anl\.|AB) (\d+)", m)}
    da = {zeichen(x) for x in s["anlagen"]} | set(s.get("_lernpfad", ()))  # Kurzskizze: Arbeitsblätter im Arbeitsplan
    if genannt - da:
        b.append(["Fehler", "Anlagen ohne Steckbrief: " + ", ".join(sorted(genannt - da))])
    if da - genannt and not s.get("arbeitsplan"):
        b.append(["Warnung", "Steckbriefe ohne Verwendung im Verlauf: " + ", ".join(sorted(da - genannt))])
    for x in s["anlagen"]:
        if not x.get("erwartungshorizont"):
            b.append(["Fehler", f"{zeichen(x)} ohne Erwartungshorizont (oder Vermerk „keiner nötig“)"])
        da_felder = {ALT.get(k, k) for k, v in x["felder"] if v.strip()}
        fehlen = [f for f in PFLICHTFELDER if f not in da_felder]
        if fehlen:
            b.append(["Fehler", f"{zeichen(x)}: Steckbrief unvollständig, es fehlt " + ", ".join(fehlen) +
                      " (Materialauftrag immer ausführlich, Lehrkraft 2026-10-12)"])
        moodle = dict(x["felder"]).get("Moodle", "").strip().lower()
        if moodle.startswith(("keine", "kein ", "entfällt", "nur papier")):
            b.append(["Fehler", f"{zeichen(x)}: ohne Moodle-Umsetzung; alles wird in den Moodle-Kurs überführt (Lehrkraft 2026-10-12)"])
        inhalt = dict(x["felder"]).get("Inhalt und Wortlaut", "")
        vorweg = [name for m, name in VORWEG.items() if re.search(m, inhalt, re.I)]
        if vorweg:
            b.append(["Hinweis" if bestand else "Warnung",
                      f"{zeichen(x)}: Auftrag nimmt vorweg ({', '.join(vorweg)}); "
                      "problemorientiert: offener Auftrag, Daten nur im Informationspool (Lehrkraft 2026-10-13)"])
        if inhalt and len(inhalt) < 250:
            b.append(["Warnung", f"{zeichen(x)}: Inhalt und Wortlaut sehr knapp ({len(inhalt)} Zeichen); Pipeline 2 braucht den Wortlaut"])
    if any(k in ALT for x in s["anlagen"] for k, _ in x["felder"]):
        b.append(["Hinweis", "Materialauftrag von vor der Niveau-Entscheidung (Feld „Niveaus und Hilfen“); neu gilt ein Niveau "
                             "mit dem Feld „Hilfen“ (Lehrkraft 2026-10-13)"])
    if not s.get("gestaltung") and not s.get("arbeitsplan"):
        b.append(["Fehler", "Gestaltungsvorgaben für alle Anlagen fehlen (Feld gestaltung)"])
    mit_moodle = [z.get("zeit", "?") for z in s["verlauf"] if "moodle" in json.dumps(z, ensure_ascii=False).lower()
                  and "abschlusstest" not in json.dumps(z, ensure_ascii=False).lower()]   # Abschlusstest im Kurs: Lehrkraft 2026-10-25
    if mit_moodle:
        b.append(["Warnung", "Verlauf plant Moodle ein (" + ", ".join(map(str, mit_moodle)) + "); die Stunde wird ohne Moodle "
                  "geplant, die Moodle-Umsetzung steht nur im Materialauftrag (Lehrkraft 2026-10-12)"])
    d = next((x for x in ls["doppelstunden"] if x["ds"] == s["ds"]), None)
    if not d:
        b.append(["Fehler", f"DS {s['ds']} gibt es in LS {ls['nr']} nicht"])
    else:
        ph = {p for z in s["verlauf"] for p in z.get("handlungsphase", "").replace(",", " ").split()}
        fehlt = [p for p in d["phasen"] if p not in ph]
        if fehlt:
            b.append(["Warnung", "Phasen der Doppelstunde nicht im Verlauf: " + ", ".join(fehlt)])
    if not s.get("klassen_akte") and not s.get("annahmen"):
        b.append(["Fehler", "Keine Klassen-Akte und keine Annahmen genannt"])
    return b


def neu(hoch=True):
    d = Document()
    sec = d.sections[0]
    if hoch:
        sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    else:
        sec.orientation = WD_ORIENT.LANDSCAPE; sec.page_width, sec.page_height = Cm(29.7), Cm(21)
    for x in ("left_margin", "right_margin", "top_margin", "bottom_margin"): setattr(sec, x, Cm(2.0))
    st = d.styles["Normal"]; st.font.name = "Arial"; st.font.size = Pt(10); st.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    for n in ("Title", "Heading 1", "Heading 2"):
        h = d.styles[n]; h.font.name = "Arial"; h.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)
    return d


def seminar_zeile(z, profil):
    """Verlaufszeile für die Seminarfassung (Profil form.seminar_zeiten, form.seminar_lernende_einzeln):
    ohne Minutenangabe und ohne Aktivitäten zu einzelnen Lernenden (Kürzel wie S12)."""
    if not profil:
        return z
    z = dict(z)
    if not profil.get("form.seminar_zeiten", True):
        z["zeit"] = ""
    if not profil.get("form.seminar_lernende_einzeln", True):
        z["aktivitaeten"] = [a for a in z["aktivitaeten"] if not re.search(r"\bS\d{2}\b", a)]
    return z


def verlaufsskizze(s, ls, befunde, seminar=None):
    """Interne Verlaufsskizze; mit seminar=<Profil> die Seminarfassung ohne Zeiten, Einzelhinweise und Prüfbericht."""
    d = neu(hoch=False)
    art = "Verlaufsplanung" if s.get("arbeitsplan") else "Verlaufsskizze"
    if s.get("arbeitsplan"):  # Kurzskizze: eine Seite für die Ausbildungslehrkraft
        for x in ("left_margin", "right_margin", "top_margin", "bottom_margin"): setattr(d.sections[0], x, Cm(1.4))
    d.add_heading(f"{art} LS {ls['nr']}, DS {s['ds']}: {s['titel']}", 0)
    p = d.add_paragraph(f"Stunden-Akte · Schritt 13 · {ls['lernfeld']} · LS {ls['nr']} „{ls['titel']}“ · "
                        f"{s['std_nr']} · {s['typ']} · {s['dauer']} min · Stand {s['datum']} · {s['stand']}")
    p.runs[0].italic = True
    tabelle(d, None, [["Leitfrage", s["leitfrage"]], ["Teilergebnis", s["teilergebnis"]],
                      ["Kompetenzen der Stunde", "\n".join(s["kompetenzen"])],
                      ["Fehlvorstellungen", "\n".join(s["fehlvorstellungen"])],
                      ["Annahmen zur Klasse", s.get("annahmen") or "siehe Klassen-Akte"]], [5.0, 20.7],
            **({"groesse": 8.5} if s.get("arbeitsplan") else {}))
    t = d.add_table(rows=1, cols=5); t.style = "Table Grid"; t.autofit = False
    kopf = ["Phase", "Lerninhalte", "Methodische Entscheidungen und Lehrer-/Schüleraktivitäten", "Aktions- und Sozialformen",
            "Materialien und Medien"]
    for c, k in zip(t.rows[0].cells, kopf):
        c.text = ""; r = c.paragraphs[0].add_run(k); r.bold = True; schatten(c, HELL)

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
    if s.get("vorlauf"):  # PU als zweite Stunde einer Doppelstunde: erste Stunde ohne Ausschuss vorweg
        band("Erste Stunde der Doppelstunde, ohne Prüfungsausschuss (nicht Gegenstand der Prüfung)")
        zeilen = s["vorlauf"] + [None] + zeilen
    else:
        band("Beginn der Doppelstunde")
    for z in zeilen:
        if z is None:
            band(f"Beginn der geprüften Stunde ({s['dauer']} min)"); continue
        r = t.add_row().cells
        z = seminar_zeile(z, seminar)
        kopfz = [f"**{z['phase']}**"] + ([f"({z['zeit']})"] if z.get("zeit") else []) \
            + ([z["handlungsphase"]] if z.get("handlungsphase") else []) + ([z["tk"]] if z.get("tk") else [])
        for c, inhalt in zip(r, (kopfz, z["inhalte"], z["aktivitaeten"], z["sozial"], z["medien"])):
            zelle(c, inhalt)
    band("Ende der Doppelstunde")
    for i, b in enumerate([3.2, 5.0, 9.6, 3.4, 4.5]):
        t.columns[i].width = Cm(b)
        for c in t.columns[i].cells: c.width = Cm(b)
    for row in t.rows:
        for c in row.cells:
            for q in c.paragraphs:
                for run in q.runs: run.font.size = Pt(8.5)
    if not s.get("arbeitsplan"):
        d.add_paragraph()
    a = d.add_paragraph()
    if s.get("arbeitsplan"):                                 # Kurzskizze: eine Seite, Zeile klein und ohne Abstand
        a.paragraph_format.space_before = a.paragraph_format.space_after = Pt(0)
        r = a.add_run("Material: "); r.bold = True; r.font.size = Pt(8.5)
        a.add_run("Lernpfad im Arbeitsplan der LS (Steckbriefe im Materialauftrag der LS)").font.size = Pt(8.5)
    else:
        a.add_run("Anlagen (Steckbriefe im Materialauftrag): ").bold = True
        a.add_run(" · ".join(f"{zeichen(x)} {x['titel']}" for x in s["anlagen"]))
    if seminar is None:
        d.add_heading("Prüfbericht", 1)
        tabelle(d, ["Stufe", "Befund"], befunde + s["pruefbericht"], [2.6, 23.1], faerben=lambda z: STUFE[z[0]])
    return d


def kurz(text, n=110):
    """Erster Satz eines Feldes für die Übersicht, höchstens n Zeichen."""
    satz = re.split(r"(?<=[.;])\s", text.strip(), maxsplit=1)[0].rstrip(";,")
    return satz if len(satz) <= n else satz[:n].rsplit(" ", 1)[0] + " …"


def materialauftrag(s, ls):
    d = neu(hoch=True)
    d.add_heading(f"Materialauftrag LS {ls['nr']}, DS {s['ds']}: {s['titel']}", 0)
    p = d.add_paragraph(f"Stunden-Akte · Schritt 14 · Material-Steckbriefe für Pipeline 2 · Stand {s['datum']} · {s['stand']}")
    p.runs[0].italic = True
    d.add_paragraph("Ausführlich nach Vorgabe der Lehrkraft: Pipeline 2 baut jede Anlage allein aus diesem Auftrag und fragt nur "
                    "Gestaltung und Lücken nach. Je Anlage: Zweck, Inhalt und Wortlaut, Aufbau und Layout, Hilfen, "
                    "Moodle, Werkzeug (Vorschlag), Quellen, Abnahmekriterien, Erwartungshorizont. Alles auf einem Niveau; Hilfen und Werkzeuge sind "
                    "Vorschläge, die Pipeline 2 mit der Lehrkraft abstimmt; alles wird in den Moodle-Kurs überführt.").runs[0].font.size = Pt(9)
    d.add_heading("Für alle Materialien gilt", 1)
    tabelle(d, None, s["material_allgemein"], [4.0, 13.0])
    if s.get("gestaltung"):
        d.add_heading("Gestaltungsvorgaben für alle Anlagen", 1)
        tabelle(d, None, s["gestaltung"], [4.0, 13.0])
    d.add_heading("Übersicht der Anlagen", 1)
    d.add_paragraph("Die Stunde ist ohne Moodle geplant. Je Anlage steht hier, wie sie als Material und wie sie im "
                    "Moodle-Kurs umgesetzt wird; die Einzelheiten stehen in den Feldern „Werkzeug (Vorschlag)“ und „Moodle“."
                    ).runs[0].font.size = Pt(9)
    tabelle(d, ["Nr.", "Titel", "Umsetzung als Material", "Umsetzung in Moodle", "Dateiname (Ordner Anlagen/)"],
            [[zeichen(x), x["titel"], kurz(dict(x["felder"]).get("Werkzeug (Vorschlag)", "")),
              kurz(dict(x["felder"]).get("Moodle", "")),
              dateiname(x)] for x in s["anlagen"]],
            [0.9, 3.6, 4.4, 4.4, 3.7], groesse=8)
    for x in s["anlagen"]:
        d.add_heading(f"{zeichen(x)} · {x['titel']}", 1)
        felder = sorted(x["felder"], key=lambda f: PFLICHTFELDER.index(ALT.get(f[0], f[0])) if ALT.get(f[0], f[0]) in PFLICHTFELDER else 99)
        tabelle(d, None, [[k, v] for k, v in felder] + [["Erwartungshorizont", x["erwartungshorizont"]]], [4.0, 13.0])
    return d


def erzeugen(ab, kurz):
    ab = pathlib.Path(ab)
    s = json.loads((ab / ".daten" / "stunde" / f"{kurz}.json").read_text(encoding="utf-8"))
    ls = json.loads((ab / ".daten" / "lernsituation" / f"{s['ls']}.json").read_text(encoding="utf-8"))
    sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "profil"))
    import profil as profilmod
    profil = profilmod.lade(ab)
    if s.get("arbeitsplan"):  # Kurzskizze einer selbstständigen LS (Profil lernsituation.planungstiefe)
        sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "lernsituation"))
        import arbeitsplan as apmod
        s["_lernpfad"] = sorted(apmod.ab_nummern(ab, s["arbeitsplan"]))
    befunde = pruefen(s, ls) + profil_befunde(s, profil)
    if profil.get("moodle.im_unterricht") == "arbeitsort":          # Kurs ist Arbeitsort (Lehrkraft 2026-10-25)
        befunde = [x for x in befunde if not x[1].startswith("Verlauf plant Moodle ein")]
    letzte = max(int(x["ds"]) for x in ls["doppelstunden"])
    if profil.get("moodle.abschlusstest_zeitpunkt") == "ende_letzte_ds" and int(s["ds"]) == letzte \
            and "Besuch" not in s.get("typ", "") and not any("Abschlusstest" in z.get("phase", "") for z in s["verlauf"]):
        befunde.append(["Warnung", "letzte DS der LS ohne Phase „Abschlusstest“ (Profil moodle.abschlusstest_zeitpunkt: "
                                   "letzte 25 min der letzten DS)"])
    ordner = ab / s["ordner"]; ordner.mkdir(parents=True, exist_ok=True)
    baut = [ls["ordner"] + "/Lernsituation.docx", ls["ordner"] + "/Fehlvorstellungen.docx"]
    ziele = []
    dokumente = [("Verlaufsskizze.docx", verlaufsskizze(s, ls, befunde), "Schritt 13")]
    if not s.get("arbeitsplan"):  # Kurzskizze: Steckbriefe stehen im Materialauftrag der LS
        dokumente.append(("Materialauftrag.docx", materialauftrag(s, ls), "Schritt 14"))
    if not (profil.get("form.seminar_zeiten", True) and profil.get("form.seminar_lernende_einzeln", True)):
        dokumente.insert(1, ("Verlaufsskizze_Seminar.docx", verlaufsskizze(s, ls, befunde, seminar=profil), "Schritt 13"))
    for name, dok, schritt in dokumente:
        z = ordner / name; dok.save(z); ziele.append(z)
        sbmod.schreiben(ab, str(z.relative_to(ab)), "stunde", f"LS {ls['nr']} DS {s['ds']} {name[:-5]}", baut, ls["fach"], schritt,
                        {k: v for k, v in s.items() if not k.startswith("_")})
    return ziele, befunde


if __name__ == "__main__":
    z, b = erzeugen(sys.argv[1], sys.argv[2]); [print(x) for x in z]; [print(*x) for x in b]
