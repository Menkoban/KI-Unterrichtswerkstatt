"""Kleiner Baukasten für die Ablaufgrafiken der README (SVG, Schulfarben).

Texte werden mit der breitesten verfügbaren Schrift (DejaVu Sans) vermessen und umbrochen, damit sie auch dann
in ihre Kästen passen, wenn der Betrachter statt Inter nur Arial oder Segoe UI hat. Reicht ein Kasten nicht,
bricht der Bau mit Fehler ab (nichts wird abgeschnitten).
"""
from __future__ import annotations

import html
import pathlib

BLAU = "#08349C"
GRUEN = "#7DDE78"
BLAU_HELL = "#E8EEF9"
BLAU_MITTEL = "#C9D6F0"
GRUEN_HELL = "#ECF9EB"
GRUEN_DUNKEL = "#1F6B1B"
TINTE = "#14213D"
GRAU = "#5B6578"
LINIE = "#D3DAE6"
HINTERGRUND = "#F7F9FC"

SCHRIFT = "Inter, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
MONO = "'JetBrains Mono', 'DejaVu Sans Mono', Consolas, monospace"

_FONTS = {
    (False, False): "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    (True, False): "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    (False, True): "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    (True, True): "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
}
_cache: dict = {}


def breite(text: str, groesse: float, fett: bool = False, mono: bool = False) -> float:
    """Breite in px, gemessen mit DejaVu (breiter als Inter, Arial, Segoe UI)."""
    try:
        from PIL import ImageFont
        key = (fett, mono, round(groesse * 4))
        if key not in _cache:
            _cache[key] = ImageFont.truetype(_FONTS[(fett, mono)], size=max(1, round(groesse * 4)))
        return _cache[key].getlength(text) / 4
    except Exception:  # ohne Pillow: grobe, großzügige Schätzung
        return len(text) * groesse * (0.62 if mono else 0.6) * (1.08 if fett else 1)


def umbrechen(text: str, groesse: float, max_breite: float, fett: bool = False, mono: bool = False) -> list[str]:
    zeilen: list[str] = []
    for absatz in text.split("\n"):
        aktuell = ""
        for wort in absatz.split(" "):
            probe = (aktuell + " " + wort).strip()
            if breite(probe, groesse, fett, mono) <= max_breite or not aktuell:
                aktuell = probe
            else:
                zeilen.append(aktuell)
                aktuell = wort
        zeilen.append(aktuell)
    for z in zeilen:
        if breite(z, groesse, fett, mono) > max_breite + 0.5:
            raise ValueError(f"Wort zu lang für {max_breite:.0f} px: {z!r}")
    return zeilen


class Svg:
    def __init__(self, w: int, h: int, titel: str):
        self.w, self.h = w, h
        self.teile: list[str] = []
        self.titel = titel
        self.rechtecke: list[tuple[str, float, float, float, float]] = []

    # Grundformen -------------------------------------------------------------------------------------------
    def rect(self, x, y, w, h, fill="#fff", stroke=LINIE, rx=12, sw=1.2, dash=None, name=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.teile.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" '
                          f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')
        if name:
            self.rechtecke.append((name, x, y, w, h))

    def text(self, x, y, s, groesse=15, fett=False, farbe=TINTE, anker="start", mono=False, kursiv=False):
        fam = MONO if mono else SCHRIFT
        gew = ' font-weight="700"' if fett else ""
        st = ' font-style="italic"' if kursiv else ""
        if mono:  # keine Ligaturen (sonst wird aus "->" ein Pfeil)
            st += ' style="font-variant-ligatures:none"' 
        self.teile.append(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-size="{groesse}"{gew}{st} '
                          f'fill="{farbe}" text-anchor="{anker}">{html.escape(s)}</text>')

    def zeilen(self, x, y, zeilen, groesse=15, abstand=1.35, **kw) -> float:
        for i, z in enumerate(zeilen):
            self.text(x, y + i * groesse * abstand, z, groesse, **kw)
        return y + (len(zeilen) - 1) * groesse * abstand

    def pille(self, x, y, s, fill=GRUEN, farbe=TINTE, groesse=12, fett=True, rechts=False) -> float:
        """Kleines Abzeichen; y ist die Oberkante. Gibt die Breite zurück."""
        w = breite(s, groesse, fett) + 16
        h = groesse + 9
        if rechts:
            x = x - w
        self.teile.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{h / 2:.1f}" '
                          f'fill="{fill}"/>')
        self.text(x + w / 2, y + h - 6.5, s, groesse, fett=fett, farbe=farbe, anker="middle")
        return w

    def pfeil(self, punkte, farbe=GRAU, sw=2.2, dash=None, kopf=True):
        d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in punkte)
        da = f' stroke-dasharray="{dash}"' if dash else ""
        mk = f' marker-end="url(#spitze{farbe.strip("#")})"' if kopf else ""
        self.teile.append(f'<path d="{d}" fill="none" stroke="{farbe}" stroke-width="{sw}" '
                          f'stroke-linejoin="round"{da}{mk}/>')
        self._farben.add(farbe)

    _farben: set = set()

    # Bausteine --------------------------------------------------------------------------------------------
    def kopf(self, titel, unter, abzeichen=()):
        self.text(40, 62, titel, 34, fett=True, farbe=BLAU)
        self.text(40, 92, unter, 16, farbe=GRAU)
        x = self.w - 40
        for a, fill, farbe in reversed(list(abzeichen)):
            w = self.pille(x, 44, a, fill=fill, farbe=farbe, groesse=13, rechts=True)
            x -= w + 8
        self.teile.append(f'<line x1="40" y1="110" x2="{self.w - 40}" y2="110" stroke="{LINIE}" stroke-width="2"/>')

    def karte(self, x, y, w, h, nummer, titel, skill=None, text="", datei=None, freigabe=None,
              gestrichelt=False, fill="#FFFFFF", nummer_fill=BLAU, titel_groesse=17, text_groesse=14.5,
              name=None):
        """Schritt-Karte: Nummer, Titel, Skill, Text, Datei, optional Freigabe-Abzeichen unten rechts."""
        self.rect(x, y, w, h, fill=fill, stroke=BLAU_MITTEL if not gestrichelt else BLAU,
                  dash="6 4" if gestrichelt else None, name=name or titel)
        innen = w - 28
        cy = y + 30
        nx = x + 14
        if nummer:
            nb = breite(nummer, 13, True) + 14
            self.teile.append(f'<rect x="{nx:.1f}" y="{cy - 16:.1f}" width="{nb:.1f}" height="21" rx="6" '
                              f'fill="{nummer_fill}"/>')
            self.text(nx + nb / 2, cy - 1, nummer, 13, fett=True, farbe="#FFFFFF", anker="middle")
            nx += nb + 9
        tz = umbrechen(titel, titel_groesse, x + w - 14 - nx, fett=True)
        cy = self.zeilen(nx, cy, tz, titel_groesse, 1.2, fett=True, farbe=TINTE)
        if skill:
            cy += 20
            for z in umbrechen(skill, 12.5, innen, mono=True):
                self.text(x + 14, cy, z, 12.5, mono=True, farbe=GRAU)
                cy += 17
            cy -= 17
        if text:
            cy += 23
            cy = self.zeilen(x + 14, cy, umbrechen(text, text_groesse, innen), text_groesse, 1.36, farbe="#2B3550")
        letzte = 0.0
        if datei:
            cy += 24
            for z in umbrechen(datei, 12.5, innen, mono=True):
                self.text(x + 14, cy, z, 12.5, mono=True, farbe=BLAU)
                letzte = breite(z, 12.5, mono=True)
                cy += 17
            cy -= 17
        unten = cy + 12
        if freigabe:
            # Abzeichen immer unten rechts an der Kartenkante, damit eine Reihe einheitlich aussieht
            unten = cy + 12 + 30
            self.pille(x + w - 12, y + h - 12 - 21, freigabe, fill=GRUEN, farbe=TINTE, groesse=12, rechts=True)
        if unten > y + h - 4:
            raise ValueError(f"Karte {titel!r} zu klein: braucht {unten - y + 6:.0f} px, hat {h}")
        return unten

    def notiz(self, x, y, w, text, groesse=13.5, farbe=GRAU, kursiv=True, anker="start", fett=False):
        z = umbrechen(text, groesse, w, fett=fett)
        if anker == "middle":
            x = x + w / 2
        return self.zeilen(x, y, z, groesse, 1.3, farbe=farbe, kursiv=kursiv, anker=anker, fett=fett)

    def pruefe_ueberlappung(self):
        r = self.rechtecke
        for i in range(len(r)):
            for j in range(i + 1, len(r)):
                a, b = r[i], r[j]
                innen = (a[1] >= b[1] and a[2] >= b[2] and a[1] + a[3] <= b[1] + b[3] and a[2] + a[4] <= b[2] + b[4]) or \
                        (b[1] >= a[1] and b[2] >= a[2] and b[1] + b[3] <= a[1] + a[3] and b[2] + b[4] <= a[2] + a[4])
                if innen:
                    continue
                if a[1] < b[1] + b[3] and b[1] < a[1] + a[3] and a[2] < b[2] + b[4] and b[2] < a[2] + a[4]:
                    raise ValueError(f"Überlappung: {a[0]!r} und {b[0]!r}")
            n, x, y, w, h = r[i]
            if x < 0 or y < 0 or x + w > self.w or y + h > self.h:
                raise ValueError(f"außerhalb der Fläche: {n!r}")

    def speichern(self, pfad: pathlib.Path):
        self.pruefe_ueberlappung()
        marker = "".join(
            f'<marker id="spitze{f.strip("#")}" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" '
            f'markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="{f}"/></marker>'
            for f in sorted(self._farben))
        kopf = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}" role="img" aria-labelledby="t">'
                f'<title id="t">{html.escape(self.titel)}</title><defs>{marker}</defs>'
                f'<rect width="{self.w}" height="{self.h}" rx="18" fill="{HINTERGRUND}"/>')
        text = kopf + "\n" + "\n".join(self.teile) + "\n</svg>\n"
        for zeichen in ("\u2013", "\u2014"):
            if zeichen in text:
                raise ValueError("Gedankenstrich in der Grafik")
        pfad.write_text(text, encoding="utf-8")
        return pfad


def kartenhoehe(w, *args, **kw) -> float:
    """Benötigte Höhe einer Karte der Breite w (Probebau auf einer leeren Fläche)."""
    probe = Svg(100000, 100000, "")
    unten = probe.karte(0, 0, w, 99999, *args, **kw)
    return unten + 10
