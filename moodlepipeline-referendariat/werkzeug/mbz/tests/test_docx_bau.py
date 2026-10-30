"""Word-Dateien als Infoseite im Bau und Infoblätter als Pop-up (Rückmeldung LS 1, 2026-10-22).

Eine Seite `{"typ": "page", "docx": [...]}` braucht kein `inhalt`; der Bau wandelt die DOCX in HTML und legt
DOCX und Bilder in den Dateibereich der Seite. Mit `popup` öffnet Moodle die Seite in einem eigenen Fenster
(RESOURCELIB_DISPLAY_POPUP = 6), oben steht dann ein Download-Knopf auf die DOCX. `allgemein.anwenden` setzt
`popup` nach dem Profilschalter `moodle.infoblaetter_popup`.
"""
import copy
import hashlib
import tarfile
import tempfile
import xml.etree.ElementTree as ET

import pytest

docx = pytest.importorskip("docx")

import allgemein  # noqa: E402
import bauen  # noqa: E402
import beispiel  # noqa: E402
import kursdefinition as kd  # noqa: E402
import profilwerte  # noqa: E402
from test_docx_seite import _docx  # noqa: E402

SATZ = ("Infoblätter öffnen sich in einem eigenen Fenster. Schieben Sie es neben die Aufgabe oder laden Sie es "
        "herunter.")


@pytest.fixture
def wurzel(tmp_path):
    w = tmp_path / "dateien"
    beispiel.dateien_anlegen(w)
    (w / "word").mkdir()
    _docx(w / "word" / "Anl_1_Zählerschrank.docx", "Zählerschrank prüfen")
    _docx(w / "word" / "Anl_2_Verteiler.docx", "Verteiler", bild=False)
    return w


def _kurs(**seite):
    kurs = copy.deepcopy(beispiel.kursdefinition())
    kurs["abschnitte"][0]["aktivitaeten"].append(
        {"typ": "page", "name": "Infoseite Zählerschrank", "abschluss": "ansehen",
         "docx": ["word/Anl_1_Zählerschrank.docx", "word/Anl_2_Verteiler.docx"], **seite})
    return kurs


def _bauen(tmp_path, wurzel, kurs):
    ziel = tmp_path / "docx.mbz"
    bauen.baue(kurs, wurzel, ziel)
    ordner = tmp_path / "entpackt"
    with tarfile.open(ziel, "r:gz") as tar:
        tar.extractall(ordner, filter="data")
    return ordner


def _seite(ordner, name):
    for p in ordner.glob("activities/page_*/page.xml"):
        page = ET.parse(p).getroot().find("page")
        if page.findtext("name") == name:
            return page, p.parent
    raise AssertionError(f"Seite {name!r} fehlt")


def _ctx(ordner_akt):
    return ET.parse(ordner_akt / "page.xml").getroot().get("contextid")


def test_seite_mit_docx_ohne_inhalt_ist_gueltig():
    assert kd.pruefe(_kurs()) == []


def test_fehlende_docx_wird_gemeldet(wurzel):
    kurs = _kurs(docx=["word/gibt_es_nicht.docx"])
    fehler = kd.pruefe(kurs, wurzel)
    assert any("gibt_es_nicht.docx" in f and "fehlt" in f for f in fehler), fehler
    assert kd.pruefe(_kurs(), wurzel) == []


def test_docx_muss_liste_von_pfaden_sein():
    fehler = kd.pruefe(_kurs(docx="word/Anl_1_Zählerschrank.docx"))
    assert any("docx" in f for f in fehler), fehler


def test_seite_ohne_inhalt_und_ohne_docx_bleibt_ungueltig():
    kurs = _kurs()
    del kurs["abschnitte"][0]["aktivitaeten"][-1]["docx"]
    assert any("inhalt fehlt" in f for f in kd.pruefe(kurs))


def test_bau_wandelt_docx_und_legt_dateien_in_die_seite(tmp_path, wurzel):
    ordner = _bauen(tmp_path, wurzel, _kurs())
    page, akt_ordner = _seite(ordner, "Infoseite Zählerschrank")
    inhalt = page.findtext("content")
    assert "<h3>Zählerschrank prüfen</h3>" in inhalt
    assert "Zählerschrank als Word</a>" in inhalt and "Verteiler als Word</a>" in inhalt
    assert "@@PLUGINFILE@@/Anl_1_Z%C3%A4hlerschrank.docx" in inhalt
    ctx = _ctx(akt_ordner)
    saetze = ET.parse(ordner / "files.xml").getroot().findall("file")
    eigene = {f.findtext("filename"): f for f in saetze
              if f.findtext("contextid") == ctx and f.findtext("component") == "mod_page"
              and f.findtext("filearea") == "content"}
    assert {"Anl_1_Zählerschrank.docx", "Anl_2_Verteiler.docx"} <= set(eigene)
    assert any(n.endswith(".png") for n in eigene), "eingebettetes Bild fehlt im Dateibereich"
    # @@PLUGINFILE@@ der Seite zeigt auf itemid 0 (mod_page/content); sonst findet Moodle die Dateien nicht
    for n, f in eigene.items():
        if n.endswith((".docx", ".png")):
            assert f.findtext("itemid") == "0", n
    daten = (wurzel / "word" / "Anl_1_Zählerschrank.docx").read_bytes()
    h = hashlib.sha1(daten).hexdigest()
    assert eigene["Anl_1_Zählerschrank.docx"].findtext("contenthash") == h
    assert (ordner / "files" / h[:2] / h).read_bytes() == daten
    ids = {f.get("id") for f in eigene.values()}
    refs = {e.findtext("id") for e in ET.parse(akt_ordner / "inforef.xml").getroot().iter("file")}
    assert ids <= refs


def test_bau_raeumt_zwischenordner_auf(tmp_path, wurzel, monkeypatch):
    zwischen = tmp_path / "zwischen"
    zwischen.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(zwischen))
    _bauen(tmp_path, wurzel, _kurs())
    assert list(zwischen.iterdir()) == []


def test_popup_seite_im_eigenen_fenster(tmp_path, wurzel):
    ordner = _bauen(tmp_path, wurzel, _kurs(popup=True))
    page, _ = _seite(ordner, "Infoseite Zählerschrank")
    assert page.findtext("display") == "6"
    optionen = page.findtext("displayoptions")
    for teil in ('s:10:"popupwidth";i:900;', 's:11:"popupheight";i:700;', 's:10:"printintro";i:0;'):
        assert teil in optionen
    inhalt = page.findtext("content")
    knopf = inhalt.index('class="btn btn-outline-primary"')
    assert knopf < inhalt.index("<h3>Zählerschrank prüfen</h3>"), "Download-Knopf steht nicht oben"
    oben = inhalt[:inhalt.index("<section>")]
    assert oben.count("@@PLUGINFILE@@/") == 2, "je DOCX ein Knopf oben"
    for url, name, text in (("Anl_1_Z%C3%A4hlerschrank.docx", "Anl_1_Zählerschrank.docx", "Zählerschrank"),
                            ("Anl_2_Verteiler.docx", "Anl_2_Verteiler.docx", "Verteiler")):
        knopf = (f'<a class="btn btn-outline-primary" href="@@PLUGINFILE@@/{url}" title="{name}" download="">'
                 '<i class="fa fa-file-word me-1" style="color:#2B579A;" aria-hidden="true"></i>'
                 f"{text} als Word</a>")
        assert oben.count(knopf) == 1, f"Knopf für {name} fehlt oder zeigt woandershin"


def test_ohne_popup_wie_bisher(tmp_path, wurzel):
    ordner = _bauen(tmp_path, wurzel, _kurs())
    page, _ = _seite(ordner, "Infoseite Zählerschrank")
    assert page.findtext("display") == "5"
    assert "popupwidth" not in page.findtext("displayoptions")
    inhalt = page.findtext("content")
    assert "btn btn-outline-primary" not in inhalt[:inhalt.index("<section>")], "Knopf oben ohne Pop-up"
    andere, _ = _seite(ordner, "Infoblatt: Leistung im Haushalt")
    assert andere.findtext("display") == "5"


def test_popup_seite_ohne_docx_ohne_knopf(tmp_path, wurzel):
    kurs = _kurs()
    beispiel_seite = kurs["abschnitte"][1]["aktivitaeten"][0]
    beispiel_seite["popup"] = True
    ordner = _bauen(tmp_path, wurzel, kurs)
    page, _ = _seite(ordner, beispiel_seite["name"])
    assert page.findtext("display") == "6"
    assert "btn btn-outline-primary" not in page.findtext("content")


def _seiten(kurs):
    return {a["name"]: a for _, a in kd.alle_aktivitaeten(kurs)}


def test_anwenden_setzt_popup_nach_profil():
    kurs = _kurs()
    erste = kurs["abschnitte"][0]["aktivitaeten"]
    erste += [{"typ": "page", "name": "Hilfekarte 1: Zähler", "inhalt": "<p>…</p>"},
              {"typ": "page", "name": "Zusatzinfo", "inhalt": "<p>…</p>", "rolle": "info"},
              {"typ": "page", "name": "Merkhilfe", "inhalt": "<p>…</p>", "rolle": "hilfe"}]
    allgemein.anwenden(kurs, profilwerte.moodle_profil({"moodle.infoblaetter_popup": True}))
    s = _seiten(kurs)
    for name in ("Infoseite Zählerschrank", "Hilfekarte 1: Zähler", "Zusatzinfo", "Merkhilfe",
                 "Infoblatt: Leistung im Haushalt"):
        assert s[name].get("popup") is True, name
    for name in ("Handlungssituation: Haus Schütte", "So geht der Abschlusstest"):
        assert not s[name].get("popup"), name
    assert kurs["kurs"]["so_arbeiten"][-1] == SATZ
    assert SATZ in kurs["kurs"]["allgemein"]
    assert kd.pruefe(kurs) == []


def test_anwenden_neutral_ohne_popup_und_satz():
    kurs = _kurs()
    kurs["kurs"]["so_arbeiten"] = ["Jede Kachel gehört zu einer Doppelstunde."]
    allgemein.anwenden(kurs, profilwerte.moodle_profil({}))
    assert not any(a.get("popup") for _, a in kd.alle_aktivitaeten(kurs))
    assert SATZ not in kurs["kurs"]["so_arbeiten"]


def test_anwenden_zweimal_ein_satz():
    kurs = _kurs()
    profil = profilwerte.moodle_profil({"moodle.infoblaetter_popup": True})
    allgemein.anwenden(kurs, profil)
    allgemein.anwenden(kurs, profil)
    assert kurs["kurs"]["so_arbeiten"].count(SATZ) == 1


def test_popup_nur_bool_und_nur_bei_seiten():
    kurs = _kurs(popup="ja")
    assert any("popup" in f for f in kd.pruefe(kurs))
    kurs = copy.deepcopy(beispiel.kursdefinition())
    url = next(a for _, a in kd.alle_aktivitaeten(kurs) if a["typ"] == "url")
    url["popup"] = True
    assert any("popup" in f for f in kd.pruefe(kurs))


def test_popup_knoepfe_je_datei_nur_einmal_mit_namen(tmp_path, wurzel):
    """Durchsicht LS 1, Punkt 26: oben je Datei ein Knopf mit Namen, unten keine Wiederholung."""
    ordner = _bauen(tmp_path, wurzel, _kurs(popup=True))
    page, _ = _seite(ordner, "Infoseite Zählerschrank")
    inhalt = page.findtext("content")
    assert inhalt.count('class="btn btn-outline-primary"') == 2
    assert "Zählerschrank als Word</a>" in inhalt and "Verteiler als Word</a>" in inhalt
    assert "Als Word herunterladen" not in inhalt
