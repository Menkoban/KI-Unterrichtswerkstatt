---
name: arbeitsblatt
description: Baut nur das Arbeitsblatt einer Anlage (DOCX aus der Schulvorlage) – Situation aus dem Modellbetrieb, Aufgaben problemorientiert, Rechen- und Skizzenfelder. Hilfekarten und Erwartungshorizont sind eigene Skills. Verwende ihn, wenn der Materialauftrag ein Arbeitsblatt verlangt oder die Lehrkraft „Arbeitsblatt zu …“ sagt.
---

# Arbeitsblatt bauen

Werkzeug: `werkzeug/vorlagen/arbeitsblatt.py` → `rendern(vorlagen/Vorlage_arbeitsblatt.docx, daten, ziel)`;
Datenfelder im Kopf der Datei (beruf, lf, lf_titel, ls, ls_titel, nr, titel, wozu, situation, quellen,
ki_hinweis, aufgaben[nr, operator, text, zeilen ≥ 8, rechenfeld, antwortsatz, skizzenfeld]). Formelzeichen als
`R_L`, `l_{ges}`, `**fett**`. Vorschau: `schule.vorschau(docx, png_praefix)`.

**Stilreferenz:** `docs/stilreferenz/vorlagen/muster/Muster_arbeitsblatt.docx`, Bilder `arbeitsblatt_seite.png`,
`arbeitsblatt_kopf_C.png`. Regeln: `docs/regeln/stilregeln.md` (Abschnitt Arbeitsblatt, Handlungssituation,
Fachliche Bezeichnungen).

## Ablauf

1. Steckbrief der Anlage lesen (Zweck, Phase, TK, Wortlaut, Aufbau, Abnahmekriterien).
2. Situation als Problem im Modellbetrieb formulieren, Aufgaben mit Operatoren; Zahlen kommen aus dem
   Skill `rechenblatt` (nie geschätzt), Abbildungen aus den Fach-Skills, jeweils mit Quelle.
3. Rendern, `pruefen()` aus `werkzeug/vorlagen/alle_bauen.py` auf die Datei, Vorschau als PNG.
4. Befunde in den Prüfbericht des Hauptskills.

## Regeln

- Kopf Variante C, Schild „Anlage n · Arbeitsblatt“, „Wozu?“-Zeile, Situation im Kasten.
- Kein „gegeben/gesucht“, keine Kennzeile, kein Ziel; keine Arbeitsanweisung, die Methode oder Lösungsweg vorgibt.
- Ein Niveau; Sie-Form; KI-Fußnote; Quellen im Fuß; fiktive Firmen als fiktiv gekennzeichnet.
- Rechenfeld als Kästchenraster ≥ 8 Zeilen; Antwortsatz nur, wo sinnvoll.
