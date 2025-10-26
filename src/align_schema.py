import pandas as pd
import pyodbc, sqlalchemy
import sqlite3
import glob
import os

from src.downloader import safe_mkdir

#iterate over files in parent directory
directory = r"data/ny_edu_data/"
wildcard = "**"
db_files = glob.glob(os.path.join(directory,wildcard, "*.*db"), recursive=True)

# SQLite database to store results

sql_con = sqlite3.connect("/data/sqlite/merged_normalized_db.db")
"""
# Define optional column name mappings to align schemas
column_map = {
    'ENTITY_ID': 'Entity_ID'
}
"""
# Track all unique columns seen
all_columns = set()

# First pass — collect all column names across databases
for db_file in db_files:
    connection  = (
        rf"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_file};"
    )
    conn = pyodbc.connect(connection)
    cursor = conn.cursor()
    tables = [t.table_name for t in cursor.tables(tableType='TABLE')]
    print(tables)


    for table in tables:
        df = pd.read_sql(f"SELECT * FROM [{table}]", conn)
        all_columns.update(df.columns)
        #df.to_sql(table, sql_con, if_exists='replace', index=False)
        #copied.append(table)
    conn.close()

# Convert set to list for consistent ordering
all_columns = list(all_columns)
print(f"Unified schema columns: {all_columns}")

# Second pass — load, normalize, and insert
for db_file in db_files:
    print(f"Processing {db_files}...")
    connection = (
        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
        rf"DBQ={db_files};"
    )
    conn = pyodbc.connect(connection)
    cursor = conn.cursor()
    tables = [t.table_name for t in cursor.tables(tableType='TABLE')]

    for table in tables:
        df = pd.read_sql(f"SELECT * FROM [{table}]", conn)

        # Reindex to full schema (add missing columns)
        df = df.reindex(columns=all_columns)

        # Add metadata columns
        df["SourceFile"] = os.path.basename(db_file)
        df["SourceTable"] = table

        # Write to SQLite
        df.to_sql("CombinedData", sql_con, if_exists="append", index=False)

    conn.close()

sql_con.close()