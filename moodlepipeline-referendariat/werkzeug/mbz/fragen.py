"""Fragen eines Tests als Moodle-Fragen-XML (questions.xml).

Jeder Test hat eine eigene Fragensammlung im Modulkontext (Kategorie „top“ und
darunter eine Kategorie mit den Fragen), wie Moodle 4/5 sie für Test-eigene
Fragen sichert. Feldnamen und Reihenfolge folgen den Backup-Klassen
`backup_qtype_<typ>_plugin` (gegen Moodle 5.1.6 erprobte Vorlage).
"""
from __future__ import annotations

import random
from decimal import Decimal
from pathlib import Path

from xmlhilfe import NULL, el, x

SITE = "moodle.example.org"
E = "                "  # Einzug im Fragen-Block


def datensaetze(q: dict) -> list[dict]:
    """Zufallswerte einer calculated-Frage; fest geseedet über Name und Formel,
    damit zwei Bauläufe dieselbe Sicherung ergeben."""
    rnd = random.Random(f"{q.get('name')}|{q.get('formel')}")
    saetze = []
    for _ in range(int(q.get("anzahl_datensaetze", 10))):
        satz = {}
        for v in q["variablen"]:
            nk = int(v.get("nachkommastellen", 0))
            satz[v["name"]] = round(rnd.uniform(float(v["min"]), float(v["max"])), nk)
        saetze.append(satz)
    return saetze


def _kategorie(cid: int, name: str, ctx: int, cmid: int, eltern: int,
               sort: int, eintraege: str) -> str:
    return (f'  <question_category id="{cid}">\n    {el("name", name)}\n'
            f"    {el('contextid', ctx)}\n    <contextlevel>70</contextlevel>\n"
            f"    {el('contextinstanceid', cmid)}\n    <info></info>\n"
            f"    <infoformat>0</infoformat>\n    <stamp>{SITE}+cat{cid}</stamp>\n"
            f"    {el('parent', eltern)}\n    {el('sortorder', sort)}\n"
            f"    <idnumber>{NULL}</idnumber>\n    <question_bank_entries>\n"
            f"{eintraege}    </question_bank_entries>\n  </question_category>")


def registrieren(b, r, fragen: list[dict]) -> list[tuple[int, float]]:
    """Fragen des Tests anlegen; liefert (question_bank_entry-Id, Punkte) je Platz."""
    top, kat = b.ids("qcat"), b.ids("qcat")
    b.fragekategorien.append(_kategorie(top, "top", r.ctx, r.cmid, 0, 0, ""))
    eintraege, slots = [], []
    for q in fragen:
        qbe, qver, qid = b.ids("qbe"), b.ids("qver"), b.ids("question")
        eintraege.append(
            f'      <question_bank_entry id="{qbe}">\n'
            f"        {el('questioncategoryid', kat)}\n"
            f"        {el('idnumber', q.get('idnummer'))}\n        <ownerid>2</ownerid>\n"
            f'        <question_version>\n          <question_versions id="{qver}">\n'
            "            <version>1</version>\n            <status>ready</status>\n"
            f"            <questions>\n{frage_xml(b, r, q, qid)}\n            </questions>\n"
            "          </question_versions>\n        </question_version>\n"
            "      </question_bank_entry>\n")
        slots.append((qbe, float(q.get("punkte", 1))))
    b.fragekategorien.append(_kategorie(kat, f"Fragen: {r.akt['name']}", r.ctx,
                                        r.cmid, top, 999, "".join(eintraege)))
    r.qcatrefs = [top, kat]
    return slots


def frage_xml(b, r, q: dict, qid: int) -> str:
    typ = q["typ"]
    # Bilder im Fragetext (dateien): Dateibereich question/questiontext der Frage im Kontext des Tests
    text, ids = b.einbetten(q["text"], q.get("dateien"), r.ctx, "question", "questiontext", qid)
    r.filerefs += ids
    kopf = (f'              <question id="{qid}">\n{E}<parent>0</parent>\n'
            f"{E}{el('name', q['name'])}\n{E}{el('questiontext', text)}\n"
            f"{E}<questiontextformat>1</questiontextformat>\n"
            f"{E}{el('generalfeedback', q.get('allgemeines_feedback', ''))}\n"
            f"{E}<generalfeedbackformat>1</generalfeedbackformat>\n"
            f"{E}<defaultmark>{float(q.get('punkte', 1)):.7f}</defaultmark>\n"
            f"{E}<penalty>0.3333333</penalty>\n{E}{el('qtype', typ)}\n"
            f"{E}<length>1</length>\n{E}<stamp>{SITE}+q{qid}</stamp>\n"
            f"{E}{el('timecreated', b.jetzt)}\n{E}{el('timemodified', b.jetzt)}\n"
            f"{E}<createdby>2</createdby>\n{E}<modifiedby>2</modifiedby>\n")
    plugin = TYPEN[typ](b, r, q, qid)
    fuss = (f"{E}<plugin_qbank_comment_question>\n{E}  <comments>\n{E}  </comments>\n"
            f"{E}</plugin_qbank_comment_question>\n"
            f"{E}<plugin_qbank_customfields_question>\n{E}  <customfields>\n"
            f"{E}  </customfields>\n{E}</plugin_qbank_customfields_question>\n"
            f"{E}<question_hints>\n{_hinweise(b, q)}{E}</question_hints>\n"
            + b._tags(q.get("tags"), E, ctx=r.ctx) + "              </question>")
    return kopf + plugin + fuss


def _hinweise(b, q: dict) -> str:
    """Hinweise je Frage (`hinweise` [HTML]): im Verhalten „interactive“ ein weiterer Versuch je Hinweis, der Hinweis
    erscheint nach einer falschen Antwort (Moodle question_hints)."""
    return "".join(f'{E}  <question_hint id="{b.ids("misc")}">\n{E}    {el("hint", h)}\n'
                   f"{E}    <hintformat>1</hintformat>\n{E}    <shownumcorrect>{NULL}</shownumcorrect>\n"
                   f"{E}    <clearwrong>0</clearwrong>\n{E}    <options>{NULL}</options>\n{E}  </question_hint>\n"
                   for h in q.get("hinweise") or [])


def _antwort(b, text, anteil: float, feedback="", fmt=1, fbfmt=1) -> str:
    return (f'{E}    <answer id="{b.ids("answer")}">\n{E}      {el("answertext", text)}\n'
            f"{E}      <answerformat>{fmt}</answerformat>\n"
            f"{E}      <fraction>{anteil:.7f}</fraction>\n{E}      {el('feedback', feedback)}\n"
            f"{E}      <feedbackformat>{fbfmt}</feedbackformat>\n{E}    </answer>\n")


def _block(typ: str, innen: str) -> str:
    return f"{E}<plugin_qtype_{typ}_question>\n{innen}{E}</plugin_qtype_{typ}_question>\n"


def _rueckmeldung(q: dict, anzahl: bool = True) -> str:
    """Sammelrückmeldung (alle Felder NOT NULL ohne Vorgabe)."""
    return (f"{E}    {el('shuffleanswers', 1 if q.get('mischen', True) else 0)}\n"
            f"{E}    {el('correctfeedback', q.get('feedback_richtig', ''))}\n"
            f"{E}    <correctfeedbackformat>1</correctfeedbackformat>\n"
            f"{E}    {el('partiallycorrectfeedback', q.get('feedback_teilweise', ''))}\n"
            f"{E}    <partiallycorrectfeedbackformat>1</partiallycorrectfeedbackformat>\n"
            f"{E}    {el('incorrectfeedback', q.get('feedback_falsch', ''))}\n"
            f"{E}    <incorrectfeedbackformat>1</incorrectfeedbackformat>\n"
            + (f"{E}    <shownumcorrect>1</shownumcorrect>\n" if anzahl else ""))


def anteile(antworten: list[dict]) -> tuple[int, list[float]]:
    """(single, Anteile): Einfachwahl 1/0; Mehrfachwahl richtig 1/n, falsch −1/m."""
    richtig = sum(1 for a in antworten if a.get("richtig"))
    falsch = len(antworten) - richtig
    if richtig <= 1:
        return 1, [1.0 if a.get("richtig") else 0.0 for a in antworten]
    return 0, [round(1 / richtig, 7) if a.get("richtig")
               else (-round(1 / falsch, 7) if falsch else 0.0) for a in antworten]


def q_multichoice(b, r, q, qid) -> str:
    single, fr = anteile(q["antworten"])
    ans = "".join(_antwort(b, a["text"], f, a.get("feedback", ""))
                  for a, f in zip(q["antworten"], fr))
    return _block("multichoice", (
        f"{E}  <answers>\n{ans}{E}  </answers>\n"
        f'{E}  <multichoice id="{qid}">\n{E}    <layout>0</layout>\n'
        f"{E}    {el('single', single)}\n" + _rueckmeldung(q, anzahl=False)
        + f"{E}    <answernumbering>abc</answernumbering>\n"
        f"{E}    <shownumcorrect>1</shownumcorrect>\n"
        f"{E}    <showstandardinstruction>1</showstandardinstruction>\n"
        f"{E}  </multichoice>\n"))


def q_truefalse(b, r, q, qid) -> str:
    richtig = q["richtig"]
    fb_r, fb_f = q.get("feedback_richtig", ""), q.get("feedback_falsch", "")
    wahr = _antwort(b, "True", 1.0 if richtig else 0.0, fb_r if richtig else fb_f, fmt=0)
    falsch = _antwort(b, "False", 0.0 if richtig else 1.0, fb_f if richtig else fb_r, fmt=0)
    wahr_id = wahr.split('"')[1]
    falsch_id = falsch.split('"')[1]
    return _block("truefalse", (
        f"{E}  <answers>\n{wahr}{falsch}{E}  </answers>\n"
        f'{E}  <truefalse id="{qid}">\n{E}    <trueanswer>{wahr_id}</trueanswer>\n'
        f"{E}    <falseanswer>{falsch_id}</falseanswer>\n"
        f"{E}    <showstandardinstruction>1</showstandardinstruction>\n{E}  </truefalse>\n"))


def q_shortanswer(b, r, q, qid) -> str:
    ans = "".join(_antwort(b, a["text"], float(a.get("anteil", 100)) / 100,
                           a.get("feedback", ""), fmt=0) for a in q["antworten"])
    return _block("shortanswer", (
        f"{E}  <answers>\n{ans}{E}  </answers>\n"
        f'{E}  <shortanswer id="{qid}">\n'
        f"{E}    {el('usecase', 1 if q.get('gross_klein') else 0)}\n{E}  </shortanswer>\n"))


def _einheitenlos() -> str:
    return (f"{E}  <numerical_units>\n{E}  </numerical_units>\n"
            f"{E}  <numerical_options>\n"
            f'{E}    <numerical_option id="{{oid}}">\n{E}      <showunits>3</showunits>\n'
            f"{E}      <unitsleft>0</unitsleft>\n{E}      <unitgradingtype>0</unitgradingtype>\n"
            f"{E}      <unitpenalty>0.1000000</unitpenalty>\n{E}    </numerical_option>\n"
            f"{E}  </numerical_options>\n")


def _zahl(wert) -> str:
    """Zahl ohne Exponent (0.0000025 statt 2.5e-06; Moodle zeigt den Text als richtige Antwort)."""
    if not isinstance(wert, float):
        return str(wert)
    text = format(Decimal(repr(wert)), "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def q_numerical(b, r, q, qid) -> str:
    ans, recs = "", ""
    for a in q["antworten"]:
        xml = _antwort(b, _zahl(a["wert"]), float(a.get("anteil", 100)) / 100,
                       a.get("feedback", ""), fmt=0)
        aid = xml.split('"')[1]
        ans += xml
        recs += (f'{E}    <numerical_record id="{b.ids("misc")}">\n{E}      <answer>{aid}</answer>\n'
                 f"{E}      {el('tolerance', a.get('toleranz', 0))}\n{E}    </numerical_record>\n")
    return _block("numerical", (
        f"{E}  <answers>\n{ans}{E}  </answers>\n"
        + _einheitenlos().replace("{oid}", str(b.ids("misc")))
        + f"{E}  <numerical_records>\n{recs}{E}  </numerical_records>\n"))


def q_calculated(b, r, q, qid) -> str:
    xml = _antwort(b, q["formel"], 1.0, q.get("antwort_feedback", ""), fmt=0)
    aid = xml.split('"')[1]
    saetze = datensaetze(q)
    defs = ""
    for v in q["variablen"]:
        nk = int(v.get("nachkommastellen", 0))
        bereich = f"uniform:{v['min']}:{v['max']}:{nk}"
        items = "".join(
            f'{E}      <dataset_item id="{b.ids("datasetitem")}">\n'
            f"{E}        {el('number', nr)}\n"
            f"{E}        {el('value', f'{float(s[v['name']]):.{nk}f}')}\n{E}      </dataset_item>\n"
            for nr, s in enumerate(saetze, start=1))
        defs += (f'{E}  <dataset_definition id="{b.ids("dataset")}">\n'
                 f"{E}    <category>0</category>\n{E}    {el('name', v['name'])}\n"
                 f"{E}    <type>1</type>\n"
                 f"{E}    {el('options', bereich)}\n"
                 f"{E}    {el('itemcount', len(saetze))}\n"
                 f"{E}    <dataset_items>\n{items}{E}    </dataset_items>\n"
                 f"{E}  </dataset_definition>\n")
    return _block("calculated", (
        f"{E}  <answers>\n{xml}{E}  </answers>\n"
        + _einheitenlos().replace("{oid}", str(b.ids("misc")))
        + f"{E}  <dataset_definitions>\n{defs}{E}  </dataset_definitions>\n"
        f"{E}  <calculated_records>\n"
        f'{E}    <calculated_record id="{b.ids("misc")}">\n{E}      <answer>{aid}</answer>\n'
        f"{E}      <tolerance>{float(q.get('toleranz', 0.01)):.7f}</tolerance>\n"
        f"{E}      <tolerancetype>1</tolerancetype>\n"
        f"{E}      {el('correctanswerlength', int(q.get('nachkommastellen', 2)))}\n"
        f"{E}      <correctanswerformat>1</correctanswerformat>\n{E}    </calculated_record>\n"
        f"{E}  </calculated_records>\n{E}  <calculated_options>\n"
        f'{E}    <calculated_option id="{b.ids("misc")}">\n{E}      <synchronize>0</synchronize>\n'
        f"{E}      <single>1</single>\n{E}      <shuffleanswers>1</shuffleanswers>\n"
        f"{E}      <correctfeedback></correctfeedback>\n{E}      <correctfeedbackformat>1</correctfeedbackformat>\n"
        f"{E}      <partiallycorrectfeedback></partiallycorrectfeedback>\n"
        f"{E}      <partiallycorrectfeedbackformat>1</partiallycorrectfeedbackformat>\n"
        f"{E}      <incorrectfeedback></incorrectfeedback>\n{E}      <incorrectfeedbackformat>1</incorrectfeedbackformat>\n"
        f"{E}      <answernumbering>abc</answernumbering>\n{E}      <shownumcorrect>1</shownumcorrect>\n"
        f"{E}    </calculated_option>\n{E}  </calculated_options>\n"))


def q_match(b, r, q, qid) -> str:
    paare = [(p["frage"], p["antwort"]) for p in q["paare"]]
    paare += [("", t) for t in q.get("ablenker", [])]  # linke Seite leer = Ablenker
    zeilen = "".join(
        f'{E}    <match id="{b.ids("answer")}">\n{E}      {el("questiontext", f)}\n'
        f"{E}      <questiontextformat>1</questiontextformat>\n"
        f"{E}      {el('answertext', a)}\n{E}    </match>\n" for f, a in paare)
    return _block("match", (
        f'{E}  <matchoptions id="{b.ids("misc")}">\n' + _rueckmeldung(q)
        + f"{E}  </matchoptions>\n{E}  <matches>\n{zeilen}{E}  </matches>\n"))


def q_ordering(b, r, q, qid) -> str:
    ans = "".join(_antwort(b, t, float(pos), "", fmt=1, fbfmt=0)
                  for pos, t in enumerate(q["elemente"], start=1))  # fraction = Position
    return _block("ordering", (
        f"{E}  <answers>\n{ans}{E}  </answers>\n"
        f'{E}  <ordering id="{b.ids("misc")}">\n{E}    <layouttype>0</layouttype>\n'
        f"{E}    <selecttype>0</selecttype>\n{E}    <selectcount>0</selectcount>\n"
        f"{E}    <gradingtype>0</gradingtype>\n{E}    <showgrading>1</showgrading>\n"
        f"{E}    <numberingstyle>none</numberingstyle>\n"
        f"{E}    {el('correctfeedback', q.get('feedback_richtig', ''))}\n"
        f"{E}    <correctfeedbackformat>1</correctfeedbackformat>\n"
        f"{E}    {el('incorrectfeedback', q.get('feedback_falsch', ''))}\n"
        f"{E}    <incorrectfeedbackformat>1</incorrectfeedbackformat>\n"
        f"{E}    {el('partiallycorrectfeedback', q.get('feedback_teilweise', ''))}\n"
        f"{E}    <partiallycorrectfeedbackformat>1</partiallycorrectfeedbackformat>\n"
        f"{E}    <shownumcorrect>1</shownumcorrect>\n{E}  </ordering>\n"))


def _ziehoption(gruppe, unendlich: bool) -> str:
    """Gruppe und `infinite` eines ddwtos-Worts, PHP-serialisiert im Feld feedback."""
    g = str(gruppe)
    return ('O:8:"stdClass":2:{s:9:"draggroup";s:%d:"%s";s:8:"infinite";b:%d;}'
            % (len(g.encode()), g, 1 if unendlich else 0))


def q_ddwtos(b, r, q, qid) -> str:
    ans = "".join(_antwort(b, w["text"], 0.0, _ziehoption(w.get("gruppe", 1),
                                                          w.get("unendlich", False)),
                           fmt=1, fbfmt=0) for w in q["woerter"])
    return _block("ddwtos", (f"{E}  <answers>\n{ans}{E}  </answers>\n"
                             f'{E}  <ddwtos id="{qid}">\n' + _rueckmeldung(q)
                             + f"{E}  </ddwtos>\n"))


def q_gapselect(b, r, q, qid) -> str:
    # Die Gruppe steht als nackte Zahl im Feld feedback.
    ans = "".join(_antwort(b, w["text"], 0.0, str(int(w.get("gruppe", 1))), fmt=1, fbfmt=0)
                  for w in q["auswahl"])
    return _block("gapselect", (f"{E}  <answers>\n{ans}{E}  </answers>\n"
                                f'{E}  <gapselect id="{b.ids("misc")}">\n' + _rueckmeldung(q)
                                + f"{E}  </gapselect>\n"))


def _hintergrund(b, r, q, qid, typ) -> None:
    rel = q["bild"]
    r.filerefs += b.ablegen(r.ctx, f"qtype_{typ}", "bgimage", qid, b.lies(rel), Path(rel).name)


def q_ddmarker(b, r, q, qid) -> str:
    _hintergrund(b, r, q, qid, "ddmarker")
    drags = "".join(
        f'{E}    <drag id="{b.ids("drag")}">\n{E}      {el("no", nr)}\n'
        f"{E}      {el('infinite', 1 if m.get('unendlich') else 0)}\n"
        f"{E}      {el('label', m['text'])}\n{E}      {el('noofdrags', int(m.get('anzahl', 1)))}\n"
        f"{E}    </drag>\n" for nr, m in enumerate(q["markierungen"], start=1))
    drops = "".join(
        f'{E}    <drop id="{b.ids("drop")}">\n{E}      {el("no", nr)}\n'
        f"{E}      {el('shape', z['form'])}\n{E}      {el('coords', z['koordinaten'])}\n"
        f"{E}      {el('choice', int(z['markierung']))}\n{E}    </drop>\n"
        for nr, z in enumerate(q["zonen"], start=1))
    return _block("ddmarker", (
        f'{E}  <ddmarker id="{qid}">\n' + _rueckmeldung(q)
        + f"{E}    {el('showmisplaced', 1 if q.get('falsche_zeigen') else 0)}\n"
        f"{E}  </ddmarker>\n{E}  <drags>\n{drags}{E}  </drags>\n"
        f"{E}  <drops>\n{drops}{E}  </drops>\n"))


def q_ddimageortext(b, r, q, qid) -> str:
    _hintergrund(b, r, q, qid, "ddimageortext")
    drags = "".join(
        f'{E}    <drag id="{b.ids("drag")}">\n{E}      {el("no", nr)}\n'
        f"{E}      {el('draggroup', o.get('gruppe', 1))}\n"
        f"{E}      {el('infinite', 1 if o.get('unendlich') else 0)}\n"
        f"{E}      {el('label', o['text'])}\n{E}    </drag>\n"
        for nr, o in enumerate(q["ziehobjekte"], start=1))
    drops = "".join(
        f'{E}    <drop id="{b.ids("drop")}">\n{E}      {el("no", nr)}\n'
        f"{E}      {el('xleft', int(z['x']))}\n{E}      {el('ytop', int(z['y']))}\n"
        f"{E}      {el('choice', int(z['objekt']))}\n{E}      {el('label', z.get('text', ''))}\n"
        f"{E}    </drop>\n" for nr, z in enumerate(q["zonen"], start=1))
    return _block("ddimageortext", (
        f'{E}  <ddimageortext id="{qid}">\n' + _rueckmeldung(q)
        + f"{E}    {el('dropzonevisibility', 1 if q.get('zonen_sichtbar') else 0)}\n"
        f"{E}  </ddimageortext>\n{E}  <drags>\n{drags}{E}  </drags>\n"
        f"{E}  <drops>\n{drops}{E}  </drops>\n"))


TYPEN = {"multichoice": q_multichoice, "truefalse": q_truefalse,
         "shortanswer": q_shortanswer, "numerical": q_numerical,
         "calculated": q_calculated, "match": q_match, "ordering": q_ordering,
         "ddwtos": q_ddwtos, "gapselect": q_gapselect, "ddmarker": q_ddmarker,
         "ddimageortext": q_ddimageortext}
