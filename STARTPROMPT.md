# Startprompt: Einrichtung beim ersten Mal

Ihre KI-App (Claude Code, Codex, Antigravity, Hermes) in der Wurzel dieses Repositorys starten, in der Cloud mit Ihrer
Kopie dieses Repositorys und Ihrem leeren, privaten Arbeitsbereich, dann den Text zwischen den Linien einfügen. Mehr ist nicht nötig; alles Weitere
fragt die KI.

---

Ich bin Lehrkraft an einer berufsbildenden Schule und möchte die KI-Unterrichtswerkstatt in diesem Repository für mich
einrichten. Bitte arbeite auf Deutsch, in der Sie-Form, und stelle mir **immer nur eine Frage zur Zeit**: kurzer
Kontext, drei gleich ausführliche Vorschläge (den empfohlenen zuerst), dazu die Möglichkeit, frei zu antworten.
Warte jeweils meine Antwort ab.

1. **Lesen:** zuerst `README.md` und `AGENTS.md` in der Wurzel und führe `bash einrichten.sh` aus, dann
   `unterrichtspipeline-referendariat/docs/ARBEITSWEISE.md` und die Profil-Vorlage
   `unterrichtspipeline-referendariat/profil/vorlage.json` (alle Einstellungen mit neutralem Standard).
2. **Technik prüfen:** Python 3, Git, `python-docx`, LibreOffice (`soffice`); fehlt etwas, sag mir kurz, wie ich es
   nachhole, und warte. Dann `python3 unterrichtspipeline-referendariat/setup_laptop.py`.
3. **Arbeitsbereich:** Finde mein privates Repository `unterrichtspipeline-referendariat-<name>` (im Werkzeug-Ordner
   oder daneben). Fehlt es, führe mich Schritt für Schritt durch `ANLEITUNG.md` (Abschnitte 1 bis 3: Konto, Fork,
   privates Repository über den vorausgefüllten Link, Zugriff für die KI-App) und warte; ich muss danach eine neue
   Sitzung mit beiden Repositories starten. Ist es leer, kopiere den Inhalt von
   `unterrichtspipeline-referendariat/docs/arbeitsbereich/repo-geruest/` hinein (mit versteckten Dateien), committe
   und pushe. Prüfe, dass der Arbeitsbereich **privat** ist und **nicht** im Git dieses Werkzeugs landet. Ich kenne
   Git nicht: Erledige alles Technische selbst und erkläre es nur in einem Satz.
4. **Einrichtungs-Interview**, eine Frage zur Zeit, in dieser Reihenfolge:
   1. Name und gewünschte Anrede in Dokumenten; Rolle (Referendariat, Lehrkraft, Quereinstieg).
   2. Schule: Name, Ort, Logo (ich lade es hoch, du legst es unter `Profil/` ab).
   3. Seminar: passt ein Profil aus `unterrichtspipeline-referendariat/seminare/`? Sonst lade ich meine
      Seminarunterlagen (Leitfaden, Entwurfsmuster, Besuchsformen) hoch, und du legst daraus ein neues Seminarprofil
      an. Ohne Seminar: `keins`.
   4. Fächer, Berufe oder Bildungsgänge, Klassen im laufenden Schuljahr (Klassen nur mit Kürzel, Lernende nie mit
      Namen). Gilt das Fachpaket Elektrotechnik (`fach.elektrotechnik`)?
   5. Rahmenlehrpläne bzw. Lehrpläne meiner Fächer: aus amtlicher Quelle laden oder ich lade sie hoch; Ablage unter
      `Quellen/`.
   6. Didaktische Quellen: Ich lade hoch, worauf meine Planung fachlich und didaktisch fußen soll, zum Beispiel
      Leitfäden und Handreichungen des Seminars, Unterlagen aus Fachseminar und Pädagogik, Fachdidaktik, Texte zu
      Kompetenzorientierung, Handlungsorientierung, Lernfeldkonzept und Medienbildung, Landesvorgaben (etwa schulisches
      Curriculum), Fachbücher und Tabellenbücher, die meine Lernenden nutzen. Lege sie im Arbeitsbereich unter
      `Quellen/Didaktik/`, `Quellen/Seminar/` und `Quellen/Fach/` ab, je mit kurzer Quellenkarte (Titel, Autor,
      Jahr, wofür nutzbar). Frag nach, wofür ich jede Quelle verwendet sehen will (Begründungen im Entwurf,
      Kompetenzformulierung, Material), und nenne mir, welche Quellen für Besuchsentwürfe üblicherweise noch fehlen.
      Diese Quellen bleiben privat; sie gehören nie in das öffentliche Werkzeug.
   7. Eigene Unterlagen: Ich lade vorhandene Arbeitsblätter, Entwürfe oder Vorlagen der Schule hoch. Leite daraus
      Gestaltung und Vorlieben ab (Kopfzeile, Schrift, Merkkasten, Aufgabenform, Umfang) und **zeige mir jeden
      abgeleiteten Wert zur Bestätigung**, bevor du ihn einträgst.
   8. Modellbetrieb: ein fiktiver Betrieb für die Handlungssituationen (Skill `modellbetrieb`) oder vorerst keiner.
   9. Moodle der Schule (nur wenn ich Moodle-Kurse möchte): Moodle-Version, ob das **Kachelformat** (format_tiles)
      installiert ist (Standard: ja, Profilwert `moodle.kachelformat`; ohne Plugin zeigt Moodle die Kurse im
      Themenformat) und ob ich selbst neue Kurse anlegen darf. Erkläre mir kurz, dass jeder Kurs vor der Übergabe in
      ein Test-Moodle eingespielt und nachgezählt wird (`moodlepipeline-referendariat/werkzeug/testmoodle/einspielen.sh`)
      und dass ich ihn in der Schule **immer als neuen Kurs** einspiele
      (`moodlepipeline-referendariat/docs/anleitung_einspielen.md`).
   10. Danach die übrigen Profilwerte gruppenweise (Arbeitsweise, Didaktik, Form, Material, Moodle): pro Gruppe nur
      die Werte, bei denen der neutrale Standard für mich wahrscheinlich nicht passt; alles andere bleibt Standard.
5. **Profil schreiben:** `Profil/lehrkraft-profil.json` im Format `{"werte": {...}}` nur mit Werten, die vom Standard
   abweichen; prüfen mit `python3 unterrichtspipeline-referendariat/profil/profil.py <arbeitsbereich>` (erzeugt auch
   `Lehrkraft-Profil.docx`). Fehler beheben, bis die Prüfung sauber ist.
6. **Sichern:** im Arbeitsbereich committen und pushen. Im Werkzeug nichts ändern.
7. **Abschluss:** Fasse in wenigen Sätzen zusammen, was eingerichtet ist und was noch fehlt, und frage mich dann wie
   der Skill `einstieg`: „Was steht an?“

---

## Später: jede neue Sitzung

Nach der Einrichtung reicht ein Satz, zum Beispiel „Was steht an? Ich muss LS 2 in LF 4 planen.“ Der Skill `einstieg`
lädt das Profil, prüft die vorhandenen Akten und schlägt die nächsten Schritte vor. Für Material: „Material für DS 3
bauen“, für Moodle: „Moodle-Kurs zu LS 2“.
