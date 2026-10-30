---
name: lernsituation
description: Schritt 04 der Unterrichtspipeline: arbeitet eine Lernsituation aus der Skizze aus (Kernkompetenz, Handlungssituation, Auftrag, Handlungsergebnis, echte Entscheidung, Bewertung, innere vollständige Handlungen als Zyklen über Doppelstunden, Doppelstunden mit Leitfrage, Inhalten, Teilergebnis, Phasen und LK). Verwende ihn, wenn die Skizze freigegeben ist und eine LS ausgearbeitet werden soll, oder bei „LS ausarbeiten“, „weiter mit LS 2“, „Doppelstunden der LS“.
---
> Werkzeug-Ordner dieses Skills: `unterrichtspipeline-referendariat/`. Alle Pfade und Befehle hier gelten relativ dazu (vorher `cd unterrichtspipeline-referendariat`). Quelle: `unterrichtspipeline-referendariat/.claude/skills/lernsituation/`.

# Lernsituation ausarbeiten (Schritt 04)

Grundlage: `docs/ARBEITSWEISE.md`, `docs/KONZEPT.md` (drei Ebenen der vollständigen Handlung,
Lehrkraft-Profil). Beispiel-Daten: `beispiele/daten/lernsituation/lf01_eg_ls01.json`.

## Ablauf

1. **Vorhandenes zuerst:** liegt die LS von der Schule vor, übernehmen und abgleichen.
2. **Entwurf** `.daten/lernsituation/<kurz>.json` aus der Skizze: Situation ausformulieren
   (Kunde, Anlass, Zitat), Auftrag der Meisterin in der Sie-Form, Handlungsergebnis,
   Bewertungskriterien, Zyklen (innere vollständige Handlung je Arbeitsschritt, 2 bis 3 je
   LS, Profil `innerer_zyklus.umfang`), Doppelstunden (Standard 2 Std.).
3. **Erzeugen:** `python lernsituation/ls_ausarbeitung.py <arbeitsbereich> <kurz>`. Der
   Generator prüft: Stunden der DS = Stunden der LS, Planen in jedem Zyklus (Fehler), alle
   Phasen je Zyklus (Warnung), alle LK der LS vorhanden, Legende passend.
4. **Fachlich gegenrechnen:** jede Zahl im Erwartungshorizont (`hinweise`) rechnen;
   Gerätedaten realistisch (Spannung, Leistung, 230 V oder 400 V), Messen und Bauen nur an
   Kleinspannung.
5. **Prüfbericht, eine Freigabe** je LS; dann die nächste LS.
6. **Selbstständige LS** (Profil `lernsituation.form` „selbststaendig_mit_geruest“, `lernsituation.planungstiefe`
   „arbeitsplan_kurzskizze“; Lehrkraft 2026-10-25): statt Stundenplanung je DS ein **Arbeitsplan**
   `.daten/arbeitsplan/<kurz>.json` (Meilensteine mit spätestem Termin, fester Lernpfad der Arbeitsblätter, Kontrolle,
   Kriterien wortgleich mit der Bewertung), erzeugt mit `python lernsituation/arbeitsplan.py <arbeitsbereich> <kurz>`
   (Arbeitsplan_Planung.docx, sobald Steckbriefe da sind auch Materialauftrag.docx der ganzen LS). Die
   Doppelstunden bekommen nur Kurzskizzen (Skill `stundenplanung`, Feld `arbeitsplan`). Termine und Zeitplan nur für
   die Lehrkraft, nicht für die Lernenden (Profil `lernsituation.zeitplan_lernende`).

## Hinweise aus dem Probelauf

- Eine Ansage zur Stunde (z. B. Kennenlernen in DS 1) kann die LS ändern (Arbeitsplan
  wandert nach DS 2): ausführen und im Prüfbericht der LS vermerken.
- Abgrenzung in jeder LS ausweisen (was nur benannt wird, was späteren LF gehört).
