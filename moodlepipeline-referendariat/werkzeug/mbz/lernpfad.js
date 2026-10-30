/*
 * „Mein Lernpfad“ (Lehrkraft 2026-10-28, Profil moodle.lernpfad_anzeige; lernpfad.py, inseln.py).
 *
 * Eine Datenbank-Aktivität ohne Einträge in Abschnitt 0 eines Themenkurses mit Übungsinseln. Das Skript (Vorlage
 * „JavaScript“) liest mit der Sitzung der Person, die die Seite öffnet, die eigene Bewertungsübersicht (Übungen und
 * Kurztests der Inseln) und zeigt den Weg durch die Inseln als Linie über drei Bahnen (Vertiefung, Standard,
 * Grundlagen), dazu dieselbe Auskunft als Text (Liste je Insel). Regel wie inseln.py: Start auf KONFIG.start, ab
 * KONFIG.grenzen[1] % eine Stufe höher, unter KONFIG.grenzen[0] % eine tiefer, sonst bleibt die Stufe; ohne Kurztest
 * bleibt sie auch. Kein Schlüssel im Quelltext; Lehrkräfte sehen einen Hinweis.
 *
 * Aufbau: reine Rechenlogik (mit node prüfbar: module.exports), dann der Moodle-Teil.
 */
(function () {
    'use strict';

    var KONFIG = /*KONFIG*/{
        "kursname": "Themenkurs",
        "farben": ["#08349C", "#7DDE78"],
        "linie": "#C62828",
        "grenzen": [50, 85],
        "start": "Standard",
        "stufen": ["Grundlagen", "Standard", "Vertiefung"],
        "inseln": []
    }/*/KONFIG*/;

    /** Zahl aus einem Text der Moodle-Oberfläche („85,00 %“, „7.5“); null ohne Zahl („-“). */
    function zahl(t) {
        if (t === null || t === undefined) {
            return null;
        }
        var m = String(t).replace(/\u00a0/g, ' ').match(/-?\d[\d.,]*/);
        if (!m) {
            return null;
        }
        var s = m[0];
        if (s.indexOf(',') >= 0) {
            s = s.replace(/\./g, '').replace(',', '.');
        }
        var n = parseFloat(s);
        return isNaN(n) ? null : n;
    }

    /** Stufe (0 = Grundlagen, 1 = Standard, 2 = Vertiefung) nach dem Kurztest; ohne Ergebnis bleibt sie. */
    function endstufe(e, prozent, grenzen) {
        if (prozent === null || prozent === undefined) {
            return e;
        }
        if (prozent >= grenzen[1]) {
            return Math.min(e + 1, 2);
        }
        if (prozent < grenzen[0]) {
            return Math.max(e - 1, 0);
        }
        return e;
    }

    function name(t) {
        return String(t || '').replace(/\s+/g, ' ').trim().toLowerCase();
    }

    /**
     * Der Pfad je Insel aus den eigenen Bewertungen. `noten`: {Name der Aktivität (klein): Prozent oder null}.
     * Ergebnis je Insel: {nr, titel, einstieg, ende, prozent, kurztestStufe, erledigt [3 × bool], begonnen,
     * fertig, offen [3 × bool], kurztestFehlt}.
     */
    function pfad(konfig, noten) {
        var stufen = konfig.stufen;
        var e = Math.max(0, stufen.indexOf(konfig.start));
        var aus = [];
        function wert(n) {
            var k = name(n);
            return Object.prototype.hasOwnProperty.call(noten, k) ? noten[k] : null;
        }
        konfig.inseln.forEach(function (insel) {
            var erledigt = insel.uebung.map(function (n) { return wert(n) !== null; });
            // Moodle öffnet nur den Kurztest der Einstiegsstufe; andere Ergebnisse (von Hand gesetzt) zählen nicht
            var prozent = wert(insel.kurztest[e]);
            var ende = endstufe(e, prozent, konfig.grenzen);
            var begonnen = erledigt.some(Boolean) || prozent !== null;
            aus.push({nr: insel.nr, titel: insel.titel, einstieg: e, ende: ende, prozent: prozent,
                      erledigt: erledigt, begonnen: begonnen, fertig: prozent !== null,
                      offen: [true, Math.max(e, ende) >= 1, Math.max(e, ende) >= 2], kurztestFehlt: false});
            e = ende;
        });
        // „Kurztest fehlt“: begonnen, ohne Kurztest, und eine spätere Insel ist schon begonnen
        for (var i = 0; i < aus.length; i++) {
            var spaeter = aus.slice(i + 1).some(function (x) { return x.begonnen; });
            aus[i].kurztestFehlt = aus[i].begonnen && !aus[i].fertig && spaeter;
        }
        return aus;
    }

    /** Die Insel, an der die Person gerade steht: die erste nicht fertige (sonst null = alle fertig). */
    function aktuelle(p) {
        for (var i = 0; i < p.length; i++) {
            if (!p[i].fertig) {
                return i;
            }
        }
        return null;
    }

    function prozentText(p) {
        return Number(p).toLocaleString('de-DE', {maximumFractionDigits: 0}) + ' %';
    }

    /** Ein Satz je Insel (Text-Alternative zur Grafik). */
    function satz(x, stufen) {
        var teile = [];
        var erledigt = stufen.filter(function (s, i) { return x.erledigt[i]; });
        if (!x.begonnen) {
            return 'noch nicht begonnen, Sie beginnen auf ' + stufen[x.einstieg] + '.';
        }
        teile.push('begonnen auf ' + stufen[x.einstieg]);
        if (x.fertig) {
            teile.push('Kurztest ' + prozentText(x.prozent));
            teile.push(x.ende > x.einstieg ? 'weiter auf ' + stufen[x.ende]
                       : x.ende < x.einstieg ? 'zurück auf ' + stufen[x.ende] : 'Sie bleiben auf ' + stufen[x.ende]);
        } else {
            teile.push(x.kurztestFehlt ? 'Kurztest fehlt, die Stufe bleibt' : 'Kurztest noch offen');
        }
        teile.push(erledigt.length ? 'geübt: ' + erledigt.join(', ') : 'noch nichts geübt');
        return teile.join(' · ') + '.';
    }

    /** Hinweis unter der Grafik: wo die nächste Insel beginnt. */
    function naechste(p, stufen) {
        var i = aktuelle(p);
        if (!p.length) {
            return '';
        }
        if (i === null) {
            return 'Alle Inseln erledigt. Zuletzt waren Sie auf ' + stufen[p[p.length - 1].ende] + '.';
        }
        if (p[i].begonnen) {
            return 'Sie arbeiten auf Insel ' + p[i].nr + ', Stufe ' + stufen[p[i].einstieg] + '.';
        }
        return 'Ihre nächste Insel (' + p[i].nr + ') beginnt auf ' + stufen[p[i].einstieg] + '.';
    }

    /** Punkte der Linie: je begonnene oder aktuelle Insel Einstieg und Ende (x = Spalte, s = Stufe). */
    function linie(p) {
        var punkte = [];
        var bis = aktuelle(p);
        p.forEach(function (x, i) {
            if (bis !== null && i > bis) {
                return;
            }
            punkte.push({spalte: i, teil: 0, stufe: x.einstieg});
            if (x.fertig) {
                punkte.push({spalte: i, teil: 1, stufe: x.ende});
            }
        });
        return punkte;
    }

    var Logik = {zahl: zahl, endstufe: endstufe, pfad: pfad, aktuelle: aktuelle, satz: satz, naechste: naechste,
                 linie: linie, name: name, KONFIG: KONFIG};
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = Logik;
        return;
    }

    // ------------------------------------------------------------------------------------------------ //
    // Moodle-Teil
    // ------------------------------------------------------------------------------------------------ //
    var CFG = (window.M && M.cfg) || {};
    var WURZEL = CFG.wwwroot || '';
    var KURS = CFG.courseId;
    var SVG = 'http://www.w3.org/2000/svg';

    function el(tag, attribute, kinder, ns) {
        var e = ns ? document.createElementNS(ns, tag) : document.createElement(tag);
        Object.keys(attribute || {}).forEach(function (k) {
            if (k === 'text') {
                e.textContent = attribute[k];
            } else {
                e.setAttribute(k, attribute[k]);
            }
        });
        (kinder || []).forEach(function (c) {
            if (c !== null && c !== undefined) {
                e.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
            }
        });
        return e;
    }

    function s(tag, attribute, kinder) {
        return el(tag, attribute, kinder, SVG);
    }

    function text(e) {
        return e ? e.textContent.replace(/\s+/g, ' ').trim() : '';
    }

    function istLehrkraft() {
        return !!document.querySelector('a[href*="/mod/data/field.php"], a[href*="/mod/data/templates.php"], ' +
            'a[href*="/course/modedit.php"]');
    }

    /**
     * Eigene Bewertungen: {Name (klein): Prozent oder null} aus der Bewertungsübersicht des Kurses. Rechnet Moodle die
     * Bewertungen gerade neu, nach kurzer Zeit noch einmal (höchstens 5-mal, wie der Sternzähler).
     */
    function holeNoten(versuch) {
        versuch = versuch || 0;
        return fetch(WURZEL + '/grade/report/user/index.php?id=' + KURS, {credentials: 'same-origin'})
            .then(function (r) {
                if (!r.ok) {
                    throw new Error('HTTP ' + r.status);
                }
                return r.text();
            }).then(function (t) {
                var doc = new DOMParser().parseFromString(t, 'text/html');
                var noten = {};
                if (!doc.querySelector('.column-itemname') && versuch < 5 &&
                        doc.querySelector('.progress, [role="progressbar"]')) {
                    return new Promise(function (fertig) { setTimeout(fertig, 3000); })
                        .then(function () { return holeNoten(versuch + 1); });
                }
                if (!doc.querySelector('.column-itemname')) {
                    throw new Error('Moodle berechnet die Bewertungen gerade neu, bitte die Seite gleich neu laden');
                }
                Array.prototype.forEach.call(doc.querySelectorAll('tr'), function (z) {
                    var kopf = z.querySelector('.column-itemname');
                    if (!kopf) {
                        return;
                    }
                    var titel = text(kopf.querySelector('.gradeitemheader, a')) || text(kopf);
                    var p = zahl(text(z.querySelector('.column-percentage')));
                    if (p === null) {
                        var g = zahl(text(z.querySelector('.column-grade')));
                        var bereich = text(z.querySelector('.column-range')).split(/[^\d.,]+/).filter(Boolean);
                        var hoechst = bereich.length ? zahl(bereich[bereich.length - 1]) : null;
                        p = g !== null && hoechst ? g * 100 / hoechst : null;
                    }
                    noten[name(titel)] = p;
                });
                return noten;
            });
    }

    /** Die Grafik: Bahnen Vertiefung (oben), Standard, Grundlagen; Inseln nebeneinander; rote Linie. */
    function grafik(p) {
        var blau = KONFIG.farben[0], gruen = KONFIG.farben[1], rot = KONFIG.linie;
        var links = 120, spalte = 120, oben = 28, bahn = 52;
        var breite = links + spalte * p.length + 12, hoehe = oben + bahn * 2 + 64;
        var y = function (stufe) { return oben + (2 - stufe) * bahn; };
        var x = function (i, teil) { return links + i * spalte + (teil ? 88 : 32); };
        var bild = s('svg', {viewBox: '0 0 ' + breite + ' ' + hoehe, width: '100%', role: 'img',
                             'aria-labelledby': 'lp-titel lp-kurz', style: 'max-width:' + breite + 'px;height:auto'});
        bild.appendChild(s('title', {id: 'lp-titel', text: 'Mein Lernpfad'}));
        bild.appendChild(s('desc', {id: 'lp-kurz', text: naechste(p, KONFIG.stufen) +
            ' Die Liste unter der Grafik beschreibt jede Insel.'}));
        [2, 1, 0].forEach(function (st) {
            bild.appendChild(s('line', {x1: links - 8, x2: breite - 8, y1: y(st), y2: y(st), stroke: '#B8C2D6',
                                        'stroke-width': 2, 'stroke-dasharray': '4 4'}));
            bild.appendChild(s('text', {x: 4, y: y(st) + 5, fill: blau, 'font-size': 16, 'font-weight': 'bold',
                                        text: KONFIG.stufen[st]}));
        });
        var jetzt = aktuelle(p);
        p.forEach(function (insel, i) {
            var x0 = links + i * spalte + 6;
            bild.appendChild(s('rect', {x: x0, y: oben - 22, width: spalte - 12, height: bahn * 2 + 44, rx: 12,
                                        fill: i === jetzt ? '#EEF3FF' : '#F7F8FA',
                                        stroke: i === jetzt ? blau : '#C9D1DE', 'stroke-width': i === jetzt ? 2 : 1}));
            bild.appendChild(s('text', {x: x0 + (spalte - 12) / 2, y: hoehe - 12, 'text-anchor': 'middle',
                                        fill: '#14213D', 'font-size': 16, text: 'Insel ' + insel.nr}));
            [0, 1, 2].forEach(function (st) {
                var cx = links + i * spalte + 60, cy = y(st);
                var fertig = insel.erledigt[st];
                bild.appendChild(s('circle', {cx: cx, cy: cy, r: 11, fill: fertig ? gruen : '#FFFFFF',
                                              stroke: insel.offen[st] ? blau : '#9AA3B2', 'stroke-width': 2,
                                              'stroke-dasharray': insel.offen[st] ? '' : '3 3'}));
                if (fertig) {
                    bild.appendChild(s('path', {d: 'M' + (cx - 5) + ' ' + cy + ' l4 4 l7 -8', fill: 'none',
                                                stroke: '#14213D', 'stroke-width': 2.5}));
                }
            });
        });
        var punkte = linie(p);
        if (punkte.length) {
            var d = punkte.map(function (q, k) { return (k ? 'L' : 'M') + x(q.spalte, q.teil) + ' ' + y(q.stufe); });
            bild.appendChild(s('path', {d: d.join(' '), fill: 'none', stroke: rot, 'stroke-width': 4,
                                        'stroke-linejoin': 'round', 'stroke-linecap': 'round'}));
            punkte.forEach(function (q) {
                bild.appendChild(s('circle', {cx: x(q.spalte, q.teil), cy: y(q.stufe), r: 4, fill: rot}));
            });
            var letzter = punkte[punkte.length - 1];
            bild.appendChild(s('circle', {cx: x(letzter.spalte, letzter.teil), cy: y(letzter.stufe), r: 9,
                                          fill: 'none', stroke: rot, 'stroke-width': 3}));
        }
        return bild;
    }

    function liste(p) {
        return el('ol', {'class': 'lp-liste'}, p.map(function (x) {
            return el('li', {}, [el('strong', {text: 'Insel ' + x.nr + ' · ' + x.titel + ': '}),
                                 satz(x, KONFIG.stufen)]);
        }));
    }

    function legende() {
        return el('p', {'class': 'lp-legende', text: 'Rote Linie: Ihr Weg (links in jeder Insel die Stufe, auf der ' +
            'Sie begonnen haben, rechts die nach dem Kurztest). Grüner Kreis mit Haken: Übung geübt. Gestrichelter ' +
            'Kreis: noch gesperrt. Ab ' + KONFIG.grenzen[1] + ' % im Kurztest geht es eine Stufe höher, unter ' +
            KONFIG.grenzen[0] + ' % eine tiefer.'});
    }

    function start() {
        if (!/\/mod\/data\/view\.php$/.test(window.location.pathname)) {
            return;
        }
        var haupt = document.querySelector('#region-main [role="main"]') || document.querySelector('#region-main') ||
            document.body;
        var ziel = el('section', {'class': 'lp', 'aria-live': 'polite', 'aria-busy': 'true'},
                      [el('p', {text: 'Ihr Lernpfad wird geladen …'})]);
        haupt.insertBefore(ziel, haupt.firstChild);
        Array.prototype.forEach.call(document.querySelectorAll('#region-main #action_bar, ' +
            '#region-main .datapreferences, #region-main .tertiary-navigation, #region-main h5'), function (x) {
            if (x.id === 'action_bar' || /no entries|keine einträge/i.test(text(x)) || !/^H5$/.test(x.tagName)) {
                x.style.setProperty('display', 'none', 'important');
            }
        });
        if (istLehrkraft()) {
            ziel.setAttribute('aria-busy', 'false');
            ziel.textContent = '';
            ziel.appendChild(el('p', {'class': 'lp-hinweis', text: 'Hier sehen Lernende ihren Weg durch die ' +
                KONFIG.inseln.length + ' Übungsinseln: je Insel die Stufe, auf der sie begonnen haben, das ' +
                'Ergebnis des Kurztests und die geübten Stufen. Die Ergebnisse der Klasse zeigt die ' +
                'Bewerterübersicht (Kurztests der Inseln).'}));
            return;
        }
        holeNoten().then(function (noten) {
            var p = pfad(KONFIG, noten);
            ziel.setAttribute('aria-busy', 'false');
            ziel.textContent = '';
            ziel.appendChild(el('p', {'class': 'lp-zeile', text: naechste(p, KONFIG.stufen)}));
            ziel.appendChild(el('div', {'class': 'lp-bild'}, [grafik(p)]));
            ziel.appendChild(legende());
            ziel.appendChild(el('h4', {text: 'Ihre Inseln'}));
            ziel.appendChild(liste(p));
        }).catch(function (e) {
            ziel.setAttribute('aria-busy', 'false');
            ziel.textContent = '';
            ziel.appendChild(el('p', {'class': 'alert alert-warning', text: 'Ihr Lernpfad ließ sich gerade nicht ' +
                'lesen (' + e.message + '). Ihre Ergebnisse stehen auch unter „Bewertungen“.'}));
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', start);
    } else {
        start();
    }
})();
