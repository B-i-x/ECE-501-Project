# Experiments Plan

## Questions
1. Does chronic absence correlate with proficiency (ELA/Math) across schools and years?
2. How do subgroup gaps appear in attendance vs proficiency?
3. How much faster is the star schema (with indexes + summary) vs baselines?

## Datasets
- NYSED Report Card Databases, 2015–2024 (Access → CSV → SQLite)

## Baselines
- **Baseline 1 (wide):** single denormalized table, minimal/no indexes.
- **Baseline 2 (normalized):** partially normalized, no indexes.
- **Star (ours):** normalized + indexes + summary materialization.

## Queries (implemented in `experiments/benchmark_queries.sql`)
- Q1: Absence rate vs proficiency (Year × School)
- Q2: Subgroup comparison (attendance × achievement)
- Q3: Year-over-year proficiency changes by district
- Q4: Absence thresholds vs achievement distribution
- Q5: Top-performing schools under low absence (ELA)

## Metrics
- Runtime (ms) with `.timer on`
- EXPLAIN QUERY PLAN complexity snapshots
- Summary refresh time (cost to maintain materialization)
- DB file size and table/index sizes (optional)

## Procedure
1. Build DB: `make build`
2. Run benchmarks: `sqlite3 db/nysed.sqlite < experiments/benchmark_queries.sql`
3. Capture timings to `figs/query_perf.csv` (or `.txt`)
4. Visualize latency distributions; compare across schemas
5. Document findings in the report (tables + plots)

## Expected Outcomes
- Star schema shows lower latency than baselines (especially joins).
- Summary materialization reduces repeated aggregation cost.
