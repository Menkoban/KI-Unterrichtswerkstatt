"""Sprachausgabe für Sprachnachrichten im Material (z. B. Meisterin im Einstieg), Lehrkraft 2026-10-16:
Microsoft-Edge-Stimmen über edge-tts (Neural-Stimmen, Deutsch). Text wird an den Dienst geschickt: nur fiktive
Inhalte, keine echten Namen von Lernenden. Ergebnis immer als KI-gestützt kennzeichnen; keine echte Stimme einer
realen Person nachbilden.

    python3 werkzeug/audio/sprachausgabe.py --stimme de-DE-KatjaNeural --tempo -5% --text "…" ziel.mp3
    python3 werkzeug/audio/sprachausgabe.py --regie text.txt --stimme … ziel.mp3   # betont, Satz für Satz
    python3 werkzeug/audio/sprachausgabe.py --stimmen          # deutsche Stimmen auflisten

Betonung (Lehrkraft 2026-10-16: „mit Betonung und Elan, so wie man es wirklich sagen würde“): Der freie Dienst
nimmt keine Sprechstile (SSML express-as) an, nur Tempo, Tonhöhe und Lautstärke je Anfrage. Darum spricht die
Regie-Datei Satz für Satz mit eigener Einstellung und setzt die Sätze mit natürlichen Pausen zusammen. Je Zeile ein
ganzer Satz (nie mitten im Satz trennen, sonst fällt die Stimme am Komma ab), vorn optional
`[tempo tonhöhe lautstärke pause_ms]`, z. B. `[+10% +8Hz +10% 400] Moin zusammen, hier ist Svenja!`

Im Cloud-Container prüft ein Proxy TLS mit eigener Zertifizierungsstelle: Ist SSL_CERT_FILE gesetzt bzw.
/root/.ccr/ca-bundle.crt vorhanden, wird diese Datei für die Prüfung genutzt (Prüfung bleibt eingeschaltet).
"""
import argparse
import asyncio
import os
import re
import ssl
import subprocess
import tempfile
from pathlib import Path

import edge_tts
from edge_tts import communicate as _comm

BUNDLE = os.environ.get("SSL_CERT_FILE") or ("/root/.ccr/ca-bundle.crt" if Path("/root/.ccr/ca-bundle.crt").exists() else None)
if BUNDLE:
    _comm._SSL_CTX = ssl.create_default_context(cafile=BUNDLE)
PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")


async def sprechen(text, ziel, stimme="de-DE-KatjaNeural", tempo="-5%"):
    await edge_tts.Communicate(text, stimme, rate=tempo, proxy=PROXY).save(str(ziel))
    return Path(ziel)


REGIE = re.compile(r"^\[([+-]\d+%)\s+([+-]\d+Hz)\s+([+-]\d+%)\s+(\d+)\]\s*(.+)$")


def regie_lesen(text, tempo):
    """Zeilen der Regie-Datei -> (Satz, Tempo, Tonhöhe, Lautstärke, Pause in ms)."""
    saetze = []
    for z in text.splitlines():
        z = z.strip()
        if not z or z.startswith("#"):
            continue
        m = REGIE.match(z)
        saetze.append((m.group(5), m.group(1), m.group(2), m.group(3), int(m.group(4))) if m
                      else (z, tempo, "+0Hz", "+0%", 350))
    return saetze


async def sprechen_regie(text, ziel, stimme="de-DE-KatjaNeural", tempo="-5%"):
    """Satz für Satz mit eigener Betonung sprechen, mit Pausen zusammensetzen, Lautheit angleichen (ffmpeg)."""
    ziel = Path(ziel)
    with tempfile.TemporaryDirectory() as tmp:
        liste = []
        for i, (satz, t, h, l, pause) in enumerate(regie_lesen(text, tempo)):
            mp3, wav = Path(tmp, f"{i:02d}.mp3"), Path(tmp, f"{i:02d}.wav")
            await edge_tts.Communicate(satz, stimme, rate=t, pitch=h, volume=l, proxy=PROXY).save(str(mp3))
            # Stille am Rand der Einzelsätze kürzen, danach die gewünschte Pause anhängen
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp3), "-af",
                            "silenceremove=start_periods=1:start_threshold=-50dB,areverse,"
                            "silenceremove=start_periods=1:start_threshold=-50dB,areverse,"
                            f"apad=pad_dur={pause / 1000}", "-ar", "24000", "-ac", "1", str(wav)], check=True)
            liste.append(f"file '{wav}'")
        Path(tmp, "liste.txt").write_text("\n".join(liste))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(Path(tmp, "liste.txt")),
                        "-af", "adelay=250,loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "24000", "-ac", "1",
                        "-b:a", "64k", str(ziel)], check=True)
    return ziel


async def stimmen():
    ctx = ssl.create_default_context(cafile=BUNDLE) if BUNDLE else None
    import aiohttp
    from edge_tts.voices import __list_voices
    async with aiohttp.ClientSession(trust_env=True) as s:
        return [v for v in await __list_voices(s, ctx, PROXY) if v["Locale"] == "de-DE"]


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("ziel", nargs="?")
    a.add_argument("--text")
    a.add_argument("--stimme", default="de-DE-KatjaNeural")
    a.add_argument("--tempo", default="-5%")
    a.add_argument("--regie", help="Regie-Datei: je Zeile ein Satz, optional [tempo tonhöhe lautstärke pause_ms]")
    a.add_argument("--stimmen", action="store_true")
    arg = a.parse_args()
    if arg.stimmen:
        for v in asyncio.run(stimmen()):
            print(v["ShortName"], v["Gender"])
    elif arg.regie:
        print(asyncio.run(sprechen_regie(Path(arg.regie).read_text(encoding="utf-8"), arg.ziel, arg.stimme, arg.tempo)))
    else:
        print(asyncio.run(sprechen(arg.text, arg.ziel, arg.stimme, arg.tempo)))
