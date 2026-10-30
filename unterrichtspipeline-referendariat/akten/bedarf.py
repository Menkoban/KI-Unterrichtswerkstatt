"""Bedarfsprüfung für den Einstieg: Was braucht ein Planungsziel, was ist da, was fehlt?

    python akten/bedarf.py --beruf Elektroniker_AS --lf 1 --ls 4 [--klasse 2026-27_EAS1a] [--stunde] [--typ alltag|eub|kub|flb|gub|pu]

Ziel ohne --stunde: die Lernsituations-Akte. Mit --stunde: zusätzlich Klassen- und Schuljahres-Akte.
Der Stand kommt aus den Steckbriefen (akten.py); eine Datei ohne Steckbrief gilt als „ungeprüft“."""
import argparse, json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import akten, arbeitsbereich

FACH = "Elektrotechnik"


def ls_aus_skizze(skizze, ls):
    """Titel und Stunden der LS aus der Tabelle der LS-Skizze (Schritt 02); bei einer DOCX-Skizze
    aus deren Daten in .daten/ls_skizze/ (Feld "ordner" = Ordner der Skizze)."""
    if skizze.suffix == ".docx":
        ab = next(p for p in skizze.parents if (p / ".daten").is_dir())
        ordner = str(skizze.parent.relative_to(ab))
        for d in (ab / ".daten" / "ls_skizze").glob("*.json"):
            s = json.loads(d.read_text(encoding="utf-8"))
            if s.get("ordner") != ordner:
                continue
            for x in s["ablauf"]:
                if x["nr"] == str(ls):
                    return {"titel": x["titel"].strip("„“"), "stunden": x["std"], "lk": ", ".join(x["lk"]), "status": s["stand"]}
        return None
    for zeile in skizze.read_text(encoding="utf-8").splitlines():
        teile = [t.strip() for t in zeile.strip().strip("|").split("|")]
        if len(teile) >= 7 and teile[0] == str(ls):
            titel = re.search(r"„([^“\"]+)[“\"]", teile[1].replace("**", ""))
            return {"titel": titel.group(1) if titel else teile[1][:60], "stunden": teile[5], "lk": teile[4], "status": teile[6]}
    return None


def bedarf(ab, beruf, lf, ls, klasse=None, stunde=False, typ="alltag"):
    ab = pathlib.Path(ab)
    sbs = {s["pfad"]: s for s in akten.steckbriefe(ab)}
    befunde = akten.pruefen(ab)
    veraltet = {b.split(":")[1].strip() for b in befunde if "veraltet" in b}

    def stand(muster, schritt, was, pflicht=True, hinweis=""):
        treffer = sorted(ab.glob(muster))
        if not treffer:
            return {"schritt": schritt, "was": was, "stand": "fehlt", "pfad": None, "pflicht": pflicht, "hinweis": hinweis}
        rel = str(treffer[0].relative_to(ab))
        sb = sbs.get(rel)
        st = "ungeprüft" if not sb else ("veraltet" if rel in veraltet else sb["stand"])
        return {"schritt": schritt, "was": was, "stand": st, "pfad": rel, "pflicht": pflicht, "hinweis": hinweis}

    b = f"{FACH}/{beruf}"
    lfm = f"{b}/LF{lf:02d}_*"
    liste = [
        stand(f"{b}/Modellbetrieb*", "02", "Modellbetrieb (je Beruf)"),
        stand(f"{lfm}/Curriculare_Analyse*", "01", f"LF {lf}: Curriculare Analyse")
        if list(ab.glob(f"{lfm}/Curriculare_Analyse*")) else
        stand(f"{FACH}/{beruf.split('_')[0]}_*/LF{lf:02d}_*/Curriculare_Analyse*", "01",
              f"LF {lf}: Curriculare Analyse (gemeinsam für die Fachrichtungen)"),
        stand(f"{lfm}/Lernsituationen_Skizze*", "02", f"LF {lf}: Lernsituationen skizziert"),
    ]
    info = None
    if liste[2]["pfad"]:
        info = ls_aus_skizze(ab / liste[2]["pfad"], ls)
        if not info:
            liste[2]["hinweis"] = f"LS {ls} steht nicht in der Skizze"
    liste += [
        stand(f"{lfm}/LS{ls:02d}_*/Lernsituation*", "04", f"LS {ls}: Lernsituation ausgearbeitet"),
        stand(f"{lfm}/LS{ls:02d}_*/Fehlvorstellungen*", "06", f"LS {ls}: Lernausgangslage und Fehlvorstellungen (themenbezogen)"),
    ]
    if stunde:
        k = f"Unterricht/{FACH}/{klasse}" if klasse else None
        liste += [
            stand(f"{k}/Jahresplanung*", "03", "Schuljahres-Akte: Jahresplanung", pflicht=False,
                  hinweis="im Ref meist Import der Schulplanung") if k else
            {"schritt": "03", "was": "Schuljahres-Akte: Jahresplanung", "stand": "fehlt", "pfad": None, "pflicht": False, "hinweis": "keine Klasse genannt"},
            stand(f"{k}/Bedingungsfeld*", "05", "Klassen-Akte: Bedingungsfeld") if k else
            {"schritt": "05", "was": "Klassen-Akte: Bedingungsfeld", "stand": "fehlt", "pfad": None, "pflicht": True, "hinweis": "keine Klasse genannt"},
            stand(f"{k}/Lernausgangslage*", "06", "Klassen-Akte: Lernausgangslage (allgemein)") if k else
            {"schritt": "06", "was": "Klassen-Akte: Lernausgangslage (allgemein)", "stand": "fehlt", "pfad": None, "pflicht": True, "hinweis": "keine Klasse genannt"},
        ]
    offen = [x for x in liste if x["stand"] != "freigegeben"]
    return {"ziel": {"beruf": beruf, "lf": lf, "ls": ls, "klasse": klasse, "stunde": stunde, "typ": typ},
            "ls_aus_skizze": info, "liste": liste, "reihenfolge": sorted(offen, key=lambda x: x["schritt"]),
            "befunde": befunde}


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--beruf", required=True); a.add_argument("--lf", type=int, required=True)
    a.add_argument("--ls", type=int, required=True); a.add_argument("--klasse"); a.add_argument("--stunde", action="store_true")
    a.add_argument("--typ", default="alltag", choices=["alltag", "eub", "kub", "flb", "gub", "pu"]); a.add_argument("--json", action="store_true")
    o = a.parse_args()
    r = bedarf(arbeitsbereich.finden(), o.beruf, o.lf, o.ls, o.klasse, o.stunde, o.typ)
    if o.json:
        print(json.dumps(r, ensure_ascii=False, indent=1)); sys.exit(0)
    z = {"freigegeben": "✓", "entwurf": "…", "fehlt": "✗", "veraltet": "!", "ungeprüft": "?"}
    if r["ls_aus_skizze"]:
        i = r["ls_aus_skizze"]; print(f"LS {o.ls} laut Skizze: „{i['titel']}“, {i['stunden']} Std., LK {i['lk']}\n")
    for x in r["liste"]:
        print(f"{z[x['stand']]} {x['schritt']} {x['was']}: {x['stand']}" + (f" ({x['hinweis']})" if x["hinweis"] else ""))
    print("\nAnstehend:", ", ".join(f"{x['schritt']} {x['was']}" for x in r["reihenfolge"]) or "nichts")
