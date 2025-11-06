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

GRADUATION_RATE_23_24 = DataLink(
    url="https://data.nysed.gov/files/gradrate/23-24/gradrate.zip",
    path_to_data_from_zip_root="2024_GRADUATION_RATE.mdb",
    folder_name="grad_rate_database_23_24"
)

PATHWAYS_23_24 = DataLink(
    url="https://data.nysed.gov/files/pathways/23-24/pathways.zip",
    path_to_data_from_zip_root="Cohort Pathways 2024_Suppressed.mdb",
    folder_name="pathways_database_23_24"
)

ENROLLMENT_23_24 = DataLink(
    url="https://data.nysed.gov/files/enrollment/23-24/enrollment_2024.zip",
    path_to_data_from_zip_root="ENROLL2024_20241105.accdb",
    folder_name="enrollment_database_23_24"
)

STUDENT_DIGITAL_RESOURCES_23_24 = DataLink(
    url="https://data.nysed.gov/files/student-digital-resources/23-24/student-digital-resources.zip",
    path_to_data_from_zip_root="Student Digital Resources 2023-24.accdb",
    folder_name="digital_resources_database_23_24"
)

AP_IB_COURSE_23_24 = DataLink(
    url="https://data.nysed.gov/files/apib/2324/APIB24.zip",
    path_to_data_from_zip_root="AP_IB_Course_2024.mdb",
    folder_name="ap_ib_course_database_23_24"
)

AP_IB_ASSESSMENT_23_24 = DataLink(
    url="https://data.nysed.gov/files/apib/2324/APIB24.zip",
    path_to_data_from_zip_root="AP_IB_Assessment_2024.mdb",
    folder_name="ap_ib_assessment_database_23_24"
)

ENGLISH_LANGUAGE_LEARNERS_23_24 = DataLink(
    url="https://data.nysed.gov/files/ell/23-24/ell_2024.zip",
    path_to_data_from_zip_root="ELL_2023_2024.accdb",
    folder_name="ell_database_23_24"
)

STUDENT_EDUCATOR_DATABASE_22_23 = DataLink(
    url="https://data.nysed.gov/files/studed/22-23/STUDED2023.zip",
    path_to_data_from_zip_root="STUDED_2023.accdb",
    folder_name="student_educator_database_22_23"
)

REPORT_CARD_22_23 = DataLink(
    url="https://data.nysed.gov/files/essa/22-23/SRC2023.zip",
    path_to_data_from_zip_root="SRC2023_Group5.accdb",
    folder_name="reportcard_database_22_23"
)

GRADUATION_RATE_22_23 = DataLink(
    url="https://data.nysed.gov/files/gradrate/22-23/gradrate.zip",
    path_to_data_from_zip_root="GRAD_RATE_AND_OUTCOMES_2023.accdb",
    folder_name="grad_rate_database_22_23"
)

PATHWAYS_22_23 = DataLink(
    url="https://data.nysed.gov/files/pathways/22-23/pathways.zip",
    path_to_data_from_zip_root="2023CareerPathwaysResearcherFile.accdb",
    folder_name="pathways_database_22_23"
)

ENROLLMENT_22_23 = DataLink(
    url="https://data.nysed.gov/files/enrollment/22-23/enrollment_2023.zip",
    path_to_data_from_zip_root="ENROLL2023_20231207.mdb",
    folder_name="enrollment_database_22_23"
)

STUDENT_DIGITAL_RESOURCES_22_23 = DataLink(
    url="https://data.nysed.gov/files/student-digital-resources/22-23/student-digital-resources.zip",
    path_to_data_from_zip_root="Student Digital Resources 2022-23.accdb",
    folder_name="digital_resources_database_22_23"
)

AP_IB_COURSE_22_23 = DataLink(
    url="https://data.nysed.gov/files/apib/2223/APIB23.zip",
    path_to_data_from_zip_root="AP_IB_Course_2023.accdb",
    folder_name="ap_ib_course_database_22_23"
)

AP_IB_ASSESSMENT_22_23 = DataLink(
    url="https://data.nysed.gov/files/apib/2223/APIB23.zip",
    path_to_data_from_zip_root="AP_IB_Assessment_2023.accdb",
    folder_name="ap_ib_assessment_database_22_23"
)

ENGLISH_LANGUAGE_LEARNERS_22_23 = DataLink(
    url="https://data.nysed.gov/files/ell/22-23/ell_2023.zip",
    path_to_data_from_zip_root="ELL_2022_2023.accdb",
    folder_name="ell_database_22_23"
)

ALL_DATASETS = [
    STUDENT_EDUCATOR_DATABASE_23_24,
    REPORT_CARD_23_24,
    GRADUATION_RATE_23_24,
    PATHWAYS_23_24,
    ENROLLMENT_23_24,
    STUDENT_DIGITAL_RESOURCES_23_24,
    AP_IB_COURSE_23_24,
    AP_IB_ASSESSMENT_23_24,
    ENGLISH_LANGUAGE_LEARNERS_23_24,
    STUDENT_EDUCATOR_DATABASE_22_23,
    REPORT_CARD_22_23,
    GRADUATION_RATE_22_23,
    PATHWAYS_22_23,
    ENROLLMENT_22_23,
    STUDENT_DIGITAL_RESOURCES_22_23,
    AP_IB_COURSE_22_23,
    AP_IB_ASSESSMENT_22_23,
    ENGLISH_LANGUAGE_LEARNERS_22_23
]