"""Gemeinsame Bausteine für das Material einer Stunde (aus der Probe LF 1, LS 1, DS 1 übernommen).

    import stunde as st
    st.einrichten(kopf=dict(beruf=…, lf="Lernfeld 1", lf_titel=…, ls="Lernsituation 1", ls_titel=…),
                  kurz="LF 1 · LS 1 · DS 2", fiktiv="Musterbetrieb GmbH und Familie Muster sind fiktiv.")
    doc, b = st.seite(3, "Anlage 3 · Arbeitsblatt", "Titel", "Kurztitel")

Bausteine: Seite mit Schulkopf (seite), Betriebsformular der Modellfirma (formularkopf), Auftragskasten der
Meisterin (kasten_auftrag), Kachel „Ihr Auftrag“ (auftrag), Schneidekarten mit Mini-Kopf (bogen, kartenraster, kartenkopf, kartenfuss),
Fotokachel 4:3 mit Nummer (fotokachel), Erwartungshorizont aus der Schulvorlage (eh_bauen), Vorschau (vorschau).
Stilreferenz: Probe LF 1 · LS 1, Musterkatalog docs/stilreferenz/probe_ls01/README.md (Bauskripte im Arbeitsbereich).
"""
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, RGBColor
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import material_bausteine as mb  # noqa: E402
import schule as s  # noqa: E402
from arbeitsblatt import KI_HINWEIS, buendig, fuss, rahmenlinie, titel, zellabstand  # noqa: E402
from vorlagen_bauen import rahmen, schattieren, tabelle_ohne_rahmen  # noqa: E402,F401

SCHWARZ, BETRIEB = "1B1F24", "2F4A5A"          # Betriebsdokumente: schwarzer Rahmen, Farbe der Modellfirma
RGB_BETRIEB = RGBColor.from_string(BETRIEB)
KOPF, KURZ, FIKTIV = {}, "", ""


def einrichten(kopf, kurz, fiktiv):
    """Kopfdaten der Stunde setzen (Beruf, LF, LS), Kurzzeile für Karten, Fiktiv-Vermerk."""
    global KURZ, FIKTIV
    KOPF.clear(); KOPF.update(kopf)
    KURZ, FIKTIV = kurz, fiktiv


def seite(nr, schild, titeltext, kurztitel, quellen=None, namensfeld=False, ki=KI_HINWEIS, fmt="A4",
          wozu=None):
    """Dokument mit Schulkopf, Titelzeile und Fußzeile; fmt A4, A4quer oder A3."""
    doc = s.dokument("A4" if fmt == "A3" else ("A4quer" if fmt == "A3quer" else fmt))
    if fmt in ("A3", "A3quer"):
        sec = doc.sections[0]
        sec.page_width, sec.page_height = (Cm(29.7), Cm(42.0)) if fmt == "A3" else (Cm(42.0), Cm(29.7))
    buendig(s.kopf(doc, **KOPF))
    fuss(doc, f"Anlage {nr} · {kurztitel} · {FIKTIV}", quellen=quellen, ki=ki, bedingt=False)
    s.leer(doc, 6)
    titel(doc, schild, titeltext, namensfeld=namensfeld, titelgroesse=17)
    if wozu:
        s.wozu(doc, wozu)
    return doc, s.nutzbreite(doc)


def label(ziel, text, vor=8, nach=2, farbe=s.RGB_BLAU):
    return mb.label(ziel, text, farbe=farbe, groesse=8, vor=vor, nach=nach, sperren=16)


def absatz(ziel, text, groesse=10.5, vor=0, nach=2, zeile=1.25, fett=False, farbe=None, kursiv=False):
    p = s.abstand(ziel.add_paragraph(), vor, nach, zeile)
    teile = text.split("**")
    for i, t in enumerate(teile):
        if t:
            s.lauf(p, t, groesse, fett=fett or bool(i % 2), farbe=farbe, kursiv=kursiv)
    return p


def formularkopf(doc, b, art, zeilen):
    """Betriebsdokument des Modellbetriebs (Profil modellbetrieb.name): schwarzer Rahmen, Titel gesperrt, Felder (Label, Wert)."""
    t = doc.add_table(1 + len(zeilen), 4)
    tabelle_ohne_rahmen(t)
    k = t.cell(0, 0).merge(t.cell(0, 1)).merge(t.cell(0, 2)).merge(t.cell(0, 3))
    rahmen(k, top=(18, SCHWARZ), left=(18, SCHWARZ), right=(18, SCHWARZ), bottom=(12, SCHWARZ))
    zellabstand(k, 0.12, 0.1, 0.25, 0.25)
    p = s.abstand(k.paragraphs[0])
    mb.tab_stopp(p, b - 0.55)
    mb.r_sperren(s.lauf(p, art.upper(), 13, fett=True, farbe=s.RGB_DUNKEL), 40)
    s.lauf(p, "\t" + s.SCHULE["betrieb"], 8.5, farbe=RGB_BETRIEB)
    for i, zeile in enumerate(zeilen, start=1):
        zellen = t.rows[i].cells
        if len(zeile) == 2:   # ein Feld über die ganze Breite
            zeile = (zeile[0], zeile[1], None, None)
        for j, (lab, wert) in enumerate(((zeile[0], zeile[1]), (zeile[2], zeile[3]))):
            if lab is None:
                zellen[1].merge(zellen[3])
                break
            zl, zw = zellen[2 * j], zellen[2 * j + 1]
            s.zeilenhoehe(t.rows[i], 0.62, genau=False)
            for z in (zl, zw):
                rahmen(z, bottom=(4, "8A929E"), left=(4, "8A929E") if z is not zl or j else (18, SCHWARZ),
                       right=(18, SCHWARZ) if (z is zw and (j == 1 or zeile[2] is None)) else None,
                       top=None)
                zellabstand(z, 0.06, 0.04, 0.15, 0.1)
                s.senkrecht(z, "center")
            s.lauf(s.abstand(zl.paragraphs[0]), lab, 7.5, farbe=s.RGB_GRAU)
            if wert.startswith("("):          # Hinweis im leeren Feld, rechts und klein
                q = s.abstand(zw.paragraphs[0]); q.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                s.lauf(q, wert, 7.5, farbe=s.RGB_GRAU)
            else:
                s.lauf(s.abstand(zw.paragraphs[0]), wert, 10.5, farbe=s.RGB_DUNKEL)
    # unterer Abschluss schwarz
    for z in t.rows[-1].cells:
        rahmen(z, bottom=(18, SCHWARZ), left=(18, SCHWARZ) if z is t.rows[-1].cells[0] else (4, "8A929E"),
               right=(18, SCHWARZ) if z is t.rows[-1].cells[-1] else None)
    s.feste_breiten(t, [2.6, b / 2 - 2.6, 2.9, b / 2 - 2.9])
    buendig(t)
    return t


def kasten_auftrag(doc, b, ueberschrift, text, groesse=10.5):
    """Auftrag der Meisterin wie im Einstiegs-Muster: blauer Rahmen, Pfeil, Kapitälchen-Überschrift."""
    t = doc.add_table(1, 2)
    tabelle_ohne_rahmen(t)
    a, z = t.rows[0].cells
    blau = (18, s.BLAU)
    rahmen(a, top=blau, bottom=blau, left=(36, s.BLAU))
    rahmen(z, top=blau, bottom=blau, right=blau)
    zellabstand(a, 0.15, 0.15, 0.2, 0.05); zellabstand(z, 0.15, 0.2, 0.05, 0.3)
    s.senkrecht(a, "top")
    s.lauf(s.abstand(a.paragraphs[0], 8), "→", 16, farbe=s.RGB_BLAU)
    p = s.abstand(z.paragraphs[0], 0, 2)
    mb.r_sperren(s.kapitaelchen(s.lauf(p, ueberschrift, 7.5, fett=True, farbe=s.RGB_BLAU)), 16)
    for zeile in text.split("\n"):
        absatz(z, zeile, groesse, 0, 1, 1.25)
    s.feste_breiten(t, [0.9, b - 0.9])
    buendig(t)
    return t


def _omml_lauf(text, groesse, fett, gerade):
    if gerade == "auto":                                    # je Stück: Zahlen mit Einheit gerade, Formelzeichen kursiv
        gerade = any(c.isdigit() for c in text)
    if LUECKE in text and len(text) > 1:                   # Kästchen der Lückenformel groß genug zum Schreiben
        return "".join(_omml_lauf(t, groesse, fett, gerade) for t in re.split(f"({LUECKE})", text) if t)
    if text == LUECKE:
        groesse, fett, gerade = groesse * 2.2, False, True
    from xml.sax.saxutils import escape
    rpr = f'<w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/>{"<w:b/>" if fett else ""}' \
          f'<w:sz w:val="{int(groesse * 2)}"/></w:rPr>'
    sty = '<m:rPr><m:nor/></m:rPr>' if gerade else ('<m:rPr><m:sty m:val="bi"/></m:rPr>' if fett else "")  # nor: LibreOffice und Word gerade
    return f'<m:r>{sty}{rpr}<m:t xml:space="preserve">{escape(text)}</m:t></m:r>'


def _omml_index(text, groesse, fett, gerade):
    """Formelstück mit tiefgestellten Indizes: „U_{F}“ wird U mit tiefgestelltem, geradem F (2026-10-27)."""
    teile = re.split(r"(\S)_\{(.+?)\}", text)
    if len(teile) == 1:
        return _omml_lauf(text, groesse, fett, gerade)
    xml = ""
    for i in range(0, len(teile), 3):
        if teile[i]:
            xml += _omml_lauf(teile[i], groesse, fett, gerade)
        if i + 2 < len(teile):
            xml += (f'<m:sSub><m:e>{_omml_lauf(teile[i + 1], groesse, fett, gerade)}</m:e>'
                    f'<m:sub>{_omml_lauf(teile[i + 2], groesse * 0.8, fett, True)}</m:sub></m:sSub>')
    return xml


def _summanden(text):
    """Teilt eine Seite an „ + “ und „ − “ außerhalb von Klammern; nur wenn mehr als ein Bruch darin steht, damit
    bestehende Formeln wie „(a + b) / c“ oder „a + b / c“ unverändert bleiben."""
    if text.count(" / ") < 2:
        return [text]
    teile, tiefe, start, i = [], 0, 0, 0
    while i < len(text):
        c = text[i]
        tiefe += c == "("
        tiefe -= c == ")"
        if tiefe == 0 and text[i:i + 3] in (" + ", " − "):
            teile += [text[start:i], text[i:i + 3]]
            start = i = i + 3
            continue
        i += 1
    return teile + [text[start:]]


def _omml_seite(text, groesse, fett, gerade):
    """Eine Seite einer Gleichung; „a / b“ (mit Leerzeichen) wird zum Bruch mit Bruchstrich, „1 / R_{1} + 1 / R_{2}“
    zu zwei Brüchen, „X_{y}“ zu einem tiefgestellten Index."""
    summanden = _summanden(text)
    if len(summanden) > 1:
        return "".join(_omml_lauf(t, groesse, fett, True) if t in (" + ", " − ") else
                       _omml_seite(t.strip(), groesse, fett, gerade) for t in summanden)
    if " / " in text:
        z, n = text.rsplit(" / ", 1)
        return (f'<m:f><m:num>{_omml_seite(z.strip(), groesse, fett, gerade)}</m:num>'
                f'<m:den>{_omml_seite(n.strip(), groesse, fett, gerade)}</m:den></m:f>')
    m = re.search(r"(\S+)\^(\S+)", text)                  # Hochzahl: „10^-3“ wird 10 hoch −3
    if m:
        vor, nach = text[:m.start()], text[m.end():]
        hoch = (f'<m:sSup><m:e>{_omml_lauf(m.group(1), groesse, fett, gerade)}</m:e>'
                f'<m:sup>{_omml_lauf(m.group(2).replace("-", "−"), groesse, fett, gerade)}</m:sup></m:sSup>')
        return (_omml_index(vor, groesse, fett, gerade) if vor else "") + hoch + \
            (_omml_seite(nach, groesse, fett, gerade) if nach else "")
    return _omml_index(text, groesse, fett, gerade)


def formel(p, text, groesse=12, fett=False, gerade=None, immer=False):
    """Formel als Word-Formel (OMML) mit echtem Bruchstrich (Profil material.formeln_als_bruch, Lehrkraft 2026-10-25):
    „I = Q / t“ wird I = Q über t. Brüche entstehen an „ / “ mit Leerzeichen, Gleichheitszeichen trennen die Seiten;
    mehrere Brüche je Seite („1 / R = 1 / R_{1} + 1 / R_{2}“) und Indizes „R_{V}“ (tiefgestellt, gerade) gehen auch.
    Formelzeichen kursiv, Einheitengleichungen (mit Ziffern) gerade, außer gerade ist gesetzt. immer: auch ohne Bruch
    als Word-Formel (im Merkkasten, damit alle Formeln einer Zeile gleich aussehen)."""
    from docx.oxml import parse_xml
    if gerade is None:                                      # mit Indizes je Stück entscheiden (wie R_{V} = 20,7 V / …)
        gerade = "auto" if "_{" in text else any(c.isdigit() for c in text)
    if not s.STIL.get("formeln_als_bruch") or (" / " not in text and "^" not in text and "_{" not in text
                                                and not immer):
        s.lauf(p, re.sub(r"_\{(.+?)\}", r"\1", text), groesse, fett=fett)
        return p
    teile = [t.strip() for t in text.split("=")]
    inhalt = _omml_lauf(" = ", groesse, fett, True).join(_omml_seite(t, groesse, fett, gerade) for t in teile)
    ns = 'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" ' \
         'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    p._p.append(parse_xml(f'<m:oMath {ns}>{inhalt}</m:oMath>'))
    return p


QUELLEN = {}   # Schlüssel -> (Nummer, Volltext); Quellenverzeichnis am Ende des Dokuments (Lehrkraft 2026-10-25)


def quellen_registrieren(eintraege):
    """Quellen eines Teils (Liste von (Schlüssel, Volltext)) in Reihenfolge nummerieren; doppelte Schlüssel einmal."""
    for k, v in eintraege:
        if k not in QUELLEN:
            QUELLEN[k] = (len(QUELLEN) + 1, v)


def q(*schluessel):
    """Kurzverweis für Abbildung, Fall oder Zitat, z. B. „[3]“ oder „[3, 5]“."""
    return "[" + ", ".join(str(QUELLEN[k][0]) for k in schluessel) + "]"


def quellenverzeichnis(doc, breite, titel="Quellenverzeichnis"):
    """Eigene Seite am Ende mit allen registrierten Quellen, nummeriert wie die Kurzverweise."""
    mb.seitenumbruch(doc)
    thema(doc, titel, abstand=0)
    for k, (n, v) in sorted(QUELLEN.items(), key=lambda x: x[1][0]):
        p = absatz(doc, "", 9, 2, 0, 1.1)
        p.paragraph_format.left_indent = Cm(0.9); p.paragraph_format.first_line_indent = Cm(-0.9)
        mb.tab_stopp(p, 0.9, "left")
        s.lauf(p, f"[{n}]\t", 9, fett=True, farbe=s.RGB_BLAU)
        s.lauf(p, v, 9)


def fassung(name=None):
    """Fassung des fortlaufenden Arbeitsblatt-Dokuments (Lehrkraft 2026-10-25): „gesamt“ für Lehrkraft und Moodle mit allen
    Infotexten, „schueler“ für Papier ohne Infotexte (die Lernenden informieren sich im Fachkundebuch), Merkkästen leer zum
    Ausfüllen. Ohne Argument: aktuelle Fassung."""
    if name:
        s.STIL["fassung"] = name
    return s.STIL.get("fassung", "gesamt")


def gesamt():
    """True in der Gesamtfassung: Infotexte, Beispielrechnungen und ausgefüllte Merkkästen nur dann bauen."""
    return fassung() != "schueler"


LUECKE = "\u25a1"   # □ für die Lückenformel


def _tex_seite(t, gerade):
    t = t.strip()
    teile = _summanden(t)                                 # „1 / □ + 1 / □“: je Summand ein Bruch (wie die Word-Formel)
    if len(teile) > 1:
        return " ".join(x.strip() if x in (" + ", " − ") else _tex_seite(x, gerade) for x in teile)
    if " / " in t:
        z, n = t.rsplit(" / ", 1)
        return r"\dfrac{" + _tex_seite(z, gerade) + "}{" + _tex_seite(n, gerade) + "}"
    t = t.replace("%", r"\%").replace(r" \%", r"\,\%")
    t = re.sub(r"(?<![_\\])\b([A-Za-zÄÖÜäöüß]{2,}(?:\s+[A-Za-zÄÖÜäöüß]{2,})*)\b(?![_{])", r"\\text{\1}", t)  # Wörter
    t = re.sub(r"([A-Za-zΑ-Ωα-ω])_([A-Za-z0-9]+)", r"\1_{\\mathrm{\2}}", t)
    t = t.replace("·", r"\cdot ").replace(LUECKE, r"\luecke{}")
    return r"\mathrm{" + t.replace(" ", r"\,") + "}" if gerade else t


def lueckenbild(f, hoehe_cm=None):
    """Lückenformel als Bild (LuaLaTeX, unicode-math): Kästchen groß genug zum Hineinschreiben, Bruch mit echtem
    Bruchstrich. Unabhängig davon, wie Word oder LibreOffice Formelgrößen umsetzen. Zwischenspeicher ~/.cache/mpr_formeln."""
    import hashlib, subprocess, tempfile
    cache = Path.home() / ".cache" / "mpr_formeln"; cache.mkdir(parents=True, exist_ok=True)
    ziel = cache / (hashlib.sha1(f.encode()).hexdigest()[:16] + ".png")
    if ziel.exists():
        return ziel
    gerade = f.strip()[:1].isdigit() and not re.search(r"[A-Za-zΑ-Ωα-ω]", f.split("=")[0].replace("1 /", ""))
    # Einheitengleichung (1 C = …) gerade, sonst Formelzeichen kursiv (auch „1 / R = …“)
    teile = re.split(r"\s*([=≤≥])\s*", f)
    tex = " ".join(_tex_seite(p, gerade) if i % 2 == 0 else {"=": "=", "≤": r"\le", "≥": r"\ge"}[p]
                   for i, p in enumerate(teile))
    quelle = (r"\documentclass[border=4pt,varwidth=24cm]{standalone}\usepackage{unicode-math}\usepackage{xcolor}"
              r"\newcommand{\luecke}{{\color[HTML]{8A929E}\fboxrule=0.6pt\fbox{\rule{0pt}{0.75cm}\hspace{1.1cm}}}}"
              r"\begin{document}\Large$\displaystyle " + tex + r"$\end{document}")
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "f.tex").write_text(quelle, encoding="utf-8")
        subprocess.run(["lualatex", "-interaction=nonstopmode", "f.tex"], cwd=d, capture_output=True, timeout=120)
        if not (Path(d) / "f.pdf").exists():
            raise RuntimeError(f"Lückenformel nicht setzbar: {f!r} ({tex})")
        subprocess.run(["pdftocairo", "-r", "300", "-png", "-transp", "-singlefile", "f.pdf", "f"], cwd=d, check=True,
                       capture_output=True)
        ziel.write_bytes((Path(d) / "f.png").read_bytes())
    return ziel


def lueckenformel(f):
    """Lückenformel für die Schülerfassung: links vom ersten „=“ bleibt alles stehen, rechts werden Formelzeichen und
    Einheiten zu Kästchen (□); Zahlen, Rechenzeichen, Klammern und Bruchstriche bleiben. „I = Q / t“ wird I = □ über □."""
    m = re.search(r"[=≤≥]", f)
    if not m:
        return f
    links, zeichen, rechts = f[:m.start()], m.group(), f[m.end():]
    rechts = re.sub(r"_\{[^}]*\}", "", rechts)              # Index gehört zum Formelzeichen und wird mit verdeckt
    wort = r"[A-Za-zÄÖÜäöüßΑ-Ωα-ωΩµ°Δ][A-Za-zÄÖÜäöüßΑ-Ωα-ωΩµ°_0-9₀-₉ₙ]*"
    rechts = re.sub(wort + r"(?:\s+" + wort + r")*", LUECKE, rechts)   # Wortgruppe wird ein Kästchen
    return links + zeichen + rechts


MERK_FARBEN = {"blau": ("08349C", "E8EEF8"), "rot": ("C0392B", "FDEDEC")}


def einheitenzeile(ziel, einheiten, groesse=11):
    """Einheitengleichungen im Merkkasten nach DIN 1313 (Lehrkraft 2026-10-25): eckige Klammer um das Formelzeichen
    („Einheit von“), rechts die Einheiten ohne Klammern, z. B. [R] = V / A = Ω. Formelzeichen kursiv, Einheiten gerade."""
    q = s.abstand(ziel.add_paragraph(), 2, 3); q.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for i, e in enumerate(einheiten):
        if i:
            s.lauf(q, "          ", groesse)
        m = re.match(r"^\[(.+?)\]\s*=\s*(.*)$", e)
        if not m:
            formel(q, e, groesse, gerade=True)
            continue
        s.lauf(q, "[", groesse)
        zeichen = s.lauf(q, m.group(1), groesse); zeichen.italic = True
        s.lauf(q, "] = ", groesse)
        formel(q, m.group(2), groesse, gerade=True)
    return q


def merkkasten_voll(mit_formeln=True):
    """Merkkasten ausgefüllt bauen? In der Gesamtfassung immer, in der Schülerfassung bei Profil
    material.merkkasten_schueler „ausgefuellt“, wenn der Kasten Formeln hat (Lehrkraft 2026-10-27). Für Module, die den
    Inhalt eines Formel-Merkkastens selbst setzen, statt gesamt() abzufragen."""
    return gesamt() or (mit_formeln and s.STIL.get("merkkasten_schueler") == "ausgefuellt")


def merkkasten(doc, breite, titel, formeln, text=None, groesse=13, einheiten=None, auftrag=None, voll=None):
    """Merkkasten für neu eingeführte Formeln und Einheitengleichungen (Lehrkraft 2026-10-25): farbiger Rand links,
    hell hinterlegt, Kennwort MERKE, Formeln zentriert, groß und fett, darunter die Einheitengleichungen (einheitenzeile)
    und optional ein erklärender Satz. Ein Eintrag in formeln, der selbst eine Liste ist, steht in einer Zeile (die
    Formel mit ihren Umstellungen). Farbe nach Profil material.merkkasten (neutral blau). Information nie nur über die
    Farbe: Kennwort MERKE.
    Schülerfassung nach Profil material.merkkasten_schueler: „lueckenformel“ (neutral) oder „leer_mit_auftrag“: kariert
    und leer, darüber der Auftrag, was einzutragen ist (auftrag, sonst aus dem Titel); „ausgefuellt“ (Lehrkraft
    2026-10-27): Kästen mit Formeln wie in der Gesamtfassung, Kästen ohne Formeln leer mit Auftrag.
    Formeln in Tabellenbuch-Form (Stilregel „Merkkasten wie im Tabellenbuch“): allgemein (R = R_{1} + R_{2} + … +
    R_{n}), als text die Legende der Formelzeichen mit Einheit. voll: ausgefüllt erzwingen (Module, die den Inhalt
    selbst setzen und st.merkkasten_voll() schon gefragt haben)."""
    if voll is None:
        voll = merkkasten_voll(bool(formeln))
    rand, fuellung = MERK_FARBEN.get(s.STIL.get("merkkasten", "blau"), MERK_FARBEN["blau"])
    einheiten = einheiten or []
    zeilen = [f if isinstance(f, (list, tuple)) else [f] for f in formeln]
    t = doc.add_table(1, 1)
    tabelle_ohne_rahmen(t)
    z = t.rows[0].cells[0]
    schattieren(z, fuellung); rahmen(z, left=(36, rand), top=(8, rand), bottom=(8, rand), right=(8, rand))
    zellabstand(z, 0.2, 0.2, 0.4, 0.3)
    p = s.abstand(z.paragraphs[0], 0, 4)
    mb.r_sperren(s.kapitaelchen(s.lauf(p, "Merke", 8, fett=True, farbe=RGBColor.from_string(rand))), 16)
    if titel:
        s.lauf(p, "   " + titel, 11, fett=True, farbe=s.RGB_DUNKEL)
    if not voll and s.STIL.get("merkkasten_schueler") in ("leer_mit_auftrag", "ausgefuellt"):
        absatz(z, auftrag or f"Tragen Sie hier ein: {titel}.", 10, 2, 4, 1.15, kursiv=True, farbe=s.RGB_DUNKEL)
        bruch = any(" / " in f for zl in zeilen for f in zl) or any(" / " in e for e in einheiten)
        s.kaestchen(z, breite - 1.0, max(2.0, (1.5 if bruch else 1.0) * (len(zeilen) + (1 if einheiten else 0)) + 0.5))
        mb.schlussabsatz(z)
    elif not voll:                                          # Schülerfassung: Lückenformel
        for f in [f for zl in zeilen for f in zl]:
            q = s.abstand(z.add_paragraph(), 4, 4); q.alignment = WD_ALIGN_PARAGRAPH.CENTER
            bild = lueckenbild(lueckenformel(f))
            b_px, h_px = Image.open(bild).size
            q.add_run().add_picture(str(bild), height=Cm(h_px / 300 * 2.54 * 0.9))
    else:
        for zl in zeilen:
            q = s.abstand(z.add_paragraph(), 3, 3); q.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for i, f in enumerate(zl):
                if i:
                    s.lauf(q, "          ", groesse)
                formel(q, f, groesse, fett=True, gerade="auto" if "_{" in f else f.strip()[:1].isdigit(), immer=True)
        if einheiten:
            einheitenzeile(z, einheiten)
        if text:
            absatz(z, text, 10, 4, 0, 1.15)
    s.feste_breiten(t, [breite]); buendig(t)
    zusammenhalten(t)
    return t


def leerzeilen(ziel, n, hoehe=0.8, breite=18.0):
    t = s.schreiblinien(ziel, n, hoehe, breite)
    buendig(t)
    return t


# ---------------------------------------------------------------- Karten (mehrere je A4)
def bogen():
    """A4 hoch mit schmalem Rand für Schneidekarten (Seitenkopf je Karte)."""
    doc = s.dokument("A4")
    sec = doc.sections[0]
    sec.left_margin = sec.right_margin = Cm(0.7)
    sec.top_margin = sec.bottom_margin = Cm(0.7)
    sec.header_distance = sec.footer_distance = Cm(0.3)
    return doc


SCHNITT = (12, "8A929E")


def kartenraster(doc, zeilen, spalten, hoehe):
    b = s.nutzbreite(doc)
    t = doc.add_table(zeilen, spalten)
    tabelle_ohne_rahmen(t)
    for zeile in t.rows:
        s.zeilenhoehe(zeile, hoehe)
        for z in zeile.cells:
            rahmenlinie(z, "dashed", top=SCHNITT, bottom=SCHNITT, left=SCHNITT, right=SCHNITT)
            zellabstand(z, 0.35, 0.2, 0.45, 0.45)
    s.feste_breiten(t, [b / spalten] * spalten)
    return t, b / spalten


def kartenkopf(zelle, breite, schild, titeltext, titelgroesse=15):
    """Mini-Kopf wie Karte A5: Farbstreifen, Schild und Titel, Logo rechts."""
    innen = breite - 0.9
    n = mb.zell_tabelle(zelle, 1, 3)
    tabelle_ohne_rahmen(n)
    st, tz, lg = n.rows[0].cells
    for z in (st, tz, lg):
        zellabstand(z, 0, 0, 0, 0)
    s.senkrecht(tz, "center")
    s.senkrecht(st, "top")
    for i, (farbe, hoehe) in enumerate(((s.BLAU, 0.75), (s.GRUEN, 0.4))):
        q = s.abstand(st.paragraphs[0] if i == 0 else st.add_paragraph())
        q.paragraph_format.line_spacing = Cm(hoehe)
        q.paragraph_format.line_spacing_rule = 4
        mb.p_schatten(q, farbe)
        s.lauf(q, "", 2)
    zellabstand(tz, 0, 0, 0.3, 0.1)
    p = s.abstand(tz.paragraphs[0], 0, 1)
    mb.r_sperren(s.kapitaelchen(s.lauf(p, schild, 7, fett=True, farbe=s.RGB_BLAU)), 20)
    s.lauf(s.abstand(tz.add_paragraph(), 0, 0, 1.0), titeltext, titelgroesse, fett=True, farbe=s.RGB_DUNKEL)
    p = s.abstand(lg.paragraphs[0]); p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    s.senkrecht(lg, "center")
    p.add_run().add_picture(str(s.LOGO), width=Cm(2.0))
    s.feste_breiten(n, [0.22, innen - 0.22 - 2.2, 2.2])
    mb.schlussabsatz(zelle)
    zelle._tc.remove(zelle.paragraphs[0]._p)
    return n


def kartenfuss(zelle, text, vor=4):
    p = s.abstand(zelle.add_paragraph(), vor, 0)
    s.lauf(p, text, 7, farbe=s.RGB_GRAU, kursiv=True)
    return p


def stufenpunkte(n, gesamt=3):
    return "●" * n + "○" * (gesamt - n)


def messenger(ziel, breite, absender, zeit, text, kopf=None, rechts="",
              groesse=12, dauer=None):
    """Nachricht im Messenger-Stil (Kopfleiste, Sprechblase mit Absender, Text, Uhrzeit); dauer = Sprachnachricht."""
    kopf = kopf or f"{s.SCHULE['betrieb']} · Team-Chat"   # Profil modellbetrieb.name
    chat = mb.zell_tabelle(ziel, 2, 1) if hasattr(ziel, "_tc") else ziel.add_table(2, 1)
    tabelle_ohne_rahmen(chat)
    k, bl = chat.rows[0].cells[0], chat.rows[1].cells[0]
    schattieren(k, "2F4A5A"); zellabstand(k, 0.1, 0.1, 0.3, 0.3)
    p = s.abstand(k.paragraphs[0])
    mb.tab_stopp(p, breite - 0.6)
    s.lauf(p, kopf, 9.5, fett=True, farbe=s.WEISS)
    if rechts:
        s.lauf(p, "\t" + rechts, 7.5, farbe=RGBColor(0xDD, 0xE6, 0xEA))
    schattieren(bl, "E6F2EA")
    rahmen(bl, left=(4, "B9D3C1"), right=(4, "B9D3C1"), bottom=(4, "B9D3C1"))
    zellabstand(bl, 0.15, 0.12, 0.35, 0.35)
    s.lauf(s.abstand(bl.paragraphs[0], 0, 2), absender, groesse - 2.5, fett=True, farbe=RGB_BETRIEB)
    if dauer:
        p = s.abstand(bl.add_paragraph(), 0, 3)
        s.lauf(p, "►  ", 11, farbe=RGB_BETRIEB)
        s.lauf(p, "▂▅▇▃▆▂▇▅▃▆▇▂▅▃▇▆▂▅▇▃▆▂▅", 9, farbe=RGBColor.from_string("6E8C7A"))
        s.lauf(p, f"  {dauer}   Sprachnachricht", 8, farbe=s.RGB_GRAU)
    absatz(bl, text, groesse, 0, 1, 1.2)
    p = s.abstand(bl.add_paragraph(), 0, 0); p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    s.lauf(p, f"{zeit} ✓✓", 7.5, farbe=s.RGB_GRAU)
    s.feste_breiten(chat, [breite])
    if not hasattr(ziel, "_tc"):
        buendig(chat)
    return chat


def fotokachel(quelle, ziel, nummer=None, groesse=(1200, 900), grund=(242, 243, 245), freisteller=False):
    """Foto auf einheitliche Kachel (Standard 4:3, hellgrauer Grund) einpassen, auch vergrößern;
    optional Nummer oben links im Bild (Schulblau). freisteller=True schneidet weißen Rand vorher ab."""
    from PIL import ImageChops
    im = Image.open(quelle).convert("RGB")
    if freisteller:
        box = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).point(
            lambda v: 255 if v > 12 else 0).getbbox()
        if box:
            pad = int(0.04 * max(im.size))
            im = im.crop((max(0, box[0] - pad), max(0, box[1] - pad), min(im.width, box[2] + pad),
                          min(im.height, box[3] + pad)))
    bw, bh = groesse
    k = Image.new("RGB", groesse, (255, 255, 255) if freisteller else grund)
    f = min((bw - 40) / im.width, (bh - 40) / im.height)
    im = im.resize((round(im.width * f), round(im.height * f)), Image.LANCZOS)
    k.paste(im, ((bw - im.width) // 2, (bh - im.height) // 2))
    if nummer is not None:
        d = ImageDraw.Draw(k)
        d.rectangle((0, 0, 118, 118), fill=(8, 52, 156))
        try:
            schrift = ImageFont.truetype("LiberationSans-Bold.ttf", 92)
        except OSError:
            schrift = ImageFont.load_default()
        d.text((59, 61), str(nummer), fill="white", font=schrift, anchor="mm")
    k.save(ziel, quality=85)
    return Path(ziel)


def auftrag(doc, breite, schritte, zeit, groesse=10):
    """Kachel „Ihr Auftrag“ (Stilregel 2026-10-23): inhaltlich offen, organisatorisch konkret, so klein wie möglich.

    schritte = [(text, sozialform), …] mit sozialform einzel | partner | gruppe | plenum: kleines Symbol rechts in der
    Zeile (ohne Wort, Korrektur 2026-10-23); zeit = Gesamtzeit rechts im Kopf, z. B. "35 min".
    Unterlagen im Text mit dem Namen nennen, den die Lernenden lesen.
    """
    import symbole
    k = doc.add_table(1, 1)
    tabelle_ohne_rahmen(k)
    z = k.rows[0].cells[0]
    schattieren(z, "F4F6F8")
    rahmen(z, left=(18, "08349C"))
    zellabstand(z, 0.1, 0.08, 0.3, 0.3)
    innen = breite - 0.6
    p = s.abstand(z.paragraphs[0], 0, 1)
    mb.tab_stopp(p, innen)
    mb.r_sperren(s.kapitaelchen(s.lauf(p, "Ihr Auftrag", 7.5, fett=True, farbe=s.RGB_BLAU)), 20)
    s.lauf(p, f"\t{zeit}", 8, fett=True, farbe=s.RGB_BLAU)
    t = mb.zell_tabelle(z, len(schritte), 3)
    tabelle_ohne_rahmen(t)
    for i, (zeile, (text, form)) in enumerate(zip(t.rows, schritte), start=1):
        nr, txt, sf = zeile.cells
        for c in (nr, txt, sf):
            zellabstand(c, 0.03, 0.03, 0, 0)
            s.senkrecht(c, "center")
        s.lauf(s.abstand(nr.paragraphs[0]), str(i), groesse, fett=True, farbe=s.RGB_BLAU)
        absatz(txt, text, groesse, 0, 0, 1.1)
        txt._tc.remove(txt.paragraphs[0]._p)
        q = s.abstand(sf.paragraphs[0]); q.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        q.add_run().add_picture(str(symbole.pfad(form)), height=Cm(0.38))
    s.feste_breiten(t, [0.45, innen - 0.45 - 0.9, 0.9])
    mb.schlussabsatz(z)
    s.feste_breiten(k, [breite]); buendig(k)
    return k


def arbeitsblaetter(quellen=None, ki=KI_HINWEIS):
    """Fortlaufendes Arbeitsblatt-Dokument einer Lernsituation (Profil material.arbeitsblaetter_fortlaufend):
    Schulkopf, einmal der Titel „Arbeitsblätter“ mit Namensfeld, Fußzeile mit Seitenzahl. Die Themen folgen mit
    thema() ohne Seitenumbruch und ohne AB-Nummer (die Nummern gibt es nur in der Planung, Lehrkraft 2026-10-23)."""
    doc = s.dokument("A4")
    buendig(s.kopf(doc, **KOPF))
    ls = KOPF.get("ls", "")
    fuss(doc, f"Arbeitsblätter {ls.replace('Lernsituation ', 'LS ')} · {KOPF.get('ls_titel', '')} · {FIKTIV}",
         quellen=quellen, ki=ki, bedingt=False)
    s.leer(doc, 6)
    titel(doc, f"Arbeitsblätter · {ls}", KOPF.get("ls_titel", ""), namensfeld=True, titelgroesse=17)
    return doc, s.nutzbreite(doc)


def thema(doc, titeltext, abstand=14):
    """Zwischenüberschrift im fortlaufenden Arbeitsblatt-Dokument (wie im Fachbuch), bleibt beim Folgenden."""
    p = s.abstand(doc.add_paragraph(), abstand, 4)
    p.paragraph_format.keep_with_next = True
    s.lauf(p, titeltext, 13, fett=True, farbe=s.RGB_DUNKEL)
    s.absatzlinie(p, unten=(6, "08349C"))
    return p


AUFGABEN = []   # XML-Elemente aller Aufgaben, für aufgaben_zusammenhalten


def aufgaben_zusammenhalten(doc):
    """Vor dem Speichern (Lehrkraft 2026-10-25): jede Aufgabe bleibt mit dem Anfang ihres Bearbeitungsteils auf einer
    Seite. Leere Abstandsabsätze direkt nach der Aufgabe halten ebenfalls zum nächsten Element."""
    from docx.oxml.ns import qn
    for el in AUFGABEN:
        n = el.getnext()
        while n is not None and n.tag == qn("w:p") and not "".join(n.itertext()).strip():
            ppr = n.get_or_add_pPr()
            if ppr.find(qn("w:keepNext")) is None:
                ppr.append(ppr.makeelement(qn("w:keepNext"), {}))
            n = n.getnext()


def aufgabe(doc, breite, nr, text, sozialform, zeit=None, groesse=10.5):
    """Eine Aufgabe im Arbeitsblatt; danach, wo sinnvoll, direkt Platz zum Schreiben (schreibplatz) oder das Material
    zur Aufgabe. Profil material.aufgaben_kaestchen: eigenes blaues Kästchen mit Symbol der Sozialform rechts
    (Lehrkraft 2026-10-23); neutral: fette Nummer und Text, Sozialform in Klammern. Zeit nur nach Profil
    material.zeit_auf_arbeitsblatt (sonst steht sie im Erwartungshorizont)."""
    import symbole
    zeit = zeit if s.STIL["zeit_auf_arbeitsblatt"] else None
    if not s.STIL["aufgaben_kaestchen"]:
        p = s.abstand(doc.add_paragraph(), 6, 2, 1.15)
        p.paragraph_format.left_indent = Cm(0.6); p.paragraph_format.first_line_indent = Cm(-0.6)
        mb.tab_stopp(p, 0.6, "left")
        s.lauf(p, f"{nr}\t", groesse, fett=True, farbe=s.RGB_BLAU)
        for j, teil in enumerate(text.split("**")):
            if teil:
                s.lauf(p, teil, groesse, fett=bool(j % 2))
        zusatz = ", ".join(x for x in (symbole.SOZIALFORM[sozialform] if s.STIL["sozialform_symbol"] else "", zeit) if x)
        if zusatz:
            s.lauf(p, f" ({zusatz})", groesse - 1.5, farbe=s.RGB_GRAU)
        p.paragraph_format.keep_with_next = True             # Aufgabe nie allein unten auf der Seite
        AUFGABEN.append(p._p)
        return p
    k = doc.add_table(1, 3)
    tabelle_ohne_rahmen(k)
    nrz, txt, rechts = k.rows[0].cells
    for z in (nrz, txt, rechts):
        schattieren(z, "EAF0FA"); s.senkrecht(z, "center")
        zellabstand(z, 0.1, 0.1, 0.12, 0.12)
    rahmen(nrz, left=(18, "08349C"))
    s.lauf(s.abstand(nrz.paragraphs[0]), str(nr), groesse + 2, fett=True, farbe=s.RGB_BLAU)
    absatz(txt, text, groesse, 0, 0, 1.15)
    txt._tc.remove(txt.paragraphs[0]._p)
    q = s.abstand(rechts.paragraphs[0]); q.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    from PIL import Image
    bild = symbole.pfad(sozialform)
    b_px, h_px = Image.open(bild).size
    if not s.STIL["sozialform_symbol"]:                     # Sozialform frei: kein Symbol (Lehrkraft 2026-10-27)
        pass
    elif 0.4 * b_px / h_px > 1.1:                            # breite Symbole (Plenum) nicht abschneiden
        q.add_run().add_picture(str(bild), width=Cm(1.1))
    else:
        q.add_run().add_picture(str(bild), height=Cm(0.4))
    if zeit:
        q = s.abstand(rechts.add_paragraph()); q.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        s.lauf(q, zeit, 7.5, fett=True, farbe=s.RGB_BLAU)
    s.feste_breiten(k, [0.75, breite - 0.75 - 1.5, 1.5])
    mb.zeile_nicht_teilen(k.rows[0])
    buendig(k)
    zusammenhalten(k, mit_folgendem=True)                   # Aufgabe nie allein unten auf der Seite (Lehrkraft 2026-10-25)
    AUFGABEN.append(k._tbl)
    return k


def zusammenhalten(*tabellen, mit_folgendem=False):
    """Tabellen (z. B. Aufgabe und ihre Übersicht) nicht über die Seite trennen: alle Absätze bleiben beim nächsten,
    Zeilen ungeteilt. mit_folgendem=True hält auch die letzte Zeile an das, was danach kommt."""
    for n, tab in enumerate(tabellen):
        for i, zeile in enumerate(tab.rows):
            mb.zeile_nicht_teilen(zeile)
            letzte = n == len(tabellen) - 1 and i == len(tab.rows) - 1
            for zelle in zeile.cells:
                for q in zelle.paragraphs:
                    q.paragraph_format.keep_with_next = mit_folgendem or not letzte


FREIGABE_PFLICHT = ("jeder_aufbau", "jeder_aufbau_jahr_1_2", "erster_aufbau", "fragen")


def freigabefeld(doc, breite, wartezeit=None, verlangt=None, feldbreite=5.2):
    """Feld „Aufbau freigegeben (Lehrkraft)“ mit Kürzelfeld vor dem Einschalten (Stilregel 2026-10-26, Profil
    ruesten.freigabe_einschalten; einheitlich für alle Mess-AB, Lehrkraft 2026-10-27). wartezeit: Funktion
    (ziel, breite), die rechts daneben die Aufgabe für die Wartezeit mit Bearbeitungsteil setzt; darüber steht
    einheitlich „Während Sie auf die Freigabe warten:“ (die Aufgabe selbst wiederholt das nicht). Ohne Freigabe
    (Profil „selbst“ oder verlangt=False) oder mit mündlicher Freigabe (material.freigabefeld_auf_blatt false) steht nur
    die Aufgabe da, ohne Feld und ohne Hinweis auf die Freigabe."""
    verlangt = s.STIL["freigabe_einschalten"] in FREIGABE_PFLICHT if verlangt is None else verlangt
    if not s.STIL.get("freigabefeld_auf_blatt", True):
        verlangt = False          # Freigabe mündlich (Profil material.freigabefeld_auf_blatt false), nur die Aufgabe
    if not verlangt:
        if wartezeit:
            wartezeit(doc, breite)
        return None
    luecke = 0.4
    t = doc.add_table(1, 3 if wartezeit else 1)
    tabelle_ohne_rahmen(t)
    links = t.rows[0].cells[0]
    rot = (18, "C62828")
    rahmen(links, top=rot, bottom=rot, left=rot, right=rot)
    schattieren(links, "FDEDEC")
    zellabstand(links, 0.2, 0.2, 0.3, 0.3); s.senkrecht(links, "top")
    absatz(links, "Aufbau freigegeben (Lehrkraft)", 11, 0, 4, fett=True, farbe=s.RGB_DUNKEL)
    absatz(links, "Erst nach der Freigabe einschalten.", 10, 0, 10, kursiv=True)
    absatz(links, "Kürzel", 10, 0, 2, farbe=s.RGB_GRAU)
    k = links.add_table(1, 1)
    tabelle_ohne_rahmen(k); s.tabellenrand(k, 8, "5F6670")
    s.zeilenhoehe(k.rows[0], 1.2)
    s.feste_breiten(k, [feldbreite - 0.7])
    mb.schlussabsatz(links)
    links._tc.remove(links.paragraphs[0]._p)
    if wartezeit:
        rechts = t.rows[0].cells[2]
        zellabstand(rechts, 0, 0, 0, 0)
        absatz(rechts, "Während Sie auf die Freigabe warten:", 10, 0, 3, fett=True, farbe=s.RGB_BLAU)
        wartezeit(rechts, breite - feldbreite - luecke)
        mb.schlussabsatz(rechts)
        if len(rechts.paragraphs) > 1 and not rechts.paragraphs[0].text.strip():
            rechts._tc.remove(rechts.paragraphs[0]._p)
        s.feste_breiten(t, [feldbreite, luecke, breite - feldbreite - luecke])
    else:
        s.feste_breiten(t, [feldbreite])
    buendig(t)
    mb.zeile_nicht_teilen(t.rows[0])
    return t


def schreibplatz(doc, breite, zeilen=5, hoehe=0.85):
    """Schreiblinien direkt unter einer Aufgabe (Lernende schreiben auf dem Arbeitsblatt)."""
    s.leer(doc, 2)
    return buendig(s.schreiblinien(doc, zeilen, hoehe, breite))


def eh_bauen(daten, ziel, nachtrag=None, persoenlich=False, teilbar=()):
    """Erwartungshorizont aus der Schulvorlage; Aufgabenzeilen nicht über die Seite trennen, außer den Aufgaben
    in teilbar (Nummern wie in den Daten), deren Zeile länger als eine halbe Seite ist.
    nachtrag(doc) kann z. B. einen Bildnachweis anhängen; persoenlich=True baut die Vorlage mit der
    Gestaltung aus dem Lehrkraft-Profil (wie material_bausteine.persoenliche_vorlage)."""
    import erwartungshorizont as eh
    vorlage = s.WURZEL / "vorlagen" / "Vorlage_erwartungshorizont.docx"
    if persoenlich:
        s.persoenlich()
        import arbeitsbereich
        vorlage = arbeitsbereich.finden() / ".daten" / "vorlagen" / "Vorlage_erwartungshorizont.docx"
        vorlage.parent.mkdir(parents=True, exist_ok=True)
        eh.vorlage(vorlage)
    eh.rendern(vorlage, daten, ziel)
    doc = Document(ziel)
    for t in doc.tables:
        for zeile in t.rows:
            if zeile.cells[0].text.strip() not in {str(n) for n in teilbar}:
                mb.zeile_nicht_teilen(zeile)
    if nachtrag:
        nachtrag(doc)
    mb.ordnen(doc)
    doc.save(ziel)
    return Path(ziel)


def eh_daten(nr, titel_anl, wozu, aufgaben, bezug, quellen="", rechenpruefung="", art="Anlage"):
    k = KOPF
    return {"beruf": k["beruf"], "lf": k["lf"].replace("Lernfeld ", ""), "lf_titel": k["lf_titel"],
            "ls": k["ls"].replace("Lernsituation ", ""), "ls_titel": k["ls_titel"], "nr": str(nr),
            "titel": titel_anl, "fiktiv": FIKTIV, "ki_hinweis": KI_HINWEIS, "wozu": wozu, "quellen": quellen,
            "kopf_loesung": "Erwartete Lösung", "aufgaben": aufgaben, "bezug": bezug,
            "rechenpruefung": rechenpruefung, "kompetenzbezug": [], "art": art}


def eh_aufgabe(nr, loesung, ergebnis, fehler, alternativen, antwortsatz=""):
    return {"nr": nr, "loesung": loesung, "ergebnis": ergebnis, "antwortsatz": antwortsatz,
            "alternativen": alternativen, "rundung": "", "zwischenergebnis": False, "fehler": fehler}


def vorschau(datei, ordner, dpi=90):
    """PNG-Vorschau je Seite (DOCX über LibreOffice, PPTX über folien.vorschau)."""
    ordner = Path(ordner); ordner.mkdir(exist_ok=True)
    praefix = ordner / Path(datei).stem
    for alt in ordner.glob(praefix.name + "-*.png"):
        alt.unlink()
    if str(datei).endswith(".pptx"):
        import folien as fo
        return fo.vorschau(datei, praefix, dpi=30)
    return s.vorschau(datei, praefix, dpi=dpi)
