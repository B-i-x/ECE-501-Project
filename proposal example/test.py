import sqlite3, pandas as pd, pyodbc

src = pyodbc.connect(r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=C:\path\your.accdb;")
dst = sqlite3.connect("data.sqlite")

# copy all tables
cursor = src.cursor()
tables = [r.table_name for r in cursor.tables(tableType='TABLE')]
for t in tables:
    df = pd.read_sql(f"SELECT * FROM [{t}]", src)
    df.to_sql(t, dst, if_exists='replace', index=False)

dst.close(); src.close()
