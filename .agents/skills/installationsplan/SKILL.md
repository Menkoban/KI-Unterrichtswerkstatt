---
name: installationsplan
description: Installationspläne (Grundriss unter/auf Putz), Übersichtsschaltpläne, Verteiler-Übersichtsschaltpläne und Leitungsbemessung aus einer gemeinsamen Verschaltung – Aderzahl berechnet, Spannungsfall und Ib ≤ In ≤ Iz geprüft, Plansatz gemeinsam geprüft. Verwende ihn nur, wenn der Materialauftrag einen dieser Pläne verlangt.
---
> Werkzeug-Ordner dieses Skills: `materialpipeline-referendariat/`. Alle Pfade und Befehle hier gelten relativ dazu (vorher `cd materialpipeline-referendariat`). Quelle: `materialpipeline-referendariat/.claude/skills/installationsplan/`.

# Installations-, Übersichts- und Verteilerplan

**Fachpaket Elektrotechnik** (Veröffentlichung 2026-11): Dieser Skill gilt nur, wenn das Profil `fach.elektrotechnik` setzt (`arbeitsbereich.fachpaket("elektrotechnik")`); sonst nicht aufrufen.

Werkzeuge: `werkzeug/installationsplan/` (`grundriss.py`, `netz.py` = Verschaltung mit berechneter Aderzahl),
`werkzeug/uebersichtsschaltplan/` (`uebersicht.py`, `verteiler.py`, `LIESMICH.md`).
**Stilreferenz (freigegeben):** Plansatz Wohnung – `installationsplan/beispiele/wohnung.py` und `wohnung_netz.py`
(einzige Quelle der Verschaltung), `uebersichtsschaltplan/beispiele/wohnung*.py` (EI-02, EI-03, Bemessung,
`wohnung_plansatz_pruefen.py`); Ausgaben `docs/stilreferenz/installationsplan_*`, `uebersichtsschaltplan_*`,
`verteilerplan_*`.

## Ablauf

1. Verschaltung als Netz (Stromkreise, Abzweigdosen, Verbraucher); daraus Aderzahlen.
2. Bemessung mit dem Rechenprüfer (Spannungsfall ≤ 3 % ab Zähler, Ib ≤ In ≤ Iz nach DIN VDE 0298-4).
3. Pläne aus derselben Verschaltung erzeugen; gemeinsame Plansatzprüfung (0 Fehler).
4. Vorschau als PNG, vergrößert prüfen.

## Regeln

`docs/regeln/installationsplan_checkliste.md` und `uebersichtsschaltplan_checkliste.md`: nie schräge Linien;
immer Abzweigdosen, je Stromkreis eine Zuleitung; Aderzahl an jeder Leitung; Verbindungspunkte; Kreuzschalter-Haken
waagerecht nach außen; Lage der Leitung nach Verlegeart mit Putzzeichen; höchstens vier Anschlüsse je Dose;
Europa-Lehrmittel als Maßstab; nichts verdecken.
