# Rechenprüfer und Diagramme (Baustein 2 und 6)

**Rechenprüfer** (`rechnen.py`): Jede Lösung wird mit Einheiten (Pint) nachgerechnet, bevor sie in den
Erwartungshorizont oder die Hilfekarten kommt.

- `gegeben()` und `schritt()` führen Größen mit Einheit.
  - Passt die Einheit einer Formel nicht, gibt es einen **Fehler**.
  - Ebenso, wenn der Wert im Materialauftrag (`erwartet=`) abweicht.
- `fehlerweg()` rechnet die typischen Fehler der Lernenden nach, deren Werte im Erwartungshorizont stehen.
- `gegenprobe()` vergleicht mit einem zweiten Weg, z. B. `lcapy_widerstand()` für Netzwerke.
- `zeilen()` liefert den Rechenweg mit eingesetzten Werten. `werte()` liefert die formatierten Ergebnisse
  (Komma, Einheit) zum Einsetzen in die Vorlagen.
- `abgleich()` durchsucht die fertigen DOCX/PPTX nach Zahlen mit Einheit:
  - Ein Wert, der nahe an einem gerechneten liegt, aber zu keinem passt, ist eine **Warnung**. So sieht man,
    ob der Fall in allen Anlagen gleich beschrieben ist.
  - Temperaturdifferenzen in °C außerhalb wörtlicher Rede („…“) ergeben eine **Warnung** (Stilregel).
- `bericht()` gibt den Prüfbericht mit Fehler / Warnung / Hinweis aus.

**Diagramme** (`diagramm.py`) im Stil der Stilreferenz `docs/stilreferenz/kennlinie_pt100.tex`:

- LuaLaTeX mit pgfplots und Liberation Sans, Achsenzahlen serifenlos mit Komma.
- Achsbeschriftung „Größe Zeichen in Einheit“.
- Die Kurven werden aus derselben Python-Rechnung abgetastet; Diagramm und Lösung passen so immer zusammen.
- Ausgabe: `.tex`, `.pdf` und `.png` mit 300 dpi für Word.
- `leer=True` erzeugt nur das beschriftete Raster für das Arbeitsblatt.

Beispiel: `python3 beispiele/ds7_leitungswiderstand.py`. Das Beispiel endet mit Exit-Code 1, wenn der
Prüfbericht einen Fehler enthält. Die Ausgaben liegen in `docs/stilreferenz/rechnen/`.

Voraussetzungen:

- `pip install pint`
- `pip install --no-deps lcapy` (dazu sympy, numpy, scipy, matplotlib, networkx, property_cached)
- LuaLaTeX mit pgfplots, fontspec, unicode-math, Liberation Sans
- poppler (pdftoppm)
