# Simulationen zu Stromlaufplänen

Eine HTML-Datei je Simulation, offline, Moodle- und tablettauglich. Der Stromlaufplan erscheint unverändert (SVG
aus dem PDF der Stilreferenz); darüber zeigt die Simulation Spannung auf den Leitungen (rot), betätigte Kontakte
(grüner Rahmen), angezogene Spulen (grün) und, wo der Strom hakt (orange gestrichelt: offener Kontakt mit
Spannung auf nur einer Seite). Im Plan anklickbar: Taster, -F2 (auslösen/zurücksetzen), -F1 nach Kurzschluss. Taster lassen sich im Bedienfeld oder direkt im Plan drücken.

| Datei | Inhalt |
|---|---|
| `stromlauf.py` | macht aus der Lage, die der Plan-Baukasten beim Zeichnen mitschreibt (`Zeichner.geo`), ein Netz aus Knoten und Kanten |
| `kern.js` | Rechenkern: Steuerung wie `plan.schaltfolge`, Hauptstromkreis (Stern/Dreieck/Kurzschluss aus der Verdrahtung), Motor- und Bimetallmodell |
| `vorlage_schuetz.html` | Seite für Schützschaltungen (Plan, Bedienung, Verlauf, Förderband) |
| `vorlage_technologieschema.html` | Seite am Technologieschema (Pakete, Gurt, Trommeln bewegt; Taster am Bedienkasten; Schütze im Schrank leuchten) |
| `pendel.js` | Kiste auf dem Pendelband: Bewegung mit dem Gurt, Endschalter aus ihrer Lage |
| `vorlage_pendel.html` | Seite für Schaltplan und/oder Technologieschema (Fassungen beides, plan, schema), Endschalter auch von Hand |
| `wendeschuetz_sim.py` | baut `simulation_wendeschuetz{,_plan,_schema}`; Gegenprobe in 10 Abläufen, geschlossener Kreis Steuerung–Motor–Kiste–Endschalter |
| `bau.py` | Logo, SVG aus PDF (mit eigenem Namensraum je Zeichnung), stabile Vorschaubilder |
| `sterndreieck_sim.py` | baut drei Fassungen (Lehrkraft 2026-10-15): `simulation_sterndreieck` (Plan + Live-Ansicht), `_plan` (nur Schaltplan), `_schema` (nur Technologieschema aus `werkzeug/technologieschema/foerderband.py`) |

Vor dem Schreiben prüft der Bau (Fehler brechen ab):
1. Plan im PDF aktuell.
2. Gegenprobe: Auf dem gezeichneten Netz schalten die Schütze in allen Abläufen (Normalanlauf, Aus und Motorschutz
   im Stern und im Dreieck) genau wie `plan.schaltfolge` aus der Beschreibung.
3. Hauptstromkreis: Stern 230 V, Dreieck 400 V je Wicklung; Stern und Dreieck zugleich = Kurzschluss.
4. Motormodell plausibel (Hochlauf vor Ablauf der Sternzeit, Strom danach ≤ I_N, Motorschutz nur bei Blockade).
5. Bedienung im Browser (Ein im Bedienfeld → Stern, Aus im Plan → Aus), keine Skriptfehler.

Neue Simulation: Plan mit dem Baukasten bauen, Netz mit `netz_aus_plan(zn.geo, ny)`, Vorlage füllen wie in
`sterndreieck_sim.py`. Nötig: Node, Playwright (Chromium), pdftocairo (alles über `werkzeug/einrichten.sh`).
