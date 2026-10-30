"""Ablaufgrafik Pipeline 3 (Moodle-Themenkurs) für die README.

Aufruf: python3 docs/visualisierung/ablauf_grafik.py  →  docs/visualisierung/ablauf_moodle.svg
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from svgbau import (BLAU, BLAU_HELL, BLAU_MITTEL, GRAU, GRUEN, GRUEN_DUNKEL, GRUEN_HELL, TINTE, Svg,  # noqa: E402
                    breite, kartenhoehe, umbrechen)

W = 1800
s = Svg(W, 2000, "Pipeline 3 Moodle: Ablauf vom Eingang bis zur Kurssicherung")
s.kopf("Pipeline 3 · Moodle-Themenkurs",
       "Skill themenkurs · aus einer fertigen Lernsituation ein Kurs für Moodle ab 5.0 · Bau nach Freigabe in "
       "höchstens 30 Minuten · Stand 25.10.2026",
       [("Übungsphase", "#FFF3D6", "#8A5300"), ("Kurs LS 1 gebaut", GRUEN, TINTE)])

L, R = 40, 1760
GAP = 40
nb = breite("0", 13, True) + 14


def nummer(x, y, n):
    b = breite(n, 13, True) + 14
    s.teile.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{b:.1f}" height="21" rx="6" fill="{BLAU}"/>')
    s.text(x + b / 2, y + 15, n, 13, fett=True, farbe="#FFFFFF", anker="middle")
    return b


def block(x, y, w, h, titel, text, fill, titelfarbe, textfarbe, datei=None, name=None, dateifarbe=GRUEN):
    s.rect(x, y, w, h, fill=fill, stroke=fill if fill == BLAU else (GRUEN if fill == GRUEN_HELL else BLAU_MITTEL),
           sw=1.4, name=name or titel)
    s.text(x + 16, y + 28, titel, 17, fett=True, farbe=titelfarbe)
    ende = s.notiz(x + 16, y + 52, w - 32, text, 13.5, farbe=textfarbe, kursiv=False)
    if datei:
        s.text(x + 16, y + h - 16, datei, 12, mono=True, farbe=dateifarbe)
        if ende + 22 > y + h - 16:
            raise ValueError("Block zu klein: " + titel)
    elif ende + 10 > y + h:
        raise ValueError("Block zu klein: " + titel)


# Eingang ----------------------------------------------------------------------------------------------------
ey, eh = 128, 120
ew = (R - L - 2 * 24) / 3
block(L, ey, ew, eh, "aus Pipeline 1: Planung",
      "Lernsituation mit Leitfragen, Teilkompetenzen und Bewertung; Fehlvorstellungen mit Diagnose-Items; "
      "Klassen-Akte (Niveau, Sprache)", BLAU, "#FFFFFF", "#FFFFFF", ".daten/lernsituation/<ls>.json")
block(L + ew + 24, ey, ew, eh, "aus Pipeline 2: Material",
      "Anlagen aller Doppelstunden, Gesamtfassung mit Infotexten, Erwartungshorizonte, Glossar-Daten",
      BLAU, "#FFFFFF", "#FFFFFF", "Anlagen/uebergabe.json · glossar_dsnn.json")
block(L + 2 * (ew + 24), ey, ew, eh, "Profil der Lehrkraft",
      "Gruppe Moodle (Kachelformat, Schulfarben, Freischaltung, Sterne und Medaillen, KI-Hinweis …) und "
      "lehrkraft.* für den Steckbrief", GRUEN_HELL, GRUEN_DUNKEL, TINTE, "python3 werkzeug/arbeitsbereich.py",
      dateifarbe=GRUEN_DUNKEL)

# Reihe 1: Eingang lesen, Grilling, Kursplan --------------------------------------------------------------------
y1 = ey + eh + 44
w1, w3 = 470, 470
w2 = R - L - w1 - w3 - 2 * GAP
k1 = ("1", "Eingang lesen", None,
      "die ganze Lernsituation als Rohstoff; was Pipeline 1 und 2 schon entschieden haben, wird nicht neu "
      "gefragt", None, None)
k2 = ("2", "Grilling bis zum gemeinsamen Kursplan", None,
      "erste Frage immer: Umfang des Kurses. Dann eine Frage zur Zeit, drei gleich ausführliche Vorschläge und "
      "freie Antwort; didaktischer Sparringspartner, widerspricht begründet mit Alternative", None, None)
k3 = ("", "Kursplan", None,
      "wächst nach jeder Antwort mit: je Aktivität Teilkompetenz, Phase, Fehlvorstellung, Lernzeit, Sozialform; "
      "Sterne, Rückblick, Lehrkraftbereich", "Kursplan.docx", "Freigabe = Startsignal")
h1 = max(kartenhoehe(w1, *k1[:5], freigabe=k1[5]), kartenhoehe(w2, *k2[:5], freigabe=k2[5]),
         kartenhoehe(w3, *k3[:5], freigabe=k3[5]))
x = L
for i, (k, w) in enumerate([(k1, w1), (k2, w2), (k3, w3)]):
    s.karte(x, y1, w, h1, k[0], k[1], k[2], k[3], k[4], freigabe=k[5], fill=GRUEN_HELL if i == 2 else "#FFFFFF")
    if i < 2:
        s.pfeil([(x + w + 2, y1 + h1 / 2), (x + w + GAP - 4, y1 + h1 / 2)], farbe=BLAU)
    x += w + GAP
for xx in (L + ew / 2, L + ew + 24 + ew / 2):
    s.pfeil([(xx, ey + eh + 2), (xx, y1 - 4)], farbe=BLAU)
s.pfeil([(L + 2 * (ew + 24) + ew / 2, ey + eh + 2), (L + 2 * (ew + 24) + ew / 2, y1 - 4)], farbe=GRUEN_DUNKEL,
        dash="5 4")

# Reihe 2: Bau in einem Lauf -----------------------------------------------------------------------------------
y2 = y1 + h1 + 44
s.pfeil([(R - w3 / 2, y1 + h1 + 2), (R - w3 / 2, y2 - 4)], farbe=BLAU)
pad = 18
h2 = 270
s.rect(L, y2, R - L, h2, fill="#FFFFFF", stroke=BLAU_MITTEL, name="Bau")
b = nummer(L + pad, y2 + 16, "3")
s.text(L + pad + b + 10, y2 + 32, "Bau in einem Lauf, ohne Rückfragen", 18, fett=True)
s.text(L + pad + b + 10 + breite("Bau in einem Lauf, ohne Rückfragen", 18, True) + 16, y2 + 32,
       "Ergebnis je Schritt im Arbeitsbereich unter <LS>/Moodle/", 14, farbe=GRAU)
iy, ih = y2 + 58, h2 - 58 - 18
# Helfer parallel
hw = 470
s.rect(L + pad, iy, hw, ih, fill=BLAU_HELL, stroke=BLAU_MITTEL, rx=10, name="Helfer")
s.text(L + pad + 14, iy + 26, "Helfer je Abschnitt, alle parallel", 15.5, fett=True, farbe=BLAU)
s.notiz(L + pad + 14, iy + 48, hw - 28,
        "Kurstext in Sie-Form, Fragen aus dem Material (Distraktoren als Fehlvorstellungen, Rechnungen mit "
        "Zufallswerten), Aktivitäten; je Abschnitt ein Teil der Kursdefinition (abschnitt_N.json)", 13.5, farbe=TINTE, kursiv=False)
cw = (hw - 28 - 3 * 10) / 4
for i, t in enumerate(["Abschnitt 1", "Abschnitt 2", "Abschnitt 3", "Abschnitt n"]):
    cx = L + pad + 14 + i * (cw + 10)
    s.rect(cx, iy + ih - 50, cw, 36, fill="#FFFFFF", stroke=BLAU_MITTEL, rx=8, name="Helfer " + t)
    s.text(cx + cw / 2, iy + ih - 27, t, 12.5, fett=True, farbe=BLAU, anker="middle")
# Zusammenbau
zx = L + pad + hw + GAP
zw = 330
s.pfeil([(L + pad + hw + 2, iy + ih / 2), (zx - 4, iy + ih / 2)], farbe=BLAU)
s.rect(zx, iy, zw, ih, fill="#FFFFFF", stroke=BLAU_MITTEL, rx=10, name="Zusammenbau")
s.text(zx + 14, iy + 26, "Zusammenbau per Programm", 15.5, fett=True, farbe=BLAU)
s.notiz(zx + 14, iy + 48, zw - 28, "ohne KI: Kursdefinition (JSON) wird zur Kurssicherung", 13.5, farbe=TINTE,
        kursiv=False)
s.text(zx + 14, iy + ih - 34, "werkzeug/mbz/kursdefinition.py", 12, mono=True, farbe=BLAU)
s.text(zx + 14, iy + ih - 16, "werkzeug/mbz/bauen.py", 12, mono=True, farbe=BLAU)
# Prüfer
px_ = zx + zw + GAP
pw = 520
s.pfeil([(zx + zw + 2, iy + ih / 2), (px_ - 4, iy + ih / 2)], farbe=BLAU)
s.rect(px_, iy, pw, ih, fill="#FFFFFF", stroke=BLAU_MITTEL, rx=10, name="Prüfer")
s.text(px_ + 14, iy + 26, "Neun schützende Prüfer", 15.5, fett=True, farbe=BLAU)
chips = ["einspielbar", "Lösungen verborgen", "gerechnete Fragen", "keine leeren Hüllen", "Angekündigtes vorhanden",
         "Medaillen lückenlos", "Alternativtexte", "Abgabe je Kachel", "Sternzähler"]
cx, cy = px_ + 14, iy + 42
for c in chips:
    cwid = breite(c, 12.5) + 18
    if cx + cwid > px_ + pw - 14:
        cx, cy = px_ + 14, cy + 32
    s.rect(cx, cy, cwid, 24, fill=BLAU_HELL, stroke=BLAU_MITTEL, rx=12, name="Chip " + c)
    s.text(cx + cwid / 2, cy + 16.5, c, 12.5, farbe=TINTE, anker="middle")
    cx += cwid + 8
if cy + 24 > iy + ih - 40:
    raise ValueError("Prüfer-Chips passen nicht")
s.text(px_ + 14, iy + ih - 16, "werkzeug/mbz/pruefen.py", 12, mono=True, farbe=BLAU)
# Rücklauf bei Fehlern
s.pfeil([(px_ + pw / 2, iy + ih + 2), (px_ + pw / 2, iy + ih + 12), (zx + zw / 2, iy + ih + 12),
         (zx + zw / 2, iy + ih + 4)], farbe="#B42318", sw=1.8, dash="5 4")
# Werkbank live
wx = px_ + pw + GAP
ww = R - pad - wx
s.pfeil([(px_ + pw + 2, iy + ih / 2), (wx - 4, iy + ih / 2)], farbe=GRUEN_DUNKEL, dash="5 4")
s.rect(wx, iy, ww, ih, fill=GRUEN_HELL, stroke=GRUEN, rx=10, name="Werkbank")
s.text(wx + 14, iy + 26, "Live in der Werkbank", 15.5, fett=True, farbe=GRUEN_DUNKEL)
s.notiz(wx + 14, iy + 48, ww - 28,
        "Sie sehen den Kurs Kachel für Kachel entstehen, nach jedem fertigen Abschnitt neu", 13.5,
        farbe=TINTE, kursiv=False)
s.text(wx + 14, iy + ih - 16, "werkzeug/mbz/vorschau.py", 12, mono=True, farbe=GRUEN_DUNKEL)

# Reihe 3: Sichtprüfung, Prüfbericht, Abnahme, Ablage -----------------------------------------------------------
y3 = y2 + h2 + 44
s.pfeil([(L + 180, y2 + h2 + 2), (L + 180, y3 - 4)], farbe=BLAU)
karten3 = [
    ("4", "Sichtprüfung", None,
     "Vorschaubilder je Abschnitt; ein frischer Helfer klickt den Kurs in der Rolle der Lernenden durch", None,
     None),
    ("", "Prüfbericht", None,
     "Fehler, Warnung, Hinweis; Leseseite: neu, selbst entschieden, unsicher", None, "Abnahme"),
    ("5", "Ablage", None,
     "Kursplan, Kursdefinition, Bauskript und Sicherung unter <LS>/Moodle/ im Arbeitsbereich",
     "<Klasse>-LFnn-LSnn.mbz", None),
    ("", "Einspielen", None,
     "immer als neuer Kurs, erst im Test-Moodle, dann im Moodle der Schule; Anleitung für alle Kurse",
     "docs/anleitung_einspielen.md", None),
]
k3w = (R - L - 3 * GAP) / 4
h3 = max(kartenhoehe(k3w, *k[:5], freigabe=k[5]) for k in karten3)
x = L
for i, k in enumerate(karten3):
    fill = BLAU_HELL if i == 3 else "#FFFFFF"
    s.karte(x, y3, k3w, h3, k[0], k[1], k[2], k[3], k[4], freigabe=k[5], fill=fill)
    if i < 3:
        s.pfeil([(x + k3w + 2, y3 + h3 / 2), (x + k3w + GAP - 4, y3 + h3 / 2)], farbe=BLAU)
    x += k3w + GAP

# Kursaufbau ---------------------------------------------------------------------------------------------------
ky = y3 + h3 + 34
s.text(L, ky + 18, "So sieht der Themenkurs aus (ein Kurs je Lernsituation)", 17, fett=True, farbe=BLAU)
kachel = [
    ("Allgemein", "Vorgeschmack, Steckbrief, „So arbeiten Sie“, Schullogo mit dem einzigen KI-Hinweis",
     BLAU_HELL, BLAU),
    ("1 Einstieg", "volle Handlungssituation als Auftrag, Selbsteinschätzung, Eingangstest", "#FFFFFF", BLAU),
    ("2 … n je Leitfrage", "ein Abschnitt je Leitfrage einer DS; Auftrag im Kacheltext, jede Kachel mit Abgabe",
     "#FFFFFF", BLAU),
    ("Rückblick", "Selbsteinschätzung, Generalprobe, Abschlusstest, Medaillen, Glossar, Evaluationsbogen",
     "#FFFFFF", BLAU),
    ("Lehrkraftbereich", "verborgen: Druckvorlagen, Handreichung, Kursplan, Erwartungshorizonte, Dashboard",
     GRUEN_HELL, GRUEN_DUNKEL),
]
kw_ = (R - L - 4 * 14) / 5
kh = max(36 + len(umbrechen(t, 13.5, kw_ - 28)) * 18.4 + 14 for _, t, _, _ in kachel)
for i, (t, tx, fill, farbe) in enumerate(kachel):
    x = L + i * (kw_ + 14)
    s.rect(x, ky + 34, kw_, kh, fill=fill, stroke=GRUEN if fill == GRUEN_HELL else BLAU_MITTEL, rx=10,
           dash="6 4" if t == "Lehrkraftbereich" else None, name="Kachel " + t)
    s.teile.append(f'<rect x="{x:.1f}" y="{ky + 34:.1f}" width="{kw_:.1f}" height="6" rx="3" fill="{farbe}"/>')
    s.text(x + 14, ky + 34 + 30, t, 15.5, fett=True, farbe=farbe)
    s.zeilen(x + 14, ky + 34 + 52, umbrechen(tx, 13.5, kw_ - 28), 13.5, 1.36, farbe=TINTE)
fy = ky + 34 + kh + 26
s.notiz(L, fy, R - L,
        "Sterne als eine Währung für den ganzen Kurs, Medaillen erst nach dem Abschlusstest. In Moodle nur "
        "automatisierte Bewertung; Abgaben ohne Note, die Lehrkraft bewertet außerhalb des Kurses. Lernende "
        "erscheinen nur als Kürzel.", 14, farbe=GRAU, kursiv=False)

# Legende ------------------------------------------------------------------------------------------------------
ly = fy + 34
lh = 56
s.rect(L, ly, R - L, lh, fill="#FFFFFF", stroke=BLAU_MITTEL, name="Legende")
pw_ = s.pille(L + 18, ly + 16, "Freigabe · Abnahme")
s.text(L + 18 + pw_ + 14, ly + 33, "nur zwei Freigaben: Kursplan vor dem Bau, Abnahme danach; Eintrag in "
       ".daten/freigaben.json (Art moodle)", 14, farbe=TINTE)
l2 = L + 1230
s.pfeil([(l2, ly + 28), (l2 + 44, ly + 28)], farbe="#B42318", sw=1.8, dash="5 4")
s.text(l2 + 58, ly + 33, "Fehler: beheben und neu bauen", 14, farbe=TINTE)
s.h = ly + lh + 24

ziel = pathlib.Path(__file__).resolve().parent / "ablauf_moodle.svg"
if len(sys.argv) > 1:
    ziel = pathlib.Path(sys.argv[1])
s.speichern(ziel)
print(ziel)
