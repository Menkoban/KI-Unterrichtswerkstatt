"""Wenn-dann-Tabelle aus der gezeichneten Steuerung (Regel 37): jede Zeile wird mit plan.schaltfolge gerechnet,
nicht von Hand geschrieben. Die Lehrkraft bestätigt die Tabelle; die Zeilen sind zugleich Prüffälle.

    python3 werkzeug/schaltplan/funktionstabelle.py
Ausgabe: docs/stilreferenz/funktionstabelle_wendeschuetz.md
"""
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
REPO = HIER.parents[1]
sys.path.insert(0, str(HIER / "beispiele"))
sys.path.insert(0, str(HIER))
import wendeschuetz as ws  # noqa: E402
from plan import schaltfolge  # noqa: E402

ZUSTAND = {(False, False): "Stillstand", (True, False): "Rechtslauf", (False, True): "Linkslauf",
           (True, True): "beide Schütze (Kurzschluss!)"}
# (Ausgangslage in Worten, Vorgeschichte, Handlung in Worten, Handlung); je Eintrag (Kennzeichen, von, bis)
ZEILEN = [
    ("Stillstand", [], "-S2 Rechts drücken", [("-S2", 2, 2.5)]),
    ("Stillstand", [], "-S3 Links drücken", [("-S3", 2, 2.5)]),
    ("Rechtslauf", [("-S2", 0, 0.5)], "-S3 Links drücken", [("-S3", 2, 2.5)]),
    ("Linkslauf", [("-S3", 0, 0.5)], "-S2 Rechts drücken", [("-S2", 2, 2.5)]),
    ("Rechtslauf", [("-S2", 0, 0.5)], "-S1 Aus drücken", [("-S1", 2, 2.5)]),
    ("Rechtslauf", [("-S2", 0, 0.5)], "-S1 Aus, danach -S3 Links", [("-S1", 2, 2.5), ("-S3", 3, 3.5)]),
    ("Rechtslauf", [("-S2", 0, 0.5)], "Kiste betätigt -B1 (Endlage rechts)", [("-B1", 2, 99)]),
    ("Endlage rechts (-B1 betätigt)", [("-S2", 0, 0.5), ("-B1", 1, 99)], "-S2 Rechts drücken", [("-S2", 2, 2.5)]),
    ("Endlage rechts (-B1 betätigt)", [("-S2", 0, 0.5), ("-B1", 1, 99)], "-S3 Links drücken", [("-S3", 2, 2.5)]),
    ("Linkslauf", [("-S3", 0, 0.5)], "Kiste betätigt -B2 (Endlage links)", [("-B2", 2, 99)]),
    ("Endlage links (-B2 betätigt)", [("-S3", 0, 0.5), ("-B2", 1, 99)], "-S2 Rechts drücken", [("-S2", 2, 2.5)]),
    ("Stillstand", [], "-S2 und -S3 gleichzeitig drücken", [("-S2", 2, 2.5), ("-S3", 2, 2.5)]),
    ("Rechtslauf", [("-S2", 0, 0.5)], "Motorschutz -F2 löst aus", [("-F2", 2, 99)]),
    ("-F2 ausgelöst (nicht zurückgesetzt)", [("-F2", 0, 99)], "-S2 Rechts drücken", [("-S2", 2, 2.5)]),
]


def rechnen(iv, t):
    ein = lambda tt: {b for b, a, e in iv if a <= tt < e}       # noqa: E731
    an = next(a for tt, a in schaltfolge(ws.st, ein, {}, ende=t) if abs(tt - t) < 1e-9)
    return ZUSTAND[(an["-Q1"], an["-Q2"])]


def tabelle():
    zeilen = []
    for nr, (lage, vor, handlung, iv) in enumerate(ZEILEN, 1):
        vorher = rechnen(vor, 1.9)
        nachher = rechnen(vor + iv, max(e for _, _, e in iv if e < 99) + 1 if any(e < 99 for *_, e in iv) else 4)
        zeilen.append((nr, lage, vorher, handlung, nachher))
    return zeilen


if __name__ == "__main__":
    z = tabelle()
    md = ["# Wenn-dann-Tabelle Wendeschützschaltung mit Endschaltern",
          "", "Aus dem gezeichneten Plan gerechnet (plan.schaltfolge), Stand: schaltplan_wendeschuetz_a3.", "",
          "| Nr. | Ausgangslage | Handlung | Ergebnis |", "|---|---|---|---|"]
    for nr, lage, vorher, handlung, nachher in z:
        if not lage.startswith(vorher.split()[0]) and vorher != "Stillstand":
            raise SystemExit(f"Zeile {nr}: Ausgangslage {lage} passt nicht zur Rechnung ({vorher})")
        md.append(f"| {nr} | {lage} | {handlung} | {nachher} |")
    ziel = REPO / "docs" / "stilreferenz" / "funktionstabelle_wendeschuetz.md"
    ziel.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
