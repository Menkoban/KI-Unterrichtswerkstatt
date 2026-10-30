# Recherche: Proportionen der Planzeichen und Gestaltung echter Industriepläne (2026-10-13)

Anlass: Rückmeldung einer Lehrkraft, Strichstärken und Zeichen im Stromlaufplan
(`docs/stilreferenz/schaltplan_wendeschuetz_industrie.png`, Quelle `schaltplan_wendeschuetz.tex`)
seien „nicht 100 % originalgetreu“ gegenüber Industrieplänen (EPLAN-PDFs).

Vorgehen: Zwei echte, frei abrufbare EPLAN-Stromlaufpläne zweier unabhängiger Hersteller als
Vektor-PDF geladen (nur im Scratchpad, nicht im Repo), Seiten mit `pdftoppm` gesichtet, mit
`pdftocairo -svg` in Vektorpfade gewandelt und Koordinaten, Strichbreiten, Strichmuster und
Schriftgrößen ausgelesen (Schrift über die PDF-Textmatrix). Alle Pläne liegen im Maßstab 1:1 auf
A3 (420 × 297 mm); Werte in mm auf dem Blatt. Normnahe Grafiken: Wikimedia Commons (SVG-Quelltext).
Die IEC-60617-Datenbank (library.iec.ch, std.iec.ch) war gesperrt (HTTP 403); Originalzeichnungen
der IEC sind deshalb **nicht** vermessen (offener Punkt).

## Quellen

| Kürzel | Quelle | Art | Seiten |
|---|---|---|---|
| **KKT** | KKT chillers (ait-deutschland GmbH): Stromlaufplan cBoxX 100, Dok.-Nr. 81707601.Kd, 22.06.2020, Revision Kd „Umstellung auf EPLAN“. https://www.kkt-chillersusa.com/wp-content/uploads/2022/06/cBoxX_100_-_Wiring_Diagram_81707601.Kd_.pdf | EPLAN-Ausgabe, Vektor, A3 | S. 14 (Sicherung, Klemmen), 24 (Motor), 26 (Motorschutzschalter, Schütz, Motor), 30 (Spulen, Wechsler, Kontaktspiegel) |
| **FES** | Festo Didactic SE: CP-COBOT-D-R23 Circuit Diagrams, Zeichnungsnr. 8175462, 12.03.2024 (EPLAN-Projekt `.elk`, Version 2023.0.3). https://ip.festo-didactic.com/Infoportal/CPFactoryLab/data/CP-COBOT-D/files_R23/schematics.pdf | EPLAN-Ausgabe, Vektor, A3 (Maßstab 0,9996) | S. 13 (Leitungsschutzschalter, Hauptschalter, Klemmen, PE), 15 (Not-Halt, Öffner, Schließer, Leuchte), 16 (Taster Reset) |
| FES-L | Festo Didactic: CP-L-LINEAR-V2 schematics, 8167762, 2025-05-20. https://ip.festo-didactic.com/Infoportal/CPFactoryLab/data/CP-L-LINEAR-V2/files_C11M0/schematics.pdf | EPLAN-Ausgabe | S. 15 (Rastschalter -S3) |
| **ZTV** | Hamburger Stadtentwässerung: ZTV-EPLAN „CAD-Anforderungen EPLAN“, Ausgabe Jan. 2026. https://www.hamburgwasser.de/fileadmin/Redakteur/Downloads/vertragsbedingungen/ZTV/ztv-eplan.pdf | Auftraggeber-Vorgabe | Abschn. 5.1 (Raster 4,00 mm, Maßstab 1:1), 8.3.6 (Symbole für 4-mm-Raster) |
| **WIK** | Wikimedia Commons, Zeichen aus „Liste der Schaltzeichen (Elektrik/Elektronik)“ (de.wikipedia), Inkscape-SVG, 1 mm = 3,5433 px: `Symbol_closing-switch.svg`, `Symbol_opener-switch.svg`, `Symbol_Normally_open_contact_(contactor).svg`, `Symbol_Fuse.svg`. https://upload.wikimedia.org/wikipedia/commons/7/79/Symbol_closing-switch.svg (übrige analog) | normnah gezeichnet (Privatautor), keine Normzeichnung | – |
| **NORM** | IEC 60617: Modul M = 2,5 mm, Abstand der Anschlusslinien 2M (Inhaltsangabe EN 60617, über Suche auf standards.globalspec.com); ISO 81714-1: Linienbreite : Modul = 1 : 10; IEC 61082-1: Linienbreiten 0,1·M·√2ⁿ (zitiert im QElectroTech-Forum, https://qelectrotech.org/forum/viewtopic.php?pid=11934, 08.05.2020) | Sekundärzitat, Normtext nicht eingesehen | – |
| **UNS** | eigener Plan: `docs/stilreferenz/schaltplan_wendeschuetz.tex` mit `werkzeug/schaltzeichen/qet/symbole.tex` (QElectroTech 1:1, 1 cm = 60 px), Plan in cm | – | – |

## Tabelle 1: Zeichen und Proportionen

L = Gesamtlänge des Kontakts (Anschluss oben bis Anschluss unten). Winkel des Schaltmessers gegen
die Senkrechte. „Überstand“ = Spitze des Schaltmessers über das Ende des Festkontakts bzw. Hakens hinaus.

| Zeichen (EN 60617) | Industrie EPLAN (KKT und FES, übereinstimmend) | WIK | UNS (QElectroTech) | Abweichung UNS |
|---|---|---|---|---|
| Schließer 07-02-01 | L = 8 mm; Festkontakt oben 2 (0,25 L), Lücke 4 (0,50 L), unten 2 (0,25 L); Messer Δx 2,5 / Δy 4,5 mm → **29,1°**, Länge 5,15 mm (0,64 L); Überstand 0,5 mm (0,06 L). KKT S. 26 (-Q151, -F151 13/14), FES S. 15 (33/34), S. 16 (Reset) | L = 19 mm; 5 / 9 / 5 mm (0,26 / 0,47 / 0,26 L); Messer Δx 3 / Δy 9 → 18,4°, Länge 0,50 L; kein Überstand | L = 10 mm; 3,33 / 3,33 / 3,33 (je 0,33 L); Messer Δx 1,33 / Δy 3,83 → **19,2°**, Länge 4,06 mm (0,41 L); Überstand 0,5 mm (0,05 L) | Lücke ⅓ statt ½ L; Messer 10° steiler und ein Drittel kürzer |
| Öffner 07-02-03 | L = 8; Festkontakte 2 / 2; Haken waagerecht 2 mm (0,25 L) zur Messerseite; Messer Δx 1,5 / Δy 4,5 → **18,4°**, Länge 4,74 (0,59 L); Spitze 0,5 über Haken, 0,5 vor Hakenende. FES S. 15 (21/22, 11/12) | Haken 3 mm (0,16 L); Messer 18,4°, Spitze 3 mm über Haken | Haken 1,67 mm (0,17 L); Messer 19,2°, Länge 0,41 L; Spitze 0,5 über, 0,33 vor Hakenende | Winkel passt; Haken und Messer kürzer, Lücke kleiner |
| Wechsler 07-02-04/05 | Messer Δx 3,0 / Δy 4,5 → 33,7°; zwei Festkontakte im Abstand ± 4 mm (1 Raster) vom Drehpunkt, je Haken 2 mm nach innen. KKT S. 24 (-F201 95/96/98), S. 30 (-K451) | – | im Plan nicht verwendet | – |
| Schütz-Hauptkontakt 07-13-02 | wie Schließer; **Halbkreis r = 1,0 mm (Ø 2 = 0,25 L)** über den ganzen oberen Festkontakt, zur Messerseite gewölbt. KKT S. 26 (-Q151 1/2…5/6) | Halbkreis r ≈ 0,92 mm bei L = 19 (Ø ≈ 0,10 L) | Halbkreis r = 0,42 mm (**Ø 0,83 mm = 0,08 L**) nur am Kontaktende | Halbkreis 2,4-mal zu klein |
| Leistungsschalter / Motorschutzschalter 07-13-05 | KKT -F151: Hauptkontakte wie Schließer, darunter je Pol ein Kasten 8 × 4 mm thermisch und 8 × 4 mm magnetisch („I>“), Kästen lückenlos aneinander; Handantrieb Quadrat 4 × 4 mm. FES -FC1: Messer wie Schließer, thermisch/magnetisch als schräge Auslöserzeichen; ein „X“ am Festkontakt kommt in beiden Plänen nicht vor | – | im Plan nicht verwendet | – |
| Sicherung 07-21-01 | Körper 2,0 × 5,0 mm (1 : 2,5) in L = 8 (KKT S. 14, -F21, als Sicherungstrennschalter mit Anschlusskreisen Ø 1,5) | 4 × 10 mm (1 : 2,5) in L = 20 | 1,67 × 5,0 mm (**1 : 3**) in L = 10 | Körper etwas zu schmal |
| Spule 07-15-01 | Kasten **8 × 4 mm** (2 : 1), Breite = 1 L = Phasenabstand; Zuleitungen auf Raster. KKT S. 30 (-Q151, -Q152) | (nur Variante mit Schrägstrich, 10 × 6 mm) | Kasten 6,67 × 3,33 mm (2 : 1), Breite 0,67 L | Verhältnis passt, Kasten relativ 1,5-mal zu klein |
| Thermorelais 07-15-21 (Motorschutz) | je Pol Kasten 8 × 4 mm, drei Pole **lückenlos** (24 mm), Bimetall-Zeichen 2 × 1,8 mm (KKT S. 26) | – | Kasten 5,33 × 2,67 mm (0,8-fach skaliert), drei getrennte Kästen mit 1,67 mm Lücke, Zeichen 1,33 × 1,6 mm | Kästen kleiner und getrennt |
| Betätigung Drücken 02-13-05 | in den vermessenen Plänen nicht vorhanden (FES-Reset: Handbetätigung allgemein, senkrechter Strich 2 mm, 8 mm links der Kontaktachse) | – | Bügel 1,67 mm hoch, Schenkel 0,83 mm | **offen**, keine Industriequelle |
| Not-Halt (Pilzdrucktaster, Zwangsöffnung) | Pilzkopf: Bogen + Steg 3 mm hoch, 8,7 mm links der Kontaktachse; Rastung; Zwangsöffnung Kreis Ø 3 mm mit Pfeil am Messer. FES S. 15 (-SF1) | – | im Plan nicht verwendet | – |
| Wirkverbindung 02-12-01 | Strichbreite **0,25 mm = Leiterbreite**, stumpfe Enden; Strich/Lücke **1,75/1,75** (KKT Schütz), 2,25/2,25 (KKT Motorschutzschalter), **2,5/2,5** (FES Not-Halt), 2,0/1,5 und 1/1 (FES); verläuft auf halber Kontakthöhe | – | 0,5 pt = **0,18 mm**, Strich/Lücke **3 pt/2 pt = 1,06/0,71 mm** | dünner und etwa halb so lange Striche |
| Klemme 03-02-02 | Kreis **Ø 1,5 mm** (KKT -XD2, FES -XD0), Geräteanschluss Ø 2,0 mm (KKT -K801) | – | Ø **0,83 mm** | knapp halb so groß |
| Verbindungspunkt 03-02-01 | gefüllt, **Ø 1,75 mm** (KKT S. 26), **Ø 1,25 mm** (FES S. 13) | – | 3,4 pt = Ø 1,20 mm | an der unteren Grenze |
| Motor 06-08-01 | Kreis **Ø 12 mm = 1,5 × Phasenabstand**; äußere Zuleitungen knicken schräg in den Kreis; PE seitlich waagerecht an den Kreis mit kurzem Anschlussstrich; „M“ 3,7 mm Schriftgröße (KKT S. 24, 26) | – | Kreis Ø 21 mm = **3 × Phasenabstand**, Zuleitungen senkrecht | Motor fast doppelt so groß |
| Meldeleuchte 08-10-01 | Kreis Ø 4 mm (0,5 L) mit Kreuz, Zuleitungen 2 + 2 mm (FES S. 15, 16) | – | im Plan nicht verwendet | – |
| Schutzerde / PE-Leiter | PE-Leiter **gleich breit** (0,25 mm) wie alle Leiter; KKT durchgezogen, FES als Strich-Punkt-Linie (6,38/0,8/0,25/0,8 mm), N ebenfalls eigene Linienart | – | PE 1,2 pt = **0,42 mm**, durchgezogen | PE in beiden Industrieplänen nicht dicker |

## Tabelle 2: Gestaltung der Industriepläne

| Merkmal | KKT (EPLAN) | FES (EPLAN) | Vorgabe ZTV / NORM | UNS |
|---|---|---|---|---|
| Blatt | A3 quer 1:1, 10 Spalten à **42 mm**, keine Zeilenbuchstaben | A3 quer 1:1, 10 Spalten à **40 mm** | Maßstab 1:1, A-Normblatt | 21,1 × 20,8 cm, 10 Spalten à **20,5 mm**, Zeilen A–F |
| Raster | alle Koordinaten auf 4/2-mm-Raster | ebenso | **4,00 mm** (ZTV 5.1, 8.3.6); IEC 60617: M = 2,5 mm, Anschlussabstand 2M | frei (cm-Werte) |
| Leiter- und Zeichenlinie | **0,25 mm** (alle 385 Leiter- und Zeichenstriche der S. 26; nur Rahmen 0,35) | **0,25 mm** | ISO 81714-1: Linie = M/10 → 0,25 mm; IEC 61082-1: Reihe 0,25 / 0,35 / 0,5 / 0,7 | 0,8 pt = **0,28 mm** |
| PE | 0,25 mm, durchgezogen | 0,25 mm, Strich-Punkt | – | 1,2 pt = 0,42 mm |
| Wirkverbindung | 0,25 mm, 1,75/1,75 bzw. 2,25/2,25 mm | 0,25 mm, 2,5/2,5 mm | – | 0,18 mm, 1,06/0,71 mm |
| Gerätekasten | Strich-Punkt 3,19/0,4/0,25/0,4 mm | Strich-Punkt 6,38/0,8/0,25/0,8 mm | ZTV 8.3.7 (Anlage, nicht im Text) | – |
| Rahmen / Schriftfeld | Rahmen 0,35 mm | Rahmen 0,35 mm, Schriftfeld und Spaltenteilung 0,18 mm | – | 1 pt (0,35) / 0,5 pt (0,18) / 0,4 pt |
| Phasenabstand (senkrecht) | **8 mm** | **8 mm** | 2M = 5 mm | **7 mm** |
| Sammelschienenabstand (waagerecht) | 4 mm | – | – | 4 mm |
| Kontaktlänge | 8 mm | 8 mm | – | 10 mm |
| Schrift | Tahoma, **normal** | Arial Narrow, **normal** | – | Liberation Sans, BMK **fett** |
| Betriebsmittelkennzeichen | **3,11 mm (8,8 pt)**, Versalhöhe 2,26 mm | **3,31 mm (9,4 pt)**, Versalhöhe 2,37 mm | – | 8 pt fett (2,82 mm) |
| Anschlussbezeichnung | **2,48 mm (7,0 pt)**, Versalhöhe 1,81 mm | **2,38 mm (6,7 pt)**, Versalhöhe 1,71 mm | – | 7 pt (2,47 mm) |
| Querverweis | 2,24 mm (6,3 pt) | 1,99 mm (5,6 pt) | – | 5 pt (1,76 mm) |
| Technische Daten am Gerät | 2,73 mm (7,7 pt) | 1,72 mm (4,9 pt, Kabel) | – | 7 pt |
| Verbindungspunkt | Ø 1,75 mm | Ø 1,25 mm | – | Ø 1,20 mm |
| Klemme | Ø 1,5 mm | Ø 1,5 mm | – | Ø 0,83 mm |
| Linienenden | Zeichen rund, Strichlinien stumpf | ebenso | – | rund |

Schriftgröße = Schriftgrad (Geviert) aus der PDF-Textmatrix; Versalhöhe aus den Glyphenumrissen.

## Befund

1. **Strichstärke der Leiter ist nicht das Problem.** Bezogen auf die Kontaktlänge ist unsere Linie
   (0,28 mm bei 10 mm, 1/36) sogar etwas feiner als EPLAN (0,25 mm bei 8 mm, 1/32).
2. **Strichstärke falsch sind PE und Wirkverbindung:** Beide Industriepläne zeichnen PE und
   Wirkverbindung in derselben Breite wie alle Leiter (0,25 mm). Unser PE ist 1,5-mal dicker,
   unsere Wirklinie dünner und mit halb so langen Strichen.
3. **Zeichengeometrie:** Die QElectroTech-Zeichen haben eine kleinere Lücke (⅓ statt ½ L) und ein
   steileres, kürzeres Schaltmesser (19° statt 29°). Dazu sind Schütz-Halbkreis (Ø 0,08 statt 0,25 L),
   Klemme (Ø 0,83 statt 1,5 mm), Spule (0,67 statt 1,0 L breit) und Thermokasten deutlich kleiner,
   der Motor fast doppelt so groß (Ø 3 statt 1,5 Phasenabstände). Gerade diese Zeichen fallen beim
   Vergleich auf.
4. **Schrift:** Größen stimmen ungefähr; Betriebsmittelkennzeichen sind in der Industrie nicht fett
   und etwa 9 pt groß, Querverweise 6 pt.
5. **Maßstab des Blattes:** Unser Blatt hat die halbe Spaltenbreite von A3; die Zeichen sind relativ
   zum Blatt etwa 2,5-mal größer als im EPLAN-Plan. Das ist eine Layoutentscheidung (Lesbarkeit),
   kein Normfehler.

## Empfehlung (Werte zum Übernehmen)

Konstruktion in Rastereinheiten R wie EPLAN; R = 4 mm ergibt das Original 1:1 auf A3.
Wenn unser Blatt so groß bleibt, R = 5 mm wählen (Kontakt 10 mm wie bisher); alle Werte skalieren
mit R, **die Linienbreite bleibt fest** (Normhinweis: Linienbreite beim Skalieren nicht mitändern).

| Größe | in R | bei R = 4 mm | bei R = 5 mm | heute |
|---|---|---|---|---|
| Kontaktlänge L | 2 R | 8 | 10 | 10 |
| Festkontakt / Lücke / Festkontakt | 0,5 / 1 / 0,5 R | 2 / 4 / 2 | 2,5 / 5 / 2,5 | 3,33 / 3,33 / 3,33 |
| Schließer-Messer Δx / Δy (Winkel) | 0,625 / 1,125 R (29°) | 2,5 / 4,5 | 3,1 / 5,6 | 1,33 / 3,83 (19°) |
| Öffner-Messer Δx / Δy, Haken | 0,375 / 1,125 R (18°), Haken 0,5 R | 1,5 / 4,5, Haken 2 | 1,9 / 5,6, Haken 2,5 | 1,33 / 3,83, Haken 1,67 |
| Wechsler-Messer Δx / Δy | 0,75 / 1,125 R (34°) | 3 / 4,5 | 3,75 / 5,6 | – |
| Überstand Messerspitze | 0,125 R | 0,5 | 0,6 | 0,5 |
| Schütz-Halbkreis Radius | 0,25 R | 1,0 | 1,25 | 0,42 |
| Spule B × H | 2 × 1 R | 8 × 4 | 10 × 5 | 6,67 × 3,33 |
| Thermokasten je Pol, lückenlos | 2 × 1 R | 8 × 4 | 10 × 5 | 5,33 × 2,67, getrennt |
| Sicherungskörper B × L | 0,5 × 1,25 R | 2 × 5 | 2,5 × 6,25 | 1,67 × 5 |
| Phasenabstand | 2 R | 8 | 10 | 7 |
| Sammelschienenabstand | 1 R | 4 | 5 | 4 |
| Motorkreis Ø | 3 R (1,5 Phasenabstände), äußere Leiter schräg hinein | 12 | 15 | 21 |
| Klemme Ø | 0,375 R | 1,5 | 1,9 | 0,83 |
| Verbindungspunkt Ø | 0,375–0,44 R | 1,5–1,75 | 1,9–2,2 | 1,2 |
| Leuchte Ø | 1 R | 4 | 5 | – |
| Linie Leiter, Zeichen, **PE**, **Wirkverbindung** | fest | 0,25 mm (0,7 pt) | 0,25–0,35 mm | 0,28 / PE 0,42 / Wirk 0,18 |
| Wirkverbindung Strich / Lücke | 0,5 / 0,5 R | 2 / 2 | 2,5 / 2,5 | 1,06 / 0,71 |
| Betriebsmittelkennzeichen | 0,8 R, **nicht fett** | 3,2 mm (9 pt) | 4 mm (11 pt) | 8 pt fett |
| Anschlussbezeichnung | 0,6 R | 2,5 mm (7 pt) | 3 mm (8,5 pt) | 7 pt |
| Querverweis | 0,5 R | 2 mm (6 pt) | 2,5 mm (7 pt) | 5 pt |
| Rahmen / Schriftfeld | fest | 0,35 / 0,18 mm | 0,35 / 0,18 mm | passt |

Weitere Hinweise:

- PE nicht über die Strichstärke kennzeichnen, sondern über die Beschriftung (wie KKT) oder optional
  als Strich-Punkt-Linie gleicher Breite (wie FES).
- Die Änderungen weichen von der QElectroTech-Vorlage ab. Wenn die Lehrkraft zustimmt, als
  Korrekturen in `werkzeug/schaltzeichen/qet/korrekturen.csv` führen (oder eigener Zeichensatz
  „EPLAN-Proportionen“) und im Material weiter QElectroTech als Grundlage nennen.
- Offen: Originalzeichnung IEC 60617 (Datenbank gesperrt), Betätigung „Drücken“ und thermische
  Betätigung in einem echten EPLAN-Plan; dafür einen weiteren Herstellerplan mit Tastern suchen.
- Fremde PDFs liegen nur im Scratchpad und kommen nicht ins Repo.
