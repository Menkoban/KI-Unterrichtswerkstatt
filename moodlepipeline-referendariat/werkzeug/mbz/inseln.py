"""Individueller Lernpfad mit Übungsinseln (KONZEPT 2026-10-28).

Eine **Übungsinsel** steht in einer Kachel dort, wo eine Fähigkeit gebraucht wird, und hat drei Stufen
„Grundlagen“, „Standard“, „Vertiefung“, je mit einer **Übung** (Test, beliebig viele Versuche) und einem
**Kurztest** (3 bis 4 berechnete Fragen, ein Versuch). Inseln zählen nicht für Sterne und Medaillen und ändern den
Stern „selbst gelöst“ nicht. Regeln (fest):

- Die erste Insel beginnt für alle auf `start` (Vorgabe „Standard“). **Die Stufe wandert mit:** jede weitere Insel
  beginnt auf der Stufe, auf der die vorige endete.
- **Wechsel nach dem Kurztest der Einstiegsstufe:** ab 85 % eine Stufe höher, 50 bis 84 % bleibt, unter 50 % eine
  tiefer (Grenzen `kurs.insel_grenzen`, Vorgabe [50, 85]); auf Grundlagen kein Abstieg, auf Vertiefung kein Aufstieg.
  Höchstens ein Wechsel je Insel: nur der Kurztest der Einstiegsstufe ist offen. Ohne Kurztest bleibt die Stufe.
- **Nach unten offen, nach oben verdienen:** die Übungen unter der Einstiegsstufe sind offen; die Stufe darüber öffnet
  sich erst mit dem Kurztest ab 85 %. Die aktuelle Stufe ist hervorgehoben (Textfeld „Ihre Stufe: …“, nur für die
  Person sichtbar, deren Stufe es ist; kein Plugin, nur Moodle-Voraussetzungen).

**Platzhalter** in den Aktivitäten einer Kachel (Kursdefinition); `einsetzen` ersetzt ihn durch die Aktivitäten:

    {"typ": "insel", "nr": 1, "name": "Insel 1: Heizmatte (P, I, R)",
     "voraussetzung": [{"abschluss": "Schritt 2.2 · …", "zustand": "abgeschlossen"}],   # optional, ganze Insel
     "start": "Standard",                    # optional, nur die erste Insel
     "text": "<p>…</p>",                     # optional, Text im Inselkopf (Vorgabe: die Regel in zwei Sätzen)
     "stufen": {"Grundlagen": {"uebung": {Test}, "kurztest": {Test}},
                "Standard":   {"uebung": {…},   "kurztest": {…}},
                "Vertiefung": {"uebung": {…},   "kurztest": {…}}}}

Ein {Test} hat die Felder eines Tests (quiz: fragen, beschreibung, verhalten, …); Name, Kennung, ID-Nummer, Sterne
(0), Versuche (Übung 0 = beliebig, Kurztest 1) und Voraussetzungen setzt `einsetzen`. Daraus entstehen je Insel in
dieser Reihenfolge: Inselkopf (Textfeld, ein Schritt der Kachel), dann je Stufe Grundlagen, Standard, Vertiefung das
Textfeld „Ihre Stufe“, die Übung und der Kurztest (eingerückt, ohne eigenen Schritt). ID-Nummern
`insel-<n>-kopf`, `insel-<n>-<g|s|v>-empfehlung|uebung|kurztest`; jede erzeugte Aktivität trägt `insel` =
{"nr", "stufe", "rolle"}. `kursdef["inseln"]` hält die Kennungen je Insel (für „Mein Lernpfad“ und Prüfer 14).

Bedingungen (alle zusätzlich zur Inselvoraussetzung, gesperrt verborgen): E(n, s) = „Insel n beginnt auf s“,
X(n, s) = „Insel n endet auf s“, E(n + 1, s) = X(n, s), mit KT(n, s) = Kurztest der Stufe s:

    X(n, V) = KT(n, S) ≥ 85 ∨ KT(n, V) ≥ 50 ∨ (KT(n, V) ohne Note ∧ E(n, V))
    X(n, S) = KT(n, G) ≥ 85 ∨ 50 ≤ KT(n, S) < 85 ∨ KT(n, V) < 50 ∨ (KT(n, S) ohne Note ∧ E(n, S))
    X(n, G) = KT(n, G) < 85 ∨ KT(n, S) < 50 ∨ (KT(n, G) ohne Note ∧ E(n, G))
    Übung G: offen · Übung S: E(n, S) ∨ E(n, V) ∨ KT(n, G) ≥ 85 · Übung V: E(n, V) ∨ KT(n, S) ≥ 85
    Kurztest s: E(n, s) ∧ Übung s bewertet (ausgegraut sichtbar, bis die Übung einen Versuch hat)
    Ihre Stufe s: X(n, s)

Moodle-Bedingung „Bewertung“: min heißt „mindestens“, max „kleiner als“ (availability_grade); ohne min und max „hat
eine Bewertung“; Verneinung über eine Untergruppe „nicht“. Eine Stufe, die in der ersten Insel niemand erreicht
(Kurztest Grundlagen und Vertiefung bei Start Standard), bleibt einzeln verborgen.

    inseln.einsetzen(kursdef)          # in place, idempotent; True, wenn etwas eingesetzt wurde
    inseln.pfad("Standard", [90, None])  # [("Standard", "Vertiefung"), ("Vertiefung", "Vertiefung")]
"""
from __future__ import annotations

import copy
import re

from xmlhilfe import x

STUFEN = ("Grundlagen", "Standard", "Vertiefung")
KURZ = {"Grundlagen": "g", "Standard": "s", "Vertiefung": "v"}
GRENZEN = (50, 85)
START = "Standard"
ROLLEN = ("kopf", "empfehlung", "uebung", "kurztest")
IDNUMMER = re.compile(r"^insel-(\d+)-(?:kopf|([gsv])-(empfehlung|uebung|kurztest))$")
FARBE = "#08349C"


# --------------------------------------------------------------------------------------------------------------- #
# Regel (Referenz für Prüfer, Tests und das Skript lernpfad.js)
# --------------------------------------------------------------------------------------------------------------- #
def endstufe(einstieg: str, prozent: float | None, grenzen=GRENZEN) -> str:
    """Stufe nach dem Kurztest der Einstiegsstufe (ohne Kurztest: die Einstiegsstufe)."""
    i = STUFEN.index(einstieg)
    if prozent is None:
        return einstieg
    if prozent >= grenzen[1]:
        return STUFEN[min(i + 1, 2)]
    if prozent < grenzen[0]:
        return STUFEN[max(i - 1, 0)]
    return einstieg


def pfad(start: str, ergebnisse: list, grenzen=GRENZEN) -> list[tuple[str, str]]:
    """(Einstieg, Ende) je Insel aus den Kurztest-Ergebnissen in % (None = kein Kurztest)."""
    aus, e = [], start
    for p in ergebnisse:
        x_ = endstufe(e, p, grenzen)
        aus.append((e, x_))
        e = x_
    return aus


# --------------------------------------------------------------------------------------------------------------- #
# Bedingungen als kleine Ausdrücke: ("wahr",), ("falsch",), ("note", kennung, min, max), ("und", […]),
# ("oder", […]), ("nicht", a); vereinfacht beim Bilden
# --------------------------------------------------------------------------------------------------------------- #
WAHR, FALSCH = ("wahr",), ("falsch",)


def note(kennung: str, lo=None, hi=None) -> tuple:
    return ("note", kennung, lo, hi)


def und(*teile) -> tuple:
    flach = []
    for t in teile:
        if t == FALSCH:
            return FALSCH
        if t == WAHR:
            continue
        flach += t[1] if t[0] == "und" else [t]
    return WAHR if not flach else flach[0] if len(flach) == 1 else ("und", flach)


def oder(*teile) -> tuple:
    flach = []
    for t in teile:
        if t == WAHR:
            return WAHR
        if t == FALSCH:
            continue
        flach += t[1] if t[0] == "oder" else [t]
    return FALSCH if not flach else flach[0] if len(flach) == 1 else ("oder", flach)


def nicht(a: tuple) -> tuple:
    if a == WAHR:
        return FALSCH
    if a == FALSCH:
        return WAHR
    return a[1] if a[0] == "nicht" else ("nicht", a)


def bedingung(a: tuple, sichtbar: bool | None = None) -> dict:
    """Ausdruck → Bedingung der Kursdefinition (kursdefinition.py: aktivitaet/min/max, bewertet, und, oder, nicht)."""
    if a[0] == "note":
        _, k, lo, hi = a
        b = {"aktivitaet": k}
        if lo is None and hi is None:
            b["bewertet"] = True
        if lo is not None:
            b["min"] = lo
        if hi is not None:
            b["max"] = hi
    elif a[0] == "nicht":
        b = {"nicht": [bedingung(a[1])]}
    elif a[0] in ("und", "oder"):
        b = {a[0]: [bedingung(t) for t in a[1]]}
    else:
        raise ValueError(f"kein Bedingungsausdruck: {a!r}")
    if sichtbar is not None:              # nur die oberste Ebene trägt es (Moodle: showc an der Wurzel)
        b["sichtbar_wenn_gesperrt"] = sichtbar
    return b


def bedingungen(a: tuple, sichtbar: bool = False) -> list[dict]:
    """Ausdruck als UND-Liste (oberste Ebene)."""
    if a == WAHR:
        return []
    if a[0] == "und":
        return [bedingung(t, sichtbar) for t in a[1]]
    return [bedingung(a, sichtbar)]


def logik(kurztests: list[dict], start: str = START, grenzen=GRENZEN) -> list[dict]:
    """Je Insel {"E": {Stufe: Ausdruck}, "X": {…}} aus den Kennungen der Kurztests [{Stufe: Kennung}]."""
    lo, hi = grenzen
    e = {s: (WAHR if s == start else FALSCH) for s in STUFEN}
    aus = []
    for kt in kurztests:
        def ab(s, mn=None, mx=None, e=e, kt=kt):
            return FALSCH if e[s] == FALSCH else note(kt[s], mn, mx)

        def ohne(s, e=e, kt=kt):
            return und(nicht(note(kt[s])), e[s]) if e[s] != FALSCH else FALSCH
        G, S, V = STUFEN
        x_ = {V: oder(ab(S, hi), ab(V, lo), ohne(V)),
              S: oder(ab(G, hi), ab(S, lo, hi), ab(V, None, lo), ohne(S)),
              G: oder(ab(G, None, hi), ab(S, None, lo), ohne(G))}
        aus.append({"E": e, "X": x_})
        e = x_
    return aus


# --------------------------------------------------------------------------------------------------------------- #
# Einsetzen
# --------------------------------------------------------------------------------------------------------------- #
def ist_platzhalter(akt: dict) -> bool:
    return isinstance(akt, dict) and akt.get("typ") == "insel"


def platzhalter(kursdef: dict) -> list[dict]:
    return [a for ab in kursdef.get("abschnitte", []) for a in ab.get("aktivitaeten", []) if ist_platzhalter(a)]


def grenzen_von(kursdef: dict) -> tuple:
    g = (kursdef.get("kurs") or {}).get("insel_grenzen") or GRENZEN
    return tuple(g)


def pruefe_platzhalter(kursdef: dict) -> list[str]:
    """Formfehler der Insel-Platzhalter (vor dem Einsetzen)."""
    f = []
    g = (kursdef.get("kurs") or {}).get("insel_grenzen")
    if g is not None and not (isinstance(g, list) and len(g) == 2 and all(isinstance(z, (int, float)) for z in g)
                              and 0 < g[0] < g[1] <= 100):
        f.append(f"kurs.insel_grenzen {g!r}: zwei Zahlen 0 < untere < obere ≤ 100")
    nummern = []
    for i, p in enumerate(platzhalter(kursdef)):
        wo = f"Insel {p.get('nr', '?')}"
        if not isinstance(p.get("nr"), int) or isinstance(p.get("nr"), bool) or p["nr"] < 1:
            f.append(f"{wo}: nr muss eine ganze Zahl ≥ 1 sein")
        nummern.append(p.get("nr"))
        if not str(p.get("name") or "").strip():
            f.append(f"{wo}: name fehlt")
        if p.get("start") is not None and (i > 0 or p["start"] not in STUFEN):
            f.append(f"{wo}: start nur an der ersten Insel und nur {', '.join(STUFEN)}")
        stufen = p.get("stufen") or {}
        if not isinstance(stufen, dict) or set(stufen) != set(STUFEN):
            f.append(f"{wo}: stufen braucht genau {', '.join(STUFEN)}")
            continue
        for s in STUFEN:
            for teil in ("uebung", "kurztest"):
                t = (stufen[s] or {}).get(teil)
                if not isinstance(t, dict) or not t.get("fragen"):
                    f.append(f"{wo} / {s}: {teil} fehlt oder hat keine fragen")
                elif teil == "kurztest" and not 3 <= len(t["fragen"]) <= 4:
                    f.append(f"{wo} / {s}: Kurztest mit {len(t['fragen'])} Fragen (3 bis 4)")
                elif t.get("sterne") or t.get("rolle"):
                    f.append(f"{wo} / {s}: {teil} ohne sterne und rolle (Inseln zählen nicht für Sterne)")
    if nummern != sorted(nummern) or len(set(nummern)) != len(nummern):
        f.append(f"Inseln: Nummern {nummern} müssen in Kursreihenfolge aufsteigen und eindeutig sein")
    return f


def _text_kopf(grenzen) -> str:
    lo, hi = (f"{z:g}" for z in grenzen)
    return ("<p>Drei Stufen: Grundlagen, Standard und Vertiefung. Ihre Stufe ist markiert. Üben Sie dort, so oft Sie "
            f"wollen, und schreiben Sie dann den Kurztest (ein Versuch): ab {hi} % geht es eine Stufe höher, unter "
            f"{lo} % eine tiefer. Die Stufen darunter sind immer offen. Ohne Sterne.</p>")


def _text_kurztest(s: str, grenzen) -> str:
    lo, hi = (f"{z:g}" for z in grenzen)
    i = STUFEN.index(s)
    teile = [f"ab {hi} % weiter auf {STUFEN[i + 1]}" if i < 2 else f"ab {lo} % bleiben Sie auf {s}",
             f"{lo} bis unter {hi} % bleiben Sie auf {s}" if i < 2 else None,
             f"unter {lo} % zurück auf {STUFEN[i - 1]}" if i > 0 else f"unter {hi} % bleiben Sie auf {s}"]
    return ("<p>Ein Versuch, ohne Sterne. Ihr Ergebnis bestimmt die Stufe der nächsten Insel: "
            + ", ".join(t for t in teile if t) + ".</p>")


TEXT_UEBUNG = "<p>Üben Sie, so oft Sie wollen; jeder Versuch bringt neue Werte. Ohne Sterne.</p>"


def label_text(akt: dict, farben=(FARBE,)) -> str:
    """Text der Textfelder einer Insel beim Bau (Name und Schulfarbe stehen dann fest): Inselkopf mit seinem Namen
    als Überschrift, „Ihre Stufe“ als hervorgehobener Kasten (Text, nicht nur Farbe)."""
    blau = (farben or (FARBE,))[0]
    rolle = (akt.get("insel") or {}).get("rolle")
    if rolle == "kopf":
        return f'<h4 style="color:{blau}">{x(akt["name"])}</h4>' + (akt.get("text") or "")
    if rolle == "empfehlung":
        s = akt["insel"]["stufe"]
        return (f'<div style="border-left:6px solid {blau};background:#EEF3FF;color:#14213D;padding:6px 12px;'
                f'border-radius:4px"><p style="margin:0"><strong>➜ Ihre Stufe: {x(s)}</strong> – hier üben Sie '
                f"weiter.</p></div>")
    return akt.get("text") or ""


def _aktivitaeten(p: dict, lg: dict, tor: list, grenzen) -> tuple[list[dict], dict]:
    nr = p["nr"]
    E, X = lg["E"], lg["X"]
    kopf_kennung = p.get("kennung") or p["name"]
    kopf = {"typ": "label", "name": p["name"], "kennung": kopf_kennung, "idnummer": f"insel-{nr}-kopf",
            "text": p.get("text") or _text_kopf(grenzen), "insel": {"nr": nr, "stufe": None, "rolle": "kopf"},
            "voraussetzung": copy.deepcopy(tor)}
    if "schritt" in p:
        kopf["schritt"] = p["schritt"]
    akts, kennungen = [kopf], {"kopf": kopf_kennung, "stufen": {}}
    _, hi = grenzen
    G, S, V = STUFEN
    def kt_ab(s):                              # Kurztest s ab der oberen Grenze (nur, wenn s Einstieg sein kann)
        return FALSCH if E[s] == FALSCH else note(_kt(nr, s), hi)
    offen_uebung = {G: WAHR, S: oder(E[S], E[V], kt_ab(G)), V: oder(E[V], kt_ab(S))}
    for s in STUFEN:
        k = KURZ[s]
        teile = p["stufen"][s]
        ue_k, kt_k, em_k = _ue(nr, s), _kt(nr, s), f"Insel {nr} · Ihre Stufe: {s}"
        gemeinsam = {"einzug": 1, "schritt": False}
        em = {"typ": "label", "name": em_k, "kennung": em_k, "idnummer": f"insel-{nr}-{k}-empfehlung", "text": "",
              "insel": {"nr": nr, "stufe": s, "rolle": "empfehlung"}, **gemeinsam}
        em["text"] = label_text(em)            # der Bau setzt ihn mit der Schulfarbe neu
        ue = {**copy.deepcopy(teile["uebung"]), "typ": "quiz", "name": teile["uebung"].get("name") or ue_k,
              "kennung": ue_k, "idnummer": f"insel-{nr}-{k}-uebung", "sterne": 0,
              "versuche": int(teile["uebung"].get("versuche", 0)),
              "insel": {"nr": nr, "stufe": s, "rolle": "uebung"}, **gemeinsam}
        ue.setdefault("beschreibung", TEXT_UEBUNG)
        kt = {**copy.deepcopy(teile["kurztest"]), "typ": "quiz", "name": teile["kurztest"].get("name") or kt_k,
              "kennung": kt_k, "idnummer": f"insel-{nr}-{k}-kurztest", "sterne": 0, "versuche": 1,
              "insel": {"nr": nr, "stufe": s, "rolle": "kurztest"}, **gemeinsam}
        kt.setdefault("beschreibung", _text_kurztest(s, grenzen))
        for a, ausdruck, extra in ((em, X[s], []), (ue, offen_uebung[s], []),
                                   (kt, E[s], [{"aktivitaet": ue_k, "bewertet": True,
                                                "sichtbar_wenn_gesperrt": True}])):
            a.pop("voraussetzung", None)
            if ausdruck == FALSCH:
                a["sichtbar"] = False          # erreicht in dieser Insel niemand (erste Insel)
                a["voraussetzung"] = copy.deepcopy(tor)
            else:
                # „Ihre Stufe“ ganz verborgen, solange die Insel zu ist (sonst stünde sie ausgegraut da)
                eigen_tor = ([dict(v, sichtbar_wenn_gesperrt=False) for v in tor] if a is em else copy.deepcopy(tor))
                a["voraussetzung"] = eigen_tor + bedingungen(ausdruck) + extra
            if not a["voraussetzung"]:
                del a["voraussetzung"]
        akts += [em, ue, kt]
        kennungen["stufen"][s] = {"empfehlung": em_k, "uebung": ue_k, "kurztest": kt_k}
    return akts, kennungen


def _ue(nr: int, s: str) -> str:
    return f"Insel {nr} · {s}: Üben"


def _kt(nr: int, s: str) -> str:
    return f"Insel {nr} · {s}: Kurztest"


def einsetzen(kursdef: dict) -> bool:
    """Insel-Platzhalter durch ihre Aktivitäten ersetzen (in place) und `kursdef["inseln"]` setzen. Ohne Platzhalter
    ändert sich nichts (False). Formfehler: ValueError."""
    ps = platzhalter(kursdef)
    if not ps:
        return False
    fehler = pruefe_platzhalter(kursdef)
    if fehler:
        raise ValueError("Inseln ungültig:\n- " + "\n- ".join(fehler))
    grenzen = grenzen_von(kursdef)
    start = ps[0].get("start") or START
    lg = logik([{s: _kt(p["nr"], s) for s in STUFEN} for p in ps], start, grenzen)
    je_platz = {id(p): i for i, p in enumerate(ps)}
    liste = []
    for ab in kursdef.get("abschnitte", []):
        neu = []
        for a in ab.get("aktivitaeten", []):
            if id(a) not in je_platz:
                neu.append(a)
                continue
            i = je_platz[id(a)]
            tor = [v for v in (a.get("voraussetzung") if isinstance(a.get("voraussetzung"), list)
                               else [a["voraussetzung"]] if a.get("voraussetzung") else [])]
            akts, kennungen = _aktivitaeten(a, lg[i], tor, grenzen)
            neu += akts
            liste.append({"nr": a["nr"], "name": a["name"], "thema": a.get("thema") or a["name"],
                          "start": start if i == 0 else None, **kennungen})
        ab["aktivitaeten"] = neu
    kursdef["inseln"] = liste
    return True


def eingesetzt(kursdef: dict | None) -> dict | None:
    """Die Kursdefinition mit eingesetzten Inseln: eine Kopie, wenn Platzhalter da sind, sonst sie selbst."""
    if not kursdef or not platzhalter(kursdef):
        return kursdef
    k = copy.deepcopy(kursdef)
    einsetzen(k)
    return k


def insel_von(akt: dict) -> dict | None:
    """Insel-Angabe einer Aktivität ({"nr", "stufe", "rolle"}) aus dem Feld `insel` oder der ID-Nummer."""
    if isinstance(akt.get("insel"), dict):
        return akt["insel"]
    m = IDNUMMER.match(str(akt.get("idnummer") or ""))
    if not m:
        return None
    stufe = {v: k for k, v in KURZ.items()}.get(m.group(2))
    return {"nr": int(m.group(1)), "stufe": stufe, "rolle": m.group(3) or "kopf"}
