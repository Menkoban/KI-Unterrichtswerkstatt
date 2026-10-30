---
name: lernsituationen-skizze
description: Schritt 02 der Unterrichtspipeline: skizziert, wie ein Lernfeld in Lernsituationen zerfällt (Titel, Handlungssituation, Handlungsergebnis, echte Entscheidung, Lernfeld-Kompetenzen mit Legende, Inhalte, Stunden), mit übergeordneter Handlungssituation im Modellbetrieb. Je Fachrichtung, ohne Kalender, Summe gleich Zeitrichtwert. Verwende ihn, wenn die curriculare Analyse steht und die Lernsituationen eines Lernfelds fehlen, oder bei „Lernsituationen planen“, „wie teilen wir das Lernfeld auf“, „Skizze“.
---
> Werkzeug-Ordner dieses Skills: `unterrichtspipeline-referendariat/`. Alle Pfade und Befehle hier gelten relativ dazu (vorher `cd unterrichtspipeline-referendariat`). Quelle: `unterrichtspipeline-referendariat/.claude/skills/lernsituationen-skizze/`.

# Lernsituationen skizzieren (Schritt 02)

Grundlage: `docs/ARBEITSWEISE.md`, `docs/KONZEPT.md` „Schritt 02 — Festlegungen“.
Beispiel-Daten: `beispiele/daten/ls_skizze/lf01_eg.json`.

## Voraussetzungen

Curriculare Analyse (01) und Modellbetrieb freigegeben. Jahresplanung (03) liefert nur die
Stundenzahl; die Skizze plant **ohne Kalender** (Grenzen wie Ferien nur, wenn die Lehrkraft
sie ausdrücklich setzt: Feld `grenzen`).

## Ablauf

1. **Vorhandenes zuerst:** Lernsituationen der Schule hochladen lassen und übernehmen.
2. **Leitidee klären, eine Frage:** übergeordnete Handlungssituation (z. B. Kunde, Haus,
   Anlage), drei gleich ausführliche Vorschläge; Varianten, die die Lehrkraft ausarbeiten
   lässt, als eigene Datei aufbewahren (`<kurz>_variante_<x>.json`).
3. **Entwurf** `.daten/ls_skizze/<kurz>.json`: je LS Titel, Situation, Ergebnis
   (möglichst materielles Handlungsprodukt), echte Entscheidung, LK, Inhalte (aus dem
   Pflichtkatalog), mathematische Grundlage, Lernort Betrieb, Stunden; Puffer und ggf.
   Klassenarbeit als eigene Zeilen; **LK-Legende** (`lk_legende`) mit Wortlaut.
4. **Erzeugen:** `python lernfeld/ls_skizze.py <arbeitsbereich> <kurz>`. Der Generator
   bricht mit Fehler ab, wenn die Stunden nicht aufgehen, eine LK fehlt oder die Legende
   unvollständig ist.
5. **Prüfbericht und Freigabe**; im Chat die LK immer mit Wortlaut nennen.

## Hinweise aus dem Probelauf

- Inhalte, die die Lehrkraft nachträglich ins Lernfeld holt, verändern Stunden mehrerer
  LS: erst die Analyse (01), dann die Skizze, dann betroffene LS neu (zurückspulen).
- Puffer und Klassenarbeit sind Entscheidungen der Lehrkraft (z. B. Klassenarbeit am Ende
  des Lernfelds, Puffer mit Präsentation und Übungszirkel).
- Gerätedaten im Kontext realistisch halten (Spannung, Leistung, Einsatzort) und über alle
  LS einheitlich (derselbe Durchlauferhitzer hängt überall am selben Ort).
