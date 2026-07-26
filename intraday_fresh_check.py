#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
intraday_fresh_check.py — 盘中数据新鲜度看门狗（阿狸咪本地兜底监控 + 即时自愈）
========================================================================
云端 cloud_intraday 每交易日 09:30 / 10:31 / 11:46 / 13:31 / 14:31 五档刷新
data/scan_result.json。本脚本在每档后运行：若发现本档 scan_result 已过期
（意味着云端该档失败/超时），立即【邮件告警 + 触发云端对应档补跑部署】。

设计：
  - 发现旧数据 → 立刻触发云端 cloud_intraday.yml 的该档 workflow_dispatch
    （复用 trigger_cloud_dispatch 的 get_pat/dispatch，抓取+盘中扫描+构建+部署一体），
    站点稍后自动刷新，无需等盘后或人工介入。
  - 节流保护（防 GitHub Actions 资源浪费）：当天同档最多触发 2 次，且两次间隔 ≥45min；
    超出后交 safety-net.yml（age>2h）兜底，避免刷爆。
  - 邮件逻辑复用 check_data_freshness.send_email（同一套 SMTP 配置），同档当天只发一次。
  - --dry-run：只打印判定与 dispatch 构造，不真触发云端（用于验证）。
用法（贴入阿狸咪盘中看门狗自动化 prompt）：
    cd E:/workspace/stock-scanner && python intraday_fresh_check.py
"""
import os
import sys
import json
import datetime
import subprocess

import check_data_freshness as cf
import trigger_cloud_dispatch as tcd   # 复用其 get_pat()(取PAT) 与 dispatch()(触发云端 workflow)

BASE = os.path.dirname(os.path.abspath(__file__))
SLOTS = [(9, 30), (10, 31), (11, 46), (13, 31), (14, 31)]
CHECK_DELAY = 40   # 云端该档跑完所需的最大合理耗时（分钟），在此之前不判定

# 每档对应的云端 cloud_intraday.yml workflow_dispatch slot（cron 串，注意不带 1-5，
# 与 cloud_intraday.yml 的 if 判定一致；盘中扫描/构建/部署步骤无 slot if，必执行）。
SLOT_CRON = {
    (9, 30): "30 1 * * *",
    (10, 31): "31 2 * * *",
    (11, 46): "46 3 * * *",
    (13, 31): "31 5 * * *",
    (14, 31): "31 6 * * *",
}

# 全局 dry-run 开关（--dry-run 仅打印判定与 dispatch 构造，不真发 API）
_DRY_RUN = "--dry-run" in sys.argv


def now():
    return datetime.datetime.now()


def sync_scan_result():
    """判定前先把 origin/main 上【云端最新推送】的 scan_result.json 拉到本地。

    关键防误判：scan_result.json 由云端任务生成后 `git push origin main`，
    阿狸咪本地不会自动同步。若直接读本地旧文件，会误以为云端该档失败→误触发补跑。
    这里只精准拉取这一个文件（不碰工作树其他改动），并用 SSH 超时防挂死。
    """
    try:
        env = dict(os.environ, GIT_SSH_COMMAND="ssh -o ConnectTimeout=15 "
                   "-o ServerAliveInterval=15 -o ServerAliveCountMax=3")
        print("  🔄 同步 origin/main 的 scan_result.json（取云端权威副本）...")
        subprocess.run(["git", "fetch", "origin", "--quiet"],
                       cwd=BASE, env=env, timeout=60,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "checkout", "origin/main", "--", "data/scan_result.json"],
                       cwd=BASE, env=env, timeout=60,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("  ✅ 已同步云端最新 scan_result.json")
    except Exception as e:
        print(f"  ⚠️  同步 origin/main 失败({e})，将基于本地副本判定（可能误报，safety-net 会兜底）")


def latest_checkable_slot(dt):
    """返回 (hour, minute, slot_datetime) 或 None。
    仅交易日 09:30~15:30 窗口内、且距该档已过去 CHECK_DELAY 分钟的最后一档。"""
    if dt.weekday() >= 5:                      # 周末跳过
        return None
    if (dt.hour < 9 or (dt.hour == 9 and dt.minute < 30)
            or dt.hour > 15 or (dt.hour == 15 and dt.minute > 30)):
        return None
    candidates = []
    for (h, m) in SLOTS:
        st = dt.replace(hour=h, minute=m, second=0, microsecond=0)
        if (dt - st).total_seconds() / 60 >= CHECK_DELAY:
            candidates.append(((h, m), st))
    return candidates[-1] if candidates else None


def _load_alert_state():
    path = os.path.join(BASE, ".intraday_alert_state.json")
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_alert_state(state):
    path = os.path.join(BASE, ".intraday_alert_state.json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False)
    except Exception:
        pass


def main():
    dt = now()
    slot = latest_checkable_slot(dt)
    if not slot:
        print("  ⏭️  非盘中可检查窗口，跳过")
        return 0

    (h, m), slot_dt = slot
    slot_key = f"{h:02d}:{m:02d}"
    slot_cron = SLOT_CRON.get((h, m), "")
    today = dt.strftime("%Y-%m-%d")
    sync_scan_result()   # 先取云端权威副本，避免读本地旧文件误判
    path = os.path.join(BASE, "data", "scan_result.json")
    ts = None
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f)
            ts = d.get("scan_time") or d.get("update_time") or ""
        except Exception:
            ts = None

    if not ts:
        detail = f"盘中档 {h:02d}:{m:02d} 的 scan_result.json 无时间字段，无法判定新鲜度"
        print(f"  ⚠️  {detail}")
        alert(slot_key, today, detail, slot_cron)
        return 1

    try:
        st = datetime.datetime.strptime(ts[:19], "%Y-%m-%d %H:%M:%S")
    except Exception:
        try:
            st = datetime.datetime.strptime(ts[:16], "%Y-%m-%d %H:%M")
        except Exception:
            print(f"  ⚠️  无法解析 scan_result 时间: {ts[:30]}")
            return 1

    age_from_slot = (dt - slot_dt).total_seconds() / 60
    if st < slot_dt:
        # 数据时间戳早于本档起点 → 云端该档未成功产出（失败/超时）
        detail = (f"盘中档 {h:02d}:{m:02d} 数据未刷新（云端该档疑似失败；"
                  f"期望 >= {slot_dt:%Y-%m-%d %H:%M}，本地最新 {ts[:16]}）")
        print(f"  🔴 {detail}")
        alert(slot_key, today, detail, slot_cron)
        return 1

    print(f"  ✅ 盘中数据新鲜（档 {h:02d}:{m:02d}，本地最新 {ts[:16]}，"
          f"距该档 {age_from_slot:.0f} 分钟）")
    return 0


def trigger_cloud_redispatch(slot_key, slot_cron, today):
    """发现旧数据 → 立即触发云端 cloud_intraday.yml 该档补跑（抓取+扫描+构建+部署一体）。

    节流保护（防 GitHub Actions 资源浪费）：当天同档最多触发 2 次，且两次间隔 ≥45min；
    超出上限交 safety-net.yml（age>2h）兜底。触发失败仅告警邮件已发，不影响主流程。
    """
    state = _load_alert_state()
    dstate = state.setdefault("dispatch", {})
    rec = dstate.get(slot_key) or {}
    count = 0 if rec.get("date") != today else rec.get("count", 0)
    last_t = rec.get("last", "")
    now = datetime.datetime.now()

    if count >= 2:
        print(f"  🔕 该档今日已触发云端补跑 {count} 次达上限，跳过（交 safety-net 兜底）")
        return
    if last_t:
        try:
            lt = datetime.datetime.strptime(last_t, "%Y-%m-%d %H:%M")
            gap = (now - lt).total_seconds() / 60
            if gap < 45:
                print(f"  ⏳ 距上次云端补跑仅 {int(gap)} 分钟（<45），跳过重复 dispatch")
                return
        except Exception:
            pass

    pat = tcd.get_pat()
    if not pat:
        print("  ⚠️ 无 GitHub PAT（GH_PAT/.gh_pat/git credential 均无），无法触发云端补跑；仅邮件告警已发")
        return
    print(f"  🚀 触发云端补跑 cloud_intraday.yml slot='{slot_cron}' ...")
    ok = tcd.dispatch("cloud_intraday.yml", slot_cron, pat, _DRY_RUN)
    if ok:
        print("  ✅ 云端补跑已触发（抓取+盘中扫描+构建+部署，稍后站点自动刷新）")
        dstate[slot_key] = {
            "date": today,
            "count": count + 1,
            "last": now.strftime("%Y-%m-%d %H:%M"),
        }
        _save_alert_state(state)
    else:
        print("  ⚠️ 云端补跑触发失败（检查 PAT/网络）；仅邮件告警已发")


def alert(slot_key, today, detail, slot_cron):
    """邮件告警（同档当天一次）+ 立即触发云端该档补跑部署（独立节流）。"""
    # —— 邮件：同档当天只发一次 ——
    state = _load_alert_state()
    last = state.get(slot_key, "")
    if last.startswith(today):
        print(f"  🔕 该档今日已邮件告警过({last})，跳过重复邮件")
    else:
        print("  📧 发送盘中过期告警邮件 ...")
        try:
            ok = cf.send_email([("盘中扫描 scan_result.json", "🔴", detail)], [])
            if ok:
                print("  ✅ 告警邮件已发送")
                state[slot_key] = f"{today} {datetime.datetime.now().strftime('%H:%M')}"
                _save_alert_state(state)
            else:
                print("  ⚠️  告警邮件发送失败（检查 check_data_freshness SMTP 配置）")
        except Exception as e:
            print(f"  ⚠️  告警邮件异常: {e}")
    # —— 云端补跑：独立节流（当天同档≤2次且间隔≥45min）——
    trigger_cloud_redispatch(slot_key, slot_cron, today)


if __name__ == "__main__":
    sys.exit(main())
