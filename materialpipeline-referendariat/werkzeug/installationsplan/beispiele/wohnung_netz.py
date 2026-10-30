"""Verschaltung der Probe-Wohnung: eine Quelle für Installationsplan (EI-01) und Übersichtsschaltplan (EI-02).

Je Stromkreis genau eine Zuleitung vom Unterverteiler; danach Abzweigdosen, die untereinander verbunden sind
(Korrektur der Lehrkraft 2026-10-14, Vorbild Europa 32690-3 S. 15). Jede Dose höchstens vier Anschlüsse
(Übersichtsschaltplan ohne schräge Abgänge). Steckdosen dürfen durchgeschleift werden (Entscheidung A).

F1 Beleuchtung     UV → X13 (Küche) → X10 → X11 → X12 (Flur) → X14 → X15 (Wohnzimmer)
F2 Steckdosen      UV → X16 (Flur) → X1;  X16 → X6 → X7 → X9 → X8 (Wohnzimmer, durchgeschleift)
F3 Arbeitsfläche   UV → X3 → X4 (durchgeschleift)
F4 Kühlschrank     UV → X2
F5 Geschirrspüler  UV → X5
F6 Elektroherd     UV → E4 (3/N/PE)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from netz import Netz  # noqa: E402

n = Netz()

f1 = n.stromkreis("F1")
n.weg("UV", "X13", "X10", "X11", "X12", "X14", "X15")
for dose, geraete in (("X13", ("Q4", "E2")), ("X10", ("Q3",)), ("X11", ("Q2",)), ("X12", ("Q1", "E1")),
                      ("X14", ("Q5",)), ("X15", ("Q6", "E3"))):
    for g in geraete:
        n.kante(dose, g)
f1.ausschaltung("Q4", ["E2"])
f1.kreuzschaltung(["Q3", "Q2", "Q1"], ["E1"])          # Außenleiter an Q3 (Küchentür), Schaltdraht von Q1
f1.wechselschaltung("Q5", "Q6", ["E3"])

f2 = n.stromkreis("F2")
n.weg("UV", "X16", "X1")
n.weg("X16", "X6", "X7", "X9", "X8")
f2.verbraucher("X1", "X6", "X7", "X9", "X8")

f3 = n.stromkreis("F3")
n.weg("UV", "X3", "X4")
f3.verbraucher("X3", "X4")
for name, geraet in (("F4", "X2"), ("F5", "X5")):
    n.stromkreis(name).verbraucher(geraet)
    n.kante("UV", geraet)
n.stromkreis("F6", aussenleiter=("L1", "L2", "L3")).verbraucher("E4")
n.kante("UV", "E4")

STROMKREIS = {"F1": "X13", "F2": "X16", "F3": "X3", "F4": "X2", "F5": "X5", "F6": "E4"}   # erstes Ziel der Zuleitung

if __name__ == "__main__":
    for m in n.pruefen():
        print(*m, sep=": ")
    for a, b, z, adern in n.tabelle():
        print(f"{a:>4}–{b:<4} {z}  {', '.join(x.split('.', 1)[1] for x in adern)}")
