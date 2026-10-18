import json
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import paho.mqtt.client as mqtt

# Cấu hình InfluxDB 2.x
URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
TOKEN = "voBHbGtEAe0OYx9yHECEIu5tsD4G7mIMbPb3I0oMHXU5KvVIrXsG74K_jmAot756u2rZGs136B7dBzTT9XUzuw=="
ORG = "Ptit"
BUCKET = "iot_processed"

client_db = InfluxDBClient(url=URL, token=TOKEN, org=ORG)
write_api = client_db.write_api(write_options=SYNCHRONOUS)

# Cấu hình MQTT Broker
MQTT_BROKER = "broker.hivemq.com"  # Hoặc broker của ông
MQTT_PORT = 1883
MQTT_TOPIC = "ptit/iot/esp32/telemetry_bminh"


def on_message(client, userdata, msg):
  try:
    payload_str = msg.payload.decode("utf-8")
    data = json.loads(payload_str)
    print(f"Nhận dữ liệu: {data}")

    # Validate dữ liệu cơ bản
    if (
        "temperature" in data
        and "humidity" in data
        and "distance_cm" in data
    ):
      # Ghi vào InfluxDB
      point = (
          Point("sensor_data")
          .tag("device_id", "ESP32_BAI2")
          .field("temperature", float(data["temperature"]))
          .field("humidity", float(data["humidity"]))
          .field("distance_cm", float(data["distance_cm"]))
          .field("rssi", int(data.get("rssi", 0)))
          .field("sequence", int(data.get("sequence", 0)))
          .time(datetime.utcnow(), WritePrecision.NS)
      )
      write_api.write(bucket=BUCKET, org=ORG, record=point)
      print("-> Đã lưu vào InfluxDB thành công!")
  except Exception as e:
    print(f"Lỗi xử lý dữ liệu: {e}")


client = mqtt.Client()
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.subscribe(MQTT_TOPIC)

print("Đang lắng nghe dữ liệu MQTT...")
client.loop_forever()