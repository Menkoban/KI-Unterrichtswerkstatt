# Installationspläne: wie echte Pläne gezeichnet sind (Recherche 2026-10-14)

Messung mit pymupdf an Vektor-PDFs (1 pt = 0,3528 mm). Die IEC-60617-Datenbank war nicht abrufbar (HTTP 403);
Angaben daraus nur aus Kurztexten der Suchtreffer. Nicht Belegtes ist so gekennzeichnet.

## Quellen
- **P1** Ausführungsplanung Elektro, Erdgeschoss, Neubau zweier Mehrfamilienhäuser, Gemeinde Wäschenbeuren, Index C,
  20.01.2023, A0, 1:50 (Maßstab nachgemessen: Bett 2 m = 40,0 mm).
  https://www.waeschenbeuren.de/rathaus-service/verwaltung/ausschreibungen/lv-elektroarbeiten
- **P2** Ingenieurbüro (wk-statik), Ausführungsplanung Einfamilienhaus, S. 6 „Grundriss Erdgeschoss Elektroplanung“,
  Stand 14.04.2020. https://www.wk-statik.de/app/download/13492359/Ausf%C3%BChrungsplanung+Einfamilienhaus.pdf
- **P3** Tapken: Schalten, Steuern und Automatisieren – Aufgabensammlung, 3. Aufl., Europa-Lehrmittel, Leseprobe S. 6, 7, 18
  (nur Messvorlage, „Kopieren verboten“). https://www.europa-lehrmittel.de/leseprobe/32690-3.pdf
- **P4** Vortragsfolien „Elektroinstallationsanlagen“ mit Abbildungen aus dem RWE-Handbuch, S. 12, 25, 26 (Rasterbild,
  nur qualitativ). https://sd8acbb1bcaa7f4c1.jimcontent.com/download/version/1509090165/module/7198736863/name/Elektroinstallationsanlagen_pdf.pdf
- W. Meyer: Ausführungspläne für Elektroanlagen, ep 9/2004.
  https://www.elektropraktiker.de/fachartikel/ausfuehrungsplaene-fuer-elektroanlagen/
- IEC 60617 (Kurztexte): S00466 Schalter, S00471 Wechselschalter, S00472 Kreuzschalter ersetzt durch S01915 „Pole
  exchanger, two-pole“ (C00264), Polzahl als Fahne (A00372), S00457/S00460/S00458 Steckdosen, S00454 Abzweigdose,
  S00481 Leuchtenauslass, S00484 Leuchte. https://library.iec.ch/grasymb/grasymb.nsf/

## Ergebnisse
| Merkmal | Befund | Beleg |
|---|---|---|
| Maßstab | 1:50 (Wohnungsbau), große Projekte 1:100 | P1, P2; elektricks.com |
| Grundriss | grau: Wände 0,38 mm mittelgrau mit grauer Füllung, Ausbau 0,25 mm hellgrau | P1 |
| Elektrozeichen | farbig je Gewerk, Starkstrom rot 0,17/0,25 mm, Leuchten cyan; P2 dunkelgrün 0,25 mm; P3 schwarz 0,25 mm | P1–P3 |
| Schalterkreis | Ø 3,77 mm (P1, 69×), Ø 3,98 mm (P3) | P1, P3 |
| Schalthebel | 4,46 mm unter 45°, Haken 2,10 mm rechtwinklig (P1); 3,8 mm unter 58°, Haken 2,13 mm (P3) | P1, P3 |
| Steckdose | Halbkreis Ø 3,77, Querstrich 3,73, Anschlussstrich 2,33 mm; Strich senkrecht zur Wand, endet an der Wandinnenseite, Halbkreis öffnet zum Raum; 2-fach: zwei Halbkreise an einem Querstrich 7,49 mm | P1–P3 |
| Schalter zur Wand | Kreis frei im Raum, Rand ca. 3 mm von der Wand (P1, ein Fall), Hebel zeigt von der Wand weg | P1, P3 |
| Wechselschalter | zwei Hebel gegenüber (oben rechts, unten links) | P1–P3 |
| Kreuzschalter | Kreis mit vier Hebeln in X-Form, Haken an allen Enden | P1, P3 |
| Leuchten | Deckenauslass Kreuz 3,6 mm (P1) / 4 mm (P3); Deckenleuchte Kreis 7,24 mm mit Kreuz (P1) | P1, P3 |
| Leitungen | Planungsbüro: keine Leitungen, Stromkreisbezeichnung an jedem Gerät („1F1.6“), Verweis auf Verteilerpläne; Lehrbuch/RWE: Leitungen rechtwinklig parallel zur Wand mit Leiterzahl | P1, P2, P4; Meyer |
| Leiterzahl | schräger Strich 3,77 mm unter 36° mit Ziffer | P3 |
| Texte | Stromkreisbezeichnung schwarz, Großbuchstaben 3,0 mm; Kennbuchstaben KS, GS, DA, A, RT am Zeichen; Kleinbuchstaben ordnen Schalter und Leuchte zu (nicht erklärt) | P1 |
| Höhen | als Hinweistext: Steckdose 0,30 m, Schalter 1,05 m, Arbeitssteckdose Küche 1,15 m, UK Unterverteiler 1,25 m ü. FFB; 10–30 cm neben Rohbauecken | P1 |
| Installationszonen DIN 18015-3 | waagerecht 30 cm breit (15–45 cm unter Decke / über Fußboden), senkrecht 20 cm (10–30 cm neben Ecken, Türen, Fenstern), Küche 100–130 cm; Vorzugsmaße 30 / 15 / 115 cm | P4 (RWE-Handbuch), Ausgabe nicht belegt |
| Legende | rechts auf dem Blatt, nach Unterputz/Aufputz und Gewerken, Zeichen in Plangröße links, Text rechts | P1, P2 |
| Schriftfeld | Bauherr, Bauvorhaben, Planinhalt, Fachplanung, Gewerk, Datum, Maßstab, Format, Erstellt, Projekt-Nr., Plan-Nr., Stand; Indextabelle | P1 |

## Abgleich mit der Bibliothek (QElectroTech 91_en_60617, Teil 11)
- Gestalt der Zeichen 11-13/11-14/11-15 stimmt mit P1/P3 überein (Schalter mit Haken, Wechselschalter gegenüber,
  Kreuzschalter in X-Form, Steckdose Halbkreis mit Anschlussstrich, Schutzkontakt als Querstrich).
- Bibliothek: Kreis Ø 3,33 mm, Hebel 5,0 mm unter 60°, Haken 1,86 mm. Für Pläne proportional auf Kreis Ø 3,77 mm
  vergrößert (Faktor 1,13, wie P1); Hebel dann 5,65 mm, Haken 2,10 mm (= P1).
- Nachprüfung 2026-10-14 (Korrektur der Lehrkraft): Herdanschluss P1 Quadrat 6,02 × 6,01 mm, Punkte Ø 1,48 mm bei 1,5/4,5 mm; Unterverteiler P1 Rechteck 7,03 × 1,91 mm mit gefülltem Dreieck; Lehrbuch P3 S. 18: Leuchte ×, Mehrfachsteckdose mit Schrägstrich und Zahl „2“.
- Fehler behoben: Das Anwendungsbeispiel `en_60617_11_14_07ex` überschrieb das Zeichen 11-14-07 (Kreuzschalter);
  Zusätze im Dateinamen (ex, A/B, _1 …) bleiben jetzt Teil der Nummer.
- Offen: Gestalt nach DIN EN 60617-11 mit Rastermaßen (Norm/Datenbank nicht zugänglich); Leitungsangabe
  „NYM-J 3x1,5“ im Grundriss in keinem echten Plan gefunden.

## Nachtrag: Verlegeart (auf, im, unter Putz) – Recherche 2026-10-14
- **Zeichen:** Putz-Schraffur (drei schräge Striche mit Deckstrich) auf dem Linienzug; Leitung **über** der Schraffur =
  auf Putz, **durch** die Schraffur = im Putz, **unter** der Schraffur = unter Putz; Leitung im Rohr: kleiner Kreis über
  der Linie (nur etz). Belege: Fachkunde Elektrotechnik, Europa-Lehrmittel, 35. Aufl., S. 681 (Tabelle „Leitungen und
  Leitungsverlegung“, Kopf „nach DIN EN 60617 und VdS 2135“) und S. 102 (Installationsplan mit Legende);
  etz Stuttgart, „Schaltzeichen“, S. 1. Nationale Nummern 111-05-01/02/03 (Makrobibliothek Torunski/Mietke, nach
  DIN 40900); in der IEC-60617-Symbolliste kein Eintrag (nationaler Zusatz, Herkunft DIN 40717 nicht belegt).
  Abbildung: `abbildungen/2026-10-14_verlegearten_etz_stuttgart_S1.png` (Quelle: etz Stuttgart, S. 1).
- **Lage der Linie:** In beiden Beispielplänen (Fachkunde S. 102, etz „Schalt- und Installationspläne“ S. 2) laufen
  die Leitungen raumseitig knapp vor der Wandlinie, Schalter sitzen auf der Leitung; das Putzzeichen steht einmal je
  Leitungsabschnitt. Eine Normregel „vor/auf/in der Wand“ ist nicht belegt.
- **Abzweigdose:** Fachkunde S. 102 und Europa-Aufgabensammlung zeichnen sie als leeren Kreis (X1, X2), nicht mit Punkt.
- Schweizer Praxis (Linienart je Decke/Boden/Wand, elektricks.com) gilt nicht für DIN-Material.
