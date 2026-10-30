"""Prüft die Skills von Pipeline 2 (.claude/skills): Kopf mit name und description, jeder genannte Pfad existiert,
jeder im Hauptskill genannte Fach-Skill ist vorhanden. Teil des Probelaufs.

    python3 werkzeug/skills_pruefen.py
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILLS = REPO / ".claude" / "skills"
BASIS = [REPO, REPO / "werkzeug", REPO / "werkzeug" / "vorlagen", REPO / "werkzeug" / "schaltplan",
         REPO / "docs" / "stilreferenz", REPO / "docs" / "stilreferenz" / "vorlagen",
         REPO / "docs" / "stilreferenz" / "vorlagen" / "muster", REPO / "werkzeug" / "simulation",
         REPO / "werkzeug" / "technologieschema", REPO / "werkzeug" / "quellen", REPO / "werkzeug" / "rechnen",
         REPO / "werkzeug" / "installationsplan", REPO / "werkzeug" / "uebersichtsschaltplan",
         REPO / "werkzeug" / "schaltplan" / "beispiele", REPO / "docs" / "regeln",
         REPO / "werkzeug" / "installationsplan" / "beispiele", REPO / "werkzeug" / "uebersichtsschaltplan" / "beispiele"]
# entstehen erst bei der Arbeit (Eingang aus Pipeline 1, erste aufgenommene Quelle)
ZUR_LAUFZEIT = {"Materialauftrag.docx", "Quellen/_karte/karte.md", "Quellen/_karte/karte.csv", "quellen/_karte/karte.md", "quellen/_karte/karte.csv", "karte.md"}
fehler = []
namen = {d.name for d in SKILLS.iterdir() if (d / "SKILL.md").exists()}
for d in sorted(SKILLS.iterdir()):
    datei = d / "SKILL.md"
    if not datei.exists():
        continue
    t = datei.read_text(encoding="utf-8")
    kopf = re.match(r"---\nname: (.+)\ndescription: (.+)\n---\n", t)
    if not kopf or kopf.group(1) != d.name:
        fehler.append(f"{d.name}: Kopf fehlt oder name passt nicht zum Ordner")
    for pfad in re.findall(r"`([\w./*-]+\.(?:py|md|docx|sty|js|html|csv|png))`", t):
        if "*" in pfad or "<" in pfad or pfad in ZUR_LAUFZEIT:
            continue
        if not any((b / pfad).exists() for b in BASIS):
            fehler.append(f"{d.name}: Pfad {pfad} nicht gefunden")
haupt = (SKILLS / "materialauftrag" / "SKILL.md").read_text(encoding="utf-8")
for s in set(re.findall(r"\| `([a-z]+)` \|", haupt)) - namen:
    fehler.append(f"materialauftrag: Fach-Skill {s} fehlt")
print(f"Skills geprüft: {len(namen)}; Fehler: {len(fehler)}")
for f in fehler:
    print("  [Fehler]", f)
sys.exit(1 if fehler else 0)
