# Anleitung: von null bis zur ersten geplanten Stunde

Für Kolleginnen und Kollegen, die die KI-Unterrichtswerkstatt nutzen möchten. Technische Vorkenntnisse sind kaum nötig;
die KI erklärt jeden Schritt und wartet auf Sie.

## 1. GitHub-Konto anlegen (einmalig, etwa fünf Minuten)

GitHub ist die Ablage und Sicherung Ihrer Planungen, mit Versionsgeschichte: Nichts geht verloren, jeder ältere Stand
lässt sich zurückholen. Sie müssen dafür nichts über Git wissen; das erledigt die KI.

1. Auf [github.com/signup](https://github.com/signup) ein kostenloses Konto anlegen (E-Mail, Passwort, Benutzername)
   und die E-Mail bestätigen. Den kostenlosen Tarif behalten.
2. Empfehlenswert: unter **Settings → Password and authentication** die Zwei-Faktor-Anmeldung einschalten.

## 2. Zwei Repositories in Ihrem Konto (zwei Klicks)

1. **Werkzeug übernehmen:** [github.com/Menkoban/KI-Unterrichtswerkstatt](https://github.com/Menkoban/KI-Unterrichtswerkstatt)
   öffnen und oben rechts **Fork**, dann **Create fork** tippen. Damit liegt eine eigene Kopie des Werkzeugs in Ihrem
   Konto. Sie ist öffentlich wie das Original und enthält nichts Persönliches.
2. **Privaten Arbeitsbereich anlegen:** [diesen Link öffnen](https://github.com/new?name=unterrichtspipeline-referendariat-IHRNAME&visibility=private&description=Pers%C3%B6nlicher+Arbeitsbereich+zur+KI-Unterrichtswerkstatt), im Feld *Repository name* `IHRNAME` durch
   Ihren Nachnamen ersetzen (zum Beispiel `unterrichtspipeline-referendariat-mueller`), prüfen, dass **Private**
   gewählt ist, und **Create repository** tippen. Sonst nichts ankreuzen. Hier landet alles, was nur Ihnen gehört:
   Profil, Quellen, Planungen, Material, Kurse.

## 3. KI-App verbinden

Erprobt ist die Werkstatt mit **Claude Code**; die Schritte unten gelten dafür. **OpenAI Codex**, **Google
Antigravity** und **Hermes Agent** lesen dieselben Anweisungen (`AGENTS.md`) und Skills (`.agents/skills/`): Dort
verbinden Sie GitHub ebenso, öffnen beide Repositories und fügen denselben Startprompt ein. Hermes Agent sucht Skills
sonst in `~/.hermes/skills/`; dann die Ordner aus `.agents/skills/` dorthin kopieren oder verlinken.

1. Ein Abo mit Claude Code (Pro oder höher) auf [claude.ai](https://claude.ai). Unter
   [claude.ai/code](https://claude.ai/code) läuft Claude Code im Browser oder in der App, auch auf dem Tablet.
2. [claude.ai/connect-github](https://claude.ai/connect-github) öffnen, GitHub verbinden und der Claude-App Zugriff auf
   **beide** Repositories geben (bei „Only select repositories“ beide auswählen).
3. Unter [claude.ai/code](https://claude.ai/code) eine neue Sitzung starten und **beide** Repositories auswählen:
   Ihre Kopie der KI-Unterrichtswerkstatt und Ihren Arbeitsbereich. Der Sitzungsstart richtet die Programme ein und
   findet den Arbeitsbereich von selbst.

**Am eigenen Rechner** geht es auch: die KI-App installieren, dann im Terminal

```bash
git clone https://github.com/<ihr-konto>/KI-Unterrichtswerkstatt.git
cd KI-Unterrichtswerkstatt
git clone https://github.com/<ihr-konto>/unterrichtspipeline-referendariat-<ihr name>.git
claude        # oder codex, hermes; in Antigravity den Ordner öffnen
```

Der Arbeitsbereich liegt dann im Werkzeug-Ordner, wird von dessen Git ignoriert und sichert sich in sein eigenes
privates Repository. Python 3, Git und LibreOffice müssen installiert sein (die KI hilft beim Nachholen).

## 4. Einrichtung mit dem Startprompt

Den Text aus [`STARTPROMPT.md`](STARTPROMPT.md) einfügen. Die KI

- prüft die Technik und richtet das **lokale Test-Moodle** ein (Moodle 5.1.6 mit Kachelformat; jeder Kurs wird dort
  vor der Abnahme live eingespielt, damit er sicher auch im Moodle der Schule hochgeht),
- legt das Gerüst des Arbeitsbereichs an,
- fragt Sie **eine Frage nach der anderen**: Schule und Logo, Seminar, Fächer und Klassen, Lehrpläne, didaktische Quellen, eigene
  Unterlagen, Modellbetrieb, Vorlieben,
- leitet aus hochgeladenen Arbeitsblättern und Entwürfen Ihre Gestaltung ab und lässt jeden Wert bestätigen,
- schreibt daraus Ihr Lehrkraft-Profil und sichert es.

Rechnen Sie für die Einrichtung mit etwa einer Stunde. Sie können jederzeit unterbrechen; der Stand liegt im
Arbeitsbereich.

## 5. Arbeiten

Sagen Sie einfach, was ansteht:

| Sie sagen | Es passiert |
|---|---|
| „Ich muss LF 3 planen.“ | Pipeline 1: curriculare Analyse, Lernsituationen, dann Doppelstunde für Doppelstunde |
| „Nächste Woche ist mein Unterrichtsbesuch.“ | Skill `besuchsstunde`: Entwurf nach Ihrem Seminarprofil |
| „Material für DS 2 bauen.“ | Pipeline 2: Materialplan, Bau, Prüfbericht |
| „Moodle-Kurs zu LS 2.“ | Pipeline 3: Kursplan, Bau, Kurssicherung (.mbz) |
| „Das war heute …“ | Skill `nachbereitung`: legt Ihre Rückschau dort ab, wo sie die nächste Planung beeinflusst |

Jedes Ergebnis kommt als Word-Datei mit Prüfbericht. Gefällt Ihnen etwas nicht, sagen Sie es: Die Korrektur wird eine
Regel in Ihrem Profil, damit sie nicht zweimal nötig ist.

## 6. Aktuell halten und weitergeben

- Neue Fassung des Werkzeugs: auf GitHub in Ihrer Kopie der KI-Unterrichtswerkstatt **Sync fork**, dann **Update
  branch** tippen (oder die KI darum bitten). Ihr Arbeitsbereich bleibt unberührt.
- Weitergeben: den Link zu dieser Anleitung teilen. Jede Person legt ihr eigenes Konto, ihre Kopie und ihren privaten
  Arbeitsbereich an.
- Nie in dieses Repository: Namen von Lernenden, Noten, Klassendaten, Ihr Profil.

## Häufige Fragen

**Kann ich das ohne Seminar oder nach dem Referendariat nutzen?** Ja. Seminarprofil `keins`; Besuchsentwürfe
entfallen, alles andere bleibt.

**Mein Fach hat kein Arbeitsblatt (z. B. Sport).** Planung und Moodle passen; beim Material sagen Sie, was Sie
stattdessen brauchen (Stationskarten, Beobachtungsbogen, Bewertungsraster). Rückmeldungen dazu helfen, das Werkzeug
zu verbessern.

**Wer sieht meine Daten?** Nur Sie: Ihr Arbeitsbereich ist privat. Was Sie in die Sitzung hochladen, verarbeitet
die KI-App nach den Bedingungen Ihres Abos; laden Sie keine Namen von Lernenden hoch.
