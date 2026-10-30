---
name: stundenplanung
description: Stundenebene der Unterrichtspipeline für eine Doppelstunde: Mikro-Einstieg mit dem, was schon feststeht, Interview Frage für Frage (Einstieg, Arbeitsblatt, Sozialform, Sicherung, Besonderheiten), dann Verlaufsskizze (Schritt 13) und Materialauftrag für Pipeline 2 (Schritt 14) mit Teilkompetenzen, Fehlvorstellungen, Annahmen und Erwartungshorizonten. Verwende ihn, wenn eine Lernsituation steht und eine Stunde geplant wird: „DS 1 planen“, „nächste Stunde“, „Verlaufsskizze“, „Materialauftrag“.
---

# Stunde planen (Schritte 13 und 14, Alltagsstunde)

Grundlage: `docs/ARBEITSWEISE.md`, `docs/KONZEPT.md` „Einstieg und Interviews“, „Planungstiefe
je Stundentyp“. Beispiel-Daten: `beispiele/daten/stunde/lf01_eg_ls01_ue01.json`.

## Ablauf

1. **Bedarf:** `python akten/bedarf.py --beruf <B> --lf <n> --ls <n> --klasse <K> --stunde`.
   Ohne Klassen-Akte: mit offenen Annahmen planen (siehe ARBEITSWEISE) oder Skill `klassenakte`.
   **Aus der letzten Nachbereitung:** `python nachbereitung/nachbereitung.py <ab> --offen --ls <ls>
   --klasse <K>`; die offenen Punkte stehen am Anfang des Mikro-Einstiegs.
2. **Mikro-Einstieg:** in wenigen Zeilen zeigen, was feststeht (Leitfrage, Inhalte,
   Teilergebnis, Phasen, LK mit Wortlaut, Fehlvorstellungen dieser DS mit Priorität,
   Stundentyp), dann offen fragen: „Was hast du dir vorgestellt?“ mit drei gleich
   ausführlichen Vorschlägen.
2a. **Stundentyp zuerst** (Lehrkraft 2026-10-25): Ist nicht gesagt, ob Alltags- oder Besuchsstunde, zuerst danach
   fragen. Alltagsstunde: nur, was die Ausbildungslehrkraft verlangt (Profil `alltag.vorgabe`), wenig Methoden.
   Besuchsstunde: aktiver, mit Methoden, Realobjekten und Live-Demonstration (Profil `besuch.gestaltung`).
3. **Interview, je eine Frage** in dieser Reihenfolge, nur so weit nötig: Einstieg,
   Aufbau des Arbeitsblatts, Sozialform, Sicherung, Besonderheiten der Stunde (z. B.
   erster Schultag, Kennenlernen). Jede Entscheidung als KONZEPT-Zeile.
   Bei Profil `methoden.vielfalt` „gering“ (Lehrkraft 2026-10-25) nur einfache, wiederkehrende,
   zur Klasse passende Formen vorschlagen; keine aufwendigen Methoden als Vorschlag.
4. **Entwurf** `.daten/stunde/<kurz>.json`: Ordner `Unterricht/<Fach>/<Klasse>/LFnn/LSnn/
   UEnn_<Kurzthema>` (ohne Datum), Kompetenzen der Stunde (TK mit „indem“, je mit LK),
   Verlauf mit Zeiten lückenlos, Handlungsphasen, didaktische Reserve, Anlagen mit
   ausführlichem Steckbrief (Zweck, Phase, TK; Inhalt und Wortlaut; Aufbau und Layout; Hilfen;
   Moodle; Werkzeug (Vorschlag); Quellen; Abnahmekriterien) und Erwartungshorizont,
   `material_allgemein` und `gestaltung` für alle Anlagen. Die Stunde selbst plant kein Moodle.
   **Anlagen chronologisch nummerieren** (Lehrkraft 2026-10-23): in der Reihenfolge des Verlaufs, je
   Arbeitsblatt zuerst das Blatt, direkt danach seine Anlagen (Infoblatt, Hilfen, Fallkarten), dann das
   nächste Blatt; Pipeline 2 baut in derselben Reihenfolge.
   Mit Profilwert `material.arbeitsblaetter_fortlaufend`: Arbeitsblätter (AB 1, AB 2, …, Einstieg auf AB 1) und
   Anlagen getrennt nummerieren, je Anlage Feld `art` = „Arbeitsblatt“ oder „Anlage“.
   Mit Profilwert `material.beamer_zeigt_arbeitsblatt`: keine Tafelbilder oder Folien, die das Arbeitsblatt
   wiederholen; Tabellen füllt die Lehrkraft am Beamer auf dem Blatt aus, eine Folie nur für Neues (Strichlisten).
   **Zeitbudget** (Lehrkraft 2026-10-23): im Verlauf je 10 min für Ankommen und Einstieg sowie für Abschluss und
   Ausblick, dazu 5 min didaktische Reserve **genau einmal** als Block `reserve` mit Minuten (z. B. „85–90 min“) und den Inhalten für Zeitnot und Zeitüberschuss, nie zusätzlich als Phase im Verlauf (Korrektur 2026-10-24); die Lernphasen füllen nur die effektive Lernzeit aus dem Profil
   (`material.effektive_lernzeit`, bei der Lehrkraft 65 min).
   **Seminarfassung** (Profil `form.seminar_zeiten`, `form.seminar_lernende_einzeln`): `Verlaufsskizze_Seminar.docx`
   und der Entwurf ohne Minutenangaben und ohne Hinweise zu einzelnen Lernenden; die interne Verlaufsskizze behält beides.
5. **Erzeugen:** `python stunde/stunde.py <arbeitsbereich> <kurz>` → `Verlaufsskizze.docx`
   (Seminarspalten) und `Materialauftrag.docx`. Der Generator prüft Zeiten, Anlagen,
   Erwartungshorizonte, Phasen der DS und die Annahmen.
6. **Eine gemeinsame Freigabe** am Ende (Alltagsstunde); bei Besuchsstunden Schritt für
   Schritt mit Skill `besuchsstunde`. Nach der Stunde Skill `nachbereitung`.

## Kurzskizze bei selbstständiger LS (Lehrkraft 2026-10-25)

Hat die LS einen Arbeitsplan (`.daten/arbeitsplan/<kurz>.json`, Skill `lernsituation` Schritt 6), wird je DS nur eine
**Kurzskizze** geplant: Stunden-Akte mit Feld `arbeitsplan`, Verlauf mit Rüstzeiten, Rundgang und Kontrolle am Ende der
DS. `stunde.py` erzeugt daraus eine einseitige Verlaufsplanung in Seminarspalten für die Ausbildungslehrkraft und
keinen eigenen Materialauftrag; die genannten Arbeitsblätter werden gegen den Lernpfad geprüft.

## Regeln

- **Profil vor jedem Vorschlag lesen** (Korrektur 2026-10-24: Hausaufgabe vorgeschlagen, obwohl `hausaufgaben: keine`): Gruppe „Didaktik“ und „Material“; kein Vorschlag, der einem Profilwert widerspricht.

- **Problemorientiert:** Einstieg mit Problem oder Widerspruch, offener Auftrag ohne Methode,
  Lösungsweg oder „gegeben/gesucht“; ursachenrelevante Daten nur im Informationspool (ARBEITSWEISE).
  **Selbstprüfung vor der Freigabe** (Korrektur Probelauf LS 5, 2026-10-27): Lässt sich mit dem Material dieser DS
  allein die Ursache schon finden (Vorgeschichte in der Notiz, Aufgabe, die Messwert und Fehlerbild verknüpft)? Dann
  ist es ein Vorgriff; die Angabe oder Aufgabe wandert in die DS, die die Ursache sucht.

- Material wird als Arbeitsblatt geplant; jede Anlage mit Erwartungshorizont oder dem
  Vermerk „keiner nötig“. Alles auf einem Niveau, Hilfen gestuft (keine Niveaus Beginner, Könner, Experte). Sprachnachrichten oder Texte von Personen des Modellbetriebs in
  der Sie-Form; Sprachausgabe als KI-gestützt kennzeichnen, keine echte Stimme nachbilden.
- Fotos von Anlagen: eigene oder lizenzfreie mit Quelle, keine KI-Fotos.
- **Lebende Übersicht:** Nach jeder Freigabe `python akten/stand.py <arbeitsbereich>` und die Dateien in `.daten/stand/` in der Webseite „Planungsstand Referendariat“ ersetzen (Adresse im README des Arbeitsbereichs). Zu Beginn jeder Planung den Stand der Lernsituation daraus zeigen (Lehrkraft 2026-10-24: der Überblick ging verloren).
