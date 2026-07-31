#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
candidate_pool 看门狗 — 根治 09:20 盘前构建失败后全天陈旧数据上线的问题。

逻辑：
  1. 检查 data/candidate_pool.json 的 update_time 距离现在多久。
  2. 若在交易时段且候选池年龄超过阈值（默认 60 分钟），自动重跑
     build_candidate_pool.py → update_data_v2.py → deploy_now.py --force。
  3. 重试最多 2 次，避免偶发抖动；仍失败则记录失败日志，不强行部署陈旧数据。

调度：建议通过 WorkBuddy automation 每 30 分钟执行一次：
  python watch_candidate_pool.py

约束：
  - 非交易日/周末不主动抓行情（依赖 is_trading_day）。
  - 候选池本身已陈旧时不部署，避免覆盖小九/阿狸咪正在推的新鲜数据。
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime, timezone, timedelta

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(WORKSPACE, "data")
POOL_FILE = os.path.join(DATA_DIR, "candidate_pool.json")
LOG_FILE = os.path.join(WORKSPACE, ".fetch_log", "watch_candidate_pool.log")
MAX_AGE_MINUTES = 60          # 交易时段内候选池最大允许年龄
RETRY_ATTEMPTS = 2            # 重跑重试次数
SLEEP_BETWEEN = 5             # 重试间隔秒

CST = timezone(timedelta(hours=8))


def _log(msg):
    ts = datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S")
    line = f"{ts} {msg}"
    print(line)
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _load_pool_update_time():
    try:
        with open(POOL_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d.get("update_time") or d.get("generated_at") or d.get("date")
    except Exception as e:
        _log(f"⚠️ 读取 candidate_pool.json 失败: {e}")
        return None


def _is_trading_day():
    try:
        sys.path.insert(0, WORKSPACE)
        from is_trading_day import is_trading_day as _itd
        return _itd(datetime.now(CST).date())
    except Exception:
        # 模块缺失时保守判断：周一到周五视为交易日
        return datetime.now(CST).weekday() < 5


def _is_trading_hours():
    """交易时段：09:30 - 15:00（粗略判断，包含午休）"""
    now = datetime.now(CST)
    hm = now.hour * 100 + now.minute
    return 930 <= hm <= 1500


def _age_minutes(update_time_str):
    try:
        dt = datetime.strptime(update_time_str[:19], "%Y-%m-%d %H:%M:%S")
        dt = dt.replace(tzinfo=CST)
        return (datetime.now(CST) - dt).total_seconds() / 60.0
    except Exception as e:
        _log(f"⚠️ 解析 update_time 失败 ({update_time_str}): {e}")
        return None


def _run(cmd_list, timeout=300, label=""):
    """运行子命令，返回 (ok, stdout, stderr)"""
    if label:
        _log(f"▶ 执行: {label} ({' '.join(cmd_list)})")
    try:
        proc = subprocess.run(
            [sys.executable] + cmd_list,
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        ok = proc.returncode == 0
        return ok, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as e:
        return False, e.stdout or "", e.stderr or ""
    except Exception as e:
        return False, "", str(e)


def _sync_to_main(files):
    """把指定文件推到 origin/main，再跑 deploy。

    关键：deploy_now.py 在某些冲突场景下会 `git reset --hard origin/main`
    重建 dist。若不先把刚重建的候选池（data/ 与 dist/ 两份）都推到 main，
    reset 会把它回退成远端陈旧版（dist-reset 覆盖陷阱，07-22 11:24 实发），
    导致线上部署的是陈旧数据。

    files: 相对 WORKSPACE 的路径列表。
    """
    if not files:
        return True
    try:
        env = dict(os.environ)
        env["GIT_SSH_COMMAND"] = "ssh -o ConnectTimeout=15"
        # 仅暂存指定文件，避免误带其它未提交改动
        subprocess.run(
            ["git", "add", "--"] + files, cwd=WORKSPACE, env=env,
            capture_output=True, timeout=60,
        )
        # 无差异则已同步，直接返回
        staged = subprocess.run(
            ["git", "diff", "--cached", "--quiet", "--"] + files,
            cwd=WORKSPACE, env=env, capture_output=True, timeout=60,
        )
        if staged.returncode == 0:
            return True
        subprocess.run(
            ["git", "commit", "-q", "-m", "auto: refresh candidate_pool (watchdog)"],
            cwd=WORKSPACE, env=env, check=True, capture_output=True, timeout=120,
        )
        for _ in range(2):
            p = subprocess.run(
                ["git", "push", "origin", "main"],
                cwd=WORKSPACE, env=env, capture_output=True, timeout=180,
            )
            if p.returncode == 0:
                _log(f"✓ 候选池已推送到 main ({len(files)} 个文件)")
                return True
            # non-fast-forward -> 用 safe_pull 安全拉取后重试（绝不用裸 git pull）
            from git_safe_sync import safe_pull
            _log("↻ 远端领先，执行 safe_pull 后重试推送")
            if not safe_pull(cwd=WORKSPACE):
                _log("↻ safe_pull 失败，重试推送仍可能失败")
        _log("⚠️ 候选池推送 main 失败，跳过部署以避免陈旧数据上线")
        return False
    except Exception as e:
        _log(f"⚠️ 同步候选池到 main 异常: {e}")
        return False


def _sync_candidate_pool_to_main():
    """兼容旧调用：仅同步 data/candidate_pool.json。"""
    return _sync_to_main([POOL_FILE])


def _rebuild_and_deploy():
    """重建候选池 → 推到 main → 前端构建 → 强制部署。"""
    # 1) 重建候选池
    #    超时 600s：完整构建实测 ~6min（mootdx 全量 A股 + 新浪港股 99 页），
    #    300s 在慢网络下必被误杀（2026-07-31 盘中两次失败即此因）。
    ok, out, err = _run(["build_candidate_pool.py"], 600, "重建候选池")
    if not ok:
        tail = (err or out).strip().splitlines()
        tail = " | ".join(tail[-3:]) if tail else "unknown"
        _log(f"✗ 重建候选池 失败: {tail}")
        return False
    _log("✓ 重建候选池 完成")
    # 1.5) 关键：先把新鲜候选池(data/)推到 main，否则 deploy 的 reset --hard 会回退为陈旧版
    if not _sync_candidate_pool_to_main():
        return False
    # 2) 前端构建（update_data_v2 会把新鲜 data/ 同步进 dist/data/，并重建 index*.html）
    ok, out, err = _run(["update_data_v2.py"], 300, "前端构建")
    if not ok:
        tail = (err or out).strip().splitlines()
        tail = " | ".join(tail[-3:]) if tail else "unknown"
        _log(f"✗ 前端构建 失败: {tail}")
        return False
    _log("✓ 前端构建 完成")
    # 2.5) 根治 dist-reset 陷阱（07-22 11:24 实发）：前端构建后，dist/data/candidate_pool.json
    #      与 dist/index*.html 已是新鲜版；必须一并推到 main，否则 deploy 的 reset --hard
    #      会把 dist 整体回退成 origin/main 的陈旧提交 → 线上部署陈旧候选池。
    dist_pool = os.path.join(WORKSPACE, "dist", "data", "candidate_pool.json")
    dist_files = [dist_pool]
    for idx in ("index.html", "index_master.html"):
        p = os.path.join(WORKSPACE, "dist", idx)
        if os.path.exists(p):
            dist_files.append(p)
    if not _sync_to_main(dist_files):
        return False
    # 3) 强制部署
    ok, out, err = _run(["deploy_now.py", "--force"], 180, "强制部署")
    if not ok:
        tail = (err or out).strip().splitlines()
        tail = " | ".join(tail[-3:]) if tail else "unknown"
        _log(f"✗ 强制部署 失败: {tail}")
        return False
    _log("✓ 强制部署 完成")
    return True


def main():
    if not _is_trading_day():
        _log("🛌 非交易日，看门狗跳过")
        return 0

    if not _is_trading_hours():
        _log("🛌 非交易时段，看门狗跳过")
        return 0

    ut = _load_pool_update_time()
    if not ut:
        _log("⚠️ candidate_pool 无 update_time，尝试重建")
        age = float("inf")
    else:
        age = _age_minutes(ut)
        if age is None:
            _log(f"⚠️ 无法计算候选池年龄，尝试重建 (update_time={ut})")
            age = float("inf")
        else:
            _log(f"ℹ️ candidate_pool 年龄 {age:.0f} 分钟 (update_time={ut})")

    if age <= MAX_AGE_MINUTES:
        _log(f"✓ 候选池新鲜（≤{MAX_AGE_MINUTES} 分钟），无需重建")
        return 0

    _log(f"🚨 候选池陈旧（{age:.0f} 分钟 > {MAX_AGE_MINUTES} 分钟），启动重建")

    for attempt in range(1, RETRY_ATTEMPTS + 1):
        _log(f"↻ 重建尝试 {attempt}/{RETRY_ATTEMPTS}")
        if _rebuild_and_deploy():
            _log("✅ 看门狗重建并部署成功")
            return 0
        if attempt < RETRY_ATTEMPTS:
            time.sleep(SLEEP_BETWEEN)

    _log("❌ 看门狗重建失败，候选池仍陈旧，已阻止陈旧数据部署")
    return 1


if __name__ == "__main__":
    sys.exit(main())
