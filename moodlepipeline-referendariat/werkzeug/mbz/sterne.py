"""Sterne als Kurswährung: Selbstlöse-Stern je Kachel, Hilfekarten, Medaillen.

Sterne sind die Bewertungspunkte des Kurses. Ein Test bekommt sie über das
Feld `sterne` (Höchstpunkte; `sterne: 0` = zählt nicht, sein Bewertungsaspekt
hat im Kursgesamt das Gewicht 0). Kursgesamt = Summe aller Sterne, die
Medaille ergibt sich aus dem Anteil erreichter an möglichen Sternen
(Kursgesamt in %, Grenzen aus dem Profil `moodle.medaillen_grenzen`).

Je Kachel gibt es einen Stern „selbst gelöst“ (`stern_aktivitaet`): ein Test
mit einer Frage und der einzigen Antwort „Stern abholen“. Er ist offen, wenn
die Abgabe der Kachel abgeschlossen ist UND keine Hilfekarte der Kachel
angesehen wurde. Wer eine Hilfekarte öffnet, bevor der Stern abgeholt ist,
bekommt ihn nicht mehr; wer sie danach öffnet, behält ihn (gewollt).

Regel für Auswertungen (Dashboard): **Stern geholt = Bewertung > 0** im
Stern-Quiz. Erkannt werden Stern-Quiz und Hilfen an der festen Kennung, nicht
am Anzeigenamen (Schrittnummern ändern die Namen): Feld `rolle` („stern“ bzw.
„hilfe“, gesetzt von `stern_aktivitaet` und `hilfekarte`) und daraus die
Moodle-ID-Nummer (`idnummern`): `stern-k<n>`, `hilfe-k<n>-s<m>` – n ist die
Kachel (gezählt wie die Kachelnummern), m der Schritt, unter dem die Hilfe
steht; mehrere Hilfen an einem Schritt bekommen -1, -2 … angehängt.

Tests mit zweitem Versuch (Lehrkraft 2026-10-23, Kursschalter `zwei_versuche`, `bestehen_prozent`,
`sterne_schluessel` aus dem Profil): ein Kacheltest wird zum Paar „Test“ / „Test, zweiter Versuch“
(`zwei_versuche`, je 1 Versuch, bestanden ab `bestehen_prozent`); der zweite Versuch und die Hilfen des Tests
öffnen sich erst nach „abgeschlossen, nicht bestanden“ des ersten. Beide Testnoten zählen nicht (Gewicht 0); die
Sterne kommen aus einer berechneten Bewertung „Sterne: <Test>“ (`sternformel`): IHK-Schlüssel nur im ersten
Versuch, im zweiten Versuch bestanden = genau 1 Stern, leere Note zählt als 0. ID-Nummern: `test-k<n>-s<m>`
(zählt als Schritt m) und `test2-k<n>-s<m>` (kein eigener Schritt). `paar_einsetzen` baut das in eine
Kursdefinition ein – ohne die Schalter tut es nichts (bisheriges Verhalten). Der Selbstlöse-Stern einer Kachel, der
auf den Test wartet, verlangt dann statt „abgeschlossen“ eine ODER-Gruppe „Test bestanden oder zweiter Versuch
bestanden“ (Lehrkraft 2026-10-23, Variante 1; `selbstloese_paar`): wer erst im zweiten Versuch ohne Hilfe besteht,
hat es selbst gelöst, wer zweimal nicht besteht, nicht. „Bestanden“ (e = 2), nicht „abgeschlossen“: der zweite
Versuch schließt auch mit „alle Versuche verbraucht“ ab.

Sternzähler (Kursschalter `sternzaehler`): genau eine Aktivität „⭐ Meine Sterne“ in Allgemein (sternzaehler.py,
Lehrkraft 2026-10-26; ersetzt die Textfelder je Sternstand vom 2026-10-23). Ihr Höchstwert N ist der Höchstwert des
Kursgesamts (`kursgesamt_max`, dieselbe Summe wie im Bau).
"""
from __future__ import annotations

import re

from kursdefinition import bewertet, im_kursgesamt, kennung_von, nur_fuer_gruppe
from xmlhilfe import x

STERN_NAME = "Ihr Stern: selbst gelöst"
MEDAILLEN = ("Grün", "Bronze", "Silber", "Gold")


def stern_aktivitaet(kachel: dict, abgabe: str, hilfen: list[str]) -> dict:
    """Stern-Quiz einer Kachel: 1 Stern, offen nach `abgabe` (abgeschlossen),
    solange keine der `hilfen` abgeschlossen (angesehen) ist."""
    return {
        "typ": "quiz", "name": STERN_NAME, "rolle": "stern",
        "kennung": f"{STERN_NAME} ({kachel['name']})",
        "beschreibung": "<p>Haben Sie alle Abgaben dieser Kachel ohne Hilfe "
                        "erledigt, öffnet sich hier Ihr Stern.</p>",
        "sterne": 1, "versuche": 1, "abschluss": "note",
        "fragen": [{"typ": "multichoice", "name": "Stern abholen",
                    "text": "<p>Sie haben es selbst gelöst. Klicken Sie an und "
                            "geben Sie ab.</p>",
                    "einzige_antwort": True,
                    "antworten": [{"text": "Stern abholen", "richtig": True}]}],
        "voraussetzung": [{"abschluss": abgabe, "zustand": "abgeschlossen"}]
                         + [{"abschluss": h, "zustand": "nicht_abgeschlossen"} for h in hilfen],
    }


def hilfekarte(name: str, inhalt: str, **weitere) -> dict:
    """Hilfe als Seite (Rolle „hilfe“), abgeschlossen beim Ansehen (Moodle merkt
    sich, wer sie geöffnet hat). Der Name ist frei; mit Schrittnummern heißt sie
    „Hilfe zu Schritt n“ (allgemein.schrittnummern)."""
    return {"typ": "page", "name": name, "inhalt": inhalt, "abschluss": "ansehen",
            "rolle": "hilfe", **weitere}


def ist_hilfe(akt: dict) -> bool:
    """Hilfe einer Kachel: Rolle „hilfe“ oder ID-Nummer „hilfe-…“."""
    return akt.get("rolle") == "hilfe" or str(akt.get("idnummer") or "").startswith("hilfe-")


def ist_zweiter_versuch(akt: dict) -> bool:
    """Zweiter Versuch eines Testpaars: Rolle „test2“ oder ID-Nummer „test2-…“ (kein eigener Schritt)."""
    return akt.get("rolle") == "test2" or str(akt.get("idnummer") or "").startswith("test2-")


def ist_stern(akt: dict) -> bool:
    """Stern-Quiz „selbst gelöst“: Rolle „stern“ oder ID-Nummer „stern-…“."""
    return akt.get("rolle") == "stern" or str(akt.get("idnummer") or "").startswith("stern-")


def ohne_eigenen_schritt(akt: dict, vorher: dict | None) -> bool:
    """Gehört die Aktivität zu keinem eigenen Schritt? Ja bei `schritt: false`, bei einer Gruppenbedingung
    (Variantenkarte je Gruppe, kursdefinition.nur_fuer_gruppe) und bei einer Medaillen-Seite direkt nach einer
    anderen (die vier Medaillen sind ein Schritt). `vorher`: die Aktivität davor in der Kachel."""
    if akt.get("schritt") is False:
        return True
    if akt.get("schritt") is None and nur_fuer_gruppe(akt):
        return True
    return bool(akt.get("medaille") and vorher and vorher.get("medaille"))


def idnummern(abschnitte: list[dict]) -> None:
    """ID-Nummern `stern-k<n>` und `hilfe-k<n>-s<m>[-i]` setzen (siehe oben).
    Eine Hilfe vor dem ersten Schritt einer Kachel ist ein Fehler (ValueError)."""
    n = 0
    for ab in abschnitte:
        if ab.get("lehrkraft"):
            continue
        n += 1
        schritt, je_schritt = 0, {}
        akts = ab.get("aktivitaeten", [])
        for i, akt in enumerate(akts):
            if ist_hilfe(akt):
                if not schritt:
                    raise ValueError(f"{ab.get('name')!r} / {akt.get('name')!r}: Hilfe vor dem ersten "
                                     f"Schritt – sie gehört unter den Schritt, zu dem sie hilft")
                je_schritt.setdefault(schritt, []).append(akt)
            elif ist_stern(akt):
                akt["idnummer"] = f"stern-k{n}"
            elif ist_zweiter_versuch(akt):
                akt["idnummer"] = f"test2-k{n}-s{schritt}"
            elif not ohne_eigenen_schritt(akt, akts[i - 1] if i else None):
                schritt += 1
                if akt.get("rolle") == "test":
                    akt["idnummer"] = f"test-k{n}-s{schritt}"
        for m, hilfen in je_schritt.items():
            for i, akt in enumerate(hilfen, start=1):
                akt["idnummer"] = f"hilfe-k{n}-s{m}" + (f"-{i}" if len(hilfen) > 1 else "")


def medaillen_bereiche(grenzen: list) -> list[tuple[str, dict]]:
    """(Medaille, Kursgesamt-Bedingung): lückenlos, obere Grenze exklusiv, Gold bis 100."""
    g = list(grenzen)
    if len(g) != len(MEDAILLEN) or not (0 < g[0] and g[-1] <= 100
                                        and all(a < b for a, b in zip(g, g[1:]))):
        raise ValueError(f"medaillen_grenzen {grenzen!r}: vier aufsteigende Zahlen "
                         f"zwischen 1 und 100 nötig")
    aus = []
    for i, name in enumerate(MEDAILLEN):
        bed = {"bewertung": "kursgesamt", "min": g[i]}
        if i + 1 < len(g):
            bed["max"] = g[i + 1]
        aus.append((name, bed))
    return aus


def medaillen_seiten(grenzen: list, felder: dict | None = None,
                     nach: str | None = None) -> list[dict]:
    """Vier Seiten „Ihre Medaille: …“ mit Kursgesamt-Bereich und Abschluss
    „ansehen“ (Kriterium der Abzeichen). `felder` je Medaille ergänzt oder
    ersetzt Felder der Seite (inhalt, dateien, tags …). `nach`: Kennung des
    Abschlusstests – die Medaille öffnet sich erst, wenn er bewertet ist (UND;
    Lehrkraft 2026-10-22: je Person genau eine Medaille zum Sternanteil in
    diesem Moment). Bedingung „bewertet ab 0 %“, nicht „abgeschlossen“: mit
    Bestehensgrenze ist ein nicht bestandener Test „abgeschlossen, nicht
    bestanden“ und erfüllt „abgeschlossen“ nicht (gemessen, Moodle 5.1.6)."""
    seiten = []
    for name, bed in medaillen_bereiche(grenzen):
        # vor dem Abschlusstest ganz verborgen, nicht ausgegraut (sonst verriete sie die Stufe vorab)
        bedingungen = [bed] + ([{"aktivitaet": nach, "min": 0,
                                 "sichtbar_wenn_gesperrt": False}] if nach else [])
        seite = {"typ": "page", "name": f"Ihre Medaille: {name}", "medaille": name,
                 "abschluss": "ansehen", "voraussetzung": bedingungen,
                 "inhalt": f"<p>Holen Sie hier Ihre Medaille ab: {name}.</p>"}
        seite.update((felder or {}).get(name, {}))
        seiten.append(seite)
    return seiten


ZWEITER_VERSUCH = ", zweiter Versuch"
SCHRITT_VORSATZ = re.compile(r"^Schritt \d+(?:\.\d+)? · ")   # wie allgemein.SCHRITT; der zweite Versuch trägt keinen


def zwei_versuche(test: dict, hilfen: list[dict], bestehen: int) -> list[dict]:
    """[Test, Test zweiter Versuch] aus einem Kacheltest: je 1 Versuch, bestanden ab `bestehen` %, `sterne` 0
    (Sterne über `sternformel`). Der erste schließt mit „bestanden“ ab – nur so meldet Moodle „abgeschlossen, nicht
    bestanden“ (gemessen 5.1.6); der zweite mit „bestanden oder alle Versuche verbraucht“ und ist ganz verborgen, bis
    der erste nicht bestanden ist. Jede der `hilfen` bekommt dieselbe Sperre zusätzlich (in place)."""
    kennung = kennung_von(test)
    t1 = dict(test, kennung=kennung, rolle="test", versuche=1, bestehensgrenze_prozent=bestehen, sterne=0,
              abschluss="bestanden")
    sperre = {"abschluss": kennung, "zustand": "nicht_bestanden", "sichtbar_wenn_gesperrt": False}
    t2 = dict(t1, name=SCHRITT_VORSATZ.sub("", test["name"]) + ZWEITER_VERSUCH, kennung=kennung + ZWEITER_VERSUCH,
              rolle="test2",
              abschluss="bestanden_oder_versuche", voraussetzung=dict(sperre))
    t2.pop("idnummer", None)
    if str(t1.get("idnummer") or "").startswith("test-"):
        t2["idnummer"] = "test2-" + t1["idnummer"][len("test-"):]
    for h in hilfen:
        h["voraussetzung"] = [*(v for v in _als_liste(h.get("voraussetzung")) if v != sperre), dict(sperre)]
    return [t1, t2]


def _als_liste(v) -> list:
    return [] if not v else (list(v) if isinstance(v, list) else [v])


def _zahl(z: float) -> str:
    return f"{float(z):g}"


def sternformel(id1: str, id2: str, grenzen: list[int], max1: float, max2: float) -> str:
    """Moodle-Formel (Anzeigeform: [[idnummer]], Trennzeichen „;“) für die Sterne eines Testpaars, Ergebnis
    0 … len(grenzen): je erreichter Grenze im ersten Versuch ein Stern; wer erst im zweiten Versuch die erste Grenze
    erreicht, bekommt genau einen. Prozent auf 5 Stellen gerundet – 11,04 von 12 sind genau 92 %, nicht 91,999…; gröber
    nicht, sonst gäbe 49,995 % einen Stern, obwohl Moodle ungerundet „nicht bestanden“ meldet (ein Stern heißt
    immer „bestanden“). Eine leere Note rechnet Moodle als 0."""
    if not grenzen:
        raise ValueError("sternformel braucht mindestens eine Grenze")
    p1 = f"round([[{id1}]]/{_zahl(max1)}*100;5)"
    p2 = f"round([[{id2}]]/{_zahl(max2)}*100;5)"
    stufe = lambda p, g: f"min(1;floor({p}/{_zahl(g)}))"  # noqa: E731
    erster = "+".join(stufe(p1, g) for g in grenzen)
    return f"={erster}+{stufe(p2, grenzen[0])}*(1-{stufe(p1, grenzen[0])})"


def punkte(akt: dict) -> float:
    """Höchstpunkte einer Aktivität im Bewertungsbuch (wie der Bau sie schreibt; 0 ohne Note): Raster-Summe bei
    Aufgaben, sonst `sterne`, sonst `punkte` (Vorgabe Test 10, sonst 100)."""
    if not bewertet(akt):
        return 0.0
    if akt.get("typ") == "assign" and akt.get("bewertungsraster"):
        return float(sum(k["punkte"] for k in akt["bewertungsraster"]))
    if akt.get("sterne"):
        return float(akt["sterne"])
    return float(akt.get("punkte", 10 if akt.get("typ") == "quiz" else 100))


def kursgesamt_teile(kursdef: dict) -> list[tuple[str, float, bool]]:
    """(Kennung, Höchstwert, ist Stern) je Posten, der im Kursgesamt zählt: bewertete Aktivitäten außer `sterne: 0`
    und `im_kursgesamt: false` (Gewicht 0) und die berechneten Bewertungen. Stern = Test mit `sterne` > 0 oder „Sterne: …“."""
    teile = [(kennung_von(a), punkte(a), a.get("typ") == "quiz" and bool(a.get("sterne")))
             for ab in kursdef.get("abschnitte", []) for a in ab.get("aktivitaeten", [])
             if im_kursgesamt(a)]
    return teile + [(b["name"], float(b["max"]), b["name"].startswith("Sterne: "))
                    for b in kursdef.get("bewertungen", [])]


def kursgesamt_max(kursdef: dict) -> float:
    """Höchstwert des Kursgesamts (Summe von `kursgesamt_teile`)."""
    return sum(p for _, p, _ in kursgesamt_teile(kursdef))


def testpunkte(test: dict) -> float:
    """Höchstpunkte eines Tests ohne Sterne (wie bauen.Bau.punkte: punkte, sonst 10)."""
    return float(test.get("punkte", 10))


def sterne_bewertung(t1: dict, t2: dict, grenzen: list[int]) -> dict:
    """Berechnete Bewertung „Sterne: <Test>“ für `kursdef["bewertungen"]` (beide Tests brauchen ihre idnummer)."""
    return {"typ": "berechnet", "name": f"Sterne: {kennung_von(t1)}", "max": len(grenzen),
            "formel": sternformel(t1["idnummer"], t2["idnummer"], grenzen, testpunkte(t1), testpunkte(t2))}


def _paare(akts: list[dict]) -> list[tuple[str, str]]:
    """(Kennung Test, Kennung zweiter Versuch) je Testpaar eines Abschnitts, in Kachelreihenfolge."""
    kennungen = {kennung_von(a) for a in akts if ist_zweiter_versuch(a)}
    return [(k, k + ZWEITER_VERSUCH) for a in akts if a.get("rolle") == "test"
            and (k := kennung_von(a)) + ZWEITER_VERSUCH in kennungen]


def selbstloese_paar(kursdef: dict, t1: dict, t2: dict) -> None:
    """Der Selbstlöse-Stern der Kachel von t1 verlangt danach je Testpaar der Kachel eine ODER-Gruppe „Test oder
    zweiter Versuch bestanden“ (alle per UND; Lehrkraft 2026-10-23: der ganze Auftrag ohne Hilfe), vorn in
    Kachelreihenfolge (in place). Bedingungen auf einen Test eines Paars (auch frühere ODER-Gruppen) fallen weg und
    werden neu gebaut – idempotent, gleich in welcher Reihenfolge die Paare entstehen; die übrigen (Hilfen
    „nicht abgeschlossen“, eine Abgabe ohne Test) bleiben. `sichtbar_wenn_gesperrt` einer ersetzten Bedingung geht
    auf die Gruppe ihres Paars über."""
    for ab in kursdef.get("abschnitte", []):
        akts = ab.get("aktivitaeten", [])
        if not any(a is t1 for a in akts):
            continue
        paare = _paare(akts)
        zu_paar = {k: i for i, p in enumerate(paare) for k in p}
        for akt in akts:
            if not ist_stern(akt):
                continue
            sichtbar, rest = {}, []
            for v in _als_liste(akt.get("voraussetzung")):
                bezug = ([b.get("abschluss", b.get("aktivitaet")) for b in v["oder"]] if isinstance(v, dict)
                         and "oder" in v else [v.get("abschluss", v.get("aktivitaet"))] if isinstance(v, dict) else [])
                treffer = [zu_paar[k] for k in bezug if k in zu_paar]
                if not treffer:
                    rest.append(v)
                elif "sichtbar_wenn_gesperrt" in v:
                    sichtbar[treffer[0]] = v["sichtbar_wenn_gesperrt"]
            gruppen = [{"oder": [{"abschluss": k1, "zustand": "bestanden"}, {"abschluss": k2, "zustand": "bestanden"}],
                        **({"sichtbar_wenn_gesperrt": sichtbar[i]} if i in sichtbar else {})}
                       for i, (k1, k2) in enumerate(paare)]
            akt["voraussetzung"] = gruppen + rest


def paar_einsetzen(kursdef: dict, kennung: str) -> bool:
    """Den Test `kennung` durch sein Paar ersetzen (zwei_versuche), die Hilfen direkt hinter ihm sperren, den
    zweiten Versuch hinter diese Hilfen stellen, ID-Nummern setzen und „Sterne: <Test>“ in `kursdef["bewertungen"]`
    eintragen; der Selbstlöse-Stern auf diesen Test wartet danach auf „bestanden in einem der beiden Versuche“
    (selbstloese_paar). Nur mit den Kursschaltern `zwei_versuche` und `sterne_schluessel` (allgemein.anwenden); ohne sie
    ändert sich nichts (False). Vor oder nach allgemein.anwenden: der zweite Versuch bekommt keine Schrittnummer."""
    kurs = kursdef.get("kurs") or {}
    grenzen = list(kurs.get("sterne_schluessel") or [])
    if not kurs.get("zwei_versuche") or not grenzen:
        return False
    bestehen = kurs.get("bestehen_prozent") or grenzen[0]
    for ab in kursdef.get("abschnitte", []):
        akts = ab.get("aktivitaeten", [])
        for i, akt in enumerate(akts):
            if kennung_von(akt) != kennung or akt.get("typ") != "quiz":
                continue
            j = i + 1
            while j < len(akts) and ist_hilfe(akts[j]):
                j += 1
            t1, t2 = zwei_versuche(akt, akts[i + 1:j], bestehen)
            akts[i:j] = [t1, *akts[i + 1:j], t2]
            idnummern(kursdef["abschnitte"])
            selbstloese_paar(kursdef, t1, t2)
            kursdef.setdefault("bewertungen", []).append(sterne_bewertung(t1, t2, grenzen))
            return True
    raise ValueError(f"Test {kennung!r} gibt es nicht")


SCHILD = "border-radius:10px;padding:1px 8px;"
SCHILD_GELB = f'<span style="background:#FFF4CC;color:#7A5A00;border:1px solid #E0A800;{SCHILD}">'
SCHILD_GRUEN = f'<span style="background:#E3F6E1;color:#1E5E1A;border:1px solid #7DDE78;{SCHILD}">'
SOZIALFORMEN = ("Gruppenarbeit", "Partnerarbeit")
SCHILD_GRAU = f'<span style="background:#EEF1F5;color:#2B3440;border:1px solid #8A94A3;{SCHILD}">'
#: Zusatz am Namen jeder Hilfe einer Kachel mit Selbstlöse-Stern (allgemein.schrittnummern): vor dem Öffnen sichtbar,
#: denn unter dem Link steht nichts mehr (Lehrkraft 2026-10-26, showdescription 0)
HILFE_ZUSATZ = " (kostet den Stern „selbst gelöst“)"


def _versuche(n) -> str:
    n = int(n or 0)
    return "beliebig viele Versuche" if n == 0 else ("ein Versuch" if n == 1 else f"{n} Versuche")


def schild_html(akt: dict, bestehen: int, grenzen: list | None = None) -> str:
    """Schilder vorn in der Beschreibung (Kursschalter `schilder`, Lehrkraft 2026-10-23), beide in einer Zeile:
    gelb die Sterne – Selbstlöse-Stern „⭐ · ohne Hilfe“; erster Test eines Paars „⭐⭐⭐ · 2 Versuche · bestanden ab
    <bestehen> %“ (Sterne = Zahl der `grenzen`); ein Test mit Sternen ohne Paar (Abschlusstest) „⭐ × 10 · ein
    Versuch“ (Zahl statt zehn ⭐, 2026-10-25); kein Sternschild am zweiten Versuch (Lehrkraft 2026-10-23). Grün die Sozialform („👥 Gruppenarbeit“,
    „👥 Partnerarbeit“; Einzelarbeit ohne Schild). Nichts davon: ""."""
    teile = []
    if ist_stern(akt):
        teile.append(f"{SCHILD_GELB}⭐ · ohne Hilfe</span>")
    elif akt.get("rolle") == "test" and grenzen:
        teile.append(f"{SCHILD_GELB}{'⭐' * len(grenzen)} · 2 Versuche · bestanden ab {_zahl(bestehen)} %</span>")
    elif akt.get("typ") == "quiz" and not akt.get("rolle") and (akt.get("sterne") or 0) > 0:
        teile.append(f"{SCHILD_GELB}⭐ × {akt['sterne']} · {_versuche(akt.get('versuche', 0))}</span>")
    if akt.get("sozialform") in SOZIALFORMEN:
        teile.append(f"{SCHILD_GRUEN}👥 {akt['sozialform']}</span>")
    return f"<p>{' '.join(teile)}</p>" if teile else ""
