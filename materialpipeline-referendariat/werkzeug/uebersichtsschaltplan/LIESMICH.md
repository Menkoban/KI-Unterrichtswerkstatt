# Übersichtsschaltpläne (Installation und Verteiler)

Plansatz Wohnung (Probe): EI-01 Installationsplan (werkzeug/installationsplan), EI-02 Übersichtsschaltplan Installation,
EI-03 Verteiler-Übersichtsschaltplan. Eine Quelle für alle: Verschaltung in
`werkzeug/installationsplan/beispiele/wohnung_netz.py` (Aderzahl je Leitung gerechnet, `netz.py`).

| Datei | Zweck |
|---|---|
| `uebersicht.py` | Generator EI-02 im Europa-Stil (32690-3): Dosenreihe, Leuchten oben, Schalter/Steckdosen unten, Aderzahl, Verbindungspunkte, Einspeisung mit Stromkreis, Leitung, Putzzeichen; Prüfung (schräg, > 4 Anschlüsse, Kreuzung, Knoten) |
| `verteiler.py` | Generator EI-03 nach Fachkunde S. 280 / 37566-7: Sammelschiene, RCD-Gruppen, LS-Abgänge |
| `beispiele/wohnung.py` | EI-02 der Wohnung |
| `beispiele/wohnung_bemessung.py` | Rechenprüfer: Länge aus EI-01, I_b ≤ I_n ≤ I_z, Spannungsfall ≤ 3 % |
| `beispiele/wohnung_verteiler.py` | EI-03 mit Bemessungstabelle (baut nur bei fehlerfreier Bemessung) |
| `beispiele/wohnung_plansatz_pruefen.py` | Gemeinsame Prüfung EI-01 (UP/AP), EI-02, EI-03; Exit-Code 1 bei Fehler |

Reihenfolge: `python3 werkzeug/installationsplan/beispiele/wohnung.py --lehrbuch` (und `--aufputz`),
`python3 werkzeug/uebersichtsschaltplan/beispiele/wohnung.py`, `…/wohnung_verteiler.py`, `…/wohnung_plansatz_pruefen.py`.
Regeln: docs/regeln/installationsplan_checkliste.md, docs/regeln/uebersichtsschaltplan_checkliste.md.
