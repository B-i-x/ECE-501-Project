# Data Dictionary — NYSED Star Schema

> Purpose: define every table/column used in analysis; keep this in sync with `sql/00_schema.sql`.

## Dimensions

### dim_year
- `year_key` (INTEGER, PK): Reporting year (e.g., 2024)
- `school_year_label` (TEXT): Human-readable label (e.g., 2023–24)

### dim_district
- `district_key` (INTEGER, PK)
- `district_id` (TEXT, UNIQUE, NOT NULL): Natural key from NYSED
- `district_name` (TEXT)
- `county_name` (TEXT)
- `nrc_code` (TEXT): Needs/Resource Capacity (if available)
- `nrc_desc` (TEXT): Description of NRC

### dim_school
- `school_key` (INTEGER, PK)
- `school_id` (TEXT, UNIQUE, NOT NULL)
- `district_key` (INTEGER, FK → dim_district.district_key)
- `school_name` (TEXT)

### dim_subject
- `subject_key` (INTEGER, PK)
- `subject_id` (TEXT, UNIQUE, NOT NULL): `ELA` | `Math`
- `subject_name` (TEXT)

### dim_grade
- `grade_key` (INTEGER, PK)
- `grade_id` (TEXT, UNIQUE, NOT NULL): `3`..`8`, `All`

### dim_subgroup
- `subgroup_key` (INTEGER, PK)
- `subgroup_id` (TEXT, UNIQUE, NOT NULL): canonical code (e.g., `F`, `M`, `SWD`, `ELL`, `ED`, `Asian`, …)
- `subgroup_name` (TEXT)

## Facts

### fact_enrollment
**Grain:** Year × School × Subgroup  
- `year_key` (INTEGER, FK → dim_year)
- `school_key` (INTEGER, FK → dim_school)
- `subgroup_key` (INTEGER, FK → dim_subgroup)
- `n_students` (INTEGER)
- **PK:** (year_key, school_key, subgroup_key)

### fact_attendance
**Grain:** Year × School × Subgroup  
- `year_key` (INTEGER, FK → dim_year)
- `school_key` (INTEGER, FK → dim_school)
- `subgroup_key` (INTEGER, FK → dim_subgroup)
- `absent_count` (INTEGER)
- `absence_rate` (REAL, 0..1)
- `enrollment` (INTEGER)
- `data_rep_flag` (TEXT)
- `partial_data_flag` (TEXT)
- `count_zero_flag` (TEXT)
- **PK:** (year_key, school_key, subgroup_key)

### fact_assessment
**Grain:** Year × School × Subject × Grade × Subgroup  
- `year_key` (INTEGER, FK → dim_year)
- `school_key` (INTEGER, FK → dim_school)
- `subject_key` (INTEGER, FK → dim_subject)
- `grade_key` (INTEGER, FK → dim_grade)
- `subgroup_key` (INTEGER, FK → dim_subgroup)
- `tested` (INTEGER)
- `n_qual` (INTEGER)
- `qual_rate` (REAL, 0..1)
- **PK:** (year_key, school_key, subject_key, grade_key, subgroup_key)
