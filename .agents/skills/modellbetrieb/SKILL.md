---
name: modellbetrieb
description: Teil von Schritt 02 der Unterrichtspipeline: legt den fiktiven Modellbetrieb eines Berufs bzw. einer Fachrichtung an (Steckbrief, Personen, Kunden, Rolle der Lernenden als Gesellinnen und Gesellen), der in allen Lernfeldern als durchgehende Handlungssituation dient. Verwende ihn, wenn für einen Beruf noch kein Modellbetrieb existiert, die Lehrkraft einen neuen Beruf plant oder „Modellbetrieb“, „Ausbildungsbetrieb für die Lernsituationen“, „fiktive Firma“ sagt.
---
> Werkzeug-Ordner dieses Skills: `unterrichtspipeline-referendariat/`. Alle Pfade und Befehle hier gelten relativ dazu (vorher `cd unterrichtspipeline-referendariat`). Quelle: `unterrichtspipeline-referendariat/.claude/skills/modellbetrieb/`.

# Modellbetrieb (Schritt 02, einmal je Beruf)

Grundlage: `docs/ARBEITSWEISE.md`, `docs/KONZEPT.md` „Schritt 02 — Festlegungen“ (durchgehender
Modellbetrieb). Beispiel-Daten: `beispiele/daten/modellbetrieb/stromhof.json`.

## Ablauf

1. **Je eine Frage** (drei gleich ausführliche Vorschläge, empfohlener zuerst):
   Betriebsart (eigener Betrieb je Fachrichtung oder gemeinsamer), Größe und Arbeitsfelder,
   Standort (Region der Schule, Profil `schule.ort`), Name; der Name kommt als `modellbetrieb.name` ins Profil.
2. **Namen prüfen:** Firmen- und Personennamen per Websuche prüfen; gibt es einen echten
   Betrieb dieses Namens in der Branche, verwerfen und neue Vorschläge machen.
3. **Daten** `.daten/modellbetrieb/<kurz>.json`: Steckbrief, Personen (mit Rolle für die
   Lernsituationen), Kunden (mit Bezug zu Lernfeldern), Rolle der Lernenden, Regeln.
4. **Erzeugen:** `python modellbetrieb/modellbetrieb.py <arbeitsbereich> <kurz>` →
   `<Fach>/<Beruf>/Modellbetrieb_<Name>.docx`.
5. **Freigabe** wie in ARBEITSWEISE beschrieben.

## Regeln

- Die Lernenden sind immer **Gesellinnen und Gesellen**, nicht Azubis; Azubis im Betrieb
  sind Adressaten von Erklärungen und Unterweisungen. Sie-Form.
- Der Betrieb „wächst mit“ über die Ausbildungsjahre; je Lernfeld kommen nur Kunden und
  Aufträge dazu. Kein echter Betrieb, keine echten Personen.
