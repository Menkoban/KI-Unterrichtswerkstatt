# Quellen zur Symbolliste (symbolliste.csv)

Abrufdatum aller Quellen: 2026-10-13. Es wurden keine fremden Dateien ins Repo übernommen, nur Nummern und Titel.

| Nr. | Titel | URL | Was sie belegt |
|---|---|---|---|
| 1 | IEC 60617 – Graphical Symbols for Diagrams, Vorschau der Datenbank (IEC Webstore, Seitenstand 2026-03-02, 53 S.) | https://webstore.iec.ch/en/iec_catalog/product/preview/?id=L3B1Yi9wZGYvcHJldmlldy9pbmZvX2llYzYwNjE3e2VkMS4wfWIucGRm | Amtliche Liste aller S-Nummern mit englischem und französischem Titel (S00001 bis S01934), ohne alte Nummern. Quelle für alle Werte in `iec_s`; die Seitenzahl im Beleg ist die PDF-Seite. |
| 2 | IEC 60617 – Graphical Symbols for Diagrams, ältere Vorschau (Stand 2018-03-02), bereitgestellt von Normservis | https://www.normservis.cz/download/view/iec/info_iec60617_DB.pdf | Vergleichsstand: zeigt z. B. S00448 (PEN-Leiter), das 2026 durch S01929 ersetzt ist. |
| 3 | QElectroTech-Elementsammlung, Ordner `10_electric/91_en_60617` (912 Elemente, Dateiname = EN-60617-Nummer, Lizenz CC-BY 3.0) | https://github.com/qelectrotech/qelectrotech-elements/tree/master/10_electric/91_en_60617 | Alte Nummern TT-AA-NN der Teile 02 bis 08 und 11 mit deutschem und englischem Titel. Hauptquelle für `iec_alt`. Die englischen Titel entsprechen den IEC-Titeln, darüber wurde jede alte Nummer der S-Nummer zugeordnet. |
| 4 | ProfiCAD-Symbolgalerie (Kategorien electrical-power-control, electronics, house-electrical-symbols, electrical-installations) | https://gallery.proficad.com/symbols/ | Zweite, unabhängige Quelle für alte Nummern (verborgenes Feld „EN 60617 TT-AA-NN“ je Symbol). Einträge mit „EN 606172 …“ gehören zu einem anderen Nummernsystem und wurden nicht verwendet. |
| 5 | Wikipedia: Liste der Schaltzeichen (Elektrik/Elektronik) | https://de.wikipedia.org/wiki/Liste_der_Schaltzeichen_(Elektrik/Elektronik) | Dritte Quelle für alte Nummern (59 Nummern, Teile 02, 04, 05). Die Seite trägt den Hinweis „Belege fehlen“. Widerspruch: Schottky-Diode dort mit 05-02-04, laut QElectroTech ist 05-02-01 der Schottky-Effekt. |
| 6 | EN IEC 61131-3:2025 (SIST-Fassung), Leseprobe mit Inhaltsverzeichnis | https://cdn.standards.iteh.ai/samples/sist/sist-en-iec-61131-3-2025/304db702494542d3967013c23cf5823b/sist-en-iec-61131-3-2025.pdf | Abschnitte und Tabellen für KOP/FUP: 8.2.2 bis 8.2.5 (Stromschienen, Verbindungen, Kontakte, Spulen), Tab. 31, 33, 44 bis 47, 73 bis 75. |
| 7 | IEC 60848:2013 GRAFCET, Leseprobe mit Inhaltsverzeichnis | https://cdn.standards.iteh.ai/samples/19077/a0175aea9c504229beb0d6b01861b5d0/IEC-60848-2013.pdf | Abschnitte und Tabellen für GRAFCET: Abschnitt 5 mit Tab. 1 bis 7, 6.2.3, 6.2.6, 6.2.7, 7.2.2 bis 7.5. |
| 8 | Einträge der IEC-60617-Datenbank im Suchmaschinen-Index, z. B. https://library.iec.ch/grasymb/grasymb.nsf/(SysSymbol)/S00227 | https://library.iec.ch/grasymb/grasymb.nsf/(SysSymbol)/S00227 | Stichprobe: S00227 = 07-02-01 („Earlier published in IEC 60617-7 07-02-01“), S00229 = 07-02-03. Bestätigt die Zuordnung alte Nummer ↔ S-Nummer über den Titel. Ein Direktabruf war nicht möglich (HTTP 403). |

## Hinweise zur Bewertung

- **belegt:** Die alte Nummer steht in Quelle 3, 4 oder 5, die S-Nummer in Quelle 1, und die Titel passen zueinander. Bei KOP/FUP/GRAFCET steht der Abschnitt bzw. die Tabelle im Inhaltsverzeichnis der Norm (Quelle 6 oder 7).
- **unsicher:** Mehrere Formen mit gleichem Titel, die nur über die Reihenfolge zugeordnet sind, ein geänderter Titel oder ein Tabellenbuch-Symbol, das kein eigenes Normsymbol ist.
- **offen:** Das Symbol gehört in die Bibliothek, aber keine Quelle nennt eine eigene Nummer. Das sind meist zusammengesetzte Symbole, z. B. LS-Schalter, RCD und NTC; die Bausteine stehen in der Beschreibung.
- Nicht verwendet wurden inoffizielle Kopien der IEC-Datenbank (z. B. auf dokumen.pub). Daraus wären auch die alten Nummern der Logik-Elemente (Teil 12) ablesbar, aber sie sind keine zulässige Quelle.
- Zu prüfen bleibt bei Zugriff auf DIN EN 60617-12 bzw. die IEC-Datenbank (Abo) Folgendes: die alten Nummern der Teile 12 und 13 und die S-Nummern, die im aktuellen Verzeichnis fehlen (Masse 02-15-04, Kreuzschalter 11-14-07, Serienschalter 11-14-05, Hupe/Klingel 08-10-05/06, Kontakte 07-06-01 bis 03, Auslöser 02-13-24/25).
