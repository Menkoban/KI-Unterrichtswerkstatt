// Rechenlogik von „Mein Stufenweg“ (stufenweg.js): node --test werkzeug/mbz/tests/stufenweg.test.js
'use strict';
const test = require('node:test');
const assert = require('node:assert');
const path = require('node:path');
const L = require(path.join(__dirname, '..', 'stufenweg.js'));

const K = {start: 'Standard', grenzen: [50, 85], stufen: ['Grundlagen', 'Standard', 'Vertiefung'],
    kacheln: [1, 2, 3].map(n => ({nr: n, titel: 'K' + n, aufgaben: ['g', 's', 'v'].map(s =>
        [1, 2].map(i => ({name: `A${n}${s}${i}`, thema: `T${n}${s}${i}`})))}))};

test('Standard → Vertiefung → Vertiefung', () => {
    const w = L.weg(K, {a1s1: 100, a1s2: 80, a2v1: 60, a2v2: 60});
    assert.deepStrictEqual(w.map(x => [x.einstieg, x.ende, x.zustand]), [[1, 2, 'fertig'], [2, 2, 'fertig'],
        [2, 2, 'offen']]);
    assert.strictEqual(w[0].richtung, 'auf');
    assert.strictEqual(L.aktuelle(w), 2);
    assert.strictEqual(L.leitsatz(w, K).art, 'bleibt');
});

test('Abstieg, laufende Kachel bleibt', () => {
    const w = L.weg(K, {a1s1: 0, a1s2: 40, a2g1: 100});
    assert.strictEqual(w[0].richtung, 'ab');
    assert.strictEqual(w[1].zustand, 'laufend');
    assert.strictEqual(w[1].ende, 0);
    const fb = L.rueckmeldung(w[0], K, 2);
    assert.match(fb.saetze[0], /trainieren Sie gezielt auf Grundlagen/);
    assert.deepStrictEqual(fb.ueben, ['T1s1', 'T1s2']);
});

test('Zahlen aus der Oberfläche', () => {
    assert.strictEqual(L.zahl('66,67 %'), 66.67);
    assert.strictEqual(L.zahl('-'), null);
});
