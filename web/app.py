# web/app.py —— IoT 数据 Agent 的 Streamlit 前端
# 职责：只负责展示和交互；所有智能逻辑走 FastAPI 后端（周六手册 v2）
import json
import uuid

import matplotlib.pyplot as plt
import pandas as pd
import requests
import streamlit as st

API_BASE = "http://127.0.0.1:8000"   # FastAPI 后端地址

st.set_page_config(page_title="IoT 数据 Agent", page_icon="🤖", layout="wide")

# ---------- 会话状态（跨重跑保险箱） ----------
# 每次交互脚本都会整页重跑，历史和 thread_id 必须存这里，否则一发消息就失忆
if "messages" not in st.session_state:
    st.session_state.messages = []          # 对话历史：[{"role": "user"/"assistant", "content": ...}]
if "thread_id" not in st.session_state:
    # thread_id 对应后端 MemorySaver 的会话隔离键（周五手册）
    st.session_state.thread_id = f"web-{uuid.uuid4().hex[:8]}"


def stream_reply(message: str):
    """请求 /chat/stream，逐个 token yield。
    周六手册的 SSE 帧格式：data: {"token": "..."}\n\n，收尾帧 data: {"done": true}
    """
    with requests.post(
        f"{API_BASE}/chat/stream",
        json={"message": message, "thread_id": st.session_state.thread_id},
        stream=True,          # 关键：流式读取，不等全部响应下载完
        timeout=60,
    ) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue                    # SSE 空行/注释帧，跳过
            payload = json.loads(line[len("data: "):])
            if payload.get("done"):
                break                       # 收尾帧，结束
            token = payload.get("token")
            if token:
                yield token                 # 逐 token 交给 st.write_stream 渲染


def draw_sensor_chart(df: pd.DataFrame):
    """画多设备温度时序曲线 + 85°C 告警阈值线"""
    # ⚠️ 按你 CSV 的实际列名改这三个变量（先用 st.dataframe 看一眼列名再改）
    ts_col, dev_col, val_col = "timestamp", "device_id", "temperature"

    # Matplotlib 默认不支持中文，不配这两行图里中文全是方块 □□
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, ax = plt.subplots(figsize=(8, 3.6), dpi=110)
    for dev, g in df.groupby(dev_col):
        ax.plot(pd.to_datetime(g[ts_col]), g[val_col], label=dev, linewidth=1.2)
    ax.axhline(85, color="red", linestyle="--", linewidth=1, label="告警阈值 85°C")
    ax.set_title("设备温度时序")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.autofmt_xdate()                      # 时间标签自动倾斜，防重叠
    return fig


# ---------- 侧边栏：数据面板（上传 + 图表） ----------
with st.sidebar:
    st.header("📁 数据面板")
    st.caption(f"会话 ID：{st.session_state.thread_id}")

    uploaded = st.file_uploader("上传传感器 CSV", type=["csv"])
    df = None
    if uploaded is not None:
        df = pd.read_csv(uploaded)
        st.caption(f"已加载 {len(df)} 行 × {len(df.columns)} 列")
        st.dataframe(df.head(20), use_container_width=True)
    elif st.button("加载项目自带清洗数据"):
        # 周四手册 sensor_stats 用的同一份数据
        df = pd.read_csv("data/processed/sensor_readings_clean.csv")

    if df is not None:
        st.pyplot(draw_sensor_chart(df))

# ---------- 主区：对话界面 ----------
st.title("🤖 IoT 时序数据分析 Agent")
st.caption("后端：LangGraph 多工具自主路由 + RAG 阈值拒答 ｜ 接口：FastAPI /chat/stream")

# 1) 先把历史消息全部渲染出来（每次重跑都靠它恢复页面）
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 2) 底部输入框；用户回车后才进入分支
if prompt := st.chat_input("问点什么，例如：TEMP-001 今天最高温多少？"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # st.write_stream 接生成器：逐 token 渲染，返回拼接好的完整文本
            full = st.write_stream(stream_reply(prompt))
        except requests.exceptions.ConnectionError:
            full = "⚠️ 连不上后端，请先启动：uvicorn api.main:app --reload --port 8000"
            st.markdown(full)
    st.session_state.messages.append({"role": "assistant", "content": full})