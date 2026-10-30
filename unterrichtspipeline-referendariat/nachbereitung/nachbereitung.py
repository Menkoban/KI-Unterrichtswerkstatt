"""Schritt 17 Nachbereitung: frei gesprochene Aussagen nach Reichweite ablegen (KONZEPT „Schritt 17 Nachbereitung“).

    python nachbereitung/nachbereitung.py <arbeitsbereich> <kurz der stunde>
    python nachbereitung/nachbereitung.py <arbeitsbereich> --offen [--ls <ls>] [--klasse <klasse>]

Daten:    <arbeitsbereich>/.daten/nachbereitung/<kurz der stunde>.json mit "stunde" (Kurzname der Stunden-Akte),
          "datum", "stand", "rohtext" (wörtlich, was die Lehrkraft gesagt hat) und "aussagen": je Aussage "text",
          "ablage" (stunde, klasse, lernsituation, profil), "status" (offen, erledigt), optional "betrifft"
          (z. B. „DS 2“, „S06“) und bei profil ein "muster" (Stichwort für gleichartige Beobachtungen).
Ergebnis: Nachbereitung.docx im Stundenordner mit Steckbrief; mit --offen die offenen Punkte für den Block
„Aus der letzten Nachbereitung“ einer neuen Stundenplanung (Klasse und Lernsituation).
Profil-Regel: eine einzelne Stunde ändert das Profil nie; erst wenn dasselbe Muster in zwei oder mehr
Nachbereitungen vorkommt, meldet der Prüfbericht einen Vorschlag; die Lehrkraft entscheidet."""
import json, pathlib, re, sys
from collections import defaultdict
from docx import Document
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HIER = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent / "lernsituation"))
from ls_ausarbeitung import STUFE, tabelle
sys.path.insert(0, str(HIER.parent / "akten"))
import steckbrief as sbmod

ABLAGEN = {"stunde": "Stunden-Akte (was tatsächlich geschah)",
           "klasse": "Klassen-Akte (Beobachtungen zur Klasse und zu Lernenden)",
           "lernsituation": "Lernsituations-Akte (Änderungen an Material, Zeiten, Aufgaben, Ablauf)",
           "profil": "Lehrkraft-Profil (nur wiederkehrende Muster)"}


def lade_alle(ab):
    ordner = pathlib.Path(ab) / ".daten" / "nachbereitung"
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(ordner.glob("*.json"))] if ordner.exists() else []


def stunde_von(ab, kurz):
    return json.loads((pathlib.Path(ab) / ".daten" / "stunde" / f"{kurz}.json").read_text(encoding="utf-8"))


def pruefen(ab, n, s):
    b = []
    if not n.get("aussagen"):
        b.append(["Fehler", "Keine Aussagen; die Nachbereitung zerlegt das Gesagte in einzelne Aussagen"])
    for i, a in enumerate(n.get("aussagen", []), 1):
        if a.get("ablage") not in ABLAGEN:
            b.append(["Fehler", f"Aussage {i}: Ablage „{a.get('ablage')}“ unbekannt ({', '.join(ABLAGEN)})"])
        if a.get("status", "offen") not in ("offen", "erledigt"):
            b.append(["Fehler", f"Aussage {i}: Status nur offen oder erledigt"])
        if a.get("ablage") == "profil" and not a.get("muster"):
            b.append(["Warnung", f"Aussage {i}: Profil-Beobachtung ohne Stichwort „muster“; Wiederholungen werden nicht erkannt"])
    if re.search(r"\b(?:Herr|Frau)\s+[A-ZÄÖÜ]", n.get("rohtext", "")) and "Terhorst" not in n.get("rohtext", ""):
        b.append(["Warnung", "Im Rohtext steht vermutlich ein echter Name; Lernende nur als Kürzel (S01 …)"])
    # Profil-Regel über alle Nachbereitungen
    zaehl = defaultdict(set)
    for m in lade_alle(ab):
        for a in m.get("aussagen", []):
            if a.get("ablage") == "profil" and a.get("muster"):
                zaehl[a["muster"]].add(m["stunde"])
    for a in n.get("aussagen", []):
        if a.get("ablage") == "profil" and a.get("muster"):
            k = len(zaehl[a["muster"]] | {n["stunde"]})
            b.append(["Hinweis" if k < 2 else "Warnung",
                      f"Profil-Muster „{a['muster']}“: {k}-mal beobachtet" +
                      (" (noch keine Profiländerung)" if k < 2 else "; Vorschlag zur Profiländerung an die Lehrkraft")])
    b.append(["Hinweis", f"Stunde {s['titel']} ({s.get('typ', 'Alltagsstunde')}); "
                         f"{sum(1 for a in n.get('aussagen', []) if a.get('status', 'offen') == 'offen')} offene Punkte"])
    return b


def offen(ab, ls=None, klasse=None):
    """Offene Punkte für „Aus der letzten Nachbereitung“: Klassen-Akte derselben Klasse, Lernsituations-Akte
    derselben LS (auch aus anderen Klassen, für den nächsten Durchgang)."""
    punkte = []
    for n in lade_alle(ab):
        try:
            s = stunde_von(ab, n["stunde"])
        except FileNotFoundError:
            continue
        for a in n.get("aussagen", []):
            if a.get("status", "offen") != "offen":
                continue
            if (a["ablage"] == "klasse" and klasse and s.get("klasse") == klasse) or \
               (a["ablage"] == "lernsituation" and ls and s["ls"] == ls):
                punkte.append({"aus": f"{n['stunde']} ({n.get('datum', '')})", "ablage": a["ablage"],
                               "betrifft": a.get("betrifft", ""), "text": a["text"]})
    return punkte


def dokument(n, s, befunde):
    d = Document(); sec = d.sections[0]; sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    for x in ("left_margin", "right_margin", "top_margin", "bottom_margin"): setattr(sec, x, Cm(2.0))
    st = d.styles["Normal"]; st.font.name = "Arial"; st.font.size = Pt(10); st.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    for h in ("Title", "Heading 1"):
        d.styles[h].font.name = "Arial"; d.styles[h].font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)
    d.add_heading(f"Nachbereitung: {s['titel']}", 0)
    p = d.add_paragraph(f"Stunden-Akte · Schritt 17 · {s.get('typ', 'Alltagsstunde')} · {s.get('klasse', '')} · "
                        f"Stand {n.get('datum', '')} · {n.get('stand', 'Entwurf')}"); p.runs[0].italic = True
    for ab_key, name in ABLAGEN.items():
        zeilen = [[a.get("betrifft", ""), a["text"], a.get("status", "offen")] for a in n["aussagen"] if a["ablage"] == ab_key]
        if zeilen:
            d.add_heading(name, 1)
            tabelle(d, ["Betrifft", "Aussage", "Status"], zeilen, [2.6, 12.0, 2.4])
    if n.get("rohtext"):
        d.add_heading("Wortlaut der Lehrkraft", 1)
        q = d.add_paragraph(n["rohtext"]); q.runs[0].font.size = Pt(9)
    d.add_heading("Prüfbericht", 1)
    tabelle(d, ["Stufe", "Befund"], befunde, [2.6, 14.4], faerben=lambda z: STUFE[z[0]])
    return d


def erzeugen(ab, kurz):
    ab = pathlib.Path(ab)
    n = json.loads((ab / ".daten" / "nachbereitung" / f"{kurz}.json").read_text(encoding="utf-8"))
    s = stunde_von(ab, n["stunde"])
    befunde = pruefen(ab, n, s)
    ziel = ab / s["ordner"] / "Nachbereitung.docx"; ziel.parent.mkdir(parents=True, exist_ok=True)
    dokument(n, s, befunde).save(ziel)
    rel = str(ziel.relative_to(ab))
    sbmod.schreiben(ab, rel, "stunde", f"Nachbereitung {s['titel'][:50]}", [s["ordner"] + "/Verlaufsskizze.docx"],
                    "Elektrotechnik", "Schritt 17", n)
    return ziel, befunde


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 2 and a[1] == "--offen":
        opt = dict(zip(a[2::2], a[3::2]))
        for x in offen(a[0], opt.get("--ls"), opt.get("--klasse")):
            print(f"[{x['ablage']}] {x['betrifft']}: {x['text']} (aus {x['aus']})")
    elif len(a) == 2:
        z, b = erzeugen(a[0], a[1]); print(z); [print(*x) for x in b]
    else:
        print(__doc__)
