"""Sterne als Kurswährung: Kursgesamt, Selbstlöse-Stern je Kachel, Medaillen."""
import json
import tarfile
import xml.etree.ElementTree as ET

import bauen
import beispiel
import kursdefinition as kd
import pruefen
import sterne

GRENZEN = [1, 50, 81, 92]
FRAGE = {"typ": "multichoice", "name": "F1", "text": "<p>Was misst ein Zähler?</p>",
         "antworten": [{"text": "Energie", "richtig": True}, {"text": "Spannung"}]}


def sternkurs(grenzen=GRENZEN) -> dict:
    """Zwei Kacheln (Test mit Sternen, Hilfekarte, Stern-Quiz), Eingangstest
    ohne Sterne und Medaillenseiten auf Kursgesamt."""
    abschnitte = [{"name": "Start", "aktivitaeten": [
        {"typ": "quiz", "name": "Eingangstest", "sterne": 0, "fragen": [FRAGE]}]}]
    for n in (1, 2):
        kachel = {"name": f"{n} · Kachel {n}", "zusammenfassung": "<p>Auftrag</p>"}
        hilfe = sterne.hilfekarte(f"Hilfekarte {n}", "<p>Ein Tipp.</p>")
        test = {"typ": "quiz", "name": f"Kacheltest {n}", "sterne": 3, "fragen": [FRAGE]}
        kachel["aktivitaeten"] = [hilfe, test,
                                  sterne.stern_aktivitaet(kachel, test["name"], [hilfe["name"]])]
        abschnitte.append(kachel)
    bilder = {n: {"dateien": [f"abzeichen/{beispiel.dateiname(n)}.png"]} for n in sterne.MEDAILLEN}
    abschluss = {"typ": "quiz", "name": "Abschlusstest", "sterne": 10, "versuche": 1,
                 "abschluss": "note", "fragen": [FRAGE]}
    abschnitte.append({"name": "Rückblick", "aktivitaeten": [
        abschluss, *sterne.medaillen_seiten(grenzen, bilder, nach="Abschlusstest")]})
    return {"kurs": {"vollname": "Sternprobe", "kurzname": "STERNE",
                     "beschreibung": "<p>Probe</p>",
                     "ki_hinweis": "Mit Hilfe von künstlicher Intelligenz erstellt"},
            "abschnitte": abschnitte,
            "abzeichen": [{"name": f"Medaille {n}", "bild": f"abzeichen/{beispiel.dateiname(n)}.png",
                           "aktivitaet": f"Ihre Medaille: {n}"} for n in sterne.MEDAILLEN]}


def gebaut(tmp_path, dateien, kurs):
    assert kd.pruefe(kurs) == []
    mbz = tmp_path / "sterne.mbz"
    bauen.baue(kurs, dateien, mbz)
    ordner = tmp_path / "entpackt"
    with tarfile.open(mbz, "r:gz") as tar:
        tar.extractall(ordner, filter="data")
    return ordner


def items(ordner):
    """Name → grade_item aus den grades.xml der Aktivitäten (gleiche Namen: Liste)."""
    root = ET.parse(ordner / "moodle_backup.xml").getroot()
    aus: dict[str, list] = {}
    for a in root.iter("activity"):
        if not a.findtext("directory"):
            continue
        g = ET.parse(ordner / a.findtext("directory") / "grades.xml").getroot()
        for gi in g.iter("grade_item"):
            aus.setdefault(a.findtext("title"), []).append(gi)
    return aus


def kurs_item(ordner):
    gb = ET.parse(ordner / "gradebook.xml").getroot()
    return next(gi for gi in gb.iter("grade_item") if gi.findtext("itemtype") == "course")


def test_kursgesamt_ist_summe_der_sterne(tmp_path, dateien):
    ordner = gebaut(tmp_path, dateien, sternkurs())
    # 2 Kacheltests × 3 + 2 Stern-Quiz × 1 + Abschlusstest 10; Eingangstest (sterne 0) zählt nicht
    assert float(kurs_item(ordner).findtext("grademax")) == 18
    it = items(ordner)
    assert float(it["Kacheltest 1"][0].findtext("grademax")) == 3
    assert [float(gi.findtext("grademax")) for gi in it[sterne.STERN_NAME]] == [1, 1]


def test_quiz_mit_null_sternen_zaehlt_nicht_im_kursgesamt(tmp_path, dateien):
    ordner = gebaut(tmp_path, dateien, sternkurs())
    ein = items(ordner)["Eingangstest"][0]
    assert ein.findtext("weightoverride") == "1"
    assert float(ein.findtext("aggregationcoef2")) == 0
    # Die gezählten behalten das automatische Gewicht
    assert items(ordner)["Kacheltest 1"][0].findtext("weightoverride") == "0"


def test_nur_bewertete_aspekte_ist_aus(tmp_path, dateien):
    """Sonst rechnet Moodle nur mit dem schon Bewerteten: nach dem ersten
    Test stünde Kursgesamt bei 100 % (Gold)."""
    ordner = gebaut(tmp_path, dateien, sternkurs())
    gb = ET.parse(ordner / "gradebook.xml").getroot()
    assert [k.findtext("aggregateonlygraded") for k in gb.iter("grade_category")] == ["0"]


def test_stern_quiz_form():
    kachel = {"name": "1 · Einstieg"}
    q = sterne.stern_aktivitaet(kachel, "Abgabe", ["Hilfekarte A", "Hilfekarte B"])
    assert q["typ"] == "quiz" and q["name"] == "Ihr Stern: selbst gelöst"
    assert q["sterne"] == 1
    (frage,) = q["fragen"]
    assert frage["typ"] == "multichoice"
    assert [a["text"] for a in frage["antworten"]] == ["Stern abholen"]
    assert kd.pruefe_frage(frage) == []
    assert q["voraussetzung"] == [
        {"abschluss": "Abgabe", "zustand": "abgeschlossen"},
        {"abschluss": "Hilfekarte A", "zustand": "nicht_abgeschlossen"},
        {"abschluss": "Hilfekarte B", "zustand": "nicht_abgeschlossen"}]


def test_stern_quiz_bedingung_hat_e_null_je_hilfe(tmp_path, dateien):
    ordner = gebaut(tmp_path, dateien, sternkurs())
    root = ET.parse(ordner / "moodle_backup.xml").getroot()
    cm = {a.findtext("title"): a for a in root.iter("activity") if a.findtext("directory")}
    sterne_quiz = [a for a in root.iter("activity") if a.findtext("title") == sterne.STERN_NAME]
    assert len(sterne_quiz) == 2
    for n, a in enumerate(sterne_quiz, start=1):
        m = ET.parse(ordner / a.findtext("directory") / "module.xml").getroot()
        v = json.loads(m.findtext("availability"))
        assert v["op"] == "&"
        assert v["c"] == [
            {"type": "completion", "cm": int(cm[f"Kacheltest {n}"].findtext("moduleid")), "e": 1},
            {"type": "completion", "cm": int(cm[f"Hilfekarte {n}"].findtext("moduleid")), "e": 0}]


def test_hilfekarte_wird_beim_ansehen_abgeschlossen():
    h = sterne.hilfekarte("Tipp: Was ist was?", "<p>Tipp</p>")
    assert h["typ"] == "page" and kd.abschluss_von(h) == "ansehen"
    assert h["rolle"] == "hilfe" and sterne.ist_hilfe(h)


def test_erkennung_per_rolle_nicht_per_name():
    """Hilfen und Stern-Quiz erkennt man an der Rolle (oder der ID-Nummer im Paket), nicht am Anzeigenamen –
    Schrittnummern ändern die Namen."""
    stern = sterne.stern_aktivitaet({"name": "2 · Kachel"}, "Test", [])
    assert stern["rolle"] == "stern" and sterne.ist_stern(stern) and not sterne.ist_hilfe(stern)
    umbenannt = dict(stern, name="Schritt 9 · etwas anderes")
    assert sterne.ist_stern(umbenannt)
    assert not sterne.ist_hilfe({"typ": "page", "name": "Hilfekarte Systemebenen", "inhalt": "<p>x</p>"})
    assert not sterne.ist_stern({"typ": "quiz", "name": sterne.STERN_NAME, "fragen": []})
    assert sterne.ist_hilfe({"typ": "page", "name": "x", "idnummer": "hilfe-k2-s3"})
    assert sterne.ist_stern({"typ": "quiz", "name": "x", "idnummer": "stern-k4"})
    assert kd.pruefe(sternkurs()) == []


def test_idnummern_je_kachel_und_schritt():
    """stern-k<n>, hilfe-k<n>-s<m>; n zählt die Kacheln wie die Kachelnummern (Lehrkraftbereich ohne), m ist der
    Schritt, unter dem die Hilfe steht; mehrere Hilfen an einem Schritt bekommen -1, -2 …"""
    def seite(name):
        return {"typ": "page", "name": name, "inhalt": "<p>x</p>"}
    k1 = {"name": "Einstieg", "aktivitaeten": [seite("A")]}
    lehr = {"name": "Material", "lehrkraft": True, "aktivitaeten": [seite("L")]}
    k2 = {"name": "Kachel", "aktivitaeten": [
        seite("S1"), sterne.hilfekarte("H1", "<p>x</p>"), seite("S2"),
        sterne.hilfekarte("H2a", "<p>x</p>"), sterne.hilfekarte("H2b", "<p>x</p>"), seite("S3")]}
    k2["aktivitaeten"].append(sterne.stern_aktivitaet(k2, "S3", ["H1", "H2a", "H2b"]))
    abschnitte = [k1, lehr, k2]
    sterne.idnummern(abschnitte)
    assert [a.get("idnummer") for a in k2["aktivitaeten"]] == [
        None, "hilfe-k2-s1", None, "hilfe-k2-s2-1", "hilfe-k2-s2-2", None, "stern-k2"]
    assert "idnummer" not in k1["aktivitaeten"][0] and "idnummer" not in lehr["aktivitaeten"][0]
    sterne.idnummern(abschnitte)            # zweimal ändert nichts
    assert k2["aktivitaeten"][-1]["idnummer"] == "stern-k2"


def test_hilfe_vor_dem_ersten_schritt_wird_abgelehnt():
    k = {"name": "Kachel", "aktivitaeten": [sterne.hilfekarte("H", "<p>x</p>"),
                                            {"typ": "page", "name": "S1", "inhalt": "<p>x</p>"}]}
    try:
        sterne.idnummern([k])
    except ValueError as e:
        assert "H" in str(e)
    else:
        raise AssertionError("Hilfe ohne Schritt davor muss abgelehnt werden")


def test_medaillen_bereiche_lueckenlos_gold_bis_100():
    seiten = sterne.medaillen_seiten(GRENZEN)
    assert [s["name"] for s in seiten] == [f"Ihre Medaille: {n}" for n in sterne.MEDAILLEN]
    assert [s["voraussetzung"] for s in seiten] == [
        [{"bewertung": "kursgesamt", "min": 1, "max": 50}],
        [{"bewertung": "kursgesamt", "min": 50, "max": 81}],
        [{"bewertung": "kursgesamt", "min": 81, "max": 92}],
        [{"bewertung": "kursgesamt", "min": 92}]]
    assert all(kd.abschluss_von(s) == "ansehen" and s["medaille"] for s in seiten)


def test_medaillen_erst_nach_dem_abschlusstest():
    seiten = sterne.medaillen_seiten(GRENZEN, nach="Abschlusstest")
    # „bewertet (ab 0 %)“ statt „abgeschlossen“: mit Bestehensgrenze ist ein nicht bestandener Test „abgeschlossen,
    # nicht bestanden“ und erfüllt „abgeschlossen“ nicht (gemessen in der Spielwiese 5.1.6, 2026-10-22)
    assert seiten[0]["voraussetzung"] == [{"bewertung": "kursgesamt", "min": 1, "max": 50},
                                          {"aktivitaet": "Abschlusstest", "min": 0,
                                           "sichtbar_wenn_gesperrt": False}]
    assert all(s["voraussetzung"][-1]["aktivitaet"] == "Abschlusstest" for s in seiten)


def test_pruefer_ohne_befund_bei_kursgesamt_medaillen(tmp_path, dateien):
    ordner = gebaut(tmp_path, dateien, sternkurs())
    fehler = [b for b in pruefen.pruefe(ordner, sternkurs())
              if b.stufe == pruefen.FEHLER and b.pruefer in (1, 6)]
    assert fehler == []


def test_p6_meldet_luecke_zwischen_50_und_81(tmp_path, dateien):
    kurs = sternkurs()
    bronze = next(a for ab in kurs["abschnitte"] for a in ab["aktivitaeten"]
                  if a["name"] == "Ihre Medaille: Bronze")
    bronze["voraussetzung"][0]["max"] = 60
    ordner = gebaut(tmp_path, dateien, kurs)
    texte = [b.text for b in pruefen.pruefe(ordner, kurs)
             if b.pruefer == 6 and b.stufe == pruefen.FEHLER]
    assert any("Lücke" in t and "60" in t and "81" in t for t in texte), texte


def test_p6_liest_ganze_liste_und_nimmt_kursgesamt(tmp_path, dateien):
    """Medaillenseite mit weiteren Bedingungen davor: gezählt wird der
    Kursgesamt-Bereich, gesperrt sichtbare Abschluss-Bedingungen stören nicht."""
    kurs = sternkurs()
    for ab in kurs["abschnitte"]:
        for a in ab["aktivitaeten"]:
            if a.get("medaille"):
                # eine Bewertungsbedingung vor dem Kursgesamt-Bereich (ab 0 %: Mindestwerte meldet Prüfer 6)
                a["voraussetzung"] = [{"abschluss": "Kacheltest 2"},
                                      {"aktivitaet": "Abschlusstest", "min": 0},
                                      *a["voraussetzung"]]
    ordner = gebaut(tmp_path, dateien, kurs)
    assert [b for b in pruefen.pruefe(ordner, kurs) if b.pruefer == 6] == []


def test_sterne_formfehler():
    def fehler(**felder):
        kurs = sternkurs()
        kurs["abschnitte"][0]["aktivitaeten"][0].update(felder)
        return [s for s in kd.pruefe(kurs) if "sterne" in s]
    assert fehler(sterne=-1) and fehler(sterne=2.5) and fehler(sterne=True)
    assert fehler(sterne=2, punkte=10)
    assert fehler(typ="page", inhalt="<p>x</p>", sterne=1)
    assert fehler(sterne=0, punkte=10) == []


def _medaillen(kurs):
    return [a for ab in kurs["abschnitte"] for a in ab["aktivitaeten"] if a.get("medaille")]


def test_p6_kursgesamt_ohne_abschlusstest_bedingung(tmp_path, dateien):
    """Medaillen auf Kursgesamt öffnen sich erst nach dem Abschlusstest (Lehrkraft 2026-10-22)."""
    kurs = sternkurs()
    for a in _medaillen(kurs):
        a["voraussetzung"] = a["voraussetzung"][:1]
    ordner = gebaut(tmp_path, dateien, kurs)
    texte = [b.text for b in pruefen.pruefe(ordner, kurs) if b.pruefer == 6 and b.stufe == pruefen.FEHLER]
    assert len([t for t in texte if "Abschlusstest" in t]) == 4, texte


def _abgeschlossen_statt_bewertet(kurs, **test):
    for a in _medaillen(kurs):
        a["voraussetzung"][-1] = {"abschluss": "Abschlusstest", "zustand": "abgeschlossen"}
    next(a for ab in kurs["abschnitte"] for a in ab["aktivitaeten"] if a["name"] == "Abschlusstest").update(test)
    return kurs


def test_p6_abschlusstest_mit_bestehensgrenze_und_bedingung_abgeschlossen(tmp_path, dateien):
    """Wer den Abschlusstest nicht besteht, ist „abgeschlossen, nicht bestanden“ und erfüllt „abgeschlossen“ nicht –
    dann bekäme er gar keine Medaille (gemessen: Abschluss „note“ mit Bestehensgrenze genügt dafür)."""
    for test in ({"bestehensgrenze_prozent": 50},
                 {"abschluss": "bestanden_oder_versuche", "bestehensgrenze_prozent": 50}):
        kurs = _abgeschlossen_statt_bewertet(sternkurs(), **test)
        ordner = gebaut(tmp_path / str(len(test)), dateien, kurs)
        texte = [b.text for b in pruefen.pruefe(ordner, kurs) if b.pruefer == 6 and b.stufe == pruefen.FEHLER]
        assert any("bestanden" in t for t in texte), texte


def test_p6_bedingung_abgeschlossen_ohne_bestehensgrenze_genuegt(tmp_path, dateien):
    kurs = _abgeschlossen_statt_bewertet(sternkurs())
    ordner = gebaut(tmp_path, dateien, kurs)
    assert [b for b in pruefen.pruefe(ordner, kurs) if b.pruefer == 6] == []


def test_medaille_vor_dem_abschlusstest_ganz_verborgen(tmp_path, dateien):
    """Sonst stünde die passende Medaille vorab ausgegraut im Kurs und verriete die Stufe."""
    ordner = gebaut(tmp_path, dateien, sternkurs())
    root = ET.parse(ordner / "moodle_backup.xml").getroot()
    for a in root.iter("activity"):
        if (a.findtext("title") or "").startswith("Ihre Medaille"):
            v = json.loads(ET.parse(ordner / a.findtext("directory") / "module.xml").getroot().findtext("availability"))
            assert v["showc"] == [False, False], v


def test_p6_abschlusstest_bedingung_mit_mindestwert(tmp_path, dateien):
    """„Abschlusstest bewertet“ heißt ab 0 %; ein Mindestwert sperrte schwache Lernende ganz von der Medaille aus."""
    kurs = sternkurs()
    for a in _medaillen(kurs):
        a["voraussetzung"][-1] = {"aktivitaet": "Abschlusstest", "min": 50}
    ordner = gebaut(tmp_path, dateien, kurs)
    texte = [b.text for b in pruefen.pruefe(ordner, kurs) if b.pruefer == 6 and b.stufe == pruefen.FEHLER]
    assert len([t for t in texte if "50" in t]) == 4, texte


def test_p6_bedingung_auf_einem_anderen_test(tmp_path, dateien):
    kurs = sternkurs()
    for a in _medaillen(kurs):
        a["voraussetzung"][-1] = {"aktivitaet": "Kacheltest 1", "min": 0}
    ordner = gebaut(tmp_path, dateien, kurs)
    texte = [b.text for b in pruefen.pruefe(ordner, kurs) if b.pruefer == 6]
    assert any("Kacheltest 1" in t for t in texte), texte


# --------------------------------------------------------------------------- #
# Tests mit zweitem Versuch, Hilfen nach Fehlversuch, Sterne nach Schlüssel
# (Lehrkraft 2026-10-23: bestanden ab 50 %, IHK-Schlüssel 50/67/92 nur im ersten
# Versuch, im zweiten Versuch bestanden = genau 1 Stern)
# --------------------------------------------------------------------------- #
SCHLUESSEL = [50, 67, 92]


def paarkurs(**schalter) -> dict:
    """sternkurs mit Test vor der Hilfe (die Hilfe gehört zum Schritt des Tests) und den Kursschaltern."""
    kurs = sternkurs()
    for ab in kurs["abschnitte"][1:3]:
        hilfe, test, stern = ab["aktivitaeten"]
        ab["aktivitaeten"] = [test, hilfe, stern]
    kurs["kurs"].update(schalter)
    return kurs


def _seite(name):
    return {"typ": "page", "name": name, "inhalt": "<p>x</p>"}


def test_zwei_versuche_paar():
    test = {"typ": "quiz", "name": "Kacheltest", "sterne": 3, "fragen": [FRAGE]}
    hilfen = [sterne.hilfekarte("Tipp A", "<p>x</p>"), sterne.hilfekarte("Tipp B", "<p>x</p>")]
    t1, t2 = sterne.zwei_versuche(test, hilfen, 50)
    assert (t1["name"], t2["name"]) == ("Kacheltest", "Kacheltest, zweiter Versuch")
    for t in (t1, t2):
        assert t["versuche"] == 1 and t["bestehensgrenze_prozent"] == 50 and t["sterne"] == 0
    assert (t1["abschluss"], t2["abschluss"]) == ("bestanden", "bestanden_oder_versuche")
    sperre = {"abschluss": kd.kennung_von(t1), "zustand": "nicht_bestanden", "sichtbar_wenn_gesperrt": False}
    assert t2["voraussetzung"] == sperre
    assert all(sperre in kd.voraussetzungen(h) for h in hilfen)
    # idnummern: Test zählt als Schritt, der zweite Versuch nicht; Hilfen hängen am Schritt des Tests
    kachel = {"name": "Kachel", "aktivitaeten": [_seite("S1"), t1, *hilfen, t2, _seite("S3")]}
    sterne.idnummern([{"name": "Start", "aktivitaeten": [_seite("A")]}, kachel])
    assert [a.get("idnummer") for a in kachel["aktivitaeten"]] == [
        None, "test-k2-s2", "hilfe-k2-s2-1", "hilfe-k2-s2-2", "test2-k2-s2", None]
    kurs = {"kurs": {"vollname": "x", "kurzname": "x", "beschreibung": "x",
                     "ki_hinweis": "mit Hilfe von künstlicher Intelligenz"}, "abschnitte": [kachel]}
    assert kd.pruefe(kurs) == []
    assert kd.ZUSTAND["nicht_bestanden"] == 3


def test_sternformel_stufen():
    f = sterne.sternformel("test-k1-s1", "test2-k1-s1", SCHLUESSEL, 12, 12)

    def sterne_bei(erster, zweiter=None):
        return pruefen.rechne(f, {"test-k1-s1": erster, "test2-k1-s1": zweiter})
    for punkte, soll in ((12, 3), (11.04, 3), (11, 2), (8.04, 2), (8, 1), (6, 1), (5.99, 0), (0, 0)):
        assert sterne_bei(punkte) == soll, (punkte, soll)
    # gerundet auf 5 Stellen: Rechenfehler an der Schwelle zählen (11,04/12 = 92 %), aber unter 50 % kein Stern –
    # Moodle meldet „bestanden“ ungerundet erst ab 6 von 12
    assert sterne_bei(5.9994) == 0 and sterne_bei(5.99999) == 0 and sterne_bei(5.988) == 0
    assert sterne_bei(6) == 1 and sterne_bei(11.04) == 3 and sterne_bei(8.04) == 2
    assert sterne_bei(0, 6) == 1            # erst im zweiten Versuch bestanden: genau 1 Stern
    assert sterne_bei(0, 12) == 1
    assert sterne_bei(0, 5.99) == 0
    assert sterne_bei(7, None) == 1         # zweiter Versuch leer: zählt als 0, die Sterne bleiben
    assert sterne_bei(12, 12) == 3          # bestanden und doch zweiter Versuch: kein Extra
    assert sterne_bei(None, None) == 0


def test_berechnetes_item_in_sicherung(tmp_path, dateien):
    kurs = paarkurs(zwei_versuche=True, bestehen_prozent=50, sterne_schluessel=SCHLUESSEL)
    assert sterne.paar_einsetzen(kurs, "Kacheltest 1") and sterne.paar_einsetzen(kurs, "Kacheltest 2")
    ordner = gebaut(tmp_path, dateien, kurs)
    it = items(ordner)
    gid = {n: it[n][0].get("id") for n in ("Kacheltest 1", "Kacheltest 1, zweiter Versuch")}
    for n in ("Kacheltest 1", "Kacheltest 1, zweiter Versuch", "Kacheltest 2"):
        gi = it[n][0]
        assert gi.findtext("weightoverride") == "1" and float(gi.findtext("aggregationcoef2")) == 0, n
        assert float(gi.findtext("gradepass")) == 0.5 * float(gi.findtext("grademax")), n
    gb = ET.parse(ordner / "gradebook.xml").getroot()
    berechnet = [gi for gi in gb.iter("grade_item") if gi.findtext("calculation") not in (None, "", "$@NULL@$")]
    assert [gi.findtext("itemname") for gi in berechnet] == ["Sterne: Kacheltest 1", "Sterne: Kacheltest 2"]
    calc = berechnet[0].findtext("calculation")
    assert berechnet[0].findtext("itemtype") == "manual" and float(berechnet[0].findtext("grademax")) == 3
    assert f"##gi{gid['Kacheltest 1']}##" in calc and f"##gi{gid['Kacheltest 1, zweiter Versuch']}##" in calc
    assert calc.startswith("=") and ";" not in calc and "[[" not in calc   # gespeicherte Form: Komma
    kat = next(gb.iter("grade_category")).get("id")
    assert berechnet[0].findtext("categoryid") == kat
    # Kursgesamt: 2 × Sterne (3) + 2 Stern-Quiz + Abschlusstest 10; Testnoten zählen nicht
    assert float(kurs_item(ordner).findtext("grademax")) == 18
    m = ET.parse(ordner / next(a.findtext("directory") for a in ET.parse(ordner / "moodle_backup.xml")
                               .getroot().iter("activity")
                               if a.findtext("title") == "Kacheltest 1, zweiter Versuch") / "module.xml").getroot()
    assert json.loads(m.findtext("availability"))["c"][0]["e"] == 3
    befunde = pruefen.pruefe(ordner, kurs)
    assert [b for b in befunde if b.stufe == pruefen.FEHLER and b.pruefer in (1, 6, 8)] == []


def test_ohne_schluessel_wie_bisher(tmp_path, dateien):
    kurs = paarkurs(zwei_versuche=None, bestehen_prozent=None, sterne_schluessel=None)
    vorher = json.dumps(kurs, sort_keys=True)
    assert sterne.paar_einsetzen(kurs, "Kacheltest 1") is False
    assert json.dumps(kurs, sort_keys=True) == vorher
    ordner = gebaut(tmp_path, dateien, kurs)
    gb = ET.parse(ordner / "gradebook.xml").getroot()
    assert [gi.findtext("itemtype") for gi in gb.iter("grade_item")] == ["course"]
    assert float(kurs_item(ordner).findtext("grademax")) == 18
    assert items(ordner)["Kacheltest 1"][0].findtext("weightoverride") == "0"


def test_p8_paar_ist_abgabe_und_p6_prueft_formel(tmp_path, dateien):
    kurs = paarkurs(zwei_versuche=True, bestehen_prozent=50, sterne_schluessel=SCHLUESSEL)
    sterne.paar_einsetzen(kurs, "Kacheltest 1")
    kurs["bewertungen"][0]["max"] = 4          # Formel liefert höchstens 3
    ordner = gebaut(tmp_path, dateien, kurs)
    befunde = pruefen.pruefe(ordner, kurs)
    assert not [b for b in befunde if b.pruefer == 8 and b.stufe == pruefen.FEHLER]
    assert any("Sterne: Kacheltest 1" in b.text for b in befunde if b.pruefer == 6 and b.stufe == pruefen.FEHLER)


# --------------------------------------------------------------------------- #
# Unabhängige Prüfung (2026-10-23): Formel gegen die Entscheidung, Moodle-Bestehen, Prüfer 6
# --------------------------------------------------------------------------- #
def _soll_sterne(g1, g2, mx):
    """Entscheidung der Lehrkraft exakt (Bruchrechnung): erster Versuch IHK-Schlüssel, sonst bestanden im zweiten = 1."""
    from fractions import Fraction
    p1 = Fraction(0) if g1 is None else Fraction(str(g1)) / Fraction(str(mx)) * 100
    p2 = Fraction(0) if g2 is None else Fraction(str(g2)) / Fraction(str(mx)) * 100
    if p1 >= SCHLUESSEL[0]:
        return sum(1 for g in SCHLUESSEL if p1 >= g)
    return 1 if p2 >= SCHLUESSEL[0] else 0


def test_sternformel_wie_entschieden_bei_anderen_hoechstpunkten():
    """Höchstpunkte, die 100 nicht teilen (7, 10, 13, 9,5): halbe-Prozent-Raster und alle Schwellen genau."""
    for mx in (7, 10, 13, 9.5, 12):
        f = sterne.sternformel("t1", "t2", SCHLUESSEL, mx, mx)
        noten = sorted({round(mx * k / 200, 5) for k in range(201)}
                       | {round(mx * s / 100 + d, 5) for s in SCHLUESSEL for d in (0, 0.001, -0.01)}) + [None]
        for g1 in noten:
            for g2 in (None, 0, round(mx / 2, 5), mx, round(mx * 0.49, 5)):
                ist = pruefen.rechne(f, {"t1": g1, "t2": g2})
                assert ist == _soll_sterne(g1, g2, mx), (mx, g1, g2, ist)


def test_stern_nur_wenn_moodle_bestanden_meldet():
    """Ein Stern heißt immer „bestanden“ (Entscheidung 2026-10-23). Moodle entscheidet „bestanden“ mit
    grade_grade::is_passed: finalgrade >= gradepass (lib/grade/grade_grade.php), ungerundet. Die Formel rundet
    vorher auf 2 Stellen: 5,9994 von 12 (49,995 %) ist bei Moodle „nicht bestanden“ (zweiter Versuch und Hilfen
    öffnen sich) und gäbe trotzdem einen Stern – im ersten wie im zweiten Versuch."""
    for mx in (12, 7, 13):
        f = sterne.sternformel("t1", "t2", SCHLUESSEL, mx, mx)
        gradepass = round(SCHLUESSEL[0] * mx / 100, 5)
        knapp = round(gradepass - 0.0001 * mx / 12 - 0.00001, 5)     # in der Rundungszone [49,995 %; 50 %)
        assert knapp < gradepass and round(knapp / mx * 100, 2) == 50
        assert pruefen.rechne(f, {"t1": knapp, "t2": None}) == 0, (mx, knapp)
        assert pruefen.rechne(f, {"t1": 0, "t2": knapp}) == 0, (mx, knapp)


def _p6_fehler_mit_formel(tmp_path, dateien, formel_von):
    kurs = paarkurs(zwei_versuche=True, bestehen_prozent=50, sterne_schluessel=SCHLUESSEL)
    sterne.paar_einsetzen(kurs, "Kacheltest 1")
    b = kurs["bewertungen"][0]
    b["formel"] = formel_von(b["formel"])
    ordner = gebaut(tmp_path, dateien, kurs)
    return [x for x in pruefen.pruefe(ordner, kurs) if x.pruefer == 6 and x.stufe == pruefen.FEHLER
            and "Sterne: Kacheltest 1" in x.text]


def test_p6_meldet_vertauschte_versuche(tmp_path, dateien):
    """Erster und zweiter Versuch vertauscht: ohne Noten 0, mit vollen Noten 3 – aber wer nur den ersten Test mit
    100 % schreibt, bekäme 1 statt 3 Sterne. Prüfer 6 muss das rot melden."""
    tausch = lambda f: f.replace("test-k2-s1", "@@").replace("test2-k2-s1", "test-k2-s1").replace("@@", "test2-k2-s1")  # noqa: E731
    assert _p6_fehler_mit_formel(tmp_path, dateien, tausch)


def test_p6_meldet_falsche_hoechstpunkte(tmp_path, dateien):
    """Formel teilt durch 3 (Sterne) statt durch 10 (Testpunkte): ohne Noten 0, voll 3 – aber schon 5 von 10 Punkten
    (50 %) gäben 3 statt 1 Stern. Prüfer 6 muss das rot melden."""
    assert _p6_fehler_mit_formel(tmp_path, dateien, lambda f: f.replace("/10*100", "/3*100"))


def test_hilfen_und_zweiter_versuch_erst_nach_nicht_bestanden_gebaut(tmp_path, dateien):
    """In der Sicherung: Test 1 schließt über „bestanden“ ab (completionpassgrade 1, Note), Hilfe und zweiter Versuch
    verlangen COMPLETION_COMPLETE_FAIL (e = 3) von Test 1, ganz verborgen. Wer Test 1 nie abgibt (Zustand 0),
    sieht beides nicht (availability/condition/completion/classes/condition.php: e = 3 nur bei Zustand 3)."""
    kurs = paarkurs(zwei_versuche=True, bestehen_prozent=50, sterne_schluessel=SCHLUESSEL)
    sterne.paar_einsetzen(kurs, "Kacheltest 1")
    ordner = gebaut(tmp_path, dateien, kurs)
    akts = {a.findtext("title"): a for a in ET.parse(ordner / "moodle_backup.xml").getroot().iter("activity")
            if a.findtext("directory")}
    modul = {n: ET.parse(ordner / a.findtext("directory") / "module.xml").getroot() for n, a in akts.items()}
    m1 = modul["Kacheltest 1"]
    assert (m1.findtext("completion"), m1.findtext("completionpassgrade"),
            m1.findtext("completiongradeitemnumber")) == ("2", "1", "0")
    cm1 = int(akts["Kacheltest 1"].findtext("moduleid"))
    for n in ("Hilfekarte 1", "Kacheltest 1, zweiter Versuch"):
        v = json.loads(modul[n].findtext("availability"))
        treffer = [(c, zeigen) for c, zeigen in pruefen._bedingungen(v) if c.get("cm") == cm1]
        assert treffer == [({"type": "completion", "cm": cm1, "e": 3}, False)], (n, v)


# --------------------------------------------------------------------------- #
# Stern „selbst gelöst“ bei Testpaaren (Lehrkraft 2026-10-23, Variante 1): keine Hilfe geöffnet UND Kacheltest in
# einem der beiden Versuche bestanden
# --------------------------------------------------------------------------- #
def _erfuellt(baum, zustand: dict) -> bool:
    """Moodle-Verfügbarkeit nachgebildet (availability/condition/completion/classes/condition.php); `zustand`: cmid →
    0 nicht abgeschlossen, 1 abgeschlossen, 2 bestanden, 3 nicht bestanden (fehlt = 0). e = 1 gilt bei 1 oder 2,
    e = 0 bei 0 oder 3, e = 2 und e = 3 nur genau."""
    if "op" in baum:
        teile = [_erfuellt(c, zustand) for c in baum["c"]]
        return all(teile) if baum["op"] == "&" else any(teile)
    assert baum["type"] == "completion", baum
    z = zustand.get(baum["cm"], 0)
    return {1: z in (1, 2), 0: z in (0, 3)}.get(baum["e"], z == baum["e"])


def _selbstloese(tmp_path, dateien, **schalter):
    """Kachel 1 mit Kacheltest, zwei Hilfen und Selbstlöse-Stern; mit Schaltern als Paar. (Verfügbarkeit des Sterns,
    cmid je Name)."""
    kurs = paarkurs(**schalter)
    ab = kurs["abschnitte"][1]
    test, hilfe, _ = ab["aktivitaeten"]
    ab["aktivitaeten"] = [test, hilfe, sterne.hilfekarte("Hilfekarte 1b", "<p>Noch ein Tipp.</p>"),
                          sterne.stern_aktivitaet(ab, "Kacheltest 1", ["Hilfekarte 1", "Hilfekarte 1b"])]
    sterne.paar_einsetzen(kurs, "Kacheltest 1")
    ordner = gebaut(tmp_path, dateien, kurs)
    root = ET.parse(ordner / "moodle_backup.xml").getroot()
    akts = [a for a in root.iter("activity") if a.findtext("directory")]
    cm = {a.findtext("title"): int(a.findtext("moduleid")) for a in akts}
    stern = next(a for a in akts if a.findtext("title") == sterne.STERN_NAME)   # der erste: Kachel 1
    roh = ET.parse(ordner / stern.findtext("directory") / "module.xml").getroot().findtext("availability")
    return json.loads(roh), cm, kurs, ordner


PAAR = dict(zwei_versuche=True, bestehen_prozent=50, sterne_schluessel=SCHLUESSEL)


def test_selbstloese_stern_nach_zweitem_versuch_ohne_hilfe(tmp_path, dateien):
    v, cm, kurs, ordner = _selbstloese(tmp_path, dateien, **PAAR)
    t1, t2 = cm["Kacheltest 1"], cm["Kacheltest 1, zweiter Versuch"]
    assert _erfuellt(v, {t1: 3, t2: 2})                  # erst im zweiten Versuch bestanden, keine Hilfe
    assert _erfuellt(v, {t1: 2})                         # gleich im ersten bestanden
    assert not _erfuellt(v, {})                          # noch nichts abgegeben
    assert [b for b in pruefen.pruefe(ordner, kurs) if b.stufe == pruefen.FEHLER and b.pruefer in (1, 6, 8)] == []
    # ohne Paar (kein Profilschlüssel) wie bisher: Test abgeschlossen, keine Hilfe angesehen
    v0, cm0, _, _ = _selbstloese(tmp_path / "ohne", dateien)
    assert v0["c"] == [{"type": "completion", "cm": cm0["Kacheltest 1"], "e": 1},
                       {"type": "completion", "cm": cm0["Hilfekarte 1"], "e": 0},
                       {"type": "completion", "cm": cm0["Hilfekarte 1b"], "e": 0}]


def test_selbstloese_stern_nicht_nach_zwei_fehlversuchen(tmp_path, dateien):
    v, cm, _, _ = _selbstloese(tmp_path, dateien, **PAAR)
    t1, t2 = cm["Kacheltest 1"], cm["Kacheltest 1, zweiter Versuch"]
    assert _erfuellt(v, {t1: 3, t2: 2})                  # Gegenprobe: nur der zweite Versuch entscheidet
    assert not _erfuellt(v, {t1: 3, t2: 3})
    assert not _erfuellt(v, {t1: 3, t2: 1})              # „alle Versuche verbraucht“ ist nicht „bestanden“


def test_selbstloese_stern_nicht_nach_hilfe(tmp_path, dateien):
    v, cm, _, _ = _selbstloese(tmp_path, dateien, **PAAR)
    t1, t2 = cm["Kacheltest 1"], cm["Kacheltest 1, zweiter Versuch"]
    assert _erfuellt(v, {t1: 3, t2: 2})                  # Gegenprobe: ohne Hilfe gäbe es ihn
    for hilfe in ("Hilfekarte 1", "Hilfekarte 1b"):
        assert not _erfuellt(v, {t1: 3, cm[hilfe]: 1, t2: 2}), hilfe


# Stern „selbst gelöst“ bei mehreren Kacheltests (Lehrkraft 2026-10-23, Anlass Kachel 2 mit Begehung und
# Begriffswand): jeder Kacheltest in einem seiner beiden Versuche bestanden, keine Hilfe der Kachel geöffnet
HILFEN_ZWEI = ("Hilfekarte 1", "Hilfekarte 1b", "Hilfekarte 1c")


def _zwei_paare_kurs(reihenfolge=("Kacheltest 1", "Kacheltest 1b")):
    """Kachel 1 mit zwei Tests (je Hilfen dahinter); der Stern wartet wie stern_anhaengen auf die letzte Abgabe."""
    kurs = paarkurs(**PAAR)
    ab = kurs["abschnitte"][1]
    test, hilfe, _ = ab["aktivitaeten"]
    test2 = {"typ": "quiz", "name": "Kacheltest 1b", "sterne": 3, "fragen": [FRAGE]}
    ab["aktivitaeten"] = [test, hilfe, test2, sterne.hilfekarte("Hilfekarte 1b", "<p>x</p>"),
                          sterne.hilfekarte("Hilfekarte 1c", "<p>x</p>"),
                          sterne.stern_aktivitaet(ab, "Kacheltest 1b", list(HILFEN_ZWEI))]
    for kennung in reihenfolge:
        assert sterne.paar_einsetzen(kurs, kennung)
    return kurs


def _stern_verfuegbarkeit(tmp_path, dateien, kurs):
    ordner = gebaut(tmp_path, dateien, kurs)
    akts = [a for a in ET.parse(ordner / "moodle_backup.xml").getroot().iter("activity") if a.findtext("directory")]
    cm = {a.findtext("title"): int(a.findtext("moduleid")) for a in akts}
    stern = next(a for a in akts if a.findtext("title") == sterne.STERN_NAME)
    roh = ET.parse(ordner / stern.findtext("directory") / "module.xml").getroot().findtext("availability")
    return json.loads(roh), cm, ordner


def test_selbstloese_stern_verlangt_alle_kacheltests(tmp_path, dateien):
    kurs = _zwei_paare_kurs()
    v, cm, ordner = _stern_verfuegbarkeit(tmp_path, dateien, kurs)
    a1, a2 = cm["Kacheltest 1"], cm["Kacheltest 1, zweiter Versuch"]
    b1, b2 = cm["Kacheltest 1b"], cm["Kacheltest 1b, zweiter Versuch"]
    assert not _erfuellt(v, {b1: 2})                     # nur der letzte Test bestanden
    assert not _erfuellt(v, {a1: 2})                     # nur der erste Test bestanden
    assert not _erfuellt(v, {a1: 2, b1: 3, b2: 3})       # zweiter Test zweimal nicht bestanden
    assert _erfuellt(v, {a1: 2, b1: 3, b2: 2})           # einer im 1., einer im 2. Versuch, keine Hilfe
    assert _erfuellt(v, {a1: 3, a2: 2, b1: 2})
    for hilfe in HILFEN_ZWEI:
        assert not _erfuellt(v, {a1: 2, b1: 3, b2: 2, cm[hilfe]: 1}), hilfe
    assert [b for b in pruefen.pruefe(ordner, kurs) if b.stufe == pruefen.FEHLER and b.pruefer in (1, 6, 8)] == []


def test_selbstloese_stern_zwei_paare_idempotent():
    kurs = _zwei_paare_kurs()
    stern = next(a for a in kurs["abschnitte"][1]["aktivitaeten"] if sterne.ist_stern(a))
    vorher = json.dumps(stern["voraussetzung"])
    t1, t2 = (a for a in kurs["abschnitte"][1]["aktivitaeten"] if kd.kennung_von(a).startswith("Kacheltest 1b"))
    sterne.selbstloese_paar(kurs, t1, t2)              # zweiter Lauf für dasselbe Paar
    assert json.dumps(stern["voraussetzung"]) == vorher
    # andere Reihenfolge der Paare: dieselbe Bedingung
    stern_r = next(a for a in _zwei_paare_kurs(("Kacheltest 1b", "Kacheltest 1"))["abschnitte"][1]["aktivitaeten"]
                   if sterne.ist_stern(a))
    assert json.dumps(stern_r["voraussetzung"]) == vorher
    oder = [v for v in stern["voraussetzung"] if "oder" in v]
    assert [[b["abschluss"] for b in g["oder"]] for g in oder] == [
        ["Kacheltest 1", "Kacheltest 1, zweiter Versuch"], ["Kacheltest 1b", "Kacheltest 1b, zweiter Versuch"]]
    assert [v for v in stern["voraussetzung"] if "oder" not in v] == [
        {"abschluss": h, "zustand": "nicht_abgeschlossen"} for h in HILFEN_ZWEI]


# --------------------------------------------------------------------------- #
# Schilder für Sterne und Sozialform (Kursschalter `schilder`, Lehrkraft 2026-10-23)
# --------------------------------------------------------------------------- #
GELB = ('<span style="background:#FFF4CC;color:#7A5A00;border:1px solid #E0A800;border-radius:10px;'
        'padding:1px 8px;">')
GRUEN = ('<span style="background:#E3F6E1;color:#1E5E1A;border:1px solid #7DDE78;border-radius:10px;'
         'padding:1px 8px;">')


def _schilderkurs(schilder=True):
    kurs = paarkurs(zwei_versuche=True, bestehen_prozent=50, sterne_schluessel=SCHLUESSEL, schilder=schilder)
    sterne.paar_einsetzen(kurs, "Kacheltest 1")
    return kurs


def _gebaut_je_name(tmp_path, dateien, kurs):
    """Name → (intro aus <typ>.xml, showdescription aus module.xml)."""
    ordner = gebaut(tmp_path, dateien, kurs)
    aus = {}
    for a in ET.parse(ordner / "moodle_backup.xml").getroot().iter("activity"):
        if not a.findtext("directory"):
            continue
        d = ordner / a.findtext("directory")
        typ = a.findtext("modulename")
        intro = ET.parse(d / f"{typ}.xml").getroot().find(typ).findtext("intro") or ""
        aus[a.findtext("title")] = (intro, ET.parse(d / "module.xml").getroot().findtext("showdescription"))
    return aus


def test_sternschild_test(tmp_path, dateien):
    akt = _gebaut_je_name(tmp_path, dateien, _schilderkurs())
    intro, zeigen = akt["Kacheltest 1"]
    assert intro.startswith(f"<p>{GELB}⭐⭐⭐ · 2 Versuche · bestanden ab 50 %</span>"), intro
    assert zeigen == "1"                 # mit Schild zeigt die Kursseite die Beschreibung (Lehrkraft 2026-10-27)
    intro2, zeigen2 = akt["Kacheltest 1, zweiter Versuch"]      # beim zweiten Versuch kein Sternschild
    assert "⭐" not in intro2 and GELB not in intro2 and zeigen2 == "0"


def test_sternschild_selbstloese(tmp_path, dateien):
    akt = _gebaut_je_name(tmp_path, dateien, _schilderkurs())
    intro, zeigen = akt[sterne.STERN_NAME]
    assert intro.startswith(f"<p>{GELB}⭐ · ohne Hilfe</span>") and zeigen == "1"


def test_sozialform_gruppe(tmp_path, dateien):
    kurs = _schilderkurs()
    akts = kurs["abschnitte"][1]["aktivitaeten"]
    akts[0]["sozialform"] = "Gruppenarbeit"                       # Kacheltest 1: beide Schilder in einer Zeile
    hilfe = next(a for a in akts if sterne.ist_hilfe(a))
    hilfe["sozialform"] = "Partnerarbeit"
    akt = _gebaut_je_name(tmp_path, dateien, kurs)
    assert akt["Kacheltest 1"][0].startswith(
        f"<p>{GELB}⭐⭐⭐ · 2 Versuche · bestanden ab 50 %</span> {GRUEN}👥 Gruppenarbeit</span></p>")
    assert akt["Hilfekarte 1"][0].startswith(f"<p>{GRUEN}👥 Partnerarbeit</span></p>")
    assert akt["Hilfekarte 1"][1] == "1"          # Schild Sozialform: Beschreibung auf der Kursseite (2026-10-27)


def test_einzelarbeit_ohne_schild(tmp_path, dateien):
    kurs = _schilderkurs()
    hilfe = next(a for a in kurs["abschnitte"][1]["aktivitaeten"] if sterne.ist_hilfe(a))
    hilfe["sozialform"] = "Einzelarbeit"
    assert sterne.schild_html(hilfe, 50) == ""     # Hinweis „kostet den Stern“ steht im Namen (2026-10-26)
    akt = _gebaut_je_name(tmp_path, dateien, kurs)
    assert "<span" not in akt["Hilfekarte 1"][0] and akt["Hilfekarte 1"][1] == "0"


def test_ohne_schalter_kein_schild(tmp_path, dateien):
    kurs = _schilderkurs(schilder=None)
    kurs["abschnitte"][1]["aktivitaeten"][0]["sozialform"] = "Gruppenarbeit"
    akt = _gebaut_je_name(tmp_path, dateien, kurs)
    for name, (intro, zeigen) in akt.items():
        assert "⭐" not in intro and "👥" not in intro and zeigen == "0", name


def test_test_ohne_paar_schild_mit_zahl():
    """Der Abschlusstest (sterne 10, ohne Paar) bekommt „⭐ × 10 · ein Versuch“ (Lehrkraft 2026-10-23, KONZEPT);
    Tests ohne Sterne (Eingangstest, Generalprobe) und der zweite Versuch bekommen kein Sternschild; das
    Sozialform-Schild bleibt."""
    test = {"typ": "quiz", "name": "Abschlusstest", "sterne": 10, "versuche": 1, "fragen": [FRAGE]}
    assert sterne.schild_html(test, 50, SCHLUESSEL) == f"<p>{sterne.SCHILD_GELB}⭐ × 10 · ein Versuch</span></p>"
    assert "beliebig viele Versuche" in sterne.schild_html(dict(test, versuche=0), 50, SCHLUESSEL)
    assert sterne.schild_html(dict(test, sterne=0), 50, SCHLUESSEL) == ""
    assert sterne.schild_html(dict(test, sterne=0, sozialform="Gruppenarbeit"), 50, SCHLUESSEL) == (
        f"<p>{GRUEN}👥 Gruppenarbeit</span></p>")
    assert sterne.schild_html(dict(test, rolle="test2", sterne=0), 50, SCHLUESSEL) == ""
