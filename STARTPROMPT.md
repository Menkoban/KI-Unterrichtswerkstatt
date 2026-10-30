# Startprompt: Einrichtung beim ersten Mal

Claude Code in der Wurzel dieses Repositorys starten (lokal oder unter claude.ai/code mit diesem Repository und Ihrem
leeren, privaten Arbeitsbereich), dann den Text zwischen den Linien einfügen. Mehr ist nicht nötig; alles Weitere
fragt die KI.

---

Ich bin Lehrkraft an einer berufsbildenden Schule und möchte die KI-Unterrichtswerkstatt in diesem Repository für mich
einrichten. Bitte arbeite auf Deutsch, in der Sie-Form, und stelle mir **immer nur eine Frage zur Zeit**: kurzer
Kontext, drei gleich ausführliche Vorschläge (den empfohlenen zuerst), dazu die Möglichkeit, frei zu antworten.
Warte jeweils meine Antwort ab.

1. **Lesen:** zuerst `README.md` und `CLAUDE.md` in der Wurzel, dann
   `unterrichtspipeline-referendariat/docs/ARBEITSWEISE.md` und die Profil-Vorlage
   `unterrichtspipeline-referendariat/profil/vorlage.json` (alle Einstellungen mit neutralem Standard).
2. **Technik prüfen:** Python 3, Git, `python-docx`, LibreOffice (`soffice`); fehlt etwas, sag mir kurz, wie ich es
   nachhole, und warte. Dann `python3 unterrichtspipeline-referendariat/setup_laptop.py`.
3. **Arbeitsbereich:** Finde mein privates Repository `unterrichtspipeline-referendariat-<name>` (im Werkzeug-Ordner
   oder daneben). Fehlt es, erkläre mir, wie ich es auf GitHub **privat** anlege, und warte. Ist es leer, kopiere
   den Inhalt von `unterrichtspipeline-referendariat/docs/arbeitsbereich/repo-geruest/` hinein (mit versteckten
   Dateien). Prüfe, dass der Arbeitsbereich **nicht** im Git dieses Werkzeugs landet.
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
   6. Eigene Unterlagen: Ich lade vorhandene Arbeitsblätter, Entwürfe oder Vorlagen der Schule hoch. Leite daraus
      Gestaltung und Vorlieben ab (Kopfzeile, Schrift, Merkkasten, Aufgabenform, Umfang) und **zeige mir jeden
      abgeleiteten Wert zur Bestätigung**, bevor du ihn einträgst.
   7. Modellbetrieb: ein fiktiver Betrieb für die Handlungssituationen (Skill `modellbetrieb`) oder vorerst keiner.
   8. Danach die übrigen Profilwerte gruppenweise (Arbeitsweise, Didaktik, Form, Material, Moodle): pro Gruppe nur
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
