# Query 1 Star Schema Version

The original query 1 files use baseline database tables that don't exist in the star schema. Use the `*_star.sql` files instead.

## Execution Order

Run these files in order:

1. `reset_star.sql` - Clean up any existing temp views/tables
2. `create_math_src_star.sql` - Get math assessment data (All Students only, for school-level proficiency)
3. `create_math_overall_star.sql` - Aggregate math proficiency by school/year
4. `create_math_outcome.sql` - Calculate math proficiency rate (reuses original, works with star schema)
5. `demo_view_star.sql` - Calculate demographic percentages from enrollment data
6. `create_pairs_year.sql` - Join math outcomes with demographics (reuses original, works with star schema)
7. `correlations.sql` - Calculate correlations (reuses original, works with star schema)

## Key Differences from Baseline Version

- **Math data**: Comes from `fact_assessment` instead of `reportcard_database_23_24."Annual EM MATH"`
- **Demographics**: Calculated from `fact_enrollment` by computing percentages of each subgroup relative to total enrollment, instead of using `enrollment_database_23_24."Demographic Factors"`

## Demographic Subgroups Used

The demo view calculates percentages for:
- `per_ell` - English Language Learners (subgroup_id = 'ELL')
- `per_swd` - Students with Disabilities (subgroup_id = 'SWD')
- `per_ecdis` - Economically Disadvantaged (subgroup_id = 'ED')
- `per_black` - Black students (subgroup_id = 'Black')
- `per_hisp` - Hispanic students (subgroup_id = 'Hispanic')
- `per_asian` - Asian students (subgroup_id = 'Asian')
- `per_white` - White students (subgroup_id = 'White')

## Note on Subgroup Data

If you're only seeing "All Students" in your results, check:
1. Does `fact_enrollment` contain data for individual subgroups (ELL, SWD, ED, etc.)?
2. Are the subgroup_ids correctly mapped in `map_subgroups` table?
3. Run: `SELECT DISTINCT subgroup_id, subgroup_name FROM dim_subgroup ORDER BY subgroup_id;` to see available subgroups

If enrollment data only has "All Students", you may need to extract demographic factors from a different source table.

