"""
data/scripts/generate_sensor_data.py
作用：模拟生成 3 个 IoT 传感器 7 天的时序数据，并故意弄脏（缺失/重复/越界），
     输出"原始脏数据"到 data/raw/sensor_readings.csv
运行：在仓库根目录执行  python data/scripts/generate_sensor_data.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

np.random.seed(42)  # 固定随机种子：任何人跑这份脚本，生成的数据完全一致（可复现）


def generate_sensor(device_id, days=7, interval_min=5,
                    baseline=60.0, amplitude=15.0, slope=0.02):
    """生成一个传感器 days 天的时序数据，每 interval_min 分钟一条
    真实数据 = 周期(昼夜) + 趋势(老化漂移) + 噪声(随机抖动) + 异常(故障尖峰)
    """
    n = days * 24 * 60 // interval_min           # 7天 × 288条/天 = 2016 条
    t = np.arange(n)
    timestamps = pd.date_range("2026-10-01", periods=n, freq=f"{interval_min}min")

    period = 24 * 60 // interval_min             # 每天的采样点数
    seasonal = amplitude * np.sin(2 * np.pi * t / period)  # ① 周期：昼夜温漂
    trend = slope * t                                      # ② 趋势：缓慢上升
    noise = np.random.normal(0, 0.5, n)                    # ③ 噪声：随机抖动

    value = baseline + seasonal + trend + noise

    # ④ 异常：随机挑 0.5% 的点注入尖峰（模拟故障），并保留真值标签
    n_anomaly = int(n * 0.005)
    idx = np.random.choice(n, n_anomaly, replace=False)
    is_anomaly = np.zeros(n, dtype=bool)
    is_anomaly[idx] = True
    value[idx] += np.random.uniform(20, 40, n_anomaly)

    return pd.DataFrame({
        "timestamp": timestamps,
        "device_id": device_id,
        "temperature": np.round(value, 2),
        "is_anomaly": is_anomaly,   # 真值标签：评测时对照用
    })


# ===== 生成 3 个设备：正常 / 漂移快 / 波动小 =====
df1 = generate_sensor("TEMP-001")
df2 = generate_sensor("TEMP-002", baseline=55, slope=0.08)
df3 = generate_sensor("TEMP-003", baseline=70, amplitude=8)

df = pd.concat([df1, df2, df3], ignore_index=True)

# ===== 模拟现实：故意弄脏数据 =====
# 缺失：随机删掉 1% 的温度值（传感器掉线）
mask = np.random.rand(len(df)) < 0.01
df.loc[mask, "temperature"] = np.nan

# 重复：复制 20 行（上报重试导致）
df = pd.concat([df, df.sample(20, random_state=42)], ignore_index=True)

# 越界：注入不可能的读数（传感器故障乱码）
df.loc[df.sample(10, random_state=42).index, "temperature"] = -999

Path("data/raw").mkdir(parents=True, exist_ok=True)  # raw/ 被 gitignore，需确保目录存在
df.to_csv("data/raw/sensor_readings.csv", index=False)
print(f"原始数据已生成：{len(df)} 行（含脏数据）→ data/raw/sensor_readings.csv")
