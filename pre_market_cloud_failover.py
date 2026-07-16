#!/usr/bin/env python3
"""
pre_market_cloud_failover.py
全时段云端健康监控 + 兜底（事件驱动 / C 方案）。

核心思路：不再用计时器傻等"距上次部署>X分钟"，而是直接查 GitHub Actions
计划部署 run 的真实状态，彻底消除"太早（云端没跑完就误兜底）/
太晚（错过了才兜底）"的张力：
- run=in_progress/queued → 云端在跑，等（OK），不误兜底
- run=success → 校验 build-stamp 已更新（确推上云端）→ OK
- run=failure/cancelled → 若无更晚的成功部署救回 → 立即兜底
- 仅当"计划时刻后 >SCHEDULE_DELAY_GRACE_MIN 仍无任何对应 run"才判真未触发
  （GitHub schedule 有调度延迟，run 可能晚出现，不能一见无 run 就兜底）
- 无 API（token 缺失/超时）→ 降级为时刻表+build-stamp 判断（B 方案）

每 30 分钟由 automation 调用（工作日 09:00~16:30，职责窗内部署：
09:20/10:31/11:46/13:31/14:31/16:30；18:31 归阿狸咪兜底）。

产出：
- data/.ops_status.json（运维状态更新）
- dist/data/.pre_market_failover.json（日志，含 run 状态摘要，不含 token）
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

# ── 阈值（分钟）──
# 旧"距上次部署>X分钟"阈值已废弃（会在正常长间隔误兜底）。
# 现采用【事件驱动】判定（见 decide_cloud）：直接查 GitHub Actions 计划部署
# run 的状态（in_progress→等 / success→校验 / failure→兜底），彻底消除
# "太早（云端没跑完）"与"太晚（错过了）"的计时器张力。
FAILOVER_THRESHOLD_MIN = 165  # 仅非交易日/无 API 时的兜底上限（>149min 长间隔）
MORNING_GRACE_HOUR = 10       # 早于 10:00 且今天无部署 → 给云端 09:20 留窗口

# 云端【部署类】workflow id（取自 .github/workflows/*.yml 的 Actions API id）。
# 仅这些 workflow 的 run 纳入"部署成功/失败"判定；
# 纯抓取（data_fetch 17:31）、纯监控（safety-net）、备份（backup）不计入。
DEPLOY_WF_IDS = {
    313023835,  # ☁️ 盘前+盘中任务（09:20/10:31/11:46/13:31/14:31 全部部署）
    313026264,  # ☁️ 收盘全景分阶段（仅 16:30 部署）
    313020864,  # ☁️ 云端收盘扫描+部署（18:31 部署）
}
# 本机监控职责窗（工作日 09:00~16:30）内需兜底的计划部署时刻（含对应 wf）。
# 18:31 在监控窗外，归阿狸咪 19:05/19:31 兜底，不列入本脚本。
DEPLOY_MOMENTS = [
    ((9, 20), 313023835),
    ((10, 31), 313023835),
    ((11, 46), 313023835),
    ((13, 31), 313023835),
    ((14, 31), 313023835),
    ((16, 30), 313026264),
]
COMPLETION_GRACE_MIN = 40     # 计划部署后 40 分钟内视为"可能仍在跑"，不判漏跑
                            # （实测云端一次部署 ~27min，40min 留足缓冲）
SCHEDULE_DELAY_GRACE_MIN = 75 # 计划时刻后 75 分钟仍无任何对应 run → 判真未触发
                            # （GitHub schedule 有调度延迟 + 运行耗时上限）
API_TIMEOUT_SEC = 30          # GitHub API 调用超时（超时降级为时刻表判断）
MISS_GRACE_MIN = 35           # 降级模式（无 API）下，计划时刻过期 35min 判漏跑


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


# ── GitHub API（事件驱动判定用）──
GCM = r"E:/workbuddy-data/vendor/PortableGit/mingw64/bin/git-credential-manager.exe"
REPO = "ah-quant999/quant-scanner-v6"
BJ = timezone(timedelta(hours=8))  # 北京时间


def get_github_token():
    """从 git-credential-manager 取缓存的 GitHub PAT（绝不打印/落盘）。
    取不到返回 None → decide_cloud 降级为时刻表判断。"""
    try:
        out = subprocess.run([GCM, "get"], input="protocol=https\nhost=github.com\n",
                             capture_output=True, text=True, timeout=20).stdout
        for line in out.splitlines():
            if line.startswith("password="):
                return line.split("=", 1)[1]
    except Exception:
        pass
    return None


def fetch_deploy_runs(token, per_page=60):
    """查最近 schedule runs，过滤出部署类 workflow，返回 (runs, error)。
    runs 元素：{created_bj, status, conclusion, wf_id, attempt}。"""
    import urllib.request
    url = (f"https://api.github.com/repos/{REPO}/actions/runs"
           f"?per_page={per_page}&event=schedule")
    req = urllib.request.Request(url)
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    try:
        with urllib.request.urlopen(req, timeout=API_TIMEOUT_SEC) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return None, f"API 调用失败: {type(e).__name__}: {e}"
    runs = []
    for run in data.get("workflow_runs", []):
        if run.get("workflow_id") not in DEPLOY_WF_IDS:
            continue
        ct = run.get("created_at", "")
        try:
            ct_bj = datetime.fromisoformat(ct.replace("Z", "+00:00")).astimezone(BJ)
        except Exception:
            continue
        runs.append({
            "created_bj": ct_bj,
            "status": run.get("status"),
            "conclusion": run.get("conclusion"),
            "wf_id": run.get("workflow_id"),
            "attempt": run.get("run_attempt"),
        })
    return runs, None


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

def map_to_moment(dt_bj, deploy_moments):
    """找 <= dt_bj 的最近计划部署时刻（同日期）。
    返回 (dt, (h,m), wf_id) 或 None。"""
    best = None
    for (h, m), wf in deploy_moments:
        cand = dt_bj.replace(hour=h, minute=m, second=0, microsecond=0)
        if cand <= dt_bj and (best is None or cand > best[0]):
            best = (cand, (h, m), wf)
    return best


def decide_cloud(now, build_stamp, build_err, is_trading_day, in_trading_hours,
                 runs=None, api_ok=True):
    """纯函数：事件驱动判定云端是否健康（可单测）。

    核心（C 方案）：直接查 GitHub Actions 计划部署 run 的真实状态，
    彻底消除"太早（云端没跑完就误兜底）/太晚（错过了才兜底）"张力：
      - run=in_progress/queued → 云端在跑，等（OK），不误兜底
      - run=success → 校验 build-stamp 已更新（确推上云端）→ OK
      - run=failure/cancelled → 若无更晚的成功部署救回 → 立即兜底
    仅当"计划时刻后 >SCHEDULE_DELAY_GRACE_MIN 仍无任何对应 run"才判真未触发
    （GitHub schedule 有调度延迟，run 可能晚出现，不能一见无 run 就兜底）。

    无 API（token 缺失/超时）→ 降级为时刻表+build-stamp 判断（B 方案）。
    返回 (cloud_ok: bool, cloud_reason: str, extra: dict)。
    """
    extra = {}
    build_dt = parse_timestamp(build_stamp) if build_stamp else None
    if build_dt:
        extra["build_dt"] = build_dt.strftime("%Y-%m-%d %H:%M:%S")
        extra["elapsed_min"] = round((now - build_dt).total_seconds() / 60.0, 1)

    # ── 降级路径：无 API ──
    if not api_ok or runs is None:
        return _decide_by_schedule(now, build_stamp, build_dt, build_err,
                                   is_trading_day, in_trading_hours, extra)

    # 构建 计划时刻 T → 最新 run
    run_by_T = {}
    for r in runs:
        mp = map_to_moment(r["created_bj"], DEPLOY_MOMENTS)
        if not mp:
            continue
        _, t_hm, _ = mp
        if t_hm not in run_by_T or r["created_bj"] > run_by_T[t_hm]["created_bj"]:
            run_by_T[t_hm] = r

    # 找"最近一个应已完成（now - T >= COMPLETION_GRACE）的计划部署 T*"
    candidates = []
    for (h, m), _ in DEPLOY_MOMENTS:
        T = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if (now - T).total_seconds() / 60.0 >= COMPLETION_GRACE_MIN:
            candidates.append(T)
    if not candidates:
        # 所有计划部署都还在"可能运行中"（<40min），不介入，等云端
        return True, (f"最近计划部署尚未超过完成宽限 {COMPLETION_GRACE_MIN} 分钟，"
                      f"云端可能在跑，等待（build-stamp={build_stamp}）"), extra
    T_star = max(candidates)
    tstar_hm = (T_star.hour, T_star.minute)
    r = run_by_T.get(tstar_hm)

    if r is None:
        overdue = (now - T_star).total_seconds() / 60.0
        if overdue < SCHEDULE_DELAY_GRACE_MIN:
            return True, (f"计划部署 {T_star:%H:%M} 暂无对应 run（调度延迟/运行中），"
                          f"已等 {overdue:.0f} 分钟（宽限 {SCHEDULE_DELAY_GRACE_MIN}），等待"),
                          extra
        return False, (f"计划部署 {T_star:%H:%M} 已过期 {overdue:.0f} 分钟仍无任何 run，"
                       f"判定云端未触发，触发兜底"), extra

    # 有 run
    extra["last_deploy_run"] = {
        "moment": f"{T_star:%H:%M}", "status": r["status"],
        "conclusion": r["conclusion"], "attempt": r["attempt"],
    }
    if r["status"] in ("in_progress", "queued", "requested", "waiting", "pending"):
        return True, (f"计划部署 {T_star:%H:%M} 的 run 仍在进行（{r['status']}），"
                      f"云端在跑，等待"), extra
    if r["conclusion"] == "success":
        if build_dt and build_dt >= T_star:
            return True, (f"计划部署 {T_star:%H:%M} 成功（success 且 build-stamp "
                          f"{build_stamp} 已更新）"), extra
        return False, (f"计划部署 {T_star:%H:%M} 报告 success 但 build-stamp "
                       f"{build_stamp} 未更新，疑似未推上云端，触发兜底"), extra
    # failure / cancelled / timed_out / startup_failure
    later_success = False
    for (h, m), _ in DEPLOY_MOMENTS:
        if (h, m) == tstar_hm:
            continue
        T2 = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if T2 > T_star and T2 <= now:
            r2 = run_by_T.get((h, m))
            if r2 and r2["conclusion"] == "success" and (not build_dt or build_dt >= T2):
                later_success = True
                break
    if later_success:
        return True, (f"计划部署 {T_star:%H:%M} 失败，但更晚的部署已成功救回"), extra
    return False, (f"计划部署 {T_star:%H:%M} 失败（{r['conclusion']}）且无更晚成功"
                   f"部署救回，触发兜底"), extra


def _decide_by_schedule(now, build_stamp, build_dt, build_err,
                         is_trading_day, in_trading_hours, extra):
    """无 API 时的降级判定（B 方案：时刻表 + build-stamp）。"""
    if not build_stamp or not build_dt:
        if not is_trading_day and not in_trading_hours:
            return True, (f"无法获取云端 build stamp，但非交易日非交易时段，跳过："
                          f"{build_err}"), extra
        return False, f"无法获取云端 build stamp：{build_err}", extra
    if is_trading_day:
        last_p = last_planned_le_now(now, [hm for hm, _ in DEPLOY_MOMENTS])
        if last_p is None:
            return True, (f"今天首个计划部署未到（当前 {now:%H:%M}），"
                          f"云端最后部署 {build_stamp}，等待盘前部署"), extra
        if build_dt >= last_p:
            elapsed = (now - build_dt).total_seconds() / 60.0
            return True, (f"云端 {build_stamp}（{elapsed:.0f} 分钟前）晚于计划 "
                          f"{last_p:%H:%M}，部署正常，无漏跑（API 不可达，降级时刻表判断）"),
                          extra
        overdue = (now - last_p).total_seconds() / 60.0
        if overdue <= MISS_GRACE_MIN:
            return True, (f"计划 {last_p:%H:%M} 刚过 {overdue:.0f} 分钟（宽限 "
                          f"{MISS_GRACE_MIN}），等待云端（降级判断）"), extra
        return False, (f"计划 {last_p:%H:%M} 已过期 {overdue:.0f} 分钟（>宽限 "
                       f"{MISS_GRACE_MIN}），云端仍停留在 {build_stamp}，判定漏跑，触发兜底"), extra
    elapsed = (now - build_dt).total_seconds() / 60.0
    if elapsed < FAILOVER_THRESHOLD_MIN:
        return True, (f"非交易日，云端 {elapsed:.0f} 分钟前有部署（{build_stamp}），未超阈值"), extra
    return False, (f"非交易日但云端 {elapsed:.0f} 分钟无部署（{build_stamp}），超过阈值触发兜底"), extra

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

    # ── 事件驱动：查 GitHub Actions 计划部署 run 状态 ──
    api_ok = False
    runs = None
    token = get_github_token()
    if token:
        runs, api_err = fetch_deploy_runs(token)
        if runs is not None:
            api_ok = True
            details["api_runs_count"] = len(runs)
        else:
            details["api_error"] = api_err
    else:
        details["api_error"] = "无 GitHub token（GCM 未缓存），降级时刻表判断"

    cloud_ok, cloud_reason, extra = decide_cloud(
        now, build_stamp, build_err, is_trading_day, in_trading_hours,
        runs=runs, api_ok=api_ok)
    details.update(extra)
    details["api_driven"] = api_ok

    details["cloud_ok"] = cloud_ok
    details["reason"] = cloud_reason

    if cloud_ok:
        write_log("OK", cloud_reason, details)
        return 0

    return run_fallback(details)


if __name__ == "__main__":
    sys.exit(main())
