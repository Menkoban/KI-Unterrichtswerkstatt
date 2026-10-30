---
name: jahresplanung
description: Schritt 03 der Unterrichtspipeline: Jahresplanung als Schuljahres-Akte je Klasse (Bildungsgang, Ausbildungsjahr, Schuljahr). Legt die Lernfelder des Jahres mit Zeitrichtwert fest, ordnet sie erst mit Stundenplan den Unterrichtswochen zu, Kalender aus amtlicher Quelle, Organisationsform als Einstellung; eigene Lernfelder werden bis auf die Lernsituationen vorbereitet. Verwende ihn, wenn die Schuljahres-Akte fehlt, eine Schulplanung hochgeladen wird oder die Lehrkraft „Jahresplanung“, „Schuljahr planen“, „wann läuft welches Lernfeld“ sagt.
---
> Werkzeug-Ordner dieses Skills: `unterrichtspipeline-referendariat/`. Alle Pfade und Befehle hier gelten relativ dazu (vorher `cd unterrichtspipeline-referendariat`). Quelle: `unterrichtspipeline-referendariat/.claude/skills/jahresplanung/`.

# Jahresplanung (Schritt 03)

Grundlage: `docs/ARBEITSWEISE.md` (gilt immer), `docs/KONZEPT.md`, „Schritt 03 — Festlegungen“.
Beispiel-Daten: `beispiele/daten/jahresplanung/2026-27_EG1.json`.

## Ablauf

1. **Vorhandenes zuerst:** Gibt es eine Schulplanung (Jahresplanung, Stundenplan,
   Stundentafel)? Wenn ja: hochladen lassen, analysieren, übernehmen, abgleichen.
   Wenn nein oder unbekannt: durchplanen, Stand bleibt Entwurf bis zum Abgleich.
2. **Angaben erfragen, je eine Frage** (Profil `interview.*`): Klasse und Bildungsgang,
   Ausbildungsjahr, Organisationsform (Teilzeit/Block, Berufsschultage), welche
   Lernfelder die Lehrkraft selbst unterrichtet. Wochentage und Stundentafel, wenn bekannt.
3. **Kalender nie aus dem Gedächtnis:** Ferien nur aus einer Datei mit amtlicher Quelle
   und Abrufdatum (`jahresplanung/ferien_<land>_<schuljahr>.json`); fehlt sie, beim
   Kultusministerium abrufen und als solche Datei ablegen. Feiertage rechnet
   `jahresplanung/kalender.py`.
4. **Lernfelder und Zeitrichtwerte** aus dem Rahmenlehrplan in `Quellen/` lesen
   (Übersicht der Lernfelder), nie schätzen.
5. **Planungsdaten** schreiben: `<arbeitsbereich>/.daten/jahresplanung/<schuljahr>_<klasse>.json`
   (Aufbau wie das Beispiel `2026-27_EG1.json`), dann erzeugen:
   `python jahresplanung/jahresplanung.py <arbeitsbereich> <schuljahr>_<klasse>`.
   Ergebnis: `Unterricht/<Fach>/<schuljahr>_<klasse>/Jahresplanung.docx` und Steckbrief.
6. **Prüfbericht** im Dokument (Fehler, Warnung, Hinweis): Quelle der Ferien, offene
   Annahmen (Wochentage, Stundentafel), Zeitrichtwert gegen verfügbare Stunden,
   Abweichungen von Rahmenlehrplan oder Schule ausgewiesen.
7. **Stundenplan hochladen (jederzeit, auch nachträglich):** Foto, PDF, Excel oder Text in
   `Eingang/` oder im Chat. Analysieren: je eigenem Lernfeld Wochentag(e) und Stunden;
   Unklares mit **einer** Frage klären. Eintragen in die Planungsdaten als
   `"stundenplan": {"quelle": "<Datei, Datum>", "lernfelder": {"1": [{"tag": "Di", "std": 2}]}}`,
   neu erzeugen. Ergebnis: jede Stunde des Lernfelds mit Datum, verfügbare Stunden gegen
   Zeitrichtwert (Abweichung im Prüfbericht). Das Dokument wandert nach `Unterlagen/`.
   Ändert sich die Zuordnung, sind Stunden-Akten mit Datum davon betroffen: im Prüfbericht nennen.
8. **Freigabe** durch die Lehrkraft: `python akten/steckbrief.py freigeben <arbeitsbereich> <pfad>`,
   Stand-Text in den Daten anpassen, neu erzeugen, `python akten/akten.py` ohne Fehler.

## Regeln

- **Ohne Stundenplan keine Zuordnung zu Wochen und Tagen** (Lehrkraft 2026-10-11): die
  Zeitrichtwerte werden chronologisch durchgeplant (Stunde 1 bis n auf der Lernfeld-Ebene);
  der Kalender dient nur als Rahmen. Erst mit Stundenplan (Stunden je Lernfeld und Woche,
  Wochentage) wird zugeordnet und geprüft, ob die Termine reichen.

- Kompetenzfeststellung liegt vorrangig in den Lernsituationen (Handlungsprodukt); Puffer und Klassenarbeit setzt die Lehrkraft (LF 1 EG: Klassenarbeit am Ende des Lernfelds).
- Umschichtungen von Zeitrichtwerten nur ausgewiesen und mit der Schule abgesprochen.
- Lernsituationen werden erst auf der Lernfeld-Ebene eingesetzt (Planung streng hierarchisch).
