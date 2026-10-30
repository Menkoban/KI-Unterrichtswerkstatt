"""Abgabe ohne Note und Datenbank (mod_data): Schema, Bau, Prüfer."""
import copy
import xml.etree.ElementTree as ET

import beispiel
import kursdefinition as kd
from conftest import akt

OHNE_NOTE = "Auftrag: Skizze Zählerschrank"
DATENBANK = "Gerätesammlung Haus Schütte"


def ordner_von(ordner, name):
    """Aktivitätsordner im entpackten Paket nach Titel."""
    root = ET.parse(ordner / "moodle_backup.xml").getroot()
    d = next(a.findtext("directory") for a in root.iter("activity")
             if a.findtext("title") == name)
    return ordner / d


def kurs_mit(aendern):
    kurs = copy.deepcopy(beispiel.kursdefinition())
    aendern(kurs)
    return kd.pruefe(kurs)


# -- Abgabe ohne Note ------------------------------------------------------ #
def test_abgabe_ohne_note_hat_keine_bewertung(paket):
    _, ordner, _ = paket
    d = ordner_von(ordner, OHNE_NOTE)
    a = ET.parse(d / "assign.xml").getroot().find("assign")
    assert a.findtext("grade") == "0"
    assert a.findtext("completionsubmit") == "1"
    # Moodle 5.1 braucht ein Grade Item (sonst „Cannot load the grade item“): Typ Text, nie im Kursgesamt;
    # dafür sind die Feedback-Kommentare an (so legt Moodle es selbst an)
    feedback = [c for c in a.iter("plugin_config")
                if c.findtext("subtype") == "assignfeedback" and c.findtext("name") == "enabled"]
    assert feedback and all(c.findtext("value") == "1" for c in feedback)
    items = list(ET.parse(d / "grades.xml").getroot().iter("grade_item"))
    assert [i.findtext("gradetype") for i in items] == ["3"]
    assert "grade_itemref" in (d / "inforef.xml").read_text()
    m = ET.parse(d / "module.xml").getroot()
    assert m.findtext("completion") == "2"
    assert m.findtext("completiongradeitemnumber") == "$@NULL@$"


def test_abgabe_mit_note_bleibt_wie_bisher(paket):
    _, ordner, _ = paket
    d = ordner_von(ordner, "Auftrag: Messprotokoll Haus Schütte")
    assert ET.parse(d / "assign.xml").getroot().findtext("assign/grade") == "10"
    assert len(list(ET.parse(d / "grades.xml").getroot().iter("grade_item"))) == 1


def test_kursnote_ohne_abgabe_ohne_note(paket):
    _, ordner, _ = paket
    kurs_item = ET.parse(ordner / "gradebook.xml").getroot().find("grade_items/grade_item")
    assert float(kurs_item.findtext("grademax")) == 20.0     # Test 10 + Raster 10


def test_bewertung_keine_verbietet_punkte_und_note():
    def aendern(k):
        akt(k, OHNE_NOTE).update(punkte=10, bewertungsraster=[
            {"kriterium": "x", "punkte": 1}], abschluss="note")
    texte = " ".join(kurs_mit(aendern))
    assert "kein punkte" in texte and "kein bewertungsraster" in texte
    assert "„note“" in texte


def test_bewertung_unbekannt_und_voraussetzung_auf_note():
    def aendern(k):
        akt(k, "Auftrag: Messprotokoll Haus Schütte")["bewertung"] = "sterne"
        akt(k, "Hinweis Teamarbeit")["voraussetzung"] = {"aktivitaet": OHNE_NOTE, "min": 50}
    texte = " ".join(kurs_mit(aendern))
    assert "sterne" in texte and "wird nicht bewertet" in texte


def test_abschluss_abgabe_und_abgeben_gleich():
    assert kd.abschluss_von({"typ": "assign", "abschluss": "abgabe"}) == "abgeben"
    assert kd.abschluss_von({"typ": "assign"}) == "abgeben"


# -- Datenbank ------------------------------------------------------------- #
def test_datenbank_xml(paket):
    _, ordner, _ = paket
    d = ordner_von(ordner, DATENBANK)
    for datei in ("data.xml", "module.xml", "inforef.xml", "grades.xml", "roles.xml",
                  "filters.xml", "calendar.xml", "grade_history.xml"):
        assert (d / datei).is_file(), datei
    root = ET.parse(d / "data.xml").getroot()
    assert root.get("modulename") == "data"
    data = root.find("data")
    assert data.findtext("assessed") == "0" and data.findtext("scale") == "0"
    assert data.findtext("completionentries") == "1"
    felder = data.findall("fields/field")
    assert [f.findtext("type") for f in felder] == ["text", "number", "textarea"]
    assert [f.findtext("required") for f in felder] == ["1", "1", "0"]
    assert all(f.find("param10") is not None for f in felder)
    assert data.find("records") is not None
    assert not list(ET.parse(d / "grades.xml").getroot().iter("grade_item"))
    m = ET.parse(d / "module.xml").getroot()
    assert m.findtext("modulename") == "data" and m.findtext("completion") == "2"


def test_datenbank_vorlagen_als_tabelle(paket):
    _, ordner, _ = paket
    data = ET.parse(ordner_von(ordner, DATENBANK) / "data.xml").getroot().find("data")
    kopf, zeile, fuss = (data.findtext(t) for t in
                         ("listtemplateheader", "listtemplate", "listtemplatefooter"))
    assert kopf.startswith("<table") and "<th>Leistung in W</th>" in kopf
    assert zeile.startswith("<tr>") and "[[Gerät]]" in zeile and "##actionsmenu##" in zeile
    assert fuss == "</tbody></table>"
    # zusammengesetzt wohlgeformt (zwei Einträge)
    ET.fromstring(kopf + zeile + zeile + fuss)
    eingabe = data.findtext("addtemplate")
    for n in ("Gerät", "Leistung in W", "Bemerkung"):
        assert f"[[{n}]]" in eingabe and f"[[{n}]]" in data.findtext("singletemplate")
    assert "[[Gerät#id]]" in eingabe and "vom Typenschild" in eingabe


def test_datenbank_abschlussarten(variante, paket):
    def aendern(k):
        akt(k, DATENBANK).update(abschluss="ansehen")
        del akt(k, DATENBANK)["eintraege_fuer_abschluss"]
    assert not [b for b in variante(aendern) if b.stufe == "Fehler"]
    assert kd.ABSCHLUSS["data"] == ("eintraege", "ansehen", "manuell", "keine")


def test_datenbank_formfehler():
    def aendern(k):
        akt(k, DATENBANK).update(
            felder=[{"name": "Gerät"}, {"name": "gerät", "typ": "datum"},
                    {"name": "[[x]]"}, {"typ": "text"}],
            eintraege_fuer_abschluss=0)
    texte = " ".join(kurs_mit(aendern))
    for erwartet in ("doppelt", "datum", "kein [, ] oder #", "ohne name", "≥ 1"):
        assert erwartet in texte, erwartet


def test_datenbank_ohne_felder_und_falscher_abschluss():
    def aendern(k):
        akt(k, DATENBANK).update(felder=[], abschluss="abgeben")
    texte = " ".join(kurs_mit(aendern))
    assert "felder fehlt" in texte and "geht bei data nicht" in texte
    def aendern2(k):
        akt(k, DATENBANK)["abschluss"] = "manuell"
    assert any("eintraege_fuer_abschluss wirkt nur" in t for t in kurs_mit(aendern2))


def test_p4_datenbank_ohne_felder(paket, tmp_path):
    import shutil
    import pruefen
    _, ordner, kurs = paket
    kopie = tmp_path / "paket"
    shutil.copytree(ordner, kopie)
    datei = ordner_von(kopie, DATENBANK) / "data.xml"
    baum = ET.parse(datei)
    felder = baum.getroot().find("data/fields")
    for f in list(felder):
        felder.remove(f)
    baum.write(datei, encoding="UTF-8", xml_declaration=True)
    assert any("ohne Felder" in b.text for b in pruefen.pruefe(kopie, kurs)
               if b.pruefer == 4 and b.stufe == pruefen.FEHLER)


# -- Rückschau ohne richtige Antwort (Eingangstest) ------------------------ #
def test_richtige_antwort_verbergen(tmp_path, dateien):
    import tarfile
    import bauen
    kurs = copy.deepcopy(beispiel.kursdefinition())
    test = next(a for ab in kurs["abschnitte"] for a in ab["aktivitaeten"] if a["typ"] == "quiz")
    test["richtige_antwort_zeigen"] = False
    ziel = tmp_path / "k.mbz"
    bauen.baue(kurs, dateien, ziel)
    with tarfile.open(ziel, "r:gz") as tar:
        tar.extractall(tmp_path / "x", filter="data")
    quiz = ET.parse(ordner_von(tmp_path / "x", test["name"]) / "quiz.xml").getroot().find(".//quiz")
    assert quiz.findtext("reviewrightanswer") == "0"
    assert quiz.findtext("reviewspecificfeedback") != "0"


def test_dekoratives_bild_mit_leerem_alt(variante):
    def aendern(kurs):
        seite = next(a for ab in kurs["abschnitte"] for a in ab["aktivitaeten"] if a["typ"] == "page")
        seite["inhalt"] += '<p><img src="x.png" alt="" role="presentation"></p><p><img src="y.png" alt=""></p>'
    befunde = [b for b in variante(aendern) if b.pruefer == 7]
    assert len(befunde) == 1 and "y.png" in befunde[0].text


def test_abschnitt_allgemein_mit_text(tmp_path, dateien):
    import tarfile
    import bauen
    kurs = copy.deepcopy(beispiel.kursdefinition())
    kurs["kurs"]["allgemein"] = "<p>Willkommen bei Familie Schütte.</p>"
    kurs["kurs"]["format"] = "tiles"
    ziel = tmp_path / "k.mbz"
    bauen.baue(kurs, dateien, ziel)
    with tarfile.open(ziel, "r:gz") as tar:
        tar.extractall(tmp_path / "x", filter="data")
    texte = [ET.parse(s).getroot() for s in (tmp_path / "x" / "sections").glob("*/section.xml")]
    null = next(s for s in texte if s.findtext("number") == "0")
    assert "Willkommen" in null.findtext("summary")
    assert ET.parse(tmp_path / "x" / "course" / "course.xml").getroot().findtext("format") == "tiles"


# -- Freigabe durch die Lehrkraft, Glossar nur zum Nachschlagen (Rückmeldung LS 1) -------------------------- #
def _gebaut(tmp_path, dateien, aendern):
    import tarfile
    import bauen
    kurs = copy.deepcopy(beispiel.kursdefinition())
    aendern(kurs)
    assert kd.pruefe(kurs) == []
    ziel = tmp_path / "k.mbz"
    bauen.baue(kurs, dateien, ziel)
    ordner = tmp_path / "entpackt"
    with tarfile.open(ziel, "r:gz") as tar:
        tar.extractall(ordner, filter="data")
    return ordner


def test_datenbank_freigabe_durch_lehrkraft(tmp_path, dateien, paket):
    _, vorher, _ = paket
    assert ET.parse(ordner_von(vorher, DATENBANK) / "data.xml").getroot().findtext("data/approval") == "0"
    ordner = _gebaut(tmp_path, dateien, lambda k: akt(k, DATENBANK).update(freigabe=True))
    assert ET.parse(ordner_von(ordner, DATENBANK) / "data.xml").getroot().findtext("data/approval") == "1"
    assert any("freigabe" in f for f in kurs_mit(lambda k: akt(k, DATENBANK).update(freigabe="ja")))


def _glossar(kurs):
    return next(a for ab in kurs["abschnitte"] for a in ab["aktivitaeten"] if a["typ"] == "glossary")


def test_glossar_nur_zum_nachschlagen(tmp_path, dateien, paket):
    """Lernende dürfen keine Einträge anlegen: Rechte-Änderung mod/glossary:write für die Rolle Student
    (Moodle kennt dafür keine Glossar-Einstellung); die Sicherung muss Rechte-Änderungen mitbringen."""
    _, vorher, kurs = paket
    name = _glossar(kurs)["name"]
    assert "<override" not in (ordner_von(vorher, name) / "roles.xml").read_text(encoding="utf-8")
    ordner = _gebaut(tmp_path, dateien, lambda k: _glossar(k).update(nur_lesen=True))
    rollen = ET.parse(ordner_von(ordner, name) / "roles.xml").getroot()
    (o,) = rollen.findall("role_overrides/override")
    assert (o.findtext("roleid"), o.findtext("capability"), o.findtext("permission")) == \
        ("5", "mod/glossary:write", "-1")
    wurzel = {s.findtext("name"): s.findtext("value")
              for s in ET.parse(ordner / "moodle_backup.xml").getroot().iter("setting")
              if s.findtext("level") == "root"}
    assert wurzel["permissions"] == "1"
    # Ohne Verweis auf die Rolle im inforef ordnet Moodle sie beim Einspielen nicht zu und verwirft die Änderung
    # still (gemessen in der Spielwiese 5.1.6, 2026-10-22)
    ref = ET.parse(ordner_von(ordner, name) / "inforef.xml").getroot()
    assert [i.text for i in ref.findall("roleref/role/id")] == ["5"]
    assert any("nur_lesen" in f for f in kurs_mit(lambda k: _glossar(k).update(nur_lesen=1)))


# -- Feedback ohne Kennzeichnung und ohne „Nicht gewählt“ (Durchsicht LS 1, 2026-10-23) ---------------------- #
def test_feedback_ohne_kennzeichnung_und_nicht_gewaehlt(paket):
    _, ordner, _ = paket
    items = ET.parse(ordner_von(ordner, "Selbsteinschätzung vorher") / "feedback.xml").getroot().iter("item")
    nach_typ = {}
    for i in items:
        assert i.findtext("label") == ""
        nach_typ.setdefault(i.findtext("typ"), []).append(i.findtext("options"))
    assert nach_typ["multichoice"] == ["h", "h"]
    assert nach_typ["textfield"] == [""]


def test_hinweise_je_frage():
    """Hinweise je Frage (interactive): question_hints im Paket, leere Hinweise sind ein Formfehler."""
    import kursdefinition as kd
    q = {"typ": "calculated", "name": "H", "text": "<p>{a} V</p>", "formel": "{a}*2",
         "variablen": [{"name": "a", "min": 1, "max": 5}], "hinweise": ["<p>Erst die Formel.</p>"]}
    assert kd.pruefe_frage(q) == []
    assert kd.pruefe_frage(dict(q, hinweise=[""])) != []

    class B:
        n = 0
        def ids(self, _):
            B.n += 1
            return B.n
    import fragen
    xml = fragen._hinweise(B(), q)
    assert "<hint>&lt;p&gt;Erst die Formel.&lt;/p&gt;</hint>" in xml and "<clearwrong>0</clearwrong>" in xml


def test_alt_aus_bildunterschrift():
    """Bild ohne Beschreibung in Word, aber mit „Abb. …“ darunter: die Unterschrift wird der alt-Text."""
    import docx_seite
    html = ('<p><img src="@@PLUGINFILE@@/a.png" alt="" role="presentation" style="x" /></p>'
            '<p><b>Abb. 2.1</b> Schnitt durch den Fußboden</p><p><img src="@@PLUGINFILE@@/b.png" alt="" '
            'role="presentation" style="x" /></p><p>Zierleiste</p>')
    aus = docx_seite.alt_aus_unterschrift(html)
    assert 'alt="Abb. 2.1 Schnitt durch den Fußboden"' in aus
    assert aus.count('alt=""') == 1          # das zweite Bild bleibt Schmuck


def test_verweise_und_bild_mit_unterschrift(tmp_path):
    """Prüfer 1: relativer Bildpfad und Link im Link; Prüfer 7: Schmuckbild mit Bildunterschrift."""
    import xml.etree.ElementTree as ET
    import pruefen

    class P:
        def alle_xml(self):
            w = ET.fromstring("<page><content>" + __import__("html").escape(
                '<img src="3/bild.svg" alt="x"><a href="<a href=\'https://x.de\'>x.de</a>">t</a>'
                '<img src="@@PLUGINFILE@@/c.png" alt="" role="presentation"><p>Abb. 5.1 Plan</p>')
                + "</content><jstemplate>var s = '&lt;img src=\"a.png\"&gt;';</jstemplate></page>")
            yield "activities/page_1/page.xml", w
    befunde = pruefen.verweis_befunde(P())
    assert any("ohne @@PLUGINFILE@@" in b for b in befunde)
    assert any("ungültiger Link" in b or "Link im Link" in b for b in befunde)
    assert not any("a.png" in b for b in befunde)        # Skriptvorlage zählt nicht
    assert any("Schmuck" in b.text for b in pruefen.p7_alt(P(), None))


def test_glossar_eintrag_ohne_autoverlinkung(tmp_path):
    """Ein Glossareintrag mit autoverlinkung false wird nicht automatisch verlinkt (usedynalink 0)."""
    import copy
    import tarfile
    import bauen
    import beispiel
    k = copy.deepcopy(beispiel.kursdefinition())
    gl = next(a for ab in k["abschnitte"] for a in ab["aktivitaeten"] if a["typ"] == "glossary")
    gl["eintraege"][0]["autoverlinkung"] = False
    wurzel = tmp_path / "d"
    beispiel.dateien_anlegen(wurzel)
    ziel = tmp_path / "k.mbz"
    bauen.baue(k, wurzel, ziel)
    with tarfile.open(ziel) as t:
        xml = next(t.extractfile(m).read().decode() for m in t.getmembers() if m.name.endswith("glossary.xml"))
    assert "<usedynalink>0</usedynalink>" in xml.split("<entries>")[1].split("</entry>")[0]


def test_moodle_knoepfe_sind_keine_ankuendigung():
    import pruefen
    assert "aufgabe abgeben" in pruefen.MOODLE_KNOEPFE and pruefen._name("Aufgabe  abgeben") in pruefen.MOODLE_KNOEPFE
