"""Dateien in Abschnittstexten und Kachelfoto (format_tiles).

Struktur des Kachelfotos nach tests/referenz/format_tiles_kachelfoto.xml
(gemessen an Moodle 5.1.6 mit format_tiles 5.1.0.2).
"""
import copy
import tarfile
import xml.etree.ElementTree as ET

import bauen
import beispiel
import kursdefinition as kd
import pruefen

ZUSAMMENFASSUNG = ('<p>Familie Schütte zeigt Ihnen ihr Haus.</p>'
                   '<p><img src="haus_schuette.png" alt="Haus Schütte"></p>')
UNVERAENDERT = ('<p>Frau Schütte: „Hören Sie selbst.“</p>'
                '<p><img src="@@PLUGINFILE@@/verteiler.png" alt="Verteiler"></p>')


def _bauen(tmp_path, dateien, fmt):
    kurs = copy.deepcopy(beispiel.kursdefinition())
    kurs["kurs"]["format"] = fmt
    erster, zweiter = kurs["abschnitte"][0], kurs["abschnitte"][1]
    erster["bild"] = "bilder/kurs.png"
    erster["zusammenfassung"] = ZUSAMMENFASSUNG
    erster["dateien"] = ["bilder/haus_schuette.png"]
    zweiter["zusammenfassung"] = UNVERAENDERT
    zweiter["dateien"] = ["bilder/verteiler.png"]
    assert kd.pruefe(kurs) == []
    ziel = tmp_path / f"{fmt}.mbz"
    bauen.baue(kurs, dateien, ziel)
    ordner = tmp_path / fmt
    with tarfile.open(ziel, "r:gz") as tar:
        tar.extractall(ordner, filter="data")
    return ziel, ordner, kurs


def _abschnitt_id(ordner, name):
    root = ET.parse(ordner / "moodle_backup.xml").getroot()
    return next(s.findtext("sectionid")
                for s in root.findall("information/contents/sections/section")
                if s.findtext("title") == name)


def _dateien(ordner, **filter_):
    return [f for f in ET.parse(ordner / "files.xml").getroot().findall("file")
            if all(f.findtext(k) == v for k, v in filter_.items())]


def _inforef(ordner, sec_id):
    root = ET.parse(ordner / f"sections/section_{sec_id}/inforef.xml").getroot()
    return {i.text for i in root.findall("fileref/file/id")}


def test_kachelfoto_wie_referenz(tmp_path, dateien):
    _, ordner, kurs = _bauen(tmp_path, dateien, "tiles")
    sec = _abschnitt_id(ordner, kurs["abschnitte"][0]["name"])
    s = ET.parse(ordner / f"sections/section_{sec}/section.xml").getroot()
    plug = s.find("plugin_format_tiles_section")
    assert plug is not None and plug.get("sectionid") == sec
    assert [(c.tag, c.text) for c in plug] == [
        ("optiontype", "1"), ("optionvalue", "kurs.png"), ("tilesversion", "2026012570")]
    opt = s.find("course_format_options")
    assert opt is not None and opt.get("id")
    assert [(c.tag, c.text) for c in opt] == [
        ("format", "tiles"), ("name", "tilephoto"), ("value", "kurs.png")]
    # Reihenfolge wie in der Referenz: nach timemodified, Plugin vor Option
    tags = [c.tag for c in s]
    assert tags[-3:] == ["timemodified", "plugin_format_tiles_section",
                         "course_format_options"]

    foto = _dateien(ordner, component="format_tiles", filearea="tilephoto", itemid=sec)
    eintraege = sorted((f.findtext("filepath"), f.findtext("filename")) for f in foto)
    assert eintraege == [("/", "."), ("/tilephoto/", "."), ("/tilephoto/", "kurs.png")]
    for f in foto:
        assert f.findtext("contextid") == str(bauen.Bau.COURSE_CTX)
    bild = next(f for f in foto if f.findtext("filename") == "kurs.png")
    assert bild.findtext("mimetype") == "image/png"
    assert (ordner / "files" / bild.findtext("contenthash")[:2]
            / bild.findtext("contenthash")).is_file()
    assert {f.get("id") for f in foto} <= _inforef(ordner, sec)


def test_dateien_der_zusammenfassung(tmp_path, dateien):
    _, ordner, kurs = _bauen(tmp_path, dateien, "tiles")
    sec = _abschnitt_id(ordner, kurs["abschnitte"][0]["name"])
    s = ET.parse(ordner / f"sections/section_{sec}/section.xml").getroot()
    assert s.findtext("summary") == ZUSAMMENFASSUNG.replace(
        'src="haus_schuette.png"', 'src="@@PLUGINFILE@@/haus_schuette.png"')
    eigen = _dateien(ordner, component="course", filearea="section", itemid=sec)
    assert sorted(f.findtext("filename") for f in eigen) == [".", "haus_schuette.png"]
    for f in eigen:
        assert f.findtext("contextid") == str(bauen.Bau.COURSE_CTX)
        assert f.findtext("filepath") == "/"
    foto = _dateien(ordner, component="format_tiles", itemid=sec)
    assert _inforef(ordner, sec) == {f.get("id") for f in eigen + foto}


def test_zusammenfassung_bleibt_byte_gleich(tmp_path, dateien):
    _, ordner, kurs = _bauen(tmp_path, dateien, "tiles")
    sec = _abschnitt_id(ordner, kurs["abschnitte"][1]["name"])
    roh = (ordner / f"sections/section_{sec}/section.xml").read_bytes()
    s = ET.fromstring(roh)
    assert s.findtext("summary") == UNVERAENDERT
    assert bauen.el("summary", UNVERAENDERT).encode("utf-8") in roh
    # zweiter Abschnitt ohne bild: kein Kachelfoto, aber die Datei
    assert s.find("plugin_format_tiles_section") is None
    assert [f.findtext("filename") for f in _dateien(
        ordner, component="course", filearea="section", itemid=sec)] == [".", "verteiler.png"]


def test_ohne_kachelformat_kein_kachelfoto(tmp_path, dateien):
    mbz, ordner, kurs = _bauen(tmp_path, dateien, "topics")
    assert not list(ordner.rglob("section.xml")) == []
    for d in ordner.rglob("section.xml"):
        assert b"plugin_format_tiles_section" not in d.read_bytes()
        assert b"tilephoto" not in d.read_bytes()
    assert _dateien(ordner, component="format_tiles") == []
    sec = _abschnitt_id(ordner, kurs["abschnitte"][0]["name"])
    assert [f.findtext("filename") for f in _dateien(
        ordner, component="course", filearea="section", itemid=sec)] == [".", "haus_schuette.png"]
    assert [b for b in pruefen.pruefe(mbz, kurs) if b.stufe == pruefen.FEHLER] == []


def test_kursdefinition_prueft_abschnittsfelder():
    kurs = beispiel.kursdefinition()
    kurs["abschnitte"][0]["dateien"] = "bilder/haus_schuette.png"
    kurs["abschnitte"][1]["bild"] = ["bilder/kurs.png"]
    fehler = kd.pruefe(kurs)
    assert any("dateien" in f for f in fehler)
    assert any("bild" in f for f in fehler)
