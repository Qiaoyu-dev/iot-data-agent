"""
rag/chunk.py
作用：把 .md 文本切成适合 Embedding 的 chunk
策略（三级）：
  ① 按 Markdown 标题（#/##/###）切成大块，标题保留在块首（块的主题标签）
  ② 块内按空行拆成段落（自然语义单元）
  ③ 超过 max_chars 的长段落退化为滑动窗口（带重叠）兜底
"""
import re


def split_by_structure(text: str, max_chars: int = 300,
                       overlap: int = 50) -> list[str]:
    """结构化切分入口：返回 chunk 字符串列表"""
    # ① 按标题行切大块。正则 (?=...) 是"前瞻"：在标题行前面断开，
    #    标题本身留在下一块的开头，不切掉
    blocks = re.split(r"(?m)(?=^#{1,3}\s)", text)

    chunks = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        # ② 块内按空行拆段落（Markdown 的段落分隔符就是空行）
        paras = [p.strip() for p in block.split("\n\n") if p.strip()]
        for para in paras:
            if len(para) <= max_chars:
                chunks.append(para)
            else:
                # ③ 超长段落兜底：滑动窗口切小
                chunks.extend(_sliding_window(para, max_chars, overlap))
    return chunks


def _sliding_window(text: str, size: int, overlap: int) -> list[str]:
    """滑动窗口：每 size 字一块，相邻块重叠 overlap 字（防答案被切断）"""
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + size])
        start += size - overlap   # 步长 = 块长 - 重叠 = 250
    return chunks


# ============ 自测：直接 python rag/chunk.py 就能看到切分效果 ============
if __name__ == "__main__":
    from pathlib import Path
    sample = Path("data/docs/manuals")
    mds = sorted(sample.glob("*.md"))
    if not mds:
        print("⚠️ data/docs/manuals/ 下没有 .md，先放文档")
    for md in mds:
        chunks = split_by_structure(md.read_text(encoding="utf-8"))
        print(f"\n=== {md.name}: 切成 {len(chunks)} 块 ===")
        for i, ck in enumerate(chunks):
            # 打印每块长度和前 30 字，肉眼检查是否沿语义边界断开
            preview = ck.replace("\n", " ")[:30]
            print(f"  [{i}] {len(ck):4d} 字 | {preview}...")