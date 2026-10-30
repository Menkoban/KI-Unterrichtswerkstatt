"""Voraussetzungen: UND-Listen, „nicht abgeschlossen“, Kursgesamt-Bewertung."""
import copy
import json
import tarfile
import xml.etree.ElementTree as ET

import bauen
import beispiel
import kursdefinition as kd
from conftest import akt

ZIEL = "So geht der Abschlusstest"
INFO = "Infoblatt: Leistung im Haushalt"
SITUATION = "Handlungssituation: Haus Schütte"


def gebaut(tmp_path, dateien, voraussetzung):
    """Beispiel mit neuer Voraussetzung an ZIEL bauen; (Ordner, Kurs)."""
    kurs = copy.deepcopy(beispiel.kursdefinition())
    akt(kurs, ZIEL)["voraussetzung"] = voraussetzung
    assert kd.pruefe(kurs) == []
    mbz = tmp_path / "v.mbz"
    bauen.baue(kurs, dateien, mbz)
    ordner = tmp_path / "entpackt"
    with tarfile.open(mbz, "r:gz") as tar:
        tar.extractall(ordner, filter="data")
    return ordner


def aktivitaeten(ordner):
    """Titel → (Ordner, cmid) laut moodle_backup.xml."""
    root = ET.parse(ordner / "moodle_backup.xml").getroot()
    return {a.findtext("title"): (ordner / a.findtext("directory"),
                                  a.findtext("moduleid"))
            for a in root.iter("activity") if a.findtext("directory")}


def verfuegbarkeit(ordner, name):
    d, _ = aktivitaeten(ordner)[name]
    return json.loads(ET.parse(d / "module.xml").getroot().findtext("availability"))


def test_liste_wird_und_mit_zwei_bedingungen(tmp_path, dateien):
    ordner = gebaut(tmp_path, dateien, [
        {"aktivitaet": INFO, "bedingung": "abgeschlossen"},
        {"abschluss": SITUATION, "zustand": "nicht_abgeschlossen"}])
    v = verfuegbarkeit(ordner, ZIEL)
    assert v["op"] == "&"
    assert len(v["c"]) == 2 and len(v["showc"]) == 2
    akts = aktivitaeten(ordner)
    assert v["c"][0] == {"type": "completion", "cm": int(akts[INFO][1]), "e": 1}


def test_nicht_abgeschlossen_ist_e_null(tmp_path, dateien):
    ordner = gebaut(tmp_path, dateien,
                    {"abschluss": SITUATION, "zustand": "nicht_abgeschlossen"})
    v = verfuegbarkeit(ordner, ZIEL)
    cm = int(aktivitaeten(ordner)[SITUATION][1])
    assert v["c"] == [{"type": "completion", "cm": cm, "e": 0}]


def test_kursgesamt_zeigt_auf_kurs_gradeitem(tmp_path, dateien):
    ordner = gebaut(tmp_path, dateien,
                    {"bewertung": "kursgesamt", "min": 81, "max": 92})
    v = verfuegbarkeit(ordner, ZIEL)
    gb = ET.parse(ordner / "gradebook.xml").getroot()
    kurs_ids = [gi.get("id") for gi in gb.iter("grade_item")
                if gi.findtext("itemtype") == "course"]
    assert len(kurs_ids) == 1
    assert v["c"] == [{"type": "grade", "id": int(kurs_ids[0]),
                       "min": 81, "max": 92}]
    assert v["showc"] == [False]


def kurs_mit(voraussetzung):
    kurs = copy.deepcopy(beispiel.kursdefinition())
    akt(kurs, ZIEL)["voraussetzung"] = voraussetzung
    return kd.pruefe(kurs)


def test_unbekannter_name_in_liste_ist_fehler():
    f = kurs_mit([{"aktivitaet": INFO},
                  {"abschluss": "Gibt es nicht", "zustand": "nicht_abgeschlossen"}])
    assert any("Gibt es nicht" in s for s in f)


def test_unbekannter_zustand_und_kursgesamt_bereich_sind_fehler():
    assert any("zustand" in s or "bedingung" in s
               for s in kurs_mit({"abschluss": INFO, "zustand": "halb"}))
    assert any("Bereich" in s
               for s in kurs_mit({"bewertung": "kursgesamt", "min": 92, "max": 81}))
    assert any("bewertung" in s for s in kurs_mit({"bewertung": "irgendwas", "min": 1}))


def test_nicht_bestanden_ist_e_drei(tmp_path, dateien):
    kurs = copy.deepcopy(beispiel.kursdefinition())
    test = next(a for _, a in kd.alle_aktivitaeten(kurs) if a["typ"] == "quiz")
    test.update(bestehensgrenze_prozent=50, versuche=1, abschluss="bestanden")
    akt(kurs, ZIEL)["voraussetzung"] = {"abschluss": kd.kennung_von(test), "zustand": "nicht_bestanden"}
    assert kd.pruefe(kurs) == []
    mbz = tmp_path / "v.mbz"
    bauen.baue(kurs, dateien, mbz)
    ordner = tmp_path / "entpackt"
    with tarfile.open(mbz, "r:gz") as tar:
        tar.extractall(ordner, filter="data")
    cm = int(aktivitaeten(ordner)[test["name"]][1])
    assert verfuegbarkeit(ordner, ZIEL)["c"] == [{"type": "completion", "cm": cm, "e": 3}]
    # ohne Bestehensgrenze gibt es kein „nicht bestanden“
    test.pop("abschluss"), test.pop("bestehensgrenze_prozent")
    assert any("nicht bestanden" in s for s in kd.pruefe(kurs))


def test_oder_gruppe_wird_verschachtelt_und_geprueft(tmp_path, dateien):
    """`{"oder": [...]}` wird eine ODER-Gruppe in der UND-Bedingung (Moodle `{"op":"|","c":[…]}`, ohne eigenes
    showc); leere Gruppe, Nicht-Liste und unbekanntes Ziel darin sind Fehler."""
    ordner = gebaut(tmp_path, dateien, [
        {"oder": [{"abschluss": INFO, "zustand": "abgeschlossen"},
                  {"abschluss": SITUATION, "zustand": "abgeschlossen"}]},
        {"abschluss": SITUATION, "zustand": "nicht_abgeschlossen"}])
    akts = aktivitaeten(ordner)
    v = verfuegbarkeit(ordner, ZIEL)
    assert v["op"] == "&" and v["showc"] == [True, True]
    assert v["c"][0] == {"op": "|", "c": [{"type": "completion", "cm": int(akts[INFO][1]), "e": 1},
                                          {"type": "completion", "cm": int(akts[SITUATION][1]), "e": 1}]}
    assert any("oder" in s for s in kurs_mit({"oder": []}))
    assert any("oder" in s for s in kurs_mit({"oder": {"abschluss": INFO}}))
    assert any("Gibt es nicht" in s for s in kurs_mit({"oder": [{"abschluss": INFO},
                                                                {"abschluss": "Gibt es nicht"}]}))
