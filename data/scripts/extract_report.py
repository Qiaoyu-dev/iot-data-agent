"""
data/scripts/extract_report.py
作用：扫描 data/docs/ 下所有 .md（递归子目录），用正则提取关键字段（告警阈值/设备型号/巡检周期），
     汇总成结构化 JSON 存到 data/eval/manual_fields.json
运行：在仓库根目录执行  python data/scripts/extract_report.py
前置：先跑通 parse_pdf.py（或放好兜底 pump_manual.md）
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # Windows 控制台默认 GBK，避免 emoji 报错

DOCS_DIR = Path("data/docs")
OUT = Path("data/eval/manual_fields.json")
OUT.parent.mkdir(parents=True, exist_ok=True)  # 确保 eval 目录存在

# 字段名 → 正则模板。[：:] 表示中英文冒号都能匹配，\s* 允许任意空格
PATTERNS = {
    "alert_threshold": r"告警阈值[：:]\s*([\d.]+\s*°?C)",
    "device_model":    r"设备型号[：:]\s*(\S+)",
    "check_cycle":     r"巡检周期[：:]\s*(\S+)",
}

results = {}
for md in sorted(DOCS_DIR.rglob("*.md")):
    text = md.read_text(encoding="utf-8")
    fields = {}
    for key, pat in PATTERNS.items():
        m = re.search(pat, text)          # search = 找第一个匹配就停
        if m:
            fields[key] = m.group(1)      # group(1) = 括号捕获的内容
    results[md.stem] = fields
    print(f"{md.name}: 提取到 {len(fields)}/{len(PATTERNS)} 个字段")

OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2),
               encoding="utf-8")
print(f"\n✅ 结构化结果已存 → {OUT}")