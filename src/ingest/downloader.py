#src/downloader.py
"""
Bulk fetcher for multiple DataLink datasets.

- Iterates ALL_DATASETS and processes each in sequence.
- Clear progress printouts for each dataset:
    - Start notice with index
    - Download progress (percent or bytes)
    - ZIP validation
    - Extraction and copy steps
    - Already-present early exit
- No special symbols in output.
"""

import sys
import time
from pathlib import Path
import urllib.request
import zipfile
import tempfile
import shutil


from app.datasets import DataLink
from app import AppConfig


def safe_mkdir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def accdb_already_there(dest_dir: Path, accdb_basename: str) -> Path | None:
    candidate = dest_dir / accdb_basename
    return candidate if candidate.exists() else None


def _norm_zip_path(p: str) -> str:
    p = p.replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    while p.startswith("/"):
        p = p[1:]
    return p


def _choose_best_member(namelist: list[str], tail: str) -> str | None:
    tail = _norm_zip_path(tail)
    matches = [name for name in namelist if _norm_zip_path(name).endswith(tail)]
    if not matches:
        return None
    matches.sort(key=lambda s: len(s))  # shortest full path first
    return matches[0]


def _format_bytes(n: int) -> str:
    # Human friendly bytes
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def download_zip_with_progress(url: str, tmp_zip_path: Path):
    """
    Stream download with progress printing.
    Prints either percentage (when content-length is available) or running byte count.
    """
    chunk_size = 1024 * 256  # 256 KB
    start = time.time()

    with urllib.request.urlopen(url) as r, tmp_zip_path.open("wb") as f:
        total = r.headers.get("Content-Length")
        total = int(total) if total is not None else None
        downloaded = 0
        last_print = 0.0

        print("  step: downloading")
        while True:
            chunk = r.read(chunk_size)
            if not chunk:
                break
            f.write(chunk)
            downloaded += len(chunk)

            now = time.time()
            # throttle prints to ~5 per second
            if now - last_print >= 0.2:
                if total:
                    pct = downloaded / total * 100
                    print(f"    progress: {pct:6.2f}%  ({_format_bytes(downloaded)} of {_format_bytes(total)})", end="\r", flush=True)
                else:
                    print(f"    progress: {_format_bytes(downloaded)} downloaded", end="\r", flush=True)
                last_print = now

        # ensure final line is printed cleanly
        if total:
            print(f"    progress: 100.00%  ({_format_bytes(downloaded)} of {_format_bytes(total)})")
        else:
            print(f"    progress: {_format_bytes(downloaded)} downloaded")

    elapsed = time.time() - start
    print(f"  done: download finished in {elapsed:.1f}s")


def extract_target_from_zip(zip_path: Path, target_rel_path: str, dest_path: Path) -> bool:
    """
    Extract the member whose ZIP path ends with target_rel_path into dest_path.
    Returns True on success, False if not found.
    """
    print("  step: validating zip")
    with zipfile.ZipFile(zip_path, "r") as zf:
        namelist = zf.namelist()
        member = _choose_best_member(namelist, target_rel_path)
        if member is None:
            return False
        print("  step: extracting target file")
        safe_mkdir(dest_path.parent)
        with zf.open(member) as src, dest_path.open("wb") as dst:
            shutil.copyfileobj(src, dst)
    print("  done: extraction complete")
    return True


def fetch_accdb_from_datalink(link: DataLink) -> int:
    """
    - Destination: AppConfig.ny_edu_data / link.folder_name / basename(path_to_data_from_zip_root)
    - If destination file exists, skip download.
    - Download, validate, extract, and place.
    Returns a status code similar to typical CLI tools.
    """
    dest_dir = Path(AppConfig.ny_edu_data) / link.folder_name
    safe_mkdir(dest_dir)

    accdb_basename = Path(link.path_to_data_from_zip_root).name
    dest_path = dest_dir / accdb_basename

    if dest_path.exists():
        print(f"  info: destination already has {dest_path}")
        return 0

    with tempfile.TemporaryDirectory(prefix="accdb_fetch_") as tdir:
        tdir = Path(tdir)
        zip_path = tdir / "payload.zip"

        try:
            download_zip_with_progress(link.url, zip_path)
        except Exception as e:
            print(f"  error: failed to download zip. detail: {e}")
            return 2

        try:
            ok = extract_target_from_zip(zip_path, link.path_to_data_from_zip_root, dest_path)
        except zipfile.BadZipFile:
            print("  error: the downloaded file is not a valid zip")
            return 3

        if not ok:
            hint = _norm_zip_path(link.path_to_data_from_zip_root)
            print(f"  error: target not found in zip. looked for path ending with '{hint}'")
            return 4

        if dest_path.exists():
            print(f"  done: placed file at {dest_path}")
            return 0

        print("  error: destination file missing after extraction")
        return 5




from app.datasets import STUDENT_EDUCATOR_DATABASE_23_24

def main():
    results = []
    print(f" dataset: {STUDENT_EDUCATOR_DATABASE_23_24.folder_name}")
    print(f"  source: {STUDENT_EDUCATOR_DATABASE_23_24.url}")
    print(f"  target: {AppConfig.ny_edu_data}/{STUDENT_EDUCATOR_DATABASE_23_24.folder_name}/{Path(STUDENT_EDUCATOR_DATABASE_23_24.path_to_data_from_zip_root).name}")
    status = fetch_accdb_from_datalink(STUDENT_EDUCATOR_DATABASE_23_24)
    results.append((STUDENT_EDUCATOR_DATABASE_23_24.folder_name, status))
    print("\nsummary:")
    for name, status in results:
        if status == 0:
            print(f"  {name}: ok")
        elif status == 2:
            print(f"  {name}: download failed")
        elif status == 3:
            print(f"  {name}: bad zip")
        elif status == 4:
            print(f"  {name}: target not found in zip")
        else:
            print(f"  {name}: error code {status}")

    # nonzero exit if any failed
    if any(code != 0 for _, code in results):
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    # You can swap in any DataLink you want here, or import fetch_accdb_from_datalink elsewhere.
    main()
