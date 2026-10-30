"""Symbole für Material (Sozialform), als PNG in vorlagen/symbole/, aus geometrischen Grundformen (keine KI-Bilder).

Aufruf: python werkzeug/vorlagen/symbole.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import PathPatch  # noqa: E402
from matplotlib.path import Path as MPath  # noqa: E402
from PIL import Image  # noqa: E402
from shapely import affinity  # noqa: E402
from shapely.geometry import Point, Polygon  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

ORDNER = Path(__file__).resolve().parents[2] / "vorlagen" / "symbole"
FARBE = "#4A5563"
SOZIALFORM = {"einzel": "Einzelarbeit", "partner": "Partnerarbeit", "gruppe": "Gruppenarbeit", "plenum": "Plenum"}


def _pfad(geom):
    verts, codes = [], []
    for g in (geom.geoms if hasattr(geom, "geoms") else [geom]):
        for ring in [g.exterior, *g.interiors]:
            xy = list(ring.coords)
            verts += xy
            codes += [MPath.MOVETO] + [MPath.LINETO] * (len(xy) - 2) + [MPath.CLOSEPOLY]
    return MPath(verts, codes)


def _speichern(geom, ziel):
    x0, y0, x1, y1 = geom.bounds
    fig = plt.figure(figsize=(3 * (x1 - x0) / (y1 - y0), 3), dpi=300)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.axis("off")
    ax.add_patch(PathPatch(_pfad(geom), facecolor=FARBE, edgecolor="none"))
    fig.savefig(ziel, transparent=True); plt.close(fig)
    b = Image.open(ziel); b.crop(b.getbbox()).save(ziel)


def person(x=0.0, s=1.0):
    kopf = Point(x, 0.42 * s).buffer(0.24 * s, 64)
    rumpf = Point(x, -0.55 * s).buffer(0.5 * s, 64).intersection(
        Polygon([(x - 1, -0.55 * s), (x + 1, -0.55 * s), (x + 1, 1), (x - 1, 1)]))
    return unary_union([kopf, affinity.scale(rumpf, 1.0, 1.25, origin=(x, -0.55 * s))])


def bauen():
    ORDNER.mkdir(parents=True, exist_ok=True)
    formen = {"einzel": person(),
              "partner": unary_union([person(-0.38, 0.82), person(0.38, 0.82)]),
              "gruppe": unary_union([person(-0.62, 0.7), person(0.62, 0.7), person(0, 0.82)]),
              "plenum": unary_union([person(x, 0.6) for x in (-0.9, -0.3, 0.3, 0.9)])}
    for name, g in formen.items():
        _speichern(g, ORDNER / f"sozial_{name}.png")
    return ORDNER


LUCIDE = "https://cdn.jsdelivr.net/npm/lucide-static@0.460.0/icons/{}.svg"
QUELLE_LUCIDE = "Symbole: Lucide (lucide.dev), ISC-Lizenz"


def lucide(name, ziel, farbe="#08349C", breite=300):
    """Symbol aus Lucide (frei, ISC-Lizenz) als PNG in Schulfarbe; SVG wird in vorlagen/symbole/lucide/
    zwischengespeichert. Quelle im Material: QUELLE_LUCIDE. Bevorzugt vor selbst gezeichneten Symbolen
    (Korrektur 2026-10-23)."""
    import urllib.request
    import cairosvg
    svg_pfad = ORDNER / "lucide" / f"{name}.svg"
    if not svg_pfad.exists():
        svg_pfad.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(LUCIDE.format(name), timeout=30) as antwort:
            svg_pfad.write_bytes(antwort.read())
    svg = svg_pfad.read_text().replace("currentColor", farbe)
    cairosvg.svg2png(bytestring=svg.encode(), write_to=str(ziel), output_width=breite, output_height=breite)
    return Path(ziel)


def pfad(form):
    """Pfad zum Sozialform-Symbol (baut die Symbole bei Bedarf)."""
    p = ORDNER / f"sozial_{form}.png"
    if not p.exists():
        bauen()
    return p


if __name__ == "__main__":
    print(bauen())
