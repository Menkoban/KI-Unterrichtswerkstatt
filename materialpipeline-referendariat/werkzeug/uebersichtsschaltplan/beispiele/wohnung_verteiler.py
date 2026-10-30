"""Probe Verteiler-Übersichtsschaltplan zur Wohnung (EI-03, Entscheidung A 2026-10-14).

Stromkreise, Aderzahl der ersten Leitung und Ziele aus wohnung_netz.py; Schutz, Querschnitt, Länge und Spannungsfall
aus wohnung_bemessung.py (Rechenprüfer). Bricht ab, wenn die Bemessung einen Fehler meldet.

    python3 werkzeug/uebersichtsschaltplan/beispiele/wohnung_verteiler.py
Ausgabe: docs/stilreferenz/verteilerplan_wohnung_a3.{tex,pdf,png}
"""
import subprocess
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent))
sys.path.insert(0, str(HIER))
from uebersicht import TEX, Plan  # noqa: E402
from verteiler import Abgang, Gruppe, Verteiler  # noqa: E402
from wohnung_bemessung import ANNAHMEN, ENTWURF, HAUPT, bemessen  # noqa: E402
from wohnung_netz import STROMKREIS, n as NETZ  # noqa: E402

ZIEL = HIER.parents[2] / "docs" / "stilreferenz" / "verteilerplan_wohnung_a3"

r, zeilen, duh = bemessen(ENTWURF)
print(r.bericht())
if not r.fehlerfrei:
    raise SystemExit("Bemessung mit Fehlern")
Z = {z["sk"]: z for z in zeilen}


def komma(x, n=1):
    return f"{x:.{n}f}".replace(".", ",")


ZIELE = {"F1": ["Beleuchtung", "Küche, Flur,", "Wohnzimmer", "→ X13"],
         "F2": ["Steckdosen", "Flur, Wohnzimmer", "→ X16"],
         "F3": ["Arbeitsfläche", "Küche", "→ X3, X4"],
         "F4": ["Kühlschrank", "→ X2"],
         "F5": ["Geschirrspüler", "→ X5"],
         "F6": ["Elektroherd", "10,5 kW", "→ E4"]}
LEITER = {"F1": "L1", "F3": "L2", "F5": "L3", "F2": "L3", "F4": "L1", "F6": "L1 L2 L3"}


def abgang(sk):
    z = Z[sk]
    n = NETZ.adern("UV", STROMKREIS[sk])
    return Abgang(sk, f"{z['char']}{z['In']}", LEITER[sk], 3 if sk == "F6" else 1, n,
                  f"NYM-J {n}\\,×\\,{komma(z['A'])}", ZIELE[sk])


RCD = ["RCD Typ A", "\\textit{I}\\textsubscript{n} = 40\\,A", "\\textit{I}\\textsubscript{Δn} = 30\\,mA"]
gruppen = [Gruppe("F10", RCD, [abgang(s) for s in ("F1", "F3", "F5")]),
           Gruppe("F20", RCD, [abgang(s) for s in ("F2", "F4", "F6")])]
v = Verteiler()
plan = v.plan({"adern": 5, "netz": "3/N/PE AC 400/230\\,V 50\\,Hz, TN-S",
               "herkunft": f"vom Zählerplatz (SLS {HAUPT['In']}\\,A)\\\\NYM-J 5\\,×\\,{HAUPT['A']}, "
                           f"{komma(HAUPT['l'], 0)}\\,m"}, gruppen, x0=40, abstand=34)
plan += "\n\\node[kopf,anchor=north west] at (28,286) {Unterverteiler UV (Flur)};"
# gestrichelter Rahmen des Verteilers (wie Fachkunde S. 280: Gehäuse des Stromkreisverteilers)
plan += "\n\\draw[raumgrenze] (30,140) rectangle (300,245);"

# Bemessungstabelle aus dem Rechenprüfer
kopf = (r"\textbf{Stromkreis} & \textbf{Schutz} & \textbf{Leitung} & \textbf{längster Weg} & \textbf{\textit{l} in m} & "
        r"\textbf{\textit{I}\textsubscript{z} in A} & \textbf{Δ\textit{u} in \%} & \textbf{erfüllt}\\ \hline" + "\n")
reihen = []
for sk in ("F1", "F2", "F3", "F4", "F5", "F6"):
    z = Z[sk]
    weg = " → ".join(z["weg"])
    reihen.append(f"{sk} {z['text']} & {z['char']}{z['In']} & NYM-J {komma(z['A'])}\\,mm² & {weg} & "
                  f"{komma(z['l'])} & {komma(z['Iz'])} & {komma(z['gesamt'], 2)} & "
                  f"{'ja' if z['gesamt'] <= 3 and z['Ib'] <= z['In'] <= z['Iz'] else 'nein'}\\\\")
tabelle = ("\\node[anchor=north west,inner sep=0,font=\\fontsize{7}{9}\\selectfont] at (28,100) {"
           "\\begin{tabular}{@{}l l l l r r r l@{}}" + kopf + "\n".join(reihen) + "\\end{tabular}};"
           "\\node[kopf,anchor=south west] at (28,101) {Bemessung (Rechenprüfer)};"
           f"\\node[fuss,anchor=north west,text width=285mm] at (28,58) {{Prüfung je Stromkreis: "
           f"\\textit{{I}}\\textsubscript{{b}} ≤ \\textit{{I}}\\textsubscript{{n}} ≤ \\textit{{I}}\\textsubscript{{z}} (DIN VDE 0100-430; \\textit{{I}}\\textsubscript{{z}} "
           f"Verlegeart C, PVC, 30\\,°C nach DIN VDE 0298-4, ohne Häufung bei 5\\,cm Spurabstand); "
           f"Spannungsfall Zähler → entferntestes Betriebsmittel beim Bemessungsstrom ≤ 3\\,\\% "
           f"(DIN 18015-1), Hauptleitung {komma(duh, 2)}\\,\\% eingerechnet. Annahmen: {ANNAHMEN}}};")
plan += "\n" + tabelle

HINWEISE = (r"Verteiler-Übersichtsschaltplan zu EI-01 (Installationsplan) und EI-02 (Übersichtsschaltplan "
            r"Installation); Stromkreise F1–F6 wie dort.\\[1mm]"
            r"Fehlerstrom-Schutzschalter (RCD) ≤ 30\,mA für alle Endstromkreise (DIN VDE 0100-410). "
            r"Zwei RCD, damit Licht und Steckdosen eines Raumes nicht gemeinsam abschalten.\\[1mm]"
            r"Aderzahl einschließlich Schutzleiter; F6 dreipolig (L1, L2, L3).\\[1mm]"
            r"Werte gerechnet, siehe Tabelle. Leitungslängen aus EI-01 mit Höhenzuschlag.\\[1mm]"
            r"Offen (Annahme, bitte prüfen): Zählerplatz, Hauptleitung und SLS, Herdleistung, "
            r"RCD-Bemessungsstrom 40\,A.")
SCHRIFTFELD = {
    "bauherr": "Familie Hinrichs, Musterstadt (fiktiv)",
    "bauvorhaben": "Sanierung Wohnung 2. OG",
    "planinhalt": "Übersichtsschaltplan Unterverteiler",
    "fachplanung": "Brinkmann Automation (fiktiver Modellbetrieb)",
    "gewerk": "Elektro",
    "massstab": "ohne", "format": "A3", "datum": "14.10.2026", "erstellt": "BA",
    "plannr": "EI-03", "stand": "Probe",
    "fuss": r"Eigene Darstellung nach dem Vorbild von Europa-Lehrmittel: Fachkunde Elektrotechnik, 35. Aufl., S. 280; "
            r"Arbeitsbuch 37566, S. 17. Zeichen nach DIN EN 60617. Erstellt mit KI-Unterstützung.",
}

if __name__ == "__main__":
    sx = 415 - 95
    rand = "\n".join(["\\draw[rahmen] (20,5) rectangle (415,292);", f"\\draw[rahmen] ({sx},5) -- ({sx},292);",
                      f"\\node[kopf,anchor=north west] at ({sx + 4},288) {{Hinweise}};",
                      f"\\node[leg,anchor=north west,text width=86mm,align=left] at ({sx + 4},281) {{{HINWEISE}}};",
                      Plan._schriftfeld(None, sx, SCHRIFTFELD)])
    tex = TEX.replace("\\usepackage{tikz}", "\\usepackage{tikz}\\usepackage{bm}") \
             .replace(" zweck/.style", " ziel/.style={font=\\fontsize{7.5}{9}\\selectfont,inner sep=0.3mm,align=center},\n zweck/.style") \
             .replace("%PLAN%", plan).replace("%RAND%", rand)
    ZIEL.with_suffix(".tex").write_text(tex, encoding="utf-8")
    e = subprocess.run(["lualatex", "-interaction=nonstopmode", "-halt-on-error", ZIEL.with_suffix(".tex").name],
                       cwd=ZIEL.parent, capture_output=True, text=True)
    if e.returncode:
        print(e.stdout[-3000:])
        raise SystemExit("LuaLaTeX-Fehler")
    for s in (".aux", ".log"):
        ZIEL.with_suffix(s).unlink(missing_ok=True)
    subprocess.run(["pdftoppm", "-png", "-r", "200", "-singlefile", ZIEL.with_suffix(".pdf").name, ZIEL.name],
                   cwd=ZIEL.parent, check=True)
    print(ZIEL.with_suffix(".png"))
