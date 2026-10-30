# Arbeitsweise der Pipeline 1 (für alle Skills verbindlich)

Diese Datei fasst die Regeln zusammen, die für jeden Schritt gelten. Die Skills in
`.claude/skills/` verweisen hierher, statt die Regeln zu wiederholen. Herkunft und Datum jeder
Regel stehen im Entscheidungsprotokoll von `docs/KONZEPT.md`. Ändert sich eine Regel, wird sie
hier und im KONZEPT geändert, nicht in einzelnen Skills.

## Rangfolge

Ansage der Lehrkraft > Seminarvorgaben > vorhandenes Material der Schule > Vorgabe der Pipeline.
Eine Abweichung von Rahmenlehrplan, Seminar oder Schule wird im Dokument ausgewiesen, nie still
übernommen.

## Mit der Lehrkraft sprechen

- **Immer auf Deutsch (Lehrkraft 2026-10-27, zweimal korrigiert):** Jede Antwort an die Lehrkraft auf Deutsch in der
  Sie-Form, auch Zusammenfassungen nach Helfern und Berichte; nie ins Englische wechseln.
- **Eine Frage nach der anderen.** Vor der Frage kurzer Kontext (worum es geht, was schon
  feststeht), damit die Lehrkraft nichts nachschlagen muss.
- **Wenig Input auf einmal (Lehrkraft 2026-10-19 in Pipeline 3, 2026-10-27 für alle drei Pipelines):** Auch der
  Kontext vor einer Frage bleibt kurz. Keine Sammellisten offener Punkte vorweg („was noch fehlt“, acht Punkte auf
  einmal); jeden Punkt erst dann nennen, wenn er als Frage dran ist, und erst nach der Antwort den nächsten.
- **Drei Vorschläge, gleich ausführlich.** Jeder Vorschlag mit Ablauf, Hilfen, Vorteilen und
  Nachteilen im selben Umfang; der empfohlene steht zuerst, seine Begründung als eigener Satz.
  Dazu immer die Möglichkeit einer freien Antwort. Kein Auswahl-Dialogwerkzeug.
- **Kürzel nie ohne Legende:** LK, TK, FV, DS, AFB usw. im Chat mit Wortlaut, im Dokument als
  Legendentabelle.
- Die Lehrkraft arbeitet am Tablet und spricht oft frei (Sprachnachricht). Offensichtlich
  fremde Satzteile (Fernsehen, Nebengespräche) ignorieren; bricht eine Nachricht mitten im Satz
  ab, darauf hinweisen und nachfragen, statt zu raten.

## Freigabe und Dokumentation

- **Vor jeder Freigabe ein Prüfbericht** mit Fehler, Warnung, Hinweis. Die Generatoren prüfen
  selbst und schreiben ihre Befunde in das Dokument; eigene Befunde kommen dazu.
- **Jede Entscheidung sofort** als Zeile im Entscheidungsprotokoll von `docs/KONZEPT.md`
  (Werkzeug), dann committen und pushen. Ergebnisse gehören in den Arbeitsbereich, nie ins
  Werkzeug; auch dort sofort committen und pushen.
- **Akten-Steckbrief:** jedes Dokument hat einen Steckbrief in `.daten/akten/` (schreiben die
  Generatoren). Bei Freigabe `stand: freigegeben` und `freigegeben_am` setzen und den Text
  „Stand“ in den Daten anpassen, dann neu erzeugen. `python akten/akten.py <arbeitsbereich>`
  muss danach ohne Fehler laufen; „veraltet“ heißt: eine Grundlage wurde später geändert, die
  Akte prüfen und, wenn sie inhaltlich nicht betroffen ist, unverändert neu erzeugen.
- Eine Änderung an einer schon freigegebenen Akte auf Ansage der Lehrkraft wird ausgeführt
  und im Prüfbericht der Akte vermerkt (Datum, was, warum).

- **Korrekturen eng auslegen (Lehrkraft 2026-10-27, gilt für alle drei Pipelines):** Eine Korrektur gilt genau für
  das, was die Lehrkraft benannt hat. Nicht stillschweigend auf Verwandtes ausdehnen (Beispiel: „keine Beschreibungen
  unter den Aktivitäten“ hat auch Sterne, Versuche und Sozialform entfernt; „Sozialform frei“ hat auch das
  Sozialform-Symbol entfernt; beides musste zurückgenommen werden). Betrifft eine Korrektur möglicherweise mehr, kurz
  nachfragen oder die Ausdehnung im Bericht ausdrücklich nennen.
- **Eine Quelle für Material und Kurs (Lehrkraft 2026-10-27):** Was im Arbeitsheft steht, wird im Kurs nicht neu
  geschrieben, sondern aus dem Heft übernommen (Infoseiten als Auszug der Gesamtfassung, Word und PDF zum Herunterladen);
  eigene Fassungen der Helfer laufen sonst auseinander.
- **Leseseite und Korrekturzähler (Lehrkraft 2026-10-25, Profil `freigabe.leseseite`):** Jede Freigabe beginnt mit
  einer Leseseite (neu, selbst entschieden, unsicher, je mit Verweis). Jede Freigabe wird in `.daten/freigaben.json`
  mit Art (planung, material, moodle) und Zahl der grundsätzlichen Korrekturen eingetragen; zwei Freigaben einer Art
  hintereinander ohne grundsätzliche Korrektur: dort reicht künftig ein Gesamtblick. Material gilt ab LS 3 als
  Gesamtblick, Planung wird ab LS 4 gezählt.

## Weitergabe

- **Erst persönlich, dann teilbar (Lehrkraft 2026-10-13, gilt für alle drei Pipelines):** Jetzt
  vollständig auf die Lehrkraft zugeschnitten, kein Umbau auf ein allgemeines Profil vorziehen. Wenn
  alles fertig ist, wird der allgemeine Teil in ein neues, teilbares Repo gezogen, das beim ersten
  Start fragt „Wer sind Sie?“ (Schule, Logo, Farben, Beruf, Seminar, Arbeitsweise). Die persönliche
  Fassung bleibt hier.

## Planen

- **Vorhandenes zuerst:** Vor jedem Schritt fragen, ob es dazu schon Dokumente gibt
  (Schulplanung, Stundenplan, Lernsituation der Schule …). Wenn ja: hochladen lassen,
  analysieren, übernehmen, abgleichen. Wenn nein: komplett durchplanen.
- **Streng von oben nach unten:** Jahresplanung → Lernfeld → Lernsituationen → Stunden.
- **Idealplanung ohne Kalender:** Skizze, Lernsituationen und Stunden werden ohne Ferien,
  Wochen und Stundenplan geplant; „Std. 1–80“ ist eine Zählung im Lernfeld. Die zeitliche
  Zuordnung macht die Lehrkraft später oder auf Ansage mit einem Stundenplan. Stunden-Ordner
  heißen bis dahin `UEnn_Kurzthema`, das Datum kommt bei der Zuordnung davor.
- **Vollständige Handlung auf drei Ebenen:** Lernfeld, Lernsituation und innerhalb der LS in
  2 bis 3 Arbeitsschritten über mehrere Doppelstunden (Profil `innerer_zyklus.umfang`).
  Planen wird nie übersprungen.
- **Problemorientierter Einstieg (Lehrkraft 2026-10-13):** Das Material nimmt nichts vorweg. Erst das
  Problem (am besten ein Widerspruch, z. B. Anzeige 180 °C, Prüfthermometer etwa 172 °C), dann
  überlegen, informieren und planen die Lernenden selbst. Der Auftrag ist offen („Ursache ermitteln,
  belegen und dem Kunden eine Empfehlung geben“) und gibt weder Methode noch Lösungsweg vor, nie
  „gegeben/gesucht“. Daten, die auf die Ursache zeigen, stehen nur im Informationspool, gemischt mit
  unwichtigen Angaben, nicht in Situation, Telefonnotiz oder Auftrag; auch keine Vorgeschichte, die auf
  die Ursache zeigt (wer was getauscht hat), und keine Aufgabe in einer Informieren-DS, die das Fehlerbild schon bis
  zur Ursache deutet. Beides erst in der DS, die die Ursache sucht (Korrektur Probelauf LS 5, 2026-10-27). Ein Fall wird in allen Anlagen
  gleich beschrieben. Gestufte Hilfekarten (Tipp, Ansatz, Lösungsweg) bleiben. Der Umfang je DS wird
  bei der Erprobung geklärt. `stunde/stunde.py` warnt bei „gegeben/gesucht“ und vorgegebenem Weg.
- **Selbstständig mit Gerüst (Grundkonzept Elektrotechnik, Lehrkraft 2026-10-25, Profil `lernsituation.form`):**
  Zu Beginn der LS stellt die Lehrkraft die Handlungssituation vor; die Lernenden bekommen einen Arbeitsplan mit den
  Teilergebnissen (Meilensteine mit spätestem Termin) und arbeiten im Team selbstständig. Jede DS beginnt mit etwa
  5 min Orientierung („Wo stehen wir?“) und endet mit einem kurzen Blick auf die Teilergebnisse; dazwischen
  moderiert und berät die Lehrkraft. Sicherheitskritische Teile (erstes Messen, erster Aufbau) leitet sie an.
  Material ist Auftrag, Arbeitsplan und Informationspool; der Moodle-Kurs ist der Lernpfad dazu.
  Werkzeug: `lernsituation/arbeitsplan.py` (Planung der LS) und Kurzskizzen je DS (Stunden-Akte mit Feld
  `arbeitsplan`); fester Lernpfad, Einzelarbeit mit freier Partnerarbeit, Kontrollblatt am Pult.
- **Rüstzeiten mitplanen (Lehrkraft 2026-10-25):** Praktische Phasen (Messen, Aufbauen, Stationen) bekommen im
  Verlauf eigene Zeit für Einweisung, Aufbau und Abbau, beim ersten Mal deutlich mehr. Welche Organisation
  (vorbereitete Plätze, Demonstration vorn mit einzelnen Lernenden, eigener Aufbau) wird je Stunde entschieden
  und mit Geräteliste in der Verlaufsskizze festgehalten. `stunde/stunde.py` warnt, wenn eine praktische Phase
  ohne Einweisung oder Aufbau im Verlauf steht.
- **Ohne echte Klasse:** Annahmen zur Klasse offen in der Verlaufsskizze nennen; die
  Klassen-Akte entsteht, sobald es eine echte Klasse gibt.
- **Material wird als Arbeitsblatt geplant.** Pipeline 2 baut es, Pipeline 3 macht daraus den
  Moodle-Kurs; in Pipeline 1 wird nicht zwischen Papier und Moodle entschieden.
- **Stunden ohne Moodle planen (Lehrkraft 2026-10-12):** Verlauf, Sozialformen und Medien der Stunde
  kommen ohne Moodle aus (Abstimmung per Handzeichen oder Karten, Sicherung an Tafel und Merkkarte).
  Wie jede Anlage als Material und im Moodle-Kurs umgesetzt wird, steht nur im Materialauftrag:
  Felder „Werkzeug (Vorschlag)“ und „Moodle“, zusammengefasst in der Übersicht der Anlagen.
  `stunde/stunde.py` warnt, wenn der Verlauf Moodle einplant.
- **Materialauftrag immer ausführlich (Lehrkraft 2026-10-12):** Pipeline 2 baut jede Anlage
  allein aus dem Auftrag. Pflichtfelder je Anlage: Zweck, Phase und TK; Inhalt und Wortlaut
  (alle Aufgaben- und Kartentexte wörtlich); Aufbau und Layout; Hilfen; Moodle;
  Werkzeug (Vorschlag); Quellen; Abnahmekriterien; dazu der Erwartungshorizont. Jede Anlage
  geht in den Moodle-Kurs (nie „Moodle: keine“). Hilfen und Werkzeuge sind Vorschläge;
  Pipeline 2 stimmt sie mit der Lehrkraft ab. Vorneweg „Für alle Materialien gilt“,
  Gestaltungsvorgaben und eine Übersicht mit Dateinamen `Anl_<Nr>_<Kurztitel>.docx`.
  `stunde/stunde.py` meldet fehlende Felder als Fehler.
- **Profil:** Werte nur über `profil.lade(<arbeitsbereich>)`, nie aus der DOCX.

## Fachlich

- **Rolle:** Die Lernenden sind Gesellinnen und Gesellen im fiktiven Modellbetrieb des Berufs,
  Ansprache in der Sie-Form. Namen von Betrieben und Personen per Websuche prüfen, damit kein
  echter Betrieb gemeint sein kann.
- **Ein Niveau (Lehrkraft 2026-10-13):** Beginner, Könner, Experte sind gestrichen, in Pipeline 1
  und 2. Alles wird zuerst auf einem Niveau geplant und gebaut, mit gestuften Hilfekarten.
  Differenzierung nach oben und unten (Niveauschachtelung) folgt erst, wenn ein Niveau läuft.
  Stunden von vor dieser Entscheidung bleiben, wie sie freigegeben sind.
- **Nachbereitung:** nach jeder Stunde frei gesprochen, nach Reichweite abgelegt (Skill
  `nachbereitung`); jede Stundenplanung beginnt mit den offenen Punkten daraus.
- **Rechnen statt schätzen:** jede Zahl im Erwartungshorizont gerechnet und plausibel (auch
  Gerätedaten: realistische Leistungen, Spannungen, Einsatzorte).
- **Abgrenzung** gegen Nachbar-Lernfelder in jedem Schritt prüfen (curriculare Analyse).
- **Fehlvorstellungen:** vor dem Entwurf recherchieren. Herkunft Forschung (mit Literatur),
  Erfahrung der Lehrkraft, eigene Beobachtung oder KI-Vermutung mit Bezug (verwandte Theorie,
  Fach- oder Praxisquelle). Reine KI-Vermutungen ohne jeden Bezug werden nicht aufgenommen.
  Nur gelesene Quellen zitieren; was nur aus einer Zusammenfassung bekannt ist, so kennzeichnen.
- **Quellen:** Abbildungen aus Fachbüchern dürfen übernommen oder nachgezeichnet werden; die
  Quelle steht immer an der Abbildung und im Literaturverzeichnis. Keine KI-Bilder für
  Schaltpläne oder Fotos von Anlagen.
- **KI-Fußnote** auf jedem KI-gestützten Material (Seminarvorgabe; Seminarprofil nach Profilwert `seminar`, Profil `material.ki_fussnote`).

## Form

- Ausgaben für die Lehrkraft als **DOCX** (XLSX, PPTX, HTML, wo es passt); PDF nur auf
  ausdrücklichen Wunsch. Interne Daten als JSON in `.daten/`.
- Fließtext in wenigen, längeren Absätzen, ohne Gedankenstriche, im Entwurf Blocksatz
  (Profil `form.*`). Feinformatierung macht die Lehrkraft in Word.
- Keine echten Namen von Lernenden (nur Kürzel), keine Modellbezeichnungen in Dateien, die ins
  Repository gehen.

## Erst testen, dann pushen (2026-10-23)

Nach jeder Änderung an einem Generator (`stunde/stunde.py`, `entwurf/entwurf.py`, `entwurf/voll.py`, …) ihn an
einer echten Akte laufen lassen; erst ohne Fehler committen und pushen.

- **Keine Problemführung** (Lehrkraft 2026-10-30): Nach der Handlungssituation führen weder Leitfragen der Doppelstunden noch Material oder Moodle-Kurs zur Ursache oder zum Lösungsweg hin. Die Lernenden stellen Vermutungen auf, informieren sich selbst, legen einen eigenen Plan an und durchlaufen die vollständige Handlung; Impulse nur im Erwartungshorizont. Eine Reihenfolge der Aktivitäten als Orientierung ist erlaubt.
- **Vollständige Handlung selbstständig** (Lehrkraft 2026-10-30): Jede Lernsituation beginnt problemorientiert mit dem Symptom; die Lernenden informieren sich, planen, entscheiden, führen aus, kontrollieren und bewerten bzw. reflektieren selbstständig. Leitfragen der Doppelstunden benennen Handlungsphasen oder Kundenfragen, nicht die Ursache oder den Fachinhalt, der zur Lösung führt.
- **Einstieg einer Lernsituation** (Lehrkraft 2026-10-30): Situation mit dem Symptom und den Fragen der Kundschaft; die Rolle (Gesellin bzw. Geselle, Facharbeiter/in) steckt in der Geschichte („Ihre Meisterin gibt Ihnen als … den Auftrag“). Der Auftrag nennt nur das Ziel, ohne Vorgehen und ohne Qualitätskriterien („systematisch“, „mit Messwerten belegen“ gehören in die Bewertung des Meilensteins); das Handlungsprodukt zeigt sich über die Fragen der Kundschaft („… und beantworten Sie der Familie ihre Fragen“). Kein eigener Absatz „Ergebnis“ im Einstieg; Bestandteile der Abgabe stehen in der Kachel bzw. im Arbeitsplan des Meilensteins. Organisation (eigenes Tempo, Meilensteine) gehört in „So arbeiten Sie“, nicht in die Situation.
