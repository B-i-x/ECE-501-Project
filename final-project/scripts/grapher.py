import csv
import numpy as np
import matplotlib.pyplot as plt
from math import exp, log

# ==== USER CONFIGURATION ====
CSV_PATH = "final-project\\experiments\\original_data\\query1\\results.csv"  # <-- replace this
OUTPUT_PNG = "final-project\\experiments\\original_data\\query1\\latency_trend.png"        # <-- replace this

# ==== LOAD DATA ====
rows = []
p50 = []
p95 = []

with open(CSV_PATH, "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(float(row["rows"]))
        p50.append(float(row["P50_seconds"]))
        p95.append(float(row["P95_seconds"]))

rows = np.array(rows)
p50 = np.array(p50)
p95 = np.array(p95)

# ==== FIT EXPONENTIAL TREND FOR P50 ====
# Model: y = a * e^(b * x)
# Take logs: ln(y) = ln(a) + b * x  → linear regression on ln(y)
log_y = np.log(p50)
coeffs = np.polyfit(rows, log_y, 1)  # slope, intercept in log space
b = coeffs[0]
ln_a = coeffs[1]
a = exp(ln_a)

# Create smooth x for trendline
x_smooth = np.linspace(min(rows), max(rows), 200)
trend_p50 = a * np.exp(b * x_smooth)

print(f"Exponential Fit: P50 ≈ {a:.6f} * exp({b:.6f} * rows)")

# ==== PLOT ====
plt.figure()
plt.plot(rows, p50, marker='o', label="P50 (median)")
plt.plot(rows, p95, marker='o', label="P95 (95th percentile)")
plt.plot(x_smooth, trend_p50, linestyle='--', label="P50 Trend (Exponential Fit)")

plt.title("Query Latency vs Rows")
plt.xlabel("Rows")
plt.ylabel("Latency (seconds)")
plt.legend()
plt.grid(True)

# Save and show
plt.savefig(OUTPUT_PNG, dpi=300, bbox_inches='tight')
plt.show()

print(f"[INFO] Plot saved to {OUTPUT_PNG}")
