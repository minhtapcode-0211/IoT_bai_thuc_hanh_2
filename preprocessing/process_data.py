from datetime import datetime
import numpy as np
import pandas as pd
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
TOKEN = "voBHbGtEAe0OYx9yHECEIu5tsD4G7mIMbPb3I0oMHXU5KvVIrXsG74K_jmAot756u2rZGs136B7dBzTT9XUzuw=="
ORG = "Ptit"
RAW_BUCKET = "iot_processed"
PROCESSED_BUCKET = "iot_processed"

client_db = InfluxDBClient(url=URL, token=TOKEN, org=ORG)
query_api = client_db.query_api()
write_api = client_db.write_api(write_options=SYNCHRONOUS)

def min_max_scale(series):
    min_val, max_val = series.min(), series.max()
    if pd.isna(min_val) or pd.isna(max_val) or max_val == min_val:
        return series * 0.0
    return (series - min_val) / (max_val - min_val)

def process_data():
    print("[PREPROCESS] Đang lấy dữ liệu từ iot_processed...")
    query = f'''
    from(bucket: "{RAW_BUCKET}")
      |> range(start: -1h)
      |> filter(fn: (r) => r["_measurement"] == "sensor_data")
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    '''
    df = query_api.query_data_frame(query)

    if df.empty:
        print("[PREPROCESS] Chưa có dữ liệu thô trong 1 giờ qua.")
        return

    df['_time'] = pd.to_datetime(df['_time'])
    df.set_index('_time', inplace=True)
    features = ['temperature', 'humidity', 'distance_cm']
    
    # Kiểm tra các cột cần thiết
    for col in features:
        if col not in df.columns:
            df[col] = np.nan

    df = df[features]

    # 1. Làm sạch & Nội suy dữ liệu thiếu
    df = df.interpolate(method='time').bfill().ffill()

    # 2. Lọc Outlier bằng phương pháp IQR
    for col in features:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        if IQR > 0:
            df[col] = np.where((df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR), np.nan, df[col])
            
    df = df.interpolate(method='time').bfill().ffill()

    # 3. Resample dữ liệu theo từng 1 phút
    df_resampled = df.resample('1min').mean().dropna()

    if df_resampled.empty:
        print("[PREPROCESS] Dữ liệu sau khi resample bị rỗng.")
        return

    # 4. Feature Engineering & Scaling
    df_resampled['temp_rolling_mean'] = df_resampled['temperature'].rolling(window=3, min_periods=1).mean()
    df_resampled['temp_scaled'] = min_max_scale(df_resampled['temperature'])
    df_resampled['hum_scaled'] = min_max_scale(df_resampled['humidity'])
    df_resampled['dist_scaled'] = min_max_scale(df_resampled['distance_cm'])

    # Loại bỏ triệt để dòng có NaN
    df_resampled = df_resampled.dropna()

    # 5. Ghi dữ liệu vào InfluxDB
    print("[PREPROCESS] Đang lưu dữ liệu đã tiền xử lý...")
    count = 0
    for timestamp, row in df_resampled.iterrows():
        p = Point("sensor_processed") \
            .time(timestamp, WritePrecision.NS) \
            .field("temperature", float(row["temperature"])) \
            .field("humidity", float(row["humidity"])) \
            .field("distance_cm", float(row["distance_cm"])) \
            .field("temp_rolling_mean", float(row["temp_rolling_mean"])) \
            .field("temp_scaled", float(row["temp_scaled"])) \
            .field("hum_scaled", float(row["hum_scaled"])) \
            .field("dist_scaled", float(row["dist_scaled"]))
        
        write_api.write(bucket=PROCESSED_BUCKET, org=ORG, record=p)
        count += 1

    print(f"--> [HOÀN THÀNH] Đã xử lý và lưu thành công {count} bản ghi vào iot_processed!")

if __name__ == "__main__":
    process_data()