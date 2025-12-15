# Index Plan

## Goals
- Speed up star-joins on (school, year, subgroup) and assessment (subject, grade).
- Keep inserts reasonably fast; favor idempotent builds.

## Existing Indexes (as in `sql/00_schema.sql`)
- Natural key uniqueness:
  - `ux_district_id(dim_district.district_id)`
  - `ux_school_id(dim_school.school_id)`
  - `ux_year_key(dim_year.year_key)`
  - `ux_subject_id(dim_subject.subject_id)`
  - `ux_grade_id(dim_grade.grade_id)`
  - `ux_subgroup_id(dim_subgroup.subgroup_id)`
- Fact access paths:
  - `ix_enroll_school_year(fact_enrollment.school_key, year_key)`
  - `ix_enroll_subgroup(fact_enrollment.subgroup_key)`
  - `ix_att_school_year(fact_attendance.school_key, year_key)`
  - `ix_att_subgroup(fact_attendance.subgroup_key)`
  - `ix_assess_school_year(fact_assessment.school_key, year_key)`
  - `ix_assess_subject_grade(fact_assessment.subject_key, grade_key)`
  - `ix_assess_subgroup(fact_assessment.subgroup_key)`

## Rationale
- Most queries group/filter by year and school; subgroup breakdowns are common.
- Assessment frequently slices by subject/grade; compound index helps.
- Natural-key uniqueness prevents dup loads from multi-year imports.

## PRAGMA / Tuning (SQLite)
- `PRAGMA journal_mode=WAL;`
- `PRAGMA synchronous=NORMAL;`
- `PRAGMA temp_store=MEMORY;`
- Optional: `PRAGMA cache_size=-800000` (≈800MB), adjust to your RAM.

## Future Experiments
- Partial indexes for common WHERE clauses (if any stable predicate emerges).
- Covering indexes for hot queries found in `experiments/time_queries.py`.
