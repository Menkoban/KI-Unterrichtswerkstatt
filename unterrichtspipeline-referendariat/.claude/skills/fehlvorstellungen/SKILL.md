---
name: fehlvorstellungen
description: Schritt 06 der Unterrichtspipeline (themenbezogener Teil): Lernausgangslage je Inhalt und Fehlvorstellungen einer Lernsituation, vorab recherchiert und belegt, mit Herkunft, Doppelstunde, Priorität, Aufdecken über ein Diagnose-Item und Aufgreifen im Unterricht. Verwende ihn, wenn eine Lernsituation freigegeben ist und ihre Fehlvorstellungen fehlen, oder bei „Fehlvorstellungen“, „Schülervorstellungen“, „Lernausgangslage zur LS“, „Präkonzepte“.
---

# Lernausgangslage und Fehlvorstellungen (Schritt 06)

Grundlage: `docs/ARBEITSWEISE.md` (Regel KI-Vermutung), `docs/KONZEPT.md` „Schritt 06“.
Beispiel-Daten: `beispiele/daten/fehlvorstellungen/lf01_eg_ls03.json`.

## Ablauf

1. **Erst recherchieren, dann entwerfen:** für jeden Inhalt der LS nach Literatur zu
   Schülervorstellungen suchen (Physikdidaktik, Technikdidaktik, Berufsbildung,
   Unfallanalysen, evidenzbasierte Unterrichtsmaterialien). Quellen möglichst im Volltext
   lesen; sonst im Prüfbericht vermerken, dass nur eine Zusammenfassung vorlag.
2. **Aufnehmen nur mit Herkunft:** Forschung (mit Literatur), Erfahrung der Lehrkraft,
   eigene Beobachtung, KI-Vermutung **mit Bezug** (Feld `bezug`). Reine KI-Vermutungen
   ohne Bezug werden nicht aufgenommen (der Generator meldet sie als Fehler).
3. **Entwurf** `.daten/fehlvorstellungen/<kurz>.json`: Lernausgangslage je Inhalt (Stand
   „unbekannt“, solange keine Quelle; Diagnose-Item je Inhalt), Fehlvorstellungen mit
   typischer Äußerung, Kern, DS, Priorität A (im Unterricht inszenieren: Vorhersagen,
   Prüfen, Erklären), B (Diagnose-Item und Hilfekarte), C (im Blick behalten); Literatur
   im APA-Stil; bewusst nicht Aufgenommenes.
4. **Erzeugen:** `python lernsituation/fehlvorstellungen.py <arbeitsbereich> <kurz>`.
5. **Mit der Lehrkraft:** KI-Vermutungen bestätigen oder streichen lassen (`bestaetigt`),
   Priorität klären; dann Freigabe.

## Hinweise aus dem Probelauf

- Höchstens etwa die Hälfte der DS als A-Einträge; Fehlvorstellungen aus früheren LS
  aufgreifen, wenn sie hier wichtiger werden (Priorität steigt).
- Nummern gestrichener Einträge werden nicht neu vergeben; die übrigen bleiben stabil.
- Fragen zu persönlichen Erfahrungen (z. B. eigener Stromschlag) nur freiwillig und anonym.
