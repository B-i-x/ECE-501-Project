-- Subjects & Grades
INSERT OR IGNORE INTO dim_subject(subject_id, subject_name)
VALUES ('ELA','English Language Arts'), ('Math','Mathematics');

INSERT OR IGNORE INTO dim_grade(grade_id)
VALUES ('3'),('4'),('5'),('6'),('7'),('8'),('All');

-- Year labels from staging (built in 09_staging_persistent.sql)
INSERT OR IGNORE INTO dim_year(year_key, school_year_label)
SELECT DISTINCT y.year_key,
       printf('%d-%02d', y.year_key-1, y.year_key-2000) AS school_year_label
FROM st_years y;
