from dataclasses import dataclass

@dataclass
class AppConfig:
    data_dir = "data"
    ny_edu_data = data_dir + "/ny_edu_data"
    sqlite_dir = data_dir + "/sqlite"