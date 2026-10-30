---
name: klassenakte
description: Schritte 05 und 06 (Klassenteil) der Unterrichtspipeline: legt die Klassen-Akte einer Klasse an oder pflegt sie, also Bedingungsfeld nach Seminar-Leitfaden 1.1 bis 1.5 mit Konsequenz je Bedingung, drei Personas, allgemeine Lernausgangslage und kommentierten Sitzplan (Bild aus dem Sitzplan-Studio, darunter die Kommentartabelle mit Noten). Ohne echte Klasse entsteht eine gekennzeichnete Musterklasse. Verwende ihn, wenn für eine Stunde oder einen Besuch die Klasse fehlt oder sich geändert hat, oder bei „Klasse anlegen“, „Sitzplan“, „Bedingungsfeld“, „Personas“, „Noten eintragen“.
---
> Werkzeug-Ordner dieses Skills: `unterrichtspipeline-referendariat/`. Alle Pfade und Befehle hier gelten relativ dazu (vorher `cd unterrichtspipeline-referendariat`). Quelle: `unterrichtspipeline-referendariat/.claude/skills/klassenakte/`.

# Klassen-Akte (Schritte 05 und 06, Klassenteil)

Grundlage: `docs/ARBEITSWEISE.md`, `docs/KONZEPT.md` Abschnitte „05 Bedingungsfeld + Sitzplan“,
„06 Lernausgangslage“. Beispiel-Daten: `.daten/klasse/<Schuljahr>_<Klasse>.json` im Arbeitsbereich (z. B. eine Musterklasse).

## Ablauf

1. **Vorhandenes zuerst:** Gibt es Klassenliste, Notenliste, Sitzplan, Förderpläne oder
   Nachteilsausgleiche? Hochladen lassen und übernehmen; Namen sofort durch Kürzel S01 … ersetzen.
   Gibt es keine echte Klasse, eine **Musterklasse** anlegen (`"musterklasse": true`, im Text
   „[Musterklasse, fiktiv]“).
2. **Interview, je eine Frage** mit drei Vorschlägen (empfohlener zuerst, freie Antwort):
   Raum und Sitzordnung, Zusammensetzung (Vorbildung, Alter, Sprache, Betriebe), Leistungsstand,
   besondere Bedarfe, drei Personas, Noten (schriftlich, sonstige).
3. **Daten** `.daten/klasse/<schuljahr>_<klasse>.json`: Raum (Reihen), Lernende mit Kürzel, Platz
   [Reihe, Platz], Niveau, Kurzbeschreibung, Kommentar, Noten; Daten zur Klasse (Statistik nach
   Seminar), drei Personas mit vorhandenem Kürzel, Abschnitte 1.1 bis 1.5 mit Konsequenz,
   Lernausgangslage je Bereich mit Quelle.
4. **Erzeugen:** `python klasse/klassenakte.py <arbeitsbereich> <kurzname>` → `Bedingungsfeld.docx`,
   `Lernausgangslage.docx`, `Sitzplan.docx` und `Sitzplan.png` im Klassenordner. Das Bild macht
   `klasse/sitzplan_bild.py` aus `klasse/sitzplan_studio.html` (Kopie des Artefakts „Sitzplan-Studio“):
   Beginner grün, Könner blau, Experte violett; Personas 1 bis 3; Punkte orange (Deutsch als
   Zweitsprache) und rot (Unterstützungsbedarf).
5. **Prüfbericht** zeigen (Fehler, Warnung, Hinweis), dann Freigabe je Datei mit
   `python akten/steckbrief.py freigeben <arbeitsbereich> <pfad>`; Zeile in `docs/KONZEPT.md`,
   commit und push im Arbeitsbereich.

## Regeln

- Nur Kürzel, nie Namen; der Generator prüft Anzahl, Plätze, Summen von Vorbildung und Niveaus.
- Das Feld Niveau in den Klassendaten beschreibt nur den Leistungsstand der Lernenden
  (Sitzplanfarben, Noten); die Planung arbeitet seit 2026-10-13 auf **einem** Niveau
  (Lehrkraft, gilt für Pipeline 1 und 2).
- Noten bei einer Musterklasse fiktiv und passend zum Niveau (Beginner 3 bis 5, Könner 2 bis 4,
  Experte 1 bis 3), mit Hinweis im Dokument.
- Der kommentierte Sitzplan mit personenbezogenen Daten wird nur passwortgeschützt versendet.
- Die Klassen-Akte wächst mit den Nachbereitungen (Skill `nachbereitung`, Ablage „Klasse“).
