"""Bild des Sitzplans aus dem Sitzplan-Studio (Screenshot) für Klassen-Akte und Entwürfe.

    python klasse/sitzplan_bild.py <arbeitsbereich> <kurzname der klasse>

Daten:    <arbeitsbereich>/.daten/klasse/<kurzname>.json (Raum, Lernende mit Platz und Niveau, Personas)
Ergebnis: <klassenordner>/Sitzplan.png. Grundlage ist klasse/sitzplan_studio.html (Kopie des Artefakts
„Sitzplan-Studio“); die Klasse wird als Anfangszustand eingesetzt, Kopfzeile und Seitenleiste werden
ausgeblendet, und Chromium (headless) fotografiert den Raum. Farben wie in der Pipeline: Beginner grün,
Könner blau, Experte violett; Personas als 1, 2, 3 am Rand; Punkte für Deutsch als Zweitsprache und
Unterstützungsbedarf (orange: Deutsch als Zweitsprache, rot: Unterstützungsbedarf). Nur Kürzel, keine Namen."""
import json, os, pathlib, shutil, subprocess, sys, tempfile

HIER = pathlib.Path(__file__).resolve().parent
STUDIO = HIER / "sitzplan_studio.html"
STUFE = {"Beginner": "hilfe", "Könner": "mittel", "Experte": "stark"}
FARBEN = ":root,:root[data-theme]{--lv-hilfe:#3f8f3a!important;--lv-mittel:#2f6fd1!important;--lv-stark:#7b4bb7!important;color-scheme:light}"
NUR_RAUM = ("header,.side,.roombar,.hint,#deskbar,#confirmTpl{display:none!important}"
            "body{padding:0!important;background:#fff!important}.app{gap:0!important}.main{display:block!important}"
            ".roomwrap{padding:0!important;border:0!important;border-radius:0!important}"
            ".stage{border:0!important;border-radius:0!important;width:1000px!important;height:680px!important}.room{transform:none!important}"
            ".tag-daz{background:#d9822b!important}.tag-foerder{background:#c0392b!important}")
BREITE, HOEHE = 1000, 680


def chromium():
    for c in (os.environ.get("CHROMIUM"), shutil.which("chromium"), shutil.which("chromium-browser"),
              "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"):
        if c and pathlib.Path(c).exists():
            return c
    treffer = sorted(pathlib.Path("/opt/pw-browsers").glob("chromium-*/chrome-linux/chrome"))
    return str(treffer[-1]) if treffer else None


def zustand(k):
    """Raum: je Reihe zwei Doppeltische mit Gang, Reihe 1 an der Tafel; Lehrkraft vorn links."""
    r = k["raum"]
    tische, x_links, x_rechts = [], 230, 560
    for i in range(r["reihen"]):
        y = 110 + i * 90
        tische += [{"id": f"r{i+1}a", "type": "doppel", "x": x_links, "y": y, "rot": 0},
                   {"id": f"r{i+1}b", "type": "doppel", "x": x_rechts, "y": y, "rot": 0}]
    tische += [{"id": "lk", "type": "lehrer", "x": 40, "y": 50, "rot": 0},
               {"id": "tafel", "type": "tafel", "x": 280, "y": 10, "rot": 0},
               {"id": "tuer", "type": "tuer", "x": 10, "y": 650, "rot": 0},
               {"id": "fenster", "type": "fenster", "x": 986, "y": 150, "rot": 0}]
    lernende = []
    for x in k["lernende"]:
        reihe, platz = x["platz"]
        tisch = f"r{reihe}{'a' if platz <= 2 else 'b'}"
        text = x.get("kommentar", "")
        tags = (["daz"] if ("Zweitsprache" in text or "DaZ" in text) else []) + \
               (["foerder"] if ("Unterstützungsbedarf" in text or "Förderbedarf" in text) else [])
        persona = x["kurz"][1] if x.get("kurz", "").startswith("P") and x["kurz"][1:2].isdigit() else ""
        lernende.append({"id": x["k"], "kz": x["k"], "name": "", "level": STUFE[x["niveau"]], "tags": tags,
                         "persona": persona, "betrieb": "", "methoden": "", "note": "",
                         "seat": {"desk": tisch, "idx": (platz - 1) % 2}})
    return {"desks": tische, "students": lernende, "showNames": False}


def erzeugen(ab, kurz):
    ab = pathlib.Path(ab)
    k = json.loads((ab / ".daten" / "klasse" / f"{kurz}.json").read_text(encoding="utf-8"))
    ziel = ab / k["ordner"] / "Sitzplan.png"; ziel.parent.mkdir(parents=True, exist_ok=True)
    html = STUDIO.read_text(encoding="utf-8")
    html = html.replace("let state=load();", "let state=" + json.dumps(zustand(k), ensure_ascii=False) + ";")
    html = html.replace("</head>", f"<style>{FARBEN}{NUR_RAUM}</style></head>", 1)
    html = html.replace("<title>Sitzplan-Studio</title>", f"<title>Sitzplan-Studio</title><style>{FARBEN}{NUR_RAUM}</style>", 1)
    c = chromium()
    if not c:
        raise SystemExit("Chromium nicht gefunden (Umgebungsvariable CHROMIUM setzen)")
    with tempfile.TemporaryDirectory() as t:
        seite = pathlib.Path(t) / "sitzplan.html"; seite.write_text(html, encoding="utf-8")
        subprocess.run([c, "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars", "--force-color-profile=srgb",
                        "--force-device-scale-factor=2", f"--window-size={BREITE},{HOEHE + 200}", "--virtual-time-budget=4000",
                        f"--screenshot={ziel}", seite.as_uri()], check=True, capture_output=True, timeout=120)
    # Das Fenster ist höher als der Raum (headless zieht die Fensterleiste ab); auf den Raum zuschneiden.
    from PIL import Image
    with Image.open(ziel) as im:
        f = im.width / BREITE
        im.crop((0, 0, im.width, int(HOEHE * f))).save(ziel)
    return ziel


if __name__ == "__main__":
    print(erzeugen(sys.argv[1], sys.argv[2]))
