"""
scripts/tune_threshold.py
作用：把评测集里应答题和拒答题的 top1 距离全部打出来，
      看能否用一个阈值分开，并给出建议值。
运行：python -m scripts.tune_threshold
"""
import json
from pathlib import Path

from rag.retrieve import retrieve

EVAL_FILE = Path("data/eval/eval_questions.jsonl")


def main():
    rows = [json.loads(l) for l in
            EVAL_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]

    pos, neg = [], []
    for r in rows:
        hits = retrieve(r["question"], top_k=3)
        d1 = hits[0]["distance"] if hits else 9.9
        src = hits[0]["source"] if hits else "-"
        bucket = pos if r["should_answer"] else neg
        bucket.append((d1, r["question"], src))

    print("=== 应答题 top1 距离（降序，最危险的排最上）===")
    for d, q, s in sorted(pos, reverse=True):
        print(f"  {d:.3f}  {q[:26]:<28} ← {s}")

    print("\n=== 拒答题 top1 距离（升序，最危险的排最上）===")
    for d, q, s in sorted(neg):
        print(f"  {d:.3f}  {q[:26]:<28} ← {s}")

    p_max = max(p[0] for p in pos)
    n_min = min(n[0] for n in neg)
    gap = n_min - p_max

    print(f"\n应答题 top1 最大值：{p_max:.3f}")
    print(f"拒答题 top1 最小值：{n_min:.3f}")
    print(f"间隙：{gap:+.3f}")

    if gap > 0:
        print(f"→ 单阈值可以分开，建议取 {(p_max + n_min) / 2:.2f}")
    else:
        print("→ 有重叠，单阈值不够，需要靠业务域闸门兜底（见步骤三）")


if __name__ == "__main__":
    main()