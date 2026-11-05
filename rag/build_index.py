"""
rag/build_index.py  (v2 · 多知识库版)
作用：遍历 data/docs/ 的一级子目录，切分 .md 后 Embedding 灌入 Chroma
隔离约定：data/docs/<子目录名>/  →  collection "iot_<子目录名>"
         manuals/ → iot_manuals，reports/ → iot_reports
运行：在仓库根目录执行  python -m rag.build_index
     （不要用 python rag/build_index.py，直接跑文件会找不到 rag 包）
依赖：chromadb、zhipuai；.env 配好 ZHIPU_API_KEY
"""
from pathlib import Path
import sys

import chromadb

sys.stdout.reconfigure(encoding="utf-8")  # Windows 控制台默认 GBK，强制 UTF-8 避免 emoji 报错

from rag.chunk import split_by_structure   # 任务一的结构化切分
from rag.embed import embed                 # 11.3 已建好的智谱封装

DOCS_DIR = Path("data/docs")
client = chromadb.PersistentClient(path="chroma_db")  # 持久化：重启不丢


def build_kb(sub: Path):
    """把一个子目录灌成一个独立知识库"""
    coll_name = f"iot_{sub.name}"
    coll = client.get_or_create_collection(coll_name)
    total = 0
    for md in sorted(sub.glob("*.md")):
        chunks = split_by_structure(md.read_text(encoding="utf-8"))
        if not chunks:
            continue
        # upsert 而不是 add：重复跑脚本不会产生重复数据（幂等）
        coll.upsert(
            ids=[f"{md.stem}#{i}" for i in range(len(chunks))],
            embeddings=embed(chunks),            # 智谱 embedding-3 批量向量化
            documents=chunks,
            metadatas=[{"source": md.name, "kb": coll_name}
                       for _ in chunks],
        )
        total += len(chunks)
        print(f"  {md.name}: {len(chunks)} chunks")
    print(f"✅ 知识库 {coll_name}: 本次写入 {total} 块，库内共 {coll.count()} 条")


def main():
    dirs = [d for d in sorted(DOCS_DIR.iterdir()) if d.is_dir()]
    if not dirs:
        print("⚠️ data/docs/ 下没有子目录，请先建 manuals/reports 并放入 .md")
        return
    for sub in dirs:
        build_kb(sub)


if __name__ == "__main__":
    main()