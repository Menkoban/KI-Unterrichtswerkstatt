"""Stand der Planung für die lebende Übersicht (Webseite): liest Akten, Profil und Skills und schreibt Datendateien.

    python akten/stand.py <arbeitsbereich>   ->  <arbeitsbereich>/.daten/stand/{doppelstunden,grundlagen,profil,werkzeug}.json

Eine Zeile je Doppelstunde (aus den Lernsituations-Akten, ergänzt um Stunden-Akte und Materialordner), je Grundlage
(Modellbetrieb, curriculare Analyse, Skizze, Jahresplanung, Klassen, Lernsituationen, Fehlvorstellungen), je
Profilwert (persönlicher Wert neben dem neutralen Standard) und je Skill der drei Pipelines. Links zeigen auf die
Dateien bei GitHub. Die Übersicht wird nach jeder Freigabe neu erzeugt (Lehrkraft 2026-10-24).
"""
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

HIER = Path(__file__).resolve().parents[1]
PIPELINES = {"Pipeline 1 Planung": HIER, "Pipeline 2 Material": HIER.parent / "materialpipeline-referendariat",
             "Pipeline 3 Moodle": HIER.parent / "moodlepipeline-referendariat"}
BERUFE = {"eg": ("Elektroniker/in EG", "Elektroniker_EG"), "as": ("Elektroniker/in AS", "Elektroniker_AS")}
# Ordner unter <Fach>/ -> (Beruf, Fachrichtung); für die Gliederung Fach > Beruf > Fachrichtung > Lernfeld
FACHRICHTUNGEN = {"Elektroniker_EG": ("Elektroniker/in", "Energie- und Gebäudetechnik", "eg"),
                  "Elektroniker_AS": ("Elektroniker/in", "Automatisierungs- und Systemtechnik", "as")}


def github(repo):
    """Basis-URL für Links auf Dateien eines Repos (Remote und aktueller Zweig)."""
    try:
        url = subprocess.run(["git", "-C", str(repo), "remote", "get-url", "origin"], capture_output=True, text=True,
                             check=True).stdout.strip()
        zweig = subprocess.run(["git", "-C", str(repo), "branch", "--show-current"], capture_output=True, text=True,
                               check=True).stdout.strip() or "main"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    url = re.sub(r"\.git$", "", url)
    url = re.sub(r"^git@github\.com:", "https://github.com/", url)
    url = re.sub(r"^https?://[^/]*?(github\.com/)", r"https://\1", url)
    url = re.sub(r"https://[^/]+/git/", "https://github.com/", url)    # Proxy-Remote der Sitzung
    return f"{url}/{{art}}/{zweig}/"


def link(basis, ab, pfad):
    if not basis or not pfad:
        return ""
    p = Path(pfad)
    rel = p.relative_to(ab) if p.is_absolute() else p
    voll = ab / rel
    if not voll.exists():
        return ""
    return basis.format(art="tree" if voll.is_dir() else "blob") + "/".join(rel.parts)


def lade(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def freigegeben(stand):
    s = (stand or "").lower()
    return "freigegeben" in s and "offen" not in s


def doppelstunden(ab, basis):
    zeilen = []
    stunden = {}
    for f in (ab / ".daten" / "stunde").glob("*.json"):
        d = lade(f)
        if d.get("ls"):
            stunden[(d["ls"], str(d.get("ds")))] = d
    for f in sorted((ab / ".daten" / "lernsituation").glob("*.json")):
        ls = lade(f)
        m = re.match(r"lf(\d+)_([a-z]+)_ls(\d+)", f.stem)
        if not m:
            continue
        lf, kuerzel, lsnr = int(m.group(1)), m.group(2), int(m.group(3))
        beruf, ordner = BERUFE.get(kuerzel, (kuerzel.upper(), kuerzel.upper()))
        lf_ordner = next((ab / "Elektrotechnik" / ordner).glob(f"LF{lf:02d}_*"), None)
        ls_ordner = next(lf_ordner.glob(f"LS{lsnr:02d}_*"), None) if lf_ordner else None
        for x in ls.get("doppelstunden", []):
            ds = str(x["ds"])
            st = stunden.get((f.stem, ds), {})
            mat = ls_ordner / "Material" / f"DS{int(ds):02d}" if ls_ordner else None
            if freigegeben(st.get("material_stand")):
                material = "freigegeben"
            elif mat and mat.exists():
                material = "vorhanden"
            else:
                material = "offen"
            if not st:
                planung = "ausgearbeitet" if freigegeben(ls.get("stand")) else "skizziert"
            else:
                planung = "Stunde freigegeben" if freigegeben(st.get("stand")) else "Stunde im Entwurf"
            verlauf = st.get("verlauf", [])
            einstieg = verlauf[0]["phase"].split(":", 1)[-1].strip() if verlauf else ""
            sozial = []
            for z in verlauf:
                for so in z.get("sozial", []):
                    k = re.sub(r"\s*\(.*\)", "", so).strip()
                    if k and k not in sozial and not k.startswith("L."):
                        sozial.append(k)
            fr = FACHRICHTUNGEN.get(ordner, (beruf, "", kuerzel))
            zeilen.append({
                "id": f"{f.stem}_ds{int(ds):02d}", "beruf": beruf, "fach": ls.get("fach") or "Elektrotechnik",
                "beruf_name": fr[0], "fachrichtung": fr[1], "lf_nr": lf,
                "lf_titel": lf_ordner.name.split("_", 1)[1].replace("_", " ") if lf_ordner else "",
                "ls_key": f.stem, "ls_titel": ls.get("titel", ""), "ls_std": ls.get("std", ""), "lf": f"LF {lf}", "ls_nr": lsnr,
                "ls": f"LS {lsnr} {ls.get('titel', '')}", "ds": int(ds), "std": x.get("std_nr", ""),
                "leitfrage": x.get("leitfrage", ""), "teilergebnis": x.get("teilergebnis", ""),
                "klasse": st.get("klasse") or "", "typ": st.get("typ", ""), "planung": planung, "material": material,
                "einstieg": einstieg, "sozialformen": ", ".join(sozial),
                "link_lernsituation": link(basis, ab, ls_ordner / "Lernsituation.docx") if ls_ordner else "",
                "link_stunde": link(basis, ab, st.get("ordner")) if st else "",
                "link_material": link(basis, ab, mat) if mat else "",
                "stand_am": st.get("datum", "")})
    return zeilen


def grundlagen(ab, basis):
    z = []

    def zeile(beruf, bereich, element, stand, pfad):
        z.append({"beruf": beruf, "bereich": bereich, "element": element,
                  "stand": "freigegeben" if freigegeben(stand) else (stand or "vorhanden")[:40],
                  "link": link(basis, ab, pfad) if pfad else ""})
    d = ab / ".daten"
    for f in sorted((d / "modellbetrieb").glob("*.json")):
        m = lade(f)
        zeile("Elektroniker/in EG", "Modellbetrieb", m.get("name") or f.stem, m.get("stand"),
              next(ab.glob("Elektrotechnik/Elektroniker_EG/Modellbetrieb_*.docx"), None))
    for f in sorted((d / "curriculare_analyse").glob("*.json")):
        m = lade(f)
        zeile("Elektroniker/in AS und EG", "Curriculare Analyse", m.get("titel") or f.stem, m.get("stand"),
              next(ab.glob("Elektrotechnik/Elektroniker_EG/LF01_*/Curriculare_Analyse.docx"), None))
    for f in sorted((d / "ls_skizze").glob("*.json")):
        m = lade(f)
        zeile("Elektroniker/in EG", "Lernsituationen-Skizze", m.get("titel") or f.stem, m.get("stand"),
              next(ab.glob("Elektrotechnik/Elektroniker_EG/LF01_*/Lernsituationen_Skizze.docx"), None))
    for f in sorted((d / "jahresplanung").glob("*.json")):
        m = lade(f)
        zeile("Elektroniker/in EG", "Jahresplanung", f.stem, m.get("stand"),
              ab / "Unterricht" / "Elektrotechnik" / f.stem / "Jahresplanung.docx")
    for f in sorted((d / "klasse").glob("*.json")):
        m = lade(f)
        zeile("Elektroniker/in EG", "Klassen-Akte", f.stem, m.get("stand"),
              ab / "Unterricht" / "Elektrotechnik" / f.stem / "Bedingungsfeld.docx")
    for f in sorted((d / "fehlvorstellungen").glob("*.json")):
        m = lade(f)
        n = re.search(r"ls(\d+)", f.stem)
        ordner = next(ab.glob(f"Elektrotechnik/Elektroniker_EG/LF01_*/LS{int(n.group(1)):02d}_*"), None) if n else None
        zeile("Elektroniker/in EG", "Fehlvorstellungen", f"LS {int(n.group(1))}" if n else f.stem, m.get("stand"),
              ordner / "Fehlvorstellungen.docx" if ordner else None)
    for f in sorted(ab.glob("Elektrotechnik/Elektroniker_AS/**/*")):          # Probelauf AS: nur Dateien
        if f.is_file() and f.suffix in (".docx", ".md") and f.name != "HERKUNFT.md":
            zeile("Elektroniker/in AS", "Probelauf", f.stem.replace("_", " "), "vorhanden (Probelauf)", f)
    return z


def moodle_stand(ls_ordner):
    """Stand des Moodle-Kurses einer Lernsituation (Pipeline 3): 0 offen, 1 Kursplan, 2 gebaut (Sicherung da),
    3 abgenommen (Durchsicht ohne offene Punkte)."""
    m = ls_ordner / "Moodle" if ls_ordner else None
    if not m or not m.exists():
        return {"stufe": 0, "text": "offen", "kurz": "", "offen": 0}
    mbz = sorted(m.glob("*.mbz"))
    plan = lade(m / "kursplan.json")
    bau = m / "bau"
    gebaut = len(list(bau.glob("abschnitt_*.json"))) if bau.exists() else 0
    geplant = len(plan.get("abschnitte", [])) or gebaut
    offen = 0
    for d in sorted(m.glob("Durchsicht_*.md"))[-1:]:
        teil = d.read_text(encoding="utf-8").split("## Offen", 1)
        if len(teil) == 2:
            offen = len(re.findall(r"^\d+\.\s", teil[1].split("\n## ", 1)[0], re.M))
    kurz = mbz[-1].stem if mbz else (plan.get("kurs") or {}).get("kurzname", "")
    if mbz and offen == 0 and list(m.glob("Durchsicht_*.md")):
        return {"stufe": 3, "text": "abgenommen", "kurz": kurz, "offen": 0, "abschnitte": geplant}
    if mbz:
        return {"stufe": 2, "text": f"gebaut, {offen} Punkte offen" if offen else "gebaut", "kurz": kurz, "offen": offen, "abschnitte": geplant}
    if gebaut:
        return {"stufe": 1, "text": f"im Bau ({gebaut} von {geplant} Abschnitten)", "kurz": kurz, "offen": 0, "abschnitte": geplant}
    if plan:
        return {"stufe": 1, "text": "Kursplan", "kurz": kurz, "offen": 0, "abschnitte": geplant}
    return {"stufe": 0, "text": "offen", "kurz": "", "offen": 0}


def struktur(ab, basis):
    """Ein Eintrag je Lernfeld und Fachrichtung: Fach > Beruf > Fachrichtung > Lernfeld mit allen Lernsituationen
    der Skizze (auch noch nicht ausgearbeitete) und den Grundlagen-Dokumenten des Lernfelds."""
    z = []
    faecher = lade(ab / "Profil" / "lehrkraft-profil.json").get("werte", {}).get("faecher") or []
    for fach_ordner in sorted(p for p in ab.iterdir() if p.is_dir() and not p.name.startswith(".")
                              and p.name not in ("Unterricht", "Profil", "Eingang", "Handover", "Moodle", "Quellen", "Ref")):
        fach = fach_ordner.name
        beruf_ordner = [b for b in sorted(fach_ordner.iterdir()) if b.is_dir()]
        if not beruf_ordner:
            z.append({"id": fach.lower(), "fach": fach, "beruf": "", "fachrichtung": "", "kuerzel": "", "lf_nr": 0,
                      "lf_titel": "", "lernsituationen": [], "dokumente": [], "leer": True})
        for b in beruf_ordner:
            beruf, fr, k = FACHRICHTUNGEN.get(b.name, (b.name.replace("_", " "), "", b.name.lower()))
            for lf in sorted(b.glob("LF*_*")):
                nr = int(re.match(r"LF(\d+)", lf.name).group(1))
                skizze = lade(ab / ".daten" / "ls_skizze" / f"lf{nr:02d}_{k}.json")
                ls = []
                for i, a in enumerate(x for x in skizze.get("ablauf", []) if str(x.get("nr", "")).isdigit()):
                    n = int(a["nr"])
                    akte = lade(ab / ".daten" / "lernsituation" / f"lf{nr:02d}_{k}_ls{n:02d}.json")
                    ordner = next(lf.glob(f"LS{n:02d}_*"), None)
                    moodle = moodle_stand(ordner)
                    ls.append({"nr": n, "key": f"lf{nr:02d}_{k}_ls{n:02d}", "moodle": moodle,
                               "titel": akte.get("titel") or a.get("titel", "").strip("„“\""), "std": a.get("std"),
                               "stand": "ausgearbeitet" if akte else "skizziert",
                               "freigegeben": freigegeben(akte.get("stand")) if akte else False,
                               "ds_anzahl": len(akte.get("doppelstunden", [])),
                               "ergebnis": kurz(a.get("ergebnis", ""), 200),
                               "link": link(basis, ab, ordner) if ordner else ""})
                if not ls:      # ohne Skizze: Ordner der Lernsituationen
                    for o in sorted(lf.glob("LS*_*")):
                        n = int(re.match(r"LS(\d+)", o.name).group(1))
                        ls.append({"nr": n, "key": f"lf{nr:02d}_{k}_ls{n:02d}", "moodle": moodle_stand(o), "titel": o.name.split("_", 1)[1].replace("_", " "),
                                   "std": None, "stand": "Probelauf", "freigegeben": False, "ds_anzahl": 0, "ergebnis": "",
                                   "link": link(basis, ab, o)})
                doks = [{"name": d.stem.replace("_", " "), "pfad": str(d.relative_to(ab)), "link": link(basis, ab, d)}
                        for d in sorted(lf.glob("*.docx"))]
                z.append({"id": f"lf{nr:02d}_{k}", "fach": fach, "beruf": beruf, "fachrichtung": fr, "kuerzel": k.upper(),
                          "lf_nr": nr, "lf_titel": lf.name.split("_", 1)[1].replace("_", " "),
                          "zeitrichtwert": skizze.get("zeitrichtwert"), "skizze_stand": (skizze.get("stand") or "")[:60],
                          "lernsituationen": ls, "dokumente": doks, "leer": False})
    for f in faecher:
        f = re.sub(r"\s*\(.*\)", "", f).strip()
        if f and not any(x["fach"] == f for x in z):
            z.append({"id": f.lower(), "fach": f, "beruf": "", "fachrichtung": "", "kuerzel": "", "lf_nr": 0,
                      "lf_titel": "", "lernsituationen": [], "dokumente": [], "leer": True})
    return z


def kurz(text, n=160):
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= n else text[:n].rsplit(" ", 1)[0] + " …"


def profil(ab):
    vorlage = lade(HIER / "profil" / "vorlage.json").get("einstellungen", [])
    p = lade(ab / "Profil" / "lehrkraft-profil.json")
    werte, herkunft = p.get("werte", {}), p.get("herkunft", {})

    def zeigen(v):
        if isinstance(v, bool):
            return "ja" if v else "nein"
        if isinstance(v, list):
            return ", ".join(map(str, v))
        return "" if v is None else str(v)
    z = []
    for e in vorlage:
        k = e["id"]
        eigen = k in werte
        z.append({"id": k, "gruppe": e.get("gruppe", ""), "titel": e.get("titel", k),
                  "erklaerung": kurz(e.get("erklaerung", ""), 220),
                  "standard": zeigen(e.get("standard")), "wert": zeigen(werte.get(k, e.get("standard"))),
                  "personalisiert": "ja" if eigen and werte.get(k) != e.get("standard") else "nein",
                  "seit": herkunft.get(k, "") if eigen else "",
                  "typ": e.get("typ", ""), "optionen": e.get("optionen", []), "roh": werte.get(k, e.get("standard"))})
    return z


def werkzeug():
    z = []
    for name, repo in PIPELINES.items():
        basis = github(repo)
        for f in sorted((repo / ".claude" / "skills").glob("*/SKILL.md")):
            text = f.read_text(encoding="utf-8")
            m = re.search(r"^description:\s*(.+)$", text, re.M)
            z.append({"pipeline": name, "skill": f.parent.name, "beschreibung": kurz(m.group(1) if m else "", 180),
                      "link": link(basis, repo, f)})
    return z


def main(ab):
    ab = Path(ab).resolve()
    basis = github(ab)
    ziel = ab / ".daten" / "stand"
    ziel.mkdir(parents=True, exist_ok=True)
    daten = {"doppelstunden": doppelstunden(ab, basis), "grundlagen": grundlagen(ab, basis), "profil": profil(ab),
             "werkzeug": werkzeug(), "struktur": struktur(ab, basis)}
    for name, zeilen in daten.items():
        (ziel / f"{name}.json").write_text(json.dumps(zeilen, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{name}.json: {len(zeilen)} Zeilen")
    (ziel / "erzeugt.txt").write_text(date.today().isoformat() + "\n", encoding="utf-8")
    return ziel


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
