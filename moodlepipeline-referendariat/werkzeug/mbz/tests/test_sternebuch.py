"""Sternebuch und Lernfeldkurs: Schema (Auswahlfelder, eigene Vorlagen, Kurstyp), Bau, Prüfer 10, Skript in node."""
import copy
import shutil
import subprocess
import tarfile
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

import bauen
import beispiel
import kursdefinition as kd
import lernfeldkurs
import pruefen
import sternebuch

KURSE = [{"name": "LS 1 Erster Kurs", "kurzname": "K-LF01-LS01"}, {"name": "LS 2 Zweiter Kurs",
                                                                     "kurzname": "K-LF01-LS02"}]
NODE = shutil.which("node")


def lernfeld(**weitere):
    """Neutraler Lernfeldkurs mit Sternebuch und Preisliste (keine persönlichen Werte)."""
    db = sternebuch.datenbank(KURSE)
    seite = sternebuch.preisliste_seite([("Joker", 5, ""), ("Tee", 10, "solange Vorrat da ist")],
                                        [("Frühstück", 60, 30, "")], KURSE)
    kurs = {"vollname": "Klasse X · LF 1", "kurzname": "X-LF01", "beschreibung": "<p>Lernfeldkurs.</p>",
            "ki_hinweis": "Erstellt mit Hilfe von künstlicher Intelligenz.", "format": "tiles"}
    themen = [{"name": "Erster Kurs", "kurzname": "K-LF01-LS01", "text": "<p>Lernsituation 1.</p>"},
              {"name": "Zweiter Kurs", "kurzname": "K-LF01-LS02", "text": "<p>Lernsituation 2.</p>"},
              {"name": "Dritter Kurs", "kurzname": None, "text": "<p>Lernsituation 3.</p>"}]
    lehr = {"name": "Material für Lehrkräfte", "zusammenfassung": "<p>Verborgen.</p>",
            "aktivitaeten": [{"typ": "page", "name": "Handreichung", "inhalt": "<p>Hinweise.</p>", "sichtbar": False}]}
    k = lernfeldkurs.kursdefinition(kurs, themen, allgemein=[db, seite], lehrkraft=lehr)
    k.update(weitere)
    return k


def bauen_und_entpacken(kurs, tmp_path):
    ziel = tmp_path / "k.mbz"
    bauen.baue(kurs, tmp_path, ziel)
    ordner = tmp_path / "x"
    with tarfile.open(ziel, "r:gz") as tar:
        tar.extractall(ordner, filter="data")
    return ziel, ordner


def datenbank_xml(ordner):
    d = next((ordner / "activities").glob("data_*"))
    return ET.parse(d / "data.xml").getroot().find("data")


def akt_von(kurs, name):
    return next(a for _, a in kd.alle_aktivitaeten(kurs) if a["name"] == name)


# -- Schema -------------------------------------------------------------------------------------------------- #
def test_lernfeldkurs_ist_gueltig():
    assert kd.pruefe(lernfeld()) == []
    assert kd.ist_lernfeldkurs(lernfeld())


def test_auswahlfelder_brauchen_optionen():
    k = lernfeld()
    felder = akt_von(k, "Sternebuch")["felder"]
    felder[0]["optionen"] = []
    felder[1]["optionen"] = ["a"]
    felder[4]["optionen"] = ["ja", "ja"]
    text = " ".join(kd.pruefe(k))
    assert "optionen muss eine Liste" in text and "optionen gibt es nur bei" in text and "Option doppelt" in text


def test_vorlagen_pruefen():
    k = lernfeld()
    db = akt_von(k, "Sternebuch")
    db["vorlagen"]["listtemplate"] += "[[Unbekannt]] [[Sterne#id]]"
    db["vorlagen"]["meinevorlage"] = "x"
    db["bearbeiten_nach_freigabe"] = "nein"
    akt_von(k, "Preisliste")["vorlagen"] = {}
    text = " ".join(kd.pruefe(k))
    assert "[[Unbekannt]]" in text and "[[Sterne" not in text
    assert "'meinevorlage' gibt es nicht" in text
    assert "bearbeiten_nach_freigabe gibt es nur bei data" in text
    assert "vorlagen gibt es nur bei Datenbanken" in text


def test_lernfeldkurs_ohne_noten_medaillen_und_sternzaehler():
    k = lernfeld(abzeichen=[{"name": "Gold", "bild": "x.png", "aktivitaet": "Preisliste"}])
    k["kurs"]["sternzaehler"] = True
    k["abschnitte"][0]["aktivitaeten"].append({"typ": "quiz", "name": "Test", "fragen": [
        {"typ": "truefalse", "name": "F", "text": "<p>?</p>", "richtig": True}]})
    text = " ".join(kd.pruefe(k))
    assert "keine abzeichen" in text and "kein sternzaehler" in text and "keine Noten" in text


def test_allgemein_ohne_note_und_kurstyp():
    k = lernfeld()
    k["allgemein_aktivitaeten"].append({"typ": "assign", "name": "Abgabe"})
    k["kurs"]["typ"] = "irgendwas"
    text = " ".join(kd.pruefe(k))
    assert "bekommen keine Note" in text and "kurs.typ" in text


def test_namen_in_allgemein_eindeutig():
    k = lernfeld()
    k["abschnitte"][0]["aktivitaeten"].append({"typ": "page", "name": "Preisliste", "inhalt": "<p>x</p>"})
    assert any("name doppelt" in f for f in kd.pruefe(k))


# -- Bau ----------------------------------------------------------------------------------------------------- #
def test_bau_sternebuch_ganz_oben(tmp_path):
    _, ordner = bauen_und_entpacken(lernfeld(), tmp_path)
    secs = [ET.parse(s).getroot() for s in (ordner / "sections").glob("*/section.xml")]
    null = next(s for s in secs if s.findtext("number") == "0")
    backup = ET.parse(ordner / "moodle_backup.xml").getroot()
    titel = {a.findtext("moduleid"): a.findtext("title") for a in backup.iter("activity")}
    assert [titel[c] for c in null.findtext("sequence").split(",")] == ["Sternebuch", "Preisliste"]
    eins = next(s for s in secs if s.findtext("number") == "1")
    assert 'href="view.php?name=K-LF01-LS01"' in eins.findtext("summary")
    drei = next(s for s in secs if s.findtext("number") == "3")
    assert lernfeldkurs.FOLGT in drei.findtext("summary") and "view.php" not in drei.findtext("summary")
    for d in (ordner / "activities").iterdir():          # keine Noten im Lernfeldkurs
        assert not list(ET.parse(d / "grades.xml").getroot().iter("grade_item"))
    assert ET.parse(ordner / "badges.xml").getroot().find("badge") is None


def test_bau_datenbank_mit_vorlagen_und_freigabe(tmp_path):
    _, ordner = bauen_und_entpacken(lernfeld(), tmp_path)
    d = datenbank_xml(ordner)
    assert d.findtext("approval") == "1" and d.findtext("manageapproved") == "0"
    felder = {f.findtext("name"): f for f in d.iter("field")}
    assert felder["Art"].findtext("type") == "menu"
    assert felder["Art"].findtext("param1").split("\n") == list(sternebuch.ARTEN.values())
    assert felder["Ausgegeben"].findtext("type") == "checkbox" and felder["Ausgegeben"].findtext("param1") == "ja"
    assert felder["Art"].findtext("param2") == "$@NULL@$"
    assert "sb-eintrag" in d.findtext("listtemplate") and "sb-formular" in d.findtext("addtemplate")
    konfig = sternebuch.konfig_aus(d.findtext("jstemplate"))
    assert [k["kurzname"] for k in konfig["themenkurse"]] == ["K-LF01-LS01", "K-LF01-LS02"]
    assert ".sb-balken" in d.findtext("csstemplate")
    assert d.findtext("completionentries") == "0"


def test_bisherige_datenbank_unveraendert(paket):
    """Rückwärtsverträglich: ohne vorlagen und bearbeiten_nach_freigabe wie bisher."""
    _, ordner, _ = paket
    d = datenbank_xml(ordner)
    assert d.findtext("manageapproved") == "1" and d.findtext("jstemplate") == ""
    assert d.findtext("csstemplate") == "" and "<table" in d.findtext("listtemplateheader")


def test_lernfeldkurs_ohne_befunde(tmp_path):
    kurs = lernfeld()
    ziel, _ = bauen_und_entpacken(kurs, tmp_path)
    befunde = pruefen.pruefe(ziel, kurs)
    fehler = [str(b) for b in befunde if b.stufe == pruefen.FEHLER]
    assert fehler == []
    assert not [b for b in befunde if b.pruefer in (4, 8)]          # Kacheln sind Wegweiser


def test_themenkurs_meldet_weiter_kacheln_ohne_abgabe(variante):
    """Prüfer 8 bleibt für Themenkurse wie bisher."""
    def aendern(k):
        k["abschnitte"].insert(1, {"name": "Leere Kachel", "zusammenfassung": "<p>x</p>", "aktivitaeten": [
            {"typ": "page", "name": "Nur lesen", "inhalt": "<p>x</p>"}]})
    assert any(b.pruefer == 8 and "Leere Kachel" in b.text for b in variante(aendern))


# -- Prüfer 10 ----------------------------------------------------------------------------------------------- #
def befunde_p10(tmp_path, aendern):
    kurs = lernfeld()
    aendern(kurs)
    ziel, _ = bauen_und_entpacken(kurs, tmp_path)
    return [b for b in pruefen.pruefe(ziel, kurs) if b.pruefer == 10]


def test_p10_ohne_freigabe(tmp_path):
    def aendern(k):
        akt_von(k, "Sternebuch").update(freigabe=False, bearbeiten_nach_freigabe=True)
    texte = " ".join(b.text for b in befunde_p10(tmp_path, aendern))
    assert "ohne Freigabe" in texte and "freigegebene Buchungen ändern" in texte


def test_p10_kein_schluessel_im_skript(tmp_path):
    def aendern(k):
        db = akt_von(k, "Sternebuch")
        db["vorlagen"]["jstemplate"] += "\nvar wstoken = 'abc'; var s = 'sesskey=Ab12Cd34Ef';"
    texte = [b.text for b in befunde_p10(tmp_path, aendern) if b.stufe == pruefen.FEHLER]
    assert any("wstoken" in t for t in texte) and any("sesskey=Ab12Cd34Ef" in t for t in texte)


def test_p10_preisliste_und_felder(tmp_path):
    def aendern(k):
        k["allgemein_aktivitaeten"] = [a for a in k["allgemein_aktivitaeten"] if a["name"] != "Preisliste"]
        akt_von(k, "Sternebuch")["felder"][0]["optionen"] = ["für mich eintauschen", "verschenken"]
    texte = " ".join(b.text for b in befunde_p10(tmp_path, aendern))
    assert "Preisliste) fehlt" in texte and "passt nicht zum Skript" in texte


def test_p10_preisliste_ohne_zahlen(tmp_path):
    def aendern(k):
        seite = akt_von(k, "Preisliste")
        seite["inhalt"] = seite["inhalt"].replace("<td>10</td>", "<td>zehn</td>")
    texte = " ".join(b.text for b in befunde_p10(tmp_path, aendern))
    assert "keine Zahl für Sterne" in texte


def test_p10_kachel_ohne_zaehlenden_kurs(tmp_path):
    def aendern(k):
        k["abschnitte"][2] = lernfeldkurs.kachel({"name": "Dritter Kurs", "kurzname": "K-LF01-LS03", "text": ""})
    hinweise = [b for b in befunde_p10(tmp_path, aendern) if b.stufe == pruefen.HINWEIS]
    assert any("K-LF01-LS03" in b.text and "nicht zählen" in b.text for b in hinweise)


@pytest.mark.skipif(not NODE, reason="node fehlt")
def test_p10_rechnet_halbierung_in_node(tmp_path):
    def aendern(k):
        db = akt_von(k, "Sternebuch")
        db["vorlagen"]["jstemplate"] = db["vorlagen"]["jstemplate"].replace(
            "return Math.floor(Math.max(0, sterne) / 2);", "return sterne;")
    texte = [b.text for b in befunde_p10(tmp_path, aendern) if b.stufe == pruefen.FEHLER]
    assert any("L.halbieren(10)" in t for t in texte)


# -- Skript und Seite ---------------------------------------------------------------------------------------- #
def test_skript_konfiguration_hin_und_zurueck():
    js = sternebuch.skript({"preisliste": "Preise", "themenkurse": [], "arten": {"a": "b"}})
    assert sternebuch.konfig_aus(js)["preisliste"] == "Preise"
    assert sternebuch.konfig_aus("ohne") is None
    assert "/*KONFIG*/" in sternebuch.JS_DATEI.read_text(encoding="utf-8")


def test_skript_ohne_helferstern():
    db = sternebuch.datenbank(KURSE, helferstern=False)
    assert "Helfer-Stern" not in db["felder"][0]["optionen"]
    assert "helfer" not in sternebuch.konfig_aus(db["vorlagen"]["jstemplate"])["arten"]


def test_verfall_noch_nicht_gebaut():
    with pytest.raises(NotImplementedError):
        sternebuch.datenbank(KURSE, verfall="schuljahresende")
    with pytest.raises(ValueError):
        sternebuch.datenbank([{"name": "ohne Kurzname"}])


def test_preisliste_lesen_wie_gebaut():
    seite = sternebuch.preisliste_seite([("Joker", 5, ""), ("Tee", 10, "")], [("Grillen", 120, 60, "")], KURSE,
                                        lernende=18)
    p = sternebuch.preise_lesen(seite["inhalt"])
    assert [(z["name"], z["sterne"]) for z in p["fuer_mich"]] == [("Joker", 5), ("Tee", 10)]
    assert [(z["name"], z["ab"], z["anteil"]) for z in p["klasse"]] == [("Grillen", 120, 60)]
    assert [z["kurzname"] for z in p["kurse"]] == ["K-LF01-LS01", "K-LF01-LS02"]
    assert p["lernende"] == 18 and p["fehler"] == []
    with pytest.raises(ValueError):
        sternebuch.preisliste_seite([], [("Grillen", 50, 60, "")], KURSE)      # Anteil über der Mindestzahl


def test_halbieren_python():
    assert [sternebuch.halbieren(n) for n in (10, 7, 0, -2)] == [5, 3, 0, 0]


def test_keine_gedankenstriche_in_texten():
    db = sternebuch.datenbank(KURSE)
    seite = sternebuch.preisliste_seite([("Joker", 5, "")], [("Frühstück", 60, 30, "")], KURSE)
    texte = [db["beschreibung"], seite["inhalt"], db["vorlagen"]["addtemplate"], db["vorlagen"]["listtemplateheader"]]
    js = sternebuch.JS_DATEI.read_text(encoding="utf-8")
    sichtbar = " ".join(texte) + " ".join(__import__("re").findall(r"'([^'\n]*)'", js))
    assert "–" not in sichtbar and "—" not in sichtbar


@pytest.mark.skipif(not NODE, reason="node fehlt")
def test_rechenlogik_in_node():
    datei = Path(__file__).with_name("sternebuch.test.js")
    r = subprocess.run([NODE, "--test", str(datei)], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]


def test_beispiel_baut_weiter(tmp_path, dateien):
    kurs = copy.deepcopy(beispiel.kursdefinition())
    bauen.baue(kurs, dateien, tmp_path / "b.mbz")
    assert not [b for b in pruefen.pruefe(tmp_path / "b.mbz", kurs) if b.pruefer == 10]
