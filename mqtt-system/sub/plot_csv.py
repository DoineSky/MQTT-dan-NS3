import matplotlib.pyplot as plt
import csv
import os
import numpy as np
from scipy import stats

# === Input manual untuk bandwidth ===
bw_input = input("Masukkan nilai bottleneck bandwidth (dalam Kbps): ").strip()
if not bw_input.isdigit():
    print("[WARNING] Input tidak valid. Default ke 512 Kbps.")
    bw_input = "512"

# Konfigurasi
qos_levels = [0, 1, 2]
data_types = ["BPR", "ACC"]
colors = ['red', 'green', 'blue']

# Subplots: 1 baris, 2 kolom (BPR & ACC)
fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=True)

# Perhitungan rata-rata dan CI
print(f"\n=== Rata-rata Latency dan Confidence Interval (BW = {bw_input} Kbps) ===\n")

for i, data_type in enumerate(data_types):
    ax = axes[i]
    for qos, color in zip(qos_levels, colors):
        filename = f"latency_{data_type.upper()}_QoS{qos}_BW{bw_input}.csv"
        if not os.path.exists(filename):
            print(f"[WARNING] File tidak ditemukan: {filename}")
            continue

        latencies = []
        with open(filename, 'r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            for row in reader:
                try:
                    latencies.append(float(row[1]))
                except:
                    continue

        if latencies:
            ax.plot(latencies, label=f"QoS {qos}", color=color)

            mean_latency = np.mean(latencies)
            if len(latencies) > 1:
                sem = stats.sem(latencies)
                ci = stats.t.interval(0.95, len(latencies)-1, loc=mean_latency, scale=sem)
                ci_str = f"{ci[0]:.2f} ms – {ci[1]:.2f} ms"
            else:
                ci = (mean_latency, mean_latency)
                ci_str = "N/A (hanya 1 data)"

            print(f"{data_type} | QoS {qos} -> Rata-rata: {mean_latency:.2f} ms | CI 95%: {ci_str}")
        else:
            print(f"[INFO] File {filename} kosong atau tidak valid.")

    ax.set_title(f"{data_type} - BW {bw_input} Kbps")
    ax.set_xlabel("Pesan ke-")
    if i == 0:
        ax.set_ylabel("Latency (ms)")
    ax.grid(True)
    ax.legend()

fig.suptitle("Perbandingan Latency BPR dan ACC untuk QoS 0-2", fontsize=14)
plt.tight_layout(rect=[0, 0, 1, 0.95])

output_filename = f"plot_comparison_BPR_ACC_BW{bw_input}.png"
plt.savefig(output_filename)
print(f"\n[INFO] Grafik disimpan ke '{output_filename}'")
