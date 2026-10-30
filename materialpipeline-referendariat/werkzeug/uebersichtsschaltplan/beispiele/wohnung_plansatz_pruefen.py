"""Gemeinsame Prüfung des Plansatzes Wohnung: EI-01 (Installationsplan unter und auf Putz), EI-02 (Übersichtsschaltplan
Installation), EI-03 (Verteiler-Übersichtsschaltplan). Prüfbericht mit Fehler / Warnung / Hinweis.

Geprüft wird, ob alle Pläne dieselbe Verschaltung (wohnung_netz.py) zeigen:
- jede Leitung genau einmal gezeichnet, mit der berechneten Aderzahl (EI-01 beide Fassungen, EI-02);
- dieselben Betriebsmittel und Dosen mit denselben Kennzeichen;
- je Stromkreis dieselbe erste Dose bzw. dasselbe Gerät, derselbe Querschnitt (EI-02 ↔ EI-03 ↔ Bemessung);
- Bemessung fehlerfrei (Rechenprüfer).

    python3 werkzeug/uebersichtsschaltplan/beispiele/wohnung_plansatz_pruefen.py
"""
import importlib.util
import re
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
GRUNDRISS = HIER.parents[1] / "installationsplan" / "beispiele"
sys.path.insert(0, str(HIER.parent))
sys.path.insert(0, str(GRUNDRISS))
sys.path.insert(0, str(HIER))
from wohnung_netz import STROMKREIS, n as NETZ  # noqa: E402

meld = []


def melde(stufe, text):
    meld.append((stufe, text))


def lade(name):
    """Grundriss-Beispiel als eigenes Modul laden (jede Fassung mit eigenem Plan)."""
    spec = importlib.util.spec_from_file_location(name, GRUNDRISS / "wohnung.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


soll = {frozenset(k) for k in NETZ.kanten}
knoten_soll = {x for k in NETZ.kanten for x in k} - {"UV"}

# ---------- EI-01 unter Putz und auf Putz ----------
for fassung, funktion in (("UP", "leitungen_unter_putz"), ("AP", "leitungen_auf_putz")):
    m = lade(f"grundriss_{fassung}")
    getattr(m, funktion)(m.p)
    gezeichnet = [frozenset(k) for k in m.KANTEN[fassung]]
    for k in soll - set(gezeichnet):
        melde("Fehler", f"EI-01 {fassung}: Leitung {'–'.join(sorted(k))} fehlt")
    for k in {k for k in gezeichnet if gezeichnet.count(k) > 1}:
        melde("Fehler", f"EI-01 {fassung}: Leitung {'–'.join(sorted(k))} doppelt")
    zahlen = {z for _, z, *_ in m.p.leitungen}
    if None in zahlen:
        melde("Fehler", f"EI-01 {fassung}: Leitung ohne Aderzahl")
    kenn = {g.stromkreis or g.kenn for g in m.p.geraete} - {"UV"}
    for k in knoten_soll - kenn:
        melde("Fehler", f"EI-01 {fassung}: {k} fehlt im Grundriss")
    for k in kenn - knoten_soll:
        melde("Fehler", f"EI-01 {fassung}: {k} im Grundriss, aber nicht in der Verschaltung")

# ---------- EI-02 Übersichtsschaltplan ----------
import wohnung as ei02  # noqa: E402  (baut beim Import nur die Felder, prüft fehlende Leitungen selbst)

for fd in ei02.u.felder:
    for l in fd.leitungen:
        if l.ziel.kenn and l.adern is None:
            melde("Fehler", f"EI-02: Leitung zu {l.ziel.kenn} ohne Aderzahl")
kenn02 = set(ei02.E) - {""}
for k in knoten_soll ^ kenn02:
    melde("Fehler", f"EI-02: {k} nicht in beiden (Verschaltung ↔ Übersichtsschaltplan)")
for m in ei02.u.pruefen():
    meld.append(m)
einsp = {e.stromkreis: e for fd in ei02.u.felder for e in fd.einspeisungen}

# ---------- EI-03 Verteiler und Bemessung ----------
from wohnung_bemessung import ENTWURF, bemessen  # noqa: E402

r, zeilen, _ = bemessen(ENTWURF)
if not r.fehlerfrei:
    melde("Fehler", "Bemessung meldet Fehler (siehe wohnung_bemessung.py)")
for sk, (char, In, A, Ib, text) in ENTWURF.items():
    e = einsp.get(sk)
    if e is None:
        melde("Fehler", f"EI-02: Einspeisung {sk} fehlt")
        continue
    if e.ziel.kenn != STROMKREIS[sk]:
        melde("Fehler", f"{sk}: EI-02 speist {e.ziel.kenn}, Verschaltung {STROMKREIS[sk]}")
    q = float(re.search(r"Cu ([\d,]+)", e.leitung).group(1).replace(",", "."))
    if q != A:
        melde("Fehler", f"{sk}: Querschnitt EI-02 {q} mm², Bemessung/EI-03 {A} mm²")
    if e.adern != NETZ.adern("UV", STROMKREIS[sk]):
        melde("Fehler", f"{sk}: Aderzahl der Zuleitung EI-02 {e.adern}, Verschaltung {NETZ.adern('UV', STROMKREIS[sk])}")
melde("Hinweis", "EI-03 bezieht Stromkreise, Aderzahl und Querschnitt direkt aus Verschaltung und Bemessung.")
melde("Hinweis", "EI-01: Kreuzungen im Wohnzimmer (unter Putz 2, auf Putz 3) zwischen F1 (obere) und F2 (untere "
                 "Installationszone), im Plan als „Kreuzung ohne Punkt“ erklärt.")

if __name__ == "__main__":
    print("Prüfbericht Plansatz Wohnung (EI-01 UP/AP, EI-02, EI-03)")
    for stufe in ("Fehler", "Warnung", "Hinweis"):
        print(f"  {stufe}: {sum(s == stufe for s, _ in meld)}")
    for s, t in dict.fromkeys(meld):
        print(f"  [{s}] {t}")
    sys.exit(1 if any(s == "Fehler" for s, _ in meld) else 0)
