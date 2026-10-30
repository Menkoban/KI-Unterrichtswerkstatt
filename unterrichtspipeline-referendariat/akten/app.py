"""Daten für die Referendariats-App (Webseite mit Chat, Schaltern, Dateien und Fortschritt).

    python akten/app.py <arbeitsbereich>                    # Stand, Ansicht-PDFs, Dateiliste, Upload-Liste
    python akten/app.py <arbeitsbereich> --assets ids.json  # hochgeladene Asset-ids eintragen ({pdf-name: id})

Erzeugt mit akten/stand.py den Planungsstand und wandelt jede Ausgabe (DOCX, PPTX, XLSX) des Arbeitsbereichs
in ein Ansicht-PDF unter .daten/ansicht/ (nicht im Repo, nur bei geändertem Inhalt neu). .daten/ansicht/index.json
merkt sich je Datei Inhalt und Asset-id der Seite und geht ins Repo, damit jede Sitzung weiß, was schon oben ist.
Die Dokumente für die Datenbank der Seite stehen danach in .daten/stand/app/ ({"zeilen": [...]}), die noch
hochzuladenden PDFs in .daten/ansicht/hochladen.txt, nicht mehr gebrauchte Asset-ids in .daten/ansicht/alt.txt.
Die DOCX bleibt die Ausgabe; das PDF ist nur zum Ansehen und Markieren (Lehrkraft 2026-10-24).
"""
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stand  # noqa: E402

ARTEN = {".docx": "Word", ".pptx": "Folien", ".xlsx": "Tabelle", ".pdf": "PDF", ".mbz": "Moodle"}
VORSCHAU = Path(__file__).resolve().parents[2] / "moodlepipeline-referendariat" / "werkzeug" / "mbz" / "vorschau.py"
AUSLASSEN = {".git", ".daten", "__pycache__", "bau", "fotos", "grafik", "original"}
GRENZE = 15 * 1024 * 1024       # größer passt nicht als Asset


def dateien(ab):
    for f in sorted(ab.rglob("*")):
        rel = f.relative_to(ab)
        if f.is_file() and f.suffix.lower() in ARTEN and not AUSLASSEN & set(rel.parts[:-1]) \
                and not f.name.startswith(("~$", ".~lock")):
            yield f, rel


def inhalt(f):
    return hashlib.sha1(f.read_bytes()).hexdigest()


def ansicht(f, ziel):
    """Ansicht-PDF schreiben; PDF wird kopiert, alles andere mit LibreOffice gewandelt."""
    if f.suffix.lower() == ".pdf":
        shutil.copyfile(f, ziel)
        return True
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", tmp, str(f)],
                       capture_output=True, timeout=180)
        aus = Path(tmp) / (f.stem + ".pdf")
        if not aus.exists():
            return False
        shutil.move(aus, ziel)
    return True


def geaendert(ab, rel):
    r = subprocess.run(["git", "-C", str(ab), "log", "-1", "--format=%cs", "--", str(rel)], capture_output=True,
                       text=True)
    return r.stdout.strip()


def main(ab):
    ab = Path(ab).resolve()
    stand.main(ab)
    basis = stand.github(ab)
    ord_ = ab / ".daten" / "ansicht"
    ord_.mkdir(parents=True, exist_ok=True)
    idx_pfad = ord_ / "index.json"
    index = stand.lade(idx_pfad) or {}
    neu, alt, hoch, zeilen = {}, [], [], []
    for f, rel in dateien(ab):
        k = str(rel)
        h = inhalt(f)
        e = dict(index.get(k, {}))
        pdf = ord_ / (hashlib.sha1(k.encode()).hexdigest()[:16] + ".pdf")
        if f.suffix.lower() == ".mbz":      # Moodle-Sicherung: Vorschau statt PDF (moodle_kurse)
            neu[k] = {"inhalt": h}
            zeilen.append({"pfad": k, "ordner": str(rel.parent), "name": rel.name, "art": "Moodle", "kb": round(f.stat().st_size / 1024),
                           "geaendert": geaendert(ab, rel), "asset": "", "kurs": f.stem, "link": stand.link(basis, ab, rel)})
            continue
        if e.get("inhalt") != h or not pdf.exists():
            if e.get("asset") and e.get("inhalt") != h:
                alt.append(e["asset"])
                e.pop("asset", None)
            if ansicht(f, pdf):
                e.update(inhalt=h, pdf=pdf.name)
            else:
                e.update(inhalt=h, pdf="")
                print("nicht gewandelt:", k)
        if e.get("pdf") and not e.get("asset"):
            if pdf.stat().st_size <= GRENZE:
                hoch.append(str(pdf))
            else:
                print("zu groß für die Ansicht:", k)
        neu[k] = e
        zeilen.append({"pfad": k, "ordner": str(rel.parent), "name": rel.name, "art": ARTEN[f.suffix.lower()],
                       "kb": round(f.stat().st_size / 1024), "geaendert": geaendert(ab, rel),
                       "asset": e.get("asset", ""), "link": stand.link(basis, ab, rel)})
    for k, e in index.items():           # gelöschte Dateien
        if k not in neu and e.get("asset"):
            alt.append(e["asset"])
    idx_pfad.write_text(json.dumps(neu, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    (ord_ / "hochladen.txt").write_text("\n".join(hoch) + ("\n" if hoch else ""), encoding="utf-8")
    alt_pfad = ord_ / "alt.txt"
    bisher = alt_pfad.read_text(encoding="utf-8").split() if alt_pfad.exists() else []
    alt_pfad.write_text("\n".join(sorted(set(bisher + alt))) + "\n", encoding="utf-8")
    hoch += moodle_kurse(ab)
    (ord_ / "hochladen.txt").write_text("\n".join(hoch) + ("\n" if hoch else ""), encoding="utf-8")
    app_dokumente(ab, zeilen)
    print(f"{len(zeilen)} Dateien, {len(hoch)} hochzuladen, {len(set(bisher + alt))} alte Assets")


def moodle_kurse(ab):
    """Kursvorschau je Moodle-Ordner (Pipeline 3, werkzeug/mbz/vorschau.py): .daten/ansicht/moodle/<kurz>/ und die
    Dokumente moodle_<kurz>.json (Kurs, Abschnitte, Bild-Assets, LS) und moodle_inhalt_<kurz>.json für die App.
    Gibt die noch hochzuladenden Bilder zurück."""
    import importlib.util
    if not VORSCHAU.exists():
        return []
    spec = importlib.util.spec_from_file_location("vorschau", VORSCHAU)
    v = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v)
    hoch = []
    app = ab / ".daten" / "stand" / "app"
    app.mkdir(parents=True, exist_ok=True)
    for m in sorted(ab.glob("Elektrotechnik/*/LF*/LS*/Moodle")):
        if not list(m.glob("*.mbz")) and not (m / "bau" / "kursdefinition.json").exists():
            continue
        tmp = ab / ".daten" / "ansicht" / "moodle" / "_neu"
        v.main(m, tmp)
        kurs = json.loads((tmp / "kurs.json").read_text(encoding="utf-8"))
        kurz = kurs["kurs"]["kurzname"] or m.parent.name
        ziel = ab / ".daten" / "ansicht" / "moodle" / kurz
        ziel.mkdir(parents=True, exist_ok=True)
        assets = stand.lade(ziel / "assets.json") or {}
        shutil.rmtree(ziel / "bilder", ignore_errors=True)
        shutil.move(str(tmp / "bilder"), ziel / "bilder")
        for n in ("kurs.json", "inhalte.json"):
            shutil.move(str(tmp / n), ziel / n)
        shutil.rmtree(tmp, ignore_errors=True)
        for b in sorted((ziel / "bilder").iterdir()):
            if b.stem not in assets:
                hoch.append(str(b))
        lf = re.match(r"LF(\d+)", m.parents[1].name).group(1)
        fr = {"Elektroniker_EG": "eg", "Elektroniker_AS": "as"}.get(m.parents[2].name, m.parents[2].name.lower())
        ls = re.match(r"LS(\d+)", m.parent.name).group(1)
        kurs.update(bilder=assets, ls_key=f"lf{lf}_{fr}_ls{ls}", ordner=str(m.relative_to(ab)))
        (app / f"moodle_{kurz}.json").write_text(json.dumps(kurs, ensure_ascii=False), encoding="utf-8")
        inh = json.loads((ziel / "inhalte.json").read_text(encoding="utf-8"))
        # Ein Dokument der Datenbank darf höchstens 256 KiB groß sein: große Kurse in Teile
        # moodle_inhalt_<kurz>.json, moodle_inhalt_<kurz>_2.json … (die Seite fügt sie zusammen, Feld „teile“)
        teile, teil = [], {}
        for k, wert in inh.items():
            if teil and len(json.dumps(teil, ensure_ascii=False).encode()) + len(json.dumps(wert, ensure_ascii=False).encode()) > 200_000:
                teile.append(teil)
                teil = {}
            teil[k] = wert
        teile.append(teil)
        for alt in app.glob(f"moodle_inhalt_{kurz}_*.json"):
            alt.unlink()
        for i, t in enumerate(teile):
            name = f"moodle_inhalt_{kurz}.json" if i == 0 else f"moodle_inhalt_{kurz}_{i + 1}.json"
            dok = {"inhalte": t, "teile": len(teile)} if i == 0 else {"inhalte": t}
            (app / name).write_text(json.dumps(dok, ensure_ascii=False), encoding="utf-8")
    return hoch


def app_dokumente(ab, zeilen_dateien=None):
    """Die Dokumente app/<name> der Datenbank: Planungsstand und Dateiliste."""
    st = ab / ".daten" / "stand"
    ziel = st / "app"
    ziel.mkdir(exist_ok=True)
    jetzt = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for name in ("doppelstunden", "grundlagen", "profil", "werkzeug", "struktur"):
        z = json.loads((st / f"{name}.json").read_text(encoding="utf-8"))
        (ziel / f"{name}.json").write_text(json.dumps({"zeilen": z, "erzeugt": jetzt}, ensure_ascii=False),
                                           encoding="utf-8")
    fp = ab / ".daten" / "fahrplan.json"          # Fahrplan der Personalisierung (akten/fahrplan.py)
    if fp.exists():
        (ziel / "fahrplan.json").write_text(fp.read_text(encoding="utf-8"), encoding="utf-8")
    if zeilen_dateien is not None:
        (ziel / "dateien.json").write_text(json.dumps({"zeilen": zeilen_dateien, "erzeugt": jetzt},
                                                      ensure_ascii=False), encoding="utf-8")


def assets(ab, ids_pfad):
    """Asset-ids nach dem Hochladen eintragen; {pdf-name oder pfad: id}."""
    ab = Path(ab).resolve()
    ord_ = ab / ".daten" / "ansicht"
    index = stand.lade(ord_ / "index.json")
    ids = {Path(k).name: v for k, v in json.loads(Path(ids_pfad).read_text(encoding="utf-8")).items()}
    for kdir in (ord_ / "moodle").glob("*/"):          # Bilder der Kursvorschau
        a_pfad = kdir / "assets.json"
        a = stand.lade(a_pfad) or {}
        for b in (kdir / "bilder").glob("*") if (kdir / "bilder").exists() else []:
            if b.name in ids:
                a[b.stem] = ids[b.name]
        if a:
            a_pfad.write_text(json.dumps(a, indent=0), encoding="utf-8")
            app = ab / ".daten" / "stand" / "app" / f"moodle_{kdir.name}.json"
            if app.exists():
                k = json.loads(app.read_text(encoding="utf-8"))
                k["bilder"] = a
                app.write_text(json.dumps(k, ensure_ascii=False), encoding="utf-8")
    n = 0
    for e in index.values():
        if e.get("pdf") in ids:
            e["asset"] = ids[e["pdf"]]
            n += 1
    (ord_ / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1, sort_keys=True),
                                     encoding="utf-8")
    rest = [p for p in (ord_ / "hochladen.txt").read_text(encoding="utf-8").split() if Path(p).name not in ids]
    (ord_ / "hochladen.txt").write_text("\n".join(rest) + ("\n" if rest else ""), encoding="utf-8")
    # Dateiliste mit den neuen ids neu schreiben
    d = json.loads((ab / ".daten" / "stand" / "app" / "dateien.json").read_text(encoding="utf-8"))
    for z in d["zeilen"]:
        z["asset"] = index.get(z["pfad"], {}).get("asset", "")
    (ab / ".daten" / "stand" / "app" / "dateien.json").write_text(json.dumps(d, ensure_ascii=False),
                                                                    encoding="utf-8")
    print(f"{n} Asset-ids eingetragen, {len(rest)} noch hochzuladen")


if __name__ == "__main__":
    if len(sys.argv) > 3 and sys.argv[2] == "--assets":
        assets(sys.argv[1], sys.argv[3])
    else:
        main(sys.argv[1] if len(sys.argv) > 1 else ".")
