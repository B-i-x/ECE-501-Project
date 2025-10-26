#!/usr/bin/env bash
set -euo pipefail
sqlite3 db/nysed.sqlite "VACUUM; ANALYZE; PRAGMA optimize;"
