# Checkliste Übersichtsschaltplan je Raum (Europa-Stil)

Vorbild: Tapken, H.: Schalten, Steuern und Automatisieren – Aufgabensammlung. 3. Aufl., Haan-Gruiten:
Europa-Lehrmittel 2025 (korr. Nachdruck 2026), S. 6–20; ergänzend Europa 33951-8 S. 20 (Leitungsangabe, Verlegeart,
Aderzahl an der Einspeisung) und 37566-7 S. 17 (Verbindungspunkt Ø 1,0 mm).
Messwerte: docs/recherche/2026-10-14_uebersichtsschaltplan.md.
Generator: werkzeug/uebersichtsschaltplan (Regeln mit * prüft `Uebersicht.pruefen()` automatisch, Fehler brechen ab).

1. Einpolig, schwarz, Linien 0,25 mm, rechtwinklig auf 5-mm-Raster. **Nie schräge Linien** (Lehrkraft 2026-10-14,
   auch wenn Europa S. 7 einmal schräg abgeht).* Deshalb höchstens vier Anschlüsse je Abzweigdose.*
1a. **Je Stromkreis ein zusammenhängender Strang** (Lehrkraft 2026-10-14, Europa S. 15): eine Zuleitung vom
   Unterverteiler in die erste Dose, danach Dosen untereinander verbunden; keine Einzelwege vom Verteiler zu jedem
   Gerät. Gliederung nach Stromkreisen, Raumgrenzen gestrichelt mit Raumname.
1b. Verschaltung und Aderzahlen aus derselben Quelle wie der Installationsplan (`netz.py`); jede Leitung der
   Verschaltung ist gezeichnet.*
2. Aufbau wie S. 15–20: Abzweigdosen (Ø 3,0 mm, weiß) in einer Reihe, Kennzeichen darüber; Leuchten (Kreuz 4 × 4 mm)
   über der Dosenreihe, Schalter und Steckdosen darunter; Kennzeichen links vom Zeichen.
3. Einspeisung von links mit gefülltem Pfeil (3,12 × 2,12 mm) bis an die Dose, „L/N/PE“ über dem Anfang.
   Gerät ohne Dose (Steckdose, Herd): Einspeisung von oben (S. 9). Herd: „L1/L2/L3/N/PE“.
4. **Aderzahl an jeder Leitung**, auch an Einspeisung und durchgeschleiften Leitungen, immer einschließlich
   Schutzleiter (S. 17), **berechnet** aus der Verschaltung (`netz.py`), gegengeprüft mit dem Soll je Gerät.* Strich 3,77 mm, 0,20 mm, 37°, Ziffer rechts oben. Soll: Ausschalter 3, Serien- und
   Wechselschalter 4, Kreuzschalter 5, Leuchte 3, Steckdose 3, Herd 5.*
5. **An jeder Einspeisung**: Stromkreis (F…), Leitungsangabe wie Europa („NYM-J Cu 1,5“) und Putzzeichen der
   Verlegeart (33951-8). Waagerecht unter der Leitung, senkrecht gedreht links daneben (von rechts lesbar,
   DIN EN 61082-1).
6. **Verbindungspunkt** (gefüllt, Ø 1,0 mm) überall, wo sich außerhalb einer Dose drei Leitungsäste treffen,
   z. B. beim Durchschleifen von Steckdosen (Entscheidung A, 2026-10-14).*
7. Keine Kreuzungen.*
8. Steckdosen mit Zweck darunter (Kühlschrank, Arbeitsfläche …); Mehrfachsteckdose mit Schrägstrich und Anzahl.
9. Kennzeichen, Dosen, Aderzahlen und Stromkreise identisch mit dem Installationsplan (Q/E/X nach DIN EN IEC 81346-2).
10. Zeichenerklärung auf dem Blatt (alle verwendeten Zeichen einschließlich Verbindungspunkt und Putzzeichen).
11. Hinweise: Netzsystem und Spannung, Leitungstyp und Querschnitte, Verweis auf Verteiler-Übersichtsschaltplan
    (Bemessungsströme, RCD, Leitungslängen). Quelle des Vorbilds und KI-Hinweis im Schriftfeld.

## Verteiler-Übersichtsschaltplan (EI-03)

Vorbild: Europa-Lehrmittel, Fachkunde Elektrotechnik 35. Aufl. S. 280 (Stromkreisverteiler), Arbeitsbuch 37566-7 S. 17.
Generator: werkzeug/uebersichtsschaltplan/verteiler.py; Werte aus `wohnung_bemessung.py` (Rechenprüfer).

V1. Einpolig, Energiefluss von oben nach unten: Einspeisung mit Pfeil, Aderzahl, Leitungsangabe, Herkunft
    (Zählerplatz, SLS) und Netz („3/N/PE AC 400/230 V 50 Hz, TN-S“) auf die Sammelschiene (0,7 mm), Abzweige mit
    Verbindungspunkt.
V2. Leitungsschutzschalter: Schließer mit Auslösepfeil, Kennzeichen links („F1“), Charakteristik und
    Bemessungsstrom rechts („B10“), Außenleiter darüber; mehrpolig mit kurzen Strichen am Schaltstück.
V3. Fehlerstrom-Schutzschalter: wie V2, Querstrich am Pfeil, Text „RCD Typ A, In, IΔn“, Polzahl als Aderzahl
    (4). Alle Endstromkreise hinter RCD ≤ 30 mA (DIN VDE 0100-410); Licht und Steckdosen eines Raumes auf
    verschiedene RCD.
V4. Jeder Abgang: Aderzahl, Putzzeichen, Leitungsangabe („NYM-J 3 × 1,5“), Ziel mit erster Dose bzw. Gerät.
V5. **Bemessung gerechnet** (Rechenprüfer, Tabelle auf dem Blatt): Ib ≤ In ≤ Iz (Iz nach DIN VDE 0298-4 für die
    Verlegeart), Spannungsfall Zähler → entferntestes Betriebsmittel beim Bemessungsstrom ≤ 3 % (DIN 18015-1);
    Leitungslänge aus dem Installationsplan. Bei Fehler wird der Plan nicht gebaut. Annahmen auf dem Blatt.

## Plansatz (EI-01 bis EI-03)

P1. Eine Verschaltung für alle Pläne (`wohnung_netz.py`); `wohnung_plansatz_pruefen.py` prüft vor jeder Freigabe:
    jede Leitung genau einmal mit berechneter Aderzahl (EI-01 unter und auf Putz, EI-02), gleiche Kennzeichen,
    gleiche erste Dose, Aderzahl und Querschnitt je Stromkreis (EI-02 ↔ EI-03 ↔ Bemessung), Bemessung fehlerfrei.*
