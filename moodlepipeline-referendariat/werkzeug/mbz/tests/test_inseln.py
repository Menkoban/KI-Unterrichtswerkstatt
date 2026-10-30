"""Übungsinseln und „Mein Lernpfad“: Regel, Schema, Bedingungsbau, Prüfer 14, Vorgriff und Skript in node."""
import copy
import itertools
import json
import shutil
import subprocess
import tarfile
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

import allgemein
import bauen
import beispiel_inseln
import inseln
import kursdefinition as kd
import lernpfad
import pruefen
import vorgriff

NODE = shutil.which("node")
G, S, V = inseln.STUFEN


# --------------------------------------------------------------------------------------------------------------- #
# Regel
# --------------------------------------------------------------------------------------------------------------- #
@pytest.mark.parametrize("einstieg, prozent, ende", [
    (S, None, S), (S, 85, V), (S, 84.99, S), (S, 50, S), (S, 49.99, G), (G, 10, G), (G, 85, S),
    (V, 100, V), (V, 50, V), (V, 49, S)])
def test_endstufe(einstieg, prozent, ende):
    assert inseln.endstufe(einstieg, prozent) == ende


def test_stufe_wandert_mit():
    assert inseln.pfad(S, [90, None, 30, 20]) == [(S, V), (V, V), (V, S), (S, G)]


# --------------------------------------------------------------------------------------------------------------- #
# Schema und Einsetzen
# --------------------------------------------------------------------------------------------------------------- #
@pytest.fixture
def kurs():
    return beispiel_inseln.kursdefinition()


def _akts(k):
    return [a for ab in k["abschnitte"] for a in ab["aktivitaeten"]]


def test_platzhalter_ist_gueltig_und_wird_eingesetzt(kurs):
    assert kd.pruefe(kurs) == []
    assert inseln.einsetzen(kurs) is True
    assert not inseln.platzhalter(kurs)
    insel1 = [a for a in _akts(kurs) if (a.get("insel") or {}).get("nr") == 1]
    assert len(insel1) == 10                                # Kopf + 3 × (Ihre Stufe, Übung, Kurztest)
    assert [a["idnummer"] for a in insel1[:4]] == ["insel-1-kopf", "insel-1-g-empfehlung", "insel-1-g-uebung",
                                                    "insel-1-g-kurztest"]
    assert all(a["schritt"] is False and a["einzug"] == 1 for a in insel1[1:])
    tests = [a for a in insel1 if a["typ"] == "quiz"]
    assert all(a["sterne"] == 0 and not kd.im_kursgesamt(a) for a in tests)
    assert [a["versuche"] for a in tests] == [0, 1, 0, 1, 0, 1]
    # erste Insel: Start Standard, Kurztest Grundlagen und Vertiefung erreicht niemand
    sichtbar = {a["kennung"]: a.get("sichtbar", True) for a in tests}
    assert sichtbar == {"Insel 1 · Grundlagen: Üben": True, "Insel 1 · Grundlagen: Kurztest": False,
                        "Insel 1 · Standard: Üben": True, "Insel 1 · Standard: Kurztest": True,
                        "Insel 1 · Vertiefung: Üben": True, "Insel 1 · Vertiefung: Kurztest": False}
    assert kurs["inseln"][1]["stufen"][V]["kurztest"] == "Insel 2 · Vertiefung: Kurztest"
    assert kurs["inseln"][0]["start"] == S and kurs["inseln"][1]["start"] is None
    assert kd.pruefe(kurs) == []
    vorher = json.dumps(kurs, sort_keys=True)
    assert inseln.einsetzen(kurs) is False                  # idempotent
    assert json.dumps(kurs, sort_keys=True) == vorher


def test_bedingungen_der_zweiten_insel(kurs):
    inseln.einsetzen(kurs)
    a = {kd.kennung_von(a): a for a in _akts(kurs)}
    tor = {"abschluss": beispiel_inseln.ABGABE_3, "zustand": "abgeschlossen"}
    # Kurztest Vertiefung: Einstieg Vertiefung (= Insel 1 Standard ab 85 %) und die Übung hat einen Versuch
    assert a["Insel 2 · Vertiefung: Kurztest"]["voraussetzung"] == [
        tor, {"aktivitaet": "Insel 1 · Standard: Kurztest", "min": 85, "sichtbar_wenn_gesperrt": False},
        {"aktivitaet": "Insel 2 · Vertiefung: Üben", "bewertet": True, "sichtbar_wenn_gesperrt": True}]
    # Ihre Stufe Grundlagen nach Insel 2: KT G < 85 oder KT S < 50 oder (kein KT G und Insel 1 endete auf G)
    assert a["Insel 2 · Ihre Stufe: Grundlagen"]["voraussetzung"][1] == {"oder": [
        {"aktivitaet": "Insel 2 · Grundlagen: Kurztest", "max": 85},
        {"aktivitaet": "Insel 2 · Standard: Kurztest", "max": 50},
        {"und": [{"nicht": [{"aktivitaet": "Insel 2 · Grundlagen: Kurztest", "bewertet": True}]},
                 {"aktivitaet": "Insel 1 · Standard: Kurztest", "max": 50}]}], "sichtbar_wenn_gesperrt": False}


@pytest.mark.parametrize("aendern, meldung", [
    (lambda p: p["stufen"].pop(V), "stufen braucht genau"),
    (lambda p: p["stufen"][S]["kurztest"]["fragen"].extend(copy.deepcopy(p["stufen"][S]["kurztest"]["fragen"])),
     "Kurztest mit 6 Fragen"),
    (lambda p: p["stufen"][G]["uebung"].update(sterne=3), "ohne sterne"),
    (lambda p: p.update(nr=0), "nr muss"),
])
def test_platzhalter_formfehler(kurs, aendern, meldung):
    aendern(inseln.platzhalter(kurs)[0])
    assert any(meldung in f for f in kd.pruefe(kurs))
    with pytest.raises(ValueError):
        inseln.einsetzen(kurs)


def test_start_nur_an_der_ersten_insel_und_nummern_aufsteigend(kurs):
    p1, p2 = inseln.platzhalter(kurs)
    p2["start"] = G
    assert any("start nur an der ersten Insel" in f for f in kd.pruefe(kurs))
    del p2["start"]
    p1["nr"], p2["nr"] = 2, 1
    assert any("aufsteigen" in f for f in kd.pruefe(kurs))


def test_start_grundlagen(kurs):
    inseln.platzhalter(kurs)[0]["start"] = G
    inseln.einsetzen(kurs)
    a = {kd.kennung_von(a): a for a in _akts(kurs)}
    assert a["Insel 1 · Grundlagen: Kurztest"].get("sichtbar", True) is True
    assert a["Insel 1 · Standard: Kurztest"]["sichtbar"] is False
    assert a["Insel 1 · Vertiefung: Üben"]["sichtbar"] is False      # zwei Stufen hoch: in Insel 1 unerreichbar


def test_neue_bedingungen_und_bewertet_im_schema(kurs):
    inseln.einsetzen(kurs)
    a = {kd.kennung_von(a): a for a in _akts(kurs)}
    a["Insel 2 · Standard: Üben"]["voraussetzung"] = [{"aktivitaet": beispiel_inseln.ABGABE_3, "bewertet": True}]
    assert any("wird nicht bewertet" in f for f in kd.pruefe(kurs))
    a["Insel 2 · Standard: Üben"]["voraussetzung"] = [{"und": []}]
    assert any("und braucht" in f for f in kd.pruefe(kurs))
    a["Insel 2 · Standard: Üben"]["voraussetzung"] = [{"aktivitaet": "Insel 1 · Standard: Üben", "bewertet": True,
                                                       "min": 3}]
    assert any("bewertet nur als true" in f for f in kd.pruefe(kurs))


def test_schrittnummern_zaehlen_die_insel_als_einen_schritt(kurs):
    ab = kurs["abschnitte"][2]
    ab["zusammenfassung"] = "<p>Auftrag</p><ol><li>Rechnen</li><li>Üben</li></ol>"
    inseln.einsetzen(kurs)
    allgemein.schrittnummern(kurs["abschnitte"])
    namen = [a["name"] for a in ab["aktivitaeten"]]
    assert namen[0].startswith("Schritt 1 · ") and namen[1] == "Schritt 2 · Insel 2: Widerstand"
    assert all(not n.startswith("Schritt") for n in namen[2:])


# --------------------------------------------------------------------------------------------------------------- #
# Bau und Prüfer 14
# --------------------------------------------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def gebaut(tmp_path_factory):
    wurzel = tmp_path_factory.mktemp("dateien")
    beispiel_inseln.beispiel.dateien_anlegen(wurzel)
    ziel = tmp_path_factory.mktemp("bau") / "inseln.mbz"
    k = beispiel_inseln.kursdefinition()
    bauen.baue(k, wurzel, ziel)
    return ziel, k, wurzel


def _entpackt(mbz, ordner):
    with tarfile.open(mbz, "r:gz") as tar:
        tar.extractall(ordner, filter="data")
    return ordner


def _modul(ordner, idnummer):
    for m in Path(ordner).glob("activities/*/module.xml"):
        if ET.parse(m).getroot().findtext("idnumber") == idnummer:
            return m
    raise KeyError(idnummer)


def test_beispiel_ohne_fehler(gebaut):
    ziel, k, _ = gebaut
    befunde = pruefen.pruefe(ziel, k)
    assert [str(b) for b in befunde if b.stufe == pruefen.FEHLER] == []
    assert not [b for b in befunde if b.pruefer == 14]
    assert pruefen.TITEL[14] == "Inseln" and len(pruefen.PRUEFER) == 15


def test_bau_schreibt_bewertet_und_und_gruppe(gebaut, tmp_path):
    o = _entpackt(gebaut[0], tmp_path / "e")
    v = json.loads(ET.parse(_modul(o, "insel-2-g-empfehlung")).getroot().findtext("availability"))
    oder = v["c"][1]
    assert oder["op"] == "|" and oder["c"][2]["op"] == "&"
    nicht = oder["c"][2]["c"][0]
    assert nicht["op"] == "!&" and set(nicht["c"][0]) == {"type", "id"}       # Bewertung ohne min und max
    assert v["showc"] == [False, False]                  # „Ihre Stufe“ ganz verborgen, auch vor dem Tor


def test_lernpfad_in_allgemein_mit_endgueltigen_namen(gebaut, tmp_path):
    o = _entpackt(gebaut[0], tmp_path / "e")
    m = ET.parse(_modul(o, lernpfad.IDNUMMER)).getroot()
    assert m.findtext("sectionnumber") == "0"
    js = ET.parse(next(_modul(o, lernpfad.IDNUMMER).parent.glob("data.xml"))).getroot().find("data").findtext(
        "jstemplate")
    konfig = lernpfad.konfig_aus(js)
    assert [i["nr"] for i in konfig["inseln"]] == [1, 2]
    assert konfig["inseln"][0]["titel"] == "Leistung und Strom"
    assert konfig["inseln"][1]["kurztest"][2] == "Insel 2 · Vertiefung: Kurztest"
    assert konfig["start"] == S and konfig["grenzen"] == [50, 85]
    assert not pruefen.GEHEIM.search(js)


def _p14(ordner, k):
    return [b for b in pruefen.pruefe(ordner, k) if b.pruefer == 14]


def _availability(ordner, idnummer, aendern):
    m = _modul(ordner, idnummer)
    baum = ET.parse(m)
    el = baum.getroot().find("availability")
    el.text = json.dumps(aendern(json.loads(el.text)))
    baum.write(m, encoding="utf-8")


def test_p14_findet_falsche_grenze(gebaut, tmp_path):
    o = _entpackt(gebaut[0], tmp_path / "e")

    def aendern(v):
        v["c"][1]["min"] = 80                      # Vertiefung schon ab 80 %
        return v
    _availability(o, "insel-1-v-uebung", aendern)
    befunde = _p14(o, gebaut[1])
    assert befunde and all(b.stufe == pruefen.FEHLER for b in befunde)
    assert any("Vertiefung Übung ist offen" in b.text and "80 %" not in b.text for b in befunde)


def test_p14_findet_zwei_offene_kurztests(gebaut, tmp_path):
    o = _entpackt(gebaut[0], tmp_path / "e")

    def aendern(v):
        v["c"] = [v["c"][0], v["c"][2]]            # ohne Einstiegsbedingung
        v["showc"] = [True, True]
        return v
    _availability(o, "insel-2-v-kurztest", aendern)
    assert any("offene Kurztests" in b.text for b in _p14(o, gebaut[1]))


def test_p14_findet_luecke_in_der_startstufe(gebaut, tmp_path):
    o = _entpackt(gebaut[0], tmp_path / "e")

    def aendern(v):
        v["c"][1]["c"] = v["c"][1]["c"][:-1]       # Fall „kein Kurztest in Insel 2“ fehlt
        return v
    _availability(o, "insel-2-s-empfehlung", aendern)
    assert any("„Ihre Stufe: Standard“ ist verborgen" in b.text for b in _p14(o, gebaut[1]))


def test_p14_kurztest_mit_zwei_versuchen_und_im_kursgesamt(tmp_path, gebaut):
    k = beispiel_inseln.kursdefinition()
    inseln.einsetzen(k)
    a = {kd.kennung_von(a): a for a in _akts(k)}
    a["Insel 1 · Standard: Kurztest"]["versuche"] = 2
    a["Insel 2 · Standard: Üben"].pop("sterne")              # zählt dann mit 10 Punkten im Kursgesamt
    ziel = tmp_path / "v.mbz"
    k["kurs"]["sternzaehler"] = False
    bauen.baue(k, gebaut[2], ziel)
    texte = [b.text for b in _p14(ziel, k)]
    assert any("Kurztest mit 2 Versuchen" in t for t in texte)
    assert any("Insel 2 · Standard: Üben" in t and "Kursgesamt" in t for t in texte)


def test_p14_stern_haengt_an_insel(tmp_path, gebaut):
    k = beispiel_inseln.kursdefinition()
    inseln.einsetzen(k)
    stern = next(a for a in _akts(k) if a.get("rolle") == "stern")
    stern["voraussetzung"].append({"aktivitaet": "Insel 1 · Standard: Kurztest", "min": 50})
    ziel = tmp_path / "v.mbz"
    bauen.baue(k, gebaut[2], ziel)
    assert any("hängt an einer Inselaktivität" in b.text for b in _p14(ziel, k))


def test_p14_fehlende_stufe_und_falscher_name_im_lernpfad(gebaut, tmp_path):
    o = _entpackt(gebaut[0], tmp_path / "e")
    m = _modul(o, "insel-2-g-uebung")
    w = ET.parse(m)
    w.getroot().find("idnumber").text = "x"
    w.write(m, encoding="utf-8")
    texte = [b.text for b in _p14(o, gebaut[1])]
    assert any("Insel 2 / Grundlagen: Übung fehlt" in t for t in texte)
    # Name umbenannt: das Skript fände die Übung nicht mehr
    w.getroot().find("idnumber").text = "insel-2-g-uebung"
    w.write(m, encoding="utf-8")
    for d in Path(o).glob("activities/quiz_*"):
        if ET.parse(d / "module.xml").getroot().findtext("idnumber") == "insel-2-g-uebung":
            q = ET.parse(d / "quiz.xml")
            q.getroot().find("quiz/name").text = "Umbenannt"
            q.write(d / "quiz.xml", encoding="utf-8")
            mb = ET.parse(Path(o) / "moodle_backup.xml")
            for akt in mb.getroot().iter("activity"):
                if akt.findtext("directory") == f"activities/{d.name}":
                    akt.find("title").text = "Umbenannt"
            mb.write(Path(o) / "moodle_backup.xml", encoding="utf-8")
    assert any("sucht 'Insel 2 · Grundlagen: Üben'" in b.text for b in _p14(o, gebaut[1]))


def test_p14_ohne_inseln_still_und_lernpfad_ohne_inseln_fehler(paket):
    _, ordner, k = paket
    assert _p14(ordner, k) == []


def test_lernpfad_braucht_inseln():
    with pytest.raises(ValueError):
        lernpfad.konfig({"kurs": {}})


def test_profil_schaltet_lernpfad(kurs):
    profil = {"moodle.lernpfad_anzeige": True}
    allgemein.anwenden(kurs, profil)
    assert kurs["kurs"]["lernpfad"] is True


# --------------------------------------------------------------------------------------------------------------- #
# Vorgriff
# --------------------------------------------------------------------------------------------------------------- #
def test_vorgriff_ohne_fehlbefund_und_ein_befund_je_insel(kurs):
    ab = kurs["abschnitte"][2]
    ab["aktivitaeten"][0].update(abgabe_bestaetigen=True, name="Ihre Vorhersage: Widerstand", kennung=None)
    ab["aktivitaeten"][0].pop("kennung")
    inseln.platzhalter(kurs)[1]["voraussetzung"] = [{"abschluss": "Ihre Vorhersage: Widerstand"}]
    assert vorgriff.pruefe(kurs) == []
    inseln.platzhalter(kurs)[1].pop("voraussetzung")
    befunde = vorgriff.pruefe(kurs)
    assert len(befunde) == 1 and "Insel 2" in befunde[0][1] and befunde[0][0] == "Fehler"


# --------------------------------------------------------------------------------------------------------------- #
# Skript in node: dieselbe Regel wie inseln.pfad
# --------------------------------------------------------------------------------------------------------------- #
@pytest.mark.skipif(not NODE, reason="node fehlt")
def test_skript_rechnet_wie_python(tmp_path):
    k = beispiel_inseln.kursdefinition()
    inseln.einsetzen(k)
    k["inseln"].append(json.loads(json.dumps({**k["inseln"][1], "nr": 3}).replace("Insel 2", "Insel 3")))
    konfig = lernpfad.konfig(k)
    faelle = []
    for e1, e2, e3 in itertools.product([None, 30, 50, 84.99, 85], repeat=3):
        soll = inseln.pfad(S, [e1, e2, e3])
        noten = {}
        for i, (einstieg, _), p in zip(range(3), soll, (e1, e2, e3)):
            noten[konfig["inseln"][i]["uebung"][inseln.STUFEN.index(einstieg)].lower()] = 100
            if p is not None:
                noten[konfig["inseln"][i]["kurztest"][inseln.STUFEN.index(einstieg)].lower()] = p
        faelle.append({"noten": noten, "soll": [[inseln.STUFEN.index(a), inseln.STUFEN.index(b)] for a, b in soll]})
    skript = tmp_path / "probe.js"
    skript.write_text(
        f"const L = require({json.dumps(str(Path(lernpfad.JS_DATEI)))});\n"
        f"const K = {json.dumps(konfig, ensure_ascii=False)};\n"
        f"const F = {json.dumps(faelle, ensure_ascii=False)};\n"
        "let fehler = 0;\n"
        "for (const f of F) { const p = L.pfad(K, f.noten);\n"
        "  const ist = p.map(x => [x.einstieg, x.ende]);\n"
        "  if (JSON.stringify(ist) !== JSON.stringify(f.soll)) { fehler++; console.log(JSON.stringify([f, ist])); } }\n"
        "const p = L.pfad(K, {});\n"
        "console.log(fehler, L.naechste(p, K.stufen), L.satz(p[0], K.stufen));\n", encoding="utf-8")
    aus = subprocess.run([NODE, str(skript)], capture_output=True, text=True, check=True).stdout.strip()
    assert aus.startswith("0 Ihre nächste Insel (1) beginnt auf Standard."), aus
    assert "noch nicht begonnen" in aus


@pytest.mark.skipif(not NODE, reason="node fehlt")
def test_skript_kurztest_fehlt_und_text(tmp_path):
    k = beispiel_inseln.kursdefinition()
    inseln.einsetzen(k)
    konfig = lernpfad.konfig(k)
    noten = {konfig["inseln"][0]["uebung"][1].lower(): 100, konfig["inseln"][1]["uebung"][1].lower(): 80}
    skript = tmp_path / "probe.js"
    skript.write_text(
        f"const L = require({json.dumps(str(Path(lernpfad.JS_DATEI)))});\n"
        f"const K = {json.dumps(konfig, ensure_ascii=False)};\n"
        f"const p = L.pfad(K, {json.dumps(noten, ensure_ascii=False)});\n"
        "console.log(JSON.stringify([p[0].kurztestFehlt, p[1].kurztestFehlt, L.satz(p[0], K.stufen), "
        "L.linie(p).length, L.zahl('84,50 %')]));\n", encoding="utf-8")
    aus = json.loads(subprocess.run([NODE, str(skript)], capture_output=True, text=True, check=True).stdout)
    assert aus[0] is True and aus[1] is False
    assert "Kurztest fehlt" in aus[2] and "geübt: Standard" in aus[2]
    assert aus[3] == 1 and aus[4] == 84.5


def test_kein_loesungsweg_im_kacheltext():
    """Lehrkraft 2026-10-30: „So gehen Sie vor“ oder eine Schrittliste im Kacheltext ist ein Fehler (Prüfer 15)."""
    assert pruefen._VORGEHEN.search("So gehen Sie vor: 1. messen")
    assert pruefen._VORGEHEN.search("Gehen Sie Schritt für Schritt vor.")
    assert not pruefen._VORGEHEN.search("Finden Sie heraus, warum das Thermostat falsch anzeigt.")
    assert pruefen._ABFOLGE.search("Messen Sie zuerst die Spannung, danach den Strom.")
