"""Rechenprüfer: jede Lösung wird mit Einheiten nachgerechnet, bevor sie ins Material kommt.

Gegebene Größen und Rechenschritte werden als Pint-Größen geführt. Passt eine Einheit nicht oder weicht das
erwartete Ergebnis des Materialauftrags ab, gibt es einen Fehler im Prüfbericht. Der Abgleich durchsucht die
fertigen Materialien (DOCX/PPTX) nach Zahlen mit Einheit und meldet Werte, die zu keinem gerechneten Wert passen
(„der Fall wird in allen Anlagen gleich beschrieben“). Gegenproben über einen zweiten Weg (z. B. lcapy) sind möglich.

    r = Rechnung("DS 7 Leitungswiderstand")
    rho = r.gegeben("ρ", 0.0178, "ohm*mm**2/m")
    ...
    r.schritt("R_L", "ρ · l / A", rho.q * l.q / A.q, "ohm", stellen=2, erwartet="3,20")
    r.zeilen()     # Rechenweg mit eingesetzten Werten für Erwartungshorizont und Hilfekarten
    r.abgleich(["Muster_erwartungshorizont.docx", ...])
    r.bericht()    # Fehler / Warnung / Hinweis
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path

import pint

ureg = pint.UnitRegistry()
Q = ureg.Quantity

# Anzeige der Einheiten im Material (Schreibweise nach DIN 1338/1313, Punkt als Malzeichen)
ANZEIGE = {
    "ohm": "Ω", "kiloohm": "kΩ", "megaohm": "MΩ", "meter": "m", "millimeter": "mm", "millimeter ** 2": "mm²",
    "ohm * millimeter ** 2 / meter": "Ω·mm²/m", "kelvin": "K", "ohm / kelvin": "Ω/K", "1 / kelvin": "1/K",
    "volt": "V", "millivolt": "mV", "ampere": "A", "milliampere": "mA", "watt": "W", "kilowatt": "kW",
    "degree_Celsius": "°C", "hertz": "Hz", "second": "s", "millisecond": "ms", "dimensionless": "",
    "1 / minute": "1/min", "newton_meter": "N·m", "kilowatt_hour": "kWh", "volt * ampere": "VA",
}


def einheit_text(einheit) -> str:
    s = str(einheit)
    if s in ANZEIGE:
        return ANZEIGE[s]
    for a, b in (("ohm", "Ω"), ("degree_Celsius", "°C"), ("kelvin", "K"), ("millimeter", "mm"), ("meter", "m"),
                 ("volt", "V"), ("ampere", "A"), ("watt", "W"), (" ** 2", "²"), (" ** 3", "³"), (" ** 4", "⁴"), (" ** -1", "⁻¹"), (" * ", "·"),
                 (" / ", "/")):
        s = s.replace(a, b)
    return s


def zahl(x: float, stellen: int | None = None) -> str:
    """Deutsche Schreibweise: Komma, Leerzeichen als Tausendertrenner ab fünf Stellen."""
    if stellen is None:
        t = f"{x:.6g}"
        if "e" in t:
            m, e = t.split("e")
            return f"{m.replace('.', ',')} · 10^{{{int(e)}}}"
    else:
        t = f"{x:.{stellen}f}"
    ganz, _, rest = t.partition(".")
    if len(ganz.lstrip("-")) >= 5:
        ganz = f"{int(ganz):,}".replace(",", " ")
    return ganz + ("," + rest if rest else "")


def kurzform(einheit: str) -> str | None:
    """Einheit in der Schreibweise des Aufrufs anzeigen: "ohm*mm**2/m" → „Ω·mm²/m“ (Pint sortiert sonst um)."""
    if einheit == "dimensionless":
        return ""
    s = einheit.replace(" ", "")
    for a, b in (("**2", "²"), ("**3", "³"), ("ohm", "Ω"), ("degC", "°C"), ("delta_degC", "K"), ("*", "·")):
        s = s.replace(a, b)
    return s


def lies_zahl(s: str) -> float:
    return float(s.replace(" ", "").replace(",", "."))


@dataclass
class Groesse:
    zeichen: str
    q: pint.Quantity
    stellen: int | None = None
    text: str = ""
    art: str = "gegeben"          # gegeben | schritt | fehlerweg
    formel: str = ""
    anzeige_einheit: str | None = None

    @property
    def wert(self) -> float:
        return float(self.q.magnitude)

    @property
    def einheit(self) -> str:
        return self.anzeige_einheit if self.anzeige_einheit is not None else einheit_text(self.q.units)

    def anzeige(self) -> str:
        e = self.einheit
        return f"{zahl(self.wert, self.stellen)} {e}".strip()


@dataclass
class Rechnung:
    titel: str
    groessen: list[Groesse] = field(default_factory=list)
    meldungen: list[tuple[str, str]] = field(default_factory=list)   # (Fehler|Warnung|Hinweis, Text)

    def melden(self, stufe: str, text: str):
        if (stufe, text) not in self.meldungen:
            self.meldungen.append((stufe, text))

    def gegeben(self, zeichen, wert, einheit="dimensionless", stellen=None, text=""):
        g = Groesse(zeichen, Q(wert, einheit), stellen, text, anzeige_einheit=kurzform(einheit))
        self.groessen.append(g)
        return g

    def schritt(self, zeichen, formel, ergebnis, einheit, stellen=2, erwartet=None, text="", art="schritt"):
        """ergebnis: Pint-Größe aus den gegebenen Größen. einheit: Zieleinheit; passt die Dimension nicht,
        ist die Formel falsch (Fehler). erwartet: Wert aus dem Materialauftrag, z. B. "3,20"."""
        if isinstance(ergebnis, Groesse):
            ergebnis = ergebnis.q
        if not isinstance(ergebnis, pint.Quantity):
            ergebnis = Q(ergebnis, "dimensionless")
        try:
            q = ergebnis.to(einheit)
        except pint.DimensionalityError:
            self.melden("Fehler", f"{zeichen} = {formel}: Einheit {einheit_text(ergebnis.units)} "
                                  f"statt {einheit_text(Q(1, einheit).units)} (Formel prüfen).")
            q = Q(ergebnis.magnitude, einheit)
            erwartet = None                     # Folgemeldung sparen: die Formel ist schon falsch
        g = Groesse(zeichen, q, stellen, text, art, formel, kurzform(einheit))
        self.groessen.append(g)
        if erwartet is not None:
            soll = lies_zahl(str(erwartet))
            st = len(str(erwartet).partition(",")[2])
            if zahl(g.wert, st) != zahl(soll, st):
                self.melden("Fehler", f"{zeichen}: Materialauftrag nennt {erwartet} {g.einheit}, "
                                      f"gerechnet {zahl(g.wert, max(st, stellen or 0) + 1)} {g.einheit}.")
        return g

    def fehlerweg(self, zeichen, beschreibung, ergebnis, einheit, stellen=2, erwartet=None):
        """Typischer Fehler der Lernenden mit seinem (falschen) Ergebnis, ebenfalls nachgerechnet."""
        return self.schritt(zeichen, beschreibung, ergebnis, einheit, stellen, erwartet, art="fehlerweg")

    def gegenprobe(self, groesse: Groesse, wert, einheit, weg: str, toleranz=0.005):
        """Zweiter, unabhängiger Rechenweg (z. B. lcapy, Kennlinie). Relative Abweichung über toleranz = Fehler."""
        w = Q(wert, einheit).to(groesse.q.units).magnitude
        abw = abs(w - groesse.wert) / abs(groesse.wert) if groesse.wert else abs(w)
        if abw > toleranz:
            self.melden("Fehler", f"Gegenprobe {groesse.zeichen} über {weg}: {zahl(w, 3)} {groesse.einheit} "
                                  f"statt {zahl(groesse.wert, 3)} {groesse.einheit}.")
        else:
            self.melden("Hinweis", f"Gegenprobe {groesse.zeichen} über {weg} stimmt ({zahl(w, 3)} {groesse.einheit}).")

    # ---------- Ausgabe für das Material ----------
    def einsetzen(self, g: Groesse) -> str:
        """Formel mit eingesetzten Werten: „R_L = ρ · l / A = 0,0178 Ω·mm²/m · 90 m / 0,5 mm² = 3,20 Ω“."""
        bekannt = {x.zeichen: x for x in self.groessen if x is not g and x.zeichen}
        def ersetze(m):
            x = bekannt[m.group(0)]
            return x.anzeige()
        muster = "|".join(re.escape(z) for z in sorted(bekannt, key=len, reverse=True))
        eingesetzt = re.sub(rf"(?<![\w]){muster}(?![\w])", ersetze, g.formel) if muster else g.formel
        return f"{g.zeichen} = {g.formel} = {eingesetzt} = {g.anzeige()}"

    def zeilen(self, mit_fehlerwegen=False) -> list[str]:
        return [self.einsetzen(g) for g in self.groessen
                if g.art == "schritt" or (mit_fehlerwegen and g.art == "fehlerweg")]

    def werte(self) -> dict[str, str]:
        """Formatierte Werte zum Einsetzen in Vorlagen: werte()["R_L"] → „3,20 Ω“."""
        return {g.zeichen: g.anzeige() for g in self.groessen}

    # ---------- Abgleich mit dem fertigen Material ----------
    def abgleich(self, dateien, naehe=0.15, ignorieren=()):
        """Sucht in den Materialien Zahlen mit den Einheiten der Rechnung. Eine Zahl ist in Ordnung, wenn sie
        einem gerechneten oder gegebenen Wert in ihrer eigenen Rundung entspricht. Liegt sie nahe an einem
        Wert (± naehe), passt aber zu keinem, gibt es eine Warnung. Ferne Zahlen (z. B. 180 °C) sind andere
        Größen und werden übergangen."""
        nach_einheit: dict[str, list[Groesse]] = {}
        for g in self.groessen:
            if g.einheit:
                nach_einheit.setdefault(g.einheit, []).append(g)
        for datei in map(Path, dateien):
            text = material_text(datei)
            for e, gs in nach_einheit.items():
                for m in re.finditer(rf"(?<![\d,.])(\d+(?:,\d+)?)\s?{re.escape(e)}(?![\w²³·/])", text):
                    roh = m.group(1)
                    if roh in ignorieren:
                        continue
                    n, st = lies_zahl(roh), len(roh.partition(",")[2])
                    if any(zahl(g.wert, st) == roh for g in gs):
                        continue
                    nah = [g for g in gs if g.wert and abs(n - g.wert) / abs(g.wert) <= naehe]
                    if nah:
                        g = min(nah, key=lambda g: abs(n - g.wert))
                        umfeld = text[max(0, m.start() - 40):m.end() + 10].replace("\n", " ")
                        self.melden("Warnung", f"{datei.name}: „{roh} {e}“ passt zu keinem gerechneten Wert "
                                               f"(nächster: {g.zeichen} = {g.anzeige()}) … {umfeld} …")
            # Temperaturdifferenzen in K (Stilregel, Lehrkraft 2026-10-14: A); wörtliche Rede in „…“ bleibt
            # Alltagssprache („rund 8 °C mehr“) und wird übergangen
            for g in (g for g in nach_einheit.get("K", []) if g.art == "schritt"):
                for st in (0, 1):
                    for m in re.finditer(rf"(?<![\d,]){re.escape(zahl(g.wert, st))}\s?°C", text):
                        if in_zitat(text, m.start()):
                            continue
                        self.melden("Warnung", f"{datei.name}: Differenz „{m.group(0)}“ (= {g.zeichen}) "
                                               "in °C außerhalb wörtlicher Rede; Differenzen in K schreiben (Stilregel).")

    def bericht(self) -> str:
        rang = {"Fehler": 0, "Warnung": 1, "Hinweis": 2}
        zeilen = [f"Prüfbericht Rechnung: {self.titel}"]
        for stufe in ("Fehler", "Warnung", "Hinweis"):
            n = sum(1 for s, _ in self.meldungen if s == stufe)
            zeilen.append(f"  {stufe}: {n}")
        for s, t in sorted(self.meldungen, key=lambda m: rang[m[0]]):
            zeilen.append(f"  [{s}] {t}")
        return "\n".join(zeilen)

    @property
    def fehlerfrei(self) -> bool:
        return not any(s == "Fehler" for s, _ in self.meldungen)


def in_zitat(text: str, pos: int) -> bool:
    """Steht pos in wörtlicher Rede „…“ (bzw. "…")? Gezählt wird innerhalb des Absatzes."""
    anfang = text.rfind("\n", 0, pos) + 1
    davor = text[anfang:pos]
    return davor.count("„") > davor.count("“") or davor.count('"') % 2 == 1


def material_text(datei: Path) -> str:
    """Fließtext einer DOCX- oder PPTX-Datei (Absätze und Tabellen), sonst Textdatei."""
    if datei.suffix == ".docx":
        from docx import Document
        from docx.oxml.ns import qn
        d = Document(datei)
        teile = []
        teile_xml = [d.element.body] + [t._element for s in d.sections for t in (s.header, s.footer)]
        for wurzel in teile_xml:
            for p in wurzel.iter(qn("w:p")):
                teile.append("".join(t.text or "" for t in p.iter(qn("w:t"))))
        return "\n".join(teile)
    if datei.suffix == ".pptx":
        from pptx import Presentation
        return "\n".join(sh.text_frame.text for f in Presentation(datei).slides for sh in f.shapes
                         if sh.has_text_frame)
    return datei.read_text(encoding="utf-8")


def lcapy_widerstand(netzliste: str, a, b) -> float:
    """Ersatzwiderstand zwischen zwei Knoten einer lcapy-Netzliste (Gegenprobe für Netzwerke)."""
    from lcapy import Circuit
    return float(Circuit(netzliste).impedance(a, b).expr)
