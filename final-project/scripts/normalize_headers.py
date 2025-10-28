#!/usr/bin/env python3
# Cross-platform CSV header normalizer.
# - Walks a directory (default: data_work) and finds all .csv files
# - Cleans ONLY the first line (header) using rules matching the original macOS/BSD sed script:
#     * strip BOM if present
#     * spaces -> _
#     * % -> pct
#     * / -> _
#     * anything not [A-Za-z0-9_,] -> _
#     * collapse multiple underscores
#     * trim leading/trailing underscores
# Usage:
#     python scripts/normalize_headers.py --root data_work
#     python scripts/normalize_headers.py --root some/other/dir --dry-run

import argparse
import re
import sys
from pathlib import Path

def clean_header(h: str) -> str:
    # strip BOM if present (utf-8-sig)
    if h and h[0] == '\ufeff':
        h = h[1:]
    # apply transformations
    h = re.sub(r"\s+", "_", h)                 # spaces -> _
    h = h.replace("%", "pct")                  # % -> pct
    h = h.replace("/", "_")                    # / -> _
    h = re.sub(r"[^A-Za-z0-9_,]", "_", h)     # weird chars -> _
    h = re.sub(r"_{2,}", "_", h)              # collapse __
    h = re.sub(r"^_+", "", h)                 # trim leading _
    h = re.sub(r"_+$", "", h)                 # trim trailing _
    return h

def process_csv(path: Path, dry_run: bool=False) -> bool:
    # Read raw to preserve original newlines
    raw = path.read_bytes()
    # detect newline style
    text = raw.decode("utf-8-sig", errors="replace")
    # choose newline style based on original content
    newline = "\r\n" if "\r\n" in text and text.count("\r\n") >= text.count("\n") else "\n"
    lines = text.splitlines()
    if not lines:
        return False
    original = lines[0]
    cleaned = clean_header(original)
    if original == cleaned:
        return False
    lines[0] = cleaned
    if not dry_run:
        out = (newline.join(lines)).encode("utf-8")
        path.write_bytes(out)
    return True

def main(argv=None):
    p = argparse.ArgumentParser(description="Normalize headers of CSV files recursively.")
    p.add_argument("--root", default="data_work", help="Root directory to search (default: data_work)")
    p.add_argument("--dry-run", action="store_true", help="Show files that would be changed without writing")
    args = p.parse_args(argv)

    root = Path(args.root)
    if not root.exists():
        print(f"[normalize_headers] Root not found: {root}", file=sys.stderr)
        return 1

    changed = 0
    total = 0
    for csv_path in root.rglob("*.csv"):
        total += 1
        if process_csv(csv_path, dry_run=args.dry_run):
            changed += 1
            action = "(dry-run) would normalize" if args.dry_run else "normalized"
            print(f"{action}: {csv_path}")
    print(f"Processed {total} CSVs; changed {changed}.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())