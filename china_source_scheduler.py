#!/usr/bin/env python3
"""
china_source_scheduler.py — 中国源确定性调度器

用途：把小九本机负责的中国源数据抓取/扫描/部署任务从 LLM 自动化手中接管，
改为由本地确定性 Python 调度器按时触发。到点就执行，不依赖模型是否"理解并执行命令"。

设计原则：
- 所有"业务动作"复用 batch_update.py 的已验证模式（pre_market / afternoon / post_close / close_p1 / close_p2 / close_deploy / backup / weekend_light）。
- 对 batch_update.py 未覆盖的 17:31 neodata / 17:35 危机雷达 / 17:40 中国源独档，单独封装为 job。
- 交易日检查内置（backup / weekend_light 除外）。
- 每个 job 写结构化心跳到 _scheduler_heartbeat.json，并追加到 _heartbeat.log。
- 单实例运行（文件锁），支持 --run-once 手动测试。

运行方式：
  前台调试：python china_source_scheduler.py
  单次测试：python china_source_scheduler.py --run-once pre_market
  后台无窗：pythonw china_source_scheduler.py

退出：Ctrl+C 或向进程发送 SIGTERM。
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path

import schedule

# ──────────────────────────────────────────────────────────
# 配置
# ──────────────────────────────────────────────────────────
WORKSPACE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(WORKSPACE, "data")
HEARTBEAT_FILE = os.path.join(WORKSPACE, "_scheduler_heartbeat.json")
HEARTBEAT_LOG = os.path.join(WORKSPACE, "_heartbeat.log")
LOCK_FILE = os.path.join(WORKSPACE, ".china_scheduler.lock")
PID_FILE = os.path.join(WORKSPACE, ".china_scheduler.pid")

# Python 解释器：batch_update.py 内部会自己找 system python 跑 fetch，
# 但调度器本身用 managed Python 3.13.12（含 schedule 库）。
PYTHON_EXE = sys.executable

# 交易日检查脚本
CHECK_TRADING_DAY = os.path.join(WORKSPACE, "check_trading_day.py")

# 调度表（工作日 = 周一~周五；假日由 check_trading_day.py 过滤）
# 每个条目：时间(HH:MM)、job名、触发函数、参数
SCHEDULE_WEEKDAY = [
    ("08:45", "pre_market",       "run_batch", {"mode": "pre_market"}),
    ("09:45", "morning_scan",     "run_batch", {"mode": "morning_scan"}),
    # ETF资金热度 T+0：交易时段约每30分钟抓取→推 main→重建→部署。
    # 避开午休，run_etf_heat() 内还有交易日与 09:35-15:10 双重守卫。
    ("09:35", "etf_heat_0935",     "run_etf_heat", {}),
    ("10:05", "etf_heat_1005",     "run_etf_heat", {}),
    ("10:35", "etf_heat_1035",     "run_etf_heat", {}),
    ("11:05", "etf_heat_1105",     "run_etf_heat", {}),
    ("11:35", "etf_heat_1135",     "run_etf_heat", {}),
    ("13:05", "etf_heat_1305",     "run_etf_heat", {}),
    ("13:35", "etf_heat_1335",     "run_etf_heat", {}),
    ("14:05", "etf_heat_1405",     "run_etf_heat", {}),
    ("14:35", "etf_heat_1435",     "run_etf_heat", {}),
    ("15:05", "etf_heat_1505",     "run_etf_heat", {}),
    ("10:30", "morning_plus",     "run_batch", {"mode": "morning_plus"}),
    ("11:45", "morning_report",   "run_batch", {"mode": "morning_report"}),
    ("13:30", "afternoon_1330",   "run_batch", {"mode": "afternoon"}),
    ("14:30", "afternoon_1430",   "run_batch", {"mode": "afternoon"}),
    ("15:20", "post_close",       "run_batch", {"mode": "post_close"}),
    ("16:30", "afternoon_1630",   "run_batch", {"mode": "afternoon"}),
    ("17:30", "close_p1",         "run_batch", {"mode": "close_p1"}),
    ("17:31", "neodata_daily",    "run_neodata", {}),
    ("17:35", "crisis_radar",     "run_crisis", {}),
    ("17:40", "china_source",     "run_china_source", {}),
    ("18:30", "close_p2",         "run_batch", {"mode": "close_p2"}),
    ("19:30", "close_deploy",     "run_batch", {"mode": "close_deploy"}),
]

SCHEDULE_DAILY = [
    ("21:00", "backup", "run_batch", {"mode": "backup"}),
]

SCHEDULE_WEEKEND = [
    ("19:30", "weekend_light", "run_batch", {"mode": "weekend_light"}),
]

# 各 job 全局超时（秒）。0 表示用 batch_update.py 内部超时。
JOB_TIMEOUT = {
    "pre_market": 3600,
    "morning_scan": 1800,
    "morning_plus": 1800,
    "morning_report": 1800,
    "afternoon": 1800,
    "post_close": 2400,
    "close_p1": 3600,
    "close_p2": 3600,
    "close_deploy": 1800,
    "backup": 1800,
    "weekend_light": 900,
    "neodata_daily": 1200,
    "crisis_radar": 600,
    "china_source": 3600,
}


# ──────────────────────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────────────────────
def _now_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _is_trading_day():
    """调用 check_trading_day.py 判断今天是否交易日。"""
    try:
        r = subprocess.run(
            [PYTHON_EXE, CHECK_TRADING_DAY],
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return "TRADE" in (r.stdout + r.stderr)
    except Exception as e:
        _log(f"交易日检查异常: {e}，fail-safe 视为交易日继续执行")
        return True


def _log(msg):
    line = f"[{_now_str()}] [china_scheduler] {msg}"
    print(line, flush=True)


def _write_heartbeat(job, status, detail=""):
    """写结构化心跳到 JSON，并追加到统一心跳日志。"""
    entry = {
        "time": _now_str(),
        "host": "xiaojiu",
        "job": job,
        "status": status,
        "detail": detail,
    }
    try:
        data = []
        if os.path.exists(HEARTBEAT_FILE):
            try:
                with open(HEARTBEAT_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = []
        if not isinstance(data, list):
            data = []
        data.append(entry)
        # 只保留最近 200 条，防止文件无限增长
        data = data[-200:]
        with open(HEARTBEAT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        _log(f"心跳 JSON 写入失败: {e}")

    try:
        with open(HEARTBEAT_LOG, "a", encoding="utf-8") as f:
            f.write(f"{_now_str()} | xiaojiu | {job} | {status} | {detail}\n")
    except Exception as e:
        _log(f"心跳日志写入失败: {e}")


def _run_subprocess(cmd, timeout, description):
    """通用子进程执行，带超时、日志、失败详情。"""
    _log(f"▶ {description}: {' '.join(cmd)}")
    start = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        elapsed = time.time() - start
        if proc.returncode == 0:
            _log(f"✓ {description} 完成 ({elapsed:.1f}s)")
            return True, ""
        else:
            tail = (proc.stderr or proc.stdout or "").strip()[-400:]
            detail = f"exit={proc.returncode} | {tail}"
            _log(f"✗ {description} 失败 ({elapsed:.1f}s): {detail}")
            return False, detail
    except subprocess.TimeoutExpired as e:
        elapsed = time.time() - start
        detail = f"TIMEOUT after {timeout}s"
        _log(f"✗ {description} 超时 ({elapsed:.1f}s): {detail}")
        return False, detail
    except Exception as e:
        elapsed = time.time() - start
        detail = f"EXCEPTION: {str(e)[:200]}"
        _log(f"✗ {description} 异常 ({elapsed:.1f}s): {detail}")
        return False, detail


# ──────────────────────────────────────────────────────────
# Job 实现
# ──────────────────────────────────────────────────────────
def run_batch(mode):
    """调用 batch_update.py 的指定模式。"""
    job_name = f"batch_{mode}"
    _write_heartbeat(job_name, "START")

    # backup / weekend_light 不检查交易日
    if mode not in ("backup", "weekend_light") and not _is_trading_day():
        _log(f"今日非交易日，跳过 {mode}")
        _write_heartbeat(job_name, "SKIP", "non-trading day")
        return

    timeout = JOB_TIMEOUT.get(mode, 1800)
    ok, detail = _run_subprocess(
        [PYTHON_EXE, "batch_update.py", mode],
        timeout=timeout,
        description=f"batch_update.py {mode}",
    )
    _write_heartbeat(job_name, "DONE" if ok else "FAILED", detail)
    return ok


def run_neodata():
    """17:31 neodata 数据抓取。前置：17:25 token 任务已由 LLM/MCP 刷新。"""
    job_name = "neodata_daily"
    _write_heartbeat(job_name, "START")
    if not _is_trading_day():
        _log("今日非交易日，跳过 neodata_daily")
        _write_heartbeat(job_name, "SKIP", "non-trading day")
        return True

    ok, detail = _run_subprocess(
        [PYTHON_EXE, "fetch_neodata_daily.py"],
        timeout=JOB_TIMEOUT.get(job_name, 1200),
        description="fetch_neodata_daily.py",
    )
    _write_heartbeat(job_name, "DONE" if ok else "FAILED", detail)
    return ok


def run_crisis():
    """17:35 危机雷达兜底：若 data/crisis_data.json 已今日更新则 SKIP。"""
    job_name = "crisis_radar"
    _write_heartbeat(job_name, "START")

    today = datetime.date.today().isoformat()
    crisis_file = os.path.join(DATA_DIR, "crisis_data.json")
    try:
        with open(crisis_file, "r", encoding="utf-8") as f:
            d = json.load(f)
        update_time = d.get("update_time", "")
        if update_time and update_time.startswith(today):
            _log(f"危机雷达数据已今日更新 ({update_time})，跳过")
            _write_heartbeat(job_name, "SKIP", f"already fresh: {update_time}")
            return True
    except Exception:
        pass

    ok, detail = _run_subprocess(
        [PYTHON_EXE, "fetch_crisis_data.py"],
        timeout=JOB_TIMEOUT.get(job_name, 600),
        description="fetch_crisis_data.py",
    )
    if not ok:
        _write_heartbeat(job_name, "FAILED", detail)
        return False

    # 验证更新成功
    try:
        with open(crisis_file, "r", encoding="utf-8") as f:
            d = json.load(f)
        update_time = d.get("update_time", "")
        if not (update_time and update_time.startswith(today)):
            _write_heartbeat(job_name, "FAILED", f"update_time still old: {update_time}")
            return False
    except Exception as e:
        _write_heartbeat(job_name, "FAILED", f"verify error: {e}")
        return False

    # 推 origin/main（让 19:30 守卫能拉到）
    push_ok, push_detail = _run_subprocess(
        [PYTHON_EXE, "-c",
         "import subprocess,os; cwd=os.getcwd(); "
         "subprocess.run(['git','add','data/crisis_data.json'],cwd=cwd); "
         "subprocess.run(['git','diff','--cached','--quiet'],cwd=cwd) or "
         "subprocess.run(['git','commit','-m','data: crisis_radar 兜底抓取 '+__import__('datetime').date.today().isoformat()],cwd=cwd); "
         "subprocess.run(['git','push','origin','main'],cwd=cwd); "
         "subprocess.run(['git','fetch','origin','main'],cwd=cwd); "
         "subprocess.run(['git','reset','--hard','origin/main'],cwd=cwd)"],
        timeout=120,
        description="push crisis_data.json to origin/main",
    )
    _write_heartbeat(job_name, "DONE" if push_ok else "FAILED", push_detail)
    return push_ok


def run_china_source():
    """17:40 中国源独档：按原 LLM 自动化步骤，依次抓取并推送/部署。"""
    job_name = "china_source_fetch"
    _write_heartbeat(job_name, "START")
    if not _is_trading_day():
        _log("今日非交易日，跳过 china_source_fetch")
        _write_heartbeat(job_name, "SKIP", "non-trading day")
        return True

    scripts = [
        "fetch_nt_data.py",
        "fetch_margin.py",
        "fetch_sh_sz_history.py",
        "fetch_etf_subscription.py",
        "fetch_up_down_stats.py",
        "fetch_north_fund.py",
        "capital_flow_summary.py",
        "fetch_stock_deviation.py",
        "fetch_sector_fund_flow.py",
        "fetch_sector_rs.py",
        "fetch_market_alerts.py",
        "fetch_concept_ranking.py",
        "fetch_cffex_holdings.py",
        "fetch_inst_trade.py",
        "fetch_sh_index_fib.py",
    ]

    failed = []
    for s in scripts:
        ok, detail = _run_subprocess(
            [PYTHON_EXE, s],
            timeout=180,
            description=f"china_source {s}",
        )
        if not ok:
            failed.append(f"{s}: {detail}")

    if len(failed) == len(scripts):
        _write_heartbeat(job_name, "FAILED", "all scripts failed")
        return False

    # 注：拉取对齐已统一到下方 commit/push 之后执行 reset --hard（safe_pull 体制），
    # 确保本轮数据先推 origin 再对齐，避免 reset 吃掉未提交数据。

    # 提交数据回 main
    commit_ok, commit_detail = _run_subprocess(
        [PYTHON_EXE, "-c",
         "import subprocess,os,datetime; cwd=os.getcwd(); "
         "subprocess.run(['git','config','user.name','xiaojiu-bot'],cwd=cwd); "
         "subprocess.run(['git','config','user.email','xiaojiu@local'],cwd=cwd); "
         "subprocess.run(['git','add','-A','data/','_heartbeat.log','.fetch_log/'],cwd=cwd); "
         "r=subprocess.run(['git','diff','--cached','--quiet'],cwd=cwd); "
         "print('PUSHED=false' if r.returncode==0 else 'PUSHED=true'); "
         "subprocess.run(['git','commit','-m','auto: 本机中国源数据 '+datetime.datetime.now().strftime('%Y-%m-%d %H:%M')],cwd=cwd); "
         "subprocess.run(['git','-c','http.version=HTTP/1.1','push','origin','main'],cwd=cwd)"],
        timeout=180,
        description="git commit/push china source data",
    )
    # 对齐远端（safe_pull 体制：先推本地数据，再 reset 拿干净基线）
    _run_subprocess(["git", "fetch", "origin", "main"], timeout=120, description="git fetch origin main")
    _run_subprocess(["git", "reset", "--hard", "origin/main"], timeout=120, description="git reset --hard origin/main")

    pushed = "PUSHED=true" in commit_detail
    if pushed:
        # 立即部署
        _run_subprocess(["git", "fetch", "origin", "gh-pages"],
                        timeout=60, description="git fetch gh-pages")
        deploy_ok, deploy_detail = _run_subprocess(
            [PYTHON_EXE, "deploy_now.py", "--force"],
            timeout=600,
            description="deploy_now.py --force",
        )
        # 还原 dist/
        _run_subprocess(["git", "checkout", "origin/main", "--", "dist/"],
                        timeout=60, description="restore dist/ from origin/main")
        _write_heartbeat(job_name, "DEPLOYED" if deploy_ok else "DEPLOY_FAILED",
                         f"failed scripts: {len(failed)} | deploy: {deploy_detail}")
        return deploy_ok
    else:
        _write_heartbeat(job_name, "DONE", f"no changes to push | failed scripts: {len(failed)}")
        return True


def run_etf_heat():
    """盘中每30分钟：抓取 ETF 资金热度（T+0 实时），弥补净申购 T+1 空窗。

    仅交易日 09:35-15:10 运行（由函数自身守卫），抓取后推送 json 并重建部署。
    """
    job_name = "etf_intraday_heat"
    try:
        now = datetime.datetime.now()
        if not _is_trading_day():
            return
        # 仅交易日 09:35-15:10 运行
        in_window = (
            (now.hour > 9 or (now.hour == 9 and now.minute >= 35))
            and (now.hour < 15 or (now.hour == 15 and now.minute <= 10))
        )
        if not in_window:
            return

        _write_heartbeat(job_name, "START")
        ok, detail = _run_subprocess(
            [PYTHON_EXE, "fetch_etf_intraday_heat.py"],
            timeout=120,
            description="etf intraday heat",
        )
        if not ok:
            _write_heartbeat(job_name, "FAILED", detail)
            return

        # 注：拉取对齐已统一到下方 commit/push 之后执行 reset --hard（safe_pull 体制）
        # 推送热度数据
        _run_subprocess(
            [PYTHON_EXE, "-c",
             "import subprocess,os,datetime; cwd=os.getcwd(); "
             "subprocess.run(['git','config','user.name','xiaojiu-bot'],cwd=cwd); "
             "subprocess.run(['git','config','user.email','xiaojiu@local'],cwd=cwd); "
             "subprocess.run(['git','add','data/etf_intraday_heat.json'],cwd=cwd); "
             "r=subprocess.run(['git','diff','--cached','--quiet'],cwd=cwd); "
             "print('PUSHED=false' if r.returncode==0 else 'PUSHED=true'); "
             "subprocess.run(['git','commit','-m','auto: ETF资金热度 '+datetime.datetime.now().strftime('%Y-%m-%d %H:%M')],cwd=cwd); "
             "subprocess.run(['git','-c','http.version=HTTP/1.1','push','origin','main'],cwd=cwd)"],
            timeout=180,
            description="git commit/push etf heat",
        )
        # 对齐远端（safe_pull 体制：先推本地数据，再 reset 拿干净基线）
        _run_subprocess(["git", "fetch", "origin", "main"], timeout=120, description="git fetch origin main")
        _run_subprocess(["git", "reset", "--hard", "origin/main"], timeout=120, description="git reset --hard origin/main")
        # 重建 dist 并部署，使网站盘中可见最新热度
        _run_subprocess([PYTHON_EXE, "update_data_v2.py"], timeout=300,
                        description="update_data_v2.py rebuild")
        _run_subprocess(["git", "fetch", "origin", "gh-pages"], timeout=60,
                        description="git fetch gh-pages")
        deploy_ok, deploy_detail = _run_subprocess(
            [PYTHON_EXE, "deploy_now.py", "--force"],
            timeout=600,
            description="deploy_now.py --force",
        )
        _run_subprocess(["git", "checkout", "origin/main", "--", "dist/"],
                        timeout=60, description="restore dist/ from origin/main")
        _write_heartbeat(job_name, "DEPLOYED" if deploy_ok else "DEPLOY_FAILED", deploy_detail)
    except Exception as e:
        _write_heartbeat(job_name, "CRASH", str(e)[:300])


# ──────────────────────────────────────────────────────────
# 调度器骨架
# ──────────────────────────────────────────────────────────
def _register_jobs():
    """按星期几注册任务。"""
    for t, name, func_name, kwargs in SCHEDULE_WEEKDAY:
        func = globals()[func_name]
        # 用闭包固定参数，避免 schedule 的 late binding 问题
        def make_job(f=func, n=name, **kw):
            def job():
                _log(f"⏰ 定时触发 {n}")
                try:
                    f(**kw)
                except Exception as e:
                    _log(f"✗ {n} 未捕获异常: {e}\n{traceback.format_exc()}")
                    _write_heartbeat(n, "CRASH", str(e)[:300])
            return job
        schedule.every().monday.at(t).do(make_job())
        schedule.every().tuesday.at(t).do(make_job())
        schedule.every().wednesday.at(t).do(make_job())
        schedule.every().thursday.at(t).do(make_job())
        schedule.every().friday.at(t).do(make_job())

    for t, name, func_name, kwargs in SCHEDULE_DAILY:
        func = globals()[func_name]
        def make_job(f=func, n=name, **kw):
            def job():
                _log(f"⏰ 定时触发 {n}")
                try:
                    f(**kw)
                except Exception as e:
                    _log(f"✗ {n} 未捕获异常: {e}\n{traceback.format_exc()}")
                    _write_heartbeat(n, "CRASH", str(e)[:300])
            return job
        schedule.every().day.at(t).do(make_job())

    for t, name, func_name, kwargs in SCHEDULE_WEEKEND:
        func = globals()[func_name]
        def make_job(f=func, n=name, **kw):
            def job():
                _log(f"⏰ 定时触发 {n}")
                try:
                    f(**kw)
                except Exception as e:
                    _log(f"✗ {n} 未捕获异常: {e}\n{traceback.format_exc()}")
                    _write_heartbeat(n, "CRASH", str(e)[:300])
            return job
        schedule.every().saturday.at(t).do(make_job())
        schedule.every().sunday.at(t).do(make_job())

    # 盘中 ETF 资金热度：每30分钟（仅交易日 09:35-15:10 内由函数自身守卫）
    schedule.every(30).minutes.do(run_etf_heat)


def _acquire_lock():
    """单实例锁（fcntl 在 Windows Git Bash 不可用，退而求其次用 pid 文件）。"""
    try:
        if os.path.exists(PID_FILE):
            with open(PID_FILE, "r", encoding="utf-8") as f:
                old_pid = f.read().strip()
            if old_pid:
                try:
                    # 检查进程是否仍在运行（Windows 用 tasklist）
                    r = subprocess.run(
                        ["tasklist", "/FI", f"PID eq {old_pid}", "/NH"],
                        capture_output=True, text=True, timeout=5
                    )
                    if old_pid in r.stdout:
                        _log(f"调度器已在运行 (PID {old_pid})，退出")
                        return False
                except Exception:
                    pass
        with open(PID_FILE, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
        return True
    except Exception as e:
        _log(f"获取单实例锁失败: {e}")
        return False


def _release_lock():
    try:
        if os.path.exists(PID_FILE):
            with open(PID_FILE, "r", encoding="utf-8") as f:
                pid = f.read().strip()
            if pid == str(os.getpid()):
                os.remove(PID_FILE)
    except Exception:
        pass


def _run_pending_loop(stop_event):
    """调度主循环。"""
    _log("调度器主循环启动")
    while not stop_event.is_set():
        try:
            schedule.run_pending()
        except Exception as e:
            _log(f"run_pending 异常: {e}")
        time.sleep(1)
    _log("调度器主循环结束")


def main():
    parser = argparse.ArgumentParser(description="中国源确定性调度器")
    parser.add_argument(
        "--run-once",
        choices=["pre_market", "morning_scan", "morning_plus", "morning_report",
                 "afternoon", "post_close", "close_p1", "close_p2", "close_deploy",
                 "backup", "weekend_light", "neodata_daily", "crisis_radar", "china_source"],
        help="单次运行指定 job，用于测试",
    )
    parser.add_argument("--dry-run", action="store_true", help="打印调度表并退出")
    args = parser.parse_args()

    if args.dry_run:
        print("=== 工作日调度 ===")
        for t, n, f, k in SCHEDULE_WEEKDAY:
            print(f"  {t}  {n}")
        print("=== 每日调度 ===")
        for t, n, f, k in SCHEDULE_DAILY:
            print(f"  {t}  {n}")
        print("=== 周末调度 ===")
        for t, n, f, k in SCHEDULE_WEEKEND:
            print(f"  {t}  {n}")
        return

    if args.run_once:
        mapping = {
            "pre_market": (run_batch, {"mode": "pre_market"}),
            "morning_scan": (run_batch, {"mode": "morning_scan"}),
            "morning_plus": (run_batch, {"mode": "morning_plus"}),
            "morning_report": (run_batch, {"mode": "morning_report"}),
            "afternoon": (run_batch, {"mode": "afternoon"}),
            "post_close": (run_batch, {"mode": "post_close"}),
            "close_p1": (run_batch, {"mode": "close_p1"}),
            "close_p2": (run_batch, {"mode": "close_p2"}),
            "close_deploy": (run_batch, {"mode": "close_deploy"}),
            "backup": (run_batch, {"mode": "backup"}),
            "weekend_light": (run_batch, {"mode": "weekend_light"}),
            "neodata_daily": (run_neodata, {}),
            "crisis_radar": (run_crisis, {}),
            "china_source": (run_china_source, {}),
        }
        func, kw = mapping[args.run_once]
        _log(f"单次运行 {args.run_once}")
        ok = func(**kw)
        sys.exit(0 if ok else 1)

    # 常驻模式
    if not _acquire_lock():
        sys.exit(2)

    try:
        _register_jobs()
        _log("=" * 60)
        _log("中国源确定性调度器已启动")
        _log(f"工作目录: {WORKSPACE}")
        _log(f"Python: {PYTHON_EXE}")
        _log("=" * 60)

        stop_event = threading.Event()
        def _on_signal(signum, frame):
            _log(f"收到信号 {signum}，准备退出...")
            stop_event.set()

        import signal
        signal.signal(signal.SIGINT, _on_signal)
        try:
            signal.signal(signal.SIGTERM, _on_signal)
        except Exception:
            pass

        _run_pending_loop(stop_event)
    finally:
        _release_lock()


if __name__ == "__main__":
    main()
