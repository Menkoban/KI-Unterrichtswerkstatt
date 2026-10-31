/*
 * Klassen-Dashboard (Lehrkraft 2026-10-31, dashboard.py). Läuft als JavaScript-Vorlage der verborgenen Datenbank-
 * Aktivität „Klassen-Dashboard“ im Lehrkraftbereich, nur in der Listenansicht und mit der Sitzung der Lehrkraft:
 *   - Teilnehmende des Kurses (Rolle Lernende) aus der Teilnehmerseite,
 *   - Selbsteinschätzungen je Meilenstein aus der Feedback-Aktivität (CSV-Download, Spalten „(K1) …“),
 *   - gespeicherte Stufen der Lehrkraft aus den Einträgen dieser Datenbank (Felder lernende, meilenstein, stufen),
 * zeigt je Meilenstein eine Tabelle (selbst, Ihre Stufe, Abweichung; rot ab KONFIG.gespraech_ab), Note nach IHK und
 * speichert jede angetippte Stufe sofort als Eintrag dieser Datenbank (normales Formular, sesskey der Sitzung).
 * Keine externen Schriften oder Dienste.
 */
(function () {
    'use strict';
    var KONFIG = /*KONFIG*/{"gespraech_ab": 2, "meilensteine": []}/*/KONFIG*/;
    var IHK = [[92, 1], [81, 2], [67, 3], [50, 4], [30, 5], [0, 6]];

    function start() {
        if (!/\/mod\/data\/view\.php$/.test(location.pathname) || /[?&]rid=/.test(location.search)) {
            return;
        }
        if (!window.M || !M.cfg || !KONFIG.meilensteine.length) {
            return;
        }
        var q = new URLSearchParams(location.search);
        var ziel = q.get('d') ? 'd=' + q.get('d') : 'id=' + q.get('id');
        var WURZEL = M.cfg.wwwroot, KURS = M.cfg.courseId, AB = KONFIG.gespraech_ab || 2;
        var MS = KONFIG.meilensteine, tab = MS[0].id, L = [], FELD = {}, DID = null;

        var wurzel = document.createElement('div');
        wurzel.className = 'kd';
        var main = document.querySelector('[role="main"]') || document.body;
        main.insertBefore(wurzel, main.firstChild);
        document.querySelectorAll('.kd-liste').forEach(function (x) { x.hidden = true; });

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
        var zahlen = el('div', {class: 'kd-zahlen'});
        var reiter = el('div', {class: 'kd-reiter', role: 'tablist'});
        var ansicht = el('div', {class: 'kd-panel'});
        [kopf, zahlen, reiter, ansicht].forEach(function (x) { wurzel.appendChild(x); });
        function status(t) { document.getElementById('kdStatus').textContent = t; }

        function teilnehmende() {
            return seite('/user/index.php?id=' + KURS + '&perpage=5000').then(function (t) {
                var aus = [];
                dok(t).querySelectorAll('table tbody tr').forEach(function (tr) {
                    var a = tr.querySelector('a[href*="user/view.php"]');
                    if (!a) { return; }
                    var k = a.cloneNode(true);
                    k.querySelectorAll('.userinitials, img, .userpicture').forEach(function (x) { x.remove(); });
                    var name = k.textContent.replace(/\s+/g, ' ').trim(), rollen = tr.textContent;
                    if (name && /Student|Teilnehmer|Schüler|Lernende/i.test(rollen) && !/Teacher|Trainer|Lehrkr|Lehrer/i.test(rollen)) { aus.push(name); }
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
            [[s + ' / ' + L.length, 'Selbsteinschätzungen da', ''], [b + ' / ' + L.length, 'von Ihnen bewertet', ''],
             [String(g), 'Gespräche nötig', ' kd-alarm'], [n ? (su / n).toFixed(1).replace('.', ',') : '–', 'Notenschnitt', '']].forEach(function (z) {
                zahlen.appendChild(el('div', {class: 'kd-zahl' + z[2]}, [el('div', {class: 'kd-w', text: z[0]}), el('div', {class: 'kd-l', text: z[1]})]));
            });
        }
        function tabelle(m) {
            ansicht.innerHTML = '';
            ansicht.appendChild(el('h3', {text: m.titel}));
            ansicht.appendChild(el('p', {class: 'kd-hinweis', text: 'Grau: Selbsteinschätzung aus „' + m.name + '“, von selbst gelesen. Tippen Sie Ihre Stufe an; sie wird sofort gespeichert. Ab ' + AB + ' Stufen Abweichung wird das Feld rot und „Gespräch“ erscheint.'}));
            var r1 = el('tr', {}, [el('th', {class: 'kd-name', rowspan: '2', text: 'Lernende'})]), r2 = el('tr');
            m.kriterien.forEach(function (k) { r1.appendChild(el('th', {class: 'kd-kr', colspan: '3', text: k.name})); });
            ['Prozent', 'Note', 'Rückmeldung'].forEach(function (t, i) { r1.appendChild(el('th', {rowspan: '2', class: i === 0 ? 'kd-grenze' : '', text: t})); });
            m.kriterien.forEach(function () { ['selbst', 'Ihre Stufe', 'Abw.'].forEach(function (t, i) { r2.appendChild(el('th', {class: i === 0 ? 'kd-grenze' : '', text: t})); }); });
            var body = el('tbody');
            L.forEach(function (p) {
                var a = auswertung(p, m), tr = el('tr', {class: a.gespraech ? 'kd-gespraech-zeile' : ''});
                tr.appendChild(el('td', {class: 'kd-name'}, [el('b', {text: p.n})]));
                m.kriterien.forEach(function (k, i) {
                    tr.appendChild(el('td', {class: 'kd-grenze'}, [p[m.id].s ? el('span', {class: 'kd-selbst', title: k.stufen[p[m.id].s[i] - 1] || '', text: String(p[m.id].s[i])}) : el('span', {class: 'kd-offen', text: 'fehlt'})]));
                    var grp = el('div', {class: 'kd-stufen', role: 'group', 'aria-label': p.n + ' · ' + k.name});
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
        function herunterladen() {
            // CSV mit Semikolon und BOM, öffnet sich in Excel; Sicherung und Übernahme in die Klassen-Akte
            var zeilen = [];
            MS.forEach(function (m) {
                var kopfzeile = ['Meilenstein', 'Lernende'];
                m.kriterien.forEach(function (k) { kopfzeile.push(k.name + ' selbst', k.name + ' Lehrkraft', k.name + ' Abweichung'); });
                zeilen.push(kopfzeile.concat(['Prozent', 'Note', 'Gespräch']));
                L.forEach(function (p) {
                    var a = auswertung(p, m), z = [m.kurz, p.n];
                    m.kriterien.forEach(function (_, i) { z.push(p[m.id].s ? p[m.id].s[i] : '', p[m.id].l[i] === null ? '' : p[m.id].l[i], a.abw[i] === null ? '' : a.abw[i]); });
                    zeilen.push(z.concat([a.proz === null ? '' : a.proz, a.note === null ? '' : a.note, a.gespraech ? 'ja' : '']));
                });
                zeilen.push([]);
            });
            var text = '\ufeff' + zeilen.map(function (z) { return z.map(function (v) { v = String(v); return /[;"\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; }).join(';'); }).join('\r\n');
            var a = document.createElement('a');
            a.href = URL.createObjectURL(new Blob([text], {type: 'text/csv;charset=utf-8'}));
            a.download = 'Bewertung_' + (document.title.split('|')[0] || 'Kurs').trim().replace(/[^\wÄÖÜäöüß-]+/g, '_') + '.csv';
            document.body.appendChild(a); a.click(); a.remove();
        }
        function zeichnen() {
            var m = MS.filter(function (x) { return x.id === tab; })[0];
            reiter.innerHTML = '';
            MS.forEach(function (x) {
                reiter.appendChild(el('button', {type: 'button', role: 'tab', 'aria-selected': String(x.id === tab), text: x.kurz,
                    on: {click: function () { tab = x.id; zeichnen(); }}}));
            });
            kennzahlen(m);
            tabelle(m);
        }

        Promise.all([teilnehmende(), feedbacks(), formular(), gespeichert()]).then(function (r) {
            var namen = r[0], fb = r[1], gs = r[3];
            return Promise.all(MS.map(function (m) { return selbst(m, fb[m.name]); })).then(function (sb) {
                L = namen.map(function (n) {
                    var p = {n: n};
                    MS.forEach(function (m, i) {
                        var g = gs[n + '|' + m.id], l = g ? g.s.slice(0, m.kriterien.length) : [];
                        while (l.length < m.kriterien.length) { l.push(null); }
                        p[m.id] = {s: sb[i][n] || null, l: l, rid: g ? g.rid : null};
                    });
                    return p;
                });
                if (!FELD.lernende || !DID) { status('Felder der Datenbank nicht gefunden'); return; }
                status(L.length + ' Lernende geladen');
                zeichnen();
            });
        }).catch(function (e) { status('Daten konnten nicht gelesen werden (' + e + ')'); });
    }

    if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', start); } else { start(); }
})();
