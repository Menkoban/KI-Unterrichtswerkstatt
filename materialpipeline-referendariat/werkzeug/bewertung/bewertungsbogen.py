"""Bewertungsbogen je Meilenstein als Excel (Lehrkraft 2026-10-31, Fahrplan 2.2): Selbsteinschätzung der Lernenden und
Einschätzung der Lehrkraft mit demselben Raster nebeneinander, Abweichungen ab der Gesprächsgrenze rot, Note nach IHK.

Blätter: „Raster“ (Kriterien und Stufen), „Bewertung“ (je Kürzel eine Zeile), „Einlesen“ (Moodle-Export der
Selbsteinschätzung hineinkopieren), „Namen“ (Kürzel und Name; **nur in der lokalen Kopie der Lehrkraft ausfüllen**,
nie im Repository). Die Kürzel kommen aus der Klassen-Akte (dieselbe Liste wie der Sitzplan).

    python3 werkzeug/bewertung/bewertungsbogen.py <bogen.json> <ziel.xlsx>

bogen.json: {"titel", "klasse", "kuerzel": [...] oder "klassenakte": "<pfad>", "kriterien": [{"name", "stufen": [vier
Sätze, Stufe 1 bis 4], "gewicht": 1}], "gespraech_ab": 2, "punkte": "stufe_minus_1" | "stufe"}.
Raster und Kriterien sind ab Kachel 1 für die Lernenden sichtbar: sie dürfen die Ursache nicht verraten (Regel „Keine
Problemführung“), also Kriterien zum Vorgehen und Ergebnis, nicht zum Fachinhalt der Lösung.
"""
import json
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as sp
from openpyxl.worksheet.datavalidation import DataValidation

# IHK-Notenschlüssel (Prozent ab): 92 = 1, 81 = 2, 67 = 3, 50 = 4, 30 = 5, darunter 6
IHK = [(92, 1), (81, 2), (67, 3), (50, 4), (30, 5), (0, 6)]
ROT, KOPF, HELL = PatternFill("solid", fgColor="F8D0CC"), PatternFill("solid", fgColor="1D4ED8"), \
    PatternFill("solid", fgColor="EEF3FC")
RAND = Border(*(Side(style="thin", color="B8C2D0"),) * 4)


def kuerzel(bogen, basis):
    if bogen.get("kuerzel"):
        return list(bogen["kuerzel"])
    akte = json.loads((basis / bogen["klassenakte"]).read_text(encoding="utf-8"))
    return [l["k"] for l in akte["lernende"]]


def kopf(zelle, text):
    zelle.value = text
    zelle.font = Font(bold=True, color="FFFFFF")
    zelle.fill = KOPF
    zelle.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
    zelle.border = RAND


def bauen(bogen, ziel, basis=Path(".")):
    kr = bogen["kriterien"]
    n = len(kr)
    ab = int(bogen.get("gespraech_ab", 2))
    minus = bogen.get("punkte", "stufe_minus_1") == "stufe_minus_1"
    namen = kuerzel(bogen, basis)
    wb = Workbook()

    # Raster
    r = wb.active
    r.title = "Raster"
    r["A1"] = f"Bewertungsraster · {bogen['titel']}"
    r["A1"].font = Font(bold=True, size=14)
    for j, t in enumerate(["Kriterium", "Gewicht", "Stufe 1", "Stufe 2", "Stufe 3", "Stufe 4"], 1):
        kopf(r.cell(3, j), t)
    for i, k in enumerate(kr, 4):
        r.cell(i, 1, k["name"]).font = Font(bold=True)
        r.cell(i, 2, k.get("gewicht", 1))
        for s in range(4):
            r.cell(i, 3 + s, k["stufen"][s])
        for j in range(1, 7):
            r.cell(i, j).alignment = Alignment(wrap_text=True, vertical="top")
            r.cell(i, j).border = RAND
    for j, b in enumerate([26, 9, 30, 30, 30, 30], 1):
        r.column_dimensions[sp(j)].width = b

    # Namen (nur lokal)
    nm = wb.create_sheet("Namen")
    nm["A1"] = "Namen nur in Ihrer eigenen Kopie eintragen (Tablet, Dienstspeicher), nie im Repository."
    nm["A1"].font = Font(bold=True, color="B91C1C")
    kopf(nm["A3"], "Kürzel")
    kopf(nm["B3"], "Name wie in Moodle")
    for i, k in enumerate(namen, 4):
        nm.cell(i, 1, k)
    nm.column_dimensions["A"].width, nm.column_dimensions["B"].width = 10, 34

    # Einlesen
    ei = wb.create_sheet("Einlesen")
    ei["A1"] = ("Moodle-Export der Selbsteinschätzung ab Zeile 4 einfügen: Spalte A der Name, danach je Kriterium die "
                "gewählte Stufe (1 bis 4, auch „3 …“ als Text) in der Reihenfolge des Rasters.")
    ei["A1"].alignment = Alignment(wrap_text=True)
    ei.merge_cells(start_row=1, start_column=1, end_row=1, end_column=n + 1)
    ei.row_dimensions[1].height = 32
    kopf(ei["A3"], "Name")
    for j, k in enumerate(kr, 2):
        kopf(ei.cell(3, j), k["name"])
    ei.column_dimensions["A"].width = 30

    # Bewertung
    bw = wb.create_sheet("Bewertung", 0)
    bw["A1"] = f"Bewertungsbogen · {bogen['titel']} · {bogen.get('klasse', '')}"
    bw["A1"].font = Font(bold=True, size=14)
    bw["A2"] = (f"Grau: Selbsteinschätzung (aus „Einlesen“). Weiß: Ihre Stufe 1 bis 4. Rot: Abweichung ab {ab} Stufen "
                f"→ kurzes Gespräch. Note nach IHK.")
    kopf(bw.cell(4, 1), "Kürzel")
    kopf(bw.cell(4, 2), "Name")
    for i, k in enumerate(kr):
        c = 3 + 3 * i
        bw.merge_cells(start_row=3, start_column=c, end_row=3, end_column=c + 2)
        kopf(bw.cell(3, c), k["name"])
        for d, t in enumerate(["selbst", "Lehrkraft", "Abw."]):
            kopf(bw.cell(4, c + d), t)
    rest = 3 + 3 * n
    for d, t in enumerate(["Punkte", "Prozent", "Note", "Gespräch"]):
        kopf(bw.cell(4, rest + d), t)
    gewichte = [k.get("gewicht", 1) for k in kr]
    maxp = sum(g * (3 if minus else 4) for g in gewichte)
    dv = DataValidation(type="whole", operator="between", formula1="1", formula2="4", allow_blank=True,
                        error="Bitte eine Stufe von 1 bis 4 eintragen.")
    bw.add_data_validation(dv)
    for z, k in enumerate(namen, 5):
        bw.cell(z, 1, k).font = Font(bold=True)
        bw.cell(z, 2, f'=IFERROR(INDEX(Namen!$B:$B,MATCH(A{z},Namen!$A:$A,0))&"","")')
        such = f'IF(B{z}="",A{z},B{z})'
        teile, abws = [], []
        for i, g in enumerate(gewichte):
            c = 3 + 3 * i
            s, l, a = sp(c), sp(c + 1), sp(c + 2)
            quelle = f"Einlesen!${sp(2 + i)}:${sp(2 + i)}"
            bw.cell(z, c, f'=IFERROR(VALUE(LEFT(INDEX({quelle},MATCH({such},Einlesen!$A:$A,0)),1)),"")').fill = HELL
            dv.add(bw.cell(z, c + 1))
            bw.cell(z, c + 2, f'=IF(OR({s}{z}="",{l}{z}=""),"",ABS({s}{z}-{l}{z}))')
            teile.append(f'IF({l}{z}="",0,{g}*({l}{z}{"-1" if minus else ""}))')
            abws.append(f'N({a}{z})>={ab}')
            bw.conditional_formatting.add(f"{a}{z}", FormulaRule(formula=[f'AND({a}{z}<>"",{a}{z}>={ab})'], fill=ROT))
        p, q, nt, gs = sp(rest), sp(rest + 1), sp(rest + 2), sp(rest + 3)
        alle = "AND(" + ",".join(f'{sp(4 + 3 * i)}{z}<>""' for i in range(n)) + ")"
        bw.cell(z, rest, f'=IF({alle},{"+".join(teile)},"")')
        bw.cell(z, rest + 1, f'=IF({p}{z}="","",ROUND({p}{z}/{maxp}*100,0))')
        stufen = "".join(f"IF({q}{z}>={g},{note}," for g, note in IHK[:-1]) + str(IHK[-1][1]) + ")" * (len(IHK) - 1)
        bw.cell(z, rest + 2, f'=IF({q}{z}="","",{stufen})')
        bw.cell(z, rest + 3, f'=IF(OR({",".join(abws)}),"ja","")')
        bw.conditional_formatting.add(f"{gs}{z}", FormulaRule(formula=[f'{gs}{z}="ja"'], fill=ROT))
        for j in range(1, rest + 4):
            bw.cell(z, j).border = RAND
            bw.cell(z, j).alignment = Alignment(horizontal="center")
    bw.column_dimensions["A"].width, bw.column_dimensions["B"].width = 9, 22
    for j in range(3, rest + 4):
        bw.column_dimensions[sp(j)].width = 9
    bw.freeze_panes = "C5"
    bw.row_dimensions[3].height = 42
    for blatt in (bw, r):        # Druck: quer, eine Seite breit
        blatt.page_setup.orientation = "landscape"
        blatt.page_setup.fitToWidth, blatt.page_setup.fitToHeight = 1, 0
        blatt.sheet_properties.pageSetUpPr.fitToPage = True
    Path(ziel).parent.mkdir(parents=True, exist_ok=True)
    wb.save(ziel)
    return ziel


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    quelle = Path(sys.argv[1]).resolve()
    print(bauen(json.loads(quelle.read_text(encoding="utf-8")), sys.argv[2], quelle.parent))
