---
name: hilfekarten
description: Optionaler Skill für gestufte Hilfekarten (Tipp, Ansatz, Lösungsweg) zu einem Arbeitsblatt. Nur wenn der Materialauftrag Hilfen vorsieht oder die Lehrkraft sie wünscht; sonst wird er nicht aufgerufen. Verwende ihn bei „Hilfekarten“, „gestufte Hilfen“, „Tipps zu Aufgabe …“.
---

# Hilfekarten (optional)

**Zuerst das Profil:** Ist `material.schriftliche_hilfen` aus, keine Hilfekarten bauen; die Impulse gehören in den
Erwartungshorizont unter „Reaktion“ (Lehrkraft 2026-10-24). Digitale Hilfen in Moodle baut Pipeline 3.

Werkzeug: `werkzeug/vorlagen/hilfekarten.py` → `rendern(vorlagen/Vorlage_hilfekarten.docx, daten, ziel)`;
Daten: stufen[nr 1–3, name, karten[aufgabe, text]], je Stufe eine Karte pro Aufgabe.
**Stilreferenz:** `docs/stilreferenz/vorlagen/muster/Muster_hilfekarten.docx`, `hilfekarten_entwurf.png`.
Weitere Muster aus der Probe LS 1 (Hilfe auf der Rückseite, Lückensätze mit Begriffskasten, Satzbausteine):
`docs/stilreferenz/probe_ls01/README.md`.

## Ablauf

1. Prüfen, ob Hilfen verlangt sind (Steckbrief „Niveaus und Hilfen“ oder Wunsch der Lehrkraft). Wenn nein: nichts tun.
2. Je Aufgabe drei Stufen: **Tipp** (lenkt den Blick, verrät nichts), **Ansatz** (benennt den Weg ohne Zahlen),
   **Lösungsweg** (Rechenweg mit eingesetzten Werten aus `rechenblatt`, `Rechnung.zeilen()`).
3. Rendern, `pruefen()`, Vorschau als PNG.

## Regeln

- Stufen bauen aufeinander auf; Stufe 1 und 2 enthalten kein Ergebnis.
- Gleiche Zahlen wie Arbeitsblatt und Erwartungshorizont (Rechenprüfer-Abgleich).
- Schild „Anlage n · Hilfekarten“, kein Namensfeld, Schnittlinien gestrichelt.
