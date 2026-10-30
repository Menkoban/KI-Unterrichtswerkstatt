// Rechenkern der Schaltungssimulation (werkzeug/simulation). Rechnet auf dem Netz, das stromlauf.py aus dem
// gezeichneten Plan erzeugt: keine zweite, von Hand geschriebene Schaltlogik. Der Ablauf der Schütze folgt
// plan.schaltfolge (je Durchlauf zieht nur ein Schütz an oder fällt ab), damit Python-Prüfung und Simulation
// dasselbe Ergebnis liefern (Gegenprobe in sterndreieck_sim.py).
"use strict";

const Kern = (() => {
  function neu(netz, verz) {
    const spulen = netz.kanten.filter(k => k.typ === "spule").map(k => k.bmk);
    const an = {}, seit = {};
    spulen.forEach(s => { an[s] = false; seit[s] = null; });
    return { netz, verz, spulen, an, seit, t: 0, betaetigt: new Set(), ausgeloest: new Set() };
  }

  // Ist ein Kontakt betätigt? Schützkontakte folgen ihrer Spule, Zeitkontakte zusätzlich der Verzögerung;
  // Taster und Bimetall-Kontakte (Kennzeichen ohne Spule) folgen den Eingaben.
  function betaetigt(z, k) {
    if (k.bmk in z.an) {
      if (k.bet === "anzug") return z.an[k.bmk] && z.seit[k.bmk] !== null && z.t - z.seit[k.bmk] >= z.verz[k.bmk] - 1e-9;
      return z.an[k.bmk];
    }
    return z.betaetigt.has(k.bmk);
  }

  function leitet(z, k) {
    if (k.typ === "ltg") return true;
    if (k.typ === "fest") return !z.ausgeloest.has(k.bmk);
    if (k.typ === "kontakt") return betaetigt(z, k) === (k.art === "S");   // Schließer betätigt, Öffner in Ruhe
    return false;                                                            // Spulen und Wicklungen sind Lasten
  }

  // Zusammenhängende Knoten über alle leitenden Kanten (Union-Find); Rückgabe: Knoten → Vertreter
  function gruppen(z) {
    const p = z.netz.knoten.map((_, i) => i);
    const f = i => { while (p[i] !== i) { p[i] = p[p[i]]; i = p[i]; } return i; };
    for (const k of z.netz.kanten) if (leitet(z, k)) { const a = f(k.a), b = f(k.b); if (a !== b) p[a] = b; }
    return z.netz.knoten.map((_, i) => f(i));
  }

  // Sollzustand aller Spulen: Spannung zwischen L1 und N an beiden Anschlüssen
  function soll(z) {
    const g = gruppen(z), q = z.netz.quellen, s = {};
    for (const k of z.netz.kanten) if (k.typ === "spule") {
      s[k.bmk] = (g[k.a] === g[q.L1] && g[k.b] === g[q.N]) || (g[k.b] === g[q.L1] && g[k.a] === g[q.N]);
    }
    return s;
  }

  // Ein Zeitpunkt wie plan.schaltfolge: bis zum stabilen Zustand, je Durchlauf nur die erste Änderung
  function stabil(z) {
    for (let n = 0; n < 20; n++) {
      const neu_ = soll(z);
      if (z.spulen.every(s => neu_[s] === z.an[s])) break;
      for (const s of z.spulen) {
        if (neu_[s] && !z.an[s]) z.seit[s] = z.t;
        if (!neu_[s]) z.seit[s] = null;
      }
      const s = z.spulen.find(s => neu_[s] !== z.an[s]);
      z.an[s] = neu_[s];
    }
  }

  // Hauptstromkreis: Kurzschluss zwischen Leitern, Spannung je Wicklung, Betriebsart
  function haupt(z) {
    const g = gruppen(z), q = z.netz.quellen;
    const leiter = ["L1", "L2", "L3", "N", "PE"];
    const von = {};
    let kurz = null;
    for (const l of leiter) {
      const r = g[q[l]];
      if (von[r] && !kurz) kurz = von[r] + "–" + l;
      von[r] = von[r] || l;
    }
    const phase = i => ["L1", "L2", "L3"].find(l => g[q[l]] === g[i]) || null;
    const m3 = z.netz.kanten.find(k => k.typ === "motor3");
    if (m3) {                                      // Motor mit drei Anschlüssen: Drehrichtung aus der Phasenfolge
      const p = [m3.a, m3.b, m3.c].map(i => ["L1", "L2", "L3"].indexOf(phase(i)));
      const modus = p.every(i => i < 0) ? "Aus" : new Set(p).size === 3 && p.every(i => i >= 0)
        ? ((p[1] - p[0] + 3) % 3 === 1 ? "Rechtslauf" : "Linkslauf") : "gestört";
      return { kurz, spannung: [], modus, gruppen: g };
    }
    const wickl = z.netz.kanten.filter(k => k.typ === "wicklung");
    const enden = wickl.map(k => [phase(k.a), phase(k.b)]);
    const spannung = wickl.map((k, i) => {
      const [pa, pb] = enden[i];
      if (pa && pb && pa !== pb) return 400;
      const frei = pa ? k.b : pb ? k.a : null;      // Ende ohne Leiter: Sternpunkt, wenn alle Wicklungen dort enden
      if (frei === null) return 0;
      const andere = wickl.filter((_, j) => j !== i && enden[j].filter(Boolean).length === 1 &&
        [wickl[j].a, wickl[j].b].some(e => g[e] === g[frei]));
      return andere.length === wickl.length - 1 ? 230 : 0;
    });
    const modus = spannung.every(u => u === 400) ? "Dreieck" : spannung.every(u => u === 230) ? "Stern"
      : spannung.every(u => u === 0) ? "Aus" : "gestört";
    return { kurz, spannung, modus, gruppen: g };
  }

  // Ein Rechenschritt: Eingaben anwenden, Steuerung stabil, Kurzschluss löst die Sicherung aus
  function schritt(z) {
    stabil(z);
    const h = haupt(z);
    if (h.kurz) {
      const k = z.netz.kanten.find(k => k.typ === "fest" && /F1$/.test(k.bmk));
      if (k) z.ausgeloest.add(k.bmk);
      return Object.assign(haupt(z), { kurzschluss: h.kurz });
    }
    return h;
  }

  // Motor und Last (vereinfachtes Modell aus Katalog-Kennlinien, Werte relativ zu den Bemessungsdaten)
  function kennlinie(punkte, x) {
    if (x <= punkte[0][0]) return punkte[0][1];
    for (let i = 1; i < punkte.length; i++) {
      const [x0, y0] = punkte[i - 1], [x1, y1] = punkte[i];
      if (x <= x1) return y0 + (y1 - y0) * (x - x0) / (x1 - x0);
    }
    return punkte[punkte.length - 1][1];
  }

  function motor(m, zustand, modus, last, dt) {
    // zustand: {n (1/min, Vorzeichen = Drehrichtung), theta (Erwärmung F2, relativ)};
    // Rückgabe: {I Netzstrom, IF2 Strom durch -F2, M Motormoment (Betrag)}
    const richtung = modus === "Linkslauf" ? -1 : 1;
    const fak = ["Dreieck", "Rechtslauf", "Linkslauf"].includes(modus) ? 1 : modus === "Stern" ? 1 / 3 : 0;
    const x = richtung * zustand.n / m.ns;                            // < 0: Gegenstrom beim Umsteuern
    const M = richtung * fak * kennlinie(m.M, x) * m.MN;
    const I = fak * kennlinie(m.I, x) * m.IN;
    const LM = last * m.MN;
    let ML;                                                             // Lastmoment gegen die Bewegung, Haftreibung
    if (Math.abs(zustand.n) > 0.5) ML = Math.sign(zustand.n) * LM;
    else ML = Math.abs(M) > LM ? Math.sign(M) * LM : M;
    const n = (zustand.n * Math.PI / 30 + (M - ML) / m.J * dt) * 30 / Math.PI;
    // ohne Antrieb bremst die Last nur bis zum Stillstand, nicht darüber hinaus
    zustand.n = fak === 0 && Math.sign(n) !== Math.sign(zustand.n) ? 0 : Math.max(-m.ns, Math.min(m.ns, n));
    const IF2 = modus === "Dreieck" ? I / Math.sqrt(3) : I;           // -F2 im Strang (Stern-Dreieck) bzw. Zuleitung
    const v = IF2 / m.Ie;
    zustand.theta += (v * v - zustand.theta) / m.tau * dt;           // Bimetall, Auslöseklasse 10
    return { I, IF2, M: Math.abs(M) };
  }

  return { neu, betaetigt, leitet, gruppen, stabil, haupt, schritt, motor, kennlinie };
})();

if (typeof module !== "undefined") module.exports = Kern;
