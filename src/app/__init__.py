from dataclasses import dataclass

@dataclass
class AppConfig:
    data_dir = "data"
    ny_edu_data = data_dir + "/ny_edu_data" # baseline datasets in accdb/mdb
    baseline_dir = data_dir + "/baseline" # baseline datasets in sqlite