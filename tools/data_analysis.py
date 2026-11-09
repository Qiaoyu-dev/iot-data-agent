import pandas as pd
from langchain_core.tools import tool

# W1 数据流水线的产物：清洗后的传感器数据
# 列：timestamp, device_id, temperature, is_anomaly
CSV_PATH = "data/processed/sensor_readings_clean.csv"

# 与设备手册一致的高告警阈值（°C），用于统计超阈值次数
HIGH_THRESHOLD = 85.0


@tool
def sensor_stats(device_id: str) -> str:
    """统计指定传感器的采集数据（样本量/均值/最值/标准差/超阈值次数）。

    适用场景：用户询问某台设备或传感器的温度统计、运行状况、
    异常情况、数据分布等【采集数据】问题时调用。
    不适用：设备手册里的参数定义、巡检流程（用 search_knowledge）。

    Args:
        device_id: 设备编号，例如 "TEMP-001"。

    Returns:
        一段统计结果文字，供 LLM 组织最终回答。
    """
    df = pd.read_csv(CSV_PATH)

    # ① 按设备过滤；设备不存在时给出可用列表，让 LLM 能纠正用户
    sub = df[df["device_id"] == device_id]
    if sub.empty:
        known = ", ".join(sorted(df["device_id"].unique()))
        return f"数据中不存在设备 {device_id}。当前可用设备：{known}"

    # ② 核心统计量（Pandas 一行一个，注意 std 默认是样本标准差）
    t = sub["temperature"]
    n_over = int((t > HIGH_THRESHOLD).sum())          # 超 85°C 次数
    n_anom = int(sub["is_anomaly"].astype(str)
                   .isin(["True", "1", "1.0"]).sum())   # 兼容 CSV 读出的布尔/字符串

    # ③ 最新一条读数，让回答有"现在进行时"的感觉
    last = sub.iloc[-1]

    return (
        f"设备 {device_id} 统计（共 {len(sub)} 条采集记录）：\n"
        f"- 均值 {t.mean():.2f}°C，最大 {t.max():.2f}°C，最小 {t.min():.2f}°C\n"
        f"- 标准差 {t.std():.2f}，超 {HIGH_THRESHOLD:.0f}°C 阈值 {n_over} 次，"
        f"标记异常点 {n_anom} 个\n"
        f"- 最新读数 {last['temperature']:.1f}°C（{last['timestamp']}）"
    )


# 直接 python tools/data_analysis.py 可自测本工具，不依赖 Agent
if __name__ == "__main__":
    print(sensor_stats.invoke({"device_id": "TEMP-001"}))
    print("-" * 40)
    print(sensor_stats.invoke({"device_id": "TEMP-999"}))  # 测不存在的设备