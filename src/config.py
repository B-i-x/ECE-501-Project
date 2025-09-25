from dataclasses import dataclass

@dataclass
class AppConfig:
    data_dir = "data"
    ny_edu_data = data_dir + "/ny_edu_data"
    sqlite_dir = data_dir + "/sqlite"

@dataclass
class DataLink:
    url: str
    path_to_data_from_zip_root: str
    folder_name: str



STUDENT_EDUCATOR_DATABASE_23_24 = DataLink(
    url="https://data.nysed.gov/files/studed/23-24/STUDED2024.zip",
    path_to_data_from_zip_root="STUDED_2024.accdb",
    folder_name="student_educator_database_23_24"
)

REPORT_CARD_23_24 = DataLink(
    url="https://data.nysed.gov/files/essa/23-24/SRC2024.zip",
    path_to_data_from_zip_root="SRC2024_Group5.accdb",
    folder_name="reportcard_database_23_24"
)

ALL_DATASETS = [
    STUDENT_EDUCATOR_DATABASE_23_24,
    REPORT_CARD_23_24,
]