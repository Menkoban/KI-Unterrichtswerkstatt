/*
 * Sternzähler „⭐ Meine Sterne“ (Lehrkraft 2026-10-26, Profil moodle.sternzaehler; sternzaehler.py).
 *
 * Eine Datenbank-Aktivität ohne Einträge in Abschnitt 0 des Themenkurses. Das Skript (Vorlage „JavaScript“) liest mit
 * der Sitzung der Person, die die Seite öffnet, die Zeile „Kursgesamt“ der eigenen Bewertungsübersicht und zeigt
 * „⭐ n von N Sternen“ mit Balken. Rechnung wie sterne.py und sternebuch.js: Kursgesamt = Summe der Sterne, ganze
 * Sterne abgerundet (15,5 → 15), Anzeige deutsch. Zeigt Moodle das Kursgesamt in Prozent, rechnet das Skript mit dem
 * Höchstwert N zurück. Lehrkräfte sehen einen kurzen Hinweis statt eines Kontostands.
 *
 * Aufbau: reine Rechenlogik (mit node prüfbar: module.exports), dann der Moodle-Teil.
 */
(function () {
    'use strict';

    var KONFIG = /*KONFIG*/{
        "max": 31,
        "kursname": "Themenkurs",
        "farben": ["#08349C", "#7DDE78"]
    }/*/KONFIG*/;

    /** Zahl aus einem Text der Moodle-Oberfläche („12,00“, „12.5“, „1.234,5“); null ohne Zahl („-“). */
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

    /** Ganze Sterne, abgerundet; ein Fließkommarest knapp darunter zählt als ganze Zahl. */
    function ganzeSterne(w) {
        if (w === null || w === undefined || isNaN(Number(w))) {
            return null;
        }
        return Math.max(0, Math.floor(Number(w) + 1e-6));
    }

    /** Sterne aus der Zelle „Bewertung“ des Kursgesamts (Punkte oder Prozent) und dem Höchstwert N. Ohne Note: 0. */
    function sterneAus(note, hoechst) {
        var w = zahl(note);
        if (w === null) {
            return 0;
        }
        if (String(note).indexOf('%') >= 0) {
            w = w * hoechst / 100;
        }
        return Math.min(hoechst, ganzeSterne(w));
    }

    function zahlText(n) {
        return Number(n).toLocaleString('de-DE', {maximumFractionDigits: 0});
    }

    /** „⭐ 1 von 31 Sternen“ */
    function zeile(n, hoechst) {
        return '⭐ ' + zahlText(n) + ' von ' + zahlText(hoechst) + ' Sternen';
    }

    /** Breite des Balkens in Prozent, eine Nachkommastelle. */
    function breite(n, hoechst) {
        return hoechst > 0 ? Math.round(Math.min(n, hoechst) * 1000 / hoechst) / 10 : 0;
    }

    var Logik = {zahl: zahl, ganzeSterne: ganzeSterne, sterneAus: sterneAus, zeile: zeile, breite: breite,
                 zahlText: zahlText, KONFIG: KONFIG};
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

    function el(tag, attribute, kinder) {
        var e = document.createElement(tag);
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

    function text(e) {
        return e ? e.textContent.replace(/\s+/g, ' ').trim() : '';
    }

    function istLehrkraft() {
        return !!document.querySelector('a[href*="/mod/data/field.php"], a[href*="/mod/data/templates.php"], ' +
            'a[href*="/course/modedit.php"]');
    }

    /** Kursgesamt lesen; rechnet Moodle die Bewertungen gerade neu, nach kurzer Zeit noch einmal (höchstens 5-mal). */
    function holeSterne(versuch) {
        versuch = versuch || 0;
        return fetch(WURZEL + '/grade/report/user/index.php?id=' + KURS, {credentials: 'same-origin'})
            .then(function (r) {
                if (!r.ok) {
                    throw new Error('HTTP ' + r.status);
                }
                return r.text();
            }).then(function (t) {
                var doc = new DOMParser().parseFromString(t, 'text/html');
                var titel = doc.querySelector('.column-itemname .courseitem');
                var z = titel && titel.closest('tr');
                if (!z && versuch < 5 && doc.querySelector('.progress, [role="progressbar"]')) {
                    return new Promise(function (fertig) { setTimeout(fertig, 3000); })
                        .then(function () { return holeSterne(versuch + 1); });
                }
                if (!z) {
                    throw new Error('Kursgesamt nicht gefunden');
                }
                return sterneAus(text(z.querySelector('.column-grade')), KONFIG.max);
            });
    }

    function balken(n) {
        var blau = KONFIG.farben[0], gruen = KONFIG.farben[1];
        return el('div', {'class': 'sz-balken', role: 'progressbar', 'aria-valuemin': '0',
                          'aria-valuemax': String(KONFIG.max), 'aria-valuenow': String(n),
                          'aria-label': zeile(n, KONFIG.max),
                          style: 'background:#fff;border:1px solid ' + blau + ';border-radius:6px;height:16px;' +
                                 'max-width:32rem;'},
                  [el('div', {style: 'background:' + gruen + ';border-radius:6px;height:14px;width:' +
                                     breite(n, KONFIG.max) + '%;'})]);
    }

    function start() {
        if (!/\/mod\/data\/view\.php$/.test(window.location.pathname)) {
            return;
        }
        var haupt = document.querySelector('#region-main [role="main"]') || document.querySelector('#region-main') ||
            document.body;
        var ziel = el('section', {'class': 'sz', 'aria-live': 'polite', 'aria-busy': 'true'},
                      [el('p', {text: 'Ihre Sterne werden geladen …'})]);
        haupt.insertBefore(ziel, haupt.firstChild);
        // Datenbank-Teile (keine Einträge, „Eintrag hinzufügen“) braucht hier niemand
        Array.prototype.forEach.call(document.querySelectorAll('#region-main #action_bar, ' +
            '#region-main .datapreferences, #region-main .tertiary-navigation, #region-main h5'), function (x) {
            if (x.id === 'action_bar' || /no entries|keine einträge/i.test(text(x)) || !/^H5$/.test(x.tagName)) {
                x.style.setProperty('display', 'none', 'important');
            }
        });
        if (istLehrkraft()) {
            ziel.setAttribute('aria-busy', 'false');
            ziel.textContent = '';
            ziel.appendChild(el('p', {'class': 'sz-hinweis', text: 'Hier sehen Lernende ihre Sterne in diesem ' +
                'Kurs: „⭐ n von ' + zahlText(KONFIG.max) + ' Sternen“ aus dem eigenen Kursgesamt, ganze Sterne ' +
                'abgerundet. Die Sterne der Klasse zeigen die Bewerterübersicht und das Lernstand-Dashboard.'}));
            return;
        }
        holeSterne().then(function (n) {
            ziel.setAttribute('aria-busy', 'false');
            ziel.textContent = '';
            ziel.appendChild(el('p', {'class': 'sz-zeile', text: zeile(n, KONFIG.max)}));
            ziel.appendChild(el('p', {'class': 'sz-kurs', text: KONFIG.kursname}));
            ziel.appendChild(balken(n));
        }).catch(function (e) {
            ziel.setAttribute('aria-busy', 'false');
            ziel.textContent = '';
            ziel.appendChild(el('p', {'class': 'alert alert-warning', text: 'Ihre Sterne ließen sich gerade nicht ' +
                'lesen (' + e.message + '). Sie stehen auch unter „Bewertungen“ als Kursgesamt.'}));
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', start);
    } else {
        start();
    }
})();
