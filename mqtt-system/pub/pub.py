import paho.mqtt.client as mqtt
import json
import time
import random
from datetime import datetime

# Konfigurasi broker
broker = "10.0.0.1"
port = 1883
obu_id = 1
duration = 5 * 60 

# Input QoS
qos_input = input("Pilih QoS (0, 1, 2): ").strip()
if qos_input not in ["0", "1", "2"]:
    print("[WARNING] QoS tidak valid. Default ke 0.")
    qos_level = 0
else:
    qos_level = int(qos_input)

retain = qos_level > 0

# Input jenis data
data_type = input("Jenis data (BPR / ACC): ").strip().upper()
if data_type not in ["BPR", "ACC"]:
    print("[WARNING] Jenis data tidak valid. Default ke BPR.")
    data_type = "BPR"

# Frekuensi kirim
if data_type == "BPR":
    interval = 1.0  # 1 Hz
else:  # ACC
    interval = 1.0 / 125  # 125 Hz

# Topik sesuai data
topic = f"cbt/obu/{obu_id}/{data_type.lower()}"

# Callback koneksi
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[PUB] Terhubung ke broker.")
    else:
        print(f"[ERROR] Gagal konek ke broker, kode: {rc}")

# Inisialisasi MQTT
client = mqtt.Client()
client.on_connect = on_connect

try:
    client.connect(broker, port, 60)
except Exception as e:
    print(f"[ERROR] Tidak bisa menghubungkan ke broker: {e}")
    exit(1)

client.loop_start()
start_time = time.time()

print(f"[PUB] Mengirim data {data_type} dari OBU-{obu_id} ke topik {topic} (QoS={qos_level})")

try:
    while time.time() - start_time < duration:
        now = time.time()

        if data_type == "BPR":
            data_value = round(random.uniform(0.9, 1.2), 3)
            payload = {
                "obu_id": obu_id,
                "timestamp": now,
                "bpr": data_value
            }
        else:  # ACC
            data_value = [round(random.uniform(-1.5, 1.5), 3) for _ in range(3)]
            payload = {
                "obu_id": obu_id,
                "timestamp": now,
                "acc": data_value
            }

        result = client.publish(topic, json.dumps(payload), qos=qos_level, retain=retain)
        result.wait_for_publish()

        if result.is_published():
            print(f"[PUB] {data_type} terkirim @ {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
        else:
            print("[PUB] Gagal mengirim data!")

        time.sleep(interval)

except KeyboardInterrupt:
    print("\n[PUB] Dihentikan oleh user.")

client.loop_stop()
client.disconnect()
print("[PUB] Selesai.")
