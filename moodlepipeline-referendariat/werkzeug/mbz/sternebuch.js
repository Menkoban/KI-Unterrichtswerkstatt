/*
 * Sternebuch: Skript der Datenbank-Aktivität (Vorlage „JavaScript“, jstemplate) im Lernfeldkurs.
 *
 * Moodle lädt dieses Skript auf der Listen- und der Eingabeseite der Datenbank (mod/data/view.php und
 * edit.php, über mod/data/js.php im Kopf der Seite). Es läuft im Browser der Person, die die Seite ansieht,
 * mit deren eigener Sitzung: Lernende sehen nur, was sie ohnehin sehen dürfen, die Lehrkraft das, was sie
 * sehen darf. Es gibt keinen Zugangsschlüssel und keine Rechte der Lehrkraft im Quelltext.
 *
 * Was es tut
 *   Lernende: Kontostand = verdiente Sterne aller Themenkurse des Lernfelds (Kursgesamt in der eigenen
 *   Bewertungsübersicht je Kurs, wie sterne.py sie baut: Kursgesamt = Summe der Sterne) plus erhaltene Sterne
 *   (geschenkt, halbiert; Helfer-Sterne) minus verschenkte, eingetauschte und für Klassenbelohnungen gebuchte
 *   Sterne. Dazu Preisliste mit „Buchen“, Klassenbalken (keine Rangliste) und die eigenen Buchungen. Auf der
 *   Eingabeseite verhindert es Buchungen über den verfügbaren Stand.
 *   Lehrkraft (erkannt an Elementen, die nur mit Bearbeitungsrechten erscheinen: Freigabe-Knöpfe, Auswahl
 *   zum Löschen, Links auf Felder und Vorlagen): offene Freigaben mit Prüfung, Konten der Klasse, Ausgabe
 *   abhaken, Helfer-Stern buchen.
 *
 * Was es nicht absichern kann: Es ist eine Anzeige- und Eingabehilfe. Gültig wird jede Buchung erst mit der
 * Freigabe der Lehrkraft (Genehmigung der Datenbank); die Prüfung in der Lehrkraft-Ansicht zeigt dafür an,
 * ob eine Buchung zum Kontostand und zur Preisliste passt.
 *
 * Preise, Klassenbelohnungen und die zählenden Themenkurse stehen in der Seite „Preisliste“ des Kurses
 * (Tabellen, im Editor änderbar, ohne Neubau). Die Werte in KONFIG sind nur der Rückfall.
 *
 * Aufbau: zuerst die reine Rechenlogik (ohne Seite, mit node prüfbar: module.exports), dann der Moodle-Teil.
 */
(function () {
    'use strict';

    // Vom Kursbau eingesetzt (sternebuch.py); hier neutrale Vorgaben für Tests.
    var KONFIG = /*KONFIG*/{
        "preisliste": "Preisliste",
        "themenkurse": [],
        "arten": {"eintauschen": "für mich eintauschen", "verschenken": "verschenken",
                  "anteil": "Anteil an einer Klassenbelohnung", "helfer": "Helfer-Stern"},
        "felder": {"art": "Art", "belohnung": "Belohnung", "sterne": "Sterne", "empfaenger": "Empfänger",
                   "ausgegeben": "Ausgegeben"},
        "helferstern": true,
        "klassenbalken": true,
        "lernendenrolle": 5
    }/*/KONFIG*/;

    // ------------------------------------------------------------------------------------------------ //
    // Rechenlogik (rein)
    // ------------------------------------------------------------------------------------------------ //

    /** Zahl aus einem Text der Moodle-Oberfläche („12,00“, „12.5“, „1.234,5“); null ohne Zahl („-“). */
    function zahl(text) {
        if (text === null || text === undefined) {
            return null;
        }
        var t = String(text).replace(/ /g, ' ');
        var m = t.match(/-?\d[\d.,]*/);
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

    /** Verdiente Sterne eines Kurses als ganze Zahl, abgerundet wie der Sternzähler (Kursgesamt 15,5 → 15);
     *  ein Fließkommarest knapp unter der ganzen Zahl (14,9999999) zählt als ganze Zahl. null bleibt null. */
    function ganzeSterne(wert) {
        if (wert === null || wert === undefined || isNaN(Number(wert))) {
            return null;
        }
        return Math.max(0, Math.floor(Number(wert) + 1e-6));
    }

    /** „1 Stern“, „5 Sterne“ */
    function sterneText(n) {
        return zahlText(n) + (Number(n) === 1 ? ' Stern' : ' Sterne');
    }

    /** Zahl für die Anzeige, deutsch (1.234), ganze Sterne ohne Nachkommastellen. */
    function zahlText(n) {
        return typeof n === 'number' && isFinite(n) ? n.toLocaleString('de-DE', {maximumFractionDigits: 0}) : String(n);
    }

    /** Verschenken: die Hälfte kommt an (abgerundet), der Rest verfällt. 10 ab, 5 an, 5 verfallen. */
    function halbieren(sterne) {
        return Math.floor(Math.max(0, sterne) / 2);
    }

    /** Text einer Buchungsart → Schlüssel (eintauschen, verschenken, anteil, helfer) oder null. */
    function artVon(text, arten) {
        var a = arten || KONFIG.arten;
        var t = String(text || '').trim().toLowerCase();
        for (var k in a) {
            if (Object.prototype.hasOwnProperty.call(a, k) && a[k].toLowerCase() === t) {
                return k;
            }
        }
        return null;
    }

    /** Empfänger „Vorname Name (#123)“ → 123, sonst null. */
    function empfaengerId(text) {
        var m = String(text || '').match(/\(#(\d+)\)\s*$/);
        return m ? parseInt(m[1], 10) : null;
    }

    function empfaengerText(person) {
        return person.name + ' (#' + person.id + ')';
    }

    var AUSGABEN = {eintauschen: 'eingetauscht', verschenken: 'abgegeben', anteil: 'reserviert'};

    function leeresKonto() {
        return {verdient: 0, erhalten: 0, abgegeben: 0, eingetauscht: 0, reserviert: 0, vorgemerkt: 0,
                stand: 0, verfuegbar: 0};
    }

    /**
     * Konten aller Personen. buchungen: [{id, art, belohnung, sterne, empfaenger, von, freigegeben}],
     * verdient: {personId: Sterne}. Nur freigegebene Buchungen zählen; eigene offene Buchungen (eintauschen,
     * verschenken, Anteil) sind „vorgemerkt“ und mindern den verfügbaren Stand. Helfer-Sterne zählen voll,
     * geschenkte halb.
     */
    function konten(buchungen, verdient) {
        var k = {};
        function konto(id) {
            if (id === null || id === undefined) {
                return null;
            }
            if (!k[id]) {
                k[id] = leeresKonto();
            }
            return k[id];
        }
        Object.keys(verdient || {}).forEach(function (id) {
            konto(id).verdient = ganzeSterne(verdient[id]) || 0;
        });
        (buchungen || []).forEach(function (b) {
            var s = gueltigeSterne(b.sterne);
            if (s === null) {
                return;
            }
            if (!b.freigegeben) {
                if (AUSGABEN[b.art]) {
                    konto(b.von).vorgemerkt += s;
                }
                return;
            }
            if (AUSGABEN[b.art]) {
                konto(b.von)[AUSGABEN[b.art]] += s;
            }
            if (b.art === 'verschenken' && b.empfaenger !== null && b.empfaenger !== undefined) {
                konto(b.empfaenger).erhalten += halbieren(s);
            }
            if (b.art === 'helfer' && b.empfaenger !== null && b.empfaenger !== undefined) {
                konto(b.empfaenger).erhalten += s;
            }
        });
        Object.keys(k).forEach(function (id) {
            var x = k[id];
            x.stand = x.verdient + x.erhalten - x.abgegeben - x.eingetauscht - x.reserviert;
            x.verfuegbar = x.stand - x.vorgemerkt;
        });
        return k;
    }

    function kontoVon(alle, id) {
        return (alle && alle[id]) || leeresKonto();
    }

    function gueltigeSterne(s) {
        var n = Number(s);
        return (isFinite(n) && n > 0 && Math.floor(n) === n) ? n : null;
    }

    /**
     * Stand einer Klassenbelohnung. Sie gilt (eine „Runde“ ist erreicht), wenn jede der `anzahl` Lernenden
     * ihren Anteil gebucht hat und die Buchung freigegeben ist. lernende: Liste der Ids (oder null: alle,
     * die gebucht haben, zählen); anzahl: Zahl der Lernenden (Vorgabe: Länge von lernende).
     */
    function klassenstand(buchungen, belohnung, anteil, lernende, anzahl) {
        var zaehler = {};
        var erlaubt = lernende ? lernende.map(String) : null;
        (buchungen || []).forEach(function (b) {
            if (b.art !== 'anteil' || !b.freigegeben || b.belohnung !== belohnung || gueltigeSterne(b.sterne) === null) {
                return;
            }
            var id = String(b.von);
            if (erlaubt && erlaubt.indexOf(id) < 0) {
                return;
            }
            zaehler[id] = (zaehler[id] || 0) + 1;
        });
        var n = anzahl || (lernende ? lernende.length : 0);
        var werte = Object.keys(zaehler).map(function (id) { return zaehler[id]; });
        var erreicht = 0;
        while (n > 0 && werte.filter(function (c) { return c >= erreicht + 1; }).length >= n) {
            erreicht += 1;
        }
        var inRunde = Math.min(n, werte.filter(function (c) { return c > erreicht; }).length);
        return {belohnung: belohnung, anteil: anteil, erreicht: erreicht, inRunde: inRunde, noetig: n,
                fehlt: Math.max(0, n - inRunde), sterneInRunde: inRunde * anteil, sterneNoetig: n * anteil,
                zaehler: zaehler};
    }

    /** Hat `person` ihren Anteil an dieser Runde schon (freigegeben oder offen) gebucht? */
    function anteilSchonGebucht(buchungen, belohnung, person, stand) {
        var gebucht = (buchungen || []).filter(function (b) {
            return b.art === 'anteil' && b.belohnung === belohnung && String(b.von) === String(person);
        }).length;
        return gebucht > stand.erreicht;
    }

    function preisVon(liste, name) {
        for (var i = 0; i < (liste || []).length; i++) {
            if (liste[i].name === name) {
                return liste[i];
            }
        }
        return null;
    }

    /**
     * Gründe gegen eine Buchung (leer = in Ordnung). b: {art, belohnung, sterne, empfaenger, von};
     * verfuegbar: verfügbarer Stand der buchenden Person ohne diese Buchung; preise: preiseLesen(…);
     * kontext: {buchungen, lernende (Ids oder null), lehrkraft (bucht die Lehrkraft?)}.
     */
    function pruefeBuchung(b, verfuegbar, preise, kontext) {
        var g = [];
        var k = kontext || {};
        var s = gueltigeSterne(b.sterne);
        if (!b.art) {
            return ['Bitte wählen Sie eine Art der Buchung.'];
        }
        if (s === null) {
            g.push('Die Zahl der Sterne muss eine ganze Zahl größer als 0 sein.');
        }
        if (b.art === 'eintauschen') {
            var p = preisVon(preise.fuerMich, b.belohnung);
            if (!p) {
                g.push('„' + (b.belohnung || '') + '“ steht nicht in der Preisliste.');
            } else if (s !== null && s !== p.sterne) {
                g.push('„' + p.name + '“ kostet laut Preisliste ' + sterneText(p.sterne) + '.');
            }
        } else if (b.art === 'verschenken') {
            if (s !== null && s % 2 !== 0) {
                g.push('Verschenken geht nur mit einer geraden Zahl: die Hälfte kommt an.');
            }
            if (b.empfaenger === null || b.empfaenger === undefined) {
                g.push('Bitte wählen Sie, wem Sie die Sterne schenken.');
            } else if (String(b.empfaenger) === String(b.von)) {
                g.push('Sich selbst kann man keine Sterne schenken.');
            } else if (k.lernende && k.lernende.map(String).indexOf(String(b.empfaenger)) < 0) {
                g.push('Die Person ist nicht in der Klasse.');
            }
        } else if (b.art === 'anteil') {
            var kp = preisVon(preise.klasse, b.belohnung);
            if (!kp) {
                g.push('„' + (b.belohnung || '') + '“ steht nicht in der Preisliste der Klasse.');
            } else {
                if (s !== null && s !== kp.anteil) {
                    g.push('Der Anteil an „' + kp.name + '“ ist ' + sterneText(kp.anteil) + '.');
                }
                if (verfuegbar < kp.ab) {
                    g.push('Für „' + kp.name + '“ braucht jede Person mindestens ' + sterneText(kp.ab) +
                           '; verfügbar sind ' + zahlText(verfuegbar) + '.');
                }
                var stand = klassenstand(k.buchungen, kp.name, kp.anteil, k.lernende, k.anzahl);
                if (anteilSchonGebucht((k.buchungen || []).filter(function (x) { return x.id !== b.id; }),
                                       kp.name, b.von, stand)) {
                    g.push('Ihren Anteil an „' + kp.name + '“ haben Sie für diese Runde schon gebucht.');
                }
            }
        } else if (b.art === 'helfer') {
            if (!k.lehrkraft) {
                g.push('Helfer-Sterne bucht nur die Lehrkraft.');
            }
            if (b.empfaenger === null || b.empfaenger === undefined) {
                g.push('Bitte wählen Sie, wer den Helfer-Stern bekommt.');
            }
        } else {
            g.push('Unbekannte Art der Buchung.');
        }
        if (AUSGABEN[b.art] && s !== null && s > verfuegbar) {
            g.push('Dafür reicht der Kontostand nicht: verfügbar sind ' + sterneText(verfuegbar) + '.');
        }
        return g;
    }

    /**
     * Preisliste aus den Tabellen der Seite „Preisliste“. tabellen: [[[Zelle, …], …], …] (erste Zeile =
     * Kopf), text: ganzer Text der Seite. Erkannt am Kopf: „Kurzname“ = zählende Themenkurse; „Anteil“ =
     * Klassenbelohnungen (Spalte „mindestens“ = Bedingung je Person); sonst „Sterne“ = Belohnungen für sich.
     * Optional im Text: „Lernende in der Klasse: 18“.
     */
    function preiseLesen(tabellen, text) {
        var aus = {fuerMich: [], klasse: [], kurse: [], lernende: null, fehler: []};
        function spalte(kopf, muster) {
            for (var i = 0; i < kopf.length; i++) {
                if (muster.test(kopf[i])) {
                    return i;
                }
            }
            return -1;
        }
        (tabellen || []).forEach(function (t) {
            if (!t || t.length < 2) {
                return;
            }
            var kopf = t[0].map(function (z) { return String(z || '').trim().toLowerCase(); });
            var name = Math.max(0, spalte(kopf, /belohnung|lernsituation|kurs\b/));
            var hinweis = spalte(kopf, /hinweis/);
            var kurz = spalte(kopf, /kurzname/);
            var anteil = spalte(kopf, /anteil/);
            var ab = spalte(kopf, /mindestens|\bab\b/);
            var sterne = spalte(kopf, /sterne/);
            t.slice(1).forEach(function (zeile) {
                var z = zeile.map(function (c) { return String(c || '').replace(/\s+/g, ' ').trim(); });
                if (!z.join('')) {
                    return;
                }
                if (kurz >= 0) {
                    if (z[kurz]) {
                        aus.kurse.push({name: z[name] || z[kurz], kurzname: z[kurz]});
                    }
                } else if (anteil >= 0) {
                    var a = zahl(z[anteil]);
                    var m = ab >= 0 ? zahl(z[ab]) : 0;
                    if (a === null || m === null) {
                        aus.fehler.push('Zeile „' + z.join(' | ') + '“: keine Zahl für Anteil oder Mindestzahl');
                    } else {
                        aus.klasse.push({name: z[name], ab: m, anteil: a, hinweis: hinweis >= 0 ? z[hinweis] : ''});
                    }
                } else if (sterne >= 0) {
                    var p = zahl(z[sterne]);
                    if (p === null) {
                        aus.fehler.push('Zeile „' + z.join(' | ') + '“: keine Zahl für Sterne');
                    } else {
                        aus.fuerMich.push({name: z[name], sterne: p, hinweis: hinweis >= 0 ? z[hinweis] : ''});
                    }
                }
            });
        });
        var m = String(text || '').match(/Lernende in der Klasse:\s*(\d+)/i);
        if (m) {
            aus.lernende = parseInt(m[1], 10);
        }
        return aus;
    }

    /** Rolle aus dem Text einer Rollenzelle: true Lernende, false Lehrkraft (oder andere Rolle), null unbekannt. */
    function lernendNachText(rtext) {
        if (/lehr|trainer|teacher|manager|kursersteller|course creator/i.test(rtext)) {
            return false;
        }
        if (/teilnehmer|student|lernend|schüler/i.test(rtext)) {
            return true;
        }
        return rtext ? false : null;
    }

    var Logik = {zahl: zahl, ganzeSterne: ganzeSterne, zahlText: zahlText, sterneText: sterneText, halbieren: halbieren, artVon: artVon, empfaengerId: empfaengerId,
                 empfaengerText: empfaengerText, konten: konten, kontoVon: kontoVon, klassenstand: klassenstand,
                 anteilSchonGebucht: anteilSchonGebucht, pruefeBuchung: pruefeBuchung, preiseLesen: preiseLesen,
                 lernendNachText: lernendNachText,
                 KONFIG: KONFIG};
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = Logik;
        return;
    }

    // ------------------------------------------------------------------------------------------------ //
    // Moodle-Teil: Daten aus der eigenen Sitzung lesen und anzeigen
    // ------------------------------------------------------------------------------------------------ //
    var M = window.M || {};
    var CFG = M.cfg || {};
    var WURZEL = CFG.wwwroot || '';
    var ICH = CFG.userId;
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

    function holeDoc(url) {
        return fetch(url, {credentials: 'same-origin'}).then(function (r) {
            if (!r.ok) {
                throw new Error('HTTP ' + r.status + ' bei ' + url);
            }
            return r.text().then(function (t) {
                var d = new DOMParser().parseFromString(t, 'text/html');
                d.endUrl = r.url;
                return d;
            });
        });
    }

    function text(e) {
        return e ? e.textContent.replace(/\s+/g, ' ').trim() : '';
    }

    function parameter() {
        return new URLSearchParams(window.location.search);
    }

    /** Liste der Datenbank (alle sichtbaren Einträge auf einer Seite) und Ziel für neue Einträge. */
    function orte() {
        var p = parameter();
        var d = p.get('d');
        var cm = p.get('id');
        var formD = document.querySelector('form input[name="d"]');
        if (!d && formD) {
            d = formD.value;
        }
        var schl = d ? 'd=' + encodeURIComponent(d) : 'id=' + encodeURIComponent(cm || CFG.contextInstanceId || '');
        return {
            liste: WURZEL + '/mod/data/view.php?' + schl + '&perpage=1000&mode=list',
            neu: WURZEL + '/mod/data/edit.php?' + schl
        };
    }

    /** Eine Buchung aus einer Zeile der Listenvorlage (Klassen sb-…, siehe sternebuch.py). */
    function buchungAus(z) {
        var nutzer = z.querySelector('.sb-von a[href*="/user/view.php"]');
        var id = nutzer ? (nutzer.getAttribute('href').match(/[?&]id=(\d+)/) || [])[1] : null;
        var bearbeiten = z.querySelector('.sb-aktionen .edit a, .sb-aktionen a[href*="/mod/data/edit.php"]');
        var freigeben = z.querySelector('.sb-aktionen .approve a');
        return {
            id: text(z.querySelector('.sb-id')),
            art: artVon(text(z.querySelector('.sb-art'))),
            belohnung: text(z.querySelector('.sb-belohnung')),
            sterne: zahl(text(z.querySelector('.sb-sterne'))),
            empfaenger: empfaengerId(text(z.querySelector('.sb-empfaenger'))),
            empfaengerName: text(z.querySelector('.sb-empfaenger')).replace(/\s*\(#\d+\)\s*$/, ''),
            ausgegeben: text(z.querySelector('.sb-ausgegeben')) !== '',
            von: id !== null && id !== undefined ? parseInt(id, 10) : null,
            vonName: text(nutzer),
            zeit: text(z.querySelector('.sb-zeit')),
            // ##approvalstatusclass##: „approved“ oder „notapproved“; ohne Genehmigung leer (dann gültig)
            freigegeben: !z.classList.contains('notapproved'),
            bearbeiten: bearbeiten ? bearbeiten.href : null,
            freigeben: freigeben ? freigeben.href : null
        };
    }

    function buchungenAus(doc) {
        return Array.prototype.map.call(doc.querySelectorAll('.sb-eintrag'), buchungAus);
    }

    function istLehrkraft(doc) {
        return !!doc.querySelector('.sb-eintrag .approve a, .sb-eintrag .disapprove a, ' +
            '.sb-eintrag input.recordcheckbox, a[href*="/mod/data/field.php"], a[href*="/mod/data/templates.php"]');
    }

    function tabellenAus(doc) {
        var bereich = doc.querySelector('#region-main') || doc.body;
        return Array.prototype.map.call(bereich.querySelectorAll('table'), function (t) {
            return Array.prototype.map.call(t.querySelectorAll('tr'), function (tr) {
                return Array.prototype.map.call(tr.querySelectorAll('th, td'), text);
            });
        });
    }

    /** Seite „Preisliste“ des Kurses über die Liste aller Seiten (unabhängig vom Kursformat). */
    function holePreise() {
        return holeDoc(WURZEL + '/mod/page/index.php?id=' + KURS).then(function (doc) {
            var links = Array.prototype.filter.call(doc.querySelectorAll('a[href*="/mod/page/view.php"]'),
                function (a) { return text(a).indexOf(KONFIG.preisliste) >= 0; });
            if (!links.length) {
                throw new Error('Seite „' + KONFIG.preisliste + '“ nicht gefunden');
            }
            return holeDoc(links[0].href);
        }).then(function (doc) {
            var bereich = doc.querySelector('#region-main') || doc.body;
            var p = preiseLesen(tabellenAus(doc), text(bereich));
            if (!p.kurse.length) {
                p.kurse = KONFIG.themenkurse.slice();
            }
            return p;
        });
    }

    /** Kurs-Ids der Themenkurse über die eigene Kursliste (Webdienst des Dashboards), sonst über den Kurznamen. */
    function kursIds(kurse) {
        var aufruf = [{index: 0, methodname: 'core_course_get_enrolled_courses_by_timeline_classification',
                       args: {offset: 0, limit: 0, classification: 'allincludinghidden', sort: 'fullname'}}];
        return fetch(WURZEL + '/lib/ajax/service.php?sesskey=' + encodeURIComponent(CFG.sesskey) +
                     '&info=core_course_get_enrolled_courses_by_timeline_classification',
            {method: 'POST', credentials: 'same-origin', headers: {'Content-Type': 'application/json'},
             body: JSON.stringify(aufruf)})
            .then(function (r) { return r.json(); })
            .then(function (antwort) {
                var liste = (antwort && antwort[0] && !antwort[0].error && antwort[0].data.courses) || [];
                var je = {};
                liste.forEach(function (c) { je[c.shortname] = c.id; });
                return je;
            })
            .catch(function () { return {}; })
            .then(function (je) {
                return Promise.all(kurse.map(function (k) {
                    if (je[k.kurzname]) {
                        return Object.assign({}, k, {id: je[k.kurzname]});
                    }
                    return holeDoc(WURZEL + '/course/view.php?name=' + encodeURIComponent(k.kurzname))
                        .then(function (doc) {
                            var m = (doc.body.className || '').match(/\bcourse-(\d+)\b/);
                            return Object.assign({}, k, {id: m ? parseInt(m[1], 10) : null});
                        })
                        .catch(function () { return Object.assign({}, k, {id: null}); });
                }));
            });
    }

    /** Eigene verdiente Sterne eines Themenkurses: Zeile Kursgesamt der eigenen Bewertungsübersicht. */
    function verdientIch(kurs) {
        if (!kurs.id) {
            return Promise.resolve(null);
        }
        return holeDoc(WURZEL + '/grade/report/user/index.php?id=' + kurs.id).then(function (doc) {
            var titel = doc.querySelector('.column-itemname .courseitem');
            var zeile = titel && titel.closest('tr');
            if (!zeile) {
                return null;
            }
            var note = text(zeile.querySelector('.column-grade'));
            var wert = zahl(note);
            if (wert !== null && note.indexOf('%') >= 0) {
                var bereich = text(zeile.querySelector('.column-range')).split(/[^\d.,]+/).filter(Boolean);
                var hoechst = bereich.length ? zahl(bereich[bereich.length - 1]) : null;
                wert = hoechst === null ? null : wert * hoechst / 100;
            }
            return wert === null ? 0 : ganzeSterne(wert);
        }).catch(function () { return null; });
    }

    /** Lehrkraft: verdiente Sterne aller Lernenden eines Themenkurses (Spalte Kursgesamt der Bewerterübersicht). */
    function verdientAlle(kurs) {
        if (!kurs.id) {
            return Promise.resolve(null);
        }
        return holeDoc(WURZEL + '/grade/report/grader/index.php?id=' + kurs.id).then(function (doc) {
            var je = {};
            Array.prototype.forEach.call(doc.querySelectorAll('tr[data-uid]'), function (tr) {
                var zelle = tr.querySelector('td.course');
                if (zelle) {
                    je[tr.getAttribute('data-uid')] = ganzeSterne(zahl(text(zelle))) || 0;
                }
            });
            return je;
        }).catch(function () { return null; });
    }

    /** Anzeigename aus dem Link zum Profil, ohne Avatar-Initialen und Bilder. */
    function nameAus(a) {
        var kopie = a.cloneNode(true);
        Array.prototype.forEach.call(kopie.querySelectorAll('.userinitials, img, .userpicture'), function (x) {
            x.parentNode.removeChild(x);
        });
        return text(kopie) || (a.querySelector('[aria-label]') || {getAttribute: function () { return ''; }})
            .getAttribute('aria-label') || text(a);
    }

    /** Teilnehmende des Lernfeldkurses; Lernende an der Rolle: Lehrkräfte sehen die bearbeitbare Rollenzelle
     *  (data-itemtype="user_roles"), Lernende nur den Rollentext in der Spalte „Rollen“ (Kopfzeile). Ist keine Rolle
     *  lesbar, zählt niemand als Lehrkraft, außer wer die eigene Lehrkraftansicht hat (KONFIG). */
    function holeTeilnehmende() {
        return holeDoc(WURZEL + '/user/index.php?id=' + KURS + '&perpage=5000').then(function (doc) {
            var alle = [];
            var gesehen = {};
            var mitRolle = false;
            var spalte = -1;
            Array.prototype.forEach.call(doc.querySelectorAll('thead th'), function (th, i) {
                if (/^\s*(rollen?|roles?)\b/i.test(text(th))) {
                    spalte = i;
                }
            });
            Array.prototype.forEach.call(doc.querySelectorAll('tr'), function (tr) {
                var a = tr.querySelector('a[href*="/user/view.php?id="]');
                if (!a) {
                    return;
                }
                var id = parseInt((a.getAttribute('href').match(/[?&]id=(\d+)/) || [])[1], 10);
                if (!id || gesehen[id]) {
                    return;
                }
                gesehen[id] = true;
                var r = tr.querySelector('[data-itemtype="user_roles"]');
                var lernend = null;
                if (r) {
                    mitRolle = true;
                    var ids = [];
                    try {
                        ids = JSON.parse(r.getAttribute('data-value') || '[]').map(String);
                    } catch (e) {
                        ids = [];
                    }
                    // Lernendenrolle und keine Lehrkraftrolle daneben (Rollentext); ohne Ids nur der Text
                    lernend = ids.length ? ids.indexOf(String(KONFIG.lernendenrolle)) >= 0 &&
                        !/lehr|trainer|teacher|manager/i.test(text(r)) : lernendNachText(text(r)) === true;
                } else if (spalte >= 0 && tr.children[spalte]) {
                    var t = lernendNachText(text(tr.children[spalte]));
                    if (t !== null) {
                        mitRolle = true;
                        lernend = t;
                    }
                }
                alle.push({id: id, name: nameAus(a), lernend: lernend});
            });
            var lernende = alle.filter(function (p) { return mitRolle ? p.lernend === true : true; });
            return {alle: alle, lernende: lernende};
        }).catch(function () { return {alle: [], lernende: []}; });
    }

    /** Ids der Lernenden, oder null, wenn die Teilnehmerliste nicht lesbar war (dann keine Prüfung darauf). */
    function idsOderNull(personen) {
        return personen && personen.length ? personen.map(function (p) { return p.id; }) : null;
    }

    function balken(wert, hoechst, beschriftung) {
        var anteil = hoechst > 0 ? Math.min(100, Math.round(wert * 100 / hoechst)) : 0;
        return el('div', {'class': 'sb-balken', role: 'progressbar', 'aria-valuemin': '0',
                          'aria-valuemax': String(hoechst), 'aria-valuenow': String(wert),
                          'aria-label': beschriftung}, [
            el('div', {'class': 'sb-balken-fuellung', style: 'width:' + anteil + '%'})
        ]);
    }

    function tabelle(kopf, zeilen, beschriftung) {
        return el('table', {'class': 'table table-sm sb-tabelle'}, [
            beschriftung ? el('caption', {text: beschriftung}) : null,
            el('thead', {}, [el('tr', {}, kopf.map(function (k) { return el('th', {scope: 'col', text: k}); }))]),
            el('tbody', {}, zeilen.map(function (z) {
                return el('tr', {}, z.map(function (c) {
                    return el('td', {}, [typeof c === 'object' && c !== null ? c : zahlText(c)]);
                }));
            }))
        ]);
    }

    function knopf(href, beschriftung, aktiv, titel) {
        if (!aktiv) {
            return el('span', {'class': 'btn btn-secondary btn-sm disabled', 'aria-disabled': 'true',
                               title: titel || '', text: beschriftung});
        }
        return el('a', {'class': 'btn btn-primary btn-sm', href: href, text: beschriftung});
    }

    function klassenbalken(buchungen, preise, lernendeIds, anzahl) {
        if (!KONFIG.klassenbalken || !preise.klasse.length) {
            return null;
        }
        return el('div', {'class': 'sb-klasse'}, [el('h4', {text: 'Klassenbalken'})].concat(
            preise.klasse.map(function (k) {
                var st = klassenstand(buchungen, k.name, k.anteil, lernendeIds, anzahl);
                var titel = k.name + ': ' + st.inRunde + ' von ' + st.noetig + ' Anteilen gebucht' +
                    (st.erreicht ? ' (schon ' + st.erreicht + '-mal erreicht)' : '');
                return el('div', {'class': 'sb-klasse-zeile'}, [
                    el('p', {text: titel}), balken(st.inRunde, st.noetig, titel),
                    el('p', {'class': 'sb-klein', text: 'Gemeinsam ' + st.sterneInRunde + ' von ' +
                        st.sterneNoetig + ' Sternen. Die Belohnung gilt, wenn alle ihren Anteil gebucht haben.'})
                ]);
            })));
    }

    function bereitstellen() {
        var haupt = document.querySelector('#region-main [role="main"]') || document.querySelector('#region-main') ||
            document.body;
        var ziel = el('section', {'class': 'sb', 'aria-live': 'polite', 'aria-busy': 'true'},
                      [el('p', {text: 'Das Sternebuch lädt …'})]);
        haupt.insertBefore(ziel, haupt.firstChild);
        return ziel;
    }

    function fehlerAnzeigen(ziel, e) {
        ziel.setAttribute('aria-busy', 'false');
        ziel.textContent = '';
        ziel.appendChild(el('p', {'class': 'alert alert-warning',
            text: 'Das Sternebuch konnte nicht alles laden (' + (e && e.message ? e.message : e) +
                  '). Die Liste darunter zeigt die Buchungen; bitte sagen Sie Ihrer Lehrkraft Bescheid.'}));
    }

    // -- Ansicht für Lernende ------------------------------------------------------------------------ //
    function ansichtLernende(ziel, d) {
        var ich = kontoVon(d.konten, ICH);
        var lernendeIds = idsOderNull(d.teilnehmende.lernende);
        var anzahl = d.preise.lernende || (lernendeIds ? lernendeIds.length : 0);
        var verdientZeilen = d.kurse.map(function (k, i) {
            var w = d.verdient[i];
            return [k.name, w === null ? 'nicht lesbar' : w];
        });
        var kinder = [
            el('h3', {text: 'Ihr Sternekonto'}),
            el('p', {'class': 'sb-stand'}, [el('span', {'class': 'sb-gross', text: '⭐ ' + zahlText(ich.verfuegbar)}),
                (ich.verfuegbar === 1 ? ' Stern kann' : ' Sterne können') + ' Sie einsetzen.']),
            tabelle(['Posten', 'Sterne'], verdientZeilen.concat([
                ['Erhalten (geschenkt und Helfer-Sterne)', ich.erhalten],
                ['Verschenkt', ich.abgegeben], ['Eingetauscht', ich.eingetauscht],
                ['Für Klassenbelohnungen gebucht', ich.reserviert],
                ['Kontostand', ich.stand], ['Noch nicht freigegeben', ich.vorgemerkt]
            ]), 'So setzt sich Ihr Kontostand zusammen'),
            el('p', {'class': 'sb-klein', text: 'Ihre Medaillen in den Themenkursen richten sich nach den ' +
                'verdienten Sternen; Eintauschen und Verschenken ändern sie nicht.'}),
            klassenbalken(d.buchungen, d.preise, lernendeIds, anzahl),
            el('h4', {text: 'Preisliste'}),
            tabelle(['Belohnung', 'Sterne', 'Hinweis', ''], d.preise.fuerMich.map(function (p) {
                var genug = ich.verfuegbar >= p.sterne;
                return [p.name, p.sterne, p.hinweis || '', knopf(d.orte.neu + '#art=eintauschen&belohnung=' +
                    encodeURIComponent(p.name), 'Eintauschen', genug, genug ? '' : 'Noch nicht genug Sterne')];
            }), 'Belohnungen für Sie'),
            d.preise.klasse.length ? tabelle(['Belohnung', 'Jede Person hat mindestens', 'Anteil', ''],
                d.preise.klasse.map(function (p) {
                    var st = klassenstand(d.buchungen, p.name, p.anteil, lernendeIds, anzahl);
                    var schon = anteilSchonGebucht(d.buchungen, p.name, ICH, st);
                    var ok = ich.verfuegbar >= Math.max(p.ab, p.anteil) && !schon;
                    return [p.name, p.ab, p.anteil, knopf(d.orte.neu + '#art=anteil&belohnung=' +
                        encodeURIComponent(p.name), 'Anteil buchen', ok,
                        schon ? 'Schon gebucht' : 'Noch nicht genug Sterne')];
                }), 'Belohnungen für die ganze Klasse') : null,
            el('p', {}, [knopf(d.orte.neu + '#art=verschenken', 'Sterne verschenken', ich.verfuegbar >= 2,
                'Noch nicht genug Sterne'), ' ',
                el('span', {'class': 'sb-klein', text: 'Beim Verschenken kommt die Hälfte an: 10 ab, 5 kommen an.'})]),
            el('h4', {text: 'Ihre Buchungen'}),
            tabelle(['Art', 'Was', 'Sterne', 'Stand'], d.buchungen.filter(function (b) {
                return String(b.von) === String(ICH) || String(b.empfaenger) === String(ICH);
            }).map(function (b) {
                var an = String(b.empfaenger) === String(ICH) && String(b.von) !== String(ICH);
                var was = b.art === 'verschenken' ? (an ? 'von ' + b.vonName : 'an ' + b.empfaengerName)
                    : (b.art === 'helfer' ? 'Helfer-Stern' : b.belohnung);
                var sterne = an ? '+' + (b.art === 'verschenken' ? halbieren(b.sterne) : b.sterne) : b.sterne;
                var stand = !b.freigegeben ? 'wartet auf Freigabe' : (b.ausgegeben ? 'ausgegeben' : 'gültig');
                return [KONFIG.arten[b.art] || '?', was, sterne, stand];
            }))
        ];
        ziel.textContent = '';
        kinder.forEach(function (k) { if (k) { ziel.appendChild(k); } });
        ziel.setAttribute('aria-busy', 'false');
        // Die Rohliste der Datenbank zeigt auch Buchungen anderer; für Lernende reicht die eigene Übersicht.
        Array.prototype.forEach.call(document.querySelectorAll('.sb-eintrag'), function (z) {
            var b = buchungAus(z);
            if (String(b.von) !== String(ICH) && String(b.empfaenger) !== String(ICH)) {
                z.style.display = 'none';
            }
        });
    }

    // -- Ansicht für die Lehrkraft ------------------------------------------------------------------- //
    function ansichtLehrkraft(ziel, d) {
        var lernende = d.teilnehmende.lernende;
        var lernendeIds = idsOderNull(lernende);
        var anzahl = d.preise.lernende || (lernendeIds ? lernendeIds.length : 0);
        var name = {};
        d.teilnehmende.alle.forEach(function (p) { name[p.id] = p.name; });
        var offen = d.buchungen.filter(function (b) { return !b.freigegeben; });
        var kontext = {buchungen: d.buchungen, lernende: idsOderNull(lernende), anzahl: anzahl};
        var kinder = [
            el('h3', {text: 'Sternebuch: Ansicht für die Lehrkraft'}),
            el('p', {}, [KONFIG.helferstern ? knopf(d.orte.neu + '#art=helfer', 'Helfer-Stern buchen', true) : null]),
            el('h4', {text: 'Offene Freigaben (' + offen.length + ')'}),
            offen.length ? tabelle(['Person', 'Art', 'Was', 'Sterne', 'Prüfung', ''], offen.map(function (b) {
                var k = kontoVon(d.konten, b.von);
                var lehr = lernendeIds ? lernendeIds.indexOf(b.von) < 0 : false;   // bucht jemand außerhalb der Lernenden
                var gruende = pruefeBuchung(b, k.verfuegbar + (AUSGABEN[b.art] ? (gueltigeSterne(b.sterne) || 0) : 0),
                    d.preise, Object.assign({lehrkraft: lehr}, kontext));
                if (!d.verdientBekannt) {
                    gruende.push('Verdiente Sterne nicht lesbar: Kontostand ungeprüft.');
                }
                var was = (b.art === 'verschenken' || b.art === 'helfer')
                    ? 'an ' + (b.empfaengerName || '?') : b.belohnung;
                return [b.vonName, KONFIG.arten[b.art] || '?', was, b.sterne,
                    gruende.length ? el('span', {'class': 'sb-warnung', text: gruende.join(' ')})
                        : el('span', {'class': 'sb-ok', text: 'passt'}),
                    b.freigeben ? el('a', {href: b.freigeben, text: 'Freigeben'}) : ''];
            })) : el('p', {text: 'Keine offenen Buchungen.'}),
            klassenbalken(d.buchungen, d.preise, lernendeIds, anzahl),
            el('h4', {text: 'Konten der Klasse'}),
            tabelle(['Person', 'Verdient', 'Erhalten', 'Verschenkt', 'Eingetauscht', 'Klasse', 'Stand', 'Offen'],
                lernende.slice().sort(function (a, b) { return a.name.localeCompare(b.name, 'de'); })
                    .map(function (p) {
                        var k = kontoVon(d.konten, p.id);
                        return [p.name, d.verdientBekannt ? k.verdient : '?', k.erhalten, k.abgegeben,
                            k.eingetauscht, k.reserviert, d.verdientBekannt ? k.stand : '?', k.vorgemerkt];
                    }), 'Alphabetisch, keine Rangliste'),
            el('h4', {text: 'Ausgabe abhaken'}),
            (function () {
                // Eintauschen und Anteile an erreichten Klassenbelohnungen (die Klasse hat sie zusammen)
                var erreicht = {};
                (d.preise.klasse || []).forEach(function (k) {
                    erreicht[k.name] = klassenstand(d.buchungen, k.name, k.anteil, lernendeIds, anzahl).erreicht > 0;
                });
                var faellig = d.buchungen.filter(function (b) {
                    return b.freigegeben && !b.ausgegeben &&
                        (b.art === 'eintauschen' || (b.art === 'anteil' && erreicht[b.belohnung]));
                });
                if (!faellig.length) {
                    return el('p', {text: 'Nichts auszugeben.'});
                }
                return tabelle(['Person', 'Belohnung', 'Gebucht', ''], faellig.map(function (b) {
                    return [b.vonName, b.belohnung + (b.art === 'anteil' ? ' (Klasse)' : ''), b.zeit,
                        b.bearbeiten ? el('a', {href: b.bearbeiten + '#ausgabe', text: 'Ausgabe abhaken'}) : ''];
                }));
            })()
        ];
        ziel.textContent = '';
        kinder.forEach(function (k) { if (k) { ziel.appendChild(k); } });
        ziel.setAttribute('aria-busy', 'false');
        // Rohliste der Datenbank: eingeklappt, auf Wunsch sichtbar (Freigeben geht oben in der Tabelle)
        var roh = document.querySelector('.sb-liste');
        if (roh) {
            roh.classList.add('sb-liste-zu');
            var zeigen = el('button', {type: 'button', 'class': 'btn btn-secondary btn-sm',
                                       'aria-expanded': 'false', text: 'Alle Buchungen als Liste zeigen'});
            zeigen.addEventListener('click', function () {
                var zu = roh.classList.toggle('sb-liste-zu');
                zeigen.setAttribute('aria-expanded', zu ? 'false' : 'true');
                zeigen.textContent = zu ? 'Alle Buchungen als Liste zeigen' : 'Liste ausblenden';
            });
            roh.parentNode.insertBefore(el('p', {}, [zeigen]), roh);
        }
    }

    // -- Eingabeseite -------------------------------------------------------------------------------- //
    function feld(klasse) {
        return document.querySelector('.sb-formular .sb-feld-' + klasse);
    }

    /** Das Texteingabefeld eines Datenbankfelds (nicht ein verstecktes Hilfsfeld). */
    function sichtbaresFeld(f) {
        return f.querySelector('input[type="text"], input[type="number"], input:not([type="hidden"])') ||
            f.querySelector('input');
    }

    function eingabe(d) {
        var form = document.querySelector('.sb-formular') && document.querySelector('.sb-formular').closest('form');
        if (!form) {
            return;
        }
        var artWahl = feld('art').querySelector('select');
        var belohnung = sichtbaresFeld(feld('belohnung'));
        var sterne = sichtbaresFeld(feld('sterne'));
        var empfaenger = sichtbaresFeld(feld('empfaenger'));
        var ausgabe = feld('ausgegeben');
        var ridFeld = form.querySelector('input[name="rid"]');
        var rid = ridFeld && ridFeld.value !== '0' ? ridFeld.value : null;
        var lehr = d.lehrkraft;
        var meldung = el('div', {'class': 'sb-meldung', role: 'status', 'aria-live': 'polite'});
        feld('art').parentNode.insertBefore(meldung, feld('art'));
        var ohneMich = d.buchungen.filter(function (b) { return !rid || b.id !== rid; });
        var von = rid ? ((d.buchungen.filter(function (b) { return b.id === rid; })[0] || {}).von || ICH) : ICH;
        var konto = kontoVon(konten(ohneMich, d.verdientJe), von);

        // Auswahl statt freier Eingabe: Belohnung aus der Preisliste, Empfänger aus der Teilnehmerliste.
        var belohnungWahl = el('select', {'class': 'form-select', 'aria-label': 'Belohnung wählen'});
        belohnung.style.setProperty('display', 'none', 'important');   // Moodle: d-inline ist !important
        belohnung.parentNode.insertBefore(belohnungWahl, belohnung);
        var empfaengerWahl = el('select', {'class': 'form-select', 'aria-label': 'Person wählen'});
        empfaenger.style.setProperty('display', 'none', 'important');   // Moodle: d-inline ist !important
        empfaenger.parentNode.insertBefore(empfaengerWahl, empfaenger);
        var personen = (lehr ? d.teilnehmende.lernende : d.teilnehmende.lernende.filter(function (p) {
            return p.id !== ICH;
        })).slice().sort(function (a, b) { return a.name.localeCompare(b.name, 'de'); });
        empfaengerWahl.appendChild(el('option', {value: '', text: 'Bitte wählen'}));
        personen.forEach(function (p) {
            empfaengerWahl.appendChild(el('option', {value: empfaengerText(p), text: p.name}));
        });
        if (empfaenger.value) {
            empfaengerWahl.value = empfaenger.value;
        }
        if (!lehr) {
            Array.prototype.forEach.call(artWahl.options, function (o) {
                if (artVon(o.value) === 'helfer') {
                    o.disabled = true;
                    o.hidden = true;
                }
            });
            if (ausgabe) {
                ausgabe.style.display = 'none';
            }
        }

        function art() {
            return artVon(artWahl.value);
        }

        function auffrischen(setzen) {
            var a = art();
            var liste = a === 'eintauschen' ? d.preise.fuerMich : (a === 'anteil' ? d.preise.klasse : []);
            var alt = setzen && setzen.belohnung !== undefined ? setzen.belohnung : belohnung.value;
            belohnungWahl.textContent = '';
            belohnungWahl.appendChild(el('option', {value: '', text: 'Bitte wählen'}));
            liste.forEach(function (p) {
                belohnungWahl.appendChild(el('option', {value: p.name,
                    text: p.name + ' (' + sterneText(a === 'anteil' ? p.anteil : p.sterne) + ')'}));
            });
            belohnungWahl.value = alt;
            feld('belohnung').style.display = liste.length ? '' : 'none';
            feld('empfaenger').style.display = (a === 'verschenken' || a === 'helfer') ? '' : 'none';
            var p = liste.filter(function (x) { return x.name === belohnungWahl.value; })[0];
            if (p) {
                sterne.value = a === 'anteil' ? p.anteil : p.sterne;
            }
            sterne.readOnly = !!p && !lehr;
            if (a !== 'verschenken' && a !== 'helfer') {
                empfaenger.value = '';
            }
            belohnung.value = liste.length ? belohnungWahl.value : (a === 'helfer' ? 'Helfer-Stern' : '');
            pruefen();
        }

        function buchung() {
            return {id: rid, art: art(), belohnung: belohnung.value, sterne: zahl(sterne.value),
                    empfaenger: empfaengerId(empfaenger.value), von: von};
        }

        function pruefen() {
            var b = buchung();
            var gruende = b.art ? pruefeBuchung(b, konto.verfuegbar, d.preise,
                {buchungen: ohneMich, lernende: idsOderNull(d.teilnehmende.lernende),
                 anzahl: d.preise.lernende, lehrkraft: lehr}) : [];
            if (!d.verdientBekannt && !lehr) {
                gruende.push('Ihre verdienten Sterne ließen sich nicht lesen. Bitte später noch einmal versuchen.');
            }
            meldung.textContent = '';
            if (b.art !== 'helfer') {    // Helfer-Stern bucht die Lehrkraft; ihr Kontostand spielt keine Rolle
                meldung.appendChild(el('p', {'class': 'sb-stand', text: 'Verfügbar: ⭐ ' + zahlText(konto.verfuegbar) +
                    (b.art === 'verschenken' && b.sterne ? ' · Es kommen ' + sterneText(halbieren(b.sterne)) +
                        ' an.' : '')}));
            }
            if (gruende.length) {
                meldung.appendChild(el('ul', {'class': 'sb-warnung'}, gruende.map(function (g) {
                    return el('li', {text: g});
                })));
            }
            return gruende;
        }

        artWahl.addEventListener('change', function () { auffrischen(); });
        belohnungWahl.addEventListener('change', function () {
            belohnung.value = belohnungWahl.value;
            auffrischen();
        });
        empfaengerWahl.addEventListener('change', function () {
            empfaenger.value = empfaengerWahl.value;
            pruefen();
        });
        sterne.addEventListener('input', pruefen);
        form.addEventListener('submit', function (ev) {
            var gruende = pruefen();
            // Lernende: nichts über den Kontostand. Die Lehrkraft sieht die Hinweise und entscheidet selbst.
            if (gruende.length && !lehr) {
                ev.preventDefault();
                meldung.setAttribute('tabindex', '-1');
                meldung.focus();
            }
        });

        // Voreinstellung aus dem Link („#art=eintauschen&belohnung=Kaffee“, „#ausgabe“)
        var hash = new URLSearchParams(window.location.hash.replace(/^#/, ''));
        var setzen = {};
        if (hash.get('art') && KONFIG.arten[hash.get('art')]) {
            artWahl.value = KONFIG.arten[hash.get('art')];
        }
        if (hash.get('belohnung')) {
            setzen.belohnung = hash.get('belohnung');
        }
        auffrischen(setzen);
        if (window.location.hash === '#ausgabe' && ausgabe && lehr) {
            var haken = ausgabe.querySelector('input[type="checkbox"]');
            if (haken) {
                haken.checked = true;
                haken.focus();
                meldung.appendChild(el('p', {text: 'Ausgabe angehakt. Bitte speichern.'}));
            }
        }
    }

    // -- Ablauf -------------------------------------------------------------------------------------- //
    function laden() {
        var o = orte();
        return Promise.all([holeDoc(o.liste), holePreise(), holeTeilnehmende()]).then(function (r) {
            var listenDoc = r[0];
            var d = {orte: o, buchungen: buchungenAus(listenDoc), preise: r[1], teilnehmende: r[2],
                     lehrkraft: istLehrkraft(listenDoc) || istLehrkraft(document)};
            return kursIds(d.preise.kurse).then(function (kurse) {
                d.kurse = kurse;
                if (d.lehrkraft) {
                    return Promise.all(kurse.map(verdientAlle)).then(function (je) {
                        var summe = {};
                        je.forEach(function (k) {
                            Object.keys(k || {}).forEach(function (id) { summe[id] = (summe[id] || 0) + k[id]; });
                        });
                        d.verdientBekannt = je.length > 0 && je.every(function (k) { return k !== null; });
                        d.verdientJe = summe;
                        d.verdient = [];
                        return d;
                    });
                }
                return Promise.all(kurse.map(verdientIch)).then(function (werte) {
                    d.verdient = werte;
                    d.verdientBekannt = werte.every(function (w) { return w !== null; });
                    var summe = 0;
                    werte.forEach(function (w) { summe += w || 0; });
                    d.verdientJe = {};
                    d.verdientJe[ICH] = summe;
                    return d;
                });
            });
        }).then(function (d) {
            d.konten = konten(d.buchungen, d.verdientJe);
            return d;
        });
    }

    function start() {
        var pfad = window.location.pathname;
        var p = parameter();
        if (/\/mod\/data\/edit\.php$/.test(pfad)) {
            laden().then(eingabe).catch(function (e) {
                var f = document.querySelector('.sb-formular');
                if (f) {
                    f.insertBefore(el('p', {'class': 'alert alert-warning', text: 'Das Sternebuch konnte den ' +
                        'Kontostand nicht laden (' + e.message + '). Ihre Buchung prüft die Lehrkraft.'}), f.firstChild);
                }
            });
            return;
        }
        if (!/\/mod\/data\/view\.php$/.test(pfad) || p.get('rid') || p.get('mode') === 'single' ||
            p.get('mode') === 'asearch') {
            return;
        }
        var ziel = bereitstellen();
        laden().then(function (d) {
            (d.lehrkraft ? ansichtLehrkraft : ansichtLernende)(ziel, d);
        }).catch(function (e) { fehlerAnzeigen(ziel, e); });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', start);
    } else {
        start();
    }
})();
