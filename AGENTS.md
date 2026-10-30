# KI-Unterrichtswerkstatt: Anweisungen für KI-Assistenten

Gilt für jede KI-App, die in diesem Repository arbeitet (Claude Code, OpenAI Codex, Google Antigravity, Hermes Agent
und andere, die `AGENTS.md` und Agent Skills lesen). Claude Code liest dieselben Regeln über `CLAUDE.md`.

## Zu Beginn jeder Sitzung

1. `bash einrichten.sh` ausführen (Claude Code macht das selbst beim Start). Das Skript findet den persönlichen
   Arbeitsbereich und teilt ihn den drei Werkzeugen mit. In Cloud- oder Linux-Umgebungen ohne LaTeX und LibreOffice:
   `bash einrichten.sh --programme`.
2. Gibt es noch keinen Arbeitsbereich mit `Profil/lehrkraft-profil.json`: auf `STARTPROMPT.md` hinweisen und die
   Einrichtung danach führen.
3. Sonst wie der Skill `einstieg`: Profil laden, vorhandene Akten prüfen, fragen „Was steht an?“

## Aufbau

Drei Werkzeuge in einem Repository; jedes hat eigene, verbindliche Regeln in seiner `CLAUDE.md` (bitte lesen, sobald
Sie in dem Ordner arbeiten):

- `unterrichtspipeline-referendariat/`: Pipeline 1, Unterrichtsplanung (Konzept `docs/KONZEPT.md`, Arbeitsweise
  `docs/ARBEITSWEISE.md`, Profil-Vorlage `profil/vorlage.json`).
- `materialpipeline-referendariat/`: Pipeline 2, Material aus dem Materialauftrag.
- `moodlepipeline-referendariat/`: Pipeline 3, Moodle-Themenkurs aus Planung und Material.

## Skills

Jeder Arbeitsschritt ist ein Skill (Agent-Skills-Format, `SKILL.md` mit Name und Beschreibung). Die Skills liegen in
`.agents/skills/` (für Codex, Antigravity und andere) und unverändert in `<werkzeug>/.claude/skills/` (für Claude
Code). Passt eine Anfrage zu einem Skill, zuerst seine `SKILL.md` lesen und ihr folgen. Pfade und Befehle in einem
Skill gelten relativ zu seinem Werkzeug-Ordner.

| Skill | Werkzeug-Ordner | Zweck |
|---|---|---|
| `besuchsstunde` | `unterrichtspipeline-referendariat/` | Besuchsstunden der Unterrichtspipeline (EUB, KUB, FLB, GUB, PU): plant die Stunde Entscheidung für Entscheidung und setzt den Entwurf nach den Vorgaben des Seminars aus dem Seminarprofil zusammen (Profilwert `seminar`, mitgeliefert Studienseminar Osnabrück, LBS), als Kurzentwurf (EUB, KUB, FLB) oder als vollen Entwurf mit Seitenbudget (GUB, PU), mit Deckblatt nach Seminar-Muster, Kompetenztabelle, Sequenzierung, kommentiertem Sitzplan, Material, Erwartungshorizont, Versicherung und KI-Übersicht; beim KUB zusätzlich Beobachtungsbogen und KUB-Protokoll |
| `curriculare-analyse` | `unterrichtspipeline-referendariat/` | Schritt 01 der Unterrichtspipeline: Curriculare Analyse eines Lernfelds aus dem Rahmenlehrplan |
| `einstieg` | `unterrichtspipeline-referendariat/` | Einstieg „Was steht an?“ der Unterrichtspipeline (Pipeline 1, Schritt 00) |
| `fehlvorstellungen` | `unterrichtspipeline-referendariat/` | Schritt 06 der Unterrichtspipeline (themenbezogener Teil): Lernausgangslage je Inhalt und Fehlvorstellungen einer Lernsituation, vorab recherchiert und belegt, mit Herkunft, Doppelstunde, Priorität, Aufdecken über ein Diagnose-Item und Aufgreifen im Unterricht |
| `jahresplanung` | `unterrichtspipeline-referendariat/` | Schritt 03 der Unterrichtspipeline: Jahresplanung als Schuljahres-Akte je Klasse (Bildungsgang, Ausbildungsjahr, Schuljahr) |
| `klassenakte` | `unterrichtspipeline-referendariat/` | Schritte 05 und 06 (Klassenteil) der Unterrichtspipeline: legt die Klassen-Akte einer Klasse an oder pflegt sie, also Bedingungsfeld nach Seminar-Leitfaden 1.1 bis 1.5 mit Konsequenz je Bedingung, drei Personas, allgemeine Lernausgangslage und kommentierten Sitzplan (Bild aus dem Sitzplan-Studio, darunter die Kommentartabelle mit Noten) |
| `lernsituation` | `unterrichtspipeline-referendariat/` | Schritt 04 der Unterrichtspipeline: arbeitet eine Lernsituation aus der Skizze aus (Kernkompetenz, Handlungssituation, Auftrag, Handlungsergebnis, echte Entscheidung, Bewertung, innere vollständige Handlungen als Zyklen über Doppelstunden, Doppelstunden mit Leitfrage, Inhalten, Teilergebnis, Phasen und LK) |
| `lernsituationen-skizze` | `unterrichtspipeline-referendariat/` | Schritt 02 der Unterrichtspipeline: skizziert, wie ein Lernfeld in Lernsituationen zerfällt (Titel, Handlungssituation, Handlungsergebnis, echte Entscheidung, Lernfeld-Kompetenzen mit Legende, Inhalte, Stunden), mit übergeordneter Handlungssituation im Modellbetrieb |
| `modellbetrieb` | `unterrichtspipeline-referendariat/` | Teil von Schritt 02 der Unterrichtspipeline: legt den fiktiven Modellbetrieb eines Berufs bzw. einer Fachrichtung an (Steckbrief, Personen, Kunden, Rolle der Lernenden als Gesellinnen und Gesellen), der in allen Lernfeldern als durchgehende Handlungssituation dient |
| `nachbereitung` | `unterrichtspipeline-referendariat/` | Schritt 17 der Unterrichtspipeline: Die Lehrkraft spricht nach einer Stunde frei ein, was war (Text oder Sprachnachricht, ohne feste Fragen) |
| `planungsmappe` | `unterrichtspipeline-referendariat/` | Fasst die Akten einer Planung (Jahresplanung, Modellbetrieb, curriculare Analyse, Skizze, Lernsituationen, Fehlvorstellungen, Stunden) zu einer Planungsmappe als DOCX zusammen, mit einer Einführung für Außenstehende (Schulleitung, Mentor, Seminar) und dem Stand jedes Dokuments |
| `stundenplanung` | `unterrichtspipeline-referendariat/` | Stundenebene der Unterrichtspipeline für eine Doppelstunde: Mikro-Einstieg mit dem, was schon feststeht, Interview Frage für Frage (Einstieg, Arbeitsblatt, Sozialform, Sicherung, Besonderheiten), dann Verlaufsskizze (Schritt 13) und Materialauftrag für Pipeline 2 (Schritt 14) mit Teilkompetenzen, Fehlvorstellungen, Annahmen und Erwartungshorizonten |
| `arbeitsblatt` | `materialpipeline-referendariat/` | Baut nur das Arbeitsblatt einer Anlage (DOCX aus der Schulvorlage): Situation aus dem Modellbetrieb, Aufgaben problemorientiert, Rechen- und Skizzenfelder |
| `dokumente` | `materialpipeline-referendariat/` | Weitere Materialarten aus den abgenommenen Schulvorlagen: Einstieg, Infoblatt/Datenblatt, Messprotokoll, Serviceauftrag, Servicebericht, Selbstkontrolle, Karte A5, Tafelbild, Folien (PPTX), Tabelle (XLSX) |
| `erwartungshorizont` | `materialpipeline-referendariat/` | Erwartungshorizont zu einer Anlage: erwartete Lösung gerechnet, anerkannte andere Wege, typische Fehler mit Reaktion |
| `hilfekarten` | `materialpipeline-referendariat/` | Optionaler Skill für gestufte Hilfekarten (Tipp, Ansatz, Lösungsweg) zu einem Arbeitsblatt |
| `installationsplan` | `materialpipeline-referendariat/` | Installationspläne (Grundriss unter/auf Putz), Übersichtsschaltpläne, Verteiler-Übersichtsschaltpläne und Leitungsbemessung aus einer gemeinsamen Verschaltung: Aderzahl berechnet, Spannungsfall und Ib ≤ In ≤ Iz geprüft, Plansatz gemeinsam geprüft |
| `materialauftrag` | `materialpipeline-referendariat/` | Hauptablauf von Pipeline 2 (Baustein 9): setzt den freigegebenen Materialauftrag einer Stunde aus Pipeline 1 in fertiges Material um: lesen, Lücken fragen, Materialplan (Freigabe 1), je Anlage den passenden Fach-Skill aufrufen, dreistufig prüfen, Prüfbericht (Freigabe 2), ablegen und an Pipeline 3 übergeben |
| `quellen` | `materialpipeline-referendariat/` | Quellen aufnehmen und nutzen: Fotos, Scans und PDF aus dem Chat ablegen, Texterkennung, Quellenkarte, Volltextsuche; eigene Recherche, wenn nichts mitgegeben ist |
| `rechenblatt` | `materialpipeline-referendariat/` | Rechenprüfer und Diagramme: jede Zahl im Material wird mit Einheiten gerechnet (Pint, Gegenprobe lcapy), Rechenweg für Erwartungshorizont und Hilfekarten, Abgleich aller Anlagen einer Stunde, Kennlinien aus derselben Rechnung |
| `simulation` | `materialpipeline-referendariat/` | Interaktive HTML-Simulationen zu Stromlaufplänen und Anlagen (offline, Schulfarben) in bis zu drei Fassungen: Schaltplan + Technologieschema, nur Schaltplan, nur Technologieschema, gerechnet auf dem gezeichneten Plan |
| `stromlaufplan` | `materialpipeline-referendariat/` | Stromlaufpläne (Haupt- und Steuerstromkreis, Schützschaltungen) im Industriestil A3 mit dem Plan-Baukasten: Beschreibung als Strompfade, Rechnung, Ablaufprüfung, Wenn-dann-Tabelle, nichts verdeckt |
| `technologieschema` | `materialpipeline-referendariat/` | Technologieschemata von Anlagen im Fachbuch-Stil (TikZ, Schrägbild mit Tiefe, Graustufen, Positionsnummern mit Legende), Betriebsmittel mit denselben Kennzeichen wie im Schaltplan |
| `themenkurs` | `moodlepipeline-referendariat/` | Hauptablauf von Pipeline 3: macht aus einer fertigen Lernsituation (Planung aus Pipeline 1, Material aller Doppelstunden aus Pipeline 2) einen Moodle-Themenkurs: Eingang lesen, Grilling bis zum gemeinsamen Kursplan (DOCX, Freigabe), Bau in einem Lauf mit parallelen Helfern je Abschnitt, Prüfer, Test-Moodle, Sichtprüfung, Abnahme, Ablage der .mbz |

## Regeln für alle drei

- **Werkzeug und Arbeitsbereich getrennt:** Ergebnisse, Profil und alles Persönliche gehören in den privaten
  Arbeitsbereich `unterrichtspipeline-referendariat-<name>` (eigenes Repository, im Werkzeug-Ordner von Git ignoriert
  oder als Nachbarordner; Pfad auch über `UPR_ARBEITSBEREICH` oder `.arbeitsbereich`). Nie etwas Persönliches in
  dieses Repository schreiben. Persönliche Vorlieben werden Profilwerte, nicht fester Code.
- Antworten auf Deutsch, in der Sie-Form. **Eine Frage zur Zeit**: kurzer Kontext, drei gleich ausführliche Vorschläge
  (empfohlener zuerst), dazu freie Antwort; erst die Antwort abwarten. Begründet widersprechen, immer mit Alternative.
- Vor jeder Freigabe ein Prüfbericht mit Fehler, Warnung, Hinweis. Jede Korrektur der Lehrkraft sofort als Regel
  festhalten (Profilwert, Stilregel oder Prüfung).
- **Moodle-Kurse: Live-Restore ist Pflicht.** Jede .mbz wird vor der Abnahme mit
  `python3 moodlepipeline-referendariat/werkzeug/testmoodle/testmoodle.py einspielen <kurs.mbz>` in das lokale
  Test-Moodle 5.1.6 mit Kachelformat eingespielt (fehlt es: `einrichten`); `testmoodle.py pruefen <kurs.mbz>` muss OK
  melden. Ohne erfolgreichen Live-Restore gilt ein Kurs nicht als fertig.
- Ausgaben für die Lehrkraft als DOCX (bzw. XLSX, PPTX, HTML); interne Daten als JSON in `.daten/` des Arbeitsbereichs.
- Lernende nur als Kürzel (S01 …), nie mit Namen. Keine Bezeichnungen von KI-Modellen in Dateien, die ins Repository
  gehen.
- Jede Änderung im Arbeitsbereich committen und pushen; Git ist dort die einzige Sicherung.
