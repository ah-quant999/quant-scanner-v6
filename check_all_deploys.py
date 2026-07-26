#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
check_all_deploys.py — 全任务部署探测守卫（通用版本）

用途：
    检测当前机器上所有预期定时任务是否「真的跑完并产生了预期产出」。
    支持三种信号源：
      1) _heartbeat.log（本地任务自写的 DONE 留痕）
      2) data/_heartbeat.log（云端 workflow 写入并 git commit 的留痕）
      3) gh-pages live site（交叉校验云端部署任务）

    被周期化自动化调用（小九-全任务心跳守卫，每30分钟）。
    退出码：0 = 所有到期任务均正常 / 1 = 有遗漏任务需人工介入。

主机自动识别：
    - CLOUD_RUNNER=true → host=cloud
    - .machine_role 文件（ALIMI / XIAOJIU）
    - 默认 xiaojiu

配置：
    TASKS 字典定义了所有任务的预期信息。修改脚本时同步更新此表。

依赖：
    Python 3.x 标准库（无第三方依赖）。在 repo-temp 目录下运行。
"""

import os
import re
import sys
import datetime
import subprocess

# ─── 路径 ───
REPO = os.path.dirname(os.path.abspath(__file__))
HEARTBEAT_LOCAL = os.path.join(REPO, "_heartbeat.log")           # 本地写入
HEARTBEAT_CLOUD = os.path.join(REPO, "data", "_heartbeat.log")   # 云端写入后 git push

TODAY = datetime.date.today().strftime("%Y-%m-%d")
NOW = datetime.datetime.now()
DOW = NOW.weekday()  # 0=周一 ... 6=周日
HOUR = NOW.hour
MINUTE = NOW.minute


# ─── 主机识别 ───
def detect_host():
    """自动判断运行主机：cloud(云端Runner) / xiaojiu / alimi"""
    if os.environ.get("CLOUD_RUNNER", "").lower() == "true":
        return "cloud"
    mrole = os.path.join(REPO, ".machine_role")
    if os.path.exists(mrole):
        with open(mrole) as f:
            role = f.read().strip().upper()
            if role in ("XIAOJIU", "ALIMI"):
                return role.lower()
    hn = os.uname().nodename.lower() if hasattr(os, 'uname') else ""
    if "workbuddy" in hn:
        return "xiaojiu"
    return "xiaojiu"  # 默认


HOST = detect_host()


# ─── 任务定义表 ───
# 每项：task_name（心跳中匹配的关键词）, expected_hosts, schedule_desc, 
#       due_window（(start_h, start_m, end_h, end_m)=该任务应在此窗口内完成且检测时已到期）
#       check_weekday（True=仅工作日检查，False=全部检查）
TASKS = [
    # ─── 盘前/早间 ───
    {"name": "pre_market_deploy",      "expected": ["xiaojiu"],           "desc": "09:20 盘前更新部署",                     "due": (9, 25, 10,  5), "weekday": True},
    {"name": "盘前全盘扫描",           "expected": ["xiaojiu"],           "desc": "09:14 盘前全盘扫描",                     "due": (9, 18, 10,  0), "weekday": True},
    {"name": "pre_market_deploy_self_heal","expected": ["xiaojiu"],       "desc": "10:05 盘前失败自愈兜底",                 "due": (10, 8, 11, 0),  "weekday": True},
    {"name": "08_交接检查",            "expected": ["xiaojiu"],           "desc": "08:00 自动交接检查",                     "due": (8, 5,  9,  0),  "weekday": True},
    {"name": "紧急交接读取",           "expected": ["xiaojiu"],           "desc": "每2h 紧急交接读取(阿狸咪)",              "due": None, "weekday": True},  # 周期性不设到期窗口

    # ─── 盘中部署（本机） ───
    {"name": "intraday_09_30",         "expected": ["xiaojiu"],           "desc": "09:30 盘中刷新部署",                     "due": (9, 33, 10,  0), "weekday": True},
    {"name": "intraday_10_31",         "expected": ["xiaojiu"],           "desc": "10:31 盘中刷新部署",                     "due": (10, 34, 11, 0), "weekday": True},
    {"name": "intraday_11_46",         "expected": ["xiaojiu"],           "desc": "11:46 盘中刷新部署",                     "due": (11, 49, 12, 30), "weekday": True},
    {"name": "intraday_13_31",         "expected": ["xiaojiu"],           "desc": "13:31 盘中刷新部署",                     "due": (13, 34, 14, 0), "weekday": True},
    {"name": "intraday_14_31",         "expected": ["xiaojiu"],           "desc": "14:31 盘中刷新部署",                     "due": (14, 34, 15, 0), "weekday": True},
    {"name": "post_close_16_31",       "expected": ["xiaojiu"],           "desc": "16:31 盘后刷新部署",                     "due": (16, 34, 17, 0), "weekday": True},
    {"name": "close_19_30_deploy",     "expected": ["xiaojiu"],           "desc": "19:30 收盘最终部署",                     "due": (19, 33, 20, 30), "weekday": True},

    # ─── 盘中数据抓取（本机） ───
    {"name": "本机中国源数据",         "expected": ["xiaojiu"],           "desc": "09-15时:40 中国源抓取(推main)",          "due": None, "weekday": True},  # 每小时一次
    {"name": "neodata_17_31",          "expected": ["xiaojiu"],           "desc": "17:31 neodata 数据抓取",                 "due": (17, 34, 18, 30), "weekday": True},
    {"name": "neodata_token_17_25",    "expected": ["xiaojiu"],           "desc": "17:25 刷新neodata token",                "due": (17, 28, 18, 0), "weekday": True},

    # ─── 看门狗/监控（本机） ───
    {"name": "candidate_pool_watchdog","expected": ["xiaojiu"],           "desc": "每整/半点 candidate_pool看门狗",         "due": None, "weekday": True},  # 周期性
    {"name": "全时段健康监控",         "expected": ["xiaojiu"],           "desc": "每30分(09:00-16:30) 云端健康监控",      "due": None, "weekday": True},  # 周期性
    {"name": "网络健康检查",           "expected": ["xiaojiu"],           "desc": "09-15时:15/:45 网络健康检查",            "due": None, "weekday": True},  # 周期性
    {"name": "心跳监控督促",           "expected": ["xiaojiu"],           "desc": "每整点 心跳监控-督促云端部署",           "due": None, "weekday": True},  # 周期性
    {"name": "C盘空间预警",            "expected": ["xiaojiu"],           "desc": "每日09:00 C盘空间预警",                  "due": (9, 3, 12, 0),  "weekday": False},  # 每日

    # ─── 云端部署 ───
    {"name": "cloud_scanner",          "expected": ["cloud"],             "desc": "18:31 云端收盘扫描+部署",                "due": (18, 34, 19, 30), "weekday": True},
    {"name": "cloud_post_close",       "expected": ["cloud"],             "desc": "15:30/16:15/16:30 云端收盘分阶段",       "due": (15, 33, 17, 0),  "weekday": True},
    {"name": "cloud_intraday",         "expected": ["cloud"],             "desc": "09:30-14:31 云端盘中任务(多档)",        "due": (9, 33, 15, 0),   "weekday": True},
    {"name": "cloud_data_fetch_17_31", "expected": ["cloud"],             "desc": "17:31 云端收盘数据抓取+部署",            "due": (17, 34, 18, 30), "weekday": True},
    {"name": "cloud_weekly",           "expected": ["cloud"],             "desc": "周期任务(周一行业图/周五名称/周六T+1)",   "due": None, "weekday": False},  # 按时按日不设到期
]


# ─── 心跳行解析 ───
HEARTBEAT_LINE_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \| (\S+) \| (\S+) \| (\S+)"
)


def parse_heartbeat_file(filepath):
    """解析心跳文件，返回列表 [(date, host, task, status, rest), ...]"""
    entries = []
    if not os.path.exists(filepath):
        return entries
    with open(filepath, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#"):
                continue
            m = HEARTBEAT_LINE_RE.match(line)
            if not m:
                continue
            date_str = line[:19]  # YYYY-MM-DD HH:MM:SS
            host = m.group(1)
            task = m.group(2)
            status = m.group(3)
            # extra = line.split("|", 3)[-1] if "|" in line else ""
            rest = line[len(m.group(0)):].strip(" |")
            entries.append((date_str, host, task, status, rest))
    return entries


def get_today_done(entries):
    """从解析结果中提取今天的所有 DONE 条目"""
    done_set = set()  # (host, task)
    for date_str, host, task, status, _ in entries:
        if date_str.startswith(TODAY) and status.upper() == "DONE":
            done_set.add((host, task))
    return done_set


def get_today_latest(entries):
    """从解析结果中提取今天的各任务最新行"""
    latest = {}
    for date_str, host, task, status, _ in entries:
        if date_str.startswith(TODAY):
            key = (host, task)
            if key not in latest or date_str > latest[key][0]:
                latest[key] = (date_str, status)
    return latest


def is_due(task_due):
    """判断当前时间是否已过任务的到期窗口"""
    if task_due is None:
        return False  # 周期性任务不设到期闸门
    sh, sm, eh, em = task_due
    due_start = sh * 60 + sm
    due_end = eh * 60 + em
    now_min = HOUR * 60 + MINUTE
    # 仅当当前时间 >= 窗口起始时，判定任务到期、应已执行
    return now_min >= due_start


def is_weekday():
    """周一~五"""
    return DOW < 5


def check_task(task, today_done, today_latest):
    """检查单个任务，返回 (name, status, detail)"""
    name = task["name"]
    due = task["due"]
    weekday_only = task["weekday"]

    if weekday_only and not is_weekday():
        return (name, "SKIP", "周末不检查")

    # 周期性任务（due=None）：无到期闸门，已有 DONE 则报已执行，否则报 WAIT（不报 MISSING）
    if due is None:
        for host in task.get("expected", []):
            if (host, name) in today_done:
                return (name, "OK", f"✅ {task['desc']}（今日已执行）")
        # 跨机检查
        for (h, t), (ts, st) in today_latest.items():
            if t == name and st == "DONE":
                return (name, "OK", f"✅ {task['desc']}（{h}已执行）")
        return (name, "WAIT", f"⏳ {task['desc']}（周期性任务，无到期闸门，后续执行将自动报告）")

    due_now = is_due(due)
    if not due_now:
        # 还没到时间，跳过
        return (name, "OK", "⏳ " + task["desc"] + "（未到期）")

    # 检查本机是否做过
    local_done = False
    for host in task.get("expected", []):
        if (host, name) in today_done:
            local_done = True
            break

    # 检查其他主机是否做过
    cross_done = False
    for (h, t), (ts, st) in today_latest.items():
        if t == name and st == "DONE":
            cross_done = True
            break

    done = local_done or cross_done

    if done:
        detail = f"✅ {task['desc']}"
        return (name, "OK", detail)
    else:
        detail = f"❌ {task['desc']} 遗漏!"
        return (name, "MISSING", detail)


def fetch_remote_heartbeat():
    """从远程 main 分支读取最新的 _heartbeat.log（含云端写入的留痕）"""
    try:
        result = subprocess.run(
            ["git", "fetch", "origin", "main"],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            return None, "git fetch failed"
        result = subprocess.run(
            ["git", "show", "origin/main:_heartbeat.log"],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=15
        )
        if result.returncode != 0:
            return None, "origin/main has no _heartbeat.log yet"
        # 写入临时解析
        tmp_path = os.path.join(REPO, "_heartbeat_remote.tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(result.stdout)
        entries = parse_heartbeat_file(tmp_path)
        os.remove(tmp_path)
        return entries, None
    except Exception as e:
        return None, str(e)


def fetch_cloud_heartbeat():
    """从 origin/main 读取 data/_heartbeat.log（云端 workflow 写入）"""
    try:
        result = subprocess.run(
            ["git", "show", "origin/main:data/_heartbeat.log"],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=15
        )
        if result.returncode != 0:
            return None, "origin/main has no data/_heartbeat.log yet"
        tmp_path = os.path.join(REPO, "_heartbeat_cloud.tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(result.stdout)
        entries = parse_heartbeat_file(tmp_path)
        os.remove(tmp_path)
        return entries, None
    except Exception as e:
        return None, str(e)


def check_live_site():
    """检查线上站点构建戳是否为今日"""
    try:
        import urllib.request
        req = urllib.request.urlopen(
            "https://ah-quant999.github.io/quant-scanner-v6/", timeout=15
        )
        html = req.read().decode("utf-8", errors="replace")
        # 找构建戳: 九宝量化 v6.0 (YYYYMMDDHHMMSS) 或 build_stamp
        m = re.search(r"(\d{14})", html[-2000:])  # 一般在页脚
        m2 = re.search(r"九宝量化.*?(\d{14})", html)
        stamp = m2.group(1) if m2 else (m.group(1) if m else None)
        if stamp:
            stamp_date = stamp[:8]  # YYYYMMDD
            today_ymd = datetime.date.today().strftime("%Y%m%d")
            if stamp_date == today_ymd:
                return True, f"线上已更新: {stamp}"
            else:
                return False, f"线上构建戳为 {stamp}({stamp_date})，非今日({today_ymd})"
        return False, "无法解析构建戳"
    except Exception as e:
        return False, f"站点不可达: {e}"


def main():
    print(f"╔═══ 全任务部署探测 [{TODAY} {HOUR:02d}:{MINUTE:02d}] ═══╗")
    print(f"  运行主机: {HOST}")
    print(f"  工作日: {'是' if is_weekday() else '否(跳过工作日专属任务)'}")

    # 0. 防御层：调用 audit_automations.py 自动修复错配的 model_id 等（2026-07-21 教训）
    audit_script = os.path.join(REPO, "audit_automations.py")
    if os.path.exists(audit_script):
        try:
            print(f"\n🛡️  防御层 audit_automations.py...")
            r = subprocess.run([sys.executable, audit_script],
                               capture_output=True, text=True, timeout=60)
            if r.returncode == 0:
                print(f"  ✅ audit OK")
            elif r.returncode == 1:
                print(f"  ⚠️ audit 发现错误（已自动修复部分）：{r.stdout.splitlines()[-1] if r.stdout else ''}")
            else:
                print(f"  ⚠️ audit 异常退出: {r.returncode}")
            if r.stderr:
                print(f"  stderr: {r.stderr[:200]}")
        except Exception as e:
            print(f"  ⚠️ audit 调用失败（不影响后续）: {e}")

    # 1. 收集所有心跳信号
    local_entries = parse_heartbeat_file(HEARTBEAT_LOCAL)
    cloud_entries = parse_heartbeat_file(HEARTBEAT_CLOUD)

    # 2. 从远程拉最新心跳（含其他机/云端刚提交的）
    print("\n📡 同步远程心跳...")
    remote_entries, err = fetch_remote_heartbeat()
    if err:
        print(f"  ⚠️ 远程 _heartbeat.log: {err}")

    cloud_remote_entries, err2 = fetch_cloud_heartbeat()
    if err2:
        print(f"  ⚠️ 远程 data/_heartbeat.log: {err2}")

    # 合并所有心跳
    all_entries = local_entries + cloud_entries
    if remote_entries:
        all_entries += remote_entries
    if cloud_remote_entries:
        all_entries += cloud_remote_entries

    today_done = get_today_done(all_entries)
    today_latest = get_today_latest(all_entries)

    print(f"\n📋 今日已 DONE 条目: {len(today_done)}")
    for (h, t) in sorted(today_done):
        print(f"  ✅ {h} | {t}")
    if not today_done:
        print("  ⚠️ 无 — 今天还没有任何任务完成留痕")

    # 3. 逐任务检查
    print(f"\n{'─'*50}")
    results = []
    missing_count = 0
    ok_count = 0
    skip_count = 0
    wait_count = 0
    for task in TASKS:
        name, status, detail = check_task(task, today_done, today_latest)
        results.append((name, status, detail))
        if status == "MISSING":
            missing_count += 1
        elif status == "OK":
            ok_count += 1
        elif status == "SKIP":
            skip_count += 1
        elif status == "WAIT":
            wait_count += 1
        print(f"  [{status}] {detail}")

    # 4. 线上站点验证
    print(f"\n{'─'*50}")
    print(f"📡 线上站点交叉验证...")
    site_ok, site_detail = check_live_site()
    if site_ok:
        print(f"  ✅ {site_detail}")
    else:
        print(f"  ⚠️ {site_detail}")

    # 5. 汇总
    print(f"\n{'═'*50}")
    print(f"  汇总: ✅ {ok_count} / ❌ {missing_count} / ⏳ {wait_count} / ⏭️ {skip_count}")
    if missing_count > 0:
        print(f"  ❗ 有 {missing_count} 个到期任务遗漏，需人工介入")
        sys.exit(1)
    else:
        print(f"  🟢 所有到期任务均已正常执行")
        sys.exit(0)


if __name__ == "__main__":
    main()

