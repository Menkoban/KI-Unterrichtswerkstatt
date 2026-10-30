"""Word-Dateien als Infoseite: DOCX → HTML mit Bildern und Download-Link."""
import base64
import re
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

docx = pytest.importorskip("docx")

import docx_seite  # noqa: E402

# 1×1-Pixel-PNG, rot
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC")


def _docx(pfad: Path, titel: str, bild_alt: str | None = "Schaltplan der Küche",
          bild: bool = True) -> Path:
    d = docx.Document()
    d.add_heading(titel, level=1)
    d.add_heading("Größen und Maße", level=2)
    p = d.add_paragraph("Der ")
    p.add_run("Zähler").bold = True
    p.add_run(" misst ")
    p.add_run("Wirkarbeit").italic = True
    p.add_run(" – äöüß ÄÖÜ <&>.")
    d.add_paragraph("Erster Punkt", style="List Bullet")
    d.add_paragraph("Zweiter Punkt", style="List Bullet")
    d.add_paragraph("Schritt eins", style="List Number")
    t = d.add_table(rows=2, cols=3)
    for z, zeile in enumerate([["Gerät", "Leistung", "Raum"],
                               ["Herd", "7 kW", "Küche"]]):
        for s, text in enumerate(zeile):
            t.cell(z, s).text = text
    if bild:
        png = pfad.parent / f"{pfad.stem}_quelle.png"
        png.write_bytes(PNG)
        form = d.add_picture(str(png))
        doc_pr = form._inline.docPr
        if bild_alt is None:
            doc_pr.attrib.pop("descr", None)
        else:
            doc_pr.set("descr", bild_alt)
    d.save(pfad)
    return pfad


@pytest.fixture
def eine(tmp_path):
    return _docx(tmp_path / "Anl_1_Zählerschrank.docx", "Zählerschrank prüfen")


def _wohlgeformt(html: str) -> ET.Element:
    return ET.fromstring(f"<div>{html}</div>")


def test_ueberschriften_werden_h3_und_h4(eine):
    html, _ = docx_seite.docx_zu_html(eine)
    assert "<h3>Zählerschrank prüfen</h3>" in html
    assert "<h4>Größen und Maße</h4>" in html
    assert "<h1" not in html and "<h2" not in html


def test_fett_kursiv_und_umlaute_maskiert(eine):
    html, _ = docx_seite.docx_zu_html(eine)
    assert "<strong>Zähler</strong>" in html
    assert "<em>Wirkarbeit</em>" in html
    assert "äöüß ÄÖÜ &lt;&amp;&gt;." in html
    _wohlgeformt(html)


def test_listen(eine):
    html, _ = docx_seite.docx_zu_html(eine)
    assert re.search(r"<ul>\s*<li>Erster Punkt</li>\s*<li>Zweiter Punkt</li>\s*</ul>", html)
    assert re.search(r"<ol>\s*<li>Schritt eins</li>\s*</ol>", html)


def test_tabelle_mit_zeilen_und_zellen(eine):
    html, _ = docx_seite.docx_zu_html(eine)
    tabelle = _wohlgeformt(html).find(".//table")
    assert tabelle is not None
    zeilen = tabelle.findall(".//tr")
    assert len(zeilen) == 2
    assert ["".join(z.itertext()).strip() for z in zeilen[1].findall("td")] == \
        ["Herd", "7 kW", "Küche"]
    assert len(zeilen[0].findall("td")) == 3
    assert "<td>Herd</td>" in html


def test_bild_als_datei_mit_alt(eine):
    html, bilder = docx_seite.docx_zu_html(eine)
    assert len(bilder) == 1
    assert bilder[0].read_bytes() == PNG
    assert bilder[0].suffix == ".png"
    img = _wohlgeformt(html).find(".//img")
    assert img.get("src") == "@@PLUGINFILE@@/" + urllib.parse.quote(bilder[0].name)
    assert img.get("alt") == "Schaltplan der Küche"
    assert img.get("role") is None


def test_bild_ohne_beschreibung_ist_dekorativ(tmp_path):
    pfad = _docx(tmp_path / "ohne_alt.docx", "Titel", bild_alt=None)
    html, _ = docx_seite.docx_zu_html(pfad)
    img = _wohlgeformt(html).find(".//img")
    assert img.get("alt") == ""
    assert img.get("role") == "presentation"


def test_seite_mit_download_link_auf_eingebettete_docx(eine):
    html, dateien = docx_seite.docx_seite_html([eine])
    assert eine in dateien
    wurzel = _wohlgeformt(html)
    links = [a for a in wurzel.iter("a")]
    assert len(links) == 1
    assert links[0].get("href") == "@@PLUGINFILE@@/Anl_1_Z%C3%A4hlerschrank.docx"
    assert "Als Word herunterladen" in "".join(wurzel.itertext())
    # Bild der DOCX liegt mit in der Seite
    assert any(d.suffix == ".png" for d in dateien)
    # Download-Link steht hinter dem Inhalt
    assert html.index("Herd") < html.index("Als Word herunterladen")


def test_zwei_docx_zwei_abschnitte_zwei_links(tmp_path):
    a = _docx(tmp_path / "a.docx", "Erstes Blatt")
    b = _docx(tmp_path / "b.docx", "Zweites Blatt", bild=False)
    html, dateien = docx_seite.docx_seite_html([a, b])
    wurzel = _wohlgeformt(html)
    abschnitte = wurzel.findall("section")
    assert len(abschnitte) == 2
    assert "Erstes Blatt" in "".join(abschnitte[0].itertext())
    assert "Zweites Blatt" in "".join(abschnitte[1].itertext())
    hrefs = [a.get("href") for a in wurzel.iter("a")]
    assert hrefs == ["@@PLUGINFILE@@/a.docx", "@@PLUGINFILE@@/b.docx"]
    assert a in dateien and b in dateien
    namen = [d.name for d in dateien]
    assert len(namen) == len(set(namen))


def test_gleiche_bildnamen_aus_zwei_docx_kollidieren_nicht(tmp_path):
    a = _docx(tmp_path / "a.docx", "A")
    b = _docx(tmp_path / "b.docx", "B")
    _, dateien = docx_seite.docx_seite_html([a, b])
    bilder = [d.name for d in dateien if d.suffix == ".png"]
    assert len(bilder) == 2 and len(set(bilder)) == 2


def test_verbundene_zellen(tmp_path):
    d = docx.Document()
    t = d.add_table(rows=3, cols=3)
    t.cell(0, 0).merge(t.cell(0, 1)).text = "breit"
    t.cell(1, 2).merge(t.cell(2, 2)).text = "hoch"
    d.save(tmp_path / "verbund.docx")
    html, _ = docx_seite.docx_zu_html(tmp_path / "verbund.docx")
    zeilen = _wohlgeformt(html).findall(".//tr")
    assert [len(z.findall("td")) for z in zeilen] == [2, 3, 2]
    assert zeilen[0].find("td").get("colspan") == "2"
    hoch = [td for td in zeilen[1].findall("td") if "hoch" in "".join(td.itertext())]
    assert hoch[0].get("rowspan") == "2"


def test_mehrfach_genutztes_bild_nur_einmal_abgelegt(tmp_path):
    png = tmp_path / "x.png"
    png.write_bytes(PNG)
    d = docx.Document()
    d.add_picture(str(png))
    d.add_picture(str(png))
    d.save(tmp_path / "doppelt.docx")
    html, bilder = docx_seite.docx_zu_html(tmp_path / "doppelt.docx")
    assert len(bilder) == 1
    quellen = [i.get("src") for i in _wohlgeformt(html).iter("img")]
    assert len(quellen) == 2 and len(set(quellen)) == 1


def test_alt_text_wird_maskiert(tmp_path):
    pfad = _docx(tmp_path / "alt.docx", "Titel", bild_alt='Plan "A" <B> & C')
    html, _ = docx_seite.docx_zu_html(pfad)
    assert _wohlgeformt(html).find(".//img").get("alt") == 'Plan "A" <B> & C'


def test_liste_am_ende_und_in_zelle_wird_geschlossen(tmp_path):
    d = docx.Document()
    t = d.add_table(rows=1, cols=1)
    zelle = t.cell(0, 0)
    zelle.paragraphs[0].text = "In der Zelle"
    zelle.paragraphs[0].style = d.styles["List Bullet"]
    d.add_paragraph("Vorher")
    d.add_paragraph("Letzter Punkt", style="List Bullet")
    d.save(tmp_path / "liste.docx")
    html, _ = docx_seite.docx_zu_html(tmp_path / "liste.docx")
    wurzel = _wohlgeformt(html)
    assert html.rstrip().endswith("</ul>")
    td = wurzel.find(".//td")
    assert td.find("ul/li").text == "In der Zelle"


def test_hyperlink_mit_maskierter_adresse(tmp_path):
    from docx.opc.constants import RELATIONSHIP_TYPE as RT
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    d = docx.Document()
    p = d.add_paragraph("Siehe ")
    url = "https://example.org/suche?a=1&b=2"
    rid = d.part.relate_to(url, RT.HYPERLINK, is_external=True)
    link = OxmlElement("w:hyperlink")
    link.set(qn("r:id"), rid)
    r = OxmlElement("w:r")
    t = OxmlElement("w:t")
    t.text = "Herstellerseite"
    r.append(t)
    link.append(r)
    p._p.append(link)
    d.save(tmp_path / "link.docx")
    html, _ = docx_seite.docx_zu_html(tmp_path / "link.docx")
    assert '<a href="https://example.org/suche?a=1&amp;b=2">Herstellerseite</a>' in html
    a = _wohlgeformt(html).find(".//a")
    assert a.get("href") == url


def test_gleichnamige_docx_in_zwei_ordnern_abgelehnt(tmp_path):
    (tmp_path / "1").mkdir()
    (tmp_path / "2").mkdir()
    a = _docx(tmp_path / "1" / "blatt.docx", "Eins", bild=False)
    b = _docx(tmp_path / "2" / "blatt.docx", "Zwei", bild=False)
    with pytest.raises(ValueError, match="blatt.docx"):
        docx_seite.docx_seite_html([a, b])


def test_bildnamen_kollidieren_ueber_bereinigten_stamm(tmp_path):
    a = _docx(tmp_path / "a b.docx", "Eins")
    b = _docx(tmp_path / "a_b.docx", "Zwei")
    with pytest.raises(ValueError, match="a_b_bild1.png"):
        docx_seite.docx_seite_html([a, b])


def test_zeilenumbruch(tmp_path):
    d = docx.Document()
    run = d.add_paragraph().add_run("Zeile 1")
    run.add_break()
    d.paragraphs[-1].add_run("Zeile 2")
    d.save(tmp_path / "umbruch.docx")
    html, _ = docx_seite.docx_zu_html(tmp_path / "umbruch.docx")
    assert "Zeile 1<br />Zeile 2" in html


def test_titel_wird_h3(tmp_path):
    d = docx.Document()
    d.add_heading("Haus Schütte", level=0)
    d.save(tmp_path / "titel.docx")
    html, _ = docx_seite.docx_zu_html(tmp_path / "titel.docx")
    assert "<h3>Haus Schütte</h3>" in html


# -- Bildschirmbreite: Bilder, Schreiblinien, Ausschneidebogen --------------- #
def test_bild_hoechstens_seitenbreit(eine):
    html, _ = docx_seite.docx_zu_html(eine)
    img = _wohlgeformt(html).find(".//img")
    assert img.get("style") == "max-width:100%;height:auto;"


def test_unterstriche_werden_umbrechende_linie(tmp_path):
    d = docx.Document()
    d.add_paragraph("weil ______________")
    d.add_paragraph("__________")
    pfad = tmp_path / "linien.docx"
    d.save(pfad)
    html, _ = docx_seite.docx_zu_html(pfad)
    assert "_____" not in html
    assert ('weil <span class="schreiblinie" style="display:inline-block;min-width:6em;'
            'width:60%;border-bottom:1px solid #9AA3AE;"></span>') in html
    assert '<div style="border-bottom:1px solid #9AA3AE;height:1.6em;"></div>' in html
    _wohlgeformt(html)


def _bogen(pfad: Path, zeilen: list[str]) -> Path:
    d = docx.Document()
    t = d.add_table(rows=len(zeilen), cols=1)
    for i, text in enumerate(zeilen):
        t.cell(i, 0).text = text
    d.save(pfad)
    return pfad


def test_ausschneidebogen_einmal(tmp_path):
    kopie = "Unsere Wahl für die Mappe: Zähler A"
    html, _ = docx_seite.docx_zu_html(_bogen(tmp_path / "bogen.docx", [kopie, kopie]))
    assert html.count("Unsere Wahl") == 1
    assert len(_wohlgeformt(html).findall(".//tr")) == 1


def test_verschiedene_kopien_bleiben(tmp_path):
    html, _ = docx_seite.docx_zu_html(_bogen(
        tmp_path / "anders.docx",
        ["Unsere Wahl für die Mappe: Zähler A", "Unsere Wahl für die Mappe: Zähler B"]))
    assert html.count("Unsere Wahl") == 2
    # nur ein Leerzeichen anders: auch das sind zwei verschiedene Kopien
    html, _ = docx_seite.docx_zu_html(_bogen(
        tmp_path / "leer.docx",
        ["Unsere Wahl für die Mappe: Zähler A", "Unsere Wahl für die Mappe: Zähler A "]))
    assert html.count("Unsere Wahl") == 2


# -- Word-Seiten mit mehreren Karten (Durchsicht LS 1, Punkt 26) --------------- #
FUSS = "LF 1 · LS 1 · DS 3 · Familie Schütte ist fiktiv. KI-gestützt erstellt"


def _kopf(zelle, kopf: list[str], logo: Path | None):
    """Kartenkopf wie in den Karten aus Pipeline 2: einzeilige Tabelle [leer, schmal | Titel | Logo] ganz oben."""
    innen = zelle.add_table(rows=1, cols=3)
    leer, titel, bild = innen.rows[0].cells
    titel.paragraphs[0].text = kopf[0]
    for zeile in kopf[1:]:
        titel.add_paragraph(zeile)
    if logo is not None:
        bild.paragraphs[0].add_run().add_picture(str(logo))
    zelle._tc.remove(innen._tbl)
    zelle._tc.insert(zelle._tc.index(zelle.paragraphs[0]._p), innen._tbl)  # Kopf vor den ersten Absatz
    return innen


def _karte(zelle, kopf: list[str], inhalt: list[str], logo: Path | None):
    _kopf(zelle, kopf, logo)
    zelle.paragraphs[0].text = inhalt[0]
    for text in inhalt[1:]:
        zelle.add_paragraph(text)
    zelle.add_paragraph(FUSS)


def _kartenbogen(pfad: Path, mit_logo: bool = True) -> Path:
    """Wie Anl_6_Auftrag_Satzanfaenge: 2×2, je Zeile zwei gleiche Kopien einer Karte."""
    logo = None
    if mit_logo:
        logo = pfad.parent / "logo.png"
        logo.write_bytes(PNG)
    d = docx.Document()
    t = d.add_table(rows=2, cols=2)
    for s in range(2):
        _karte(t.cell(0, s), ["Anlage 6 · Auftragskarte", "Kriterienkarten"],
               ["Woran merkt Familie Schütte, was für ein Betrieb wir sind?", "Schreiben Sie 3 bis 5 Karten."], logo)
        _karte(t.cell(1, s), ["Anlage 6 · Hilfe", "Satzanfänge"],
               ["Wenn Ihnen der Anfang fehlt:", "„Wichtig ist, dass …“"], logo)
    d.save(pfad)
    return pfad


def _knopftexte(html: str) -> list[str]:
    return ["".join(a.itertext()) for a in _wohlgeformt(html).iter("a")]


def test_knoepfe_je_datei_mit_namen(tmp_path):
    a = _docx(tmp_path / "Anl_6_Leitkarte.docx", "Leitkarte", bild=False)
    b = _docx(tmp_path / "Anl_6_Auftrag_Satzanfaenge.docx", "Satzanfänge", bild=False)
    c = _docx(tmp_path / "DS3_Anl_5c_Entscheidungsstreifen.docx", "Streifen", bild=False)
    pdf = tmp_path / "Anl_6_Leitkarte.pdf"
    pdf.write_bytes(b"%PDF")
    html, _ = docx_seite.docx_seite_html([a, b, c], {a: pdf})
    assert _knopftexte(html) == ["Leitkarte als PDF", "Leitkarte als Word", "Auftrag Satzanfaenge als Word",
                                 "Entscheidungsstreifen als Word"]
    assert html.count(docx_seite.PDF_HINWEIS) == 1
    # genau eine Datei: wie bisher
    html, _ = docx_seite.docx_seite_html([a], {a: pdf})
    assert _knopftexte(html) == ["Als PDF herunterladen", "Als Word herunterladen"]


def _eine_karte(pfad: Path, kopf: list[str]) -> Path:
    logo = pfad.parent / "logo.png"
    logo.write_bytes(PNG)
    d = docx.Document()
    _karte(d.add_table(rows=1, cols=1).cell(0, 0), kopf, ["Schreiben Sie weiter."], logo)
    d.save(pfad)
    return pfad


def test_knopfname_aus_kartentitel(tmp_path):
    a = _eine_karte(tmp_path / "Anl_6_Auftrag_Satzanfaenge.docx", ["Anlage 6 · Auftragskarte", "Satzanfänge"])
    b = _docx(tmp_path / "Anl_6_Leitkarte.docx", "Leitkarte", bild=False)
    html, _ = docx_seite.docx_seite_html([a, b])
    assert _knopftexte(html) == ["Satzanfänge als Word", "Leitkarte als Word"]


def test_knopfname_ohne_karte_aus_dateiname(tmp_path):
    a = _docx(tmp_path / "Anl_6_Auftrag_Satzanfaenge.docx", "Satzanfänge", bild=False)
    b = _docx(tmp_path / "Anl_5a_Kriterienzettel.docx", "Kriterienzettel", bild=False)
    html, _ = docx_seite.docx_seite_html([a, b])
    assert _knopftexte(html) == ["Auftrag Satzanfaenge als Word", "Kriterienzettel als Word"]


def test_knopfname_hilfekarte_nur_wenn_sonst_keine(tmp_path):
    # Auftragskarte „Kriterienkarten“ vor Hilfe „Satzanfänge“: der Auftrag benennt die Datei
    a = _kartenbogen(tmp_path / "Anl_6_Auftrag_Satzanfaenge.docx")
    hilfe = _eine_karte(tmp_path / "Anl_4_Hilfe_Grundriss.docx", ["Anlage 4 · Hilfe", "Raumplan zeichnen"])
    html, _ = docx_seite.docx_seite_html([hilfe, a])
    assert _knopftexte(html) == ["Raumplan zeichnen als Word", "Kriterienkarten als Word"]
    # Hilfe zuerst im Dokument, Auftrag danach: trotzdem der Auftrag
    d = docx.Document(a)
    zeilen = d.tables[0]._tbl.tr_lst
    zeilen[0].addprevious(zeilen[1])
    d.save(a)
    html, _ = docx_seite.docx_seite_html([hilfe, a])
    assert _knopftexte(html)[-1] == "Kriterienkarten als Word"


def test_keine_doppelten_knoepfe(tmp_path):
    a = _docx(tmp_path / "Anl_6_Leitkarte.docx", "Leitkarte", bild=False)
    b = _docx(tmp_path / "Anl_6_Auftrag_Satzanfaenge.docx", "Satzanfänge", bild=False)
    pdf = tmp_path / "Anl_6_Leitkarte.pdf"
    pdf.write_bytes(b"%PDF")
    pdf_b = tmp_path / "Anl_6_Auftrag_Satzanfaenge.pdf"
    pdf_b.write_bytes(b"%PDF")
    for oben in (False, True):
        html, _ = docx_seite.docx_seite_html([a, b, a], {a: pdf, b: pdf_b}, knoepfe_oben=oben)
        hrefs = [x.get("href") for x in _wohlgeformt(html).iter("a")]
        assert len(hrefs) == len(set(hrefs)) == 4, (oben, hrefs)
        assert html.count(docx_seite.PDF_HINWEIS) == 1
    # oben: alle Knöpfe vor dem ersten Abschnitt
    assert html.rindex("btn-outline-primary") < html.index("<section>")


def test_kopien_nebeneinander_einmal(tmp_path):
    d = docx.Document()
    t = d.add_table(rows=1, cols=2)
    for s in range(2):
        t.cell(0, s).text = "Für die Mappe nehmen wir: Zähler A"
    pfad = tmp_path / "nebeneinander.docx"
    d.save(pfad)
    html, _ = docx_seite.docx_zu_html(pfad)
    assert html.count("Für die Mappe") == 1
    assert len(_wohlgeformt(html).findall(".//td")) == 1


def test_ungleiche_zellen_bleiben(tmp_path):
    d = docx.Document()
    t = d.add_table(rows=3, cols=2)
    t.cell(0, 0).text, t.cell(0, 1).text = "Zähler A", "Zähler A "       # ein Leerzeichen anders
    t.cell(1, 0).text, t.cell(1, 1).text = "Kunde", "Familie Schütte"
    t.cell(2, 0).text, t.cell(2, 1).text = "", ""                        # leere Ausfüllzeile
    pfad = tmp_path / "ungleich.docx"
    d.save(pfad)
    html, _ = docx_seite.docx_zu_html(pfad)
    assert html.count("Zähler A") == 2
    assert len(_wohlgeformt(html).findall(".//td")) == 6


def _karten(html: str):
    """Kartenblöcke: div mit Kopf-div als erstem Kind."""
    return [div for div in _wohlgeformt(html).iter("div")
            if len(div) and div[0].tag == "div" and div.get("class") == "karte"]


def test_karte_mit_blauem_kopf(tmp_path):
    html, _ = docx_seite.docx_zu_html(_kartenbogen(tmp_path / "Anl_6_Auftrag_Satzanfaenge.docx"))
    assert "<table" not in html, "Karten stehen untereinander, nicht in einer Tabelle"
    assert html.count("Kriterienkarten") == 1 and html.count("Satzanfänge") == 1
    karten = _karten(html)
    assert len(karten) == 2
    kopf = karten[0][0]
    assert "background:#08349C" in kopf.get("style") and "color:#fff" in kopf.get("style")
    assert "Kriterienkarten" in "".join(kopf.itertext())
    assert "Woran merkt" in "".join(karten[0].itertext())
    assert "Woran merkt" not in "".join(kopf.itertext())
    assert html.index("Kriterienkarten") < html.index("Satzanfänge")


def test_hilfekarte_gelb(tmp_path):
    html, _ = docx_seite.docx_zu_html(_kartenbogen(tmp_path / "karten.docx"))
    hilfe = [k for k in _karten(html) if "Hilfe" in "".join(k[0].itertext())]
    assert len(hilfe) == 1
    stil = hilfe[0].get("style")
    assert "background:#FFF4CC" in stil and "border:1px solid #E0A800" in stil
    assert "#08349C" not in (hilfe[0][0].get("style") or "")
    assert "Wichtig ist" in "".join(hilfe[0].itertext())


def test_schulkopf_ohne_leere_spalte(tmp_path):
    logo = tmp_path / "logo.png"
    logo.write_bytes(PNG)
    d = docx.Document()
    t = d.add_table(rows=1, cols=3)
    t.cell(0, 1).text = "BBS Musterstadt · Lernfeld 1"
    t.cell(0, 2).paragraphs[0].add_run().add_picture(str(logo))
    d.add_paragraph("Text")
    pfad = tmp_path / "kopf.docx"
    d.save(pfad)
    html, _ = docx_seite.docx_zu_html(pfad)
    zellen = _wohlgeformt(html).findall(".//td")
    assert len(zellen) == 2
    assert all("".join(z.itertext()).strip() or z.find(".//img") is not None for z in zellen)


def test_fusszeile_einmal_klein_grau(tmp_path):
    html, _ = docx_seite.docx_zu_html(_kartenbogen(tmp_path / "karten.docx", mit_logo=False))
    assert html.count("KI-gestützt erstellt") == 1
    assert html.rstrip().endswith("</p>") and html.rindex("KI-gestützt") > html.rindex("Wichtig ist")
    assert f'<p style="font-size:smaller;color:#6B7280;">{FUSS}</p>' in html
    # mehrere Dateien auf einer Seite: Fußzeile einmal, ganz am Ende hinter den Knöpfen
    a = _kartenbogen(tmp_path / "a.docx", mit_logo=False)
    b = _kartenbogen(tmp_path / "b.docx", mit_logo=False)
    html, _ = docx_seite.docx_seite_html([a, b])
    assert html.count("KI-gestützt erstellt") == 1
    assert html.rindex("KI-gestützt") > html.rindex("btn-outline-primary")
