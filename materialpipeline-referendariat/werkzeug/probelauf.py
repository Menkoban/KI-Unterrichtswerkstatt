"""Probelauf des Werkzeugkastens: baut alle Stilreferenzen neu und führt alle Prüfungen aus.

    python3 werkzeug/probelauf.py            alles
    python3 werkzeug/probelauf.py sterndreieck plansatz   nur diese Punkte (Teil des Namens genügt)

Jeder Punkt meldet OK oder Fehler (mit dem Ende der Ausgabe). Rückgabewert 1, sobald ein Punkt fehlschlägt.
PDFs werden mit festem Datum gebaut (SOURCE_DATE_EPOCH), damit ein Probelauf ohne Änderung keine neuen Dateien
erzeugt; was sich trotzdem geändert hat, zeigt der Bericht am Ende (git status).
"""
import os
import subprocess
import sys
import time
import zipfile
from io import BytesIO
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STIL = REPO / "docs" / "stilreferenz"
PY = sys.executable

ENV = {**os.environ,
       "SOURCE_DATE_EPOCH": "1791936000",        # 14.10.2026, nur für reproduzierbare PDFs
       "FORCE_SOURCE_DATE": "1",
       "TEXINPUTS": str(REPO / "werkzeug" / "schaltzeichen") + "//:"}

GRUNDRISS = "werkzeug/installationsplan/beispiele/wohnung.py"
UEBERSICHT = "werkzeug/uebersichtsschaltplan/beispiele/"
WENDE = "schaltplan_wendeschuetz_a3"

# (Name, Befehle); jeder Befehl: (Argumente, Arbeitsverzeichnis relativ zum Repo)
PUNKTE = [
    ("Installationsplan EI-01 unter Putz", [([PY, GRUNDRISS], ".")]),
    ("Installationsplan EI-01 Lehrbuch", [([PY, GRUNDRISS, "--lehrbuch"], ".")]),
    ("Installationsplan EI-01 auf Putz", [([PY, GRUNDRISS, "--aufputz"], ".")]),
    ("Übersichtsschaltplan EI-02", [([PY, UEBERSICHT + "wohnung.py"], ".")]),
    ("Bemessung Wohnung", [([PY, UEBERSICHT + "wohnung_bemessung.py"], ".")]),
    ("Verteiler-Übersichtsschaltplan EI-03", [([PY, UEBERSICHT + "wohnung_verteiler.py"], ".")]),
    ("Plansatz Wohnung gemeinsam prüfen", [([PY, UEBERSICHT + "wohnung_plansatz_pruefen.py"], ".")]),
    ("Stern-Dreieck-Anlauf", [([PY, "werkzeug/schaltplan/beispiele/sterndreieck.py"], ".")]),
    ("Technologieschema Förderband", [([PY, "werkzeug/technologieschema/foerderband.py"], ".")]),
    ("Simulation Stern-Dreieck, drei Fassungen (Gegenprobe mit dem Plan, Bedienung im Browser)",
     [([PY, "werkzeug/simulation/sterndreieck_sim.py"], ".")]),
    ("Wendeschützschaltung mit Endschaltern", [([PY, "werkzeug/schaltplan/beispiele/wendeschuetz.py"], ".")]),
    ("Wenn-dann-Tabelle Wendeschütz (aus dem Plan gerechnet)", [([PY, "werkzeug/schaltplan/funktionstabelle.py"], ".")]),
    ("Technologieschema Pendelförderband", [([PY, "werkzeug/technologieschema/pendelband.py"], ".")]),
    ("Simulation Wendeschütz, drei Fassungen (Gegenprobe, geschlossener Kreis mit Endschaltern, Browser)",
     [([PY, "werkzeug/simulation/wendeschuetz_sim.py"], ".")]),
    ("Quellenaufnahme (Texterkennung, Quellenkarte, Suche)", [([PY, "werkzeug/quellen/probe.py"], ".")]),
    ("Skills von Pipeline 2 (Kopf, Pfade, Fach-Skills)", [([PY, "werkzeug/skills_pruefen.py"], ".")]),
    ("Rechenprüfer DS 7 Leitungswiderstand", [([PY, "werkzeug/rechnen/beispiele/ds7_leitungswiderstand.py"], ".")]),
    ("Vorlagen (DOCX, PPTX, XLSX) mit Prüf-Checkliste", [([PY, "werkzeug/vorlagen/alle_bauen.py"], ".")]),
]


def aufraeumen():
    """Hilfsdateien von LuaLaTeX entfernen (nur die eigenen, mit festen Namen)."""
    for s in (".aux", ".log"):
        (STIL / (WENDE + s)).unlink(missing_ok=True)


def nur_zeitstempel(datei):
    """True, wenn ein neu gebautes DOCX/PPTX/XLSX inhaltlich dem Stand im Repo gleicht (nur ZIP-Zeiten anders)."""
    alt = subprocess.run(["git", "show", f"HEAD:{datei}"], cwd=REPO, capture_output=True)
    if alt.returncode:
        return False
    a, b = zipfile.ZipFile(BytesIO(alt.stdout)), zipfile.ZipFile(REPO / datei)
    return a.namelist() == b.namelist() and all(a.read(n) == b.read(n) for n in a.namelist())


def office_zuruecksetzen():
    """Office-Dateien ohne inhaltliche Änderung auf den Repo-Stand zurücksetzen, damit git status nur Echtes zeigt."""
    geaendert = subprocess.run(["git", "diff", "--name-only"], cwd=REPO, capture_output=True, text=True).stdout.split()
    gleich = [d for d in geaendert if d.endswith((".docx", ".pptx", ".xlsx")) and nur_zeitstempel(d)]
    if gleich:
        subprocess.run(["git", "checkout", "--", *gleich], cwd=REPO, check=True)


def lauf(name, befehle):
    t = time.time()
    for args, wo in befehle:
        e = subprocess.run(args, cwd=REPO / wo, env=ENV, capture_output=True, text=True)
        if e.returncode:
            aus = (e.stdout + e.stderr).strip().splitlines()
            return False, time.time() - t, aus[-15:]
    return True, time.time() - t, []


def main(auswahl):
    def norm(t):
        return t.lower().replace("-", "").replace(" ", "").replace("ö", "oe").replace("ü", "ue").replace("ä", "ae")
    punkte = [p for p in PUNKTE if not auswahl or any(norm(a) in norm(p[0]) for a in auswahl)]
    if not punkte:
        sys.exit("Kein Punkt passt zu: " + " ".join(auswahl))
    fehler = 0
    print(f"Probelauf Werkzeugkasten ({len(punkte)} Punkte)")
    for name, befehle in punkte:
        ok, dauer, aus = lauf(name, befehle)
        print(f"  {'OK    ' if ok else 'FEHLER'} {name} ({dauer:.0f} s)")
        if not ok:
            fehler += 1
            for z in aus:
                print("         | " + z)
    aufraeumen()
    office_zuruecksetzen()
    st = subprocess.run(["git", "status", "--short", "--", "docs/stilreferenz", "vorlagen"], cwd=REPO,
                        capture_output=True, text=True).stdout.rstrip()
    print("Prüfbericht Probelauf")
    print(f"  Fehler: {fehler}")
    print(f"  Hinweis: {'geänderte Stilreferenzen (bitte ansehen):' if st else 'keine Stilreferenz verändert.'}")
    for z in st.splitlines():
        print("    " + z)
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
