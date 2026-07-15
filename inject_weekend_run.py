#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""周末轻量维护：向 dist/index_master.html 注入 window.WEEKEND_RUN 标注。

设计约束（来自用户铁律）：
- 不调用任何行情接口，不执行 update_data_v2，不修改任何数据 JSON 的 update_time。
- 只修改 dist/index_master.html 里的一个 window 变量占位符。
- 若 dist 已有 window.WEEKEND_RUN 则替换其值；否则在 CANDIDATE_POOL 声明前插入。
"""
import os
import re
import json
import sys
import datetime

WS = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(WS, "dist", "index_master.html")


def main():
    now = datetime.datetime.now()
    wk_cn = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][now.weekday()]
    wk_en = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"][now.weekday()]
    ts = now.strftime("%Y-%m-%d %H:%M")
    data = {
        "last_run": ts,
        "weekday": wk_cn,
        "weekday_en": wk_en,
        "note": "周末轻量维护已执行（数据仍为最近交易日收盘）",
    }

    if not os.path.exists(TARGET):
        print("✗ dist/index_master.html 不存在，跳过 WEEKEND_RUN 注入")
        sys.exit(0)

    with open(TARGET, "r", encoding="utf-8") as f:
        html = f.read()

    js = "window.WEEKEND_RUN = " + json.dumps(data, ensure_ascii=False) + ";"

    if "window.WEEKEND_RUN" in html:
        html = re.sub(r"window\.WEEKEND_RUN\s*=\s*\{.*?\};", js, html, flags=re.S)
    else:
        # 在 CANDIDATE_POOL 声明前插入，确保渲染前定义
        html = html.replace("window.CANDIDATE_POOL", js + "\nwindow.CANDIDATE_POOL", 1)

    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✓ WEEKEND_RUN 注入成功: {wk_cn} {ts}")


if __name__ == "__main__":
    main()
