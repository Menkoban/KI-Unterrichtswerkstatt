"""Probe der Quellenaufnahme (Teil des Probelaufs): erzeugt ein Foto mit deutschem Text und ein PDF ohne
Textschicht, nimmt beide in ein Testverzeichnis auf und prüft Texterkennung, Quellenkarte, Doppelerkennung und
Suche. Das Repo bleibt unberührt.
"""
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aufnehmen import aufnehmen, karte_lesen  # noqa: E402
from suche import suchen  # noqa: E402

TEXT = ["Wendeschützschaltung mit Tasterverriegelung", "Die Selbsthaltung überbrückt den Ein-Taster.",
        "Größe des Bemessungsstroms: 3,3 A"]
fehler = []
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    schrift = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 44)
    bild = Image.new("RGB", (1800, 500), "white")
    d = ImageDraw.Draw(bild)
    for i, z in enumerate(TEXT):
        d.text((60, 60 + i * 120), z, fill="black", font=schrift)
    bild.save(tmp / "foto.jpg", quality=90)
    bild.save(tmp / "scan.pdf")                          # PDF ohne Textschicht → Seite wird gerendert und erkannt
    wurzel = tmp / "quellen"
    e1, m1 = aufnehmen(tmp / "foto.jpg", "fachbuch", "Probe Fachbuch", "1. Aufl.", 12, "Probe", wurzel=wurzel)
    e2, m2 = aufnehmen(tmp / "scan.pdf", "material", "Probe Arbeitsblatt", "", "", "Probe", wurzel=wurzel)
    e3, m3 = aufnehmen(tmp / "foto.jpg", "fachbuch", "Probe Fachbuch", "1. Aufl.", 12, "Probe", wurzel=wurzel)
    if len(karte_lesen(wurzel)) != 2 or "schon vorhanden" not in m3:
        fehler.append("Doppelte Datei nicht erkannt")
    for e in (e1, e2):
        text = (wurzel / e["datei"]).with_suffix(".txt").read_text(encoding="utf-8")
        for wort in ("Wendeschützschaltung", "Selbsthaltung", "überbrückt", "Größe"):
            if wort not in text:
                fehler.append(f"{e['datei']}: „{wort}“ nicht erkannt")
    if "Seite unbekannt" not in e2["hinweis"]:
        fehler.append("fehlende Seitenangabe nicht gemeldet")
    if len(suchen("tasterverriegelung", wurzel)) != 2:
        fehler.append("Suche findet nicht beide Quellen")
    if not (wurzel / "_karte" / "karte.md").exists():
        fehler.append("karte.md fehlt")
print("Probe Quellenaufnahme:", "OK" if not fehler else "Fehler")
for f in fehler:
    print("  [Fehler]", f)
sys.exit(1 if fehler else 0)
