"""Pflicht-Prüfung vor der Abnahme: Einspielprotokoll muss zur aktuellen .mbz passen."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import testmoodle  # noqa: E402


def test_ohne_protokoll_fehler(tmp_path):
    mbz = tmp_path / "kurs.mbz"; mbz.write_bytes(b"x")
    assert testmoodle.pruefen(mbz)[0] is False


def test_passendes_protokoll_ok_und_neubau_fehler(tmp_path):
    mbz = tmp_path / "kurs.mbz"; mbz.write_bytes(b"x")
    (tmp_path / "kurs.einspielprotokoll.json").write_text(json.dumps(
        {"sha256": testmoodle._sha256(mbz), "ok": True, "moodle": "5.1.6", "zeit": "jetzt", "format": "tiles"}))
    assert testmoodle.pruefen(mbz)[0] is True
    mbz.write_bytes(b"neu gebaut")
    ok, text = testmoodle.pruefen(mbz)
    assert ok is False and "neu gebaut" in text
