import sqlite3
import pandas as pd
import pyodbc

DATA_PATH = r"C:\Users\alexr\Downloads\enrollment_2024\ENROLL2024_20241105.accdb"

src = pyodbc.connect(rf"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={DATA_PATH};")
dst = sqlite3.connect("data.db")

# copy all tables
cursor = src.cursor()
tables = [r.table_name for r in cursor.tables(tableType='TABLE')]
for t in tables:
    df = pd.read_sql(f"SELECT * FROM [{t}]", src)
    df.to_sql(t, dst, if_exists='replace', index=False)

dst.close(); src.close()
