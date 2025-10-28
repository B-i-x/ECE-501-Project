#!/usr/bin/env python3
import re
import sys
import time
import zipfile
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm  # for progress bars

DOWNLOADS_URL = "https://data.nysed.gov/downloads.php"
OUT_DIR = Path(__file__).resolve().parents[1] / "data_raw"
START_YEAR = 2015
CURRENT_YEAR = datetime.now().year

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://data.nysed.gov/",
}


def fetch_html():
    r = requests.get(DOWNLOADS_URL, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


def find_report_card_links(soup):
    """Find all ZIP links matching SRC20**.zip pattern."""
    links = {}
    for a in soup.find_all("a", href=True):
        href = a["href"]
        match = re.search(r"(SRC20\d{2})\.zip", href, re.I)
        if match:
            year = int(match.group(1)[-4:])  # extract year
            if START_YEAR <= year <= CURRENT_YEAR:
                links[year] = urljoin(DOWNLOADS_URL, href)
    return links


def download_file(url, dest):
    """Download file to destination with progress bar."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, headers=HEADERS, stream=True, timeout=120) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        with open(dest, "wb") as f, tqdm(
            total=total, unit="B", unit_scale=True, desc=dest.name
        ) as pbar:
            for chunk in r.iter_content(8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))


def unzip_file(zip_path):
    """Unzip file into folder with same name (SRC20XX)."""
    extract_dir = zip_path.with_suffix("")
    if extract_dir.exists():
        print(f"    Skipping unzip (already exists): {extract_dir.name}")
        return
    with zipfile.ZipFile(zip_path, "r") as zf:
        extract_dir.mkdir(parents=True, exist_ok=True)
        zf.extractall(extract_dir)
    print(f"    Unzipped to {extract_dir.name}")


def main():
    print(f"Fetching links from {DOWNLOADS_URL} ...")
    html = fetch_html()
    soup = BeautifulSoup(html, "html.parser")
    links = find_report_card_links(soup)

    if not links:
        print("No SRC20**.zip links found. Page structure may have changed.", file=sys.stderr)
        sys.exit(1)

    for year in range(START_YEAR, CURRENT_YEAR + 1):
        url = links.get(year)
        if not url:
            print(f"No Report Card ZIP found for {year}")
            continue

        filename = Path(url).name  # e.g., SRC2022.zip
        zip_path = OUT_DIR / filename

        if zip_path.exists():
            print(f"[{year}] Skipping download (exists): {filename}")
        else:
            print(f"[{year}] Downloading {filename} ...")
            try:
                download_file(url, zip_path)
                time.sleep(1)
            except Exception as e:
                print(f"Download failed for {year}: {e}", file=sys.stderr)
                continue

        try:
            unzip_file(zip_path)
        except Exception as e:
            print(f"Unzip failed for {year}: {e}", file=sys.stderr)

    print("All Report Card databases processed.")


if __name__ == "__main__":
    main()
