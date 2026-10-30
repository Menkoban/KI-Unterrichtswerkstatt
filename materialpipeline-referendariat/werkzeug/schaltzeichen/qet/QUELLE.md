# Quelle der Schaltzeichen

Die Zeichnungen in `symbole.tex` sind **unverändert übertragen** (Maßstab 60 px = 1 cm) aus der
QElectroTech-Elementsammlung, Ordner `10_electric/91_en_60617`
(https://github.com/qelectrotech/qelectrotech-elements, abgerufen 2026-10-13).

Lizenz der Sammlung: Nutzung in Schaltplänen ohne Bedingungen; Weitergabe außerhalb eines Schaltplans
(z. B. dieser Katalog) unter **CC-BY 3.0** (Namensnennung: „QElectroTech-Elementsammlung“). Die Sammlung
darf nicht als Trainingsdaten für maschinelles Lernen verwendet werden.

Nummer = EN-60617-Nummer aus dem Dateinamen, deutscher Name aus der Elementdatei.
Korrekturen an defekten Quellelementen stehen in `korrekturen.csv`.
Neu erzeugen: `python -I qet2tikz.py <pfad>/91_en_60617 qet`, Katalog: `python katalog.py 02,03,04,05,06,07,08,11 <ziel.pdf>`.
