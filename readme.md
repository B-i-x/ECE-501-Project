# Setup Instructions

Follow these steps to set up the project environment:

## 1. Create and Activate Python Virtual Environment
1. Open a terminal and navigate to the project root directory.
2. Create a virtual environment:
    ```bash
    python -m venv venv
    ```
3. Activate the virtual environment:
    - On Windows:
      ```bash
      .\venv\Scripts\activate
      ```
    - On macOS/Linux:
      ```bash
      source venv/bin/activate
      ```

## 2. Install Dependencies

2. Install the dependencies from the `pyproject.toml` file:
    ```bash
    pip install -e .
    ```

Your environment is now set up and ready to use!

# Usage instructions

## Important commands

To run all queries defined as in [in the execution file](/execution_config.yaml)
```powershell
run_all
```

Make sure config works
```powershell
test_config
```

If you want to make new commands, edit pyproject.toml


## File Structure Overview
All commands are defined in the pyproject.toml
```
ECE-501-Project
├─ docs
├─ execution_config.yaml
├─ pyproject.toml
├─ readme.md
├─ sql
│  └─ {queries}
├─ src
│  ├─ app
│  ├─ execute
│  ├─ ingest
│  ├─ load
│  ├─ reporting
│  └─ transform
└─ util
```

### Docs

Where documentation goes. honestly, right now I am just storing old stuff in there.

### execution_config.yaml

Where you can configure how you want to run your queries. Which queries to run. What datasets to use. Important file

### pyproject.toml

Project environment definition. 

### SQL Directory

Every folder inside the sql directory defines a new query. baseline_query1's name is defined by the folder `sql/baseline_query1`
All sql files in the folder will be run according to the file sequence. In order to finish the definition of a new folder you need to go to [src->app->queries](/src/app/queries.py) and create a new QuerySpec object. Fill it out as the other queries are. Now the query is fully defined and you can execute it using run_all or run_query

### src/app

Things that are defined and shared across the code base such as query definitions and paths and datasets

### src/execute

Code related to running queries

### src/ingest

Gets the data from the new york website and downloads it

### src/load

Turns the .accdb or .mdb files into sqlite3 .db files that the baseline uses.

### src/reporting

Code related to how we store the resulting data and how to then put it in a graph

### src/transform

Code related to transforming the baseline sqlite files into a more efficient databse

### util

Short scripts
- query_sql_combiner.py : Gets all sql for a query and puts in your clipboard with good formatting. Good for conversations with LLM when your sql is not working
- simple_schema_analysis : Prints all the tables and their columns for a sqlite database file (.db). Again, good for conversations with LLM when your setting up your queries
 