# Recherche: Repositories für Pipeline 2 (2026-10-13)

Vier Recherchen auf öffentlichem GitHub, GitLab, Codeberg und CTAN, jeder Treffer per Abruf geprüft.
Nichts installiert. Bewertung: **übernehmen** · *als Idee* · ungeeignet. Noch keine Entscheidung;
die Werkzeugwahl fällt in E2 bis E8 bzw. beim Bau der ersten Anlagen.

## Kandidaten für die Werkzeugkette

| Zweck | Werkzeug | Lizenz | Bewertung | Bemerkung |
|---|---|---|---|---|
| DOCX-Vorlagen | docxtpl (elapouya/python-docx-template) | LGPL-2.1 | **übernehmen** | Jinja2 in Word-Vorlage; Layout bearbeitet die Lehrkraft in Word, Python füllt Daten |
| Einheiten, Rechenprüfer | Pint (hgrecco/pint) | BSD | **übernehmen** | jede Lösung gerechnet, Einheitenfehler fallen auf |
| Netzwerke rechnen + Schaltbild | lcapy (mph-/lcapy) | LGPL-2.1 | **übernehmen** | Netzliste → europäisches Schaltbild (über CircuiTikZ) und symbolische Lösung |
| Schaltbilder, normtreu | CircuiTikZ (`european`), TeX Live | LPPL | **übernehmen** | Kern für DIN EN 60617; PDF → SVG/EMF |
| Steuerstromkreise | tikz-relay (CTAN) | LPPL | **übernehmen** | Schütze, Taster, Relais nach IEC 60617; Umfang am Handbuch prüfen |
| Kontaktplan (KOP) | tikz-ladder (CTAN) | LPPL | **übernehmen** | IEC 61131-3 |
| GRAFCET | grafcet (CTAN) | LPPL | **übernehmen** | EN 60848 |
| Einfache Stromkreise | schemdraw (cdelker/schemdraw) | MIT | **übernehmen** (begrenzt) | IEC-Stil nur für R, Poti, LDR, Sicherung; Gatter nur US-Form |
| Installationssymbole | Wikimedia Commons, „Liste der Schaltzeichen“ | je Datei | **übernehmen** als Quelle | Lizenz und Quelle je Symbol ins Literaturverzeichnis |
| Symbolvorlagen | qelectrotech-elements | CC-BY 3.0 bei Weitergabe | *als Idee* | Vorlage für fehlende Symbole |
| Stromlaufpläne komplett | QElectroTech | GPL-2.0 | *beobachten* | CLI-Export noch nicht in einem Release |
| Technologieschemata | draw.io-Bibliotheken + Desktop-CLI unter Xvfb | Apache-2.0 | **übernehmen** | Verfahren wie rlespinasse/docker-drawio-desktop-headless |
| Blockschaltbilder, Abläufe | D2 (terrastruct/d2) | MPL-2.0 | **übernehmen** | eine Datei, SVG/PNG/PDF/PPTX; Mermaid nur mit Chromium |
| Kennlinien | matplotlib + eigenes `.mplstyle` (Vorbild SciencePlots) | – | **übernehmen** | schwarz-weiß-tauglich, Niveaufarben |
| Simulation | Falstad CircuitJS (iframe, Schaltung in der URL) | GPL-2.0 | **übernehmen** | Symbole nicht normgerecht → im Material vermerken |
| Simulation | PhET | CC BY 4.0 (vor 29.03.2026) | *als Idee* | Namensnennung Pflicht, Datum prüfen |
| SPS/GRAFCET interaktiv | eigene kleine HTML-Simulation | – | *als Idee* | keine reife freie Lösung gefunden |
| Sichtprüfung | LibreOffice headless / unoserver + pdftoppm | MIT | **übernehmen** | DOCX/PPTX → PDF → PNG |
| Moodle-Export | eigener GIFT-Export oder gift-wrapper | Apache-2.0 | *als Idee* | eigentlich Pipeline 3 |
| Moodle-Fragetypen | Formulas, STACK | GPL-3 | *als Idee* | bei der Schule klären, ob installiert |
| Aufgaben-Datenmodell | R/exams, typst exercise-bank | GPL / MIT | *als Idee* | eine Vorlage → Blatt, Lösung, Moodle; Metadaten Niveau, LK, LF |

Nicht gefunden: freier FUP-Generator (LOGO!) nach IEC 60617-12, freie Bibliothek für
Installationspläne nach DIN 18015, offenes Repo mit ET-Berufsschulmaterial. Diese Teile bauen wir selbst.

## Planungsablauf und Skills

| Quelle | Lizenz | Was wir übernehmen könnten |
|---|---|---|
| obra/superpowers: brainstorming, writing-plans, verification-before-completion | MIT | Zusammenfassung mit markierten Annahmen nach jedem Block; Freigabe-Tor; Plan mit prüfbarem Ergebnis je Anlage; „fertig“ nur mit Beleg |
| mattpocock/skills: grilling | MIT | Entscheidungsbaum, gefragt wird nur, was entscheidbar ist; Fakten selbst nachlesen; fertig erst, wenn nichts stillschweigend angenommen ist |
| anthropics/skills: doc-coauthoring, pptx/docx | Apache-2.0 bzw. nur einsehbar | Reader-Test (Helfer löst das Blatt als Lernende/r je Niveau); Sichtprüfung mit frischen Augen |
| anthropics/k12-teacher-skills | Apache-2.0 | Differenzierung in drei Stufen, Diagnose-Items aus Fehlvorstellungen, Bewertungsraster |
| GarethManning/claude-education-skills | CC BY-SA 4.0 | gestufte Hilfen, fehlerhafte Beispiele als Prüfkriterien |
