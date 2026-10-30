"""Word-Dateien (DOCX) als HTML für eine Moodle-Textseite.

    html, bilder = docx_zu_html(pfad)          # eine DOCX
    html, dateien = docx_seite_html([a, b])    # Seite: je DOCX ein Abschnitt

Überschriften werden h3/h4 (h1/h2 belegt Moodle selbst), Absätze, fett/kursiv,
Listen und Tabellen bleiben erhalten. Eingebettete Bilder werden als Dateien
in einen Zwischenordner geschrieben; `alt` kommt aus der Bildbeschreibung in
Word, fehlt sie, gilt das Bild als Schmuck (`alt=""`, `role="presentation"`).
Alle Verweise stehen als `@@PLUGINFILE@@/<dateiname>`; die zurückgegebenen
Dateien gehören in den Dateibereich der Seite.
"""
from __future__ import annotations

import html as _html
import io
import os
import re
import tempfile
import urllib.parse
from pathlib import Path

import docx
from docx.oxml.ns import qn
from docx.table import Table, _Cell
from docx.text.hyperlink import Hyperlink
from docx.text.paragraph import Paragraph

PDF_KNOPF = "Als PDF herunterladen"
WORD_KNOPF = "Als Word herunterladen"
PDF_HINWEIS = "Das PDF können Sie direkt ausfüllen, am Tablet oder am PC. Speichern nicht vergessen."
_SYMBOL = '<i class="fa {} me-1" style="color:{};" aria-hidden="true"></i>'

# Moodle filtert HTML: nur einfache Inline-Stile, kein position, keine Verläufe.
BILD_STIL = "max-width:100%;height:auto;"
SCHREIBLINIE = ('<span class="schreiblinie" style="display:inline-block;min-width:6em;'
                'width:60%;border-bottom:1px solid #9AA3AE;"></span>')
LINIENABSATZ = '<div style="border-bottom:1px solid #9AA3AE;height:1.6em;"></div>'
_UNTERSTRICHE = re.compile(r"_{5,}(?![^<]*>)")  # nicht innerhalb eines Tags
_NUR_UNTERSTRICHE = re.compile(r"\s*_{5,}\s*")
# Papier-Fußzeile der Blätter aus Pipeline 2 („LF 1 · LS 1 · DS 3 …“, „KI-gestützt erstellt“)
_FUSSZEILE = re.compile(r"\bLF\s*\d+\s*·\s*LS\s*\d+|KI-gestützt erstellt")
FUSS_STIL = "font-size:smaller;color:#6B7280;"
# Karten (Durchsicht LS 1, Punkt 26): untereinander, Kopf in Schulblau; Hilfekarten als gelber Kasten
KARTE_STIL = "margin:0 0 1em 0;border:1px solid #08349C;border-radius:6px;"
KARTE_KOPF_STIL = "background:#08349C;color:#fff;padding:0.4em 0.8em;border-radius:5px 5px 0 0;"
HILFE_STIL = "margin:0 0 1em 0;background:#FFF4CC;border:1px solid #E0A800;border-radius:6px;"
HILFE_KOPF_STIL = "padding:0.4em 0.8em;"
KARTE_INHALT_STIL = "padding:0.4em 0.8em;"
_ANLAGE = re.compile(r"^(?:DS\d+_)?(?:Anl_?\d+[a-z]?_)?", re.IGNORECASE)


def _lies(pfad: Path) -> bytes:
    """Datei lesen, auch jenseits der Windows-Pfadgrenze von 260 Zeichen."""
    pfad = Path(pfad)
    try:
        return pfad.read_bytes()
    except (FileNotFoundError, OSError):
        if os.name != "nt":
            raise
        return Path("\\\\?\\" + str(pfad.resolve())).read_bytes()


def _sicher(name: str) -> str:
    """Dateinamensteil ohne Leer- und Sonderzeichen."""
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("_") or "datei"


def _url(name: str) -> str:
    return "@@PLUGINFILE@@/" + urllib.parse.quote(name)


class _Wandler:
    """Wandelt eine geöffnete DOCX in HTML und sammelt die Bilder."""

    def __init__(self, dok, stamm: str, ziel: Path):
        self.dok = dok
        self.stamm = _sicher(stamm)
        self.ziel = ziel
        self.bilder: list[Path] = []
        self.fuss: list[str] = []   # Papier-Fußzeilen, je Text einmal; stehen am Ende der Seite
        self.karten: list[tuple[str, bool]] = []   # (Kartentitel, Hilfekarte?) in Dokumentreihenfolge
        self._rid_datei: dict[str, str] = {}
        self._nummern = self._nummernformate()

    # -- Listen ---------------------------------------------------------- #
    def _nummernformate(self) -> dict[tuple[str, str], str]:
        """(numId, ilvl) → numFmt, z. B. 'bullet' oder 'decimal'."""
        try:
            wurzel = self.dok.part.numbering_part.element
        except (KeyError, NotImplementedError, AttributeError):
            return {}
        abstrakt: dict[str, dict[str, str]] = {}
        for an in wurzel.findall(qn("w:abstractNum")):
            ebenen = {}
            for lvl in an.findall(qn("w:lvl")):
                fmt = lvl.find(qn("w:numFmt"))
                ebenen[lvl.get(qn("w:ilvl"))] = fmt.get(qn("w:val")) if fmt is not None else "decimal"
            abstrakt[an.get(qn("w:abstractNumId"))] = ebenen
        formate = {}
        for num in wurzel.findall(qn("w:num")):
            ref = num.find(qn("w:abstractNumId"))
            if ref is None:
                continue
            for ilvl, fmt in abstrakt.get(ref.get(qn("w:val")), {}).items():
                formate[(num.get(qn("w:numId")), ilvl)] = fmt
        return formate

    def _listenart(self, p: Paragraph) -> str | None:
        """'ul', 'ol' oder None für einen Absatz."""
        num_pr = None
        if p._p.pPr is not None and p._p.pPr.numPr is not None:
            num_pr = p._p.pPr.numPr
        else:
            stil = p.style
            while stil is not None and num_pr is None:
                ppr = stil.element.pPr
                if ppr is not None and ppr.numPr is not None:
                    num_pr = ppr.numPr
                stil = stil.base_style
        if num_pr is not None and num_pr.numId is not None:
            num_id = str(num_pr.numId.val)
            if num_id == "0":
                return None
            ilvl = str(num_pr.ilvl.val) if num_pr.ilvl is not None else "0"
            fmt = self._nummern.get((num_id, ilvl))
            if fmt is not None:
                return "ul" if fmt in ("bullet", "none") else "ol"
        name = (p.style.name or "").lower() if p.style is not None else ""
        if "number" in name or "nummer" in name:
            return "ol"
        if "bullet" in name or "aufzählung" in name or num_pr is not None:
            return "ul"
        return None

    # -- Inline ---------------------------------------------------------- #
    def _bild(self, rid: str, alt: str | None, stil: str = BILD_STIL) -> str:
        if rid not in self._rid_datei:
            teil = self.dok.part.related_parts[rid]
            endung = Path(str(teil.partname)).suffix.lower() or ".bin"
            name = f"{self.stamm}_bild{len(self.bilder) + 1}{endung}"
            datei = self.ziel / name
            datei.write_bytes(teil.blob)
            self.bilder.append(datei)
            self._rid_datei[rid] = name
        name = self._rid_datei[rid]
        if alt and alt.strip():
            return (f'<img src="{_url(name)}" alt="{_html.escape(alt.strip())}" '
                    f'style="{stil}" />')
        return f'<img src="{_url(name)}" alt="" role="presentation" style="{stil}" />'

    def _lauf(self, run) -> list[tuple[bool, bool, str]]:
        """Teile eines Laufs: (fett, kursiv, html)."""
        teile = []
        fett, kursiv = bool(run.bold), bool(run.italic)
        for kind in run._r:
            if kind.tag == qn("w:t"):
                teile.append((fett, kursiv, _html.escape(kind.text or "", quote=False)))
            elif kind.tag == qn("w:tab"):
                teile.append((fett, kursiv, " "))
            elif kind.tag in (qn("w:br"), qn("w:cr")):
                teile.append((False, False, "<br />"))
            elif kind.tag == qn("w:drawing"):
                for blip in kind.iter(qn("a:blip")):
                    rid = blip.get(qn("r:embed"))
                    if rid:
                        doc_pr = next(kind.iter(qn("wp:docPr")), None)
                        alt = doc_pr.get("descr") if doc_pr is not None else None
                        teile.append((False, False, self._bild(rid, alt)))
        return teile

    def _inline(self, p: Paragraph) -> str:
        teile: list[tuple[bool, bool, str]] = []
        for stueck in p.iter_inner_content():
            if isinstance(stueck, Hyperlink):
                innen = "".join(t for _, _, t in
                                (x for r in stueck.runs for x in self._lauf(r)))
                adresse = stueck.address
                if adresse:
                    teile.append((False, False,
                                  f'<a href="{_html.escape(adresse)}">{innen}</a>'))
                else:
                    teile.append((False, False, innen))
            else:
                teile.extend(self._lauf(stueck))
        # gleich formatierte Nachbarn zusammenfassen
        aus, gruppe, fmt = [], [], None
        for fett, kursiv, text in teile + [(None, None, None)]:
            if (fett, kursiv) != fmt and gruppe:
                inhalt = "".join(gruppe)
                if fmt[1] and inhalt.strip():
                    inhalt = f"<em>{inhalt}</em>"
                if fmt[0] and inhalt.strip():
                    inhalt = f"<strong>{inhalt}</strong>"
                aus.append(inhalt)
                gruppe = []
            fmt = (fett, kursiv)
            if text is not None:
                gruppe.append(text)
        return _UNTERSTRICHE.sub(SCHREIBLINIE, "".join(aus).strip())

    # -- Blöcke ---------------------------------------------------------- #
    @staticmethod
    def _ueberschrift(p: Paragraph) -> str | None:
        name = (p.style.name or "").lower() if p.style is not None else ""
        if name in ("title", "titel"):
            return "h3"
        m = re.match(r"(heading|überschrift)\s*(\d)", name)
        if m:
            return "h3" if m.group(2) == "1" else "h4"
        return None

    @staticmethod
    def _rohtext(element) -> str:
        """Exakter Text eines Elements (Leerzeichen zählen), samt Tab und Umbruch."""
        teile = []
        for kind in element.iter(qn("w:t"), qn("w:tab"), qn("w:br"), qn("w:cr"), qn("w:tc")):
            if kind.tag == qn("w:t"):
                teile.append(kind.text or "")
            elif kind.tag == qn("w:tc"):
                teile.append("\x1e")  # Zellgrenze
            else:
                teile.append("\x1f")  # Tab oder Umbruch
        return "".join(teile)

    @staticmethod
    def _hat_bild(element) -> bool:
        return next(element.iter(qn("a:blip")), None) is not None

    @classmethod
    def _leer(cls, tc) -> bool:
        return not cls._rohtext(tc).strip(" \t\n\x1e\x1f\xa0") and not cls._hat_bild(tc)

    @classmethod
    def _kopftabelle(cls, tbl) -> bool:
        """Schul- bzw. Kartenkopf: eine einzige Zeile mit Text und Bild (Logo)."""
        return (len(tbl.tr_lst) == 1 and cls._hat_bild(tbl)
                and bool(re.search(r"[^\s\x1e\x1f]", cls._rohtext(tbl))))

    def _karte(self, zelle: _Cell) -> str | None:
        """Eine Zelle, die mit einem Kartenkopf beginnt, als Kartenblock; sonst None."""
        bloecke = list(zelle.iter_inner_content())
        while (bloecke and isinstance(bloecke[0], Paragraph) and not bloecke[0].text.strip()
               and not self._hat_bild(bloecke[0]._p)):
            bloecke.pop(0)
        if not bloecke or not isinstance(bloecke[0], Table) or not self._kopftabelle(bloecke[0]._tbl):
            return None
        kopf = bloecke.pop(0)
        kopfzellen = [_Cell(tc, kopf) for tc in kopf._tbl.tr_lst[0].tc_lst]
        zeilen = [self._inline(p) for z in kopfzellen for p in z.paragraphs if p.text.strip()]
        titel = "<br />".join([f'<span style="font-size:smaller;">{z}</span>' for z in zeilen[:-1]]
                              + zeilen[-1:])
        hilfe = "hilfe" in " ".join(z.text for z in kopfzellen).lower()
        letzte = [p.text.strip() for z in kopfzellen for p in z.paragraphs if p.text.strip()][-1:]
        if letzte:
            self.karten.append((letzte[0], hilfe))
        inhalt = self._bloecke(bloecke)
        return (f'<div class="karte" style="{HILFE_STIL if hilfe else KARTE_STIL}">'
                f'<div style="{HILFE_KOPF_STIL if hilfe else KARTE_KOPF_STIL}">{titel}</div>'
                f'<div style="{KARTE_INHALT_STIL}">\n{inhalt}\n</div></div>')

    def _tabelle(self, t: Table) -> str:
        zeilen, karten = [], []
        nur_karten = True
        vorige = None
        kopf = self._kopftabelle(t._tbl)
        for tr in t._tbl.tr_lst:
            tcs = list(tr.tc_lst)
            spalten = 0
            # Ausschneidebogen nebeneinander: alle Zellen der Zeile exakt gleich (Leerzeichen zählen,
            # mit Text, ohne verbundene Zellen) → eine Zelle über die ganze Breite.
            texte = {self._rohtext(tc) for tc in tcs}
            if (len(tcs) > 1 and len(texte) == 1
                    and all(tc.grid_span == 1 and tc.vMerge is None for tc in tcs)
                    and re.search(r"[^\s_\x1e\x1f]", next(iter(texte)))):
                spalten, tcs = len(tcs), tcs[:1]
            # Ausschneidebogen untereinander: eine Zeile aus einer Zelle je Kopie; dieselbe Kopie
            # direkt darunter nur einmal zeigen. Exakter Text, Leerzeichen zählen.
            # Zeilen nur aus Linien (Ausfüllzeilen) bleiben.
            roh = "\x1e" + self._rohtext(tcs[0]) if len(tcs) == 1 else None
            kopie = roh is not None and bool(re.search(r"[^\s_\x1e\x1f]", roh))
            if kopie and roh == vorige:
                continue
            vorige = roh if kopie else None
            if kopf:   # Schul- bzw. Kartenkopf: leere Zellen (ohne Text, ohne Bild) weglassen
                tcs = [tc for tc in tcs if not self._leer(tc)] or tcs[:1]
            zellen = []
            for tc in tcs:
                if tc.vMerge == "continue":
                    continue
                attr = ""
                if spalten > 1:
                    attr += f' colspan="{spalten}"'
                elif tc.grid_span > 1:
                    attr += f' colspan="{tc.grid_span}"'
                if tc.vMerge == "restart":
                    try:
                        hoehe = tc.bottom - tc.top
                    except ValueError:  # unregelmäßige Tabelle: keine Zelle darunter
                        hoehe = 1
                    if hoehe > 1:
                        attr += f' rowspan="{hoehe}"'
                zelle = _Cell(tc, t)
                karte = self._karte(zelle)
                if karte is not None:
                    karten.append(karte)
                    inhalt = karte
                else:
                    if not self._leer(tc):
                        nur_karten = False
                    inhalt = self._bloecke(zelle.iter_inner_content(), in_zelle=True)
                zellen.append(f"<td{attr}>{inhalt}</td>")
            zeilen.append("<tr>" + "".join(zellen) + "</tr>")
        if karten and nur_karten:   # Kartenbogen: Karten untereinander statt Tabelle
            return "\n".join(karten)
        return '<table class="table table-bordered">\n' + "\n".join(zeilen) + "\n</table>"

    def _bloecke(self, inhalt, in_zelle: bool = False) -> str:
        aus: list[str] = []
        liste: str | None = None
        bloecke = list(inhalt)
        for block in bloecke:
            art = self._listenart(block) if isinstance(block, Paragraph) else None
            if liste and art != liste:
                aus.append(f"</{liste}>")
                liste = None
            if isinstance(block, Table):
                aus.append(self._tabelle(block))
                continue
            if not art and _NUR_UNTERSTRICHE.fullmatch(block.text):
                aus.append(LINIENABSATZ)
                continue
            if not art and not self._ueberschrift(block) and _FUSSZEILE.search(block.text):
                fuss = self._inline(block)
                if fuss and fuss not in self.fuss:
                    self.fuss.append(fuss)
                continue
            text = self._inline(block)
            if not text:
                continue
            if art:
                if liste is None:
                    aus.append(f"<{art}>")
                    liste = art
                aus.append(f"<li>{text}</li>")
                continue
            ebene = self._ueberschrift(block)
            if ebene:
                aus.append(f"<{ebene}>{text}</{ebene}>")
            elif in_zelle and len(bloecke) == 1:
                aus.append(text)
            else:
                aus.append(f"<p>{text}</p>")
        if liste:
            aus.append(f"</{liste}>")
        return "\n".join(aus)


# --------------------------------------------------------------------------- #
# Heft-Stil (Lehrkraft 2026-10-27): die Infoseite sieht aus wie der Infokasten im Arbeitsblatt. Alles kommt
# aus der direkten Formatierung der Word-Datei (Zellfarbe, Rahmen, Innenabstand, Schriftgröße, Farbe),
# Formeln (OMML) werden TeX für MathJax. Breite 680 px wie die Textbreite des Blatts (10 207 Twips).
# --------------------------------------------------------------------------- #
HEFT_STIL = "font-family:Arial,Helvetica,sans-serif;color:#1B1F24;font-size:15px;line-height:1.45;"
HEFT_GRUND = 21          # halbe Punkt: Grundschrift der Blätter (10,5 pt) = 15 px
_PX_JE_HALBPUNKT = 15 / 21
_TWIP_PX = 1 / 15        # 680 px auf 10 207 Twips
_EMU_PX = 1 / 9525
M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
_TEX_ZEICHEN = {"·": r"\cdot ", "×": r"\times ", "−": "-", "≈": r"\approx ", "≤": r"\le ", "≥": r"\ge ",
                "Ω": r"\Omega ", "Δ": r"\Delta ", "η": r"\eta ", "ϑ": r"\vartheta ", "θ": r"\theta ",
                "ρ": r"\rho ", "α": r"\alpha ", "φ": r"\varphi ", "π": r"\pi ", "%": r"\%", "°": r"^\circ ",
                "€": r"\text{€}", " ": r"\,", "→": r"\rightarrow ", "{": r"\{", "}": r"\}",
                "#": r"\#", "&": r"\&", "_": r"\_", "$": r"\$"}
_ADRESSE = re.compile(r"https?://[^\s<>\"]*[^\s<>\".,;:)]")
_AB = re.compile(r"\bAB(\s|&nbsp;)(\d+)\b(?![^<]*>)")   # \s umfasst das geschützte Leerzeichen


def _tex_text(t: str) -> str:
    return "".join(_TEX_ZEICHEN.get(z, z) for z in t)


def omml_tex(el) -> str:
    """OMML (Word-Formel) als TeX: Brüche, Indizes, Normaltext; reicht für die Formeln der Blätter."""
    tag = el.tag
    if tag == M + "r":
        t = "".join(x.text or "" for x in el.iter(M + "t"))
        rpr = el.find(M + "rPr")
        if rpr is not None and rpr.find(M + "nor") is not None:
            return r"\text{" + t.replace("\\", "").replace("{", "").replace("}", "") + "}" if t.strip() \
                else (r"\;" if t else "")
        sty = rpr.find(M + "sty").get(M + "val") if rpr is not None and rpr.find(M + "sty") is not None else "i"
        tex = _tex_text(t)
        return r"\mathrm{" + tex + "}" if sty in ("p", "b") and t.strip() else tex
    kinder = lambda name: "".join(omml_tex(k) for k in (el.find(M + name) if el.find(M + name) is not None else []))
    if tag == M + "f":
        return r"\frac{" + kinder("num") + "}{" + kinder("den") + "}"
    if tag == M + "sSub":
        return "{" + kinder("e") + "}_{" + kinder("sub") + "}"
    if tag == M + "sSup":
        return "{" + kinder("e") + "}^{" + kinder("sup") + "}"
    if tag == M + "sSubSup":
        return "{" + kinder("e") + "}_{" + kinder("sub") + "}^{" + kinder("sup") + "}"
    if tag == M + "rad":
        return r"\sqrt{" + kinder("e") + "}"
    if tag in (M + "rPr", M + "fPr", M + "sSubPr", M + "sSupPr", M + "radPr", M + "ctrlPr", M + "oMathParaPr"):
        return ""
    return "".join(omml_tex(k) for k in el if isinstance(k.tag, str))


def _farbe(wert: str | None) -> str | None:
    return f"#{wert}" if wert and re.fullmatch(r"[0-9A-Fa-f]{6}", wert) else None


def _linie(b) -> str:
    """CSS-Linie aus einem Word-Rahmen (w:top, w:left …)."""
    if b is None or b.get(qn("w:val")) in (None, "nil", "none"):
        return "none"
    px = max(1, round(int(b.get(qn("w:sz")) or 4) / 8 * 4 / 3))
    return f"{px}px solid {_farbe(b.get(qn('w:color'))) or '#1B1F24'}"


class _HeftWandler(_Wandler):
    """Wie _Wandler, aber mit der Gestaltung des Blatts (Inline-Stile, die Moodle stehen lässt)."""

    def _lauf_heft(self, r) -> str:
        from docx.text.run import Run
        run = Run(r, None)
        teile = []
        for kind in r:
            if kind.tag == qn("w:t"):   # Leerzeichenfolgen wie in Word (Abstand nach „INFO“, zwischen Formeln)
                teile.append(re.sub(r" {2,}", lambda m: " " + "&nbsp;" * (len(m.group(0)) - 1),
                                    _html.escape(kind.text or "", quote=False)))
            elif kind.tag == qn("w:tab"):
                teile.append("&emsp;")
            elif kind.tag in (qn("w:br"), qn("w:cr")):
                teile.append("<br />")
            elif kind.tag == qn("w:drawing"):
                for blip in kind.iter(qn("a:blip")):
                    rid = blip.get(qn("r:embed"))
                    if rid:
                        doc_pr = next(kind.iter(qn("wp:docPr")), None)
                        ext = next(kind.iter(qn("wp:extent")), None)
                        breite = round(int(ext.get("cx")) * _EMU_PX) if ext is not None else None
                        stil = (f"width:{breite}px;" if breite else "") + "max-width:100%;height:auto;vertical-align:middle;"
                        teile.append(self._bild(rid, doc_pr.get("descr") if doc_pr is not None else None, stil))
        text = "".join(teile)
        if not text:
            return ""
        rpr = r.rPr
        stil = []
        if rpr is not None:
            farbe = rpr.find(qn("w:color"))
            f = _farbe(farbe.get(qn("w:val"))) if farbe is not None else None
            if f and f.upper() not in ("#1B1F24", "#000000"):
                stil.append(f"color:{f};")
            sz = rpr.find(qn("w:sz"))
            if sz is not None and int(sz.get(qn("w:val"))) != HEFT_GRUND:
                stil.append(f"font-size:{round(int(sz.get(qn('w:val'))) * _PX_JE_HALBPUNKT)}px;")
            if rpr.find(qn("w:caps")) is not None:
                stil.append("text-transform:uppercase;")
            if rpr.find(qn("w:spacing")) is not None:
                stil.append("letter-spacing:.12em;")
            bdr = rpr.find(qn("w:bdr"))
            if bdr is not None and bdr.get(qn("w:val")) not in ("nil", "none"):
                stil.append(f"display:inline-block;border:{_linie(bdr)};padding:1px 6px;")
            hl = rpr.find(qn("w:shd"))
            if hl is not None and _farbe(hl.get(qn("w:fill"))):
                stil.append(f"background:{_farbe(hl.get(qn('w:fill')))};")
            va = rpr.find(qn("w:vertAlign"))
            if va is not None and va.get(qn("w:val")) in ("superscript", "subscript"):
                text = f"<sup>{text}</sup>" if va.get(qn("w:val")) == "superscript" else f"<sub>{text}</sub>"
        if stil:
            text = f'<span style="{"".join(stil)}">{text}</span>'
        if run.italic and text.strip():
            text = f"<em>{text}</em>"
        if run.bold and text.strip():
            text = f"<strong>{text}</strong>"
        return text

    def _inline(self, p: Paragraph) -> str:
        aus = []
        for kind in p._p:
            if kind.tag == qn("w:r"):
                aus.append(self._lauf_heft(kind))
            elif kind.tag == qn("w:hyperlink"):
                innen = "".join(self._lauf_heft(r) for r in kind.iter(qn("w:r")))
                rid = kind.get(qn("r:id"))
                adresse = p.part.rels[rid].target_ref if rid and rid in p.part.rels else None
                aus.append(f'<a href="{_html.escape(adresse)}">{innen}</a>' if adresse else innen)
            elif kind.tag in (M + "oMath", M + "oMathPara"):
                formeln = [kind] if kind.tag == M + "oMath" else list(kind.iter(M + "oMath"))
                aus.append(" ".join(r"\(\displaystyle " + omml_tex(f) + r"\)" for f in formeln))   # Brüche groß wie in Word
        text = "".join(aus).strip()
        if "<a " not in text:   # Adresse als Link: sonst macht Moodles Filter aus einer .jpg-Adresse ein Bild
            text = _ADRESSE.sub(lambda m: f'<a href="{m.group(0)}">{m.group(0)}</a>', text)
        return _UNTERSTRICHE.sub(SCHREIBLINIE, text)

    @staticmethod
    def _absatz_stil(p: Paragraph) -> str:
        ppr = p._p.pPr
        vor, nach, stil = 0, 6, []
        if ppr is not None:
            sp = ppr.find(qn("w:spacing"))
            if sp is not None:
                vor = round(int(sp.get(qn("w:before")) or 0) * _TWIP_PX)
                nach = round(int(sp.get(qn("w:after")) or 90) * _TWIP_PX)
            jc = ppr.find(qn("w:jc"))
            if jc is not None and jc.get(qn("w:val")) in ("center", "right"):
                stil.append(f"text-align:{jc.get(qn('w:val'))};")
            ind = ppr.find(qn("w:ind"))
            if ind is not None:
                links = int(ind.get(qn("w:left")) or ind.get(qn("w:start")) or 0)
                haengend = int(ind.get(qn("w:hanging")) or 0)
                if links:
                    stil.append(f"padding-left:{round(links * _TWIP_PX)}px;")
                if haengend:
                    stil.append(f"text-indent:-{round(haengend * _TWIP_PX)}px;")
            rand = ppr.find(qn("w:pBdr"))
            if rand is not None:
                for seite in ("top", "bottom"):
                    b = rand.find(qn(f"w:{seite}"))
                    if b is not None:
                        stil.append(f"border-{seite}:{_linie(b)};padding-{seite}:3px;")
            shd = ppr.find(qn("w:shd"))
            if shd is not None and _farbe(shd.get(qn("w:fill"))):
                stil.append(f"background:{_farbe(shd.get(qn('w:fill')))};")
        return f"margin:{vor}px 0 {nach}px;" + "".join(stil)

    def _zellstil(self, tc, tbl, zeile: int, spalte: int, zeilen: int, spalten: int) -> str:
        tcpr = tc.tcPr
        stil = []
        tblpr = tbl.tblPr
        tbl_rand = tblpr.find(qn("w:tblBorders")) if tblpr is not None else None
        tc_rand = tcpr.find(qn("w:tcBorders")) if tcpr is not None else None
        innen = {"top": zeile > 0, "bottom": zeile < zeilen - 1, "left": spalte > 0, "right": spalte < spalten - 1}
        for seite in ("top", "left", "bottom", "right"):
            b = tc_rand.find(qn(f"w:{seite}")) if tc_rand is not None else None
            if b is None and tbl_rand is not None:
                ersatz = {"top": "insideH", "bottom": "insideH", "left": "insideV", "right": "insideV"}[seite]
                b = tbl_rand.find(qn(f"w:{ersatz if innen[seite] else seite}"))
            stil.append(f"border-{seite}:{_linie(b)};")
        if tcpr is not None:
            shd = tcpr.find(qn("w:shd"))
            if shd is not None and _farbe(shd.get(qn("w:fill"))):
                stil.append(f"background:{_farbe(shd.get(qn('w:fill')))};")
            va = tcpr.find(qn("w:vAlign"))
            if va is not None:
                stil.append("vertical-align:{};".format({"center": "middle"}.get(va.get(qn("w:val")),
                                                                                  va.get(qn("w:val")))))
        rand = {"top": 0, "bottom": 0, "left": 108, "right": 108}
        mar = tblpr.find(qn("w:tblCellMar")) if tblpr is not None else None
        for quelle in (mar, tcpr.find(qn("w:tcMar")) if tcpr is not None else None):
            if quelle is not None:
                for seite in rand:
                    m = quelle.find(qn(f"w:{seite}"))
                    if m is not None:
                        rand[seite] = int(m.get(qn("w:w")) or 0)
        stil.append("padding:{}px {}px {}px {}px;".format(*(round(rand[s] * _TWIP_PX)
                                                           for s in ("top", "right", "bottom", "left"))))
        return "".join(stil)

    def _tabelle(self, t: Table) -> str:
        tbl = t._tbl
        trs = list(tbl.tr_lst)
        spalten = len(tbl.tblGrid.gridCol_lst) if tbl.tblGrid is not None else 1
        tblpr = tbl.tblPr
        ind = tblpr.find(qn("w:tblInd")) if tblpr is not None else None
        einzug = round(int(ind.get(qn("w:w")) or 0) * _TWIP_PX) if ind is not None else 0
        if len(trs) == 1 and len(trs[0].tc_lst) == 1:   # Kasten (Info, Merke, Beispiel): ein Block
            tc = trs[0].tc_lst[0]
            inhalt = self._bloecke(_Cell(tc, t).iter_inner_content())
            return (f'<div style="{self._zellstil(tc, tbl, 0, 0, 1, 1)}margin:8px 0 10px {einzug}px;">'
                    f"\n{inhalt}\n</div>")
        breite = sum(int(g.get(qn("w:w")) or 0) for g in tbl.tblGrid.gridCol_lst) if tbl.tblGrid is not None else 0
        zeilen = []
        for zi, tr in enumerate(trs):
            kopf = tr.trPr is not None and tr.trPr.find(qn("w:tblHeader")) is not None
            zellen, sp = [], 0
            for tc in tr.tc_lst:
                if tc.vMerge == "continue":
                    sp += tc.grid_span
                    continue
                attr = f' colspan="{tc.grid_span}"' if tc.grid_span > 1 else ""
                if tc.vMerge == "restart":
                    try:
                        hoehe = tc.bottom - tc.top
                    except ValueError:
                        hoehe = 1
                    if hoehe > 1:
                        attr += f' rowspan="{hoehe}"'
                w = tc.tcPr.find(qn("w:tcW")) if tc.tcPr is not None else None
                if w is not None and breite and w.get(qn("w:type")) == "dxa":
                    attr += f' width="{round(int(w.get(qn("w:w"))) / breite * 100)}%"'
                stil = self._zellstil(tc, tbl, zi, sp, len(trs), spalten)
                sp += tc.grid_span
                inhalt = self._bloecke(_Cell(tc, t).iter_inner_content(), in_zelle=True)
                tag = "th" if kopf else "td"
                zellen.append(f'<{tag}{attr} style="{stil}text-align:left;">{inhalt}</{tag}>')
            zeilen.append('<tr style="border:none;">' + "".join(zellen) + "</tr>")   # Moodle rahmt tr und tbody
        px = round(breite * _TWIP_PX)
        return (f'<table style="border-collapse:collapse;border:none;background:transparent;width:{px}px;max-width:100%;'
                f'margin:6px 0 8px {einzug}px;">'
                '\n<tbody style="border:none;">\n' + "\n".join(zeilen) + "\n</tbody></table>")

    def _bloecke(self, inhalt, in_zelle: bool = False) -> str:
        aus: list[str] = []
        liste: str | None = None
        bloecke = list(inhalt)
        for block in bloecke:
            art = self._listenart(block) if isinstance(block, Paragraph) else None
            if liste and art != liste:
                aus.append(f"</{liste}>")
                liste = None
            if isinstance(block, Table):
                aus.append(self._tabelle(block))
                continue
            text = self._inline(block)
            if not text:
                continue
            stil = self._absatz_stil(block)
            if art:
                if liste is None:
                    aus.append(f'<{art} style="margin:0 0 6px;padding-left:1.4em;">')
                    liste = art
                aus.append(f'<li style="{stil}">{text}</li>')
                continue
            ebene = self._ueberschrift(block)
            if ebene:
                aus.append(f'<{ebene} style="{stil}font-size:17px;">{text}</{ebene}>')
            else:
                aus.append(f'<p style="{stil}">{text}</p>')
        if liste:
            aus.append(f"</{liste}>")
        return "\n".join(aus)

    def fusszeilen(self) -> None:
        """KI-Hinweis aus der Papier-Fußzeile (steht dort, nicht im Text des Auszugs)."""
        for s in self.dok.sections:
            for p in s.footer.paragraphs + [p for t in s.footer.tables for z in t._cells for p in z.paragraphs]:
                text = _html.escape(p.text.strip(), quote=False)
                if "KI-gestützt" in text and text not in self.fuss:
                    self.fuss.append(text)


def _wandeln(pfad: Path, heft: bool = False) -> tuple[str, list[Path], list[str], list[tuple[str, bool]]]:
    pfad = Path(pfad)
    dok = docx.Document(io.BytesIO(_lies(pfad)))
    ziel = Path(tempfile.mkdtemp(prefix="docx_bilder_"))
    w = (_HeftWandler if heft else _Wandler)(dok, pfad.stem, ziel)
    html = alt_aus_unterschrift(w._bloecke(dok.iter_inner_content()))
    if heft:
        w.fusszeilen()
    if not w.bilder:
        ziel.rmdir()
    return html, w.bilder, w.fuss, w.karten


_SCHMUCK = re.compile(r'<img\b([^>]*?)\balt=""\s*role="presentation"([^>]*)>')
_UNTERSCHRIFT = re.compile(r"\b((?:Abb|Abbildung|Tab|Tabelle)\.?\s*\d+(?:\.\d+)?\b[^<]{0,200})")


def alt_aus_unterschrift(html: str) -> str:
    """Bilder ohne Bildbeschreibung in Word, aber mit Bildunterschrift („Abb. 2.1 …“ in den nächsten Zeilen, vor dem
    nächsten Bild): die Unterschrift wird der Alternativtext (Inhaltsbild, kein Schmuck; Sichtprüfung LS 5)."""
    def ersetzen(m):
        rest = html[m.end():m.end() + 2000].split("<img", 1)[0]
        alt = None
        for teil in re.split(r"</(?:p|td|div|li|h\d)>|<br\s*/?>", rest):   # die Bildunterschrift ist ein Absatz
            text = re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", teil))).strip()
            u = _UNTERSCHRIFT.match(text)
            if u:
                alt = u.group(1).strip()
                break
        if not alt:
            return m.group(0)
        return f'<img{m.group(1)}alt="{_html.escape(alt)}"{m.group(2)}>'
    return _SCHMUCK.sub(ersetzen, html)


def heft_verweise(html: str, kacheln: dict[str, int] | None) -> str:
    """„AB 5“ im Heft heißt im Kurs „Kachel 3“ (die Kachel, in der das Blatt steht); die Word-Datei bleibt wie
    im Heft. Nicht genannte Blätter bleiben stehen."""
    if not kacheln:
        return html
    def ersetzen(m):   # „LS 3, AB 4“ meint ein Blatt einer anderen Lernsituation: bleibt
        anderes = re.search(r"LS(?:\s|&nbsp;)?\d+,\s?$", m.string[max(0, m.start() - 12):m.start()])
        if m.group(2) not in kacheln or anderes:
            return m.group(0)
        return f"Kachel{m.group(1)}{kacheln[m.group(2)]}"
    return _AB.sub(ersetzen, html)


def _fuss_html(fuss: list[str]) -> str:
    return "\n".join(f'<p style="{FUSS_STIL}">{f}</p>' for f in fuss)


def docx_zu_html(pfad: Path) -> tuple[str, list[Path]]:
    """HTML und Bilddateien einer DOCX; Bilder liegen in einem Zwischenordner (ohne Bilder: keiner bleibt
    zurück). Den Zwischenordner räumt der Aufrufer nach dem Ablegen weg. Papier-Fußzeilen stehen je Text
    einmal, klein und grau am Ende."""
    html, bilder, fuss, _ = _wandeln(pfad)
    if fuss:
        html += "\n" + _fuss_html(fuss)
    return html, bilder


def knopfname(datei: str, karten: list[tuple[str, bool]] | None = None) -> str:
    """Name für den Knopf: der Titel der ersten Karte der Datei, die keine Hilfekarte ist (die Hilfe
    gehört zum Auftrag, der Auftrag benennt die Datei); nur Hilfekarten: die erste davon. Ohne Karte aus
    dem Dateinamen: ohne Anlage-Präfix („Anl_6_“, „Anl7_“, „DS3_Anl_5c_“), Unterstriche als Leerzeichen.
    `Anl_6_Leitkarte.docx` → „Leitkarte“."""
    titel = [t for t, hilfe in karten or [] if not hilfe] or [t for t, _ in karten or []]
    if titel:
        return titel[0]
    stamm = Path(datei).stem
    return (_ANLAGE.sub("", stamm) or stamm).replace("_", " ").strip()


def _knopf(name: str, text: str, symbol: str, farbe: str) -> str:
    return (f'<a class="btn btn-outline-primary" href="{_url(name)}" title="{_html.escape(name)}" download="">'
            f"{_SYMBOL.format(symbol, farbe)}{text}</a>")


def knoepfe_html(docx_name: str, pdf_name: str | None = None, name: str | None = None,
                 hinweis: bool = True) -> str:
    """Download-Knöpfe einer DOCX: mit ausfüllbarem PDF zuerst der PDF-Knopf, dann Word, darunter der
    Hinweis (`hinweis`); ohne PDF nur der Word-Knopf. Mit `name` heißen die Knöpfe „<name> als Word“ bzw.
    „<name> als PDF“ (Seiten mit mehreren Dateien)."""
    wort = _html.escape(name, quote=False) if name else None
    word = _knopf(docx_name, f"{wort} als Word" if wort else WORD_KNOPF, "fa-file-word", "#2B579A")
    if not pdf_name:
        return f"<p>{word}</p>"
    pdf = _knopf(pdf_name, f"{wort} als PDF" if wort else PDF_KNOPF, "fa-file-pdf", "#C0392B")
    return f"<p>{pdf} {word}</p>" + (f'\n<p class="small">{PDF_HINWEIS}</p>' if hinweis else "")


def docx_seite_html(dateien: list[Path], pdfs: dict[Path, Path] | None = None,
                    knoepfe_oben: bool = False, heft: bool = False,
                    kacheln: dict[str, int] | None = None,
                    druck: set[Path] | None = None) -> tuple[str, list[Path]]:
    """Eine Seite aus mehreren DOCX: je Datei ein Abschnitt mit Inhalt und am Ende die Download-Knöpfe
    (mit PDF, wenn `pdfs` zur DOCX eins nennt); mit `knoepfe_oben` stehen alle Knöpfe stattdessen oben vor
    dem ersten Abschnitt. Jede Datei bekommt ihre Knöpfe genau einmal, bei mehreren Dateien mit Namen; der
    PDF-Hinweis steht einmal je Seite, Papier-Fußzeilen einmal ganz am Ende. Zurück kommen HTML und alle
    Dateien der Seite (Bilder, die DOCX selbst, PDFs). Mit `heft` sieht die Seite aus wie das Blatt
    (Infoseiten, Lehrkraft 2026-10-27): Gestaltung aus Word, 680 px breit, „AB n“ nach `kacheln`; das PDF
    ist dann ein Druckbild, ohne Ausfüll-Hinweis; ebenso jedes PDF in `druck`."""
    pfade = list(dict.fromkeys(map(Path, dateien)))
    pdfs = pdfs or {}
    mehrere = len(pfade) > 1
    teile, alle, fuss, knoepfe = [], [], [], []
    hinweis = not heft
    for pfad in pfade:
        inhalt, bilder, neu, karten = _wandeln(pfad, heft)
        if heft:
            inhalt = heft_verweise(inhalt, kacheln)
        fuss += [f for f in neu if f not in fuss]
        pdf = pdfs.get(pfad)
        k = knoepfe_html(pfad.name, pdf.name if pdf else None,
                         knopfname(pfad.name, karten) if mehrere else None,
                         hinweis=hinweis and pdf not in (druck or set()))
        hinweis = hinweis and not (pdf and pdf not in (druck or set()))
        knoepfe.append(k)
        teile.append(f"<section>\n{inhalt}\n</section>" if knoepfe_oben
                     else f"<section>\n{inhalt}\n{k}\n</section>")
        alle.extend(bilder)
        alle.append(pfad)
        if pdf:
            alle.append(pdf)
    namen = [d.name for d in alle]
    doppelt = sorted({n for n in namen if namen.count(n) > 1})
    if doppelt:
        raise ValueError(f"Dateiname mehrfach auf derselben Seite: {', '.join(doppelt)}")
    if knoepfe_oben:
        teile = knoepfe + teile
    if fuss:
        teile.append(_fuss_html(fuss))
    if heft:
        return f'<div style="{HEFT_STIL}">\n' + "\n".join(teile) + "\n</div>", alle
    return "\n".join(teile), alle
