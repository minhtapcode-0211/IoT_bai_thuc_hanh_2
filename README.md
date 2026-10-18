 IoT Data Pipeline - End-to-End Real-Time Monitoring System

Hệ thống thu thập, lưu trữ, tiền xử lý và trực quan hóa dữ liệu cảm biến thời gian thực sử dụng ESP32, MQTT Broker, InfluxDB Cloud và Python.

 Kiến trúc Hệ thống
1. **Firmware**: ESP32 (mô phỏng Wokwi) phát dữ liệu định dạng JSON.
2. **Broker**: MQTT Broker (`broker.hivemq.com:1883`).
3. **Collector**: Python Client lắng nghe Topic `ptit/iot/esp32/telemetry_bminh` và ghi vào InfluxDB Cloud.
4. **Storage**: InfluxDB Cloud 2.x (Org: `Ptit`, Bucket: `iot_processed`).
5. **Preprocessing**: Nội suy missing value, lọc Outlier (IQR), Resample (1 min), Min-Max Scaling, Rolling Mean.
6. **Dashboard**: Giao diện Desktop Tkinter + Matplotlib.

 Hướng dẫn Cài đặt & Chạy Dự án

1. Cài đặt Môi trường
bash
git clone <URL_REPOSITORY_CUA_BAN>
cd IoT_Data_Pipeline
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

2. Chạy Dịch vụ
Khởi chạy 3 Terminal song song:
Terminal 1 (Thu thập dữ liệu):
Bash
python collector/mqtt_to_influx.py
Terminal 2 (Tiền xử lý dữ liệu):
Bash
python preprocessing/process_data.py
Terminal 3 (Dashboard Giám sát):
Bash
python app/dashboard.py
