"""Volltextsuche in den aufgenommenen Quellen (erkannter Text neben jeder Datei).

    python3 werkzeug/quellen/suche.py "Wendeschütz" [--kontext 80]

Ausgabe je Treffer: Werk, Auflage, Seite, Datei und eine Textstelle; Groß-/Kleinschreibung egal.
"""
import argparse
import re
from pathlib import Path

from aufnehmen import REPO, eigene_quellen, karte_lesen  # noqa: F401


def suchen(begriff, wurzel=None, kontext=80):
    treffer = []
    wurzel = wurzel or eigene_quellen()
    for e in karte_lesen(wurzel):
        txt = (wurzel / e["datei"]).with_suffix(".txt")
        if not txt.exists():
            continue
        text = re.sub(r"\s+", " ", txt.read_text(encoding="utf-8"))
        for m in re.finditer(re.escape(begriff), text, re.IGNORECASE):
            a, b = max(0, m.start() - kontext), min(len(text), m.end() + kontext)
            treffer.append((e, "…" + text[a:b] + "…"))
    return treffer


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("begriff")
    a.add_argument("--kontext", type=int, default=80)
    a.add_argument("--wurzel", default=None, help="sonst Quellen/ im Arbeitsbereich")
    arg = a.parse_args()
    t = suchen(arg.begriff, Path(arg.wurzel) if arg.wurzel else None, arg.kontext)
    print(f"{len(t)} Treffer für „{arg.begriff}“")
    for e, stelle in t:
        print(f"- {e['werk']} {e['auflage']} S. {e['seite']} ({e['datei']}): {stelle}")
