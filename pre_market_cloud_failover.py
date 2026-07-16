#!/usr/bin/env python3
"""
pre_market_cloud_failover.py
全时段云端健康监控 + 兜底。
原为"盘前 09:20 兜底检查"（已废弃），现改为全时段轮询：
- 每 30 分钟由 automation 调用（工作日 09:00~16:30）
- 核心：按 SCHEDULE_TRADING 计划时刻表判断"漏跑"——
  只有某计划部署时刻已过去 > MISS_GRACE_MIN(35min) 且云端自该时刻起
  无任何新部署，才判定真实漏跑并触发本机补跑；
  正常的长部署间隔（11:46→13:31=105min、18:31→21:00=149min）
  不会误触发（历史 bug：纯"距上次部署>75min"阈值会每次都误兜底）。

产出：
- data/.ops_status.json（运维状态更新）
- dist/data/.pre_market_failover.json（日志）
- 失败时触发本机补跑并 deploy_now.py --force
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST_DATA = os.path.join(ROOT, "dist", "data")
LOG_FILE = os.path.join(DIST_DATA, ".pre_market_failover.json")
BUILD_STAMP_PATTERN = re.compile(r"build\s*[:=]\s*(\d{14})", re.IGNORECASE)

PY = r"C:\Users\Administrator\AppData\Local\Microsoft\WindowsApps\python.exe"

# 阈值（分钟）
GRACE_PERIOD_MIN = 30        # 宽限期：距上次部署 ≤ 30 分钟 → OK
# ⚠️ 注意：云端计划部署间隔本身就有 > 75 分钟的（午间 11:46→13:31=105min、
# 晚间 18:31→21:00=149min）。纯"距上次部署>X分钟"的阈值判断会在这些正常间隔
# 误兜底。故改为"按云端计划时刻表判断漏跑"（见 SCHEDULE 与 compute_miss）。
FAILOVER_THRESHOLD_MIN = 165 # 兜底阈值（仅作非交易日/无计划表的兜底上限，>149min）
MORNING_GRACE_HOUR = 10      # 早于 10:00 且今天无部署 → 给云端 09:20 留窗口

# 云端计划部署时刻（交易日，本地时区，24h）。
# 来源：盘中 09:20/10:31/11:46/13:31/14:31；收盘 15:30/16:15/16:30；
#       抓取 17:31；扫描+部署 18:31；备份 21:00。
# 用途：精确判断"某次计划部署是否漏跑"——只有某计划时刻已过去 > MISS_GRACE_MIN
# 且云端自该时刻起没有任何新部署，才判定为真实漏跑并兜底；正常间隔不会误触发。
SCHEDULE_TRADING = [
    (9, 20), (10, 31), (11, 46), (13, 31), (14, 31),
    (15, 30), (16, 15), (16, 30), (17, 31), (18, 31), (21, 0),
]
MISS_GRACE_MIN = 35          # 某次计划部署后超过 35 分钟仍无新部署 → 判定漏跑


def run(cmd, cwd=ROOT, timeout=300, capture=True):
    """运行命令，返回 (exit_code, stdout, stderr)。

    重要：生产脚本经 WindowsApps/python.exe 桩启动后会派生真实解释器子进程
    并继承 stdout 管道；孙进程持有管道写端会导致 capture_output 的 EOF 永久
    等待（死锁，进程卡死、日志写不出）。改为临时文件重定向收集输出，
    从根本上避免管道挂起。
    """
    import tempfile
    print(f"[RUN] {cmd}")
    if not capture:
        try:
            p = subprocess.run(
                cmd, cwd=cwd, shell=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=timeout,
            )
            return p.returncode, "", ""
        except subprocess.TimeoutExpired:
            return -1, "", ""
    tf = tempfile.NamedTemporaryFile(
        mode="w", suffix=".log", delete=False,
        encoding="utf-8", errors="replace",
    )
    out_path = tf.name
    tf.close()
    try:
        full = f'{cmd} > "{out_path}" 2>&1'
        p = subprocess.run(full, cwd=cwd, shell=True, timeout=timeout)
        try:
            with open(out_path, encoding="utf-8", errors="replace") as f:
                combined = f.read()
        except Exception:
            combined = ""
        return p.returncode, combined, ""
    except subprocess.TimeoutExpired:
        return -1, "", ""
    finally:
        try:
            os.remove(out_path)
        except Exception:
            pass


def today_str():
    return datetime.now().strftime("%Y-%m-%d")


def now_dt():
    return datetime.now()


def parse_timestamp(ts: str):
    """尝试解析各种时间字符串。"""
    if not ts:
        return None
    # 14 位纯数字格式（%Y%m%d%H%M%S）优先完整匹配
    if len(ts) == 14 and ts.isdigit():
        try:
            return datetime.strptime(ts, "%Y%m%d%H%M%S")
        except ValueError:
            pass
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(ts[: len(fmt)], fmt)
        except ValueError:
            continue
    return None


def fetch_remote_build_stamp():
    """从 origin/gh-pages 的 index.html 取 build stamp。"""
    ec, out, err = run("git fetch origin gh-pages")
    if ec != 0:
        return None, f"git fetch gh-pages failed: {err[:200]}"
    ec, out, err = run("git show origin/gh-pages:index.html")
    if ec != 0:
        return None, f"git show origin/gh-pages:index.html failed: {err[:200]}"
    # 优先匹配 <meta name="build-stamp" content="20260715123456">
    m = re.search(r'<meta\s+name=["\']build-stamp["\']\s+content=["\'](\d{14})["\']', out)
    if m:
        return m.group(1), None
    # 后备：匹配 build: 20260... / build=20260...
    m2 = BUILD_STAMP_PATTERN.search(out)
    if m2:
        return m2.group(1), None
    # 最后兜底：页面里找 20xxxxxxxxxxxx 14 位数字
    m3 = re.search(r"(20\d{12})", out)
    if m3:
        return m3.group(1), None
    return None, "no build stamp found in gh-pages index.html"


def check_trading_day():
    """今天是否交易日。"""
    ec, out, err = run(f"{PY} check_trading_day.py")
    if ec == 0 and "SKIP" in out.upper():
        return False
    return True


def update_ops_status(updates):
    """运维状态合并写入 data/.ops_status.json。"""
    p = os.path.join(ROOT, "data", ".ops_status.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    cur = {}
    if os.path.exists(p):
        try:
            cur = json.load(open(p, encoding="utf-8"))
        except Exception:
            cur = {}
    cur.update(updates)
    cur["updated_at"] = now_dt().strftime("%Y-%m-%d %H:%M:%S")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(cur, f, ensure_ascii=False, indent=2)


def write_log(status: str, reason: str, details: dict):
    """写入日志并更新 ops_status。"""
    os.makedirs(DIST_DATA, exist_ok=True)
    entry = {
        "time": now_dt().strftime("%Y-%m-%d %H:%M:%S"),
        "status": status,
        "reason": reason,
        "details": details,
    }
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(entry, f, ensure_ascii=False, indent=2)
    print(json.dumps(entry, ensure_ascii=False, indent=2))
    update_ops_status({
        "cloud_deploy_time": details.get("build_stamp") or details.get("update_time", ""),
        "failover_status": status,
        "failover_time": entry["time"],
    })


def run_fallback(details: dict) -> int:
    """兜底补跑：10 步骤，失败立即返回。"""
    print("\n=== 云端超时，启动本机补跑 ===")
    steps = [
        (f"{PY} build_candidate_pool.py", "重建候选池", 180),
        (f"{PY} fetch_industry_map.py --shards 1", "行业映射", 300),
        (f"{PY} fetch_market_alerts.py", "市场异动", 120),
        (f"{PY} fetch_52w_high.py", "52周新高", 120),
        (f"{PY} fetch_sector_fund_flow.py", "板块资金流", 120),
        (f"{PY} fetch_sector_rs.py", "板块RS", 120),
        (f"{PY} fetch_analyst_ratings.py", "分析师评级", 120),
        (f"{PY} fetch_concept_ranking.py", "概念排名", 120),
        (f"{PY} update_data_v2.py --fast", "重建dist", 300),
        (f"{PY} deploy_now.py --force", "强制部署", 300),
    ]
    fb = {"steps": []}
    for cmd, name, timeout in steps:
        ec, out, err = run(cmd, timeout=timeout)
        fb["steps"].append({
            "name": name, "cmd": cmd, "exit": ec,
            "tail": (out + err)[-500:],
        })
        if ec != 0:
            write_log("FAILED", f"兜底补跑在 [{name}] 失败，exit={ec}",
                      {**details, "fallback": fb})
            return 1
    write_log("RECOVERED", "云端超时，本机已补跑并强制部署",
              {**details, "fallback": fb})
    return 0


def _planned_at(now, h, m):
    return now.replace(hour=h, minute=m, second=0, microsecond=0)

def last_planned_le_now(now, schedule):
    """返回 <= now 的最大计划部署时刻（今天），无则 None。"""
    cands = [_planned_at(now, h, m) for (h, m) in schedule
             if _planned_at(now, h, m) <= now]
    return max(cands) if cands else None

def decide_cloud(now, build_stamp, build_err, is_trading_day, in_trading_hours):
    """纯函数：判定云端是否健康（可被单测直接验证）。

    核心：按 SCHEDULE_TRADING 计划时刻表判断"漏跑"——
    只有某计划时刻已过去 > MISS_GRACE_MIN 且云端自该时刻起无任何新部署，
    才判定漏跑并兜底；正常的长部署间隔（11:46→13:31=105min、
    18:31→21:00=149min）不会误触发。

    返回 (cloud_ok: bool, cloud_reason: str, extra: dict)。
    """
    cloud_ok = False
    cloud_reason = ""
    elapsed_min = None
    build_dt = None
    extra = {}

    if build_stamp:
        build_dt = parse_timestamp(build_stamp)
        if build_dt:
            elapsed_min = (now - build_dt).total_seconds() / 60.0
            extra["build_dt"] = build_dt.strftime("%Y-%m-%d %H:%M:%S")
            extra["elapsed_min"] = round(elapsed_min, 1)

    if not build_stamp or not build_dt:
        if not is_trading_day and not in_trading_hours:
            cloud_ok = True
            cloud_reason = (f"无法获取云端 build stamp，但非交易日非交易时段，"
                            f"跳过：{build_err}")
        else:
            cloud_ok = False
            cloud_reason = f"无法获取云端 build stamp：{build_err}"
        return cloud_ok, cloud_reason, extra

    if is_trading_day:
        last_p = last_planned_le_now(now, SCHEDULE_TRADING)
        if last_p is None:
            # 今天首个计划部署（09:20）还未到 → 等待盘前，不介入
            cloud_ok = True
            cloud_reason = (f"今天首个计划部署未到（当前 {now:%H:%M}），"
                            f"云端最后部署 {build_stamp}，等待盘前部署")
        elif build_dt >= last_p:
            # 云端已在最近一次计划部署后成功部署 → 正常
            cloud_ok = True
            cloud_reason = (f"云端 {build_stamp}（{elapsed_min:.0f} 分钟前）晚于"
                            f"计划 {last_p:%H:%M}，部署正常，无漏跑")
        else:
            # 云端停留在 last_p 之前 → last_p 未成功部署
            overdue = (now - last_p).total_seconds() / 60.0
            if overdue <= MISS_GRACE_MIN:
                cloud_ok = True
                cloud_reason = (f"计划 {last_p:%H:%M} 刚过 {overdue:.0f} 分钟"
                                f"（宽限 {MISS_GRACE_MIN}），等待云端")
            else:
                cloud_ok = False
                cloud_reason = (f"计划 {last_p:%H:%M} 已过期 {overdue:.0f} 分钟"
                                f"（>宽限 {MISS_GRACE_MIN}），云端仍停留在"
                                f" {build_stamp}，判定漏跑，触发兜底")
    else:
        # 非交易日：保守地仅用阈值（监控本就只在工作日跑，极少见）
        if elapsed_min < FAILOVER_THRESHOLD_MIN:
            cloud_ok = True
            cloud_reason = (f"非交易日，云端 {elapsed_min:.0f} 分钟前有部署"
                            f"（{build_stamp}），未超阈值")
        else:
            cloud_ok = False
            cloud_reason = (f"非交易日但云端 {elapsed_min:.0f} 分钟无部署"
                            f"（{build_stamp}），超过阈值触发兜底")
    return cloud_ok, cloud_reason, extra

def main():
    now = now_dt()

    # ── 判断是否进入交易时段 ──
    is_trading_day = check_trading_day()
    in_trading_hours = 9 <= now.hour <= 15

    # 非交易日且非交易时段 → 跳过
    if not is_trading_day and not in_trading_hours:
        write_log("SKIPPED", "非交易日且非交易时段", {"trading_day": False})
        return 0

    # ── 获取云端最近部署 ──
    build_stamp, build_err = fetch_remote_build_stamp()
    now_ts = now.strftime("%Y%m%d%H%M%S")

    details = {
        "build_stamp": build_stamp,
        "build_stamp_error": build_err,
        "check_time": now_ts,
        "trading_day": is_trading_day,
    }

    cloud_ok, cloud_reason, extra = decide_cloud(
        now, build_stamp, build_err, is_trading_day, in_trading_hours)
    details.update(extra)

    details["cloud_ok"] = cloud_ok
    details["reason"] = cloud_reason

    if cloud_ok:
        write_log("OK", cloud_reason, details)
        return 0

    return run_fallback(details)


if __name__ == "__main__":
    sys.exit(main())
