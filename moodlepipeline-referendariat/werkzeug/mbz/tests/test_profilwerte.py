"""Profilwerte für den Kursbau: fehlende Schlüssel neutral aus der Vorlage, eigene Werte gewinnen."""
import profilwerte

#: Schlüssel, die der Kursbau braucht (Bauplan Rückmeldung LS 1, Global Constraints)
SCHLUESSEL = ["lehrkraft.anrede", "lehrkraft.email", "moodle.schullogo", "moodle.ki_hinweis", "moodle.steckbrief",
              "moodle.handlungssituation", "moodle.kachelnummern", "moodle.kachelbilder",
              "moodle.kachelbilder_stil", "moodle.medaillen_grenzen", "moodle.schulfarben"]


def test_fehlende_schluessel_neutral():
    p = profilwerte.moodle_profil({})
    assert set(SCHLUESSEL) <= set(p)
    assert p["moodle.kachelnummern"] is False
    assert p["moodle.steckbrief"] is False
    assert p["moodle.ki_hinweis"] is False
    assert p["moodle.handlungssituation"] == "kurz_in_allgemein"
    assert p["moodle.kachelbilder"] == "keine"
    assert p["moodle.medaillen_grenzen"] == [1, 50, 81, 92]
    assert p["moodle.schullogo"] == ""


def test_werte_gewinnen():
    eigene = {"lehrkraft.anrede": "Herr Muster", "lehrkraft.email": "muster@schule.example",
              "moodle.schullogo": "Profil/logo.png", "moodle.ki_hinweis": True, "moodle.steckbrief": True,
              "moodle.handlungssituation": "einstiegskachel", "moodle.kachelnummern": True,
              "moodle.kachelbilder": "ki_illustration", "moodle.kachelbilder_stil": "skizze",
              "moodle.medaillen_grenzen": [5, 40, 70, 90], "moodle.schulfarben": ["#08349C", "#7DDE78"],
              "ansprache": "du"}
    p = profilwerte.moodle_profil(eigene)
    for k in SCHLUESSEL:
        assert p[k] == eigene[k], k
    assert p["ansprache"] == "du"   # Schlüssel anderer Gruppen gehen nicht verloren


def test_anrede_dativ():
    assert profilwerte.anrede_dativ("Herr Muster") == "Herrn Muster"
    assert profilwerte.anrede_dativ("Frau Muster") == "Frau Muster"
    assert profilwerte.anrede_dativ("") == ""


def test_neue_profilschluessel_neutral():
    """Bauplan Kursdurchsicht LS 1 (2026-10-23): ohne die neuen Schlüssel baut ein Kurs wie bisher."""
    p = profilwerte.moodle_profil({})
    assert p["moodle.allgemein_stil"] == "schlicht"
    assert p["moodle.bestehen_prozent"] == 0 and p["moodle.sterne_schluessel"] == []
    for k in ("moodle.schrittnummern_mit_kachel", "moodle.tests_zwei_versuche", "moodle.schilder",
              "moodle.pdf_formular"):
        assert p[k] is False, k


def test_profilschluessel_sternzaehler_neutral():
    """Sternzähler in Allgemein (Lehrkraft 2026-10-23): Vorlage neutral aus, anwenden reicht den Schalter weiter."""
    import allgemein
    p = profilwerte.moodle_profil({})
    assert p["moodle.sternzaehler"] is False
    for wert in (False, True):
        kurs = {"kurs": {}, "abschnitte": []}
        allgemein.anwenden(kurs, profilwerte.moodle_profil({"moodle.sternzaehler": wert}))
        assert kurs["kurs"]["sternzaehler"] is wert
