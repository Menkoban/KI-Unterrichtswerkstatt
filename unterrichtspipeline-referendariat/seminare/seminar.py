"""Seminarprofile (Veröffentlichung, Lehrkraft 2026-11): je Seminar ein Ordner `seminare/<id>/seminar.json` mit Name,
Ort, Anschrift, Besuchsformen (Kurz- oder voller Entwurf, Paragraf), Seitenbudget, dienstlicher Versicherung,
KI-Fußnote und Hinweisen je Besuchsform. Ausgewählt wird über den Profilwert `seminar` (neutral „keins“).
Mitgeliefert: `osnabrueck-bbs` (Studienseminar Osnabrück, LBS).

    import seminar
    s = seminar.lade(profil)          # dict aus seminar.json; Abbruch mit Meldung, wenn keins gewählt ist
    seminar.verfuegbar()              # ["osnabrueck-bbs", ...]
"""
import json
import pathlib

ORDNER = pathlib.Path(__file__).resolve().parent


def verfuegbar():
    return sorted(p.parent.name for p in ORDNER.glob("*/seminar.json"))


def lade(profil):
    """Seminarprofil zum Profilwert `seminar` (profil: dict {id: wert} oder die Kennung selbst)."""
    kennung = profil.get("seminar", "keins") if isinstance(profil, dict) else profil
    pfad = ORDNER / str(kennung) / "seminar.json"
    if not kennung or kennung == "keins" or not pfad.exists():
        raise SystemExit(f"Kein Seminarprofil gewählt (Profilwert seminar = {kennung!r}). Verfügbar: "
                         + ", ".join(verfuegbar()) + ". Im Profil eintragen oder ein eigenes Seminar unter seminare/ anlegen.")
    return json.loads(pfad.read_text(encoding="utf-8"))


def faecher(profil):
    """(berufliche Fachrichtung, Unterrichtsfach) aus dem Profilwert `faecher` („Elektrotechnik (berufliche
    Fachrichtung)“, „Mathematik (Unterrichtsfach)“); fehlt eine Angabe, ein Platzhalter in eckigen Klammern."""
    fr, uf = "[Fachrichtung]", "[Unterrichtsfach]"
    for f in profil.get("faecher", []):
        if "(berufliche Fachrichtung)" in f:
            fr = f.replace("(berufliche Fachrichtung)", "").strip()
        elif "(Unterrichtsfach)" in f:
            uf = f.replace("(Unterrichtsfach)", "").strip()
    return fr, uf
