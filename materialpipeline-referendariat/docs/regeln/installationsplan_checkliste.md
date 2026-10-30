# Installationsplan-Checkliste (Grundriss nach DIN EN 60617-11)

Grundlage: Messung echter Pläne, `docs/recherche/2026-10-14_installationsplaene.md` (P1 Planungsbüro,
P3 Lehrbuch). Generator: `werkzeug/installationsplan/grundriss.py`. Stilreferenz:
`docs/stilreferenz/installationsplan_wohnung_a3.png`. Gilt zusätzlich zu den allgemeinen Regeln 4, 16, 17 und 20
der Schaltplan-Checkliste (Zeichen aus der Bibliothek, Vorschau vergrößert prüfen, mindestens 200 dpi).

## Blatt
1. Maßstab 1:50 (Wohnung); Blatt A3 quer. Rahmen mit Heftrand 20 mm links, sonst 5 mm.
2. Rechts eine Spalte mit Legende (Zeichen in Plangröße links, Text rechts), Hinweisen und Schriftfeld (Bauherr,
   Bauvorhaben, Planinhalt, Fachplanung, Gewerk, Maßstab, Format, Datum, Erstellt, Plan-Nr., Stand).
3. Unter dem Schriftfeld eine eigene Zeile für Quelle und KI-Hinweis; Texte überlappen keine Linien.
4. Fiktive Bauherren und Betriebe als fiktiv gekennzeichnet.

## Grundriss
5. Grundriss grau: Wände 0,38 mm mittelgrau mit grauer Füllung, Türen und Fenster 0,25 mm hellgrau.
6. Türen mit Blatt und Aufschlagbogen; Raumstempel mit Name und Fläche (gerechnet), frei von Zeichen und Texten.

## Elektrozeichen
7. Elektro rot, Strichstärke 0,25 mm; Gestalt nach Bibliothek (11-13, 11-14, 11-15), Proportionen nach P1:
   Schalterkreis Ø 3,77 mm, Hebel 4,46 mm unter 45°, Haken 2,10 mm nach außen.
8. Steckdose: Anschlussstrich 2,33 mm senkrecht zur Wand, endet an der Wandinnenseite; Querstrich (Schutzkontakt)
   3,73 mm parallel zur Wand; Halbkreis Ø 3,77 mm öffnet zum Raum. **Mehrfachsteckdose: ein Zeichen mit
   Schrägstrich durch den Halbkreis und Anzahl** (Bibliothek 11-13-02, Lehrbuch P3; Korrektur der Lehrkraft 2026-10-14,
   vorher zwei Halbkreise wie im CAD-Plan P1).
9. Schalter: Kreis frei im Raum, Rand 3 mm von der Wand, Hebel zeigen von der Wand weg; kein Hebel ragt in die Wand.
10. Schalter an der Schlossseite der Tür, 10–30 cm neben der Öffnung (senkrechte Installationszone DIN 18015-3);
    Abweichungen begründen (z. B. Schalter auf beiden Seiten derselben Wand).
11. Kreuzschalter mit vier Hebeln in X-Form (Bibliothek 11-14-07, nicht das Anwendungsbeispiel 11-14-07ex).
11a. **Leuchte als Leuchtenauslass ×** (3,6 × 3,6 mm, P1; Lehrbuch P3 und RWE ebenfalls), nicht ⊗ (Korrektur der
    Lehrkraft 2026-10-14). **Herdanschluss** als Quadrat 6,0 mm mit drei Punkten Ø 1,48 mm (P1, RWE), nicht als Dose.
    **Unterverteiler** als Rechteck 7,03 × 1,91 mm, diagonal halb gefüllt (P1).

## Beschriftung
12. **Gerätekennzeichen wie im Europa-Lehrbuch** (Entscheidung der Lehrkraft 2026-10-14, B): Q Schalter, E Leuchten
    und Herd, X Steckdosen und Abzweigdosen, je Plan durchnummeriert (Steckdosen vor Dosen, damit die Nummern in
    Industrie- und Lehrbuch-Fassung gleich bleiben); Funktion (Kühlschrank, Arbeitssteckdose …) im Hinweis;
    Stromkreise nur im Übersichtsschaltplan. Industrie-Darstellung (Standard): keine Leitungen. Hinweistext: Installationshöhen
    (Steckdose 0,30 m, Schalter 1,05 m, Arbeitssteckdose Küche 1,15 m, UK Verteiler 1,25 m ü. FFB), Installationszonen,
    Verweis auf den Übersichtsschaltplan.
13. Beschriftung schwarz, nie auf Zeichen, Hebeln, Türbögen oder Wänden; Steckdosen-Text vor dem Zeichen zur
    Raumseite, Schaltertext neben dem Kreis zwischen den Hebeln.

## Lehrbuch-Fassung (Schalter `--lehrbuch`, Entscheidung 2026-10-14 A)
14. Leitungen rot 0,25 mm, **immer gerade und rechtwinklig**, auch zu den Leuchten (Korrektur der Lehrkraft
    2026-10-14); keine schrägen Leitungen. Leitungen enden am Anschlussstrich der Steckdose (zwischen Wand und Querstrich) oder in der Mitte von
    Schalter, Leuchte und Dose (Zeichen weiß gefüllt).
14a. **Primär an den Wänden entlang** (Korrektur der Lehrkraft 2026-10-14): Türöffnungen werden entlang der Wand
    überquert, nie am Türblatt entlang. **Lage wie Fachkunde Elektrotechnik S. 102** (Entscheidung A, 2026-10-14):
    Leitungen raumseitig knapp vor der Wand (Spuren 13–33 cm vor der Wand, 5 cm Abstand); jedes Gerät sitzt auf seiner
    Leitung (im Lehrbuch-Plan um die Spurlage vor die Wand gesetzt), Schalter über einen kurzen Strich angeschlossen.
    Wer früher an ein Gerät abgeht, liegt weiter vorn, damit nichts kreuzt; keine Leitung läuft vor einem fremden Gerät.
14c. **Lage folgt der Verlegeart** (Korrektur der Lehrkraft 2026-10-14): auf Putz → Leitung vor der Wand (raumseitig,
    Geräte auf ihrer Leitung); im Putz und unter Putz → Leitung in der Wand gezeichnet (Spuren in der Wand, Geräte
    an der Wand mit kurzem Anschlussstrich). Putzzeichen und Lage müssen übereinstimmen; der Generator setzt die
    Lage aus der Verlegeart jeder Leitung.
14b. **Verlegeart mit Putzzeichen** (Fachkunde S. 681, etz S. 1): Schraffur aus drei Schrägstrichen mit Deckstrich;
    unter Putz = Schraffur zur Raumseite, auf Putz = zur Wandseite, im Putz = Leitung mittig durch die Schraffur.
    Je Leitung dort, wo Platz ist (nicht im Bündel); Hinweis „alle Leitungen unter Putz“; Legende zeigt das Zeichen.
15. Leiterzahl an jeder Leitung: schräger Strich 3,77 mm unter 36° mit Ziffer (P3), einschließlich PE
    (Ausschaltung 3, Wechselschalter 4, Kreuzschalter 5, Herd 5); Strich und Ziffer frei von anderen Linien und Texten.
16. Abzweigdose als leerer Kreis Ø 3,0 mm (Fachkunde S. 102, P3) für jeden Licht- und Steckdosenzweig; Leitungen kreuzen keine Zeichen, Hebel, Türen
    oder Texte. Unvermeidbare Kreuzungen ohne Punkt (keine Verbindung) und im Hinweis erklärt.
17. Parallele Leitungen: wer früher abbiegt, liegt auf der Seite, zu der er abbiegt (keine Kreuzung im Bündel).

18. **Je Stromkreis eine Zuleitung, Abzweigdosen untereinander verbunden** (Korrektur der Lehrkraft 2026-10-14,
    Vorbild Europa 32690-3 S. 15): keine Einzelwege vom Unterverteiler zu jedem Gerät. Dose bei jeder Verzweigung,
    höchstens vier Anschlüsse; Steckdosen dürfen durchgeschleift werden. Verschaltung in einer `netz.py`-Datei,
    die Installationsplan und Übersichtsschaltplan gemeinsam nutzen.
19. **Aderzahl gerechnet, nicht eingetragen**: `Netz.adern()` zählt je Leitung die Leiter, deren Anschlüsse auf
    beiden Seiten liegen (Außenleiter, N, PE, korrespondierende Leiter, Schaltdraht).
20. **Nie schräge Linien** (Lehrkraft 2026-10-14), auch nicht im Übersichtsschaltplan.
21. **Haken der Schalter immer waagerecht nach außen** (Korrektur der Lehrkraft 2026-10-14): obere Haken nach
    außen-unten, untere nach außen-oben, auch wenn das Zeichen zur Wand gedreht ist. Belege: Bibliothek 11-14-07
    (EN 60617-11, „Intermediate switch“), Europa 32690-3 S. 15 und S. 18 (Grundriss), etz Stuttgart „Schaltzeichen“
    S. 5, Elektricks 2019 S. 6. Ein Kreuzschalter an einer Seitenwand sieht deshalb genauso aus wie in der Norm.
    `schalter_tikz(typ, dreh)` setzt die Haken in Blattlage.
