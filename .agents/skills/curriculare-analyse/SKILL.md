---
name: curriculare-analyse
description: Schritt 01 der Unterrichtspipeline: Curriculare Analyse eines Lernfelds aus dem Rahmenlehrplan. Zerlegt den Lernfeldtext eng am Wortlaut in Lernfeld-Kompetenzen (LK-01 …) nach Phasen der vollständigen Handlung, konkretisiert die Inhalte (Pflicht, Optional, Verschoben), grenzt gegen Nachbar-Lernfelder ab und ordnet den Lernort Betrieb zu. Gilt für alle Fachrichtungen eines Berufs mit gemeinsamem Lernfeld. Verwende ihn, wenn für ein Lernfeld noch keine curriculare Analyse vorliegt oder die Lehrkraft „Lernfeld analysieren“, „was steht im Rahmenlehrplan zu LF …“, „Lernfeldkompetenzen“ sagt.
---
> Werkzeug-Ordner dieses Skills: `unterrichtspipeline-referendariat/`. Alle Pfade und Befehle hier gelten relativ dazu (vorher `cd unterrichtspipeline-referendariat`). Quelle: `unterrichtspipeline-referendariat/.claude/skills/curriculare-analyse/`.

# Curriculare Analyse (Schritt 01)

Grundlage: `docs/ARBEITSWEISE.md` (gilt immer), `docs/KONZEPT.md` „Schritt 01 — Festlegungen“.
Beispiel-Daten: `beispiele/daten/curriculare_analyse/lf01_elektroniker.json`.

## Ablauf

1. **Vorhandenes zuerst:** Gibt es ein schulisches Curriculum (SchuCu) oder eine Analyse der
   Schule? Wenn ja, hochladen lassen und übernehmen bzw. abgleichen.
2. **Quelle lesen:** Rahmenlehrplan aus `Quellen/` (Seite des Lernfelds und Liste der
   Entsprechungen). Nie aus dem Gedächtnis. Gilt das Lernfeld für mehrere Fachrichtungen,
   wird die Analyse **einmal** erstellt und gilt für alle (die Skizze kommt je Fachrichtung).
3. **Entwurf schreiben** (`.daten/curriculare_analyse/<kurz>.json`):
   - **LK** eng am Lehrplanwortlaut, geordnet nach Informieren … Bewerten, je mit Phase,
     grobem AFB und Kompetenzbereich (FK, SoK, SeK, MK); keine weitere Zerlegung.
   - **Inhalte aus dem Lehrplantext** (die Klammer-Stichworte) und **Inhaltskatalog**:
     Pflicht, Optional, Verschoben; als eigene Konkretisierung gekennzeichnet.
   - **Abgrenzung** gegen alle Nachbar-Lernfelder desselben und des folgenden Jahres, die
     Inhalte berühren; Abweichungen der Praxis vom Lehrplantext ausweisen.
   - **Querschnittsthemen** nur, wenn ausdrücklich genannt; **Lernort Betrieb** aus der
     Liste der Entsprechungen.
4. **Mit der Lehrkraft klären, je eine Frage** (drei gleich ausführliche Vorschläge):
   Inhaltskatalog (was Pflicht, was optional, was verschoben), Abgrenzung, wo die Praxis
   vom Lehrplan abweicht.
5. **Erzeugen:** `python lernfeld/curriculare_analyse.py <arbeitsbereich> <kurz>` →
   `<ordner>/Curriculare_Analyse.docx`. Die Befunde des Generators stehen im Prüfbericht.
6. **Freigabe** nach Prüfbericht; `python akten/steckbrief.py freigeben <arbeitsbereich>
   <pfad>`, Stand-Text in den Daten anpassen, neu erzeugen, KONZEPT-Zeile, commit, push.

## Hinweise aus dem Probelauf

- Fehlt ein Inhalt, den die Lehrkraft im Lernfeld will (z. B. Schutzeinrichtungen im
  Überblick), wird er im Katalog ergänzt und die Abgrenzung angepasst; danach alle darauf
  aufbauenden Akten prüfen (akten.py meldet sie als veraltet).
- Die Abgrenzung immer auch gegen spätere Jahre prüfen (z. B. LF 5 für Netzsysteme und
  Schutzmaßnahmen), nicht nur gegen das Nachbar-Lernfeld laut Lehrplantext.
