---
name: stromlaufplan
description: Stromlaufpläne (Haupt- und Steuerstromkreis, Schützschaltungen) im Industriestil A3 mit dem Plan-Baukasten – Beschreibung als Strompfade, Rechnung, Ablaufprüfung, Wenn-dann-Tabelle, nichts verdeckt. Verwende ihn nur, wenn der Materialauftrag einen Stromlaufplan verlangt (z. B. Wendeschütz, Stern-Dreieck, Selbsthaltung).
---

# Stromlaufplan

**Fachpaket Elektrotechnik** (Veröffentlichung 2026-11): Dieser Skill gilt nur, wenn das Profil `fach.elektrotechnik` setzt (`arbeitsbereich.fachpaket("elektrotechnik")`); sonst nicht aufrufen.

Werkzeug: `werkzeug/schaltplan/plan.py` (Plan, Steuerung, Pfad, K, Sich, Spule, Parallel; `steuerung_zeichnen`,
`kontaktspiegel`, `blatt`, `schaltfolge`, `ueberdeckungen`), Hauptstromkreis-Bausteine `hauptstrom.py`, Zeichen
`werkzeug/schaltzeichen/planzeichen.sty` (Norm-Nr. und Beleg im Katalog). Wenn-dann-Tabelle:
`werkzeug/schaltplan/funktionstabelle.py`.

**Stilreferenzen (freigegeben):** `werkzeug/schaltplan/beispiele/wendeschuetz.py` (mit Endschaltern, Umschalten im
Lauf nur über Aus) und `sterndreieck.py`; Ausgaben `docs/stilreferenz/schaltplan_*_a3.*`,
`funktionstabelle_wendeschuetz.md`.

## Ablauf

1. **Variante klären** (Regel 36), z. B. Verriegelung, Endschalter, Zeitrelais.
2. Rechnung mit dem Rechenprüfer (Typenschild als Annahme kennzeichnen; Einstellwert -F2 gerechnet, Regel 34).
3. Plan als Beschreibung (Strompfade) wie in den Beispielen; Hauptstromkreis aus Bausteinen.
4. **Wenn-dann-Tabelle** aus dem Plan rechnen und der Lehrkraft vorlegen (Regel 37); jede Zeile wird ein Prüffall
   in `ablauf_pruefen`.
5. Bauen (LuaLaTeX, TEXINPUTS auf `werkzeug/schaltzeichen//`), `ueberdeckungen` ohne Treffer, Vorschau als PNG.

## Regeln

`docs/regeln/schaltplan_checkliste.md` vollständig, besonders: Industriestandard A3 mit Raster und Schriftfeld;
Kennzeichen links, Anschlüsse rechts; keine Wirklinien über mehrere Pfade; Verbindungspunkt an jeder Abzweigung;
Kontaktspiegel statt Querverweisen; keine Absenkung am Pfadanfang; Verriegelungsöffner auf einer Höhe;
Endschalter als Positionsschalter 07-08-02 unter der Selbsthaltung; nichts verdecken.
