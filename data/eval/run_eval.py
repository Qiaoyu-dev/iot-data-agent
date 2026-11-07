"""
data/eval/run_eval.py
作用：加载评测集，逐条跑检索，计算两个指标：
     ① Hit Rate@3：应答问题中 top3 命中正确来源的比例
     ② 拒答准确率：拒答问题中正确"零证据通过"的比例
运行：在仓库根目录执行  python data/eval/run_eval.py
前置：eval_questions.jsonl 已建好，build_index.py 已灌库
"""
import json
from pathlib import Path

from rag.retrieve import retrieve

EVAL_FILE = Path("data/eval/eval_questions.jsonl")
TOP_K = 3
# 与周一 search_test.py 校准的阈值保持一致
DISTANCE_THRESHOLD = 1.2


def load_questions() -> list[dict]:
    """逐行读 JSONL，跳过空行"""
    lines = EVAL_FILE.read_text(encoding="utf-8").splitlines()
    return [json.loads(ln) for ln in lines if ln.strip()]


def kept_sources(question: str) -> list[str]:
    """检索并做阈值过滤，返回保留下来的证据来源列表"""
    hits = retrieve(question, top_k=TOP_K)
    return [h["source"] for h in hits
            if h["distance"] < DISTANCE_THRESHOLD]


def main():
    questions = load_questions()
    answerable = [q for q in questions if q["should_answer"]]
    refuse = [q for q in questions if not q["should_answer"]]

    # ===== 指标一：Hit Rate@3（应答类）=====
    hit = 0
    for q in answerable:
        sources = kept_sources(q["question"])
        # 命中 = 正确来源出现在保留证据里
        ok = any(q["gold_source"] in s for s in sources)
        hit += ok
        print(f"{'✅' if ok else '❌'} [Q{q['id']}] {q['question'][:24]} → {sources}")

    # ===== 指标二：拒答准确率（拒答类）=====
    refuse_ok = 0
    for q in refuse:
        n_kept = len(kept_sources(q["question"]))
        ok = (n_kept == 0)   # 期望：所有证据都因超阈值被丢弃
        refuse_ok += ok
        print(f"{'✅' if ok else '❌'} [Q{q['id']}] 拒答测试：{q['question'][:24]}"
              f"（残留证据 {n_kept} 条）")

    # ===== 汇总报告 =====
    print(f"\n========== 评测报告 ==========")
    print(f"Hit Rate@{TOP_K}: {hit}/{len(answerable)} = {hit/len(answerable):.0%}")
    if refuse:
        print(f"拒答准确率:  {refuse_ok}/{len(refuse)} = {refuse_ok/len(refuse):.0%}")


if __name__ == "__main__":
    main()