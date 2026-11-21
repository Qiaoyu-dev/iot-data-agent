"""
tests/test_knowledge.py
单元测试：tools/domain.py 的纯函数 —— _in_domain / _has_exact_hit。
原则：纯函数测试不烧 API key、不依赖网络，快且可复现。
运行：pytest tests/test_knowledge.py -v
"""
from tools import domain as K


def test_in_domain_rejects_out_of_domain():
    # 命中域外黑名单 → 应该拒答
    assert K._in_domain("今天食堂吃什么") is False
    assert K._in_domain("我请了年假") is False
    assert K._in_domain("帮我写一首诗") is False


def test_in_domain_allows_legal_queries():
    # 不含黑名单词、但可能没有专业词的合法问题 → 放行，交给距离阈值兜底
    # （这正是你 Q17/Q22/Q24 从白名单误杀改成黑名单放行的原因）
    assert K._in_domain("停电了怎么恢复") is True
    assert K._in_domain("三点复测怎么做") is True


def test_has_exact_hit():
    # 编码型 token（TEMP-001 这类）出现在文本里 → 精确命中
    assert K._has_exact_hit("TEMP-001 温度", "设备 TEMP-001 的读数") is True
    assert K._has_exact_hit("TEMP-001 温度", "设备一切正常") is False
