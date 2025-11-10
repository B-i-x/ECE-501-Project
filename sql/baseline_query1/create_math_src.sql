CREATE TEMP TABLE math_src AS
SELECT *
FROM reportcard_database_23_24."Annual EM MATH"
LIMIT CAST(:n_limit AS INTEGER);