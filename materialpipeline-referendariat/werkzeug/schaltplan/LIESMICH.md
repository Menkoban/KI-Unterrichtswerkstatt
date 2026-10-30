# Plan-Baukasten

Stromlaufpläne werden nicht mehr über Koordinaten gezeichnet, sondern als Strompfade beschrieben
(`beispiele/wendeschuetz.py`). `plan.py` (Steuerstromkreis) und `hauptstrom.py` (dreipolige Bausteine)
ordnen alles nach `docs/regeln/schaltplan_checkliste.md` an; Zeichen aus `werkzeug/schaltzeichen/planzeichen.sty`.

Erzeugen: `python werkzeug/schaltplan/beispiele/wendeschuetz.py`, dann in `docs/stilreferenz`
`TEXINPUTS=../../werkzeug/schaltzeichen//: lualatex schaltplan_wendeschuetz_a3.tex`.

Jede Korrektur der Lehrkraft wird im Programm umgesetzt (nicht im einzelnen Plan) und gilt damit für alle Pläne.
