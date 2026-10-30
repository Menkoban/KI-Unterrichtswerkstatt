"""Profilwerte für den Kursbau (Rückmeldung LS 1, 2026-10-22).

Der Kursbau liest das Lehrkraft-Profil nur über `arbeitsbereich.profil()`. Fehlt dort ein Schlüssel (älteres
Profil, andere Lehrkraft), gilt der Standard aus der Vorlage von Pipeline 1 – neutral, also das bisherige
Verhalten: keine Kachelnummern, kein Steckbrief, kein Logo, KI-Hinweis wie bisher.

    moodle_profil(werte)      # {id: wert} mit allen Schlüsseln lehrkraft.* und moodle.* der Vorlage
    anrede_dativ("Herr X")    # "Herrn X"
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import arbeitsbereich  # noqa: E402

GRUPPEN = ("lehrkraft.", "moodle.")


def standards() -> dict:
    """Standardwerte {id: standard} aus `profil/vorlage.json` von Pipeline 1 (zur Laufzeit gelesen)."""
    vorlage = arbeitsbereich.werkzeug_pipeline1() / "profil" / "vorlage.json"
    return {e["id"]: e["standard"] for e in json.loads(vorlage.read_text(encoding="utf-8"))["einstellungen"]}


def moodle_profil(werte: dict) -> dict:
    """Alle Schlüssel lehrkraft.* und moodle.* der Vorlage, darüber die eigenen Werte (eigene gewinnen)."""
    profil = {k: v for k, v in standards().items() if k.startswith(GRUPPEN)}
    profil.update(werte)
    return profil


def anrede_dativ(anrede: str) -> str:
    """„Herr X“ → „Herrn X“ (für „von Herrn X“), sonst unverändert."""
    return "Herrn" + anrede[4:] if anrede == "Herr" or anrede.startswith("Herr ") else anrede
