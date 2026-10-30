"""Steckbrief einer Akte schreiben (gemeinsam für alle Generatoren).

Der Stand (entwurf/freigegeben) und das Freigabedatum bleiben beim Neuerzeugen erhalten.
„zuletzt_bearbeitet“ ändert sich nur, wenn sich der Inhalt geändert hat (Fingerabdruck der
Daten ohne die Felder „stand“ und „datum“) oder wenn eine Grundlage (baut_auf) seit der letzten
Bearbeitung geändert wurde; dann gilt die neu erzeugte Akte als geprüft und aktuell. So meldet
akten.py nach einem bloßen Neuerzeugen nicht alle nachfolgenden Akten als veraltet."""
import datetime as dt, hashlib, json, pathlib

OHNE = {"stand", "datum"}


def fingerabdruck(inhalt):
    if isinstance(inhalt, dict):
        inhalt = {k: v for k, v in inhalt.items() if k not in OHNE}
    return hashlib.sha256(json.dumps(inhalt, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def schreiben(ab, rel, art, titel, baut_auf, fach, notiz, inhalt, vorher=None):
    """Schreibt .daten/akten/<rel>.json. `inhalt` sind die Daten, aus denen die Akte entsteht;
    `vorher` ein älterer Steckbrief, dessen Stand übernommen wird, wenn es noch keinen gibt."""
    ab = pathlib.Path(ab)
    sbp = ab / ".daten" / "akten" / (rel + ".json"); sbp.parent.mkdir(parents=True, exist_ok=True)
    alt = json.loads(sbp.read_text(encoding="utf-8")) if sbp.exists() else (vorher or {})
    jetzt = dt.datetime.now().strftime("%Y-%m-%dT%H:%M")
    h = fingerabdruck(inhalt)
    zuletzt = alt.get("zuletzt_bearbeitet")
    eltern = []
    for b in baut_auf:
        p = ab / ".daten" / "akten" / (b + ".json")
        if p.exists():
            eltern.append(json.loads(p.read_text(encoding="utf-8"))["zuletzt_bearbeitet"])
    if not zuletzt or alt.get("inhalt_hash") != h or (eltern and max(eltern) > zuletzt):
        zuletzt = jetzt
    sb = {"art": art, "titel": titel, "pfad": rel, "stand": alt.get("stand", "entwurf"),
          "freigegeben_am": alt.get("freigegeben_am"), "zuletzt_bearbeitet": zuletzt, "baut_auf": baut_auf,
          "fach": fach, "notiz": notiz, "inhalt_hash": h}
    sbp.write_text(json.dumps(sb, ensure_ascii=False, indent=1), encoding="utf-8")
    return sb


def freigeben(ab, rel):
    """Setzt Stand „freigegeben“ und das Freigabedatum (jetzt)."""
    sbp = pathlib.Path(ab) / ".daten" / "akten" / (rel + ".json")
    sb = json.loads(sbp.read_text(encoding="utf-8"))
    sb["stand"], sb["freigegeben_am"] = "freigegeben", dt.datetime.now().strftime("%Y-%m-%dT%H:%M")
    sbp.write_text(json.dumps(sb, ensure_ascii=False, indent=1), encoding="utf-8")
    return sb


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 4 and sys.argv[1] == "freigeben":
        print(freigeben(sys.argv[2], sys.argv[3]))
    else:
        print("python akten/steckbrief.py freigeben <arbeitsbereich> <pfad der akte>")
