# So spielen Sie einen Themenkurs ein

Allgemeine Anleitung für alle Themenkurse (Entscheidung Punkt 24). Kursbezogene Angaben (Gruppen, Freischaltplan,
Medaillen) stehen in der Handreichung im verborgenen Lehrkraftbereich des Kurses.

1. **Sicherung bereitlegen:** die `.mbz` aus `<LS>/Moodle/` im Arbeitsbereich.
2. **Gegengeprüft ist er schon:** Jeder Kurs wurde vor der Abnahme live in ein Test-Moodle 5.1.6 mit Kachelformat
   eingespielt und nachgezählt; das Protokoll liegt als `<kurs>.einspielprotokoll.json` neben der `.mbz`. Durchklicken
   können Sie ihn dort mit `python3 werkzeug/testmoodle/testmoodle.py ansehen` (http://localhost:8095).
3. **Immer als neuen Kurs einspielen:** im Moodle der Schule „Wiederherstellen“ → Datei hochladen → „In einen neuen
   Kurs“ (Kursbereich Ihrer Klasse) → Kursname und Kurzname aus der Sicherung übernehmen. Nur so erscheint der Kurs
   als Kacheln. Spielen Sie ihn in einen schon bestehenden Kurs ein, übernimmt Moodle zwar die Inhalte, behält aber
   die Einstellungen des alten Kurses. Muss es trotzdem ein bestehender Kurs sein: danach im Kurs unter
   „Einstellungen → Kursformat“ auf „Tiles“ stellen und speichern.
4. **Einschreibung:** im Themenkurs unter Teilnehmer/innen → Einschreibemethoden → „Meta-Einschreibung (Kursbezug)“
   hinzufügen und den Lernfeldkurs der Klasse wählen. Die Klasse ist damit automatisch eingeschrieben.
5. **Link im Lernfeldkurs:** in der Kachel der Lernsituation einen Link (Textfeld oder Link-Aktivität) auf den
   Themenkurs setzen.
6. **Gruppen zuteilen:** Teilnehmer/innen → Gruppen; die leeren Gruppen (z. B. „Team A“) mit der Klasse füllen.
7. **Freischalten:** Der Einstieg ist sichtbar; weitere Abschnitte im Unterricht über das Auge sichtbar schalten.
8. **Abzeichen aktivieren:** Die Abzeichen für die Medaillen kommen ausgeschaltet an (Status „Nicht verfügbar“). Im
   Kurs oben „Mehr → Badges“ wählen (so heißen die Abzeichen im deutschen Moodle). In der Liste bei jeder Medaille
   rechts auf die drei Punkte (Aktionen) klicken, „Zugriff aktivieren“ wählen und im Fenster „Bestätigen“ auf
   „Aktivieren“ drücken. Der Status springt auf „Verfügbar“; erst dann bekommen die Lernenden ihre
   Medaille. Das für alle vier Medaillen wiederholen.
9. **Kurz durchklicken** mit „Rolle wechseln → Schüler/in“.
