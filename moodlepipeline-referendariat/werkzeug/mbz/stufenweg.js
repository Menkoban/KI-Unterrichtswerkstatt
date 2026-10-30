/*
 * „Mein Stufenweg“ (KONFIG 2026-11, Prototyp; stufen.py). Eine Datenbank-Aktivität ohne Einträge in Allgemein. Das
 * Skript (Vorlage „JavaScript“) liest mit der Sitzung der ansehenden Person die eigene Bewertungsübersicht, rechnet je
 * Kachel nach der Regel aus stufen.py (Start KONFIG.start; Durchschnitt aller Aufgaben der eigenen Stufe, erster
 * Versuch: ab KONFIG.grenzen[1] % eine Stufe höher, unter KONFIG.grenzen[0] % eine tiefer, sonst bleibt sie; solange
 * nicht alle Aufgaben bewertet sind, bleibt sie auch) und zeigt den Weg in einer von zwei Darstellungen:
 *   verlauf  (A, Standard, Lehrkraft 2026-11) Verlauf über die Kacheln mit drei Höhen, aktueller Punkt
 *            hervorgehoben, darunter Rückmeldekarten
 *   karten   (B, Option) eine Karte je Kachel mit Stufenzeichen, Ergebnisring und Rückmeldung
 * Bildsprache „Schalen“: Grundlagen ein, Standard zwei, Vertiefung drei Ringe um einen Kern (Form und Text, nicht nur
 * Farbe). Alles steht auch als Text da (Karten, Beschriftung der Grafik). Kein Schlüssel im Quelltext.
 *
 * Aufbau: reine Rechenlogik (mit node prüfbar: module.exports), dann der Moodle-Teil.
 */
(function () {
    'use strict';

    var KONFIG = /*KONFIG*/{
        "darstellung": "verlauf",
        "farben": ["#08349C", "#7DDE78"],
        "grenzen": [50, 85],
        "start": "Standard",
        "stufen": ["Grundlagen", "Standard", "Vertiefung"],
        "kacheln": []
    }/*/KONFIG*/;

    // ------------------------------------------------------------------------------------------------ //
    // Rechenlogik
    // ------------------------------------------------------------------------------------------------ //
    function zahl(t) {
        if (t === null || t === undefined) {
            return null;
        }
        var m = String(t).replace(/ /g, ' ').match(/-?\d[\d.,]*/);
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

    function name(t) {
        return String(t || '').replace(/\s+/g, ' ').trim().toLowerCase();
    }

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

    /**
     * Weg je Kachel aus den eigenen Bewertungen ({Name klein: Prozent oder null}). Ergebnis je Kachel: {nr, titel,
     * einstieg, ende, mittel, ergebnisse [{name, thema, prozent}], erledigt, anzahl, zustand (offen | laufend |
     * fertig), richtung (auf | ab | bleibt | null)}.
     */
    function weg(konfig, noten) {
        var e = Math.max(0, konfig.stufen.indexOf(konfig.start));
        return konfig.kacheln.map(function (k) {
            var ergebnisse = (k.aufgaben[e] || []).map(function (a) {
                var key = name(a.name);
                var p = Object.prototype.hasOwnProperty.call(noten, key) ? noten[key] : null;
                return {name: a.name, thema: a.thema, prozent: p};
            });
            var erledigt = ergebnisse.filter(function (r) { return r.prozent !== null; }).length;
            var fertig = ergebnisse.length > 0 && erledigt === ergebnisse.length;
            var mittel = fertig ? ergebnisse.reduce(function (s, r) { return s + r.prozent; }, 0) / ergebnisse.length
                : null;
            var ende = endstufe(e, mittel, konfig.grenzen);
            var x = {nr: k.nr, titel: k.titel, einstieg: e, ende: ende, mittel: mittel, ergebnisse: ergebnisse,
                     erledigt: erledigt, anzahl: ergebnisse.length,
                     zustand: fertig ? 'fertig' : erledigt ? 'laufend' : 'offen',
                     richtung: fertig ? (ende > e ? 'auf' : ende < e ? 'ab' : 'bleibt') : null};
            e = ende;
            return x;
        });
    }

    /** Index der Kachel, an der die Person steht (erste nicht fertige); null = alle fertig. */
    function aktuelle(w) {
        for (var i = 0; i < w.length; i++) {
            if (w[i].zustand !== 'fertig') {
                return i;
            }
        }
        return null;
    }

    /** Stufe jetzt: Einstieg der aktuellen Kachel, sonst Ende der letzten. */
    function jetzt(w, konfig) {
        var i = aktuelle(w);
        if (!w.length) {
            return Math.max(0, konfig.stufen.indexOf(konfig.start));
        }
        return i === null ? w[w.length - 1].ende : w[i].einstieg;
    }

    function prozentText(p) {
        return Math.round(p).toLocaleString('de-DE') + '\u00a0%';
    }

    function aufzaehlen(liste) {
        liste = liste.map(function (t) { return '„' + t + '“'; });
        if (liste.length <= 1) {
            return liste.join('');
        }
        return liste.slice(0, -1).join(', ') + ' und ' + liste[liste.length - 1];
    }

    /** Automatische Rückmeldung je Kachel: {titel, saetze [Text], stark [Themen], ueben [Themen]}. */
    function rueckmeldung(x, konfig, naechste) {
        var st = konfig.stufen, g = konfig.grenzen;
        var stark = x.ergebnisse.filter(function (r) { return r.prozent !== null && r.prozent >= g[1]; })
            .map(function (r) { return r.thema; });
        var ueben = x.ergebnisse.filter(function (r) { return r.prozent !== null && r.prozent < 60; })
            .map(function (r) { return r.thema; });
        var weiter = naechste ? 'In Kachel ' + naechste + ' ' : 'Ab jetzt ';
        var t = 'Kachel ' + x.nr, s = [];
        if (x.zustand === 'offen') {
            return {titel: t + ': noch nicht begonnen', saetze: ['Sie arbeiten hier auf ' + st[x.einstieg] + '.'],
                    stark: [], ueben: []};
        }
        if (x.zustand === 'laufend') {
            s.push('Läuft: ' + x.erledigt + ' von ' + x.anzahl + ' Aufgaben erledigt. Für Ihre nächste Stufe zählt ' +
                   'der erste Versuch jeder Aufgabe.');
            if (stark.length) {
                s.push('Schon stark bei ' + aufzaehlen(stark) + '.');
            }
            return {titel: t + ': in Arbeit auf ' + st[x.einstieg], saetze: s, stark: stark, ueben: ueben};
        }
        var p = prozentText(x.mittel);
        if (x.richtung === 'auf') {
            t += ': ' + p + ', Aufstieg!';
            s.push('Stark gemacht. ' + weiter + 'arbeiten Sie auf ' + st[x.ende] + '.');
        } else if (x.richtung === 'ab') {
            t += ': ' + p + ', gezielt trainieren';
            s.push(weiter + 'trainieren Sie gezielt auf ' + st[x.ende] + ': gleiches Ziel, mehr Gerüst. Mit ' +
                   g[1] + '\u00a0% geht es wieder eine Stufe höher.');
        } else if (x.einstieg === 2 && x.mittel >= g[1]) {
            t += ': ' + p + ', Bestwert';
            s.push('Bestwert auf Vertiefung. Sie bleiben ganz oben.');
        } else if (x.einstieg === 0 && x.mittel < g[0]) {
            t += ': ' + p + ', Sie bleiben auf Grundlagen';
            s.push('Sie festigen weiter die Grundlagen. Mit ' + g[1] + '\u00a0% geht es eine Stufe höher.');
        } else {
            t += ': ' + p + ', Sie bleiben auf ' + st[x.ende];
            s.push(x.einstieg < 2 ? 'Solide. Bis zum Aufstieg fehlten ' + Math.ceil(g[1] - x.mittel) +
                   ' Prozentpunkte.' : 'Solide: Sie halten Vertiefung.');
        }
        if (stark.length) {
            s.push((x.richtung === 'ab' ? 'Das sitzt schon: ' : 'Stark bei ') + aufzaehlen(stark) + '.');
        }
        if (ueben.length) {
            s.push('Üben Sie ' + aufzaehlen(ueben) + '.');
        }
        return {titel: t, saetze: s, stark: stark, ueben: ueben};
    }

    /** Ein Satz oben: wo man steht und wie es zuletzt ging. */
    function leitsatz(w, konfig) {
        var st = konfig.stufen, i = aktuelle(w), j = jetzt(w, konfig);
        var fertige = w.filter(function (x) { return x.zustand === 'fertig'; });
        var letzte = fertige.length ? fertige[fertige.length - 1] : null;
        var wo = i === null ? 'Alle Kacheln erledigt.' : 'Kachel ' + w[i].nr + ' von ' + w.length + '.';
        if (!letzte) {
            return {art: 'start', text: 'Sie starten auf ' + st[j] + '. ' + wo};
        }
        if (letzte.richtung === 'auf') {
            return {art: 'auf', text: 'Aufgestiegen! Willkommen auf ' + st[j] + '. ' + wo};
        }
        if (letzte.richtung === 'ab') {
            return {art: 'ab', text: 'Sie trainieren jetzt gezielt auf ' + st[j] + ', damit der nächste Schritt ' +
                    'sitzt. ' + wo};
        }
        return {art: 'bleibt', text: 'Sie sind auf Kurs: ' + st[j] + '. ' + wo};
    }

    var Logik = {zahl: zahl, name: name, endstufe: endstufe, weg: weg, aktuelle: aktuelle, jetzt: jetzt,
                 rueckmeldung: rueckmeldung, leitsatz: leitsatz, KONFIG: KONFIG};
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
    var BLAU = KONFIG.farben[0], GRUEN = KONFIG.farben[1], TINTE = '#14213D';
    var TON = {auf: ['#E8F8E7', '#0B5D1E', '▲ Aufstieg'], ab: ['#FFF4DB', '#6B4A00', '◆ Training'],
               bleibt: ['#E6EDFA', BLAU, '● bleibt']};

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

    /** Stufenzeichen „Schalen“ als SVG-Gruppe (Mittelpunkt cx, cy; Kantenlänge g). */
    function zeichen(stufe, cx, cy, g, titel) {
        var n = stufe + 1, k = g / 48, dunkel = n === 3;
        var grp = s('g', {transform: 'translate(' + (cx - g / 2) + ' ' + (cy - g / 2) + ') scale(' + k + ')'});
        if (titel) {
            grp.appendChild(s('title', {text: 'Stufe ' + KONFIG.stufen[stufe]}));
        }
        grp.appendChild(s('rect', {x: 1, y: 1, width: 46, height: 46, rx: 13,
                                   fill: dunkel ? BLAU : (n === 1 ? '#E8F8E7' : '#E6EDFA'),
                                   stroke: dunkel ? 'none' : BLAU, 'stroke-opacity': 0.25, 'stroke-width': 1.5}));
        grp.appendChild(s('circle', {cx: 24, cy: 24, r: 4.6, fill: dunkel ? GRUEN : BLAU}));
        var winkel = [-35, 205, 95];
        for (var i = 0; i < n; i++) {
            var r = n === 3 ? 9 + 5.6 * i : 10 + 6.5 * i, w = winkel[i] * Math.PI / 180;
            grp.appendChild(s('circle', {cx: 24, cy: 24, r: r, fill: 'none', stroke: dunkel ? '#FFFFFF' : BLAU,
                                         'stroke-width': 2.2}));
            grp.appendChild(s('circle', {cx: 24 + r * Math.cos(w), cy: 24 + r * Math.sin(w), r: 3.1, fill: GRUEN,
                                         stroke: dunkel ? '#FFFFFF' : BLAU, 'stroke-width': 1.4}));
        }
        return grp;
    }

    function zeichenBild(stufe, px) {
        var b = s('svg', {viewBox: '0 0 ' + px + ' ' + px, width: px, height: px, 'aria-hidden': 'true',
                          focusable: 'false', 'class': 'sw-zeichen'});
        b.appendChild(zeichen(stufe, px / 2, px / 2, px));
        return b;
    }

    function stil() {
        if (document.getElementById('sw-stil')) {
            return;
        }
        var css = [
            '.sw{color:' + TINTE + ';font-size:16px;line-height:1.45;margin:0 0 1rem 0;max-width:980px}',
            '.sw *{box-sizing:border-box}',
            '.sw-held{position:relative;overflow:hidden;border-radius:20px;padding:18px 20px;margin:0 0 16px 0;' +
                'background:' + BLAU + ';color:#fff;display:flex;align-items:center;gap:16px}',
            '.sw-held .sw-zeichen{flex:0 0 auto;background:#fff;border-radius:16px;padding:4px}',
            '.sw-held small{display:block;text-transform:uppercase;letter-spacing:.09em;font-size:.78em;opacity:.85}',
            '.sw-held strong{display:block;font-size:1.7em;line-height:1.15}',
            '.sw-held p{margin:4px 0 0}',
            '.sw-held.sw-auf::after{content:"";position:absolute;right:-30px;top:-30px;width:150px;height:150px;' +
                'border-radius:50%;border:14px solid ' + GRUEN + ';opacity:.5}',
            '.sw-funken i{position:absolute;width:9px;height:9px;border-radius:50%;background:' + GRUEN + ';' +
                'opacity:0;animation:sw-funke 1.6s ease-out .3s 2}',
            '@keyframes sw-funke{0%{opacity:0;transform:translate(0,0) scale(.4)}20%{opacity:1}' +
                '100%{opacity:0;transform:translate(var(--dx),var(--dy)) scale(1)}}',
            '@media (prefers-reduced-motion:reduce){.sw-funken i,.sw-halo{animation:none!important}}',
            '.sw-grafik{background:#F7F9FD;border:1px solid #D5DDEB;border-radius:18px;padding:6px 4px;' +
                'margin:0 0 16px 0}',
            '.sw-grafik svg{display:block;width:100%;height:auto}',
            '.sw-halo{animation:sw-puls 2.2s ease-in-out infinite;transform-box:fill-box;transform-origin:center}',
            '@keyframes sw-puls{0%,100%{opacity:.35}50%{opacity:.9}}',
            '.sw h4{color:' + BLAU + ';font-size:1.1em;margin:18px 0 8px}',
            '.sw-liste{list-style:none;margin:0;padding:0;display:grid;gap:10px}',
            '.sw-fb{display:flex;gap:12px;align-items:flex-start;background:#fff;border:1px solid #D5DDEB;' +
                'border-left:7px solid #B8C2D6;border-radius:14px;padding:12px 14px}',
            '.sw-fb.auf{border-left-color:' + GRUEN + '}.sw-fb.ab{border-left-color:#F2B635}' +
                '.sw-fb.bleibt{border-left-color:' + BLAU + '}.sw-fb.laufend{border-left-style:dashed}',
            '.sw-fb p{margin:2px 0}.sw-fb strong{color:' + TINTE + '}',
            '.sw-schild{display:inline-block;border-radius:999px;padding:1px 10px;font-size:.85em;font-weight:700;' +
                'margin:0 6px 0 0;vertical-align:middle}',
            '.sw-karten{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px}',
            '.sw-karte{position:relative;background:#fff;border:1px solid #D5DDEB;border-radius:18px;' +
                'padding:14px 16px 16px;display:flex;flex-direction:column;gap:8px}',
            '.sw-karte.jetzt{border:3px solid ' + BLAU + ';box-shadow:0 6px 18px rgba(8,52,156,.15)}',
            '.sw-karte.spaeter{background:#F7F8FA;color:#4A5568}',
            '.sw-karte .sw-kopf{font-size:.85em;text-transform:uppercase;letter-spacing:.07em;color:#4A5878}',
            '.sw-karte h5{margin:0;font-size:1.02em;color:' + TINTE + '}',
            '.sw-mitte{display:flex;align-items:center;gap:12px}',
            '.sw-mitte .sw-stufe{font-weight:800;font-size:1.2em;color:' + BLAU + '}',
            '.sw-band{position:absolute;top:-1px;right:14px;background:' + BLAU + ';color:#fff;font-weight:700;' +
                'font-size:.8em;padding:3px 10px;border-radius:0 0 10px 10px}',
            '.sw-legende{font-size:.9em;color:#4A5568;margin:8px 4px 0}',
            '@media (max-width:560px){.sw-held{padding:14px}.sw-held strong{font-size:1.4em}.sw-held.sw-auf::after{display:none}}',
            '.sw-fb .sw-zeichen,.sw-mitte .sw-zeichen{flex:0 0 auto}',
            '#region-main .sw ~ * h5, [data-region="empty-message"]{display:none!important}'
        ].join('\n');
        document.head.appendChild(el('style', {id: 'sw-stil', text: css}));
    }

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

    // ---------------------------------------------------------------- gemeinsamer Kopf (beide Darstellungen)
    function held(w) {
        var j = jetzt(w, KONFIG), l = leitsatz(w, KONFIG);
        var kasten = el('div', {'class': 'sw-held sw-' + l.art}, [
            zeichenBild(j, 76),
            el('div', {}, [el('small', {text: 'Ihre Stufe jetzt'}), el('strong', {text: KONFIG.stufen[j]}),
                           el('p', {text: l.text})])]);
        if (l.art === 'auf') {
            var funken = el('span', {'class': 'sw-funken', 'aria-hidden': 'true'});
            [[-60, -40], [40, -50], [70, 10], [-40, 40], [10, 55], [-75, 5]].forEach(function (d, i) {
                var f = el('i', {style: 'left:' + (60 + i * 7) + 'px;top:50%;--dx:' + d[0] + 'px;--dy:' + d[1] + 'px;' +
                                 (i % 2 ? 'background:#fff' : '')});
                funken.appendChild(f);
            });
            kasten.appendChild(funken);
        }
        return kasten;
    }

    function schild(richtung) {
        var t = TON[richtung];
        return el('span', {'class': 'sw-schild', style: 'background:' + t[0] + ';color:' + t[1], text: t[2]});
    }

    function karteRueckmeldung(x, i, w) {
        var fb = rueckmeldung(x, KONFIG, w[i + 1] ? w[i + 1].nr : null);
        var art = x.zustand === 'fertig' ? x.richtung : x.zustand;
        var kopf = el('p', {}, [x.richtung ? schild(x.richtung) : null, el('strong', {text: fb.titel})]);
        return el('li', {'class': 'sw-fb ' + art}, [zeichenBild(x.einstieg, 40),
            el('div', {}, [kopf].concat(fb.saetze.map(function (t) { return el('p', {text: t}); })))]);
    }

    // ---------------------------------------------------------------- Darstellung A: Verlauf
    function verlauf(w, breite) {
        var n = w.length, schmal = breite < 560;
        var links = schmal ? 8 : 132, rechts = 10, oben = schmal ? 74 : 64, bahn = schmal ? 96 : 80;
        var spalte = (breite - links - rechts) / Math.max(n, 1);
        var hoehe = oben + bahn * 2 + 92;
        var y = function (st) { return oben + (2 - st) * bahn; };
        var xp = function (i) { return links + spalte * (i + 0.5); };
        var i0 = aktuelle(w), j = jetzt(w, KONFIG);
        var bild = s('svg', {viewBox: '0 0 ' + breite + ' ' + hoehe, width: breite, height: hoehe, role: 'img',
                             'aria-labelledby': 'sw-a-titel sw-a-text'});
        bild.appendChild(s('title', {id: 'sw-a-titel', text: 'Mein Stufenweg als Verlauf'}));
        bild.appendChild(s('desc', {id: 'sw-a-text', text: w.map(function (x, i) {
            return 'Kachel ' + x.nr + ': ' + KONFIG.stufen[x.einstieg] + (x.mittel !== null ? ', ' +
                prozentText(x.mittel) : '') + (i === i0 ? ', hier sind Sie' : '') + '.';
        }).join(' ') + ' Die Karten unter der Grafik beschreiben jede Kachel.'}));
        // Bahnen
        [2, 1, 0].forEach(function (st) {
            var aktiv = st === j;
            bild.appendChild(s('rect', {x: links - 4, y: y(st) - bahn / 2 + 4, width: breite - links - rechts + 4,
                                        height: bahn - 8, rx: 14, fill: aktiv ? '#E6EDFA' : 'transparent'}));
            bild.appendChild(s('line', {x1: links, x2: breite - rechts, y1: y(st), y2: y(st), stroke: '#C3CCDD',
                                        'stroke-width': 1.5, 'stroke-dasharray': '2 6', 'stroke-linecap': 'round'}));
            if (schmal) {
                bild.appendChild(s('text', {x: links + 8, y: y(st) - 33, 'font-size': 12.5,
                                            'font-weight': 700, fill: '#4A5878', 'letter-spacing': '.06em',
                                            text: KONFIG.stufen[st].toUpperCase()}));
            } else {
                bild.appendChild(zeichen(st, 22, y(st), 30));
                bild.appendChild(s('text', {x: 44, y: y(st) + 5, 'font-size': 15, 'font-weight': 700,
                                            fill: aktiv ? BLAU : '#4A5878', text: KONFIG.stufen[st]}));
            }
        });
        // Linie: echte Stücke durchgezogen, der Weg ab der aktuellen Kachel gestrichelt
        var bis = i0 === null ? n - 1 : i0;
        for (var i = 0; i < n - 1; i++) {
            var a = {x: xp(i), y: y(w[i].einstieg)}, b = {x: xp(i + 1), y: y(i + 1 <= bis ? w[i + 1].einstieg : j)};
            var mx = (a.x + b.x) / 2;
            var echt = i + 1 <= bis;
            bild.appendChild(s('path', {d: 'M' + a.x + ' ' + a.y + ' C' + mx + ' ' + a.y + ' ' + mx + ' ' + b.y + ' ' +
                                           b.x + ' ' + b.y, fill: 'none', stroke: echt ? BLAU : '#9AA3B2',
                                        'stroke-width': echt ? 5 : 3, 'stroke-linecap': 'round',
                                        'stroke-dasharray': echt ? '' : '2 8'}));
            if (echt && w[i].richtung) {
                var t = TON[w[i].richtung], bw = schmal ? 84 : 98;
                var cy = (a.y + b.y) / 2 + (a.y === b.y ? -22 : 0);
                bild.appendChild(s('rect', {x: mx - bw / 2, y: cy - 13, width: bw, height: 26, rx: 13, fill: t[0],
                                            stroke: '#FFFFFF', 'stroke-width': 2}));
                bild.appendChild(s('text', {x: mx, y: cy + 5, 'text-anchor': 'middle', 'font-size': schmal ? 12.5 : 14,
                                            'font-weight': 700, fill: t[1], text: t[2]}));
            }
        }
        // Punkte
        w.forEach(function (x, i) {
            var spaeter = i0 !== null && i > i0;
            var st = spaeter ? j : x.einstieg, cx = xp(i), cy = y(st);
            if (i === i0) {
                bild.appendChild(s('circle', {cx: cx, cy: cy, r: 34, fill: GRUEN, 'class': 'sw-halo'}));
                bild.appendChild(s('rect', {x: cx - 52, y: cy - 62, width: 104, height: 24, rx: 12, fill: TINTE}));
                bild.appendChild(s('text', {x: cx, y: cy - 45, 'text-anchor': 'middle', 'font-size': 13.5,
                                            'font-weight': 700, fill: '#FFFFFF', text: 'Sie sind hier'}));
            }
            if (spaeter) {
                bild.appendChild(s('circle', {cx: cx, cy: cy, r: 20, fill: '#FFFFFF', stroke: '#9AA3B2',
                                              'stroke-width': 2, 'stroke-dasharray': '4 4'}));
                bild.appendChild(s('text', {x: cx, y: cy + 5, 'text-anchor': 'middle', 'font-size': 14,
                                            fill: '#6B7385', text: '?'}));
            } else {
                bild.appendChild(s('circle', {cx: cx, cy: cy, r: 27, fill: '#FFFFFF'}));
                bild.appendChild(zeichen(x.einstieg, cx, cy, 46, true));
            }
            var unten = oben + bahn * 2 + 50;
            bild.appendChild(s('text', {x: cx, y: unten, 'text-anchor': 'middle', 'font-size': 15, 'font-weight': 700,
                                        fill: TINTE, text: 'Kachel ' + x.nr}));
            var zeile = x.zustand === 'fertig' ? prozentText(x.mittel) : x.zustand === 'laufend'
                ? x.erledigt + ' von ' + x.anzahl + ' erledigt' : spaeter ? 'kommt noch' : 'jetzt starten';
            bild.appendChild(s('text', {x: cx, y: unten + 21, 'text-anchor': 'middle', 'font-size': 14,
                                        fill: x.zustand === 'fertig' ? BLAU : '#4A5568',
                                        'font-weight': x.zustand === 'fertig' ? 700 : 400, text: zeile}));
        });
        return bild;
    }

    function zeigeVerlauf(ziel, w) {
        var flaeche = el('div', {'class': 'sw-grafik'});
        ziel.appendChild(held(w));
        ziel.appendChild(flaeche);
        var zeichne = function () {
            flaeche.textContent = '';
            flaeche.appendChild(verlauf(w, Math.max(300, Math.floor(flaeche.clientWidth - 8))));
        };
        zeichne();
        var warte;
        window.addEventListener('resize', function () { clearTimeout(warte); warte = setTimeout(zeichne, 150); });
        ziel.appendChild(el('p', {'class': 'sw-legende', text: 'Oben Vertiefung, Mitte Standard, unten Grundlagen. ' +
            'Ab ' + KONFIG.grenzen[1] + '\u00a0% im Durchschnitt der Aufgaben einer Kachel (erster Versuch) geht es eine ' +
            'Stufe höher, unter ' + KONFIG.grenzen[0] + '\u00a0% trainieren Sie eine Stufe tiefer.'}));
        ziel.appendChild(el('h4', {text: 'Ihre Rückmeldungen'}));
        var liste = el('ol', {'class': 'sw-liste'});
        var i0 = aktuelle(w);
        w.forEach(function (x, i) {
            if (i0 === null || i <= i0) {
                liste.appendChild(karteRueckmeldung(x, i, w));
            }
        });
        ziel.appendChild(liste);
    }

    // ---------------------------------------------------------------- Darstellung B: Karten
    function ring(x) {
        var g = 76, r = 30, u = 2 * Math.PI * r, m = 38;
        var b = s('svg', {viewBox: '0 0 ' + g + ' ' + g, width: g, height: g, role: 'img',
                          'aria-label': x.mittel !== null ? 'Ergebnis ' + prozentText(x.mittel)
                              : x.erledigt + ' von ' + x.anzahl + ' Aufgaben erledigt'});
        b.appendChild(s('circle', {cx: m, cy: m, r: r, fill: 'none', stroke: '#E3E8F1', 'stroke-width': 8}));
        var anteil = x.mittel !== null ? x.mittel / 100 : x.anzahl ? x.erledigt / x.anzahl : 0;
        if (anteil > 0) {
            b.appendChild(s('circle', {cx: m, cy: m, r: r, fill: 'none', stroke: x.mittel !== null ? BLAU : '#9AA3B2',
                                       'stroke-width': 8, 'stroke-linecap': 'round',
                                       'stroke-dasharray': (u * anteil) + ' ' + u, transform: 'rotate(-90 38 38)'}));
        }
        KONFIG.grenzen.forEach(function (p) {             // Marken bei 50 % und 85 %
            var w = (p / 100 * 360 - 90) * Math.PI / 180;
            b.appendChild(s('line', {x1: m + 24 * Math.cos(w), y1: m + 24 * Math.sin(w), x2: m + 36 * Math.cos(w),
                                     y2: m + 36 * Math.sin(w), stroke: TINTE, 'stroke-width': 1.6}));
        });
        b.appendChild(s('text', {x: m, y: m + 5, 'text-anchor': 'middle', 'font-size': 15,
                                 'font-weight': 800, fill: TINTE,
                                 text: x.mittel !== null ? Math.round(x.mittel) + '%' : x.erledigt + '/' + x.anzahl}));
        return b;
    }

    function zeigeKarten(ziel, w) {
        ziel.appendChild(held(w));
        var gitter = el('div', {'class': 'sw-karten', role: 'list'});
        var i0 = aktuelle(w), j = jetzt(w, KONFIG);
        w.forEach(function (x, i) {
            var spaeter = i0 !== null && i > i0;
            var karte = el('div', {'class': 'sw-karte' + (i === i0 ? ' jetzt' : '') + (spaeter ? ' spaeter' : ''),
                                   role: 'listitem'});
            if (i === i0) {
                karte.appendChild(el('span', {'class': 'sw-band', text: 'Jetzt dran'}));
            }
            karte.appendChild(el('div', {'class': 'sw-kopf', text: 'Kachel ' + x.nr}));
            karte.appendChild(el('h5', {text: x.titel}));
            var st = spaeter ? j : x.einstieg;
            var mitte = el('div', {'class': 'sw-mitte'}, [zeichenBild(st, 52),
                el('div', {style: 'flex:1 1 auto'}, [el('div', {'class': 'sw-stufe', text: KONFIG.stufen[st]}),
                    el('div', {style: 'font-size:.9em;color:#4A5568', text: spaeter ? 'voraussichtlich' :
                        x.zustand === 'fertig' ? 'Durchschnitt, erster Versuch' : x.zustand === 'laufend'
                            ? 'in Arbeit' : 'hier starten Sie'})]),
                spaeter ? null : ring(x)]);
            karte.appendChild(mitte);
            if (!spaeter) {
                var fb = rueckmeldung(x, KONFIG, w[i + 1] ? w[i + 1].nr : null);
                if (x.richtung) {
                    karte.appendChild(el('p', {style: 'margin:0'}, [schild(x.richtung)]));
                }
                fb.saetze.forEach(function (t) { karte.appendChild(el('p', {style: 'margin:0', text: t})); });
            } else {
                karte.appendChild(el('p', {style: 'margin:0', text: 'Noch nicht begonnen. Ihre Stufe hier ergibt ' +
                    'sich aus Kachel ' + w[i0].nr + '.'}));
            }
            gitter.appendChild(karte);
        });
        ziel.appendChild(gitter);
        ziel.appendChild(el('p', {'class': 'sw-legende', text: 'Ring: Durchschnitt aller Aufgaben der Kachel im ' +
            'ersten Versuch; die Marken stehen bei ' + KONFIG.grenzen[0] + '\u00a0% und ' + KONFIG.grenzen[1] + '\u00a0%. Ab ' +
            KONFIG.grenzen[1] + '\u00a0% geht es eine Stufe höher, unter ' + KONFIG.grenzen[0] + '\u00a0% trainieren Sie ' +
            'eine Stufe tiefer.'}));
    }

    function zeigen(ziel, w) {
        ziel.setAttribute('aria-busy', 'false');
        ziel.textContent = '';
        if (KONFIG.darstellung === 'karten') {
            zeigeKarten(ziel, w);
        } else {
            zeigeVerlauf(ziel, w);
        }
    }

    function start() {
        if (!/\/mod\/data\/view\.php$/.test(window.location.pathname)) {
            return;
        }
        stil();
        var haupt = document.querySelector('#region-main [role="main"]') || document.querySelector('#region-main') ||
            document.body;
        var ziel = el('section', {'class': 'sw', 'aria-live': 'polite', 'aria-busy': 'true'},
                      [el('p', {text: 'Ihr Stufenweg wird geladen …'})]);
        haupt.insertBefore(ziel, haupt.firstChild);
        Array.prototype.forEach.call(document.querySelectorAll('#region-main #action_bar, ' +
            '#region-main .datapreferences, #region-main .tertiary-navigation'), function (x) {
            x.style.setProperty('display', 'none', 'important');
        });
        if (istLehrkraft()) {
            var demo = {};
            var e = 1, ergebnisse = [[100, 100, 67], [100, 100, 33]];
            KONFIG.kacheln.forEach(function (k, i) {
                (k.aufgaben[e] || []).forEach(function (a, m) {
                    if (ergebnisse[i]) {
                        demo[name(a.name)] = ergebnisse[i][m] === undefined ? 100 : ergebnisse[i][m];
                    }
                });
                if (i === 0) {
                    e = 2;
                }
            });
            zeigen(ziel, weg(KONFIG, demo));
            ziel.insertBefore(el('p', {'class': 'alert alert-info', text: 'Lehrkraftansicht: Vorschau mit ' +
                'Beispielwerten. Lernende sehen hier ihren eigenen Weg aus ihren Bewertungen.'}), ziel.firstChild);
            return;
        }
        holeNoten().then(function (noten) {
            zeigen(ziel, weg(KONFIG, noten));
        }).catch(function (e) {
            ziel.setAttribute('aria-busy', 'false');
            ziel.textContent = '';
            ziel.appendChild(el('p', {'class': 'alert alert-warning', text: 'Ihr Stufenweg ließ sich gerade nicht ' +
                'lesen (' + e.message + '). Ihre Ergebnisse stehen auch unter „Bewertungen“.'}));
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', start);
    } else {
        start();
    }
})();
