"""Fähigkeiten für LS 2 (2026-10-25): Zugriff nach Gruppe, Gruppierungen, Aufgabe mit Entwurf, Gruppierung,
Bewertungsworkflow, Dateien und Anhängen, Rubrik mit Stufen, Note außerhalb des Kursgesamts, Feedback mit
Auswertung, Bilder im Fragetext, Glossar mit Bildquelle und Aliassen, Schrittnummern (Varianten, Medaillen)."""
import copy
import json
import tarfile
import xml.etree.ElementTree as ET

import allgemein
import bauen
import beispiel
import kursdefinition as kd
import pruefen
import sterne
from conftest import akt

RASTER = "Auftrag: Messprotokoll Haus Schütte"
SKIZZE = "Auftrag: Skizze Zählerschrank"
STUFEN = [{"kriterium": "Messwerte richtig", "punkte": 2, "stufen": [
              {"punkte": 2, "bezeichnung": "erfüllt", "beschreibung": "alle Werte richtig"},
              {"punkte": 1, "bezeichnung": "teilweise erfüllt"},
              {"punkte": 0, "bezeichnung": "nicht erfüllt", "beschreibung": "kaum Werte"}]},
          {"kriterium": "Einheiten", "punkte": 1, "stufen": [
              {"punkte": 1, "bezeichnung": "ja"}, {"punkte": 0, "bezeichnung": "nein"}]}]


def _kurs():
    kurs = copy.deepcopy(beispiel.kursdefinition())
    kurs["gruppen"] = ["G1", "G2", "P01", "P02"]
    kurs["gruppierungen"] = {"Gruppen DS 1": ["G1", "G2"], "Paare": ["P01", "P02"]}
    ab = kurs["abschnitte"][1]
    ab["aktivitaeten"][3:3] = [
        {"typ": "page", "name": "Ihre Variante: Gruppe 1", "inhalt": "<p>Variante 1</p>", "einzug": 1,
         "voraussetzung": {"gruppe": "G1", "sichtbar_wenn_gesperrt": False}},
        {"typ": "page", "name": "Ihre Variante: Gruppe 2", "inhalt": "<p>Variante 2</p>", "einzug": 1,
         "voraussetzung": {"gruppe": "G2"}}]
    r = akt(kurs, RASTER)
    r.update(bewertungsraster=copy.deepcopy(STUFEN), raster_vorschau=False, bewertungsworkflow=True,
             im_kursgesamt=False, gruppierung="Paare", abgabe_bestaetigen=True,
             dateien=["bilder/verteiler.png"], anhaenge=["lehrkraft/Anlage_2_Messprotokoll.docx"],
             beschreibung='<p>Messen Sie.</p><p><img src="verteiler.png" alt="Verteiler"></p>')
    fb = akt(kurs, "Selbsteinschätzung vorher")
    fb["ergebnis_zeigen"] = True
    q = akt(kurs, "Eingangstest: Was wissen Sie schon?")["fragen"][0]
    q.update(dateien=["bilder/haus_schuette.png"],
             text=q["text"] + '<p><img src="haus_schuette.png" alt="Haus Schütte"></p>')
    g = akt(kurs, "Glossar Stromhof")
    g["eintraege"].append({"begriff": "Schutzschalter (Beispiel)", "definition": "<p>Schützt Menschen.</p>",
                           "bild": "bilder/verteiler.png", "bild_alt": "Verteiler mit RCD",
                           "bild_quelle": "Bildquelle: eigenes Foto", "aliasse": ["RCD", "FI-Schalter"]})
    return kurs


def _bauen(tmp_path, dateien, kurs):
    ziel = tmp_path / "kurs.mbz"
    bauen.baue(kurs, dateien, ziel)
    ordner = tmp_path / "x"
    with tarfile.open(ziel, "r:gz") as tar:
        tar.extractall(ordner, filter="data")
    return ziel, ordner


def _ordner(ordner, titel):
    root = ET.parse(ordner / "moodle_backup.xml").getroot()
    return ordner / next(a.findtext("directory") for a in root.iter("activity") if a.findtext("title") == titel)


def _gruppen(ordner):
    g = ET.parse(ordner / "groups.xml").getroot()
    gruppen = {x.findtext("name"): x.get("id") for x in g.findall("group")}
    gruppierungen = {x.findtext("name"): (x.get("id"), [gg.findtext("groupid") for gg in x.iter("grouping_group")])
                     for x in g.iter("grouping")}
    return gruppen, gruppierungen


def test_gueltig_und_ohne_fehler(tmp_path, dateien):
    kurs = _kurs()
    assert kd.pruefe(kurs, dateien) == []
    ziel, _ = _bauen(tmp_path, dateien, kurs)
    assert [b for b in pruefen.pruefe(ziel, kurs) if b.stufe == pruefen.FEHLER] == []


def test_zugriff_nach_gruppe(tmp_path, dateien):
    _, ordner = _bauen(tmp_path, dateien, _kurs())
    gruppen, _ = _gruppen(ordner)
    for titel, name in (("Ihre Variante: Gruppe 1", "G1"), ("Ihre Variante: Gruppe 2", "G2")):
        m = ET.parse(_ordner(ordner, titel) / "module.xml").getroot()
        v = json.loads(m.findtext("availability"))
        assert v == {"op": "&", "c": [{"type": "group", "id": int(gruppen[name])}], "showc": [False]}


def test_gruppierungen_und_aufgabe(tmp_path, dateien):
    _, ordner = _bauen(tmp_path, dateien, _kurs())
    gruppen, gruppierungen = _gruppen(ordner)
    gid, mitglieder = gruppierungen["Paare"]
    assert mitglieder == [gruppen["P01"], gruppen["P02"]]
    assert gruppierungen["Gruppen DS 1"][1] == [gruppen["G1"], gruppen["G2"]]
    d = _ordner(ordner, RASTER)
    a = ET.parse(d / "assign.xml").getroot().find("assign")
    assert a.findtext("teamsubmissiongroupingid") == gid and a.findtext("teamsubmission") == "1"
    assert a.findtext("submissiondrafts") == "1" and a.findtext("markingworkflow") == "1"
    assert ET.parse(d / "module.xml").getroot().findtext("groupingid") == gid
    assert "@@PLUGINFILE@@/verteiler.png" in a.findtext("intro")
    assert "<table" not in a.findtext("intro")          # Rubrik statt Tabelle
    files = ET.parse(ordner / "files.xml").getroot()
    bereiche = {(f.findtext("component"), f.findtext("filearea"), f.findtext("filename")) for f in files}
    assert ("mod_assign", "intro", "verteiler.png") in bereiche
    assert ("mod_assign", "introattachment", "Anlage_2_Messprotokoll.docx") in bereiche
    # Vorgaben unverändert
    s = ET.parse(_ordner(ordner, SKIZZE) / "assign.xml").getroot().find("assign")
    assert (s.findtext("submissiondrafts"), s.findtext("markingworkflow"), s.findtext("teamsubmissiongroupingid")) \
        == ("0", "0", "0")


def test_rubrik(tmp_path, dateien):
    _, ordner = _bauen(tmp_path, dateien, _kurs())
    g = ET.parse(_ordner(ordner, RASTER) / "grading.xml").getroot()
    area = g.find("area")
    assert area.findtext("areaname") == "submissions" and area.findtext("activemethod") == "rubric"
    d = area.find("definitions/definition")
    assert d.findtext("method") == "rubric" and d.findtext("status") == "20"
    assert json.loads(d.findtext("options"))["alwaysshowdefinition"] == 0
    krit = d.findall("plugin_gradingform_rubric_definition/criteria/criterion")
    assert [k.findtext("description") for k in krit] == ["Messwerte richtig", "Einheiten"]
    assert [lv.findtext("score") for lv in krit[0].iter("level")] == ["0.00000", "1.00000", "2.00000"]
    assert krit[0].find("levels/level[3]").findtext("definition") == "erfüllt: alle Werte richtig"
    assert ET.parse(_ordner(ordner, RASTER) / "assign.xml").getroot().findtext("assign/grade") == "3"
    # ohne Stufen: Tabelle wie bisher, leerer Bewertungsbereich
    assert ET.parse(_ordner(ordner, SKIZZE) / "grading.xml").getroot().find("area") is None


def test_raster_vorschau_vorgabe_an(tmp_path, dateien):
    kurs = _kurs()
    akt(kurs, RASTER).pop("raster_vorschau")
    _, ordner = _bauen(tmp_path, dateien, kurs)
    d = ET.parse(_ordner(ordner, RASTER) / "grading.xml").getroot().find("area/definitions/definition")
    assert json.loads(d.findtext("options"))["alwaysshowdefinition"] == 1


def test_nicht_im_kursgesamt(tmp_path, dateien):
    kurs = _kurs()
    _, ordner = _bauen(tmp_path, dateien, kurs)
    gi = ET.parse(_ordner(ordner, RASTER) / "grades.xml").getroot().find("grade_items/grade_item")
    assert gi.findtext("weightoverride") == "1" and float(gi.findtext("aggregationcoef2")) == 0
    assert float(gi.findtext("grademax")) == 3
    kurs_item = ET.parse(ordner / "gradebook.xml").getroot().find("grade_items/grade_item")
    assert float(kurs_item.findtext("grademax")) == 10     # ohne das Raster zählt nur der Abschlusstest (10)
    assert sterne.kursgesamt_max(kurs) == float(kurs_item.findtext("grademax"))
    assert all(k != RASTER for k, _, _ in sterne.kursgesamt_teile(kurs))


def test_feedback_auswertung_und_vorgabe(tmp_path, dateien):
    _, ordner = _bauen(tmp_path, dateien, _kurs())
    fb = ET.parse(_ordner(ordner, "Selbsteinschätzung vorher") / "feedback.xml").getroot()
    assert fb.findtext("feedback/publish_stats") == "1"


def test_bild_im_fragetext(tmp_path, dateien):
    _, ordner = _bauen(tmp_path, dateien, _kurs())
    q = ET.parse(ordner / "questions.xml").getroot()
    text = next(x.findtext("questiontext") for x in q.iter("question") if "<img" in x.findtext("questiontext"))
    assert 'src="@@PLUGINFILE@@/haus_schuette.png"' in text
    files = ET.parse(ordner / "files.xml").getroot()
    datei = next(f for f in files if f.findtext("component") == "question" and f.findtext("filename") != ".")
    assert datei.findtext("filearea") == "questiontext" and datei.findtext("filename") == "haus_schuette.png"
    inforef = (_ordner(ordner, "Eingangstest: Was wissen Sie schon?") / "inforef.xml").read_text()
    assert f"<id>{datei.get('id')}</id>" in inforef


def test_glossar_bildquelle_und_aliasse(tmp_path, dateien):
    _, ordner = _bauen(tmp_path, dateien, _kurs())
    g = ET.parse(_ordner(ordner, "Glossar Stromhof") / "glossary.xml").getroot()
    e = next(x for x in g.iter("entry") if x.findtext("concept") == "Schutzschalter (Beispiel)")
    assert [a.findtext("alias_text") for a in e.iter("alias")] == ["RCD", "FI-Schalter"]
    d = e.findtext("definition")
    assert d.index("<img") < d.index("Bildquelle: eigenes Foto")


def test_pruefe_meldet_fehler():
    kurs = _kurs()
    kurs["abschnitte"][1]["aktivitaeten"][3]["voraussetzung"] = {"gruppe": "G9"}
    akt(kurs, SKIZZE).update(gruppierung="Trios", gruppenabgabe=False)
    akt(kurs, "Infoblatt: Leistung im Haushalt").update(ergebnis_zeigen=True, bewertungsworkflow=True)
    r = akt(kurs, RASTER)
    r["bewertungsraster"][0]["stufen"][0]["punkte"] = 3
    del r["bewertungsraster"][1]["stufen"]
    kurs["gruppierungen"]["Leer"] = []
    texte = " ".join(kd.pruefe(kurs))
    for teil in ("Gruppe 'G9' gibt es nicht", "Gruppierung 'Trios' gibt es nicht", "wirkt nur mit gruppenabgabe",
                 "ergebnis_zeigen gibt es nur bei feedback", "bewertungsworkflow gibt es nur bei Aufgaben",
                 "stufen bei allen Kriterien", "nicht leere Liste"):
        assert teil in texte, teil
    del r["bewertungsraster"][0]["stufen"]
    r["bewertung"], r["im_kursgesamt"] = "keine", False
    r.pop("bewertungsraster")
    assert "im_kursgesamt false braucht eine Note" in " ".join(kd.pruefe(kurs))


def test_stufen_hoechste_gleich_punkte():
    kurs = _kurs()
    akt(kurs, RASTER)["bewertungsraster"][0]["stufen"][0]["punkte"] = 3
    assert "höchste Stufe 3 ≠ punkte 2" in " ".join(kd.pruefe(kurs))


# -- Schrittnummern: Varianten je Gruppe, Medaillen, verborgene Schritte -------- #
def _kachel(akts, liste):
    return {"name": "Kachel", "zusammenfassung": "<ol>" + "<li>x</li>" * liste + "</ol>", "aktivitaeten": akts}


def test_varianten_je_gruppe_ohne_nummer():
    akts = [{"typ": "page", "name": "Fall"},
            {"typ": "page", "name": "Variante 1", "voraussetzung": {"gruppe": "G1"}},
            {"typ": "page", "name": "Variante 2", "voraussetzung": [{"gruppe": "G2"}]},
            {"typ": "assign", "name": "Gutachten"}, sterne.hilfekarte("Hilfe", "<p>x</p>")]
    ab = _kachel(akts, 2)
    allgemein.schrittnummern([ab], mit_kachel=True)
    assert [a["name"] for a in akts] == ["Schritt 1.1 · Fall", "Variante 1", "Variante 2", "Schritt 1.2 · Gutachten",
                                         "Hilfe zu 1.2"]
    sterne.idnummern([ab])
    assert akts[4]["idnummer"] == "hilfe-k1-s2"


def test_medaillen_ein_schritt_und_verborgener_schritt():
    medaillen = sterne.medaillen_seiten([1, 50, 81, 92], nach="Abschlusstest")
    akts = [{"typ": "quiz", "name": "Generalprobe"},
            {"typ": "quiz", "name": "Abschlusstest", "sichtbar": False, "schritt": True},
            {"typ": "page", "name": "Notiz", "sichtbar": False}, *medaillen,
            {"typ": "glossary", "name": "Glossar"}]
    allgemein.schrittnummern([_kachel(akts, 4)], mit_kachel=True)
    namen = [a["name"] for a in akts]
    assert namen[:3] == ["Schritt 1.1 · Generalprobe", "Schritt 1.2 · Abschlusstest", "Notiz"]
    assert namen[3:7] == [f"Schritt 1.3 · Ihre Medaille: {m}" for m in sterne.MEDAILLEN]
    assert namen[7] == "Schritt 1.4 · Glossar"
    allgemein.schrittnummern([_kachel(akts, 4)], mit_kachel=True)       # zweimal: unverändert
    assert [a["name"] for a in akts] == namen


def test_schritt_false_nimmt_aus():
    akts = [{"typ": "page", "name": "A"}, {"typ": "page", "name": "Bild", "schritt": False},
            {"typ": "page", "name": "B"}]
    allgemein.schrittnummern([_kachel(akts, 2)])
    assert [a["name"] for a in akts] == ["Schritt 1 · A", "Bild", "Schritt 2 · B"]
    assert "schritt muss true oder false" in " ".join(
        kd.pruefe({**_kurs(), "abschnitte": [dict(_kurs()["abschnitte"][0], aktivitaeten=[
            dict(_kurs()["abschnitte"][0]["aktivitaeten"][0], schritt="ja")])]}))


# -- Sichtprüfung LS 2 (2026-10-26) -------------------------------------------------------------- #
def test_mindestschrift_16px():
    t = bauen.mindestschrift('<p style="font-size:13px">a</p><small>b</small> .x { font-size: 0.9em; } '
                             'font-size:1.6em font-size:20px font-size: small')
    assert "13px" not in t and "0.9em" not in t and "<small" not in t
    assert "font-size:16px" in t and "font-size:1.6em" in t and "font-size:20px" in t


def test_schrift_im_paket_mindestens_16px(tmp_path, dateien):
    import re as _re
    kurs = _kurs()
    akt(kurs, "Infoblatt: Leistung im Haushalt")["inhalt"] += '<p style="font-size:12px">Quelle</p>'
    _, ordner = _bauen(tmp_path, dateien, kurs)
    for p in ordner.rglob("*.xml"):
        for wert, einheit in _re.findall(r"font-size\s*:\s*(\d*\.?\d+)\s*(px|em|rem)", p.read_text()):
            assert float(wert) >= (16 if einheit == "px" else 1), (p, wert, einheit)


def test_kursseite_ohne_beschreibungen(tmp_path, dateien):
    """Lehrkraft 2026-10-26: auf der Kursseite nur der Auftrag; Beschreibungen nur in der Aktivität (Seiten mit
    printintro 1), Prüfer 11 meldet showdescription 1."""
    kurs = _kurs()
    kurs["kurs"]["schilder"] = True
    akt(kurs, "Infoblatt: Leistung im Haushalt")["beschreibung"] = "<p>Lesen Sie zu zweit.</p>"
    ziel, ordner = _bauen(tmp_path, dateien, kurs)
    for m in ordner.glob("activities/*/module.xml"):
        assert ET.parse(m).getroot().findtext("showdescription") == "0", m
    seite = ET.parse(_ordner(ordner, "Infoblatt: Leistung im Haushalt") / "page.xml").getroot().find("page")
    assert 's:10:"printintro";i:1' in seite.findtext("displayoptions")
    assert [b for b in pruefen.pruefe(ziel, kurs) if b.pruefer == 11 and b.stufe == pruefen.FEHLER] == []
    m = _ordner(ordner, "Infoblatt: Leistung im Haushalt") / "module.xml"
    m.write_text(m.read_text().replace("<showdescription>0</showdescription>", "<showdescription>1</showdescription>"))
    assert [b for b in pruefen.pruefe(ordner, kurs) if b.pruefer == 11 and b.stufe == pruefen.FEHLER]


def test_hilfe_name_mit_stern_hinweis():
    import allgemein
    kachel = {"name": "K", "zusammenfassung": "<ol><li>a</li></ol>", "aktivitaeten": [
        {"typ": "quiz", "name": "Test", "fragen": []}, sterne.hilfekarte("Tipp", "<p>x</p>")]}
    kachel["aktivitaeten"].append(sterne.stern_aktivitaet(kachel, "Test", ["Tipp"]))
    allgemein.schrittnummern([kachel], mit_kachel=True)
    assert kachel["aktivitaeten"][1]["name"] == "Hilfe zu 1.1 (kostet den Stern „selbst gelöst“)"
    assert sterne.schild_html(kachel["aktivitaeten"][1], 50, [50, 81, 92]) == ""


def test_rueckschau_ohne_bewertung(tmp_path, dateien):
    kurs = _kurs()
    akt(kurs, "Eingangstest: Was wissen Sie schon?").update(rueckschau_bewertung=False, richtige_antwort_zeigen=False)
    _, ordner = _bauen(tmp_path, dateien, kurs)
    q = ET.parse(_ordner(ordner, "Eingangstest: Was wissen Sie schon?") / "quiz.xml").getroot().find("quiz")
    assert [q.findtext(f) for f in ("reviewcorrectness", "reviewmarks", "reviewspecificfeedback",
                                    "reviewrightanswer")] == ["0", "0", "0", "0"]
    assert q.findtext("reviewattempt") == "69888"


def test_aufgabe_ohne_note_mit_textbewertung(tmp_path, dateien):
    kurs = _kurs()
    ziel, ordner = _bauen(tmp_path, dateien, kurs)
    gi = ET.parse(_ordner(ordner, SKIZZE) / "grades.xml").getroot().find("grade_items/grade_item")
    assert gi.findtext("gradetype") == "3"
    kurs_item = ET.parse(ordner / "gradebook.xml").getroot().find("grade_items/grade_item")
    assert float(kurs_item.findtext("grademax")) == 10          # Textbewertung zählt nicht
    assert not [b for b in pruefen.pruefe(ziel, kurs) if b.stufe == pruefen.FEHLER]
