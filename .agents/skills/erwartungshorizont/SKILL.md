---
name: erwartungshorizont
description: Erwartungshorizont zu einer Anlage – erwartete Lösung gerechnet, anerkannte andere Wege, typische Fehler mit Reaktion. Pflicht je Anlage, außer der Materialauftrag vermerkt „keiner nötig“. Verwende ihn nach jedem Arbeitsblatt oder bei „Erwartungshorizont“, „Lösung zu Anlage …“.
---
> Werkzeug-Ordner dieses Skills: `materialpipeline-referendariat/`. Alle Pfade und Befehle hier gelten relativ dazu (vorher `cd materialpipeline-referendariat`). Quelle: `materialpipeline-referendariat/.claude/skills/erwartungshorizont/`.

# Erwartungshorizont

Werkzeug: `werkzeug/vorlagen/erwartungshorizont.py` → `rendern(vorlagen/Vorlage_erwartungshorizont.docx, daten, ziel)`;
Daten: aufgaben[nr, loesung, ergebnis, antwortsatz, alternativen, rundung, fehler[]], bezug, rechenpruefung,
kompetenzbezug (leer = aus). **Stilreferenz:** `Muster_erwartungshorizont.docx`, `erwartungshorizont_entwurf.png`.

## Ablauf

1. Erwartungshorizont aus dem Materialauftrag übernehmen und gegen die gebaute Anlage abgleichen.
2. Jede Lösung mit dem Skill `rechenblatt` rechnen (Rechenweg mit eingesetzten Werten, Ergebnis hervorgehoben);
   typische Fehler aus `Rechnung.fehlerweg()` und den Fehlvorstellungen des Auftrags.
3. Rendern, `pruefen()`, Rechenprüfer-Abgleich über alle Anlagen der Stunde, Vorschau als PNG.

## Regeln

- Graues Schild „Erwartungshorizont zu Anlage n“; anerkannte andere Wege und Rundung immer angeben.
- Bei Plänen und Schemata: Soll-Lösung als Bild aus demselben Generator (z. B. vollständiger Plan zur Lückenaufgabe).
- Vermerk „keiner nötig“ nur, wenn der Auftrag ihn setzt.
