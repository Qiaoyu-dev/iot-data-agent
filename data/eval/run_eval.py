"""
data/eval/run_eval.py  (v3 · 生产同源版)
改动：
  1. Hit Rate 改为「答案关键词命中」，不再死磕文件名
  2. 检索上下文直接复用 tools.knowledge.retrieve_contexts，与生产链路同源
运行：python -m data.eval.run_eval
"""
import json
from pathlib import Path

from tools.knowledge import search_knowledge, retrieve_contexts

EVAL_FILE = Path("data/eval/eval_questions.jsonl")
TOP_K = 3        # 最终送入模型的上下文条数（对齐生产 kept[:3]）


def load_questions() -> list[dict]:
    lines = EVAL_FILE.read_text(encoding="utf-8").splitlines()
    return [json.loads(ln) for ln in lines if ln.strip()]


def is_hit(q: dict, hits: list[dict]) -> bool:
    """优先用关键词判内容，没有关键词才退回文件名判"""
    kws = q.get("gold_keywords") or []
    if kws:
        blob = " ".join(h["text"] for h in hits)
        return any(k in blob for k in kws)
    return any(q["gold_source"] in h["source"] for h in hits)


def main():
    questions = load_questions()
    answerable = [q for q in questions if q["should_answer"]]
    refuse = [q for q in questions if not q["should_answer"]]

    # ===== 指标一：Hit Rate@3 =====
    hit = 0
    for q in answerable:
        hits = retrieve_contexts(q["question"], max_keep=TOP_K)
        ok = is_hit(q, hits)
        hit += ok
        srcs = [h["source"] for h in hits]
        print(f"{'✅' if ok else '❌'} [Q{q['id']}] {q['question'][:22]} → {srcs}")

    # ===== 指标二：拒答准确率（走生产链路）=====
    refuse_ok = 0
    for q in refuse:
        out = search_knowledge.invoke({"query": q["question"]})
        ok = ("未找到" in out) or ("不属于" in out)
        refuse_ok += ok
        flag = "✅" if ok else "❌"
        print(f"{flag} [Q{q['id']}] 拒答：{q['question'][:22]} → {out[:36]}...")

    # ===== 汇总 =====
    print("\n========== 评测报告 ==========")
    print(f"Hit Rate@{TOP_K}: {hit}/{len(answerable)} = {hit/len(answerable):.0%}")
    if refuse:
        print(f"拒答准确率:  {refuse_ok}/{len(refuse)} = {refuse_ok/len(refuse):.0%}")


if __name__ == "__main__":
    main()
