#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
weekly_maintain_stock_meta.py — 周度个股元数据维护编排（本机/云端均可调用）
============================================================================

铁律对应：每周补足新股票的一切、删除退市股的一切，并把数据提交主仓「存好别再丢」。

步骤：
  1. fetch_industry_map.py   重建行业映射（覆盖股池并集，含新进股票行业）
  2. fetch_concept_map.py    重建概念映射并回填 industry_map.json 的 concepts
  3. maintain_industry_map.py  删退市股 + enrich candidate_pool/gold_pool + BaoStock 补行业
  4. git 提交并推主仓（pull --rebase 防冲突），让云端日常部署自然带上最新元数据
  5. verify_coverage()       核验候选池+金股池 行业/板块/概念 覆盖率（跟踪更新效果）
  6. deploy_site()           重建 dist 并部署到 gh-pages（周度任务必须含部署）

任一抓取步骤失败不致命，后续步骤继续；最后统一 git 提交已刷新的数据文件。

用法：
  python weekly_maintain_stock_meta.py
  python weekly_maintain_stock_meta.py --no-push   # 只刷新不提交（调试用）
"""
import os
import sys
import time
import subprocess
import json
import argparse

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")


def log(msg):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), msg))


def run(cmd):
    log("RUN: %s" % cmd)
    r = subprocess.run(cmd, shell=True, cwd=BASE)
    return r.returncode == 0


def verify_coverage():
    """核验候选池+金股池的 行业/板块/概念 覆盖率，作为「跟踪更新」的回报。"""
    pools = {}
    for fn in ("candidate_pool.json", "gold_pool.json"):
        p = os.path.join(DATA, fn)
        if os.path.exists(p):
            try:
                d = json.load(open(p, "r", encoding="utf-8"))
                pools[fn] = d.get("stocks", {})
            except Exception:
                pools[fn] = {}
    for fn, stocks in pools.items():
        n = len(stocks)
        if not n:
            continue
        ind = sum(1 for v in stocks.values() if v.get("industry"))
        con = sum(1 for v in stocks.values() if v.get("concepts"))
        board = sum(1 for v in stocks.values() if v.get("board_label") or v.get("board"))
        log("覆盖率 %s: 行业 %d/%d (%.0f%%) | 板块 %d/%d (%.0f%%) | 概念 %d/%d (%.0f%%)"
            % (fn, ind, n, 100.0*ind/n, board, n, 100.0*board/n, con, n, 100.0*con/n))


def deploy_site():
    """部署到 gh-pages（周度任务必须含部署，确保网站带上最新元数据）。"""
    dp = os.path.join(BASE, "deploy_now.py")
    if not os.path.exists(dp):
        log("[SKIP] deploy_now.py 不存在，跳过部署")
        return
    # 先重建 dist（把最新元数据注入全站），再部署
    if os.path.exists(os.path.join(BASE, "update_data_v2.py")):
        run("%s update_data_v2.py" % sys.executable) or log("[WARN] update_data_v2 失败")
    if os.path.exists(os.path.join(BASE, "ensure_standalone_sync.py")):
        run("%s ensure_standalone_sync.py --inject-buildstamp" % sys.executable) \
            or log("[WARN] ensure_standalone_sync 失败")
    run("%s deploy_now.py --force" % sys.executable) or log("[WARN] deploy 失败，请手动检查")


def git_commit_push():
    """安全提交数据文件并推主仓（先 pull --rebase）。"""
    targets = [
        "data/industry_map.json",
        "data/concept_map.json",
        "data/candidate_pool.json",
        "data/gold_pool.json",
    ]
    existing = [t for t in targets if os.path.exists(os.path.join(BASE, t))]
    if not existing:
        log("无可提交数据文件，跳过")
        return
    run("git add " + " ".join(existing))
    # 仅在有变更时提交
    st = subprocess.run("git status --porcelain " + " ".join(existing),
                        shell=True, cwd=BASE, capture_output=True, text=True)
    if not st.stdout.strip():
        log("数据无变更，无需提交")
        return
    ts = time.strftime("%Y-%m-%d %H:%M")
    run('git commit -m "weekly: 维护个股行业/概念元数据 %s" ' % ts)
    run("git pull --rebase --autostash origin main")
    run("git push origin main")
    log("已提交并推主仓")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-push", action="store_true", help="只刷新不提交")
    args = ap.parse_args()

    py = sys.executable
    t0 = time.time()

    log("=== 周度个股元数据维护开始 ===")
    # 1. 行业重建（best-effort，可能 20+ 分钟）
    if os.path.exists(os.path.join(BASE, "fetch_industry_map.py")):
        run("%s fetch_industry_map.py" % py) or log("[WARN] fetch_industry_map 失败，沿用既有行业数据")
    else:
        log("[SKIP] fetch_industry_map.py 不存在")

    # 2. 概念重建 + 回填 industry_map
    if os.path.exists(os.path.join(BASE, "fetch_concept_map.py")):
        run("%s fetch_concept_map.py" % py) or log("[WARN] fetch_concept_map 失败，沿用既有概念数据")
    else:
        log("[SKIP] fetch_concept_map.py 不存在")

    # 3. 删退市 + enrich 股池 + 补行业
    if os.path.exists(os.path.join(BASE, "maintain_industry_map.py")):
        run("%s maintain_industry_map.py" % py) or log("[WARN] maintain_industry_map 失败")
    else:
        log("[SKIP] maintain_industry_map.py 不存在")

    # 4. 提交主仓
    if not args.no_push:
        git_commit_push()
    else:
        log("[no-push] 跳过提交")

    # 5. 覆盖率核验（跟踪更新效果）
    verify_coverage()

    # 6. 部署到 gh-pages（周度任务必须含部署）
    if not args.no_push:
        deploy_site()
    else:
        log("[no-push] 跳过部署")

    log("=== 完成，耗时 %.1f 分 ===" % ((time.time() - t0) / 60))


if __name__ == "__main__":
    main()
