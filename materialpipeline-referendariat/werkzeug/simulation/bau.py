"""Gemeinsame Hilfen für den Bau der Simulationsseiten (Logo, SVG aus PDF, stabile Vorschaubilder)."""
import base64
import io
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def logo_uri():
    """Schullogo (Profil schule.logo, neutral im Werkzeug) verkleinert als eingebettetes Bild, damit die Datei offline bleibt."""
    import sys
    from PIL import Image
    sys.path.insert(0, str(REPO / "werkzeug" / "vorlagen"))
    import schule
    im = Image.open(schule.LOGO)
    im.thumbnail((240, 130))
    puffer = io.BytesIO()
    im.save(puffer, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(puffer.getvalue()).decode()


def svg_aus_pdf(pdf, praefix=""):
    """Erste Seite eines PDF als SVG (Vektor), ohne XML-Kopf zum Einbetten. praefix: eigene Namen für Glyphen und
    Beschneidungen, wenn mehrere SVG auf einer Seite stehen (sonst nutzt das zweite die Glyphen des ersten)."""
    svg = subprocess.run(["pdftocairo", "-svg", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
    svg = svg[svg.index("<svg"):]
    if praefix:
        for alt, neu in (('id="', f'id="{praefix}'), ('href="#', f'href="#{praefix}'), ("url(#", f"url(#{praefix}")):
            svg = svg.replace(alt, neu)
    return svg


def bild_schreiben(ziel, daten):
    """Vorschau nur ersetzen, wenn sie sich sichtbar ändert (Kantenglättung schwankt um einzelne Pixel)."""
    from PIL import Image, ImageChops
    if ziel.exists():
        alt, neu = Image.open(ziel).convert("RGB"), Image.open(io.BytesIO(daten)).convert("RGB")
        if alt.size == neu.size:
            diff = ImageChops.difference(alt, neu).convert("L").point(lambda v: 255 if v > 48 else 0)
            if diff.histogram()[255] < 150:            # weniger als 150 deutlich veränderte Pixel
                return
    ziel.write_bytes(daten)
