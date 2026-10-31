"""Klassen-Dashboard und Selbsteinschätzung am Meilenstein (Lehrkraft 2026-10-31, Fahrplan 2.2).

Bausteine für die Kursdefinition:
  selbsteinschaetzung(ms)       Feedback-Aktivität „Selbsteinschätzung <Meilenstein>“ (nicht anonym, Pflicht): je
                                Kriterium eine Auswahl „1 …“ bis „4 …“ mit Kennung K1, K2 …; gehört in die Kachel des
                                Meilensteins direkt vor die Abgabe (die Abgabe setzt sie als Voraussetzung voraus).
  dashboard_aktivitaet(liste)   verborgene Datenbank-Aktivität „Klassen-Dashboard“ für den Lehrkraftbereich: zeigt je
                                Meilenstein Selbsteinschätzung, Stufe der Lehrkraft, Abweichung (rot ab gespraech_ab),
                                Note nach IHK; speichert die Stufen als eigene Einträge (klassendashboard.js).

Ein Meilenstein: {"id": "m1", "kurz": "Meilenstein 1", "titel": "Meilenstein 1 · …", "kriterien": [{"name", "stufen":
[vier Sätze]}]}. Die Kriterien sind ab Kachel 1 sichtbar und verraten die Ursache nicht (Regel „Keine Problemführung“).
Die Aktivität muss im Lehrkraftbereich liegen und selbst verborgen sein (Prüfer 2).
"""
import json
import re
from pathlib import Path

JS_DATEI = Path(__file__).with_name("klassendashboard.js")
NAME = "Klassen-Dashboard"

CSS = """
.kd{--kd-blau:#08349C;--kd-blau-hell:#e3e9f8;--kd-rot:#c92a2a;--kd-rot-hell:#fbe3e3;--kd-gruen:#2f7d3a;--kd-gruen-hell:#e5f5e8;
  --kd-linie:#d6dbe7;--kd-grau:#eef1f7;--kd-text:#151b2b;--kd-leise:#5a6377;color:var(--kd-text);margin-bottom:1.5rem;
  font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.kd-kopf{display:flex;flex-wrap:wrap;gap:.5rem 1rem;align-items:baseline;justify-content:space-between}
.kd-kopf h2{color:var(--kd-blau);margin:0}
.kd-status{color:var(--kd-gruen);font-size:.875rem}
.kd-zahlen{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:.6rem;margin:.8rem 0}
.kd-zahl{border:1px solid var(--kd-linie);border-radius:10px;padding:.5rem .8rem;background:#fff}
.kd-w{font-size:1.5rem;font-weight:700;font-variant-numeric:tabular-nums}
.kd-l{font-size:.85rem;color:var(--kd-leise)}
.kd-alarm{border-color:var(--kd-rot)} .kd-alarm .kd-w{color:var(--kd-rot)}
.kd-reiter{display:flex;flex-wrap:wrap;gap:.3rem;border-bottom:2px solid var(--kd-linie);margin-bottom:.6rem}
.kd-reiter button{border:0;background:none;padding:.5rem .9rem;font-weight:700;color:var(--kd-leise);border-bottom:3px solid transparent;margin-bottom:-2px}
.kd-reiter button[aria-selected="true"]{color:var(--kd-blau);border-bottom-color:var(--kd-blau)}
.kd-hinweis{color:var(--kd-leise);font-size:.9rem}
.kd-tw{overflow-x:auto}
.kd-tab{border-collapse:separate;border-spacing:0;width:100%;font-variant-numeric:tabular-nums;background:#fff}
.kd-tab th,.kd-tab td{padding:.4rem .5rem;border-bottom:1px solid var(--kd-linie);text-align:center;white-space:nowrap}
.kd-tab th{background:var(--kd-grau);font-size:.8rem;color:var(--kd-leise)}
.kd-tab th.kd-kr{color:var(--kd-text);white-space:normal;min-width:9rem}
.kd-tab .kd-name{text-align:left;position:sticky;left:0;background:#fff}
.kd-tab th.kd-name{background:var(--kd-grau)}
.kd-grenze{border-left:2px solid var(--kd-linie)}
.kd-selbst{display:inline-flex;width:1.9rem;height:1.9rem;border-radius:50%;align-items:center;justify-content:center;background:var(--kd-grau);font-weight:700}
.kd-stufen{display:inline-flex;gap:3px}
.kd-stb{width:1.9rem;height:1.9rem;border-radius:6px;border:1px solid var(--kd-linie);background:#fff;font-weight:700;color:var(--kd-leise);padding:0}
.kd-stb[aria-pressed="true"]{background:var(--kd-blau);border-color:var(--kd-blau);color:#fff}
.kd-stb:focus-visible,.kd-reiter button:focus-visible{outline:3px solid var(--kd-blau);outline-offset:2px}
.kd-abw{display:inline-block;min-width:2rem;border-radius:6px;padding:2px 0;font-weight:700}
.kd-rot{background:var(--kd-rot-hell);color:var(--kd-rot);outline:2px solid var(--kd-rot)}
.kd-offen{color:var(--kd-leise);font-size:.85rem}
.kd-note{font-weight:700;font-size:1.05rem}
.kd-pill{display:inline-block;border-radius:999px;padding:1px 9px;font-size:.85rem;font-weight:700;background:var(--kd-grau);color:var(--kd-leise)}
.kd-pill-rot{background:var(--kd-rot);color:#fff} .kd-pill-ok{background:var(--kd-gruen-hell);color:var(--kd-gruen)}
.kd-gespraech-zeile td.kd-name{box-shadow:inset 4px 0 0 var(--kd-rot)}
.kd-knopf{border:1px solid var(--kd-blau);background:#fff;color:var(--kd-blau);border-radius:8px;padding:.35rem .8rem;font-weight:700}
.kd-liste,[data-region="empty-message"],#sticky-footer,.stickyfooter{display:none !important}
"""


def selbsteinschaetzung(ms: dict, abschluss: str = "abgeben") -> dict:
    """Feedback-Aktivität der Lernenden für einen Meilenstein (direkt vor die Abgabe legen)."""
    elemente = [{"typ": "info", "text": "<p>Schätzen Sie Ihr Ergebnis ehrlich ein, bevor Sie es abgeben. Ihre Lehrkraft "
                                         "bewertet es mit denselben Stufen; weichen beide stark ab, sprechen Sie kurz darüber.</p>"}]
    for i, k in enumerate(ms["kriterien"], start=1):
        elemente.append({"typ": "auswahl", "frage": k["name"], "kennung": f"K{i}", "pflicht": True,
                         "optionen": [f"{s} {t}" for s, t in enumerate(k["stufen"], start=1)]})
    return {"typ": "feedback", "name": f"Selbsteinschätzung {ms['kurz']}", "anonym": False, "abschluss": abschluss,
            "beschreibung": "", "elemente": elemente}


def skript(konfig: dict) -> str:
    js = JS_DATEI.read_text(encoding="utf-8")
    neu, n = re.subn(r"/\*KONFIG\*/.*?/\*/KONFIG\*/", lambda _: "/*KONFIG*/" + json.dumps(konfig, ensure_ascii=False)
                     + "/*/KONFIG*/", js, count=1, flags=re.S)
    if n != 1:
        raise ValueError("klassendashboard.js: Markierung /*KONFIG*/ … /*/KONFIG*/ fehlt")
    return neu


def dashboard_aktivitaet(meilensteine: list[dict], gespraech_ab: int = 2) -> dict:
    """Verborgene Datenbank-Aktivität für den Lehrkraftbereich."""
    konfig = {"gespraech_ab": gespraech_ab,
              "meilensteine": [{"id": m["id"], "kurz": m["kurz"], "titel": m.get("titel", m["kurz"]),
                                "name": selbsteinschaetzung(m)["name"], "kriterien": m["kriterien"]} for m in meilensteine]}
    return {"typ": "data", "name": NAME, "idnummer": "klassendashboard", "abschluss": "keine", "sichtbar": False,
            "beschreibung": "<p>Nur für Lehrkräfte: Selbsteinschätzungen und Ihre Bewertung je Meilenstein.</p>",
            "felder": [{"name": "lernende", "typ": "text", "beschreibung": "Name wie in Moodle"},
                       {"name": "meilenstein", "typ": "text", "beschreibung": "Kennung des Meilensteins"},
                       {"name": "stufen", "typ": "text", "beschreibung": "Stufen der Lehrkraft je Kriterium"}],
            "vorlagen": {"listtemplateheader": "", "listtemplatefooter": "",
                         "listtemplate": '<div class="kd-liste kd-eintrag" data-mehr="##moreurl##" data-l="[[lernende]]" '
                                         'data-m="[[meilenstein]]" data-s="[[stufen]]"></div>',
                         "singletemplate": "<p>[[lernende]] · [[meilenstein]] · [[stufen]]</p>",
                         "addtemplate": '<div data-feld="lernende">[[lernende]]</div><div data-feld="meilenstein">'
                                        '[[meilenstein]]</div><div data-feld="stufen">[[stufen]]</div>',
                         "csstemplate": CSS, "jstemplate": skript(konfig)}}
