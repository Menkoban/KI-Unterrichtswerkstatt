# Schaltplan-Checkliste (Industriestandard)

Gesammelt aus allen Korrekturen der Lehrkraft am Wendeschütz-Plan (2026-10-13). Gilt für **jeden**
Stromlaufplan; Prüfpunkt S7 der Prüf-Checkliste verweist hierher. Stilreferenz:
`docs/stilreferenz/schaltplan_wendeschuetz.tex` (Industrie) bzw. mit Schalter als Lehrbuch-Darstellung.

## Blatt
1. Industrie-Darstellung als Standard: Blattrahmen, Spalten 0–9 oben und unten, Zeilen A–F links und rechts,
   Schriftfeld (Betrieb, erstellt/geprüft, Titel, Anlage =, Ort +, Blatt x/y, Norm DIN EN 61082).
   Lehrbuch-Darstellung nur per Schalter (ohne Rahmen, mit Strompfadnummern).
2. Netz oben: L1, L2, L3, N, PE mit Netzangabe (z. B. 3/N/PE AC 400/230 V 50 Hz). **Bezeichnungen innerhalb
   des Rahmens, nichts abgeschnitten.** PE durchgehend und etwas kräftiger.
3. Hauptstromkreis links, Steuerstromkreis rechts; ausreichend Abstand zwischen Betriebsmitteln.

## Schaltzeichen
4. Nur Zeichen aus der Bibliothek (`\szQ{…}`, 1:1 aus der EN-60617-Sammlung), nie aus dem Gedächtnis.
   Kontaktlänge 1,0. Proportionale Vergrößerung (z. B. Motor) und Spiegeln sind erlaubt.
5. Schütz-Hauptkontakte mit Schützfunktion (07-13-02), Hilfskontakte als Schließer (07-02-01)/Öffner (07-02-03).
6. -F2 Motorschutzrelais: Hauptstromkreis Thermorelais-Antrieb als Kasten (07-15-21); Steuerstromkreis
   Öffner 95–96 (07-02-03) mit thermischer Betätigung (02-13-25) und Wirkverbindung.
7. Sicherungen (07-21-01) mit Anschlussstummeln, Anschlussnummern sauber neben dem Zeichen (nicht auf Linien).
8. Motor (06-08-01) so groß, dass die drei Leiter ohne Knick genau an den Anschlüssen U1, V1, W1 enden.

## Leitungen und Verbindungen
9. Leitungen durchgezogen, ohne Lücken; jede Leitung endet exakt an einem Anschluss.
10. Verbindungspunkt (03-02-01) an jeder T-Abzweigung, nie an bloßen Kreuzungen.
11. Klemmen (03-02-02, offener Kreis) mit Leistenbezeichnung (-X1) und Klemmennummer.
12. Einheitliche Strichstärke 0,8 pt; Wirkverbindungen gestrichelt (02-12-01), ohne andere Kontakte zu kreuzen.

## Bezeichnungen
13. Vollständige Anschlussbezeichnungen an **jedem** Betriebsmittel: Hauptkontakte 1–2, 3–4, 5–6;
    Hilfsschließer 13–14 (43–44 …), Hilfsöffner 21–22 (11–12 bei Aus-Taster), Motorschutz 95–96, Spule A1–A2,
    Motor U1/V1/W1, Klemmen.
14. Betriebsmittelkennzeichen fett (-F1, -Q1, -S1 …), Zusatzangaben klein daneben (3 × 16 A gG, 1,5 kW,
    Einstellwert, Rechtslauf/Linkslauf). Offen nach Tabellenbuch: -Q oder -K für Schütze, -S0 oder -S1 für Aus.
15. **Keine Querverweise.** Kontaktspiegel unter jeder Spule (S | Ö, H = Hauptkontakte, Zahl = Spalte des
    Kontakts) und Legende.

## Prüfung
16. Vorschau mit Kantenglättung vergrößert ansehen: Linien, Anschlüsse, Beschriftungen, Rahmen.
17. Jedes verwendete Zeichen im Katalog nachschlagen (Nummer, Status belegt).

## Korrektur der Lehrkraft (2026-10-13): Originaltreue
18. **Einheitliche, feine Strichstärke** wie in echten Industrieplänen (EPLAN): Leitungen, Zeichen und Rahmen
    nach festen Werten aus der Recherche (`docs/recherche/2026-10-13_planzeichen_proportionen.md`), PE nicht dicker
    als andere Leiter, sofern Originalpläne das nicht zeigen.
19. **Zeichen originalgetreu**: Proportionen (z. B. Winkel des Schaltmessers, Halbkreis, Kastenmaße) gegen die
    Normgrafik geprüft; auch die Elementsammlung kann abweichen. Abweichungen werden korrigiert und belegt.
20. Vorschau immer mit mindestens 200 dpi erzeugen, damit Linien nicht durch die Rasterung unterschiedlich dick wirken.

## Korrektur der Lehrkraft (2026-10-13): Anordnung wie im Industrieplan
21. **Jede Leitung bis an ihren Anschluss** ziehen, auch die mittlere Motorleitung V1 bis in den Motor. Nach dem
    Zeichnen jede Leitungsende-Koordinate gegen einen Anschluss prüfen.
22. **Betätigungen immer links** vom Kontakt (Taster, Not-Halt, thermische Betätigung von -F2, Aus-Taster -S1),
    Wirkverbindung von links an das Schaltmesser. Schließer: Messer nach links. **Öffner: Haken und Messer nach
    rechts** (korrigiert 2026-10-13), die Wirklinie läuft durch die Kontaktlücke an das Messer.
23. **Betriebsmittelkennzeichen links** neben das Betriebsmittel (-F3, -S1, -Q1 …), technische Daten darunter.
24. **Wirkverbindung endet am Schaltmesser** und überdeckt weder Kontakte noch Anschlussnummern oder Abzweige.
25. **Reihenfolge im Strompfad** (präzisiert 2026-10-13, geändert 2026-10-15): Aus-Öffner **über** der
    Selbsthaltung; die **Schütz-Verriegelungs-Öffner (-Q1, -Q2) unter** der Selbsthaltung, direkt über der Spule.
    **Tasterverriegelung (Lehrkraft 2026-10-15): Umschalten nur über Aus.** Der Öffner des Gegentasters liegt im
    Tasterzweig, in Reihe mit dem Ein-Taster; die Selbsthaltung überbrückt beide (Voltimum, Schützschaltungen
    Nr. 3). Die Variante „direktes Umschalten“ (Gegentaster-Öffner über der Selbsthaltung) nur auf ausdrücklichen
    Wunsch. Die Ablaufprüfung prüft: kein direktes Umsteuern, Umsteuern über Aus, beide Taster zugleich ohne Wirkung.
26. **Keine Wirklinien über mehrere Strompfade** (Lehrkraft 2026-10-13): Jeder Tasterkontakt hat seine eigene
    Betätigung links und sein Kennzeichen; die Zusammengehörigkeit zeigt das Kennzeichen. (Baukasten: WIRKLINIE = "einzeln".)
27. **Abstände (Prüfung 2026-10-13):** Anschlussnummern 1,2 mm ab Zeichenkante (nicht ab Achse), frei von
    Verbindungspunkten; Kennzeichen mindestens 2 mm von der Messerspitze; Wirklinie beginnt und endet mit einem
    Strich (Strichmuster an die Länge angepasst); Texte bleiben innerhalb des Rahmens.
28. **Wirklinien aus vielen kurzen Strichen** (≈ 1,2 mm) mit kleinen Lücken (halbe Strichlänge), Anfang und Ende
    jeweils ein Strich (Wunsch der Lehrkraft 2026-10-13).

## Probe Stern-Dreieck (2026-10-14)
29. **Zeitrelais**: Spule mit Ansprechverzögerung (07-15-08, Zusatzkasten mit Kreuz), Kontakte mit
    Verzögerungszeichen (07-05-01 anzugverzögerter Schließer, 07-05-03 Öffner), keine Betätigung links.
    Ein Wechsler: 15–16 (Öffner) und 15–18 (Schließer), wie im Schulbeispiel (Jugend & Volk ZA44).
30. **Stern-Dreieck nach Herstellerplänen** (Korrektur der Lehrkraft 2026-10-14; Moeller-Katalog SDAINL,
    Siemens 24499345 Bild 6/7): Netz-, Dreieck- und Sternschütz **nebeneinander auf einer Höhe**; Dreieckschütz hinter
    der Sicherung vor dem Netzschütz abgegriffen; **Sternbrücke oben** am Sternschütz (1–3–5), 2/4/6 an das
    Dreieckschütz; Motorschutzrelais hinter dem Netzschütz im Strang U1, V1, W1 auf 0,58 · I_N (reines
    Überlastrelais, **Kurzschlussschutz durch -F1**); Motor mit seitlichen Anschlüssen in Vorzugsschaltung
    (L1–U1–V2, L2–V1–W2, L3–W1–U2), Klemmen -X1 1–6 auf einer Höhe, PE von unten ohne Kreuzung.
    Steuerstromkreis wie Moeller: Zeitrelais direkt, Stern über -K1 15–16, Dreieck über -K1 15–18, Netz über
    Stern-Schließer mit Selbsthaltung. Schütze: Netz und Dreieck 0,58 · I_N, Stern 0,33 · I_N (Siemens S. 7).
30a. **Parallelzweig am Pfadanfang** zweigt direkt auf der Verteilleitung ab (keine Absenkung); **Verriegelungs-
    öffner** in allen Pfaden auf gleicher Höhe direkt über den Spulen (Lehrkraft 2026-10-14, im Baukasten).
31. **Ablaufprüfung aus dem Plan**: `plan.schaltfolge()` spielt die gezeichnete Steuerung durch (Ein, Umschalten,
    Aus, Motorschutz); dazu Verriegelungsprüfung (Öffner des anderen Schützes im Pfad). Fehler verhindern den Bau.

## Korrektur der Lehrkraft (2026-10-14): nichts verdecken
32. **Kein Text verdeckt eine Leitung, ein Zeichen oder einen anderen Text** (Kennzeichen, Anschlussnummern, Daten).
    `plan.ueberdeckungen()` prüft jeden Stromlaufplan vor dem Bau (Schätzung der Textbreite); Treffer sind Fehler.
    Bei Installations- und Übersichtsplänen gilt dieselbe Regel in der Sichtprüfung (vergrößerte Vorschau).

## Endschalter (2026-10-15, Wendeschütz mit Endlagen)
33. **Endschalter als Positionsschalter-Öffner 07-08-02** (Kennzeichen am Messer, keine Betätigung links), Kennzeichen
    -B…, darunter die Endlage. Im Pfad der eigenen Fahrtrichtung **unter der Selbsthaltung**, damit er trotz
    Selbsthaltung abschaltet und nur diese Richtung sperrt. Die Ablaufprüfung prüft Abschalten, Sperren und das
    Wegfahren aus der Endlage in Gegenrichtung.
34. **Einstellwert des Motorschutzrelais wird gerechnet** (Rechenprüfer, Typenschild als Annahme) und muss im
    angegebenen Einstellbereich liegen.

## Simulationen (Korrektur der Lehrkraft 2026-10-15)
35. **Betätigte Kontakte werden in Arbeitsstellung gezeichnet**: Schließer geschlossen, Öffner geöffnet
    (Verriegelungen, Endschalter, Gegentaster sichtbar). Ein Rahmen allein genügt nicht. `kontakte.js`; die
    Bauprüfung prüft nach „Ein“, dass die Kontakte des Schützes umgeschaltet erscheinen.
36. **Varianten vor dem Zeichnen klären** (Lehre aus 2026-10-15): Hat eine Schaltung Lehrbuch-Varianten (z. B.
    Wendeschütz „Umschalten nur über Aus“ oder „direkt“, mit/ohne Endschalter), wird die Variante vorher gefragt,
    nicht angenommen. Eine Variante nie als „die richtige“ darstellen, wenn es mehrere gibt.
37. **Soll-Ablauf als Wenn-dann-Tabelle** vor jeder Simulation: Was passiert bei welchem Taster, Endschalter, in welchem
    Zustand. Die Lehrkraft bestätigt die Tabelle; jede Zeile wird eine automatische Prüfung im Plan und im Browser.
