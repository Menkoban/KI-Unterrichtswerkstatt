"""Arbeitsplan einer selbstständigen Lernsituation (Profil lernsituation.form „selbststaendig_mit_geruest“,
lernsituation.planungstiefe „arbeitsplan_kurzskizze“; Lehrkraft 2026-10-25).

    python lernsituation/arbeitsplan.py <arbeitsbereich> <ls-kurz>

Daten:    <arbeitsbereich>/.daten/arbeitsplan/<ls-kurz>.json (Meilensteine, Lernpfad, Kriterien) und
          .daten/lernsituation/<ls-kurz>.json.
Ergebnis: <ordner>/Arbeitsplan_Planung.docx für die Lehrkraft und, sobald der Lernpfad Steckbriefe hat,
          <ordner>/Materialauftrag.docx für Pipeline 2; (Meilensteine mit Termin, Abgabe, Material und
          Angeleitetem, Lernpfad der Arbeitsblätter, Kontrolle, Kriterien, Prüfbericht). Den Arbeitsplan für die
          Lernenden baut Pipeline 2 aus diesen Daten; die Doppelstunden stehen als Kurzskizzen in .daten/stunde
          (Feld „arbeitsplan“, stunde/stunde.py).
Prüft: jedes Arbeitsblatt gehört zu genau einem Meilenstein, Nummern lückenlos, Meilensteine decken die
Zyklen der LS, Termine passen zu den Doppelstunden, Kriterien wortgleich mit der Bewertung der LS.
"""
import json, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from ls_ausarbeitung import STUFE, tabelle
sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "stunde"))
import stunde as stmod
sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "akten"))
import steckbrief as sbmod


def kriterien(ls):
    return [k.strip() for k in ls["bewertung"].split("·")]


def pruefen(ap, ls):
    b = []
    nummern = [x["nr"] for x in ap["lernpfad"]]
    if nummern != list(range(1, len(nummern) + 1)):
        b.append(["Fehler", f"Lernpfad nicht lückenlos nummeriert: {nummern}"])
    ms = {m["nr"] for m in ap["meilensteine"]}
    for x in ap["lernpfad"]:
        if x["meilenstein"] not in ms:
            b.append(["Fehler", f"AB {x['nr']} gehört zu keinem Meilenstein"])
    if len(ap["meilensteine"]) != len(ls.get("zyklen", [])):
        b.append(["Warnung", f"{len(ap['meilensteine'])} Meilensteine, aber {len(ls.get('zyklen', []))} Zyklen in der LS"])
    letzte = max(int(d["ds"]) for d in ls["doppelstunden"])
    for m in ap["meilensteine"]:
        if not 1 <= m["bis_ds"] <= letzte:
            b.append(["Fehler", f"Meilenstein {m['nr']}: Termin DS {m['bis_ds']} liegt außerhalb der LS"])
    if ap.get("kriterien") and ap["kriterien"] != kriterien(ls):
        b.append(["Warnung", "Kriterien weichen von der Bewertung der LS ab"])
    return b


def dokument(ap, ls, befunde):
    d = stmod.neu(hoch=False)
    d.add_heading(f"Arbeitsplan LS {ls['nr']}: {ls['titel']} (Planung)", 0)
    p = d.add_paragraph(f"Lernsituation selbstständig mit Gerüst · {ls['lernfeld']} · {ls['std']} Stunden · "
                        f"Stand {ap['datum']} · {ap['stand']}")
    p.runs[0].italic = True
    tabelle(d, None, [["Auftrag", ls["auftrag"]], ["Handlungsergebnis", ls["handlungsergebnis"]],
                      ["Arbeitsform", ap["arbeitsform"]], ["Kontrolle", ap["kontrolle"]],
                      ["Zeitplan der Lernenden", ap["zeitplan"]]], [5.0, 20.7])
    d.add_heading("Meilensteine", 1)
    tabelle(d, ["Nr.", "Meilenstein", "Spätestens", "Abgabe", "Arbeitsblätter", "Bereit liegt", "Angeleitet"],
            [[str(m["nr"]), m["titel"], m.get("termin") or f"Ende DS {m['bis_ds']}", m["abgabe"],
              ", ".join(f"AB {x['nr']}" for x in ap["lernpfad"] if x["meilenstein"] == m["nr"]),
              m["material"], m["angeleitet"]] for m in ap["meilensteine"]],
            [0.9, 3.6, 2.0, 5.0, 2.6, 5.6, 6.0], groesse=8.5)
    d.add_page_break()
    d.add_heading("Lernpfad (feste Reihenfolge, eigenes Tempo)", 1)
    tabelle(d, ["AB", "Titel", "Worum es geht", "Meilenst.", "Etwa in DS", "Fehlvorstellung"],
            [[str(x["nr"]), x["titel"], x["inhalt"], str(x["meilenstein"]), x["ds"], x.get("fv", "")]
             for x in ap["lernpfad"]], [1.0, 4.6, 11.6, 2.0, 2.0, 4.5], groesse=8)
    d.add_heading("Bewertet wird (Lehrkraft, Rückmeldung in der nächsten Stunde)", 1)
    for k in ap["kriterien"]:
        d.add_paragraph(k, style="List Bullet")
    d.add_heading("Prüfbericht", 1)
    tabelle(d, ["Stufe", "Befund"], befunde + ap["pruefbericht"], [2.6, 23.1], faerben=lambda z: STUFE[z[0]])
    return d


def anlagen(ap):
    """Steckbriefe für den Materialauftrag der LS: der Arbeitsplan der Lernenden und die Arbeitsblätter des Lernpfads."""
    return ([ap["arbeitsplan_anlage"]] if ap.get("arbeitsplan_anlage") else []) + \
        [dict(art="Arbeitsblatt", nr=x["nr"], titel=x["titel"], kurz=x["titel"], felder=x["felder"],
              erwartungshorizont=x["erwartungshorizont"]) for x in ap["lernpfad"] if x.get("felder")]


def pruefen_steckbriefe(ap):
    b = []
    for x in anlagen(ap):
        da = {k for k, v in x["felder"] if v.strip()}
        fehlen = [f for f in stmod.PFLICHTFELDER if f not in da]
        if fehlen:
            b.append(["Fehler", f"{stmod.zeichen(x)}: Steckbrief unvollständig, es fehlt " + ", ".join(fehlen)])
        if not x.get("erwartungshorizont"):
            b.append(["Fehler", f"{stmod.zeichen(x)} ohne Erwartungshorizont"])
        inhalt = dict(x["felder"]).get("Inhalt und Wortlaut", "")
        vorweg = [n for m, n in stmod.VORWEG.items() if re.search(m, inhalt, re.I)]
        if vorweg:
            b.append(["Warnung", f"{stmod.zeichen(x)}: Auftrag nimmt vorweg ({', '.join(vorweg)})"])
    ohne = [x["nr"] for x in ap["lernpfad"] if not x.get("felder")]
    if ohne and len(ohne) < len(ap["lernpfad"]):
        b.append(["Warnung", "Arbeitsblätter ohne Steckbrief: " + ", ".join(f"AB {n}" for n in ohne)])
    return b


def materialauftrag(ap, ls):
    s = dict(ds=f"1 bis {len(ls['doppelstunden'])}", titel=f"{ls['titel']} (Lernpfad)", datum=ap["datum"], stand=ap["stand"],
             material_allgemein=ap["material_allgemein"], gestaltung=ap["gestaltung"], anlagen=anlagen(ap))
    d = stmod.materialauftrag(s, ls)
    d.paragraphs[0].runs[0].text = f"Materialauftrag LS {ls['nr']}: {ls['titel']} (Arbeitsplan und Lernpfad)"
    return d


def erzeugen(ab, kurz):
    ab = pathlib.Path(ab)
    ap = json.loads((ab / ".daten" / "arbeitsplan" / f"{kurz}.json").read_text(encoding="utf-8"))
    ls = json.loads((ab / ".daten" / "lernsituation" / f"{kurz}.json").read_text(encoding="utf-8"))
    befunde = pruefen(ap, ls)
    ordner = ab / ap["ordner"]; ordner.mkdir(parents=True, exist_ok=True)
    z = ordner / "Arbeitsplan_Planung.docx"
    if any(x.get("felder") for x in ap["lernpfad"]):
        befunde += pruefen_steckbriefe(ap)
    dokument(ap, ls, befunde).save(z)
    if any(x.get("felder") for x in ap["lernpfad"]):
        m = ordner / "Materialauftrag.docx"
        materialauftrag(ap, ls).save(m)
        sbmod.schreiben(ab, str(m.relative_to(ab)), "arbeitsplan", f"LS {ls['nr']} Materialauftrag",
                        [str(z.relative_to(ab))], ls["fach"], "Schritt 14", ap)
    sbmod.schreiben(ab, str(z.relative_to(ab)), "arbeitsplan", f"LS {ls['nr']} Arbeitsplan",
                    [ls["ordner"] + "/Lernsituation.docx"], ls["fach"], "Schritt 12", ap)
    return z, befunde


def ab_nummern(ab, kurz):
    """Nummern der Arbeitsblätter im Lernpfad („AB 3“), für die Prüfung der Kurzskizzen."""
    p = pathlib.Path(ab) / ".daten" / "arbeitsplan" / f"{kurz}.json"
    return {f"AB {x['nr']}" for x in json.loads(p.read_text(encoding="utf-8"))["lernpfad"]}


if __name__ == "__main__":
    z, b = erzeugen(sys.argv[1], sys.argv[2]); print(z); [print(*x) for x in b]
