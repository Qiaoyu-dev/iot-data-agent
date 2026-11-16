# IoT 设备时序数据分析 Agent

## 业务背景
水泵房每天产生海量时序数据（泵压、温度、振动），运维靠人工盯盘、查手册——慢且容易漏。
本项目是一个 IoT 设备运维 Agent：运维用自然语言提问
（"PUMP-X201 昨晚为什么报警？""TEMP-001 这周温度趋势？"），
Agent 自动查询实时数据、检索运维手册，给出带引用来源的诊断结论。

## 技术栈
LangGraph · Chroma · FastAPI · DeepSeek · 智谱 embedding-3 · RAGAS

## 架构图
   ![系统架构](docs/architecture.png)

## 评测指标
RAGAS 离线评测（跑分后回填真实值）：

| 指标 | 说明 | 目标 | 实测 |
|---|---|---|---|
| Faithfulness（忠实度） | 回答是否忠于检索内容、不编造 | ≥ 0.8 | 0.614 |
| Answer Relevancy（答案相关性） | 回答是否切题 | ≥ 0.8 | 0.591 |
| Context Precision（上下文精确率） | 检索结果中相关片段占比 | ≥ 0.7 | 0.875 |
| Context Recall（上下文召回率） | 回答所需信息是否都被检索到 | ≥ 0.7 | 0.771 |


## 评测基线（W1 · 2026-11-05）
| 指标 | 数值 | 说明 |
|---|---|---|
| Hit Rate@3 | 100%（8/8） | 5类分层测评集，检索命中率 |
| 拒答准确率 | 100%（2/2） | 库外问题正确拒答 |
| 知识库规模 | iot_manuals 7 chunks | 距离阈值 1.2 |

## 快速启动
1. pip install -r requirements.txt
2. 复制 .env.example 为 .env，填入你的 API Key
3. python rag/build_index.py        # 建向量库
4. uvicorn api.main:app --port 8000 # 启动后端（终端 A）
5. curl http://127.0.0.1:8000/health            # 应返回 {"status":"ok"}
   curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"message\":\"PUMP-X201 的告警阈值是多少？\"}"
6. streamlit run web/app.py       #启动前端（终端B）

> 注：Python 3.14 下 ragas 的依赖 scikit-network 无 cp314 wheel、需 MSVC 编译，`pip install -r requirements.txt` 会卡在它上面。
> 但它只在 ragas 生成测试集时用到，跑 faithfulness/answer_relevancy/context_recall 三指标评测不需要。
> 本项目 `.venv` 已用 `pip install ragas==0.4.4 --no-deps` 跳过它装好；全新复现时同样用 `--no-deps` 装 ragas、再补齐其余依赖即可。