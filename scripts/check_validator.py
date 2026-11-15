"""
scripts/check_validator.py
作用：不启动服务，直接验证 ChatRequest 的校验规则有没有生效
      —— 用来区分「模型没写对」和「路由根本没用这个模型」两种完全不同的病
运行：项目根目录执行 python -m scripts.check_validator
"""
from pydantic import ValidationError

# 你的 ChatRequest 定义在哪就 import 哪：多数人写在 api/main.py
from api.schemas import ChatRequest

CASES = [
    ("空字符串",     "",          422),
    ("三个空格",     "   ",       422),
    ("正常中文",     "你好",      200),
    ("超长 600 字",  "a" * 600,   422),
]

def main() -> int:
    failed = 0
    for name, raw, expect in CASES:
        try:
            obj = ChatRequest(message=raw)
            got, detail = 200, f"通过，message={obj.message!r}"
        except ValidationError as e:
            got, detail = 422, e.errors()[0]["msg"]
        ok = got == expect
        failed += 0 if ok else 1
        print(f"{'✅' if ok else '❌'} {name}: 期望 {expect} / 实际 {got} | {detail}")
    print()
    if failed:
        print("→ 模型层就有问题：去改 ChatRequest（看原因 A / A2），别碰路由")
    else:
        print("→ 模型层正常：问题在路由参数（原因 B / C），或服务没重启（原因 D）")
    return failed

if __name__ == "__main__":
    raise SystemExit(1 if main() else 0)