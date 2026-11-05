"""
rag/inspect_db.py
作用：查看 chroma_db 里有哪些集合、各多少条数据、原文长什么样
运行：在仓库根目录执行  python -m rag.inspect_db
     可选参数：--sample 3  每个集合打印前 3 条原文（默认不打印）
"""
import argparse
import sys

import chromadb

sys.stdout.reconfigure(encoding="utf-8")  # Windows 控制台默认 GBK，强制 UTF-8 避免 emoji 报错


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=int, default=0,
                        help="每个集合打印前 N 条原文，默认 0 不打印")
    args = parser.parse_args()

    client = chromadb.PersistentClient(path="chroma_db")

    collections = client.list_collections()
    if not collections:
        print("⚠️ chroma_db 里还没有任何集合，先跑 python -m rag.build_index")
        return

    for coll in collections:
        count = coll.count()
        print(f"📚 {coll.name}  →  {count} 条")

        if args.sample > 0 and count > 0:
            data = coll.get(limit=args.sample)
            for doc, meta in zip(data["documents"], data["metadatas"]):
                source = meta.get("source", "?")
                preview = doc[:60].replace("\n", " ")
                print(f"    [{source}] {preview}{'...' if len(doc) > 60 else ''}")


if __name__ == "__main__":
    main()
