"""Simulation Wendeschützschaltung mit Endschaltern am Pendelförderband, drei Fassungen (Lehrkraft 2026-10-15):
Schaltplan + Technologieschema, nur Schaltplan, nur Technologieschema. Gerechnet wird auf dem gezeichneten Plan
(stromlauf.py → kern.js), die Kiste und die Endschalter aus der Lage im Technologieschema (pendel.js).

Prüfungen vor dem Schreiben (Fehler brechen ab):
1. Der Plan im PDF ist aktuell (TeX-Quelle gleich der heutigen Beschreibung).
2. Gegenprobe: Der JS-Kern liefert auf dem Netz aus der Zeichnung in allen Abläufen dieselben Schützzustände wie
   plan.schaltfolge aus der Beschreibung.
3. Hauptstromkreis aus der Zeichnung: -Q1 = Rechtslauf, -Q2 = Linkslauf, beide zugleich = Kurzschluss.
4. Geschlossener Kreis Steuerung – Motor – Kiste – Endschalter: Die Kiste fährt rechts bis -B1 und hält vor dem
   Bandende, fährt nach -S3 links bis -B2 und hält; Motorschutz löst normal nicht aus, bei blockiertem Band schon.
5. Bedienung im Browser in allen drei Fassungen (Rechts ein, Aus), keine Skriptfehler.

    python3 werkzeug/simulation/wendeschuetz_sim.py
Ausgabe: docs/stilreferenz/simulation_wendeschuetz{,_plan,_schema}.{html,png}
"""
import json
import math
import subprocess
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
REPO = HIER.parents[1]
sys.path.insert(0, str(REPO / "werkzeug" / "schaltplan" / "beispiele"))
sys.path.insert(0, str(REPO / "werkzeug" / "technologieschema"))
sys.path.insert(0, str(HIER))
import wendeschuetz as ws  # noqa: E402  (baut Plan und Rechnung, ohne zu schreiben)
import pendelband  # noqa: E402
from bau import bild_schreiben, logo_uri, svg_aus_pdf  # noqa: E402
from plan import blatt, schaltfolge  # noqa: E402
from stromlauf import netz_aus_plan  # noqa: E402

ZIEL = REPO / "docs" / "stilreferenz" / "simulation_wendeschuetz"
PT = 72 / 25.4
fehler = []

# ---------------------------------------------------------------- 1. Plan aktuell?
if ws.ZIEL.with_suffix(".tex").read_text(encoding="utf-8") != blatt(ws.p, "\n".join(ws.zn.z + ws.zn.oben)):
    fehler.append("Stromlaufplan veraltet: erst werkzeug/schaltplan/beispiele/wendeschuetz.py ausführen")
netz = netz_aus_plan(ws.zn.geo, ws.ny)
NETZ = dict(kanten=netz["kanten"], quellen=netz["quellen"], knoten=list(range(len(netz["knoten"]))))
LAGE = [(round(x * PT, 2), round((297 - y) * PT, 2)) for x, y in netz["knoten"]]

# Technologieschema ohne bewegte Teile als Bühne
buehne = HIER / "_buehne_pendel"
buehne.mkdir(exist_ok=True)
try:
    pendelband.bauen(buehne / "pendelband", beweglich=False)
    schema_svg = svg_aus_pdf(buehne / "pendelband.pdf", "ts-")
finally:
    for d in buehne.iterdir():
        d.unlink()
    buehne.rmdir()
SCH = pendelband.LAGE

# ---------------------------------------------------------------- Motor (Rechnung zum Plan und Annahmen)
P, nN, ns = ws.P.wert * 1000, 1440.0, 1500.0
MOTOR = dict(
    ns=ns, nN=nN, v_N=0.4, MN=round(P / (2 * math.pi * nN / 60), 2), IN=ws.IN.wert, Ie=ws.IF2.wert, J=0.05,
    tau=round(-6.0 / math.log(1 - 1.2 ** 2 / 7.2 ** 2), 1), theta_aus=1.2 ** 2,
    M=[[0, 2.2], [0.2, 1.9], [0.4, 1.8], [0.6, 2.0], [0.8, 2.6], [0.88, 2.8], [0.93, 2.2], [nN / ns, 1.0], [1.0, 0.0]],
    I=[[0, ws.ia_in.wert], [0.4, 5.7], [0.7, 5.2], [0.88, 4.0], [0.93, 2.5], [nN / ns, 1.0], [1.0, 0.4]],
)
BED = dict(rechts="-S2", links="-S3", aus="-S1", f1="-F1", f2="-F2", last=40,
           ansicht_haupt=" ".join(f"{v * PT:.1f}" for v in (15, 12, 150, 125)),
           ansicht_steuer=" ".join(f"{v * PT:.1f}" for v in (175, 12, 212, 160)))
KERN = (HIER / "kern.js").read_text(encoding="utf-8")
PENDEL = (HIER / "pendel.js").read_text(encoding="utf-8")
KONTAKTE = (HIER / "kontakte.js").read_text(encoding="utf-8")

# ---------------------------------------------------------------- 2.–4. Gegenprobe mit Node
SZENARIEN = {        # (Kennzeichen, von, bis) betätigt
    "rechts": [("-S2", 0, 0.5)],
    "links": [("-S3", 0, 0.5)],
    "endlage_rechts": [("-S2", 0, 0.5), ("-B1", 2, 9)],
    "an_endlage_rechts_kein_rechts": [("-S2", 0, 0.5), ("-B1", 0, 9)],
    "an_endlage_rechts_links": [("-S3", 0, 0.5), ("-B1", 0, 9)],
    "endlage_links": [("-S3", 0, 0.5), ("-B2", 2, 9)],
    "umsteuern": [("-S2", 0, 0.5), ("-S3", 2, 2.5)],
    "aus": [("-S2", 0, 0.5), ("-S1", 2, 2.5)],
    "motorschutz": [("-S2", 0, 0.5), ("-F2", 2, 9)],
    "beide": [("-S2", 0, 0.5), ("-S3", 0, 0.5)],
}
TEST = r"""
const Kern = require(process.argv[2]), Pendel = require(process.argv[3]);
const d = JSON.parse(require("fs").readFileSync(0, "utf8"));
const aus = { folgen: {}, haupt: {} };
for (const [name, iv] of Object.entries(d.szenarien)) {
  const z = Kern.neu(d.netz, {}); const v = [];
  for (let t = 0; t <= 6 + 1e-9; t += 0.1) {
    z.t = t; z.betaetigt = new Set(iv.filter(([b, a, e]) => a <= t && t < e).map(x => x[0]));
    Kern.stabil(z); v.push([Math.round(t * 10) / 10, Object.assign({}, z.an)]);
  }
  aus.folgen[name] = v;
}
for (const [name, an] of Object.entries({ aus: [], rechts: ["-Q1"], links: ["-Q2"], beide: ["-Q1", "-Q2"] })) {
  const z = Kern.neu(d.netz, {}); an.forEach(s => z.an[s] = true);
  const h = Kern.haupt(z); aus.haupt[name] = { modus: h.modus, kurz: h.kurz };
}
// geschlossener Kreis wie auf der Seite: 0,1-s-Schritte der Steuerung, Motor und Kiste in 0,01 s
function kreis(last, taster, ende) {
  const z = Kern.neu(d.netz, {}), m = { n: 0, theta: 0 }, k = Pendel.neu(d.sch);
  let end = Pendel.schritt(k, d.sch, 0, 0), f2 = null, anschlag = false;
  const spur = [];
  for (let t = 0; t < ende - 1e-9; t = Math.round((t + 0.1) * 10) / 10) {
    z.t = t;
    z.betaetigt = new Set([...taster.filter(([b, a, e]) => a <= t && t < e).map(x => x[0]), ...Object.keys(end)]);
    if (f2 !== null) z.betaetigt.add("-F2");
    const h = Kern.schritt(z);
    for (let i = 0; i < 10; i++) {
      Kern.motor(d.motor, m, h.modus, last, 0.01);
      end = Pendel.schritt(k, d.sch, d.motor.v_N * m.n / d.motor.nN, 0.01);
      anschlag = anschlag || k.anschlag;
    }
    if (m.theta >= d.motor.theta_aus && f2 === null) f2 = t;
    spur.push([t, h.modus, k.x, Object.keys(end)]);
  }
  return { spur, f2, anschlag };
}
aus.normal = kreis(0.4, [["-S2", 0, 0.5], ["-S3", 25, 25.5]], 50);
aus.blockiert = kreis(3.0, [["-S2", 0, 0.5]], 40);
process.stdout.write(JSON.stringify(aus));
"""


def gegenprobe():
    datei = HIER / "_test_wende.js"
    datei.write_text(TEST, encoding="utf-8")
    try:
        e = subprocess.run(["node", str(datei), str(HIER / "kern.js"), str(HIER / "pendel.js")], capture_output=True,
                           text=True, input=json.dumps(dict(netz=NETZ, motor=MOTOR, sch=SCH, szenarien=SZENARIEN)))
    finally:
        datei.unlink()
    if e.returncode:
        raise SystemExit("Node-Fehler:\n" + e.stderr)
    return json.loads(e.stdout)


erg = gegenprobe()
for name, iv in SZENARIEN.items():
    py = schaltfolge(ws.st, lambda t, iv=iv: {b for b, a, e in iv if a <= t < e}, {}, ende=6)
    js = erg["folgen"][name]
    abw = [t for (t, a), (tj, b) in zip(py, js) if a != b or abs(t - tj) > 1e-9]
    if len(py) != len(js) or abw:
        fehler.append(f"Gegenprobe {name}: Simulation weicht vom Plan ab ab t = {abw[0] if abw else '?'} s")
for name, soll in (("aus", "Aus"), ("rechts", "Rechtslauf"), ("links", "Linkslauf")):
    if erg["haupt"][name]["modus"] != soll or erg["haupt"][name]["kurz"]:
        fehler.append(f"Hauptstromkreis {name}: {erg['haupt'][name]}")
if not erg["haupt"]["beide"]["kurz"]:
    fehler.append("Hauptstromkreis: -Q1 und -Q2 zugleich ohne Kurzschluss")
spur = erg["normal"]["spur"]


def erstes(bed):
    return next((s for s in spur if bed(s)), None)


b1 = erstes(lambda s: "-B1" in s[3])
halt_r = erstes(lambda s: s[0] < 25 and b1 and s[0] > b1[0] and s[1] == "Aus")
b2 = erstes(lambda s: "-B2" in s[3] and s[0] > 25)
ende = spur[-1]
if not b1 or not halt_r:
    fehler.append("Kreis: Kiste erreicht -B1 nicht oder Motor hält dort nicht")
if not b2 or ende[1] != "Aus" or "-B2" not in ende[3]:
    fehler.append("Kreis: nach -S3 fährt die Kiste nicht bis -B2 oder hält dort nicht")
if erg["normal"]["anschlag"]:
    fehler.append("Kreis: Kiste schlägt am Bandende an (Nachlauf zu lang)")
if erg["normal"]["f2"] is not None:
    fehler.append(f"Kreis: Motorschutz löst im Normalbetrieb aus (t = {erg['normal']['f2']} s)")
if erg["blockiert"]["f2"] is None:
    fehler.append("Kreis: Motorschutz löst bei blockiertem Band nicht aus")
nachlauf = [s[2] for s in spur if s[0] < 25][-1] + SCH["kiste"]["b"] - SCH["endschalter"]["-B1"]["kontakt"]

# ---------------------------------------------------------------- HTML
fuss = (f"Modell: Steuerung und Hauptstromkreis werden auf dem gezeichneten Plan gerechnet (gleicher Ablauf wie die "
        f"Prüfung des Plans), Drehrichtung aus der Phasenfolge am Motor; die Endschalter betätigt die Kiste aus ihrer "
        f"Lage im Technologieschema. Motor {ws.wert(ws.P)} kW, I<sub>N</sub> = {ws.wert(ws.IN)} A aus der Rechnung "
        f"zum Plan. Annahmen: n<sub>N</sub> = {nN:.0f} 1/min, Kennlinien typischer Verlauf eines vierpoligen "
        f"Normmotors, Trägheitsmoment Motor und Band 0,05 kg·m², Lastmoment konstant, Bandgeschwindigkeit 0,4 m/s "
        f"bei n<sub>N</sub>, Band im Bild ≈ 6,2 m; Motorschutzrelais als Bimetall der Auslöseklasse 10 (vereinfacht), "
        f"eingestellt auf {ws.wert(ws.IF2)} A.<br>Stromlaufplan: Stilreferenz schaltplan_wendeschuetz_a3; "
        f"Technologieschema: technologieschema_pendelband; Zeichen nach DIN EN 60617 (Positionsschalter 07-08-02 "
        f"nach QElectroTech-Bibliothek, CC-BY 3.0).<br>KI-gestützt erstellt (Werkzeug, Version und Datum laut "
        f"KI-Verzeichnis). Beispiel aus der Erprobung der Materialpipeline.")
plan_svg = svg_aus_pdf(ws.ZIEL.with_suffix(".pdf"), "sp-")
ERSATZ = {"@@TITEL@@": ws.p.titel, "@@UNTERTITEL@@": ws.p.untertitel, "@@BETRIEB@@": ws.p.betrieb,
          "@@FUSS@@": fuss, "@@KERN@@": KERN, "@@PENDEL@@": PENDEL, "@@KONTAKTE@@": KONTAKTE, "@@LOGO@@": logo_uri(),
          "@@NETZ@@": json.dumps(NETZ, separators=(",", ":")), "@@LAGE@@": json.dumps(LAGE, separators=(",", ":")),
          "@@SCH@@": json.dumps(SCH, ensure_ascii=False), "@@MOTOR@@": json.dumps(MOTOR),
          "@@BED@@": json.dumps(BED, ensure_ascii=False), "@@PLAN@@": plan_svg, "@@SCHEMA@@": schema_svg}
FASSUNGEN = {"": ("beides", "Schaltplan und Technologieschema"), "_plan": ("plan", "Stromlaufplan"),
             "_schema": ("schema", "Technologieschema")}
seiten = {}
for endung, (modus, art) in FASSUNGEN.items():
    html = (HIER / "vorlage_pendel.html").read_text(encoding="utf-8").replace("@@MODUS@@", modus).replace("@@ART@@", art)
    for k, v in ERSATZ.items():
        html = html.replace(k, v)
    if "@@" in html.replace(plan_svg, "").replace(schema_svg, ""):
        fehler.append("Platzhalter nicht ersetzt")
    seiten[endung] = html

if __name__ == "__main__":
    print("Prüfbericht Simulation Wendeschütz mit Endschaltern")
    print(f"  Netz aus dem Plan: {len(netz['knoten'])} Knoten, {len(netz['kanten'])} Kanten")
    if b1 and b2:
        print(f"  Kreis: -B1 bei t = {b1[0]} s, Nachlauf nach Betätigen {nachlauf / SCH['massstab'] * 100:.0f} cm; -B2 bei t = {b2[0]} s; "
              f"Motorschutz bei blockiertem Band nach {erg['blockiert']['f2']} s")
    print(f"  Fehler: {len(fehler)}")
    for f_ in fehler:
        print("  [Fehler]", f_)
    if fehler:
        sys.exit(1)
    from playwright.sync_api import sync_playwright
    meldungen = []

    def tippen(s, ziel):
        ziel.hover(); s.mouse.down(); s.wait_for_timeout(400); s.mouse.up(); s.wait_for_timeout(1200)

    with sync_playwright() as pw:
        vor = Path("/opt/pw-browsers/chromium")
        b = pw.chromium.launch(executable_path=str(vor) if vor.exists() else None)
        for endung, html in seiten.items():
            datei = ZIEL.with_name(ZIEL.name + endung)
            datei.with_suffix(".html").write_text(html, encoding="utf-8")
            s = b.new_page(viewport={"width": 1400, "height": 900}, device_scale_factor=1)
            s.on("pageerror", lambda e: meldungen.append(str(e)))
            s.goto(datei.with_suffix(".html").as_uri())
            ort = "#schema g.taste" if FASSUNGEN[endung][0] == "schema" else "#plan rect.taste"
            tippen(s, s.locator(f'{ort}[data-bmk="-S2"] >> nth=0'))
            if s.evaluate("modus()") != "Rechtslauf":
                meldungen.append(f"{datei.name}: nach -S2 nicht Rechtslauf, sondern {s.evaluate('modus()')}")
            # Kontakte in Arbeitsstellung: 3 Hauptkontakte, Selbsthaltung 13–14 und Verriegelung 21–22 von -Q1
            if s.evaluate("arbeitsstellung()") < 5:
                meldungen.append(f"{datei.name}: Kontakte von -Q1 nicht in Arbeitsstellung gezeichnet")
            tippen(s, s.locator(f'{ort}[data-bmk="-S3"] >> nth=0'))     # Tasterverriegelung: kein direktes Umsteuern
            if s.evaluate("modus()") != "Rechtslauf":
                meldungen.append(f"{datei.name}: -S3 im Rechtslauf steuert direkt um ({s.evaluate('modus()')})")
            tippen(s, s.locator(f'{ort}[data-bmk="-S1"] >> nth=0'))
            if s.evaluate("modus()") != "Aus":
                meldungen.append(f"{datei.name}: nach -S1 nicht Aus, sondern {s.evaluate('modus()')}")
            # Kurz angetippt (Druck und Loslassen vor dem nächsten Rechenschritt) an der Endlage rechts: -S3 muss
            # umsteuern (Fehlerbild der Lehrkraft 2026-10-15: „konnte nicht mehr umschalten“)
            s.evaluate("vorspulen(10)")
            ziel = s.locator(f'{ort}[data-bmk="-S3"] >> nth=0')
            ziel.dispatch_event("pointerdown", {"pointerId": 1, "bubbles": True})
            ziel.dispatch_event("pointerup", {"pointerId": 1, "bubbles": True})
            s.evaluate("rechneSchritte(15)")
            if s.evaluate("modus()") != "Linkslauf":
                meldungen.append(f"{datei.name}: kurzes Antippen von -S3 an der Endlage rechts steuert nicht um "
                                 f"({s.evaluate('modus()')})")
            s.mouse.move(0, 0)
            s.evaluate("vorspulen(3)")
            s.wait_for_timeout(200)
            bild_schreiben(datei.with_suffix(".png"), s.screenshot(full_page=True))
            print(datei.with_suffix(".html"))
        b.close()
    if meldungen:
        sys.exit("Fehler im Browser: " + "; ".join(meldungen))
