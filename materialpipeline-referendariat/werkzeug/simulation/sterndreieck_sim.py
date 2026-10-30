"""Simulation Stern-Dreieck-Anlauf (Entscheidung A, 2026-10-15): eine HTML-Datei, offline, mit dem echten
Stromlaufplan (SVG aus dem PDF der Stilreferenz) und einer Überlagerung, die auf dem gezeichneten Plan rechnet
(stromlauf.py → kern.js).

Prüfungen vor dem Schreiben (Fehler brechen ab):
1. Der Plan im PDF ist aktuell (TeX-Quelle gleich der heutigen Beschreibung).
2. Gegenprobe: Der JS-Kern liefert auf dem Netz aus der Zeichnung für jeden Ablauf dieselben Schützzustände wie
   plan.schaltfolge aus der Beschreibung (Normalanlauf, Aus und Motorschutz im Stern und im Dreieck).
3. Hauptstromkreis aus der Zeichnung: Stern = 230 V je Wicklung, Dreieck = 400 V, Stern und Dreieck zugleich →
   Kurzschluss erkannt.
4. Motormodell: Hochlauf im Stern vor Ablauf der Sternzeit, Strom nach dem Hochlauf ≤ I_N, Motorschutz löst im
   Normalbetrieb nicht aus, bei blockiertem Band aber doch.

    python3 werkzeug/simulation/sterndreieck_sim.py
Ausgabe: docs/stilreferenz/simulation_sterndreieck{,_plan}.{html,png} (kombiniert, nur Schaltplan)
"""
import json
import math
import subprocess
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
REPO = HIER.parents[1]
sys.path.insert(0, str(REPO / "werkzeug" / "schaltplan" / "beispiele"))
sys.path.insert(0, str(HIER))
import sterndreieck as sd  # noqa: E402  (baut Plan und Rechnung, ohne zu schreiben)
from plan import blatt, schaltfolge  # noqa: E402
from stromlauf import netz_aus_plan  # noqa: E402
sys.path.insert(0, str(REPO / "werkzeug" / "technologieschema"))
import foerderband  # noqa: E402

PLAN = sd.ZIEL
ZIEL = REPO / "docs" / "stilreferenz" / "simulation_sterndreieck"
PT = 72 / 25.4
fehler = []

# ---------------------------------------------------------------- 1. Plan aktuell?
if PLAN.with_suffix(".tex").read_text(encoding="utf-8") != blatt(sd.p, "\n".join(sd.zn.z + sd.zn.oben)):
    fehler.append("Stromlaufplan veraltet: erst werkzeug/schaltplan/beispiele/sterndreieck.py ausführen")

netz = netz_aus_plan(sd.zn.geo, sd.ny)
NETZ = dict(kanten=netz["kanten"], quellen=netz["quellen"], knoten=list(range(len(netz["knoten"]))))
LAGE = [(round(x * PT, 2), round((297 - y) * PT, 2)) for x, y in netz["knoten"]]

# ---------------------------------------------------------------- Motor (Rechnung und Annahmen)
P, nN, ns = sd.P.wert * 1000, 1455.0, 1500.0
MN = P / (2 * math.pi * nN / 60)
Ie = sd.IF2.wert
tau = -6.0 / math.log(1 - 1.2 ** 2 / 7.2 ** 2)          # Klasse 10: bei 7,2 · I_e Auslösung nach ≈ 6 s
MOTOR = dict(
    ns=ns, nN=nN, v_N=0.5, MN=round(MN, 2), IN=sd.IN.wert, Ie=Ie, J=0.4, tau=round(tau, 1), theta_aus=1.2 ** 2,
    # typische Kennlinien eines 4-poligen Normmotors, relativ zu n_s, M_N und I_N (Annahme, Katalog-Verlauf)
    M=[[0, 2.2], [0.2, 1.9], [0.4, 1.8], [0.6, 2.0], [0.8, 2.6], [0.88, 2.8], [0.94, 2.2], [nN / ns, 1.0], [1.0, 0.0]],
    I=[[0, sd.ia_in.wert], [0.4, 6.6], [0.7, 6.0], [0.88, 4.6], [0.94, 2.8], [nN / ns, 1.0], [1.0, 0.4]],
)
BED = dict(ein="-S2", aus="-S1", f1="-F1", f2="-F2", k1="-K1", motor="-M1", t_k1=sd.T_K1, last=40,
           # Ausschnitte (x, y von oben, Breite, Höhe in mm): nur der belegte Teil des Blatts
           ansicht_haupt=" ".join(f"{v * PT:.1f}" for v in (15, 12, 200, 145)),
           ansicht_steuer=" ".join(f"{v * PT:.1f}" for v in (200, 12, 212, 192)))
KERN = (HIER / "kern.js").read_text(encoding="utf-8")
KONTAKTE = (HIER / "kontakte.js").read_text(encoding="utf-8")

# ---------------------------------------------------------------- 2.–4. Gegenprobe mit Node
SZENARIEN = {"normal": {}, "aus_stern": {"aus_bei": 4.0}, "f2_stern": {"f2_bei": 4.0},
             "aus_dreieck": {"aus_bei": 12.0}, "f2_dreieck": {"f2_bei": 12.0}}
TEST = r"""
const Kern = require(process.argv[2]);
const d = JSON.parse(require("fs").readFileSync(0, "utf8"));
const aus = {};
function ein(sz, t) {
  const m = new Set(t < 0.5 ? ["-S2"] : []);
  if (sz.aus_bei !== undefined && sz.aus_bei <= t && t < sz.aus_bei + 0.5) m.add("-S1");
  if (sz.f2_bei !== undefined && t >= sz.f2_bei) m.add("-F2");
  return m;
}
aus.folgen = {};
for (const [name, sz] of Object.entries(d.szenarien)) {
  const z = Kern.neu(d.netz, { "-K1": d.t_k1 }); const v = [];
  for (let t = 0; t <= 14 + 1e-9; t += 0.1) { z.t = t; z.betaetigt = ein(sz, t); Kern.stabil(z); v.push([Math.round(t * 10) / 10, Object.assign({}, z.an)]); }
  aus.folgen[name] = v;
}
// Hauptstromkreis bei festen Schützzuständen
aus.haupt = {};
for (const [name, an] of Object.entries({ aus: [], stern: ["-Q1", "-Q2"], dreieck: ["-Q1", "-Q3"], beide: ["-Q1", "-Q2", "-Q3"] })) {
  const z = Kern.neu(d.netz, { "-K1": d.t_k1 });
  an.forEach(s => z.an[s] = true);
  const h = Kern.haupt(z); aus.haupt[name] = { modus: h.modus, spannung: h.spannung, kurz: h.kurz };
}
// Motor: Normalanlauf mit Sternzeit und Last, Werte je Sekunde
function anlauf(last, t_k1, ende) {
  const m = { n: 0, theta: 0 }, r = []; let modus = "Stern", f2 = null;
  for (let i = 1; i <= ende * 100; i++) {
    const t = i / 100; modus = t < t_k1 ? "Stern" : "Dreieck";
    if (f2 !== null) modus = "Aus";
    const w = Kern.motor(d.motor, m, modus, last, 0.01);
    if (m.theta >= d.motor.theta_aus && f2 === null) f2 = t;
    if (i % 100 === 0) r.push([t, m.n, w.I]);
  }
  return { verlauf: r, f2 };
}
aus.motor = { normal: anlauf(0.4, d.t_k1, 120), fest: anlauf(3.0, d.t_k1, 120) };
process.stdout.write(JSON.stringify(aus));
"""


def gegenprobe():
    (HIER / "_test.js").write_text(TEST, encoding="utf-8")
    try:
        e = subprocess.run(["node", str(HIER / "_test.js"), str(HIER / "kern.js")], capture_output=True, text=True,
                           input=json.dumps(dict(netz=NETZ, t_k1=sd.T_K1, motor=MOTOR, szenarien=SZENARIEN)))
    finally:
        (HIER / "_test.js").unlink()
    if e.returncode:
        raise SystemExit("Node-Fehler:\n" + e.stderr)
    return json.loads(e.stdout)


ergebnis = gegenprobe()
for name, sz in SZENARIEN.items():
    py = schaltfolge(sd.st, sd.eingaben(**sz), {"-K1": sd.T_K1}, ende=14)
    js = ergebnis["folgen"][name]
    abw = [t for (t, a), (tj, b) in zip(py, js) if a != b or abs(t - tj) > 1e-9]
    if len(py) != len(js) or abw:
        fehler.append(f"Gegenprobe {name}: Simulation weicht vom Plan ab ab t = {abw[0] if abw else '?'} s")
h = ergebnis["haupt"]
erwart = {"aus": ("Aus", None), "stern": ("Stern", None), "dreieck": ("Dreieck", None)}
for name, (modus, _) in erwart.items():
    if h[name]["modus"] != modus or h[name]["kurz"]:
        fehler.append(f"Hauptstromkreis {name}: Simulation zeigt {h[name]}")
if not h["beide"]["kurz"]:
    fehler.append("Hauptstromkreis: Stern- und Dreieckschütz zugleich ohne Kurzschluss")
mn, mf = ergebnis["motor"]["normal"], ergebnis["motor"]["fest"]
n_vor = mn["verlauf"][sd.T_K1 - 2][1]
I_ende = mn["verlauf"][-1][2]
if n_vor < 0.9 * ns:
    fehler.append(f"Motormodell: im Stern nur {n_vor:.0f} 1/min vor dem Umschalten")
if I_ende > sd.IN.wert:
    fehler.append(f"Motormodell: Strom nach Hochlauf {I_ende:.1f} A > I_N")
if mn["f2"] is not None:
    fehler.append(f"Motormodell: Motorschutz löst im Normalbetrieb nach {mn['f2']} s aus")
if mf["f2"] is None:
    fehler.append("Motormodell: Motorschutz löst bei blockiertem Band nicht aus")

# ---------------------------------------------------------------- HTML
svg = subprocess.run(["pdftocairo", "-svg", str(PLAN.with_suffix(".pdf")), "-"], capture_output=True, text=True,
                     check=True).stdout
svg = svg[svg.index("<svg"):]
quellen = ("Stromlaufplan: Stilreferenz schaltplan_sterndreieck_a3 (Abgleich mit Moeller-Katalog SDAINL, Eaton, "
           "Siemens 24499345, Jugend &amp; Volk ZA44).")
fuss = (f"Modell: Steuerung und Hauptstromkreis werden auf dem gezeichneten Plan gerechnet (gleicher Ablauf wie die "
        f"Prüfung des Plans). Motor {sd.wert(sd.P)} kW, I<sub>N</sub> = {sd.wert(sd.IN)} A, "
        f"I<sub>A</sub>/I<sub>N</sub> = {sd.wert(sd.ia_in)} aus der Rechnung zum Plan. Annahmen: n<sub>N</sub> = "
        f"{nN:.0f} 1/min, Drehmoment- und Stromkennlinie typischer Verlauf eines vierpoligen Normmotors, "
        f"Trägheitsmoment Motor und Band 0,4 kg·m², Lastmoment konstant, Bandgeschwindigkeit 0,5 m/s bei n<sub>N</sub>; Motorschutzrelais als Bimetall der "
        f"Auslöseklasse 10 (vereinfacht), eingestellt auf {sd.wert(sd.IF2)} A. Ausgleichsvorgänge beim Umschalten "
        f"(Stromspitze durch Restspannung) sind nicht nachgebildet.<br>{quellen}<br>"
        f"KI-gestützt erstellt (Werkzeug, Version und Datum laut KI-Verzeichnis). Beispiel aus der Erprobung der "
        f"Materialpipeline.")
def logo_uri():
    """Schullogo (Profil schule.logo, neutral im Werkzeug) verkleinert als eingebettetes Bild, damit die Datei offline bleibt."""
    import base64
    import io
    from PIL import Image
    sys.path.insert(0, str(REPO / "werkzeug" / "vorlagen"))
    import schule
    im = Image.open(schule.LOGO)
    im.thumbnail((240, 130))
    puffer = io.BytesIO()
    im.save(puffer, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(puffer.getvalue()).decode()


ersatz = {"@@TITEL@@": sd.p.titel, "@@UNTERTITEL@@": sd.p.untertitel, "@@BETRIEB@@": sd.p.betrieb,
          "@@EIN@@": "-S2 Ein", "@@AUS@@": "-S1 Aus", "@@F1@@": "-F1", "@@F2@@": "-F2", "@@K1@@": "-K1",
          "@@FUSS@@": fuss, "@@KERN@@": KERN, "@@KONTAKTE@@": KONTAKTE, "@@NETZ@@": json.dumps(NETZ, separators=(",", ":")),
          "@@LAGE@@": json.dumps(LAGE, separators=(",", ":")), "@@MOTOR@@": json.dumps(MOTOR),
          "@@BED@@": json.dumps(BED, ensure_ascii=False), "@@PLAN@@": svg, "@@LOGO@@": logo_uri()}
# Technologieschema ohne bewegte Teile als Bühne; Pakete, Gurt und Trommeln zeichnet die Simulation
buehne = HIER / "_buehne"
buehne.mkdir(exist_ok=True)
try:
    foerderband.bauen(buehne / "foerderband", beweglich=False)
    schema_svg = subprocess.run(["pdftocairo", "-svg", str(buehne / "foerderband.pdf"), "-"], capture_output=True,
                                text=True, check=True).stdout
finally:
    for d in buehne.iterdir():
        d.unlink()
    buehne.rmdir()
schema_svg = schema_svg[schema_svg.index("<svg"):]
ersatz_schema = dict(ersatz, **{"@@SCHEMA@@": schema_svg, "@@LAGE@@": json.dumps(foerderband.LAGE, ensure_ascii=False)})

FASSUNGEN = {"": "voll", "_plan": "nurplan", "_schema": "schema"}   # Lehrkraft 2026-10-15: drei Fassungen
seiten = {}
for endung, modus in FASSUNGEN.items():
    vorlage = "vorlage_technologieschema.html" if modus == "schema" else "vorlage_schuetz.html"
    html = (HIER / vorlage).read_text(encoding="utf-8").replace("@@MODUS@@", modus)
    for k, v in (ersatz_schema if modus == "schema" else ersatz).items():
        html = html.replace(k, v)
    if "@@" in html.replace(svg, "").replace(schema_svg, ""):
        fehler.append("Platzhalter nicht ersetzt")
    seiten[endung] = html

if __name__ == "__main__":
    print("Prüfbericht Simulation Stern-Dreieck")
    print(f"  Netz aus dem Plan: {len(netz['knoten'])} Knoten, {len(netz['kanten'])} Kanten")
    print(f"  Hochlauf im Stern: {n_vor:.0f} 1/min nach {sd.T_K1 - 1} s; Strom nach Hochlauf {I_ende:.1f} A; "
          f"Motorschutz bei blockiertem Band nach {mf['f2']} s")
    print(f"  Fehler: {len(fehler)}")
    for f in fehler:
        print("  [Fehler]", f)
    if fehler:
        sys.exit(1)
    from playwright.sync_api import sync_playwright
    meldungen = []

    def bild_schreiben(ziel, daten):
        """Vorschau nur ersetzen, wenn sie sich sichtbar ändert (Kantenglättung schwankt um einzelne Pixel)."""
        import io
        from PIL import Image, ImageChops
        if ziel.exists():
            alt, neu = Image.open(ziel).convert("RGB"), Image.open(io.BytesIO(daten)).convert("RGB")
            if alt.size == neu.size:
                diff = ImageChops.difference(alt, neu).convert("L").point(lambda v: 255 if v > 48 else 0)
                if diff.histogram()[255] < 150:          # weniger als 150 deutlich veränderte Pixel
                    return
        ziel.write_bytes(daten)

    def tippen(s, ziel):
        ziel.hover(); s.mouse.down(); s.wait_for_timeout(400); s.mouse.up(); s.wait_for_timeout(1200)

    with sync_playwright() as pw:
        vor = Path("/opt/pw-browsers/chromium")        # vorinstallierter Browser der Cloud-Umgebung
        b = pw.chromium.launch(executable_path=str(vor) if vor.exists() else None)
        for endung, html in seiten.items():
            datei = ZIEL.with_name(ZIEL.name + endung)
            datei.with_suffix(".html").write_text(html, encoding="utf-8")
            s = b.new_page(viewport={"width": 1400, "height": 900}, device_scale_factor=1)
            s.on("pageerror", lambda e: meldungen.append(str(e)))
            s.goto(datei.with_suffix(".html").as_uri())
            # Bedienprüfung in Echtzeit: Ein (Bedienfeld bzw. im Plan), dann Aus im Plan
            schema = FASSUNGEN[endung] == "schema"
            modus = (lambda: s.evaluate("modus()")) if schema else (lambda: s.text_content("#modus"))
            ein = {"voll": "#ein", "nurplan": "rect.taste >> nth=1", "schema": "g.taste >> nth=0"}[FASSUNGEN[endung]]
            aus = "g.taste >> nth=1" if schema else "rect.taste >> nth=0"     # -S1: im Plan erster Taster
            tippen(s, s.locator(ein))
            if modus() != "Stern":
                meldungen.append(f"{datei.name}: nach Ein nicht Stern, sondern {modus()}")
            tippen(s, s.locator(aus))
            if modus() != "Aus":
                meldungen.append(f"{datei.name}: nach -S1 nicht Aus, sondern {modus()}")
            s.mouse.move(0, 0)                               # kein Hover im Vorschaubild
            s.evaluate("vorspulen(4)")
            s.wait_for_timeout(200)
            bild_schreiben(datei.with_suffix(".png"), s.screenshot(full_page=True))
            print(datei.with_suffix(".html"))
        b.close()
    if meldungen:
        sys.exit("Fehler im Browser: " + "; ".join(meldungen))
