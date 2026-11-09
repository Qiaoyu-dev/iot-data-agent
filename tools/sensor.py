from pathlib import Path
import pandas as pd
from langchain_core.tools import tool

DATA = Path("data/processed/sensor_readings_clean.csv")

def _load():
    if not DATA.exists():
        return None
    return pd.read_csv(DATA, parse_dates=["timestamp"])

@tool
def get_sensor_temperature(device_id: str) -> str:
    """查询指定传感器的最新温度读数，device_id 例如 TEMP-001"""
    df = _load()
    if df is None:
        return "数据文件不存在，请先运行数据生成脚本"
    d = df[df.device_id == device_id.upper()].sort_values("timestamp")
    if d.empty:
        return f"没有设备 {device_id} 的数据"
    latest = d.iloc[-1]
    status = "异常" if latest["is_anomaly"] else "正常"
    return f"{device_id} 最新温度 {latest['temperature']}°C（{latest['timestamp']}，状态：{status}）"

@tool
def get_sensor_stats(device_id: str) -> str:
    """查询指定传感器的统计信息：均值/最大/最小/异常点数，用于判断趋势"""
    df = _load()
    if df is None:
        return "数据文件不存在，请先运行数据生成脚本"
    d = df[df.device_id == device_id.upper()]
    if d.empty:
        return f"没有设备 {device_id} 的数据"
    return (f"{device_id} 近7天统计：均值 {d.temperature.mean():.1f}°C，"
            f"最高 {d.temperature.max():.1f}°C，最低 {d.temperature.min():.1f}°C，"
            f"异常点 {int(d.is_anomaly.sum())} 个")
