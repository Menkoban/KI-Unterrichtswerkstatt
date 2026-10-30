"""Infokästen aus dem Arbeitsheft (Gesamtfassung aus Pipeline 2) als eigene Word- und PDF-Datei und als Infoseite.

Lehrkraft 2026-10-27: Infoseiten sehen aus wie der Infokasten im Arbeitsblatt (Profil `moodle.infoseiten_wie_heft`),
und auf jeder Infoseite gibt es Word und PDF zum Herunterladen, die genauso aussehen (`moodle.infoseiten_downloads`
„word_pdf“). Eine Quelle für alles: der Auszug aus der Gesamtfassung.

    kaesten(gesamt)                                   # [(Index im Body, Kennwort, Titel), …]
    auszug(gesamt, [56, 58], ziel)                    # Word-Datei mit genau diesen Kästen, Kopf- und Fußzeile
    pdf(ziel_docx)                                    # PDF daneben (LibreOffice)
    infoseiten_anwenden(kursdef, seiten, dateien)     # Infoseiten der Kursdefinition umstellen

`seiten` je Infoseite (Name der Seite): {"kaesten": [Index, …], "modus": "heft" | "lassen",
"datei": "<n>/<Name>.docx", "kacheln": {AB-Nummer: Kachel}, "extra": [weitere Word-Dateien], "ersetzen": {Text: anders,
z. B. eine Adresse, die in dieser Kachel noch nicht stehen soll}}. „heft“: die Seite zeigt den Auszug (Word wird beim
Bau mit docx_seite im Heft-Stil gewandelt, 680 px breit, mittig); „lassen“: das HTML der Seite bleibt, nur die
Download-Knöpfe zeigen Word und PDF des Auszugs.
"""
from __future__ import annotations

import copy
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
KASTEN = re.compile(r"^(Info|Unterlage)\s{2,}(.+)$", re.S)
FASSUNG = 2   # bei Änderungen am Auszug erhöhen: dann entstehen alle Auszüge neu
QUELLE = re.compile(r"\[(\d+(?:\s*[,–-]\s*\d+)*)\]")   # [3], [6, 8], [4–6]


def _text(el) -> str:
    return "".join(t.text or "" for t in el.iter(W + "t"))


def kaesten(gesamt: Path) -> list[tuple[int, str, str]]:
    """Alle Info- und Unterlage-Kästen der Gesamtfassung: (Index im Body, Kennwort, Anfang des Titels)."""
    import docx
    body = docx.Document(str(gesamt)).element.body
    aus = []
    for i, el in enumerate(body.iterchildren()):
        if el.tag == W + "tbl":
            m = KASTEN.match(_text(el))
            if m:
                aus.append((i, m.group(1), m.group(2)[:80]))
    return aus


def _nummern(gruppe: str) -> list[str]:
    """„6, 8“ → [6, 8]; „4–6“ → [4, 5, 6]."""
    aus = []
    for teil in re.split(r"\s*,\s*", gruppe.strip()):
        grenzen = [int(z) for z in re.split(r"\s*[–-]\s*", teil)]
        aus += [str(n) for n in range(grenzen[0], grenzen[-1] + 1)]
    return aus


def _quellen(body) -> dict[str, object]:
    """Einträge des Quellenverzeichnisses am Ende der Gesamtfassung: Nummer → Absatz."""
    aus, im_verzeichnis = {}, False
    for el in body.iterchildren():
        t = _text(el)
        if el.tag == W + "p" and t.strip() == "Quellenverzeichnis":
            im_verzeichnis = True
            continue
        if im_verzeichnis and el.tag == W + "p":
            m = re.match(r"\[(\d+)\]", t)
            if m:
                aus[m.group(1)] = el
    return aus


def auszug(gesamt: Path, teile: list[int], ziel: Path, ersetzen: dict[str, str] | None = None) -> Path:
    """Word-Datei mit den Body-Elementen `teile` der Gesamtfassung in Heftreihenfolge (Formatvorlagen, Bilder,
    Kopf- und Fußzeile mit KI-Hinweis bleiben). Die in den Kästen genannten Quellen [n] folgen als kurzes
    Quellenverzeichnis wie im Heft. `ersetzen`: Text, der im Auszug anders heißen soll."""
    import docx
    d = docx.Document(str(gesamt))
    body = d.element.body
    els = list(body.iterchildren())
    schluss = els[-1]
    assert schluss.tag == W + "sectPr", "Gesamtfassung ohne Abschlusseinstellungen"
    if not any("Reference" in c.tag for c in schluss):     # spätere Abschnitte erben Kopf und Fuß vom ersten
        vorbild = next((s for el in els[:-1] for s in el.iter(W + "sectPr")
                        if any("Reference" in c.tag for c in s)), None)
        if vorbild is not None:
            for c in reversed([c for c in vorbild if "Reference" in c.tag]):
                schluss.insert(0, copy.deepcopy(c))
    quellen = _quellen(body)
    behalten = [els[i] for i in sorted(teile)]
    genannt = sorted({n for el in behalten for gruppe in QUELLE.findall(_text(el)) for n in _nummern(gruppe)
                      if n in quellen}, key=int)
    kopf = next((el for el in els if el.tag == W + "p" and _text(el).strip() == "Quellenverzeichnis"), None)
    eintraege = [copy.deepcopy(quellen[n]) for n in genannt]
    kopf_kopie = copy.deepcopy(kopf) if (kopf is not None and eintraege) else None
    for el in els[:-1]:
        body.remove(el)
    leer = next((e for e in els if e.tag == W + "p" and not _text(e).strip()), None)
    for el in behalten:
        schluss.addprevious(el)
        schluss.addprevious(copy.deepcopy(leer) if leer is not None else body.makeelement(W + "p", {}))
    if kopf_kopie is not None:
        for br in kopf_kopie.iter(W + "br"):        # im Heft beginnt das Verzeichnis auf einer neuen Seite
            br.getparent().remove(br)
        for pb in list(kopf_kopie.iter(W + "pageBreakBefore")):
            pb.getparent().remove(pb)
        schluss.addprevious(kopf_kopie)
        for e in eintraege:
            schluss.addprevious(e)
    for alt, neu in (ersetzen or {}).items():
        for t in body.iter(W + "t"):
            if t.text and alt in t.text:
                t.text = t.text.replace(alt, neu)
    ziel = Path(ziel)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    d.save(str(ziel))
    return ziel


def pdf(docx_pfad: Path) -> Path:
    """PDF neben der Word-Datei (LibreOffice), gleicher Name."""
    docx_pfad = Path(docx_pfad)
    ziel = docx_pfad.with_suffix(".pdf")
    arbeit = Path(tempfile.mkdtemp(prefix="heftauszug_"))
    try:
        quelle = arbeit / "auszug.docx"
        shutil.copyfile(docx_pfad, quelle)
        subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(arbeit), str(quelle)],
                       check=True, capture_output=True, timeout=240)
        shutil.move(str(arbeit / "auszug.pdf"), ziel)
    finally:
        shutil.rmtree(arbeit, ignore_errors=True)
    return ziel


_KNOPF_ALT = r"<p[^>]*>(?:(?!</p>).)*?@@PLUGINFILE@@/{}(?:(?!</p>).)*</p>"


def _auszug_mit_pdf(gesamt: Path, teile: list[int], ziel: Path, mit_pdf: bool,
                    ersetzen: dict[str, str] | None = None) -> None:
    """Auszug und PDF nur neu, wenn sich Gesamtfassung oder Kastenauswahl geändert haben (LibreOffice ist
    langsam); der Stempel neben der Datei hält beides fest."""
    stempel = ziel.with_name(f".{ziel.name}.auszug")
    soll = json.dumps({"fassung": FASSUNG, "gesamt": Path(gesamt).name, "groesse": Path(gesamt).stat().st_size,
                       "zeit": int(Path(gesamt).stat().st_mtime), "teile": sorted(teile),
                       "ersetzen": ersetzen or {}}, ensure_ascii=False)
    pdf_da = ziel.with_suffix(".pdf").is_file() or not mit_pdf
    if ziel.is_file() and pdf_da and stempel.is_file() and stempel.read_text(encoding="utf-8") == soll:
        return
    auszug(gesamt, teile, ziel, ersetzen)
    if mit_pdf:
        pdf(ziel)
    stempel.write_text(soll, encoding="utf-8")


def infoseiten_anwenden(kursdef: dict, seiten: dict[str, dict], dateien: Path, gesamt: Path,
                        wie_heft: bool = True, downloads: str = "word_pdf") -> list[str]:
    """Infoseiten der Kursdefinition nach `seiten` (Schlüssel: Name der Seite) umstellen, siehe Modulbeschreibung;
    `wie_heft` und `downloads` kommen aus dem Profil (moodle.infoseiten_wie_heft, moodle.infoseiten_downloads).
    Ohne `wie_heft` bleibt jede Seite, wie sie ist („lassen“). `extra` in einer Vorgabe: weitere Word-Dateien der
    Seite, die als eigener Knopf unter dem Kasten stehen. Gibt die Namen der umgestellten Seiten zurück; eine
    genannte Seite, die im Kurs fehlt, ist ein Fehler."""
    import docx_seite
    dateien = Path(dateien)
    mit_pdf = downloads == "word_pdf"
    gefunden = []
    for ab in kursdef.get("abschnitte", []):
        for akt in ab.get("aktivitaeten", []):
            vorgabe = seiten.get(akt.get("name"))
            if akt.get("typ") != "page" or vorgabe is None:
                continue
            rel = vorgabe["datei"]
            _auszug_mit_pdf(gesamt, vorgabe["kaesten"], dateien / rel, mit_pdf, vorgabe.get("ersetzen"))
            pdf_rel = Path(rel).with_suffix(".pdf").as_posix() if mit_pdf else None
            if mit_pdf and akt.get("beschreibung"):
                akt["beschreibung"] = re.sub(r"\bals Word herunterladen", "als Word oder PDF herunterladen",
                                             akt["beschreibung"])
            if wie_heft and vorgabe.get("modus") == "heft":
                extra = vorgabe.get("extra") or []
                akt["inhalt"] = "\n".join(docx_seite.knoepfe_html(Path(e).name,
                                                                 name=docx_seite.knopfname(Path(e).name))
                                          for e in extra)
                akt["dateien"] = list(extra)
                akt["docx"] = [rel]
                akt["docx_stil"] = "heft"
                if pdf_rel:
                    akt["docx_pdf"] = [pdf_rel]
                akt["kacheln"] = {str(k): v for k, v in (vorgabe.get("kacheln") or {}).items()}
                akt["breite"] = 680
            else:
                name = Path(rel).name
                knopf = docx_seite.knoepfe_html(name, Path(pdf_rel).name if pdf_rel else None, hinweis=False)
                alt = re.compile(_KNOPF_ALT.format(re.escape(name)), re.S)
                inhalt = akt.get("inhalt") or ""
                if alt.search(inhalt):
                    inhalt = alt.sub(lambda m: knopf, inhalt, count=1)
                else:   # Knopf oben in den äußeren Rahmen
                    inhalt = re.sub(r"^(<div[^>]*>)?", lambda m: (m.group(1) or "") + knopf, inhalt, count=1)
                akt["inhalt"] = inhalt
                akt.setdefault("dateien", [])
                for d in (rel, pdf_rel):
                    if d and d not in akt["dateien"]:
                        akt["dateien"].append(d)
            gefunden.append(akt["name"])
    fehlt = sorted(set(seiten) - set(gefunden))
    if fehlt:
        raise ValueError("Infoseiten nicht im Kurs: " + ", ".join(fehlt))
    return gefunden
