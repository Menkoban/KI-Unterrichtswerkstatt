---
name: materialauftrag
description: Hauptablauf von Pipeline 2 (Baustein 9): setzt den freigegebenen Materialauftrag einer Stunde aus Pipeline 1 in fertiges Material um – lesen, Lücken fragen, Materialplan (Freigabe 1), je Anlage den passenden Fach-Skill aufrufen, dreistufig prüfen, Prüfbericht (Freigabe 2), ablegen und an Pipeline 3 übergeben. Verwende ihn, sobald ein Materialauftrag vorliegt oder die Lehrkraft „Material bauen“, „Anlagen für DS …“, „setz den Auftrag um“ sagt.
---
> Werkzeug-Ordner dieses Skills: `materialpipeline-referendariat/`. Alle Pfade und Befehle hier gelten relativ dazu (vorher `cd materialpipeline-referendariat`). Quelle: `materialpipeline-referendariat/.claude/skills/materialauftrag/`.

# Materialauftrag umsetzen (Baustein 9)

Grundlage: `CLAUDE.md`, `docs/KONZEPT.md` (Entscheidungsprotokoll), `docs/regeln/*`. Eingang aus Pipeline 1:
`Materialauftrag.docx` im Stundenordner und `.daten/stunde/<kurz>.json` (Feld `anlagen`). Der Auftrag ist die
einzige Grundlage.

**Werkzeug und Arbeitsbereich (Aufteilung 2026-10-19, wie Pipeline 1):** Dieses Repo ist nur das Werkzeug.
Material, Bauskripte, Fotos, Bibliothek, eigene Quellen und das Profil liegen im gemeinsamen persönlichen
Arbeitsbereich aller Pipelines. Zuerst `python3 werkzeug/arbeitsbereich.py`: findet den Arbeitsbereich und zeigt
die Profil-Einstellungen der Gruppe „Material“ (ein Niveau, effektive Lernzeit, Fotos, Sprachaufnahmen,
Notenschlüssel …). Alle Entscheidungen richten sich nach dem Profil; Ergebnisse nie ins Werkzeug schreiben.

## Ablauf

1. **Lesen.** Auftrag, Steckbrief jeder Anlage (Zweck, Phase, TK, Inhalt, Aufbau, Hilfen, Moodle, Werkzeug,
   Quellen, Abnahmekriterien, Erwartungshorizont), `<LF>/Bibliothek/` und `<LF>/<LS>/Material/` im Arbeitsbereich,
   `Quellen/_karte/karte.md` (Suche: `python3 werkzeug/quellen/suche.py BEGRIFF`). Lesebericht als Tabelle mit
   getrennten Spalten **„Vorlage vorhanden?“** und **„Material für diese Stunde“** (wiederverwenden, anpassen,
   wird gebaut); echte Lücken einzeln benennen (Korrektur der Lehrkraft 2026-10-16: „neu“ war missverständlich).
   **Umfang (E10, Lehrkraft 2026-10-19):** Der Lesebericht schätzt je Anlage die Bearbeitungszeit und vergleicht
   die Summe mit der effektiven Lernzeit (etwa 75–80 von 90 min); bei Überladung Warnung mit Vorschlag (Zusatz,
   Reserve, Hilfe zum Holen). Keine feste Obergrenze.
   Modellbetrieb, Personen und Kundschaft kommen aus dem Auftrag (z. B. EG: Stromhof Elektro GmbH,
   AS: Brinkmann Automation).
   **Ältere Aufträge mit drei Niveaus** (Entscheidung A, 2026-10-16): ein Blatt für alle ohne Niveau-Namen und
   Farbbänder; Beginner- und Könner-Hilfen werden gestufte Hilfekarten (leichteste Hilfe zuerst, letzte Stufe
   löst nur einen Teil), Experten-Inhalte werden freiwillige Zusatzaufgabe für Schnelle.
2. **Nur Lücken fragen**, strikt eine Frage zur Zeit, drei gleich ausführliche Vorschläge (empfohlener zuerst) und
   freie Antwort. Hat eine Schaltung Varianten, wird die Variante gefragt, nie angenommen (Regel 36).
3. **Materialplan** je Anlage: Datei `Anl_<Nr>_<Kurztitel>.<endung>`, Format (DOCX, sonst XLSX/PPTX/HTML; PDF nur
   auf Wunsch), Fach-Skill, Stilreferenz (zuerst `docs/stilreferenz/probe_ls01/README.md`), Quellen, Prüfschritte. Nur Anlagen, die der Auftrag verlangt; eine
   Materialart ohne Anlage im Auftrag wird nicht gebaut. **Freigabe 1.**
   **Reihenfolge chronologisch** (Lehrkraft 2026-10-23): Materialplan und Bau folgen dem Stundenverlauf. Je
   Arbeitsblatt zuerst das Blatt, dann die Anlagen, die es braucht (Infoblatt, Hilfekarten, Fallkarten,
   Erwartungshorizont), dann das nächste Arbeitsblatt mit seinen Anlagen. Einstiegsmaterial vor dem ersten
   Blatt, Sicherung am Ende. So sieht die Lehrkraft, wie die Materialien ineinandergreifen; Zahlen und
   Begriffe des Blatts sind die Vorgabe für seine Anlagen.
   **Profil `material.arbeitsblaetter_fortlaufend`** (Lehrkraft 2026-10-23): Schülerarbeit fortlaufend auf AB 1, AB 2, …
   (Einstieg mit Nachricht und Auftrag oben auf AB 1, Blätter schließen direkt aneinander an); Anlagen eigenständig
   und getrennt nummeriert. Ein Dokument je Lernsituation wie ein Fachkundebuch: `<LS>/Material/Arbeitsblaetter_LSnn.docx`
   aus `baue_arbeitsblaetter.py`, die Inhalte je Doppelstunde in `DSnn/ab_dsnn.py` (Liste `ARBEITSBLAETTER`),
   Werkzeug-Bausteine `stunde.arbeitsblaetter()` und `stunde.thema()`, `stunde.aufgabe()`; im Stundenordner als `Anlagen/Arbeitsblaetter.docx`.
   **Profil `material.beamer_zeigt_arbeitsblatt`:** keine Folie oder Tafelvorlage, die das Arbeitsblatt wiederholt.
   **Gesamt-PDF nur auf Anforderung:** `python3 werkzeug/paket.py <LS>/Material DSnn <Scratch-Ordner>`.
4. **Bauen** je Anlage mit dem Fach-Skill (Elektro-Fach-Skills `stromlaufplan`, `installationsplan`, `technologieschema`, `simulation` nur
   mit Profil `fach.elektrotechnik`, Fachpaket Elektrotechnik; sonst Rückfrage an die Lehrkraft):

   | Anlage im Auftrag | Skill |
   |---|---|
   | Arbeitsblatt | `arbeitsblatt` |
   | gestufte Hilfen (nur wenn verlangt oder gewünscht) | `hilfekarten` |
   | Erwartungshorizont (Pflicht je Anlage, außer Vermerk „keiner nötig“) | `erwartungshorizont` |
   | Einstieg, Infoblatt/Datenblatt, Messprotokoll, Serviceauftrag/-bericht, Selbstkontrolle, Karte A5, Tafelbild, Folien, Tabelle | `dokumente` |
   | Stromlaufplan (Schütz-, Steuerschaltungen) | `stromlaufplan` |
   | Installations-, Übersichts-, Verteilerplan, Bemessung | `installationsplan` |
   | Technologieschema | `technologieschema` |
   | Simulation | `simulation` |
   | Rechnungen, Diagramme (für jede Anlage mit Zahlen) | `rechenblatt` |
   | mitgegebene oder gesuchte Quellen | `quellen` |

   Gibt es für eine verlangte Anlage keinen Skill: mit der passenden Vorlage bauen und der Lehrkraft melden,
   damit ein Skill entsteht.
   **Vor dem Bau `docs/regeln/stilregeln.md` lesen** (Korrektur 2026-10-23: eine bestehende Regel wurde
   übersehen). Vorlagen über `material_bausteine.persoenliche_vorlage(name, vorlage_fn)`, damit Kopf, Wozu-Zeile
   und Ausrichtung dem Profil folgen; KI-Fußnote als Standardtext (`arbeitsblatt.KI_HINWEIS`).
5. **Prüfen** dreistufig nach `docs/regeln/pruefcheckliste.md`: Automatik (`werkzeug/vorlagen/alle_bauen.py`
   `pruefen()`, Rechenprüfer-Abgleich über alle Anlagen), Sichtprüfung als Bild durch einen frischen Helfer,
   Leser-Test in der Rolle der Facharbeiterin/des Facharbeiters. Fehler vorher selbst beheben.
   Alle drei Stufen **vor** dem ersten Vorzeigen (Korrektur 2026-10-23: abgeschnittene Beschriftung,
   verdeckte Wege und eine allein stehende Überschrift hätte die Sichtprüfung gefunden).
6. **Prüfbericht** (Fehler / Warnung / Hinweis), Vorschau als PNG, **Freigabe 2.**
   Bei Profil `freigabe.leseseite` (Lehrkraft 2026-10-25) beginnt er mit einer Leseseite: neu, selbst entschieden,
   unsicher, je mit Verweis; Freigabe in `.daten/freigaben.json` eintragen (Art material, Zahl der Korrekturen).
7. **Ablage** im Arbeitsbereich: Bauskripte und Ausgaben in `<Fach>/<Beruf>/<LF>/<LS>/Material/<DS>/`
   (`arbeitsbereich.material(...)`; Skripte finden das Werkzeug über `MPR_WERKZEUG` oder den Nachbarordner
   `materialpipeline-referendariat`), Übertragbares in `<LF>/Bibliothek/`, Kopie in
   `<Stundenordner>/Anlagen/`; `werkzeug/uebergabe.py` schreibt `Anlagen/uebergabe.json` für Pipeline 3. KONZEPT im Werkzeug; commit und push in beiden Repos.

## Regeln

- Problemorientiert: erst das Problem im Modellbetrieb des Auftrags, keine Arbeitsanweisung, die Methode
  oder Lösungsweg vorgibt; ein Niveau; Sie-Form; KI-Fußnote; Quelle an jeder Abbildung und im Literaturverzeichnis.
- Mitgegebenes ist Rohstoff: immer neu im Pipeline-Stil, Original bleibt als Beleg im Materialpool.
- Jede Korrektur der Lehrkraft sofort als Regel festhalten (Checkliste, Stilregel oder Beispiel im Fach-Skill).
- Je Materialart Buch führen: nach drei Freigaben in Folge ohne inhaltliche Änderung vorschlagen, Freigabe 1 für
  diese Art wegzulassen (Endfreigabe bleibt).
