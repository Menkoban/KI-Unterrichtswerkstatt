"""„Mein Lernpfad“ (Lehrkraft 2026-10-28; Kursschalter `lernpfad`, Profil
`moodle.lernpfad_anzeige`).

Genau eine Aktivität in Abschnitt 0 eines Themenkurses mit Übungsinseln (inseln.py), unter dem Sternzähler: eine
Datenbank (mod_data, Moodle-Kern) ohne Einträge, ohne Abschluss und ohne Note; Lernende legen nichts an (`nur_lesen`).
Das Skript `lernpfad.js` (Vorlage „JavaScript“) liest mit der Sitzung der ansehenden Person die eigene
Bewertungsübersicht und zeigt je Insel die Einstiegsstufe, das Ergebnis des Kurztests, die erreichte Stufe und die
geübten Stufen, als Linie über drei Bahnen und als Text. Die Namen der Übungen und Kurztests stehen in der
Konfiguration des Skripts (die Bewertungsübersicht nennt die Aktivitäten beim Namen); der Bau setzt sie mit den
endgültigen Namen (nach den Schrittnummern) ein, Prüfer 14 vergleicht sie mit dem Paket.

    a = aktivitaet(konfig(kursdef, namen), "KL1a · LF 1 · LS 5 …", ("#08349C", "#7DDE78"))
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import inseln

JS_DATEI = Path(__file__).with_name("lernpfad.js")
KONFIG = re.compile(r"/\*KONFIG\*/(.*?)/\*/KONFIG\*/", re.S)
IDNUMMER = "lernpfad"
NAME = "Mein Lernpfad"
FARBEN = ("#08349C", "#7DDE78")
LINIE = "#C62828"          # rote Linie wie im Bild zu Entscheidung 5 (Kontrast 5,6 : 1 auf Weiß)
SCHRITT = re.compile(r"^(?:Schritt \d+(?:\.\d+)? · )?(?:Insel \d+\s*[:·]\s*)?")


def skript(konfig: dict) -> str:
    quelle = JS_DATEI.read_text(encoding="utf-8")
    if not KONFIG.search(quelle):
        raise ValueError("lernpfad.js: Markierung /*KONFIG*/ … /*/KONFIG*/ fehlt")
    return KONFIG.sub(lambda _: "/*KONFIG*/" + json.dumps(konfig, ensure_ascii=False, indent=8) + "/*/KONFIG*/",
                      quelle, count=1)


def konfig_aus(js: str) -> dict | None:
    m = KONFIG.search(js or "")
    return json.loads(m.group(1)) if m else None


def konfig(kursdef: dict, namen: dict | None = None) -> dict:
    """Konfiguration des Skripts aus `kursdef["inseln"]` (inseln.einsetzen). `namen`: {Kennung: Name im Kurs}
    (Vorgabe: die Kennung)."""
    namen = namen or {}
    liste = kursdef.get("inseln") or []
    if not liste:
        raise ValueError("„Mein Lernpfad“ braucht Übungsinseln (kursdef['inseln'], inseln.einsetzen)")
    return {"kursname": (kursdef.get("kurs") or {}).get("vollname", ""),
            "farben": list(FARBEN), "linie": LINIE, "grenzen": list(inseln.grenzen_von(kursdef)),
            "start": liste[0].get("start") or inseln.START, "stufen": list(inseln.STUFEN),
            "inseln": [{"nr": i["nr"], "titel": SCHRITT.sub("", i.get("thema") or namen.get(i["kopf"], i["kopf"])),
                        "uebung": [namen.get(i["stufen"][s]["uebung"], i["stufen"][s]["uebung"])
                                   for s in inseln.STUFEN],
                        "kurztest": [namen.get(i["stufen"][s]["kurztest"], i["stufen"][s]["kurztest"])
                                     for s in inseln.STUFEN]} for i in liste]}


def aktivitaet(k: dict, kursname: str, farben: tuple[str, str] = FARBEN) -> dict:
    """Die Datenbank-Aktivität „Mein Lernpfad“ (Kursdefinition, typ data)."""
    blau, gruen = (tuple(farben) + FARBEN)[:2]
    k = dict(k, kursname=kursname or k.get("kursname", ""), farben=[blau, gruen])
    css = (f".lp {{ border:1px solid {blau}; border-radius:6px; padding:10px 14px; margin:0 0 1rem 0; "
           f"font-size:16px; background:#fff; color:#14213D; }}\n"
           f".lp-zeile {{ font-weight:bold; font-size:1.2em; color:{blau}; margin:0 0 8px 0; }}\n"
           ".lp-bild { overflow-x:auto; margin:0 0 8px 0; }\n"
           ".lp-legende, .lp-liste, .lp-hinweis { font-size:16px; }\n"
           f".lp h4 {{ color:{blau}; font-size:1.1em; margin-top:12px; }}\n"
           '[data-region="empty-message"] { display:none !important; }\n')
    return {
        "typ": "data", "name": NAME, "kennung": "Lernpfad", "idnummer": IDNUMMER, "abschluss": "keine",
        "nur_lesen": True, "beschreibung": "",
        "felder": [{"name": "Hinweis", "typ": "text", "beschreibung": "wird nicht benutzt"}],
        "vorlagen": {"listtemplateheader": "", "listtemplate": "", "listtemplatefooter": "",
                     "singletemplate": "", "addtemplate": "<p>Hier werden keine Einträge angelegt.</p>",
                     "csstemplate": css, "jstemplate": skript(k)},
    }
