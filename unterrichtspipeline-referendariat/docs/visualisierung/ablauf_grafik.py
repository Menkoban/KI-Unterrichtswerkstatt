"""Ablaufgrafiken Pipeline 1 für die README: Übersicht der Schritte 00 bis 17 und Besuchsstunde Schritt für Schritt.

Aufruf: python3 docs/visualisierung/ablauf_grafik.py [zielordner]
  →  ablauf_unterrichtsplanung.svg und ablauf_besuchsstunde.svg (Standard: neben diesem Skript)
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from svgbau import (BLAU, BLAU_HELL, BLAU_MITTEL, GRAU, GRUEN, GRUEN_DUNKEL, GRUEN_HELL, LINIE, TINTE, Svg,  # noqa: E402
                    breite, kartenhoehe, umbrechen)

W, H = 1800, 1430
s = Svg(W, H, "Pipeline 1 Unterrichtsplanung: Ablauf der Schritte 00 bis 17 mit Profil und Freigaben")
s.kopf("Pipeline 1 · Unterrichtsplanung",
       "Schritte 00 bis 17 · zwölf Skills · von oben nach unten geplant, Stunde für Stunde unterrichtet · "
       "Stand 25.10.2026",
       [("Übungsphase", "#FFF3D6", "#8A5300"), ("erprobt an LF 1, LS 1 bis 3", GRUEN, TINTE)])

LX, LW = 40, 150          # Ebenen-Spalte
MX, MR = 232, 1520        # Hauptfläche
RX, RR = 1556, 1760       # rechte Spalte
GAP = 34

# Profil-Band ------------------------------------------------------------------------------------------------
s.rect(40, 128, W - 80, 62, fill=GRUEN_HELL, stroke=GRUEN, sw=1.6, name="Profil")
s.text(60, 156, "Profil der Lehrkraft", 18, fett=True, farbe=GRUEN_DUNKEL)
s.text(60, 178, "Profil/lehrkraft-profil.json", 12.5, mono=True, farbe=GRUEN_DUNKEL)
s.notiz(300, 154, 1440,
        "119 Einstellungen mit neutralem Standard im Werkzeug, Ihre Werte im Arbeitsbereich. Jeder Skill liest sie "
        "über profil.lade(); Ihre Werte gewinnen. Jede Korrektur wird sofort Profilwert, Regel oder Prüfung.",
        14.5, farbe=TINTE, kursiv=False)


def ebene(y, h, titel, unter):
    s.rect(LX, y, LW, h, fill=BLAU, stroke=BLAU, rx=12, name="Ebene " + titel)
    zt = umbrechen(titel, 17, LW - 24, fett=True)
    yy = s.zeilen(LX + 12, y + 28, zt, 17, 1.2, fett=True, farbe="#FFFFFF")
    s.zeilen(LX + 12, yy + 22, umbrechen(unter, 12.5, LW - 24), 12.5, 1.3, farbe="#DCE5F7")


def pfeil_rechts(x1, x2, y):
    s.pfeil([(x1 + 3, y), (x2 - 4, y)], farbe=BLAU)


def pfeil_runter(x, y1, y2, farbe=BLAU, dash=None):
    s.pfeil([(x, y1 + 2), (x, y2 - 4)], farbe=farbe, dash=dash)


# Einstieg ---------------------------------------------------------------------------------------------------
y0, h0 = 214, 112
ebene(y0, h0, "Einstieg", "je Anliegen")
s.karte(MX, y0, 640, h0, "00", "Was steht an?", "einstieg",
        "Ihre Ansage, frei oder als Sprachnachricht. Der Skill prüft die Akten (vorhanden, fehlt, veraltet) "
        "und schlägt die Reihenfolge der fehlenden Schritte vor.")
s.notiz(MX + 672, y0 + 26, MR - MX - 672,
        "Nur das Fehlende wird geplant, jede neue Akte mit eigener Freigabe. Vorhandenes zuerst: Schulplanung, "
        "Curriculum oder alte Entwürfe in Eingang/ hochladen, sonst wird komplett durchgeplant.", 14.5,
        farbe=GRAU, kursiv=False)

# Makro ------------------------------------------------------------------------------------------------------
y1 = y0 + h0 + 28
kw = (MR - MX - 3 * GAP) / 4
makro = [
    ("01", "Curriculare Analyse", "curriculare-analyse",
     "Rahmenlehrplan eng am Wortlaut: LK-01 … nach vollständiger Handlung; Inhalte Pflicht, Optional, "
     "Verschoben; Lernort Betrieb", "Curriculare_Analyse.docx"),
    ("02", "Lernsituationen-Skizze", "lernsituationen-skizze",
     "Lernsituationen mit Handlungsergebnis, echter Entscheidung, LK mit Legende und Stunden; ohne Kalender",
     "Lernsituationen_Skizze.docx"),
    ("02", "Modellbetrieb", "modellbetrieb",
     "fiktiver Betrieb je Beruf als durchgehende Handlungssituation: Steckbrief, Personen, Kunden",
     "Modellbetrieb_<Name>.docx"),
    ("03", "Jahresplanung", "jahresplanung",
     "Lernfelder des Schuljahres mit Zeitrichtwert; Wochen erst mit Stundenplan, Kalender aus amtlicher Quelle",
     "Jahresplanung.docx"),
]
h1 = max(kartenhoehe(kw, n, t, sk, tx, f, freigabe="Freigabe") for n, t, sk, tx, f in makro)
ebene(y1, h1, "Makro", "je Lernfeld, Beruf oder Schuljahr, wiederverwendbar")
for i, (n, t, sk, tx, f) in enumerate(makro):
    x = MX + i * (kw + GAP)
    s.karte(x, y1, kw, h1, n, t, sk, tx, f, freigabe="Freigabe")
    if i:
        pfeil_rechts(x - GAP, x, y1 + h1 / 2)
pfeil_runter(MX + kw / 2, y0 + h0, y1)

# Meso -------------------------------------------------------------------------------------------------------
y2 = y1 + h1 + 28
kw5 = (MR - MX - 4 * GAP) / 5
meso = [
    ("04", "Lernsituation", "lernsituation",
     "Kernkompetenz, Handlungssituation, Auftrag, Bewertung; Zyklen über Doppelstunden, je DS Leitfrage und "
     "Teilergebnis", "Lernsituation.docx", False),
    ("05", "Bedingungsfeld", "klassenakte",
     "je Klasse nach Seminar-Leitfaden 1.1 bis 1.5, je Bedingung eine Konsequenz; drei Personas; "
     "kommentierter Sitzplan; nur Kürzel", "Bedingungsfeld.docx Sitzplan.docx", False),
    ("06", "Lernausgangslage der Klasse", "klassenakte",
     "Klassenteil von 06: allgemeine Lernausgangslage je Bereich, jede Einschätzung mit Quelle; laufend aus "
     "den Nachbereitungen", "Lernausgangslage.docx", False),
    ("06", "Fehlvorstellungen", "fehlvorstellungen",
     "Thementeil von 06: Lernausgangslage je Inhalt der LS; je Fehlvorstellung Beleg, Herkunft, Priorität, "
     "Diagnose-Item, Aufgreifen", "Fehlvorstellungen.docx", False),
    ("LS", "Arbeitsplan", "lernsituation · selbstständige LS",
     "Meilensteine mit spätestem Termin, fester Lernpfad, Kriterien; daraus der Materialauftrag der ganzen LS",
     "Arbeitsplan_Planung.docx", True),
]
h2 = max(kartenhoehe(kw5, n, t, sk, tx, f, freigabe="Freigabe", titel_groesse=15.5, text_groesse=14) for n, t, sk, tx, f, _ in meso)
ebene(y2, h2, "Meso", "je Lernsituation bzw. Klasse")
for i, (n, t, sk, tx, f, gs) in enumerate(meso):
    x = MX + i * (kw5 + GAP)
    s.karte(x, y2, kw5, h2, n, t, sk, tx, f, freigabe="Freigabe", gestrichelt=gs, titel_groesse=15.5,
            text_groesse=14)
    if i:
        pfeil_rechts(x - GAP, x, y2 + h2 / 2)
pfeil_runter(MX + kw / 2, y1 + h1, y2)

# Mikro ------------------------------------------------------------------------------------------------------
y3 = y2 + h2 + 28
tw = 196
vx = MX + tw + 46
vw = MR - vx
LBW = 210                  # Beschriftung links in jeder Zeile
GZ = 12
cx0 = vx + LBW
cwr = MR - 12 - cx0        # Breite für die Schritt-Karten einer Zeile

T13 = ("Mikro-Einstieg mit dem, was feststeht; Interview Frage für Frage (Einstieg, Arbeitsblatt, Sozialform, "
       "Sicherung, Besonderheiten); Verlauf mit Zeiten in Seminarspalten. 07 bis 12 und 16 laufen mit, ohne eigenes "
       "Dokument: Teilkompetenzen mit „indem“, Methoden aus Interview und Profil, Fehlvorstellungen im Mikro-Einstieg, "
       "typische Fehler im Erwartungshorizont")
T14 = ("je Anlage ein ausführlicher Steckbrief (Zweck, Phase, TK, Inhalt, Aufbau, Hilfen, Quellen, "
       "Abnahmekriterien) und Erwartungshorizont; Anlagen chronologisch")
TKS = ("Verlaufsplanung auf einer Seite in Seminarspalten für die Ausbildungslehrkraft, mit Rüstzeiten, Rundgang und "
       "Kontrolle am Ende der DS; Abgleich mit dem Lernpfad; kein eigener Materialauftrag je DS; 07 bis 12 und 16 "
       "laufen mit wie bei der Alltagsstunde")
cw2 = (cwr - GAP) / 2
hA = max(kartenhoehe(cw2, "13", "Verlaufsskizze", None, T13, "Verlaufsskizze.docx Verlaufsskizze_Seminar.docx"),
         kartenhoehe(cw2, "14", "Materialauftrag", None, T14, "Materialauftrag.docx")) + 2 * GZ
hB = kartenhoehe(cwr, "KS", "Kurzskizze je DS", None, TKS, "Stunden-Akte mit Feld arbeitsplan") + 2 * GZ
besuch = [("07", "Sachanalyse", "Kap. 2.3"), ("08", "Auswahl und Reduktion", "Kap. 2.4"),
          ("09", "Kompetenzen", "Kap. 2.2, Kompetenztabelle"), ("10", "Einordnung", "Kap. 2.1, Sequenzierung"),
          ("11", "Methoden", "Kap. 3"), ("12", "Differenzierung", "Kap. 2.4 und 3"),
          ("16", "Antizipation", "interne Notiz zur Stunde")]
PRO_REIHE = 4
chw = (cwr - (PRO_REIHE - 1) * 10) / PRO_REIHE
NBW = breite("00", 13, True) + 14


def _chip_zeilen(tt, kap):
    return umbrechen(tt, 14, chw - 28 - NBW, fett=True), umbrechen(kap, 12.5, chw - 20)


chip_h = max(26 + (len(a) - 1) * 18 + 8 + len(b) * 17 + 10 for a, b in (_chip_zeilen(tt, k) for _, tt, k in besuch))
TB = ("dazu 13 und 14 wie bei der Alltagsstunde; 15 ist in 09 enthalten. Ergebnis: Entwurf_<Art>.docx, "
      "einzeln in der Grafik „Besuchsstunde Schritt für Schritt“")
hC = GZ + 2 * chip_h + 10 + 12 + len(umbrechen(TB, 13.5, cwr)) * 18 + 8 + GZ
zeilen_h = [max(hA, 118), max(hB, 118), max(hC, 118)]
h3 = sum(zeilen_h) + 2 * 12
ebene(y3, h3, "Mikro", "je Doppelstunde, Tiefe nach Stundentyp")
s.rect(MX, y3, tw, h3, fill=BLAU_HELL, stroke=BLAU_MITTEL, name="Stundentyp")
s.text(MX + 16, y3 + h3 / 2 - 70, "Stundentyp", 17, fett=True, farbe=BLAU)
s.text(MX + 16, y3 + h3 / 2 - 48, "zuerst klären", 17, fett=True, farbe=BLAU)
s.notiz(MX + 16, y3 + h3 / 2 - 16, tw - 30,
        "Alltag oder Besuch? Ist es nicht gesagt, fragt die Stundenplanung zuerst danach. Selbstständige LS "
        "laut Profil lernsituation.form.", 13.5, farbe=TINTE, kursiv=False)
pfeil_runter(MX + kw + GAP + kw / 2, y2 + h2, y3)


def zeile(y, h, titel, unter, skill, freigabe, gestrichelt=False):
    s.rect(vx, y, vw, h, fill="#FBFCFE", stroke=BLAU if gestrichelt else BLAU_MITTEL,
           dash="6 4" if gestrichelt else None, name="Zeile " + titel)
    yy = s.zeilen(vx + 14, y + 30, umbrechen(titel, 16.5, LBW - 28, fett=True), 16.5, 1.2, fett=True, farbe=BLAU)
    yy = s.zeilen(vx + 14, yy + 20, umbrechen(unter, 13, LBW - 28), 13, 1.3, farbe=TINTE)
    s.text(vx + 14, yy + 20, skill, 12.5, mono=True, farbe=GRAU)
    s.pille(vx + 14, yy + 32, freigabe)
    if yy + 32 + 21 > y + h - 6:
        raise ValueError("Zeile zu niedrig: " + titel)
    s.pfeil([(MX + tw + 2, y3 + h3 / 2), (MX + tw + 22, y3 + h3 / 2), (MX + tw + 22, y + h / 2), (vx - 4, y + h / 2)],
            farbe=BLAU)


ya = y3
zeile(ya, zeilen_h[0], "Alltagsstunde", "gelenkte LS", "stundenplanung", "eine Freigabe am Ende")
s.karte(cx0, ya + GZ, cw2, zeilen_h[0] - 2 * GZ, "13", "Verlaufsskizze", None, T13,
        "Verlaufsskizze.docx Verlaufsskizze_Seminar.docx")
s.karte(cx0 + cw2 + GAP, ya + GZ, cw2, zeilen_h[0] - 2 * GZ, "14", "Materialauftrag", None, T14,
        "Materialauftrag.docx")
pfeil_rechts(cx0 + cw2, cx0 + cw2 + GAP, ya + zeilen_h[0] / 2)
yb = ya + zeilen_h[0] + 12
zeile(yb, zeilen_h[1], "Selbstständige LS", "mit Arbeitsplan", "stundenplanung", "Freigabe", gestrichelt=True)
s.karte(cx0, yb + GZ, cwr, zeilen_h[1] - 2 * GZ, "KS", "Kurzskizze je DS", None, TKS,
        "Stunden-Akte mit Feld arbeitsplan")
yc = yb + zeilen_h[1] + 12
zeile(yc, zeilen_h[2], "Besuchsstunde", "EUB, KUB, FLB, GUB, PU", "besuchsstunde", "Freigabe je Schritt")
for i, (n, tt, kap) in enumerate(besuch):
    x = cx0 + (i % PRO_REIHE) * (chw + 10)
    y = yc + GZ + (i // PRO_REIHE) * (chip_h + 10)
    s.rect(x, y, chw, chip_h, fill="#FFFFFF", stroke=BLAU_MITTEL, rx=10, name="Besuch " + n)
    s.teile.append(f'<rect x="{x + 10:.1f}" y="{y + 9:.1f}" width="{NBW:.1f}" height="21" rx="6" fill="{BLAU}"/>')
    s.text(x + 10 + NBW / 2, y + 24, n, 13, fett=True, farbe="#FFFFFF", anker="middle")
    za, zb = _chip_zeilen(tt, kap)
    yy = s.zeilen(x + 10 + NBW + 8, y + 25, za, 14, 1.28, fett=True)
    s.zeilen(x + 10, yy + 21, zb, 12.5, 1.36, farbe=GRAU)
s.notiz(cx0, yc + GZ + 2 * chip_h + 10 + 26, cwr, TB, 13.5, farbe=GRAU, kursiv=False)
hz = zeilen_h[0]

# Nach der Stunde --------------------------------------------------------------------------------------------
y4 = y3 + h3 + 30
nw = 640
mw = (MR - MX - nw - 2 * GAP) / 2
T17 = ("frei gesprochen, auch als Sprachnachricht; jede Aussage nach Reichweite abgelegt: Stunde, Klasse, "
       "Lernsituation oder Profil")
TM = "alle Akten einer Planung in einem DOCX mit Einführung für Schule, Mentor oder Seminar"
TW = "Planungsstand je LS, Ansicht-PDFs, Freigabe-Knöpfe, Chat mit der Arbeitssitzung"
h4 = max(kartenhoehe(nw, "17", "Nachbereitung", "nachbereitung", T17, "Nachbereitung.docx",
                     freigabe="Ablage bestätigen"),
         kartenhoehe(mw, "M", "Planungsmappe", "planungsmappe", TM),
         kartenhoehe(mw, "W", "Stand und Werkbank", "akten/stand.py · akten/app.py", TW))
ebene(y4, h4, "Nach der Stunde", "laufend und auf Abruf")
s.karte(MX, y4, nw, h4, "17", "Nachbereitung", "nachbereitung",
        T17, "Nachbereitung.docx", freigabe="Ablage bestätigen")
s.karte(MX + nw + GAP, y4, mw, h4, "M", "Planungsmappe", "planungsmappe",
        TM)
s.karte(MX + nw + 2 * GAP + mw, y4, mw, h4, "W", "Stand und Werkbank", "akten/stand.py · akten/app.py",
        TW)
# Pfeile: Stunde → Nachbereitung, offene Punkte zurück
ax = MX + 560
pfeil_runter(ax, y3 + h3, y4)
s.pfeil([(MX + 110, y4 - 2), (MX + 110, y3 + h3 + 4)], farbe=GRUEN_DUNKEL, dash="5 4")
s.text(MX + 122, y3 + h3 + 20, "offene Punkte am Anfang der nächsten Stundenplanung", 12.5, farbe=GRUEN_DUNKEL,
       fett=True)
# Nachbereitung → Profil (links außen)
s.pfeil([(MX, y4 + h4 - 26), (MX - 18, y4 + h4 - 26), (MX - 18, 190 + 4)], farbe=GRUEN_DUNKEL, dash="5 4")

# Rechte Spalte: Ablage und Übergabe --------------------------------------------------------------------------
rw = RR - RX
s.rect(RX, y0, rw, y1 + h1 - y0, fill="#FFFFFF", stroke=BLAU_MITTEL, name="Ablage")
s.text(RX + 14, y0 + 30, "Ablage im", 17, fett=True, farbe=BLAU)
s.text(RX + 14, y0 + 52, "Arbeitsbereich", 17, fett=True, farbe=BLAU)
yy = y0 + 84
for pfad, was in [("<Fach>/<Beruf>/<LF>/", "Lernfeld, Modellbetrieb"), ("…/<LS>/", "wiederverwendbare Planung"),
                  ("Unterricht/<Klasse>/", "Stunden: LF › LS › UE"), (".daten/", "Daten, Steckbriefe, freigaben.json")]:
    s.text(RX + 14, yy, pfad, 12.5, mono=True, farbe=BLAU)
    yy = s.zeilen(RX + 14, yy + 19, umbrechen(was, 13.5, rw - 28), 13.5, 1.3, farbe=TINTE) + 30
s.notiz(RX + 14, yy, rw - 28, "nur Daten; das Werkzeug bleibt allgemein", 13, farbe=GRAU)

py, ph = y2, y3 + h3 - y2
s.rect(RX, py, rw, ph, fill=BLAU, stroke=BLAU, name="Übergabe")
s.text(RX + 14, py + 32, "Übergabe an", 18, fett=True, farbe="#FFFFFF")
s.text(RX + 14, py + 56, "Pipeline 2", 18, fett=True, farbe=GRUEN)
yy = py + 90
for absatz in ["Materialauftrag je Stunde (Schritt 14) oder je selbstständiger LS aus dem Arbeitsplan.",
               "Steckbrief je Anlage: Zweck, Phase, Teilkompetenz, Inhalt, Aufbau, Quellen, Abnahme, "
               "Erwartungshorizont.",
               "Fertiges Material kommt nach Anlagen/ im Stundenordner zurück."]:
    yy = s.zeilen(RX + 14, yy, umbrechen(absatz, 14, rw - 28), 14, 1.36, farbe="#FFFFFF") + 30
s.text(RX + 14, yy, "Materialauftrag.docx", 12.5, mono=True, farbe=GRUEN)
s.text(RX + 14, yy + 18, ".daten/stunde/<kurz>.json", 11.5, mono=True, farbe=GRUEN)
if yy + 30 > py + ph:
    raise ValueError("Übergabe-Kasten zu klein")
# Pfeile in die Übergabe
s.pfeil([(MR + 2, y2 + h2 / 2), (RX - 4, y2 + h2 / 2)], farbe=BLAU)
s.pfeil([(MR + 2, y3 + hz / 2), (RX - 4, y3 + hz / 2)], farbe=BLAU)

# Legende ----------------------------------------------------------------------------------------------------
ly = y4 + h4 + 26
s.h = H = ly + 92 + 24
s.rect(40, ly, W - 80, H - ly - 24, fill="#FFFFFF", stroke=BLAU_MITTEL, name="Legende")
pw = s.pille(60, ly + 18, "Freigabe")
s.notiz(60 + pw + 14, ly + 34, 1010,
        "Vor jeder Freigabe: Prüfbericht (Fehler, Warnung, Hinweis) und Leseseite (neu, selbst entschieden, "
        "unsicher). Eintrag in .daten/freigaben.json mit Zahl der grundsätzlichen Korrekturen; zweimal ohne "
        "Korrektur: künftig Gesamtblick.", 14, farbe=TINTE, kursiv=False)
lx2 = 1190
s.rect(lx2, ly + 16, 46, 26, fill="#FFFFFF", stroke=BLAU, rx=6, dash="6 4")
s.text(lx2 + 58, ly + 34, "nur bei selbstständiger LS", 14, farbe=TINTE)
s.pfeil([(lx2, ly + 66), (lx2 + 44, ly + 66)], farbe=GRUEN_DUNKEL, dash="5 4")
s.text(lx2 + 58, ly + 71, "Rückfluss aus der Nachbereitung", 14, farbe=TINTE)
s.text(W - 60, ly + 71, "Lernende nur als Kürzel (S01 …)", 14, farbe=GRAU, anker="end")

ORDNER = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent
print(s.speichern(ORDNER / "ablauf_unterrichtsplanung.svg"))


# =============================================================================================================
# Zweite Grafik: Besuchsstunde Schritt für Schritt (07 bis 16)
# =============================================================================================================
b = Svg(W, 2000, "Pipeline 1 Besuchsstunde: Schritte 07 bis 16 und wie sie in den Entwurf eingehen")
b.kopf("Pipeline 1 · Besuchsstunde Schritt für Schritt",
       "Schritte 07 bis 16 · Skill besuchsstunde · Entwurf nach den Vorgaben des Seminars (Seminarprofil) · "
       "Stand 25.10.2026",
       [("Übungsphase", "#FFF3D6", "#8A5300"), ("erprobt an EUB, KUB, GUB, PU", GRUEN, TINTE)])
L2, R2 = 40, W - 40

# Eingang ----------------------------------------------------------------------------------------------------
ey, eh = 128, 112
ew = (R2 - L2 - 2 * 24) / 3
baender = [
    ("Eingang", "Lernsituation (04), Bedingungsfeld (05), Lernausgangslage und Fehlvorstellungen (06); "
                "Besuchsart (EUB, KUB, FLB, GUB, PU) aus der Ref-Akte", BLAU, "#FFFFFF", "#FFFFFF"),
    ("Entscheidungen einzeln", "je Entscheidung kurzer Kontext, drei gleich ausführliche Vorschläge, der "
                               "empfohlene zuerst, dazu freie Antwort; jede Entscheidung als Zeile im KONZEPT",
     "#FFFFFF", BLAU, TINTE),
    ("Profil der Lehrkraft", "z. B. Gestaltung von Besuchsstunden (besuch.gestaltung), Seminarfassung ohne "
                             "Minuten und ohne Hinweise zu einzelnen Lernenden", GRUEN_HELL, GRUEN_DUNKEL, TINTE),
]
for i, (tt, tx, fill, tf, xf) in enumerate(baender):
    x = L2 + i * (ew + 24)
    b.rect(x, ey, ew, eh, fill=fill, stroke=fill if fill == BLAU else (GRUEN if fill == GRUEN_HELL else BLAU_MITTEL),
           sw=1.4, name=tt)
    b.text(x + 16, ey + 28, tt, 17, fett=True, farbe=tf)
    ende = b.notiz(x + 16, ey + 52, ew - 32, tx, 13.5, farbe=xf, kursiv=False)
    if ende + 10 > ey + eh:
        raise ValueError("Band zu klein: " + tt)

# Schritte ---------------------------------------------------------------------------------------------------
G2 = 40
sw3 = (R2 - L2 - 2 * G2) / 3
schritte = [
    ("07", "Sachanalyse", "besuchsstunde",
     "Analyse der Thematik mit schlichten Zwischenüberschriften: Bedeutung für die berufliche Wirklichkeit, das "
     "Fach selbst, übergreifende Bezüge (auch zu anderen Fächern), Komplexität, Schwierigkeit und Abstraktion",
     "Kap. 2.3, höchstens 1,5 Seiten · als Text nur bei GUB und PU"),
    ("08", "Auswahl und Reduktion", "besuchsstunde",
     "Reduktion nach Grüner, vertikal und horizontal: fachlich korrekt, ausbaufähig, angemessen; jede "
     "Vereinfachung wird intern gegen die Fehlvorstellungen geprüft",
     "Kap. 2.4, 1 Seite · als Text nur bei GUB und PU"),
    ("09", "Kompetenzen", "besuchsstunde",
     "Kernkompetenz der Stunde ohne Handlungsebene; Kompetenztabelle nach Seminar-Muster (… indem …, "
     "Kompetenzbereich in Klammern); Schritt 15 Kompetenzfeststellung ist hier enthalten",
     "Kap. 2.2, 0,5 Seiten · Kompetenztabelle in Anhang I"),
    ("10", "Einordnung", "besuchsstunde",
     "Rahmenlehrplan, Verortung, Legitimation der Kernkompetenz der LS; Sequenzierung in der Seminar-Vorlage, "
     "im Original befüllt, mit Zeile Handlungssituation",
     "Kap. 2.1, 0,5 Seiten · Sequenzierung in Anhang I"),
    ("11", "Methoden", "besuchsstunde",
     "Gestaltung der Verlaufsstruktur: Varianten mit Kontext zur Wahl; dazu intern je Phase Begründung, Vor- "
     "und Nachteile und die verworfene Alternative",
     "Kap. 3, 1 Seite"),
    ("12", "Differenzierung", "besuchsstunde",
     "je Stunde aus einem offenen Werkzeugkasten vorgeschlagen, die Lehrkraft wählt; gestützt auf die Diagnose "
     "in der Klassen-Akte",
     "fließt in Kap. 2.4 und Kap. 3 · kommentierter Sitzplan in Anhang I"),
    ("13", "Verlaufsskizze", "stundenplanung",
     "Seminarspalten im Hochformat: Phase, Lerninhalte, methodische Entscheidungen mit Lehrer- und "
     "Schüleraktivitäten, Aktions- und Sozialformen, Medien; Anlagen nummeriert",
     "Anhang I, höchstens 2 Seiten"),
    ("14", "Materialauftrag", "stundenplanung",
     "kein Material in Pipeline 1, sondern je Anlage ein ausführlicher Steckbrief an Pipeline 2; das fertige "
     "Material wird an den Entwurf angehängt",
     "Anhang II Material"),
    ("16", "Antizipation", "besuchsstunde",
     "interne Notiz je Phase: Stolperstelle, woran erkennbar, Reaktion oder Impuls, Hilfe aus dem Material; "
     "Plan B für Zeitnot, Zeitüberschuss, Technikausfall, Sicherheit",
     "fließt in Kap. 3 · Fehlvorstellungen stehen nur hier, nicht im Entwurf"),
]
hs = max(kartenhoehe(sw3, n, tt, sk, tx, None, freigabe="Freigabe", hinweis=hw) for n, tt, sk, tx, hw in schritte)
y = ey + eh + 44
b.pfeil([(L2 + sw3 / 2, ey + eh + 2), (L2 + sw3 / 2, y - 4)], farbe=BLAU)
for r in range(3):
    for c in range(3):
        n, tt, sk, tx, hw = schritte[3 * r + c]
        x = L2 + c * (sw3 + G2)
        b.karte(x, y, sw3, hs, n, tt, sk, tx, None, freigabe="Freigabe", hinweis=hw)
        if c < 2:
            b.pfeil([(x + sw3 + 2, y + hs / 2), (x + sw3 + G2 - 4, y + hs / 2)], farbe=BLAU)
    if r < 2:
        xr, xl, ym = L2 + 2 * (sw3 + G2) + sw3 / 2, L2 + sw3 / 2, y + hs + 20
        b.pfeil([(xr, y + hs + 2), (xr, ym), (xl, ym), (xl, y + hs + 40 - 4)], farbe=BLAU)
    y += hs + 40

# Entwurf ----------------------------------------------------------------------------------------------------
y += 4
b.text(L2, y + 18, "Daraus setzt entwurf/entwurf.py den Entwurf zusammen", 17, fett=True, farbe=BLAU)
y += 34
kw_ = 500
gw_ = 660
zw_ = R2 - L2 - kw_ - gw_ - 2 * 24
TK = ("ohne Fließtext: Deckblatt nach Seminar-Muster, Kernkompetenz, Kompetenztabelle, Verlaufsskizze, "
      "Sequenzierung mit Handlungssituation, kommentierter Sitzplan, Literatur, Material, Zielvereinbarungen. "
      "Beim KUB zusätzlich Beobachtungsbogen und KUB-Protokoll.")
budget = [("Kap. 1", "Analyse des Bedingungsfeldes", "1,5", "05 (+ 06)"),
          ("Kap. 2.1", "Analyse der curricularen Vorgaben", "0,5", "10"),
          ("Kap. 2.2", "Angestrebte Kompetenzen", "0,5", "09"),
          ("Kap. 2.3", "Analyse der Thematik", "1,5", "07"),
          ("Kap. 2.4", "Auswahl- und Reduktionsentscheidungen", "1", "08 (+ 12)"),
          ("Kap. 3", "Gestaltung der Verlaufsstruktur", "1", "11 (+ 12, 16)")]
hb = 52 + 24 + len(budget) * 26 + 44
hk = max(52 + len(umbrechen(TK, 14, kw_ - 32)) * 19 + 16, hb)
hb = hk
b.rect(L2, y, kw_, hk, fill="#FFFFFF", stroke=BLAU_MITTEL, name="Kurzentwurf")
b.text(L2 + 16, y + 30, "Kurzentwurf: EUB, KUB, FLB", 17, fett=True, farbe=BLAU)
b.notiz(L2 + 16, y + 56, kw_ - 32, TK, 14, farbe=TINTE, kursiv=False)
gx = L2 + kw_ + 24
b.rect(gx, y, gw_, hb, fill="#FFFFFF", stroke=BLAU_MITTEL, name="Voller Entwurf")
b.text(gx + 16, y + 30, "Voller Entwurf: GUB, PU", 17, fett=True, farbe=BLAU)
cols = [gx + 16, gx + 100, gx + 470, gx + 540]
yy = y + 58
for ct, cx_ in zip(["Teil", "Inhalt", "Seiten", "aus Schritt"], cols):
    b.text(cx_, yy, ct, 12.5, fett=True, farbe=GRAU)
for teil, inhalt, seiten, aus in budget:
    yy += 26
    b.teile.append(f'<line x1="{gx + 16}" y1="{yy - 18:.1f}" x2="{gx + gw_ - 16}" y2="{yy - 18:.1f}" '
                   f'stroke="{LINIE}" stroke-width="1"/>')
    for wert, cx_, fett in zip([teil, inhalt, seiten, aus], cols, [True, False, False, False]):
        b.text(cx_, yy, wert, 14, fett=fett, farbe=TINTE)
    if breite(inhalt, 14) > cols[2] - cols[1] - 10 or breite(aus, 14) > gx + gw_ - 16 - cols[3]:
        raise ValueError("Tabellenspalte zu schmal: " + inhalt)
b.notiz(gx + 16, yy + 30, gw_ - 32, "Kap. 1 bis 3 höchstens sechs Seiten, im fertigen Satz gemessen; dazu Anhang, "
        "Literatur nach APA 7, Versicherung und KI-Verzeichnis", 13.5, farbe=GRAU, kursiv=False)
zx = gx + gw_ + 24
b.rect(zx, y, zw_, hb, fill=BLAU, stroke=BLAU, name="Erzeugen")
b.text(zx + 16, y + 30, "Ergebnis", 17, fett=True, farbe="#FFFFFF")
ende = b.notiz(zx + 16, y + 56, zw_ - 32,
               "zuerst stunde/stunde.py (13, 14), dann entwurf/entwurf.py; GUB und PU in zwei Durchläufen mit "
               "gemessenem Seitenbudget. Persönliche Felder des Deckblatts bleiben Platzhalter.", 14,
               farbe="#FFFFFF", kursiv=False)
for i, f in enumerate(["Entwurf_<Art>.docx", "Pruefbericht_Entwurf_<Art>.docx", "KUB_Protokoll.docx (KUB)"]):
    b.text(zx + 16, y + hb - 56 + i * 19, f, 12.5, mono=True, farbe=GRUEN)
if ende + 30 > y + hb - 56:
    raise ValueError("Ergebnis-Kasten zu klein")

# Legende ----------------------------------------------------------------------------------------------------
ly = y + hb + 26
b.rect(L2, ly, R2 - L2, 60, fill="#FFFFFF", stroke=BLAU_MITTEL, name="Legende")
pw_ = b.pille(L2 + 18, ly + 18, "Freigabe")
b.text(L2 + 18 + pw_ + 14, ly + 35, "Besuchsstunden werden Schritt für Schritt freigegeben, je Schritt mit "
       "Prüfbericht (Fehler, Warnung, Hinweis); vor der Freigabe Sichtprüfung und Abgleich mit den "
       "Seminar-Originalen.", 14, farbe=TINTE)
b.h = ly + 60 + 24
print(b.speichern(ORDNER / "ablauf_besuchsstunde.svg"))
