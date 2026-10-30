"""Lokales Test-Moodle für jeden Rechner (Lehrkraft 2026-10-30: Pflicht für alle, auch lokal mit Codex unter Windows).

Jeder Kurs wird vor der Abnahme **live** in ein frisches Moodle 5.1.6 mit Kachelformat eingespielt und nachgezählt;
erst mit passendem Einspielprotokoll ist er abnahmefähig. Das Test-Moodle wird bei der Einrichtung einmal installiert:

    python3 werkzeug/testmoodle/testmoodle.py einrichten           # einmalig (Startprompt), ca. 600 MB Download
    python3 werkzeug/testmoodle/testmoodle.py einspielen <kurs.mbz> # nach jedem Bau: Live-Restore, Protokoll
    python3 werkzeug/testmoodle/testmoodle.py pruefen <kurs.mbz>    # vor der Abnahme: Protokoll passt zur .mbz?
    python3 werkzeug/testmoodle/testmoodle.py ansehen              # im Browser durchklicken (http://localhost:8095)
    python3 werkzeug/testmoodle/testmoodle.py stoppen              # Datenbank und Webserver beenden

Windows: PHP 8.3 (windows.php.net) und PostgreSQL 16 (Paket ohne Installer) werden in den Test-Ordner geladen, nichts
wird ins System installiert. macOS und Linux: PHP 8.2+ und PostgreSQL 16 aus dem System (brew bzw. apt); fehlen sie,
nennt das Programm den Befehl. Moodle 5.1.6 und format_tiles kommen von moodle.org, je mit Prüfsumme.
Ordner: `--ordner` oder Umgebungsvariable UPR_TESTMOODLE, sonst `%LOCALAPPDATA%\\KI-Unterrichtswerkstatt\\testmoodle`
bzw. `~/.ki-unterrichtswerkstatt/testmoodle`. Ohne Kachelformat prüfen: Umgebungsvariable KACHELN=0 und neuer Ordner.
Nur Python-Standardbibliothek.
"""
import argparse
import hashlib
import json
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path

HIER = Path(__file__).resolve().parent
WINDOWS = platform.system() == "Windows"
MOODLE_URL = "https://download.moodle.org/download.php/direct/stable501/moodle-5.1.6.zip"
PHP_LISTE = "https://windows.php.net/downloads/releases/releases.json"
PG_URL = "https://get.enterprisedb.com/postgresql/postgresql-16.11-1-windows-x64-binaries.zip"
TILES_INFO = "https://download.moodle.org/api/1.3/pluginfo.php?plugin=format_tiles&format=json&minversion=0&branch=5.1"
PORT_DB, PORT_WEB = 5433, 8095
ADMIN, PASSWORT = "admin", "Test-Moodle-2026!"   # nur lokal, nie im Netz erreichbar (127.0.0.1)
PHP_EXT = ["curl", "fileinfo", "gd", "intl", "mbstring", "openssl", "pgsql", "pdo_pgsql", "soap", "sodium", "zip", "exif"]
VCREDIST = "https://aka.ms/vs/17/release/vc_redist.x64.exe"


def ordner(arg=None):
    if arg or os.environ.get("UPR_TESTMOODLE"):
        return Path(arg or os.environ["UPR_TESTMOODLE"]).expanduser().resolve()
    if WINDOWS:
        return Path(os.environ.get("LOCALAPPDATA", Path.home())) / "KI-Unterrichtswerkstatt" / "testmoodle"
    if os.geteuid() == 0:   # Cloud-Container: PostgreSQL läuft als Benutzer postgres und braucht einen offenen Ordner
        return Path("/var/tmp/ki-unterrichtswerkstatt-testmoodle")
    return Path.home() / ".ki-unterrichtswerkstatt" / "testmoodle"


def laden(url, ziel, md5=None, sha256=None):
    if ziel.exists() and _pruefsumme_ok(ziel, md5, sha256):
        return ziel
    print(f"Lade {url.rsplit('/', 1)[-1]} …", flush=True)
    anfrage = urllib.request.Request(url, headers={"User-Agent": "KI-Unterrichtswerkstatt-Testmoodle"})
    with urllib.request.urlopen(anfrage) as antwort, open(ziel, "wb") as f:
        shutil.copyfileobj(antwort, f, 1 << 20)
    if not _pruefsumme_ok(ziel, md5, sha256):
        ziel.unlink()
        raise SystemExit(f"Prüfsumme von {ziel.name} stimmt nicht; Download verworfen. Bitte später erneut versuchen.")
    return ziel


def _pruefsumme_ok(datei, md5, sha256):
    if not (md5 or sha256):
        return True
    h = hashlib.md5() if md5 else hashlib.sha256()
    with open(datei, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest().lower() == (md5 or sha256).lower()


def _text(url):
    anfrage = urllib.request.Request(url, headers={"User-Agent": "KI-Unterrichtswerkstatt-Testmoodle"})
    with urllib.request.urlopen(anfrage) as a:
        return a.read().decode("utf-8")


def entpacken(zipdatei, ziel):
    with zipfile.ZipFile(zipdatei) as z:
        z.extractall(ziel)


# ---------------------------------------------------------------- Programme (PHP, PostgreSQL)

class Umgebung:
    def __init__(self, o):
        self.o = o
        self.moodle = o / "moodle"
        self.daten = o / "moodledata"
        self.pgdaten = o / "pgdaten"
        self.root = (not WINDOWS) and os.geteuid() == 0   # PostgreSQL startet nicht als root (Cloud-Container)

    # PHP
    def php(self):
        if WINDOWS:
            return [str(self.o / "php" / "php.exe"), "-c", str(self.o / "php" / "php.ini")]
        return ["php", "-d", "max_input_vars=5000", "-d", "memory_limit=2048M"]

    # PostgreSQL
    def pgbin(self, name):
        if WINDOWS:
            return str(self.o / "pgsql" / "bin" / f"{name}.exe")
        pfad = shutil.which(name)
        if pfad:
            return pfad
        for kandidat in sorted(Path("/usr/lib/postgresql").glob("*/bin"), reverse=True) + \
                [Path("/opt/homebrew/opt/postgresql@16/bin"), Path("/usr/local/opt/postgresql@16/bin")]:
            if (kandidat / name).exists():
                return str(kandidat / name)
        raise SystemExit("PostgreSQL fehlt. Linux: sudo apt install postgresql-16 · macOS: brew install postgresql@16")

    def pg(self, *args, pruefen=True):
        befehl = [self.pgbin(args[0]), *args[1:]]
        if self.root:
            befehl = ["su", "postgres", "-c", " ".join(shlex.quote(a) for a in befehl)]
        return subprocess.run(befehl, check=pruefen, capture_output=True, text=True)

    @property
    def port(self):
        """Datenbank-Port dieses Test-Ordners (ab 5433 der erste freie, gemerkt in port.txt)."""
        datei = self.o / "port.txt"
        if not datei.exists():
            import socket
            port = PORT_DB
            while socket.socket().connect_ex(("127.0.0.1", port)) == 0:
                port += 1
            datei.write_text(str(port))
        return int(datei.read_text())

    def db_laeuft(self):
        return self.pg("pg_ctl", "-D", str(self.pgdaten), "status", pruefen=False).returncode == 0 and \
            self.pg("pg_isready", "-h", "127.0.0.1", "-p", str(self.port), pruefen=False).returncode == 0

    def db_starten(self):
        if self.db_laeuft():
            return
        if not (self.pgdaten / "PG_VERSION").exists():
            self.pgdaten.mkdir(parents=True, exist_ok=True)
            if self.root:
                shutil.chown(self.pgdaten, "postgres")
            self.pg("initdb", "-D", str(self.pgdaten), "-U", "postgres", "-A", "trust", "-E", "UTF8")
        log = self.o / "pg.log"
        if self.root:
            log.touch(); shutil.chown(log, "postgres")
        self.pg("pg_ctl", "-D", str(self.pgdaten), "-o", f"-p {self.port} -c listen_addresses=127.0.0.1", "-l", str(log),
                "-w", "start")
        for _ in range(30):
            if self.db_laeuft():
                return
            time.sleep(1)
        raise SystemExit(f"Die Datenbank startet nicht; siehe {log}.")

    def db_stoppen(self):
        if self.db_laeuft():
            self.pg("pg_ctl", "-D", str(self.pgdaten), "-m", "fast", "stop", pruefen=False)

    def run_php(self, *args, ausgabe=False):
        r = subprocess.run([*self.php(), *args], capture_output=True, text=True, cwd=self.moodle)
        if r.returncode != 0:
            raise SystemExit(f"PHP-Fehler bei {' '.join(map(str, args[:2]))}:\n{(r.stdout + r.stderr)[-3000:]}")
        return r.stdout if ausgabe else None


def _php_windows(o):
    liste = json.loads(_text(PHP_LISTE))["8.3"]
    eintrag = next(v for k, v in liste.items() if isinstance(v, dict) and "nts" in k and "x64" in k)
    zipdatei = laden("https://windows.php.net/downloads/releases/" + eintrag["zip"]["path"], o / "php.zip",
                     sha256=eintrag["zip"]["sha256"])
    if not (o / "php" / "php.exe").exists():
        entpacken(zipdatei, o / "php")
    ini = ['extension_dir="ext"', "max_input_vars=5000", "memory_limit=2048M", "max_execution_time=0",
           "upload_max_filesize=512M", "post_max_size=512M", "date.timezone=Europe/Berlin"]
    ini += [f"extension={e}" for e in PHP_EXT]
    (o / "php" / "php.ini").write_text("\n".join(ini) + "\n", encoding="utf-8")
    r = subprocess.run([str(o / "php" / "php.exe"), "-v"], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("PHP startet nicht. Meist fehlt die Microsoft-Laufzeit „Visual C++ Redistributable“: "
                         f"{VCREDIST} installieren und `einrichten` erneut starten.")


def _pg_windows(o):
    if not (o / "pgsql" / "bin" / "pg_ctl.exe").exists():
        entpacken(laden(PG_URL, o / "pgsql.zip"), o)


def _php_posix():
    if not shutil.which("php"):
        raise SystemExit("PHP fehlt. Linux: sudo apt install php8.3-cli php8.3-pgsql php8.3-intl php8.3-mbstring "
                         "php8.3-xml php8.3-curl php8.3-zip php8.3-gd php8.3-soap · macOS: brew install php")
    v = subprocess.run(["php", "-r", "echo PHP_VERSION;"], capture_output=True, text=True).stdout
    if tuple(map(int, v.split(".")[:2])) < (8, 2):
        raise SystemExit(f"PHP {v} ist zu alt; Moodle 5.1 braucht PHP 8.2 oder neuer.")


# ---------------------------------------------------------------- Befehle

def einrichten(o):
    o.mkdir(parents=True, exist_ok=True)
    u = Umgebung(o)
    if WINDOWS:
        _php_windows(o); _pg_windows(o)
    else:
        _php_posix()
    md5 = _text(MOODLE_URL + ".md5").split("=")[-1].strip()
    if not (u.moodle / "public" / "version.php").exists():
        entpacken(laden(MOODLE_URL, o / "moodle-5.1.6.zip", md5=md5), o)
    u.db_starten()
    u.daten.mkdir(exist_ok=True)
    if not (u.moodle / "config.php").exists():
        u.pg("psql", "-h", "127.0.0.1", "-p", str(u.port), "-U", "postgres", "-qc",
             "create database moodle encoding 'UTF8' template template0;", pruefen=False)
        print("Installiere Moodle 5.1.6 (einige Minuten) …", flush=True)
        u.run_php("admin/cli/install.php", "--non-interactive", "--agree-license", "--lang=en",
                  f"--wwwroot=http://localhost:{PORT_WEB}", f"--dataroot={u.daten}", "--dbtype=pgsql",
                  "--dbhost=127.0.0.1", f"--dbport={u.port}", "--dbname=moodle", "--dbuser=postgres", "--dbpass=",
                  "--fullname=Test-Moodle", "--shortname=test", f"--adminuser={ADMIN}", f"--adminpass={PASSWORT}",
                  "--adminemail=admin@example.invalid")
    if os.environ.get("KACHELN", "1") == "1" and not (u.moodle / "public/course/format/tiles/version.php").exists():
        info = json.loads(_text(TILES_INFO))["pluginfo"]["version"]
        entpacken(laden(info["downloadurl"], o / "format_tiles.zip", md5=info["downloadmd5"]),
                  u.moodle / "public" / "course" / "format")
        u.run_php("admin/cli/upgrade.php", "--non-interactive")
    release = re.search(r"\$release\s*=\s*'([^']+)'", (u.moodle / "public" / "version.php").read_text(encoding="utf-8")).group(1)
    kacheln = (u.moodle / "public/course/format/tiles/version.php").exists()
    print(f"Test-Moodle bereit: Moodle {release}, Kachelformat {'ja' if kacheln else 'nein'}, Ordner {o}")


def einspielen(o, mbz):
    u = Umgebung(o)
    if not (u.moodle / "config.php").exists():
        einrichten(o)
    u.db_starten()
    mbz = Path(mbz).resolve()
    aus = u.run_php(str(HIER / "einspielen_als_admin.php"), str(u.moodle), str(mbz), "1", ausgabe=True)
    m = re.search(r"Restored course ID: (\d+)", aus)
    if not m:
        raise SystemExit("Einspielen ohne Kurs-Nummer abgebrochen:\n" + aus[-3000:])
    zaehlung = u.run_php(str(HIER / "zaehlen.php"), str(u.moodle), m.group(1), ausgabe=True)
    release = re.search(r"\$release\s*=\s*'([^']+)'", (u.moodle / "public" / "version.php").read_text(encoding="utf-8")).group(1)
    fmt = re.search(r"\| Format (\w+)", zaehlung)
    protokoll = {"mbz": mbz.name, "sha256": _sha256(mbz), "moodle": release,
                 "kachelformat_installiert": (u.moodle / "public/course/format/tiles/version.php").exists(),
                 "kurs_id": int(m.group(1)), "format": fmt.group(1) if fmt else "",
                 "zeit": datetime.now().isoformat(timespec="seconds"), "ok": True,
                 "zaehlung": zaehlung.splitlines()}
    ziel = _protokolldatei(mbz)
    ziel.write_text(json.dumps(protokoll, ensure_ascii=False, indent=1), encoding="utf-8")
    print(zaehlung)
    print(f"Live-Restore erfolgreich (Moodle {release}, Kurs {m.group(1)}). Protokoll: {ziel}")


def _sha256(datei):
    h = hashlib.sha256()
    with open(datei, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _protokolldatei(mbz):
    return Path(mbz).with_name(Path(mbz).stem + ".einspielprotokoll.json")


def pruefen(mbz):
    """True, wenn zur .mbz ein erfolgreiches Einspielprotokoll derselben Datei vorliegt (Pflicht vor der Abnahme)."""
    p = _protokolldatei(mbz)
    if not p.exists():
        return False, f"Kein Live-Restore: {p.name} fehlt. Erst `testmoodle.py einspielen {Path(mbz).name}`."
    d = json.loads(p.read_text(encoding="utf-8"))
    if d.get("sha256") != _sha256(mbz):
        return False, "Die .mbz wurde nach dem letzten Live-Restore neu gebaut; erneut einspielen."
    if not d.get("ok"):
        return False, "Der letzte Live-Restore war nicht erfolgreich."
    return True, f"Live-Restore in Moodle {d['moodle']} am {d['zeit']} (Format {d['format']})."


def ansehen(o):
    u = Umgebung(o)
    u.db_starten()
    router = o / "router.php"
    router.write_text(ROUTER.replace("@@ROOT@@", str(u.moodle / "public").replace("\\", "/")), encoding="utf-8")
    print(f"Test-Moodle läuft: http://localhost:{PORT_WEB}  (Anmeldung {ADMIN} / {PASSWORT}); beenden mit Strg+C")
    subprocess.run([*u.php(), "-S", f"127.0.0.1:{PORT_WEB}", "-t", str(u.moodle / "public"), str(router)],
                   cwd=u.moodle)


ROUTER = r"""<?php
// Router für den eingebauten PHP-Webserver (Moodle 5.1, Webroot public/).
$uri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$root = '@@ROOT@@';
if (preg_match('#^(.+?\.php)(/.*)?$#', $uri, $m) && is_file($root.$m[1])) return false;
if ($uri === '/' || ($uri !== '/' && is_file($root.$uri))) return false;
if (is_dir($root.$uri) && is_file($root.rtrim($uri, '/').'/index.php')) return false;
$_SERVER['SCRIPT_NAME'] = '/r.php'; $_SERVER['SCRIPT_FILENAME'] = $root.'/r.php';
require $root.'/r.php';
"""


def main():
    ap = argparse.ArgumentParser(description="Lokales Test-Moodle 5.1.6 mit Kachelformat (Live-Restore)")
    ap.add_argument("befehl", choices=["einrichten", "einspielen", "pruefen", "ansehen", "stoppen"])
    ap.add_argument("mbz", nargs="?")
    ap.add_argument("--ordner")
    a = ap.parse_args()
    o = ordner(a.ordner)
    if a.befehl in ("einspielen", "pruefen") and not a.mbz:
        raise SystemExit("Bitte die .mbz angeben.")
    if a.befehl == "einrichten":
        einrichten(o)
    elif a.befehl == "einspielen":
        einspielen(o, a.mbz)
    elif a.befehl == "pruefen":
        ok, text = pruefen(a.mbz)
        print(("OK: " if ok else "FEHLER: ") + text)
        sys.exit(0 if ok else 1)
    elif a.befehl == "ansehen":
        ansehen(o)
    else:
        Umgebung(o).db_stoppen()
        print("Test-Moodle gestoppt.")


if __name__ == "__main__":
    main()
