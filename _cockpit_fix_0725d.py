#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
驾驶舱精选 A/B 档标题加阈值提示
- A 档标题旁加 "A 档 ≥70 优先"
- B 档标题旁加 "B 档 ≥50 重点跟踪"
目标：index_master.html + standalone/{overview,predict,gold,health,query,shmonitor}.html
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
TARGETS = [
    "index_master.html",
    "standalone/overview.html",
    "standalone/predict.html",
    "standalone/gold.html",
    "standalone/health.html",
    "standalone/query.html",
    "standalone/shmonitor.html",
]

PATCHES = [
    (
        "A-tier-badge",
        "html += '<div style=\"font-size:13px;font-weight:700;color:#004d40;margin:6px 0 4px;\">🅰️ 拿住别动型（双真 + 不超买 + EMA完好）<span style=\"font-size:10px;color:#00695c;font-weight:400;margin-left:6px;\">· 按总评分降序</span></div>';",
        "html += '<div style=\"font-size:13px;font-weight:700;color:#004d40;margin:6px 0 4px;\">🅰️ 拿住别动型（双真 + 不超买 + EMA完好）<span style=\"font-size:10px;background:#fff3e0;color:#e65100;padding:1px 6px;border-radius:4px;margin-left:6px;\">A 档 ≥70 优先</span><span style=\"font-size:10px;color:#00695c;font-weight:400;margin-left:6px;\">· 按总评分降序</span></div>';",
    ),
    (
        "B-tier-badge",
        "html += '<div style=\"font-size:13px;font-weight:700;color:#004d40;margin:6px 0 4px;\">🅱️ 提前埋伏型（早期信号，趋势未确认）<span style=\"font-size:10px;color:#00695c;font-weight:400;margin-left:6px;\">· 按总评分降序</span></div>';",
        "html += '<div style=\"font-size:13px;font-weight:700;color:#004d40;margin:6px 0 4px;\">🅱️ 提前埋伏型（早期信号，趋势未确认）<span style=\"font-size:10px;background:#fff3e0;color:#e65100;padding:1px 6px;border-radius:4px;margin-left:6px;\">B 档 ≥50 重点跟踪</span><span style=\"font-size:10px;color:#00695c;font-weight:400;margin-left:6px;\">· 按总评分降序</span></div>';",
    ),
]

ok = 0
fail = 0
for rel in TARGETS:
    path = os.path.join(BASE, rel)
    with open(path, "r", encoding="utf-8") as f:
        s = f.read()
    for name, old, new in PATCHES:
        cnt = s.count(old)
        if cnt == 1:
            s = s.replace(old, new)
        elif cnt == 0:
            # 可能已打过，检查新串
            if new in s:
                print(f"  {rel}: {name} already applied")
                continue
            print(f"  ❌ {rel}: {name} OLD not found")
            fail += 1
        else:
            print(f"  ❌ {rel}: {name} OLD ambiguous ({cnt})")
            fail += 1
    with open(path, "w", encoding="utf-8") as f:
        f.write(s)
    print(f"✅ {rel}")
    ok += 1

print(f"\n结果：{ok} 个文件处理，{fail} 处失败")
raise SystemExit(1 if fail else 0)
