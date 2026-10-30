"""Die schützenden Prüfer (KONZEPT Punkt 27, Prüfer 8 seit 2026-10-22, Prüfer 9 Sternzähler seit
2026-10-23, Prüfer 10 Sternebuch seit 2026-10-25, Prüfer 12 Infoseiten mit Word und PDF seit 2026-10-27, Prüfer 13 Vorgriff seit 2026-10-27, Prüfer 14 Inseln seit 2026-10-28) für eine gebaute Sicherung. Prüfer 10 meldet nur etwas, wenn der
Kurs ein Sternebuch hat (sternebuch.py).

    befunde = pruefe(paket, kursdef)       # paket: .mbz oder entpackter Ordner

Jeder Prüfer liefert Befunde mit Stufe „Fehler“ (hält den Bau an) oder
„Hinweis“. Die Kursdefinition ist optional; ohne sie gelten Namensregeln
(„Lehrkr…“ im Abschnitt, „Lösung“ im Titel, „Medaille“ im Titel).

    python3 pruefen.py kurs.mbz [--kurs kurs.json]
"""
from __future__ import annotations

import ast
import decimal
import difflib
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import inseln  # noqa: E402
import kursdefinition as kd  # noqa: E402
import sternebuch  # noqa: E402
import vorgriff  # noqa: E402

FEHLER, HINWEIS = "Fehler", "Hinweis"
TITEL = {1: "Paket gültig", 2: "Lösungen verborgen", 3: "Rechenfragen",
         4: "Keine leeren Hüllen", 5: "Angekündigtes vorhanden",
         6: "Medaillen lückenlos", 7: "Alternativtexte", 8: "Abgabe je Kachel", 9: "Sternzähler",
         10: "Sternebuch", 11: "Kursseite nur Auftrag", 12: "Infoseiten mit Word und PDF", 13: "Vorgriff",
         14: "Inseln"}


@dataclass
class Befund:
    stufe: str
    pruefer: int
    text: str

    def __str__(self) -> str:
        return f"[{self.stufe}] P{self.pruefer} {TITEL[self.pruefer]}: {self.text}"


# --------------------------------------------------------------------------- #
# Paket lesen
# --------------------------------------------------------------------------- #
class Paket:
    """Ein entpacktes Paket mit den Angaben aus moodle_backup.xml."""

    def __init__(self, ordner: Path):
        self.o = Path(ordner)
        self._cache: dict[str, ET.Element | None] = {}
        self.kaputt: list[str] = []
        b = self.xml("moodle_backup.xml")
        if b is None:
            raise ValueError("moodle_backup.xml fehlt oder ist kein XML")
        self.backup = b
        self.akts = [{k: a.findtext(k) for k in ("moduleid", "sectionid", "modulename",
                                                 "title", "directory")}
                     for a in b.findall("information/contents/activities/activity")]
        self.secs = [{k: s.findtext(k) for k in ("sectionid", "title", "directory")}
                     for s in b.find("information/contents/sections")]

    def xml(self, rel: str) -> ET.Element | None:
        if rel not in self._cache:
            try:
                self._cache[rel] = ET.parse(self.o / rel).getroot()
            except FileNotFoundError:
                self._cache[rel] = None
            except ET.ParseError as e:
                self.kaputt.append(f"{rel}: {e}")
                self._cache[rel] = None
        return self._cache[rel]

    def modul(self, a: dict) -> ET.Element | None:
        return self.xml(f"{a['directory']}/module.xml")

    def haupt(self, a: dict) -> ET.Element | None:
        w = self.xml(f"{a['directory']}/{a['modulename']}.xml")
        return None if w is None else w.find(a["modulename"])

    def abschnitt(self, sec_id: str) -> ET.Element | None:
        s = next((s for s in self.secs if s["sectionid"] == sec_id), None)
        return None if s is None else self.xml(f"{s['directory']}/section.xml")

    def sichtbar(self, a: dict) -> bool:
        m, s = self.modul(a), self.abschnitt(a["sectionid"])
        return (m is not None and m.findtext("visible") == "1"
                and (s is None or s.findtext("visible") == "1"))

    def html_texte(self):
        """(Ort, HTML) aus Kursbeschreibung, Abschnitten und Aktivitäten."""
        k = self.xml("course/course.xml")
        if k is not None:
            yield "Kursbeschreibung", k.findtext("summary") or ""
        for s in self.secs:
            sx = self.xml(f"{s['directory']}/section.xml")
            if sx is not None:
                yield f"Abschnitt {s['title']}", sx.findtext("summary") or ""
        for a in self.akts:
            h = self.haupt(a)
            if h is not None:
                for feld in ("intro", "content"):
                    if h.findtext(feld):
                        yield f"{a['title']} ({feld})", h.findtext(feld)

    def alle_xml(self):
        for p in sorted(self.o.rglob("*.xml")):
            rel = p.relative_to(self.o).as_posix()
            w = self.xml(rel)
            if w is not None:
                yield rel, w


def entpacken(mbz: Path) -> Path:
    ziel = Path(tempfile.mkdtemp(prefix="mbz_pruefen_"))
    with tarfile.open(mbz, "r:gz") as tar:
        tar.extractall(ziel, filter="data")
    return ziel


def _verfuegbarkeit(m: ET.Element | None) -> dict | None:
    roh = None if m is None else m.findtext("availability")
    if not roh or roh == "$@NULL@$":
        return None
    return json.loads(roh)


def _name(t: str) -> str:
    return re.sub(r"\s+", " ", t or "").strip().lower()


def _akt_def(kursdef: dict | None) -> dict:
    return {a["name"]: (ab, a) for ab, a in kd.alle_aktivitaeten(kursdef or {})}


def _kurs_items(p: Paket) -> list[str]:
    """Ids der Kursgesamt-Bewertung (Kurs-Gradeitem) aus gradebook.xml."""
    gb = p.xml("gradebook.xml")
    return [gi.get("id") for gi in (gb.iter("grade_item") if gb is not None else [])
            if gi.findtext("itemtype") == "course"]


def _berechnete(p: Paket) -> list[ET.Element]:
    """Berechnete Kurs-Gradeitems (mit calculation, z. B. „Sterne: <Test>“) aus gradebook.xml."""
    gb = p.xml("gradebook.xml")
    return [gi for gi in (gb.iter("grade_item") if gb is not None else [])
            if (gi.findtext("calculation") or "$@NULL@$") not in ("", "$@NULL@$")]


def _in_formeln(p: Paket) -> set[str]:
    """Gradeitem-Ids, auf die eine berechnete Bewertung zeigt (##gi<id>##)."""
    return {i for gi in _berechnete(p) for i in re.findall(r"##gi(\d+)##", gi.findtext("calculation"))}


def _bedingungen(v: dict | None):
    """(Bedingung, gesperrt sichtbar) aller Einzelbedingungen eines UND-Baums."""
    if not v:
        return
    showc = v.get("showc") or [v.get("show", False)] * len(v.get("c", []))
    for c, zeigen in zip(v.get("c", []), showc):
        if "c" in c:
            yield from _bedingungen(c)
        else:
            yield c, bool(zeigen)


# --------------------------------------------------------------------------- #
# (1) Paket gültig und vollständig
# --------------------------------------------------------------------------- #
#: HTML-Felder mit Skript oder Stil (Vorlagen der Datenbank), in denen „src“ und „href“ Programmtext sind
OHNE_HTML = {"jstemplate", "csstemplate"}
SRC = re.compile(r"""<(?:img|source|audio|video|iframe)\b[^>]*?\bsrc\s*=\s*(["'])(.*?)\1""", re.I | re.S)
HREF = re.compile(r"""<a\b[^>]*?\bhref\s*=\s*(["'])(.*?)\1""", re.I | re.S)
OK_SRC = re.compile(r"^(?:@@PLUGINFILE@@/|https?://|data:|//|\$@)", re.I)


def verweis_befunde(p: Paket) -> list[str]:
    """Kaputte Verweise im HTML der Aktivitäten (Sichtprüfung LS 5): Bild mit relativem Pfad statt
    @@PLUGINFILE@@ (im Kurs 404), Link im Link (`<a href="<a href=…`) und verschachtelte Links."""
    aus = []
    for rel, w in p.alle_xml():
        for knoten in w.iter():
            t = knoten.text or ""
            if knoten.tag in OHNE_HTML or "<" not in t:
                continue
            for m in SRC.finditer(t):
                if not OK_SRC.match(m.group(2).strip()):
                    aus.append(f"{rel} <{knoten.tag}>: Bild mit Pfad {m.group(2)[:60]!r} ohne @@PLUGINFILE@@ "
                               "(erscheint im Kurs nicht)")
            for m in HREF.finditer(t):
                if "<" in m.group(2) or not m.group(2).strip():
                    aus.append(f"{rel} <{knoten.tag}>: ungültiger Link {m.group(2)[:60]!r}")
            for teil in re.split(r"</a\s*>", t, flags=re.I):
                if len(re.findall(r"<a\b", teil, re.I)) > 1:
                    aus.append(f"{rel} <{knoten.tag}>: Link im Link")
                    break
    return aus


def p1_paket(p: Paket, kursdef: dict | None) -> list[Befund]:
    f = [Befund(FEHLER, 1, t) for t in kd.pruefe(kursdef)] if kursdef else []
    for rel in ("files.xml", "questions.xml", "course/course.xml", "groups.xml",
                "gradebook.xml", "roles.xml"):
        if p.xml(rel) is None:
            f.append(Befund(FEHLER, 1, f"{rel} fehlt"))
    list(p.alle_xml())
    f += [Befund(FEHLER, 1, f"kein gültiges XML: {k}") for k in p.kaputt]
    f += [Befund(FEHLER, 1, t) for t in verweis_befunde(p)]
    version = p.backup.findtext("information/backup_version") or ""
    if not version.isdigit():
        f.append(Befund(FEHLER, 1, "backup_version fehlt"))
    elif int(version) > 2025041400:
        f.append(Befund(HINWEIS, 1, f"backup_version {version}: spielt erst in neuerem "
                                    f"Moodle als 5.0 ein"))
    cmids = {a["moduleid"] for a in p.akts}
    for a in p.akts:
        for datei in ("module.xml", f"{a['modulename']}.xml", "inforef.xml"):
            if p.xml(f"{a['directory']}/{datei}") is None:
                f.append(Befund(FEHLER, 1, f"{a['title']}: {datei} fehlt"))
        m = p.modul(a)
        if m is not None and (m.get("id") != a["moduleid"]
                              or m.findtext("sectionid") != a["sectionid"]):
            f.append(Befund(FEHLER, 1, f"{a['title']}: module.xml passt nicht zu "
                                       f"moodle_backup.xml"))
    for a in p.akts:          # Moodle 5.1: Aufgabe ohne Grade Item bricht beim Öffnen ab („Cannot load the grade item“)
        g = p.xml(f"{a['directory']}/grades.xml")
        if a["modulename"] == "assign" and not list(g.iter("grade_item") if g is not None else []):
            f.append(Befund(FEHLER, 1, f"{a['title']}: Aufgabe ohne Bewertungsaspekt – Moodle kann sie nicht öffnen"))
    in_folge: dict[str, str] = {}
    for s in p.secs:
        sx = p.xml(f"{s['directory']}/section.xml")
        if sx is None:
            f.append(Befund(FEHLER, 1, f"Abschnitt {s['title']}: section.xml fehlt"))
            continue
        for c in filter(None, (sx.findtext("sequence") or "").split(",")):
            if c not in cmids:
                f.append(Befund(FEHLER, 1, f"Abschnitt {s['title']}: cmid {c} ohne Aktivität"))
            in_folge[c] = s["sectionid"]
    for a in p.akts:
        if in_folge.get(a["moduleid"]) != a["sectionid"]:
            f.append(Befund(FEHLER, 1, f"{a['title']}: steht in keiner Abschnittsfolge"))
    # Dateispeicher
    dateien = p.xml("files.xml")
    datei_ids = set()
    for d in (dateien if dateien is not None else []):
        datei_ids.add(d.get("id"))
        if d.findtext("filename") == ".":
            continue
        h = d.findtext("contenthash")
        pfad = p.o / "files" / h[:2] / h
        if not pfad.is_file():
            f.append(Befund(FEHLER, 1, f"Datei {d.findtext('filename')} fehlt im Paket"))
        elif hashlib.sha1(pfad.read_bytes()).hexdigest() != h:
            f.append(Befund(FEHLER, 1, f"Datei {d.findtext('filename')}: Prüfsumme falsch"))
    kategorien = {c.get("id") for c in p.xml("questions.xml").iter("question_category")} \
        if p.xml("questions.xml") is not None else set()
    eintraege = {e.get("id") for e in p.xml("questions.xml").iter("question_bank_entry")} \
        if p.xml("questions.xml") is not None else set()
    for rel, w in p.alle_xml():
        if rel.endswith("inforef.xml"):
            for i in w.findall("fileref/file/id"):
                if i.text not in datei_ids:
                    f.append(Befund(FEHLER, 1, f"{rel}: Datei-Id {i.text} fehlt in files.xml"))
            for i in w.findall("question_categoryref/question_category/id"):
                if i.text not in kategorien:
                    f.append(Befund(FEHLER, 1, f"{rel}: Fragenkategorie {i.text} fehlt"))
        for q in w.iter("questionbankentryid"):
            if q.text not in eintraege:
                f.append(Befund(FEHLER, 1, f"{rel}: Frage {q.text} fehlt in questions.xml"))
    # Bezüge in Voraussetzungen und Abzeichen
    noten = set(_kurs_items(p)) | {gi.get("id") for gi in _berechnete(p)}   # auch berechnete (stufen.py)
    for a in p.akts:
        g = p.xml(f"{a['directory']}/grades.xml")
        noten |= {gi.get("id") for gi in (g.iter("grade_item") if g is not None else [])}
    for a in p.akts:
        try:
            v = _verfuegbarkeit(p.modul(a))
        except json.JSONDecodeError:
            f.append(Befund(FEHLER, 1, f"{a['title']}: Voraussetzung ist kein JSON"))
            continue
        for c in (v or {}).get("c", []):
            if c.get("type") == "grade" and str(c.get("id")) not in noten:
                f.append(Befund(FEHLER, 1, f"{a['title']}: Voraussetzung auf unbekannte Bewertung"))
            if c.get("type") == "completion" and str(c.get("cm")) not in cmids:
                f.append(Befund(FEHLER, 1, f"{a['title']}: Voraussetzung auf unbekannte Aktivität"))
    abz = p.xml("badges.xml")
    for par in (abz.iter("parameter") if abz is not None else []):
        name = par.findtext("name") or ""
        if name.startswith("module_") and name[7:] not in cmids:
            f.append(Befund(FEHLER, 1, f"Abzeichen zeigt auf unbekannte Aktivität {name}"))
    return f


# --------------------------------------------------------------------------- #
# (2) Lösungen und Lehrkraftmaterial verborgen
# --------------------------------------------------------------------------- #
def p2_verborgen(p: Paket, kursdef: dict | None) -> list[Befund]:
    f = []
    defs = _akt_def(kursdef)
    lehr_def = {ab.get("name") for ab in (kursdef or {}).get("abschnitte", []) if ab.get("lehrkraft")}
    lehr_ids = set()
    for s in p.secs:
        if s["title"] in lehr_def or (not kursdef and "lehrkr" in (s["title"] or "").lower()):
            lehr_ids.add(s["sectionid"])
            sx = p.xml(f"{s['directory']}/section.xml")
            if sx is not None and sx.findtext("visible") != "0":
                f.append(Befund(FEHLER, 2, f"Abschnitt {s['title']!r} für Lehrkräfte ist sichtbar"))
    if not lehr_ids:
        f.append(Befund(HINWEIS, 2, "kein Abschnitt für Lehrkräfte im Kurs"))
    for a in p.akts:
        ab_akt = defs.get(a["title"])
        loesung = ("loesung" in (ab_akt[1].get("markierungen") or []) if ab_akt
                   else bool(re.search(r"lösung|erwartungshorizont", a["title"] or "", re.I)))
        m = p.modul(a)
        verborgen = m is not None and m.findtext("visible") == "0"
        if (a["sectionid"] in lehr_ids or loesung) and not verborgen:
            grund = "Lösung" if loesung else "Lehrkraftmaterial"
            f.append(Befund(FEHLER, 2, f"{a['title']!r} ({grund}) ist für Lernende sichtbar"))
    return f


# --------------------------------------------------------------------------- #
# (3) Rechenfragen: jede Zufallsvariante rechnet
# --------------------------------------------------------------------------- #
FUNKTIONEN = {n: getattr(math, n) for n in (
    "acos", "acosh", "asin", "asinh", "atan", "atan2", "atanh", "ceil", "cos",
    "cosh", "exp", "expm1", "floor", "fmod", "log10", "log1p", "sin", "sinh",
    "sqrt", "tan", "tanh")}
def _runde(x: float, stellen: int = 0) -> float:
    """round wie in PHP/Moodle: halbe Stellen von der Null weg (Python rundet 0,5 zur geraden Zahl)."""
    q = decimal.Decimal(1).scaleb(-int(stellen))
    return float(decimal.Decimal(repr(float(x))).quantize(q, rounding=decimal.ROUND_HALF_UP))


FUNKTIONEN.update(abs=abs, max=max, min=min, pow=math.pow, power=math.pow, round=_runde,
                  sum=lambda *z: sum(z), average=lambda *z: sum(z) / len(z),
                  pi=lambda: math.pi, log=math.log, deg2rad=math.radians,
                  rad2deg=math.degrees)


def _wert(werte: dict, name: str) -> str:
    v = werte[name]
    return f"({0.0 if v is None else float(v)!r})"   # leere Note zählt als 0 (wie Moodle)


def rechne(formel: str, werte: dict) -> float:
    """Eine Moodle-Formel mit eingesetzten Werten sicher ausrechnen: Rechenfragen mit {name}, Bewertungsformeln mit
    führendem „=“ und [[idnummer]] bzw. ##gi<id>## (Schlüssel in `werte`: idnummer bzw. „gi<id>“, None = leer = 0).
    Anzeigeform mit „;“ als Trennzeichen (deutsche Oberfläche) geht auch, dann ohne Dezimalkomma."""
    text = formel.strip()
    if text.startswith("="):
        text = text[1:]
    text = text.replace(";", ",")
    text = re.sub(r"\{([A-Za-z_]\w*)\}", lambda m: _wert(werte, m.group(1)), text)
    text = re.sub(r"\[\[([^\[\]]+)\]\]", lambda m: _wert(werte, m.group(1)), text)
    text = re.sub(r"##(gi\d+)##", lambda m: _wert(werte, m.group(1)), text)
    if "^" in text:
        raise ValueError("„^“ ist in Moodle kein Potenzzeichen (pow(a, b) nehmen)")

    def w(k):
        if isinstance(k, ast.Expression):
            return w(k.body)
        if isinstance(k, ast.Constant) and isinstance(k.value, (int, float)):
            return k.value
        if isinstance(k, ast.UnaryOp) and isinstance(k.op, (ast.USub, ast.UAdd)):
            return -w(k.operand) if isinstance(k.op, ast.USub) else w(k.operand)
        if isinstance(k, ast.BinOp):
            l, r = w(k.left), w(k.right)
            ops = {ast.Add: lambda: l + r, ast.Sub: lambda: l - r, ast.Mult: lambda: l * r,
                   ast.Div: lambda: l / r, ast.Mod: lambda: math.fmod(l, r),
                   ast.Pow: lambda: l ** r}
            if type(k.op) in ops:
                return ops[type(k.op)]()
        if (isinstance(k, ast.Call) and isinstance(k.func, ast.Name)
                and k.func.id in FUNKTIONEN and not k.keywords):
            return FUNKTIONEN[k.func.id](*[w(a) for a in k.args])
        raise ValueError(f"unerlaubter Ausdruck in der Formel: {ast.dump(k)[:60]}")

    return float(w(ast.parse(text, mode="eval")))


def p3_rechnen(p: Paket, kursdef: dict | None) -> list[Befund]:
    f = []
    plausibel = {q["name"]: q["plausibel"] for _, a in kd.alle_aktivitaeten(kursdef or {})
                 for q in a.get("fragen", []) if q.get("plausibel")}
    fx = p.xml("questions.xml")
    for q in (fx.iter("question") if fx is not None else []):
        typ, name = q.findtext("qtype"), q.findtext("name")
        if typ == "numerical":
            for a in q.findall(".//answers/answer"):
                t = a.findtext("answertext")
                if t != "*" and not _endlich(t):
                    f.append(Befund(FEHLER, 3, f"{name}: Antwort {t!r} ist keine endliche Zahl"))
        if typ not in ("calculated", "calculatedsimple", "calculatedmulti"):
            continue
        werte: dict[int, dict] = {}
        for d in q.iter("dataset_definition"):
            for it in d.iter("dataset_item"):
                werte.setdefault(int(it.findtext("number")), {})[d.findtext("name")] = it.findtext("value")
        genannt = set(re.findall(r"\{([A-Za-z_]\w*)\}", q.findtext("questiontext") or ""))
        bekannt = set().union(*werte.values()) if werte else set()
        if genannt - bekannt:
            f.append(Befund(FEHLER, 3, f"{name}: Platzhalter ohne Werte: {sorted(genannt - bekannt)}"))
        if not werte:
            f.append(Befund(FEHLER, 3, f"{name}: keine Zufallswerte (Datensätze)"))
        formeln = [a.findtext("answertext") for a in q.findall(".//answers/answer")]
        for nr, satz in sorted(werte.items()):
            for formel in formeln:
                try:
                    erg = rechne(formel, satz)
                except (ValueError, KeyError, ZeroDivisionError, OverflowError,
                        SyntaxError, TypeError) as e:
                    f.append(Befund(FEHLER, 3, f"{name}, Variante {nr}: {formel!r} rechnet "
                                               f"nicht ({e.__class__.__name__}: {e})"))
                    continue
                if not math.isfinite(erg):
                    f.append(Befund(FEHLER, 3, f"{name}, Variante {nr}: Ergebnis {erg}"))
                elif name in plausibel and not plausibel[name][0] <= erg <= plausibel[name][1]:
                    f.append(Befund(FEHLER, 3, f"{name}, Variante {nr}: {erg:.4g} liegt außerhalb "
                                               f"{plausibel[name]}"))
                elif abs(erg) > 1e9:
                    f.append(Befund(HINWEIS, 3, f"{name}, Variante {nr}: {erg:.4g} unplausibel groß"))
    return f


def _endlich(t) -> bool:
    try:
        return math.isfinite(float(t))
    except (TypeError, ValueError):
        return False


# --------------------------------------------------------------------------- #
# (4) Keine leeren Hüllen
# --------------------------------------------------------------------------- #
def _leer(html: str | None) -> bool:
    if html and re.search(r"<(img|iframe|video|audio|object|svg)\b", html, re.I):
        return False
    return not re.sub(r"<[^>]+>|&nbsp;|\s", "", html or "")


def p4_huellen(p: Paket, kursdef: dict | None) -> list[Befund]:
    f = []
    dateien = p.xml("files.xml")
    mit_datei = {d.findtext("contextid") + d.findtext("component")
                 for d in (dateien if dateien is not None else []) if d.findtext("filename") != "."}
    for a in p.akts:
        h, typ, t = p.haupt(a), a["modulename"], a["title"]
        if h is None:
            continue
        ctx = p.xml(f"{a['directory']}/{typ}.xml").get("contextid")
        if typ == "page" and _leer(h.findtext("content")):
            f.append(Befund(FEHLER, 4, f"Seite {t!r} ohne Inhalt"))
        elif typ == "label" and _leer(h.findtext("intro")):
            f.append(Befund(FEHLER, 4, f"Textfeld {t!r} ohne Text"))
        elif typ == "quiz" and not list(h.iter("question_instance")):
            f.append(Befund(FEHLER, 4, f"Test {t!r} ohne Fragen"))
        elif typ in ("folder", "resource") and ctx + f"mod_{typ}" not in mit_datei:
            f.append(Befund(FEHLER, 4, f"{'Ordner' if typ == 'folder' else 'Datei'} {t!r} ohne Datei"))
        elif typ == "url" and not (h.findtext("externalurl") or "").strip():
            f.append(Befund(FEHLER, 4, f"Link {t!r} ohne Adresse"))
        elif typ == "feedback" and not list(h.iter("item")):
            f.append(Befund(FEHLER, 4, f"Feedback {t!r} ohne Fragen"))
        elif typ == "assign" and _leer(h.findtext("intro")):
            f.append(Befund(HINWEIS, 4, f"Aufgabe {t!r} ohne Aufgabenstellung"))
        elif typ == "data" and not list(h.iter("field")):
            f.append(Befund(FEHLER, 4, f"Datenbank {t!r} ohne Felder"))
        elif typ == "glossary" and not list(h.iter("entry")):
            f.append(Befund(HINWEIS, 4, f"Glossar {t!r} ohne Einträge"))
    lernfeld = _ist_lernfeldkurs(p, kursdef)
    for s in p.secs:
        sx = p.xml(f"{s['directory']}/section.xml")
        if sx is not None and sx.findtext("number") != "0" and not sx.findtext("sequence"):
            if lernfeld and not _leer(sx.findtext("summary")):
                continue            # Lernfeldkurs: die Kachel ist ein Wegweiser (Text und Link zum Themenkurs)
            f.append(Befund(HINWEIS, 4, f"Abschnitt {s['title']!r} ohne Aktivitäten"))
    return f


def _ist_lernfeldkurs(p: Paket, kursdef: dict | None) -> bool:
    """Lernfeldkurs: kurs.typ „lernfeld“ (ohne Kursdefinition: Kachel-Links über den Kurznamen, keine Note)."""
    if kursdef:
        return kd.ist_lernfeldkurs(kursdef)
    return bool(_lernfeld_links(p)) and not any(
        list(p.xml(f"{a['directory']}/grades.xml").iter("grade_item"))
        for a in p.akts if p.xml(f"{a['directory']}/grades.xml") is not None)


# --------------------------------------------------------------------------- #
# (5) Angekündigtes ist vorhanden
# --------------------------------------------------------------------------- #
ARTEN = ("infoblatt", "test", "selbsttest", "eingangstest", "abschlusstest",
         "generalprobe", "aufgabe", "auftrag", "abgabe", "ordner", "glossar",
         "selbsteinschätzung", "erklärvideo", "video", "simulation", "ihre medaille",
         "druckvorlagen", "handreichung", "arbeitsblatt", "tipp", "ansatz",
         "lösungsweg", "feedback", "rückblick")
ZITAT = re.compile(r"„([^“”\"<>]{2,120})[“”\"]")
#: Knöpfe und Bedienelemente von Moodle (deutsche Oberfläche), keine Aktivitäten (Sichtprüfung LS 5: „Aufgabe abgeben“)
MOODLE_KNOEPFE = {"aufgabe abgeben", "abgabe hinzufügen", "abgabe bearbeiten", "abgeben", "änderungen speichern",
                  "test beginnen", "versuch beenden", "alles abgeben und beenden", "prüfen", "erneut versuchen"}


def p5_angekuendigt(p: Paket, kursdef: dict | None) -> list[Befund]:
    f = []
    namen = {_name(a["title"]) for a in p.akts} | {_name(s["title"]) for s in p.secs}
    for ort, html in p.html_texte():
        for roh in ZITAT.findall(html):
            z = _name(roh)
            if z in namen or z in MOODLE_KNOEPFE:
                continue
            if any(z in n or n in z for n in namen if len(n) > 3):
                f.append(Befund(HINWEIS, 5, f"{ort}: „{roh}“ nennt einen Namen nur ungenau"))
                continue
            aehnlich = difflib.get_close_matches(z, namen, n=1, cutoff=0.75)
            if aehnlich or z.startswith(ARTEN):
                tipp = f" (gemeint: „{aehnlich[0]}“?)" if aehnlich else ""
                f.append(Befund(FEHLER, 5, f"{ort}: angekündigt „{roh}“, gibt es im Kurs "
                                           f"nicht{tipp}"))
    return f


# --------------------------------------------------------------------------- #
# (6) Medaillen-Bereiche lückenlos
# --------------------------------------------------------------------------- #
def p6_medaillen(p: Paket, kursdef: dict | None) -> list[Befund]:
    f = []
    defs = _akt_def(kursdef)
    noten_von: dict[str, dict] = {}
    for a in p.akts:
        g = p.xml(f"{a['directory']}/grades.xml")
        for gi in (g.iter("grade_item") if g is not None else []):
            noten_von[gi.get("id")] = a
    abz = p.xml("badges.xml")
    badges = [] if abz is None else [
        (b.findtext("name"), {par.findtext("name") for par in b.iter("parameter")})
        for b in abz.iter("badge")]
    kurs_ids = set(_kurs_items(p))
    gruppen: dict[str, list] = {}
    for a in p.akts:
        markiert = (a["title"] in defs and defs[a["title"]][1].get("medaille")) \
            or (not kursdef and "medaille" in (a["title"] or "").lower())
        if not markiert:
            continue
        # Alle Bewertungsbedingungen der UND-Liste; die auf Kursgesamt zuerst
        bed = sorted(((c, z) for c, z in _bedingungen(_verfuegbarkeit(p.modul(a)))
                      if c.get("type") == "grade"),
                     key=lambda cz: str(cz[0].get("id")) not in kurs_ids)
        if not bed:
            f.append(Befund(FEHLER, 6, f"{a['title']!r}: Medaille ohne Bewertungsbereich"))
            continue
        gruppen.setdefault(str(bed[0][0]["id"]), []).append((bed[0][0], bed[0][1], a))
    for gid, eintraege in gruppen.items():
        test = noten_von.get(gid)
        tname = "Kursgesamt" if gid in kurs_ids else (test["title"] if test else "?")
        if gid in kurs_ids:
            # Kursgesamt: Sterne wachsen; die Medaille öffnet sich erst nach dem Abschlusstest
            f += _nach_abschlusstest(p, [a for _, _, a in eintraege])
        elif test is None or test["modulename"] != "quiz":
            f.append(Befund(FEHLER, 6, f"Medaillen hängen an keiner Testbewertung ({tname})"))
        else:
            versuche = p.haupt(test).findtext("attempts_number")
            if versuche != "1":
                f.append(Befund(FEHLER, 6, f"{tname!r} hat {versuche} Versuche (0 = "
                                           f"unbegrenzt) – dann sind mehrere Medaillen erreichbar"))
        eintraege.sort(key=lambda e: float(e[0].get("min", 0)))
        if float(eintraege[0][0].get("min", 0)) != 1:
            f.append(Befund(FEHLER, 6, f"unterste Medaille beginnt bei "
                                       f"{eintraege[0][0].get('min', 0)} % statt 1 %"))
        for (b1, _, a1), (b2, _, a2) in zip(eintraege, eintraege[1:]):
            if b1.get("max") is None or float(b1["max"]) != float(b2.get("min", 0)):
                art = "Überschneidung" if b1.get("max") is None or float(b1["max"]) > float(
                    b2.get("min", 0)) else "Lücke"
                f.append(Befund(FEHLER, 6, f"{art} zwischen {a1['title']!r} (bis {b1.get('max')} %)"
                                           f" und {a2['title']!r} (ab {b2.get('min')} %)"))
        if eintraege[-1][0].get("max") is not None and float(eintraege[-1][0]["max"]) <= 100:
            f.append(Befund(FEHLER, 6, f"oberste Medaille endet bei {eintraege[-1][0]['max']} % "
                                       f"– 100 % bekäme keine"))
        if len(eintraege) != 4:
            f.append(Befund(HINWEIS, 6, f"{len(eintraege)} statt vier Medaillen an {tname!r}"))
        for bed, zeigen, a in eintraege:
            m = p.modul(a)
            if zeigen:
                f.append(Befund(HINWEIS, 6, f"{a['title']!r} ist gesperrt sichtbar – mehrere "
                                            f"Medaillen erscheinen gleichzeitig"))
            if not (m.findtext("completion") == "2" and m.findtext("completionview") == "1"):
                f.append(Befund(FEHLER, 6, f"{a['title']!r}: Abschluss „angesehen“ fehlt"))
            treffer = [n for n, pars in badges if f"module_{a['moduleid']}" in pars]
            if len(treffer) != 1:
                f.append(Befund(FEHLER, 6, f"{a['title']!r}: {len(treffer)} Abzeichen statt genau einem"))
    return f + _sternformeln(p, noten_von)


def _sternformeln(p: Paket, noten_von: dict) -> list[Befund]:
    """Berechnete Sterne (Testpaar): die Formel zeigt nur auf Testnoten im Paket, ist in der gespeicherten Form
    (Komma, kein „;“) und liefert 0 ohne Noten und genau den Höchstwert bei vollen Noten – sonst stimmen
    Kursgesamt und Medaillen nicht."""
    f = []
    for gi in _berechnete(p):
        name, calc = gi.findtext("itemname"), gi.findtext("calculation")
        ids = re.findall(r"##gi(\d+)##", calc)
        fremd = [i for i in ids if i not in noten_von or noten_von[i]["modulename"] != "quiz"]
        if fremd or not ids:
            f.append(Befund(FEHLER, 6, f"{name!r}: Formel zeigt auf keine oder unbekannte Testnote {fremd}"))
            continue
        if ";" in calc or "[[" in calc:
            f.append(Befund(FEHLER, 6, f"{name!r}: Formel nicht in der gespeicherten Form (##gi…##, Komma)"))
            continue
        hoechst = {}
        for i in ids:
            g = p.xml(f"{noten_von[i]['directory']}/grades.xml")
            hoechst[f"gi{i}"] = next(float(x.findtext("grademax")) for x in g.iter("grade_item") if x.get("id") == i)
        try:
            leer = rechne(calc, {k: None for k in hoechst})
            voll = rechne(calc, hoechst)
        except (ValueError, SyntaxError, ZeroDivisionError) as e:
            f.append(Befund(FEHLER, 6, f"{name!r}: Formel rechnet nicht ({e})"))
            continue
        grademax = float(gi.findtext("grademax") or 0)
        if leer != 0 or voll != grademax:
            f.append(Befund(FEHLER, 6, f"{name!r}: Formel gibt {leer:g} ohne Noten und {voll:g} bei vollen Noten, "
                                       f"Höchstwert ist {grademax:g}"))
            continue
        f += _sternpaar(p, noten_von, name, calc, hoechst, grademax)
    return f


def _sternpaar(p: Paket, noten_von: dict, name: str, calc: str, hoechst: dict, grademax: float) -> list[Befund]:
    """Testpaar (zweiter Versuch: ID-Nummer „test2-…“ oder Name „…, zweiter Versuch“): nur der erste Versuch voll
    gibt den Höchstwert, nur der erste genau auf seiner Bestehensgrenze 1 Stern, nur der zweite voll genau 1 Stern.
    So fallen vertauschte Versuche und falsche Höchstpunkte auf."""
    erste, zweite = [], []
    for k in hoechst:
        a = noten_von[k[2:]]
        m = p.modul(a)
        idn = (m.findtext("idnumber") if m is not None else "") or ""
        zweit = idn.startswith("test2-") or (a["title"] or "").endswith(", zweiter Versuch")
        (zweite if zweit else erste).append(k)
    if len(erste) != 1 or len(zweite) != 1:
        return []
    k1, k2 = erste[0], zweite[0]
    g = p.xml(f"{noten_von[k1[2:]]['directory']}/grades.xml")
    gradepass = next(float(x.findtext("gradepass") or 0) for x in g.iter("grade_item") if x.get("id") == k1[2:])
    faelle = [("nur der erste Versuch voll", {k1: hoechst[k1], k2: None}, grademax),
              ("nur der zweite Versuch voll", {k1: None, k2: hoechst[k2]}, 1)]
    if gradepass > 0:
        faelle.append((f"nur der erste Versuch genau bestanden ({gradepass:g})", {k1: gradepass, k2: None}, 1))
    f = []
    for text, noten, soll in faelle:
        ist = rechne(calc, noten)
        if ist != soll:
            f.append(Befund(FEHLER, 6, f"{name!r}: {text} gibt {ist:g} statt {soll:g} – Versuche vertauscht oder "
                                       f"falsche Höchstpunkte in der Formel?"))
    return f


def _nach_abschlusstest(p: Paket, medaillen: list[dict]) -> list[Befund]:
    """Medaillen auf Kursgesamt öffnen sich erst nach dem Abschlusstest (Lehrkraft 2026-10-22): UND-Bedingung
    „Abschlusstest bewertet“ (Bewertung ab 0 %) oder „abgeschlossen“. „Abgeschlossen“ trägt nur ohne
    Bestehensgrenze: sonst ist, wer nicht besteht, „abgeschlossen, nicht bestanden“ (gemessen, Moodle 5.1.6)."""
    f, quiz = [], {a["moduleid"]: a for a in p.akts if a["modulename"] == "quiz"}
    noten = {}
    for a in quiz.values():
        g = p.xml(f"{a['directory']}/grades.xml")
        for gi in (g.iter("grade_item") if g is not None else []):
            noten[gi.get("id")] = (a, float(gi.findtext("gradepass") or 0))
    gemeldet = set()
    for a in medaillen:
        bedingungen = [c for c, _ in _bedingungen(_verfuegbarkeit(p.modul(a)))]
        bewertet = [c for c in bedingungen if c.get("type") == "grade" and str(c.get("id")) in noten]
        fertig = [quiz[str(c.get("cm"))] for c in bedingungen
                  if c.get("type") == "completion" and c.get("e") == 1 and str(c.get("cm")) in quiz]
        for c in bewertet:
            test = noten[str(c.get("id"))][0]
            if float(c.get("min") or 0) > 0:
                f.append(Befund(FEHLER, 6, f"{a['title']!r} verlangt im {test['title']!r} mindestens {c['min']} % – "
                                           f"wer darunter bleibt, bekäme keine Medaille (Bedingung ab 0 % nehmen)"))
            if "abschlusstest" not in (test["title"] or "").lower():
                f.append(Befund(HINWEIS, 6, f"{a['title']!r} wartet auf {test['title']!r} – ist das der "
                                            f"Abschlusstest?"))
        if not bewertet and not fertig:
            f.append(Befund(FEHLER, 6, f"{a['title']!r} öffnet sich vor dem Abschlusstest – Bedingung "
                                       f"„Abschlusstest bewertet“ fehlt"))
        for test in fertig:
            m = p.modul(test)
            grenze = any(t is test and gp > 0 for t, gp in noten.values())
            durch_bestehen = m is not None and m.findtext("completionpassgrade") == "1"
            if (grenze or durch_bestehen) and test["moduleid"] not in gemeldet:
                gemeldet.add(test["moduleid"])
                f.append(Befund(FEHLER, 6, f"{a['title']!r} wartet auf „{test['title']} abgeschlossen“, der Test hat "
                                           f"aber eine Bestehensgrenze – wer nicht besteht, ist „nicht bestanden“ und "
                                           f"bekäme keine Medaille (Bedingung „bewertet ab 0 %“ nehmen)"))
    return f


# --------------------------------------------------------------------------- #
# (7) Alternativtexte (leeres alt nur bei ausdrücklich dekorativen Bildern: role="presentation")
# --------------------------------------------------------------------------- #
IMG = re.compile(r"<img\b[^>]*>", re.I)
ALT = re.compile(r"""\balt\s*=\s*(["'])(.*?)\1""", re.I | re.S)


UNTERSCHRIFT = re.compile(r"^\s*(?:Abb|Abbildung|Tab|Tabelle)\.?\s*\d")


def p7_alt(p: Paket, kursdef: dict | None) -> list[Befund]:
    """Jedes Bild mit alt-Text; als Schmuck (alt="" mit role="presentation") nur ohne Bildunterschrift: steht
    direkt danach „Abb. n …“, ist es ein Inhaltsbild ohne Beschreibung (Sichtprüfung LS 5)."""
    f = []
    for rel, w in p.alle_xml():
        for knoten in w.iter():
            text = knoten.text or ""
            for treffer in IMG.finditer(text):
                tag = treffer.group(0)
                m = ALT.search(tag)
                dekorativ = re.search(r"""role\s*=\s*["']presentation|aria-hidden\s*=\s*["']true""", tag, re.I)
                quelle = re.search(r"src\s*=\s*[\"']([^\"']+)", tag)
                wo = f"{rel} <{knoten.tag}>: Bild {quelle.group(1) if quelle else '?'}"
                if not m or (not m.group(2).strip() and not dekorativ):
                    f.append(Befund(FEHLER, 7, f"{wo} ohne alt-Text"))
                elif not m.group(2).strip():
                    danach = re.sub(r"<[^>]+>", " ", text[treffer.end():treffer.end() + 600].split("<img", 1)[0])
                    if UNTERSCHRIFT.match(danach):
                        f.append(Befund(FEHLER, 7, f"{wo} mit Bildunterschrift, aber als Schmuck ohne alt-Text"))
    return f


# --------------------------------------------------------------------------- #
# (8) Abgabe je Kachel (Lehrkraft 2026-10-22): jede inhaltliche Kachel hat eine
# Form von Abgabe – Test mit Sternen (oder der Eingangstest), Aufgabe oder
# Datenbank mit Abschluss über Einträge. Das Stern-Quiz „selbst gelöst“ zählt
# nicht (ID-Nummer „stern-…“, sterne.idnummern).
# --------------------------------------------------------------------------- #
def _zaehlt_im_kursgesamt(p: Paket, a: dict) -> bool:
    g = p.xml(f"{a['directory']}/grades.xml")
    for gi in (g.iter("grade_item") if g is not None else []):
        null = gi.findtext("weightoverride") == "1" and float(gi.findtext("aggregationcoef2") or 0) == 0
        text = gi.findtext("gradetype") == "3"       # Textbewertung (Aufgabe ohne Note) zählt nie
        if float(gi.findtext("grademax") or 0) > 0 and not null and not text:
            return True
    return False


def _ist_abgabe(p: Paket, a: dict) -> bool:
    m, typ = p.modul(a), a["modulename"]
    if m is None:
        return False
    if typ == "assign":
        return True
    if typ == "data":
        h = p.haupt(a)
        return m.findtext("completion") == "2" and h is not None and int(h.findtext("completionentries") or 0) > 0
    if typ == "quiz":
        if (m.findtext("idnumber") or "").startswith("stern-"):
            return False
        if "eingangstest" in (a["title"] or "").lower() or _zaehlt_im_kursgesamt(p, a):
            return True
        # Testpaar: Note mit Gewicht 0, die Sterne kommen aus einer berechneten Bewertung (sterne.sternformel)
        g = p.xml(f"{a['directory']}/grades.xml")
        return any(gi.get("id") in _in_formeln(p) for gi in (g.iter("grade_item") if g is not None else []))
    return False


def p8_abgabe(p: Paket, kursdef: dict | None) -> list[Befund]:
    f = []
    if _ist_lernfeldkurs(p, kursdef):
        return f              # Lernfeldkurs: Kacheln sind Wegweiser zu den Themenkursen, die Abgaben liegen dort
    lehr_def = {ab.get("name") for ab in (kursdef or {}).get("abschnitte", []) if ab.get("lehrkraft")}
    for s in p.secs:
        sx = p.xml(f"{s['directory']}/section.xml")
        if sx is None or sx.findtext("number") == "0":
            continue
        if s["title"] in lehr_def or (not kursdef and "lehrkr" in (s["title"] or "").lower()):
            continue
        if not any(_ist_abgabe(p, a) for a in p.akts if a["sectionid"] == s["sectionid"]):
            f.append(Befund(FEHLER, 8, f"Kachel {s['title']!r} ohne Abgabe (Test mit Sternen, Aufgabe oder "
                                       f"Datenbank mit Abschluss über Einträge)"))
    return f


# --------------------------------------------------------------------------- #
# (9) Sternzähler (Lehrkraft 2026-10-26, sternzaehler.py): genau eine Aktivität „⭐ Meine Sterne“ (Datenbank mit
# Skript, ID-Nummer „sternzaehler“) in Allgemein, ohne Abschluss und Voraussetzung, Lernende können nichts anlegen,
# Höchstwert im Skript = Höchstwert des Kursgesamts. Alte Textfelder je Sternstand („sternzaehler-<n>“) sind ein Fehler.
# --------------------------------------------------------------------------- #
ALTER_ZAEHLER = re.compile(r"^sternzaehler-\d+$")


def p9_sternzaehler(p: Paket, kursdef: dict | None) -> list[Befund]:
    import sternzaehler
    f = []
    ids = {a["moduleid"]: ((p.modul(a).findtext("idnumber") if p.modul(a) is not None else "") or "") for a in p.akts}
    alt = [a for a in p.akts if ALTER_ZAEHLER.match(ids[a["moduleid"]])]
    if alt:
        f.append(Befund(FEHLER, 9, f"{len(alt)} alte Sternzähler-Textfelder (je Sternstand eins) – es gibt nur noch "
                                   f"eine Aktivität „{sternzaehler.NAME}“"))
    zaehler = [a for a in p.akts if ids[a["moduleid"]] == sternzaehler.IDNUMMER]
    soll = bool((kursdef or {}).get("kurs", {}).get("sternzaehler")) and not _ist_lernfeldkurs(p, kursdef)
    if not zaehler:
        if soll:
            f.append(Befund(FEHLER, 9, "Sternzähler eingeschaltet, aber keine Aktivität „⭐ Meine Sterne“"))
        return f
    if len(zaehler) > 1:
        f.append(Befund(FEHLER, 9, f"{len(zaehler)} Sternzähler statt genau einem"))
    a = zaehler[0]
    m, h = p.modul(a), p.haupt(a)
    if a["modulename"] != "data" or h is None:
        return f + [Befund(FEHLER, 9, f"{a['title']!r} ist keine Datenbank-Aktivität")]
    if m.findtext("sectionnumber") != "0":
        f.append(Befund(FEHLER, 9, f"{a['title']!r} steht nicht in Allgemein"))
    if m.findtext("completion") != "0":
        f.append(Befund(FEHLER, 9, f"{a['title']!r} hat eine Abschlussbedingung"))
    if _verfuegbarkeit(m):
        f.append(Befund(FEHLER, 9, f"{a['title']!r} hat eine Voraussetzung"))
    rollen = p.xml(f"{a['directory']}/roles.xml")
    gesperrt = rollen is not None and any(o.findtext("capability") == "mod/data:writeentry"
                                          and o.findtext("permission") == "-1" for o in rollen.iter("override"))
    if not gesperrt:
        f.append(Befund(FEHLER, 9, f"{a['title']!r}: Lernende könnten Einträge anlegen (mod/data:writeentry)"))
    konfig = sternzaehler.konfig_aus(h.findtext("jstemplate") or "")
    gb = p.xml("gradebook.xml")
    hoechst = [float(gi.findtext("grademax") or 0) for gi in (gb.iter("grade_item") if gb is not None else [])
               if gi.findtext("itemtype") == "course"]
    if not konfig:
        f.append(Befund(FEHLER, 9, f"{a['title']!r}: Skript ohne Konfiguration"))
    elif hoechst and float(konfig.get("max", -1)) != hoechst[0]:
        f.append(Befund(FEHLER, 9, f"Sternzähler bis {konfig.get('max')}, Kursgesamt aber bis {hoechst[0]:g}"))
    if GEHEIM.search(h.findtext("jstemplate") or ""):
        f.append(Befund(FEHLER, 9, f"{a['title']!r}: Skript enthält etwas wie einen Schlüssel"))
    return f


# --------------------------------------------------------------------------- #
# (10) Sternebuch (Lehrkraft 2026-10-25, sternebuch.py): Buchungen nur mit Freigabe, freigegebene nur von der
# Lehrkraft änderbar, kein Schlüssel im Skript, Konfiguration passt zu Feldern und Preisliste, Rechenlogik
# (Halbierung, Kontostand, Klassenbelohnung) mit node gerechnet.
# --------------------------------------------------------------------------- #
#: Was im Skript nicht stehen darf: Zugangsschlüssel, Webdienst-Token, fest eingetragene Sitzungsschlüssel, Passwörter
GEHEIM = re.compile(r"wstoken|webservice/rest|\btoken\s*[:=]|passw(?:or)?t|password|api[_-]?key|"
                    r"sesskey\s*[:=]\s*['\"][A-Za-z0-9]{6,}|sesskey=[A-Za-z0-9]{6,}", re.I)
#: Was die Listenvorlage für das Skript enthalten muss
LISTE_NOETIG = ("sb-eintrag", "##approvalstatusclass##", "##user##", "##id##", "##approve##")
LERNFELD_LINK = re.compile(r"""href=["'][^"']*view\.php\?name=([^"'&]+)""", re.I)


def _lernfeld_links(p: Paket) -> dict[str, str]:
    """{Kurzname: Abschnitt} der Kachel-Links über den Kurznamen (lernfeldkurs.kurslink)."""
    import urllib.parse
    aus = {}
    for s in p.secs:
        sx = p.xml(f"{s['directory']}/section.xml")
        for k in LERNFELD_LINK.findall((sx.findtext("summary") if sx is not None else "") or ""):
            aus[urllib.parse.unquote(k)] = s["title"]
    return aus


def _sternebuecher(p: Paket) -> list[tuple[dict, ET.Element]]:
    aus = []
    for a in p.akts:
        if a["modulename"] != "data":
            continue
        h, m = p.haupt(a), p.modul(a)
        if h is None:
            continue
        konfig = sternebuch.konfig_aus(h.findtext("jstemplate") or "")
        idn = (m.findtext("idnumber") if m is not None else "") or ""
        if idn == sternebuch.IDNUMMER or (konfig is not None and "preisliste" in konfig and idn != "sternzaehler"):
            aus.append((a, h))
    return aus


#: Rechenprobe in node: (Ausdruck, erwartetes Ergebnis als JSON)
NODE_PROBEN = (
    ("L.halbieren(10)", 5), ("L.halbieren(7)", 3), ("L.halbieren(0)", 0),
    # 1 verdient 50, schenkt 2 zehn (5 kommen an), tauscht 5 ein, bucht 30 Anteil → Stand 5; offen 4 → verfügbar 1.
    # 2 bekommt 5 und einen Helfer-Stern → 6; verschenkt 8, noch offen → verfügbar −2
    ("(function(){var k=L.konten(["
     "{art:'verschenken',sterne:10,von:1,empfaenger:2,freigegeben:true},"
     "{art:'eintauschen',sterne:5,von:1,freigegeben:true},"
     "{art:'anteil',sterne:30,von:1,belohnung:'F',freigegeben:true},"
     "{art:'eintauschen',sterne:4,von:1,freigegeben:false},"
     "{art:'helfer',sterne:1,von:9,empfaenger:2,freigegeben:true},"
     "{art:'verschenken',sterne:8,von:2,empfaenger:1,freigegeben:false}],{1:50,2:0});"
     "return [k[1].stand,k[1].verfuegbar,k[2].erhalten,k[2].stand,k[2].verfuegbar];})()", [5, 1, 6, 6, -2]),
    # Klassenbelohnung: gilt erst, wenn alle drei gebucht haben
    ("(function(){var b=[{art:'anteil',belohnung:'F',sterne:30,von:1,freigegeben:true},"
     "{art:'anteil',belohnung:'F',sterne:30,von:2,freigegeben:true},"
     "{art:'anteil',belohnung:'F',sterne:30,von:3,freigegeben:false}];"
     "var a=L.klassenstand(b,'F',30,[1,2,3]);b[2].freigegeben=true;var c=L.klassenstand(b,'F',30,[1,2,3]);"
     "return [a.erreicht,a.inRunde,a.fehlt,c.erreicht,c.inRunde];})()", [0, 2, 1, 1, 0]),
    # Buchung über den Kontostand und ungerades Verschenken werden abgewiesen
    ("[L.pruefeBuchung({art:'eintauschen',belohnung:'K',sterne:10,von:1},9,"
     "{fuerMich:[{name:'K',sterne:10}],klasse:[]},{}).length>0,"
     "L.pruefeBuchung({art:'verschenken',sterne:7,von:1,empfaenger:2},20,{fuerMich:[],klasse:[]},{}).length>0,"
     "L.pruefeBuchung({art:'eintauschen',belohnung:'K',sterne:10,von:1},10,"
     "{fuerMich:[{name:'K',sterne:10}],klasse:[]},{}).length]", [True, True, 0]),
)


def _node_proben(js: str, tabellen_html: str | None) -> tuple[list[str], list[str]]:
    """(Fehler, Hinweise) der Rechenprobe in node; ohne node ein Hinweis."""
    node = shutil.which("node")
    if not node:
        return [], ["node nicht gefunden: Rechenlogik des Skripts nicht gerechnet"]
    with tempfile.TemporaryDirectory(prefix="sternebuch_") as d:
        datei = Path(d) / "sternebuch.js"
        datei.write_text(js, encoding="utf-8")
        proben = [f"try{{a.push(JSON.stringify({ausdruck}))}}catch(e){{a.push('FEHLER '+e.message)}}"
                  for ausdruck, _ in NODE_PROBEN]
        if tabellen_html is not None:
            tab = sternebuch._Tabellen()
            tab.feed(tabellen_html)
            tabellen = [[["".join(z) for z in zeile] for zeile in t] for t in tab.tabellen]
            proben.append(f"a.push(JSON.stringify(L.preiseLesen({json.dumps(tabellen)},"
                          f"{json.dumps(''.join(tab.text))})))")
        code = f"var L=require({json.dumps(str(datei))});var a=[];{';'.join(proben)};console.log(JSON.stringify(a));"
        try:
            r = subprocess.run([node, "-e", code], capture_output=True, text=True, timeout=30)
        except subprocess.TimeoutExpired:
            return ["Rechenprobe in node: Zeitüberschreitung"], []
    if r.returncode != 0:
        return [f"Skript lässt sich in node nicht laden: {r.stderr.strip()[:200]}"], []
    werte = json.loads(r.stdout.strip().splitlines()[-1])
    f = []
    for (ausdruck, soll), ist in zip(NODE_PROBEN, werte):
        if ist != json.dumps(soll, separators=(",", ":")):
            f.append(f"Rechenprobe {ausdruck[:60]}…: erwartet {soll}, Skript rechnet {ist}")
    if tabellen_html is not None:
        js_preise = json.loads(werte[-1])
        py = sternebuch.preise_lesen(tabellen_html)
        vergleich = ([(z["name"], z["sterne"]) for z in py["fuer_mich"]],
                     [(z["name"], z["ab"], z["anteil"]) for z in py["klasse"]], [z["kurzname"] for z in py["kurse"]])
        aus_js = ([(z["name"], z["sterne"]) for z in js_preise["fuerMich"]],
                  [(z["name"], z["ab"], z["anteil"]) for z in js_preise["klasse"]],
                  [z["kurzname"] for z in js_preise["kurse"]])
        if vergleich != aus_js:
            f.append(f"Preisliste: Skript liest {aus_js}, der Prüfer {vergleich}")
    return f, []


def p10_sternebuch(p: Paket, kursdef: dict | None) -> list[Befund]:
    f = []
    seiten = {a["title"]: a for a in p.akts if a["modulename"] == "page"}
    for a, h in _sternebuecher(p):
        t = a["title"]
        if h.findtext("approval") != "1":
            f.append(Befund(FEHLER, 10, f"{t!r}: Buchungen gelten ohne Freigabe der Lehrkraft (approval)"))
        if h.findtext("manageapproved") != "0":
            f.append(Befund(FEHLER, 10, f"{t!r}: Lernende können freigegebene Buchungen ändern (manageapproved)"))
        js = h.findtext("jstemplate") or ""
        for treffer in sorted({m.group(0) for m in GEHEIM.finditer(js)}):
            f.append(Befund(FEHLER, 10, f"{t!r}: Skript enthält „{treffer}“, kein Schlüssel und kein Token im "
                                        f"Quelltext"))
        konfig = sternebuch.konfig_aus(js)
        if konfig is None:
            f.append(Befund(FEHLER, 10, f"{t!r}: Skript ohne Konfiguration (/*KONFIG*/)"))
            continue
        felder = {fe.findtext("name"): fe for fe in h.iter("field")}
        for schluessel, name in konfig.get("felder", {}).items():
            if name not in felder:
                f.append(Befund(FEHLER, 10, f"{t!r}: Feld {name!r} ({schluessel}) fehlt in der Datenbank"))
        art = felder.get(konfig.get("felder", {}).get("art"))
        optionen = (art.findtext("param1") or "").split("\n") if art is not None else []
        if art is not None and sorted(optionen) != sorted(konfig.get("arten", {}).values()):
            f.append(Befund(FEHLER, 10, f"{t!r}: Auswahl im Feld Art {optionen} passt nicht zum Skript "
                                        f"{list(konfig.get('arten', {}).values())}"))
        liste = h.findtext("listtemplate") or ""
        for teil in LISTE_NOETIG:
            if teil not in liste:
                f.append(Befund(FEHLER, 10, f"{t!r}: Listenvorlage ohne {teil} (das Skript liest die Buchungen "
                                            f"daraus)"))
        seite = seiten.get(konfig.get("preisliste"))
        html = None
        if seite is None:
            f.append(Befund(FEHLER, 10, f"{t!r}: Seite {konfig.get('preisliste')!r} (Preisliste) fehlt im Kurs"))
        else:
            html = p.haupt(seite).findtext("content") or ""
            if not p.sichtbar(seite):
                f.append(Befund(FEHLER, 10, f"Preisliste {seite['title']!r} ist für Lernende verborgen"))
            preise = sternebuch.preise_lesen(html)
            f += [Befund(FEHLER, 10, f"Preisliste: {x}") for x in preise["fehler"]]
            if not preise["fuer_mich"]:
                f.append(Befund(FEHLER, 10, "Preisliste ohne Belohnungen (Tabelle mit Spalte „Sterne“)"))
            for k in preise["klasse"]:
                if k["anteil"] > k["ab"]:
                    f.append(Befund(FEHLER, 10, f"Klassenbelohnung {k['name']!r}: Anteil {k['anteil']:g} über der "
                                                f"Mindestzahl {k['ab']:g}"))
            kurse = [k["kurzname"] for k in preise["kurse"]] or [k["kurzname"] for k in konfig.get("themenkurse", [])]
            if not kurse:
                f.append(Befund(FEHLER, 10, "Keine Themenkurse, deren Sterne zählen (Tabelle „Kurzname“)"))
            for kurz, abschnitt in _lernfeld_links(p).items():
                if kurz not in kurse:
                    f.append(Befund(HINWEIS, 10, f"Kachel {abschnitt!r} verlinkt {kurz!r}, dessen Sterne im "
                                                 f"Sternebuch nicht zählen"))
            for kurz in kurse:
                if _lernfeld_links(p) and kurz not in _lernfeld_links(p):
                    f.append(Befund(HINWEIS, 10, f"{kurz!r} zählt im Sternebuch, hat aber keine Kachel"))
        fehler, hinweise = _node_proben(js, html)
        f += [Befund(FEHLER, 10, f"{t!r}: {x}") for x in fehler]
        f += [Befund(HINWEIS, 10, f"{t!r}: {x}") for x in hinweise]
    return f


# --------------------------------------------------------------------------- #
# (11) Kursseite nur mit dem Auftrag (Lehrkraft 2026-10-26): unter den Aktivitäten stehen keine Beschreibungen,
# Anweisungen oder Bilder (showdescription 0); was in der Beschreibung steht, muss in der Aktivität ankommen
# (Seiten: printintro 1). Textfelder zeigen ihren Text immer auf der Kursseite: Hinweis.
# --------------------------------------------------------------------------- #
def _klartext(html: str | None) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html or "")).strip()


def _lehr(p: Paket, a: dict, kursdef: dict | None) -> bool:
    """Steht die Aktivität im Lehrkraftbereich?"""
    lehr = {ab.get("name") for ab in (kursdef or {}).get("abschnitte", []) if ab.get("lehrkraft")}
    titel = next((s["title"] for s in p.secs if s["sectionid"] == a["sectionid"]), "")
    return titel in lehr or (not kursdef and "lehrkr" in (titel or "").lower())


def p11_kursseite(p: Paket, kursdef: dict | None) -> list[Befund]:
    import bauen as _bau
    f = []
    for a in p.akts:
        m, h = p.modul(a), p.haupt(a)
        if m is None or h is None:
            continue
        intro = h.findtext("intro") or ""
        if m.findtext("showdescription") == "1" and not ("⭐" in intro or "👥" in intro):
            f.append(Befund(FEHLER, 11, f"{a['title']!r} zeigt seine Beschreibung auf der Kursseite (showdescription 1)"))
        if a["modulename"] == "page" and _bau.hat_text(h.findtext("intro")):
            opt = h.findtext("displayoptions") or ""
            if not re.search(r's:10:"printintro";(?:i:1|s:1:"1")', opt):
                f.append(Befund(FEHLER, 11, f"Seite {a['title']!r}: Beschreibung wird nirgends angezeigt (printintro 0)"))
        # Link „neues Fenster“/„automatisch“ (öffnet die Adresse direkt) und Datei als Download zeigen ihre
        # Beschreibung nie: sichtbar für Lernende ein Fehler, im Lehrkraftbereich ein Hinweis
        art = h.findtext("display")
        verloren = ((a["modulename"] == "url" and art in ("0", "3", "5"))
                    or (a["modulename"] == "resource" and art in ("4", "5", "6")))
        sx = p.abschnitt(a["sectionid"])
        im_kacheltext = sx is not None and _klartext(h.findtext("intro")) in _klartext(sx.findtext("summary"))
        if verloren and _bau.hat_text(h.findtext("intro")) and not im_kacheltext:
            f.append(Befund(FEHLER if p.sichtbar(a) or (m.findtext("visibleold") == "1" and not _lehr(p, a, kursdef))
                            else HINWEIS, 11,
                            f"{a['title']!r}: öffnet direkt, die Beschreibung erscheint nirgends (Anzeige „eingebettet“ "
                            f"nehmen oder den Text in den Kacheltext bzw. die Handreichung)"))
        if a["modulename"] == "label" and not (m.findtext("idnumber") or "").startswith(("sternzaehler", "insel-")) \
                and not _ist_lernfeldkurs(p, kursdef) and m.findtext("visible") == "1":
            f.append(Befund(HINWEIS, 11, f"Textfeld {a['title']!r} steht mit seinem Text auf der Kursseite"))
    return f


# --------------------------------------------------------------------------- #
# (12) Infoseiten mit Word und PDF (Lehrkraft 2026-10-27, Profil `moodle.infoseiten_downloads` „word_pdf“,
# in der Kursdefinition kurs.infoseiten_downloads): jede Infoseite (rolle „info“) bietet Word und PDF zum
# Herunterladen; fehlt einer der beiden Knöpfe, ist das ein Fehler.
# --------------------------------------------------------------------------- #
_DOWNLOAD = re.compile(r'href="@@PLUGINFILE@@/[^"]+\.(docx|pdf)"', re.I)


def p12_infoseiten(p: Paket, kursdef: dict | None) -> list[Befund]:
    if ((kursdef or {}).get("kurs") or {}).get("infoseiten_downloads") != "word_pdf":
        return []
    defs = _akt_def(kursdef)
    f = []
    for a in p.akts:
        akt = defs.get(a["title"], (None, {}))[1]
        h = p.haupt(a)
        if a["modulename"] != "page" or akt.get("rolle") != "info" or h is None:
            continue
        arten = {m.lower() for m in _DOWNLOAD.findall(h.findtext("content") or "")}
        fehlt = [n for n, e in (("Word", "docx"), ("PDF", "pdf")) if e not in arten]
        if fehlt:
            f.append(Befund(FEHLER, 12, f"Infoseite {a['title']!r}: kein Download als {' und '.join(fehlt)} "
                                        f"(Profil: Word und PDF auf jeder Infoseite)"))
    return f


# --------------------------------------------------------------------------- #
# (13) Vorgriff (Lehrkraft 2026-10-27): nichts Zeigendes ist vor der Vorhersage erreichbar, an der es hängt
# (vorgriff.py, an der Kursdefinition). Mit kurs.freischaltgruppen (Kachelnummern, die gemeinsam freigeschaltet
# werden) auch spätere Kacheln derselben Gruppe als Hinweis.
# --------------------------------------------------------------------------- #
def p13_vorgriff(p: Paket, kursdef: dict | None) -> list[Befund]:
    if not kursdef:
        return []
    gruppen = (kursdef.get("kurs") or {}).get("freischaltgruppen")
    return [Befund(FEHLER if s == "Fehler" else HINWEIS, 13, t) for s, t in vorgriff.pruefe(kursdef, gruppen)]


# --------------------------------------------------------------------------- #
# (14) Inseln (individueller Lernpfad, inseln.py, Lehrkraft 2026-10-28): jede Insel vollständig (drei Stufen mit
# Übung und Kurztest), Kurztests mit einem Versuch und 3 bis 4 berechneten Fragen, Übungen und Kurztests ohne Sterne
# und nicht im Kursgesamt, kein Stern „selbst gelöst“ hängt an einer Insel. Die Voraussetzungen im Paket werden wie
# Moodle ausgewertet, für jeden möglichen Weg (Kurztest der Einstiegsstufe: keiner, an und um die Grenzen): genau
# eine Startstufe je Insel (die Endstufe der vorigen), Übungen nach unten offen und nach oben verdient, genau ein
# „Ihre Stufe“. „Mein Lernpfad“ (lernpfad.py): genau eine Aktivität in Allgemein, Namen im Skript wie im Kurs.
# --------------------------------------------------------------------------- #
#: Höchstzahl der ausgewerteten Wege (bei vielen Inseln nur noch die Vertreter der drei Ergebnisbereiche)
WEGE_HOECHST = 6000


def _inselteile(p: Paket) -> dict:
    """{(nr, Stufe|None, Rolle): Aktivität aus moodle_backup} nach den ID-Nummern insel-…"""
    aus = {}
    for a in p.akts:
        m = p.modul(a)
        i = inseln.insel_von({"idnummer": (m.findtext("idnumber") if m is not None else "") or ""})
        if i:
            aus[(i["nr"], i["stufe"], i["rolle"])] = a
    return aus


def _gradeitems(p: Paket, a: dict) -> list[str]:
    g = p.xml(f"{a['directory']}/grades.xml")
    return [gi.get("id") for gi in (g.iter("grade_item") if g is not None else [])]


def _qtypen(p: Paket) -> dict:
    """{question_bank_entry-Id: Fragetyp} aus questions.xml."""
    fx = p.xml("questions.xml")
    aus = {}
    for e in (fx.iter("question_bank_entry") if fx is not None else []):
        q = next(e.iter("question"), None)
        aus[e.get("id")] = q.findtext("qtype") if q is not None else None
    return aus


def _atome(baum: dict | None):
    if not baum:
        return
    for c in baum.get("c", []):
        if "c" in c:
            yield from _atome(c)
        else:
            yield c


def p14_inseln(p: Paket, kursdef: dict | None) -> list[Befund]:
    import lernpfad
    f = []
    teile = _inselteile(p)
    ids = {a["moduleid"]: ((p.modul(a).findtext("idnumber") if p.modul(a) is not None else "") or "") for a in p.akts}
    pfade = [a for a in p.akts if ids[a["moduleid"]] == lernpfad.IDNUMMER]
    nummern = sorted({k[0] for k in teile})
    if not nummern:
        if pfade:
            f.append(Befund(FEHLER, 14, f"„{lernpfad.NAME}“ ohne Übungsinseln"))
        return f
    stufen = inseln.STUFEN
    # vollständig, Kurztests und Übungen
    qtyp = _qtypen(p)
    vollstaendig = True
    for n in nummern:
        if (n, None, "kopf") not in teile:
            f.append(Befund(HINWEIS, 14, f"Insel {n}: kein Inselkopf (Textfeld insel-{n}-kopf)"))
        for s in stufen:
            for rolle in ("uebung", "kurztest"):
                a = teile.get((n, s, rolle))
                if a is None or a["modulename"] != "quiz":
                    f.append(Befund(FEHLER, 14, f"Insel {n} / {s}: {'Übung' if rolle == 'uebung' else 'Kurztest'} "
                                                f"fehlt (Test mit ID-Nummer insel-{n}-{inseln.KURZ[s]}-{rolle})"))
                    vollstaendig = False
                    continue
                h = p.haupt(a)
                versuche = int(h.findtext("attempts_number") or 0) if h is not None else -1
                slots = [r.findtext("questionbankentryid") for r in h.iter("question_reference")] if h is not None else []
                if rolle == "kurztest":
                    if versuche != 1:
                        f.append(Befund(FEHLER, 14, f"{a['title']!r}: Kurztest mit {versuche or 'beliebig vielen'} "
                                                    f"Versuchen (genau einer)"))
                    if not 3 <= len(slots) <= 4:
                        f.append(Befund(FEHLER, 14, f"{a['title']!r}: Kurztest mit {len(slots)} Fragen (3 bis 4)"))
                    andere = sorted({qtyp.get(q) for q in slots} - {"calculated", "calculatedsimple", "calculatedmulti"})
                    if andere:
                        f.append(Befund(HINWEIS, 14, f"{a['title']!r}: Kurztest mit Fragen vom Typ {', '.join(map(str, andere))} "
                                                     f"(vorgesehen: berechnete Fragen)"))
                elif versuche != 0:
                    f.append(Befund(HINWEIS, 14, f"{a['title']!r}: Übung mit {versuche} Versuchen (vorgesehen: beliebig viele)"))
                if _zaehlt_im_kursgesamt(p, a) or set(_gradeitems(p, a)) & _in_formeln(p):
                    f.append(Befund(FEHLER, 14, f"{a['title']!r}: zählt im Kursgesamt (Inseln geben keine Sterne)"))
                if h is not None and "⭐" in (h.findtext("intro") or ""):
                    f.append(Befund(FEHLER, 14, f"{a['title']!r}: Sternschild an einer Inselaktivität"))
            if (n, s, "empfehlung") not in teile:
                f.append(Befund(HINWEIS, 14, f"Insel {n} / {s}: kein Textfeld „Ihre Stufe“ (Hervorhebung fehlt)"))
    # Stern „selbst gelöst“ unabhängig von den Inseln
    insel_cms = {a["moduleid"] for a in teile.values()}
    insel_gi = {g for a in teile.values() for g in _gradeitems(p, a)}
    for a in p.akts:
        if not ids[a["moduleid"]].startswith("stern-"):
            continue
        for c in _atome(_verfuegbarkeit(p.modul(a))):
            if str(c.get("cm")) in insel_cms or (c.get("type") == "grade" and str(c.get("id")) in insel_gi):
                f.append(Befund(FEHLER, 14, f"{a['title']!r} hängt an einer Inselaktivität (der Stern „selbst "
                                            f"gelöst“ ist unabhängig von der Stufe)"))
                break
    # Mein Lernpfad
    konfig = None
    if not pfade:
        f.append(Befund(HINWEIS, 14, f"{len(nummern)} Übungsinseln, aber keine Aktivität „{lernpfad.NAME}“ "
                                     f"(Profil moodle.lernpfad_anzeige)"))
    else:
        if len(pfade) > 1:
            f.append(Befund(FEHLER, 14, f"{len(pfade)} Aktivitäten „{lernpfad.NAME}“ statt einer"))
        a = pfade[0]
        m, h = p.modul(a), p.haupt(a)
        if a["modulename"] != "data" or h is None:
            f.append(Befund(FEHLER, 14, f"{a['title']!r} ist keine Datenbank-Aktivität"))
        else:
            if m.findtext("sectionnumber") != "0":
                f.append(Befund(FEHLER, 14, f"{a['title']!r} steht nicht in Allgemein"))
            if m.findtext("completion") != "0" or _verfuegbarkeit(m):
                f.append(Befund(FEHLER, 14, f"{a['title']!r} hat eine Abschlussbedingung oder Voraussetzung"))
            rollen = p.xml(f"{a['directory']}/roles.xml")
            if not (rollen is not None and any(o.findtext("capability") == "mod/data:writeentry"
                                               and o.findtext("permission") == "-1" for o in rollen.iter("override"))):
                f.append(Befund(FEHLER, 14, f"{a['title']!r}: Lernende könnten Einträge anlegen (mod/data:writeentry)"))
            js = h.findtext("jstemplate") or ""
            if GEHEIM.search(js):
                f.append(Befund(FEHLER, 14, f"{a['title']!r}: Skript enthält etwas wie einen Schlüssel"))
            konfig = lernpfad.konfig_aus(js)
            if not konfig:
                f.append(Befund(FEHLER, 14, f"{a['title']!r}: Skript ohne Konfiguration"))
            else:
                titel = {(n, s, r): teile[(n, s, r)]["title"] for (n, s, r) in teile}
                in_konfig = [i.get("nr") for i in konfig.get("inseln", [])]
                if in_konfig != nummern:
                    f.append(Befund(FEHLER, 14, f"„{lernpfad.NAME}“ kennt die Inseln {in_konfig}, im Kurs sind es "
                                                f"{nummern}"))
                for i in konfig.get("inseln", []):
                    for rolle in ("uebung", "kurztest"):
                        for s, name in zip(stufen, i.get(rolle, [])):
                            soll = titel.get((i.get("nr"), s, rolle))
                            if soll is not None and _name(soll) != _name(name):
                                f.append(Befund(FEHLER, 14, f"„{lernpfad.NAME}“ sucht {name!r}, im Kurs heißt die "
                                                            f"Aktivität {soll!r}"))
    if not vollstaendig:
        return f
    # Startstufen und Stufen: Voraussetzungen wie Moodle auswerten
    grenzen = tuple((konfig or {}).get("grenzen") or inseln.grenzen_von(kursdef or {}))
    start = (konfig or {}).get("start") or next((i.get("start") for i in (kursdef or {}).get("inseln", [])
                                                 if i.get("start")), None)
    if not start:      # ohne Lernpfad und Kursdefinition: der einzige nicht verborgene Kurztest der ersten Insel
        sichtbar = [s for s in stufen if p.modul(teile[(nummern[0], s, "kurztest")]).findtext("visibleold") == "1"]
        start = sichtbar[0] if len(sichtbar) == 1 else inseln.START
    f += _wege(p, teile, nummern, start, grenzen)
    return f


def _wege(p: Paket, teile: dict, nummern: list, start: str, grenzen: tuple) -> list[Befund]:
    """Alle Wege durch die Inseln auswerten (siehe p14_inseln)."""
    stufen = inseln.STUFEN
    lo, hi = grenzen
    cm_von = {a["moduleid"]: k for k, a in teile.items()}
    gi_von = {g: k for k, a in teile.items() for g in _gradeitems(p, a)}
    baum = {k: _verfuegbarkeit(p.modul(a)) for k, a in teile.items()}
    sichtbar = {k: p.modul(a).findtext("visibleold") == "1" for k, a in teile.items()}
    befunde: list[str] = []
    n_wege = [0]
    grenz = [None, 0, lo - 0.01, lo, hi - 0.01, hi, 100]     # an jeder Insel geprüft
    vertreter = [None, lo - 0.01, lo, hi]                    # weiter verfolgt, wenn es sonst zu viele Wege wären
    tiefe_voll = 0                                           # so viele Inseln mit allen Ergebnissen verfolgen
    while tiefe_voll < len(nummern) and len(grenz) ** (tiefe_voll + 1) * len(vertreter) ** max(
            0, len(nummern) - tiefe_voll - 2) <= WEGE_HOECHST:
        tiefe_voll += 1

    def kompiliere(b):
        """Voraussetzungsbaum → Funktion(noten) (Moodle-Auswertung, einmal übersetzt für viele Wege): Bewertung „min“ = mindestens, „max“ = kleiner als; Bedingungen außerhalb der Inseln gelten als erfüllt."""
        if not b:
            return lambda noten: True
        teile = []
        for c in b.get("c", []):
            if "c" in c:
                teile.append(kompiliere(c))
            elif c.get("type") == "grade" and str(c.get("id")) in gi_von:
                k_, mn, mx = gi_von[str(c.get("id"))], c.get("min"), c.get("max")
                teile.append(lambda noten, k_=k_, mn=mn, mx=mx: (noten.get(k_) is not None and (
                    mn is None or noten[k_] >= mn) and (mx is None or noten[k_] < mx)))
            elif c.get("type") == "completion" and str(c.get("cm")) in cm_von and c.get("e") in (0, 1, 2):
                k_, soll = cm_von[str(c.get("cm"))], c.get("e") != 0
                teile.append(lambda noten, k_=k_, soll=soll: (noten.get(k_) is not None) == soll)
            else:
                teile.append(lambda noten: True)   # keine Inselaktivität (Tor der Insel, Kursgesamt): erfüllt
        op = b.get("op", "&")
        if op == "&":
            return lambda noten: all(f(noten) for f in teile)
        if op == "|":
            return lambda noten: any(f(noten) for f in teile)
        if op == "!&":
            return lambda noten: not all(f(noten) for f in teile)
        return lambda noten: not any(f(noten) for f in teile)
    pruef = {k: (kompiliere(baum[k]) if sichtbar[k] else (lambda noten: False)) for k in teile}

    def offen(k, noten):
        return pruef[k](noten)

    def melden(text, weg):
        if len(befunde) < 12 and text not in [b.split(" (Weg: ")[0] for b in befunde]:
            befunde.append(f"{text} (Weg: {weg or 'Start'})")

    def geh(i, e, noten, weg):
        n = nummern[i]
        ie = stufen.index(e)
        n_wege[0] += 1
        for s in stufen:                               # vor dem Üben
            soll = {"uebung": stufen.index(s) <= ie, "kurztest": False, "empfehlung": s == e}
            for rolle, w in soll.items():
                if offen((n, s, rolle), noten) != w:
                    melden(f"Insel {n}, Start {e}: {s} {_ROLLE[rolle]} ist {'gesperrt' if w else 'offen'}, "
                           f"soll {'offen' if w else 'gesperrt'} sein", weg)
        geuebt = {**noten, **{(n, s, "uebung"): 100.0 for s in stufen}}
        kt_offen = [s for s in stufen if offen((n, s, "kurztest"), geuebt)]
        if kt_offen != [e]:
            melden(f"Insel {n}, Start {e}: offene Kurztests {kt_offen or 'keiner'} statt genau {e}", weg)
        for o in grenz:
            danach = dict(geuebt) if o is None else {**geuebt, (n, e, "kurztest"): o}
            x_ = inseln.endstufe(e, o, grenzen)
            for s in stufen:
                si = stufen.index(s)
                w_ue = si <= ie or (o is not None and o >= hi and si == ie + 1)
                if offen((n, s, "uebung"), danach) != w_ue:
                    melden(f"Insel {n}, Start {e}, Kurztest {_pt(o)}: {s} Übung ist "
                           f"{'gesperrt' if w_ue else 'offen'}, soll {'offen' if w_ue else 'gesperrt'} sein", weg)
                if offen((n, s, "empfehlung"), danach) != (s == x_):
                    melden(f"Insel {n}, Start {e}, Kurztest {_pt(o)}: „Ihre Stufe: {s}“ ist "
                           f"{'sichtbar' if s != x_ else 'verborgen'} (Stufe ist {x_})", weg)
                if s != e and offen((n, s, "kurztest"), danach):
                    melden(f"Insel {n}, Start {e}, Kurztest {_pt(o)}: auch der Kurztest {s} ist offen "
                           f"(höchstens ein Wechsel je Insel)", weg)
            if i + 1 < len(nummern) and n_wege[0] < WEGE_HOECHST and (i < tiefe_voll or o in vertreter):
                geh(i + 1, x_, danach, f"{weg + ' → ' if weg else ''}Insel {n} Kurztest {e} {_pt(o)}")
    geh(0, start, {}, "")
    return [Befund(FEHLER, 14, b) for b in befunde]


_ROLLE = {"uebung": "Übung", "kurztest": "Kurztest", "empfehlung": "„Ihre Stufe“"}


def _pt(o) -> str:
    return "ohne Ergebnis" if o is None else f"{o:g} %"


PRUEFER = (p1_paket, p2_verborgen, p3_rechnen, p4_huellen, p5_angekuendigt,
           p6_medaillen, p7_alt, p8_abgabe, p9_sternzaehler, p10_sternebuch, p11_kursseite, p12_infoseiten,
           p13_vorgriff, p14_inseln)


def pruefe(paket: Path, kursdef: dict | None = None) -> list[Befund]:
    """Alle Prüfer über ein Paket (.mbz oder entpackter Ordner)."""
    paket = Path(paket)
    kursdef = inseln.eingesetzt(kursdef)          # Insel-Platzhalter wie beim Bau einsetzen (Kopie)
    ordner = entpacken(paket) if paket.is_file() else paket
    p = Paket(ordner)
    befunde = []
    for pruefer in PRUEFER:
        befunde += pruefer(p, kursdef)
    return befunde


def bericht(befunde: list[Befund]) -> str:
    if not befunde:
        return f"Alle {len(PRUEFER)} Prüfer ohne Befund."
    fehler = sum(b.stufe == FEHLER for b in befunde)
    return "\n".join([str(b) for b in befunde]
                     + [f"{fehler} Fehler, {len(befunde) - fehler} Hinweise"])


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Schützende Prüfer für eine .mbz")
    ap.add_argument("paket", type=Path)
    ap.add_argument("--kurs", type=Path, help="Kursdefinition (JSON)")
    arg = ap.parse_args()
    kurs = json.loads(arg.kurs.read_text(encoding="utf-8")) if arg.kurs else None
    ergebnis = pruefe(arg.paket, kurs)
    print(bericht(ergebnis))
    sys.exit(1 if any(b.stufe == FEHLER for b in ergebnis) else 0)
