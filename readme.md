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

4. **Run the script**:
    ```bash
    python src\downloader.py --url "https://data.nysed.gov/files/studed/23-24/STUDED2024.zip" --file-folder "student_educator_database_23_24" --accdb-name "STUDED_2024.accdb"

    ```