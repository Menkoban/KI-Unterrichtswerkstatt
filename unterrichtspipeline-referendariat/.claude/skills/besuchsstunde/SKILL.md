---
name: besuchsstunde
description: Besuchsstunden der Unterrichtspipeline (EUB, KUB, FLB, GUB, PU): plant die Stunde Entscheidung für Entscheidung und setzt den Entwurf nach den Vorgaben des Seminars aus dem Seminarprofil zusammen (Profilwert `seminar`, mitgeliefert Studienseminar Osnabrück, LBS), als Kurzentwurf (EUB, KUB, FLB) oder als vollen Entwurf mit Seitenbudget (GUB, PU), mit Deckblatt nach Seminar-Muster, Kompetenztabelle, Sequenzierung, kommentiertem Sitzplan, Material, Erwartungshorizont, Versicherung und KI-Übersicht; beim KUB zusätzlich Beobachtungsbogen und KUB-Protokoll. Verwende ihn, wenn eine Stunde besucht oder geprüft wird: „nächste Woche ist mein GUB“, „Entwurf für den EUB“, „KUB vorbereiten“, „Prüfungsunterricht planen“.
---

# Besuchsstunde und Entwurf (Schritte 07 bis 16)

Grundlage: `docs/ARBEITSWEISE.md`, `docs/KONZEPT.md` („Planungstiefe je Stundentyp“, Entwurf,
Seitenbudget, Protokollzeilen zu EUB, KUB, GUB, PU vom 11. und 12.10.2026). Seminarprofil: `seminare/<id>/seminar.json`
(Profilwert `seminar`; Name, Anschrift, Besuchsformen, Seitenbudget, Versicherung, Hinweise); ohne gewähltes Seminar
zuerst das Seminar im Profil klären.

**Seminar-Originale und didaktische Quellen** liegen im **Arbeitsbereich** (aus dem Einrichtungs-Interview):
`Quellen/Seminar/` (Leitfaden zum Unterrichtsentwurf, Weisungen für die Prüfung, Muster, Formulare wie das
KUB-Protokoll) und `Quellen/Didaktik/` (Fachdidaktik, Kompetenz- und Handlungsorientierung, Landesvorgaben), je mit
Quellenkarte. Vor dem Entwurf die passenden Originale lesen; Begründungen im Entwurf stützen sich auf diese Quellen und
stehen im Literaturverzeichnis. Fehlen sie, die Lehrkraft einmal darum bitten und sonst mit dem Seminarprofil allein
arbeiten (im Prüfbericht als Warnung „Seminar-Originale fehlen“). Ältere Arbeitsbereiche: auch `Quellen/` direkt und
im Werkzeug `Quellen/Wiki_StS_OS/`, `Quellen/Seminar_Downloads/` (nur in der privaten Fassung des Werkzeugs).
Eigene frühere Besuche als Beispiel: im Arbeitsbereich `.daten/stunde/*.json` mit Feld `besuch`.

## Ablauf

1. **Einordnen:** Besuchsart (EUB, KUB, FLB, GUB, PU), Klasse, LS und DS; `akten/bedarf.py
   --stunde --typ …`. Fehlt die Klassen-Akte, zuerst Skill `klassenakte`.
2. **Entscheidungen einzeln**, je mit kurzem Kontext und drei gleich ausführlichen Vorschlägen
   (Aufbau, Ablauf, Hilfen, Vor- und Nachteile; empfohlener zuerst, Begründung als eigener
   Satz; freie Antwort). Kein Auswahl-Werkzeug. Reihenfolge: Umfang (PU: 45 min oder Antrag auf
   90; geprüfte Hälfte), Kern, Phasen (Einstieg, Erarbeitung, Vergleich, Sicherung, Abschluss),
   Kompetenzen (Kernkompetenz ohne „indem“, TK mit „indem“ und Bereich FK, SoK, SeK, MK),
   besondere Bedarfe (sonderpädagogische Konzeption oder Heterogenitätstabelle), bei GUB und PU
   Schichten der Sachanalyse und Reduktion (Grüner, keine Vermengung von Ansätzen). Jede
   Entscheidung sofort als KONZEPT-Zeile, commit und push.
3. **Stunden-Daten** `.daten/stunde/<kurz>.json` wie bei `stundenplanung`, dazu Feld `besuch`
   (Art, Deckblatt, Kernkompetenz, TK, Sequenz mit genau einer Besuchsstunde, Literatur nur
   zitiert, KI-Verzeichnis; GUB und PU zusätzlich `kapitel` k1, k21 bis k24, k3, ggf.
   `sonderpaedagogik` oder `heterogenitaet`, `abkuerzungen`; KUB zusätzlich `beobachtung`).
   Ist der PU die zweite Stunde einer Doppelstunde, steht die erste Stunde als `vorlauf` davor.
4. **Erzeugen:** `python stunde/stunde.py <ab> <kurz>` (Verlaufsskizze, Materialauftrag), dann
   `python entwurf/entwurf.py <ab> <kurz>` → `Entwurf_<ART>.docx` und
   `Pruefbericht_Entwurf_<ART>.docx`, beim KUB `KUB_Protokoll.docx`. GUB und PU: zwei Durchläufe
   mit Seitenzahlen aus dem Satz und Messung des Budgets (1,5 · 0,5 · 0,5 · 1,5 · 1 · 1, ± 10 %,
   Kap. 1 bis 3 höchstens 6 Seiten). Fertiges Material aus Pipeline 2 liegt als
   `Anlagen/Anl_<nr>_<titel>.docx` und wird angehängt; fehlendes meldet der Entwurf mit „folgt“.
5. **Sichtprüfung:** DOCX nach PDF und Bild (soffice, pdftoppm) und Seiten ansehen; Deckblatt
   gegen das Seminar-Muster, Verlaufsskizze höchstens zwei Seiten.
6. **Abgleich mit den Seminar-Originalen** vor der Freigabe; Änderungen berichten.
7. **Freigabe:** `stand` im Stunden-JSON setzen, beide Generatoren neu laufen lassen, dann
   `python akten/steckbrief.py freigeben` für Verlaufsskizze, Materialauftrag und Entwurf;
   KONZEPT-Zeile, commit und push.

## Regeln

- Problemorientierter Einstieg und offener Auftrag wie in ARBEITSWEISE; nichts vorwegnehmen.

- Stunden werden ohne Moodle geplant; die Moodle-Umsetzung steht nur im Materialauftrag.
- Materialauftrag immer ausführlich (Pflichtfelder siehe ARBEITSWEISE); ein Niveau; Hilfen und
  Werkzeuge sind Vorschläge für Pipeline 2.
- KUB: alle Beobachtenden sehen alles, sitzen hinten; Bogen nach UB-BBS LK 2025.
- PU: Hinweise der Weisungen (Thema 15 Tage vorher, Abgabe am Vortag bis 12 Uhr an alle
  Mitglieder des Ausschusses, Sitzplan passwortgeschützt, zwei gedruckte Exemplare mit
  unterschriebener Versicherung, Reflexion höchstens 10 Minuten) stehen im Prüfbericht.
- Jede Lösung gerechnet; Werte aus Normen mit Quelle und Vermerk, wenn das Normblatt nicht
  vorlag. Reine KI-Vermutungen ohne Bezug werden gestrichen.
- Persönliche Felder des Deckblatts bleiben Platzhalter; keine Modellbezeichnungen in Dateien.
