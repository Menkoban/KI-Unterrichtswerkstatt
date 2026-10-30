"""Differenzierte Aufgaben in drei Stufen je Kachel (KONZEPT 2026-11, Prototyp zur Entscheidung der Lehrkraft).

In jeder Kachel steht der gemeinsame Teil für alle (Auftrag, Infoseite), dann die **Aufgaben in drei Stufen**
Grundlagen, Standard, Vertiefung: gleiches Lernziel, anderes Gerüst und andere Schwierigkeit, Aufgabenformen nach
dem Thema (berechnet, Zuordnen, Auswahl, Lückentext, Reihenfolge …). **Jede Lernende sieht nur ihre eigene Stufe**;
die anderen sind ganz verborgen (die Lehrkraft kann einzeln freigeben). Regeln (fest):

- Start auf `start` (Vorgabe Standard). Die Stufe wandert mit: jede Kachel beginnt auf der Stufe, auf der die vorige
  endete.
- Nach einer Kachel entscheidet der **Durchschnitt aller Aufgaben ihrer Stufe (erster Versuch)**: ab 85 % eine Stufe
  höher, 50 bis 84 % bleibt, unter 50 % eine tiefer (Grenzen `kurs.stufen_grenzen`, Vorgabe [50, 85]); auf
  Grundlagen kein Abstieg, auf Vertiefung kein Aufstieg. Solange nicht alle Aufgaben bewertet sind, bleibt die Stufe.
  Eine Kachel ohne Stufen-Platzhalter ändert die Stufe nicht.
- Umsetzung nur mit Moodle-Kern: je Kachel und Stufe eine **verborgene berechnete Bewertung** „Mittelwert“ (Gewicht 0)
  und Voraussetzungen „Bewertung“ darauf; die Aufgaben sind Tests mit Bewertungsmethode „erster Versuch“.

Kennzeichnung (Bildsprache „Schalen“: ein Kern mit einer, zwei oder drei Elektronenschalen; Form und Text tragen die
Stufe, nicht nur die Farbe): (a) „Mein Stufenweg“ in Allgemein (stufenweg.js, Verlauf mit Aufstieg/Abstieg und
Rückmeldekarten; Karten als Option), (b) oben in der Kachel eine Zeile „Stufe: …“ mit Zeichen (nach Aufstieg bzw.
Bleiben ein kleiner Zusatz, nach Abstieg keiner). Unter den Aufgaben kein Zeichen (Lehrkraft 2026-11).

**Platzhalter** in den Aktivitäten einer Kachel (Kursdefinition); `einsetzen` ersetzt ihn:

    {"typ": "stufen", "kachel": 1, "titel": "Wie wird aus Temperatur eine Spannung?",
     "start": "Standard",                     # optional, nur der erste Platzhalter
     "aufgaben": {"Grundlagen": [{"thema": "Teilspannungen", "fragen": […], …Testfelder}, …],
                  "Standard": […], "Vertiefung": […]}}      # je Stufe 1 bis 6 Aufgaben

Daraus entstehen: oben in der Kachel die Stufenkästen (Textfelder, je Stufe und Übergang einer), an der Stelle des
Platzhalters je Stufe die Aufgaben (Tests, ein Schritt je Aufgabe), dazu je Stufe eine
berechnete Bewertung. ID-Nummern `stufe-k<n>-<g|s|v>-<i>` (Aufgaben), `stufe-k<n>-<g|s|v>-mittel`,
`stufe-k<n>-<g|s|v>-kopf-<start|auf|ab|bleibt>`. `kursdef["stufen"]` hält je Kachel die
Namen der Aufgaben und ihre Themen (für stufenweg.js).

    stufen.einsetzen(kursdef)              # in place, idempotent; True, wenn etwas eingesetzt wurde
    stufen.dateien_anlegen(wurzel)         # Stufenzeichen (SVG) unter wurzel/stufen/
    stufen.weg_aktivitaet(kursdef, "verlauf" | "karten")   # „Mein Stufenweg“ (Datenbank mit Skript)
"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import inseln
from inseln import FALSCH, WAHR, nicht, oder, und
from xmlhilfe import x

STUFEN = inseln.STUFEN
KURZ = inseln.KURZ
GRENZEN = (50, 85)
START = "Standard"
FARBEN = ("#08349C", "#7DDE78")
ORDNER = "stufen"
JS_DATEI = Path(__file__).with_name("stufenweg.js")
KONFIG = re.compile(r"/\*KONFIG\*/(.*?)/\*/KONFIG\*/", re.S)
TINTE = "#14213D"


# --------------------------------------------------------------------------------------------------------------- #
# Regel (Referenz für Tests und stufenweg.js)
# --------------------------------------------------------------------------------------------------------------- #
def endstufe(einstieg: str, prozent: float | None, grenzen=GRENZEN) -> str:
    return inseln.endstufe(einstieg, prozent, grenzen)


def mittel(werte: list) -> float | None:
    """Durchschnitt der Aufgaben einer Stufe; None, solange eine Aufgabe ohne Bewertung ist."""
    if not werte or any(w is None for w in werte):
        return None
    return sum(werte) / len(werte)


def pfad(start: str, kacheln: list[list], grenzen=GRENZEN) -> list[tuple[str, str, float | None]]:
    """(Einstieg, Ende, Durchschnitt) je Kachel aus den Ergebnissen der Aufgaben der Einstiegsstufe in %."""
    aus, e = [], start
    for werte in kacheln:
        m = mittel(werte)
        ende = endstufe(e, m, grenzen)
        aus.append((e, ende, m))
        e = ende
    return aus


# --------------------------------------------------------------------------------------------------------------- #
# Bedingungen: Ausdrücke wie inseln.py, dazu ("calc", idnummer, min, max) für berechnete Bewertungen
# --------------------------------------------------------------------------------------------------------------- #
def note(kennung: str, lo=None, hi=None) -> tuple:
    return ("note", kennung, lo, hi)


def calc(idnummer: str, lo=None, hi=None) -> tuple:
    return ("calc", idnummer, lo, hi)


def bedingung(a: tuple, sichtbar: bool | None = None) -> dict:
    """Ausdruck → Bedingung der Kursdefinition. Verneinung einer UND-Gruppe wird „nicht alle“ (Moodle !&)."""
    art = a[0]
    if art in ("note", "calc"):
        _, k, lo, hi = a
        b = {"aktivitaet": k} if art == "note" else {"bewertung": k}
        if lo is None and hi is None:
            b["bewertet"] = True
        if lo is not None:
            b["min"] = lo
        if hi is not None:
            b["max"] = hi
    elif art == "nicht":
        innen = a[1][1] if a[1][0] == "und" else [a[1]]
        b = {"nicht": [bedingung(t) for t in innen]}
    elif art in ("und", "oder"):
        b = {art: [bedingung(t) for t in a[1]]}
    else:
        raise ValueError(f"kein Bedingungsausdruck: {a!r}")
    if sichtbar is not None:
        b["sichtbar_wenn_gesperrt"] = sichtbar
    return b


def bedingungen(a: tuple, sichtbar: bool = False) -> list[dict]:
    if a == WAHR:
        return []
    if a[0] == "und":
        return [bedingung(t, sichtbar) for t in a[1]]
    return [bedingung(a, sichtbar)]


def auswerten(a: tuple, noten: dict) -> bool:
    """Ausdruck mit Noten in % auswerten ({Kennung oder idnummer: Prozent}, fehlt = ohne Bewertung); für Tests."""
    art = a[0]
    if art == "wahr":
        return True
    if art == "falsch":
        return False
    if art in ("note", "calc"):
        _, k, lo, hi = a
        w = noten.get(k)
        if w is None:
            return False
        return (lo is None or w >= lo) and (hi is None or w < hi)
    if art == "nicht":
        return not auswerten(a[1], noten)
    if art == "und":
        return all(auswerten(t, noten) for t in a[1])
    if art == "oder":
        return any(auswerten(t, noten) for t in a[1])
    raise ValueError(a)


def logik(kacheln: list[dict], start: str = START, grenzen=GRENZEN) -> list[dict]:
    """Je Kachel {"E": {Stufe: Ausdruck}, "X": {…}} aus {"aufgaben": {Stufe: [Kennung]}, "mittel": {Stufe: idnummer}}.
    E = Kachel beginnt auf der Stufe, X = Kachel endet auf der Stufe. Bewertet sein können nur die Aufgaben der
    Einstiegsstufe (die anderen sind verborgen); darum genügt je Stufe „alle bewertet ∧ Mittelwert im Bereich“."""
    lo, hi = grenzen
    e = {s: (WAHR if s == start else FALSCH) for s in STUFEN}
    aus = []
    for k in kacheln:
        def fertig(s, k=k):
            return und(*[note(q) for q in k["aufgaben"][s]])

        def ab(s, mn=None, mx=None, e=e, k=k):
            return FALSCH if e[s] == FALSCH else und(fertig(s), calc(k["mittel"][s], mn, mx))

        def offen(s, e=e):
            return FALSCH if e[s] == FALSCH else und(nicht(fertig(s)), e[s])
        G, S, V = STUFEN
        x_ = {V: oder(ab(S, hi), ab(V, lo), offen(V)),
              S: oder(ab(G, hi), ab(S, lo, hi), ab(V, None, lo), offen(S)),
              G: oder(ab(G, None, hi), ab(S, None, lo), offen(G))}
        aus.append({"E": e, "X": x_})
        e = x_
    return aus


# --------------------------------------------------------------------------------------------------------------- #
# Bildsprache: Stufenzeichen „Schalen“ (Kern mit 1, 2, 3 Schalen und je einem Elektron)
# --------------------------------------------------------------------------------------------------------------- #
WINKEL = (-35, 205, 95)       # Lage der Elektronen auf Schale 1, 2, 3 (Grad)


def zeichen_svg(stufe: str, farben=FARBEN, groesse: int = 48) -> str:
    """Stufenzeichen als eigenständige SVG-Datei: Grundlagen eine, Standard zwei, Vertiefung drei Schalen; die
    Vertiefung zusätzlich auf dunklem Grund. Titel als Textalternative."""
    import math
    blau, gruen = (tuple(farben) + FARBEN)[:2]
    n = STUFEN.index(stufe) + 1
    dunkel = n == 3
    grund = blau if dunkel else ("#E8F8E7" if n == 1 else "#E6EDFA")
    linie = "#FFFFFF" if dunkel else blau
    kern = gruen if dunkel else blau
    teile = [f'<rect x="1" y="1" width="46" height="46" rx="13" fill="{grund}"'
             + ("" if dunkel else f' stroke="{blau}" stroke-opacity=".25" stroke-width="1.5"') + "/>",
             f'<circle cx="24" cy="24" r="4.6" fill="{kern}"/>']
    for i in range(n):
        r = 9 + 5.6 * i if n == 3 else 10 + 6.5 * i
        teile.append(f'<circle cx="24" cy="24" r="{r:.1f}" fill="none" stroke="{linie}" stroke-width="2.2"/>')
        w = math.radians(WINKEL[i])
        teile.append(f'<circle cx="{24 + r * math.cos(w):.2f}" cy="{24 + r * math.sin(w):.2f}" r="3.1" '
                     f'fill="{gruen}" stroke="{blau if not dunkel else "#FFFFFF"}" stroke-width="1.4"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="{groesse}" height="{groesse}" '
            f'role="img" aria-label="Stufe {stufe}"><title>Stufe {stufe}</title>' + "".join(teile) + "</svg>\n")


def datei(stufe: str) -> str:
    return f"{ORDNER}/stufe_{stufe.lower()}.svg"


def dateien_anlegen(wurzel: Path, farben=FARBEN) -> list[str]:
    aus = []
    for s in STUFEN:
        p = Path(wurzel) / datei(s)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(zeichen_svg(s, farben), encoding="utf-8")
        aus.append(datei(s))
    return aus


def _img(stufe: str, px: int) -> str:
    return (f'<img src="{Path(datei(stufe)).name}" alt="Zeichen der Stufe {stufe}" width="{px}" height="{px}" '
            f'style="vertical-align:middle;margin-right:10px">')


# --------------------------------------------------------------------------------------------------------------- #
# Text oben in der Kachel
# --------------------------------------------------------------------------------------------------------------- #
#: Kasten oben in der Kachel in einer Zeile: Zeichen + „Stufe: …“ (Lehrkraft 2026-11, Bild „Wie suchen wir den Fehler?“).
#: Nach einem Aufstieg bzw. beim Bleiben ein kleiner, ruhiger Zusatz in derselben Zeile; nach einem Abstieg keiner.
#: Kein Untertext mit Grenzen in Prozent, keine Zeile „Ihre Aufgaben“, kein Zeichen unter den Aufgaben; die Regel
#: steht in „Mein Stufenweg“ und in der Handreichung.
ZUSATZ = {"start": None, "auf": "▲ aufgestiegen", "ab": None, "bleibt": "auf Kurs"}


def kopf_text(stufe: str, uebergang: str, farben=FARBEN) -> str:
    """Stufe oben in der Kachel, eine Zeile: Zeichen, „Stufe: Grundlagen“, ggf. kleiner Zusatz (Text, nicht nur Farbe)."""
    blau = (tuple(farben) + FARBEN)[0]
    zusatz = ""
    if ZUSATZ[uebergang]:
        zusatz = (f'<span style="font-size:.85em;color:#4A5878;margin-left:12px;vertical-align:middle">'
                  f"{x(ZUSATZ[uebergang])}</span>")
    return (f'<p style="margin:0 0 6px 0;font-size:16px;color:{TINTE};border:1.5px solid {blau};border-radius:12px;'
            f'padding:6px 12px;background:#F5F8FF">{_img(stufe, 34)}'
            f'<strong style="font-size:1.15em;color:{blau};vertical-align:middle">Stufe: {x(stufe)}</strong>'
            f"{zusatz}</p>")


# --------------------------------------------------------------------------------------------------------------- #
# Einsetzen
# --------------------------------------------------------------------------------------------------------------- #
def ist_platzhalter(akt: dict) -> bool:
    return isinstance(akt, dict) and akt.get("typ") == "stufen"


def platzhalter(kursdef: dict) -> list[dict]:
    return [a for ab in kursdef.get("abschnitte", []) for a in ab.get("aktivitaeten", []) if ist_platzhalter(a)]


def grenzen_von(kursdef: dict) -> tuple:
    return tuple((kursdef.get("kurs") or {}).get("stufen_grenzen") or GRENZEN)


def pruefe_platzhalter(kursdef: dict) -> list[str]:
    f = []
    nummern = []
    for i, p in enumerate(platzhalter(kursdef)):
        wo = f"Stufen Kachel {p.get('kachel', '?')}"
        nummern.append(p.get("kachel"))
        if not isinstance(p.get("kachel"), int) or p["kachel"] < 1:
            f.append(f"{wo}: kachel muss eine ganze Zahl ≥ 1 sein")
        if p.get("start") is not None and (i > 0 or p["start"] not in STUFEN):
            f.append(f"{wo}: start nur am ersten Platzhalter und nur {', '.join(STUFEN)}")
        aufg = p.get("aufgaben") or {}
        if set(aufg) != set(STUFEN):
            f.append(f"{wo}: aufgaben braucht genau {', '.join(STUFEN)}")
            continue
        for s in STUFEN:
            if not 1 <= len(aufg[s]) <= 6:
                f.append(f"{wo} / {s}: 1 bis 6 Aufgaben")
            for j, a in enumerate(aufg[s], start=1):
                if not a.get("fragen"):
                    f.append(f"{wo} / {s} / Aufgabe {j}: fragen fehlen")
                if not str(a.get("thema") or "").strip():
                    f.append(f"{wo} / {s} / Aufgabe {j}: thema fehlt (Rückmeldung „Stark bei …“)")
    if nummern != sorted(nummern) or len(set(nummern)) != len(nummern):
        f.append(f"Stufen: Kacheln {nummern} müssen aufsteigen und eindeutig sein")
    return f


def _kennung(n: int, s: str, i: int) -> str:
    return f"Stufe K{n} {s} {i}"


def _mittel_id(n: int, s: str) -> str:
    return f"stufe-k{n}-{KURZ[s]}-mittel"


def einsetzen(kursdef: dict) -> bool:
    ps = platzhalter(kursdef)
    if not ps:
        return False
    fehler = pruefe_platzhalter(kursdef)
    if fehler:
        raise ValueError("Stufen ungültig:\n- " + "\n- ".join(fehler))
    farben = tuple((kursdef.get("kurs") or {}).get("schulfarben") or FARBEN)
    grenzen = grenzen_von(kursdef)
    start = ps[0].get("start") or START
    spec = [{"aufgaben": {s: [_kennung(p["kachel"], s, i) for i in range(1, len(p["aufgaben"][s]) + 1)]
                          for s in STUFEN},
             "mittel": {s: _mittel_id(p["kachel"], s) for s in STUFEN}} for p in ps]
    lg = logik(spec, start, grenzen)
    liste, bewertungen = [], kursdef.setdefault("bewertungen", [])
    je_platz = {id(p): i for i, p in enumerate(ps)}
    for ab in kursdef.get("abschnitte", []):
        oben, neu = [], []
        for a in ab.get("aktivitaeten", []):
            if id(a) not in je_platz:
                neu.append(a)
                continue
            i = je_platz[id(a)]
            n = a["kachel"]
            E = lg[i]["E"]
            vorher = lg[i - 1]["E"] if i > 0 else None
            # (b) Kasten oben in der Kachel: je Stufe und Übergang (gegenüber der Einstiegsstufe der vorigen Kachel)
            for s in STUFEN:
                if E[s] == FALSCH:
                    continue
                if vorher is None:
                    varianten = [("start", WAHR)]
                else:
                    j = STUFEN.index(s)
                    varianten = [("auf", vorher[STUFEN[j - 1]] if j > 0 else FALSCH),
                                 ("ab", vorher[STUFEN[j + 1]] if j < 2 else FALSCH),
                                 ("bleibt", vorher[s])]
                for art, vor in varianten:
                    ausdruck = und(E[s], vor)
                    if ausdruck == FALSCH:
                        continue
                    k = f"Stufe K{n} {s}: Kopf {art}"
                    oben.append({"typ": "label", "name": k, "kennung": k, "schritt": False,
                                 "idnummer": f"stufe-k{n}-{KURZ[s]}-kopf-{art}",
                                 "text": kopf_text(s, art, farben), "dateien": [datei(s)],
                                 "stufe": {"kachel": n, "stufe": s, "rolle": "kopf", "uebergang": art},
                                 **({"voraussetzung": bedingungen(ausdruck)} if ausdruck != WAHR else {})})
            eintrag = {"kachel": n, "titel": a.get("titel") or ab.get("name", ""), "aufgaben": {}}
            for s in STUFEN:
                aufg = a["aufgaben"][s]
                bed = [] if E[s] == WAHR else bedingungen(E[s]) if E[s] != FALSCH else None
                gruppe = []
                eintrag["aufgaben"][s] = []
                for j, t in enumerate(aufg, start=1):
                    q = copy.deepcopy(t)
                    thema = q.pop("thema")
                    q.update(typ="quiz", kennung=_kennung(n, s, j), idnummer=f"stufe-k{n}-{KURZ[s]}-{j}",
                             bewertungsmethode="erste", versuche=int(t.get("versuche", 0)))
                    q.setdefault("name", f"Aufgabe {n}.{j} · {thema}")
                    q.setdefault("punkte", 10)
                    q["stufe"] = {"kachel": n, "stufe": s, "rolle": "aufgabe", "thema": thema}
                    gruppe.append(q)
                    eintrag["aufgaben"][s].append({"kennung": q["kennung"], "name": q["name"], "thema": thema})
                for g in gruppe:
                    if bed is None:
                        g["sichtbar"] = False        # erreicht in dieser Kachel niemand (erste Kachel)
                    elif bed:
                        g["voraussetzung"] = copy.deepcopy(bed)
                neu += gruppe
                ids = "+".join(f"[[stufe-k{n}-{KURZ[s]}-{j}]]" for j in range(1, len(aufg) + 1))
                if not any(b.get("idnummer") == _mittel_id(n, s) for b in bewertungen):
                    bewertungen.append({"typ": "berechnet", "name": f"Kachel {n} · {s}: Mittelwert",
                                        "idnummer": _mittel_id(n, s), "max": 100, "verborgen": True,
                                        "im_kursgesamt": False,
                                        # jede Aufgabe hat 10 Punkte: Summe / Anzahl · 10 = Mittelwert in %
                                        "formel": f"=({ids})/{len(aufg)}*10"})
            liste.append(eintrag)
        ab["aktivitaeten"] = oben + neu
    kursdef["stufen"] = liste
    kursdef.setdefault("kurs", {})["stufen_start"] = start
    return True


# --------------------------------------------------------------------------------------------------------------- #
# „Mein Stufenweg“ in Allgemein: Datenbank ohne Einträge mit Skript (wie lernpfad.py)
# --------------------------------------------------------------------------------------------------------------- #
#: Standard ist der Verlauf (Lehrkraft 2026-11, Prototyp); die Karten bleiben als Option
DARSTELLUNGEN = {"verlauf": "Mein Stufenweg", "karten": "Mein Stufenweg (Karten)"}


def konfig(kursdef: dict, darstellung: str) -> dict:
    liste = kursdef.get("stufen") or []
    if not liste:
        raise ValueError("„Mein Stufenweg“ braucht Stufen-Aufgaben (kursdef['stufen'], stufen.einsetzen)")
    farben = list((tuple((kursdef.get("kurs") or {}).get("schulfarben") or FARBEN) + FARBEN)[:2])
    return {"darstellung": darstellung, "farben": farben, "grenzen": list(grenzen_von(kursdef)),
            "start": (kursdef.get("kurs") or {}).get("stufen_start") or START, "stufen": list(STUFEN),
            "kacheln": [{"nr": k["kachel"], "titel": re.sub(r"^\d+\s*·\s*", "", k["titel"]),
                         "aufgaben": [[{"name": a["name"], "thema": a["thema"]} for a in k["aufgaben"][s]]
                                      for s in STUFEN]} for k in liste]}


def skript(k: dict) -> str:
    quelle = JS_DATEI.read_text(encoding="utf-8")
    if not KONFIG.search(quelle):
        raise ValueError("stufenweg.js: Markierung /*KONFIG*/ … /*/KONFIG*/ fehlt")
    return KONFIG.sub(lambda _: "/*KONFIG*/" + json.dumps(k, ensure_ascii=False, indent=8) + "/*/KONFIG*/",
                      quelle, count=1)


def weg_aktivitaet(kursdef: dict, darstellung: str = "verlauf") -> dict:
    """Die Datenbank-Aktivität „Mein Stufenweg“ in einer der beiden Darstellungen (allgemein_aktivitaeten)."""
    k = konfig(kursdef, darstellung)
    blau, gruen = k["farben"]
    css = (f".sw {{ --sw-blau:{blau}; --sw-gruen:{gruen}; }}\n"
           '[data-region="empty-message"] { display:none !important; }\n')
    name = DARSTELLUNGEN[darstellung]
    return {"typ": "data", "name": name, "kennung": name, "idnummer": f"stufenweg-{darstellung}",
            "abschluss": "keine", "nur_lesen": True, "beschreibung": "",
            "felder": [{"name": "Hinweis", "typ": "text", "beschreibung": "wird nicht benutzt"}],
            "vorlagen": {"listtemplateheader": "", "listtemplate": "", "listtemplatefooter": "",
                         "singletemplate": "", "addtemplate": "<p>Hier werden keine Einträge angelegt.</p>",
                         "csstemplate": css, "jstemplate": skript(k)}}
