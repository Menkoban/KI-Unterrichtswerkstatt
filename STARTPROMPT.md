# Startprompt: Einrichtung beim ersten Mal

Ihre KI-App (Codex, Claude Code, Antigravity oder Hermes) in einem **leeren Ordner** auf Ihrem Rechner öffnen, zum
Beispiel `Dokumente\KI-Werkstatt`, und den Text zwischen den Linien einfügen. Mehr ist nicht nötig: Die KI holt die
Werkstatt, installiert alles, richtet das Test-Moodle ein und beginnt dann mit Ihrer Personalisierung. Rechnen Sie mit
etwa einer Stunde; Sie können jederzeit unterbrechen und später „Weiter mit der Einrichtung“ sagen.

---

Ich bin Lehrkraft an einer berufsbildenden Schule und möchte die **KI-Unterrichtswerkstatt**
(https://github.com/Menkoban/KI-Unterrichtswerkstatt) auf diesem Rechner einrichten. Ich kenne mich mit Git und
Programmierung nicht aus: Erledige alles Technische selbst, erkläre es höchstens in einem Satz und frage mich nur, wenn
du meine Zustimmung oder eine Angabe brauchst. Arbeite auf Deutsch, in der Sie-Form. Wenn du mich etwas fragst, dann
**immer nur eine Frage zur Zeit**: kurzer Kontext, drei gleich ausführliche Vorschläge (den empfohlenen zuerst), dazu
die Möglichkeit, frei zu antworten. Warte jeweils meine Antwort ab.

**Teil A: Installation**

1. **System erkennen** (Windows, macOS oder Linux) und alle Befehle passend wählen (unter Windows `python` statt
   `python3`, PowerShell).
2. **Programme prüfen und nachinstallieren:** Git, Python 3.10 oder neuer, LibreOffice. Fehlt etwas, installiere es
   nach meiner Zustimmung selbst (Windows: `winget`, macOS: `brew`, Linux: `apt`) oder nenne mir den einen Link, den
   ich anklicken muss. Unter Windows zusätzlich die Microsoft-Laufzeit „Visual C++ Redistributable (x64)“.
3. **Werkstatt holen:** Ist dieser Ordner noch nicht die Werkstatt, klone
   `https://github.com/Menkoban/KI-Unterrichtswerkstatt.git` in einen Unterordner `KI-Unterrichtswerkstatt` und arbeite
   ab jetzt dort. Lies dann `README.md` und `AGENTS.md` und halte dich an `AGENTS.md`.
4. **Python-Pakete:** `pip install -r materialpipeline-referendariat/werkzeug/vorlagen/anforderungen.txt` (bei einem
   Paket, das sich nicht installieren lässt, weitermachen und es mir am Ende nennen), danach
   `python3 unterrichtspipeline-referendariat/setup_laptop.py`.
5. **Persönlicher Arbeitsbereich:** Hier liegt später alles, was nur mir gehört (Profil, Quellen, Planungen, Material,
   Kurse). Lege den Ordner `unterrichtspipeline-referendariat-<mein Nachname>` **im Werkstatt-Ordner** an (er ist dort
   vom Git der Werkstatt ausgeschlossen) und kopiere den Inhalt von
   `unterrichtspipeline-referendariat/docs/arbeitsbereich/repo-geruest/` hinein, samt versteckter Dateien. Mach daraus
   ein eigenes Git-Repository. Zur Sicherung: Habe ich ein GitHub-Konto und ist `gh` angemeldet, lege ein **privates**
   Repository gleichen Namens an und pushe dorthin; sonst frag mich, ob ich ein Konto anlegen möchte (kostenlos, du
   führst mich durch) oder vorerst nur lokal mit Sicherung in meinem Cloud-Ordner (OneDrive, Nextcloud, iCloud)
   arbeite. Prüfe am Ende, dass der Arbeitsbereich **nicht** im Git der Werkstatt landet. Dann `python3 einrichten.py`.
6. **Test-Moodle (Pflicht):** `python3 moodlepipeline-referendariat/werkzeug/testmoodle/testmoodle.py einrichten`
   (Moodle 5.1.6 mit Kachelformat, etwa 600 MB, einige Minuten). Jeder Moodle-Kurs wird später vor der Abnahme live
   dort eingespielt; ohne Test-Moodle gibt es keine fertigen Kurse. Meldet der Befehl einen Fehler, erkläre mir die
   Abhilfe und wiederhole ihn, bis „Test-Moodle bereit“ erscheint.
7. **Kurzer Bericht:** was installiert ist, was fehlt (mit Abhilfe), wo mein Arbeitsbereich liegt. Dann weiter mit Teil B.

**Teil B: Personalisierung (Einrichtungs-Interview)**

Lies zuerst `unterrichtspipeline-referendariat/docs/ARBEITSWEISE.md` und die Profil-Vorlage
`unterrichtspipeline-referendariat/profil/vorlage.json` (alle Einstellungen mit neutralem Standard). Dann frage mich,
eine Frage zur Zeit, in dieser Reihenfolge:

1. Name und gewünschte Anrede in Dokumenten; Rolle (Referendariat, Lehrkraft, Quereinstieg).
2. Schule: Name, Ort, Logo (ich lade es hoch, du legst es unter `Profil/` ab).
3. Seminar: Passt ein Profil aus `unterrichtspipeline-referendariat/seminare/`? Sonst lade ich meine Seminarunterlagen
   (Leitfaden, Entwurfsmuster, Besuchsformen) hoch, und du legst daraus ein neues Seminarprofil an. Ohne Seminar: `keins`.
4. Fächer, Berufe oder Bildungsgänge, Klassen im laufenden Schuljahr (Klassen nur mit Kürzel, Lernende nie mit
   Namen). Gilt das Fachpaket Elektrotechnik (`fach.elektrotechnik`)? Wenn ja: LuaLaTeX nachinstallieren (Windows:
   MiKTeX, macOS: MacTeX, Linux: `python3 einrichten.py --programme`).
5. Rahmenlehrpläne bzw. Lehrpläne meiner Fächer: aus amtlicher Quelle laden oder ich lade sie hoch; Ablage unter
   `Quellen/`.
6. Didaktische Quellen: Ich lade hoch, worauf meine Planung fachlich und didaktisch fußen soll, zum Beispiel Leitfäden
   und Handreichungen des Seminars, Unterlagen aus Fachseminar und Pädagogik, Fachdidaktik, Texte zu
   Kompetenzorientierung, Handlungsorientierung, Lernfeldkonzept und Medienbildung, Landesvorgaben (etwa schulisches
   Curriculum), Fach- und Tabellenbücher meiner Lernenden. Lege sie unter `Quellen/Didaktik/`, `Quellen/Seminar/` und
   `Quellen/Fach/` ab, je mit kurzer Quellenkarte (Titel, Autor, Jahr, wofür nutzbar). Frag, wofür ich jede Quelle
   verwendet sehen will, und nenne mir, welche Quellen für Besuchsentwürfe üblicherweise noch fehlen.
7. Eigene Unterlagen: Ich lade vorhandene Arbeitsblätter, Entwürfe oder Vorlagen der Schule hoch. Leite daraus
   Gestaltung und Vorlieben ab (Kopfzeile, Schrift, Merkkasten, Aufgabenform, Umfang) und **zeige mir jeden
   abgeleiteten Wert zur Bestätigung**, bevor du ihn einträgst.
8. Modellbetrieb: ein fiktiver Betrieb für die Handlungssituationen (Skill `modellbetrieb`) oder vorerst keiner.
9. Moodle der Schule (nur wenn ich Moodle-Kurse möchte): Version, ob das **Kachelformat** installiert ist (Standard:
   ja) und ob ich selbst neue Kurse anlegen darf. Erkläre kurz, dass jeder Kurs vor der Übergabe im Test-Moodle live
   eingespielt wird und dass ich ihn in der Schule **immer als neuen Kurs** einspiele
   (`moodlepipeline-referendariat/docs/anleitung_einspielen.md`).
10. Danach die übrigen Profilwerte gruppenweise (Arbeitsweise, Didaktik, Form, Material, Moodle): pro Gruppe nur die
    Werte, bei denen der neutrale Standard für mich wahrscheinlich nicht passt; alles andere bleibt Standard.

**Abschluss**

- Profil schreiben: `Profil/lehrkraft-profil.json` im Format `{"werte": {...}}`, nur Werte, die vom Standard
  abweichen; prüfen mit `python3 unterrichtspipeline-referendariat/profil/profil.py <arbeitsbereich>` (erzeugt auch
  `Lehrkraft-Profil.docx`), bis die Prüfung sauber ist.
- Im Arbeitsbereich committen und sichern. In der Werkstatt selbst nichts ändern.
- In wenigen Sätzen zusammenfassen, was eingerichtet ist und was noch fehlt, dann fragen: „Was steht an?“

---

## Später: jede neue Sitzung

Die KI-App im Ordner `KI-Unterrichtswerkstatt` öffnen und einfach sagen, was ansteht, zum Beispiel „Was steht an? Ich
muss LS 2 in LF 4 planen.“, „Nächste Woche ist mein Unterrichtsbesuch.“, „Material für DS 3 bauen.“ oder
„Moodle-Kurs zu LS 2.“ Neue Fassungen der Werkstatt holt „Bitte aktualisiere die Werkstatt“ (`git pull`); Ihr
Arbeitsbereich bleibt dabei unberührt.
