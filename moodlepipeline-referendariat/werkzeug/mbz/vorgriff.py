"""Prüfer „Vorgriff“ (Lehrkraft 2026-10-27): Nichts im Kurs darf eine Vorhersage vorwegnehmen.

In den Sichtprüfungen LS 3 und LS 4 fanden frische Helfer jedes Mal Hilfen, Tests oder Infoseiten, die vor der
zugehörigen Vorhersage erreichbar waren. Dieser Prüfer sucht das an der Kursdefinition, bevor gebaut wird:

- **Vorhersage** ist eine Aktivität mit `vorhersage: true`, sonst eine nach dem Absenden gesperrte Abgabe
  (`abgabe_bestaetigen`) oder eine Abstimmung (feedback), deren Name nach Vorhersage, Vermutung, Schätzung oder
  „vorher überlegen“ klingt; nie Meilenstein-Abgaben und die Selbsteinschätzung. `vorhersage: false` nimmt eine aus.
- **Fehler:** Eine sichtbare Aktivität, die etwas zeigt (Seite, Hilfe, Test, Datei, Simulation, Video), die in
  derselben Kachel nach der Vorhersage steht, hängt weder direkt noch über
  eine Kette von Bedingungen an ihr. Ausnahmen: der Stern „selbst gelöst“ (wartet ohnehin auf alle Abgaben) und
  einzeln verborgene Aktivitäten (die Lehrkraft gibt sie frei) und die Hilfen direkt unter der Vorhersage (sie
  gehören zu ihr).
- **Hinweis** (nur mit `gruppen`, Freischaltung je Meilenstein): eine Hilfe oder ein Test in einer späteren Kachel
  derselben Gruppe hängt nicht an der Vorhersage und ist damit vorher erreichbar.

    python3 vorgriff.py <kursdefinition.json>
"""
import json
import re
import sys

import inseln
import kursdefinition as kd
import sterne

#: Zustände, die nur gelten, wenn die Aktivität bearbeitet wurde (auch „nicht bestanden“: der Test wurde gemacht)
POSITIV = {"abgeschlossen", "bestanden", "nicht_bestanden"}
#: Aktivitäten, die etwas zeigen und damit eine Vorhersage vorwegnehmen können: Seiten (Info, Hilfe), Tests,
#: Dateien und Simulationen, Videos, Glossar
VERRATEN = {"page", "quiz", "resource", "url", "folder", "glossary", "label"}
VORHERSAGE_NAME = re.compile(r"Vorhersage|Vermutung|Schätzung|Einschätzung|vorher|überlegen", re.I)


def ist_vorhersage(akt: dict) -> bool:
    name = akt.get("name") or ""
    if akt.get("vorhersage") is not None:
        return bool(akt["vorhersage"])
    if "Meilenstein" in name or "Selbsteinschätzung" in name:
        return False
    if akt.get("typ") == "assign" and not akt.get("abgabe_bestaetigen"):
        return False
    return akt.get("typ") in ("assign", "feedback") and bool(VORHERSAGE_NAME.search(name))


def _bedingt_durch(bedingungen: list, ziel: str, hängt) -> bool:
    """Gilt die Bedingungsliste (UND) nur, wenn `ziel` erledigt ist? ODER-Gruppen nur, wenn jeder Zweig es verlangt;
    UND-Gruppen, wenn eine ihrer Bedingungen es verlangt; Verneinungen verlangen nie etwas (Übungsinseln: „Kurztest
    ohne Note“)."""
    for v in bedingungen:
        if not isinstance(v, dict):
            continue
        if "und" in v:
            if isinstance(v["und"], list) and _bedingt_durch(v["und"], ziel, hängt):
                return True
            continue
        if "nicht" in v:
            continue
        if "oder" in v:
            zweige = [z if isinstance(z, list) else [z] for z in v["oder"]]
            if zweige and all(_bedingt_durch(z, ziel, hängt) for z in zweige):
                return True
            continue
        name = kd.ziel_von(v)
        if not name:
            continue
        positiv = kd.zustand_von(v) in POSITIV or "min" in v
        if positiv and (name == ziel or hängt(name, ziel)):
            return True
    return False


def pruefe(kursdef: dict, gruppen: list[list[int]] | None = None) -> list[tuple[str, str]]:
    """Befunde als (Stufe, Text) mit Stufe „Fehler“ oder „Hinweis“. `gruppen`: Kachelnummern (1 = erste Kachel nach
    „Allgemein“), die gemeinsam freigeschaltet werden (Lernpfad, z. B. [[2, 3, 4, 5, 6, 7], [8, 9, 10]]); nur dann
    prüft der Prüfer auch spätere Kacheln derselben Gruppe. Übungsinseln (inseln.py; Platzhalter werden in einer
    Kopie eingesetzt) gelten als ein Ganzes: ein Befund je Insel, nicht je Übung und Kurztest; ihre Stufen hängen über
    ODER-Zweige an den Kurztests der vorigen Insel, entscheidend ist die Voraussetzung der Insel (UND)."""
    kursdef = inseln.eingesetzt(kursdef)
    akt_von = {}
    for _, a in kd.alle_aktivitaeten(kursdef):
        for n in {kd.kennung_von(a), a.get("name")}:
            if n:
                akt_von[n] = a
    merk: dict = {}

    def hängt(name: str, ziel: str, tiefe=0) -> bool:
        if (name, ziel) in merk:
            return merk[(name, ziel)]
        merk[(name, ziel)] = False                       # gegen Kreise
        a = akt_von.get(name)
        erg = bool(a) and tiefe < 40 and _bedingt_durch(kd.voraussetzungen(a), ziel,
                                                        lambda n, z: hängt(n, z, tiefe + 1))
        merk[(name, ziel)] = erg
        return erg

    befunde = []
    abschnitte = [ab for ab in kursdef.get("abschnitte", []) if not ab.get("lehrkraft")]
    for i, ab in enumerate(abschnitte):
        akts = ab.get("aktivitaeten", [])
        for j, v in enumerate(akts):
            if not ist_vorhersage(v):
                continue
            vname = kd.kennung_von(v)
            eigene_hilfen = set()
            for a in akts[j + 1:]:                       # Hilfen direkt unter der Vorhersage gehören zu ihr
                if not sterne.ist_hilfe(a):
                    break
                eigene_hilfen.add(id(a))
            gemeldet = set()                             # Inseln: ein Befund je Insel
            for a in akts[j + 1:]:
                if sterne.ist_stern(a) or a.get("sichtbar") is False or id(a) in eigene_hilfen:
                    continue
                if a.get("typ") not in VERRATEN:          # Abgaben und Abstimmungen verraten nichts
                    continue
                if not hängt(kd.kennung_von(a), vname):
                    insel = inseln.insel_von(a)
                    if insel and insel["nr"] in gemeldet:
                        continue
                    was = f"Insel {insel['nr']} ({a.get('name')!r} und weitere)" if insel else repr(a.get("name"))
                    if insel:
                        gemeldet.add(insel["nr"])
                    befunde.append(("Fehler", f"{ab.get('name')!r}: {was} ist vor der Vorhersage "
                                              f"{v.get('name')!r} erreichbar"))
            gruppe = next((g for g in (gruppen or []) if i + 1 in g), [])
            for spaeter in [abschnitte[k - 1] for k in gruppe if k > i + 1 and k <= len(abschnitte)]:
                gemeldet = set()
                for a in spaeter.get("aktivitaeten", []):
                    if not (sterne.ist_hilfe(a) or a.get("typ") == "quiz") or a.get("sichtbar") is False:
                        continue
                    if sterne.ist_stern(a) or sterne.ist_zweiter_versuch(a):
                        continue
                    if not hängt(kd.kennung_von(a), vname):
                        insel = inseln.insel_von(a)
                        if insel and insel["nr"] in gemeldet:
                            continue
                        if insel:
                            gemeldet.add(insel["nr"])
                        was = f"Insel {insel['nr']} ({a.get('name')!r} und weitere)" if insel else repr(a.get("name"))
                        befunde.append(("Hinweis", f"{spaeter.get('name')!r}: {was} ist bei gemeinsamer "
                                                   f"Freischaltung vor der Vorhersage {v.get('name')!r} "
                                                   f"({ab.get('name')!r}) erreichbar"))
    return befunde


if __name__ == "__main__":
    for pfad in sys.argv[1:]:
        b = pruefe(json.loads(open(pfad, encoding="utf-8").read()))
        print(f"{pfad}: {sum(s == 'Fehler' for s, _ in b)} Fehler, {sum(s == 'Hinweis' for s, _ in b)} Hinweise")
        for s, t in b:
            print(f"  {s:7} {t}")
