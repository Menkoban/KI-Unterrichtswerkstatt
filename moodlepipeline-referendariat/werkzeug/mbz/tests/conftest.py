"""Gemeinsame Vorrichtungen: Beispielkurs einmal bauen."""
import copy
import sys
import tarfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bauen  # noqa: E402
import beispiel  # noqa: E402
import pruefen  # noqa: E402


@pytest.fixture(scope="session")
def dateien(tmp_path_factory):
    wurzel = tmp_path_factory.mktemp("dateien")
    beispiel.dateien_anlegen(wurzel)
    return wurzel


@pytest.fixture(scope="session")
def paket(tmp_path_factory, dateien):
    """(mbz, entpackter Ordner, Kursdefinition) des Beispiels."""
    ziel = tmp_path_factory.mktemp("bau") / "beispiel.mbz"
    kurs = beispiel.kursdefinition()
    bauen.baue(kurs, dateien, ziel)
    ordner = ziel.parent / "entpackt"
    with tarfile.open(ziel, "r:gz") as tar:
        tar.extractall(ordner, filter="data")
    return ziel, ordner, kurs


@pytest.fixture
def variante(tmp_path, dateien):
    """Baut eine abgewandelte Kopie des Beispiels und liefert die Befunde."""
    def bauen_und_pruefen(aendern):
        kurs = copy.deepcopy(beispiel.kursdefinition())
        aendern(kurs)
        ziel = tmp_path / "variante.mbz"
        bauen.baue(kurs, dateien, ziel)
        return pruefen.pruefe(ziel, kurs)
    return bauen_und_pruefen


def akt(kurs, name):
    """Aktivität der Kursdefinition nach Name."""
    return next(a for ab in kurs["abschnitte"] for a in ab["aktivitaeten"] if a["name"] == name)
