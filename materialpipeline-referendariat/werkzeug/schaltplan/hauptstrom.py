"""Bausteine des Hauptstromkreises (dreipolig, Polabstand 8 mm). Jeder Baustein beginnt an den drei
Anschlüssen (xs, y) und gibt die y-Lage der unteren Anschlüsse zurück. Regeln wie in plan.py:
Anschlussbezeichnungen rechts, Kennzeichen und Daten links, Leitungen nur zwischen Anschlusspunkten."""
from plan import KONTAKT, Zeichner


def _anr3(zn, xs, y, oben, unten, halb=0.0):
    for x, o, u in zip(xs, oben, unten):
        zn.anr(x, y, o, u, halb)


def einspeisung(zn: Zeichner, xs, netz_y, y):
    for x, l in zip(xs, ("L1", "L2", "L3")):
        zn.ltg(x, netz_y[l], x, y)
        zn.punkt(x, netz_y[l])
    return y


def sicherung3(zn: Zeichner, xs, y, bmk, daten=""):
    for x in xs:
        zn.tikz(f"\\pzSicherung{{{x:.2f}}}{{{y:.2f}}}")
        zn.glied("fest", bmk, x, y)
    _anr3(zn, xs, y, "135", "246", halb=1.0)
    zn.bmk(xs[0] - 3, y - 2.6, bmk, daten)
    y -= KONTAKT
    for x in xs:
        zn.ltg(x, y, x, y - 4)
    return y - 4


def wendeschuetz(zn: Zeichner, xs, y, q1, q2, abstand=40.0):
    """Zwei Schützgruppen, -Q2 rechts daneben, Phasentausch L1 ↔ L3 unter den Kontakten."""
    xd = [x + abstand for x in xs]
    for i, (x, x2) in enumerate(zip(xs, xd)):
        ya = y - 4 * (i + 1)
        zn.ltg(x, ya, x2, ya)
        zn.ltg(x2, ya, x2, y - 16)
        zn.punkt(x, ya)
    for x in xs:
        zn.ltg(x, y, x, y - 16)
    y0 = y - 16
    for gruppe, bmk in ((xs, q1), (xd, q2)):
        w = []
        for x in gruppe:
            zn.n += 1
            w.append(f"w{zn.n}")
            zn.tikz(f"\\pzSchuetz{{{x:.2f}}}{{{y0:.2f}}}{{w{zn.n}}}")
            zn.glied("kontakt", bmk, x, y0, art="S", bet="")
            zn.kontakte.append((bmk, "S", "", "", x))
        zn.wirklinie(gruppe[0] - 1.111, y0 - 4, gruppe[-1] - 1.111, y0 - 4)
        _anr3(zn, gruppe, y0, "135", "246")
        zn.bmk(gruppe[0] - 4.5, y0 - 2.6, bmk)
    yu = y0 - KONTAKT
    # Phasentausch: -Q2 Pol 1 (L1) an W, Pol 2 an V, Pol 3 (L3) an U
    for k, (von, nach) in enumerate(((xd[0], xs[2]), (xd[1], xs[1]), (xd[2], xs[0]))):
        yy = yu - 4 * (k + 1)
        zn.ltg(von, yu, von, yy)
        zn.ltg(von, yy, nach, yy)
        zn.punkt(nach, yy)
    zn.tikz(f"\\node[dat,anchor=west] at ({xd[0] + 2:.2f},{yu - 17:.2f}) {{Phasentausch L1 ↔ L3}};")
    ende = yu - 16
    for x in xs:
        zn.ltg(x, yu, x, ende)
    # Hauptkontakte im Kontaktspiegel mit Anschlüssen
    zn.kontakte = [k for k in zn.kontakte if not (k[0] in (q1, q2) and k[2] == "")]
    for gruppe, bmk in ((xs, q1), (xd, q2)):
        for x, (o, u) in zip(gruppe, (("1", "2"), ("3", "4"), ("5", "6"))):
            zn.kontakte.append((bmk, "S", o, u, x))
    return ende


def thermo3(zn: Zeichner, xs, y, bmk, daten=""):
    for x in xs:
        zn.tikz(f"\\pzThermo{{{x:.2f}}}{{{y:.2f}}}")
        zn.glied("fest", bmk, x, y)
    for x, o, u in zip(xs, "135", "246"):
        zn.tikz(f"\\node[anr,anchor=south west] at ({x + 0.8:.2f},{y - 1.9:.2f}) {{{o}}};")
        zn.tikz(f"\\node[anr,anchor=north west] at ({x + 0.8:.2f},{y - 6.1:.2f}) {{{u}}};")
    zn.bmk(xs[0] - 5, y - 2.6, bmk, daten)
    y -= KONTAKT
    for x in xs:
        zn.ltg(x, y, x, y - 6)
    return y - 6


def klemmen(zn: Zeichner, xs, y, bmk, pe_x=None, nummern="123"):
    for x, n in zip(xs, nummern):
        zn.oben.append(f"\\pzKlemme{{({x:.2f},{y:.2f})}}")
        zn.tikz(f"\\node[anr,anchor=west] at ({x + 1:.2f},{y + 1.4:.2f}) {{{n}}};")
    if pe_x is not None:
        zn.oben.append(f"\\pzKlemme{{({pe_x:.2f},{y:.2f})}}")
        zn.tikz(f"\\node[anr,anchor=west] at ({pe_x + 1:.2f},{y + 1.4:.2f}) {{PE}};")
    zn.bmk(xs[0] - 3, y, bmk)
    return y


def motor(zn: Zeichner, xs, y, bmk, daten="", pe=None):
    """Drehstrommotor Ø 12 mm; V1 senkrecht bis an den Kreis, U1/W1 schräg (KKT S. 24/26).
    pe = (x, y_bus): PE-Leiter von der Sammelschiene waagerecht an den Kreis."""
    xa, xb, xc = xs
    yc = y - 14
    zn.ltg(xb, y, xb, yc + 6)                                    # V1 bis an den Kreis (Regel 21)
    for x, w in ((xa, 120), (xc, 60)):
        import math
        px, py = xb + 6 * math.cos(math.radians(w)), yc + 6 * math.sin(math.radians(w))
        zn.ltg(x, y, x, yc + 9)
        zn.ltg(x, yc + 9, px, py)
    zn.tikz(f"\\pzMotor{{({xb:.2f},{yc:.2f})}}")
    # Anschlüsse U1, V1, W1 am Kreis für die Simulation (Drehrichtung aus der Phasenfolge)
    ende = {x: (round(xb + 6 * math.cos(math.radians(w)), 2), round(yc + 6 * math.sin(math.radians(w)), 2))
            for x, w in ((xa, 120), (xc, 60))}
    zn.geo.append(dict(typ="motor3", bmk=bmk, a=ende[xa], b=(round(xb, 2), round(yc + 6, 2)), c=ende[xc]))
    for x, t in zip(xs, ("U1", "V1", "W1")):
        zn.tikz(f"\\node[anr,anchor=west] at ({x + 0.8:.2f},{y - 4.5:.2f}) {{{t}}};")
    zn.bmk(xa - 6, yc + 1, bmk, daten)
    if pe:
        px, pyb = pe
        zn.ltg(px, pyb, px, yc)
        zn.ltg(px, yc, xb + 6, yc)
        zn.punkt(px, pyb)
        zn.tikz(f"\\node[anr,anchor=south] at ({(px + xb + 6) / 2:.2f},{yc:.2f}) {{PE}};")
    return yc - 6


def _schuetzgruppe(zn: Zeichner, gruppe, y0, bmk, zusatz=""):
    """Drei Hauptkontakte 07-13-02 nebeneinander mit gemeinsamer Wirkverbindung; Kontaktspiegel 1–2, 3–4, 5–6."""
    for x in gruppe:
        zn.n += 1
        zn.tikz(f"\\pzSchuetz{{{x:.2f}}}{{{y0:.2f}}}{{w{zn.n}}}")
        zn.glied("kontakt", bmk, x, y0, art="S", bet="")
    zn.wirklinie(gruppe[0] - 1.111, y0 - 4, gruppe[-1] - 1.111, y0 - 4)
    _anr3(zn, gruppe, y0, "135", "246")
    zn.bmk(gruppe[0] - 4.5, y0 - 2.6, bmk, zusatz)
    for x, (o, u) in zip(gruppe, (("1", "2"), ("3", "4"), ("5", "6"))):
        zn.kontakte.append((bmk, "S", o, u, x))


def netz_und_dreieck(zn: Zeichner, xs, y, q_netz, q_dreieck, abstand=40.0, zusatz=("Netz", "Dreieck")):
    """Netzschütz in der Hauptachse, Dreieckschütz rechts daneben, beide hinter der Sicherung abgegriffen
    (je Strangstrom 0,58 · I_N). Gibt (y unten, Abgänge des Dreieckschützes) zurück."""
    xd = [x + abstand for x in xs]
    for i, (x, x2) in enumerate(zip(xs, xd)):
        ya = y - 4 * (i + 1)
        zn.ltg(x, ya, x2, ya)
        zn.ltg(x2, ya, x2, y - 16)
        zn.punkt(x, ya)
    for x in xs:
        zn.ltg(x, y, x, y - 16)
    y0 = y - 16
    _schuetzgruppe(zn, xs, y0, q_netz, zusatz[0])
    _schuetzgruppe(zn, xd, y0, q_dreieck, zusatz[1])
    return y0 - KONTAKT, xd


def motor6(zn: Zeichner, xs, y, bmk, daten="", unten=("W2", "U2", "V2"), pe=None):
    """Drehstrommotor mit sechs Anschlüssen (Stern-Dreieck): oben U1, V1, W1 wie motor(), unten in der Reihenfolge
    des Klemmbretts W2, U2, V2 (Dreieck: U1–W2, V1–U2, W1–V2 liegen übereinander). Gibt y der unteren Anschlüsse."""
    import math
    xa, xb, xc = xs
    yc = y - 14
    zn.ltg(xb, y, xb, yc + 6)
    zn.ltg(xb, yc - 6, xb, yc - 14)
    for x, w in ((xa, 120), (xc, 60)):
        px, py = xb + 6 * math.cos(math.radians(w)), yc + 6 * math.sin(math.radians(w))
        zn.ltg(x, y, x, yc + 9)
        zn.ltg(x, yc + 9, px, py)
        qx, qy = xb + 6 * math.cos(math.radians(-w)), yc + 6 * math.sin(math.radians(-w))
        zn.ltg(qx, qy, x, yc - 9)
        zn.ltg(x, yc - 9, x, yc - 14)
    zn.tikz(f"\\pzMotor{{({xb:.2f},{yc:.2f})}}")
    for x, t in zip(xs, ("U1", "V1", "W1")):
        zn.tikz(f"\\node[anr,anchor=west] at ({x + 0.8:.2f},{y - 4.5:.2f}) {{{t}}};")
    for x, t in zip(xs, unten):
        zn.tikz(f"\\node[anr,anchor=west] at ({x + 0.8:.2f},{yc - 10.5:.2f}) {{{t}}};")
    zn.bmk(xa - 6, yc + 1, bmk, daten)
    if pe:
        px, pyb = pe
        zn.ltg(px, pyb, px, yc)
        zn.ltg(px, yc, xb + 6, yc)
        zn.punkt(px, pyb)
        zn.tikz(f"\\node[anr,anchor=south] at ({px - 6:.2f},{yc:.2f}) {{PE}};")
    return yc - 14


def stern(zn: Zeichner, xs, y, q_stern, xd, y_dreieck, laengen=(10.0, 15.0, 20.0), zusatz="Stern"):
    """Unter den unteren Motoranschlüssen: Abgänge des Dreieckschützes (xd) waagerecht an die Leitungen
    W2, U2, V2 (Verbindungspunkt), darunter das Sternschütz; dessen Ausgänge bilden den Sternpunkt."""
    # Abgänge des Dreieckschützes: senkrecht bis zur eigenen Höhe, dann nach links (Höhe fällt mit dem Pol,
    # damit sich die Abgänge nicht gegenseitig kreuzen)
    for i, (x, xq) in enumerate(zip(xs, xd)):
        yr = y - laengen[i]
        zn.ltg(xq, y_dreieck, xq, yr)
        zn.ltg(xq, yr, x, yr)
        zn.punkt(x, yr)
    y0 = y - laengen[-1] - 6
    for x in xs:
        zn.ltg(x, y, x, y0)
    _schuetzgruppe(zn, list(xs), y0, q_stern, zusatz)
    yu = y0 - KONTAKT
    ys = yu - 4
    for x in xs:
        zn.ltg(x, yu, x, ys)
    zn.ltg(xs[0], ys, xs[-1], ys)
    zn.punkt(xs[1], ys)
    zn.tikz(f"\\node[dat,anchor=west] at ({xs[-1] + 2:.2f},{ys:.2f}) {{Sternpunkt}};")
    return ys


def sterndreieck(zn: Zeichner, xs, y, q_netz, q_stern, q_dreieck, f2, f2_daten, motor_bmk, motor_daten,
                 pe_x, pe_bus, abstand=48.0, r_motor=8.0):
    """Hauptstromkreis Stern-Dreieck nach Herstellerplänen (Moeller-Katalog SDAINL, Siemens 24499345 Bild 6):
    Netz-, Dreieck- und Sternschütz nebeneinander auf einer Höhe; Dreieckschütz hinter der Sicherung, vor dem
    Netzschütz abgegriffen; Sternbrücke oben am Sternschütz (1–3–5); Motorschutzrelais hinter dem Netzschütz im
    Strang U1, V1, W1 (0,58 · I_N); Motor mit seitlichen Anschlüssen, Vorzugsschaltung L1–U1–V2, L2–V1–W2,
    L3–W1–U2 (Siemens S. 5). Die Leitungen sind so geführt, dass nur die drei Verbindungen Sternschütz →
    Dreieckschütz Leitungen kreuzen (wie Moeller). Gibt y unter dem Motor zurück."""
    import math
    xd = [x + abstand for x in xs]                       # Dreieckschütz
    xq = [x + 2 * abstand for x in xs]                   # Sternschütz
    # Abgriff für das Dreieckschütz (wie Wendeschütz)
    for i, (x, x2) in enumerate(zip(xs, xd)):
        ya = y - 4 * (i + 1)
        zn.ltg(x, ya, x2, ya)
        zn.ltg(x2, ya, x2, y - 16)
        zn.punkt(x, ya)
    for x in xs:
        zn.ltg(x, y, x, y - 16)
    y0 = y - 16
    _schuetzgruppe(zn, list(xs), y0, q_netz, "Netz")
    _schuetzgruppe(zn, xd, y0, q_dreieck, "Dreieck")
    _schuetzgruppe(zn, xq, y0, q_stern, "Stern")
    # Sternbrücke oben am Sternschütz
    yb = y0 + 4
    for x in xq:
        zn.ltg(x, y0, x, yb)
    zn.ltg(xq[0], yb, xq[-1], yb)
    zn.punkt(xq[1], yb)
    zn.tikz(f"\\node[dat,anchor=south] at ({xq[1]:.2f},{yb + 0.6:.2f}) {{Sternbrücke}};")
    yu = y0 - KONTAKT
    # Motorschutzrelais hinter dem Netzschütz
    for x in xs:
        zn.ltg(x, yu, x, yu - 6)
    ye = thermo3(zn, xs, yu - 6, f2, f2_daten)
    # Sternschütz 2/4/6 an das Dreieckschütz 2/4/6: Pol 1 an den nächsten Leiter (U2-Seite), Höhe fällt nach außen
    ziele = (xd[2], xd[1], xd[0])
    for k, (x, xz) in enumerate(zip(xq, ziele)):
        yj = yu - 6 - 5 * k
        zn.ltg(x, yu, x, yj)
        zn.ltg(x, yj, xz, yj)
        zn.punkt(xz, yj)
    # Klemmen -X1 auf einer Höhe: 1 U1, 2 V1, 3 W1, 4 U2, 5 V2, 6 W2
    yk = ye - 4
    klemmen(zn, xs, yk, "-X1", nummern="123")
    klemmen(zn, xd, yk, "", nummern="564")
    # Motor zwischen Netz- und Dreieckseite; Leitungen waagerecht an den Kreis
    xm = (xs[-1] + xd[0]) / 2
    ym = ye - 22
    r = r_motor
    a = 5.0                                              # Abstand der seitlichen Anschlüsse
    links = ((xs[2], a, "W1"), (xs[1], 0, "V1"), (xs[0], -a, "U1"))
    rechts = ((xd[0], a, "V2"), (xd[1], 0, "W2"), (xd[2], -a, "U2"))
    for (x, dy, t) in links:
        rand = xm - math.sqrt(r * r - dy * dy)
        zn.ltg(x, ye, x, ym + dy)
        zn.ltg(x, ym + dy, rand, ym + dy)
        zn.tikz(f"\\node[anr,anchor=south east] at ({rand - 0.8:.2f},{ym + dy + 0.2:.2f}) {{{t}}};")
    for (x, dy, t) in rechts:
        rand = xm + math.sqrt(r * r - dy * dy)
        zn.ltg(x, yu, x, ym + dy)
        zn.ltg(x, ym + dy, rand, ym + dy)
        zn.tikz(f"\\node[anr,anchor=south west] at ({rand + 0.8:.2f},{ym + dy + 0.2:.2f}) {{{t}}};")
    zn.tikz(f"\\pzMotorR{{({xm:.2f},{ym:.2f})}}{{{r}}}")
    # Wicklungen für die Simulation: Anfang U1/V1/W1 links, Ende U2/V2/W2 rechts (gleiches dy wie oben)
    ende = {t: (round(xm + math.sqrt(r * r - dy * dy), 2), round(ym + dy, 2)) for _, dy, t in rechts}
    for _, dy, t in links:
        zn.geo.append(dict(typ="wicklung", bmk=motor_bmk, name=t[0],
                           a=(round(xm - math.sqrt(r * r - dy * dy), 2), round(ym + dy, 2)), b=ende[t[0] + "2"]))
    zn.bmk(xs[0] - 3, ym, motor_bmk, motor_daten)       # Kennzeichen links (Regel 23)
    # Schutzleiter von unten an den Motor (kreuzt keine Leitung)
    yp = ym - r - 6
    zn.ltg(pe_x, pe_bus, pe_x, yp)
    zn.ltg(pe_x, yp, xm, yp)
    zn.ltg(xm, yp, xm, ym - r)
    zn.punkt(pe_x, pe_bus)
    zn.tikz(f"\\node[anr,anchor=south] at ({(pe_x + xm) / 2:.2f},{yp:.2f}) {{PE}};")
    return yp, xd, xq
