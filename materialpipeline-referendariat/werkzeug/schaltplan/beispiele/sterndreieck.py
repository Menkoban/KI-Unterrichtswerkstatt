"""Probe Stern-Dreieck-Anlauf (Entscheidung A, 2026-10-14): Haupt- und Steuerstromkreis aus dem Plan-Baukasten,
Werte mit dem Rechenprüfer, Ablauf der Steuerung als Schaltfolge nachgeprüft.

Kennzeichen wie im Schulbeispiel „Stern-Dreieck-Anlauf“ (Netzschütz -Q1, Sternschütz -Q2, Dreieckschütz -Q3,
Zeitrelais -K1 anzugsverzögert). Motorschutzrelais -F2 im Strang (U1, V1, W1), eingestellt auf 0,58 · I_N.

    python3 werkzeug/schaltplan/beispiele/sterndreieck.py
Ausgabe: docs/stilreferenz/schaltplan_sterndreieck_a3.{tex,pdf,png}
"""
import math
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

ZIEL = REPO / "docs" / "stilreferenz" / "schaltplan_sterndreieck_a3"

# ---------------------------------------------------------------- Rechnung (Typenschild als Annahme)
r = Rechnung("Stern-Dreieck-Anlauf Förderband")
P = r.gegeben("P_N", 7.5, "kW", stellen=1, text="Bemessungsleistung (Typenschild)")
U = r.gegeben("U", 400, "V", stellen=0, text="Netz 3/N/PE AC 400/230 V; Motor 400 V Δ / 690 V Y")
eta = r.gegeben("η", 0.89, stellen=2, text="Wirkungsgrad (Typenschild)")
cos = r.gegeben("cos φ", 0.83, stellen=2, text="Leistungsfaktor (Typenschild)")
ia_in = r.gegeben("I_A/I_N", 7.0, stellen=1, text="Anzugsstromverhältnis (Katalog)")
IN = r.schritt("I_N", "P_N / (√3 · U · η · cos φ)", P.q / (math.sqrt(3) * U.q * eta.q * cos.q), "A", stellen=1)
Istr = r.schritt("I_Str", "I_N / √3", IN.q / math.sqrt(3), "A", stellen=1, text="Strangstrom im Dreieck")
IF2 = r.schritt("I_F2", "0,58 · I_N", 0.58 * IN.q, "A", stellen=1, text="Einstellwert -F2 im Strang")
IAD = r.schritt("I_AΔ", "I_A/I_N · I_N", ia_in.q * IN.q, "A", stellen=0, text="Anzugsstrom direkt im Dreieck")
IAY = r.schritt("I_AY", "I_AΔ / 3", IAD.q / 3, "A", stellen=0, text="Anzugsstrom im Stern (Netz)")
r.schritt("I_Q1", "I_N / √3", IN.q / math.sqrt(3), "A", stellen=1, text="Netzschütz -Q1 (Strangstrom, AC-3)")
r.schritt("I_Q3", "I_N / √3", IN.q / math.sqrt(3), "A", stellen=1, text="Dreieckschütz -Q3 (Strangstrom, AC-3)")
r.schritt("I_Q2", "I_N / 3", IN.q / 3, "A", stellen=1, text="Sternschütz -Q2 (AC-3)")
r.gegenprobe(IAY, ia_in.wert * IN.wert / 3, "A", "Zahlen direkt")
T_K1 = 10
r.gegeben("t_K1", T_K1, "s", stellen=0, text="Sternzeit -K1 (Annahme; Moeller nennt für seine Kombination ca. 10 s, je nach Hochlaufzeit einstellen)")
# typische Fehler der Lernenden
r.fehlerweg("I_F2,f", "Einstellung auf I_N statt Strangstrom", IN.q, "A", stellen=1)
r.fehlerweg("I_AY,f", "I_AΔ / √3 statt / 3", IAD.q / math.sqrt(3), "A", stellen=0)


def wert(g, n=1):
    return zahl(g.wert, n)


# ---------------------------------------------------------------- Ablauf der Steuerung als Schaltfolge
def eingaben(aus_bei=None, f2_bei=None):
    """Ein-Taster -S2 die ersten 0,5 s; optional Aus-Taster -S1 oder Auslösen von -F2."""
    def ein(t):
        m = {"-S2"} if t < 0.5 else set()
        if aus_bei is not None and aus_bei <= t < aus_bei + 0.5:
            m.add("-S1")
        if f2_bei is not None and t >= f2_bei:
            m.add("-F2")
        return m
    return ein


def ablauf_pruefen(st, t_k1=10.0):
    """Ablauf aus der gezeichneten Steuerung (plan.schaltfolge), nicht aus einer zweiten Logik."""
    v = schaltfolge(st, eingaben(), {"-K1": t_k1}, ende=14)
    zu = {t: (a["-Q1"], a["-Q2"], a["-Q3"]) for t, a in v}
    if any(a["-Q2"] and a["-Q3"] for _, a in v):
        r.melden("Fehler", "Ablauf: Stern- und Dreieckschütz gleichzeitig ein (Kurzschluss)")
    if zu[1.0] != (True, True, False):
        r.melden("Fehler", f"Ablauf: nach 1 s nicht Stern (Q1, Q2, Q3 = {zu[1.0]})")
    if zu[t_k1 + 1] != (True, False, True):
        r.melden("Fehler", f"Ablauf: nach {t_k1 + 1:.0f} s nicht Dreieck (Q1, Q2, Q3 = {zu[t_k1 + 1]})")
    for name, ein in (("Aus-Taster -S1", eingaben(aus_bei=8.0)), ("Motorschutz -F2", eingaben(f2_bei=8.0))):
        if any(v for s_, v in schaltfolge(st, ein, {"-K1": t_k1}, ende=14)[110][1].items() if s_ != "-K1"):
            r.melden("Fehler", f"Ablauf: {name} schaltet nicht ab")
    # Gegenseitige Verriegelung: Schaltfolge zeigt kein Überlappen, auch wenn Schütze gleich schnell wären;
    # deshalb zusätzlich prüfen, dass der Pfad jedes der beiden Schütze einen Öffner des anderen enthält
    pfad = {pf.elemente[-1].bmk: pf.elemente for pf in st.pfade}

    def oeffner(folge, bmk):
        return any((isinstance(e, K) and e.bmk == bmk and e.art == "Ö") or
                   (isinstance(e, Parallel) and all(oeffner(z, bmk) for z in e.zweige)) for e in folge)
    for a_, b_ in (("-Q2", "-Q3"), ("-Q3", "-Q2")):
        if not oeffner(pfad[a_], b_):
            r.melden("Fehler", f"Verriegelung fehlt: kein Öffner von {b_} im Pfad von {a_}")
    umschalt = next(t for t, a in v if a["-Q3"])
    r.melden("Hinweis", f"Ablauf aus dem Plan geprüft: Stern ab 0 s, Dreieck ab {zahl(umschalt, 1)} s, -Q2 und -Q3 "
                        f"nie gleichzeitig; Aus-Taster und Motorschutz schalten ab.")
    return v


# ---------------------------------------------------------------- Plan
p = Plan(titel="Stern-Dreieck-Anlauf", untertitel="Antrieb Förderband -M1", zusatz="Haupt- und Steuerstromkreis",
         datum="14.10.2026")
zn = Zeichner()
ny = netz(zn, 405)

xs = (60.0, 68.0, 76.0)
pe_x = 190.0
y = hs.einspeisung(zn, xs, ny, 248)
y = hs.sicherung3(zn, xs, y, "-F1", "3 × 25 A gG")
hs.sterndreieck(zn, xs, y, "-Q1", "-Q2", "-Q3", "-F2", f"eingest. {wert(IF2)} A\\\\(0,58 · I\\textsubscript{{N}})",
                "-M1", f"{wert(P)} kW, 400 V Δ", pe_x, ny["PE"])

st = Steuerung(
    x0=220.0,
    stamm=[Sich("-F3", zusatz="2 A"),
           K("-F2", "Ö", "95", "96", bet="thermisch"),
           K("-S1", "Ö", "11", "12", bet="druck", zusatz="Aus"),
           Parallel([[K("-S2", "S", "13", "14", bet="druck", zusatz="Ein")], [K("-Q1", "S", "13", "14")]])],
    pfade=[
        Pfad([Spule("-K1", f"{zahl(T_K1, 0)} s", art="anzug")]),
        Pfad([K("-K1", "Ö", "15", "16", bet="anzug"), K("-Q3", "Ö", "21", "22"), Spule("-Q2", "Stern")]),
        Pfad([Parallel([[K("-Q2", "S", "13", "14")], [K("-Q1", "S", "43", "44")]]), Spule("-Q1", "Netz")]),
        Pfad([K("-K1", "S", "15", "18", bet="anzug"), K("-Q2", "Ö", "21", "22"), Spule("-Q3", "Dreieck")]),
    ],
    pfad_abstand=46.0, n_x=400.0)
yn = steuerung_zeichnen(zn, st, ny["L1"], ny["N"])
kontaktspiegel(zn, yn - 8)
zn.tikz("\\node[dat,anchor=west] at (220,%.1f) {Kontaktspiegel: Zahl = Spalte des Kontakts};" % (yn - 36))

if __name__ == "__main__":
    ablauf_pruefen(st, T_K1)
    for m in ueberdeckungen(zn.z + zn.oben):          # nichts verdecken (Lehrkraft 2026-10-14)
        r.melden("Fehler", m)
    print("\n".join(r.zeilen()))
    print(r.bericht())
    if not r.fehlerfrei:
        raise SystemExit("Rechnung oder Ablauf mit Fehlern")
    ZIEL.with_suffix(".tex").write_text(blatt(p, "\n".join(zn.z + zn.oben)), encoding="utf-8")
    env = {"TEXINPUTS": str(REPO / "werkzeug" / "schaltzeichen") + "//:", "PATH": "/usr/bin:/bin:/usr/local/bin"}
    import os
    env = {**os.environ, **env}
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
