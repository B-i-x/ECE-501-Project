#!/usr/bin/env python3
"""
Fetch a ZIP from a URL, extract, locate an .accdb, and place it in:
    data/nyse_data/{file_folder}

Usage examples:
  python fetch_accdb.py \
      --url "https://example.com/nyse-data.zip" \
      --file-folder "2025-09-24" \
      --zip-root "unzipped/top/dir"        # OPTIONAL: path inside the ZIP
      --accdb-name "nyse_data.accdb"       # OPTIONAL: exact .accdb to pick

Notes:
- If --zip-root is provided, the search for .accdb starts there (inside the archive).
- If --accdb-name is provided, we'll select that file if found; otherwise first .accdb found.
- If the destination already contains the .accdb (by that name if provided, otherwise any .accdb),
  the script exits without downloading.
"""

import argparse
import sys
from pathlib import Path
import urllib.request
import zipfile
import tempfile
import shutil


def safe_mkdir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def accdb_already_there(dest_dir: Path, accdb_name: str | None) -> Path | None:
    if accdb_name:
        candidate = dest_dir / accdb_name
        return candidate if candidate.exists() else None
    # No specific name: if any .accdb is present, consider it "already there"
    for p in dest_dir.glob("*.accdb"):
        if p.is_file():
            return p
    return None


def download_zip(url: str, tmp_zip_path: Path):
    with urllib.request.urlopen(url) as r, tmp_zip_path.open("wb") as f:
        shutil.copyfileobj(r, f)


def find_accdb_in_extract(extract_root: Path, zip_root: str | None, accdb_name: str | None) -> Path | None:
    """
    Returns Path to the located .accdb inside extract_root, or None if not found.
    - If zip_root is provided, search starts at extract_root/zip_root.
    - If accdb_name is provided, prefer a file with that exact name.
    """
    search_base = extract_root / zip_root if zip_root else extract_root
    if not search_base.exists():
        return None

    # If specific name given, look for it first
    if accdb_name:
        for p in search_base.rglob(accdb_name):
            if p.is_file() and p.suffix.lower() == ".accdb":
                return p

    # Otherwise return the first .accdb we find
    for p in search_base.rglob("*.accdb"):
        if p.is_file():
            return p
    return None


def main():
    parser = argparse.ArgumentParser(description="Download ZIP, extract .accdb, place into data/nyse_data/{file_folder}.")
    parser.add_argument("--url", required=True, help="Direct URL to the ZIP file.")
    parser.add_argument("--file-folder", required=True, help="Subfolder name under data/nyse_data for destination.")
    parser.add_argument("--zip-root", default=None,
                        help="(Optional) Path inside the ZIP to start searching for the .accdb (e.g., 'top/dir').")
    parser.add_argument("--accdb-name", default=None,
                        help="(Optional) Exact .accdb file name to select if multiple exist.")
    args = parser.parse_args()

    dest_dir = Path("data") / "nyse_data" / args.file_folder
    safe_mkdir(dest_dir)

    # Skip if we already have it
    existing = accdb_already_there(dest_dir, args.accdb_name)
    if existing:
        print(f"✔ ACCDB already present at: {existing}")
        sys.exit(0)

    # Work in a temp area
    with tempfile.TemporaryDirectory(prefix="accdb_fetch_") as tdir:
        tdir = Path(tdir)
        zip_path = tdir / "payload.zip"

        print(f"↓ Downloading ZIP from {args.url} ...")
        try:
            download_zip(args.url, zip_path)
        except Exception as e:
            print(f"✖ Failed to download ZIP: {e}", file=sys.stderr)
            sys.exit(2)

        # Extract
        extract_root = tdir / "extract"
        safe_mkdir(extract_root)

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_root)
        except zipfile.BadZipFile:
            print("✖ The downloaded file is not a valid ZIP.", file=sys.stderr)
            sys.exit(3)

        # Locate .accdb
        accdb_path = find_accdb_in_extract(extract_root, args.zip_root, args.accdb_name)
        if not accdb_path:
            base_hint = f"{args.zip_root}/" if args.zip_root else ""
            print(f"✖ No .accdb found under extracted '{base_hint}'.", file=sys.stderr)
            sys.exit(4)

        final_name = args.accdb_name if args.accdb_name else accdb_path.name
        dest_path = dest_dir / final_name

        # Double-check we didn't race with a parallel process
        if dest_path.exists():
            print(f"✔ ACCDB already present at: {dest_path}")
            sys.exit(0)

        # Copy into place
        shutil.copy2(accdb_path, dest_path)
        print(f"✔ ACCDB copied to: {dest_path}")


if __name__ == "__main__":
    main()
