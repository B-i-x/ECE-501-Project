import sqlite3, os
import pandas as pd
import numpy as np
import matplotlib.pylab as plt
import seaborn as sns
import sqlalchemy as sa
import pyodbc
from collections import Counter
from pathlib import Path
from sqlalchemy import create_engine, URL

DATA_PATH = r"..\data\nyse_data\reportcard_database_23_24\SRC2024_Group5.accdb"
connection = rf"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={DATA_PATH};"
#src = pyodbc.connect(rf"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={DATA_PATH};")

#connecting sqlAlchemy to pyodbc
src = pyodbc.connect(connection)
src_url = URL.create("access+pyodbc", query={"odbc_connect": connection})
engine = create_engine(src_url)

dst = sqlite3.connect("../data/sqlite/studed.db")


cur = src.cursor()

for table_info in cur.tables(tableType='TABLE'):
    print(table_info.table_name)

# Enumerate ALL objects; don't restrict by tableType
rows = list(cur.tables())

# Keep real stuff; skip Access system/temp objects
ALLOW_TYPES = {"TABLE", "VIEW", "SYSTEM TABLE"}
def wanted(r):
    name = (r.table_name or "").strip()
    if not name:
        return False
    # Skip system & temp
    if name.startswith("MSys") or name.startswith("~"):
        return False
    return (r.table_type or "").upper() in ALLOW_TYPES

objs = [r for r in rows if wanted(r)]

# Show what we found by type
counts = Counter((r.table_type or "UNKNOWN").upper() for r in objs)
print("Discovered objects:", counts)

# Dedup by name (Access can return duplicates with different schema/catalog)
seen = set()
tables = []
for r in objs:
    nm = r.table_name
    if nm not in seen:
        seen.add(nm)
        tables.append(nm)

print(f"Will attempt to copy {len(tables)} objects:")
for nm in tables:
    print(" -", nm)

# Copy loop
copied, skipped = [], []
for t in tables:
    try:
        # Some Access "VIEWs" (saved queries) can be parameterized or call VBA functions;
        # those will fail over ODBC—catch and skip them.
        with engine.begin() as src:
            df = pd.read_sql(f"SELECT * FROM [{t}]", src)
            df.to_sql(t, dst, if_exists='replace', index=False)
            copied.append(t)
            print(f"✔ Copied: {t} ({len(df)} rows)")
    except Exception as e:
        skipped.append((t, str(e)))
        print(f"✖ Skipped: {t} -> {e}")

print("\nSummary:")
print(f"Copied: {len(copied)}")
if skipped:
    print(f"Skipped: {len(skipped)}")
    for name, err in skipped:
        print(f" - {name}: {err}")

dst.close(); src.close()
