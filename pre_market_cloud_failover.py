#!/usr/bin/env python3
"""
pre_market_cloud_failover.py
全时段云端健康监控 + 兜底。
原为"盘前 09:20 兜底检查"（已废弃），现改为全时段轮询：
- 每 30-60 分钟由 automation 调用
- 检查云端最近一次成功部署距今是否超过 90 分钟（交易时段内）
- 超时则触发本机补跑 + 强制部署

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
GRACE_PERIOD_MIN = 45        # 宽限期：距上次部署在 45 分钟内 → OK
FAILOVER_THRESHOLD_MIN = 90  # 兜底阈值：距上次部署超过 90 分钟 → 触发兜底
MORNING_GRACE_HOUR = 10      # 早于 10:00 且今天无部署 → 给云端 09:20 留窗口


def run(cmd, cwd=ROOT, timeout=300):
    """运行命令，返回 (exit_code, stdout, stderr)"""
    print(f"[RUN] {cmd}")
    try:
        p = subprocess.run(
            cmd, cwd=cwd, shell=True, capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=timeout,
        )
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as e:
        return -1, e.stdout or "", e.stderr or ""


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


def main():
    now = now_dt()

    # ── 判断是否进入交易时段 ──
    is_trading_day = check_trading_day()
    in_trading_hours = 9 <= now.hour <= 15
    is_morning = now.hour < MORNING_GRACE_HOUR

    # 非交易日且非交易时段 → 跳过
    if not is_trading_day and not in_trading_hours:
        write_log("SKIPPED", "非交易日且非交易时段", {"trading_day": False})
        return 0

    # ── 获取云端最近部署 ──
    build_stamp, build_err = fetch_remote_build_stamp()
    now_ts = now.strftime("%Y%m%d%H%M%S")
    today_prefix = now.strftime("%Y%m%d")

    details = {
        "build_stamp": build_stamp,
        "build_stamp_error": build_err,
        "check_time": now_ts,
        "trading_day": is_trading_day,
    }

    cloud_ok = False
    cloud_reason = ""
    elapsed_min = None

    if build_stamp:
        build_dt = parse_timestamp(build_stamp)
        if build_dt:
            elapsed_min = (now - build_dt).total_seconds() / 60.0
            details["build_dt"] = build_dt.strftime("%Y-%m-%d %H:%M:%S")
            details["elapsed_min"] = round(elapsed_min, 1)

            is_today = build_stamp.startswith(today_prefix)

            if is_today:
                # ── 今天有云端部署 ──
                if elapsed_min < GRACE_PERIOD_MIN:
                    cloud_ok = True
                    cloud_reason = (f"云端 {elapsed_min:.0f} 分钟前有部署"
                                    f"({build_stamp})，在宽限期内，跳过")
                elif elapsed_min < FAILOVER_THRESHOLD_MIN:
                    cloud_ok = True
                    cloud_reason = (f"云端 {elapsed_min:.0f} 分钟前有部署"
                                    f"({build_stamp})，距触发兜底还有"
                                    f"{FAILOVER_THRESHOLD_MIN - elapsed_min:.0f}分钟")
                else:
                    cloud_ok = False
                    cloud_reason = (f"云端最近部署距今 {elapsed_min:.0f} 分钟"
                                    f"({build_stamp})，超过阈值"
                                    f" {FAILOVER_THRESHOLD_MIN} 分钟，触发兜底")
            else:
                # ── 最后一次部署不是今天 ──
                if is_morning and is_trading_day:
                    # 早于 10:00，给云端 09:20 留窗口
                    cloud_ok = True
                    cloud_reason = (f"云端最近部署 {build_stamp}（非今天），"
                                    f"早于 {MORNING_GRACE_HOUR}:00，等待云端")
                else:
                    cloud_ok = False
                    cloud_reason = (f"云端最近部署 {build_stamp}（非今天），"
                                    f"距现在 {elapsed_min:.0f} 分钟，且已过"
                                    f" {MORNING_GRACE_HOUR}:00，触发兜底")
        else:
            cloud_reason = f"build stamp {build_stamp} 格式无法解析"
    else:
        cloud_reason = f"无法获取云端 build stamp: {build_err}"

    details["cloud_ok"] = cloud_ok
    details["reason"] = cloud_reason

    if cloud_ok:
        write_log("OK", cloud_reason, details)
        return 0

    return run_fallback(details)


if __name__ == "__main__":
    sys.exit(main())
