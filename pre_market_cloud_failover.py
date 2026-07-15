#!/usr/bin/env python3
"""
pre_market_cloud_failover.py
盘前兜底检查：主链路是 GitHub Actions 09:20 cloud_intraday。
本机 09:20 只检查云端是否已经部署了今天的数据；如果没有，才启动本机补跑。

产出：
- dist/data/.pre_market_failover.json（日志，供前端展示兜底状态）
- 失败时触发本机补跑并 deploy_now.py --force
"""

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST_DATA = os.path.join(ROOT, "dist", "data")
LOG_FILE = os.path.join(DIST_DATA, ".pre_market_failover.json")
BUILD_STAMP_PATTERN = re.compile(r"build\s*[:=]\s*(\d{14})", re.IGNORECASE)
UPDATE_TIME_PATTERN = re.compile(r'"update_time"\s*:\s*"([^"]+)"')

PY = r"C:\Users\Administrator\AppData\Local\Microsoft\WindowsApps\python.exe"


def run(cmd, cwd=ROOT, timeout=300):
    """运行命令，返回 (exit_code, stdout, stderr)"""
    print(f"[RUN] {cmd}")
    try:
        p = subprocess.run(
            cmd,
            cwd=cwd,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as e:
        return -1, e.stdout or "", e.stderr or ""


def today_str():
    return datetime.now().strftime("%Y-%m-%d")


def today_deadline():
    """今天 09:20 之后的数据才算云端成功。"""
    now = datetime.now()
    return now.replace(hour=9, minute=20, second=0, microsecond=0)


def parse_timestamp(ts: str):
    """尝试解析各种时间字符串。"""
    if not ts:
        return None
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%Y%m%d%H%M%S",
    ):
        try:
            return datetime.strptime(ts[: len(fmt)], fmt)
        except ValueError:
            continue
    return None


def fetch_remote_build_stamp():
    """从 origin/gh-pages 的 index.html 里取 build stamp。"""
    ec, out, err = run("git fetch origin gh-pages")
    if ec != 0:
        return None, f"git fetch gh-pages failed: {err[:200]}"
    ec, out, err = run("git show origin/gh-pages:index.html")
    if ec != 0:
        return None, f"git show origin/gh-pages:index.html failed: {err[:200]}"
    m = BUILD_STAMP_PATTERN.search(out)
    if m:
        return m.group(1), None
    # 备用：从页面里找 20xxxxxxxxxxxx 这种 14 位数字
    m2 = re.search(r"(20\d{12})", out)
    if m2:
        return m2.group(1), None
    return None, "no build stamp found in gh-pages index.html"


def fetch_remote_update_time():
    """从 origin/gh-pages 的 scan_data.json 取 update_time。"""
    ec, out, err = run("git show origin/gh-pages:dist/data/scan_data.json 2>/dev/null")
    if ec != 0:
        return None, f"scan_data.json not in gh-pages: {(err or '')[:200]}"
    try:
        d = json.loads(out)
        ut = d.get("update_time") or d.get("updated_at")
        return ut, None
    except Exception as e:
        return None, f"parse scan_data.json failed: {e}"


def check_trading_day():
    """今天是否交易日。"""
    ec, out, err = run(f"{PY} check_trading_day.py")
    if ec == 0 and "SKIP" in out.upper():
        return False
    return True


def write_log(status: str, reason: str, details: dict):
    os.makedirs(DIST_DATA, exist_ok=True)
    entry = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": status,
        "reason": reason,
        "details": details,
    }
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(entry, f, ensure_ascii=False, indent=2)
    print(json.dumps(entry, ensure_ascii=False, indent=2))


def main():
    if not check_trading_day():
        write_log("SKIPPED", "Today is not a trading day", {})
        return 0

    build_stamp, build_err = fetch_remote_build_stamp()
    update_time, ut_err = fetch_remote_update_time()

    deadline = today_deadline()
    now = datetime.now()

    cloud_ok = False
    cloud_reason = ""
    details = {
        "build_stamp": build_stamp,
        "build_stamp_error": build_err,
        "update_time": update_time,
        "update_time_error": ut_err,
        "deadline": deadline.strftime("%Y-%m-%d %H:%M:%S"),
    }

    if build_stamp:
        try:
            build_dt = datetime.strptime(build_stamp, "%Y%m%d%H%M%S")
            if build_dt >= deadline:
                cloud_ok = True
                cloud_reason = f"云端 build stamp {build_stamp} 在 09:20 之后，兜底无需动作"
            else:
                cloud_reason = f"云端 build stamp {build_stamp} 在 09:20 之前，判定为失败"
            details["build_dt"] = build_dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            cloud_reason = f"build stamp {build_stamp} 格式无法解析"

    if not cloud_ok and update_time:
        ut_dt = parse_timestamp(update_time)
        if ut_dt and ut_dt >= deadline:
            cloud_ok = True
            cloud_reason = f"云端 scan_data update_time {update_time} 在 09:20 之后，兜底无需动作"
        elif ut_dt:
            cloud_reason = f"云端 scan_data update_time {update_time} 在 09:20 之前，判定为失败"
        else:
            cloud_reason = f"云端 scan_data update_time {update_time} 无法解析"

    if not cloud_ok and not build_stamp and not update_time:
        cloud_reason = "无法获取云端 build stamp 和 update_time，判定为失败"

    details["cloud_ok"] = cloud_ok
    details["reason"] = cloud_reason

    if cloud_ok:
        write_log("OK", cloud_reason, details)
        return 0

    # 兜底补跑
    print("\n=== 云端失败，启动本机盘前补跑 ===")
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

    fallback_details = {"steps": []}
    for cmd, name, timeout in steps:
        ec, out, err = run(cmd, timeout=timeout)
        fallback_details["steps"].append(
            {
                "name": name,
                "cmd": cmd,
                "exit": ec,
                "tail": (out + err)[-500:],
            }
        )
        if ec != 0:
            write_log(
                "FAILED",
                f"兜底补跑在 [{name}] 失败，exit={ec}",
                {**details, "fallback": fallback_details},
            )
            return 1

    write_log(
        "RECOVERED",
        "云端未成功，本机已补跑并强制部署",
        {**details, "fallback": fallback_details},
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
