"""Beispiel DS 7 (Siegelstation, Pt100 in Zweileiterschaltung): Lösung nachrechnen, mit den Mustern abgleichen,
Diagramm für den Erwartungshorizont und leeres Raster für das Arbeitsblatt bauen.

    cd werkzeug/rechnen && python3 beispiele/ds7_leitungswiderstand.py
"""
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent))
from rechnen import Rechnung, lcapy_widerstand  # noqa: E402
from diagramm import Achse, Diagramm  # noqa: E402

REPO = HIER.parents[2]
MUSTER = REPO / "docs/stilreferenz/vorlagen/muster"
ZIEL = REPO / "docs/stilreferenz/rechnen"

r = Rechnung("DS 7 Leitungswiderstand Pt100")
rho = r.gegeben("ρ", 0.0178, "ohm*mm**2/m", text="Kupfer bei 20 °C")
l1 = r.gegeben("l", 45, "m", text="einfache Leitungslänge")
A = r.gegeben("A", 0.5, "mm**2")
R0 = r.gegeben("R_0", 100, "ohm")
alpha = r.gegeben("α", 0.00385, "1/K", stellen=5)
s = r.schritt("S", "R_0 · α", R0.q * alpha.q, "ohm/K", stellen=3, text="Steigung der Kennlinie")
lges = r.schritt("l_ges", "2 · l", 2 * l1.q, "m", stellen=0)
RL = r.schritt("R_L", "ρ · l_ges / A", rho.q * lges.q / A.q, "ohm", stellen=2, erwartet="3,20")
dT = r.schritt("Δϑ", "R_L / S", RL.q / s.q, "K", stellen=1, erwartet="8,3")
# Anlage 5: Messung mit Nachbildung 3,3 Ω (E12)
RN = r.gegeben("R_N", 3.3, "ohm", stellen=1)
r.schritt("Δϑ_N", "R_N / S", RN.q / s.q, "K", stellen=1)
# weitere Zahlen des Falls, damit der Abgleich sie kennt
r.gegeben("l_Linie", 40, "m", text="Verlängerung der Verpackungslinie (Umbauprotokoll)")
r.gegeben("Δϑ_max", 8.5, "K", stellen=1, text="obere Grenze der Rundung im Erwartungshorizont")
# typische Fehler der Lernenden (Werte stehen im Erwartungshorizont)
RLf = r.fehlerweg("R_L,f", "ρ · l / A", rho.q * l1.q / A.q, "ohm", stellen=2, erwartet="1,60")
r.fehlerweg("Δϑ_f", "R_L,f / S", RLf.q / s.q, "K", stellen=1, erwartet="4,2")
r.fehlerweg("Kehrwert", "S / R_L", (s.q / RL.q).magnitude, "dimensionless", stellen=2, erwartet="0,12")

# Gegenprobe: Ersatzwiderstand der Messschleife (Hin- und Rückleiter, Pt100 bei 180 °C) mit lcapy
R180 = 100 * (1 + 0.00385 * 180)
rl1 = 0.0178 * 45 / 0.5
schleife = lcapy_widerstand(f"RL1 1 2 {rl1}\nRpt 2 3 {R180}\nRL2 3 0 {rl1}", 1, 0)
r.gegenprobe(dT, (schleife - 100) / 0.385 - 180, "K", "lcapy-Netzwerk (Schleife bei 180 °C)")

r.abgleich([MUSTER / f"Muster_{n}.docx" for n in
            ("erwartungshorizont", "hilfekarten", "arbeitsblatt", "einstieg", "infoblatt", "serviceauftrag",
             "messprotokoll")])

print("\n".join(r.zeilen()))
print()
print(r.bericht())

# Diagramm: wahre Temperatur → angezeigte Temperatur
pt = lambda t: 100 * (1 + 0.00385 * t)                         # noqa: E731
mit_l = lambda t: pt(t) + RL.wert                               # noqa: E731
d = Diagramm(Achse("Temperatur", "ϑ", "°C", 0, 250, 50), Achse("Widerstand", "R", "Ω", 95, 200, 20))
d.kurve(pt, "Pt100 allein")
d.kurve(mit_l, f"Pt100 + Zuleitung (R_L = {RL.anzeige()})", gestrichelt=True)
y = d.ablesen(180, mit_l, farbe="heiss")
x_anz = 180 + dT.wert
d._teile.append(f"\\draw[black!60,dotted,line width=0.8pt] (axis cs:{x_anz:.4g},{y:.6g}) -- (axis cs:{x_anz:.4g},95);"
                f"\\fill[dunkel] (axis cs:{x_anz:.4g},{y:.6g}) circle (1.8pt);")
d.massband(180, x_anz, 103, dT.anzeige())
d.notiz(177, 128, "wahr 180 °C", "east").notiz(191, 118, f"Anzeige {180 + dT.wert:.0f} °C", "west")
print(d.bauen(ZIEL / "ds7_kennlinie_loesung"))

leer = Diagramm(Achse("Temperatur", "ϑ", "°C", 0, 250, 50), Achse("Widerstand", "R", "Ω", 95, 200, 20), leer=True)
print(leer.bauen(ZIEL / "ds7_kennlinie_leer"))
sys.exit(0 if r.fehlerfrei else 1)
