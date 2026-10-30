---
name: technologieschema
description: Technologieschemata von Anlagen im Fachbuch-Stil (TikZ, Schrägbild mit Tiefe, Graustufen, Positionsnummern mit Legende), Betriebsmittel mit denselben Kennzeichen wie im Schaltplan. Verwende ihn nur, wenn der Materialauftrag ein Technologieschema oder eine Anlagendarstellung verlangt.
---
> Werkzeug-Ordner dieses Skills: `materialpipeline-referendariat/`. Alle Pfade und Befehle hier gelten relativ dazu (vorher `cd materialpipeline-referendariat`). Quelle: `materialpipeline-referendariat/.claude/skills/technologieschema/`.

# Technologieschema

**Fachpaket Elektrotechnik** (Veröffentlichung 2026-11): Dieser Skill gilt nur, wenn das Profil `fach.elektrotechnik` setzt (`arbeitsbereich.fachpaket("elektrotechnik")`); sonst nicht aufrufen.

Werkzeug: `werkzeug/technologieschema/anlage.py` (Szene: boden, band, karton, antrieb, kabelkanal, bedienkasten,
schaltschrank, geraet, nummer, beschriften; `bauen` mit pdflatex). Gezeichnet wird, was ruht; was sich in einer
Simulation bewegt, wird mit `beweglich=False` weggelassen und als Lage (`szene.lage`) mitgegeben.
**Stilreferenzen (freigegeben):** `docs/stilreferenz/technologieschema_siegelstation.*` (Maßstab),
`technologieschema_foerderband.*` (`foerderband.py`), `technologieschema_pendelband.*` (`pendelband.py`).

## Ablauf

1. Anlage und Betriebsmittel aus dem Auftrag bzw. dem Schaltplan (gleiche Kennzeichen).
2. Szene aus Bausteinen; neue Teile als Baustein in `anlage.py` ergänzen, nicht in der Szene ausmalen.
3. Positionsnummern so setzen, dass Hinweislinien nicht durch bewegte Teile laufen; Legende spaltenweise.
4. Bauen, Vorschau als PNG, vergrößert prüfen.

## Regeln

- Fachbuch-Niveau wie Siegelstation; Graustufen, farbig nur Signal (Taster grün/rot, Kabel dunkelblau).
- Bestehende Szenen bleiben Zeichen für Zeichen gleich, wenn Bausteine geändert werden (vorher/nachher vergleichen).
- Nichts verdecken; Quelle bei übernommenen Abbildungen.
