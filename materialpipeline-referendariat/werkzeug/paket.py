"""Stundenmaterial als Gesamt-PDF, nur auf Anforderung der Lehrkraft (gearbeitet wird in Word; Lehrkraft 2026-10-23).

    python3 werkzeug/paket.py <LS-Materialordner> <DSnn> <Zielordner>

Reihenfolge: Arbeitsblätter der Lernsituation (Arbeitsblaetter_LSnn.docx), dann die Anlagen der Doppelstunde nach
Nummer (Anl_<n>_*.docx/.pptx); die Erwartungshorizonte (EH_*.docx) kommen in ein eigenes PDF, damit sie nicht mit
ausgeteilt werden. Der Zielordner liegt außerhalb des Repos (PDF gehört nicht in die Ablage).
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def nummer(pfad):
    m = re.match(r"Anl_(\d+)_", pfad.name)
    return (int(m.group(1)), pfad.suffix != ".pptx", pfad.name) if m else (999, True, pfad.name)


def pdf(dateien, ziel, tmp):
    teile = []
    for d in dateien:
        subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(tmp), str(d)],
                       check=True, capture_output=True, timeout=180)
        teile.append(str(Path(tmp) / (d.stem + ".pdf")))
    subprocess.run(["pdfunite", *teile, str(ziel)], check=True)
    return ziel


def paket(material, ds, ziel):
    material, ziel = Path(material), Path(ziel)
    ziel.mkdir(parents=True, exist_ok=True)
    ls = material.parent.name.split("_")[0]                    # z. B. LS02
    blaetter = sorted(material.glob("Arbeitsblaetter_*.docx"))
    anlagen = sorted([p for p in (material / ds).glob("Anl_*") if p.suffix in (".docx", ".pptx")], key=nummer)
    ehs = sorted((material / ds).glob("EH_*.docx"))
    with tempfile.TemporaryDirectory() as tmp:
        a = pdf(blaetter + anlagen, ziel / f"{ls}_{ds}_Material_gesamt.pdf", tmp)
        e = pdf(ehs, ziel / f"{ls}_{ds}_Erwartungshorizonte.pdf", tmp) if ehs else None
    return a, e


if __name__ == "__main__":
    for p in paket(*sys.argv[1:4]):
        if p:
            print(p)
