"""Lernfeldkurs (KONZEPT 2026-10-19 Punkt 1, 2026-10-25 Frage 10): ein schlanker Kurs je Klasse und Lernfeld.

Oben in „Allgemein“ stehen die Aktivitäten des Kurses (z. B. Sternebuch und Preisliste, sternebuch.py), darunter
je Lernsituation eine Kachel mit einem Link zum Themenkurs. Der Lernfeldkurs hat keine Noten, keine Medaillen und
keine Abzeichen (kurs.typ „lernfeld“); die Medaillen bleiben in den Themenkursen.

Kurslinks über den Kurznamen: Die Kurs-Ids entstehen erst beim Einspielen. Moodle öffnet einen Kurs auch über
`course/view.php?name=<Kurzname>` (course/view.php, Parameter name → shortname, Kurznamen sind eindeutig). Der Link
steht relativ in der Kachel (`view.php?name=…`): die Kachel erscheint immer unter …/course/ (Kursseite,
Abschnittsseite), so passt er auch, wenn das Moodle in einem Unterordner liegt, und niemand muss nach dem Einspielen
Ids eintragen. Ein Kurs, der noch nicht gebaut ist (ohne kurzname), steht als „folgt“ da.

    kursdef = kursdefinition(kurs={...}, themen=[{"name": "LS 1 · …", "kurzname": "…", "text": "<p>…</p>"}],
                             allgemein=[sternebuch.datenbank(...), sternebuch.preisliste_seite(...)])
"""
from __future__ import annotations

import urllib.parse

from xmlhilfe import x

FOLGT = "Dieser Themenkurs folgt."


def kurslink(kurzname: str) -> str:
    """Relativer Link auf einen Kurs über seinen Kurznamen (von einer Seite unter …/course/ aus)."""
    return "view.php?name=" + urllib.parse.quote(kurzname, safe="")


def kachel(thema: dict) -> dict:
    """Abschnitt (Kachel) einer Lernsituation: Text, darunter der Knopf zum Themenkurs oder „folgt“."""
    text = thema.get("text") or ""
    if thema.get("kurzname"):
        knopf = (f'<p><a class="btn btn-primary" href="{x(kurslink(thema["kurzname"]))}">'
                 f'{x(thema.get("knopf") or "Zum Themenkurs")}</a></p>')
    else:
        knopf = f"<p><strong>{x(thema.get('folgt') or FOLGT)}</strong></p>"
    ab = {"name": thema["name"], "zusammenfassung": text + knopf, "sichtbar": thema.get("sichtbar", True),
          "aktivitaeten": []}
    if thema.get("bild"):
        ab["bild"] = thema["bild"]
    return ab


def kursdefinition(kurs: dict, themen: list[dict], allgemein: list[dict] | None = None,
                   lehrkraft: dict | None = None) -> dict:
    """Kursdefinition eines Lernfeldkurses: `kurs` wie beim Themenkurs (kursdefinition.py), `themen` je
    Lernsituation {name, kurzname (None = folgt), text, bild, knopf}, `allgemein` die Aktivitäten oben in Allgemein,
    `lehrkraft` ein verborgener Abschnitt (lehrkraft true) am Ende."""
    if not themen:
        raise ValueError("Lernfeldkurs ohne Lernsituationen")
    abschnitte = [kachel(t) for t in themen]
    if lehrkraft:
        abschnitte.append(dict(lehrkraft, lehrkraft=True, sichtbar=False))
    return {"kurs": dict(kurs, typ="lernfeld"), "allgemein_aktivitaeten": list(allgemein or []),
            "abschnitte": abschnitte}
