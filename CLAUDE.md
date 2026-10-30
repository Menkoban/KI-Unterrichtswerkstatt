# KI-Unterrichtswerkstatt

Drei Werkzeuge in einem Repository; jedes hat eigene Regeln in seiner `CLAUDE.md`:

- `unterrichtspipeline-referendariat/`: Pipeline 1, Unterrichtsplanung (Konzept `docs/KONZEPT.md`, Arbeitsweise
  `docs/ARBEITSWEISE.md`, Profil-Vorlage `profil/vorlage.json`).
- `materialpipeline-referendariat/`: Pipeline 2, Material aus dem Materialauftrag.
- `moodlepipeline-referendariat/`: Pipeline 3, Moodle-Themenkurs aus Planung und Material.

## Für alle drei

- **Werkzeug und Arbeitsbereich getrennt:** Ergebnisse, Profil und alles Persönliche gehören in den privaten
  Arbeitsbereich `unterrichtspipeline-referendariat-<name>` (eigenes Repository, im Werkzeug-Ordner von Git ignoriert
  oder als Nachbarordner; Pfad auch über `UPR_ARBEITSBEREICH` oder `.arbeitsbereich`). Nie etwas Persönliches in
  dieses Repository schreiben. Persönliche Vorlieben werden Profilwerte, nicht fester Code.
- **Erste Sitzung ohne Profil:** auf `STARTPROMPT.md` hinweisen und die Einrichtung danach führen.
- Antworten auf Deutsch, in der Sie-Form. Eine Frage zur Zeit, drei gleich ausführliche Vorschläge (empfohlener
  zuerst), dazu freie Antwort. Begründet widersprechen, immer mit Alternative.
- Lernende nur als Kürzel (S01 …), nie mit Namen. Keine Modellbezeichnungen in Dateien, die ins Repository gehen.
- Jede Änderung im Arbeitsbereich committen und pushen; Git ist dort die einzige Sicherung.
