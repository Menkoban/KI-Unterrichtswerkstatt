---
name: rechenblatt
description: Rechenprüfer und Diagramme – jede Zahl im Material wird mit Einheiten gerechnet (Pint, Gegenprobe lcapy), Rechenweg für Erwartungshorizont und Hilfekarten, Abgleich aller Anlagen einer Stunde, Kennlinien aus derselben Rechnung. Verwende ihn für jede Anlage mit Zahlen, Formeln oder Diagrammen.
---
> Werkzeug-Ordner dieses Skills: `materialpipeline-referendariat/`. Alle Pfade und Befehle hier gelten relativ dazu (vorher `cd materialpipeline-referendariat`). Quelle: `materialpipeline-referendariat/.claude/skills/rechenblatt/`.

# Rechenblatt und Diagramme

Werkzeuge: `werkzeug/rechnen/rechnen.py` (Rechnung: gegeben, schritt, gegenprobe, fehlerweg, zeilen, abgleich,
bericht), `werkzeug/rechnen/diagramm.py` (Diagramme im Stil der Pt100-Kennlinie), `LIESMICH.md`.
**Stilreferenz:** `werkzeug/rechnen/beispiele/ds7_leitungswiderstand.py`, Ausgaben `docs/stilreferenz/rechnen/`,
`docs/stilreferenz/kennlinie_pt100.*`.

## Ablauf

1. Je Anlage eine Rechnung: gegebene Größen mit Einheit und Herkunft (Auftrag, Quelle oder als **Annahme**
   gekennzeichnet), Schritte mit Formel, erwartete Werte aus dem Auftrag.
2. Gegenprobe über einen zweiten Weg; typische Fehler als Fehlerwege.
3. `abgleich()` über alle fertigen Anlagen der Stunde: gleiche Zahlen im ganzen Fall.
4. `bericht()` in den Prüfbericht; Fehler vor der Freigabe beheben.

## Regeln

- Jede Lösung wird gerechnet, nicht geschätzt; Annahmen offen ausweisen (z. B. Typenschild, Sternzeit).
- Normwerte mit Beleg (Norm, Tabellenbuch, Herstellerdatenblatt über den Skill `quellen`).
- Formelzeichen mit echten Indizes; deutsche Zahlschreibweise (Komma).
