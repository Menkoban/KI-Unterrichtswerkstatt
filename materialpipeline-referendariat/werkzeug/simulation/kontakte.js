// Kontakte im Stromlaufplan in ihrer wirklichen Stellung zeichnen (Korrektur der Lehrkraft 2026-10-15: ein
// betätigter Öffner muss sichtbar öffnen, ein betätigter Schließer schließen). Der Plan bleibt unverändert; für einen
// betätigten Kontakt wird das Messer der Ruhelage weiß überdeckt und das Messer in Arbeitsstellung darübergezeichnet.
// Maße wie planzeichen.sty (mm, y nach oben, Ursprung = oberer Anschluss): Schließer-Messer (0,-6)→(-2,5,-1,5),
// Öffner-Messer (0,-6)→(1,5,-1,5) mit Haken (0,-2)→(2,-2), Positionsschalter-Kennzeichen am Messer (07-08-02).
"use strict";

const Kontakte = (() => {
  const NS = "http://www.w3.org/2000/svg", MM = 72 / 25.4, PZ = 0.25 * MM;
  const RUHE = { S: [-2.5, -1.5], "Ö": [1.5, -1.5] };
  const ARBEIT = { S: [0, -2], "Ö": [-1.2, -1.6] };            // geschlossen an den Festkontakt bzw. weggeklappt
  const MARKE = [[0.45, -4.65], [0.45, -2.9], [1.033, -2.9]];  // Positionsschalter-Kennzeichen (Ruhelage)

  function linie(g, punkte, farbe, breite) {
    const e = document.createElementNS(NS, "polyline");
    e.setAttribute("points", punkte.map(p => p.map(v => v.toFixed(2)).join(",")).join(" "));
    e.setAttribute("fill", "none"); e.setAttribute("stroke", farbe); e.setAttribute("stroke-width", breite);
    e.setAttribute("stroke-linecap", "round"); e.setAttribute("stroke-linejoin", "round");
    g.appendChild(e);
    return e;
  }
  function drehen([x, y], w) { return [x * Math.cos(w) - (y + 6) * Math.sin(w), x * Math.sin(w) + (y + 6) * Math.cos(w) - 6]; }

  // Für jeden Kontakt eine Gruppe mit Maske und Arbeitsstellung; Rückgabe: Funktion, die den Zustand übernimmt
  function anlegen(svg, eltern, netz, lage) {
    const gruppen = netz.kanten.map(k => {
      if (k.typ !== "kontakt" || !(k.art in RUHE)) return null;
      const [x0, y0] = lage[k.a];
      const P = ([dx, dy]) => [x0 + dx * MM, y0 - dy * MM];
      const g = document.createElementNS(NS, "g");
      g.style.display = "none";
      const ruhe = [[0, -6], RUHE[k.art]], arbeit = [[0, -6], ARBEIT[k.art]];
      linie(g, ruhe.map(P), "#fff", PZ + 1.4);                             // Ruhelage überdecken
      const marke = k.bet === "position";
      if (marke) linie(g, MARKE.map(P), "#fff", PZ + 1.4);
      // Zeitkontakt (07-05-01/03): Doppelstrich der Verzögerung reicht bis an das Messer auf halber Höhe (y = -4)
      const verz = k.bet === "anzug", xr = k.art === "S" ? -1.111 : 0.667;
      const xa = ARBEIT[k.art][0] * 2 / (ARBEIT[k.art][1] + 6);           // Messer in Arbeitsstellung bei y = -4
      if (verz && xa < xr) for (const y of [-3.85, -4.15]) linie(g, [[xa, y], [xr, y]].map(P), "#fff", PZ + 0.8);
      if (k.art === "Ö") linie(g, [[0, -2], [2, -2]].map(P), "#000", PZ);  // Haken wieder herstellen
      if (verz) for (const y of [-3.85, -4.15]) linie(g, [[Math.min(xa, xr), y], [xa, y]].map(P), "#000", PZ);
      linie(g, [[0, -6], [0, -6.6]].map(P), "#000", PZ);                   // Drehpunkt
      linie(g, arbeit.map(P), "#000", PZ);
      if (marke) {                                                          // Kennzeichen dreht mit dem Messer
        const w = Math.atan2(ARBEIT["Ö"][0], ARBEIT["Ö"][1] + 6) - Math.atan2(RUHE["Ö"][0], RUHE["Ö"][1] + 6);
        linie(g, MARKE.map(p => P(drehen(p, -w))), "#000", PZ);
      }
      eltern.appendChild(g);
      return g;
    });
    return (betaetigt) => netz.kanten.forEach((k, i) => {
      if (gruppen[i]) gruppen[i].style.display = betaetigt(k) ? "" : "none";
    });
  }

  return { anlegen };
})();
