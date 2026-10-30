"""Abschnitt „Allgemein“ und Kachelnummern (Rückmeldung LS 1, 2026-10-22).

Allgemein (Abschnitt 0) zeigt von oben nach unten: Vorgeschmack (`kurs.vorgeschmack`, ein, zwei Sätze) →
Steckbrief (Lernfeld, Umfang, Ergebnis aus `kurs.steckbrief`, dazu der Ansprechpartner; nur bei
`moodle.steckbrief`) → „So arbeiten Sie in diesem Kurs“ (`kurs.so_arbeiten`, Liste; Überschrift änderbar mit
`kurs.so_arbeiten_titel`, z. B. „So funktioniert das Sternebuch“ im Lernfeldkurs) → unten Schullogo
(`moodle.schullogo`) und KI-Hinweis (`moodle.ki_hinweis`). Der KI-Hinweis steht dann genau einmal im Kurs:
`anwenden` setzt `kurs.ki_hinweis_in_allgemein`, und der Bau lässt ihn in der Kursbeschreibung weg.
Neutrales Profil (Standard der Vorlage) = bisheriges Verhalten: kein Logo, kein Steckbrief, keine Nummern,
KI-Hinweis in der Kursbeschreibung.
Mit `moodle.infoblaetter_popup` setzt `anwenden` an Infoseiten, Infoblättern und Hilfekarten `popup` (eigenes
Fenster, Download-Knopf bei Word-Seiten) und ergänzt „So arbeiten Sie in diesem Kurs“ um einen Satz dazu.
Mit `moodle.schrittnummern` heißen die Hauptaktivitäten einer Kachel „Schritt n · Name“ (passend zur nummerierten
Liste im Kacheltext), Hilfen „Hilfe zu Schritt n“ direkt darunter und eingerückt; das Stern-Quiz bleibt ohne
Nummer. Die ID-Nummern der Hilfen und Stern-Quiz (sterne.idnummern) setzt `anwenden` immer.
Im Lernfeldkurs (kurs.typ „lernfeld“) gibt es keinen Sternzähler und keinen Pop-up-Satz.

    html, dateien = allgemein_html(kursdef["kurs"], profil)
    nummeriere(kursdef["abschnitte"])             # „1 · Einstieg“, Lehrkraftbereich ohne Nummer
    anwenden(kursdef, profil, logo_wurzel=..., dateien_wurzel=...)   # beides in die Kursdefinition schreiben
"""
import os
import re
from pathlib import Path

import sterne
from kursdefinition import kennung_von
from profilwerte import anrede_dativ
from xmlhilfe import x

KI_SATZ = "Dieser Kurs wurde von {} mit Hilfe von künstlicher Intelligenz erstellt und geprüft."
STECKBRIEF = ("Lernfeld", "Umfang", "Ergebnis")
NUMMER = re.compile(r"^\d+ · ")
SCHRITT = re.compile(r"^Schritt \d+(?:\.\d+)? · ")
LI_PREFIX = re.compile(r"(<li\b[^>]*>)(?:<strong>\d+\.\d+</strong> )?", re.I)
OL_OHNE_ZAHLEN = '<ol style="list-style:none;padding-left:0">'
LISTE = re.compile(r"<ol\b[^>]*>(.*?)</ol>", re.S | re.I)
SCHULFARBEN = ("#08349C", "#7DDE78")          # BBS-Blau, Grün (Standard ohne moodle.schulfarben)
FLAECHE_GRUEN, FLAECHE_BLAU = "#CDEFCB", "#D7DFF0"   # deckende helle Flächen hinter der Logo-Karte
POPUP_SATZ = ("Infoblätter öffnen sich in einem eigenen Fenster. Schieben Sie es neben die Aufgabe oder laden Sie "
              "es herunter.")

#: Kursschlüssel ← Profilschlüssel (Bauplan Kursdurchsicht LS 1); Standard aus der Vorlage = bisheriges Verhalten
KURS_SCHALTER = {"pdf_formular": "moodle.pdf_formular", "schilder": "moodle.schilder",
                 "sterne_schluessel": "moodle.sterne_schluessel", "bestehen_prozent": "moodle.bestehen_prozent",
                 "zwei_versuche": "moodle.tests_zwei_versuche",
                 "schrittnummern_mit_kachel": "moodle.schrittnummern_mit_kachel",
                 "sternzaehler": "moodle.sternzaehler", "lernpfad": "moodle.lernpfad_anzeige",
                 "infoseiten_wie_heft": "moodle.infoseiten_wie_heft",
                 "infoseiten_downloads": "moodle.infoseiten_downloads"}


def ki_satz(profil: dict) -> str:
    """Der KI-Hinweis mit der Anrede der Lehrkraft im Dativ („von Herrn Muster“); ohne Anrede mit dem Namen, ohne
    beides ohne „von …“."""
    wer = anrede_dativ(profil.get("lehrkraft.anrede") or "") or profil.get("lehrkraft.name") or ""
    return KI_SATZ.format(wer) if wer else KI_SATZ.replace("von {} ", "")


def _steckbrief(kurs: dict, profil: dict) -> str:
    werte = kurs.get("steckbrief") or {}
    zeilen = [(k, x(werte[k])) for k in STECKBRIEF if werte.get(k)]
    anrede, email = profil.get("lehrkraft.anrede", ""), profil.get("lehrkraft.email", "")
    if anrede and email:
        zeilen.append(("Ansprechpartner",
                       f'{x(anrede)} · <a href="mailto:{x(email)}">{x(email)}</a>'))
    if not zeilen:
        return ""
    return ('<table class="table"><tbody>'
            + "".join(f'<tr><th scope="row">{k}</th><td>{v}</td></tr>' for k, v in zeilen)
            + "</tbody></table>")


def allgemein_html(kurs: dict, profil: dict) -> tuple[str, list[str]]:
    """HTML für Abschnitt 0 und die Dateien darin (Pfade wie im Profil, hier nur das Schullogo).
    `moodle.allgemein_stil` „schulfarben“: Begrüßungskasten oben, Logo-Karte unten; sonst schlicht (bisher)."""
    bunt = profil.get("moodle.allgemein_stil") == "schulfarben"
    teile, dateien = [], []
    if kurs.get("vorgeschmack"):
        teile.append(_begruessung(kurs, profil) if bunt else f"<p>{x(kurs['vorgeschmack'])}</p>")
    if profil.get("moodle.steckbrief"):
        teile.append(_steckbrief(kurs, profil))
    if kurs.get("so_arbeiten"):
        teile.append(f"<h3>{x(kurs.get('so_arbeiten_titel') or 'So arbeiten Sie in diesem Kurs')}</h3><ul>"
                     + "".join(f"<li>{x(p)}</li>" for p in kurs["so_arbeiten"]) + "</ul>")
    logo = profil.get("moodle.schullogo") or ""
    if logo:
        dateien.append(logo)
    if bunt:
        teile.append(_logo_karte(logo, profil))
        return "".join(t for t in teile if t), dateien
    if logo:
        teile.append(f'<p><img src="{x(Path(logo).name)}" alt="Logo der Schule" width="180"></p>')
    if profil.get("moodle.ki_hinweis"):
        teile.append(f"<p>{x(ki_satz(profil))}</p>")
    return "".join(t for t in teile if t), dateien


def _farben(profil: dict) -> tuple[str, str]:
    """(Schulblau, Schulgrün) aus `moodle.schulfarben`, sonst die BBS-Farben."""
    f = list(profil.get("moodle.schulfarben") or [])
    return (f + [SCHULFARBEN[0]])[0], (f[1:] + [SCHULFARBEN[1]])[0]


def _begruessung(kurs: dict, profil: dict) -> str:
    """Begrüßungskasten ganz oben: Schulblau, weiße Schrift, Überschrift mit Symbol in Grün, darunter der Satz
    `vorgeschmack` wörtlich (Lehrkraft 2026-10-23)."""
    blau, gruen = _farben(profil)
    titel = kurs.get("begruessung_titel") or "Willkommen"
    return (f'<div style="background:{blau};color:#fff;border-radius:6px;padding:12px 16px;">'
            f'<p style="font-weight:bold;font-size:1.15em;margin:0 0 6px 0;">'
            f'<i class="fa fa-bolt" style="color:{gruen};" aria-hidden="true"></i> {x(titel)}</p>'
            f'<p style="margin:0;">{x(kurs["vorgeschmack"])}</p></div>')


def _logo_karte(logo: str, profil: dict) -> str:
    """Logo und KI-Satz in einer weißen Karte mit dünnem Rahmen in Schulblau, dahinter zwei überlappende
    Farbflächen (Grün oben links, helles Blau unten rechts). Moodle filtert `position` und Verläufe: die
    Überlappung entsteht nur über verschachtelte Blöcke mit negativen Rändern, „halbdurchsichtig“ mit deckenden
    hellen Farben. Ohne Logo und ohne KI-Hinweis keine Karte."""
    satz = profil.get("moodle.ki_hinweis") and x(ki_satz(profil)).replace(
        "künstlicher Intelligenz", "<b>künstlicher Intelligenz</b>")
    if not logo and not satz:
        return ""
    blau, _ = _farben(profil)
    bild = (f'<img src="{x(Path(logo).name)}" alt="Logo der Schule" width="180" '
            f'style="float:left;margin:0 16px 8px 0;">' if logo else "")
    text = f'<p style="color:{blau};margin:0;">{satz}</p>' if satz else ""
    return (f'<div style="background:{FLAECHE_BLAU};border-radius:8px;margin:24px 0 8px 25%;padding:0 0 16px 0;">'
            f'<div style="background:{FLAECHE_GRUEN};border-radius:8px;margin:0 25% 0 -33%;padding:16px 0 0 0;">'
            f'<div style="background:#fff;border:1px solid {blau};border-radius:6px;margin:0 -20% 0 16px;'
            f'padding:12px 16px;">{bild}{text}<div style="clear:both;"></div></div></div></div>')


def nummeriere(abschnitte: list[dict]) -> None:
    """„n · Name“ vor jede Kachel, lückenlos; der Lehrkraftbereich bleibt ohne Nummer. Eine vorhandene Nummer
    wird ersetzt, zweimal nummerieren ändert also nichts."""
    n = 0
    for ab in abschnitte:
        if ab.get("lehrkraft"):
            continue
        n += 1
        ab["name"] = f"{n} · {NUMMER.sub('', ab.get('name') or '')}"


def schrittnummern(abschnitte: list[dict], mit_kachel: bool = False) -> None:
    """„Schritt n · Name“ vor jede Hauptaktivität einer Kachel, deren Kacheltext eine nummerierte Liste hat (ein
    Schritt = eine Hauptaktivität, Reihenfolge = Liste; passt die Zahl nicht, ValueError). Hilfen (sterne.ist_hilfe)
    heißen „Hilfe zu Schritt n“ – bei mehreren mit „ · alter Name“ – und werden eingerückt (`einzug` 1); das
    Stern-Quiz und verborgene Aktivitäten bleiben, wie sie sind, und zählen nicht als Schritt (außer mit `schritt:
    true`, z. B. Abschlusstest, den die Lehrkraft einzeln freigibt; `schritt: false` nimmt eine sichtbare aus); der
    zweite Versuch eines Testpaars (sterne.ist_zweiter_versuch) zählt auch nicht und bleibt ohne „Schritt … ·“.
    Aktivitäten nur für eine Gruppe (Variantenkarten, kursdefinition.nur_fuer_gruppe) zählen nicht; aufeinander
    folgende Medaillen-Seiten (`medaille`) sind ein Schritt und tragen dieselbe Nummer. Verweise laufen
    über die Kennung: fehlt sie, wird der alte Name zur Kennung.
    Kacheln ohne Liste und der Lehrkraftbereich bleiben unverändert; zweimal nummerieren ändert nichts.
    `mit_kachel` (`moodle.schrittnummern_mit_kachel`): „Schritt k.n · Name“, „Hilfe zu k.n“ (k = Kachelnummer wie in
    `nummeriere`), und die Liste im Kacheltext zeigt dieselben Nummern („<strong>k.n</strong> “ statt Listenzahl)."""
    k = 0
    for ab in abschnitte:
        if not ab.get("lehrkraft"):
            k += 1
        liste = LISTE.search(ab.get("zusammenfassung") or "")
        if ab.get("lehrkraft") or not liste:
            continue
        vorn = f"{k}." if mit_kachel else ""
        akts = ab.get("aktivitaeten", [])
        art = [_schrittart(a, akts[i - 1] if i else None) for i, a in enumerate(akts)]
        schritte = len(re.findall(r"<li\b", liste.group(1), re.I))
        if schritte != art.count("neu"):
            raise ValueError(f"Kachel {ab.get('name')!r}: {schritte} Schritte im Kacheltext, aber {art.count('neu')} "
                             f"Aktivitäten (ohne Hilfen und Stern) – ein Schritt = eine Aktivität")
        n, hilfen = 0, {}
        for akt, wie in zip(akts, art):
            if wie == "ohne":
                continue                  # Stern, Verborgenes und Varianten je Gruppe bleiben ohne Nummer
            akt.setdefault("kennung", kennung_von(akt))
            if wie == "zweiter":
                continue                  # gehört zum Schritt des ersten Tests (Name ohne Vorsatz: sterne.zwei_versuche)
            if wie == "hilfe":
                if not n:
                    raise ValueError(f"Kachel {ab.get('name')!r}: Hilfe {akt['kennung']!r} vor dem ersten Schritt")
                hilfen.setdefault(n, []).append(akt)
            else:
                n += 1 if wie == "neu" else 0      # „gleich“: weitere Medaille im selben Schritt
                akt["name"] = f"Schritt {vorn}{n} · {SCHRITT.sub('', akt['name'])}"
        zusatz = sterne.HILFE_ZUSATZ if any(sterne.ist_stern(a) for a in akts) else ""
        for n, liste_n in hilfen.items():
            for akt in liste_n:
                akt["name"] = ((f"Hilfe zu {vorn}{n}" if mit_kachel else f"Hilfe zu Schritt {n}")
                               + (f" · {akt['kennung']}" if len(liste_n) > 1 else "") + zusatz)
                akt["einzug"] = 1
        if mit_kachel:
            ab["zusammenfassung"] = _liste_mit_kachel(ab["zusammenfassung"], liste, k)


def _schrittart(akt: dict, vorher: dict | None) -> str:
    """Rolle einer Aktivität beim Nummerieren: „neu“ (eigener Schritt), „gleich“ (weitere Medaillen-Seite, gleiche
    Nummer wie die davor), „hilfe“, „zweiter“ (zweiter Versuch eines Testpaars) oder „ohne“ (Stern, Verborgenes ohne
    `schritt: true`, Variante je Gruppe, `schritt: false`)."""
    if sterne.ist_stern(akt):
        return "ohne"
    if sterne.ist_zweiter_versuch(akt):
        return "zweiter" if akt.get("sichtbar", True) else "ohne"
    if sterne.ist_hilfe(akt):
        return "hilfe" if akt.get("sichtbar", True) else "ohne"
    if not akt.get("schritt", akt.get("sichtbar", True)):
        return "ohne"
    if sterne.ohne_eigenen_schritt(akt, vorher):
        return "gleich" if akt.get("medaille") and akt.get("schritt") is not False else "ohne"
    return "neu"


def _liste_mit_kachel(text: str, liste: re.Match, k: int) -> str:
    """Die erste nummerierte Liste ohne Listenzahlen, jedes `<li>` vorn mit „<strong>k.n</strong> “."""
    zaehler = iter(range(1, 1000))
    innen = LI_PREFIX.sub(lambda m: f"{m.group(1)}<strong>{k}.{next(zaehler)}</strong> ", liste.group(1))
    return text[:liste.start()] + f"{OL_OHNE_ZAHLEN}{innen}</ol>" + text[liste.end():]


def ist_infoblatt(akt: dict) -> bool:
    """Infoseite (auch aus Word), Infoblatt oder Hilfekarte: Feld `rolle` („info“, „hilfe“), sonst Word-Dateien
    oder der Name („Hilfekarte“ wie in sterne.hilfekarte, „Infoblatt“)."""
    if akt.get("typ") != "page":
        return False
    if akt.get("rolle"):
        return akt["rolle"] in ("info", "hilfe")
    name = (akt.get("name") or "").lower()
    return bool(akt.get("docx")) or "hilfekarte" in name or "infoblatt" in name


def infoblaetter_popup(kursdef: dict) -> None:
    """Infoblätter und Hilfekarten öffnen sich in einem eigenen Fenster (Profil `moodle.infoblaetter_popup`,
    Rückmeldung LS 1); dazu ein Satz in „So arbeiten Sie in diesem Kurs“ (höchstens einmal)."""
    for ab in kursdef.get("abschnitte", []):
        for akt in ab.get("aktivitaeten", []):
            if ist_infoblatt(akt):
                akt["popup"] = True
    liste = kursdef["kurs"].setdefault("so_arbeiten", [])
    if POPUP_SATZ not in liste:
        liste.append(POPUP_SATZ)


def anwenden(kursdef: dict, profil: dict, logo_wurzel: Path | None = None,
             dateien_wurzel: Path | None = None) -> None:
    """Allgemein, KI-Hinweis und Nummern nach dem Profil in die Kursdefinition schreiben; ein vorhandenes
    `kurs.allgemein` wird überschrieben, sobald Allgemein-Inhalt entsteht. `logo_wurzel`: Ordner, gegen den
    `moodle.schullogo` aufgelöst wird (der Arbeitsbereich); `dateien_wurzel`: Wurzel der Dateien beim Bau – der
    Logo-Pfad wird relativ zu ihr abgelegt (mit „/“), damit die Kursdefinition keinen rechnerabhängigen Pfad
    enthält. Ohne beide bleibt der Pfad, wie er im Profil steht."""
    kurs = kursdef["kurs"]
    lernfeld = kurs.get("typ") == "lernfeld"     # Lernfeldkurs: keine Infoblätter, keine Sterne im Kurs
    if profil.get("moodle.infoblaetter_popup") and not lernfeld:
        infoblaetter_popup(kursdef)
    html, dateien = allgemein_html(kurs, profil)
    if html:
        kurs["allgemein"] = html
        kurs["allgemein_dateien"] = [Path(os.path.relpath(Path(logo_wurzel) / d, dateien_wurzel)).as_posix()
                                     if logo_wurzel and dateien_wurzel else d for d in dateien]
    if profil.get("moodle.ki_hinweis"):
        kurs["ki_hinweis"] = ki_satz(profil)
        kurs["ki_hinweis_in_allgemein"] = True
    for schluessel, profilschluessel in KURS_SCHALTER.items():
        kurs[schluessel] = profil.get(profilschluessel)
    kurs["schulfarben"] = list(_farben(profil))      # Sternzähler und eigene Bausteine in den Schulfarben
    if lernfeld:
        kurs["sternzaehler"] = False      # das Konto über alle Themenkurse zeigt das Sternebuch
    sterne.idnummern(kursdef["abschnitte"])
    if profil.get("moodle.schrittnummern"):
        schrittnummern(kursdef["abschnitte"], mit_kachel=bool(kurs.get("schrittnummern_mit_kachel")))
    if profil.get("moodle.kachelnummern"):
        nummeriere(kursdef["abschnitte"])
