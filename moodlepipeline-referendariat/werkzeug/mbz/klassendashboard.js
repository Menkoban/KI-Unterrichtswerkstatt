/*
 * Klassen-Dashboard (Lehrkraft 2026-10-31, dashboard.py). Läuft als JavaScript-Vorlage der verborgenen Datenbank-
 * Aktivität „Klassen-Dashboard“ im Lehrkraftbereich, nur in der Listenansicht und mit der Sitzung der Lehrkraft:
 *   - Teilnehmende des Kurses (Rolle Lernende) mit Nutzer-Id aus der Teilnehmerseite,
 *   - Selbsteinschätzungen je Meilenstein aus der Feedback-Aktivität (CSV-Download, Spalten „(K1) …“),
 *   - gespeicherte Bewertungen der Lehrkraft aus den Einträgen dieser Datenbank (Felder lernende, meilenstein, stufen),
 *   - mit KONFIG.stufenweg: je Lernendem die Bewertungsübersicht und daraus der Stufenweg (Regel wie stufenweg.js).
 * Ansichten: je Meilenstein eine Tabelle (Selbsteinschätzung, Ihre Bewertung, Abweichung; rot ab KONFIG.gespraech_ab;
 * Note nach IHK), „Stufenweg der Klasse“, „Eine Person“ (Auswahlmenü, Verlaufskurve, Meilensteine). Jede angetippte
 * Stufe wird sofort als Eintrag dieser Datenbank gespeichert. Keine externen Schriften oder Dienste.
 */
(function () {
    'use strict';
    var KONFIG = /*KONFIG*/{"gespraech_ab": 2, "meilensteine": []}/*/KONFIG*/;
    var IHK = [[92, 1], [81, 2], [67, 3], [50, 4], [30, 5], [0, 6]];
    var SVGNS = 'http://www.w3.org/2000/svg';

    // ---------------------------------------------------------------- Stufenweg (gleiche Regel wie stufenweg.js)
    function zahl(t) {
        var m = String(t === null || t === undefined ? '' : t).replace(/ /g, ' ').match(/-?\d[\d.,]*/);
        if (!m) { return null; }
        var s = m[0];
        if (s.indexOf(',') >= 0) { s = s.replace(/\./g, '').replace(',', '.'); }
        var n = parseFloat(s);
        return isNaN(n) ? null : n;
    }
    function klein(t) { return String(t || '').replace(/\s+/g, ' ').trim().toLowerCase(); }
    function endstufe(e, p, g) { if (p === null || p === undefined) { return e; } if (p >= g[1]) { return Math.min(e + 1, 2); } if (p < g[0]) { return Math.max(e - 1, 0); } return e; }
    function weg(k, noten) {
        var e = Math.max(0, k.stufen.indexOf(k.start));
        return k.kacheln.map(function (ka) {
            var erg = (ka.aufgaben[e] || []).map(function (a) { var key = klein(a.name); return Object.prototype.hasOwnProperty.call(noten, key) ? noten[key] : null; });
            var fertig = erg.length > 0 && erg.every(function (p) { return p !== null; });
            var mittel = fertig ? erg.reduce(function (s, p) { return s + p; }, 0) / erg.length : null;
            var ende = endstufe(e, mittel, k.grenzen), x = {titel: ka.titel, nr: ka.nr, einstieg: e, ende: ende, mittel: mittel,
                zustand: fertig ? 'fertig' : (erg.some(function (p) { return p !== null; }) ? 'laufend' : 'offen')};
            e = ende;
            return x;
        });
    }

    // Umgebung: (a) als Vorlage der Datenbank in Moodle selbst, (b) eingebettet im Lernstand-Dashboard (Datei-Aktivität
    // im Lehrkraftbereich, Behälter #kd-ziel); dann werden Kurs, sesskey und die Datenbank selbst gesucht.
    function umgebung() {
        var behaelter = document.getElementById('kd-ziel');
        if (!behaelter) {
            if (!/\/mod\/data\/view\.php$/.test(location.pathname) || /[?&]rid=/.test(location.search)) { return Promise.resolve(null); }
            if (!window.M || !M.cfg) { return Promise.resolve(null); }
            var q = new URLSearchParams(location.search), main = document.querySelector('[role="main"]') || document.body;
            var b = document.createElement('div');
            main.insertBefore(b, main.firstChild);
            return Promise.resolve({behaelter: b, wurzel: M.cfg.wwwroot, kurs: M.cfg.courseId, sesskey: M.cfg.sesskey,
                ziel: q.get('d') ? 'd=' + q.get('d') : 'id=' + q.get('id')});
        }
        var P = null;
        try { P = window.parent !== window ? window.parent.M : window.M; } catch (e) { P = null; }
        var i = location.pathname.indexOf('/pluginfile.php');
        var wurzel = P && P.cfg && P.cfg.wwwroot ? P.cfg.wwwroot : location.origin + (i >= 0 ? location.pathname.slice(0, i) : '');
        // Kurs: aus Moodle (eingebettet) oder mit der Suche des Lernstand-Dashboards (liveKursId, Original)
        var kursP = P && P.cfg && P.cfg.courseId > 1 ? Promise.resolve(P.cfg.courseId) :
            (typeof window.liveKursId === 'function' ? Promise.resolve(window.liveKursId(wurzel)) : Promise.resolve(null));
        var sk = P && P.cfg ? Promise.resolve(P.cfg.sesskey) : fetch(wurzel + '/my/', {credentials: 'same-origin'}).then(function (r) { return r.text(); })
            .then(function (t) { return (t.match(/"sesskey":"([^"]+)"/) || [])[1]; });
        var kurs = null;
        return kursP.then(function (k) { kurs = k; return Promise.all([sk, fetch(wurzel + '/mod/data/index.php?id=' + kurs, {credentials: 'same-origin'}).then(function (r) { return r.text(); })]); }).then(function (r) {
            var cmid = null;
            new DOMParser().parseFromString(r[1], 'text/html').querySelectorAll('a[href*="mod/data/view.php?id="]').forEach(function (a) {
                if (a.textContent.replace(/\s+/g, ' ').trim() === KONFIG.daten_name) { cmid = (a.getAttribute('href').match(/id=(\d+)/) || [])[1]; }
            });
            return {behaelter: behaelter, wurzel: wurzel, kurs: kurs, sesskey: r[0], ziel: cmid ? 'id=' + cmid : null};
        });
    }

    function start(U) {
        if (!U || !KONFIG.meilensteine.length) { return; }
        var M = {cfg: {sesskey: U.sesskey}};
        var ziel = U.ziel;
        var WURZEL = U.wurzel, KURS = U.kurs, AB = KONFIG.gespraech_ab || 2, SW = KONFIG.stufenweg || null;
        var MS = KONFIG.meilensteine, tab = MS[0].id, L = [], FELD = {}, DID = null, person = null, wegGeladen = null;

        var wurzel = U.behaelter;
        wurzel.classList.add('kd');
        if (!ziel) { wurzel.textContent = 'Die Datenbank „' + KONFIG.daten_name + '“ fehlt im Kurs; ohne sie kann nichts gespeichert werden.'; return; }

        function el(tag, attrs, kids) {
            var e = document.createElement(tag);
            Object.keys(attrs || {}).forEach(function (k) {
                if (k === 'text') { e.textContent = attrs[k]; }
                else if (k === 'on') { Object.keys(attrs.on).forEach(function (ev) { e.addEventListener(ev, attrs.on[ev]); }); }
                else { e.setAttribute(k, attrs[k]); }
            });
            (kids || []).forEach(function (c) { if (c !== null && c !== undefined) { e.appendChild(typeof c === 'string' ? document.createTextNode(c) : c); } });
            return e;
        }
        function sv(tag, attrs) { var e = document.createElementNS(SVGNS, tag); Object.keys(attrs).forEach(function (k) { if (k === 'text') { e.textContent = attrs[k]; } else { e.setAttribute(k, attrs[k]); } }); return e; }
        function seite(pfad) { return fetch(WURZEL + pfad, {credentials: 'same-origin'}).then(function (r) { return r.text(); }); }
        function dok(t) { return new DOMParser().parseFromString(t, 'text/html'); }
        function csv(t) {
            var z = [], f = [], w = '', s = false;
            for (var i = 0; i < t.length; i++) {
                var c = t[i];
                if (s) { if (c === '"' && t[i + 1] === '"') { w += '"'; i++; } else if (c === '"') { s = false; } else { w += c; } }
                else if (c === '"') { s = true; } else if (c === ',') { f.push(w); w = ''; }
                else if (c === '\n') { f.push(w); z.push(f); f = []; w = ''; } else if (c !== '\r') { w += c; }
            }
            if (w || f.length) { f.push(w); z.push(f); }
            return z;
        }

        var kopf = el('div', {class: 'kd-kopf'}, [el('h2', {text: 'Klassen-Dashboard'}), el('span', {class: 'kd-status', id: 'kdStatus', text: 'lädt …'}),
            el('button', {class: 'kd-knopf', type: 'button', text: 'Als Tabelle herunterladen', on: {click: function () { herunterladen(); }}})]);
        var zahlen = el('div', {class: 'kd-zahlen'}), reiter = el('div', {class: 'kd-reiter', role: 'tablist'}), ansicht = el('div', {class: 'kd-panel'});
        [kopf, zahlen, reiter, ansicht].forEach(function (x) { wurzel.appendChild(x); });
        function status(t) { document.getElementById('kdStatus').textContent = t; }

        // ------------------------------------------------------------ Daten lesen
        function teilnehmende() {
            return seite('/user/index.php?id=' + KURS + '&perpage=5000').then(function (t) {
                var aus = [];
                dok(t).querySelectorAll('table tbody tr').forEach(function (tr) {
                    var a = tr.querySelector('a[href*="user/view.php"]');
                    if (!a) { return; }
                    var k = a.cloneNode(true);
                    k.querySelectorAll('.userinitials, img, .userpicture').forEach(function (x) { x.remove(); });
                    var name = k.textContent.replace(/\s+/g, ' ').trim(), rollen = tr.textContent;
                    var uid = (a.getAttribute('href').match(/[?&]id=(\d+)/) || [])[1];
                    if (name && /Student|Teilnehmer|Schüler|Lernende/i.test(rollen) && !/Teacher|Trainer|Lehrkr|Lehrer/i.test(rollen)) { aus.push({n: name, uid: uid}); }
                });
                return aus;
            });
        }
        function feedbacks() {
            return seite('/mod/feedback/index.php?id=' + KURS).then(function (t) {
                var aus = {};
                dok(t).querySelectorAll('a[href*="mod/feedback/view.php?id="]').forEach(function (a) {
                    aus[a.textContent.replace(/\s+/g, ' ').trim()] = (a.getAttribute('href').match(/id=(\d+)/) || [])[1];
                });
                return aus;
            });
        }
        function selbst(m, cmid) {
            if (!cmid) { return Promise.resolve({}); }
            return seite('/mod/feedback/show_entries.php?id=' + cmid + '&download=csv').then(function (t) {
                var z = csv(t.replace(/^﻿/, '')), k = z.shift() || [];
                var sp = m.kriterien.map(function (_, i) { return k.findIndex(function (h) { return h.indexOf('(K' + (i + 1) + ')') === 0; }); });
                var aus = {};
                z.forEach(function (r) {
                    if (!r[0]) { return; }
                    aus[r[0].trim()] = sp.map(function (j) { var v = parseInt(String(r[j] || '').trim(), 10); return isNaN(v) ? null : v; });
                });
                return aus;
            });
        }
        function formular() {
            return seite('/mod/data/edit.php?' + ziel).then(function (t) {
                var d = dok(t);
                ['lernende', 'meilenstein', 'stufen'].forEach(function (n) {
                    var x = d.querySelector('[data-feld="' + n + '"] input, [data-feld="' + n + '"] textarea');
                    FELD[n] = x ? x.getAttribute('name') : null;
                });
                var di = d.querySelector('input[name="d"]');
                DID = di ? di.value : null;
            });
        }
        function gespeichert() {
            return seite('/mod/data/view.php?' + ziel + '&perpage=1000').then(function (t) {
                var aus = {};
                dok(t).querySelectorAll('.kd-eintrag').forEach(function (x) {
                    var rid = (String(x.getAttribute('data-mehr')).match(/rid=(\d+)/) || [])[1];
                    aus[x.getAttribute('data-l') + '|' + x.getAttribute('data-m')] = {rid: rid, s: String(x.getAttribute('data-s')).split(',').map(function (v) {
                        var n = parseInt(v, 10); return isNaN(n) ? null : n; })};
                });
                return aus;
            });
        }
        function noten(uid, versuch) {
            versuch = versuch || 0;
            return seite('/grade/report/user/index.php?id=' + KURS + '&userid=' + uid).then(function (t) {
                var aus = {}, d = dok(t);
                if (!d.querySelector('.column-itemname')) {
                    // Moodle rechnet die Bewertungen gerade neu: kurz warten und noch einmal lesen (wie stufenweg.js)
                    if (versuch < 6) { return new Promise(function (ok) { setTimeout(ok, 3000); }).then(function () { return noten(uid, versuch + 1); }); }
                    throw new Error('Bewertungen werden neu berechnet');
                }
                d.querySelectorAll('tr').forEach(function (z) {
                    var k = z.querySelector('.column-itemname');
                    if (!k) { return; }
                    var titel = ((k.querySelector('.gradeitemheader, a') || k).textContent || '');
                    var p = zahl((z.querySelector('.column-percentage') || {}).textContent);
                    if (p === null) {
                        var g = zahl((z.querySelector('.column-grade') || {}).textContent);
                        var b = String((z.querySelector('.column-range') || {}).textContent || '').split(/[^\d.,]+/).filter(Boolean);
                        var h = b.length ? zahl(b[b.length - 1]) : null;
                        p = g !== null && h ? g * 100 / h : null;
                    }
                    aus[klein(titel)] = p;
                });
                return aus;
            });
        }
        function stufenwegLaden() {
            if (!SW) { return Promise.resolve(); }
            if (!wegGeladen) {
                status('liest die Stufenwege …');
                wegGeladen = Promise.all(L.map(function (p) { return noten(p.uid).then(function (n) { p.weg = weg(SW, n); }).catch(function () { p.weg = null; }); }))
                    .then(function () { status(L.length + ' Lernende geladen'); });
            }
            return wegGeladen;
        }

        // ------------------------------------------------------------ Speichern
        var warten = {};
        function speichern(p, m) {
            var key = p.n + '|' + m.id;
            clearTimeout(warten[key]);
            status('speichert …');
            warten[key] = setTimeout(function () {
                var f = new FormData();
                f.append('d', DID);
                f.append('sesskey', M.cfg.sesskey);
                if (p[m.id].rid) { f.append('rid', p[m.id].rid); }
                f.append(FELD.lernende, p.n);
                f.append(FELD.meilenstein, m.id);
                f.append(FELD.stufen, p[m.id].l.map(function (v) { return v === null ? '' : v; }).join(','));
                f.append('saveandview', '1');
                fetch(WURZEL + '/mod/data/edit.php', {method: 'POST', body: f, credentials: 'same-origin'}).then(function (r) {
                    var rid = (r.url.match(/rid=(\d+)/) || [])[1];
                    if (rid) { p[m.id].rid = rid; }
                    status(rid ? 'gespeichert' : 'Speichern fehlgeschlagen, bitte Seite neu laden');
                }).catch(function () { status('Speichern fehlgeschlagen, bitte Seite neu laden'); });
            }, 500);
        }

        // ------------------------------------------------------------ Auswertung
        function auswertung(p, m) {
            var d = p[m.id], n = m.kriterien.length, abw = [], g = false, alle = true, pkt = 0;
            for (var i = 0; i < n; i++) {
                var s = d.s ? d.s[i] : null, l = d.l[i];
                if (l === null) { alle = false; } else { pkt += l - 1; }
                var a = (s !== null && l !== null) ? Math.abs(s - l) : null;
                abw.push(a);
                if (a !== null && a >= AB) { g = true; }
            }
            var proz = alle ? Math.round(pkt / (3 * n) * 100) : null, note = null;
            if (proz !== null) { for (var j = 0; j < IHK.length; j++) { if (proz >= IHK[j][0]) { note = IHK[j][1]; break; } } }
            return {abw: abw, gespraech: g, proz: proz, note: note, selbst: !!d.s, bewertet: alle};
        }
        function kennzahlen(m) {
            var s = 0, b = 0, g = 0, su = 0, n = 0;
            L.forEach(function (p) { var a = auswertung(p, m); if (a.selbst) { s++; } if (a.bewertet) { b++; } if (a.gespraech) { g++; } if (a.note) { su += a.note; n++; } });
            zahlen.innerHTML = '';
            [[s + ' / ' + L.length, 'Selbsteinschätzungen da · ' + m.kurz, ''], [b + ' / ' + L.length, 'von Ihnen bewertet', ''],
             [String(g), 'Gespräche nötig', ' kd-alarm'], [n ? (su / n).toFixed(1).replace('.', ',') : '–', 'Notenschnitt', '']].forEach(function (z) {
                zahlen.appendChild(el('div', {class: 'kd-zahl' + z[2]}, [el('div', {class: 'kd-w', text: z[0]}), el('div', {class: 'kd-l', text: z[1]})]));
            });
        }

        // ------------------------------------------------------------ Ansicht: Meilenstein
        function raster(m) {
            var t = el('table', {class: 'kd-tab kd-raster'}, [el('thead', {}, [el('tr', {}, [el('th', {class: 'kd-name', text: 'Kriterium'})].concat([1, 2, 3, 4].map(function (s) { return el('th', {text: 'Stufe ' + s}); })))])]);
            var b = el('tbody');
            m.kriterien.forEach(function (k) { b.appendChild(el('tr', {}, [el('td', {class: 'kd-name', text: k.name})].concat(k.stufen.map(function (x) { return el('td', {class: 'kd-umbruch', text: x}); })))); });
            t.appendChild(b);
            return el('details', {class: 'kd-details'}, [el('summary', {text: 'Raster dieses Meilensteins anzeigen (Stufen 1 bis 4)'}), el('div', {class: 'kd-tw'}, [t])]);
        }
        function tabelle(m) {
            ansicht.innerHTML = '';
            ansicht.appendChild(el('h3', {text: m.titel}));
            ansicht.appendChild(el('div', {class: 'kd-erklaerung'}, [
                el('p', {}, [el('b', {text: 'Selbsteinschätzung (grau): '}), 'die Stufe, die sich die oder der Lernende vor der Abgabe in „' + m.name + '“ selbst gegeben hat. Sie wird von selbst gelesen.']),
                el('p', {}, [el('b', {text: 'Ihre Bewertung (blau): '}), 'Ihre Stufe für dasselbe Kriterium. Beide nutzen dieselbe Skala, die Stufen 1 bis 4 Ihres Rasters. Tippen Sie die Stufe an; sie wird sofort gespeichert und ergibt die Note.']),
                el('p', {}, [el('b', {text: 'Abweichung: '}), 'Unterschied zwischen beiden. Ab ' + AB + ' Stufen wird das Feld rot, und „Gespräch“ erscheint.'])]));
            ansicht.appendChild(raster(m));
            var r1 = el('tr', {}, [el('th', {class: 'kd-name', rowspan: '2', text: 'Lernende'})]), r2 = el('tr');
            m.kriterien.forEach(function (k) { r1.appendChild(el('th', {class: 'kd-kr', colspan: '3', text: k.name})); });
            ['Prozent', 'Note', 'Rückmeldung'].forEach(function (t, i) { r1.appendChild(el('th', {rowspan: '2', class: i === 0 ? 'kd-grenze' : '', text: t})); });
            m.kriterien.forEach(function () { ['Selbst­einschätzung', 'Ihre Bewertung', 'Abw.'].forEach(function (t, i) { r2.appendChild(el('th', {class: (i === 0 ? 'kd-grenze ' : '') + 'kd-klein', text: t})); }); });
            var body = el('tbody');
            L.forEach(function (p) {
                var a = auswertung(p, m), tr = el('tr', {class: a.gespraech ? 'kd-gespraech-zeile' : ''});
                tr.appendChild(el('td', {class: 'kd-name'}, [el('button', {class: 'kd-person', type: 'button', text: p.n, on: {click: function () { person = p; tab = 'person'; zeichnen(); }}})]));
                m.kriterien.forEach(function (k, i) {
                    tr.appendChild(el('td', {class: 'kd-grenze'}, [p[m.id].s ? el('span', {class: 'kd-selbst', title: 'Selbsteinschätzung Stufe ' + p[m.id].s[i] + ': ' + (k.stufen[p[m.id].s[i] - 1] || ''), text: String(p[m.id].s[i])}) : el('span', {class: 'kd-offen', text: 'fehlt'})]));
                    var grp = el('div', {class: 'kd-stufen', role: 'group', 'aria-label': 'Ihre Bewertung ' + p.n + ' · ' + k.name});
                    [1, 2, 3, 4].forEach(function (v) {
                        grp.appendChild(el('button', {class: 'kd-stb', type: 'button', title: 'Stufe ' + v + ': ' + k.stufen[v - 1], 'aria-pressed': String(p[m.id].l[i] === v), text: String(v),
                            on: {click: function () { p[m.id].l[i] = (p[m.id].l[i] === v) ? null : v; zeichnen(); speichern(p, m); }}}));
                    });
                    tr.appendChild(el('td', {}, [grp]));
                    var ab = a.abw[i];
                    tr.appendChild(el('td', {}, [el('span', {class: 'kd-abw' + (ab !== null && ab >= AB ? ' kd-rot' : ''), text: ab === null ? '–' : String(ab)})]));
                });
                tr.appendChild(el('td', {class: 'kd-grenze', text: a.proz === null ? '–' : a.proz + ' %'}));
                tr.appendChild(el('td', {}, [el('span', {class: 'kd-note', text: a.note === null ? '–' : String(a.note)})]));
                tr.appendChild(el('td', {}, [a.gespraech ? el('span', {class: 'kd-pill kd-pill-rot', text: 'Gespräch'}) :
                    (a.bewertet ? el('span', {class: 'kd-pill kd-pill-ok', text: 'schriftlich'}) : el('span', {class: 'kd-pill', text: a.selbst ? 'zu bewerten' : 'wartet'}))]));
                body.appendChild(tr);
            });
            ansicht.appendChild(el('div', {class: 'kd-tw'}, [el('table', {class: 'kd-tab'}, [el('thead', {}, [r1, r2]), body])]));
        }

        // ------------------------------------------------------------ Ansicht: Stufenweg
        function ringe(st, gr) {
            var s = sv('svg', {viewBox: '0 0 26 26', width: gr || 24, height: gr || 24, role: 'img', 'aria-label': SW.stufen[st], class: 'kd-ringe'});
            var f = ['var(--kd-st0)', 'var(--kd-st1)', 'var(--kd-st2)'][st];
            s.appendChild(sv('circle', {cx: 13, cy: 13, r: 3.5, fill: f}));
            for (var i = 0; i <= st; i++) { s.appendChild(sv('circle', {cx: 13, cy: 13, r: 6.5 + i * 3, fill: 'none', stroke: f, 'stroke-width': 1.6})); }
            return s;
        }
        function kurve(p) {
            var W = 440, H = 240, x0 = 84, x1 = W - 20, ys = [180, 118, 56], n = SW.kacheln.length;
            var s = sv('svg', {viewBox: '0 0 ' + W + ' ' + H, class: 'kd-kurve', role: 'img', 'aria-label': 'Stufenweg von ' + p.n});
            [0, 1, 2].forEach(function (st) {
                s.appendChild(sv('line', {x1: x0, x2: x1, y1: ys[st], y2: ys[st], stroke: 'var(--kd-linie)', 'stroke-dasharray': '4 5'}));
                s.appendChild(sv('text', {x: x0 - 10, y: ys[st] + 4, 'text-anchor': 'end', 'font-size': 13, fill: 'var(--kd-leise)', text: SW.stufen[st]}));
            });
            var dx = n > 1 ? (x1 - x0) / (n - 1) : 0, pts = [];
            (p.weg || []).forEach(function (k, i) {
                s.appendChild(sv('text', {x: x0 + i * dx, y: H - 8, 'text-anchor': 'middle', 'font-size': 12, fill: 'var(--kd-leise)', text: 'K' + k.nr}));
                if (k.zustand !== 'offen') { pts.push([x0 + i * dx, ys[k.einstieg], k]); }
            });
            if (pts.length > 1) {
                // geschwungene Kurve durch alle Punkte (Catmull-Rom als Bézier)
                var d = 'M' + pts[0][0] + ',' + pts[0][1];
                for (var i = 0; i < pts.length - 1; i++) {
                    var p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(pts.length - 1, i + 2)];
                    // Kontrollpunkte auf die Höhe des Abschnitts begrenzt: die Kurve schießt nie über eine Stufe hinaus
                    var lo = Math.min(p1[1], p2[1]), hi = Math.max(p1[1], p2[1]);
                    var c1y = Math.min(hi, Math.max(lo, p1[1] + (p2[1] - p0[1]) / 6)), c2y = Math.min(hi, Math.max(lo, p2[1] - (p3[1] - p1[1]) / 6));
                    d += ' C' + (p1[0] + (p2[0] - p0[0]) / 6) + ',' + c1y + ' ' + (p2[0] - (p3[0] - p1[0]) / 6) + ',' + c2y + ' ' + p2[0] + ',' + p2[1];
                }
                var boden = ys[0] + 18;
                s.appendChild(sv('path', {d: d + ' L' + pts[pts.length - 1][0] + ',' + boden + ' L' + pts[0][0] + ',' + boden + ' Z', fill: 'var(--kd-blau-hell)', opacity: '0.6'}));
                s.appendChild(sv('path', {d: d, fill: 'none', stroke: 'var(--kd-blau)', 'stroke-width': 3.5, 'stroke-linecap': 'round'}));
            }
            pts.forEach(function (q, i) {
                var letzt = i === pts.length - 1;
                s.appendChild(sv('circle', {cx: q[0], cy: q[1], r: letzt ? 9 : 6, fill: letzt ? 'var(--kd-gruen)' : '#fff', stroke: 'var(--kd-blau)', 'stroke-width': 2.5}));
                if (q[2].mittel !== null) { s.appendChild(sv('text', {x: q[0], y: q[1] - 14, 'text-anchor': 'middle', 'font-size': 11, fill: 'var(--kd-leise)', text: Math.round(q[2].mittel) + ' %'})); }
            });
            return s;
        }
        function stufenwegAnsicht() {
            ansicht.innerHTML = '';
            ansicht.appendChild(el('h3', {text: 'Stufenweg der Klasse'}));
            if (!SW) { ansicht.appendChild(el('p', {class: 'kd-hinweis', text: 'Dieser Kurs hat keine gestuften Aufgaben.'})); return; }
            ansicht.appendChild(el('p', {class: 'kd-hinweis', text: 'Auf welcher Stufe jede und jeder in jeder Kachel gearbeitet hat: ein Ring Grundlagen, zwei Standard, drei Vertiefung; ▲ aufgestiegen, ▼ abgestiegen. Namen antippen öffnet den Verlauf.'}));
            person = person || L[0];
            var wahl = el('select', {class: 'kd-wahl', 'aria-label': 'Lernende für den Verlauf wählen', on: {change: function (e) { person = L[e.target.selectedIndex]; stufenwegAnsicht(); }}});
            L.forEach(function (p) { var o = el('option', {text: p.n}); if (p === person) { o.selected = true; } wahl.appendChild(o); });
            ansicht.appendChild(el('div', {class: 'kd-karte kd-verlauf'}, [el('div', {class: 'kd-kopf'}, [el('h4', {text: 'Lernweg von ' + person.n}), el('label', {class: 'kd-wahl-l'}, ['Lernende: ', wahl])]),
                person.weg ? kurve(person) : el('p', {class: 'kd-hinweis', text: 'Noch keine Ergebnisse.'})]));
            var h = el('tr', {}, [el('th', {class: 'kd-name', text: 'Lernende'})].concat(SW.kacheln.map(function (k) { return el('th', {text: 'Kachel ' + k.nr}); })).concat([el('th', {class: 'kd-grenze', text: 'jetzt'})]));
            var body = el('tbody');
            L.forEach(function (p) {
                var tr = el('tr', {}, [el('td', {class: 'kd-name'}, [el('button', {class: 'kd-person', type: 'button', text: p.n, on: {click: function () { person = p; tab = 'person'; zeichnen(); }}})])]), jetzt = null;
                (p.weg || SW.kacheln.map(function () { return {zustand: 'offen'}; })).forEach(function (k) {
                    if (k.zustand === 'offen') { tr.appendChild(el('td', {}, [el('span', {class: 'kd-offen', text: '·'})])); return; }
                    var pf = k.zustand === 'fertig' && k.ende > k.einstieg ? el('span', {class: 'kd-auf', text: '▲'}) : (k.zustand === 'fertig' && k.ende < k.einstieg ? el('span', {class: 'kd-ab', text: '▼'}) : null);
                    tr.appendChild(el('td', {title: SW.stufen[k.einstieg]}, [ringe(k.einstieg), pf]));
                    jetzt = k.zustand === 'fertig' ? k.ende : k.einstieg;
                });
                tr.appendChild(el('td', {class: 'kd-grenze', text: jetzt === null ? '–' : SW.stufen[jetzt]}));
                body.appendChild(tr);
            });
            ansicht.appendChild(el('div', {class: 'kd-tw'}, [el('table', {class: 'kd-tab'}, [el('thead', {}, [h]), body])]));
            var vert = el('div', {class: 'kd-vert'});
            SW.kacheln.forEach(function (k, i) {
                var n = [0, 0, 0];
                L.forEach(function (p) { if (p.weg && p.weg[i].zustand !== 'offen') { n[p.weg[i].einstieg]++; } });
                vert.appendChild(el('div', {class: 'kd-vk'}, [el('b', {text: 'Kachel ' + k.nr})].concat([2, 1, 0].map(function (st) {
                    return el('div', {class: 'kd-balken'}, [ringe(st, 18), el('span', {class: 'kd-b', style: 'width:' + (n[st] * 10 + 2) + 'px;background:' + ['var(--kd-st0)', 'var(--kd-st1)', 'var(--kd-st2)'][st]}), String(n[st])]);
                }))));
            });
            ansicht.appendChild(el('h4', {text: 'Verteilung je Kachel'}));
            ansicht.appendChild(vert);
        }

        // ------------------------------------------------------------ Ansicht: eine Person
        function personAnsicht() {
            ansicht.innerHTML = '';
            person = person || L[0];
            var wahl = el('select', {class: 'kd-wahl', 'aria-label': 'Lernende wählen', on: {change: function (e) { person = L[e.target.selectedIndex]; zeichnen(); }}});
            L.forEach(function (p) { var o = el('option', {text: p.n}); if (p === person) { o.selected = true; } wahl.appendChild(o); });
            ansicht.appendChild(el('div', {class: 'kd-kopf'}, [el('h3', {text: person.n}), el('label', {class: 'kd-wahl-l'}, ['Lernende: ', wahl])]));
            var spalten = el('div', {class: 'kd-person-raster'});
            if (SW) {
                spalten.appendChild(el('div', {class: 'kd-karte'}, [el('h4', {text: 'Stufenweg'}), person.weg ? kurve(person) : el('p', {class: 'kd-hinweis', text: 'Noch keine Ergebnisse.'})]));
            }
            var ms = el('div', {class: 'kd-karte'}, [el('h4', {text: 'Meilensteine'})]);
            MS.forEach(function (m) {
                var a = auswertung(person, m), t = el('table', {class: 'kd-tab kd-mini'}, [el('thead', {}, [el('tr', {}, [el('th', {class: 'kd-name', text: m.kurz}), el('th', {text: 'Selbst'}), el('th', {text: 'Sie'}), el('th', {text: 'Abw.'})])])]), b = el('tbody');
                m.kriterien.forEach(function (k, i) {
                    var ab = a.abw[i];
                    b.appendChild(el('tr', {}, [el('td', {class: 'kd-name kd-umbruch', text: k.name}), el('td', {text: person[m.id].s ? String(person[m.id].s[i]) : '–'}),
                        el('td', {text: person[m.id].l[i] === null ? '–' : String(person[m.id].l[i])}), el('td', {}, [el('span', {class: 'kd-abw' + (ab !== null && ab >= AB ? ' kd-rot' : ''), text: ab === null ? '–' : String(ab)})])]));
                });
                t.appendChild(b);
                ms.appendChild(el('div', {class: 'kd-tw'}, [t]));
                ms.appendChild(el('p', {class: 'kd-hinweis'}, [a.note ? 'Note ' + a.note + ' (' + a.proz + ' %)' : 'noch nicht bewertet', ' ', a.gespraech ? el('span', {class: 'kd-pill kd-pill-rot', text: 'Gespräch'}) : null]));
            });
            spalten.appendChild(ms);
            ansicht.appendChild(spalten);
        }

        function herunterladen() {
            // CSV mit Semikolon und BOM, öffnet sich in Excel; Sicherung und Übernahme in die Klassen-Akte
            var zeilen = [];
            MS.forEach(function (m) {
                var k = ['Meilenstein', 'Lernende'];
                m.kriterien.forEach(function (kr) { k.push(kr.name + ' Selbsteinschätzung', kr.name + ' Ihre Bewertung', kr.name + ' Abweichung'); });
                zeilen.push(k.concat(['Prozent', 'Note', 'Gespräch']));
                L.forEach(function (p) {
                    var a = auswertung(p, m), z = [m.kurz, p.n];
                    m.kriterien.forEach(function (_, i) { z.push(p[m.id].s ? p[m.id].s[i] : '', p[m.id].l[i] === null ? '' : p[m.id].l[i], a.abw[i] === null ? '' : a.abw[i]); });
                    zeilen.push(z.concat([a.proz === null ? '' : a.proz, a.note === null ? '' : a.note, a.gespraech ? 'ja' : '']));
                });
                zeilen.push([]);
            });
            var text = '﻿' + zeilen.map(function (z) { return z.map(function (v) { v = String(v); return /[;"\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; }).join(';'); }).join('\r\n');
            var a = document.createElement('a');
            a.href = URL.createObjectURL(new Blob([text], {type: 'text/csv;charset=utf-8'}));
            a.download = 'Bewertung_' + (document.title.split('|')[0] || 'Kurs').trim().replace(/[^\wÄÖÜäöüß-]+/g, '_') + '.csv';
            document.body.appendChild(a);
            a.click();
            a.remove();
        }

        function zeichnen() {
            reiter.innerHTML = '';
            var tabs = MS.map(function (m) { return [m.id, m.kurz]; });
            if (SW) { tabs.push(['weg', 'Stufenweg der Klasse']); }
            tabs.push(['person', 'Eine Person']);
            tabs.forEach(function (t) {
                reiter.appendChild(el('button', {type: 'button', role: 'tab', 'aria-selected': String(t[0] === tab), text: t[1], on: {click: function () { tab = t[0]; zeichnen(); }}}));
            });
            var m = MS.filter(function (x) { return x.id === tab; })[0];
            kennzahlen(m || MS[0]);
            if (m) { tabelle(m); return; }
            ansicht.innerHTML = '';
            ansicht.appendChild(el('p', {class: 'kd-hinweis', text: 'lädt …'}));
            stufenwegLaden().then(function () { if (tab === 'weg') { stufenwegAnsicht(); } else { personAnsicht(); } });
        }

        Promise.all([teilnehmende(), feedbacks(), formular(), gespeichert()]).then(function (r) {
            var tn = r[0], fb = r[1], gs = r[3];
            return Promise.all(MS.map(function (m) { return selbst(m, fb[m.name]); })).then(function (sb) {
                L = tn.map(function (t) {
                    var p = {n: t.n, uid: t.uid, weg: null};
                    MS.forEach(function (m, i) {
                        var g = gs[t.n + '|' + m.id], l = g ? g.s.slice(0, m.kriterien.length) : [];
                        while (l.length < m.kriterien.length) { l.push(null); }
                        p[m.id] = {s: sb[i][t.n] || null, l: l, rid: g ? g.rid : null};
                    });
                    return p;
                });
                if (!FELD.lernende || !DID) { status('Felder der Datenbank nicht gefunden'); return; }
                status(L.length + ' Lernende geladen');
                zeichnen();
            });
        }).catch(function (e) { status('Daten konnten nicht gelesen werden (' + e + ')'); });
    }

    function los() { umgebung().then(start); }
    if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', los); } else { los(); }
})();
