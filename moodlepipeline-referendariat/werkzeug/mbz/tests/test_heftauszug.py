"""Infoseiten wie im Heft (Lehrkraft 2026-10-27): Auszug aus der Gesamtfassung, Heft-Stil, Prüfer 12."""
import shutil

import pytest

docx = pytest.importorskip("docx")

import docx_seite  # noqa: E402
import heftauszug  # noqa: E402
import pruefen  # noqa: E402
from conftest import akt  # noqa: E402
from docx.oxml import parse_xml  # noqa: E402
from docx.oxml.ns import nsdecls  # noqa: E402

FORMEL = ('<m:oMath xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"><m:r><m:t>I</m:t></m:r>'
          '<m:r><m:rPr><m:nor/></m:rPr><m:t> = </m:t></m:r><m:f><m:num><m:r><m:t>Q</m:t></m:r></m:num>'
          '<m:den><m:r><m:t>t</m:t></m:r></m:den></m:f></m:oMath>')


def _kasten(d, kennwort, titel, fuellung="F1F3F6", text="Siehe AB 2 und LS 3, AB 2 [3]."):
    t = d.add_table(rows=1, cols=1)
    zelle = t.cell(0, 0)
    zelle._tc.get_or_add_tcPr().append(parse_xml(f'<w:shd {nsdecls("w")} w:val="clear" w:fill="{fuellung}"/>'))
    zelle.paragraphs[0].add_run(f"{kennwort}   {titel}")
    zelle.add_paragraph(text)
    zelle.add_paragraph()._p.append(parse_xml(FORMEL))
    return t


@pytest.fixture
def gesamt(tmp_path):
    d = docx.Document()
    d.sections[0].footer.paragraphs[0].text = "KI-gestützt erstellt; Werkzeug siehe KI-Verzeichnis."
    d.add_paragraph("AB 1 Aufgabe")
    _kasten(d, "Info", "Erster Kasten")
    d.add_paragraph("Aufgabe zwischen den Kästen")
    _kasten(d, "Unterlage", "Zweiter Kasten", text="Ohne Quelle.")
    d.add_paragraph("Quellenverzeichnis")
    d.add_paragraph("[3]\tQuelle drei")
    d.add_paragraph("[4]\tQuelle vier")
    pfad = tmp_path / "Gesamt.docx"
    d.save(str(pfad))
    return pfad


def test_kaesten_und_auszug(gesamt, tmp_path):
    k = heftauszug.kaesten(gesamt)
    assert [(kw, t[:6]) for _, kw, t in k] == [("Info", "Erster"), ("Unterlage", "Zweite")]
    ziel = heftauszug.auszug(gesamt, [k[0][0]], tmp_path / "a.docx")
    text = "\n".join(p.text for p in docx.Document(str(ziel)).paragraphs)
    assert "Aufgabe" not in text and "Quelle drei" in text and "Quelle vier" not in text
    assert "KI-gestützt" in docx.Document(str(ziel)).sections[0].footer.paragraphs[0].text


def test_quellennummern():
    assert heftauszug._nummern("6, 8") == ["6", "8"]
    assert heftauszug._nummern("4–6") == ["4", "5", "6"]


def test_heft_stil(gesamt, tmp_path):
    ziel = heftauszug.auszug(gesamt, [heftauszug.kaesten(gesamt)[0][0]], tmp_path / "Info_A.docx")
    pdf = tmp_path / "Info_A.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    html, dateien = docx_seite.docx_seite_html([ziel], {ziel: pdf}, knoepfe_oben=True, heft=True,
                                               kacheln={"2": 3})
    assert "background:#F1F3F6" in html                     # Kasten mit Zellfarbe statt Tabelle
    assert r"\frac{Q}{t}" in html and r"\text{ = }" in html  # Formel als TeX
    assert "Kachel 3" in html and "LS 3, AB 2" in html        # „AB n“ nur im eigenen Kurs ersetzt
    assert docx_seite.PDF_KNOPF in html and docx_seite.WORD_KNOPF in html
    assert docx_seite.PDF_HINWEIS not in html                 # Druck-PDF, kein Formular
    assert "KI-gestützt" in html
    assert pdf in dateien


def test_infoseiten_anwenden(gesamt, tmp_path, monkeypatch):
    monkeypatch.setattr(heftauszug, "pdf", lambda p: shutil.copyfile(p, p.with_suffix(".pdf")))
    i = heftauszug.kaesten(gesamt)[0][0]
    kurs = {"abschnitte": [{"aktivitaeten": [
        {"typ": "page", "name": "Info · A", "inhalt": "<div><p><a href=\"@@PLUGINFILE@@/A.docx\">x</a></p></div>",
         "dateien": ["2/A.docx"]},
        {"typ": "page", "name": "Info · B", "inhalt": "<p>alt</p>", "dateien": ["2/bild.png", "2/B.docx"]}]}]}
    seiten = {"Info · A": {"datei": "2/A.docx", "kaesten": [i], "modus": "lassen"},
              "Info · B": {"datei": "2/B.docx", "kaesten": [i], "modus": "heft", "kacheln": {2: 3}}}
    heftauszug.infoseiten_anwenden(kurs, seiten, tmp_path, gesamt)
    a, b = kurs["abschnitte"][0]["aktivitaeten"]
    assert "A.pdf" in a["inhalt"] and "2/A.pdf" in a["dateien"] and "<p>alt</p>" not in a["inhalt"]
    assert b["docx"] == ["2/B.docx"] and b["docx_stil"] == "heft" and b["docx_pdf"] == ["2/B.pdf"]
    assert b["breite"] == 680 and b["kacheln"] == {"2": 3} and b["dateien"] == []
    with pytest.raises(ValueError):
        heftauszug.infoseiten_anwenden(kurs, {"Info · fehlt": seiten["Info · A"]}, tmp_path, gesamt)


def test_p12_infoseite_ohne_pdf(variante):
    def aendern(k):
        k["kurs"]["infoseiten_downloads"] = "word_pdf"
        akt(k, "Infoblatt: Leistung im Haushalt")["rolle"] = "info"
    assert any("PDF" in b.text for b in variante(aendern) if b.pruefer == 12 and b.stufe == pruefen.FEHLER)
