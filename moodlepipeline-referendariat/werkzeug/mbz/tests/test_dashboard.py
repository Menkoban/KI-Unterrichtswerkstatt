"""Klassen-Dashboard und Selbsteinschätzung (dashboard.py): Aufbau, Kennungen, verborgen, Skript mit Konfiguration."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import dashboard  # noqa: E402

MS = {"id": "m1", "kurz": "Meilenstein 1", "titel": "Meilenstein 1 · Probe",
      "kriterien": [{"name": "A", "stufen": ["a1", "a2", "a3", "a4"]}, {"name": "B", "stufen": ["b1", "b2", "b3", "b4"]}]}


def test_selbsteinschaetzung():
    f = dashboard.selbsteinschaetzung(MS)
    auswahl = [e for e in f["elemente"] if e["typ"] == "auswahl"]
    assert f["name"] == "Selbsteinschätzung Meilenstein 1" and f["anonym"] is False
    assert [e["kennung"] for e in auswahl] == ["K1", "K2"] and auswahl[0]["optionen"][0] == "1 a1"


def test_dashboard_aktivitaet():
    d = dashboard.dashboard_aktivitaet([MS], gespraech_ab=2)
    assert d["typ"] == "data" and d["sichtbar"] is False and [f["name"] for f in d["felder"]] == ["lernende", "meilenstein", "stufen"]
    konfig = json.loads(re.search(r"/\*KONFIG\*/(.*?)/\*/KONFIG\*/", d["vorlagen"]["jstemplate"], re.S).group(1))
    assert konfig["meilensteine"][0]["name"] == "Selbsteinschätzung Meilenstein 1" and konfig["gespraech_ab"] == 2
    assert "fonts.googleapis" not in d["vorlagen"]["jstemplate"] + d["vorlagen"]["csstemplate"]
    assert 'data-feld="stufen"' in d["vorlagen"]["addtemplate"] and "kd-eintrag" in d["vorlagen"]["listtemplate"]


def test_lernstand_behaelt_alle_ansichten():
    """Das Original (Lernstand-Dashboard) bleibt erhalten; dazu kommt genau eine Ansicht „Bewertung und Stufenweg“."""
    html = dashboard.lernstand_datei({"kurs": "K", "kurzname": "K", "medaillen": [], "stern_tests": [], "hilfekarten": [],
                                      "testpaare": [], "sterne_max": 3, "fehlvorstellungen": [], "tests": [], "feedbacks": []},
                                     [MS])
    for tab in ("tab-live", "tab-abschluss", "tab-paare", "tab-fv", "tab-vn", "tab-kd"):
        assert html.count(f'id="{tab}"') == 1
    assert 'id="kd-ziel"' in html and dashboard.DATEN_NAME in html and "fonts.googleapis" not in html
