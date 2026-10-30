---
name: dokumente
description: Weitere Materialarten aus den abgenommenen Schulvorlagen – Einstieg, Infoblatt/Datenblatt, Messprotokoll, Serviceauftrag, Servicebericht, Selbstkontrolle, Karte A5, Tafelbild, Folien (PPTX), Tabelle (XLSX). Verwende ihn, wenn der Materialauftrag eine dieser Anlagen verlangt.
---
> Werkzeug-Ordner dieses Skills: `materialpipeline-referendariat/`. Alle Pfade und Befehle hier gelten relativ dazu (vorher `cd materialpipeline-referendariat`). Quelle: `materialpipeline-referendariat/.claude/skills/dokumente/`.

# Weitere Dokumente aus den Vorlagen

Je Art ein Skript in `werkzeug/vorlagen/` (gleichnamig: `einstieg.py`, `infoblatt.py`, `messprotokoll.py`,
`serviceauftrag.py`, `servicebericht.py`, `selbstkontrolle.py`, `karte_a5.py`, `tafelbild.py`, `folien.py`);
Vorlagen in `vorlagen/`, Muster in `docs/stilreferenz/vorlagen/muster/`, Entwürfe und Vorschauen in
`docs/stilreferenz/vorlagen/`. Datenfelder stehen jeweils im Kopf des Skripts; Muster-Daten (`muster_daten()`)
zeigen ein vollständiges Beispiel (LF 1, LS 3, DS 7).

**Muster aus der Probe LS 1 (Lehrkraft 2026-10-19, Layouts abgenommen):** `docs/stilreferenz/probe_ls01/README.md`
listet je Materialart (Karten, Bildkarten mit Duplex, Rollen- und Beobachtungskarten, Fahrplan und Rundenplan,
Dossier, Raster, Checkliste, Bewertungsbogen mit Notenschlüssel, Kompetenzcheck) Skript, Funktion und Vorschau.
Muster sind Vorbild für Aufbau und Optik; jede Stunde bleibt individuell. Gemeinsame Bausteine: `werkzeug/vorlagen/stunde.py`.

## Ablauf

1. Passende Art und Vorlage wählen, Muster-Daten als Vorbild, Inhalte aus dem Steckbrief.
2. Zahlen aus `rechenblatt`, Abbildungen aus den Fach-Skills mit Quelle.
3. Bauen, `pruefen()` aus `alle_bauen.py`, Vorschau als PNG.

## Regeln (Auszug, vollständig in `docs/regeln/stilregeln.md`)

- Einstieg und Serviceauftrag sind die Handlungssituation: ohne „Wozu?“-Zeile, Problem zuerst, nichts vorwegnehmen.
- Betriebsdokumente im Einstieg wie echte Unterlagen des Modellbetriebs (fiktiv gekennzeichnet).
- Selbstkontrolle: Einschätzungsskalen vierstufig, Bezeichnung über jedem Kreis.
- Karten A5/A6: kein abgeschnittener Text. Folien und Tafelbild nach Abschnitt „Folien und Tafelbild“.
- Format je Material: DOCX, XLSX, PPTX oder HTML; PDF nur auf ausdrücklichen Wunsch.
- Sprachnachrichten und andere Sprachaufnahmen vermeiden (Lehrkraft 2026-10-16): Aufträge schriftlich, z. B. als
  Messenger-Nachricht, Notiz oder E-Mail des Modellbetriebs. Nur auf ausdrücklichen Wunsch der Lehrkraft:
  `werkzeug/audio/sprachausgabe.py --regie` (Satz für Satz betont), Stimme `de-DE-KatjaNeural`, Transkript wörtlich.
