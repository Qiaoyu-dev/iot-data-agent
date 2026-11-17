"""
作用：把 .md 文本切成适合 Embedding 的 chunk
rag/chunk.py  (v3 · 段落贪心合并版)
改动点：
  1. 每个 chunk 前面加上所属章节标题，检索时上下文更完整
  2. 相邻段落贪心合并到 max_chars，避免「引言句」和「编号正文」被拆成两个 chunk
  3. 超长段落仍走滑动窗口（相邻块 overlap）
"""
import re

HEADING_RE = re.compile(r"(?m)^(#{1,3})\s+(.+)$")


def split_by_structure(text: str, max_chars: int = 250,
                       overlap: int = 50) -> list[str]:
    """结构化切分：按 Markdown 标题切块，每块带上所属章节标题"""
    # ① 在标题行前面断开，标题留在下一块开头
    blocks = re.split(r"(?m)(?=^#{1,3}\s)", text)

    chunks: list[str] = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # ② 提取本块的标题，正文与标题分离
        first_line, _, rest = block.partition("\n")
        m = HEADING_RE.match(first_line)
        heading = m.group(2).strip() if m else ""
        body = rest.strip() if m else block

        # ③ 正文按空行拆段落，再把相邻短段贪心合并，逼近 max_chars 才断开
        paras = [p.strip() for p in body.split("\n\n") if p.strip()]
        buf = ""
        for para in paras:
            if len(para) > max_chars:
                # 先把已累积的内容落盘，再对超长段落滑动窗口切
                if buf:
                    chunks.append(f"【{heading}】{buf}" if heading else buf)
                    buf = ""
                for piece in _sliding_window(para, max_chars, overlap):
                    chunks.append(f"【{heading}】{piece}" if heading else piece)
            else:
                candidate = f"{buf}\n\n{para}" if buf else para
                if len(candidate) <= max_chars:
                    buf = candidate
                else:
                    chunks.append(f"【{heading}】{buf}" if heading else buf)
                    buf = para
        if buf:
            chunks.append(f"【{heading}】{buf}" if heading else buf)
    return chunks


def _sliding_window(text: str, size: int, overlap: int) -> list[str]:
    """滑动窗口：超长段落切块，相邻块重叠 overlap 字，防答案被切断"""
    out = []
    start = 0
    while start < len(text):
        out.append(text[start:start + size])
        start += size - overlap
    return out


# ============ 自测：python rag/chunk.py ============
if __name__ == "__main__":
    from pathlib import Path

    total = 0
    for md in sorted(Path("data/docs/manuals").glob("*.md")):
        chunks = split_by_structure(md.read_text(encoding="utf-8"))
        lens = [len(c) for c in chunks]
        total += len(chunks)
        print(f"=== {md.name}: {len(chunks)} 块 | "
              f"长度 {min(lens)}~{max(lens)} 字 | 均值 {sum(lens)//len(lens)} ===")
        for i, ck in enumerate(chunks):
            preview = ck.replace("\n", " ")[:36]
            print(f"  [{i}] {len(ck):4d} 字 | {preview}...")
    print(f"\n总计 {total} 块")