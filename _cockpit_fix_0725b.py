# -*- coding: utf-8 -*-
"""2026-07-25 傍晚修复（主人反馈）：
1. .content 恢复全站居中（margin: 0 auto）——上一轮误改为全站左对齐
2. cockpitBlock 彩色圆弧条跑到卡片右外侧：box-shadow 漏写 inset 关键字，补上 → 回到左内侧
3. 删除「早期信号雷达」：块 + 函数 + 2 处挂钩（主人不要了）
"""
import io, sys

FILES = [
    'index_master.html',
    'standalone/overview.html',
    'standalone/predict.html',
    'standalone/gold.html',
    'standalone/health.html',
    'standalone/query.html',
    'standalone/shmonitor.html',
]

PATCHES = [
    ("P1 恢复居中",
     ".content { padding: 14px; max-width: 1400px; margin: 0; }",
     ".content { padding: 14px; max-width: 1400px; margin: 0 auto; }"),
    ("P2 彩条回左侧(inset)",
     "box-shadow:4px 0 0 0 '+color+', 0 1px 2px rgba(0,0,0,0.04);",
     "box-shadow:inset 4px 0 0 0 '+color+', 0 1px 2px rgba(0,0,0,0.04);"),
    ("P3 删雷达块",
     "  // 🛰 早期信号雷达（苗头阶段：B档早期信号 + 三重选股，异步填充）\n  h += cockpitBlock('🛰 早期信号雷达（苗头阶段 · 信号未确认，仅供跟踪）', '<div id=\"cockpitEarlyRadar\" style=\"font-size:12px;color:#999;\">加载早期信号...</div>', '#ffe0b2', '#e65100');\n",
     ""),
    ("P4 删挂钩1",
     "    try{ renderCockpitEarlyRadar(d); }catch(e){}\n",
     ""),
    ("P5 删挂钩2",
     "    try{ renderCockpitEarlyRadar(null); }catch(e2){}\n",
     ""),
]

# P6: 删函数体（跨多行，用起止标记切）
FN_START = "// 🛰 早期信号雷达（2026-07-25 新增：B档早期信号 + 三重选股苗头，带触发标签；数据不可得则如实显示暂无）\nfunction renderCockpitEarlyRadar(d){"
FN_END = "  el.innerHTML = hh;\n}\nfunction buildCockpitTierRecommendAlimiHTML"
FN_END_KEEP = "function buildCockpitTierRecommendAlimiHTML"

total_fail = 0
for fp in FILES:
    with io.open(fp, 'r', encoding='utf-8') as f:
        src = f.read()
    orig = src
    results = []
    for name, old, new in PATCHES:
        n = src.count(old)
        if n == 1:
            src = src.replace(old, new)
            results.append(f"{name}:OK")
        elif n == 0:
            results.append(f"{name}:MISS")
        else:
            results.append(f"{name}:MULTI({n})")
    # P6 函数体删除
    i = src.find(FN_START)
    j = src.find(FN_END)
    if i >= 0 and j > i:
        src = src[:i] + src[j + len(FN_END) - len(FN_END_KEEP):]
        results.append("P6删函数:OK")
    else:
        results.append(f"P6删函数:MISS(i={i},j={j})")
    fail = [r for r in results if 'OK' not in r]
    total_fail += len(fail)
    status = 'PARTIAL' if fail else 'ALL-OK'
    if src != orig:
        with io.open(fp, 'w', encoding='utf-8') as f:
            f.write(src)
    print(f"[{status}] {fp}: " + ' | '.join(results))

sys.exit(1 if total_fail else 0)
