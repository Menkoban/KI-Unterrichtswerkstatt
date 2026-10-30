"""Baut aus einer Kursdefinition eine Moodle-Kurssicherung (.mbz).

    baue(kursdef, dateien_wurzel, ziel_mbz)

Ziel ist der Moodle-Kern ab 5.0 ohne Plugins: Kopf und Modulversionen stehen
auf 5.0 (backup_version 2025041400); neuere Moodle-Versionen spielen ältere
Sicherungen ein. Die XML-Strukturen folgen einer echten 5.0-Sicherung und der
gegen Moodle 5.1.6 erprobten Vorlage aus Bersenbrück. Das Format der
Kursdefinition steht in `kursdefinition.py`.

    python3 bauen.py kurs.json --dateien <ordner> --ziel kurs.mbz
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import shutil
import sys
import tarfile
import tempfile
import time
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kursdefinition as kd  # noqa: E402
import fragen  # noqa: E402
import inseln  # noqa: E402
import lernpfad  # noqa: E402
import stufen  # noqa: E402
import sterne  # noqa: E402
import sternzaehler  # noqa: E402
from xmlhilfe import NULL, el, mime, php, x  # noqa: E402

ZIEL = {"moodle_version": "2025041404", "moodle_release": "5.0.4 (Build: 20251208)",
        "backup_version": "2025041400", "backup_release": "5.0",
        "modul_version": "2025041400"}
LEER_HASH = hashlib.sha1(b"").hexdigest()
#: Autor der Glossareinträge. Ein seltener Benutzername, damit der Restore
#: nicht mit einem vorhandenen Konto gleichen Namens kollidiert.
AUTOR = {"username": "p3_kursautor", "email": "p3_kursautor@example.org",
         "firstname": "Kurs", "lastname": "Autor"}
SCHULFARBE = "#08349C"
GRADE_TEXT = 3            # GRADE_TYPE_TEXT: Bewertungsaspekt ohne Note (nur Rückmeldetext), nicht im Kursgesamt

ANZEIGE_RESOURCE = {"automatisch": 0, "eingebettet": 1, "download": 4}
ANZEIGE_URL = {"automatisch": 0, "eingebettet": 1, "neues_fenster": 3}
#: Seite: RESOURCELIB_DISPLAY_OPEN bzw. _POPUP (lib/resourcelib.php); Größe des Pop-up-Fensters
SEITE_OFFEN, SEITE_POPUP = 5, 6
POPUP_GROESSE = {"popupwidth": 900, "popupheight": 700}
BEWERTUNGSMETHODE = {"hoechste": 1, "durchschnitt": 2, "erste": 3, "letzte": 4}
_WAEHREND, _DANACH = 65536, 4096 + 256
QUIZ_VERHALTEN = {"deferredfeedback": _DANACH,
                  "immediatefeedback": _DANACH | _WAEHREND,
                  "interactive": _DANACH | _WAEHREND}
LIKERT = ["trifft nicht zu", "trifft eher nicht zu", "trifft eher zu",
          "trifft zu"]


#: Schrift mindestens 16 px (Barrierefreiheit, Lehrkraft 2026-10-26): kleinere Angaben in Kurstexten, Bildquellen,
#: Hinweisen und Vorlagen (auch CSS des Sternebuchs) werden beim Bau auf 16 px bzw. 1em angehoben
_SCHRIFT = re.compile(r"(font-size\s*:\s*)(\d*\.?\d+)\s*(px|pt|em|rem|%)", re.I)
_SCHRIFT_WORT = re.compile(r"(font-size\s*:\s*)(xx-small|x-small|small|smaller)\b", re.I)
_MINDEST = {"px": 16.0, "pt": 12.0, "em": 1.0, "rem": 1.0, "%": 100.0}


def mindestschrift(text: str) -> str:
    """font-size unter 16 px (12 pt, 1em, 100 %) auf das Mindestmaß; <small> (auch als &lt;small&gt; im XML)
    wird zu <span>."""
    def heben(m):
        einheit = m.group(3).lower()
        return m.group(0) if float(m.group(2)) >= _MINDEST[einheit] else f"{m.group(1)}{_MINDEST[einheit]:g}{einheit}"
    text = _SCHRIFT.sub(heben, text)
    text = _SCHRIFT_WORT.sub(lambda m: m.group(1) + "1em", text)
    return re.sub(r"(<|&lt;)(/?)small\b", r"\1\2span", text)


class Ids:
    """Fortlaufende Ids je Art; Moodle vergibt beim Restore ohnehin neue."""
    START = {"section": 10, "cmid": 100, "instance": 5000, "ctx": 2000,
             "file": 9000, "qcat": 700, "qbe": 800, "qver": 850,
             "question": 900, "answer": 20000, "slot": 990, "gradeitem": 6100,
             "tag": 90000, "dataset": 70000, "datasetitem": 700000,
             "drag": 80000, "drop": 85000, "badge": 60000, "krit": 61000,
             "param": 62000, "group": 400, "grouping": 480, "user": 300, "usectx": 3000,
             "misc": 100000}

    def __init__(self):
        self._z = dict(self.START)

    def __call__(self, art: str) -> int:
        self._z[art] += 1
        return self._z[art]


@dataclass
class Akt:
    """Eine Aktivität mit vorab vergebenen Ids (für Bezüge nach vorn)."""
    akt: dict
    typ: str
    cmid: int
    instance: int
    ctx: int
    sec_id: int
    sec_nr: int
    sichtbar: int
    sichtbar_alt: int
    gradeitem: int | None = None
    filerefs: list = field(default_factory=list)
    userrefs: list = field(default_factory=list)
    qcatrefs: list = field(default_factory=list)
    rolerefs: list = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Der Bau
# --------------------------------------------------------------------------- #
class Bau:
    COURSE_ID, COURSE_CTX = 1, 1000

    def __init__(self, kursdef: dict, wurzel: Path):
        self.k = kursdef
        self.kurs = kursdef["kurs"]
        self.wurzel = Path(wurzel)
        self.ids = Ids()
        self.jetzt = int(time.time())
        self.inhalt: dict[str, bytes] = {}
        self.dateisaetze: list[dict] = []
        self._ordner: set = set()
        self.akts: dict[str, Akt] = {}
        self.abschnitte: list[tuple[int, dict]] = []
        self.abschnittsliste: list[tuple[int, str]] = []
        self.fragekategorien: list[str] = []
        self.kurs_filerefs: list[int] = []
        self.gruppen: list[int] = []
        # Gruppen und Gruppierungen vorab: Gruppenbedingungen und Aufgaben verweisen beim Bau darauf
        self.gruppen_ids = {name: self.ids("group") for name in kd.alle_gruppen(kursdef)}
        self.gruppierung_ids = {name: self.ids("grouping") for name in kursdef.get("gruppierungen") or {}}
        self.badge_ids: list[int] = []
        self.autor: dict | None = None
        self.grade_kat = self.ids("misc")
        self.grade_sort = 1
        self.grade_summe = 0.0
        self.rechte = False          # Rechte-Änderungen im Paket (Einstellung „permissions“ beim Einspielen)

    # -- Dateien --------------------------------------------------------- #
    def lies(self, rel: str) -> bytes:
        pfad = self.wurzel / rel
        if not pfad.is_file():
            raise FileNotFoundError(f"Datei {rel!r} fehlt unter {self.wurzel}")
        return pfad.read_bytes()

    def ablegen(self, ctx: int, comp: str, area: str, itemid: int,
                daten: bytes, name: str) -> list[int]:
        """Datei in den Dateispeicher; liefert die Ids für inforef.xml."""
        h = hashlib.sha1(daten).hexdigest()
        self.inhalt.setdefault(f"files/{h[:2]}/{h}", daten)
        neu = []
        schluessel = (ctx, comp, area, itemid)
        if schluessel not in self._ordner:
            self._ordner.add(schluessel)
            neu.append(self._satz(ctx, comp, area, itemid, LEER_HASH, ".", 0, 0))
        neu.append(self._satz(ctx, comp, area, itemid, h, name, len(daten), 1))
        return neu

    def _satz(self, ctx, comp, area, itemid, h, name, groesse, sort,
              pfad: str = "/") -> int:
        fid = self.ids("file")
        self.dateisaetze.append(dict(id=fid, hash=h, ctx=ctx, comp=comp,
                                     area=area, itemid=itemid, name=name,
                                     groesse=groesse, sort=sort, pfad=pfad))
        return fid

    def bilder(self, html: str, dateien: list, r: Akt, comp: str, area: str,
               itemid: int = 0) -> str:
        """Dateien ablegen und `src="name"` auf @@PLUGINFILE@@ umstellen."""
        html, ids = self.einbetten(html, dateien, r.ctx, comp, area, itemid)
        r.filerefs += ids
        return html

    def einbetten(self, html: str, dateien: list, ctx: int, comp: str, area: str,
                  itemid: int) -> tuple[str, list[int]]:
        """Wie `bilder`, für beliebigen Kontext; liefert HTML und Datei-Ids."""
        ids: list[int] = []
        for rel in dateien or []:
            name = Path(rel).name
            ids += self.ablegen(ctx, comp, area, itemid, self.lies(rel), name)
            ziel = "@@PLUGINFILE@@/" + urllib.parse.quote(name)
            html = re.sub(r'src=(["\'])' + re.escape(name) + r'\1',
                          f'src="{ziel}"', html)
        return html, ids

    def kachelfoto(self, sec_id: int, rel: str) -> tuple[str, list[int]]:
        """Kachelfoto (format_tiles) eines Abschnitts: XML für section.xml und
        Datei-Ids. Aufbau wie eine echte Sicherung mit format_tiles 5.1: Datei
        unter /tilephoto/ und je ein Verzeichniseintrag „.“ für /tilephoto/ und /."""
        name = Path(rel).name
        daten = self.lies(rel)
        h = hashlib.sha1(daten).hexdigest()
        self.inhalt.setdefault(f"files/{h[:2]}/{h}", daten)
        ort = (self.COURSE_CTX, "format_tiles", "tilephoto", sec_id)
        ids = [self._satz(*ort, h, name, len(daten), 0, "/tilephoto/"),
               self._satz(*ort, LEER_HASH, ".", 0, 0, "/tilephoto/"),
               self._satz(*ort, LEER_HASH, ".", 0, 0, "/")]
        xml = (f'  <plugin_format_tiles_section sectionid="{sec_id}">\n'
               "    <optiontype>1</optiontype>\n"
               f"    {el('optionvalue', name)}\n"
               "    <tilesversion>2026012570</tilesversion>\n"
               "  </plugin_format_tiles_section>\n"
               f'  <course_format_options id="{self.ids("misc")}">\n'
               "    <format>tiles</format>\n    <name>tilephoto</name>\n"
               f"    {el('value', name)}\n  </course_format_options>\n")
        return xml, ids

    def xml(self, pfad: str, koerper: str) -> None:
        self.inhalt[pfad] = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                             + mindestschrift(koerper)).encode("utf-8")

    # -- Ablauf ---------------------------------------------------------- #
    def baue(self) -> bytes:
        self._vorbelegen()
        for r in self.allgemein_rs:       # Sternzähler: erste Aktivitäten in Allgemein
            self._aktivitaet(r)
        self._abschnitt(self._sec0, 0, {"name": None, "zusammenfassung": self.kurs.get("allgemein", ""),
                                         "dateien": self.kurs.get("allgemein_dateien")}, self.allgemein_rs)
        for nr, (sec_id, ab) in enumerate(self.abschnitte, start=1):
            rs = [self.akts[kd.kennung_von(a)] for a in ab.get("aktivitaeten", [])]
            for r in rs:
                self._aktivitaet(r)
            self._abschnitt(sec_id, nr, ab, rs)
        self._kurs()
        self._oben()
        self._moodle_backup()
        return self._packen()

    def _vorbelegen(self) -> None:
        self._sec0 = self.ids("section")
        for nr, ab in enumerate(self.k["abschnitte"], start=1):
            sec_id = self.ids("section")
            self.abschnitte.append((sec_id, ab))
            sec_sicht = 1 if ab.get("sichtbar", not ab.get("lehrkraft")) else 0
            for a in ab.get("aktivitaeten", []):
                eigen = 1 if a.get("sichtbar", True) else 0
                r = Akt(a, a["typ"], self.ids("cmid"), self.ids("instance"),
                        self.ids("ctx"), sec_id, nr,
                        sichtbar=eigen if sec_sicht else 0, sichtbar_alt=eigen)
                if kd.bewertet(a) or a["typ"] == "assign":     # Aufgabe ohne Note: Textbewertung (_grade_item_akt)
                    r.gradeitem = self.ids("gradeitem")
                self.akts[kd.kennung_von(a)] = r
        # Sternzähler (Kursschalter `sternzaehler`, Lehrkraft 2026-10-26): genau eine Aktivität „⭐ Meine Sterne“
        # (Datenbank mit Skript, sternzaehler.py) als erste Aktivität in Allgemein, unter dem Begrüßungskasten.
        self.allgemein_rs: list[Akt] = []
        self.sternzaehler_n = sterne.kursgesamt_max(self.k) if self.kurs.get("sternzaehler") else None
        if self.sternzaehler_n:
            a = sternzaehler.aktivitaet(self.sternzaehler_n, self.kurs.get("vollname", ""),
                                        tuple(self.kurs.get("schulfarben") or sternzaehler.FARBEN))
            if kd.kennung_von(a) in self.akts:
                raise ValueError(f"Kennung {kd.kennung_von(a)!r} ist für den Sternzähler reserviert")
            kd.pruefe_oder_abbrechen({"kurs": {"vollname": "x", "kurzname": "x", "beschreibung": "x",
                                               "ki_hinweis": "mit Hilfe von künstlicher Intelligenz"},
                                      "abschnitte": [{"name": "x", "aktivitaeten": [a]}]})
            r = Akt(a, "data", self.ids("cmid"), self.ids("instance"), self.ids("ctx"), self._sec0, 0,
                    sichtbar=1, sichtbar_alt=1)
            self.akts[kd.kennung_von(a)] = r
            self.allgemein_rs.append(r)
        # „Mein Lernpfad“ (Kursschalter `lernpfad`, Profil moodle.lernpfad_anzeige, Lehrkraft 2026-10-28): eine
        # Datenbank mit Skript unter dem Sternzähler, nur in Kursen mit Übungsinseln; Namen erst jetzt endgültig
        if self.kurs.get("lernpfad") and self.k.get("inseln"):
            a = lernpfad.aktivitaet(lernpfad.konfig(self.k, {k: r.akt["name"] for k, r in self.akts.items()}),
                                    self.kurs.get("vollname", ""),
                                    tuple(self.kurs.get("schulfarben") or lernpfad.FARBEN))
            if kd.kennung_von(a) in self.akts:
                raise ValueError(f"Kennung {kd.kennung_von(a)!r} ist für „Mein Lernpfad“ reserviert")
            r = Akt(a, "data", self.ids("cmid"), self.ids("instance"), self.ids("ctx"), self._sec0, 0,
                    sichtbar=1, sichtbar_alt=1)
            self.akts[kd.kennung_von(a)] = r
            self.allgemein_rs.append(r)
        # Aktivitäten oben in Allgemein (`allgemein_aktivitaeten`, z. B. das Sternebuch), unter dem Sternzähler
        for a in self.k.get("allgemein_aktivitaeten") or []:
            eigen = 1 if a.get("sichtbar", True) else 0
            r = Akt(a, a["typ"], self.ids("cmid"), self.ids("instance"), self.ids("ctx"), self._sec0, 0,
                    sichtbar=eigen, sichtbar_alt=eigen)
            self.akts[kd.kennung_von(a)] = r
            self.allgemein_rs.append(r)
        # berechnete Bewertungen (Sterne je Testpaar): eigene Gradeitems im Kurs
        self.berechnet = [(self.ids("gradeitem"), b) for b in self.k.get("bewertungen", [])]
        # Kurs-Gradeitem nach den Aktivitäten, aber vor dem Bau: Voraussetzungen
        # auf die Kursgesamtbewertung zeigen auf diese Id (Restore schlüsselt um).
        self.kurs_gradeitem = self.ids("gradeitem")

    # -- Abschnitt ------------------------------------------------------- #
    def _abschnitt(self, sec_id: int, nr: int, ab: dict, rs: list[Akt]) -> None:
        sicht = 1 if ab.get("sichtbar", not ab.get("lehrkraft")) else 0
        # Dateien der Zusammenfassung: Kurskontext, filearea section, itemid =
        # Abschnitts-Id. Das Kachelfoto gibt es nur im Kachelformat.
        text, ids = self.einbetten(ab.get("zusammenfassung", ""), ab.get("dateien"),
                                   self.COURSE_CTX, "course", "section", sec_id)
        kachel = ""
        if ab.get("bild") and self.kurs.get("format", "tiles") == "tiles":
            kachel, foto = self.kachelfoto(sec_id, ab["bild"])
            ids += foto
        self.xml(f"sections/section_{sec_id}/section.xml", (
            f'<section id="{sec_id}">\n'
            f"  {el('number', nr)}\n  {el('name', ab.get('name'))}\n"
            f"  {el('summary', text)}\n"
            f"  <summaryformat>1</summaryformat>\n"
            f"  {el('sequence', ','.join(str(r.cmid) for r in rs))}\n"
            f"  {el('visible', sicht)}\n"
            f"  <availabilityjson>{NULL}</availabilityjson>\n"
            f"  <component>{NULL}</component>\n  <itemid>{NULL}</itemid>\n"
            f"  {el('timemodified', self.jetzt)}\n{kachel}</section>"))
        refs = "".join(f"    <file>\n      <id>{i}</id>\n    </file>\n" for i in ids)
        self.xml(f"sections/section_{sec_id}/inforef.xml",
                 f"<inforef>\n  <fileref>\n{refs}  </fileref>\n</inforef>" if ids
                 else "<inforef>\n</inforef>")
        titel = ab.get("name") or str(nr)
        self.abschnittsliste.append((sec_id, titel))

    # -- Aktivität ------------------------------------------------------- #
    def _aktivitaet(self, r: Akt) -> None:
        if r.typ in kd.NICHT_UNTERSTUETZT:
            raise NotImplementedError(
                f"{r.akt['name']!r}: Aktivitätstyp {r.typ!r} wird noch nicht "
                f"gebaut. Bitte vorerst eine Abgabe (assign) verwenden.")
        ordner = f"activities/{r.typ}_{r.cmid}"
        schild = self._schild(r)
        # Schilder vorn in der Beschreibung (Kopie: die Kursdefinition bleibt, wie sie ist). Die Beschreibung steht nur
        # in der Aktivität, nicht auf der Kursseite (showdescription 0, Lehrkraft 2026-10-26: auf der Kursseite steht
        # nur der Auftrag im Kacheltext), außer bei Tests mit Sternschild (unten).
        if schild:
            r.akt = dict(r.akt, beschreibung=schild + (r.akt.get("beschreibung") or ""))
        if (r.akt.get("insel") or {}).get("rolle") in ("kopf", "empfehlung"):
            # Textfelder der Übungsinseln: Name und Schulfarbe stehen erst jetzt fest (Schrittnummern, Profil)
            r.akt = dict(r.akt, text=inseln.label_text(r.akt, tuple(self.kurs.get("schulfarben") or ())))
        # Ausnahme (Lehrkraft 2026-10-27): Aktivitäten mit Schild (Sterne und Versuche an Tests, Sozialform) zeigen
        # ihre Beschreibung auf der Kursseite, damit das Schild unter dem Link steht
        r.zeige_beschreibung = bool(schild) or bool(r.akt.get("beschreibung_auf_kursseite"))
        innen = BAUER[r.typ](self, r)
        self.xml(f"{ordner}/{r.typ}.xml",
                 f'<activity id="{r.instance}" moduleid="{r.cmid}" '
                 f'modulename="{r.typ}" contextid="{r.ctx}">\n{innen}\n</activity>')
        self.xml(f"{ordner}/module.xml", self._modul(r))
        rechte = self._rechte(r)          # vor inforef: die Rolle muss dort genannt sein
        self.xml(f"{ordner}/inforef.xml", self._inforef(r))
        self.xml(f"{ordner}/roles.xml", "<roles>\n  <role_overrides>\n" + rechte
                 + "  </role_overrides>\n  <role_assignments>\n  </role_assignments>\n</roles>")
        self.xml(f"{ordner}/grades.xml", "<activity_gradebook>\n  <grade_items>"
                 + self._grade_item_akt(r) + "</grade_items>\n"
                 "  <grade_letters>\n  </grade_letters>\n</activity_gradebook>")
        self.xml(f"{ordner}/grade_history.xml",
                 "<grade_history>\n  <grade_grades>\n  </grade_grades>\n</grade_history>")
        self.xml(f"{ordner}/calendar.xml", "<events>\n</events>")
        filter_aus = ("    <filter_active>\n      <filter>glossary</filter>\n"
                      "      <active>-1</active>\n    </filter_active>\n"
                      if r.akt.get("glossar_aus") else "")
        self.xml(f"{ordner}/filters.xml", "<filters>\n  <filter_actives>\n"
                 f"{filter_aus}  </filter_actives>\n  <filter_configs>\n"
                 "  </filter_configs>\n</filters>")
        if r.typ == "assign":
            self.xml(f"{ordner}/grading.xml", self._bewertungsbereich(r))

    def _bewertungsbereich(self, r: Akt) -> str:
        """grading.xml einer Aufgabe: leer, mit Stufen im Raster (kd.raster_mit_stufen) eine Rubrik
        (gradingform_rubric) im Bereich „submissions“, Aufbau wie backup_activity_grading_structure_step und
        backup_gradingform_rubric_plugin (Moodle 5.1). raster_vorschau false: alwaysshowdefinition 0."""
        a = r.akt
        if not (kd.bewertet(a) and kd.raster_mit_stufen(a)):
            return "<areas>\n</areas>"
        optionen = {"sortlevelsasc": 1, "lockzeropoints": 1,
                    "alwaysshowdefinition": 1 if a.get("raster_vorschau", True) else 0,
                    "showdescriptionteacher": 1, "showdescriptionstudent": 1, "showscoreteacher": 1,
                    "showscorestudent": 1, "enableremarks": 1, "showremarksstudent": 1}
        kriterien = []
        for sort, k in enumerate(a["bewertungsraster"], start=1):
            stufen = "".join(
                f'                  <level id="{self.ids("misc")}">\n'
                f"                    {el('score', f'{float(st['punkte']):.5f}')}\n"
                f"                    {el('definition', _stufentext(st))}\n"
                "                    <definitionformat>0</definitionformat>\n                  </level>\n"
                for st in sorted(k["stufen"], key=lambda st: st["punkte"]))
            kriterien.append(
                f'              <criterion id="{self.ids("misc")}">\n                {el("sortorder", sort)}\n'
                f"                {el('description', k['kriterium'])}\n"
                "                <descriptionformat>0</descriptionformat>\n"
                f"                <levels>\n{stufen}                </levels>\n              </criterion>\n")
        return (f'<areas>\n  <area id="{self.ids("misc")}">\n    <areaname>submissions</areaname>\n'
                "    <activemethod>rubric</activemethod>\n    <definitions>\n"
                f'      <definition id="{self.ids("misc")}">\n        <method>rubric</method>\n'
                f"        {el('name', a.get('raster_name') or 'Bewertungsraster ' + a['name'])}\n"
                "        <description></description>\n        <descriptionformat>1</descriptionformat>\n"
                "        <status>20</status>\n"
                f"        {el('timecreated', self.jetzt)}\n        {el('timemodified', self.jetzt)}\n"
                f"        {el('options', json.dumps(optionen, separators=(',', ':')))}\n"
                "        <plugin_gradingform_rubric_definition>\n          <criteria>\n"
                + "".join(kriterien) + "          </criteria>\n        </plugin_gradingform_rubric_definition>\n"
                "        <instances>\n        </instances>\n      </definition>\n    </definitions>\n"
                "  </area>\n</areas>")

    def _schild(self, r: Akt) -> str:
        """Stern- und Sozialform-Schild der Aktivität (sterne.schild_html), nur mit dem Kursschalter `schilder`;
        Textfelder haben keine Beschreibung unter dem Link."""
        if not self.kurs.get("schilder") or r.typ == "label":
            return ""
        return sterne.schild_html(r.akt, self.kurs.get("bestehen_prozent") or 0,
                                  self.kurs.get("sterne_schluessel"))

    def _rechte(self, r: Akt) -> str:
        """Rechte-Änderungen der Aktivität für die Rolle Student (id 5 wie in roles.xml): Glossar „nur_lesen“ –
        Lernende dürfen keine Einträge anlegen (Moodle hat dafür keine Glossar-Einstellung)."""
        recht = {"glossary": "mod/glossary:write", "data": "mod/data:writeentry"}.get(r.typ)
        if not (recht and r.akt.get("nur_lesen")):
            return ""
        self.rechte = True
        r.rolerefs.append(5)      # ohne Verweis im inforef ordnet Moodle die Rolle nicht zu und verwirft die Änderung
        return (f'    <override id="{self.ids("misc")}">\n      <roleid>5</roleid>\n'
                f"      <capability>{recht}</capability>\n      <permission>-1</permission>\n"
                f"      {el('timemodified', self.jetzt)}\n      <modifierid>0</modifierid>\n    </override>\n")

    def _abschluss(self, r: Akt) -> dict:
        """Felder für module.xml und das Modul selbst."""
        art = kd.abschluss_von(r.akt)
        d = {"completion": 0, "view": 0, "pass": 0, "gradenr": None, "modul": {}}
        if art == "manuell":
            d["completion"] = 1
        elif art != "keine":
            d["completion"] = 2
            if art == "ansehen":
                d["view"] = 1
            elif art == "abgeben":
                d["modul"]["completionsubmit"] = 1
            elif art == "eintraege":
                d["modul"]["completionentries"] = int(
                    r.akt.get("eintraege_fuer_abschluss", 1))
            elif art == "note":
                d["gradenr"] = 0
            elif art.startswith("bestanden"):
                d.update(gradenr=0, **{"pass": 1})
                if art == "bestanden_oder_versuche":
                    d["modul"]["completionattemptsexhausted"] = 1
        return d

    def _verfuegbarkeit(self, r: Akt) -> str | None:
        bedingungen = kd.voraussetzungen(r.akt)
        if not bedingungen:
            return None
        teile = [self._bedingung(v) for v in bedingungen]
        return json.dumps({"op": "&", "c": [b for b, _ in teile],
                           "showc": [z for _, z in teile]},
                          separators=(",", ":"))

    def _bedingung(self, v: dict) -> tuple[dict, bool]:
        """Eine Bedingung als availability-Eintrag und ob sie gesperrt sichtbar ist. ODER-Gruppe (`oder`): Unterbaum
        {"op":"|","c":[…]} ohne eigenes showc (Moodle: nur die Wurzel trägt es), Vorgabe gesperrt sichtbar;
        Verneinung (`nicht`): {"op":"!&","c":[…]}, Vorgabe verborgen."""
        if "oder" in v:
            return ({"op": "|", "c": [self._bedingung(b)[0] for b in v["oder"]]},
                    bool(v.get("sichtbar_wenn_gesperrt", True)))
        if "und" in v:            # UND-Gruppe (Zweig einer ODER-Gruppe, Übungsinseln): Unterbaum ohne showc
            return ({"op": "&", "c": [self._bedingung(b)[0] for b in v["und"]]},
                    bool(v.get("sichtbar_wenn_gesperrt", False)))
        if "nicht" in v:          # Verneinung (Sternzähler n = 0): „nicht alle“, gilt auch ohne Note
            return ({"op": "!&", "c": [self._bedingung(b)[0] for b in v["nicht"]]},
                    bool(v.get("sichtbar_wenn_gesperrt", False)))
        if "gruppe" in v:         # Mitglied der Gruppe (availability_group); Vorgabe ganz verborgen
            return ({"type": "group", "id": self.gruppen_ids[v["gruppe"]]},
                    bool(v.get("sichtbar_wenn_gesperrt", False)))
        if v.get("bewertung") not in (None, "kursgesamt"):   # berechnete Bewertung (idnummer oder name)
            gid = next(g for g, b in self.berechnet if v["bewertung"] in (b.get("idnummer"), b["name"]))
            bed = {"type": "grade", "id": gid}
            for k in ("min", "max"):
                if v.get(k) is not None:
                    bed[k] = v[k]
            return bed, bool(v.get("sichtbar_wenn_gesperrt", False))
        if v.get("bewertet"):     # „hat eine Bewertung“: Bewertungsbedingung ohne min und max
            return ({"type": "grade", "id": self.akts[kd.ziel_von(v)].gradeitem},
                    bool(v.get("sichtbar_wenn_gesperrt", False)))
        if v.get("bewertung") == "kursgesamt" or "min" in v or "max" in v:
            gid = (self.kurs_gradeitem if v.get("bewertung") == "kursgesamt"
                   else self.akts[kd.ziel_von(v)].gradeitem)
            bed = {"type": "grade", "id": gid}
            if v.get("min") is not None:
                bed["min"] = v["min"]
            if v.get("max") is not None:
                bed["max"] = v["max"]
            return bed, bool(v.get("sichtbar_wenn_gesperrt", False))
        ziel = self.akts[kd.ziel_von(v)]
        bed = {"type": "completion", "cm": ziel.cmid,
               "e": kd.ZUSTAND[kd.zustand_von(v)]}
        return bed, bool(v.get("sichtbar_wenn_gesperrt", True))

    def _tags(self, woerter, einzug: str, ctx: int | None = None) -> str:
        if not woerter:
            return f"{einzug}<tags>\n{einzug}</tags>\n"
        attr = f' contextid="{ctx}"' if ctx else ""
        zeilen = "".join(
            f'{einzug}  <tag id="{self.ids("tag")}"{attr}>\n'
            f"{einzug}    {el('name', str(w).lower())}\n"
            f"{einzug}    {el('rawname', w)}\n{einzug}  </tag>\n" for w in woerter)
        return f"{einzug}<tags>\n{zeilen}{einzug}</tags>\n"

    def _modul(self, r: Akt) -> str:
        ab = self._abschluss(r)
        verf = self._verfuegbarkeit(r)
        gruppen = 1 if r.akt.get("gruppenabgabe") else 0
        gruppierung = self.gruppierung_ids.get(r.akt.get("gruppierung"), 0)
        return (
            f'<module id="{r.cmid}" version="{ZIEL["modul_version"]}">\n'
            f"  {el('modulename', r.typ)}\n  {el('sectionid', r.sec_id)}\n"
            f"  {el('sectionnumber', r.sec_nr)}\n"
            f"  {el('idnumber', r.akt.get('idnummer', ''))}\n"
            f"  {el('added', self.jetzt)}\n  <score>0</score>\n  {el('indent', int(r.akt.get('einzug', 0)))}\n"
            f"  {el('visible', r.sichtbar)}\n  <visibleoncoursepage>1</visibleoncoursepage>\n"
            f"  {el('visibleold', r.sichtbar_alt)}\n  {el('groupmode', gruppen)}\n"
            f"  {el('groupingid', gruppierung)}\n  {el('completion', ab['completion'])}\n"
            f"  {el('completiongradeitemnumber', ab['gradenr'])}\n"
            f"  {el('completionpassgrade', ab['pass'])}\n"
            f"  {el('completionview', ab['view'])}\n  <completionexpected>0</completionexpected>\n"
            f"  {el('availability', verf)}\n  {el('showdescription', 1 if getattr(r, 'zeige_beschreibung', False) else 0)}\n"
            f"  <downloadcontent>1</downloadcontent>\n  <lang></lang>\n"
            + self._tags(r.akt.get("tags"), "  ") + "</module>")

    def _inforef(self, r: Akt) -> str:
        teile = ["<inforef>"]
        for tag, inner, ids in (("fileref", "file", r.filerefs),
                                ("userref", "user", r.userrefs),
                                ("question_categoryref", "question_category",
                                 r.qcatrefs),
                                ("roleref", "role", r.rolerefs)):
            if ids:
                teile.append(f"  <{tag}>")
                teile += [f"    <{inner}>\n      <id>{i}</id>\n    </{inner}>"
                          for i in ids]
                teile.append(f"  </{tag}>")
        if r.gradeitem:
            teile.append(f"  <grade_itemref>\n    <grade_item>\n      <id>"
                         f"{r.gradeitem}</id>\n    </grade_item>\n  </grade_itemref>")
        return "\n".join(teile + ["</inforef>"])

    # -- Bewertung ------------------------------------------------------- #
    def punkte(self, r: Akt) -> float:
        return sterne.punkte(r.akt)       # eine Rechnung für Bau und Sternzähler (sterne.kursgesamt_max)

    def _grade_item_akt(self, r: Akt) -> str:
        if not r.gradeitem:
            return "\n  "
        if not kd.bewertet(r.akt):
            # Aufgabe ohne Note: Moodle 5.1 braucht ein Grade Item (assign::get_grade_item, sonst „Cannot load the grade
            # item“ beim Öffnen, gemessen 2026-10-25). Bewertungstyp Text (wie Moodle mit Feedback-Kommentaren und
            # Bewertung „Keine“): keine Note, zählt nie im Kursgesamt.
            self.grade_sort += 1
            return "\n" + self._grade_item(r.gradeitem, self.grade_kat, r.akt["name"], "mod", r.typ, r.instance, 0,
                                           100.0, self.grade_sort, idnummer=r.akt.get("idnummer"),
                                           gradetype=GRADE_TEXT) + "\n  "
        grademax = self.punkte(r)
        grenze = float(r.akt.get("bestehensgrenze_prozent") or 0) * grademax / 100
        self.grade_sort += 1
        # sterne 0 bzw. im_kursgesamt false: die Aktivität behält ihre Note, zählt aber nicht im Kursgesamt –
        # Gewicht von Hand auf 0 (Natürlich: fällt aus Summe und Höchstwert).
        null = r.akt.get("sterne") == 0 or r.akt.get("im_kursgesamt") is False
        if not null:
            self.grade_summe += grademax
        return "\n" + self._grade_item(r.gradeitem, self.grade_kat, r.akt["name"],
                                       "mod", r.typ, r.instance, 0, grademax,
                                       self.grade_sort, grenze, gewicht_null=null,
                                       idnummer=r.akt.get("idnummer")) + "\n  "

    def berechnung(self, formel: str) -> str:
        """Formel in der Form, die Moodle speichert und sichert: [[idnummer]] → ##gi<id>##, Trennzeichen „,“
        (calc_formula::unlocalize; „;“ ist nur die Anzeige der deutschen Oberfläche, EvalMath lehnt es ab)."""
        gi = {r.akt["idnummer"]: r.gradeitem for r in self.akts.values() if r.akt.get("idnummer") and r.gradeitem}

        def ersetze(m):
            if m.group(1) not in gi:
                raise ValueError(f"Formel {formel!r}: keine bewertete Aktivität mit idnummer {m.group(1)!r}")
            return f"##gi{gi[m.group(1)]}##"
        return kd.IDVERWEIS.sub(ersetze, formel).replace(";", ",")

    def _berechnete_items(self) -> str:
        """Berechnete Bewertungen als Kurs-Gradeitems (manual mit calculation); sie zählen im Kursgesamt."""
        teile = []
        for gid, b in self.berechnet:
            self.grade_sort += 1
            # im_kursgesamt false (z. B. Stufen-Mittelwerte, stufen.py): Gewicht 0, zählt nicht im Kursgesamt;
            # verborgen: Lernende sehen die Zeile nicht in ihrer Bewertungsübersicht (Bedingungen lesen sie trotzdem)
            null = b.get("im_kursgesamt") is False
            if not null:
                self.grade_summe += float(b["max"])
            teile.append(self._grade_item(gid, self.grade_kat, b["name"], "manual", None, None, None,
                                          float(b["max"]), self.grade_sort, gewicht_null=null,
                                          idnummer=b.get("idnummer"), verborgen=bool(b.get("verborgen")),
                                          berechnung=self.berechnung(b["formel"])) + "\n")
        return "".join(teile)

    def _grade_item(self, gid, kat, name, typ, modul, inst, nr, grademax,
                    sort, grenze=0.0, gewicht_null: bool = False, idnummer: str | None = None,
                    berechnung: str | None = None, gradetype: int = 1, verborgen: bool = False) -> str:
        z = lambda t, v: f"      {el(t, v)}\n"  # noqa: E731
        return (f'    <grade_item id="{gid}">\n' + z("categoryid", kat)
                + z("itemname", name) + z("itemtype", typ) + z("itemmodule", modul)
                + z("iteminstance", inst) + z("itemnumber", nr)
                + z("iteminfo", None) + z("idnumber", idnummer or None) + z("calculation", berechnung)
                + z("gradetype", gradetype) + z("grademax", f"{grademax:.5f}")
                + z("grademin", "0.00000") + z("scaleid", None) + z("outcomeid", None)
                + z("gradepass", f"{grenze:.5f}") + z("multfactor", "1.00000")
                + z("plusfactor", "0.00000") + z("aggregationcoef", "0.00000")
                + z("aggregationcoef2", "0.00000") + z("weightoverride", int(gewicht_null))
                + z("sortorder", sort) + z("display", 0) + z("decimals", None)
                + z("hidden", int(verborgen)) + z("locked", 0) + z("locktime", 0)
                + z("needsupdate", 0) + z("timecreated", self.jetzt)
                + z("timemodified", self.jetzt)
                + "      <grade_grades>\n      </grade_grades>\n    </grade_item>")

    # -- Kurs ------------------------------------------------------------ #
    def _kurs(self) -> None:
        k = self.kurs
        fmt = k.get("format", "tiles")
        if k.get("kursbild"):
            self.kurs_filerefs += self.ablegen(
                self.COURSE_CTX, "course", "overviewfiles", 0,
                self.lies(k["kursbild"]), Path(k["kursbild"]).name)
        optionen = ([("hiddensections", "1"), ("coursedisplay", "0")]
                    if fmt == "topics" else
                    [("basecolour", SCHULFARBE), ("coursedisplay", "1"),
                     ("courseshowtileprogress", "2"), ("defaulttileicon", "pie-chart"),
                     ("displayfilterbar", "0"), ("hiddensections", "1"),
                     ("courseusesubtiles", "0"), ("usesubtilesseczero", "0")])
        # ohne installiertes Kachelformat fällt Moodle auf „topics“ zurück: verborgene Abschnitte dort ebenfalls ganz
        # unsichtbar (Lehrkraftbereich; Sichtprüfung LS 5)
        rueckfall = [("topics", "hiddensections", "1")] if fmt != "topics" else []
        opt = "".join(f"    <courseformatoption>\n      {el('format', f)}\n"
                      f"      <sectionid>0</sectionid>\n      {el('name', n)}\n"
                      f"      {el('value', v)}\n    </courseformatoption>\n"
                      for f, n, v in [(fmt, n, v) for n, v in optionen] + rueckfall)
        # KI-Hinweis genau einmal im Kurs: steht er unten in Allgemein (Profil moodle.ki_hinweis), nicht auch hier
        beschreibung = (("" if k.get("ki_hinweis_in_allgemein") else f"<p>{x(k['ki_hinweis'])}</p>")
                        + k.get("beschreibung", ""))
        start = int(k.get("startdatum", self.jetzt))
        self.xml("course/course.xml", (
            f'<course id="{self.COURSE_ID}" contextid="{self.COURSE_CTX}">\n'
            f"  {el('shortname', k['kurzname'])}\n  {el('fullname', k['vollname'])}\n"
            f"  <idnumber></idnumber>\n  {el('summary', beschreibung)}\n"
            f"  <summaryformat>1</summaryformat>\n  {el('format', fmt)}\n"
            f"  <showgrades>1</showgrades>\n  <newsitems>0</newsitems>\n"
            f"  {el('startdate', start)}\n  <enddate>0</enddate>\n  <marker>0</marker>\n"
            f"  <maxbytes>0</maxbytes>\n  <legacyfiles>0</legacyfiles>\n"
            f"  <showreports>0</showreports>\n  <visible>1</visible>\n"
            f"  <groupmode>0</groupmode>\n  <groupmodeforce>0</groupmodeforce>\n"
            f"  <defaultgroupingid>0</defaultgroupingid>\n  <lang></lang>\n  <theme></theme>\n"
            f"  {el('timecreated', self.jetzt)}\n  {el('timemodified', self.jetzt)}\n"
            f"  <requested>0</requested>\n  <showactivitydates>1</showactivitydates>\n"
            f"  <showcompletionconditions>1</showcompletionconditions>\n"
            f"  <pdfexportfont>{NULL}</pdfexportfont>\n"
            f"  {el('enablecompletion', 1 if k.get('abschlussverfolgung', True) else 0)}\n"
            f"  <completionnotify>0</completionnotify>\n"
            f'  <category id="1">\n    <name>Allgemein</name>\n'
            f"    <description></description>\n  </category>\n"
            f"  <tags>\n  </tags>\n  <customfields>\n  </customfields>\n"
            f"  <courseformatoptions>\n{opt}  </courseformatoptions>\n"
            + ("  <plugin_format_tiles_course>\n    <dummycourse></dummycourse>\n"
               "  </plugin_format_tiles_course>\n" if fmt == "tiles" else "")
            + "</course>"))
        enrol = "".join(self._enrol(i, m, s, rolle) for i, m, s, rolle in
                        ((1, "manual", 0, 5), (2, "guest", 1, 0), (3, "self", 1, 5)))
        self.xml("course/enrolments.xml",
                 f"<enrolments>\n  <enrols>\n{enrol}  </enrols>\n</enrolments>")
        self.xml("course/roles.xml", "<roles>\n  <role_overrides>\n  </role_overrides>"
                 "\n  <role_assignments>\n  </role_assignments>\n</roles>")
        glossar = any(r.typ == "glossary" and r.akt.get("autoverlinkung", True)
                      for r in self.akts.values())
        aktiv = ("    <filter_active>\n      <filter>glossary</filter>\n"
                 "      <active>1</active>\n    </filter_active>\n" if glossar else "")
        self.xml("course/filters.xml", f"<filters>\n  <filter_actives>\n{aktiv}"
                 "  </filter_actives>\n  <filter_configs>\n  </filter_configs>\n</filters>")
        self.xml("course/calendar.xml", "<events>\n</events>")
        self.xml("course/completiondefaults.xml",
                 "<course_completion_defaults>\n</course_completion_defaults>")
        self.xml("course/contentbank.xml", "<contents>\n</contents>")

    def _enrol(self, eid, methode, status, rolle) -> str:
        nullen = "".join(f"      <{f}>{NULL}</{f}>\n" for f in (
            [f"customint{i}" for i in range(1, 9)]
            + [f"customchar{i}" for i in range(1, 4)]
            + ["customdec1", "customdec2"]
            + [f"customtext{i}" for i in range(1, 5)]))
        return (f'    <enrol id="{eid}">\n      {el("enrol", methode)}\n'
                f"      {el('status', status)}\n      <name>{NULL}</name>\n"
                "      <enrolperiod>0</enrolperiod>\n      <enrolstartdate>0</enrolstartdate>\n"
                "      <enrolenddate>0</enrolenddate>\n      <expirynotify>0</expirynotify>\n"
                "      <expirythreshold>0</expirythreshold>\n      <notifyall>0</notifyall>\n"
                "      <password></password>\n      <cost></cost>\n      <currency></currency>\n"
                f"      {el('roleid', rolle)}\n{nullen}"
                f"      {el('timecreated', self.jetzt)}\n      {el('timemodified', self.jetzt)}\n"
                "      <user_enrolments>\n      </user_enrolments>\n    </enrol>\n")

    # -- Dateien der obersten Ebene -------------------------------------- #
    def _oben(self) -> None:
        self.xml("badges.xml", self._abzeichen())
        self.xml("groups.xml", self._gruppen())
        self.xml("files.xml", self._files())
        self.xml("questions.xml", "<question_categories>\n"
                 + "\n".join(self.fragekategorien) + "\n</question_categories>")
        teile = ["<inforef>"]
        if self.gruppen:
            teile += ["  <groupref>"] + [f"    <group>\n      <id>{g}</id>\n    </group>"
                                         for g in self.gruppen] + ["  </groupref>"]
        teile.append("  <roleref>\n    <role>\n      <id>5</id>\n    </role>\n  </roleref>")
        if self.kurs_filerefs:
            teile += ["  <fileref>"] + [f"    <file>\n      <id>{f}</id>\n    </file>"
                                        for f in self.kurs_filerefs] + ["  </fileref>"]
        self.xml("course/inforef.xml", "\n".join(teile + ["</inforef>"]))
        self.xml("completion.xml", "<course_completion>\n</course_completion>")
        self.xml("scales.xml", "<scales_definition>\n</scales_definition>")
        self.xml("outcomes.xml", "<outcomes_definition>\n</outcomes_definition>")
        berechnet = self._berechnete_items()      # vor dem Kurs-Item: es zählt ihre Höchstwerte mit
        if self.sternzaehler_n is not None and self.grade_summe != self.sternzaehler_n:
            raise ValueError(f"Sternzähler bis {self.sternzaehler_n:g}, Kursgesamt aber bis {self.grade_summe:g}")
        kurs_item = self._grade_item(self.kurs_gradeitem, None, None, "course",
                                     None, self.grade_kat, None, self.grade_summe, 1)
        self.xml("gradebook.xml", (
            "<gradebook>\n  <attributes>\n  </attributes>\n  <grade_categories>\n"
            f'    <grade_category id="{self.grade_kat}">\n      <parent>{NULL}</parent>\n'
            f"      <depth>1</depth>\n      <path>/{self.grade_kat}/</path>\n"
            "      <fullname>?</fullname>\n      <aggregation>13</aggregation>\n"
            "      <keephigh>0</keephigh>\n      <droplow>0</droplow>\n"
            # „Nur bewertete Aspekte“ = Nein: noch nicht Bewertetes zählt mit 0 –
            # sonst stünde Kursgesamt nach dem ersten Test bei 100 % (Gold).
            "      <aggregateonlygraded>0</aggregateonlygraded>\n"
            "      <aggregateoutcomes>0</aggregateoutcomes>\n"
            f"      {el('timecreated', self.jetzt)}\n      {el('timemodified', self.jetzt)}\n"
            "      <hidden>0</hidden>\n    </grade_category>\n  </grade_categories>\n"
            f"  <grade_items>\n{berechnet}{kurs_item}\n  </grade_items>\n"
            "  <grade_letters>\n  </grade_letters>\n  <grade_settings>\n"
            f'    <grade_setting id="{self.ids("misc")}">\n      <name>minmaxtouse</name>\n'
            "      <value>1</value>\n    </grade_setting>\n"
            # Kursgesamt in der eigenen Bewertungsübersicht auch, solange einzelne Tests noch verborgen sind
            # (Abschlusstest): sonst zeigt Moodle Lernenden „-“, und Sternzähler und Sternebuch lesen 0 Sterne.
            # 2 = GRADE_REPORT_SHOW_REAL_TOTAL_IF_CONTAINS_HIDDEN (gleicher Wert wie Moodle intern rechnet)
            f'    <grade_setting id="{self.ids("misc")}">\n      <name>report_user_showtotalsifcontainhidden</name>\n'
            "      <value>2</value>\n    </grade_setting>\n  </grade_settings>\n</gradebook>"))
        self.xml("grade_history.xml",
                 "<grade_history>\n  <grade_grades>\n  </grade_grades>\n</grade_history>")
        self.xml("roles.xml", "<roles_definition>\n  <role id=\"5\">\n    <name></name>\n"
                 "    <shortname>student</shortname>\n"
                 f"    <nameincourse>{NULL}</nameincourse>\n    <description></description>\n"
                 "    <sortorder>5</sortorder>\n    <archetype>student</archetype>\n"
                 "  </role>\n</roles_definition>")
        if self.autor:
            self.xml("users.xml", self._users())
        self.inhalt["moodle_backup.log"] = b""

    def _gruppen(self) -> str:
        teile = []
        for name, gid in self.gruppen_ids.items():
            self.gruppen.append(gid)
            teile.append(
                f'  <group id="{gid}">\n    {el("name", name)}\n    <idnumber></idnumber>\n'
                f"    <description>{NULL}</description>\n    <descriptionformat>0</descriptionformat>\n"
                f"    <enrolmentkey>{NULL}</enrolmentkey>\n    <picture>0</picture>\n"
                "    <visibility>0</visibility>\n    <participation>1</participation>\n"
                f"    {el('timecreated', self.jetzt)}\n    {el('timemodified', self.jetzt)}\n"
                "    <group_members>\n    </group_members>\n  </group>\n")
        gruppierungen = []
        for name, gid in self.gruppierung_ids.items():
            zu = "".join(f'        <grouping_group id="{self.ids("misc")}">\n'
                         f"          {el('groupid', self.gruppen_ids[g])}\n"
                         f"          {el('timeadded', self.jetzt)}\n        </grouping_group>\n"
                         for g in self.k["gruppierungen"][name])
            gruppierungen.append(
                f'    <grouping id="{gid}">\n      {el("name", name)}\n      <idnumber></idnumber>\n'
                f"      <description>{NULL}</description>\n      <descriptionformat>0</descriptionformat>\n"
                f"      <configdata>{NULL}</configdata>\n"
                f"      {el('timecreated', self.jetzt)}\n      {el('timemodified', self.jetzt)}\n"
                f"      <grouping_groups>\n{zu}      </grouping_groups>\n    </grouping>\n")
        return ("<groups>\n" + "".join(teile) + "  <groupcustomfields>\n  </groupcustomfields>\n"
                "  <groupings>\n" + "".join(gruppierungen) + "    <groupingcustomfields>\n    </groupingcustomfields>\n"
                "  </groupings>\n</groups>")

    def _files(self) -> str:
        teile = ["<files>"]
        for f in self.dateisaetze:
            ist_datei = f["name"] != "."
            teile.append(
                f'  <file id="{f["id"]}">\n    {el("contenthash", f["hash"])}\n'
                f"    {el('contextid', f['ctx'])}\n    {el('component', f['comp'])}\n"
                f"    {el('filearea', f['area'])}\n    {el('itemid', f['itemid'])}\n"
                f"    {el('filepath', f['pfad'])}\n    {el('filename', f['name'])}\n"
                f"    <userid>2</userid>\n    {el('filesize', f['groesse'])}\n"
                f"    {el('mimetype', mime(f['name']) if ist_datei else None)}\n"
                f"    <status>0</status>\n    {el('timecreated', self.jetzt)}\n"
                f"    {el('timemodified', self.jetzt)}\n"
                f"    {el('source', f['name'] if ist_datei else None)}\n"
                f"    <author>{NULL}</author>\n    <license>{NULL}</license>\n"
                f"    {el('sortorder', f['sort'])}\n    <repositorytype>{NULL}</repositorytype>\n"
                f"    <repositoryid>{NULL}</repositoryid>\n    <reference>{NULL}</reference>\n"
                "  </file>")
        return "\n".join(teile + ["</files>"])

    def _abzeichen(self) -> str:
        teile = []
        for z in self.k.get("abzeichen", []):
            bid = self.ids("badge")
            self.badge_ids.append(bid)
            ziel = self.akts[z["aktivitaet"]]
            gesamt, krit = self.ids("krit"), self.ids("krit")
            daten = self.lies(z["bild"])
            h = hashlib.sha1(daten).hexdigest()
            self.inhalt.setdefault(f"files/{h[:2]}/{h}", daten)
            self._satz(self.COURSE_CTX, "badges", "badgeimage", bid, LEER_HASH, ".", 0, 0)
            for nr, name in enumerate(("f1.png", "f2.png", "f3.png"), start=1):
                self._satz(self.COURSE_CTX, "badges", "badgeimage", bid, h, name,
                           len(daten), nr)
            teile.append(
                f'  <badge id="{bid}">\n    {el("name", z["name"])}\n'
                f"    {el('description', z.get('beschreibung', z['name']))}\n"
                f"    {el('timecreated', self.jetzt)}\n    {el('timemodified', self.jetzt)}\n"
                "    <usercreated>2</usercreated>\n    <usermodified>2</usermodified>\n"
                f"    {el('issuername', self.kurs.get('schule') or self.kurs['vollname'])}\n"
                "    <issuerurl></issuerurl>\n    <issuercontact></issuercontact>\n"
                f"    <expiredate>{NULL}</expiredate>\n    <expireperiod>{NULL}</expireperiod>\n"
                f"    <type>2</type>\n    {el('courseid', self.COURSE_ID)}\n"
                "    <message></message>\n    <messagesubject></messagesubject>\n"
                "    <attachment>1</attachment>\n    <notification>0</notification>\n"
                "    <status>0</status>\n    <nextcron>0</nextcron>\n    <version></version>\n"
                "    <language>de</language>\n    <imagecaption></imagecaption>\n"
                "    <criteria>\n"
                f'      <criterion id="{gesamt}">\n        {el("badgeid", bid)}\n'
                "        <criteriatype>0</criteriatype>\n        <method>1</method>\n"
                "        <description></description>\n        <descriptionformat>1</descriptionformat>\n"
                "        <parameters>\n        </parameters>\n      </criterion>\n"
                f'      <criterion id="{krit}">\n        {el("badgeid", bid)}\n'
                "        <criteriatype>1</criteriatype>\n        <method>1</method>\n"
                "        <description></description>\n        <descriptionformat>1</descriptionformat>\n"
                f'        <parameters>\n          <parameter id="{self.ids("param")}">\n'
                f"            {el('critid', krit)}\n"
                f"            {el('name', f'module_{ziel.cmid}')}\n"
                f"            {el('value', ziel.cmid)}\n"
                "            <criteriatype>1</criteriatype>\n          </parameter>\n"
                "        </parameters>\n      </criterion>\n    </criteria>\n"
                "    <endorsement>\n    </endorsement>\n    <alignments>\n    </alignments>\n"
                "    <relatedbadges>\n    </relatedbadges>\n    <manual_awards>\n"
                "    </manual_awards>\n    <tags>\n    </tags>\n  </badge>\n")
        return "<badges>\n" + "".join(teile) + "</badges>"

    def autor_id(self) -> int:
        if self.autor is None:
            self.autor = dict(AUTOR, id=self.ids("user"), ctx=self.ids("usectx"))
        return self.autor["id"]

    def _users(self) -> str:
        u = self.autor
        j = self.jetzt
        return (f'<users>\n  <user id="{u["id"]}" contextid="{u["ctx"]}">\n'
                f"    {el('username', u['username'])}\n    <idnumber></idnumber>\n"
                f"    {el('email', u['email'])}\n    <phone1></phone1>\n    <phone2></phone2>\n"
                "    <institution></institution>\n    <department></department>\n"
                "    <address></address>\n    <city></city>\n    <country>DE</country>\n"
                "    <lastip></lastip>\n    <picture>0</picture>\n"
                f"    <description>{NULL}</description>\n    <descriptionformat>1</descriptionformat>\n"
                f"    <imagealt>{NULL}</imagealt>\n    <auth>manual</auth>\n"
                f"    {el('firstname', u['firstname'])}\n    {el('lastname', u['lastname'])}\n"
                "    <firstnamephonetic></firstnamephonetic>\n    <lastnamephonetic></lastnamephonetic>\n"
                "    <middlename></middlename>\n    <alternatename></alternatename>\n"
                f"    <mnethosturl>{NULL}</mnethosturl>\n    <confirmed>1</confirmed>\n"
                "    <policyagreed>0</policyagreed>\n    <deleted>0</deleted>\n    <lang>de</lang>\n"
                "    <theme></theme>\n    <timezone>99</timezone>\n"
                f"    <firstaccess>{j}</firstaccess>\n    <lastaccess>{j}</lastaccess>\n"
                f"    <lastlogin>{j}</lastlogin>\n    <currentlogin>{j}</currentlogin>\n"
                "    <mailformat>1</mailformat>\n    <maildigest>0</maildigest>\n"
                "    <maildisplay>2</maildisplay>\n    <autosubscribe>1</autosubscribe>\n"
                f"    <trackforums>0</trackforums>\n    <timecreated>{j}</timecreated>\n"
                f"    <timemodified>{j}</timemodified>\n    <trustbitmask>0</trustbitmask>\n"
                "    <custom_fields>\n    </custom_fields>\n    <tags>\n    </tags>\n"
                "    <preferences>\n    </preferences>\n    <roles>\n      <role_overrides>\n"
                "      </role_overrides>\n      <role_assignments>\n      </role_assignments>\n"
                "    </roles>\n  </user>\n</users>")

    # -- moodle_backup.xml ----------------------------------------------- #
    def _moodle_backup(self) -> None:
        k = self.kurs
        name = f"sicherung-{k['kurzname']}.mbz"
        nutzer = 1 if self.autor else 0
        akts = sorted(self.akts.values(), key=lambda r: (r.sec_nr, r.cmid))
        acts = "".join(
            f"        <activity>\n          {el('moduleid', r.cmid)}\n"
            f"          {el('sectionid', r.sec_id)}\n          {el('modulename', r.typ)}\n"
            f"          {el('title', r.akt['name'])}\n"
            f"          {el('directory', f'activities/{r.typ}_{r.cmid}')}\n        </activity>\n"
            for r in akts)
        secs = "".join(
            f"        <section>\n          {el('sectionid', s)}\n          {el('title', t)}\n"
            f"          {el('directory', f'sections/section_{s}')}\n        </section>\n"
            for s, t in self.abschnittsliste)
        wurzel = [("filename", name), ("imscc11", 0), ("users", nutzer),
                  ("anonymize", 0), ("role_assignments", 0), ("activities", 1),
                  ("blocks", 1), ("files", 1), ("filters", 1), ("comments", 0),
                  ("badges", 1 if self.badge_ids else 0), ("calendarevents", 1),
                  ("userscompletion", 0), ("logs", 0), ("grade_histories", 0),
                  ("questionbank", 1), ("groups", 1), ("competencies", 0),
                  ("customfield", 1), ("contentbankcontent", 1), ("legacyfiles", 1)]
        if self.rechte:
            wurzel.append(("permissions", 1))
        st = "".join(f"      <setting>\n        <level>root</level>\n        {el('name', n)}\n"
                     f"        {el('value', v)}\n      </setting>\n" for n, v in wurzel)
        for s, _ in self.abschnittsliste:
            for teil in ("included", "userinfo"):
                wert = 1 if teil == "included" else nutzer
                st += (f"      <setting>\n        <level>section</level>\n"
                       f"        <section>section_{s}</section>\n"
                       f"        <name>section_{s}_{teil}</name>\n"
                       f"        <value>{wert}</value>\n      </setting>\n")
        for r in akts:
            schl = f"{r.typ}_{r.cmid}"
            for teil in ("included", "userinfo"):
                wert = 1 if teil == "included" else (1 if r.userrefs else 0)
                st += (f"      <setting>\n        <level>activity</level>\n"
                       f"        <activity>{schl}</activity>\n"
                       f"        <name>{schl}_{teil}</name>\n"
                       f"        <value>{wert}</value>\n      </setting>\n")
        info = "".join(f"    {el(t, v)}\n" for t, v in (
            ("name", name), ("moodle_version", ZIEL["moodle_version"]),
            ("moodle_release", ZIEL["moodle_release"]),
            ("backup_version", ZIEL["backup_version"]),
            ("backup_release", ZIEL["backup_release"]), ("backup_date", self.jetzt),
            ("mnet_remoteusers", 0), ("include_files", 1),
            ("include_file_references_to_external_content", 0),
            ("original_wwwroot", "https://moodle.example.org"),
            ("original_site_identifier_hash", hashlib.md5(b"p3").hexdigest()),
            ("original_course_id", self.COURSE_ID), ("original_course_format",
                                                     k.get("format", "tiles")),
            ("original_course_fullname", k["vollname"]),
            ("original_course_shortname", k["kurzname"]),
            ("original_course_startdate", int(k.get("startdatum", self.jetzt))),
            ("original_course_enddate", 0),
            ("original_course_contextid", self.COURSE_CTX),
            ("original_system_contextid", 1)))
        backup_id = hashlib.md5(f"{k['kurzname']}{self.jetzt}".encode()).hexdigest()
        self.xml("moodle_backup.xml", (
            f"<moodle_backup>\n  <information>\n{info}    <details>\n"
            f'      <detail backup_id="{backup_id}">\n        <type>course</type>\n'
            "        <format>moodle2</format>\n        <interactive>1</interactive>\n"
            "        <mode>10</mode>\n        <execution>1</execution>\n"
            "        <executiontime>0</executiontime>\n      </detail>\n    </details>\n"
            f"    <contents>\n      <activities>\n{acts}      </activities>\n"
            f"      <sections>\n{secs}      </sections>\n      <course>\n"
            f"        {el('courseid', self.COURSE_ID)}\n        {el('title', k['kurzname'])}\n"
            "        <directory>course</directory>\n      </course>\n    </contents>\n"
            f"    <settings>\n{st}    </settings>\n  </information>\n</moodle_backup>"))

    def _packen(self) -> bytes:
        eintraege: list[tuple[str, bool]] = []
        gesehen: set[str] = set()
        for pfad in self.inhalt:
            teile = pfad.split("/")[:-1]
            for i in range(1, len(teile) + 1):
                d = "/".join(teile[:i]) + "/"
                if d not in gesehen:
                    gesehen.add(d)
                    eintraege.append((d, True))
            eintraege.append((pfad, False))
        index = [f"Moodle archive file index. Count: {len(eintraege)}"]
        index += [f"{p}\td\t0\t?" if d else f"{p}\tf\t{len(self.inhalt[p])}\t{self.jetzt}"
                  for p, d in eintraege]
        puffer = io.BytesIO()
        with tarfile.open(fileobj=puffer, mode="w:gz") as tar:
            def datei(pfad, daten):
                info = tarfile.TarInfo(pfad)
                info.size, info.mode, info.mtime = len(daten), 0o644, self.jetzt
                tar.addfile(info, io.BytesIO(daten))
            datei(".ARCHIVE_INDEX", ("\n".join(index) + "\n").encode())
            for pfad, ist_ordner in eintraege:
                if ist_ordner:
                    info = tarfile.TarInfo(pfad)
                    info.type, info.mode, info.mtime = tarfile.DIRTYPE, 0o755, self.jetzt
                    tar.addfile(info)
                else:
                    datei(pfad, self.inhalt[pfad])
        return puffer.getvalue()


# --------------------------------------------------------------------------- #
# Aktivitäten (je Typ eine kleine Funktion; liefert das innere XML)
# --------------------------------------------------------------------------- #
def hat_text(html: str | None) -> bool:
    """Hat eine Beschreibung sichtbaren Inhalt (Text oder Bild)?"""
    return bool(html) and (bool(re.search(r"<(img|svg|video|audio|iframe)\b", html, re.I))
                           or bool(re.sub(r"<[^>]+>|&nbsp;|\s", "", html)))


def _intro(a: dict, text: str | None = None) -> str:
    return (f"    {el('intro', a.get('beschreibung', '') if text is None else text)}\n"
            "    <introformat>1</introformat>\n")


def _docx_teil(b: Bau, r: Akt, liste: list[str], knopf: bool, heft: bool = False,
               pdf_liste: list[str] | None = None, kacheln: dict[str, int] | None = None,
               druck_pdf: bool = False) -> str:
    """HTML aus den Word-Dateien einer Seite; DOCX und Bilder in den Dateibereich der Seite. Mit `knopf` stehen
    die Download-Knöpfe oben statt am Ende (Pop-up-Seiten, statt eines Druckknopfs), je Datei einmal; bei
    mehreren Dateien mit Namen („Leitkarte als Word“). Mit dem Kursschalter
    `pdf_formular` entsteht je DOCX ein ausfüllbares PDF; nur mit mindestens einem Feld kommt es in den
    Dateibereich und bekommt einen eigenen Knopf. Mit `heft` (Infoseite wie im Heft, Lehrkraft 2026-10-27)
    gestaltet docx_seite die Seite wie das Blatt; `pdf_liste` nennt je DOCX das fertige Druck-PDF dazu. Mit
    `druck_pdf` (Infoseite, Profil `moodle.infoseiten_downloads` „word_pdf“) bekommt jede DOCX ohne
    ausfüllbares PDF ein Druck-PDF, ohne Ausfüll-Hinweis."""
    import docx_seite   # erst hier: python-docx braucht nur, wer Word-Dateien einbindet
    pfade = [b.wurzel / rel for rel in liste]
    pdfs: dict[Path, Path] = {}
    fest = {p: b.wurzel / rel for p, rel in zip(pfade, pdf_liste or []) if rel}
    if fest:
        pdfs.update(fest)
    elif b.kurs.get("pdf_formular"):
        import pdf_formular   # erst hier: Word/LibreOffice und PyMuPDF braucht nur, wer den Schalter setzt
        for p in pfade:
            ziel = Path(tempfile.mkdtemp(prefix="docx_pdf_")) / f"{p.stem}.pdf"
            try:
                pdf_formular.docx_zu_pdf(p, ziel)
                if pdf_formular.formular_felder(ziel) > 0:
                    pdfs[p] = ziel
                    continue
            except BaseException:
                for pdf in [ziel, *pdfs.values()]:
                    shutil.rmtree(pdf.parent, ignore_errors=True)
                raise
            shutil.rmtree(ziel.parent, ignore_errors=True)
    druck: set[Path] = set(fest.values())
    if druck_pdf:
        import pdf_formular
        for p in pfade:
            if p not in pdfs:
                pdfs[p] = Path(tempfile.mkdtemp(prefix="docx_pdf_")) / f"{p.stem}.pdf"
                pdf_formular.docx_zu_pdf(p, pdfs[p])
                druck.add(pdfs[p])
    try:
        html, dateien = docx_seite.docx_seite_html(pfade, pdfs, knoepfe_oben=knopf, heft=heft, kacheln=kacheln,
                                                   druck=druck)
    except BaseException:
        for pdf in pdfs.values():
            if pdf not in fest.values():
                shutil.rmtree(pdf.parent, ignore_errors=True)
        raise
    try:
        for d in dateien:
            r.filerefs += b.ablegen(r.ctx, "mod_page", "content", 0, docx_seite._lies(d), d.name)
    finally:
        bleiben = set(pfade) | set(fest.values())
        for ordner in {d.parent for d in dateien if d not in bleiben}:   # Zwischenordner der Bilder
            shutil.rmtree(ordner, ignore_errors=True)
    return html


_WORD_LINK = re.compile(r'<a\b[^>]*href="@@PLUGINFILE@@/([^"]+\.docx)"[^>]*>')


def _pdf_zu_word_knoepfen(b: Bau, r: Akt, inhalt: str) -> str:
    """Infoseite mit eigenem HTML (Profil `moodle.infoseiten_downloads` „word_pdf“): zu jedem Word-Knopf ohne
    PDF entsteht das PDF derselben Word-Datei (sieht aus wie das Blatt) und ein Knopf davor."""
    import docx_seite
    import pdf_formular
    pfade = {Path(rel).name: rel for rel in r.akt.get("dateien") or []}
    vorhanden = set(re.findall(r'href="@@PLUGINFILE@@/([^"]+)\.pdf"', inhalt))
    for name in dict.fromkeys(urllib.parse.unquote(n) for n in _WORD_LINK.findall(inhalt)):
        stamm = Path(name).stem
        if stamm in vorhanden or name not in pfade:
            continue
        ordner = Path(tempfile.mkdtemp(prefix="info_pdf_"))
        try:
            ziel = ordner / f"{stamm}.pdf"
            pdf_formular.docx_zu_pdf(b.wurzel / pfade[name], ziel)
            r.filerefs += b.ablegen(r.ctx, "mod_page", "content", 0, ziel.read_bytes(), ziel.name)
        finally:
            shutil.rmtree(ordner, ignore_errors=True)
        knopf = docx_seite._knopf(ziel.name, docx_seite.PDF_KNOPF, "fa-file-pdf", "#C0392B")
        inhalt = re.sub(r'(<a\b[^>]*href="@@PLUGINFILE@@/' + re.escape(urllib.parse.quote(name)) + '"|<a\b[^>]*href="@@PLUGINFILE@@/'
                        + re.escape(name) + '")', lambda m: knopf + " " + m.group(1), inhalt, count=1)
    return inhalt


def b_page(b: Bau, r: Akt) -> str:
    a = r.akt
    popup = bool(a.get("popup"))
    inhalt = b.bilder(a.get("inhalt", ""), a.get("dateien"), r, "mod_page", "content")
    if a.get("rolle") == "info" and b.kurs.get("infoseiten_downloads") == "word_pdf":
        inhalt = _pdf_zu_word_knoepfen(b, r, inhalt)
    if a.get("docx_stil") == "heft":   # Infoseite wie im Heft: zuerst der Kasten, danach weitere Knöpfe
        inhalt = _docx_teil(b, r, a["docx"], True, heft=True, pdf_liste=a.get("docx_pdf"),
                            kacheln=a.get("kacheln")) + inhalt
    elif a.get("docx"):
        inhalt += _docx_teil(b, r, a["docx"], popup,
                             druck_pdf=a.get("rolle") == "info" and b.kurs.get("infoseiten_downloads") == "word_pdf")
    if popup:   # Infoblatt im Pop-up mittig statt links (Lehrkraft 2026-10-27); Heftbreite 680 px
        inhalt = (f'<div class="mdp-mitte" style="max-width:{int(a.get("breite") or 820)}px;margin:0 auto;">'
                  f"{inhalt}</div>")
    # Beschreibung (mit Schildern) oben in der Seite, sonst ginge sie ohne Anzeige auf der Kursseite verloren
    mit_intro = 1 if hat_text(a.get("beschreibung")) else 0
    optionen = {**(POPUP_GROESSE if popup else {}), "printheading": 1, "printintro": mit_intro,
                "printlastmodified": 0}
    return (f'  <page id="{r.instance}">\n    {el("name", a["name"])}\n{_intro(a)}'
            f"    {el('content', inhalt)}\n    <contentformat>1</contentformat>\n"
            f"    <legacyfiles>0</legacyfiles>\n    <legacyfileslast>{NULL}</legacyfileslast>\n"
            f"    {el('display', SEITE_POPUP if popup else SEITE_OFFEN)}\n"
            f"    {el('displayoptions', php(optionen))}\n"
            f"    <revision>1</revision>\n    {el('timemodified', b.jetzt)}\n  </page>")


def b_label(b: Bau, r: Akt) -> str:
    a = r.akt
    text = b.bilder(a["text"], a.get("dateien"), r, "mod_label", "intro")
    return (f'  <label id="{r.instance}">\n    {el("name", a["name"])}\n'
            f"{_intro(a, text)}    {el('timemodified', b.jetzt)}\n  </label>")


def b_resource(b: Bau, r: Akt) -> str:
    a = r.akt
    r.filerefs += b.ablegen(r.ctx, "mod_resource", "content", 0, b.lies(a["datei"]),
                            Path(a["datei"]).name)
    vorgabe = "eingebettet" if a["datei"].lower().endswith((".html", ".htm")) else "automatisch"
    anzeige = ANZEIGE_RESOURCE[a.get("anzeige", vorgabe)]
    return (f'  <resource id="{r.instance}">\n    {el("name", a["name"])}\n{_intro(a)}'
            "    <tobemigrated>0</tobemigrated>\n    <legacyfiles>0</legacyfiles>\n"
            f"    <legacyfileslast>{NULL}</legacyfileslast>\n    {el('display', anzeige)}\n"
            f"    {el('displayoptions', php({'printintro': 1}))}\n"
            "    <filterfiles>0</filterfiles>\n    <revision>1</revision>\n"
            f"    {el('timemodified', b.jetzt)}\n  </resource>")


def b_folder(b: Bau, r: Akt) -> str:
    a = r.akt
    for rel in a["dateien"]:
        r.filerefs += b.ablegen(r.ctx, "mod_folder", "content", 0, b.lies(rel), Path(rel).name)
    return (f'  <folder id="{r.instance}">\n    {el("name", a["name"])}\n{_intro(a)}'
            f"    <revision>1</revision>\n    {el('timemodified', b.jetzt)}\n"
            "    <display>0</display>\n    <showexpanded>1</showexpanded>\n"
            "    <showdownloadfolder>1</showdownloadfolder>\n    <forcedownload>0</forcedownload>\n"
            "  </folder>")


def b_url(b: Bau, r: Akt) -> str:
    a = r.akt
    return (f'  <url id="{r.instance}">\n    {el("name", a["name"])}\n{_intro(a)}'
            f"    {el('externalurl', a['adresse'])}\n"
            f"    {el('display', ANZEIGE_URL[a.get('anzeige', 'automatisch')])}\n"
            f"    {el('displayoptions', php({'printintro': 1}))}\n"
            f"    <parameters>a:0:{{}}</parameters>\n    {el('timemodified', b.jetzt)}\n  </url>")


def _raster_html(raster: list) -> str:
    zeilen = "".join(f"<tr><td>{x(k['kriterium'])}</td><td>{x(k.get('beschreibung', ''))}"
                     f"</td><td>{x(k['punkte'])}</td></tr>" for k in raster)
    return ('<h4>Bewertungsraster</h4><table class="table"><thead><tr><th>Kriterium</th>'
            f"<th>Beschreibung</th><th>Punkte</th></tr></thead><tbody>{zeilen}</tbody></table>")


def b_assign(b: Bau, r: Akt) -> str:
    a = r.akt
    intro = b.bilder(a.get("beschreibung", ""), a.get("dateien"), r, "mod_assign", "intro")
    for rel in a.get("anhaenge") or []:      # zusätzliche Dateien (introattachments), unter der Beschreibung
        r.filerefs += b.ablegen(r.ctx, "mod_assign", "introattachment", 0, b.lies(rel), Path(rel).name)
    if a.get("bewertungsraster") and not kd.raster_mit_stufen(a):
        # Raster ohne Stufen: Tabelle in der Beschreibung, Punkte als Summe; mit
        # Stufen: echte Rubrik in grading.xml (Bau._bewertungsbereich).
        intro += _raster_html(a["bewertungsraster"])
    wege = a.get("abgabe", ["datei"])
    team = 1 if a.get("gruppenabgabe") else 0
    # bewertung „keine“: grade 0 heißt in Moodle Bewertungstyp „Keine“ (keine Note); dazu ein Grade Item vom Typ
    # Text, das nie im Kursgesamt zählt (Bau._grade_item_akt).
    abschluss = b._abschluss(r)["modul"]
    konf = [("file", "assignsubmission", "enabled", int("datei" in wege)),
            ("file", "assignsubmission", "maxfilesubmissions", int(a.get("max_dateien", 3))),
            ("file", "assignsubmission", "maxsubmissionsizebytes", 0),
            ("file", "assignsubmission", "filetypeslist", a.get("dateitypen", "")),
            ("onlinetext", "assignsubmission", "enabled", int("onlinetext" in wege)),
            ("onlinetext", "assignsubmission", "wordlimit", 0),
            ("onlinetext", "assignsubmission", "wordlimitenabled", 0),
            ("comments", "assignsubmission", "enabled", 1),
            # Feedback-Kommentare immer an: ohne sie legt Moodle bei Bewertung „Keine“ kein Grade Item an, und Moodle
            # 5.1 bricht die Ansicht der Abgabe ab. Rückmeldung bleibt freiwillig (Lehrkraft schreibt keine).
            ("comments", "assignfeedback", "enabled", 1)]
    konf_xml = "".join(
        f'      <plugin_config id="{b.ids("misc")}">\n        <plugin>{p}</plugin>\n'
        f"        <subtype>{s}</subtype>\n        <name>{n}</name>\n"
        f"        {el('value', v)}\n      </plugin_config>\n" for p, s, n, v in konf)
    felder = [("alwaysshowdescription", 1), ("submissiondrafts", 1 if a.get("abgabe_bestaetigen") else 0),
              ("sendnotifications", 0), ("sendlatenotifications", 0),
              ("sendstudentnotifications", 1), ("duedate", 0), ("cutoffdate", 0),
              ("gradingduedate", 0), ("allowsubmissionsfromdate", 0),
              ("grade", int(b.punkte(r))), ("timemodified", b.jetzt),
              ("completionsubmit", abschluss.get("completionsubmit", 0)),
              ("requiresubmissionstatement", 0), ("teamsubmission", team),
              ("requireallteammemberssubmit", 0),
              ("teamsubmissiongroupingid", b.gruppierung_ids.get(a.get("gruppierung"), 0)),
              ("blindmarking", 0), ("hidegrader", 0), ("revealidentities", 0),
              ("attemptreopenmethod", "untilpass"), ("maxattempts", 1),
              ("markingworkflow", 1 if a.get("bewertungsworkflow") else 0), ("markingallocation", 0),
              ("markinganonymous", 0), ("preventsubmissionnotingroup", 0)]
    return (f'  <assign id="{r.instance}">\n    {el("name", a["name"])}\n{_intro(a, intro)}'
            + "".join(f"    {el(n, v)}\n" for n, v in felder)
            + "    <activity></activity>\n    <activityformat>1</activityformat>\n"
            "    <timelimit>0</timelimit>\n    <submissionattachments>0</submissionattachments>\n"
            "    <gradepenalty>0</gradepenalty>\n    <userflags>\n    </userflags>\n"
            "    <submissions>\n    </submissions>\n    <grades>\n    </grades>\n"
            f"    <plugin_configs>\n{konf_xml}    </plugin_configs>\n  </assign>")


def _stufentext(st: dict) -> str:
    """Text einer Rubrik-Stufe: „Bezeichnung: Beschreibung“ (eins von beiden genügt)."""
    return ": ".join(t for t in (str(st.get("bezeichnung") or "").strip(), str(st.get("beschreibung") or "").strip())
                     if t)


def b_feedback(b: Bau, r: Akt) -> str:
    a = r.akt
    items = []
    for pos, e in enumerate(a["elemente"], start=1):
        t = e.get("typ", "info")
        if t == "info":
            typ, name, pres, wert = "label", "", e.get("text", ""), 0
        elif t in ("likert", "auswahl"):
            optionen = e.get("optionen") or LIKERT
            bauart = "c" if e.get("mehrfach") else "r"
            typ, name, pres, wert = ("multichoice", e["frage"],
                                     f"{bauart}>>>>>" + "|".join(optionen), 1)
        elif t == "text":
            typ, name, pres, wert = "textfield", e["frage"], "60|255", 1
        else:
            raise ValueError(f"{a['name']}: Feedback-Element {t!r} unbekannt "
                             f"(info, likert, auswahl, text)")
        items.append(
            f'      <item id="{b.ids("misc")}">\n        <template>0</template>\n'
            f"        {el('name', name)}\n        <label></label>\n"
            f"        {el('presentation', pres)}\n        {el('typ', typ)}\n"
            f"        {el('hasvalue', wert)}\n        {el('position', pos)}\n"
            f"        {el('required', 1 if e.get('pflicht') else 0)}\n"
            "        <dependitem>0</dependitem>\n        <dependvalue></dependvalue>\n"
            f"        {el('options', 'h' if typ == 'multichoice' else '')}\n      </item>")
    abschluss = b._abschluss(r)["modul"]
    return (f'  <feedback id="{r.instance}">\n    {el("name", a["name"])}\n{_intro(a)}'
            f"    {el('anonymous', 1 if a.get('anonym', True) else 2)}\n"
            "    <email_notification>0</email_notification>\n    <multiple_submit>0</multiple_submit>\n"
            "    <autonumbering>0</autonumbering>\n    <site_after_submit></site_after_submit>\n"
            "    <page_after_submit></page_after_submit>\n    <page_after_submitformat>1</page_after_submitformat>\n"
            f"    {el('publish_stats', 1 if a.get('ergebnis_zeigen') else 0)}\n    <timeopen>0</timeopen>\n"
            f"    <timeclose>0</timeclose>\n    {el('timemodified', b.jetzt)}\n"
            f"    {el('completionsubmit', abschluss.get('completionsubmit', 0))}\n"
            "    <items>\n" + "\n".join(items) + "\n    </items>\n  </feedback>")


def b_glossary(b: Bau, r: Akt) -> str:
    a = r.akt
    eintraege, zuordnung = [], {}
    if a.get("eintraege"):
        uid = b.autor_id()
        r.userrefs.append(uid)
    for e in a.get("eintraege", []):
        eid = b.ids("instance")
        definition = e["definition"]
        if e.get("bild"):
            name = Path(e["bild"]).name
            r.filerefs += b.ablegen(r.ctx, "mod_glossary", "entry", eid, b.lies(e["bild"]), name)
            definition += (f'<p><img src="@@PLUGINFILE@@/{urllib.parse.quote(name)}" '
                           f'alt="{x(e.get("bild_alt", e["begriff"]))}" '
                           'style="max-width:100%;height:auto"></p>')
            if e.get("bild_quelle"):    # Quelle direkt unter dem Bild
                definition += f'<p style="font-size:16px;color:#4A5260;">{x(e["bild_quelle"])}</p>'
        aliasse = "".join(f'          <alias id="{b.ids("misc")}">\n            {el("alias_text", t)}\n'
                          "          </alias>\n" for t in e.get("aliasse") or [])
        if e.get("anhang"):
            r.filerefs += b.ablegen(r.ctx, "mod_glossary", "attachment", eid,
                                    b.lies(e["anhang"]), Path(e["anhang"]).name)
        if e.get("kategorie"):
            zuordnung.setdefault(e["kategorie"], []).append(eid)
        eintraege.append(
            f'      <entry id="{eid}">\n        {el("userid", uid)}\n'
            f"        {el('concept', e['begriff'])}\n        {el('definition', definition)}\n"
            "        <definitionformat>1</definitionformat>\n        <definitiontrust>0</definitiontrust>\n"
            f"        {el('attachment', '1' if e.get('anhang') else '')}\n"
            f"        {el('timecreated', b.jetzt)}\n        {el('timemodified', b.jetzt)}\n"
            "        <teacherentry>1</teacherentry>\n        <sourceglossaryid>0</sourceglossaryid>\n"
            f"        <usedynalink>{0 if e.get('autoverlinkung') is False else 1}</usedynalink>\n"
            "        <casesensitive>0</casesensitive>\n"
            "        <fullmatch>1</fullmatch>\n        <approved>1</approved>\n"
            f"        <aliases>\n{aliasse}        </aliases>\n        <ratings>\n        </ratings>\n"
            "      </entry>")
    kategorien = "".join(
        f'      <category id="{b.ids("misc")}">\n        {el("name", k)}\n'
        "        <usedynalink>0</usedynalink>\n        <category_entries>\n"
        + "".join(f'          <category_entry id="{b.ids("misc")}">\n'
                  f"            <entryid>{eid}</entryid>\n          </category_entry>\n"
                  for eid in zuordnung.get(k, []))
        + "        </category_entries>\n      </category>\n"
        for k in a.get("kategorien", []))
    verlinken = 1 if a.get("autoverlinkung", True) else 0
    return (f'  <glossary id="{r.instance}">\n    {el("name", a["name"])}\n{_intro(a)}'
            "    <allowduplicatedentries>0</allowduplicatedentries>\n"
            "    <displayformat>dictionary</displayformat>\n    <mainglossary>0</mainglossary>\n"
            "    <showspecial>1</showspecial>\n    <showalphabet>1</showalphabet>\n"
            "    <showall>1</showall>\n    <allowcomments>0</allowcomments>\n"
            f"    <allowprintview>1</allowprintview>\n    {el('usedynalink', verlinken)}\n"
            f"    {el('defaultapproval', 0 if a.get('freigabe_noetig', True) else 1)}\n"
            "    <globalglossary>0</globalglossary>\n    <entbypage>10</entbypage>\n"
            "    <editalways>0</editalways>\n    <rsstype>0</rsstype>\n    <rssarticles>0</rssarticles>\n"
            "    <assessed>0</assessed>\n    <assesstimestart>0</assesstimestart>\n"
            "    <assesstimefinish>0</assesstimefinish>\n    <scale>0</scale>\n"
            f"    {el('timecreated', b.jetzt)}\n    {el('timemodified', b.jetzt)}\n"
            "    <completionentries>0</completionentries>\n"
            "    <entries>\n" + "\n".join(eintraege) + "\n    </entries>\n"
            "    <entriestags>\n    </entriestags>\n"
            f"    <categories>\n{kategorien}    </categories>\n  </glossary>")


def b_quiz(b: Bau, r: Akt) -> str:
    a = r.akt
    slots = fragen.registrieren(b, r, a["fragen"])
    instanzen = "\n".join(
        f'      <question_instance id="{b.ids("slot")}">\n        {el("slot", nr)}\n'
        f"        {el('page', nr)}\n        <requireprevious>0</requireprevious>\n"
        f"        <maxmark>{marke:.7f}</maxmark>\n"
        f'        <question_reference id="{b.ids("slot")}">\n'
        f"          {el('usingcontextid', r.ctx)}\n          <component>mod_quiz</component>\n"
        "          <questionarea>slot</questionarea>\n"
        f"          {el('questionbankentryid', qbe)}\n          <version>{NULL}</version>\n"
        "        </question_reference>\n      </question_instance>"
        for nr, (qbe, marke) in enumerate(slots, start=1))
    summe = sum(m for _, m in slots)
    verhalten = a.get("verhalten", "deferredfeedback")
    sicht = QUIZ_VERHALTEN[verhalten]
    # rueckschau_bewertung false (Eingangstest): Rückschau nur mit den eigenen Antworten, ohne richtig/falsch,
    # Punkte und Rückmeldungen (verrät keine spätere Entdeckung)
    bewertung_zeigen = sicht if a.get("rueckschau_bewertung", True) else 0
    abschluss = b._abschluss(r)["modul"]
    felder = [("timeopen", 0), ("timeclose", 0), ("timelimit", 60 * int(a.get("zeit_minuten", 0))),
              ("overduehandling", "autosubmit"), ("graceperiod", 0),
              # Wiederholen einer Frage im selben Versuch nur in Tests ohne Sterne (Übungstest, Generalprobe; Testpaare mit
              # rolle test/test2 zählen als Sternetests), sonst holt „Weitere Frage dieser Art“ die volle Sternzahl (Sichtprüfung LS 3)
              ("canredoquestions", 1 if verhalten == "interactive" and not a.get("sterne") and not a.get("rolle") else 0),
              ("preferredbehaviour", verhalten), ("attempts_number", int(a.get("versuche", 0))),
              ("attemptonlast", 0), ("grademethod", BEWERTUNGSMETHODE[a.get("bewertungsmethode", "hoechste")]),
              ("decimalpoints", 2), ("questiondecimalpoints", -1),
              ("reviewattempt", 69888), ("reviewcorrectness", bewertung_zeigen), ("reviewmarks", bewertung_zeigen),
              ("reviewspecificfeedback", bewertung_zeigen), ("reviewgeneralfeedback", bewertung_zeigen),
              ("reviewrightanswer", sicht if a.get("richtige_antwort_zeigen", True) else 0), ("reviewoverallfeedback", 4352),
              ("questionsperpage", 1), ("navmethod", "free"), ("shuffleanswers", 1),
              ("sumgrades", f"{summe:.5f}"), ("grade", f"{b.punkte(r):.5f}"),
              ("timecreated", b.jetzt), ("timemodified", b.jetzt), ("password", ""),
              ("subnet", ""), ("browsersecurity", "securewindow" if a.get("vollbild") else "-"),
              ("delay1", 0), ("delay2", 0), ("showuserpicture", 0), ("showblocks", 0),
              ("completionattemptsexhausted", abschluss.get("completionattemptsexhausted", 0)),
              ("completionminattempts", 0), ("allowofflineattempts", 0)]
    intro = b.bilder(a.get("beschreibung", ""), a.get("dateien"), r, "mod_quiz", "intro")
    return (f'  <quiz id="{r.instance}">\n    {el("name", a["name"])}\n{_intro(a, intro)}'
            + "".join(f"    {el(n, v)}\n" for n, v in felder)
            + f"    <question_instances>\n{instanzen}\n    </question_instances>\n"
            f'    <sections>\n      <section id="{b.ids("slot")}">\n        <firstslot>1</firstslot>\n'
            "        <heading></heading>\n        <shufflequestions>0</shufflequestions>\n"
            "      </section>\n    </sections>\n    <overrides>\n    </overrides>\n"
            "    <grades>\n    </grades>\n    <attempts>\n    </attempts>\n  </quiz>")


def _datenvorlagen(felder: list) -> dict:
    """Listen-, Einzel- und Eingabevorlage: die Einträge als Tabelle."""
    namen = [f["name"] for f in felder]
    kopf = "".join(f"<th>{x(n)}</th>" for n in namen)
    zellen = "".join(f"<td>[[{n}]]</td>" for n in namen)
    einzeln = "".join(f'<tr><th scope="row">{x(n)}</th><td>[[{n}]]</td></tr>'
                      for n in namen)
    eingabe = "".join(
        f'<tr><th scope="row"><label for="[[{f["name"]}#id]]">{x(f["name"])}</label>'
        f"</th><td>[[{f['name']}]]"
        + (f'<br><small class="text-muted">{x(f["beschreibung"])}</small>'
           if f.get("beschreibung") else "") + "</td></tr>" for f in felder)
    return {
        "listtemplateheader": ('<table class="table table-striped table-sm"><thead><tr>'
                               f"{kopf}<th>Eingetragen von</th><th></th></tr></thead><tbody>"),
        "listtemplate": f"<tr>{zellen}<td>##user##</td><td>##actionsmenu##</td></tr>",
        "listtemplatefooter": "</tbody></table>",
        "singletemplate": ('<table class="table table-sm"><tbody>' + einzeln
                           + '<tr><th scope="row">Eingetragen von</th><td>##user## '
                           "(##timeadded##)</td></tr></tbody></table>"
                           "<div>##actionsmenu##</div>"),
        "addtemplate": f'<table class="table table-sm"><tbody>{eingabe}</tbody></table>',
    }


#: param1 … param10 je Feldtyp (übrige NULL). text: param1 = Autolink aus; number: param1 = Nachkommastellen
#: (0, field/number/field.class.php); textarea: param2 Spalten, param3 Zeilen, param5 Dateigröße
#: (0 = Vorgabe der Website); menu und checkbox: param1 = Optionen, eine je Zeile (datenfeld_params).
DATENFELD_PARAMS = {"text": {1: "0"}, "number": {1: "0"},
                    "textarea": {1: "0", 2: "60", 3: "8", 5: "0"}, "menu": {}, "checkbox": {}}


def datenfeld_params(f: dict) -> dict:
    """param1 … param10 eines Datenbankfelds; Auswahlfelder tragen ihre Optionen in param1."""
    if f["typ"] in kd.DATENFELDER_AUSWAHL:
        return {1: "\n".join(f["optionen"])}
    return DATENFELD_PARAMS[f["typ"]]


def b_data(b: Bau, r: Akt) -> str:
    a = r.akt
    felder = [dict(f, typ=f.get("typ", "text"), name=str(f["name"]).strip())
              for f in a["felder"]]
    vorlagen = {"csstemplate": "", "jstemplate": "", "asearchtemplate": "", "rsstemplate": "",
                "rsstitletemplate": "", **_datenvorlagen(felder), **(a.get("vorlagen") or {})}
    abschluss = b._abschluss(r)["modul"]
    feld_xml = "".join(
        f'      <field id="{b.ids("misc")}">\n        {el("type", f["typ"])}\n'
        f"        {el('name', f['name'])}\n"
        f"        {el('description', f.get('beschreibung', ''))}\n"
        f"        {el('required', 1 if f.get('pflicht') else 0)}\n"
        + "".join(f"        {el(f'param{i}', datenfeld_params(f).get(i))}\n"
                  for i in range(1, 11))
        + "      </field>\n" for f in felder)
    # Reihenfolge wie backup_data_stepslib.php; keine Bewertung (assessed 0),
    # Einträge sofort sichtbar (approval 0) oder erst nach Freigabe (freigabe).
    werte = [("comments", 0), ("timeavailablefrom", 0), ("timeavailableto", 0),
             ("timeviewfrom", 0), ("timeviewto", 0), ("requiredentries", 0),
             ("requiredentriestoview", 0), ("maxentries", 0), ("rssarticles", 0),
             ("singletemplate", vorlagen["singletemplate"]),
             ("listtemplate", vorlagen["listtemplate"]),
             ("listtemplateheader", vorlagen["listtemplateheader"]),
             ("listtemplatefooter", vorlagen["listtemplatefooter"]),
             ("addtemplate", vorlagen["addtemplate"]), ("rsstemplate", vorlagen["rsstemplate"]),
             ("rsstitletemplate", vorlagen["rsstitletemplate"]), ("csstemplate", vorlagen["csstemplate"]),
             ("jstemplate", vorlagen["jstemplate"]), ("asearchtemplate", vorlagen["asearchtemplate"]),
             ("approval", 1 if a.get("freigabe") else 0),
             ("manageapproved", 1 if a.get("bearbeiten_nach_freigabe", True) else 0),
             ("scale", 0), ("assessed", 0), ("assesstimestart", 0),
             ("assesstimefinish", 0), ("defaultsort", 0), ("defaultsortdir", 0),
             ("editany", 0), ("notification", 0), ("timemodified", b.jetzt),
             ("config", None),
             ("completionentries", abschluss.get("completionentries", 0))]
    return (f'  <data id="{r.instance}">\n    {el("name", a["name"])}\n{_intro(a)}'
            + "".join(f"    {el(n, v)}\n" for n, v in werte)
            + f"    <fields>\n{feld_xml}    </fields>\n"
            "    <records>\n    </records>\n    <recordstags>\n    </recordstags>\n  </data>")


BAUER = {"page": b_page, "label": b_label, "resource": b_resource,
         "folder": b_folder, "url": b_url, "assign": b_assign,
         "feedback": b_feedback, "glossary": b_glossary, "quiz": b_quiz,
         "data": b_data}


def baue(kursdef: dict, dateien_wurzel: Path, ziel_mbz: Path) -> Path:
    """Kursdefinition prüfen, Sicherung bauen und schreiben. Insel-Platzhalter (inseln.py) werden vorher in die
    Kursdefinition eingesetzt (in place)."""
    inseln.einsetzen(kursdef)
    stufen.einsetzen(kursdef)             # differenzierte Aufgaben je Kachel (stufen.py)
    kd.pruefe_oder_abbrechen(kursdef, dateien_wurzel)
    daten = Bau(kursdef, Path(dateien_wurzel)).baue()
    ziel = Path(ziel_mbz)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_bytes(daten)
    return ziel


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Kurssicherung (.mbz) bauen")
    p.add_argument("kurs", type=Path)
    p.add_argument("--dateien", type=Path, help="Wurzel der Dateien (Vorgabe: Ordner der JSON)")
    p.add_argument("--ziel", type=Path, required=True)
    arg = p.parse_args()
    kurs = json.loads(arg.kurs.read_text(encoding="utf-8"))
    print(baue(kurs, arg.dateien or arg.kurs.parent, arg.ziel))
