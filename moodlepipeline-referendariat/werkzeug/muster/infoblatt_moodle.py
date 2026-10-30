"""Muster: Infoblatt als Moodle-Textseite (Entscheidung Punkt 7, Lehrkraft 2026-10-20).

Gleiches Design wie die Druckvorlage aus Pipeline 2 (Schild, Titel, „Wozu?“, nummerierte Abschnitte, Abbildung und
Tabelle mit Nummer und Quelle, Randspalte mit grüner Linie), aber ohne Schulkopf (hat Moodle) und ohne Fußzeile;
unten Quellen und die Druckfassung zum Herunterladen; der KI-Hinweis steht nur einmal in der Kursbeschreibung
(Punkt 32, Lehrkraft 2026-10-21).
Nur Inline-Stile, weil Moodle <style>-Blöcke im Seiteninhalt filtert; die Randspalte rutscht am Handy unter den Text
(flex-wrap).

    python3 werkzeug/muster/infoblatt_moodle.py <ausgabeordner> --name "Vorname Nachname"

Schreibt inhalt.html (das, was in die Moodle-Seite kommt), vorschau.html (im Moodle-Rahmen) und zwei Bildschirmfotos.
"""
import argparse
import base64
from pathlib import Path

BLAU, GRUEN, DUNKEL, GRAU, LINIE = "#08349C", "#7DDE78", "#1B1F24", "#5F6670", "#C9CED6"
P2 = Path(__file__).resolve().parents[3] / "materialpipeline-referendariat" / "docs" / "stilreferenz" / "vorlagen"


def bild(pfad):
    return "data:image/png;base64," + base64.b64encode(Path(pfad).read_bytes()).decode()


def abschnitt(nr, titel, inhalt):
    return (f'<h3 style="color:{BLAU};font-size:1.15rem;margin:1.4rem 0 .4rem;">'
            f'<span style="display:inline-block;min-width:2rem;">{nr}</span>{titel}</h3>{inhalt}')


def absatz(text):
    return f'<p style="margin:.3rem 0 .6rem;line-height:1.5;">{text}</p>'


def rand(titel, zeilen):
    z = "".join(f'<div style="margin:.1rem 0;">{x}</div>' for x in zeilen)
    return f'<div style="margin-bottom:1rem;"><div style="font-weight:bold;color:{DUNKEL};">{titel}</div>{z}</div>'


def inhalt(name, abb1, abb2):
    tab = "".join(f'<tr><td style="border:1px solid #9AA3AD;padding:.2rem .8rem;text-align:center;">{a}</td>'
                  f'<td style="border:1px solid #9AA3AD;padding:.2rem .8rem;text-align:center;">{b}</td></tr>'
                  for a, b in (("−50", "80,31"), ("0", "100,00"), ("50", "119,40"), ("100", "138,51"),
                               ("150", "157,33"), ("200", "175,86"), ("250", "194,10")))
    haupt = (
        abschnitt("1", "Aufbau und Wirkungsweise",
                  absatz("Ein Pt100 ist ein Messwiderstand aus Platin. Bei 0 °C hat er einen Widerstand von genau "
                         "100 Ω. Mit steigender Temperatur nimmt sein Widerstand zu (Kaltleiterverhalten). Der "
                         "Zusammenhang ist in DIN EN IEC 60751 festgelegt und über den genutzten Bereich nahezu linear.")
                  + absatz("Für überschlägige Rechnungen genügt der mittlere Temperaturbeiwert zwischen 0 °C und 100 °C:")
                  + f'<p style="text-align:center;font-size:1.05rem;margin:.6rem 0 1rem;">R<sub>ϑ</sub> = R<sub>0</sub>'
                    f' · (1 + α · Δϑ) &nbsp;&nbsp; mit &nbsp; R<sub>0</sub> = 100 Ω, &nbsp;α = 3,85 · 10<sup>−3</sup> 1/K</p>'
                  + '<div style="display:flex;flex-wrap:wrap;gap:1.5rem;align-items:flex-start;">'
                    f'<figure style="margin:0;flex:1 1 260px;max-width:340px;"><img src="{abb1}" alt="Kennlinie Pt100: '
                    'Widerstand steigt linear mit der Temperatur" style="width:100%;">'
                    f'<figcaption style="font-size:.8rem;color:{GRAU};">Abb. 1: Kennlinie Pt100 (eigene Darstellung, '
                    'Werte nach DIN EN IEC 60751)</figcaption></figure>'
                    '<div style="flex:0 1 auto;"><div style="font-weight:bold;font-size:.85rem;margin-bottom:.3rem;">'
                    'Tab. 1: Grundwerte Pt100</div><table style="border-collapse:collapse;font-size:.9rem;">'
                    '<thead><tr><th style="border:1px solid #9AA3AD;padding:.2rem .8rem;background:#E8EEF8;">ϑ in °C</th>'
                    '<th style="border:1px solid #9AA3AD;padding:.2rem .8rem;background:#E8EEF8;">R in Ω</th></tr>'
                    f'</thead><tbody>{tab}</tbody></table></div></div>')
        + abschnitt("2", "Genauigkeitsklassen",
                    absatz("Die Norm legt zulässige Grenzabweichungen fest: Klasse A ± (0,15 + 0,002 · |ϑ|) K, Klasse B "
                           "± (0,30 + 0,005 · |ϑ|) K, mit ϑ in °C. Diese Werte gelten für den Messwiderstand allein, "
                           "nicht für Leitung und Auswertung."))
        + abschnitt("3", "Anschlussarten",
                    absatz("Das Auswertegerät (Messumformer, Analogeingang der Steuerung) misst den Widerstand des "
                           "gesamten angeschlossenen Stromkreises und rechnet ihn in eine Temperatur um. Je nach Anzahl "
                           "der Adern unterscheidet man drei Schaltungen:")
                    + absatz("<b>Zweileiterschaltung:</b> Messwiderstand und beide Adern der Anschlussleitung liegen in "
                             "Reihe. <b>Dreileiterschaltung:</b> Über eine dritte Ader erfasst das Gerät den "
                             "Leitungswiderstand und gleicht ihn aus, sofern alle Adern gleich sind. "
                             "<b>Vierleiterschaltung:</b> Ein Aderpaar führt den Messstrom, das andere misst die "
                             "Spannung direkt am Fühler.")
                    + f'<figure style="margin:.4rem 0;"><img src="{abb2}" alt="Zwei-, Drei- und Vierleiterschaltung '
                      f'eines Pt100 am Messumformer" style="width:100%;max-width:560px;"><figcaption style="font-size:.8rem;'
                      f'color:{GRAU};">Abb. 2: Anschlussarten von Widerstandsthermometern (eigene Darstellung)'
                      '</figcaption></figure>')
        + abschnitt("4", "Widerstand von Leitungen",
                    absatz("Der Widerstand eines Leiters hängt von Werkstoff, Länge und Querschnitt ab: R = ρ · l / A. "
                           "Spezifischer Widerstand von Kupfer bei 20 °C: ρ<sub>Cu</sub> = 0,0178 Ω · mm²/m; weitere "
                           "Werkstoffe siehe Tabellenbuch.")))
    seite = (rand("Begriffe", ["Pt = Platin", "100 = Nennwiderstand in Ω bei 0 °C", "Ebenso: Pt500, Pt1000"])
             + rand("Formelzeichen", ["R<sub>ϑ</sub> Widerstand bei ϑ", "R<sub>0</sub> Widerstand bei 0 °C",
                                      "α Temperaturbeiwert", "Δϑ Temperaturdifferenz", "ρ spezifischer Widerstand",
                                      "l Leiterlänge", "A Leiterquerschnitt"])
             + rand("Norm", ["DIN EN IEC 60751: Industrielle Platin-Widerstandsthermometer und "
                             "Platin-Temperatursensoren"])
             + rand("Weiterlesen", ["Tabellenbuch Elektrotechnik, Abschnitt Temperaturmessung"]))
    return (
        f'<div style="font-family:Arial,Helvetica,sans-serif;color:{DUNKEL};max-width:1000px;">'
        # Titel und Art stehen schon im Seitennamen „Infoblatt: …“ (Moodle zeigt ihn als Überschrift)
        f'<p style="color:{GRAU};margin:0 0 1rem;padding-bottom:.6rem;border-bottom:1px solid {LINIE};">'
        f'<b>Wozu?</b> Nachschlagen: Aufbau, Kennwerte und Anschlussarten von Pt100-Fühlern. Nutzen Sie nur, was Sie '
        f'für Ihren Auftrag brauchen.</p>'
        f'<div style="display:flex;flex-wrap:wrap;gap:2rem;">'
        f'<div style="flex:1 1 480px;min-width:0;">{haupt}</div>'
        f'<aside style="flex:0 1 220px;border-left:4px solid {GRUEN};padding-left:.8rem;font-size:.85rem;'
        f'color:{GRAU};">{seite}</aside></div>'
        f'<p style="margin:1.5rem 0 .3rem;"><a href="#" style="color:{BLAU};">&#128462; Druckfassung (Word) '
        f'herunterladen</a></p>'
        f'<p style="font-size:.8rem;color:{GRAU};border-top:1px solid {LINIE};padding-top:.5rem;margin-top:1rem;">'
        f'Quellen: eigene Darstellung; Grundwerte und '
        f'Grenzabweichungen nach DIN EN IEC 60751.</p></div>')


RAHMEN = """<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Infoblatt Pt100 – Moodle-Vorschau</title></head>
<body style="margin:0;background:#f8f9fa;font-family:Arial,Helvetica,sans-serif;">
<div style="background:#fff;border-bottom:1px solid #dee2e6;padding:.6rem 1.2rem;display:flex;align-items:center;gap:1rem;">
<b style="color:#0f6cbf;">Moodle</b><span style="color:#495057;">Startseite</span><span style="color:#495057;">Dashboard</span>
<span style="color:#495057;">Meine Kurse</span></div>
<div style="max-width:1140px;margin:0 auto;padding:1rem;">
<div style="font-size:.85rem;color:#0f6cbf;margin-bottom:.6rem;">EG1 LF 1 · LS 3 Der Temperaturfühler zeigt falsche Werte
 › Erkunden: Wie misst ein Pt100? › Infoblatt: Widerstandsthermometer Pt100</div>
<div style="background:#fff;border:1px solid #dee2e6;border-radius:.5rem;padding:1.5rem 1.8rem;">
<div style="font-size:.8rem;color:#6a737b;margin-bottom:.3rem;">Textseite</div>
<h1 style="font-size:1.6rem;margin:0 0 1rem;color:#1d2125;">Infoblatt: Widerstandsthermometer Pt100</h1>
%INHALT%</div></div></body></html>"""


def main():
    a = argparse.ArgumentParser()
    a.add_argument("ziel")
    a.add_argument("--name", required=True)
    arg = a.parse_args()
    ziel = Path(arg.ziel); ziel.mkdir(parents=True, exist_ok=True)
    html = inhalt(arg.name, bild(P2 / "entwurf" / "infoblatt_abb-1.png"), bild(P2 / "entwurf" / "infoblatt_abb-2.png"))
    (ziel / "inhalt.html").write_text(html, encoding="utf-8")
    vorschau = ziel / "vorschau.html"
    vorschau.write_text(RAHMEN.replace("%INHALT%", html), encoding="utf-8")
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        exe = Path("/opt/pw-browsers/chromium")
        b = p.chromium.launch(executable_path=str(exe)) if exe.exists() else p.chromium.launch()
        for name, breite in (("bildschirm", 1280), ("handy", 390)):
            s = b.new_page(viewport={"width": breite, "height": 800}, device_scale_factor=1 if breite > 500 else 2)
            s.goto(vorschau.as_uri())
            s.screenshot(path=str(ziel / f"vorschau_{name}.png"), full_page=True)
        b.close()
    print(ziel)


if __name__ == "__main__":
    main()
