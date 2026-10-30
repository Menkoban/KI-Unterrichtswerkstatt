---
name: einstieg
description: Einstieg „Was steht an?“ der Unterrichtspipeline (Pipeline 1, Schritt 00). Die Lehrkraft sagt frei, was ansteht (eine Stunde, eine Lernsituation, ein Lernfeld, ein Besuch, eine Abgabe), auch als Sprachnachricht. Der Skill findet den Arbeitsbereich, lädt das Lehrkraft-Profil, prüft die vorhandenen Akten und meldet „das habe ich, das fehlt, das ist veraltet“; danach schlägt er die Reihenfolge der fehlenden Schritte vor und startet nur diese, jeden mit eigener Freigabe. Verwende ihn bei jedem Planungsbeginn, auch ohne Nennung des Namens, etwa „ich muss LS 4 planen“, „nächste Woche ist mein GUB“, „wo war ich?“.
---

# Einstieg: Was steht an? (Schritt 00)

Grundlage: `docs/ARBEITSWEISE.md` (gilt immer), `docs/KONZEPT.md`, Abschnitte 1 (Akten), „Einstieg und
Interviews“, 5b (Grundgerüst G1 bis G5).

## Ablauf

1. **Arbeitsbereich finden:** `python akten/arbeitsbereich.py`. Bricht es ab, die Meldung
   wörtlich weitergeben und nach dem Pfad fragen; nie raten.
2. **Profil laden:** `python profil/profil.py <arbeitsbereich> --pruefen`. Fehler zuerst
   beheben lassen. Alle weiteren Schritte richten sich nach dem Profil (Fragen, Freigabe,
   Format). Werte immer über `profil.lade()`, nie aus der DOCX.
3. **Überblick:** `python akten/akten.py <arbeitsbereich>`. Fragt die Lehrkraft „wo war
   ich?“, genügt dieser Überblick mit „zuletzt gearbeitet an“ und einem Vorschlag, wie es
   weitergeht.
4. **Ansage verstehen:** Fach, Beruf, Lernfeld, Lernsituation, ggf. Klasse, Stunde, Termin
   und Stundentyp (Alltag, EUB/KUB/FLB, GUB/PU; Besuchstermine aus `Ref/`). Fehlt etwas
   Wesentliches, **eine** Frage dazu, nach Profil (`interview.*`): kurzer Kontext, drei
   Vorschläge, empfohlener zuerst, freie Antwort. Nie mehrere Fragen auf einmal.
5. **Bedarf prüfen:** `python akten/bedarf.py --beruf <B> --lf <n> --ls <n> [--klasse <K>]
   [--stunde] [--typ ...]`. Ziel ohne `--stunde` ist die Lernsituations-Akte; mit
   `--stunde` kommen Klassen- und Schuljahres-Akte dazu.
6. **Melden**, kurz und in dieser Form:
   - **Das habe ich:** freigegebene Akten (mit Datum)
   - **Das ist offen:** Entwurf, veraltet (mit Grund), ungeprüft (Datei ohne Steckbrief)
   - **Das fehlt:** fehlende Akten mit Schritt-Nummer
   - **Vorschlag:** Reihenfolge der fehlenden Schritte (nach Schrittnummer; Grundlagen
     vor dem, was darauf aufbaut), dazu Planungstiefe nach Stundentyp
7. **Vorhandenes zuerst:** Bevor ein fehlender Schritt startet, fragen, ob es dafür schon
   Dokumente gibt (Schulplanung, Stundenplan, Curriculum, Lernsituation der Schule …).
   Wenn ja: hochladen lassen (`Eingang/` oder Chat-Anhang), analysieren, übernehmen,
   abgleichen. Wenn nein oder unbekannt: komplett durchplanen; ein späterer Abgleich
   bleibt möglich.
8. **Erst nach Zustimmung** den ersten fehlenden Schritt starten. Jeder Schritt endet mit
   Prüfbericht und eigener Freigabe; erst dann der nächste. Zuständige Skills:
   01 `curriculare-analyse` · 02 `modellbetrieb`, `lernsituationen-skizze` · 03 `jahresplanung` ·
   04 `lernsituation` · 05/06 Klasse `klassenakte` · 06 `fehlvorstellungen` · 13/14 `stundenplanung` ·
   07 bis 16 Besuche `besuchsstunde` · 17 `nachbereitung` · Mappe `planungsmappe`.

## Regeln

- Der Einstieg selbst erzeugt **keine** Akte und ändert nichts; er liest nur.
- Interviews hängen an der Akte: gefragt wird nur, was eine fehlende oder veraltete Akte braucht.
- Ist eine Grundlage nur Entwurf, wird sie zuerst freigegeben, bevor darauf aufgebaut wird.
- Jede neue Akte bekommt beim Anlegen ihren Steckbrief in `.daten/akten/` (schreiben die
  Generatoren über `akten/steckbrief.py`); Freigabe mit `python akten/steckbrief.py freigeben
  <arbeitsbereich> <pfad>`; danach `python akten/akten.py` ohne Fehler.
- Arbeitsbereich und Werkzeug nie vermischen: Ergebnisse nur in den Arbeitsbereich.
- Lernende nur als Kürzel.
- **Lebende Übersicht:** Nach jeder Freigabe `python akten/stand.py <arbeitsbereich>` und die Dateien in `.daten/stand/` in der Webseite „Planungsstand Referendariat“ ersetzen (Adresse im README des Arbeitsbereichs). Zu Beginn jeder Planung den Stand der Lernsituation daraus zeigen (Lehrkraft 2026-10-24: der Überblick ging verloren).
