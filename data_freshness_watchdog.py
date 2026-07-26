#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data_freshness_watchdog.py — 九宝量化数据新鲜度自动值守

核心目标：发现关键数据陈旧 -> 自动重跑对应 fetch + 重建 dist + 部署，
不再依赖人工发现"数据旧了"。

规则：
- 行情类数据（板块资金 / ETF / 概念 / 主力 / 北向 / 跟风 / 龙虎榜 / 板块RS）：
    * 仅在【交易日】且当前时间 >= 16:00 检查：若数据 update_time 早于当日 15:30，
      判定盘后缺失 -> 自动重跑对应 fetch + update_data_v2 + deploy + 推 main。
    * 周末 / 法定假日：行情源关闭，重跑只会得到最近交易日快照且易伪造时间戳，
      故【不强行重跑】，仅记录告警，等待下一交易日盘后刷新（不伪造时间戳）。
- 非行情类数据（投行信号 maharo / 危机雷达宏观 / 股池构成）：
    * 任何时间，若 age 超过阈值（默认 48h）-> 自动重跑对应脚本 + 部署。
- 防抖：同一次修复后 30 分钟内不重复触发。
- 所有动作写入 data/freshness_watchdog.log。
"""
import os
import sys
import json
import time
import datetime
import subprocess

WORKSPACE = os.path.dirname(os.path.abspath(__file__))

# 安全同步：彻底消除 stash-pop 冲突（data/ 双机重写根因）
try:
    from git_safe_sync import safe_pull
except ImportError:
    sys.path.insert(0, WORKSPACE)
    from git_safe_sync import safe_pull

DATA_DIR = os.path.join(WORKSPACE, "data")
LOG_FILE = os.path.join(DATA_DIR, "freshness_watchdog.log")
COOLDOWN = 1800  # 30 分钟
NON_MARKET_MAX_AGE_H = 48

# (数据文件, 类型, 重跑脚本)
CRITICAL = [
    ("sector_fund_flow.json", "market", ["fetch_sector_fund_flow.py"]),
    ("etf_subscription.json", "market", ["fetch_etf_subscription.py"]),
    ("concept_ranking.json", "market", ["fetch_concept_ranking.py"]),
    ("market_alerts.json", "market", ["fetch_market_alerts.py"]),
    ("sector_rs.json", "market", ["fetch_sector_rs.py"]),
    ("sh_index_fib.json", "market", ["fetch_sh_index_fib.py"]),  # 同脚本同时产出 sz_index_fib.json（健康看板「选股驾驶舱」大盘可操作区依赖源）
    ("main_stock.json", "market", ["fetch_main_stock.py"]),
    ("north_fund.json", "market", ["fetch_north_fund.py"]),
    ("herding_data.json", "market", ["fetch_herding_data.py"]),
    ("lhb_result.json", "market", ["fetch_lhb.py"]),
    ("maharo_signals.json", "non_market", ["fetch_maharo_signals.py", "--non-interactive"]),
    ("crisis_data.json", "non_market", ["fetch_crisis_data.py"]),
    ("gold_pool.json", "non_market", ["scanner.py", "full"]),  # 2026-07-20 修：原 build_candidate_pool.py 不生成金股池
    ("cockpit_backtest.json", "non_market", ["cockpit_backtest_now.py"]),  # 健康看板「选股驾驶舱」⑦历史回测胜率块依赖源（cloud_post_close 16:30 每日重算）
    # ─── 2026-07-19 闭环审计补入：前端核心展示数据 ───
    ("top10_daily.json", "market", ["generate_top10.py"]),  # 驾驶舱③区共振候选核心依赖（total_score）
    ("nt_data.json", "market", ["fetch_nt_data.py"]),  # 北向资金+交易日历
    ("crds_result.json", "market", ["calc_crds.py"]),  # CRDS 综合逆势分卡片
    ("capital_flow_summary.json", "market", ["capital_flow_summary.py"]),  # 资金流汇总
    ("recommend.json", "market", ["generate_recommend.py"]),  # 推荐列表
    ("margin_data.json", "market", ["fetch_margin_etf.py"]),  # 融资融券（同脚本产出 etf_subscription.json，已监控）
    ("sh_sz_history.json", "market", ["fetch_sh_sz_history.py"]),  # 沪深历史（双机负责，云端不抓，监控兜底）
    ("macro_data.json", "non_market", ["fetch_macro_data.py"]),  # 宏观经济
    ("industry_map.json", "non_market", ["fetch_industry_map.py"]),  # 行业映射（cloud_weekly 每周重建）
    ("stock_names.json", "non_market", ["fetch_stock_names.py"]),  # 股票名称映射（cloud_weekly 每周五）
    ("guanlan_reports.json", "non_market", ["guanlan_extractor.py"]),  # 观澜台研报
    ("overnight_timeline.json", "non_market", ["fetch_overnight_timeline.py"]),  # 隔夜时间线
    ("fomc_summary.json", "non_market", ["fetch_fomc.py"]),  # FOMC 会议纪要
]


def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = "[%s] %s" % (ts, msg)
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def get_data_time(fn):
    p = os.path.join(DATA_DIR, fn)
    if not os.path.exists(p):
        return None
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception:
        return None
    for k in ("update_time", "fetch_time", "generated_at", "as_of", "scan_time"):
        v = d.get(k)
        if v:
            return v
    return None


def parse_time(s):
    if not s:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.datetime.strptime(s, fmt)
        except Exception:
            pass
    return None


def is_trading_day(d):
    try:
        from is_trading_day import is_trading_day as f
        return f(d)
    except Exception:
        return d.weekday() < 5  # 兜底：周一到周五


def last_trading_day(now):
    d = now.date()
    while not is_trading_day(d):
        d -= datetime.timedelta(days=1)
    return d


def run(script_args, timeout=300):
    try:
        subprocess.run(
            [sys.executable] + script_args,
            cwd=WORKSPACE,
            timeout=timeout,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        return True
    except Exception as e:
        log("  [ERR] %s 失败: %s" % (" ".join(script_args), e))
        return False


def git_sync():
    """部署前先从 origin/main 安全同步本地数据（拿到小九/云端已产出的新鲜数据），
    避免在本机弱网上重复抓取，也避免用本机陈旧本地数据覆盖 main 上的新鲜数据。

    旧实现：stash → ff-only pull → stash pop，双机数据冲突时 pop 必冲突、留下 UU 混乱。
    现统一走 safe_pull()：拉取前丢弃本地派生数据改动（总会被重新构建、权威版在
    origin/main），干净树 rebase 拉取，冲突安全 pop。永绝后患。"""
    try:
        ok = safe_pull()
        if ok:
            log("  已同步 origin/main 最新数据")
        else:
            log("  git 同步跳过(网络问题或分叉)")
    except Exception as e:
        log("  [WARN] git_sync 异常(忽略): %s" % e)


def main():
    now = datetime.datetime.now()
    today = now.date()
    trading = is_trading_day(today)
    last_td = last_trading_day(now)

    log("值守启动 | 今天=%s 交易日=%s 最近交易日=%s" % (today, trading, last_td))

    # 先与 origin/main 同步（拿到小九/云端已产出的新鲜数据），再评估本地陈旧度
    git_sync()

    # 冷却检查
    cooldown_file = os.path.join(WORKSPACE, ".freshness_watchdog.lastfix")
    if os.path.exists(cooldown_file):
        try:
            last_fix = float(open(cooldown_file).read().strip())
            if time.time() - last_fix < COOLDOWN:
                log("冷却中（%d秒前修复过），跳过本次" % int(time.time() - last_fix))
                return
        except Exception:
            pass

    market_stale = []        # 行情类需修复（仅交易日盘后）
    nonmarket_stale = []     # 非行情类需修复（任何时间超阈值）
    market_stale_weekend = []  # 行情类周末陈旧（只告警）

    for fn, typ, scripts in CRITICAL:
        tstr = get_data_time(fn)
        t = parse_time(tstr)
        if t is None:
            log("WARN %s: 无有效时间，视为缺失" % fn)
            (market_stale if typ == "market" else nonmarket_stale).append((fn, scripts))
            continue
        age_h = (now - t).total_seconds() / 3600.0
        if typ == "market":
            if trading and now.hour >= 16:
                deadline = datetime.datetime.combine(today, datetime.time(15, 30))
                if t < deadline:
                    market_stale.append((fn, scripts))
                    log("FIX %s: 交易日盘后缺失 (数据时间 %s < 15:30) -> 待修复" % (fn, tstr))
                else:
                    log("OK %s: 新鲜 (%s)" % (fn, tstr))
            else:
                if t.date() < last_td:
                    market_stale_weekend.append((fn, tstr))
                    log("WARN %s: 周末行情陈旧 (数据 %s < 最近交易日 %s)，等待下一交易日盘后刷新" % (fn, tstr, last_td))
                else:
                    log("OK %s: 周末可接受 (%s)" % (fn, tstr))
        else:
            if age_h > NON_MARKET_MAX_AGE_H:
                nonmarket_stale.append((fn, scripts))
                log("FIX %s: 非行情类陈旧 (%.0fh) -> 待修复" % (fn, age_h))
            else:
                log("OK %s: 新鲜 (%s)" % (fn, tstr))

    to_fix = []
    if trading and now.hour >= 16:
        to_fix += market_stale
    to_fix += nonmarket_stale

    if not to_fix:
        log("无需要自动修复的项目")
        if market_stale_weekend:
            log("周末行情陈旧 %d 项，等待下一交易日自动刷新（不伪造时间戳）" % len(market_stale_weekend))
        return

    log("开始自动修复 %d 项..." % len(to_fix))
    all_scripts = []
    for fn, scripts in to_fix:
        all_scripts.extend(scripts)
    seen = set()
    uniq = []
    for s in all_scripts:
        if s not in seen:
            seen.add(s)
            uniq.append(s)
    for s in uniq:
        log("  运行 %s" % s)
        run([s], timeout=300)
    log("  重建 dist (update_data_v2.py --fast)")
    run(["update_data_v2.py", "--fast"], timeout=400)
    log("  推送数据到 main (push_china_data.py)")
    run(["push_china_data.py"], timeout=180)
    log("  部署 (deploy_now.py --force)")
    run(["deploy_now.py", "--force"], timeout=900)
    try:
        open(cooldown_file, "w").write(str(time.time()))
    except Exception:
        pass
    log("自动修复完成，共 %d 项" % len(to_fix))


if __name__ == "__main__":
    main()
