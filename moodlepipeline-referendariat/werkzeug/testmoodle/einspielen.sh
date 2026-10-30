#!/bin/bash
# Echtes Einspielen einer Sicherung in ein frisches Moodle 5.1.6 (Cloud-Container, PHP 8.3 + PostgreSQL 16).
#   werkzeug/testmoodle/einspielen.sh <kurs.mbz> [arbeitsordner]
# Lädt Moodle einmal herunter, installiert es ohne Webserver (mit Kachelformat format_tiles), spielt die Sicherung
# per CLI ein und zählt nach. Ohne Kachelformat: KACHELN=0 werkzeug/testmoodle/einspielen.sh <kurs.mbz> <neuer ordner>
set -euo pipefail
HIER=$(dirname "$(realpath "$0")")   # vor dem cd bestimmen (sonst ist ein relativer Aufrufpfad falsch)
MBZ=$(realpath "$1"); W=${2:-/var/tmp/testmoodle}; P=/var/tmp/testmoodle_pg; B=/usr/lib/postgresql/16/bin
PHP="php -d max_input_vars=5000 -d memory_limit=2048M"
DB=moodle; [ "$W" = /var/tmp/testmoodle ] || DB="moodle_$(echo "$W" | md5sum | cut -c1-8)"   # je Arbeitsordner eine Datenbank
mkdir -p "$W/data" "$P"
if [ ! -f "$W/moodle/public/version.php" ]; then
  curl -sS -fL -o "$W/moodle.tgz" "https://download.moodle.org/download.php/direct/stable501/moodle-5.1.6.tgz"
  tar -xzf "$W/moodle.tgz" -C "$W"
fi
chown postgres "$P"
if ! pg_isready -h /tmp -p 5433 -q; then
  [ -d "$P/data" ] || su postgres -c "$B/initdb -D $P/data -A trust -U postgres >/dev/null"
  su postgres -c "$B/pg_ctl -D $P/data -o '-p 5433 -k /tmp' -l $P/log start" >/dev/null; sleep 3
fi
cd "$W/moodle"
if [ ! -f config.php ]; then
  psql -h /tmp -p 5433 -U postgres -qc "create database $DB encoding 'UTF8' template template0;"
  $PHP admin/cli/install.php --non-interactive --agree-license --lang=en --wwwroot=http://localhost:8095 \
    --dataroot="$W/data" --dbtype=pgsql --dbhost=/tmp --dbport=5433 --dbname=$DB --dbuser=postgres --dbpass= \
    --fullname=Testlabor --shortname=lab --adminuser=admin --adminpass='Lab-Test-2026!' \
    --adminemail=admin@example.invalid --skip-database >/dev/null 2>&1 || true
  $PHP admin/cli/install_database.php --agree-license --lang=en --fullname=Testlabor --shortname=lab \
    --adminuser=admin --adminpass='Lab-Test-2026!' --adminemail=admin@example.invalid >/dev/null
fi
# Kachelformat wie im Schul-Moodle (Standard, Lehrkraft 2026-10-30): format_tiles aus dem Plugin-Verzeichnis von
# moodle.org, Prüfsumme geprüft. KACHELN=0 prüft das Einspielen in ein Moodle ohne Kachelformat.
if [ "${KACHELN:-1}" = "1" ] && [ ! -f public/course/format/tiles/version.php ]; then
  INFO=$(curl -sS -f "https://download.moodle.org/api/1.3/pluginfo.php?plugin=format_tiles&format=json&minversion=0&branch=5.1")
  URL=$(echo "$INFO" | python3 -c 'import json,sys; print(json.load(sys.stdin)["pluginfo"]["version"]["downloadurl"])')
  MD5=$(echo "$INFO" | python3 -c 'import json,sys; print(json.load(sys.stdin)["pluginfo"]["version"]["downloadmd5"])')
  curl -sS -fL -o "$W/tiles.zip" "$URL"
  echo "$MD5  $W/tiles.zip" | md5sum -c --quiet
  (cd public/course/format && unzip -q -o "$W/tiles.zip")
  $PHP admin/cli/upgrade.php --non-interactive >/dev/null
  echo "Kachelformat format_tiles installiert."
fi
if [ "${KACHELN:-1}" = "0" ] && [ -f public/course/format/tiles/version.php ]; then
  echo "Hinweis: Dieses Test-Moodle hat das Kachelformat schon; für KACHELN=0 einen neuen Arbeitsordner angeben."
fi
# als Administrator angemeldet: sonst verwirft Moodle die Rechte-Änderungen der Aktivitäten
$PHP "$HIER/einspielen_als_admin.php" "$W/moodle" "$MBZ" 1 | tee "$W/restore.log" | tail -2
ID=$(grep -o "Restored course ID: [0-9]*" "$W/restore.log" | grep -o "[0-9]*$")
sed "s/^\$c = 2;/\$c = $ID;/" "$HIER/zaehlen.php" > "$W/zaehlen.php"
$PHP "$W/zaehlen.php" "$W/moodle"
