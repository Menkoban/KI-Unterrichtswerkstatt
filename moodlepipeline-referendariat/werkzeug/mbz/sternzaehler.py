"""Sternzähler „⭐ Meine Sterne“ (Lehrkraft 2026-10-26, ersetzt die Textfelder je Sternstand vom 2026-10-23).

Genau eine Aktivität in Abschnitt 0 des Themenkurses (Kursschalter `sternzaehler`, Profil `moodle.sternzaehler`):
eine Datenbank (mod_data) ohne Einträge, ohne Abschluss, Lernende können nichts anlegen (`nur_lesen`, Recht
mod/data:writeentry entzogen). Das Skript `sternzaehler.js` (Vorlage „JavaScript“) liest das eigene Kursgesamt aus
der Bewertungsübersicht und zeigt „⭐ n von N Sternen“ mit Balken in den Schulfarben; N = sterne.kursgesamt_max.

    akt = aktivitaet(31, "KL1a · LF 1 · LS 2 Sicher beim Kunden")
"""
from __future__ import annotations

import json
import re
from pathlib import Path

JS_DATEI = Path(__file__).with_name("sternzaehler.js")
KONFIG = re.compile(r"/\*KONFIG\*/(.*?)/\*/KONFIG\*/", re.S)
IDNUMMER = "sternzaehler"
NAME = "⭐ Meine Sterne"
FARBEN = ("#08349C", "#7DDE78")


def skript(konfig: dict) -> str:
    quelle = JS_DATEI.read_text(encoding="utf-8")
    if not KONFIG.search(quelle):
        raise ValueError("sternzaehler.js: Markierung /*KONFIG*/ … /*/KONFIG*/ fehlt")
    return KONFIG.sub(lambda _: "/*KONFIG*/" + json.dumps(konfig, ensure_ascii=False, indent=8) + "/*/KONFIG*/",
                      quelle, count=1)


def konfig_aus(js: str) -> dict | None:
    m = KONFIG.search(js or "")
    return json.loads(m.group(1)) if m else None


def aktivitaet(n_max: float, kursname: str, farben: tuple[str, str] = FARBEN) -> dict:
    """Die Datenbank-Aktivität „⭐ Meine Sterne“ (Kursdefinition, typ data); N muss eine ganze Sternzahl sein."""
    if n_max != int(n_max) or n_max <= 0:
        raise ValueError(f"Kursgesamt-Höchstwert {n_max:g} ist keine ganze Sternzahl > 0")
    blau, gruen = farben
    css = (f".sz {{ background:#FFF4CC; color:#5C4300; border:1px solid #E0A800; border-radius:6px; "
           f"padding:10px 14px; margin:0 0 1rem 0; font-size:16px; }}\n"
           f".sz-zeile {{ font-weight:bold; font-size:1.3em; margin:0; color:{blau}; }}\n"
           ".sz-kurs, .sz-hinweis { margin:2px 0 8px 0; font-size:16px; }\n"
           # leeres Bild „keine Einträge“ von Moodle ausblenden (Sichtprüfung LS 5)
           '[data-region="empty-message"] { display:none !important; }\n')
    return {
        "typ": "data", "name": NAME, "kennung": "Sternzähler", "idnummer": IDNUMMER, "abschluss": "keine",
        "nur_lesen": True,
        "beschreibung": "",
        "felder": [{"name": "Hinweis", "typ": "text", "beschreibung": "wird nicht benutzt"}],
        "vorlagen": {"listtemplateheader": "", "listtemplate": "", "listtemplatefooter": "",
                     "singletemplate": "", "addtemplate": "<p>Hier werden keine Einträge angelegt.</p>",
                     "csstemplate": css,
                     "jstemplate": skript({"max": int(n_max), "kursname": kursname, "farben": [blau, gruen]})},
    }
