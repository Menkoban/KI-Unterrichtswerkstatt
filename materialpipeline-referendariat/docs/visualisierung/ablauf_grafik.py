"""Ablaufgrafik Pipeline 2 (Material) für die README.

Aufruf: python3 docs/visualisierung/ablauf_grafik.py  →  docs/visualisierung/ablauf_material.svg
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from svgbau import (BLAU, BLAU_HELL, BLAU_MITTEL, GRAU, GRUEN, GRUEN_DUNKEL, GRUEN_HELL, TINTE, Svg,  # noqa: E402
                    breite, kartenhoehe, umbrechen)

W = 1800
s = Svg(W, 2000, "Pipeline 2 Material: Ablauf vom Materialauftrag bis zur Übergabe an Pipeline 3")
s.kopf("Pipeline 2 · Materialerstellung",
       "Hauptskill materialauftrag · vom Materialauftrag zu fertigem Material · Ergebnisse im persönlichen "
       "Arbeitsbereich · Stand 25.10.2026",
       [("Übungsphase", "#FFF3D6", "#8A5300"), ("LF 1, LS 1 bis 3 gebaut", GRUEN, TINTE)])

L, R = 76, 1760           # Fläche; links davon die Rücklauf-Linie
GAP = 40

# Eingangsbänder ---------------------------------------------------------------------------------------------
by, bh = 128, 76
bw = (R - L - 24) / 2
s.rect(L, by, bw, bh, fill=GRUEN_HELL, stroke=GRUEN, sw=1.6, name="Profil")
s.text(L + 18, by + 28, "Profil der Lehrkraft", 18, fett=True, farbe=GRUEN_DUNKEL)
s.notiz(L + 18, by + 52, bw - 36,
        "Gruppen Material und Form: ein Niveau, effektive Lernzeit, schriftliche Hilfen, Merkkasten, "
        "Fassungen", 13.5, farbe=TINTE, kursiv=False)
rx = L + bw + 24
s.rect(rx, by, bw, bh, fill=BLAU_HELL, stroke=BLAU_MITTEL, sw=1.4, name="Regeln")
s.text(rx + 18, by + 28, "Regeln im Werkzeug", 18, fett=True, farbe=BLAU)
s.notiz(rx + 18, by + 52, bw - 36,
        "docs/regeln/stilregeln.md, pruefcheckliste.md, Checklisten für Pläne; abgenommene Muster in "
        "docs/stilreferenz/", 13.5, farbe=TINTE, kursiv=False)

# Reihe 1: Eingang, Lesen, Lücken, Materialplan ---------------------------------------------------------------
y1 = by + bh + 34
ew = 270
rest = R - L - ew - 3 * GAP
w1, w2, w3 = rest * 0.38, rest * 0.26, rest * 0.36
karten1 = [
    ("1", "Lesen und Bibliothek prüfen", None,
     "Materialauftrag mit Steckbrief je Anlage, Bibliothek des Lernfelds, Material der LS, Quellenkarte. "
     "Lesebericht: Vorlage vorhanden? wiederverwenden, anpassen oder neu bauen; Zeitschätzung gegen die "
     "effektive Lernzeit", None, None, w1),
    ("2", "Nur Lücken fragen", None,
     "strikt eine Frage zur Zeit, drei gleich ausführliche Vorschläge, der empfohlene zuerst, dazu eine "
     "freie Antwort", None, None, w2),
    ("3", "Materialplan", None,
     "je Anlage Datei Anl_<Nr>_<Kurztitel>, Format, Fach-Skill, Stilreferenz, Quellen, Prüfschritte; "
     "chronologisch nach dem Stundenverlauf, nur was der Auftrag verlangt", None, "Freigabe 1", w3),
]
h1 = max(kartenhoehe(k[6], k[0], k[1], k[2], k[3], k[4], freigabe=k[5]) for k in karten1)
TE = "je Stunde oder je selbstständiger LS; die einzige Grundlage"
h1 = max(h1, 80 + len(umbrechen(TE, 13.5, ew - 32)) * 17.6 + 52)
# Eingang aus Pipeline 1
s.rect(L, y1, ew, h1, fill=BLAU, stroke=BLAU, name="Eingang")
s.text(L + 16, y1 + 30, "aus Pipeline 1", 13, fett=True, farbe=GRUEN)
s.text(L + 16, y1 + 54, "Materialauftrag", 18, fett=True, farbe="#FFFFFF")
s.notiz(L + 16, y1 + 80, ew - 32, TE, 13.5,
        farbe="#FFFFFF", kursiv=False)
s.text(L + 16, y1 + h1 - 34, "Materialauftrag.docx", 12, mono=True, farbe=GRUEN)
s.text(L + 16, y1 + h1 - 16, ".daten/stunde/<kurz>.json", 12, mono=True, farbe=GRUEN)
x = L + ew + GAP
s.pfeil([(L + ew + 2, y1 + h1 / 2), (x - 4, y1 + h1 / 2)], farbe=BLAU)
for i, k in enumerate(karten1):
    s.karte(x, y1, k[6], h1, k[0], k[1], k[2], k[3], k[4], freigabe=k[5])
    if i < len(karten1) - 1:
        s.pfeil([(x + k[6] + 2, y1 + h1 / 2), (x + k[6] + GAP - 4, y1 + h1 / 2)], farbe=BLAU)
    x += k[6] + GAP
ende1 = x - GAP

# Reihe 2: Bauen ---------------------------------------------------------------------------------------------
y2 = y1 + h1 + 44
s.pfeil([(ende1 - w3 / 2, y1 + h1 + 2), (ende1 - w3 / 2, y2 - 4)], farbe=BLAU)
skills = [
    ("arbeitsblatt", "Arbeitsblatt aus der Schulvorlage, problemorientiert"),
    ("erwartungshorizont", "Lösung gerechnet, andere Wege, typische Fehler; Pflicht je Anlage"),
    ("dokumente", "Einstieg, Infoblatt, Messprotokoll, Serviceauftrag, Folien, Tabelle"),
    ("rechenblatt", "jede Zahl mit Einheiten gerechnet, Abgleich aller Anlagen"),
    ("quellen", "Fotos, Scans, PDF, Texterkennung, Recherche mit Quellenangabe"),
    ("stromlaufplan", "Industriestil A3 nach DIN EN 60617"),
    ("installationsplan", "Installations- und Übersichtspläne, Leitungsbemessung"),
    ("technologieschema", "Anlagen im Fachbuch-Stil, Vektor"),
    ("simulation", "interaktives HTML, nur bei Bedarf im Unterricht"),
    ("hilfekarten", "nur wenn verlangt und das Profil sie zulässt"),
]
pad = 18
links_w = 1010
spw = (links_w - pad - 14) / 2
zh = []
for sk, tx in skills:
    zh.append(19 + len(umbrechen(tx, 13.5, spw - 24)) * 18.5 + 14)
reihen = [max(zh[i], zh[i + 1]) for i in range(0, len(skills), 2)]
inhalt_h = sum(reihen) + 10 * (len(reihen) - 1)
h2 = 64 + inhalt_h + 58
s.rect(L, y2, R - L, h2, fill="#FFFFFF", stroke=BLAU_MITTEL, name="Bauen")
nb = breite("4", 13, True) + 14
s.teile.append(f'<rect x="{L + pad:.1f}" y="{y2 + 16:.1f}" width="{nb:.1f}" height="21" rx="6" fill="{BLAU}"/>')
s.text(L + pad + nb / 2, y2 + 31, "4", 13, fett=True, farbe="#FFFFFF", anker="middle")
s.text(L + pad + nb + 10, y2 + 32, "Bauen je Anlage mit dem passenden Fach-Skill", 18, fett=True)
s.text(L + pad + nb + 10 + breite("Bauen je Anlage mit dem passenden Fach-Skill", 18, True) + 16, y2 + 32,
       "in der Reihenfolge des Materialplans, Bauskripte im Arbeitsbereich", 14, farbe=GRAU)
yy = y2 + 56
for r in range(len(reihen)):
    for c in range(2):
        sk, tx = skills[2 * r + c]
        cx = L + pad + c * (spw + 14)
        s.rect(cx, yy, spw, reihen[r], fill=BLAU_HELL, stroke=BLAU_MITTEL, rx=8, name="Skill " + sk)
        s.text(cx + 12, yy + 21, sk, 13, mono=True, fett=True, farbe=BLAU)
        s.zeilen(cx + 12, yy + 41, umbrechen(tx, 13.5, spw - 24), 13.5, 1.37, farbe=TINTE)
    yy += reihen[r] + 10
s.notiz(L + pad, y2 + h2 - 22, links_w,
        "Vorlagen über material_bausteine.persoenliche_vorlage() mit den Profilwerten; KI-Fußnote; Quelle an "
        "jeder Abbildung und im Quellenverzeichnis", 13.5, farbe=GRAU)

# rechts im Bau-Kasten: die Ergebnisse
ox = L + pad + links_w + 30
ow = R - pad - ox
s.text(ox, y2 + 66, "aus denselben Bauskripten", 14, fett=True, farbe=GRAU)
ergebnisse = [
    ("Schülerfassung", "für Papier",
     "Aufgaben mit Rechenfeldern auf dem Blatt, ohne Infotexte; die Lernenden informieren sich selbst im "
     "Fachkundebuch; Merkkasten nach Profil zum Ausfüllen"),
    ("Gesamtfassung", "für Lehrkraft und Moodle",
     "alle Infotexte, Beispielrechnungen und Merkkästen, Formeln mit echtem Bruchstrich; daraus baut "
     "Pipeline 3 den Kurs"),
    ("Erwartungshorizont", "je Anlage",
     "erwartete Lösung gerechnet, anerkannte andere Wege, typische Fehler mit Reaktion und Impulsen "
     "für die Lernbegleitung"),
]
ey = y2 + 84
eh_frei = y2 + h2 - 18 - ey
eh = (eh_frei - 2 * 12) / 3
for t, unter, tx in ergebnisse:
    s.rect(ox, ey, ow, eh, fill=GRUEN_HELL if t != "Erwartungshorizont" else "#FFFFFF",
           stroke=GRUEN if t != "Erwartungshorizont" else BLAU_MITTEL, rx=10, name="Ergebnis " + t)
    s.text(ox + 14, ey + 25, t, 16, fett=True, farbe=GRUEN_DUNKEL if t != "Erwartungshorizont" else BLAU)
    s.text(ox + 14 + breite(t, 16, True) + 10, ey + 25, unter, 13, farbe=GRAU)
    z = umbrechen(tx, 13.5, ow - 28)
    ende = s.zeilen(ox + 14, ey + 47, z, 13.5, 1.36, farbe=TINTE)
    if ende + 10 > ey + eh:
        raise ValueError("Ergebniskasten zu klein: " + t)
    ey += eh + 12

# Reihe 3: Prüfen, Prüfbericht, Ablage, Übergabe ---------------------------------------------------------------
y3 = y2 + h2 + 44
s.pfeil([(L + 180, y2 + h2 + 2), (L + 180, y3 - 4)], farbe=BLAU)
pw5 = 640
pw6, pw7 = 330, 300
pw8 = R - L - pw5 - pw6 - pw7 - 3 * GAP
stufen = [("Automatik", "alle_bauen.py prüft jede Datei; Rechenprüfer gleicht alle Anlagen ab"),
          ("Sichtprüfung", "als Bild durch einen frischen Helfer: nichts abgeschnitten oder verdeckt"),
          ("Leser-Test", "in der Rolle der Facharbeiterin oder des Facharbeiters")]
sw_ = (pw5 - 2 * pad - 2 * 12) / 3
sh = max(19 + len(umbrechen(t, 13.5, sw_ - 24)) * 18.5 + 18 for _, t in stufen)
h3 = max(56 + sh + 44, kartenhoehe(pw6, "6", "Prüfbericht", None,
                                   "Fehler, Warnung, Hinweis; Leseseite: neu, selbst entschieden, unsicher; "
                                   "Vorschau als PNG", None, freigabe="Freigabe 2"))
s.rect(L, y3, pw5, h3, fill="#FFFFFF", stroke=BLAU_MITTEL, name="Prüfen")
s.teile.append(f'<rect x="{L + 14:.1f}" y="{y3 + 14:.1f}" width="{nb:.1f}" height="21" rx="6" fill="{BLAU}"/>')
s.text(L + 14 + nb / 2, y3 + 29, "5", 13, fett=True, farbe="#FFFFFF", anker="middle")
s.text(L + 14 + nb + 10, y3 + 30, "Dreistufig prüfen, vor dem ersten Vorzeigen", 17, fett=True)
for i, (t, tx) in enumerate(stufen):
    cx = L + pad + i * (sw_ + 12)
    s.rect(cx, y3 + 50, sw_, sh, fill=BLAU_HELL, stroke=BLAU_MITTEL, rx=8, name="Stufe " + t)
    s.text(cx + 12, y3 + 72, f"{i + 1}. {t}", 14.5, fett=True, farbe=BLAU)
    s.zeilen(cx + 12, y3 + 93, umbrechen(tx, 13.5, sw_ - 24), 13.5, 1.37, farbe=TINTE)
s.notiz(L + pad, y3 + h3 - 18, pw5 - 2 * pad, "Fehler werden vorher selbst behoben; Prüfpunkte aus "
        "pruefcheckliste.md", 13.5, farbe=GRAU)
x = L + pw5 + GAP
s.pfeil([(L + pw5 + 2, y3 + h3 / 2), (x - 4, y3 + h3 / 2)], farbe=BLAU)
s.karte(x, y3, pw6, h3, "6", "Prüfbericht", None,
        "Fehler, Warnung, Hinweis; Leseseite: neu, selbst entschieden, unsicher; Vorschau als PNG", None,
        freigabe="Freigabe 2")
x2 = x + pw6 + GAP
s.pfeil([(x + pw6 + 2, y3 + h3 / 2), (x2 - 4, y3 + h3 / 2)], farbe=BLAU)
s.rect(x2, y3, pw7, h3, fill="#FFFFFF", stroke=BLAU_MITTEL, name="Ablage")
s.teile.append(f'<rect x="{x2 + 14:.1f}" y="{y3 + 14:.1f}" width="{nb:.1f}" height="21" rx="6" fill="{BLAU}"/>')
s.text(x2 + 14 + nb / 2, y3 + 29, "7", 13, fett=True, farbe="#FFFFFF", anker="middle")
s.text(x2 + 14 + nb + 10, y3 + 30, "Ablage", 17, fett=True)
yy = y3 + 58
for pfad, was in [("<LS>/Material/<DS>/", "Bauskripte und Ausgaben"), ("<LF>/Bibliothek/", "Übertragbares"),
                  ("Unterricht/…/Anlagen/", "Kopie für die Stunde")]:
    s.text(x2 + 14, yy, pfad, 12.5, mono=True, farbe=BLAU)
    yy = s.zeilen(x2 + 14, yy + 18, umbrechen(was, 13.5, pw7 - 28), 13.5, 1.3, farbe=TINTE) + 24
if yy - 10 > y3 + h3:
    raise ValueError("Ablage zu klein")
x3 = x2 + pw7 + GAP
s.pfeil([(x2 + pw7 + 2, y3 + h3 / 2), (x3 - 4, y3 + h3 / 2)], farbe=BLAU)
s.rect(x3, y3, pw8, h3, fill=BLAU, stroke=BLAU, name="Übergabe")
s.text(x3 + 16, y3 + 30, "an Pipeline 3", 13, fett=True, farbe=GRUEN)
s.text(x3 + 16, y3 + 54, "Moodle-Kurs", 18, fett=True, farbe="#FFFFFF")
ende = s.notiz(x3 + 16, y3 + 82, pw8 - 32,
               "Anlagen, Gesamtfassung und Glossar-Daten; uebergabe.json beschreibt jede Datei", 13.5,
               farbe="#FFFFFF", kursiv=False)
s.text(x3 + 16, y3 + h3 - 34, "uebergabe.json", 12, mono=True, farbe=GRUEN)
s.text(x3 + 16, y3 + h3 - 16, "glossar_dsnn.json", 12, mono=True, farbe=GRUEN)
if ende + 30 > y3 + h3 - 34:
    raise ValueError("Übergabe zu klein")

# Rücklauf: Korrektur wird Regel -----------------------------------------------------------------------------
lx = 50
s.pfeil([(L, y3 + h3 - 30), (lx, y3 + h3 - 30), (lx, by + bh / 2), (L - 4, by + bh / 2)], farbe=GRUEN_DUNKEL,
        dash="5 4")

# Legende ----------------------------------------------------------------------------------------------------
ly = y3 + h3 + 26
lh = 70
s.rect(L, ly, R - L, lh, fill="#FFFFFF", stroke=BLAU_MITTEL, name="Legende")
pw = s.pille(L + 18, ly + 14, "Freigabe 1 · 2")
s.notiz(L + 18 + pw + 14, ly + 30, 860,
        "Freigabe 1 am Materialplan, Freigabe 2 nach dem Prüfbericht; Eintrag in .daten/freigaben.json (Art "
        "material, Zahl der grundsätzlichen Korrekturen).", 14, farbe=TINTE, kursiv=False)
l2 = L + 1080
s.pfeil([(l2, ly + 28), (l2 + 44, ly + 28)], farbe=GRUEN_DUNKEL, dash="5 4")
s.notiz(l2 + 58, ly + 33, R - l2 - 76,
        "Jede Korrektur der Lehrkraft wird sofort Regel: Stilregel, Prüfpunkt oder Profilwert.", 14, farbe=TINTE,
        kursiv=False)
s.h = ly + lh + 24

ziel = pathlib.Path(__file__).resolve().parent / "ablauf_material.svg"
if len(sys.argv) > 1:
    ziel = pathlib.Path(sys.argv[1])
s.speichern(ziel)
print(ziel)
