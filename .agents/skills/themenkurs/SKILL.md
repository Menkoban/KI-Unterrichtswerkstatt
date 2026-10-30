---
name: themenkurs
description: Hauptablauf von Pipeline 3: macht aus einer fertigen Lernsituation (Planung aus Pipeline 1, Material aller Doppelstunden aus Pipeline 2) einen Moodle-Themenkurs – Eingang lesen, Grilling bis zum gemeinsamen Kursplan (DOCX, Freigabe), Bau in einem Lauf mit parallelen Helfern je Abschnitt, Prüfer, Test-Moodle, Sichtprüfung, Abnahme, Ablage der .mbz. Verwende ihn, sobald die Lehrkraft „Moodle-Kurs zu LS …“, „Themenkurs bauen“, „mach daraus einen Kurs“ sagt oder das Material einer Lernsituation fertig ist.
---
> Werkzeug-Ordner dieses Skills: `moodlepipeline-referendariat/`. Alle Pfade und Befehle hier gelten relativ dazu (vorher `cd moodlepipeline-referendariat`). Quelle: `moodlepipeline-referendariat/.claude/skills/themenkurs/`.

# Themenkurs bauen (Pipeline 3)

Grundlage: `CLAUDE.md`, `docs/KONZEPT.md` (Entscheidungsprotokoll, Punkte 1–33), `docs/regeln/umsetzungskatalog.md`.
Ziel: **schneller, schlanker Kursbau**; Bau nach Freigabe in höchstens 30 Minuten.

## 0. Arbeitsbereich und Profil

`python3 werkzeug/arbeitsbereich.py` findet den Arbeitsbereich und zeigt die Profil-Gruppe „Moodle“ (Kachelformat,
Schulfarben, Kurstexte, Freischaltung, Eingangsdiagnose, Generalprobe, Versuche, Medaillen und Grenzen, Tests ohne
Glossar, Gruppenabgaben, Videos, Dashboard, Schullogo, KI-Hinweis, Steckbrief, Handlungssituation, Kachelnummern,
Kachelbilder und Stil) sowie `lehrkraft.*` (Name, Anrede, E-Mail). Alles richtet sich nach dem Profil. Ergebnisse nur
in den Arbeitsbereich: `<Fach>/<Beruf>/<LF>/<LS>/Moodle/` (`arbeitsbereich.moodle(...)`).

## 1. Eingang lesen (nichts davon neu fragen)

- Lernsituation aus Pipeline 1: `.daten/lernsituation/<ls>.json` (Kernkompetenz, Handlungssituation,
  Handlungsergebnis, Doppelstunden mit Leitfrage, Teilkompetenzen, Bewertung), `Fehlvorstellungen.docx`
  bzw. `.daten` (Diagnose-Items), Klassen-Akte (Niveau, Sprache, Personas).
- Material aller Doppelstunden aus Pipeline 2: `Unterricht/…/<Stunde>/Anlagen/uebergabe.json` und die Dateien.
- Eingang ist **die ganze Lernsituation**; Doppelstunden sind Rohstoff, nicht zwingend je ein Abschnitt.
- **Kurs und Unterricht getrennt** (Lehrkraft 2026-10-25): Der Kurs überführt die Inhalte 1:1 in einen eigenständigen
  Kurs, der auch in einem anderen Jahr ohne Besuch und ohne diese Stundenplanung funktioniert. Der Kursbau ändert keine
  freigegebene Planung, schon gar keine Besuchsstunde; Kacheln beschreiben Inhalte und Reihenfolge, nicht Minuten oder
  Stunden.

## 2. Grilling bis zum gemeinsamen Kursplan

- Grilling nach „Grill-Me / Grill-with-Docs“: **eine Frage zur Zeit**, kurzer Kontext, drei gleich ausführliche
  Vorschläge (empfohlener zuerst) und freie Antwort; Entscheidungsbaum Ast für Ast; so lange, bis Lehrkraft und KI
  denselben Plan haben. Keine festen Cluster.
- **Didaktischer Fokus und Sparringspartner:** didaktische Entscheidungen ausdrücklich fragen; je Entscheidung
  höchstens ein Denkanstoß mit Alternative und kurzer Begründung (Handlungsorientierung, vollständige Handlung,
  Meyer, Klafki, Seminarerwartung). Technik und Gestaltung entscheidet die Pipeline.
- **Proaktiv widersprechen:** passt eine Antwort der Lehrkraft nicht (zur Didaktik, zum Fach, zur Technik oder zu
  früheren Entscheidungen), das sofort und deutlich sagen, mit Grund und besserem Vorschlag.
- **Erste Frage immer: Umfang des Themenkurses** – ganze Lernsituation mit allen Phasen der vollständigen Handlung,
  nur einige Phasen (z. B. Informieren und Planen) oder nur eine Phase. Nie stillschweigend alles annehmen.
- **Abgaben bündeln** (Lehrkraft 2026-10-26): keine Abgabe je Einzelaufgabe; geschlossene Aufgaben als Testfragen, offene
  höchstens eine Abgabe je Arbeitsblatt, Meilensteine immer als Abgabe; der Kurs bleibt Arbeitsort.
- **Abgaben:** **jede inhaltliche Kachel hat eine Form von Abgabe** – Test, Abgabe oder Auftrag mit Ergebnis
  (Einstieg: der Eingangstest); dazu je Zyklus die Abgabe des Handlungsprodukts. **In Moodle nur automatisierte
  Bewertung:** Abgaben ohne Note und ohne Rückmeldung; die Lehrkraft bewertet außerhalb des Kurses.
- **Sterne:** Gewichtung je Kurs im Kursplan festlegen (welche Tests und Aktivitäten wie viele Sterne geben).
- Gefragt wird typischerweise: Gliederung (Vorschlag: **ein Abschnitt je Leitfrage der Doppelstunde**, Titel = Leitfrage,
  einmal Freischalten je DS; **Phase an jeder Aktivität** im Kursplan, Aktivitäten in Phasenfolge; keine
  Unterabschnitte; kein Phasen- oder Zyklusname im Titel); Selbsttests je Abschnitt (nur wo sinnvoll);
  Sonderfälle bei Abgaben und Bewertung; Videos (Helfer sucht 3–5 deutsche Kandidaten, Auswahl durch die
  Lehrkraft); eigene Simulationen oder klickbare Bilder, die die KI vorschlägt; Abweichungen vom
  Umsetzungskatalog.
- Der **Kursplan (DOCX)** wächst nach jeder Antwort mit (`werkzeug/kursplan.py`): Einstieg (Handlungssituation,
  Selbsteinschätzung vorher, Eingangstest mit Fehlvorstellungen), je Abschnitt die Aktivitäten mit didaktischer
  Begründung (Teilkompetenz, Phase, warum diese Aktivität, Fehlvorstellung, Lernzeit, Sozialform), Rückblick
  (Selbsteinschätzung nachher, Generalprobe, bewerteter Abschlusstest, Medaillen, Glossar), verborgener
  Lehrkraftbereich, verbleibender Bewertungsaufwand, offene Punkte markiert. **Freigabe des Kursplans** = Startsignal.

## 3. Bau in einem Lauf (ohne Rückfragen)

1. Je Abschnitt **ein Helfer, alle parallel**: Kurstext (knapp, sachlich, 2–3 Sätze je Abschnitt, Sie-Form,
   Niveau aus der Klassen-Akte), Fragen (aus dem Material; Anforderungsbereiche frei, Begründung im Kursplan;
   Operatoren korrekt; Distraktoren als Fehlvorstellungen mit ID-Nummer und antwortspezifischer Rückmeldung;
   Rechnungen als berechnete Fragen mit Zufallswerten auf gleichem Niveau), Aktivitätsbeschreibungen. Ausgabe je
   Abschnitt als Teil der Kursdefinition (JSON, `werkzeug/mbz/kursdefinition.py`).
2. **Zusammenbau per Programm** (`werkzeug/mbz/bauen.py`), ohne KI.
3. **Die Prüfer** (`werkzeug/mbz/pruefen.py`, derzeit 14, Liste in `TITEL`; Prüfer 14 „Inseln“ wertet die
   Voraussetzungen der Übungsinseln für alle Wege aus; Prüfer 13 „Vorgriff“ an der
   Kursdefinition), bei Fehlern beheben und neu bauen; danach im Test-Moodle einspielen (`werkzeug/testmoodle/einspielen.sh`).
4. Vorschaubilder je Abschnitt; **Sichtprüfung durch einen frischen Helfer** in der Rolle der Lernenden.
5. **Prüfbericht** (Fehler / Warnung / Hinweis) und **Abnahme** durch die Lehrkraft.

**Live in der Werkbank** (Lehrkraft 2026-10-24): Nach jedem fertigen Abschnitt (abschnitt_N.json) und nach der
fertigen Sicherung `python3 ../unterrichtspipeline-referendariat/akten/app.py <arbeitsbereich>` ausführen, neue Bilder
aus `.daten/ansicht/hochladen.txt` als Asset der Werkbank hochladen (`--assets`) und `app/moodle_<kurz>` sowie
`app/moodle_inhalt_<kurz>` setzen; die Lehrkraft sieht den Kurs dann Kachel für Kachel entstehen
(`werkzeug/mbz/vorschau.py`, solange die Sicherung fehlt aus `bau/`).

## 4. Fester Aufbau-Rahmen (keine Pflichtbausteine darüber hinaus)

- **Gestufte Aufgaben** (empfohlener Weg für Differenzierung, KONZEPT 2026-11): die Aufgaben einer Kachel als
  Platzhalter `{"typ": "stufen", "kachel", "titel", "aufgaben": {Grundlagen|Standard|Vertiefung: [{thema, fragen, …}]}}`
  (`werkzeug/mbz/stufen.py`); Auftrag und Infoseite bleiben gemeinsam, gleiches Lernziel auf allen Stufen,
  Aufgabenformen nach dem Thema. Der Bau setzt Stufenkasten (ohne Prozent-Untertext), Stufenzeichen, verborgene
  Mittelwerte und Voraussetzungen ein; „Mein Stufenweg“ (Verlauf) mit `stufen.dateien_anlegen(wurzel)` und
  `allgemein_aktivitaeten: [stufen.weg_aktivitaet(kursdef)]` nach `stufen.einsetzen(kursdef)`. Nach dem Einspielen
  einmal Cron laufen lassen (Bewertungen neu berechnen).
- **Individueller Lernpfad mit Übungsinseln** (weiter verfügbar, nur wenn der Kursplan ihn ausdrücklich vorsieht): Übungsinseln als Platzhalter `{"typ": "insel", …}`
  in der Kachel, an der die Fähigkeit gebraucht wird (`werkzeug/mbz/inseln.py`: drei Stufen mit Übung und Kurztest,
  Voraussetzung der ganzen Insel = die Abgabe davor); Bedingungen, Hervorhebung „Ihre Stufe“ und ID-Nummern macht
  der Bau. Inseln geben keine Sterne und ändern den Stern „selbst gelöst“ nicht. „Mein Lernpfad“ in Allgemein mit
  `moodle.lernpfad_anzeige` (`lernpfad.py`). Beispiel: `werkzeug/mbz/beispiel_inseln.py`.
- Abschnitt „Allgemein“ kurz und nie leer, jeder Teil per Profilschalter: Vorgeschmack auf die Situation (ein bis
  zwei Sätze), Steckbrief (Lernfeld, Umfang, Ergebnis, Ansprechpartner mit `lehrkraft.anrede` und `lehrkraft.email`),
  „So arbeiten Sie in diesem Kurs“, ganz unten Schullogo mit dem **einzigen KI-Hinweis** im Kurs: „Dieser Kurs wurde
  von <Anrede Name> mit Hilfe von künstlicher Intelligenz erstellt und von ihm/ihr geprüft.“ Nicht in der
  Kursbeschreibung, nicht in Aktivitäten; Werkzeug, Version und Datum im Lehrkraftbereich. Dateien aus Pipeline 2
  behalten ihre KI-Fußzeile.
- **Die volle Handlungssituation steht in Kachel 1** (Einstieg) als deren Auftrag (`moodle.handlungssituation`),
  darunter Selbsteinschätzung und Eingangstest.
- **Auftrag im Kacheltext** (Abschnittsbeschreibung) ganz oben, genau einmal, kein eigenes Element „Ihr Auftrag“:
  Problem und Ergebnis, Arbeitsschritte in der Reihenfolge, in der sie gemacht werden; darunter die Aktivitäten
  chronologisch.
- **Word-Dateien nie nur als Download:** je Datei eine Infoseite, die den Inhalt zeigt, Download am Ende.
- Kachelformat laut Profil; **Kachelbilder** (`moodle.kachelbilder`, flache SVG-Illustration in den Schulfarben, als
  PNG) und **Kachelnummern** 1, 2, 3 … (`moodle.kachelnummern`); der Lehrkraftbereich hat weder Bild noch Nummer.
- Einstieg sichtbar; alle weiteren Abschnitte verborgen, die Lehrkraft schaltet frei; Abschlussverfolgung überall.
- **Sterne als eine Währung für den ganzen Kurs:** aus Tests (nach Prozent), Abschlusstest und weiteren
  Aktivitäten, dazu **je Kachel ein Stern „selbst gelöst“**, wenn der Auftrag ohne Hilfekarte erledigt wurde.
  **Hilfekarten sind frei zugänglich**; wer eine öffnet, verliert den Selbstlöse-Stern dieser Kachel (Moodle merkt
  es sich, die Lehrkraft sieht es im Dashboard).
- **Begriffswand idiotensicher:** Begriffe aufs Foto ziehen und Alltagswort → Fachbegriff zuordnen, als Test mit
  Sternen; kein freies Schreiben, das für andere sichtbar wird.
- Selbsteinschätzung **nur zweimal je Lernsituation** (Einstieg und Rückblick, Sätze aus dem Kompetenzcheck von
  Pipeline 2), in keinem Abschnitt dazwischen.
- Rückblick: Selbsteinschätzung (dieselben „Ich-kann“-Sätze wie am Anfang, zwei Niveau-Fragen, „Das nehme ich
  mit …“), Generalprobe (beliebig viele Versuche), bewerteter Abschlusstest (ein Versuch, Vollbild, ohne Glossar),
  vier Medaillen-Seiten mit Zugriff nach **Anteil erreichter von möglichen Sternen** (Kursgesamt, „Nur bewertete
  Aspekte“ = Nein; Grenzen aus `moodle.medaillen_grenzen`: teilgenommen, Bronze, Silber, Gold), **erst nach dem
  Abschlusstest** (UND-Bedingung „Abschlusstest bewertet“), und je ein Abzeichen („Holen Sie hier
  Ihre Medaille ab.“), Glossar **nur zum Nachschlagen** (Kategorien „Begriffe“ und „Unsere Musterlösungen“, von der
  Pipeline gefüllt; Lernende legen keine Einträge an).
- Verborgener Lehrkraftbereich: Ordner „Druckvorlagen LS n“ mit unveränderten Originalen aus Pipeline 2 (keine PDFs),
  einseitige Handreichung (Ablauf, Freischaltplan, Bewertungsaufwand, Medaillen, Dashboard, Liste „Nur für diese
  Klasse“), Kursplan, Erwartungshorizonte, Notenschlüssel, Bewertungsbogen, KI-Verzeichnis, Lernstand-Dashboard
  (erste Ansicht: **Live-Klassenübersicht** je Lernende – Sterne erreicht/möglich, Medaille, Kacheln ohne Stern,
  geöffnete Hilfekarten; die übrigen Ansichten als Zusatz).
- Kursname „<Klasse> · LF n · LS n <Titel>“, Kurzname „<Klasse>-LFnn-LSnn“, Schulfarben, Kursbild aus der
  Handlungssituation; Kachelformat nur laut Profil.
- Barrierefreiheit: Alternativtexte, Gliederung, Kontrast, nie nur Farbe, ≥ 16 px, Tastatur bei eigenem HTML.
- Quellen an jeder Abbildung und im Literaturverzeichnis, egal woher (Europathek, Verlage, Internet, Hersteller).

## 5. Ablage

Kursplan, Kursdefinition, Bauskript und `.mbz` unter `<LS>/Moodle/` im Arbeitsbereich; KONZEPT nur bei neuen
Entscheidungen; commit und push in beiden Repos. **Test-Moodle ist die Spielwiese** (`C:\moodle-playground`,
http://localhost:8090): dort jeden Kurs **als neuen Kurs** einspielen
(`python ~/.claude/skills/moodle-spielwiese/scripts/spielwiese.py import --schueler <mbz>`) und durchklicken.
Einspiel-Anleitung: `docs/anleitung_einspielen.md` (allgemein, gilt für alle Kurse; immer als neuen Kurs).
