"""域门判断与编码 token 匹配，保持零重依赖，便于单测。"""
import re

# 域外黑名单：明显不属于水泵房设备运维的话题才拒答。
# 其余（含"停电恢复 / 历史数据 / 三点复测"这类不含专业词的合法问题）一律放行，
# 交给检索距离阈值兜底——避免白名单误杀合法问题。
OUT_OF_DOMAIN_TERMS = (
    # 餐饮 / 生活
    "食堂", "开饭", "午饭", "晚饭", "早饭", "点餐", "吃饭",
    # 人事 / 行政
    "年假", "请假", "放假", "考勤", "工资", "薪资", "招聘", "社保", "公积金",
    # 公司事务 / 闲聊
    "年终总结", "团建", "年会", "福利",
    "天气", "股票", "游戏", "电影", "音乐", "新闻", "明星",
    # 通用无关请求
    "写诗", "翻译", "画画", "写代码",
)

# 子串匹配覆盖不了的变体写法（如「写一首诗」「写首诗」）
OUT_OF_DOMAIN_PATTERNS = (
    re.compile(r"写.{0,4}诗"),
)

# 编码型 token：E03 / TEMP-001 / PUMP-X201 这类"字母+数字"标识符
_TOKEN_RE = re.compile(r"[A-Z]{1,5}[-_]?\d{2,4}")


def _in_domain(query: str) -> bool:
    """黑名单排除：命中域外话题返回 False 拒答，否则放行给阈值判定。"""
    q = query.upper()
    if any(p.search(q) for p in OUT_OF_DOMAIN_PATTERNS):
        return False
    return not any(t.upper() in q for t in OUT_OF_DOMAIN_TERMS)


def _has_exact_hit(query: str, text: str) -> bool:
    """query 里的编码 token 出现在 text 里 → 精确命中，绕过距离阈值。"""
    tokens = _TOKEN_RE.findall(query.upper())
    if not tokens:
        return False
    up = text.upper()
    return any(t in up for t in tokens)
