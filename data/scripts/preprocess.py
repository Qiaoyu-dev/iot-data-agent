"""
data/scripts/preprocess.py
作用：读取脏数据，执行清洗三板斧（去重/越界处理/时序插值）+ 格式化，
     输出干净数据到 data/processed/sensor_readings_clean.csv
运行：在仓库根目录执行  python data/scripts/preprocess.py
前置：先跑 generate_sensor_data.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

df_raw = pd.read_csv("data/raw/sensor_readings.csv")
df = df_raw.copy()

# ===== 第一板斧：去重 —— 同一设备同一时刻只留一条 =====
df = df.drop_duplicates(subset=["timestamp", "device_id"])

# ===== 第二板斧：越界值置缺失 —— -999 是故障码，不是数据 =====
df.loc[df.temperature < -50, "temperature"] = np.nan

# ===== 第三板斧：时序插值填补缺失（不能填均值，会抹平周期）=====
df = df.sort_values(["device_id", "timestamp"])
df["temperature"] = (df.groupby("device_id")["temperature"]
                     .transform(lambda s: s.interpolate(limit_direction="both")))

# ===== 格式化：时间戳统一 ISO 格式，设备ID统一大写 =====
df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime("%Y-%m-%dT%H:%M:%S")
df["device_id"] = df["device_id"].str.upper()

Path("data/processed").mkdir(parents=True, exist_ok=True)  # 确保输出目录存在
df.to_csv("data/processed/sensor_readings_clean.csv", index=False)

# ===== 清洗报告（好习惯，写进 commit 说明）=====
print(f"原始 {len(df_raw)} 行 → 清洗后 {len(df)} 行（去重+插值完成）")
print(f"清洗后缺失值剩余：{df['temperature'].isna().sum()} 个")
