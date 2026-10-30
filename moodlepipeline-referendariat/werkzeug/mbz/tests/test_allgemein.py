"""Abschnitt „Allgemein“ (Vorgeschmack, Steckbrief, So arbeiten Sie, Logo, KI-Hinweis) und Kachelnummern.

Rückmeldung LS 1 (2026-10-22): der KI-Hinweis steht genau einmal im Kurs, unten in Allgemein neben dem Logo –
nicht in der Kursbeschreibung, nicht in Aktivitäten. Neutrales Profil = bisheriges Verhalten.
"""
import copy
from pathlib import Path
import json
import re
import tarfile
import xml.etree.ElementTree as ET

import allgemein
import bauen
import beispiel
import kursdefinition as kd
import profilwerte
import sterne
import xmlhilfe

#: Zusatz am Namen der Hilfen in Kacheln mit Selbstlöse-Stern (Lehrkraft 2026-10-26)
Z = sterne.HILFE_ZUSATZ
SATZ = "Dieser Kurs wurde von Herrn Muster mit Hilfe von künstlicher Intelligenz erstellt und geprüft."
STECKBRIEF = {"Lernfeld": "LF 1 Elektrotechnische Systeme analysieren", "Umfang": "8 Unterrichtsstunden",
              "Ergebnis": "Info-Mappe für Familie Schütte"}


def _profil(**eigene):
    return profilwerte.moodle_profil({"lehrkraft.anrede": "Herr Muster", "lehrkraft.email": "muster@schule.example",
                                      **eigene})


def _voll(logo="bilder/logo.png"):
    return _profil(**{"moodle.schullogo": logo, "moodle.ki_hinweis": True, "moodle.steckbrief": True,
                      "moodle.kachelnummern": True})


def _kurs():
    kurs = copy.deepcopy(beispiel.kursdefinition())
    kurs["kurs"].update(vorgeschmack="Familie Schütte hat ein Haus gekauft.", steckbrief=dict(STECKBRIEF),
                        so_arbeiten=["Jede Kachel gehört zu einer Doppelstunde.", "Hilfen holen Sie sich selbst."])
    return kurs


def _bauen(tmp_path, dateien, kurs):
    assert kd.pruefe(kurs) == []
    ziel = tmp_path / "allgemein.mbz"
    bauen.baue(kurs, dateien, ziel)
    ordner = tmp_path / "entpackt"
    with tarfile.open(ziel, "r:gz") as tar:
        tar.extractall(ordner, filter="data")
    return ordner


def _alle_xml(ordner):
    return {p: p.read_text(encoding="utf-8") for p in ordner.rglob("*.xml")}


def _allgemein_summary(ordner):
    root = ET.parse(ordner / "moodle_backup.xml").getroot()
    sec = next(s.findtext("sectionid") for s in root.findall("information/contents/sections/section")
               if s.findtext("title") == "0")
    return ET.parse(ordner / f"sections/section_{sec}/section.xml").getroot().findtext("summary"), sec


def test_reihenfolge_und_inhalt():
    html, dateien = allgemein.allgemein_html(_kurs()["kurs"], _voll())
    teile = ["Familie Schütte hat ein Haus gekauft.", "<table", "Lernfeld", "Umfang", "Ergebnis",
             "Ansprechpartner", "So arbeiten Sie in diesem Kurs", "<li>Jede Kachel", 'alt="Logo der Schule"', SATZ]
    stellen = [html.index(t) for t in teile]
    assert stellen == sorted(stellen)
    assert 'Herr Muster · <a href="mailto:muster@schule.example">muster@schule.example</a>' in html
    assert 'src="logo.png"' in html
    assert dateien == ["bilder/logo.png"]


def test_steckbrief_nur_bei_profilwert():
    html, _ = allgemein.allgemein_html(_kurs()["kurs"], _profil(**{"moodle.steckbrief": False}))
    assert "<table" not in html and "Ansprechpartner" not in html
    assert "Familie Schütte hat ein Haus gekauft." in html and "So arbeiten Sie" in html


def test_neutrales_profil_ohne_logo_und_ki_satz():
    html, dateien = allgemein.allgemein_html(_kurs()["kurs"], profilwerte.moodle_profil({}))
    assert dateien == [] and "<img" not in html and "künstlicher Intelligenz" not in html


def test_nummern_lehrkraft_ohne_nummer():
    abschnitte = [{"name": n} for n in ("Einstieg", "Info", "Üben", "Material für Lehrkräfte", "Mappe", "Rückblick")]
    abschnitte[3]["lehrkraft"] = True
    allgemein.nummeriere(abschnitte)
    assert [a["name"] for a in abschnitte] == ["1 · Einstieg", "2 · Info", "3 · Üben", "Material für Lehrkräfte",
                                               "4 · Mappe", "5 · Rückblick"]
    allgemein.nummeriere(abschnitte)   # zweimal nummerieren ändert nichts
    assert abschnitte[5]["name"] == "5 · Rückblick"


def test_ki_hinweis_genau_einmal_unten_in_allgemein(tmp_path, dateien):
    (dateien / "bilder" / "logo.png").write_bytes((dateien / "bilder" / "kurs.png").read_bytes())
    kurs = _kurs()
    allgemein.anwenden(kurs, _voll())
    ordner = _bauen(tmp_path, dateien, kurs)
    # Schlüssel = Pfad im Paket, damit ein zweiter Satz in einer anderen Kachel (auch section.xml) auffällt
    treffer = {p.relative_to(ordner).as_posix(): t.count("künstlicher Intelligenz")
               for p, t in _alle_xml(ordner).items() if "künstlicher Intelligenz" in t}
    summary, sec = _allgemein_summary(ordner)
    assert treffer == {f"sections/section_{sec}/section.xml": 1}, treffer
    assert summary.rstrip().endswith(f"{SATZ}</p>")
    assert 'src="@@PLUGINFILE@@/logo.png"' in summary
    kurs_summary = ET.parse(ordner / "course/course.xml").getroot().findtext("summary")
    assert "künstlicher Intelligenz" not in kurs_summary
    logo = [f for f in ET.parse(ordner / "files.xml").getroot().findall("file")
            if f.findtext("filename") == "logo.png"]
    assert [(f.findtext("component"), f.findtext("filearea"), f.findtext("itemid")) for f in logo] == [
        ("course", "section", sec)]
    namen = [s.findtext("title") for s in ET.parse(ordner / "moodle_backup.xml").getroot()
             .findall("information/contents/sections/section")]
    assert namen == ["0", "1 · Einstieg: Der Auftrag im Haus Schütte", "2 · Erarbeitung: Leistung und Strom",
                     "3 · Rückblick", "Material für Lehrkräfte"]


def test_neutrales_profil_wie_bisher(tmp_path, dateien):
    kurs = copy.deepcopy(beispiel.kursdefinition())
    for ab in kurs["abschnitte"]:
        ab["name"] = ab["name"].split(" · ", 1)[-1]
    allgemein.anwenden(kurs, profilwerte.moodle_profil({}))
    ordner = _bauen(tmp_path, dateien, kurs)
    kurs_summary = ET.parse(ordner / "course/course.xml").getroot().findtext("summary")
    assert kurs_summary.startswith(f"<p>{kurs['kurs']['ki_hinweis']}</p>")
    summary, _ = _allgemein_summary(ordner)
    assert "<img" not in (summary or "")
    assert [ab["name"] for ab in kurs["abschnitte"]] == ["Einstieg: Der Auftrag im Haus Schütte",
                                                         "Erarbeitung: Leistung und Strom", "Rückblick",
                                                         "Material für Lehrkräfte"]


def test_mime_audio():
    assert [xmlhilfe.mime(f"a.{e}") for e in ("mp3", "m4a", "ogg", "wav")] == [
        "audio/mp3", "audio/mp4", "audio/ogg", "audio/wav"]


def test_logo_pfad_relativ_zur_bauwurzel(tmp_path):
    """Kein rechnerabhängiger Pfad in der Kursdefinition (sie wird als bau/kursdefinition.json versioniert)."""
    kurs = _kurs()
    arbeitsbereich, bau = tmp_path / "Bereich", tmp_path / "Bereich" / "LS" / "bau" / "dateien"
    allgemein.anwenden(kurs, _voll(logo="Profil/logo.png"), logo_wurzel=arbeitsbereich, dateien_wurzel=bau)
    assert kurs["kurs"]["allgemein_dateien"] == ["../../../Profil/logo.png"]
    assert str(tmp_path) not in str(kurs)


def test_ki_satz_ohne_anrede():
    mit_name = profilwerte.moodle_profil({"lehrkraft.anrede": "", "lehrkraft.name": "Alex Muster"})
    assert allgemein.ki_satz(mit_name) == ("Dieser Kurs wurde von Alex Muster mit Hilfe von künstlicher "
                                           "Intelligenz erstellt und geprüft.")
    ohne = profilwerte.moodle_profil({"lehrkraft.anrede": "", "lehrkraft.name": ""})
    assert allgemein.ki_satz(ohne) == "Dieser Kurs wurde mit Hilfe von künstlicher Intelligenz erstellt und geprüft."


# -- Schrittnummern (Profil moodle.schrittnummern, Lehrkraft 2026-10-22) ------------------------------------- #
def _schrittkachel():
    import sterne
    s = lambda n: {"typ": "page", "name": n, "inhalt": "<p>x</p>", "abschluss": "ansehen"}  # noqa: E731
    test = {"typ": "quiz", "name": "Test: Was steht wo?", "sterne": 3, "fragen": [
        {"typ": "truefalse", "name": "F", "text": "<p>Stimmt das?</p>", "richtig": True}]}
    kachel = {"name": "Begehung", "zusammenfassung": "<p>Auftrag</p><ol><li>Erkunden</li><li>Testen</li>"
                                                    "<li>Planen</li></ol>",
              "aktivitaeten": [s("Haus erkunden"), test, sterne.hilfekarte("Tipp", "<p>x</p>"),
                               sterne.hilfekarte("Ansatz", "<p>x</p>"), s("Arbeitsplan")]}
    kachel["aktivitaeten"].append(sterne.stern_aktivitaet(kachel, test["name"], ["Tipp", "Ansatz"]))
    return kachel


def test_schrittnummern_vor_jeder_hauptaktivitaet():
    kachel = _schrittkachel()
    allgemein.schrittnummern([kachel])
    akts = kachel["aktivitaeten"]
    assert [a["name"] for a in akts] == [
        "Schritt 1 · Haus erkunden", "Schritt 2 · Test: Was steht wo?", "Hilfe zu Schritt 2 · Tipp" + Z,
        "Hilfe zu Schritt 2 · Ansatz" + Z, "Schritt 3 · Arbeitsplan", "Ihr Stern: selbst gelöst"]
    assert [a.get("einzug", 0) for a in akts] == [0, 0, 1, 1, 0, 0]
    # Verweise laufen über die Kennung (alter Name): die Voraussetzungen des Sterns bleiben gültig
    kurs = {"kurs": {"vollname": "K", "kurzname": "K", "beschreibung": "<p>x</p>",
                     "ki_hinweis": "mit Hilfe von künstlicher Intelligenz"}, "abschnitte": [kachel]}
    assert kd.pruefe(kurs) == []
    allgemein.schrittnummern([kachel])      # zweimal ändert nichts
    assert akts[1]["name"] == "Schritt 2 · Test: Was steht wo?" and akts[2]["name"] == "Hilfe zu Schritt 2 · Tipp" + Z


def test_eine_hilfe_heisst_nur_hilfe_zu_schritt():
    kachel = _schrittkachel()
    kachel["aktivitaeten"] = [a for a in kachel["aktivitaeten"] if a["name"] != "Ansatz"]
    allgemein.schrittnummern([kachel])
    assert kachel["aktivitaeten"][2]["name"] == "Hilfe zu Schritt 2" + Z


def test_schrittnummern_nur_mit_liste_und_passender_zahl():
    ohne = _schrittkachel()
    ohne["zusammenfassung"] = "<p>Kein Auftrag mit Schritten</p>"
    lehr = dict(_schrittkachel(), lehrkraft=True)
    allgemein.schrittnummern([ohne, lehr])
    assert ohne["aktivitaeten"][0]["name"] == "Haus erkunden" and lehr["aktivitaeten"][0]["name"] == "Haus erkunden"
    falsch = _schrittkachel()
    falsch["zusammenfassung"] = "<ol><li>Eins</li><li>Zwei</li></ol>"
    try:
        allgemein.schrittnummern([falsch])
    except ValueError as e:
        assert "2" in str(e) and "3" in str(e)
    else:
        raise AssertionError("Schrittliste und Aktivitäten müssen 1:1 passen")


def test_anwenden_schrittnummern_nach_profil():
    kurs = {"kurs": {}, "abschnitte": [_schrittkachel()]}
    allgemein.anwenden(kurs, profilwerte.moodle_profil({}))
    assert kurs["abschnitte"][0]["aktivitaeten"][0]["name"] == "Haus erkunden"
    allgemein.anwenden(kurs, profilwerte.moodle_profil({"moodle.schrittnummern": True}))
    assert kurs["abschnitte"][0]["aktivitaeten"][0]["name"] == "Schritt 1 · Haus erkunden"
    # ID-Nummern der Hilfen und Sterne setzt anwenden immer (Dashboard, Prüfer 8)
    assert kurs["abschnitte"][0]["aktivitaeten"][-1]["idnummer"] == "stern-k1"


# -- Schrittnummern mit Kachelnummer (Profil moodle.schrittnummern_mit_kachel, Lehrkraft 2026-10-23) ---------- #
def _zwei_kacheln():
    erste = {"name": "Einstieg", "zusammenfassung": "<p>Willkommen</p>",
             "aktivitaeten": [{"typ": "page", "name": "Start", "inhalt": "<p>x</p>"}]}
    zweite = _schrittkachel()
    zweite["aktivitaeten"] = [a for a in zweite["aktivitaeten"] if a["name"] != "Ansatz"]   # eine Hilfe
    zweite["aktivitaeten"][2], zweite["aktivitaeten"][1] = zweite["aktivitaeten"][1], zweite["aktivitaeten"][2]
    return [{"name": "Lehrkraft", "lehrkraft": True, "aktivitaeten": []}, erste, zweite]


def test_schritt_mit_kachelnummer():
    abschnitte = _zwei_kacheln()            # Hilfe steht unter Schritt 1 der zweiten Kachel
    allgemein.schrittnummern(abschnitte, mit_kachel=True)
    akts = abschnitte[2]["aktivitaeten"]
    assert [a["name"] for a in akts] == [
        "Schritt 2.1 · Haus erkunden", "Hilfe zu 2.1" + Z, "Schritt 2.2 · Test: Was steht wo?",
        "Schritt 2.3 · Arbeitsplan", "Ihr Stern: selbst gelöst"]
    text = abschnitte[2]["zusammenfassung"]
    assert '<ol style="list-style:none;padding-left:0">' in text
    assert "<li><strong>2.1</strong> Erkunden</li><li><strong>2.2</strong> Testen</li>" in text
    assert re.search(r"<ol[^>]*><li><strong>2\.1</strong> ", text)
    assert abschnitte[1]["aktivitaeten"][0]["name"] == "Start"           # Kachel ohne Liste bleibt
    mehr = _schrittkachel()                                               # zwei Hilfen: mit Kennung
    allgemein.schrittnummern([mehr], mit_kachel=True)
    assert [a["name"] for a in mehr["aktivitaeten"][2:4]] == ["Hilfe zu 1.2 · Tipp" + Z, "Hilfe zu 1.2 · Ansatz" + Z]


def test_mit_kachel_zweimal_gleich():
    abschnitte = _zwei_kacheln()
    allgemein.schrittnummern(abschnitte, mit_kachel=True)
    einmal = copy.deepcopy(abschnitte)
    allgemein.schrittnummern(abschnitte, mit_kachel=True)
    assert abschnitte == einmal


def test_ohne_schalter_wie_bisher():
    abschnitte = _zwei_kacheln()
    vorher = abschnitte[2]["zusammenfassung"]
    allgemein.schrittnummern(abschnitte)
    assert [a["name"] for a in abschnitte[2]["aktivitaeten"][:3]] == [
        "Schritt 1 · Haus erkunden", "Hilfe zu Schritt 1" + Z, "Schritt 2 · Test: Was steht wo?"]
    assert abschnitte[2]["zusammenfassung"] == vorher


def test_anwenden_gibt_kachelschalter_weiter():
    kurs = {"kurs": {}, "abschnitte": _zwei_kacheln()}
    allgemein.anwenden(kurs, profilwerte.moodle_profil({"moodle.schrittnummern": True,
                                                        "moodle.schrittnummern_mit_kachel": True}))
    assert kurs["abschnitte"][2]["aktivitaeten"][0]["name"] == "Schritt 2.1 · Haus erkunden"


def test_einzug_im_paket(tmp_path, dateien):
    kurs = _kurs()
    kurs["abschnitte"][0]["aktivitaeten"][0]["einzug"] = 1
    ordner = _bauen(tmp_path, dateien, kurs)
    root = ET.parse(ordner / "moodle_backup.xml").getroot()
    einzug = {a.findtext("title"): ET.parse(ordner / a.findtext("directory") / "module.xml").getroot()
              .findtext("indent") for a in root.iter("activity") if a.findtext("directory")}
    assert einzug[kurs["abschnitte"][0]["aktivitaeten"][0]["name"]] == "1"
    assert sorted(set(einzug.values())) == ["0", "1"]
    kurs["abschnitte"][0]["aktivitaeten"][0]["einzug"] = -1
    assert any("einzug" in f for f in kd.pruefe(kurs))


def test_verborgene_hauptaktivitaet_ohne_schrittnummer():
    """Verborgenes (z. B. Material, das erst nach einer Kontrolle sichtbar wird) bekommt keine Nummer und zählt
    nicht gegen die Liste im Kacheltext (Lehrkraft 2026-10-23)."""
    kachel = _schrittkachel()
    verborgen = {"typ": "page", "name": "Rollenkarten", "inhalt": "<p>x</p>", "sichtbar": False}
    kachel["aktivitaeten"].insert(4, verborgen)
    allgemein.schrittnummern([kachel])
    assert verborgen["name"] == "Rollenkarten"
    assert kachel["aktivitaeten"][5]["name"] == "Schritt 3 · Arbeitsplan"
    # Gegenprobe: sichtbar zählt sie mit – dann passt die Liste (3 Schritte) nicht mehr
    kachel = _schrittkachel()
    kachel["aktivitaeten"].insert(4, dict(verborgen, sichtbar=True))
    try:
        allgemein.schrittnummern([kachel])
    except ValueError as e:
        assert "4 Aktivitäten" in str(e)
    else:
        raise AssertionError("sichtbare Zusatzaktivität muss die Liste sprengen")


# -- Allgemein in Schulfarben (Profil moodle.allgemein_stil, Lehrkraft 2026-10-23) ---------------------------- #
KASTEN = '<div style="background:#08349C;color:#fff;border-radius:6px;padding:12px 16px;">'
BLITZ = '<i class="fa fa-bolt" style="color:#7DDE78;" aria-hidden="true"></i>'


def _bunt(**eigene):
    return _voll(**{}) | {"moodle.allgemein_stil": "schulfarben", **eigene}


def test_begruessungskasten_oben():
    kurs = _kurs()["kurs"]
    kurs["begruessung_titel"] = "Ein neuer Auftrag für den Stromhof"
    html, _ = allgemein.allgemein_html(kurs, _bunt())
    assert html.startswith(KASTEN)
    kasten = html[:html.index("</div>")]
    assert BLITZ + " Ein neuer Auftrag für den Stromhof</p>" in kasten
    assert "Familie Schütte hat ein Haus gekauft." in kasten
    assert html.count("Familie Schütte hat ein Haus gekauft.") == 1
    assert html.index("</div>") < html.index("<table")          # Steckbrief erst unter dem Kasten
    del kurs["begruessung_titel"]
    html, _ = allgemein.allgemein_html(kurs, _bunt())
    assert BLITZ + " Willkommen</p>" in html


def test_begruessung_blitz_als_symbol():
    """Emoji ignorieren die Schriftfarbe: der Blitz ist ein Font-Awesome-Symbol in Grün."""
    html, _ = allgemein.allgemein_html(_kurs()["kurs"], _bunt())
    assert "⚡" not in html
    assert re.search(r'<i class="fa fa-bolt[^"]*" style="color:#7DDE78;"', html)


def test_logo_karte_ohne_position():
    html, dateien = allgemein.allgemein_html(_kurs()["kurs"], _bunt())
    assert "position:" not in html and "gradient" not in html and "opacity" not in html
    assert dateien == ["bilder/logo.png"]
    karte = html[html.index("</ul>"):]                 # Logo-Karte: alles unter „So arbeiten Sie“
    assert "#D7DFF0" in karte and "border:1px solid #08349C" in karte
    assert 'alt="Logo der Schule" width="180"' in karte
    assert "<b>künstlicher Intelligenz</b>" in karte and "color:#08349C" in karte
    assert karte.index('alt="Logo der Schule"') < karte.index("<b>künstlicher Intelligenz</b>")
    assert re.search(r"margin:[^;\"]*-\d", karte)      # Überlappung nur über negative Ränder
    assert karte.count("<div") == 4 and "<p><img" not in karte    # ein Block, kein loses Logo darunter
    assert html.index("So arbeiten Sie") < html.index("#CDEFCB")      # Karte steht unten


def test_schlicht_wie_bisher():
    assert profilwerte.moodle_profil({})["moodle.allgemein_stil"] == "schlicht"
    kurs = _kurs()["kurs"]
    kurs["begruessung_titel"] = "Ein neuer Auftrag"
    erwartet = ("<p>Familie Schütte hat ein Haus gekauft.</p>"
                '<table class="table"><tbody><tr><th scope="row">Lernfeld</th>'
                "<td>LF 1 Elektrotechnische Systeme analysieren</td></tr>"
                '<tr><th scope="row">Umfang</th><td>8 Unterrichtsstunden</td></tr>'
                '<tr><th scope="row">Ergebnis</th><td>Info-Mappe für Familie Schütte</td></tr>'
                '<tr><th scope="row">Ansprechpartner</th><td>Herr Muster · <a href="mailto:muster@schule.example">'
                "muster@schule.example</a></td></tr></tbody></table>"
                "<h3>So arbeiten Sie in diesem Kurs</h3><ul><li>Jede Kachel gehört zu einer Doppelstunde.</li>"
                "<li>Hilfen holen Sie sich selbst.</li></ul>"
                '<p><img src="logo.png" alt="Logo der Schule" width="180"></p>'
                f"<p>{SATZ}</p>")
    assert allgemein.allgemein_html(kurs, _voll()) == (erwartet, ["bilder/logo.png"])
    leer, _ = allgemein.allgemein_html(kurs, profilwerte.moodle_profil({}))
    assert leer == ("<p>Familie Schütte hat ein Haus gekauft.</p><h3>So arbeiten Sie in diesem Kurs</h3><ul>"
                    "<li>Jede Kachel gehört zu einer Doppelstunde.</li><li>Hilfen holen Sie sich selbst.</li></ul>")


def test_anwenden_setzt_kursschluessel_aus_profil():
    kurs = _kurs()
    allgemein.anwenden(kurs, profilwerte.moodle_profil({}))
    k = kurs["kurs"]
    assert (k["pdf_formular"], k["schilder"], k["zwei_versuche"], k["schrittnummern_mit_kachel"]) == (
        False, False, False, False)
    assert k["sterne_schluessel"] == [] and k["bestehen_prozent"] == 0
    kurs = _kurs()
    allgemein.anwenden(kurs, _profil(**{"moodle.pdf_formular": True, "moodle.schilder": True,
                                        "moodle.tests_zwei_versuche": True, "moodle.schrittnummern_mit_kachel": True,
                                        "moodle.sterne_schluessel": [50, 67, 92], "moodle.bestehen_prozent": 50}))
    k = kurs["kurs"]
    assert (k["pdf_formular"], k["schilder"], k["zwei_versuche"], k["schrittnummern_mit_kachel"]) == (
        True, True, True, True)
    assert k["sterne_schluessel"] == [50, 67, 92] and k["bestehen_prozent"] == 50


def test_zweiter_versuch_ohne_eigene_schrittnummer():
    """Der zweite Versuch gehört zum Schritt des ersten Tests (wie eine Hilfe): keine eigene Nummer, kein
    „Schritt k.n ·“ – gleich, ob das Paar vor oder nach den Schrittnummern eingesetzt wird."""
    import sterne

    def kurs():
        kachel = {"name": "Kachel", "zusammenfassung": "<ol><li>Testen</li><li>Planen</li></ol>",
                  "aktivitaeten": [{"typ": "quiz", "name": "Test", "fragen": [
                      {"typ": "truefalse", "name": "F", "text": "<p>Stimmt das?</p>", "richtig": True}]},
                      {"typ": "page", "name": "Arbeitsplan", "inhalt": "<p>x</p>"}]}
        return {"kurs": {"zwei_versuche": True, "sterne_schluessel": [50, 67, 92], "bestehen_prozent": 50},
                "abschnitte": [kachel]}
    vorher, nachher = kurs(), kurs()
    sterne.paar_einsetzen(vorher, "Test")
    allgemein.schrittnummern(vorher["abschnitte"], mit_kachel=True)
    allgemein.schrittnummern(nachher["abschnitte"], mit_kachel=True)
    sterne.paar_einsetzen(nachher, "Test")
    for k in (vorher, nachher):
        assert [a["name"] for a in k["abschnitte"][0]["aktivitaeten"]] == [
            "Schritt 1.1 · Test", "Test, zweiter Versuch", "Schritt 1.2 · Arbeitsplan"]


# --------------------------------------------------------------------------- #
# Sternzähler (Lehrkraft 2026-10-26): genau eine Aktivität „⭐ Meine Sterne“ (Datenbank mit Skript) in Allgemein.
# --------------------------------------------------------------------------- #
KURSNAME = "EG1 · LF 1 · LS 1 Der Stromhof"


def _sternkurs(n_sterne, schalter=True):
    """Kleinster Kurs mit Kursgesamt-Höchstwert `n_sterne`: ein Test mit so vielen Sternen."""
    return {"kurs": {"vollname": KURSNAME, "kurzname": "STERN", "beschreibung": "<p>Kurs</p>",
                     "ki_hinweis": "Erstellt mit Hilfe von künstlicher Intelligenz",
                     "allgemein": "<div>Willkommen</div>", "sternzaehler": schalter},
            "abschnitte": [{"name": "Kachel", "aktivitaeten": [
                {"typ": "quiz", "name": "Test", "sterne": n_sterne, "fragen": [
                    {"typ": "truefalse", "name": "F", "text": "<p>Stimmt das?</p>", "richtig": True}]}]}]}


def _abschnitt0(ordner):
    """Aktivitäten in Abschnitt 0 als (Ordner, module.xml-Wurzel)."""
    _, sec = _allgemein_summary(ordner)
    folge = ET.parse(ordner / f"sections/section_{sec}/section.xml").getroot().findtext("sequence") or ""
    backup = ET.parse(ordner / "moodle_backup.xml").getroot()
    ordner_je = {a.findtext("moduleid"): a.findtext("directory") for a in backup.iter("activity")}
    return [(ordner / ordner_je[c], ET.parse(ordner / ordner_je[c] / "module.xml").getroot())
            for c in folge.split(",") if c]


def test_sternzaehler_eine_datenbank(tmp_path, dateien):
    import pruefen
    import sternzaehler
    ordner = _bauen(tmp_path, dateien, _sternkurs(26))
    akts = _abschnitt0(ordner)
    assert len(akts) == 1
    d, m = akts[0]
    assert m.findtext("modulename") == "data" and m.findtext("idnumber") == "sternzaehler"
    assert m.findtext("completion") == "0" and m.findtext("availability") == "$@NULL@$"
    h = ET.parse(d / "data.xml").getroot().find("data")
    assert h.findtext("name") == "⭐ Meine Sterne"
    assert sternzaehler.konfig_aus(h.findtext("jstemplate"))["max"] == 26
    assert "mod/data:writeentry" in (d / "roles.xml").read_text()
    assert [b for b in pruefen.p9_sternzaehler(pruefen.Paket(ordner), _sternkurs(26)) if b.stufe == "Fehler"] == []
    assert not list(ordner.glob("activities/label_*"))


def test_sternzaehler_ohne_schalter_nichts(tmp_path, dateien):
    import pruefen
    (tmp_path / "aus").mkdir()
    ordner = _bauen(tmp_path / "aus", dateien, _sternkurs(3, schalter=False))
    assert _abschnitt0(ordner) == []
    befunde = pruefen.p9_sternzaehler(pruefen.Paket(ordner), _sternkurs(3, schalter=False))
    assert befunde == []


def test_sternzaehler_skript_rechnet(tmp_path):
    import shutil
    import subprocess
    if not shutil.which("node"):
        return
    js = Path(__file__).resolve().parents[1] / "sternzaehler.js"
    probe = ("const L=require(%r); const a=[L.sterneAus('15,50',31), L.sterneAus('48,39 %%',31), "
             "L.sterneAus('-',31), L.sterneAus('31,00',31), L.zeile(1,31), L.zahlText(1234)]; "
             "console.log(JSON.stringify(a));" % str(js))
    aus = subprocess.run(["node", "-e", probe], capture_output=True, text=True, check=True).stdout
    assert json.loads(aus) == [15, 15, 0, 31, "⭐ 1 von 31 Sternen", "1.234"]
