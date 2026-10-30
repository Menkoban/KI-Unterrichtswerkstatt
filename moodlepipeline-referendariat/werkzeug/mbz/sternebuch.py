"""Sternebuch: Sterne eintauschen, verschenken, Klassenbelohnungen (Lehrkraft 2026-10-25, Profil moodle.sternebuch).

Das Sternebuch ist eine Datenbank-Aktivität (Moodle-Kern, mod_data) mit eigenen Vorlagen und dem Skript
`sternebuch.js` (Vorlage „JavaScript“). Eine Buchung ist ein Eintrag mit den Feldern

    Art         Auswahl: für mich eintauschen | verschenken | Anteil an einer Klassenbelohnung | Helfer-Stern
    Belohnung   Text (Name aus der Preisliste; das Skript bietet eine Auswahl an)
    Sterne      Zahl (Preis, Anteil oder verschenkte Sterne; beim Verschenken kommt die Hälfte an)
    Empfänger   Text „Vorname Name (#Nutzer-Id)“ (das Skript bietet die Teilnehmenden zur Auswahl an)
    Ausgegeben  Ankreuzfeld der Lehrkraft (Belohnung übergeben)

Jede Buchung gilt erst mit der Freigabe der Lehrkraft (Genehmigung der Datenbank); freigegebene Buchungen kann nur
noch die Lehrkraft ändern (`bearbeiten_nach_freigabe` false). Das Skript liest alles mit der Sitzung der Person,
die die Seite ansieht (keine Lehrkraftrechte, kein Schlüssel im Quelltext). Rechnung wie in sternebuch.js:

    verdient   = Kursgesamt je Themenkurs (Summe der Sterne, sterne.kursgesamt_max), über alle Themenkurse
    Kontostand = verdient + erhalten − verschenkt − eingetauscht − Anteile an Klassenbelohnungen
    erhalten   = Hälfte der geschenkten Sterne (abgerundet: 10 ab, 5 an, 5 verfallen) + Helfer-Sterne

Preise, Klassenbelohnungen und die zählenden Themenkurse stehen in der Seite „Preisliste“ (`preisliste_seite`):
Tabellen, die die Lehrkraft im Editor ändert, ohne Neubau; das Skript liest sie bei jedem Aufruf. Die Medaillen
der Themenkurse richten sich weiter nach den verdienten Sternen.

    db = datenbank(themenkurse=[{"name": "LS 1", "kurzname": "…"}])
    seite = preisliste_seite(fuer_mich=[("Hilfe-Joker", 5, "")], klasse=[("Frühstück", 60, 30, "")],
                             themenkurse=[…])
"""
from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path

from xmlhilfe import x

JS_DATEI = Path(__file__).with_name("sternebuch.js")
KONFIG = re.compile(r"/\*KONFIG\*/(.*?)/\*/KONFIG\*/", re.S)
IDNUMMER = "sternebuch"
ARTEN = {"eintauschen": "für mich eintauschen", "verschenken": "verschenken",
         "anteil": "Anteil an einer Klassenbelohnung", "helfer": "Helfer-Stern"}
FELDER = {"art": "Art", "belohnung": "Belohnung", "sterne": "Sterne", "empfaenger": "Empfänger",
          "ausgegeben": "Ausgegeben"}
#: Moodle-Rolle der Lernenden (Id der Archetyp-Rolle „student“ in einer Standard-Installation)
LERNENDENROLLE = 5
#: Kopfzeilen der Preisliste; das Skript erkennt die Tabellen an diesen Wörtern (sternebuch.js, preiseLesen)
KOPF_FUER_MICH = ("Belohnung", "Sterne", "Hinweis")
KOPF_KLASSE = ("Belohnung", "Jede Person hat mindestens", "Anteil je Person", "Hinweis")
KOPF_KURSE = ("Lernsituation", "Kurzname")
FARBEN = ("#08349C", "#7DDE78")      # Vorgabe wie allgemein.SCHULFARBEN; der Kurs gibt seine eigenen mit


def skript(konfig: dict) -> str:
    """sternebuch.js mit eingesetzter Konfiguration (JSON zwischen den Markierungen)."""
    quelle = JS_DATEI.read_text(encoding="utf-8")
    if not KONFIG.search(quelle):
        raise ValueError("sternebuch.js: Markierung /*KONFIG*/ … /*/KONFIG*/ fehlt")
    json_text = json.dumps(konfig, ensure_ascii=False, indent=8)
    return KONFIG.sub(lambda _: f"/*KONFIG*/{json_text}/*/KONFIG*/", quelle, count=1)


def konfig_aus(js: str) -> dict | None:
    """Die eingesetzte Konfiguration eines Sternebuch-Skripts (None ohne Markierung)."""
    m = KONFIG.search(js or "")
    return json.loads(m.group(1)) if m else None


def _vorlagen(farben: tuple[str, str]) -> dict:
    """Listen-, Einzel- und Eingabevorlage mit den Klassen, die sternebuch.js liest (sb-…), und das CSS."""
    f = FELDER
    zellen = "".join(f'<td class="sb-{k}">[[{f[k]}]]</td>' for k in ("art", "belohnung", "sterne", "empfaenger",
                                                                       "ausgegeben"))
    aktionen = ('<td class="sb-aktionen"><span class="sb-id" hidden>##id##</span>'
                "##approve## ##disapprove## ##edit## ##delete## ##delcheck##</td>")
    kopf = "".join(f'<th scope="col">{x(t)}</th>' for t in (
        "Art", "Belohnung", "Sterne", "Empfänger", "Ausgegeben", "Von", "Gebucht", "Freigabe", "Aktionen"))
    einzeln = "".join(f'<tr><th scope="row">{x(f[k])}</th><td class="sb-{k}">[[{f[k]}]]</td></tr>'
                      for k in ("art", "belohnung", "sterne", "empfaenger", "ausgegeben"))
    beschriftung = {"art": "Art der Buchung", "belohnung": "Belohnung", "empfaenger": "An wen",
                    "sterne": "Sterne", "ausgegeben": "Ausgegeben (nur die Lehrkraft)"}
    eingabe = "".join(
        f'<div class="sb-feld sb-feld-{k} mb-3">'
        + (f'<label for="[[{f[k]}#id]]">{x(beschriftung[k])}</label> ' if k != "ausgegeben"
           else f"<p>{x(beschriftung[k])}</p>")
        + f"[[{f[k]}]]</div>" for k in ("art", "belohnung", "empfaenger", "sterne", "ausgegeben"))
    blau, gruen = farben
    css = f""".sb {{ margin: 0 0 1.5rem 0; }}
.sb h3, .sb h4 {{ color: {blau}; }}
.sb-stand {{ background: #FFF4CC; color: #7A5A00; border: 1px solid #E0A800; border-radius: 6px; padding: 8px 12px; }}
.sb-gross {{ font-size: 1.6em; font-weight: bold; }}
.sb, .sb p, .sb td, .sb th, .sb li, .sb-formular {{ font-size: 16px; }}
.sb-klein {{ font-size: 16px; color: #444; }}
.sb table {{ width: 100%; max-width: 100%; }}
.sb td, .sb th {{ white-space: normal; overflow-wrap: anywhere; }}
.sb-liste-zu {{ display: none; }}
.sb-balken {{ background: #fff; border: 1px solid {blau}; border-radius: 6px; height: 14px; max-width: 32rem; }}
.sb-balken-fuellung {{ background: {gruen}; border-radius: 6px; height: 12px; }}
.sb-warnung {{ color: #8A1C1C; }}
.sb-ok {{ color: #1E5E1A; font-weight: bold; }}
.sb-tabelle caption {{ caption-side: top; color: {blau}; font-weight: bold; }}
.sb-meldung {{ margin-bottom: 1rem; }}
"""
    return {
        "listtemplateheader": ('<table class="table table-sm sb-liste"><caption>Alle Buchungen</caption>'
                               f"<thead><tr>{kopf}</tr></thead><tbody>"),
        "listtemplate": (f'<tr class="sb-eintrag ##approvalstatusclass##">{zellen}<td class="sb-von">##user##</td>'
                         '<td class="sb-zeit">##timeadded##</td><td class="sb-status">##approvalstatus##</td>'
                         f"{aktionen}</tr>"),
        "listtemplatefooter": "</tbody></table>",
        "singletemplate": ('<table class="table table-sm"><tbody>' + einzeln
                           + '<tr><th scope="row">Von</th><td>##user## (##timeadded##)</td></tr>'
                           '<tr><th scope="row">Freigabe</th><td>##approvalstatus##</td></tr></tbody></table>'
                           "<div>##actionsmenu##</div>"),
        "addtemplate": f'<div class="sb-formular">{eingabe}</div>',
        "csstemplate": css,
    }


def datenbank(themenkurse: list[dict], *, name: str = "Sternebuch", preisliste: str = "Preisliste",
              helferstern: bool = True, klassenbalken: bool = True, verfall: str = "nie",
              farben: tuple[str, str] = FARBEN, beschreibung: str | None = None,
              lernendenrolle: int = LERNENDENROLLE) -> dict:
    """Datenbank-Aktivität „Sternebuch“ (Kursdefinition, typ data). `themenkurse`: [{name, kurzname}] als Rückfall,
    falls die Preisliste keine Tabelle „Kurzname“ hat; `preisliste`: Name der Seite mit den Preisen. Verfall der
    Sterne gibt es noch nicht (nur „nie“)."""
    if verfall != "nie":
        raise NotImplementedError(f"Verfall der Sterne {verfall!r}: bisher nur „nie“ (KONZEPT 2026-10-25)")
    for k in themenkurse:
        if not k.get("kurzname") or not k.get("name"):
            raise ValueError(f"Themenkurs {k!r}: name und kurzname nötig")
    arten = {k: v for k, v in ARTEN.items() if helferstern or k != "helfer"}
    konfig = {"preisliste": preisliste, "themenkurse": [{"name": k["name"], "kurzname": k["kurzname"]}
                                                        for k in themenkurse],
              "arten": arten, "felder": FELDER, "helferstern": helferstern, "klassenbalken": klassenbalken,
              "lernendenrolle": lernendenrolle}
    vorlagen = _vorlagen(farben)
    vorlagen["jstemplate"] = skript(konfig)
    return {
        "typ": "data", "name": name, "idnummer": IDNUMMER, "abschluss": "keine",
        "beschreibung": beschreibung if beschreibung is not None else (
            "<p>Hier sehen Sie Ihr Sternekonto über alle Themenkurse des Lernfelds und buchen Belohnungen. "
            "Jede Buchung gilt erst, wenn Ihre Lehrkraft sie freigegeben hat.</p>"),
        "felder": [
            {"name": FELDER["art"], "typ": "menu", "optionen": list(arten.values()), "pflicht": True},
            {"name": FELDER["belohnung"], "typ": "text"},
            {"name": FELDER["sterne"], "typ": "number", "pflicht": True},
            {"name": FELDER["empfaenger"], "typ": "text"},
            {"name": FELDER["ausgegeben"], "typ": "checkbox", "optionen": ["ja"]},
        ],
        "freigabe": True, "bearbeiten_nach_freigabe": False,
        "vorlagen": vorlagen,
    }


def _tabelle(beschriftung: str, kopf: tuple, zeilen: list) -> str:
    return (f'<table class="table"><caption>{x(beschriftung)}</caption><thead><tr>'
            + "".join(f'<th scope="col">{x(k)}</th>' for k in kopf) + "</tr></thead><tbody>"
            + "".join("<tr>" + "".join(f"<td>{x(z)}</td>" for z in zeile) + "</tr>" for zeile in zeilen)
            + "</tbody></table>")


def preisliste_seite(fuer_mich: list[tuple], klasse: list[tuple], themenkurse: list[dict], *,
                     name: str = "Preisliste", einleitung: str | None = None,
                     lernende: int | None = None) -> dict:
    """Seite „Preisliste“: Tabellen „Belohnungen für Sie“ (Belohnung, Sterne, Hinweis), „Belohnungen für die ganze
    Klasse“ (Belohnung, mindestens je Person, Anteil je Person, Hinweis) und „Diese Kurse zählen“ (Lernsituation,
    Kurzname; ein Kurs ohne kurzname fehlt, bis er gebaut ist). `lernende`: feste Zahl der Lernenden für die
    Klassenbelohnung (sonst zählt das Skript die Teilnehmenden mit der Rolle der Lernenden)."""
    for z in fuer_mich:
        if len(z) != 3 or not isinstance(z[1], int) or z[1] <= 0:
            raise ValueError(f"Belohnung {z!r}: (Name, Sterne > 0, Hinweis)")
    for z in klasse:
        if len(z) != 4 or not all(isinstance(n, int) and n > 0 for n in z[1:3]) or z[2] > z[1]:
            raise ValueError(f"Klassenbelohnung {z!r}: (Name, mindestens > 0, Anteil > 0 und ≤ mindestens, Hinweis)")
    kurse = [(k["name"], k["kurzname"]) for k in themenkurse if k.get("kurzname")]
    teile = [einleitung if einleitung is not None else
             "<p>Für Ihre Sterne gibt es Belohnungen. Buchen Sie sie im Sternebuch; jede Buchung gilt erst, wenn "
             "Ihre Lehrkraft sie freigegeben hat. Die Preise können sich ändern; es gilt, was hier steht.</p>",
             _tabelle("Belohnungen für Sie", KOPF_FUER_MICH, fuer_mich)]
    if klasse:
        teile += [_tabelle("Belohnungen für die ganze Klasse", KOPF_KLASSE, klasse),
                  "<p>Eine Klassenbelohnung gibt es, wenn alle ihren Anteil gebucht haben. Buchen kann nur, wer "
                  "mindestens so viele Sterne hat wie angegeben.</p>"]
    if lernende:
        teile.append(f"<p>Lernende in der Klasse: {int(lernende)}</p>")
    teile += [_tabelle("Diese Kurse zählen für Ihr Sternekonto", KOPF_KURSE, kurse),
              "<p>Verschenken: Sie geben eine gerade Zahl Sterne ab, die Hälfte kommt an. Beispiel: 10 ab, "
              "5 kommen an.</p>"]
    return {"typ": "page", "name": name, "inhalt": "".join(teile), "abschluss": "keine"}


# --------------------------------------------------------------------------------------------------------------- #
# Preisliste lesen wie das Skript (für den Prüfer, ohne node)
# --------------------------------------------------------------------------------------------------------------- #
class _Tabellen(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tabellen, self._zelle, self._zeile, self.text = [], None, None, []

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.tabellen.append([])
        elif tag == "tr" and self.tabellen:
            self._zeile = []
            self.tabellen[-1].append(self._zeile)
        elif tag in ("td", "th") and self._zeile is not None:
            self._zelle = []
            self._zeile.append(self._zelle)

    def handle_endtag(self, tag):
        if tag in ("td", "th"):
            self._zelle = None

    def handle_data(self, data):
        self.text.append(data)
        if self._zelle is not None:
            self._zelle.append(data)


def _zahl(text: str):
    m = re.search(r"-?\d[\d.,]*", (text or "").replace("\xa0", " "))
    if not m:
        return None
    s = m.group(0)
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def preise_lesen(html: str) -> dict:
    """Wie preiseLesen in sternebuch.js: {fuer_mich, klasse, kurse, lernende, fehler}."""
    p = _Tabellen()
    p.feed(html or "")
    aus = {"fuer_mich": [], "klasse": [], "kurse": [], "lernende": None, "fehler": []}

    def spalte(kopf, muster):
        return next((i for i, k in enumerate(kopf) if re.search(muster, k)), -1)
    for t in p.tabellen:
        zeilen = [[re.sub(r"\s+", " ", "".join(z)).strip() for z in zeile] for zeile in t]
        if len(zeilen) < 2:
            continue
        kopf = [k.lower() for k in zeilen[0]]
        name = max(0, spalte(kopf, r"belohnung|lernsituation|kurs\b"))
        hinweis, kurz = spalte(kopf, "hinweis"), spalte(kopf, "kurzname")
        anteil, ab, sterne = spalte(kopf, "anteil"), spalte(kopf, r"mindestens|\bab\b"), spalte(kopf, "sterne")

        def zelle(z, i):
            return z[i] if 0 <= i < len(z) else ""
        for z in zeilen[1:]:
            if not "".join(z):
                continue
            if kurz >= 0:
                if zelle(z, kurz):
                    aus["kurse"].append({"name": zelle(z, name) or zelle(z, kurz), "kurzname": zelle(z, kurz)})
            elif anteil >= 0:
                a, m = _zahl(zelle(z, anteil)), (_zahl(zelle(z, ab)) if ab >= 0 else 0)
                if a is None or m is None:
                    aus["fehler"].append(f"Zeile „{' | '.join(z)}“: keine Zahl für Anteil oder Mindestzahl")
                else:
                    aus["klasse"].append({"name": zelle(z, name), "ab": m, "anteil": a, "hinweis": zelle(z, hinweis)})
            elif sterne >= 0:
                s = _zahl(zelle(z, sterne))
                if s is None:
                    aus["fehler"].append(f"Zeile „{' | '.join(z)}“: keine Zahl für Sterne")
                else:
                    aus["fuer_mich"].append({"name": zelle(z, name), "sterne": s, "hinweis": zelle(z, hinweis)})
    m = re.search(r"Lernende in der Klasse:\s*(\d+)", "".join(p.text), re.I)
    if m:
        aus["lernende"] = int(m.group(1))
    return aus


def halbieren(sterne: int) -> int:
    """Wie halbieren in sternebuch.js: 10 ab, 5 an (abgerundet)."""
    return max(0, int(sterne)) // 2
