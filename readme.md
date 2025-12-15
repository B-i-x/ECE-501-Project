# NYSED Educational Data Warehouse — ECE 501 Final Project

This project builds a **SQLite data warehouse** from the 2024 **New York State Education Department (NYSED) Report Card Databases**.  
It integrates Access databases into a unified **star schema** that supports analysis of **enrollment composition**, **attendance**, and **academic achievement** (Grades 3–8 ELA and Math).

---

## Important Note: 
Because this is a combination of codebases, it is possible some work is duplicated or some things may not work. If it does not run, please try Alex Romero's uploaded code for running queries and you can look through the code here in final-project/sql for sql related to the star schema. Thank you!

---

## Project Objectives

- Extract and standardize NYSED annual report card datasets (.mdb/.accdb)
- Build a **reproducible star schema** using SQLite
- Enable analysis of subgroups, attendance, and proficiency
- Compare baseline designs (wide vs star) for performance
- Validate data quality and consistency across years (reach goal)

---

## 0) Repository layout (key paths)
```
ECE-501-Project/
	readme.md
	execution_config.yaml
	pyproject.toml
	sql/
		{queries}
	final-project/
		README.md
		data_raw/              # SRCYYYY/*.mdb|*.accdb  (NOT in git)
		data_work/             # extracted CSVs         (NOT in git)
		db/star_schema.db      # output DB              (NOT in git)
		scripts/
			run_pipeline.py
```

## 1) Environment setup

```bash
cd ECE-501-Project/final-project
```

### All platforms (Conda)
```bash
conda env create -f environment.yml
conda activate ece501-final
```

### Windows
- Install [Microsoft Access Database Engine 2016 Redistributable](https://www.microsoft.com/en-us/download/details.aspx?id=54920)
- Verify the ODBC driver exists: `Microsoft Access Driver (*.mdb, *.accdb)`

### macOS
```bash
brew install mdbtools
```

### Linux
```bash
sudo apt update
sudo apt install mdbtools
```

## 2) Data placement

```
final-project/data_raw/SRC2015/*.mdb|*.accdb
...
final-project/data_raw/SRC2024/*.mdb|*.accdb
```

Download all NYSED Report Card databases from https://data.nysed.gov/downloads.php
Unzip into appropriate directories.

## 3) One-command run
```bash
python final-project/scripts/run_pipeline.py
```

## 4) Verifying run
```bash
sqlite3 final-project/db/nysed.sqlite "SELECT count(*) FROM fact_enrollment;"
```

## 5) Change environments

You now have a file `ECE-501-Project/final-project/db/star_schema.db` that you will import in the next phase.

```bash
cp db/star_schema.db ../data/baseline/star_schema.db
cp data_raw/SRC2024/SRC2024_Group5.accdb ../data/ny_edu_data/reportcard_database_23_24/SRC2024_Group5.accdb
cd ..
```

## 6) Run all queries on baseline and star schema

```bash
run_all
```

## 7) Test to ensure config works (optional)

```bash
test_config
```

## 8) Plot (optional)

```bash
dual_plot
```