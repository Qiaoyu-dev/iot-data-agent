"""
data/preview_data.py
作用：读取清洗后的数据，画出时序图并标红异常点，肉眼验收数据质量
运行：在仓库根目录执行  python data/preview_data.py
产出：data/preview.png
"""
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]  # 中文标题不乱码
plt.rcParams["axes.unicode_minus"] = False                       # 负号正常显示

df = pd.read_csv("data/sensor_readings_clean.csv", parse_dates=["timestamp"])

d = df[df.device_id == "TEMP-001"]
plt.figure(figsize=(14, 4))
plt.plot(d.timestamp, d.temperature, lw=0.6, label="temperature")

# 把真值异常点标红，看尖峰是否显眼
anomaly = d[d.is_anomaly]
plt.scatter(anomaly.timestamp, anomaly.temperature,
            c="red", s=20, zorder=5, label="anomaly")

plt.title("TEMP-001 温度时序（清洗后）")
plt.legend()
plt.tight_layout()
plt.savefig("data/preview.png", dpi=120)
print("验收图已保存 → data/preview.png（应看到：正弦周期 + 缓慢上翘 + 红色尖峰）")
