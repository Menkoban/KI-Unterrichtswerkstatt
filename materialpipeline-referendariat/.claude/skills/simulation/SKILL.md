---
name: simulation
description: Interaktive HTML-Simulationen zu Stromlaufplänen und Anlagen (offline, Schulfarben) in bis zu drei Fassungen – Schaltplan + Technologieschema, nur Schaltplan, nur Technologieschema –, gerechnet auf dem gezeichneten Plan. Nur bei Bedarf im Unterricht (Lehrkraft 2026-10-15), nicht auf Vorrat. Verwende ihn, wenn der Materialauftrag eine Simulation verlangt.
---

# Simulation

**Fachpaket Elektrotechnik** (Veröffentlichung 2026-11): Dieser Skill gilt nur, wenn das Profil `fach.elektrotechnik` setzt (`arbeitsbereich.fachpaket("elektrotechnik")`); sonst nicht aufrufen.

Werkzeuge: `werkzeug/simulation/` – `stromlauf.py` (Netz aus `Zeichner.geo`), `kern.js` (Steuerung wie
`plan.schaltfolge`, Hauptstromkreis, Motor, Bimetall), `kontakte.js` (Kontakte in Arbeitsstellung), `pendel.js`,
`bau.py` (Logo, SVG aus PDF mit eigenem Namensraum, stabile Vorschau), Vorlagen `vorlage_pendel.html` (drei
Fassungen), `vorlage_schuetz.html`, `vorlage_technologieschema.html`; `LIESMICH.md`.
**Stilreferenzen (freigegeben):** `wendeschuetz_sim.py` (Muster für neue Fälle) und `sterndreieck_sim.py`;
Ausgaben `docs/stilreferenz/simulation_*`.

## Ablauf

1. Plan mit dem Skill `stromlaufplan`, Schema mit `technologieschema`; Wenn-dann-Tabelle bestätigt (Regel 37).
2. Bauskript nach dem Muster `wendeschuetz_sim.py`: Plan aktuell? Gegenprobe JS gegen `plan.schaltfolge` in allen
   Tabellenzeilen; Hauptstromkreis (Drehrichtung/Betriebsart, Kurzschluss); geschlossener Kreis mit der Anlage;
   Bedienung im Browser (auch kurzes Antippen).
3. Bauen, Vorschau als PNG, in den Probelauf aufnehmen.

## Regeln

- Logik 1:1 aus dem gezeichneten Plan, für alle Fassungen gleich; keine zweite Logik von Hand.
- Betätigte Kontakte in Arbeitsstellung (Regel 35); Spannung rot, „hier hakt es“ orange, nichts verdecken.
- Schulfarben mit Schullogo aus dem Profil (`schule.logo`); Annahmen, Quellen und KI-Fußnote in der Fußzeile.
- Tablet: jeder Tastendruck zählt mindestens 0,2 s, kein Abbruch durch Wischen.
