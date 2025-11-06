import csv
import numpy as np
import matplotlib.pyplot as plt

# ==== USER CONFIGURATION ====
CSV_PATH = "final-project\\experiments\\original_data\\query1\\results.csv"  # <-- replace this
OUTPUT_PNG = "final-project\\experiments\\original_data\\query1\\latency_trend.png"        # <-- replace this

# ==== LOAD DATA ====
rows = []
p50 = []
p95 = []

with open(CSV_PATH, "r") as f:
    r = csv.DictReader(f)
    for row in r:
        rows.append(float(row["rows"]))
        p50.append(float(row["P50_seconds"]))
        p95.append(float(row["P95_seconds"]))

rows = np.array(rows, dtype=float)
p50  = np.array(p50, dtype=float)
p95  = np.array(p95, dtype=float)

# ==== LINEAR FIT FOR P50 ====
# Model: y = m * x + c
coeffs = np.polyfit(rows, p50, 1)  # [m, c]
m, c = coeffs[0], coeffs[1]
trend_p50 = m * rows + c

# Compute R²
y_pred = trend_p50
ss_res = np.sum((p50 - y_pred) ** 2)
ss_tot = np.sum((p50 - np.mean(p50)) ** 2)
r2 = 1 - (ss_res / ss_tot)

# Smooth line for plotting
x_smooth = np.linspace(rows.min(), rows.max(), 200)
trend_smooth = m * x_smooth + c

print(f"Linear Fit: P50 ≈ {m:.6f} * rows + {c:.6f} (R² = {r2:.4f})")

# ==== PLOT ====
plt.figure(figsize=(8, 5))
plt.plot(rows, p50, marker='o', label="P50 (median)")
plt.plot(rows, p95, marker='o', label="P95 (95th percentile)")
plt.plot(x_smooth, trend_smooth, linestyle='--', label=f"P50 Trend (Linear Fit, R²={r2:.3f})")

plt.title("Query Latency vs Rows")
plt.xlabel("Rows")
plt.ylabel("Latency (seconds)")
plt.legend()
plt.grid(True)

plt.savefig(OUTPUT_PNG, dpi=300, bbox_inches='tight')
plt.show()

print(f"[INFO] Plot saved to {OUTPUT_PNG}")
