CREATE TEMP TABLE math_src AS
SELECT *
FROM src."Annual EM MATH"
LIMIT :n_limit;