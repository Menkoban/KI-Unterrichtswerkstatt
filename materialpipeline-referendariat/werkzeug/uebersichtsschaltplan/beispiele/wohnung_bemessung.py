"""Bemessung der Stromkreise der Probe-Wohnung für den Verteiler-Übersichtsschaltplan (EI-03), mit Rechenprüfer.

Leitungslänge aus dem Grundriss (Unterputz-Fassung, wohnung.py) plus senkrechte Wege; Strombelastbarkeit und
Spannungsfall je Stromkreis. Jede Zahl ist gerechnet (Pint), Annahmen stehen in ANNAHMEN und kommen auf den Plan.

Prüfungen:
- Überlastschutz: I_b ≤ I_n ≤ I_z (DIN VDE 0100-430), I_z für Verlegeart C (Leitung direkt in der Massivwand),
  PVC, 30 °C (DIN VDE 0298-4, Tab. 3). Keine Häufung: Spuren 5 cm auseinander, mehr als der doppelte Durchmesser.
- Spannungsfall vom Zähler bis zum entferntesten Betriebsmittel ≤ 3 % beim Bemessungsstrom der vorgeschalteten
  Schutzeinrichtung (DIN 18015-1, Wert über Europa-Tabellenbuch; Normtext nicht eingesehen).

    python3 werkzeug/uebersichtsschaltplan/beispiele/wohnung_bemessung.py
"""
import math
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
REPO = HIER.parents[2]
sys.path.insert(0, str(REPO / "werkzeug" / "rechnen"))
sys.path.insert(0, str(REPO / "werkzeug" / "installationsplan" / "beispiele"))
from rechnen import Rechnung  # noqa: E402
import importlib.util  # noqa: E402

# Grundriss-Beispiel unter eigenem Namen laden (das Übersichtsschaltplan-Beispiel heißt ebenfalls wohnung.py)
_spec = importlib.util.spec_from_file_location(
    "grundriss_wohnung", REPO / "werkzeug" / "installationsplan" / "beispiele" / "wohnung.py")
grundriss = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(grundriss)
from wohnung_netz import n as NETZ, STROMKREIS  # noqa: E402

KAPPA = 56            # m/(Ω·mm²) Kupfer (Europa-Tabellenbuch)
U0, U = 230, 400      # V
GRENZE = 3.0          # % Spannungsfall Zähler → Betriebsmittel (DIN 18015-1)
# I_z in A, Verlegeart C, PVC, 30 °C (DIN VDE 0298-4 Tab. 3): (Querschnitt, belastete Adern) → I_z
IZ_C = {(1.5, 2): 19.5, (1.5, 3): 17.5, (2.5, 2): 27, (2.5, 3): 24, (10, 3): 57}
# Annahmen (offen vorgelegt): Raumhöhe 2,50 m, waagerechte Führung in der oberen Installationszone 2,20 m
# (DIN 18015-3), Mitte Unterverteiler 1,50 m; senkrechter Weg zum Betriebsmittel je nach Montagehöhe
HOEHE = {"zone": 2.20, "UV": 1.50, "schalter": 1.05, "steckdose": 0.30, "arbeit": 1.15, "leuchte": 2.50,
         "herd": 0.70}
ART = {"Q": "schalter", "E": "leuchte", "X": "steckdose"}
ARBEIT = {"X3", "X4"}
HAUPT = dict(l=8.0, A=10, In=35)   # Zählerplatz → UV: NYM-J 5×10, SLS 35 A (Annahme)
ANNAHMEN = ("Raumhöhe 2,50 m; Leitungen waagerecht in der oberen Installationszone (2,20 m, DIN 18015-3), Steckdosen F2 in "
            "der unteren (0,30 m); "
            "Mitte UV 1,50 m; Zählerplatz → UV 8 m NYM-J 5×10 hinter SLS 35 A; κ = 56 m/(Ω·mm²); cos φ = 1; "
            "Strom über die ganze Länge gleich dem Bemessungsstrom (ungünstigster Fall).")

grundriss.leitungen_unter_putz(grundriss.p)
WAAG = {frozenset(k): sum(math.dist(a, b) for a, b in zip(v, v[1:])) for k, v in grundriss.STRECKEN.items()}


def senkrecht(knoten):
    if knoten == "E4":
        return HOEHE["zone"] - HOEHE["herd"]
    if knoten in ARBEIT:
        return HOEHE["zone"] - HOEHE["arbeit"]
    art = ART.get(knoten[0])
    if art is None or knoten.startswith("X1") and len(knoten) == 3 and knoten not in ("X1",):
        return 0.0                                     # Abzweigdose X10–X16 liegt in der Zone
    return abs(HOEHE["zone"] - HOEHE[art])


def wege(sk):
    """Alle Wege vom UV zu den Betriebsmitteln des Stromkreises (Baum aus der Verschaltung)."""
    nb = {}
    for a, b in NETZ.kanten:
        nb.setdefault(a, set()).add(b)
        nb.setdefault(b, set()).add(a)
    start = STROMKREIS[sk]
    erg, offen = [], [(start, ["UV", start])]
    while offen:
        k, w = offen.pop()
        weiter = [m for m in nb[k] if m not in w]
        if not weiter:
            erg.append(w)
        offen += [(m, w + [m]) for m in weiter]
    return erg


UNTEN = {"F2"}          # Steckdosen in der unteren Installationszone 0,30 m durchgeschleift (Entscheidung A)


def laenge(weg, sk=""):
    """Waagerecht aus dem Grundriss; senkrecht: UV hinauf in die Zone, je Steckdose der Durchschleifung hinab und
    wieder hinauf, am Ende hinab zum Betriebsmittel."""
    l = sum(WAAG[frozenset(k)] for k in zip(weg, weg[1:]))
    if sk in UNTEN:                                  # UV hinab in die untere Zone, Steckdosen dort
        return l + HOEHE["UV"] - HOEHE["steckdose"]
    l += HOEHE["zone"] - HOEHE["UV"]
    for k in weg[1:-1]:
        if k[0] == "X" and senkrecht(k) > 0:            # durchgeschleifte Steckdose: hinab und hinauf
            l += 2 * senkrecht(k)
    return l + senkrecht(weg[-1])


def bemessen(schutz, name="Bemessung Wohnung"):
    """schutz: Stromkreis → (Charakteristik, I_n in A, Querschnitt in mm², I_b in A, Text)."""
    r = Rechnung(name)
    kappa = r.gegeben("κ", KAPPA, "m/(ohm*mm**2)", stellen=0)
    lh, Ah, Inh = (r.gegeben(z, HAUPT[k], e, stellen=0) for z, k, e in
                   (("l_H", "l", "m"), ("A_H", "A", "mm**2"), ("I_n,H", "In", "A")))
    u0 = r.gegeben("U_0", U0, "V", stellen=0)
    u = r.gegeben("U", U, "V", stellen=0)
    dUh = r.schritt("ΔU_H", "l_H · I_n,H / (κ · A_H)", lh.q * Inh.q / (kappa.q * Ah.q), "V", stellen=2,
                    text="Hauptleitung je Außenleiter (symmetrische Last)")
    duh = r.schritt("Δu_H", "ΔU_H / U_0 · 100", dUh.q / u0.q * 100, "dimensionless", stellen=2, text="in %")
    zeilen = []
    for sk, (char, In, A, Ib, text) in schutz.items():
        dreh = sk == "F6"
        weg = max(wege(sk), key=lambda w: laenge(w, sk))
        l = r.gegeben(f"l_{sk}", round(laenge(weg, sk), 1), "m", stellen=1, text=f"{sk}: {' → '.join(weg)}")
        a = r.gegeben(f"A_{sk}", A, "mm**2", stellen=1)
        i = r.gegeben(f"I_n,{sk}", In, "A", stellen=0)
        iz = r.gegeben(f"I_z,{sk}", IZ_C[(A, 3 if dreh else 2)], "A", stellen=1, text="Verlegeart C")
        if not (Ib <= In <= iz.wert):
            r.melden("Fehler", f"{sk}: I_b ≤ I_n ≤ I_z verletzt ({Ib} A, {In} A, {iz.wert} A)")
        if dreh:   # Drehstrom symmetrisch: ΔU = √3 · l · I / (κ · A), bezogen auf U = 400 V
            dU = r.schritt(f"ΔU_{sk}", "√3 · l · I_n / (κ · A)", math.sqrt(3) * l.q * i.q / (kappa.q * a.q), "V",
                           stellen=2)
            du = r.schritt(f"Δu_{sk}", f"ΔU_{sk} / U · 100", dU.q / u.q * 100, "dimensionless", stellen=2)
        else:      # Wechselstrom: ΔU = 2 · l · I / (κ · A), bezogen auf U_0 = 230 V
            dU = r.schritt(f"ΔU_{sk}", "2 · l · I_n / (κ · A)", 2 * l.q * i.q / (kappa.q * a.q), "V", stellen=2)
            du = r.schritt(f"Δu_{sk}", f"ΔU_{sk} / U_0 · 100", dU.q / u0.q * 100, "dimensionless", stellen=2)
        proz = du.wert
        gesamt = proz + duh.wert
        if gesamt > GRENZE:
            r.melden("Fehler", f"{sk} ({text}): Spannungsfall {gesamt:.2f} % > {GRENZE:.0f} % "
                               f"(Stromkreis {proz:.2f} % + Hauptleitung {duh.wert:.2f} %, l = {l.wert:.1f} m)")
        zeilen.append(dict(sk=sk, text=text, char=char, In=In, A=A, Iz=iz.wert, l=l.wert, du=proz,
                           gesamt=gesamt, weg=weg, Ib=Ib))
    return r, zeilen, duh.wert


# Entscheidung A (2026-10-14): Licht B10, Steckdosen F2 in 2,5 mm², übrige 1,5 mm² B16, Herd B20 dreipolig
# mit 2,5 mm² (DIN 18015-1: Herd mindestens 20 A)
ENTWURF = {"F1": ("B", 10, 1.5, 3, "Beleuchtung"), "F2": ("B", 16, 2.5, 10, "Steckdosen Flur/Wohnzimmer"),
           "F3": ("B", 16, 1.5, 10, "Arbeitsfläche Küche"), "F4": ("B", 16, 1.5, 2, "Kühlschrank"),
           "F5": ("B", 16, 1.5, 10, "Geschirrspüler"), "F6": ("B", 20, 2.5, 15.2, "Elektroherd 10,5 kW")}

if __name__ == "__main__":
    r, zeilen, duh = bemessen(ENTWURF)
    print(f"Hauptleitung: {duh:.2f} %")
    for z in zeilen:
        print(f"{z['sk']} {z['char']}{z['In']:>2} {z['A']} mm²  I_z {z['Iz']:>4} A  l {z['l']:5.1f} m  "
              f"Δu {z['du']:.2f} % + {duh:.2f} % = {z['gesamt']:.2f} %   {' → '.join(z['weg'])}")
    print(r.bericht())
