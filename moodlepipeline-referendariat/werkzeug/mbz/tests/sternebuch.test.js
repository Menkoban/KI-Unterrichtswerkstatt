// Rechenlogik des Sternebuchs (sternebuch.js) mit node prüfen: node --test werkzeug/mbz/tests/sternebuch.test.js
'use strict';
const test = require('node:test');
const assert = require('node:assert');
const path = require('node:path');
const L = require(path.join(__dirname, '..', 'sternebuch.js'));

const PREISE = {
    fuerMich: [{name: 'Hilfe-Joker', sterne: 5}, {name: 'Kaffee', sterne: 10}, {name: 'Abgabe-Joker', sterne: 20}],
    klasse: [{name: 'Frühstück', ab: 60, anteil: 30}, {name: 'Grillen', ab: 120, anteil: 60}],
    kurse: [], lernende: null, fehler: []
};

test('Halbierung: 10 ab, 5 an, 5 verfallen; ungerade abgerundet', () => {
    assert.strictEqual(L.halbieren(10), 5);
    assert.strictEqual(L.halbieren(2), 1);
    assert.strictEqual(L.halbieren(7), 3);
    assert.strictEqual(L.halbieren(-4), 0);
});

test('Zahlen aus der Moodle-Oberfläche', () => {
    assert.strictEqual(L.zahl('12,00'), 12);
    assert.strictEqual(L.zahl('12.50'), 12.5);
    assert.strictEqual(L.zahl('1.234,5'), 1234.5);
    assert.strictEqual(L.zahl('-'), null);
    assert.strictEqual(L.zahl(' 26,00 (100 %)'), 26);
});

test('Empfänger mit Nutzer-Id', () => {
    assert.strictEqual(L.empfaengerId('S01 Muster (#42)'), 42);
    assert.strictEqual(L.empfaengerId('ohne Id'), null);
    assert.strictEqual(L.empfaengerText({id: 7, name: 'S07'}), 'S07 (#7)');
    assert.strictEqual(L.artVon('Verschenken'), 'verschenken');
    assert.strictEqual(L.artVon('Helfer-Stern'), 'helfer');
    assert.strictEqual(L.artVon('etwas anderes'), null);
});

test('Kontostand: verdient + erhalten - verschenkt - eingetauscht - Anteile; nur Freigegebenes zählt', () => {
    const b = [
        {art: 'verschenken', sterne: 10, von: 1, empfaenger: 2, freigegeben: true},
        {art: 'eintauschen', belohnung: 'Kaffee', sterne: 10, von: 1, freigegeben: true},
        {art: 'anteil', belohnung: 'Frühstück', sterne: 30, von: 1, freigegeben: true},
        {art: 'eintauschen', belohnung: 'Hilfe-Joker', sterne: 5, von: 1, freigegeben: false},
        {art: 'helfer', sterne: 1, von: 99, empfaenger: 2, freigegeben: true},
        {art: 'helfer', sterne: 3, von: 2, empfaenger: 2, freigegeben: false},   // von Lernenden angelegt: zählt nicht
        {art: 'verschenken', sterne: 4, von: 2, empfaenger: 1, freigegeben: false}
    ];
    const k = L.konten(b, {1: 60, 2: 3});
    assert.deepStrictEqual([k[1].verdient, k[1].abgegeben, k[1].eingetauscht, k[1].reserviert, k[1].stand],
        [60, 10, 10, 30, 10]);
    assert.strictEqual(k[1].vorgemerkt, 5);
    assert.strictEqual(k[1].verfuegbar, 5);
    assert.strictEqual(k[2].erhalten, 6);           // 5 geschenkt (halbiert) + 1 Helfer-Stern
    assert.strictEqual(k[2].stand, 9);
    assert.strictEqual(k[2].verfuegbar, 5);         // 4 verschenkt, noch offen
    assert.strictEqual(L.kontoVon(k, 3).stand, 0);  // ohne Buchungen
});

test('Ungültige Sternzahlen zählen nicht', () => {
    const k = L.konten([{art: 'eintauschen', sterne: -5, von: 1, freigegeben: true},
                        {art: 'eintauschen', sterne: 2.5, von: 1, freigegeben: true}], {1: 10});
    assert.strictEqual(k[1].stand, 10);
});

test('Klassenbelohnung gilt erst, wenn alle Lernenden ihren Anteil haben', () => {
    const b = [1, 2, 3].map((id) => ({art: 'anteil', belohnung: 'Frühstück', sterne: 30, von: id,
                                     freigegeben: id !== 3}));
    let s = L.klassenstand(b, 'Frühstück', 30, [1, 2, 3]);
    assert.deepStrictEqual([s.erreicht, s.inRunde, s.fehlt, s.sterneInRunde, s.sterneNoetig], [0, 2, 1, 60, 90]);
    b[2].freigegeben = true;
    s = L.klassenstand(b, 'Frühstück', 30, [1, 2, 3]);
    assert.deepStrictEqual([s.erreicht, s.inRunde, s.fehlt], [1, 0, 3]);
    // zweite Runde: 1 bucht erneut
    b.push({art: 'anteil', belohnung: 'Frühstück', sterne: 30, von: 1, freigegeben: true});
    s = L.klassenstand(b, 'Frühstück', 30, [1, 2, 3]);
    assert.deepStrictEqual([s.erreicht, s.inRunde], [1, 1]);
    // feste Zahl der Lernenden (Preisliste „Lernende in der Klasse: 4“)
    assert.strictEqual(L.klassenstand(b, 'Frühstück', 30, [1, 2, 3], 4).erreicht, 0);
    // Anteile von Personen außerhalb der Klasse zählen nicht
    assert.strictEqual(L.klassenstand(b.concat([{art: 'anteil', belohnung: 'Frühstück', sterne: 30, von: 9,
        freigegeben: true}]), 'Frühstück', 30, [1, 2, 3]).zaehler[9], undefined);
});

test('Buchungen über den Kontostand werden abgewiesen', () => {
    const k = {buchungen: [], lernende: [1, 2, 3]};
    assert.deepStrictEqual(L.pruefeBuchung({art: 'eintauschen', belohnung: 'Kaffee', sterne: 10, von: 1}, 10,
        PREISE, k), []);
    assert.ok(L.pruefeBuchung({art: 'eintauschen', belohnung: 'Kaffee', sterne: 10, von: 1}, 9, PREISE, k).length);
    assert.ok(L.pruefeBuchung({art: 'eintauschen', belohnung: 'Kaffee', sterne: 3, von: 1}, 50, PREISE, k)
        .some((g) => g.includes('kostet laut Preisliste 10')));
    assert.ok(L.pruefeBuchung({art: 'eintauschen', belohnung: 'Pizza', sterne: 3, von: 1}, 50, PREISE, k).length);
});

test('Verschenken: gerade Zahl, nicht an sich selbst, nur an die Klasse', () => {
    const k = {buchungen: [], lernende: [1, 2, 3]};
    assert.deepStrictEqual(L.pruefeBuchung({art: 'verschenken', sterne: 10, von: 1, empfaenger: 2}, 10, PREISE, k), []);
    assert.ok(L.pruefeBuchung({art: 'verschenken', sterne: 7, von: 1, empfaenger: 2}, 10, PREISE, k).length);
    assert.ok(L.pruefeBuchung({art: 'verschenken', sterne: 10, von: 1, empfaenger: 1}, 10, PREISE, k).length);
    assert.ok(L.pruefeBuchung({art: 'verschenken', sterne: 10, von: 1, empfaenger: 8}, 10, PREISE, k).length);
    assert.ok(L.pruefeBuchung({art: 'verschenken', sterne: 10, von: 1, empfaenger: null}, 10, PREISE, k).length);
    assert.ok(L.pruefeBuchung({art: 'verschenken', sterne: 12, von: 1, empfaenger: 2}, 10, PREISE, k).length);
});

test('Anteil: Mindestzahl je Person und nur ein Anteil je Runde', () => {
    const k = {buchungen: [], lernende: [1, 2]};
    assert.deepStrictEqual(L.pruefeBuchung({art: 'anteil', belohnung: 'Frühstück', sterne: 30, von: 1}, 60,
        PREISE, k), []);
    assert.ok(L.pruefeBuchung({art: 'anteil', belohnung: 'Frühstück', sterne: 30, von: 1}, 59, PREISE, k)
        .some((g) => g.includes('mindestens 60')));
    k.buchungen = [{id: '1', art: 'anteil', belohnung: 'Frühstück', sterne: 30, von: 1, freigegeben: false}];
    assert.ok(L.pruefeBuchung({art: 'anteil', belohnung: 'Frühstück', sterne: 30, von: 1}, 90, PREISE, k)
        .some((g) => g.includes('schon gebucht')));
    // dieselbe Buchung beim Bearbeiten zählt nicht gegen sich selbst
    assert.deepStrictEqual(L.pruefeBuchung({id: '1', art: 'anteil', belohnung: 'Frühstück', sterne: 30, von: 1}, 90,
        PREISE, k), []);
});

test('Helfer-Stern nur von der Lehrkraft', () => {
    assert.ok(L.pruefeBuchung({art: 'helfer', sterne: 1, von: 1, empfaenger: 1}, 0, PREISE, {}).length);
    assert.deepStrictEqual(L.pruefeBuchung({art: 'helfer', sterne: 1, von: 9, empfaenger: 1}, 0, PREISE,
        {lehrkraft: true}), []);
});

test('Preisliste aus Tabellen lesen', () => {
    const p = L.preiseLesen([
        [['Belohnung', 'Sterne', 'Hinweis'], ['Kaffee', '10', 'solange Vorrat da ist'], ['Abgabe-Joker', '20', '']],
        [['Belohnung', 'Jede Person hat mindestens', 'Anteil je Person', 'Hinweis'], ['Frühstück', '60', '30', '']],
        [['Lernsituation', 'Kurzname'], ['LS 1', 'EG1-LF01-LS01']],
        [['Belohnung', 'Sterne'], ['Kaputt', 'viele']]
    ], 'Lernende in der Klasse: 18');
    assert.deepStrictEqual(p.fuerMich.map((x) => [x.name, x.sterne]), [['Kaffee', 10], ['Abgabe-Joker', 20]]);
    assert.deepStrictEqual(p.klasse.map((x) => [x.name, x.ab, x.anteil]), [['Frühstück', 60, 30]]);
    assert.deepStrictEqual(p.kurse, [{name: 'LS 1', kurzname: 'EG1-LF01-LS01'}]);
    assert.strictEqual(p.lernende, 18);
    assert.strictEqual(p.fehler.length, 1);
});

test('Verdiente Sterne abgerundet wie der Sternzähler, Anzeige deutsch', () => {
    assert.strictEqual(L.ganzeSterne(15.5), 15);
    assert.strictEqual(L.ganzeSterne(14.999999999), 15);
    assert.strictEqual(L.ganzeSterne(null), null);
    assert.strictEqual(L.zahlText(1234), '1.234');
    const k = L.konten([], {7: 15.5});
    assert.strictEqual(k[7].verdient, 15);
    assert.strictEqual(k[7].stand, 15);
});

test('Rolle aus dem Rollentext: Lehrkraft nie Lernende', () => {
    assert.strictEqual(L.lernendNachText('Student'), true);
    assert.strictEqual(L.lernendNachText('Teilnehmer/in'), true);
    assert.strictEqual(L.lernendNachText('Teacher'), false);
    assert.strictEqual(L.lernendNachText('Trainer/in'), false);
    assert.strictEqual(L.lernendNachText('Student, Non-editing teacher'), false);
    assert.strictEqual(L.lernendNachText(''), null);
});
