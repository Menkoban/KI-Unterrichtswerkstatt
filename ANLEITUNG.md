# Anleitung: von null bis zur ersten geplanten Stunde

Für Kolleginnen und Kollegen, die die KI-Unterrichtswerkstatt nutzen möchten. Technische Vorkenntnisse sind kaum nötig;
die KI erklärt jeden Schritt und wartet auf Sie.

## 1. Konten

1. **GitHub:** auf [github.com](https://github.com) ein kostenloses Konto anlegen. GitHub ist die Ablage und
   Sicherung Ihrer Planungen.
2. **Claude:** ein Abo mit Claude Code (Pro oder höher) auf [claude.ai](https://claude.ai). Unter
   [claude.ai/code](https://claude.ai/code) läuft Claude Code im Browser oder in der App, auch auf dem Tablet.
3. Claude Zugriff auf GitHub geben: in claude.ai unter den Einstellungen GitHub verbinden und Ihr künftiges
   Arbeitsbereich-Repository freigeben.

## 2. Privaten Arbeitsbereich anlegen

Auf GitHub: **New repository**, Name `unterrichtspipeline-referendariat-<ihr name>` (zum Beispiel
`unterrichtspipeline-referendariat-mueller`), Sichtbarkeit **Private**, ohne README, ohne Lizenz. Hier landet alles,
was nur Ihnen gehört: Profil, Planungen, Material, Kurse. Das Repository bleibt privat.

## 3. Werkzeug und Arbeitsbereich zusammenbringen

**Variante A: in der Cloud (claude.ai/code, empfohlen am Tablet)**

1. Neue Sitzung starten und **beide** Repositories auswählen: `Menkoban/ki-unterrichtswerkstatt` (oder Ihre Kopie davon) und
   Ihren Arbeitsbereich.
2. Der Sitzungsstart richtet die Programme ein und findet den Arbeitsbereich von selbst.

**Variante B: auf dem eigenen Rechner**

```bash
git clone https://github.com/Menkoban/ki-unterrichtswerkstatt.git
cd ki-unterrichtswerkstatt
git clone https://github.com/<ihr-konto>/unterrichtspipeline-referendariat-<ihr name>.git
claude
```

Der Arbeitsbereich liegt im Werkzeug-Ordner, wird von dessen Git ignoriert und sichert sich in sein eigenes
Repository. Unter Windows geht dasselbe in der Eingabeaufforderung; Python 3, Git und LibreOffice müssen installiert
sein (die KI hilft beim Nachholen).

## 4. Einrichtung mit dem Startprompt

Den Text aus [`STARTPROMPT.md`](STARTPROMPT.md) einfügen. Die KI

- prüft die Technik,
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

- Neue Fassung des Werkzeugs: `git pull` im Werkzeug-Ordner (in der Cloud geschieht das beim Sitzungsstart). Ihr
  Arbeitsbereich bleibt unberührt.
- Weitergeben: den Link zu diesem Repository teilen. Jede Person legt ihren eigenen privaten Arbeitsbereich an.
- Nie in dieses Repository: Namen von Lernenden, Noten, Klassendaten, Ihr Profil.

## Häufige Fragen

**Kann ich das ohne Seminar oder nach dem Referendariat nutzen?** Ja. Seminarprofil `keins`; Besuchsentwürfe
entfallen, alles andere bleibt.

**Mein Fach hat kein Arbeitsblatt (z. B. Sport).** Planung und Moodle passen; beim Material sagen Sie, was Sie
stattdessen brauchen (Stationskarten, Beobachtungsbogen, Bewertungsraster). Rückmeldungen dazu helfen, das Werkzeug
zu verbessern.

**Wer sieht meine Daten?** Nur Sie: Ihr Arbeitsbereich ist privat. Was Sie in die Sitzung hochladen, verarbeitet
Claude nach den Bedingungen Ihres Abos; laden Sie keine Namen von Lernenden hoch.
