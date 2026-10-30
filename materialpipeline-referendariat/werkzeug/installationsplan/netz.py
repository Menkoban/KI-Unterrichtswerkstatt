"""Leitungsnetz einer Installation: Aderzahl jeder Leitung aus der Verschaltung berechnet, nicht eingetragen.

Knoten sind Unterverteiler, Abzweigdosen und Betriebsmittel; Kanten sind Leitungen (Baum je Stromkreis, keine
Maschen). Jede Ader ist ein Leiter mit einer Menge von Anschlusspunkten (z. B. Außenleiter L: Unterverteiler und
Schalter). Eine Leitung braucht eine Ader, wenn der Leiter Anschlusspunkte auf beiden Seiten der Leitung hat.
Der Schutzleiter geht zu jedem Betriebsmittel, auch zu Schaltern (Europa 32690-3 S. 17: „mit einem Schutzleiter,
auch wenn dieser für das Betriebsmittel nicht erforderlich ist“).

Beispiel Ausschaltung: UV–X1: L, N, PE = 3; X1–Q1: L, Schaltdraht, PE = 3; X1–E1: Schaltdraht, N, PE = 3.
"""
from __future__ import annotations

from collections import defaultdict


class Stromkreis:
    def __init__(self, netz: "Netz", name: str, quelle: str, aussenleiter=("L",)):
        self.netz, self.name, self.quelle = netz, name, quelle
        self.aussenleiter = aussenleiter
        for l in aussenleiter:
            netz.ader(f"{name}.{l}", quelle)
        netz.ader(f"{name}.N", quelle)
        netz.ader(f"{name}.PE", quelle)
        self.nr = 0

    def _neu(self, art):
        self.nr += 1
        return f"{self.name}.{art}{self.nr}"

    def _pe(self, *geraete):
        self.netz.netze[f"{self.name}.PE"].update(geraete)

    def verbraucher(self, *geraete):
        """Steckdose, Herd, Geräteanschluss: alle Außenleiter, N und PE."""
        for l in self.aussenleiter:
            self.netz.netze[f"{self.name}.{l}"].update(geraete)
        self.netz.netze[f"{self.name}.N"].update(geraete)
        self._pe(*geraete)

    def _leuchten(self, schaltdraht_von, leuchten):
        sd = self._neu("Schaltdraht")
        self.netz.ader(sd, schaltdraht_von, *leuchten)
        self.netz.netze[f"{self.name}.N"].update(leuchten)
        self._pe(*leuchten)

    def ausschaltung(self, q, leuchten):
        self.netz.netze[f"{self.name}.L"].add(q)
        self._pe(q)
        self._leuchten(q, leuchten)

    def wechselschaltung(self, q_l, q_lampe, leuchten):
        """Außenleiter an q_l, zwei korrespondierende Leiter q_l–q_lampe, Schaltdraht von q_lampe zur Leuchte."""
        self.kreuzschaltung([q_l, q_lampe], leuchten)

    def kreuzschaltung(self, schalter, leuchten):
        """schalter: Wechselschalter, Kreuzschalter …, Wechselschalter in Reihenfolge der Verdrahtung."""
        self.netz.netze[f"{self.name}.L"].add(schalter[0])
        self._pe(*schalter)
        for a, b in zip(schalter, schalter[1:]):
            for _ in range(2):
                self.netz.ader(self._neu("Korrespondierend"), a, b)
        self._leuchten(schalter[-1], leuchten)


class Netz:
    def __init__(self):
        self.kanten: list[tuple[str, str]] = []
        self.netze: dict[str, set] = {}
        self.stromkreise: dict[str, Stromkreis] = {}

    def kante(self, a, b):
        self.kanten.append((a, b))

    def weg(self, *knoten):
        for a, b in zip(knoten, knoten[1:]):
            self.kante(a, b)

    def ader(self, name, *knoten):
        self.netze[name] = set(knoten)

    def stromkreis(self, name, quelle="UV", aussenleiter=("L",)):
        sk = Stromkreis(self, name, quelle, aussenleiter)
        self.stromkreise[name] = sk
        return sk

    def _nachbarn(self, ohne=None):
        nb = defaultdict(set)
        for k in self.kanten:
            if k == ohne:
                continue
            a, b = k
            nb[a].add(b)
            nb[b].add(a)
        return nb

    def _seite(self, start, ohne):
        nb, gesehen, offen = self._nachbarn(ohne), {start}, [start]
        while offen:
            for m in nb[offen.pop()] - gesehen:
                gesehen.add(m)
                offen.append(m)
        return gesehen

    def _kante(self, a, b):
        for k in self.kanten:
            if k in ((a, b), (b, a)):
                return k
        raise KeyError(f"Keine Leitung {a}–{b}")

    def leiter(self, a, b) -> list[str]:
        """Namen der Adern in der Leitung a–b."""
        k = self._kante(a, b)
        seite = self._seite(a, k)
        return sorted(n for n, pkt in self.netze.items() if pkt & seite and pkt - seite)

    def adern(self, a, b) -> int:
        return len(self.leiter(a, b))

    def pruefen(self):
        """Baum ohne Maschen, alle Anschlusspunkte erreichbar; jede Leitung führt den Schutzleiter."""
        meld = []
        knoten = {x for k in self.kanten for x in k}
        if len(set(map(frozenset, self.kanten))) != len(self.kanten):
            meld.append(("Fehler", "Leitung doppelt eingetragen"))
        # Wald: Kanten = Knoten − Komponenten
        komp, rest = 0, set(knoten)
        while rest:
            rest -= self._seite(rest.pop(), None)
            komp += 1
        if len(self.kanten) != len(knoten) - komp:
            meld.append(("Fehler", "Leitungsnetz hat eine Masche"))
        for n, pkt in self.netze.items():
            if not pkt <= knoten:
                meld.append(("Fehler", f"{n}: Anschluss ohne Leitung: {sorted(pkt - knoten)}"))
        for a, b in self.kanten:
            if not any(x.endswith(".PE") for x in self.leiter(a, b)):
                meld.append(("Fehler", f"Leitung {a}–{b} ohne Schutzleiter"))
        return meld

    def tabelle(self):
        """Leitung, Aderzahl, Adern – für Erwartungshorizont und Prüfbericht."""
        return [(a, b, self.adern(a, b), self.leiter(a, b)) for a, b in self.kanten]
