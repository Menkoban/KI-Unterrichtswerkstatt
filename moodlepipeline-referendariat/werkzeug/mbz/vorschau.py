"""Kursvorschau für die Werkbank: liest eine gebaute Sicherung (.mbz) oder, solange der Kurs entsteht, die
Bausteine im Ordner bau/ und schreibt daraus eine Vorschau im Aufbau des Moodle-Kurses.

    python3 werkzeug/mbz/vorschau.py <Moodle-Ordner der LS> <Zielordner>

<Moodle-Ordner> ist z. B. .../LS01_.../Moodle (mit <kurz>.mbz oder bau/kursdefinition.json). Ergebnis im Zielordner:
kurs.json (Kurs, Abschnitte, Aktivitäten, Bau-Stand), inhalte.json (HTML je Seite, Textfeld, Test) und bilder/ mit
den Bildern der Kacheln und Seiten (für den Upload als Asset). Bilder stehen im HTML als @@BILD:<hash>@@; die Seite
setzt die Asset-Adresse ein. Skripte und Ereignis-Attribute werden entfernt; Audio, Dateien und Fragen erscheinen
als Hinweis. Lehrkraft 2026-10-24: den Kurs in der Werkbank sehen, auch während er sich aufbaut.
"""
import json
import re
import shutil
import sys
import tarfile
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

BILDTYPEN = {"image/png": ".png", "image/jpeg": ".jpg", "image/svg+xml": ".svg", "image/gif": ".gif", "image/webp": ".webp"}
TYPNAME = {"page": "Textseite", "quiz": "Test", "assign": "Aufgabe", "folder": "Verzeichnis", "resource": "Datei",
           "label": "Textfeld", "glossary": "Glossar", "data": "Datenbank", "feedback": "Feedback", "url": "Link",
           "forum": "Forum", "h5pactivity": "H5P", "lesson": "Lektion", "choice": "Abstimmung"}
GRENZE_HTML = 60000


def saeubern(html):
    html = re.sub(r"<script\b.*?</script>", "", html or "", flags=re.S | re.I)
    html = re.sub(r"\son[a-z]+\s*=\s*(\"[^\"]*\"|'[^']*')", "", html, flags=re.I)
    html = re.sub(r"javascript:", "", html, flags=re.I)
    return html


def text(el, pfad):
    x = el.find(pfad)
    return x.text if x is not None and x.text and x.text != "$@NULL@$" else ""


def aus_mbz(mbz, ziel):
    with tempfile.TemporaryDirectory() as tmp:
        with tarfile.open(mbz, "r:gz") as t:
            t.extractall(tmp, filter="data")
        tmp = Path(tmp)
        info = ET.parse(tmp / "moodle_backup.xml").getroot().find("information")
        course = ET.parse(tmp / "course" / "course.xml").getroot()
        # Dateien: (contextid, component, filearea, itemid, filename) -> (hash, mimetype)
        dateien = {}
        for f in ET.parse(tmp / "files.xml").getroot():
            if text(f, "filename") in (".", ""):
                continue
            dateien[(text(f, "contextid"), text(f, "component"), text(f, "filearea"), text(f, "itemid"),
                     text(f, "filename"))] = (text(f, "contenthash"), text(f, "mimetype"))
        bilder = ziel / "bilder"
        bilder.mkdir(parents=True, exist_ok=True)

        def bild(h, mime):
            endung = BILDTYPEN.get(mime)
            if not endung:
                return None
            quelle = tmp / "files" / h[:2] / h
            if quelle.exists() and quelle.stat().st_size < 4_000_000:
                shutil.copyfile(quelle, bilder / (h + endung))
                return h
            return None

        def plugin(html, ctx, comp, area, item):
            def ersetze(m):
                name = m.group(1).split("?")[0]
                from urllib.parse import unquote
                d = dateien.get((ctx, comp, area, item, unquote(name)))
                if d and bild(*d):
                    return f"@@BILD:{d[0]}@@"
                return "#datei:" + unquote(name)
            return re.sub(r"@@PLUGINFILE@@/([^\"'\s)>]+)", ersetze, html)

        kurs_ctx = course.get("contextid") or ""
        akt = {}
        for a in info.find("contents").find("activities"):
            akt[text(a, "moduleid")] = {"typ": text(a, "modulename"), "name": text(a, "title"), "ordner": text(a, "directory")}
        inhalte, abschnitte = {}, []
        for s in info.find("contents").find("sections"):
            sx = ET.parse(tmp / text(s, "directory") / "section.xml").getroot()
            sid = sx.get("id")
            kachel = next((v[0] for k, v in dateien.items() if k[1] == "format_tiles" and k[3] == sid and bild(*v)), None)
            liste = []
            for mid in [m for m in text(sx, "sequence").split(",") if m]:
                a = akt.get(mid)
                if not a:
                    continue
                ordner = tmp / a["ordner"]
                modul = ET.parse(ordner / "module.xml").getroot()
                ax = ET.parse(ordner / f"{a['typ']}.xml").getroot()
                ctx = ax.get("contextid") or ""
                inner = ax[0]
                intro = plugin(saeubern(text(inner, "intro")), ctx, "mod_" + a["typ"], "intro", "0")
                html = intro
                if a["typ"] == "page":
                    html = plugin(saeubern(text(inner, "content")), ctx, "mod_page", "content", "0")
                elif a["typ"] == "quiz":
                    n = len(inner.findall(".//question_instance"))
                    html = intro + f"<p class='mv-hinweis'>Test mit {n} Fragen. Die Fragen sehen Sie im Moodle-Kurs.</p>"
                elif a["typ"] in ("folder", "resource"):
                    namen = [k[4] for k in dateien if k[0] == ctx and k[2] == "content"]
                    html = intro + ("<ul>" + "".join(f"<li>{n}</li>" for n in sorted(namen)) + "</ul>" if namen else "")
                inhalte[mid] = html[:GRENZE_HTML]
                liste.append({"id": mid, "typ": a["typ"], "art": TYPNAME.get(a["typ"], a["typ"]), "name": a["name"],
                              "sichtbar": text(modul, "visible") != "0", "einrueckung": int(text(modul, "indent") or 0),
                              "label": a["typ"] == "label"})
            abschnitte.append({"nr": int(text(sx, "number") or 0), "name": text(sx, "name") or ("Allgemeines" if text(sx, "number") == "0" else f"Abschnitt {text(sx, 'number')}"),
                               "zusammenfassung": plugin(saeubern(text(sx, "summary")), kurs_ctx, "course", "section", sid)[:GRENZE_HTML],
                               "sichtbar": text(sx, "visible") != "0", "kachel": kachel, "aktivitaeten": liste, "stand": "gebaut"})
        abschnitte.sort(key=lambda x: x["nr"])
        kurs = {"name": text(info, "original_course_fullname"), "kurzname": text(info, "original_course_shortname"),
                "format": text(course, "format"), "zusammenfassung": saeubern(text(course, "summary"))[:GRENZE_HTML],
                "quelle": "mbz", "datei": Path(mbz).name}
        return kurs, abschnitte, inhalte


def aus_bau(moodle, ziel):
    """Während des Baus: Kursdefinition und fertige Abschnitte aus bau/ (noch ohne Sicherung)."""
    bau = moodle / "bau"
    k = json.loads((bau / "kursdefinition.json").read_text(encoding="utf-8"))
    bilder = ziel / "bilder"
    bilder.mkdir(parents=True, exist_ok=True)
    abschnitte, inhalte = [], {}
    for i, a in enumerate(k.get("abschnitte", [])):
        datei = bau / f"abschnitt_{i}.json"
        fertig = datei.exists()
        d = json.loads(datei.read_text(encoding="utf-8")) if fertig else a
        liste = []
        for j, x in enumerate(d.get("aktivitaeten", [])):
            mid = f"{i}_{j}"
            typ = x.get("typ", "geplant")
            liste.append({"id": mid, "typ": typ, "art": TYPNAME.get(typ, "geplant"), "name": x.get("name") or x.get("platzhalter", ""),
                          "sichtbar": True, "einrueckung": 0, "label": typ == "label", "geplant": "platzhalter" in x})
            inhalte[mid] = saeubern(x.get("inhalt") or x.get("intro") or "")[:GRENZE_HTML]
        abschnitte.append({"nr": i, "name": d.get("name", f"Abschnitt {i}"), "zusammenfassung": saeubern(d.get("zusammenfassung", ""))[:GRENZE_HTML],
                           "sichtbar": d.get("sichtbar", True), "kachel": None, "aktivitaeten": liste,
                           "stand": "gebaut" if fertig else "geplant"})
    kurs = {"name": k["kurs"].get("vollname", ""), "kurzname": k["kurs"].get("kurzname", ""), "format": k["kurs"].get("format", "tiles"),
            "zusammenfassung": saeubern(k["kurs"].get("beschreibung", "")), "quelle": "bau", "datei": ""}
    return kurs, abschnitte, inhalte


def main(moodle, ziel):
    moodle, ziel = Path(moodle).resolve(), Path(ziel).resolve()
    if ziel.exists():
        shutil.rmtree(ziel / "bilder", ignore_errors=True)
    ziel.mkdir(parents=True, exist_ok=True)
    mbz = sorted(moodle.glob("*.mbz"), key=lambda p: p.stat().st_mtime)
    neuer_bau = (moodle / "bau" / "kursdefinition.json").exists() and (not mbz or max(
        p.stat().st_mtime for p in (moodle / "bau").glob("abschnitt_*.json")) > mbz[-1].stat().st_mtime + 60)
    kurs, abschnitte, inhalte = aus_bau(moodle, ziel) if (neuer_bau or not mbz) else aus_mbz(mbz[-1], ziel)
    gebaut = sum(a["stand"] == "gebaut" for a in abschnitte)
    kurs["bau"] = {"abschnitte": len(abschnitte), "gebaut": gebaut, "aktivitaeten": sum(len(a["aktivitaeten"]) for a in abschnitte)}
    (ziel / "kurs.json").write_text(json.dumps({"kurs": kurs, "abschnitte": abschnitte}, ensure_ascii=False), encoding="utf-8")
    (ziel / "inhalte.json").write_text(json.dumps(inhalte, ensure_ascii=False), encoding="utf-8")
    print(f"{kurs['kurzname']}: {len(abschnitte)} Abschnitte ({gebaut} gebaut), {kurs['bau']['aktivitaeten']} Aktivitäten, "
          f"{len(list((ziel / 'bilder').iterdir()))} Bilder, Quelle {kurs['quelle']}")
    return ziel


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
