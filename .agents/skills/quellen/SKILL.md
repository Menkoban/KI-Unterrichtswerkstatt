---
name: quellen
description: Quellen aufnehmen und nutzen – Fotos, Scans und PDF aus dem Chat ablegen, Texterkennung, Quellenkarte, Volltextsuche; eigene Recherche, wenn nichts mitgegeben ist. Verwende ihn, wenn die Lehrkraft etwas anhängt („hier die Seite aus …“) oder für eine Anlage Belege, Werte oder Abbildungen gebraucht werden.
---
> Werkzeug-Ordner dieses Skills: `materialpipeline-referendariat/`. Alle Pfade und Befehle hier gelten relativ dazu (vorher `cd materialpipeline-referendariat`). Quelle: `materialpipeline-referendariat/.claude/skills/quellen/`.

# Quellen

Werkzeuge: `werkzeug/quellen/aufnehmen.py` (Ablage im Arbeitsbereich `Quellen/<art>/<werk>/`, Texterkennung
Deutsch, Quellenkarte `Quellen/_karte/karte.csv` und `karte.md`), `suche.py`, `LIESMICH.md`. Eigene Quellen sind
persönlich und liegen nie im Werkzeug (Aufteilung 2026-10-19).

## Ablauf

1. **Mitgegeben:** Datei aufnehmen (`--art fachbuch|norm|hersteller|material`, Werk, Auflage, Seite, Thema,
   Rechte). Den Kommentar der Lehrkraft beachten: was genutzt werden soll (ganze Seite, Ausschnitt, Werte).
   Fehlen Seite oder Auflage oder meldet die Karte „kaum Text“ / „Sprachfassung prüfen“: nachfragen.
2. **Nichts mitgegeben:** selbst recherchieren – Europa-Lehrmittel zuerst, dann Normen, Herstellerunterlagen
   (möglichst direkt beim Hersteller, deutsche Fassung), offizielle Darstellungen. Downloads in einen eigenen
   Ordner im Arbeitsverzeichnis, mit `python3 -I` lesen; nur Benötigtes aufnehmen.
3. **Nutzen:** Suche nach Begriffen, Werte und Abbildungen mit Werk und Seite an die Fach-Skills geben.

## Regeln

- Mitgegebenes ist Rohstoff: eigenes Material immer neu im Pipeline-Stil, Original bleibt als Beleg.
- Quelle immer an der Abbildung und im Literaturverzeichnis; Abbildungen dürfen übernommen, nachgebessert oder
  nachgezeichnet werden.
- Quellen bleiben im privaten Arbeitsbereich, nie in einer teilbaren Fassung (E11); „Kopieren verboten“-Leseproben nur als
  Maßreferenz, nicht ablegen. Dateien über 100 MB vorher teilen.
