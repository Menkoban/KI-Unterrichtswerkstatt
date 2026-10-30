# Schaltzeichen-Bibliothek

- `qet/symbole.tex`: 912 Schaltzeichen nach EN 60617 (Teile 02–08, 11), je Zeichen `\szQ{07-02-01}` usw.,
  1:1 aus der QElectroTech-Sammlung übertragen (Quelle und Lizenz: `qet/QUELLE.md`).
- `qet/symbole.csv`: Nummer, deutscher Name, Quelldatei, Maße.
- `katalog/Schaltzeichenkatalog_EN60617.pdf`: alle Zeichen mit Nummer und Namen zur Prüfung.
- `symbolliste.csv` (Recherche): Abgleich mit IEC-60617-Datenbank (S-Nummern) und Lücken (Logik, KOP/FUP, GRAFCET).
- **Ergänzung** (Liste, Beleg und Status je Zeichen: `ergaenzung.csv`, Quellen und Lückenliste: `quellen_ergaenzung.md`):
  - `qet_logik/symbole.tex`: 9 Logikelemente nach DIN EN 60617-12 aus QET (`\szL{und2}`), `qet_geraete/symbole.tex`:
    11 zusammengesetzte Gerätesymbole aus QET (`\szG{ls_1p}`), beide erzeugt mit `python -I qet2tikz_ergaenzung.py <pfad>/qelectrotech-elements`.
  - `kop_fup/symbole.tex`: 12 KOP-Zeichen mit tikz-ladder (`\szK{schliesser}`), 14 FUP-Kästen (`\szF{ton}`).
  - `grafcet/symbole.tex`: 13 GRAFCET-Elemente mit dem Paket grafcet bzw. eigener TikZ-Zeichnung (`\szA{schritt}`).
  - Katalog: `python -I katalog.py L,K,F,A,G katalog/Schaltzeichenkatalog_Ergaenzung.pdf [png-ordner]`.
    tikz-ladder und ifsym (für grafcet) fehlen in TeX Live aus Ubuntu: aus CTAN laden
    (`https://mirrors.ctan.org/graphics/pgf/contrib/tikz-ladder.zip`, `https://mirrors.ctan.org/fonts/ifsym.zip`),
    entpacken außerhalb des Repos und die Ordner über `SZ_CTAN=<ordner1>:<ordner2>` angeben.
- `bbsschaltzeichen.sty`: alte, von Hand gezeichnete Makros des Wendeschütz-Plans. **Werden ersetzt** durch
  Makros auf Basis von `\szQ` (Regel: nie aus dem Gedächtnis zeichnen).
