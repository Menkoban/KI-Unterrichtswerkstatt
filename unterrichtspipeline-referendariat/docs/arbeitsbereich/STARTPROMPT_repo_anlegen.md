# Startprompt: persönlichen Arbeitsbereich anlegen (lokale Sitzung)

In Claude Code am eigenen Rechner (mit eigenem GitHub-Login) starten und einfügen:

---

Lege für mich ein neues privates GitHub-Repository an und befülle es mit einem
vorbereiteten Grundgerüst. Arbeite Schritt für Schritt und sag mir am Ende, was du
gemacht hast.

1. Prüfe, ob Git und `gh` installiert sind und ich mit `gh auth status` angemeldet bin.
   Fehlt etwas, erkläre kurz, wie ich es nachhole (Windows, winget), und warte.
2. Lege das Repository an: `gh repo create <mein GitHub-Konto>/unterrichtspipeline-referendariat-<name>
   --private --description "Persönlicher Arbeitsbereich zur Unterrichtspipeline: Akten,
   Profil, Ref-Akte"`. Kein README, keine Lizenz, kein .gitignore automatisch erzeugen.
   Existiert es schon, nichts überschreiben, sondern mich fragen.
3. Hole das Grundgerüst aus `unterrichtspipeline-referendariat/` (Ordner im Repository), Branch
   `claude/repo-review-cloud-workflow-j2fyqg` (falls gemergt: `main`), Ordner
   `docs/arbeitsbereich/repo-geruest/` (temporär mit `--depth 1 --branch <branch>` klonen).
4. Klone das neue, leere Repository nach
   `C:\Users\<mein Benutzer>\Desktop\unterrichtspipeline-referendariat-<name>` (oder frag
   mich, wohin) und kopiere den **Inhalt** von `repo-geruest/` hinein, samt versteckter
   Ordner und Dateien (`.daten/`, alle `.gitkeep`). Nichts weiter ändern.
5. Prüfe: README.md, CLAUDE.md und die Ordner Profil, Ref, Elektrotechnik, Mathematik,
   Unterricht, Quellen, .daten sind da.
6. Committe auf `main` mit „Grundgerüst persönlicher Arbeitsbereich“ und pushe.
7. Lösche den temporären Klon aus Schritt 3.
8. Erinnere mich, unter https://claude.ai/connect-github zu prüfen, ob die
   Claude-GitHub-App Zugriff auf das neue Repository hat (bei „nur ausgewählte
   Repositories“ hinzufügen).

Das Repository muss privat bleiben.
