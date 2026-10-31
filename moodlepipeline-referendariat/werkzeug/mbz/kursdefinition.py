"""Kursdefinition eines Themen- oder Lernfeldkurses (Pipeline 3): Format und Prüfung.

Ein Themenkurs ist ein JSON-Objekt (in Python ein dict). Pfade zu Dateien sind
relativ zur `dateien_wurzel`, die `bauen.baue()` mitbekommt. Ein Kurs ist
gültig, wenn `pruefe(kursdef)` eine leere Liste liefert.

    {
      "kurs": {
        "vollname":  "EG1 · LF 1 · LS 1 Der Stromhof und das Haus Schütte",
        "kurzname":  "EG1-LF01-LS01",
        "beschreibung": "<p>…</p>",              # HTML
        "ki_hinweis": "Erstellt von Alex … mit Hilfe von künstlicher Intelligenz",
        "format": "tiles",                        # Standard Kachelformat (format_tiles); "topics" nur ohne Plugin
        "ursache": {"begriffe": ["Spannungsteiler"], "ab_kachel": 5},  # Prüfer 15 Keine Problemführung; sonst {"keine": true}
        "abschlussverfolgung": true,
        "allgemein": "<p>…</p>",                  # optional, Text im Abschnitt „Allgemein“ (0)
        "allgemein_dateien": ["Profil/logo.png"], # optional, Dateien darin (wie dateien eines Abschnitts)
        "ki_hinweis_in_allgemein": true,          # optional: KI-Hinweis steht in allgemein, nicht in der
                                                  # Kursbeschreibung (allgemein.anwenden, Profil)
        "vorgeschmack": "…", "steckbrief": {"Lernfeld": "…", "Umfang": "…", "Ergebnis": "…"},
        "so_arbeiten": ["…"],                     # optional, Bausteine für allgemein (allgemein.py)
        "so_arbeiten_titel": "…",                 # optional, Überschrift dazu (Vorgabe „So arbeiten Sie …“)
        "freischaltgruppen": [[2, 3], [4, 5]],    # optional, Kacheln je Meilenstein-Freischaltung (Prüfer 13)
        "kursbild": "bilder/kurs.png",            # optional
        "schule": "BBS …",                        # optional, Aussteller der Abzeichen
        "startdatum": 1790000000,                 # optional, Unix-Zeit
        "typ": "themenkurs"                       # oder "lernfeld": Lernfeldkurs (Wegweiser mit Kacheln je
                                                  # Lernsituation, ohne Noten, Medaillen und Abzeichen;
                                                  # Kacheln ohne eigene Abgabe, lernfeldkurs.py)
      },
      "gruppen": ["Team A", "Team B"],            # leere Gruppen, optional
      "gruppierungen": {"Paare": ["P01", "P02"]}, # optional: Gruppierung → Gruppen (Namen aus gruppen);
                                                  # Aufgaben verweisen über gruppierung darauf
      "allgemein_aktivitaeten": [ … ],            # optional, Aktivitäten oben in „Allgemein“ (Abschnitt 0),
                                                  # unter dem Sternzähler; ohne Note (z. B. das Sternebuch)
      "abschnitte": [                             # Abschnitt 0 legt der Bau an (Text: kurs.allgemein)
        {"name": "1 · Einstieg: …", "zusammenfassung": "<p>…</p>",
         "sichtbar": true, "lehrkraft": false,    # lehrkraft: verborgener Bereich
         "dateien": ["bilder/haus.png"],          # optional, Bilder/Audio der Zusammen-
                                                  # fassung; im HTML als src="haus.png"
         "bild": "bilder/kachel.png",             # optional, Kachelfoto (nur Format tiles)
         "aktivitaeten": [ … ]}
      ],
      "bewertungen": [                            # berechnete Bewertungen im Bewertungsbuch, optional
        {"typ": "berechnet", "name": "Sterne: Kacheltest", "max": 3,
         "formel": "=min(1;floor(round([[test-k2-s3]]/10*100;2)/50))+…",   # [[idnummer]], „;“ (sterne.sternformel)
         "idnummer": "…", "verborgen": false,     # optional: ID-Nummer, für Lernende verborgen
         "im_kursgesamt": true}                   # optional, false: Gewicht 0 (z. B. Stufen-Mittelwerte, stufen.py)
      ],
      "abzeichen": [                              # Kursabzeichen, automatisch vergeben
        {"name": "Medaille Gold", "beschreibung": "…", "bild": "abzeichen/gold.png",
         "aktivitaet": "Ihre Medaille: Gold"}     # Kriterium: Abschluss dieser Aktivität
      ]
    }

Jede Aktivität hat `typ` und `name` und optional:
`kennung` (eindeutig im Kurs, Vorgabe: name; Voraussetzungen und Abzeichen
verweisen darüber – so dürfen z. B. alle Stern-Quiz gleich heißen),
`beschreibung` (HTML), `sichtbar` (bool), `abschluss` (siehe ABSCHLUSS;
„abgabe“ gilt wie „abgeben“),
`voraussetzung`, `tags` (Liste), `idnummer`, `markierungen` (z. B.
["loesung"] – muss verborgen sein), `medaille` ("Grün", "Bronze", …),
`einzug` (ganze Zahl ≥ 0, Einrückung auf der Kursseite; Hilfen unter ihrem
Schritt: 1, siehe allgemein.schrittnummern),
`schritt` (bool, optional: true zählt eine einzeln verborgene Aktivität doch als
Schritt, false nimmt eine sichtbare aus; Vorgabe siehe allgemein.schrittnummern).

`voraussetzung`, eine Bedingung oder eine Liste davon (alle müssen gelten):
    {"aktivitaet": "Abschlusstest", "min": 50, "max": 81}     # Bewertung in %
    {"aktivitaet": "Tipp", "bedingung": "abgeschlossen"}      # oder "bestanden"
    {"abschluss": "Hilfekarte 1", "zustand": "nicht_abgeschlossen"}
    {"bewertung": "kursgesamt", "min": 81, "max": 92}         # Kursgesamt in %
    {"bewertung": "stufe-k1-s-mittel", "min": 85}             # berechnete Bewertung (idnummer oder name) in %
                                                              # (auch mit "bewertet": true; stufen.py)
    {"aktivitaet": "Kurztest", "bewertet": true}              # hat eine Bewertung (Moodle ohne min/max)
    {"oder": [Bedingung, Bedingung, …]}                       # ODER-Gruppe: eine genügt
    {"und": [Bedingung, Bedingung, …]}                        # UND-Gruppe (z. B. als Zweig einer ODER-Gruppe)
    {"nicht": [Bedingung, …]}                                 # Verneinung: nicht alle gelten
    {"gruppe": "G1"}                                          # Mitglied der Gruppe (Name aus gruppen)
Bewertung in %: min heißt „mindestens“, max „kleiner als“ (Moodle availability_grade).
„abschluss“/„zustand“ sind andere Namen für „aktivitaet“/„bedingung“;
Zustände: abgeschlossen, nicht_abgeschlossen, bestanden, nicht_bestanden
(nur bei Tests mit Abschluss „bestanden“: Moodle „abgeschlossen, nicht bestanden“).
optional `"sichtbar_wenn_gesperrt"` (Vorgabe: Bewertung und Gruppe nein, Abschluss ja).
Eine Aktivität mit Gruppenbedingung (z. B. Variantenkarte je Gruppe) ist kein
eigener Schritt (nur_fuer_gruppe).

Typabhängige Felder:
    page       inhalt (HTML), dateien [Bilder; im HTML als src="name.png"],
               docx [Word-Dateien]: je Datei ein Abschnitt mit dem Inhalt und am
               Ende „Als Word herunterladen“, mit Kursschalter pdf_formular und
               Feldern im Blatt davor „Als PDF herunterladen“ (docx_seite.PDF_KNOPF /
               WORD_KNOPF; DOCX, PDF und Bilder liegen in der Seite);
               inhalt oder docx genügt, beides: inhalt zuerst.
               popup (bool): Seite öffnet sich in einem eigenen Fenster, bei
               docx oben ein Download-Knopf je Datei (Profil
               moodle.infoblaetter_popup, gesetzt von allgemein.anwenden);
               rolle "info" | "hilfe" (optional, Infoblatt bzw. Hilfe; siehe sterne.py)
               docx_stil "heft": Seite wie das Blatt (heftauszug.py, Profil
               moodle.infoseiten_wie_heft); dazu docx_pdf [je DOCX das Druck-PDF],
               kacheln {AB-Nummer: Kachel} für „AB n“ → „Kachel k“, breite (px)
    label      text (HTML), dateien
    resource   datei, anzeige "eingebettet" | "download" | "automatisch"
    folder     dateien [Liste]
    url        adresse, anzeige "automatisch" | "eingebettet" | "neues_fenster"
    assign     abgabe ["datei", "onlinetext"], max_dateien, gruppenabgabe (bool),
               punkte, bewertungsraster [{kriterium, beschreibung, punkte}],
               bewertung "punkte" (Vorgabe) | "keine": ohne Note, ohne Eintrag
               im Bewertungsbuch und ohne Rückmeldung; punkte und
               bewertungsraster sind dann nicht erlaubt.
               Raster mit `stufen` [{punkte, bezeichnung, beschreibung}] je
               Kriterium (alle Kriterien, höchste Stufe = punkte): echte Rubrik
               (gradingform_rubric), sonst Tabelle in der Beschreibung;
               raster_vorschau (bool, Vorgabe true; false: Lernende sehen die
               Rubrik erst mit der Bewertung, alwaysshowdefinition 0).
               abgabe_bestaetigen (bool: Entwurf, dann „Abgeben“, submissiondrafts),
               gruppierung (Name aus gruppierungen, nur mit gruppenabgabe),
               bewertungsworkflow (bool: Bewertung erst nach Freigabe sichtbar,
               markingworkflow), dateien [Bilder der Beschreibung, src="name"],
               anhaenge [zusätzliche Dateien der Aufgabe, introattachments],
               im_kursgesamt (bool, Vorgabe true; false: Note bleibt, Gewicht 0
               im Kursgesamt – zählt nicht zu Sternen und Medaillen)
    data       felder [{name, typ: "text"|"textarea"|"number"|"menu"|"checkbox",
               beschreibung, pflicht (bool), optionen [Texte] (nur und Pflicht bei
               menu und checkbox)}], eintraege_fuer_abschluss (Vorgabe 1, nur mit
               abschluss "eintraege"); ohne Bewertung. Der Bau legt Listen-,
               Einzel- und Eingabevorlage als Tabelle an. freigabe (bool):
               Einträge erscheinen erst nach Freigabe durch die Lehrkraft.
               bearbeiten_nach_freigabe (bool, Vorgabe true; false: freigegebene
               Einträge kann nur noch die Lehrkraft ändern, Moodle manageapproved).
               vorlagen {Moodle-Name: Text}: eigene Vorlagen statt der Tabellen,
               Namen wie in Moodle (VORLAGEN: listtemplateheader, listtemplate,
               listtemplatefooter, singletemplate, addtemplate, asearchtemplate,
               csstemplate, jstemplate); [[Feld]] muss ein Feld sein.
    quiz       fragen [Frage], sterne (Höchstpunkte als Sterne der Kurswährung;
               0 = zählt nicht im Kursgesamt, Gewicht 0; siehe sterne.py),
               versuche (0 = unbegrenzt), bewertungsmethode
               ("hoechste" | "durchschnitt" | "erste" | "letzte"), punkte,
               bestehensgrenze_prozent, verhalten ("deferredfeedback" |
               "immediatefeedback" | "interactive"), vollbild (bool),
               glossar_aus (bool), zeit_minuten (0 = ohne Zeitlimit),
               richtige_antwort_zeigen (bool, Vorgabe true; false beim Eingangstest,
               damit die Rückschau keine spätere Entdeckung verrät),
               rueckschau_bewertung (bool, Vorgabe true; false: Rückschau nur mit den
               eigenen Antworten, ohne richtig/falsch, Punkte und Rückmeldungen),
               rolle "stern" (Stern-Quiz „selbst gelöst“, sterne.stern_aktivitaet),
               "test" | "test2" (erster/zweiter Versuch, sterne.zwei_versuche)
    feedback   anonym (bool), elemente [{typ: "likert"|"auswahl"|"text"|"info",
               frage, optionen, mehrfach, kennung (Moodle-Label, z. B. K1; erscheint
               im Export als „(K1) …“), pflicht}], ergebnis_zeigen (bool: Lernende sehen
               die Auswertung, publish_stats)
    glossary   kategorien [Namen], eintraege [{begriff, definition, kategorie,
               bild, bild_alt, bild_quelle (Text unter dem Bild), aliasse [Texte,
               verlinken wie der Begriff], anhang, autoverlinkung (bool, Vorgabe true; false: dieser Eintrag
               wird nicht automatisch verlinkt, z. B. weil er einen Fall auflöst)}], freigabe_noetig (bool),
               autoverlinkung (bool),
               nur_lesen (bool): nur zum Nachschlagen, Lernende können keine
               Einträge anlegen (Rechte-Änderung mod/glossary:write; bei data
               mod/data:writeentry, z. B. Sternzähler „⭐ Meine Sterne“)
    workshop   im Schema vorgesehen, Bau noch nicht unterstützt
    insel      Platzhalter einer Übungsinsel (individueller Lernpfad, inseln.py): nr, name, stufen
               {Grundlagen|Standard|Vertiefung: {uebung: Test, kurztest: Test}}, voraussetzung (ganze
               Insel), start (nur erste Insel). Bau und Prüfung setzen die Aktivitäten ein
               (inseln.einsetzen); dazu kurs.insel_grenzen [50, 85] (optional) und kurs.lernpfad (bool,
               Aktivität „Mein Lernpfad“ in Allgemein, lernpfad.py; Profil moodle.lernpfad_anzeige).

Frage (im Test): typ, name, text (HTML), idnummer, tags, punkte,
allgemeines_feedback, dateien [Bilder im Fragetext, src="name.png"], hinweise [HTML; im Verhalten
„interactive“ ein weiterer Versuch je Hinweis, z. B. Grundlagen-Übungen der Inseln] und je Typ:
    multichoice   antworten [{text, richtig, feedback}], einzige_antwort (bool:
                  eine Antwort genügt, z. B. „Stern abholen“)
    truefalse     richtig (bool), feedback_richtig, feedback_falsch
    shortanswer   antworten [{text, anteil (0–100), feedback}], gross_klein
    numerical     antworten [{wert, toleranz, anteil, feedback}]
    calculated    formel ("{U}/{R}"), variablen [{name, min, max,
                  nachkommastellen}], toleranz (relativ), nachkommastellen,
                  anzahl_datensaetze, plausibel [min, max]
    match         paare [{frage, antwort}], ablenker [Text]
    ddwtos        text mit [[n]], woerter [{text, gruppe}]
    gapselect     text mit [[n]], auswahl [{text, gruppe}]
    ordering      elemente [Text in richtiger Reihenfolge]
    ddmarker      bild, markierungen [{text, anzahl}],
                  zonen [{form, koordinaten, markierung}]
    ddimageortext bild, ziehobjekte [{text, gruppe}], zonen [{x, y, objekt}]
"""
from __future__ import annotations

import re
from pathlib import Path

import inseln

TYPEN = ("page", "label", "resource", "folder", "url", "assign", "quiz",
         "feedback", "glossary", "data", "workshop")
NICHT_UNTERSTUETZT = ("workshop",)

FRAGETYPEN = ("multichoice", "truefalse", "shortanswer", "numerical",
              "calculated", "match", "ddwtos", "gapselect", "ordering",
              "ddmarker", "ddimageortext")

#: andere Schreibweisen einer Abschlussbedingung
ABSCHLUSS_GLEICH = {"abgabe": "abgeben"}
#: erlaubte Abschlussbedingungen je Typ; die erste ist die Vorgabe.
ABSCHLUSS = {
    "page": ("ansehen", "manuell", "keine"),
    "resource": ("ansehen", "manuell", "keine"),
    "folder": ("ansehen", "manuell", "keine"),
    "url": ("ansehen", "manuell", "keine"),
    "glossary": ("ansehen", "manuell", "keine"),
    "label": ("keine",),
    "assign": ("abgeben", "note", "manuell", "keine"),
    "feedback": ("abgeben", "ansehen", "manuell", "keine"),
    "quiz": ("note", "bestanden", "bestanden_oder_versuche", "ansehen",
             "manuell", "keine"),
    "data": ("eintraege", "ansehen", "manuell", "keine"),
    "workshop": ("keine",),
}

PFLICHT = {
    "page": ("inhalt",), "label": ("text",), "resource": ("datei",),
    "folder": ("dateien",), "url": ("adresse",), "quiz": ("fragen",),
    "feedback": ("elemente",), "assign": (), "glossary": (), "workshop": (),
    "data": ("felder",),
}

BEWERTET = ("quiz", "assign")
#: Zustände einer Abschluss-Bedingung → Wert „e“ in Moodles Voraussetzung
#: 3 = COMPLETION_COMPLETE_FAIL („abgeschlossen, nicht bestanden“; nur bei Abschluss „bestanden“, gemessen 5.1.6)
ZUSTAND = {"abgeschlossen": 1, "nicht_abgeschlossen": 0, "bestanden": 2, "nicht_bestanden": 3}
DATENFELDER = ("text", "textarea", "number", "menu", "checkbox")
#: Datenfelder mit Auswahl (Moodle param1: eine Option je Zeile)
DATENFELDER_AUSWAHL = ("menu", "checkbox")
#: eigene Vorlagen einer Datenbank (Feldnamen von mod_data)
VORLAGEN = ("listtemplateheader", "listtemplate", "listtemplatefooter", "singletemplate", "addtemplate",
            "asearchtemplate", "rsstemplate", "rsstitletemplate", "csstemplate", "jstemplate")
#: Kurstypen: Themenkurs (je Lernsituation) und Lernfeldkurs (Wegweiser, ohne Noten und Medaillen)
KURSTYPEN = ("themenkurs", "lernfeld")
FELDVERWEIS = re.compile(r"\[\[([^\[\]#]+)(?:#(?:id|name|description))?\]\]")
#: Rollen eines Tests: Stern-Quiz „selbst gelöst“, erster und zweiter Versuch (sterne.zwei_versuche)
TESTROLLEN = ("stern", "test", "test2")
IDVERWEIS = re.compile(r"\[\[([^\[\]]+)\]\]")
LUECKE = re.compile(r"\[\[(\d+)\]\]")


def abschluss_von(akt: dict) -> str:
    """Die wirksame Abschlussbedingung (Angabe oder Vorgabe je Typ)."""
    if akt.get("abschluss"):
        return ABSCHLUSS_GLEICH.get(akt["abschluss"], akt["abschluss"])
    if akt.get("typ") == "quiz" and akt.get("bestehensgrenze_prozent"):
        return ("bestanden_oder_versuche" if int(akt.get("versuche", 0)) > 0
                else "bestanden")
    return ABSCHLUSS.get(akt.get("typ"), ("keine",))[0]


def bewertet(akt: dict) -> bool:
    """Bekommt die Aktivität eine Note (Eintrag im Bewertungsbuch)?"""
    return akt.get("typ") in BEWERTET and akt.get("bewertung") != "keine"


def nur_fuer_gruppe(akt: dict) -> bool:
    """Steht die Aktivität nur einer Gruppe offen (Gruppenbedingung auf oberster Ebene, z. B. Variantenkarte)?"""
    return any(isinstance(v, dict) and "gruppe" in v for v in voraussetzungen(akt))


def im_kursgesamt(akt: dict) -> bool:
    """Zählt die Note der Aktivität im Kursgesamt (Sterne, Medaillen)? Nein ohne Note, bei `sterne: 0` und bei
    `im_kursgesamt: false` (Gewicht 0)."""
    return bewertet(akt) and akt.get("sterne") != 0 and akt.get("im_kursgesamt", True) is not False


def kennung_von(akt: dict) -> str | None:
    """Eindeutiger Verweisname einer Aktivität (kennung, sonst name)."""
    return akt.get("kennung") or akt.get("name")


#: Pseudo-Abschnitt der Aktivitäten in „Allgemein“ (allgemein_aktivitaeten)
ALLGEMEIN = {"name": "Allgemein", "allgemein": True}


def alle_aktivitaeten(kursdef: dict):
    """(Abschnitt, Aktivität) in Kursreihenfolge; Aktivitäten in „Allgemein“ zuerst (Abschnitt ALLGEMEIN)."""
    for akt in kursdef.get("allgemein_aktivitaeten") or []:
        yield ALLGEMEIN, akt
    for ab in kursdef.get("abschnitte", []):
        for akt in ab.get("aktivitaeten", []):
            yield ab, akt


def pruefe(kursdef: dict, wurzel: Path | None = None) -> list[str]:
    """Alle Formfehler der Kursdefinition als Sätze; leer heißt gültig. Mit
    `wurzel` (Wurzel der Dateien beim Bau) meldet sie auch fehlende Word-Dateien."""
    if inseln.platzhalter(kursdef):   # Übungsinseln: Platzhalter prüfen, dann die eingesetzte Kopie
        f = inseln.pruefe_platzhalter(kursdef)
        return f if f else pruefe(inseln.eingesetzt(kursdef), wurzel)
    f: list[str] = []
    kurs = kursdef.get("kurs") or {}
    for feld in ("vollname", "kurzname", "beschreibung", "ki_hinweis"):
        if not str(kurs.get(feld, "")).strip():
            f.append(f"kurs.{feld} fehlt")
    if "künstlicher Intelligenz" not in str(kurs.get("ki_hinweis", "")):
        f.append("kurs.ki_hinweis muss „… mit Hilfe von künstlicher "
                 "Intelligenz“ enthalten (Punkt 32)")
    if kurs.get("format", "tiles") not in ("topics", "tiles"):
        f.append(f"kurs.format {kurs.get('format')!r}: erlaubt topics, tiles")
    f += _pruefe_kurstyp(kursdef)
    if not kursdef.get("abschnitte"):
        f.append("keine abschnitte")
    for ab in kursdef.get("abschnitte", []):
        dateien = ab.get("dateien", [])
        if not isinstance(dateien, list) or not all(isinstance(d, str) for d in dateien):
            f.append(f"Abschnitt {ab.get('name', '?')!r}: dateien muss eine Liste "
                     f"von Pfaden sein")
        if "bild" in ab and not isinstance(ab["bild"], str):
            f.append(f"Abschnitt {ab.get('name', '?')!r}: bild muss ein Pfad sein")

    f += _pruefe_gruppen(kursdef)
    namen: dict[str, dict] = {}
    # berechnete Bewertungen als Ziel einer Bewertungsbedingung ({"bewertung": idnummer oder name}, stufen.py)
    berechnet = {f"bewertung:{k}": b for b in kursdef.get("bewertungen", []) for k in (b.get("idnummer"), b.get("name"))
                 if k}
    for ab, akt in alle_aktivitaeten(kursdef):
        wo = f"{ab.get('name', '?')} / {akt.get('name', '?')}"
        typ = akt.get("typ")
        for feld in ("inhalt", "text", "beschreibung"):
            if isinstance(akt.get(feld), str):
                f += [f"{wo}: {x}" for x in tex_befunde(akt[feld])]
        if typ not in TYPEN:
            f.append(f"{wo}: unbekannter typ {typ!r}")
            continue
        if typ in NICHT_UNTERSTUETZT:
            f.append(f"{wo}: typ {typ!r} ist vorgesehen, aber noch nicht "
                     f"gebaut – bitte vorerst eine Abgabe (assign) nehmen")
        if not akt.get("name"):
            f.append(f"{wo}: name fehlt")
        elif kennung_von(akt) in namen:
            f.append(f"{wo}: name doppelt – Namen müssen eindeutig sein "
                     f"(sonst eine eindeutige kennung angeben)")
        namen[kennung_von(akt)] = akt
        for feld in PFLICHT.get(typ, ()):
            if typ == "page" and feld == "inhalt" and akt.get("docx"):
                continue
            if not akt.get(feld):
                f.append(f"{wo}: {feld} fehlt oder ist leer")
        if abschluss_von(akt) not in ABSCHLUSS[typ]:
            f.append(f"{wo}: abschluss {akt.get('abschluss')!r} geht bei "
                     f"{typ} nicht (erlaubt: {', '.join(ABSCHLUSS[typ])})")
        if typ == "quiz":
            f += _pruefe_test(akt, wo)
        elif "sterne" in akt:
            f.append(f"{wo}: sterne gibt es nur bei Tests (quiz)")
        if typ == "assign":
            abgabe = akt.get("abgabe", ["datei"])
            if not abgabe or set(abgabe) - {"datei", "onlinetext"}:
                f.append(f"{wo}: abgabe {abgabe!r}: erlaubt datei, onlinetext")
            f += _pruefe_bewertung(akt, wo)
            f += _pruefe_aufgabe(akt, wo, kursdef)
        else:
            f += [f"{wo}: {feld} gibt es nur bei Aufgaben (assign)" for feld in AUFGABE_FELDER if feld in akt]
        if "ergebnis_zeigen" in akt and (typ != "feedback" or not isinstance(akt["ergebnis_zeigen"], bool)):
            f.append(f"{wo}: ergebnis_zeigen gibt es nur bei feedback und nur als true oder false")
        if "schritt" in akt and not isinstance(akt["schritt"], bool):
            f.append(f"{wo}: schritt muss true oder false sein")
        if typ == "data":
            f += _pruefe_datenbank(akt, wo)
        elif "vorlagen" in akt:
            f.append(f"{wo}: vorlagen gibt es nur bei Datenbanken (data)")
        if typ == "page":
            f += _pruefe_seite(akt, wo, wurzel)
        elif "popup" in akt or "docx" in akt:
            f.append(f"{wo}: popup und docx gibt es nur bei Seiten (page)")
        elif "rolle" in akt and not (typ == "quiz" and akt["rolle"] in TESTROLLEN):
            f.append(f"{wo}: rolle {akt['rolle']!r}: bei {typ} nicht erlaubt (Seiten: info, hilfe; "
                     f"Tests: {', '.join(TESTROLLEN)})")
        e = akt.get("einzug", 0)
        if not isinstance(e, int) or isinstance(e, bool) or e < 0:
            f.append(f"{wo}: einzug muss eine ganze Zahl ≥ 0 sein")
        for feld, art in (("freigabe", "data"), ("bearbeiten_nach_freigabe", "data"), ("nur_lesen", ("glossary", "data"))):
            if feld in akt and (typ not in (art if isinstance(art, tuple) else (art,))
                                or not isinstance(akt[feld], bool)):
                f.append(f"{wo}: {feld} gibt es nur bei {art} und nur als true oder false")
        if typ == "glossary":
            kats = akt.get("kategorien", [])
            for e in akt.get("eintraege", []):
                if not e.get("begriff") or not e.get("definition"):
                    f.append(f"{wo}: Glossareintrag ohne begriff/definition")
                if e.get("kategorie") and e["kategorie"] not in kats:
                    f.append(f"{wo}: Kategorie {e['kategorie']!r} fehlt in "
                             f"kategorien")
                al = e.get("aliasse", [])
                if not isinstance(al, list) or not all(isinstance(t, str) and t.strip() for t in al):
                    f.append(f"{wo}: aliasse von {e.get('begriff')!r} muss eine Liste von Texten sein")
                if e.get("bild_quelle") and not e.get("bild"):
                    f.append(f"{wo}: bild_quelle bei {e.get('begriff')!r} ohne bild")

    for akt in kursdef.get("allgemein_aktivitaeten") or []:
        if bewertet(akt):
            f.append(f"Allgemein / {akt.get('name', '?')}: Aktivitäten in Allgemein bekommen keine Note "
                     f"(bewertung „keine“ oder ein Abschnitt)")

    for ab, akt in alle_aktivitaeten(kursdef):
        v = akt.get("voraussetzung")
        if v:
            f += _pruefe_voraussetzung(v, akt, {**namen, **berechnet}, alle_gruppen(kursdef))
    f += _pruefe_bewertungen(kursdef)
    for z in kursdef.get("abzeichen", []):
        ziel = namen.get(z.get("aktivitaet"))
        if not z.get("name") or not z.get("bild"):
            f.append(f"Abzeichen {z.get('name')!r}: name und bild nötig")
        if ziel is None:
            f.append(f"Abzeichen {z.get('name')!r}: Aktivität "
                     f"{z.get('aktivitaet')!r} gibt es nicht")
        elif abschluss_von(ziel) == "keine":
            f.append(f"Abzeichen {z.get('name')!r}: {ziel['name']!r} hat "
                     f"keine Abschlussverfolgung")
    return f


def ist_lernfeldkurs(kursdef: dict) -> bool:
    """Lernfeldkurs (kurs.typ „lernfeld“): Wegweiser zu den Themenkursen, ohne Noten und Medaillen."""
    return (kursdef.get("kurs") or {}).get("typ") == "lernfeld"


def _pruefe_kurstyp(kursdef: dict) -> list[str]:
    """kurs.typ und was ein Lernfeldkurs nicht hat (Noten, Medaillen, Abzeichen, Sternzähler)."""
    kurs = kursdef.get("kurs") or {}
    typ = kurs.get("typ", "themenkurs")
    if typ not in KURSTYPEN:
        return [f"kurs.typ {typ!r}: erlaubt {', '.join(KURSTYPEN)}"]
    allg = kursdef.get("allgemein_aktivitaeten")
    if allg is not None and not isinstance(allg, list):
        return ["allgemein_aktivitaeten muss eine Liste sein"]
    if typ != "lernfeld":
        return []
    f = []
    if kursdef.get("abzeichen") or kursdef.get("bewertungen"):
        f.append("Lernfeldkurs: keine abzeichen und keine bewertungen (Medaillen bleiben in den Themenkursen)")
    if kurs.get("sternzaehler"):
        f.append("Lernfeldkurs: kein sternzaehler (der Kurs hat keine Sterne; das Konto zeigt das Sternebuch)")
    for ab, akt in alle_aktivitaeten(kursdef):
        if bewertet(akt) or akt.get("medaille"):
            f.append(f"Lernfeldkurs / {akt.get('name', '?')}: keine Noten und keine Medaillen")
    return f


def voraussetzungen(akt: dict) -> list[dict]:
    """Die Bedingungen einer Aktivität als Liste (ein dict zählt als eine)."""
    v = akt.get("voraussetzung")
    if not v:
        return []
    return list(v) if isinstance(v, list) else [v]


def ziel_von(v: dict) -> str | None:
    """Name der Aktivität, auf die eine Bedingung zeigt."""
    return v.get("aktivitaet", v.get("abschluss"))


def zustand_von(v: dict) -> str:
    """Geforderter Abschlusszustand einer Abschluss-Bedingung."""
    return v.get("zustand", v.get("bedingung", "abgeschlossen"))


def _pruefe_voraussetzung(v, akt: dict, namen: dict, gruppen=None) -> list[str]:
    if isinstance(v, list):
        return [s for b in v for s in _pruefe_bedingung(b, akt, namen, gruppen)]
    return _pruefe_bedingung(v, akt, namen, gruppen)


def _bereich_ok(v: dict) -> bool:
    lo, hi = v.get("min", 0), v.get("max")
    return 0 <= lo <= 100 and (hi is None or lo < hi <= 100)


def _pruefe_bedingung(v, akt: dict, namen: dict, gruppen=None) -> list[str]:
    wo = f"{akt.get('name')}: voraussetzung"
    if not isinstance(v, dict):
        return [f"{wo}: {v!r} ist keine Bedingung"]
    if "oder" in v:
        if not isinstance(v["oder"], list) or not v["oder"]:
            return [f"{wo}: oder braucht eine nicht leere Liste von Bedingungen"]
        return [s for b in v["oder"] for s in _pruefe_bedingung(b, akt, namen, gruppen)]
    for gruppe in ("nicht", "und"):
        if gruppe in v:
            if not isinstance(v[gruppe], list) or not v[gruppe]:
                return [f"{wo}: {gruppe} braucht eine nicht leere Liste von Bedingungen"]
            return [s for b in v[gruppe] for s in _pruefe_bedingung(b, akt, namen, gruppen)]
    if "gruppe" in v:
        if v["gruppe"] not in (gruppen or ()):
            return [f"{wo}: Gruppe {v['gruppe']!r} gibt es nicht (gruppen)"]
        return []
    if "bewertung" in v:
        if v["bewertung"] != "kursgesamt" and f"bewertung:{v['bewertung']}" not in namen:
            return [f"{wo}: bewertung {v['bewertung']!r}: erlaubt kursgesamt oder eine berechnete Bewertung "
                    "(idnummer oder name aus bewertungen)"]
        if v.get("bewertet") is not None and (v["bewertet"] is not True or "min" in v or "max" in v):
            return [f"{wo}: bewertet nur als true und ohne min/max"]
        if not _bereich_ok(v):
            return [f"{wo}: Bereich {v.get('min', 0)}–{v.get('max')} % ist ungültig"]
        return []
    ziel = namen.get(ziel_von(v))
    if ziel is None:
        return [f"{wo} zeigt auf {ziel_von(v)!r}, die es nicht gibt"]
    if ziel is akt:
        return [f"{wo} zeigt auf sich selbst"]
    if v.get("bewertet") is not None:
        if v["bewertet"] is not True or "min" in v or "max" in v:
            return [f"{wo}: bewertet nur als true und ohne min/max"]
        if not bewertet(ziel):
            return [f"{wo}: {ziel['name']!r} wird nicht bewertet"]
        return []
    if "min" in v or "max" in v:
        if not bewertet(ziel):
            return [f"{wo}: {ziel['name']!r} wird nicht bewertet"]
        if not _bereich_ok(v):
            return [f"{wo}: Bereich {v.get('min', 0)}–{v.get('max')} % ist ungültig"]
        return []
    bed = zustand_von(v)
    if bed not in ZUSTAND:
        return [f"{wo}: zustand {bed!r}: erlaubt {', '.join(ZUSTAND)}"]
    ab = abschluss_von(ziel)
    if ab == "keine":
        return [f"{wo}: {ziel['name']!r} hat keine Abschlussverfolgung"]
    if bed in ("bestanden", "nicht_bestanden") and not ab.startswith("bestanden"):
        return [f"{wo}: {ziel['name']!r} kann nicht bestanden (und nicht nicht bestanden) werden"]
    return []


def alle_gruppen(kursdef: dict) -> list[str]:
    """Namen der Gruppen des Kurses (gruppen), in Reihenfolge."""
    return list(kursdef.get("gruppen") or [])


def _pruefe_gruppen(kursdef: dict) -> list[str]:
    """gruppen eindeutig, gruppierungen {Name: [Gruppen aus gruppen]}."""
    f = []
    gruppen = kursdef.get("gruppen") or []
    if not isinstance(gruppen, list) or not all(isinstance(g, str) and g.strip() for g in gruppen):
        return ["gruppen muss eine Liste von Namen sein"]
    if len(set(gruppen)) != len(gruppen):
        f.append("gruppen: Name doppelt")
    gg = kursdef.get("gruppierungen") or {}
    if not isinstance(gg, dict):
        return f + ["gruppierungen muss ein Objekt {Name: [Gruppen]} sein"]
    for name, liste in gg.items():
        if not isinstance(liste, list) or not liste:
            f.append(f"Gruppierung {name!r}: braucht eine nicht leere Liste von Gruppen")
            continue
        for g in liste:
            if g not in gruppen:
                f.append(f"Gruppierung {name!r}: Gruppe {g!r} fehlt in gruppen")
    return f


#: Felder, die es nur bei Aufgaben gibt
AUFGABE_FELDER = ("abgabe_bestaetigen", "gruppierung", "bewertungsworkflow", "anhaenge", "im_kursgesamt",
                  "raster_vorschau")


def raster_mit_stufen(akt: dict) -> bool:
    """Bewertungsraster als echte Rubrik (jedes Kriterium mit stufen)?"""
    raster = akt.get("bewertungsraster") or []
    return bool(raster) and all(k.get("stufen") for k in raster)


def _pruefe_aufgabe(akt: dict, wo: str, kursdef: dict) -> list[str]:
    """Aufgabe: Schalter, Gruppierung, Dateien und Rubrik mit Stufen."""
    f = []
    for feld in ("abgabe_bestaetigen", "bewertungsworkflow", "im_kursgesamt", "raster_vorschau"):
        if feld in akt and not isinstance(akt[feld], bool):
            f.append(f"{wo}: {feld} muss true oder false sein")
    if akt.get("gruppierung") is not None:
        if akt["gruppierung"] not in (kursdef.get("gruppierungen") or {}):
            f.append(f"{wo}: Gruppierung {akt['gruppierung']!r} gibt es nicht (gruppierungen)")
        if not akt.get("gruppenabgabe"):
            f.append(f"{wo}: gruppierung wirkt nur mit gruppenabgabe")
    for feld in ("dateien", "anhaenge"):
        d = akt.get(feld, [])
        if not isinstance(d, list) or not all(isinstance(x, str) for x in d):
            f.append(f"{wo}: {feld} muss eine Liste von Pfaden sein")
    if akt.get("im_kursgesamt") is False and not bewertet(akt):
        f.append(f"{wo}: im_kursgesamt false braucht eine Note (bewertung „punkte“)")
    raster = akt.get("bewertungsraster") or []
    if any(k.get("stufen") for k in raster) and not raster_mit_stufen(akt):
        f.append(f"{wo}: stufen bei allen Kriterien des Rasters oder bei keinem")
    for k in raster if raster_mit_stufen(akt) else []:
        punkte = [s.get("punkte") for s in k["stufen"]]
        if not all(isinstance(p, (int, float)) and not isinstance(p, bool) and p >= 0 for p in punkte):
            f.append(f"{wo}: Kriterium {k.get('kriterium')!r}: jede Stufe braucht punkte ≥ 0")
        elif len(set(punkte)) != len(punkte):
            f.append(f"{wo}: Kriterium {k.get('kriterium')!r}: Punkte einer Stufe doppelt")
        elif max(punkte) != k.get("punkte"):
            f.append(f"{wo}: Kriterium {k.get('kriterium')!r}: höchste Stufe {max(punkte)} ≠ punkte {k.get('punkte')}")
        if not all(str(s.get("bezeichnung") or s.get("beschreibung") or "").strip() for s in k["stufen"]):
            f.append(f"{wo}: Kriterium {k.get('kriterium')!r}: jede Stufe braucht bezeichnung oder beschreibung")
    return f


def _pruefe_bewertungen(kursdef: dict) -> list[str]:
    """Berechnete Bewertungen (`bewertungen`, z. B. Sterne je Testpaar): Formel mit „=“, Verweise [[idnummer]] auf
    bewertete Aktivitäten, max > 0."""
    f = []
    ids = {a.get("idnummer"): a for _, a in alle_aktivitaeten(kursdef) if a.get("idnummer")}
    for b in kursdef.get("bewertungen", []):
        wo = f"Bewertung {b.get('name')!r}"
        if b.get("typ") != "berechnet" or not b.get("name"):
            f.append(f"{wo}: typ „berechnet“ und name nötig")
        formel = str(b.get("formel") or "")
        if not formel.startswith("="):
            f.append(f"{wo}: formel muss mit „=“ beginnen")
        for idn in IDVERWEIS.findall(formel):
            if idn not in ids or not bewertet(ids[idn]):
                f.append(f"{wo}: formel zeigt auf [[{idn}]], keine bewertete Aktivität hat diese idnummer")
        m = b.get("max")
        if not isinstance(m, (int, float)) or isinstance(m, bool) or m <= 0:
            f.append(f"{wo}: max muss eine Zahl > 0 sein")
    return f


def _pruefe_bewertung(akt: dict, wo: str) -> list[str]:
    """Abgabe: „bewertung“ und was dazu passt."""
    art = akt.get("bewertung", "punkte")
    if art not in ("punkte", "keine"):
        return [f"{wo}: bewertung {art!r}: erlaubt punkte, keine"]
    if art == "punkte":
        return []
    f = [f"{wo}: bewertung „keine“ verträgt kein {feld} (keine Note)"
         for feld in ("punkte", "bewertungsraster") if feld in akt]
    if abschluss_von(akt) == "note":
        f.append(f"{wo}: abschluss „note“ geht nicht bei bewertung „keine“ "
                 f"(abgeben nehmen)")
    return f


def _pruefe_seite(akt: dict, wo: str, wurzel: Path | None) -> list[str]:
    """Seite: Word-Dateien, Pop-up und Rolle."""
    f = []
    if "popup" in akt and not isinstance(akt["popup"], bool):
        f.append(f"{wo}: popup muss true oder false sein")
    if akt.get("rolle") not in (None, "info", "hilfe"):
        f.append(f"{wo}: rolle {akt['rolle']!r}: erlaubt info, hilfe")
    if akt.get("docx_stil") not in (None, "heft"):
        f.append(f"{wo}: docx_stil {akt['docx_stil']!r}: erlaubt heft")
    if "breite" in akt and (not isinstance(akt["breite"], int) or isinstance(akt["breite"], bool)
                            or not 300 <= akt["breite"] <= 1200):
        f.append(f"{wo}: breite muss eine ganze Zahl zwischen 300 und 1200 (px) sein")
    for rel in akt.get("docx_pdf") or []:
        if not str(rel).lower().endswith(".pdf"):
            f.append(f"{wo}: docx_pdf {rel!r} ist keine PDF-Datei")
        elif wurzel is not None and not (Path(wurzel) / rel).is_file():
            f.append(f"{wo}: PDF-Datei {rel!r} fehlt unter {wurzel}")
    if "docx" not in akt:
        return f
    liste = akt["docx"]
    if not isinstance(liste, list) or not all(isinstance(d, str) for d in liste):
        return f + [f"{wo}: docx muss eine Liste von Pfaden sein"]
    for rel in liste:
        if not rel.lower().endswith(".docx"):
            f.append(f"{wo}: docx {rel!r} ist keine Word-Datei (.docx)")
        elif wurzel is not None and not (Path(wurzel) / rel).is_file():
            f.append(f"{wo}: Word-Datei {rel!r} fehlt unter {wurzel}")
    return f


def _pruefe_datenbank(akt: dict, wo: str) -> list[str]:
    """Datenbank: Felder und Abschluss über Einträge."""
    f = []
    gesehen = set()
    for feld in akt.get("felder", []):
        name = str(feld.get("name", "")).strip()
        if not name:
            f.append(f"{wo}: Datenbankfeld ohne name")
            continue
        # Moodle lehnt [ ] in Feldnamen ab; # stört die Vorlagen ([[name#id]]).
        if re.search(r"[\[\]#]", name):
            f.append(f"{wo}: Feldname {name!r} darf kein [, ] oder # enthalten")
        if name.lower() in gesehen:
            f.append(f"{wo}: Feldname {name!r} doppelt")
        gesehen.add(name.lower())
        typ = feld.get("typ", "text")
        if typ not in DATENFELDER:
            f.append(f"{wo}: Feld {name!r}: typ {feld.get('typ')!r} "
                     f"(erlaubt: {', '.join(DATENFELDER)})")
        optionen = feld.get("optionen")
        if typ in DATENFELDER_AUSWAHL:
            if (not isinstance(optionen, list) or not optionen
                    or not all(isinstance(o, str) and o.strip() and "\n" not in o for o in optionen)):
                f.append(f"{wo}: Feld {name!r}: optionen muss eine Liste einzeiliger Texte sein")
            elif len(set(optionen)) != len(optionen):
                f.append(f"{wo}: Feld {name!r}: Option doppelt")
        elif optionen is not None:
            f.append(f"{wo}: Feld {name!r}: optionen gibt es nur bei {', '.join(DATENFELDER_AUSWAHL)}")
    vorlagen = akt.get("vorlagen", {})
    if not isinstance(vorlagen, dict):
        f.append(f"{wo}: vorlagen muss ein Objekt {{Moodle-Name: Text}} sein")
        vorlagen = {}
    for name, text in vorlagen.items():
        if name not in VORLAGEN:
            f.append(f"{wo}: Vorlage {name!r} gibt es nicht (erlaubt: {', '.join(VORLAGEN)})")
        elif not isinstance(text, str):
            f.append(f"{wo}: Vorlage {name!r} muss Text sein")
        elif name not in ("csstemplate", "jstemplate"):
            for ziel in FELDVERWEIS.findall(text):
                if ziel.strip().lower() not in gesehen:
                    f.append(f"{wo}: Vorlage {name!r} nennt [[{ziel}]], das Feld gibt es nicht")
    n = akt.get("eintraege_fuer_abschluss")
    if abschluss_von(akt) == "eintraege":
        if n is not None and (not isinstance(n, int) or n < 1):
            f.append(f"{wo}: eintraege_fuer_abschluss muss eine Zahl ≥ 1 sein")
    elif n is not None:
        f.append(f"{wo}: eintraege_fuer_abschluss wirkt nur mit abschluss "
                 f"„eintraege“")
    return f


def _pruefe_test(akt: dict, wo: str) -> list[str]:
    f = []
    if "sterne" in akt:
        s = akt["sterne"]
        if not isinstance(s, int) or isinstance(s, bool) or s < 0:
            f.append(f"{wo}: sterne muss eine ganze Zahl ≥ 0 sein")
        elif s > 0 and "punkte" in akt:
            f.append(f"{wo}: sterne und punkte zugleich – sterne sind die Punkte")
    ab = abschluss_von(akt)
    if ab.startswith("bestanden") and not akt.get("bestehensgrenze_prozent"):
        f.append(f"{wo}: „bestanden“ braucht bestehensgrenze_prozent")
    if ab == "bestanden_oder_versuche" and int(akt.get("versuche", 0)) < 1:
        f.append(f"{wo}: „alle Versuche verbraucht“ braucht versuche ≥ 1")
    if akt.get("bewertungsmethode", "hoechste") not in (
            "hoechste", "durchschnitt", "erste", "letzte"):
        f.append(f"{wo}: bewertungsmethode {akt['bewertungsmethode']!r}")
    ids = [q.get("idnummer") for q in akt.get("fragen", []) if q.get("idnummer")]
    if len(ids) != len(set(ids)):
        f.append(f"{wo}: idnummer einer Frage doppelt")
    for q in akt.get("fragen", []):
        f += [f"{wo} / Frage {q.get('name', '?')}: {m}" for m in pruefe_frage(q)]
    return f


TEX = re.compile(r"\\\((.*?)\\\)", re.S)


def _ohne_text(tex: str) -> str:
    """TeX ohne \\text{…}, \\mathrm{…} und \\operatorname{…} (darin sind Wörter und Sonderzeichen erlaubt)."""
    return re.sub(r"\\(?:text|mathrm|operatorname)\s*\{[^{}]*\}", "", tex)


def tex_befunde(html: str, variablen: set[str] = frozenset()) -> list[str]:
    """Fallen im Mathemodus \\( … \\) (Sichtprüfung LS 3): Zeichen außerhalb von ASCII wie €, °, Ω ergeben in MathJax
    „Math input error“ (\\text{€}, \\Omega, \\cdot schreiben); in berechneten Fragen setzt Moodle für {Q} in
    \\frac{Q}{I} die Zufallszahl ein, wenn Q eine Variable ist (\\frac QI oder \\mathit Q schreiben)."""
    f = []
    for tex in TEX.findall(html or ""):
        fremd = sorted({z for z in _ohne_text(tex) if ord(z) > 127})
        if fremd:
            f.append(f"Zeichen {''.join(fremd)!r} im Mathemodus außerhalb von \\text{{}}: {tex[:40]!r}")
        for m in re.finditer(r"(\\frac|\\mathit|\\mathrm|[_^}])\s*\{([A-Za-z_]\w*)\}", tex):
            if m.group(2) in variablen:
                f.append(f"Formelzeichen {{{m.group(2)}}} heißt wie eine Variable und wird ersetzt: {tex[:40]!r}")
    return f


def pruefe_frage(q: dict) -> list[str]:
    """Formfehler einer Frage."""
    t = q.get("typ")
    if t not in FRAGETYPEN:
        return [f"unbekannter typ {t!r}"]
    f = []
    if not q.get("name"):
        f.append("name fehlt")
    if not str(q.get("text", "")).strip():
        f.append("text fehlt")
    d = q.get("dateien", [])
    if not isinstance(d, list) or not all(isinstance(x, str) for x in d):
        f.append("dateien muss eine Liste von Pfaden sein")
    h = q.get("hinweise", [])
    if not isinstance(h, list) or not all(isinstance(x, str) and x.strip() for x in h):
        f.append("hinweise muss eine Liste von Texten sein")
    if t == "multichoice":
        a = q.get("antworten", [])
        if (len(a) < (1 if q.get("einzige_antwort") else 2)
                or not any(x.get("richtig") for x in a)):
            f.append("mindestens zwei Antworten, davon eine richtig")
    elif t == "truefalse" and not isinstance(q.get("richtig"), bool):
        f.append("richtig muss true oder false sein")
    elif t == "shortanswer":
        if not any(float(x.get("anteil", 100)) == 100 for x in q.get("antworten", [])):
            f.append("keine Antwort mit anteil 100")
    elif t == "numerical":
        a = q.get("antworten", [])
        if not a or any(not isinstance(x.get("wert"), (int, float)) for x in a):
            f.append("antworten brauchen einen Zahlenwert 'wert'")
    elif t == "calculated":
        if not q.get("formel"):
            f.append("formel fehlt")
        namen = {v.get("name") for v in q.get("variablen", [])}
        genannt = set(re.findall(r"\{([A-Za-z_]\w*)\}", q.get("formel", "")))
        if genannt - namen:
            f.append(f"Platzhalter ohne Variable: {sorted(genannt - namen)}")
        for v in q.get("variablen", []):
            if not ("min" in v and "max" in v and v["min"] <= v["max"]):
                f.append(f"Variable {v.get('name')}: min/max fehlen")
    elif t == "match":
        if len(q.get("paare", [])) < 2 or len(q.get("paare", [])) + len(
                q.get("ablenker", [])) < 3:
            f.append("mindestens zwei paare und drei Antworten (mit ablenker)")
    elif t in ("ddwtos", "gapselect"):
        auswahl = q.get("woerter" if t == "ddwtos" else "auswahl", [])
        luecken = [int(n) for n in LUECKE.findall(q.get("text", ""))]
        if not luecken:
            f.append("keine Lücke [[n]] im text")
        if any(not 1 <= n <= len(auswahl) for n in luecken):
            f.append("eine Lücke zeigt auf keine Auswahl")
    elif t == "ordering":
        if len(q.get("elemente", [])) < 3:
            f.append("mindestens drei elemente")
    elif t == "ddmarker":
        if not q.get("bild") or not q.get("markierungen") or not q.get("zonen"):
            f.append("bild, markierungen und zonen nötig")
        for z in q.get("zonen", []):
            if z.get("form") not in ("circle", "rectangle", "polygon"):
                f.append(f"Zonenform {z.get('form')!r}")
            if not 1 <= int(z.get("markierung", 0)) <= len(q.get("markierungen", [])):
                f.append("Zone zeigt auf keine Markierung")
    elif t == "ddimageortext":
        if not q.get("bild") or not q.get("ziehobjekte") or not q.get("zonen"):
            f.append("bild, ziehobjekte und zonen nötig")
        for z in q.get("zonen", []):
            if not 1 <= int(z.get("objekt", 0)) <= len(q.get("ziehobjekte", [])):
                f.append("Zone zeigt auf kein Ziehobjekt")
    namen = {v.get("name") for v in q.get("variablen", [])} if t == "calculated" else set()
    texte = [q.get("text", ""), q.get("allgemeines_feedback", "")] + [
        str(x.get(k, "")) for x in q.get("antworten", []) if isinstance(x, dict) for k in ("text", "rueckmeldung")]
    for txt in texte:
        f += tex_befunde(str(txt), namen)
    return f


class KursdefinitionFehler(ValueError):
    """Die Kursdefinition ist nicht baubar."""


def pruefe_oder_abbrechen(kursdef: dict, wurzel: Path | None = None) -> None:
    fehler = pruefe(kursdef, wurzel)
    if fehler:
        raise KursdefinitionFehler("Kursdefinition ungültig:\n- "
                                   + "\n- ".join(fehler))
