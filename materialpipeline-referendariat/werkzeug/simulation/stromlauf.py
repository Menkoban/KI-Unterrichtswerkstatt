"""Stromlaufplan als Netz für Simulationen: aus der Lage, die der Plan-Baukasten beim Zeichnen mitschreibt
(Zeichner.geo), entsteht ein Graph aus Knoten und Kanten. Die Simulation rechnet damit auf dem gezeichneten Plan,
nicht auf einer zweiten Beschreibung.

Kanten: ltg (Leitung, leitet immer), fest (Sicherung, Bimetall; leitet, solange nicht ausgelöst), kontakt (Schließer
oder Öffner), spule (Last zwischen zwei Knoten), wicklung (Motorwicklung), motor3 (Motor mit U1, V1, W1 = a, b, c). Leitungen verbinden sich nur an
Endpunkten: Ein Endpunkt, der auf einer anderen Leitung liegt, teilt diese (Abzweig); Kreuzungen ohne Endpunkt
bleiben getrennt.
"""


def _auf(p, a, b):
    """Liegt Punkt p im Inneren der waagerechten oder senkrechten Strecke a–b?"""
    (x, y), (x1, y1), (x2, y2) = p, a, b
    if x1 == x2 == x:
        return min(y1, y2) < y < max(y1, y2)
    if y1 == y2 == y:
        return min(x1, x2) < x < max(x1, x2)
    return False


def netz_aus_plan(geo, netz_y, x_ein=28.0):
    """geo: Zeichner.geo; netz_y: {"L1": y, …} der Netzleitungen; x_ein: linkes Ende der Netzleitungen.
    Rückgabe: dict(knoten=[(x, y)], kanten=[{…, a, b}], quellen={"L1": Knoten, …})."""
    leitungen = [g for g in geo if g["typ"] == "ltg"]
    glieder = [g for g in geo if g["typ"] != "ltg"]
    # Schräge Leitungen (z. B. Motoranschluss U1/W1 nach KKT) verbinden nur an ihren Enden
    enden = {p for g in geo for p in (g["a"], g["b"], g.get("c")) if p}
    teile = []
    for g in leitungen:
        auf = sorted([p for p in enden if _auf(p, g["a"], g["b"])] + [g["a"], g["b"]])
        teile += [dict(typ="ltg", a=p, b=q) for p, q in zip(auf, auf[1:])]
    knoten = sorted({p for g in teile + glieder for p in (g["a"], g["b"], g.get("c")) if p})
    nr = {p: i for i, p in enumerate(knoten)}
    kanten = []
    for g in teile + glieder:
        k = {s: w for s, w in g.items() if s not in ("a", "b", "c")}
        k["a"], k["b"] = nr[g["a"]], nr[g["b"]]
        if "c" in g:
            k["c"] = nr[g["c"]]
        kanten.append(k)
    quellen = {}
    for l, y in netz_y.items():
        p = (round(x_ein, 2), round(y, 2))
        if p not in nr:
            raise ValueError(f"Netzleitung {l} nicht gefunden")
        quellen[l] = nr[p]
    return dict(knoten=knoten, kanten=kanten, quellen=quellen)
