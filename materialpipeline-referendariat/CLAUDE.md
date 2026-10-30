# Materialpipeline Referendariat (Pipeline 2)

Zweite von drei Pipelines. Planung und alle didaktischen Entscheidungen kommen aus
`unterrichtspipeline-referendariat/` (Ordner im Repository) (dort `docs/KONZEPT.md`); dieses Repo
setzt den Materialauftrag einer Stunde in fertiges Material um.

## Arbeitsweise mit der Lehrkraft

- Eine Entscheidung nach der anderen: kurzer Kontext, drei gleich ausführliche Vorschläge (empfohlener
  zuerst), dazu freie Antwort. Kein Auswahl-Dialogwerkzeug.
- **Strikt eine Frage zur Zeit** (Lehrkraft 2026-10-13): erst die Antwort abwarten, dann die
  nächste Frage. Nicht zwischen Fragen springen, keine zweite Frage anhängen. Was aus dem
  Hintergrund kommt (Helfer, andere Sitzungen), wird erst nach der Antwort angesprochen.
- **Aus Korrekturen lernen:** Jede Korrektur der Lehrkraft sofort als Regel festhalten
  (Prüf-Checkliste, Stilregel oder Few-Shot-Beispiel), damit sie nicht zweimal nötig ist.
- **Begründet widersprechen, immer mit Alternative** (Lehrkraft 2026-10-22, gilt für alle drei Pipelines): Passt eine Entscheidung nicht oder hält die KI etwas anderes begründet für besser, sagt sie das von sich aus, argumentiert (Didaktik, Fach, Technik, bisher Entschiedenes) und nennt immer einen Alternativvorschlag; nie stillschweigend umsetzen.
- Vor jeder Freigabe ein Prüfbericht mit Fehler / Warnung / Hinweis.
- Jede Entscheidung sofort in `docs/KONZEPT.md`, dann commit und push.
- Die Lehrkraft arbeitet am Tablet: Ausgaben als DOCX (bzw. XLSX, PPTX, HTML je
  Material); zum Ansehen und zur Freigabe zusätzlich als PDF, wenn das Profil `form.ansicht_als_pdf` es verlangt
  (Lehrkraft 2026-10-27), sonst PDF nur auf ausdrücklichen Wunsch.
- Rangfolge: Ansage der Lehrkraft > Seminarvorgaben > Material > Vorgabe der Pipeline.

## Regeln für Material

- **Werkzeug und Arbeitsbereich** (Lehrkraft 2026-10-19, wie Pipeline 1): Dieses Repo ist nur das Werkzeug.
  Material, Bauskripte, Fotos, Bibliothek, eigene Quellen und das Profil liegen im gemeinsamen persönlichen
  Arbeitsbereich `unterrichtspipeline-referendariat-<name>`; persönliche Regeln stehen im Profil
  (Gruppen „Material“ und „Form“). Zuerst `python3 werkzeug/arbeitsbereich.py`; Ergebnisse nie ins Werkzeug schreiben.
  Bauskripte holen Vorlagen über `material_bausteine.persoenliche_vorlage(...)` (Gestaltung aus dem Profil);
  die Vorlagen im Werkzeug bleiben neutral. Persönliche Vorlieben nie fest ins Werkzeug schreiben, sondern
  als Profilwert (Vorlage `profil/vorlage.json` in Pipeline 1, neutraler Standard).

- Zuschnitt: Auftrag je Stunde, Ablage je Lernsituation, Bibliothek je Lernfeld;
  vor jeder Anlage zuerst die Bibliothek prüfen (wiederverwenden, anpassen, neu).
- Handlungsorientiert, im Modellbetrieb (Brinkmann Automation, fiktiv); Lernende
  sind Facharbeiter/innen, Ansprache in der Sie-Form.
- **Problemorientierter Einstieg** (Philosophie der Lehrkraft, 2026-10-13): Material nimmt nichts vorweg.
  Erst das Problem, dann denken die Lernenden selbst nach, was zu tun ist, informieren sich selbst und
  erstellen selbst einen Plan. Keine Arbeitsanweisung, die Methode oder Lösungsweg vorgibt.
- Vorerst **ein Niveau** (Lehrkraft 2026-10-13): keine Stufen Beginner/Könner/Experte, bis
  ein Niveau läuft; Differenzierung wird danach geklärt. Gestufte Hilfekarten (Tipp, Ansatz,
  Lösungsweg) bleiben, außer das Profil schaltet sie ab (`material.schriftliche_hilfen`, Lehrkraft 2026-10-24:
  aus; Hilfe persönlich, Impulse im Erwartungshorizont). Aus Altaufträgen mit drei Fassungen nur die mittlere bauen.
- Jede Lösung wird gerechnet, nicht geschätzt; Erwartungshorizont je Anlage.
- **Quellen:** Abbildungen und Schemata aus Fachbüchern dürfen übernommen,
  nachgebessert oder nachgezeichnet werden (Entscheidung der Lehrkraft); die Quelle
  steht **immer** im Material, an der Abbildung und im Literaturverzeichnis.
- KI-Fußnote auf jedem KI-gestützten Material (Seminarvorgabe; Seminarprofil nach Profilwert `seminar`).
- **Schule, Logo, Modellbetrieb, Fachpaket** (Veröffentlichung 2026-11): Schulname, Logo und Modellbetrieb kommen aus dem
  Profil (`schule.*`, `modellbetrieb.name`; neutral BBS Musterstadt, Platzhalter-Logo, Musterbetrieb). Die Elektro-Skills
  (Stromlauf-, Installationsplan, Technologieschema, Simulation) gehören zum Fachpaket Elektrotechnik und gelten nur bei
  `fach.elektrotechnik`.
- Technische Grafiken als Vektor, normgerecht (DIN EN 60617); keine KI-Bilder für
  Schaltpläne.
- Keine echten Namen von Lernenden im Repo, nur Kürzel. Keine Modellbezeichnungen in
  Dateien, die ins Repo gehen.
- Dateien größer als 100 MB passen nicht in GitHub; große Scans vorher teilen.
- **Erst testen, dann pushen** (2026-10-23): nach jeder Änderung am Werkzeug `python3 werkzeug/vorlagen/alle_bauen.py` und die betroffenen Bauskripte im Arbeitsbereich laufen lassen; erst ohne Fehler committen.
