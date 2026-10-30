"""Ausfüllbares PDF zu Word-Seiten und zwei Knöpfe (Durchsicht LS 1, 2026-10-23).

Mit dem Kursschalter `kurs["pdf_formular"]` wandelt der Bau jede DOCX einer Seite in ein PDF, legt Textfelder
über die Schreibzeilen (≥5 `_`) und über leere Tabellenzellen (≥18 pt hoch) und bietet das PDF neben der
Word-Datei an. Ohne Felder (reines Infoblatt) gibt es kein PDF und nur den Word-Knopf.
"""
import copy
import hashlib
import tarfile
import xml.etree.ElementTree as ET

import pytest

pymupdf = pytest.importorskip("pymupdf")
pytest.importorskip("docx")

import bauen  # noqa: E402
import beispiel  # noqa: E402
import pdf_formular  # noqa: E402
from test_docx_seite import _docx  # noqa: E402

HINWEIS = "Das PDF können Sie direkt ausfüllen, am Tablet oder am PC. Speichern nicht vergessen."


def _pdf_mit_schreibzeilen(pfad):
    """Zwei Schreibzeilen und eine Tabelle: links Text, rechts eine leere Zelle, 30 pt hoch."""
    dok = pymupdf.open()
    seite = dok.new_page()
    seite.insert_text((72, 100), "weil ______________", fontsize=11)
    seite.insert_text((72, 130), "weil ______________", fontsize=11)
    x0, x1, x2, y0, y1 = 72, 222, 472, 200, 230
    for a, b in (((x0, y0), (x2, y0)), ((x0, y1), (x2, y1)),
                 ((x0, y0), (x0, y1)), ((x1, y0), (x1, y1)), ((x2, y0), (x2, y1))):
        seite.draw_line(a, b, width=1)
    seite.insert_text((78, 220), "Begründung", fontsize=11)
    dok.save(pfad)
    dok.close()
    return pfad


def _pdf_nur_text(pfad):
    dok = pymupdf.open()
    dok.new_page().insert_text((72, 100), "Ein Infoblatt ohne Lücken.", fontsize=11)
    dok.save(pfad)
    dok.close()
    return pfad


def test_formularfelder_auf_schreibzeilen(tmp_path):
    pdf = _pdf_mit_schreibzeilen(tmp_path / "blatt.pdf")
    assert pdf_formular.formular_felder(pdf) == 3
    dok = pymupdf.open(pdf)
    felder = list(dok[0].widgets())
    assert sorted(w.field_name for w in felder) == ["feld_1_1", "feld_1_2", "feld_1_3"]
    for w in felder:
        assert w.field_type == pymupdf.PDF_WIDGET_TYPE_TEXT
        assert w.text_fontsize == 11
    zeilen = sorted((w.rect for w in felder if w.rect.y1 < 150), key=lambda r: r.y0)
    assert len(zeilen) == 2
    for r in zeilen:      # über den Unterstrichen, nicht über „weil“
        assert r.x0 > 90 and r.x1 > 150
    zelle = next(w.rect for w in felder if w.rect.y0 >= 195)
    assert zelle.x0 >= 222 and zelle.x1 <= 472 and zelle.height >= 18


def test_infoblatt_ohne_felder(tmp_path):
    pdf = _pdf_nur_text(tmp_path / "info.pdf")
    vorher = pdf.read_bytes()
    assert pdf_formular.formular_felder(pdf) == 0
    assert pdf.read_bytes() == vorher


@pytest.fixture
def wurzel(tmp_path):
    w = tmp_path / "dateien"
    beispiel.dateien_anlegen(w)
    (w / "word").mkdir()
    d = _docx(w / "word" / "Anl_5_Streifen.docx", "Entscheidungsstreifen", bild=False)
    import docx
    dok = docx.Document(d)
    dok.add_paragraph("Wir wählen, weil ______________")
    dok.save(d)
    return w


def _bauen(tmp_path, wurzel, schalter, monkeypatch, pdf_quelle=_pdf_mit_schreibzeilen):
    def falsches_word(docx_pfad, ziel):
        return pdf_quelle(ziel)
    monkeypatch.setattr(pdf_formular, "docx_zu_pdf", falsches_word)
    kurs = copy.deepcopy(beispiel.kursdefinition())
    if schalter is not None:
        kurs["kurs"]["pdf_formular"] = schalter
    kurs["abschnitte"][0]["aktivitaeten"].append(
        {"typ": "page", "name": "Streifen", "abschluss": "ansehen", "docx": ["word/Anl_5_Streifen.docx"]})
    ziel = tmp_path / "pdf.mbz"
    bauen.baue(kurs, wurzel, ziel)
    ordner = tmp_path / "entpackt"
    with tarfile.open(ziel, "r:gz") as tar:
        tar.extractall(ordner, filter="data")
    for p in ordner.glob("activities/page_*/page.xml"):
        wurzel_xml = ET.parse(p).getroot()
        page = wurzel_xml.find("page")
        if page.findtext("name") == "Streifen":
            ctx = wurzel_xml.get("contextid")
            namen = {f.findtext("filename"): f for f in ET.parse(ordner / "files.xml").getroot().findall("file")
                     if f.findtext("contextid") == ctx and f.findtext("filearea") == "content"}
            return page.findtext("content"), namen, ordner
    raise AssertionError("Seite fehlt")


def test_knoepfe_pdf_und_word(tmp_path, wurzel, monkeypatch):
    inhalt, dateien, ordner = _bauen(tmp_path, wurzel, True, monkeypatch)
    pdf_k = inhalt.index("Als PDF herunterladen")
    word_k = inhalt.index("Als Word herunterladen")
    assert pdf_k < word_k < inhalt.index(HINWEIS)
    assert inhalt.count(HINWEIS) == 1
    assert f'<p class="small">{HINWEIS}</p>' in inhalt
    assert '<a class="btn btn-outline-primary" href="@@PLUGINFILE@@/Anl_5_Streifen.pdf"' in inhalt
    assert '<a class="btn btn-outline-primary" href="@@PLUGINFILE@@/Anl_5_Streifen.docx"' in inhalt
    assert "fa-file-pdf" in inhalt and "#C0392B" in inhalt
    assert "fa-file-word" in inhalt and "#2B579A" in inhalt
    assert "Anl_5_Streifen.pdf" in dateien
    h = dateien["Anl_5_Streifen.pdf"].findtext("contenthash")
    daten = (ordner / "files" / h[:2] / h).read_bytes()
    assert hashlib.sha1(daten).hexdigest() == h
    assert len(list(pymupdf.open(stream=daten, filetype="pdf")[0].widgets())) == 3


@pytest.mark.parametrize("schalter", [False, None])
def test_ohne_schalter_nur_word(tmp_path, wurzel, monkeypatch, schalter):
    aufrufe = []
    monkeypatch.setattr(pdf_formular, "formular_felder", lambda p: aufrufe.append(p) or 3)
    inhalt, dateien, _ = _bauen(tmp_path, wurzel, schalter, monkeypatch)
    assert "Als Word herunterladen" in inhalt
    assert "Als PDF herunterladen" not in inhalt and HINWEIS not in inhalt
    assert not any(n.endswith(".pdf") for n in dateien)
    assert aufrufe == []


def test_schalter_an_aber_ohne_felder_nur_word(tmp_path, wurzel, monkeypatch):
    inhalt, dateien, _ = _bauen(tmp_path, wurzel, True, monkeypatch, pdf_quelle=_pdf_nur_text)
    assert "Als Word herunterladen" in inhalt
    assert "Als PDF herunterladen" not in inhalt and HINWEIS not in inhalt
    assert not any(n.endswith(".pdf") for n in dateien)


def _tabelle(seite, xs, ys):
    for y in ys:
        seite.draw_line((xs[0], y), (xs[-1], y), width=1)
    for x in xs:
        seite.draw_line((x, ys[0]), (x, ys[-1]), width=1)


def test_flache_leere_zelle_ohne_feld(tmp_path):
    """Mittlere Zeile 10 pt hoch und leer (Abstandshalter): kein Feld. Die 30 pt hohen leeren Zellen darüber
    und darunter bekommen je eins (eine Zelle trägt Text, sonst erkennt PyMuPDF die Tabelle nicht)."""
    dok = pymupdf.open()
    seite = dok.new_page()
    _tabelle(seite, (72, 222, 472), (200, 230, 240, 270))
    seite.insert_text((78, 220), "Kriterium", fontsize=11)
    pdf = tmp_path / "flach.pdf"
    dok.save(pdf)
    dok.close()
    assert pdf_formular.formular_felder(pdf) == 3
    for w in pymupdf.open(pdf)[0].widgets():
        assert not (w.rect.y0 > 229 and w.rect.y1 < 241)
        assert w.rect.height >= 18 - 4


def test_zellenfeld_nicht_auf_rahmen_und_helvetica(tmp_path):
    pdf = _pdf_mit_schreibzeilen(tmp_path / "blatt.pdf")
    pdf_formular.formular_felder(pdf)
    felder = list(pymupdf.open(pdf)[0].widgets())
    assert all(w.text_font == "Helv" for w in felder)
    zelle = next(w.rect for w in felder if w.rect.y0 >= 195)
    assert zelle.x0 > 223 and zelle.x1 < 471 and zelle.y0 > 201 and zelle.y1 < 229


def test_mehrere_schreibzeilen_in_einer_zeile_erst_ab_fuenf(tmp_path):
    """Vier `_` sind keine Schreibzeile; zwei Läufe in derselben Zeile ergeben zwei getrennte Felder."""
    dok = pymupdf.open()
    dok.new_page().insert_text((72, 100), "a ____ b _____ c ______", fontsize=11)
    pdf = tmp_path / "zeile.pdf"
    dok.save(pdf)
    dok.close()
    assert pdf_formular.formular_felder(pdf) == 2
    rechtecke = sorted((w.rect for w in pymupdf.open(pdf)[0].widgets()), key=lambda r: r.x0)
    assert rechtecke[0].x1 < rechtecke[1].x0          # keine Überlappung, kein Feld über „c“


def test_feldnamen_je_seite_eindeutig(tmp_path):
    dok = pymupdf.open()
    for _ in range(2):
        dok.new_page().insert_text((72, 100), "Name: __________", fontsize=11)
    pdf = tmp_path / "zwei.pdf"
    dok.save(pdf)
    dok.close()
    assert pdf_formular.formular_felder(pdf) == 2
    namen = [w.field_name for s in pymupdf.open(pdf) for w in s.widgets()]
    assert namen == ["feld_1_1", "feld_2_1"]


def test_ohne_word_und_libreoffice_klare_meldung_und_kein_restordner(tmp_path, monkeypatch):
    tmp = tmp_path / "temp"
    tmp.mkdir()
    monkeypatch.setattr(pdf_formular.tempfile, "tempdir", str(tmp))
    monkeypatch.setattr(pdf_formular, "_mit_word", lambda q, z: False)
    monkeypatch.setattr(pdf_formular, "_soffice", lambda: None)
    docx = _docx(tmp_path / "Blatt.docx", "Blatt", bild=False)
    with pytest.raises(RuntimeError, match="Weder Word noch LibreOffice"):
        pdf_formular.docx_zu_pdf(docx, tmp_path / "aus" / "Blatt.pdf")
    assert list(tmp.iterdir()) == []


def test_word_weg_ergebnis_am_ziel_und_kein_restordner(tmp_path, monkeypatch):
    tmp = tmp_path / "temp"
    tmp.mkdir()
    monkeypatch.setattr(pdf_formular.tempfile, "tempdir", str(tmp))
    monkeypatch.setattr(pdf_formular, "_mit_word", lambda q, z: bool(_pdf_nur_text(z)))
    docx = _docx(tmp_path / "Blatt.docx", "Blatt", bild=False)
    ziel = pdf_formular.docx_zu_pdf(docx, tmp_path / "aus" / "Blatt.pdf")
    assert ziel == (tmp_path / "aus" / "Blatt.pdf").resolve() and ziel.is_file()
    assert list(tmp.iterdir()) == []


def test_bau_infoblatt_hinterlaesst_keinen_temp_ordner(tmp_path, wurzel, monkeypatch):
    tmp = tmp_path / "temp"
    tmp.mkdir()
    monkeypatch.setattr(bauen.tempfile, "tempdir", str(tmp))
    _bauen(tmp_path, wurzel, True, monkeypatch, pdf_quelle=_pdf_nur_text)
    assert not [p for p in tmp.iterdir() if p.name.startswith("docx_pdf_")]


# Gezeichnete Schreiblinien (Word: Linie oder Absatzrahmen unten statt `_`), Nachtrag 2026-10-23.
# Jedes Blatt trägt zusätzlich eine freie Linie 200 pt bei y=700: genau sie soll ein Feld bekommen.

def _blatt(tmp_path, zeichne, name="linie.pdf", frei=True):
    dok = pymupdf.open()
    seite = dok.new_page()
    zeichne(seite)
    if frei:
        seite.draw_line((100, 700), (300, 700), width=0.5)
    pdf = tmp_path / name
    dok.save(pdf)
    dok.close()
    return pdf


def _felder(pdf):
    return [w.rect for w in pymupdf.open(pdf)[0].widgets()]


def _ist_freie_linie(r):
    return abs(r.x0 - 100) < 2 and abs(r.x1 - 300) < 2 and 697 <= r.y1 <= 700.5 and r.height >= 12


@pytest.mark.parametrize("form", ["linie", "flaches_rechteck"])
def test_gezeichnete_linie_wird_feld(tmp_path, form):
    def zeichne(seite):
        if form == "flaches_rechteck":      # so legt Word einen Absatzrahmen unten ab
            seite.draw_rect(pymupdf.Rect(100, 399.6, 300, 400), color=None, fill=(0, 0, 0))
        else:
            seite.draw_line((100, 400), (300, 400), width=0.5)
    pdf = _blatt(tmp_path, zeichne, frei=False)
    assert pdf_formular.formular_felder(pdf) == 1
    r, = _felder(pdf)
    assert abs(r.x0 - 100) < 2 and abs(r.x1 - 300) < 2
    assert 397 <= r.y1 <= 400.5 and 12 <= r.height <= 20


@pytest.mark.parametrize("ueberstand", [0, 6])
def test_tabellenrahmen_kein_feld(tmp_path, ueberstand):
    """Auch Randlinien, die über die Tabelle hinausragen (Kopfleiste der Anlagen), sind Rahmen."""
    def zeichne(seite):
        for y in (200, 230, 260):
            seite.draw_line((72 - ueberstand, y), (472 + ueberstand, y), width=1)
        for x in (72, 222, 472):
            seite.draw_line((x, 200), (x, 260), width=1)
        for x in (78, 228):
            for y in (220, 250):
                seite.insert_text((x, y), "Text", fontsize=11)
    pdf = _blatt(tmp_path, zeichne)
    assert pdf_formular.formular_felder(pdf) == 1
    assert _ist_freie_linie(_felder(pdf)[0])


def test_kurze_linie_kein_feld(tmp_path):
    pdf = _blatt(tmp_path, lambda s: s.draw_line((100, 400), (140, 400), width=0.5))
    assert pdf_formular.formular_felder(pdf) == 1
    assert _ist_freie_linie(_felder(pdf)[0])


def test_unterstrichene_ueberschrift_kein_feld(tmp_path):
    def zeichne(seite):
        seite.insert_text((72, 100), "Unterstrichene Überschrift", fontsize=14)
        seite.draw_line((72, 102), (250, 102), width=0.8)
        seite.insert_text((72, 802), "Fußzeile auf der Trennlinie", fontsize=9)    # Linie quer durch den Text
        seite.draw_line((72, 800), (520, 800), width=0.5)
    pdf = _blatt(tmp_path, zeichne)
    assert pdf_formular.formular_felder(pdf) == 1
    assert _ist_freie_linie(_felder(pdf)[0])


def test_gestrichelter_kasten_kein_feld(tmp_path):
    """Schneidekasten wie im Entscheidungsstreifen: gestrichelt, Ecken an senkrechten Linien."""
    def zeichne(seite):
        seite.draw_rect(pymupdf.Rect(8, 22, 562, 291), color=(0.5, 0.5, 0.5), width=1.4, dashes="[4 1] 0")
        seite.draw_rect(pymupdf.Rect(8, 300, 562, 500), color=(0, 0, 0), width=0.5)
    pdf = _blatt(tmp_path, zeichne)
    assert pdf_formular.formular_felder(pdf) == 1
    assert _ist_freie_linie(_felder(pdf)[0])


def test_linie_in_leerer_zelle_nur_ein_feld(tmp_path):
    """Schreiblinie in einer leeren Zelle: das Zellenfeld genügt, kein zweites Feld darüber."""
    def zeichne(seite):
        _tabelle(seite, (72, 222, 472), (200, 260))
        seite.insert_text((78, 220), "Kriterium", fontsize=11)
        seite.draw_line((230, 250), (460, 250), width=0.5)
    pdf = _blatt(tmp_path, zeichne)
    assert pdf_formular.formular_felder(pdf) == 2
    rechtecke = sorted(_felder(pdf), key=lambda r: r.y0)
    assert rechtecke[0].x0 >= 222 and rechtecke[0].y1 <= 260
    assert _ist_freie_linie(rechtecke[1])


def test_kasten_aus_einzellinien_kein_feld(tmp_path):
    """Notizkasten aus vier Einzellinien mit Text darin: keine Tabelle, trotzdem Rahmen."""
    def zeichne(seite):
        for a, b in (((100, 300), (400, 300)), ((100, 360), (400, 360)),
                     ((100, 300), (100, 360)), ((400, 300), (400, 360))):
            seite.draw_line(a, b, width=0.8)
        seite.insert_text((110, 320), "Notiz", fontsize=11)
    pdf = _blatt(tmp_path, zeichne)
    assert pdf_formular.formular_felder(pdf) == 1
    assert _ist_freie_linie(_felder(pdf)[0])


def test_gestrichelte_schneidelinie_kein_feld(tmp_path):
    pdf = _blatt(tmp_path, lambda s: s.draw_line((8, 400), (562, 400), width=1.4, dashes="[4 1] 0"))
    assert pdf_formular.formular_felder(pdf) == 1
    assert _ist_freie_linie(_felder(pdf)[0])
