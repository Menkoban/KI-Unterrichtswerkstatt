"""Stufen-Aufgaben (stufen.py, KONZEPT 2026-11): Regel, Bedingungsbau gegen die Regel, Einsetzen, Bau, Skript."""
import copy
import itertools
import shutil
import subprocess
from pathlib import Path

import pytest

import bauen
import kursdefinition as kd
import pruefen
import stufen

G, S, V = stufen.STUFEN
NODE = shutil.which("node")


def test_mittel_erst_wenn_alle_bewertet():
    assert stufen.mittel([100, None]) is None
    assert stufen.mittel([100, 50]) == 75


def test_pfad():
    assert stufen.pfad(S, [[100, 100, 67], [33, 100, 100], [None]]) == [
        (S, V, pytest.approx(88.9, 0.01)), (V, V, pytest.approx(77.8, 0.01)), (V, V, None)]
    assert stufen.pfad(S, [[30, 30], [100]])[1][:2] == (G, S)


def _spec(n):
    return [{"aufgaben": {s: [f"K{k} {s} {i}" for i in (1, 2)] for s in stufen.STUFEN},
             "mittel": {s: f"m{k}{s}" for s in stufen.STUFEN}} for k in range(1, n + 1)]


@pytest.mark.parametrize("ergebnisse", list(itertools.product([None, "halb", 20, 60, 90], repeat=3)))
def test_bedingungen_folgen_der_regel(ergebnisse):
    """Für alle Verläufe über drei Kacheln: genau die Stufe der Regel ist Einstieg (E) jeder Kachel."""
    spec = _spec(3)
    lg = stufen.logik(spec)
    noten, e, werte = {}, S, []
    for k, erg in zip(spec, ergebnisse):
        aufg = k["aufgaben"][e]
        if erg == "halb":
            noten[aufg[0]] = 100
            w = [100, None]
        elif erg is not None:
            noten.update({q: erg for q in aufg})
            noten[k["mittel"][e]] = erg
            w = [erg, erg]
        else:
            w = [None, None]
        werte.append(w)
        e = stufen.endstufe(e, stufen.mittel(w))
    erwartet = [x[0] for x in stufen.pfad(S, werte)]
    for i, l in enumerate(lg):
        wahr = [s for s in stufen.STUFEN if stufen.auswerten(l["E"][s], noten)]
        assert wahr == [erwartet[i]], (i, ergebnisse)


def _kurs():
    def aufg(t):
        return {"thema": t, "fragen": [{"typ": "truefalse", "name": t, "text": "<p>?</p>", "richtig": True}]}
    return {"kurs": {"vollname": "T", "kurzname": "T", "beschreibung": "<p>x</p>",
                     "ki_hinweis": "mit Hilfe von künstlicher Intelligenz", "format": "topics"},
            "abschnitte": [{"name": f"{n} · K", "aktivitaeten": [
                {"typ": "label", "name": f"Auftrag {n}", "text": "<p>A</p>"},
                {"typ": "stufen", "kachel": n, "titel": f"Kachel {n}",
                 "aufgaben": {s: [aufg(f"{s} {n} a"), aufg(f"{s} {n} b")] for s in stufen.STUFEN}}]}
                for n in (1, 2)]}


def test_einsetzen(tmp_path):
    k = _kurs()
    assert stufen.einsetzen(k)
    assert not stufen.einsetzen(k)
    akts = k["abschnitte"][1]["aktivitaeten"]
    assert akts[0]["idnummer"].startswith("stufe-k2-") and "-kopf-" in akts[0]["idnummer"]
    assert {a["idnummer"] for a in akts if "-kopf-" in a.get("idnummer", "")} == {
        "stufe-k2-g-kopf-ab", "stufe-k2-s-kopf-bleibt", "stufe-k2-v-kopf-auf"}
    assert [b["idnummer"] for b in k["bewertungen"]][:3] == ["stufe-k1-g-mittel", "stufe-k1-s-mittel",
                                                              "stufe-k1-v-mittel"]
    assert all(b["verborgen"] and b["im_kursgesamt"] is False for b in k["bewertungen"])
    q = next(a for a in akts if a.get("idnummer") == "stufe-k2-s-1")
    assert q["bewertungsmethode"] == "erste" and not q.get("beschreibung_auf_kursseite")
    assert "stufe_" not in (q.get("beschreibung") or "")                # kein Zeichen unter den Aufgaben
    assert not any(a.get("idnummer", "").endswith("-teil") for a in akts)  # keine Zeile „Ihre Aufgaben“
    kopf = {a["idnummer"]: a["text"] for a in akts if "-kopf-" in a.get("idnummer", "")}
    assert "Stufe: Grundlagen" in kopf["stufe-k2-g-kopf-ab"] and "aufgestiegen" not in kopf["stufe-k2-g-kopf-ab"]
    assert "aufgestiegen" in kopf["stufe-k2-v-kopf-auf"]
    assert all("%" not in t and "Ihre Stufe in dieser Kachel" not in t for t in kopf.values())


def test_bau_und_pruefer(tmp_path):
    stufen.dateien_anlegen(tmp_path)
    k = _kurs()
    stufen.einsetzen(k)
    k["allgemein_aktivitaeten"] = [stufen.weg_aktivitaet(k, "verlauf"), stufen.weg_aktivitaet(k, "karten")]
    ziel = bauen.baue(copy.deepcopy(k), tmp_path, tmp_path / "t.mbz")
    befunde = pruefen.pruefe(ziel, k)
    assert not [b for b in befunde if b.stufe == pruefen.FEHLER], pruefen.bericht(befunde)


def test_bedingung_auf_unbekannte_bewertung():
    k = _kurs()
    stufen.einsetzen(k)
    k["bewertungen"] = []
    assert any("berechnete Bewertung" in f for f in kd.pruefe(k))


def test_zeichen_svg_hat_textalternative():
    for s in stufen.STUFEN:
        svg = stufen.zeichen_svg(s)
        assert f"<title>Stufe {s}</title>" in svg
        assert svg.count('fill="none"') == stufen.STUFEN.index(s) + 1     # eine, zwei, drei Schalen


@pytest.mark.skipif(not NODE, reason="node fehlt")
def test_skript_in_node():
    t = Path(__file__).with_name("stufenweg.test.js")
    r = subprocess.run([NODE, "--test", str(t)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
