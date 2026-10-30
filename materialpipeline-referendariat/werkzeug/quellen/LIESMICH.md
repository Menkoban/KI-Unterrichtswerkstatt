# Quellen aufnehmen (Fahrplan Schritt 3)

Die Lehrkraft hängt Fotos, Scans oder PDF direkt im Chat an, optional mit einem Satz zu Werk und Seite
(Entscheidung A, 2026-10-15). Die Pipeline nimmt sie so auf:

    python3 werkzeug/quellen/aufnehmen.py DATEI --art fachbuch|norm|hersteller|material --werk "…" \
            --auflage "…" --seite 112 --thema "…" --rechte "nur intern"
    python3 werkzeug/quellen/suche.py "Begriff"

- Ablage `quellen/<art>/<werk>/…` mit erkanntem Text daneben (`.txt`, Tesseract Deutsch; PDF mit Textschicht direkt).
- Quellenkarte `quellen/_karte/karte.csv` (maschinell) und `karte.md` (zum Lesen).
- Doppelte Dateien werden erkannt; über 100 MB abgelehnt (vorher teilen); HEIC-Fotos vom Tablet werden JPG.
- Fehlen Seite oder Auflage, steht das als Hinweis in der Karte und wird bei der Lehrkraft nachgefragt.
- Mitgegebenes ist Rohstoff: eigenes Material entsteht immer neu im Pipeline-Stil, Original bleibt als Beleg
  (Entscheidung A, 2026-10-15). Quellen bleiben im privaten Repo, nie in einer teilbaren Fassung (E11).
- `probe.py` prüft das Ganze in einem Testverzeichnis (Teil des Probelaufs).

## Erfahrungen aus dem Test mit Internetquellen (2026-10-15)

- Herstellerdatenblatt (Siemens 3RU2116-1EB0, Spiegel bei RS): bestätigt den Einstellbereich 2,8…4 A und CLASS 10
  von -F2 im Wendeschütz-Plan. Der Spiegel lieferte aber die **chinesische** Fassung; die Aufnahme meldet das jetzt
  („Sprachfassung prüfen“). Datenblätter möglichst direkt beim Hersteller in Deutsch holen.
- Ein Download kann statt der Datei eine Webseite liefern; solche „PDF“ werden abgelehnt.
- Simuliertes Handyfoto (schräg, dunkler, leicht unscharf, JPG 70 %): 98 % der Wörter erkannt.
- Suche findet Textstellen mit Werk und Seite, z. B. „AUS-Taster“ in der Voltimum-Übersicht der Schützschaltungen.
