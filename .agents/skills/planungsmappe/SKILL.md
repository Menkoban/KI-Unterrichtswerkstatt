---
name: planungsmappe
description: Fasst die Akten einer Planung (Jahresplanung, Modellbetrieb, curriculare Analyse, Skizze, Lernsituationen, Fehlvorstellungen, Stunden) zu einer Planungsmappe als DOCX zusammen, mit einer Einführung für Außenstehende (Schulleitung, Mentor, Seminar) und dem Stand jedes Dokuments. Verwende ihn, wenn die Lehrkraft etwas zeigen oder abgeben will: „Mappe“, „alles in einem Dokument“, „für das Gespräch mit der Schule“, „zum Mitnehmen“.
---
> Werkzeug-Ordner dieses Skills: `unterrichtspipeline-referendariat/`. Alle Pfade und Befehle hier gelten relativ dazu (vorher `cd unterrichtspipeline-referendariat`). Quelle: `unterrichtspipeline-referendariat/.claude/skills/planungsmappe/`.

# Planungsmappe

Grundlage: `docs/ARBEITSWEISE.md`. Beispiel-Daten: `beispiele/daten/mappe/lf01_eg_probelauf.json`.

## Ablauf

1. **Zweck und Leser klären, eine Frage:** für wen (Schulleitung, Mentor, Seminar), was
   hinein soll (ganzes Lernfeld, eine LS, eine Besuchsstunde).
2. **Daten** `.daten/mappe/<kurz>.json`: Titel, Deckblatt (Name der Lehrkraft nicht raten,
   erfragen oder aus dem Profil), Einführung in wenigen längeren Absätzen ohne
   Gedankenstriche (worum es geht, wie die Planung entsteht, auf einen Blick, wie es
   weitergeht), KI-Hinweis, Liste der Dokumente in der Reihenfolge der Planung.
3. **Erzeugen:** `python mappe/planungsmappe.py <arbeitsbereich> <kurz>`. Nur freigegebene
   Dokumente ohne Hinweis; Querformat bleibt erhalten. Ein Wechsel von quer zurück nach
   hoch wird in manchen Programmen eine Seite zu früh angezeigt; dann das Dokument mit
   `"format": "quer"` einbinden.
4. **Prüfen:** in PDF umwandeln (nur zur Kontrolle), Seitenformat und Inhaltsverzeichnis
   ansehen; die DOCX an die Lehrkraft senden.
