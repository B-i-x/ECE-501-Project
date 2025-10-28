#!/usr/bin/env python3
# Cross-platform build/task runner.
# Replaces GNU Make targets with Python subcommands:
#   - normalize : run header normalization on CSVs
#   - extract   : run ETL extract script if present
#   - clean     : remove generated files in data_work/
#   - build     : typical pipeline (extract -> normalize)

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"
ETL = ROOT / "etl"

def cmd_normalize(args) -> int:
    script = SCRIPTS / "normalize_headers.py"
    if not script.exists():
        print(f"[build] Missing script: {script}", file=sys.stderr)
        return 1
    cmd = [sys.executable, str(script), "--root", args.root]
    if args.dry_run:
        cmd.append("--dry-run")
    print("[build] Running:", " ".join(cmd))
    return subprocess.call(cmd)

def cmd_extract(args) -> int:
    # Run your ETL entrypoint if it exists; otherwise, no-op
    etl_entry = ETL / "extract_report_card.py"
    if not etl_entry.exists():
        print(f"[build] No ETL entrypoint found at {etl_entry}; skipping extract.")
        return 0
    cmd = [sys.executable, str(etl_entry)]
    print("[build] Running:", " ".join(cmd))
    return subprocess.call(cmd)

def cmd_clean(args) -> int:
    target = Path(args.target)
    if not target.exists():
        print(f"[build] Nothing to clean: {target}")
        return 0
    if target.is_file():
        target.unlink(missing_ok=True)
        print(f"[build] Removed file: {target}")
        return 0
    # remove everything inside target but keep the folder
    removed = 0
    for p in target.rglob("*"):
        try:
            if p.is_file() or p.is_symlink():
                p.unlink(missing_ok=True)
                removed += 1
            elif p.is_dir():
                shutil.rmtree(p)
                removed += 1
        except Exception as e:
            print(f"[build] Warning: could not remove {p}: {e}", file=sys.stderr)
    print(f"[build] Cleaned {removed} items in {target}")
    return 0

def cmd_build(args) -> int:
    # Typical pipeline: extract -> normalize
    rc = cmd_extract(args)
    if rc != 0:
        return rc
    return cmd_normalize(args)

def make_parser():
    ap = argparse.ArgumentParser(description="Cross-platform task runner (Python).")
    ap.add_argument("--root", default="data_work", help="Root folder for CSVs (normalize).")
    ap.add_argument("--dry-run", action="store_true", help="Dry-run where supported.")
    sub = ap.add_subparsers(dest="command", required=True)

    sub.add_parser("normalize", help="Normalize CSV headers").set_defaults(func=cmd_normalize)
    sub.add_parser("extract", help="Run ETL extraction if available").set_defaults(func=cmd_extract)

    p_clean = sub.add_parser("clean", help="Remove generated artifacts (default: data_work)")
    p_clean.add_argument("--target", default="data_work", help="Folder or file to clean")
    p_clean.set_defaults(func=cmd_clean)

    sub.add_parser("build", help="Run standard pipeline (extract -> normalize)").set_defaults(func=cmd_build)
    return ap

def main(argv=None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    return args.func(args)

if __name__ == "__main__":
    raise SystemExit(main())