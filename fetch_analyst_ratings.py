#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分析师研报评级 — akshare 直查模式
用法：python fetch_analyst_ratings.py
输出：data/analyst_ratings.json

策略：
  1. 从 gold_pool.json 取评分最高的 TOP40 个股
  2. stock_research_report_em() 批量查每只股的研报
  3. 筛选当日/近期研报，提取评级、机构、报告数
  4. 汇总 upgrades/downgrades/new_coverage/hot_stocks
"""
import json, os, sys, datetime, time as _time
import akshare as ak

OUT = "data/analyst_ratings.json"
MAX_STOCKS = 40  # 最多查40只（避免过慢）
TODAY = datetime.date.today().isoformat()

def log(msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

def load_gold_codes():
    """从金股池取评分最高的股票代码列表"""
    gp_path = "data/gold_pool.json"
    codes = []
    try:
        with open(gp_path, encoding='utf-8') as f:
            gp = json.load(f)
        stocks = gp.get("stocks", {})
        sorted_items = sorted(stocks.items(),
            key=lambda x: x[1].get("score", 0) or 0, reverse=True)
        for k, v in sorted_items:
            code = k.split("_")[-1]  # sz_000776 → 000776
            if len(code) == 6 and code.isdigit():
                codes.append(code)
    except Exception as e:
        log(f"⚠️ 读取金股池失败: {e}")
    return codes[:MAX_STOCKS]

def fetch_stock_reports(code):
    """查询单只个股研报，返回最近的报告列表"""
    try:
        df = ak.stock_research_report_em(symbol=code)
        if df.empty:
            return []
        reports = []
        for _, row in df.head(20).iterrows():
            date_str = str(row.get("日期", ""))
            reports.append({
                "code": code,
                "name": str(row.get("股票简称", "")),
                "title": str(row.get("报告名称", ""))[:120],
                "rating": str(row.get("东财评级", "")),
                "institution": str(row.get("机构", "")),
                "report_count_1m": int(row.get("近一月个股研报数", 0) or 0),
                "industry": str(row.get("行业", "")),
                "date": date_str,
            })
        return reports
    except Exception as e:
        return []

def main():
    log("分析师研报抓取 (akshare)...")
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    result = {
        "update_time": now_str,
        "upgrades": [],
        "downgrades": [],
        "new_coverage": [],
        "hot_stocks": [],
        "latest_reports": [],
        "note": "",
    }

    codes = load_gold_codes()
    log(f"金股池 TOP{len(codes)} 只，开始逐只查询...")

    all_reports = []
    done = 0
    for code in codes:
        reports = fetch_stock_reports(code)
        all_reports.extend(reports)
        done += 1
        if done % 10 == 0:
            log(f"  进度: {done}/{len(codes)}")
        _time.sleep(0.3)  # 限速

    log(f"共获取 {len(all_reports)} 条研报记录")

    # 筛选当日研报
    today_reports = [r for r in all_reports if r["date"] == TODAY]
    # 近一周研报
    week_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    week_reports = [r for r in all_reports if r["date"] >= week_ago]

    log(f"当日研报: {len(today_reports)} 条, 近一周: {len(week_reports)} 条")

    # 汇总热点个股（近3日有研报 + 正面评级 = 新增推荐信号）
    three_days_ago = (datetime.date.today() - datetime.timedelta(days=3)).isoformat()
    POSITIVE_RATINGS = {"买入", "增持", "强烈推荐", "推荐", "优于大市", "跑赢行业"}
    
    seen_codes = set()
    hot_list = []
    # 先按日期排序（最新的在前），再按评级优先级排序
    def rating_priority(r):
        rt = r.get("rating", "")
        if rt in ("买入", "强烈推荐"): return 0
        if rt in ("增持", "推荐"): return 1
        if rt in ("优于大市", "跑赢行业"): return 2
        return 99
    
    for r in sorted(all_reports, key=lambda x: (x["date"], rating_priority(x)), reverse=True):
        code = r["code"]
        if code not in seen_codes and r["report_count_1m"] > 0:
            # 只收录近3日内有正面评级的 → 代表近期新增关注
            rt = r.get("rating", "").strip()
            if rt and rt != "nan" and rt in POSITIVE_RATINGS and r["date"] >= three_days_ago:
                seen_codes.add(code)
                hot_list.append({
                    "code": code,
                    "name": r["name"],
                    "rating": rt,
                    "institution": r["institution"],
                    "report_count_1m": r["report_count_1m"],
                    "date": r["date"],
                })

    result["hot_stocks"] = hot_list[:20]

    # 最新研报
    result["latest_reports"] = [
        {"code": r["code"], "name": r["name"], "title": r["title"],
         "rating": r["rating"], "institution": r["institution"], "date": r["date"]}
        for r in today_reports[:30] if r["date"] == TODAY
    ]

    # 评级统计
    rating_counts = {}
    for r in today_reports:
        rt = r["rating"]
        if rt and rt != "nan":
            rating_counts[rt] = rating_counts.get(rt, 0) + 1
    if rating_counts:
        result["rating_summary"] = rating_counts

    result["note"] = f"数据源: akshare(TOP{len(codes)}个股), 近3日新增推荐{len(hot_list)}只（买入/增持）"
    if len(today_reports) == 0:
        result["note"] += f" (当日研报{len(today_reports)}条, 盘后T+1发布)"

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    log(f"✅ 已保存: {OUT} (热点{len(hot_list)}只, 当日{len(today_reports)}条)")

if __name__ == "__main__":
    from fetch_logger import record_success, record_failure
    try:
        main()
        record_success(__file__)
    except Exception as e:
        record_failure(__file__, str(e))
        raise
