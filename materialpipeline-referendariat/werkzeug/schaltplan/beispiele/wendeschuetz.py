"""Wendeschützschaltung mit Endschaltern (Stilreferenz; Endschalter ergänzt nach Entscheidung A, 2026-10-15).

Pendelförderband: Rechtslauf bis zur Endlage rechts (-B1), Linkslauf bis zur Endlage links (-B2). Tasterverriegelung im
Tasterzweig der Selbsthaltung und Schützverriegelung: Umschalten nur über -S1 Aus (Lehrkraft 2026-10-15); die Endschalter (Positionsschalter-Öffner 07-08-02) liegen je im Pfad ihrer
Fahrtrichtung unter der Selbsthaltung, damit sie auch bei gehaltener Selbsthaltung abschalten.

Werte mit dem Rechenprüfer (Typenschild als Annahme), Ablauf aus der gezeichneten Steuerung (plan.schaltfolge).

    python3 werkzeug/schaltplan/beispiele/wendeschuetz.py
Ausgabe: docs/stilreferenz/schaltplan_wendeschuetz_a3.{tex,pdf,png}
"""
import math
import os
import subprocess
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
REPO = HIER.parents[2]
sys.path.insert(0, str(HIER.parent))
sys.path.insert(0, str(REPO / "werkzeug" / "rechnen"))
import hauptstrom as hs  # noqa: E402
from plan import (K, Parallel, Pfad, Plan, Sich, Spule, Steuerung, Zeichner, blatt, kontaktspiegel, netz,  # noqa: E402
                  schaltfolge, steuerung_zeichnen, ueberdeckungen)
from rechnen import Rechnung, zahl  # noqa: E402

ZIEL = REPO / "docs" / "stilreferenz" / "schaltplan_wendeschuetz_a3"

# ---------------------------------------------------------------- Rechnung (Typenschild als Annahme)
r = Rechnung("Wendeschützschaltung Pendelförderband")
P = r.gegeben("P_N", 1.5, "kW", stellen=1, text="Bemessungsleistung (Typenschild)")
U = r.gegeben("U", 400, "V", stellen=0, text="Netz 3/N/PE AC 400/230 V")
eta = r.gegeben("η", 0.82, stellen=2, text="Wirkungsgrad (Typenschild, Annahme)")
cos = r.gegeben("cos φ", 0.80, stellen=2, text="Leistungsfaktor (Typenschild, Annahme)")
ia_in = r.gegeben("I_A/I_N", 6.0, stellen=1, text="Anzugsstromverhältnis (Katalog, Annahme)")
IN = r.schritt("I_N", "P_N / (√3 · U · η · cos φ)", P.q / (math.sqrt(3) * U.q * eta.q * cos.q), "A", stellen=1)
IF2 = r.schritt("I_F2", "I_N", IN.q, "A", stellen=1, text="Einstellwert -F2 = Bemessungsstrom (Motor im Dreieck, -F2 in der Zuleitung)")
IA = r.schritt("I_A", "I_A/I_N · I_N", ia_in.q * IN.q, "A", stellen=0, text="Anzugsstrom beim Einschalten und Reversieren")
r.gegenprobe(IN, 1500 / (math.sqrt(3) * 400 * 0.82 * 0.80), "A", "Zahlen direkt")
F2_BEREICH = (2.8, 4.0)                              # Einstellbereich des Motorschutzrelais (Katalogreihe)
if not F2_BEREICH[0] <= IF2.wert <= F2_BEREICH[1]:
    r.melden("Fehler", f"Einstellwert {zahl(IF2.wert, 1)} A liegt nicht im Bereich von -F2")
r.fehlerweg("I_F2,f", "Einstellung auf Anzugsstrom statt Bemessungsstrom", IA.q, "A", stellen=1)
r.melden("Hinweis", "Korrektur gegenüber der ersten Fassung: -F2 war mit 3,5…5 A, eingestellt 4,5 A, angegeben; "
                    "gerechnet sind 3,3 A, daher Bereich 2,8…4 A.")


def wert(g, n=1):
    return zahl(g.wert, n)


# ---------------------------------------------------------------- Plan
p = Plan(titel="Wendeschützschaltung", untertitel="Antrieb Pendelförderband -M1",
         zusatz="Haupt- und Steuerstromkreis, mit Endschaltern", datum="15.10.2026")
zn = Zeichner()
ny = netz(zn, 360)

xs = (60.0, 68.0, 76.0)       # Platz links für Kennzeichen und Daten (Regel 23)
pe_x = 140.0
y = hs.einspeisung(zn, xs, ny, 248)
y = hs.sicherung3(zn, xs, y, "-F1", "3 × 16 A gG")
y = hs.wendeschuetz(zn, xs, y, "-Q1", "-Q2")
y = hs.thermo3(zn, xs, y, "-F2", f"{zahl(F2_BEREICH[0], 1)}…{zahl(F2_BEREICH[1], 0)} A\\\\ eingest. {wert(IF2)} A")
y = hs.klemmen(zn, xs, y, "-X1", pe_x=pe_x)
hs.motor(zn, xs, y, "-M1", f"{wert(P)} kW", pe=(pe_x, ny["PE"]))

st = Steuerung(
    x0=220.0,
    stamm=[Sich("-F3", zusatz="2 A"),
           K("-F2", "Ö", "95", "96", bet="thermisch"),
           K("-S1", "Ö", "11", "12", bet="druck", zusatz="Aus")],
    pfade=[
        # Umschalten nur über -S1 Aus (Lehrkraft 2026-10-15): der Öffner des Gegentasters liegt im Tasterzweig,
        # die Selbsthaltung überbrückt Tasterverriegelung und Ein-Taster (Voltimum, Schützschaltungen Nr. 3)
        Pfad([Parallel([[K("-S3", "Ö", "21", "22", bet="druck", zusatz="Links"),
                         K("-S2", "S", "13", "14", bet="druck", zusatz="Rechts")],
                        [K("-Q1", "S", "13", "14")]]),
              K("-B1", "Ö", "11", "12", bet="position", zusatz="Endlage\\\\rechts"),
              K("-Q2", "Ö", "21", "22"),
              Spule("-Q1", "Rechtslauf")]),
        Pfad([Parallel([[K("-S2", "Ö", "21", "22", bet="druck", zusatz="Rechts"),
                         K("-S3", "S", "13", "14", bet="druck", zusatz="Links")],
                        [K("-Q2", "S", "13", "14")]]),
              K("-B2", "Ö", "11", "12", bet="position", zusatz="Endlage\\\\links"),
              K("-Q1", "Ö", "21", "22"),
              Spule("-Q2", "Linkslauf")]),
    ],
    pfad_abstand=64.0, n_x=350.0)
yn = steuerung_zeichnen(zn, st, ny["L1"], ny["N"])
kontaktspiegel(zn, yn - 8)
zn.tikz("\\node[dat,anchor=west] at (300,%.1f) {Kontaktspiegel: Zahl = Spalte des Kontakts};" % (yn - 12))


# ---------------------------------------------------------------- Ablauf aus der gezeichneten Steuerung
def eingaben(taster=(("-S2", 0.0),), endlagen=(), f2_bei=None):
    """taster: (Kennzeichen, Zeitpunkt) je 0,5 s gedrückt; endlagen: (Kennzeichen, ab, bis) betätigt."""
    def ein(t):
        m = {b for b, t0 in taster if t0 <= t < t0 + 0.5}
        m |= {b for b, a, e in endlagen if a <= t < e}
        if f2_bei is not None and t >= f2_bei:
            m.add("-F2")
        return m
    return ein


def ablauf_pruefen(st):
    def zustand(ein, t):
        return next(a for tt, a in schaltfolge(st, ein, {}, ende=t) if abs(tt - t) < 1e-9)
    faelle = [
        ("Rechts ein", eingaben(), 2, {"-Q1": True, "-Q2": False}),
        ("Links ein", eingaben((("-S3", 0.0),)), 2, {"-Q1": False, "-Q2": True}),
        ("Endlage rechts schaltet ab", eingaben(endlagen=(("-B1", 2.0, 9.0),)), 3, {"-Q1": False, "-Q2": False}),
        ("an der Endlage rechts kein Rechtslauf", eingaben((("-S2", 0.0),), (("-B1", 0.0, 9.0),)), 2,
         {"-Q1": False, "-Q2": False}),
        ("an der Endlage rechts Linkslauf möglich", eingaben((("-S3", 0.0),), (("-B1", 0.0, 9.0),)), 2,
         {"-Q1": False, "-Q2": True}),
        ("Endlage links schaltet ab", eingaben((("-S3", 0.0),), (("-B2", 2.0, 9.0),)), 3, {"-Q1": False, "-Q2": False}),
        ("kein direktes Umsteuern: -S3 im Rechtslauf", eingaben((("-S2", 0.0), ("-S3", 2.0))), 3,
         {"-Q1": True, "-Q2": False}),
        ("kein direktes Umsteuern: -S2 im Linkslauf", eingaben((("-S3", 0.0), ("-S2", 2.0))), 3,
         {"-Q1": False, "-Q2": True}),
        ("Umsteuern über Aus: -S2, -S1, -S3", eingaben((("-S2", 0.0), ("-S1", 2.0), ("-S3", 4.0))), 5,
         {"-Q1": False, "-Q2": True}),
        ("Aus-Taster", eingaben((("-S2", 0.0), ("-S1", 2.0))), 3, {"-Q1": False, "-Q2": False}),
        ("Motorschutz", eingaben(f2_bei=2.0), 3, {"-Q1": False, "-Q2": False}),
        ("beide Taster zugleich", eingaben((("-S2", 0.0), ("-S3", 0.0))), 1, {"-Q1": False, "-Q2": False}),
    ]
    for name, ein, t, soll in faelle:
        ist = zustand(ein, t)
        if ist != soll:
            r.melden("Fehler", f"Ablauf „{name}“: {ist} statt {soll}")
    pfad = {pf.elemente[-1].bmk: pf.elemente for pf in st.pfade}
    for a_, b_ in (("-Q1", "-Q2"), ("-Q2", "-Q1")):
        if not any(isinstance(e, K) and e.bmk == b_ and e.art == "Ö" for e in pfad[a_]):
            r.melden("Fehler", f"Verriegelung fehlt: kein Öffner von {b_} im Pfad von {a_}")
    for spule, b in (("-Q1", "-B1"), ("-Q2", "-B2")):
        if not any(isinstance(e, K) and e.bmk == b and e.art == "Ö" for e in pfad[spule]):
            r.melden("Fehler", f"Endschalter {b} fehlt im Pfad von {spule}")
    r.melden("Hinweis", f"Ablauf aus dem Plan geprüft ({len(faelle)} Fälle): Rechts/Links, Endlagen schalten ab und "
                        f"sperren nur ihre Richtung, kein direktes Umsteuern (nur über Aus), beide Taster zugleich "
                        f"ohne Wirkung, Aus und Motorschutz, Verriegelung.")


if __name__ == "__main__":
    ablauf_pruefen(st)
    for m in ueberdeckungen(zn.z + zn.oben):          # nichts verdecken (Lehrkraft 2026-10-14)
        r.melden("Fehler", m)
    print("\n".join(r.zeilen()))
    print(r.bericht())
    if not r.fehlerfrei:
        raise SystemExit("Rechnung oder Ablauf mit Fehlern")
    ZIEL.with_suffix(".tex").write_text(blatt(p, "\n".join(zn.z + zn.oben)), encoding="utf-8")
    env = {**os.environ, "TEXINPUTS": str(REPO / "werkzeug" / "schaltzeichen") + "//:"}
    e = subprocess.run(["lualatex", "-interaction=nonstopmode", "-halt-on-error", ZIEL.with_suffix(".tex").name],
                       cwd=ZIEL.parent, capture_output=True, text=True, env=env)
    if e.returncode:
        print(e.stdout[-3000:])
        raise SystemExit("LuaLaTeX-Fehler")
    for s in (".aux", ".log"):
        ZIEL.with_suffix(s).unlink(missing_ok=True)
    subprocess.run(["pdftoppm", "-png", "-r", "200", "-singlefile", ZIEL.with_suffix(".pdf").name, ZIEL.name],
                   cwd=ZIEL.parent, check=True)
    print(ZIEL.with_suffix(".png"))
