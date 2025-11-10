# File Structure Overview

The file structure is shown below
```
/ECE-501-Project/
├── data/
├── docs/
├── sql/
├── src/
│   ├── app/
│   ├── execute/
│   ├── ingest/
│   ├── load/
│   ├── reporting/
│   ├── transform/
├── util/
├── execution_config.yaml
├── pyproject.toml
```

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

Where documentation goes

### execution_config.yaml

Where you can configure how you want to run your queries. Which queries to run. What datasets to use. Important file

### pyproject.toml

Project environment definition. 

### SQL Directory

Every folder inside the sql directory defines a new query. baseline_query1's name is defined by the folder `sql/baseline_query1`
All sql files in the folder will be run according to the file sequence. In order to finish the definition of a new folder you need to go to [src->app->queries](/src/app/queries.py) and create a new QuerySpec object. Fill it out as the other queries are. Now the query is fully defined and you can execute it using run_all or run_query