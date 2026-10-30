// Kiste auf dem Pendelförderband: Bewegung mit dem Gurt, Endschalter aus der Lage der Kiste (werkzeug/simulation).
// Lage in cm im Technologieschema (pendelband.py → LAGE). Genutzt von der Seite und von der Gegenprobe in Node.
"use strict";

const Pendel = (() => {
  function neu(lage) {
    return { x: lage.kiste.start + 0.12, anschlag: false };       // x: linke Vorderkante der Kiste
  }

  // v: Gurtgeschwindigkeit in m/s (Vorzeichen = Richtung); Rückgabe: betätigte Endschalter mit Auslenkung (cm)
  function schritt(p, lage, v, dt) {
    const k = lage.kiste, b = lage.band;
    p.x += v * lage.massstab * dt;
    const links = b.x0 + 0.05, rechts = b.x1 - 0.05 - k.b;           // Anschlag am Bandende
    p.anschlag = p.x < links || p.x > rechts;
    p.x = Math.max(links, Math.min(rechts, p.x));
    const betaetigt = {};
    for (const [bmk, e] of Object.entries(lage.endschalter)) {
      const weg = e.seite > 0 ? p.x + k.b - e.kontakt : e.kontakt - p.x;
      if (weg >= 0) betaetigt[bmk] = weg;
    }
    return betaetigt;
  }

  return { neu, schritt };
})();

if (typeof module !== "undefined") module.exports = Pendel;
