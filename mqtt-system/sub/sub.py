import matplotlib
matplotlib.use('Agg')

import paho.mqtt.client as mqtt
from paho.mqtt.subscribeoptions import SubscribeOptions

import json
import time
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats
import csv
import os
import sys
import threading

# Input QoS
qos_input = input("Pilih QoS Subscriber (0, 1, 2): ").strip()
if qos_input not in ["0", "1", "2"]:
    print("[WARNING] QoS tidak valid, default ke 0.")
    qos_level = 0
else:
    qos_level = int(qos_input)

# Input jenis data
data_type = input("Jenis data (BPR / ACC): ").strip().upper()
if data_type not in ["BPR", "ACC"]:
    print("[WARNING] Jenis data tidak dikenali. Default ke BPR.")
    data_type = "BPR"

# Input bandwidth
bw_input = input("Bottleneck bandwidth (Kbps): ").strip()
if not bw_input.isdigit():
    print("[WARNING] Bandwidth tidak valid. Default ke 128.")
    bw_input = "128"

# Konfigurasi broker & topik
broker = "10.0.0.1"
port = 1883
topic = f"cbt/obu/1/{data_type.lower()}"

# File paths
combined_csv_filename = f"latency_queue_{data_type}_QoS{qos_level}_BW{bw_input}.csv"
queue_filename = f"queue_count_{data_type}.csv"

# Variabel global
latencies = []
total_bytes_received = 0
message_count = 0
skip_first_message = True
start_time = None
queue_samples = []

def log_to_file(text):
    if qos_level != 0:
        with open("log.txt", "a") as f:
            f.write(text + "\n")

def save_to_csv():
    if not latencies and not queue_samples:
        print("[INFO] Tidak ada data untuk disimpan.")
        return

    with open(combined_csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Detik ke-", "Latency (ms)", "Queued Messages"])

        max_len = max(len(latencies), len(queue_samples))
        for i in range(max_len):
            latency = f"{latencies[i]:.3f}" if i < len(latencies) else ""
            queue_val = queue_samples[i] if i < len(queue_samples) else ""
            writer.writerow([i+1, latency, queue_val])

    print(f"[INFO] Data latency & antrean disimpan ke '{os.path.abspath(combined_csv_filename)}'")

def save_plot():
    if not latencies:
        return
    avg_latency = np.mean(latencies)
    if len(latencies) > 1:
        sem = stats.sem(latencies)
        ci_range = stats.t.interval(0.95, len(latencies) - 1, loc=avg_latency, scale=sem)
    else:
        ci_range = (avg_latency, avg_latency)

    plt.figure(figsize=(10, 5))
    plt.plot(latencies, label="Latency (ms)", color='blue')
    plt.axhline(avg_latency, color='green', linestyle='--', label=f'Avg: {avg_latency:.2f} ms')
    plt.fill_between(range(len(latencies)), ci_range[0], ci_range[1], color='orange', alpha=0.3, label='95% CI')
    plt.title(f"Latency vs Waktu (QoS={qos_level}, BW={bw_input}kbps, Data={data_type})")
    plt.xlabel("Pesan ke-")
    plt.ylabel("Latency (ms)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plot_name = f"latency_plot_{data_type}_qos{qos_level}_bw{bw_input}.png"
    plt.savefig(plot_name)
    print(f"[INFO] Grafik disimpan ke '{os.path.abspath(plot_name)}'")

def save_queue_average():
    if not queue_samples:
        print("[INFO] Tidak ada data antrean untuk disimpan.")
        return
    avg_queue = np.mean(queue_samples)

    header = ["QoS", "Bandwidth", "Data", "AvgQueuedMessages"]
    if not os.path.exists(queue_filename):
        with open(queue_filename, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)

    with open(queue_filename, mode='a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([qos_level, bw_input, data_type, round(avg_queue, 2)])

    print(f"[INFO] Rata-rata antrean disimpan ke '{queue_filename}'")

# Callback koneksi
def on_connect(client, userdata, flags, reasonCode, properties=None):
    global start_time
    if reasonCode == 0:
        print("[Subscriber] Terhubung ke broker MQTT.")
        options = SubscribeOptions(qos=qos_level)
        client.subscribe(topic, options=options)
        start_time = time.time()
    else:
        print(f"[ERROR] Gagal konek ke broker. Kode: {reasonCode}")

# Callback pesan masuk
def on_message(client, userdata, msg):
    global latencies, total_bytes_received, message_count, skip_first_message

    try:
        payload_str = msg.payload.decode()
        if not payload_str.strip():
            print("[INFO] Pesan kosong diterima, dilewati.")
            return

        payload = json.loads(payload_str)
        received_time = time.time()
        publish_time = payload.get("timestamp", None)

        if publish_time is None:
            print("[WARNING] Timestamp tidak ditemukan.")
            return

        latency_ms = (received_time - publish_time) * 1000

        if skip_first_message:
            skip_first_message = False
            return

        if latency_ms > 10000:
            print(f"[WARNING] Latency terlalu tinggi: {latency_ms:.2f} ms → dilewati.")
            return

        latencies.append(latency_ms)
        total_bytes_received += len(msg.payload)
        message_count += 1

        log = (
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Received | "
            f"Size={len(msg.payload)}B | QoS={msg.qos} | "
            f"Latency={latency_ms:.2f}ms"
        )
        print(log)
        log_to_file(log)

    except Exception as e:
        print(f"[ERROR] Gagal parsing pesan: {e}")

def queue_sampler():
    while running:
        queued = len(client._in_messages)
        queue_samples.append(queued)
        time.sleep(1)

# Inisialisasi client MQTT
client = mqtt.Client(client_id="sub-client", protocol=mqtt.MQTTv5)
client.on_connect = on_connect
client.on_message = on_message

# Koneksi
try:
    client.connect(broker, port, 60)
except Exception as e:
    print(f"[ERROR] Tidak bisa menghubungkan ke broker: {e}")
    sys.exit(1)

print(f"[Subscriber] Menunggu pesan... (QoS={qos_level}, Data={data_type}, BW={bw_input} kbps)")

# Loop utama
running = True
try:
    client.loop_start()
    thread = threading.Thread(target=queue_sampler)
    thread.start()

    for _ in range(300):  
        time.sleep(1)
    print("\n[INFO] Waktu 5 menit selesai. Menghentikan client.")
except KeyboardInterrupt:
    print("\n[Subscriber] Dihentikan oleh user.")
finally:
    running = False
    thread.join()
    client.loop_stop()
    client.disconnect()
    save_to_csv()
    save_plot()
    save_queue_average()
