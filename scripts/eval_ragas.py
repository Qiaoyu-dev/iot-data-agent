"""
scripts/eval_ragas.py
作用：用 RAGAS 跑项目的四指标评测
     faithfulness（忠实度）/ answer_relevancy（答案相关性）/ context_precision（上下文精确率）/ context_recall（上下文召回率）
流程：读评测集 jsonl → 逐条跑 Agent 拿 answer + retrieve 拿 contexts → RAGAS 打分 → 输出分数表 + 存结果
运行（终端 B，Git Bash，项目根目录执行）：
     python -m scripts.eval_ragas
前置：
    1) 向量库已建好：python -m rag.build_index
    2) .env 配好 DEEPSEEK_API_KEY + ZHIPU_API_KEY
    3) pip install ragas langchain-openai datasets pandas
"""
import asyncio
import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # Windows 控制台 GBK，强制 UTF-8 防中文/emoji 报错

# 让脚本无论 `python scripts/eval_ragas.py` 还是 `python -m scripts.eval_ragas` 都能 import 项目根目录的 agent/rag
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

import pandas as pd
from datasets import Dataset

# RAGAS 0.2+ 标准导入
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import ChatOpenAI
from langchain_core.embeddings import Embeddings

# 项目自身模块：复用 W2 Agent + 生产检索链路（与 search_knowledge 同源）
from agent.graph import graph
from tools.knowledge import retrieve_contexts
from rag.embed import embed

# ============ 配置区（按需改） ============
EVAL_PATH = Path("data/eval/eval_questions.jsonl")   # 检索评测集；RAGAS 只吃其中 should_answer=true 的行
LIMIT = None                               # 验证时设 10 跑子集，确认无误后改回 None 跑全量

# ============ 1. 把智谱 embedding 包成 LangChain Embeddings 接口 ============
# RAGAS 的 context_recall 要用 embeddings 算 ground_truth 与 contexts 的相似度；
# 你 W1 的 rag/embed.py 返回 list[list[float]]，不是 LangChain 接口，这里包一层复用
class ZhipuEmbeddings(Embeddings):
    def embed_documents(self, texts):
        return embed(texts)

    def embed_query(self, text):
        return embed([text])[0]

# ============ 2. 配置 RAGAS 的 LLM judge + embeddings ============
judge_llm = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com",
    api_key=os.environ["DEEPSEEK_API_KEY"],
)
ragas_llm = LangchainLLMWrapper(judge_llm)
ragas_embeddings = LangchainEmbeddingsWrapper(ZhipuEmbeddings())

# ============ 3. 读评测集（jsonl 每行一条 {question, gold_answer, should_answer, ...}） ============
def load_eval_set(path: Path) -> list:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            # 只对「应答类」问题跑 RAGAS 三指标；拒答类(Q8/Q9)的 gold_answer 为空，
            # 三指标对空标准答案无意义，其拒答准确率由 data/eval/run_eval.py 单独出。
            if row.get("should_answer", True):
                rows.append(row)
    return rows

# ============ 4. 跑单条：拿最终回答 + 检索上下文 ============
async def run_one(question: str, tid: str):
    # 4a. 拿最终回答（复用 W2 的 graph；每条独立 thread_id，避免多轮记忆互相污染）
    result = await graph.ainvoke(
        {"messages": [("user", question)]},
        config={"configurable": {"thread_id": tid}},
    )
    answer = result["messages"][-1].content
    # 4b. 拿检索上下文（走生产 search_knowledge 同一取上下文逻辑，避免两处漂移）
    contexts = [h["text"] for h in retrieve_contexts(question)]
    return answer, contexts

async def collect(rows):
    questions, answers, contexts_list, ground_truths = [], [], [], []
    for i, r in enumerate(rows, 1):
        q = r["question"]
        answer, contexts = await run_one(q, f"eval-{i}")
        questions.append(q)
        answers.append(answer)
        contexts_list.append(contexts)
        ground_truths.append(r["gold_answer"])  # 字段映射：现有评测集的标准答案字段叫 gold_answer
        print(f"[{i}/{len(rows)}] {q[:28]}... contexts={len(contexts)}")
    return questions, answers, contexts_list, ground_truths

# ============ 5. 主流程 ============
def main():
    rows = load_eval_set(EVAL_PATH)
    if LIMIT:
        rows = rows[:LIMIT]
        print(f"⚠️ 只跑前 {LIMIT} 条验证；确认无误后把 LIMIT 改回 None 跑全量\n")
    print(f"评测集共 {len(rows)} 条，逐条跑 Agent + 检索...\n")
    questions, answers, contexts_list, ground_truths = asyncio.run(collect(rows))

    ds = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts_list,
        "ground_truth": ground_truths,
    })

    print("\n开始 RAGAS 四指标打分（每条要调多次 LLM，50 条约 5-15 分钟）...")
    result = evaluate(
        ds,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=ragas_llm,
        embeddings=ragas_embeddings,
    )
    df = result.to_pandas()

    # 存明细 + 打印平均分
    df.to_csv("data/ragas_result.csv", index=False, encoding="utf-8-sig")
    print("\n===== 四指标平均分（回填 README 用） =====")
    for col in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
        print(f"  {col}: {df[col].mean():.3f}")
    print("\n明细已存 data/ragas_result.csv")

if __name__ == "__main__":
    main()