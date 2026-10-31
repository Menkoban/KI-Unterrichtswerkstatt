"""Bewertungsbogen: Blätter, Kürzel, Formeln für Abweichung und Note."""
import json
import sys
from pathlib import Path

from openpyxl import load_workbook

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
import bewertungsbogen  # noqa: E402


def test_bogen(tmp_path):
    bogen = json.loads((HIER / "beispiel_bogen.json").read_text(encoding="utf-8"))
    ziel = bewertungsbogen.bauen(bogen, tmp_path / "b.xlsx")
    wb = load_workbook(ziel)
    assert wb.sheetnames == ["Bewertung", "Raster", "Namen", "Einlesen"]
    bw = wb["Bewertung"]
    assert [bw.cell(z, 1).value for z in range(5, 9)] == ["S01", "S02", "S03", "S04"]
    letzte = 3 + 3 * len(bogen["kriterien"])
    assert bw.cell(4, letzte + 3).value == "Gespräch"
    assert ">=2" in bw.cell(5, letzte + 3).value and "IF(" in bw.cell(5, letzte + 2).value
    assert wb["Namen"]["B4"].value is None          # Namen nie vorbefüllt
