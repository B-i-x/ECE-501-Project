#!/usr/bin/env python3
import csv
import numpy as np
import matplotlib.pyplot as plt

# ==== USER CONFIGURATION ====
CSV_PATH   = "final-project\\experiments\\overlayed_data.csv"  # update as needed
OUTPUT_PNG = "final-project\\experiments\\original_data\\query1\\latency_trend_star_vs_original.png"

# ==== LOAD DATA ====
rows = []
orig_p50, orig_p95 = [], []
our_p50,  our_p95  = [], []

with open(CSV_PATH, "r", newline="") as f:
    r = csv.DictReader(f)
    for row in r:
        rows.append(float(row["rows"]))
        orig_p50.append(float(row["original_P50_seconds"]))
        orig_p95.append(float(row["original_P95_seconds"]))
        our_p50.append(float(row["our_P50_seconds"]))
        our_p95.append(float(row["our_P95_seconds"]))

rows     = np.array(rows, dtype=float)
orig_p50 = np.array(orig_p50, dtype=float)
orig_p95 = np.array(orig_p95, dtype=float)
our_p50  = np.array(our_p50,  dtype=float)
our_p95  = np.array(our_p95,  dtype=float)

# ==== LINEAR FITS FOR P50 (original & our) ====
def linfit(x, y):
    m, c = np.polyfit(x, y, 1)            # slope, intercept
    yhat  = m * x + c
    ss_res = np.sum((y - yhat) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else float("nan")
    return m, c, r2

m_o, c_o, r2_o = linfit(rows, orig_p50)
m_s, c_s, r2_s = linfit(rows, our_p50)

x_smooth = np.linspace(rows.min(), rows.max(), 200)
trend_orig_p50 = m_o * x_smooth + c_o
trend_our_p50  = m_s * x_smooth + c_s

print(f"[FIT] Original P50  ~ {m_o:.6f} * rows + {c_o:.6f}  (R²={r2_o:.4f})")
print(f"[FIT] Star     P50  ~ {m_s:.6f} * rows + {c_s:.6f}  (R²={r2_s:.4f})")

# ==== PLOT ====
plt.figure(figsize=(9, 5.5))

# Data series (4 lines)
plt.plot(rows, orig_p50, marker='o', label="Original P50")
plt.plot(rows, orig_p95, marker='s', label="Original P95")
plt.plot(rows, our_p50,  marker='o', label="Our P50")
plt.plot(rows, our_p95,  marker='s', label="Our P95")

# Trend lines (2 lines)
plt.plot(x_smooth, trend_orig_p50, linestyle='--',
         label=f"Original P50 Trend (R²={r2_o:.3f})")
plt.plot(x_smooth, trend_our_p50,  linestyle='--',
         label=f"Our P50 Trend (R²={r2_s:.3f})")

plt.title("Query Latency vs Rows — Original vs Our Schema")
plt.xlabel("Rows")
plt.ylabel("Latency (seconds)")
plt.grid(True, alpha=0.3)
plt.legend()

plt.tight_layout()
plt.savefig(OUTPUT_PNG, dpi=300, bbox_inches='tight')
plt.show()
print(f"[INFO] Plot saved to {OUTPUT_PNG}")
