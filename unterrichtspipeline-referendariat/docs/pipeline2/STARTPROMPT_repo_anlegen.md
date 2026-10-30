# Startprompt: Repository für Pipeline 2 anlegen (lokale Sitzung)

In Claude Code am eigenen Rechner (mit eigenem GitHub-Login) in einem beliebigen
Arbeitsordner starten und den folgenden Text einfügen:

---

Lege für mich ein neues privates GitHub-Repository an und befülle es mit einem
vorbereiteten Grundgerüst. Arbeite Schritt für Schritt und sag mir am Ende, was
du gemacht hast.

1. Prüfe, ob Git und die GitHub-Kommandozeile `gh` installiert sind und ob ich mit
   `gh auth status` angemeldet bin. Fehlt etwas, erkläre mir kurz, wie ich es
   nachhole (Windows, winget), und warte auf mich.
2. Lege das Repository an: `gh repo create materialpipeline-referendariat
   --private --description "Pipeline 2: Unterrichtsmaterial (DOCX, XLSX, PPTX,
   HTML-Simulationen, Videos) aus dem Materialauftrag der Unterrichtspipeline;
   Übergabe an die Moodle-Pipeline"`. Kein README, keine Lizenz, kein .gitignore
   automatisch erzeugen. Existiert es schon, nichts überschreiben, sondern mich fragen.
3. Hole das Grundgerüst aus meinem Repository `unterrichtspipeline-referendariat/` (Ordner im Repository),
   Branch `claude/repo-review-cloud-workflow-j2fyqg` (falls der schon in `main`
   gemergt ist: `main`), Ordner `docs/pipeline2/repo-geruest/`. Am einfachsten:
   das Repo in einen temporären Ordner klonen (`--depth 1 --branch <branch>`).
4. Klone das neue, leere Repository `materialpipeline-referendariat` nach
   `C:\Users\<mein Benutzer>\Desktop\materialpipeline-referendariat` (oder frag
   mich, wohin) und kopiere den **Inhalt** von `repo-geruest/` hinein, samt der
   versteckten Dateien `.gitignore` und aller `.gitkeep`. Nichts weiter ändern.
5. Prüfe, dass diese Dateien da sind: README.md, CLAUDE.md, .gitignore,
   docs/KONZEPT.md und die Ordner auftraege, quellen (fachbuecher,
   normen_vorschriften, hersteller, _karte), bibliothek/Elektrotechnik/LF01,
   material/Elektrotechnik, vorlagen, skills, werkzeuge.
6. Committe auf `main` mit der Nachricht „Grundgerüst Materialpipeline (Pipeline 2)“
   und pushe.
7. Lösche den temporären Klon von Schritt 3.
8. Sag mir zum Schluss, dass ich unter https://claude.ai/connect-github
   prüfen soll, ob die Claude-GitHub-App Zugriff auf das neue Repository hat
   (bei „nur ausgewählte Repositories“ muss ich es dort hinzufügen), damit
   Cloud-Sitzungen am Tablet damit arbeiten können.

Das Repository muss privat bleiben, weil später Auszüge aus gekauften
Fachbüchern hineinkommen.
