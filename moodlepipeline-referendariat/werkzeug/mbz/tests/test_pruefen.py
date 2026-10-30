"""Jeder der neun Prüfer schlägt bei einem absichtlichen Fehler an."""
import copy
import re
import shutil
import xml.etree.ElementTree as ET

import pytest

import bauen
import beispiel
import pruefen
from conftest import akt


def fehler(befunde, nr):
    return [b for b in befunde if b.pruefer == nr and b.stufe == pruefen.FEHLER]


def test_p1_fehlende_datei_im_paket(paket, tmp_path):
    _, ordner, kurs = paket
    kopie = tmp_path / "paket"
    shutil.copytree(ordner, kopie)
    blob = next(p for p in (kopie / "files").rglob("*") if p.is_file())
    blob.unlink()
    assert fehler(pruefen.pruefe(kopie, kurs), 1)


def test_p1_kaputtes_xml_und_falsche_folge(paket, tmp_path):
    _, ordner, kurs = paket
    kopie = tmp_path / "paket"
    shutil.copytree(ordner, kopie)
    (kopie / "groups.xml").write_text("<groups>", encoding="utf-8")
    sec = next(p for p in (kopie / "sections").glob("*/section.xml")
               if "<sequence></sequence>" in p.read_text())
    sec.write_text(sec.read_text().replace("<sequence></sequence>", "<sequence>99999</sequence>"))
    texte = " ".join(b.text for b in fehler(pruefen.pruefe(kopie, kurs), 1))
    assert "kein gültiges XML" in texte and "99999" in texte


def test_p2_lehrkraftbereich_sichtbar(variante):
    def aendern(k):
        k["abschnitte"][-1]["sichtbar"] = True
    assert fehler(variante(aendern), 2)


def test_p2_loesung_sichtbar(variante):
    def aendern(k):
        loesung = akt(k, "Erwartungshorizont Messprotokoll")
        k["abschnitte"][-1]["aktivitaeten"].remove(loesung)
        loesung["sichtbar"] = True
        k["abschnitte"][0]["aktivitaeten"].append(loesung)
    assert any("Lösung" in b.text for b in fehler(variante(aendern), 2))


@pytest.mark.parametrize("formel, plausibel", [("{P}/({U}-230)", None),
                                               ("{P}^2", None),
                                               ("{P}/{U}", [50, 100])])
def test_p3_rechenfrage_rechnet_nicht(variante, formel, plausibel):
    def aendern(k):
        q = next(q for q in akt(k, "Abschlusstest")["fragen"] if q["typ"] == "calculated")
        q["formel"] = formel
        q["plausibel"] = plausibel
    assert fehler(variante(aendern), 3)


def test_p4_leere_seite(variante):
    def aendern(k):
        akt(k, "Infoblatt: Leistung im Haushalt").update(inhalt="<p>&nbsp;</p>", dateien=[])
    assert any("ohne Inhalt" in b.text for b in fehler(variante(aendern), 4))


def test_p4_test_ohne_fragen(paket, tmp_path):
    _, ordner, kurs = paket
    kopie = tmp_path / "paket"
    shutil.copytree(ordner, kopie)
    quiz = next((kopie / "activities").glob("quiz_*")) / "quiz.xml"
    baum = ET.parse(quiz)
    instanzen = baum.getroot().find("quiz/question_instances")
    for i in list(instanzen):
        instanzen.remove(i)
    baum.write(quiz, encoding="UTF-8", xml_declaration=True)
    assert any("ohne Fragen" in b.text for b in fehler(pruefen.pruefe(kopie, kurs), 4))


def test_p5_angekuendigt_aber_fehlt(variante):
    def aendern(k):
        akt(k, "So geht der Abschlusstest")["inhalt"] += \
            "<p>Lesen Sie vorher das „Infoblatt: Spannung im Haus“.</p>"
    assert any("Infoblatt: Spannung" in b.text for b in fehler(variante(aendern), 5))


def test_p6_luecke_zwischen_medaillen(variante):
    def aendern(k):
        akt(k, "Ihre Medaille: Bronze")["voraussetzung"]["min"] = 55
    assert any("Lücke" in b.text for b in fehler(variante(aendern), 6))


def test_p6_mehrere_versuche_und_fehlendes_abzeichen(variante):
    def aendern(k):
        akt(k, "Abschlusstest").update(versuche=0, abschluss="bestanden")
        k["abzeichen"].pop()
    texte = " ".join(b.text for b in fehler(variante(aendern), 6))
    assert "Versuche" in texte and "0 Abzeichen" in texte


def test_p6_gruen_nicht_ab_einem_prozent(variante):
    def aendern(k):
        akt(k, "Ihre Medaille: Grün")["voraussetzung"]["min"] = 10
    assert any("1 %" in b.text for b in fehler(variante(aendern), 6))


def test_p7_bild_ohne_alt(variante):
    def aendern(k):
        a = akt(k, "Infoblatt: Leistung im Haushalt")
        a["inhalt"] = a["inhalt"].replace('alt="Abb. 1: Stromkreisverteiler (eigene Darstellung)"', "")
    assert fehler(variante(aendern), 7)


KACHEL2 = "2 · Erarbeitung: Leistung und Strom"
ABGABEN = ("Auftrag: Messprotokoll Haus Schütte", "Gerätesammlung Haus Schütte", "Auftrag: Skizze Zählerschrank")


def _ohne_abgaben(k):
    ab = next(a for a in k["abschnitte"] if a["name"] == KACHEL2)
    ab["aktivitaeten"] = [a for a in ab["aktivitaeten"] if a["name"] not in ABGABEN]
    return ab


def _p8(befunde):
    return [b.text for b in fehler(befunde, 8)]


def test_p8_kachel_ohne_abgabe(variante):
    texte = _p8(variante(_ohne_abgaben))
    assert len(texte) == 1 and "Erarbeitung" in texte[0], texte


def test_p8_stern_quiz_allein_ist_keine_abgabe(variante):
    import sterne

    def aendern(k):
        ab = _ohne_abgaben(k)
        stern = sterne.stern_aktivitaet(ab, "Abschlusstest", [])
        stern["idnummer"] = "stern-k2"
        ab["aktivitaeten"].append(stern)
    assert _p8(variante(aendern))


def test_p8_test_ohne_sterne_nur_als_eingangstest(variante):
    uebung = {"typ": "quiz", "name": "Übung: Leistung", "sterne": 0, "fragen": [
        {"typ": "truefalse", "name": "Ü1", "text": "<p>P = U · I?</p>", "richtig": True}]}

    def ohne_sterne(k):
        _ohne_abgaben(k)["aktivitaeten"].append(dict(uebung))
    assert _p8(variante(ohne_sterne))

    def mit_sternen(k):
        _ohne_abgaben(k)["aktivitaeten"].append(dict(uebung, sterne=3))
    assert _p8(variante(mit_sternen)) == []

    def eingangstest_ohne_einstieg(k):
        # Einstieg: der Eingangstest (sterne 0) genügt; ohne ihn fehlt die Abgabe
        k["abschnitte"][0]["aktivitaeten"] = [a for a in k["abschnitte"][0]["aktivitaeten"]
                                              if a["typ"] != "quiz"]
    texte = _p8(variante(eingangstest_ohne_einstieg))
    assert len(texte) == 1 and "Einstieg" in texte[0], texte


def test_p8_datenbank_nur_mit_abschluss_eintraege(variante):
    def aendern(k):
        ab = _ohne_abgaben(k)
        ab["aktivitaeten"].append({"typ": "data", "name": "Sammlung", "abschluss": "ansehen",
                                   "felder": [{"name": "Gerät"}]})
    assert _p8(variante(aendern))

    def eintraege(k):
        ab = _ohne_abgaben(k)
        ab["aktivitaeten"].append({"typ": "data", "name": "Sammlung", "abschluss": "eintraege",
                                   "felder": [{"name": "Gerät"}]})
    assert _p8(variante(eintraege)) == []


def test_p8_lehrkraftbereich_ohne_kursdefinition(paket, variante, tmp_path, dateien):
    """Ohne Kursdefinition erkennt Prüfer 8 den Lehrkraftbereich am Namen („Lehrkr…“) und meldet ihn nicht."""
    mbz, _, _ = paket
    assert _p8(pruefen.pruefe(mbz)) == []
    kurs = copy.deepcopy(beispiel.kursdefinition())
    _ohne_abgaben(kurs)
    ziel = tmp_path / "ohne.mbz"
    bauen.baue(kurs, dateien, ziel)
    texte = _p8(pruefen.pruefe(ziel))
    assert len(texte) == 1 and "Erarbeitung" in texte[0], texte


def test_rechne():
    assert pruefen.rechne("{P}/{U}", {"P": 2300, "U": 230}) == pytest.approx(10)
    assert pruefen.rechne("sqrt(pow({a},2))+pi()", {"a": 3}) == pytest.approx(3 + 3.14159265)
    with pytest.raises(ValueError):
        pruefen.rechne("__import__('os')", {})


def _sternzaehler_paket(tmp_path, dateien):
    kurs = copy.deepcopy(beispiel.kursdefinition())
    kurs["kurs"]["sternzaehler"] = True
    ziel = tmp_path / "stern.mbz"
    bauen.baue(kurs, dateien, ziel)
    ordner = pruefen.entpacken(ziel)
    return ordner, kurs


def test_p_sternzaehler_genau_eine_aktivitaet(tmp_path, dateien):
    """Prüfer 9 (Lehrkraft 2026-10-26): genau eine Aktivität „⭐ Meine Sterne“, Höchstwert = Kursgesamt, Lernende
    können nichts anlegen; fehlt sie, ist der Höchstwert falsch oder die Sperre weg: Fehler."""
    import sternzaehler
    ordner, kurs = _sternzaehler_paket(tmp_path, dateien)
    assert fehler(pruefen.pruefe(ordner, kurs), 9) == []
    d = next(m.parent for m in ordner.glob("activities/data_*/module.xml")
             if ET.parse(m).getroot().findtext("idnumber") == sternzaehler.IDNUMMER)

    def kaputt(name, aendern):
        kopie = tmp_path / f"kaputt_{name}"
        shutil.copytree(ordner, kopie)
        aendern(kopie / d.relative_to(ordner))
        return fehler(pruefen.pruefe(kopie, kurs), 9)

    def hoechst(z):
        t = (z / "data.xml").read_text(encoding="utf-8")
        neu = re.sub(r'("max"|&quot;max&quot;): (\d+)', lambda m: f"{m.group(1)}: {int(m.group(2)) + 2}", t, count=1)
        assert neu != t
        (z / "data.xml").write_text(neu, encoding="utf-8")

    def offen(z):
        t = (z / "roles.xml").read_text(encoding="utf-8")
        (z / "roles.xml").write_text(t.replace("mod/data:writeentry", "mod/data:viewentry"), encoding="utf-8")
    assert kaputt("hoechst", hoechst)
    assert kaputt("offen", offen)
    ohne = copy.deepcopy(kurs)
    ohne["kurs"]["sternzaehler"] = False
    ziel = tmp_path / "ohne.mbz"
    bauen.baue(ohne, dateien, ziel)
    assert fehler(pruefen.pruefe(ziel, kurs), 9)        # Schalter an, aber keine Aktivität
