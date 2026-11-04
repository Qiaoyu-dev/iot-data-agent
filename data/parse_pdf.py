"""
data/parse_pdf.py
作用：遍历 data/docs_raw/ 下所有 PDF，逐页提取文字层文本，
     输出 Markdown 到 data/docs/{同名}.md，每页带页码标记（RAG 溯源用）。
运行：在仓库根目录执行  python data/parse_pdf.py
依赖：pip install pypdf
"""
from pathlib import Path
from pypdf import PdfReader

RAW_DIR = Path("data/docs_raw")   # 原始 PDF 放这里
OUT_DIR = Path("data/docs")       # 解析结果输出到这里
OUT_DIR.mkdir(parents=True, exist_ok=True)  # 目录不存在就自动创建


def parse_pdf(pdf_path: Path) -> str:
    """解析单个 PDF，返回带页码标记的完整文本"""
    reader = PdfReader(pdf_path)
    parts = []
    for i, page in enumerate(reader.pages, start=1):
        # extract_text() 对纯图片页会返回 None，用 or "" 兜底
        text = (page.extract_text() or "").strip()
        if not text:
            continue  # 跳过没有文字层的页（图片页/空白页）
        # 页码标记：明天切块后会留在 chunk 里，检索结果可溯源到页
        parts.append(f"[第{i}页]\n{text}")
    return "\n\n".join(parts)


def main():
    pdfs = sorted(RAW_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"⚠️ {RAW_DIR}/ 下没有找到 PDF，请先放入设备手册")
        return
    for pdf in pdfs:
        content = parse_pdf(pdf)
        if not content:
            print(f"⚠️ {pdf.name} 没有提取到任何文字（可能是扫描件）")
            continue
        out_path = OUT_DIR / f"{pdf.stem}.md"   # stem = 去掉扩展名的文件名
        out_path.write_text(content, encoding="utf-8")
        print(f"✅ {pdf.name} → {out_path}（{len(content)} 字符）")


if __name__ == "__main__":
    main()