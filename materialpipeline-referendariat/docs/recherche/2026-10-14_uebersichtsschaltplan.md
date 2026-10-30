# Übersichtsschaltplan (einpolig) im Europa-Stil – Recherche 2026-10-14

Messung mit pymupdf an Europa-Leseproben (1 pt = 0,3528 mm). Quell-PDFs und Ausschnitte nur lokal (nicht im Repo).

## (a) Installation je Raum – Europa-Aufgabensammlung 32690-3 (Tapken, Schalten, Steuern und Automatisieren – Aufgabensammlung, 3. Aufl. 2025, korr. Nachdruck 2026), S. 6/7, 18/19
| Element | Wert |
|---|---|
| Leitung | 0,25 mm |
| Leiterzahl | Strich 3,77 mm, 0,20 mm, ca. 37° zur Waagerechten (auf senkrechten Leitungen gleiche Lage), Mitte auf der Leitung ca. 10 mm hinter der Dose; Ziffer 9 pt rechts oben |
| Abzweigdose X | Kreis Ø 3,0 mm (S. 6/7) bzw. 2,0 mm (S. 18/19), weiß gefüllt; Kennzeichen darüber |
| Schalter Q | Kreis Ø 4,0 mm, Hebel 3,8–5,8 mm unter 58°, Haken 2,13 mm; Kennzeichen links |
| Leuchte E | Kreuz 4 × 4 mm; Kennzeichen links |
| Steckdose X | Halbkreis 4,0 × 2,0 mm, Schutzkontaktstrich 4,0 mm; Mehrfach: Strich 1,83 mm unter 42° mit Zahl |
| Einspeisung | Linie 12,6 mm + gefülltes Dreieck 3,12 × 2,12 mm bis an die Dose, „L/N/PE“ darüber |
| Schrift | Univers 9 pt (andere Europa-Titel: Normschrift 8 pt, Strich 45–60°) |
Leitungen rechtwinklig, Geräte unten, Dosen in einer Reihe, Verbindungen Dose–Dose waagerecht.

## (b) Verteiler – Europa-Bausteine (kein vollständiges Europa-Beispiel einer Wohnung gefunden)
- Arbeitsbuch 37566-7 S. 17: Einspeiseschiene mit Punkt Ø 1,0 mm, „230 V 50 Hz“; LS „F1“ links, rechts „LS-Schalter / Typ B16“
  (Normschrift 8 pt), Schaltglied 3,85 mm; Leiterzahl 3,70 mm unter 45° mit „3“.
- Fachkunde 35. Aufl. S. 280: LS und RCD („RCD Typ B“), Schaltglied 3,76 mm unter 30°, Zähler-Rechteck „kWh“.
- 35911-8 S. 20: Hauptstromversorgung einpolig, Zähler „Wh“, SLS, „Überspannungsschutz SPD Typ 1“.
- Tabellenbuch 26. Aufl. S. 99: dreipoliger LS „praxisüblich“ mit Kreuz am Festkontakt.
- Vollständiges Wohnungs-Beispiel nur aus fremder Quelle (voltimum-PDF S. 254, Verlag nicht belegt; nicht als Vorlage
  verwendbar): Einspeisung 3/N/PE mit Pfeil und Leitungsangabe, Hauptsicherung, RCDs 40 A/30 mA, LS F1…F9 mit B16A/B10A,
  Außenleiter über dem Abgang, Stromkreisnummer und Raum rechts.
- Fehlend: Tabellenbuch S. 92/93 („Installationsschaltpläne“, „Schaltzeichen für Übersichtsschaltpläne“) – im Druck prüfen.

## Normen und Regeln (Belegstand)
- DIN EN 61082-1: Übersichtsschaltplan meist einpolig (Europa 32416-12 S. 12; IEC-Datenbank Anwendungsklasse).
- DIN 18015-1:2020 (über Hager Tipp 21, 2023): Schaltpläne zeigen Art und Aufbau der Stromkreise, Schutz-, Trenn- und
  Schaltgeräte mit Einbauort; Herd 3L/N/PE, Schutzeinrichtung mind. 20 A; Waschmaschine/Trockner eigene Stromkreise.
- DIN VDE 0100-410 (Europa 37566-7): RCD ≤ 30 mA für Steckdosenstromkreise bis 32 A.
- DIN EN IEC 81346-2: Europa nutzt F (LS, RCD), Q (Schalter), X (Dose, Steckdose), E (Leuchte).
- Nicht eingesehen: Normtexte 61082-1, 0100-510/-530, 81346-2:2019.

## Werkzeuge
- QElectroTech-Elemente `10_electric/11_singlepole` (CC BY 3.0), Rau-Elektrik/elektroplan (MIT, Verteilerpläne für QET,
  Industrie-Stil), schemdraw (MIT, ohne Installationszeichen). Eigener Generator wie beim Grundriss bleibt sinnvoll.

## Nachtrag: Vollständigkeit (Korrektur der Lehrkraft 2026-10-14)
- 32690-3 S. 15–20 (Lernsituation Wohnung): Leuchten über der Dosenreihe, Schalter und Steckdosen darunter, Einspeisung
  von links; S. 17: „Geben Sie für alle Leitungen die Anzahl der Adern mit einem Schutzleiter an, auch wenn dieser
  für das Betriebsmittel nicht erforderlich ist.“ Aderzahl auch auf Dose-Dose-Verbindungen.
- 33951-8 S. 20: Einspeisung mit Aderzahl „3“, Leitungsangabe „NYM-J Cu 1,5“ und Putzzeichen auf der Leitung.
- 37566-7 S. 17: Verbindungspunkt Ø 1,0 mm; LS mit „Typ B16“ am Stromkreis.
- Durchschleifen von Steckdosen: kein Europa-Beispiel; Darstellung mit Verbindungspunkt (Entscheidung A).
