import tkinter as tk
from tkinter import ttk
from influxdb_client import InfluxDBClient
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import pandas as pd

URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
TOKEN = "voBHbGtEAe0OYx9yHECEIu5tsD4G7mIMbPb3I0oMHXU5KvVIrXsG74K_jmAot756u2rZGs136B7dBzTT9XUzuw=="
ORG = "Ptit"
BUCKET = "iot_processed"

client = InfluxDBClient(url=URL, token=TOKEN, org=ORG)
query_api = client.query_api()

def fetch_data(measurement):
    query = f'''
    from(bucket: "{BUCKET}")
      |> range(start: -1h)
      |> filter(fn: (r) => r["_measurement"] == "{measurement}")
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    '''
    df = query_api.query_data_frame(query)
    if not df.empty:
        df['_time'] = pd.to_datetime(df['_time'])
        df.set_index('_time', inplace=True)
    return df

root = tk.Tk()
root.title("IoT Real-time Dashboard - B23DCCN538")
root.geometry("1000x650")

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 5))

def update_charts():
    ax1.clear()
    ax2.clear()

    # Đồ thị 1: Dữ liệu thô từ ESP32
    df_raw = fetch_data("sensor_data")
    if not df_raw.empty and 'temperature' in df_raw.columns:
        ax1.plot(df_raw.index, df_raw['temperature'], label='Nhiệt độ (°C)', color='red')
        ax1.plot(df_raw.index, df_raw['humidity'], label='Độ ẩm (%)', color='blue')
        ax1.set_title("Dữ liệu thô từ ESP32 (sensor_data)")
        ax1.legend()

    # Đồ thị 2: Dữ liệu đã xử lý
    df_proc = fetch_data("sensor_processed")
    if not df_proc.empty and 'temp_rolling_mean' in df_proc.columns:
        ax2.plot(df_proc.index, df_proc['temp_rolling_mean'], label='Temp Rolling Mean', color='green')
        ax2.plot(df_proc.index, df_proc['temp_scaled'], label='Temp Scaled [0-1]', color='orange')
        ax2.set_title("Dữ liệu đã tiền xử lý (sensor_processed)")
        ax2.legend()

    canvas.draw()

btn = ttk.Button(root, text="🔄 Tải lại dữ liệu", command=update_charts)
btn.pack(side=tk.TOP, pady=5)

canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

update_charts()
root.mainloop()