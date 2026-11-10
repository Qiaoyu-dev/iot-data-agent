# IoT 设备时序数据分析 Agent

## 业务背景
工厂传感器每天产生海量时序数据，运维靠人工盯盘、查手册——慢且容易漏。
本项目是一个 IoT 设备数据分析 Agent：运维人员用自然语言提问
（"TEMP-001 昨晚为什么报警？"），Agent 自动查询实时数据、
检索运维手册，给出带引用来源的诊断结论。

## 技术栈
LangGraph · Chroma · FastAPI · DeepSeek · 智谱 embedding-3 · RAGAS

## 架构图
（W2 补充）

## 评测指标
（W2 用 RAGAS 跑出基线后补充）

## 评测基线（W1 · 2026-11-05）
| 指标 | 数值 | 说明 |
|---|---|---|
| Hit Rate@3 | XX%（N条评测集） | 检索命中率 |
| 拒答准确率 | XX% | 库外问题正确拒答 |
| 知识库规模 | iot_manuals XX chunks | 距离阈值 1.2 |

## 快速启动
1. pip install -r requirements.txt
2. 复制 .env.example 为 .env，填入你的 API Key
3. python rag/build_index.py  # 建向量库
（后续步骤随开发补充）