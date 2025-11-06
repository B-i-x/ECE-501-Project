# Setup Instructions

Follow these steps to set up the project environment:

## 1. Create and Activate Python Virtual Environment
1. Open a terminal and navigate to the project directory.
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
1. Ensure you have `pip` and `build` installed:
    ```bash
    pip install --upgrade pip build
    ```
2. Install the dependencies from the `pyproject.toml` file:
    ```bash
    pip install .
    ```

## 3. Verify Installation
1. Check that the dependencies are installed correctly:
    ```bash
    pip list
    ```

Your environment is now set up and ready to use!