"""SSE 流式请求测试脚本
为什么用 Python 而不是 curl：Git Bash 在中文 Windows 上会把命令行里的中文
按 GBK 编码发出去，导致 FastAPI 报 "There was an error parsing the body"。
Python 源文件是 UTF-8，json 序列化天然 UTF-8，不受终端编码影响。

运行：
    python tools/sse_test.py                          # 用默认问题
    python tools/sse_test.py "HUM-002 这周湿度多少？"   # 自定义问题
"""
import sys
import httpx

# 默认问题直接写在 UTF-8 源文件里，避免 argv 编码问题
DEFAULT_MESSAGE = "TEMP-001 这周平均温度多少？"


def main() -> None:
    message = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MESSAGE
    thread_id = sys.argv[2] if len(sys.argv) > 2 else "sse-test"

    url = "http://127.0.0.1:8000/chat/stream"
    print(f"→ POST {url}  message={message!r}\n", flush=True)

    with httpx.stream(
        "POST",
        url,
        json={"message": message, "thread_id": thread_id},
        timeout=httpx.Timeout(60.0),
    ) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if line:
                print(line, flush=True)


if __name__ == "__main__":
    main()
