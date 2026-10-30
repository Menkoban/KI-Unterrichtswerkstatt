"""Schulkalender: Ferien aus amtlicher Datei, Feiertage nach dem Niedersächsischen Feiertagsgesetz
(Neujahr, Karfreitag, Ostermontag, 1. Mai, Christi Himmelfahrt, Pfingstmontag, Tag der Deutschen
Einheit, Reformationstag, 1. und 2. Weihnachtstag), Ostern nach der Gaußschen Osterformel.
Nie aus dem Gedächtnis: Ferien kommen nur aus der JSON mit Quelle."""
import datetime as dt, json, pathlib

T = dt.timedelta


def ostersonntag(j):
    a, b, c = j % 19, j // 100, j % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25; g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    monat = (h + l - 7 * m + 114) // 31; tag = (h + l - 7 * m + 114) % 31 + 1
    return dt.date(j, monat, tag)


def feiertage_niedersachsen(j):
    o = ostersonntag(j)
    return {dt.date(j, 1, 1): "Neujahr", o - T(2): "Karfreitag", o + T(1): "Ostermontag",
            dt.date(j, 5, 1): "Tag der Arbeit", o + T(39): "Christi Himmelfahrt", o + T(50): "Pfingstmontag",
            dt.date(j, 10, 3): "Tag der Deutschen Einheit", dt.date(j, 10, 31): "Reformationstag",
            dt.date(j, 12, 25): "1. Weihnachtstag", dt.date(j, 12, 26): "2. Weihnachtstag"}


def laden(pfad):
    k = json.loads(pathlib.Path(pfad).read_text(encoding="utf-8"))
    k["_start"] = dt.date.fromisoformat(k["erster_schultag"]); k["_ende"] = dt.date.fromisoformat(k["letzter_schultag"])
    k["_ferien"] = [(n, dt.date.fromisoformat(a), dt.date.fromisoformat(b)) for n, a, b in k["ferien"]]
    ft = {}
    for j in range(k["_start"].year, k["_ende"].year + 1):
        ft.update(feiertage_niedersachsen(j))
    k["_feiertage"] = {d: n for d, n in ft.items() if k["_start"] <= d <= k["_ende"]}
    return k


def frei(k, d):
    """None, wenn Schultag; sonst Grund."""
    if d.weekday() >= 5: return "Wochenende"
    for n, a, b in k["_ferien"]:
        if a <= d <= b: return n
    return k["_feiertage"].get(d)


def wochen(k):
    """Je Kalenderwoche: Montag, Schultage (Mo–Fr) und freie Werktage mit Grund."""
    montag = k["_start"] - T(k["_start"].weekday()); out = []
    while montag <= k["_ende"]:
        tage = [montag + T(i) for i in range(5)]
        tage = [d for d in tage if k["_start"] <= d <= k["_ende"]]
        schul = [d for d in tage if not frei(k, d)]
        frei_ = [(d, frei(k, d)) for d in tage if frei(k, d)]
        out.append({"kw": montag.isocalendar()[1], "montag": montag, "schultage": schul, "frei": frei_})
        montag += T(7)
    return out
