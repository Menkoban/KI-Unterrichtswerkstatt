"""Bau des Beispiels: Paket, XML, Vollständigkeit."""
import copy
import tarfile
import xml.etree.ElementTree as ET

import pytest

import bauen
import beispiel
import kursdefinition as kd
import pruefen
from conftest import akt


def test_paket_ist_tar_gz_mit_kopf(paket):
    mbz, _, _ = paket
    with tarfile.open(mbz, "r:gz") as tar:
        namen = tar.getnames()
    assert ".ARCHIVE_INDEX" in namen and "moodle_backup.xml" in namen


def test_jede_xml_ist_wohlgeformt(paket):
    _, ordner, _ = paket
    dateien = list(ordner.rglob("*.xml"))
    assert len(dateien) > 100
    for d in dateien:
        ET.parse(d)


def test_version_5_0(paket):
    _, ordner, _ = paket
    info = ET.parse(ordner / "moodle_backup.xml").getroot().find("information")
    assert info.findtext("backup_version") == "2025041400"
    assert info.findtext("backup_release") == "5.0"


def test_jede_aktivitaet_in_moodle_backup_gelistet(paket):
    _, ordner, kurs = paket
    root = ET.parse(ordner / "moodle_backup.xml").getroot()
    gelistet = {a.findtext("directory"): a.findtext("title")
                for a in root.findall("information/contents/activities/activity")}
    ordner_da = {f"activities/{p.name}" for p in (ordner / "activities").iterdir()}
    assert set(gelistet) == ordner_da
    namen = {a["name"] for _, a in kd.alle_aktivitaeten(kurs)}
    assert set(gelistet.values()) == namen
    einstellungen = {s.findtext("name") for s in root.iter("setting")}
    for d in gelistet:
        assert f"{d.split('/')[1]}_included" in einstellungen


def test_beispiel_ohne_befund(paket):
    mbz, _, kurs = paket
    assert pruefen.pruefe(mbz, kurs) == []


def test_alle_fragetypen_gebaut(paket):
    _, ordner, _ = paket
    typen = {q.findtext("qtype") for q in ET.parse(ordner / "questions.xml").iter("question")}
    assert typen == set(kd.FRAGETYPEN)


def test_einstellungen_des_abschlusstests(paket):
    _, ordner, _ = paket
    root = ET.parse(ordner / "moodle_backup.xml").getroot()
    quiz = ordner / next(a.findtext("directory") for a in root.iter("activity")
                         if a.findtext("title") == "Abschlusstest")
    q = ET.parse(quiz / "quiz.xml").getroot().find("quiz")
    assert q.findtext("browsersecurity") == "securewindow"
    assert q.findtext("attempts_number") == "1"
    assert q.findtext("completionattemptsexhausted") == "1"
    assert "glossary" in (quiz / "filters.xml").read_text()
    m = ET.parse(quiz / "module.xml").getroot()
    assert m.findtext("completionpassgrade") == "1"


def test_gruppenabgabe_und_gruppen(paket):
    _, ordner, _ = paket
    a = next((ordner / "activities").glob("assign_*"))
    assert ET.parse(a / "assign.xml").getroot().findtext("assign/teamsubmission") == "1"
    assert len(ET.parse(ordner / "groups.xml").getroot().findall("group")) == 4


def test_vier_abzeichen_mit_bild(paket):
    _, ordner, _ = paket
    badges = ET.parse(ordner / "badges.xml").getroot().findall("badge")
    assert len(badges) == 4
    bilder = [f for f in ET.parse(ordner / "files.xml").getroot()
              if f.findtext("component") == "badges" and f.findtext("filename") == "f1.png"]
    assert len(bilder) == 4


def test_ki_hinweis_oben_in_der_kursbeschreibung(paket):
    _, ordner, kurs = paket
    summary = ET.parse(ordner / "course/course.xml").getroot().findtext("summary")
    assert summary.startswith(f"<p>{kurs['kurs']['ki_hinweis']}</p>")


def test_ungueltige_kursdefinition_bricht_ab(tmp_path, dateien):
    kurs = copy.deepcopy(beispiel.kursdefinition())
    kurs["kurs"]["ki_hinweis"] = ""
    akt(kurs, "Abschlusstest")["fragen"][0]["antworten"] = []
    fehler = kd.pruefe(kurs)
    assert any("ki_hinweis" in f for f in fehler)
    assert any("Antworten" in f for f in fehler)
    with pytest.raises(kd.KursdefinitionFehler):
        bauen.baue(kurs, dateien, tmp_path / "x.mbz")


def test_workshop_klar_nicht_unterstuetzt(tmp_path, dateien):
    kurs = copy.deepcopy(beispiel.kursdefinition())
    kurs["abschnitte"][1]["aktivitaeten"].append({"typ": "workshop", "name": "Peer-Review"})
    assert any("workshop" in f and "noch nicht" in f for f in kd.pruefe(kurs))
    with pytest.raises(kd.KursdefinitionFehler):
        bauen.baue(kurs, dateien, tmp_path / "x.mbz")
