
class AppConfig:
    data_dir = "data"
    ny_edu_data = data_dir + "/ny_edu_data"
    sqlite_dir = data_dir + "/sqlite"

class DataLink:
    url: str
    path_to_data_from_zip_root: str
    folder_name: str

#    python src\downloader.py --url "https://data.nysed.gov/files/studed/23-24/STUDED2024.zip" --file-folder "student_educator_database_23_24" --accdb-name "STUDED_2024.accdb"
STUDENT_EDUCATOR_DATABASE_23_24 = DataLink(
    url="https://data.nysed.gov/files/studed/23-24/STUDED2024.zip",
    path_to_data_from_zip_root="STUDED_2024.accdb",
    folder_name="student_educator_database_23_24"
)