#!/usr/bin/env bash
set -euo pipefail
sqlite3 db/nysed.sqlite < sql/99_checks.sql | tee design/checks_out.txt
