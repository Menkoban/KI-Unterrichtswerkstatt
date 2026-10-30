---
name: nachbereitung
description: Schritt 17 der Unterrichtspipeline: Die Lehrkraft spricht nach einer Stunde frei ein, was war (Text oder Sprachnachricht, ohne feste Fragen). Der Skill zerlegt das Gesagte in einzelne Aussagen, schlägt je Aussage die Ablage vor (Stunden-, Klassen-, Lernsituations-Akte, Lehrkraft-Profil), lässt bestätigen und erzeugt Nachbereitung.docx; offene Punkte erscheinen in der nächsten Stundenplanung unter „Aus der letzten Nachbereitung“. Verwende ihn nach jeder Stunde oder jedem Besuch: „Nachbereitung“, „wie lief die Stunde“, „das war heute …“, „Reflexion zu DS 2“.
---

# Nachbereitung (Schritt 17)

Grundlage: `docs/KONZEPT.md` „Schritt 17 Nachbereitung: frei sprechen, nach Reichweite sortieren“.
Beispiel-Daten: `beispiele/daten/nachbereitung/lf01_eg_ls01_ue02.json` (fiktiv).

## Ablauf

1. **Zuhören:** Die Lehrkraft spricht frei; keine Fragebögen. TV- oder Störgeräusch-Fragmente
   ignorieren; bricht eine Nachricht mitten im Satz ab, darauf hinweisen. Namen von Lernenden
   sofort durch Kürzel ersetzen.
2. **Zerlegen und zuordnen:** jede Aussage einzeln, mit vorgeschlagener Ablage:
   - **Stunde:** was tatsächlich geschah (Zeiten, Abweichungen, Ergebnis)
   - **Klasse:** Beobachtungen zur Klasse und zu Lernenden (Kürzel)
   - **Lernsituation:** Änderungen an Material, Zeiten, Aufgaben, Ablauf (wirkt auch auf den
     nächsten Durchgang mit anderen Klassen)
   - **Profil:** nur wiederkehrende Muster, mit Stichwort `muster`
   Als Liste zeigen; die Lehrkraft bestätigt oder verschiebt.
3. **Daten** `.daten/nachbereitung/<kurz der stunde>.json` mit `stunde`, `datum`, `stand`,
   `rohtext` (wörtlich) und `aussagen` (`text`, `ablage`, `status` offen oder erledigt, optional
   `betrifft`, `muster`).
4. **Erzeugen:** `python nachbereitung/nachbereitung.py <arbeitsbereich> <kurz>` →
   `Nachbereitung.docx` im Stundenordner mit Prüfbericht; Freigabe mit
   `python akten/steckbrief.py freigeben`, commit und push.
5. **Weitergeben:** Klassen-Aussagen in die Klassen-Akte übernehmen, wenn sie dauerhaft gelten
   (Skill `klassenakte`); Lernsituations-Aussagen als Änderung an der LS-Akte vorschlagen.

## Regeln

- **Profil-Regel:** Eine einzelne Stunde ändert das Profil nie. Der Prüfbericht meldet erst ab
  zwei Nachbereitungen mit demselben `muster` einen Vorschlag; die Lehrkraft entscheidet. Auf
  ausdrücklichen Zuruf („merk dir das grundsätzlich“) sofort.
- **Rückkopplung:** Jede neue Stundenplanung beginnt mit
  `python nachbereitung/nachbereitung.py <ab> --offen --ls <ls> --klasse <klasse>`
  (Block „Aus der letzten Nachbereitung“). Erledigte Punkte werden abgehakt (`status: erledigt`),
  nicht gelöscht.
- Nach Besuchen dient die Nachbereitung als Grundlage für Reflexion, Gespräche und Portfolio.
