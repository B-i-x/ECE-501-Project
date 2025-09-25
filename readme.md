# Setup Instructions

1. **Set up a virtual environment**:
    ```bash
    python -m venv venv
    ```

2. **Activate the virtual environment**:
    - On Windows:
      ```bash
      venv\Scripts\activate
      ```
    - On macOS/Linux:
      ```bash
      source venv/bin/activate
      ```

3. **Install the required dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Running the downloader**:
    will proabably put this in a config.json sson
    
    Get student and educator database 2023-2024
    ```bash
    python src\downloader.py --url "https://data.nysed.gov/files/studed/23-24/STUDED2024.zip" --file-folder "student_educator_database_23_24" --accdb-name "STUDED_2024.accdb"
    ```

    Get report card databse 23-24
    ```bash
    python src\downloader.py --url "https://data.nysed.gov/files/essa/23-24/SRC2024.zip" --file-folder "reportcard_database_23_24" --accdb-name "SRC2024_Group5.accdb"
    ```

5. example sql query
'''sql
SELECT ENTITY_CD, ENTITY_NAME, NUM_SUSPENSIONS
FROM suspensions
WHERE YEAR = 2022
ORDER BY NUM_SUSPENSIONS DESC
LIMIT 10;
'''