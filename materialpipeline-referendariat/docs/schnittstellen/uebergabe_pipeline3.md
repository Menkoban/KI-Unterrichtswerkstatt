# Übergabe an Pipeline 3 (E8, Lehrkraft 2026-10-13: A)

Pipeline 2 übergibt **je Stunde ein Paket**: den Ordner `Anlagen/` des Stundenordners mit allen fertigen
Dateien und daneben die Beschreibungsdatei `Anlagen/uebergabe.json`. Pipeline 3 baut daraus den Moodle-Abschnitt
der Stunde und muss nichts raten: Zweck, Phase und Reihenfolge der Anlagen stehen in der Beschreibung.

## Regeln

- Ein Eintrag je Anlage, in der Reihenfolge des Einsatzes in der Stunde.
- Nur freigegebenes Material (Prüfbericht ohne Fehler, Freigabe der Lehrkraft).
- Die Logik der Stunde bleibt online erhalten: erst Problem (Einstieg), dann Informationspool zum Auswählen,
  Hilfen gestuft, Lösungen (Erwartungshorizont) nie für Lernende sichtbar.
- `moodle` ist ein **Vorschlag**; Pipeline 3 entscheidet endgültig.
- Keine Namen von Lernenden, keine Modellbezeichnungen.

## Felder

| Feld | Bedeutung |
|---|---|
| `stunde` | Kürzel und Titel der Stunde (aus dem Materialauftrag), LF, LS, DS, Datum |
| `materialauftrag` | Pfad zum freigegebenen `Materialauftrag.docx` |
| `anlagen[]` | je Anlage: `nr`, `datei`, `art` (Materialart, z. B. `einstieg`, `arbeitsblatt`, `hilfekarten`), `titel`, `wozu`, `phase` (Einstieg, Planung, Erarbeitung, Sicherung, Abschluss), `sozialform`, `zeit_min`, `sichtbar_fuer` (`lernende` / `lehrkraft`), `freischaltung` (`sofort`, `nach_anlage:<nr>`, `gestuft`), `gehoert_zu` (Nr. der Anlage, auf die sie sich bezieht), `moodle` (Vorschlag: `datei`, `ordner`, `seite`, `aufgabe`, `test`, `h5p`), `pool` (true, wenn Teil des Informationspools) |
| `hinweise` | freie Hinweise an Pipeline 3 (z. B. „Hilfekarten nur nach Anfrage freischalten“) |

## Beispiel (Muster DS 7, gekürzt)

```json
{
  "stunde": {"kurz": "LF1-LS3-DS7", "titel": "Können wir den Fehler beweisen?", "lf": 1, "ls": 3, "ds": 7},
  "materialauftrag": "../Materialauftrag.docx",
  "anlagen": [
    {"nr": 1, "datei": "Anl_1_Reklamation.docx", "art": "einstieg", "titel": "Reklamation an der Siegelstation",
     "wozu": "Problem und offener Auftrag", "phase": "Einstieg", "sozialform": "Plenum", "zeit_min": 10,
     "sichtbar_fuer": "lernende", "freischaltung": "sofort", "moodle": "datei", "pool": false},
    {"nr": 2, "datei": "Anl_2_Pt100.docx", "art": "infoblatt", "titel": "Widerstandsthermometer Pt100",
     "wozu": "Nachschlagen", "phase": "Erarbeitung", "sichtbar_fuer": "lernende",
     "freischaltung": "nach_anlage:1", "moodle": "ordner", "pool": true},
    {"nr": 4, "datei": "Anl_4_Hilfekarten.docx", "art": "hilfekarten", "gehoert_zu": 3,
     "phase": "Erarbeitung", "sichtbar_fuer": "lernende", "freischaltung": "gestuft", "moodle": "h5p"},
    {"nr": 6, "datei": "EH_Anl_3.docx", "art": "erwartungshorizont", "gehoert_zu": 3,
     "sichtbar_fuer": "lehrkraft", "moodle": "keine"}
  ],
  "hinweise": ["Erwartungshorizont nie für Lernende sichtbar."]
}
```

Die Datei schreibt `werkzeug/uebergabe.py` (`schreiben(stundenordner, stunde, anlagen, hinweise)`); sie prüft
Pflichtfelder und Dateinamen.

## Merkliste der Lehrkraft für Pipeline 3 (2026-10-15)

Beim Umsetzen in Moodle werden Schaubilder interaktiv, nicht nur als Bild eingebunden:

- **Technologieschema** (z. B. Siegelstation): als Simulation. Jedes Teil lässt sich anklicken und zeigt, was es
  ist und tut. Die Anlage lässt sich bewegen und live vorführen.
- **Schaltpläne:** als Simulation, in der jeder Schalter bzw. Kontakt **einzeln** anklickbar ist. Man sieht, wie
  der Strom fließt, ob er überhaupt fließt und **wo er hakt** (an welchem offenen Kontakt der Stromweg endet).
- Grundlage ist der Simulationsbaukasten aus Pipeline 2 (`werkzeug/simulation`, Stilreferenz
  `simulation_sterndreieck.html`): Er rechnet auf dem gezeichneten Plan, Plan und Simulation bleiben gleich.
