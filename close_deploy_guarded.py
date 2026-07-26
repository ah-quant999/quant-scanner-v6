#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
close_deploy_guarded.py — 阿狸咪 19:30 收盘最终部署「守卫」
====================================================
【根因】2026-07-16/17 事故：云端已部署/算出新数据，但阿狸咪用本地陈旧数据
        重新 deploy，或云端失败后无告警，导致主站显示旧数据。

【本脚本逻辑】
  1. 先查云端今天是否已成功部署（GitHub API）。
     - 已成功 → 跳过，不覆盖。
  2. 云端正在运行 → 等待完成（最多 10 分钟）。
     - 成功 → 跳过。
  3. 云端无运行或失败 → 用 PAT 触发 cloud_scanner。
     - 触发成功 → 等待完成。
  4. 最终云端仍失败/超时 → 阿狸咪本地也**不强行部署陈旧数据**。
     - 仅当本地 core data 是今日收盘后（>=18:30）新鲜产出时，才允许兜底部署。
     - 否则写入告警文件/状态，退出非零，等主人处理。

用法：
  python close_deploy_guarded.py
退出码：0=云端已到位/跳过  1=告警(不部署)  2=无 PAT
"""
import time  # 模块顶部引入，被 wait_for_run 使用
import os
import re
import sys
import json
import socket
import subprocess
import urllib.request
import argparse
from datetime import datetime, timezone, timedelta

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
SITE_URL = "https://ah-quant999.github.io/quant-scanner-v6/"
REPO = "ah-quant999/quant-scanner-v6"
CLOUD_WORKFLOW = "cloud_scanner.yml"
DATA_FETCH_WORKFLOW = "cloud_data_fetch.yml"
PAT_PATH = os.path.join(WORKSPACE, ".gh_pat")
TZ = timezone(timedelta(hours=8))
ALERT_FILE = os.path.join(WORKSPACE, "data", ".deploy_alert.json")


def log(msg):
    ts = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def get_pat():
    """优先 GH_PAT 环境变量，其次 .gh_pat 文件。"""
    pat = os.environ.get("GH_PAT", "").strip()
    if pat:
        return pat
    if os.path.exists(PAT_PATH):
        try:
            with open(PAT_PATH, encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            log(f"⚠️ 读取 .gh_pat 失败: {e}")
    return None


def github_api(method, path, pat, body=None):
    """调用 GitHub API，返回 (ok, data|err_msg)。path 不含主机部分。"""
    url = f"https://api.github.com/repos/{REPO}/{path}"
    req = urllib.request.Request(url, method=method, headers={
        "Authorization": f"Bearer {pat}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    })
    if body is not None:
        req.data = json.dumps(body).encode("utf-8")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            if data:
                return True, json.loads(data)
            return True, {}
    except urllib.error.HTTPError as e:
        try:
            err = e.read().decode("utf-8", "ignore")
        except Exception:
            err = ""
        return False, f"HTTP {e.code}: {err[:200]}"
    except Exception as e:
        return False, str(e)


def cloud_status_today(pat, workflow=CLOUD_WORKFLOW):
    """
    查询指定 workflow 北京时间今日运行状态。
    返回 (status, run_id):
      status = 'success' | 'failure' | 'in_progress' | 'queued' | 'none'
    """
    ok, data = github_api("GET", f"actions/workflows/{workflow}/runs?per_page=10", pat)
    if not ok:
        log(f"⚠️ 查询云端 run 失败: {data}")
        return "none", None

    today_bj = datetime.now(TZ).date().isoformat()
    for run in data.get("workflow_runs", []):
        created = run.get("created_at", "")
        # GitHub 返回 UTC ISO8601，需转成北京时间再判断日期
        try:
            ct_utc = datetime.fromisoformat(created.replace("Z", "+00:00"))
            ct_bj = ct_utc.astimezone(TZ)
            created_bj = ct_bj.date().isoformat()
        except Exception:
            created_bj = created[:10]
        if created_bj != today_bj:
            continue
        status = run.get("status")
        conclusion = run.get("conclusion")
        run_id = run.get("id")
        if status in ("in_progress", "queued"):
            return status, run_id
        if conclusion == "success":
            return "success", run_id
        if conclusion == "failure":
            return "failure", run_id
    return "none", None


def wait_for_run(pat, run_id, timeout=3600):
    """轮询 run 直到完成或超时。返回 'success' | 'failure' | 'timeout'。
    核心扫描 2400s + 构建部署，预留 60 分钟避免慢 run 被误判。"""
    start = datetime.now()
    while (datetime.now() - start).total_seconds() < timeout:
        ok, data = github_api("GET", f"actions/runs/{run_id}", pat)
        if not ok:
            log(f"⚠️ 轮询 run {run_id} 失败: {data}")
            return "failure"
        status = data.get("status")
        conclusion = data.get("conclusion")
        if status == "completed":
            return "success" if conclusion == "success" else "failure"
        log(f"⏳ 云端 run {run_id} 状态: {status}...")
        time.sleep(20)
    return "timeout"


def dispatch_cloud(pat, workflow=CLOUD_WORKFLOW):
    """派发一个 workflow_dispatch。返回 True/False。"""
    body = {"ref": "main"}
    ok, data = github_api("POST", f"actions/workflows/{workflow}/dispatches", pat, body=body)
    if not ok:
        log(f"❌ dispatch {workflow} 失败: {data}")
        return False
    log(f"✅ dispatch {workflow} 已发送")
    return True


def extract_scan_time(text):
    """从 HTML 文本里取 SCAN_DATA.scan_time 或 build-stamp。"""
    m = re.search(r'"scan_time"\s*:\s*"([^"]+)"', text)
    if m:
        return m.group(1)
    b = re.search(r'name="build-stamp"\s+content="(\d+)"', text)
    if b:
        return b.group(1)
    return None


def parse_ts(s):
    """把 scan_time / build-stamp 解析成带时区的 datetime。"""
    if not s:
        return None
    s = s.strip()
    try:
        s2 = s.replace("T", " ").replace("Z", "").strip()
        if len(s2) >= 19:
            return datetime.strptime(s2[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=TZ)
        if len(s2) == 14 and s2.isdigit():
            return datetime.strptime(s2, "%Y%m%d%H%M%S").replace(tzinfo=TZ)
    except Exception:
        pass
    return None


def remote_scan_time():
    try:
        req = urllib.request.Request(SITE_URL, headers={"User-Agent": "guard/1.0"})
        html = urllib.request.urlopen(req, timeout=12).read().decode("utf-8", "ignore")
        return extract_scan_time(html)
    except Exception as e:
        log(f"⚠️ 读取线上站点失败: {e}")
    return None


def local_scan_time():
    p = os.path.join(WORKSPACE, "dist", "index.html")
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8", errors="ignore") as f:
            return extract_scan_time(f.read())
    except Exception as e:
        log(f"⚠️ 读取本地 dist 失败: {e}")
    return None


def local_core_data_fresh():
    """
    判断本地核心数据是否今日收盘后产出。
    检查 data/gold_pool.json 的 update_time 是否 >= 今天 18:30。
    """
    p = os.path.join(WORKSPACE, "data", "gold_pool.json")
    if not os.path.exists(p):
        return False, "gold_pool.json 不存在"
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        ts = d.get("update_time") or d.get("data_time") or d.get("generated_at") or ""
        dt = parse_ts(ts)
        if not dt:
            return False, f"无法解析 gold_pool 时间戳: {ts!r}"
        now = datetime.now(TZ)
        cutoff = now.replace(hour=18, minute=30, second=0, microsecond=0)
        if dt.date() == now.date() and dt >= cutoff:
            return True, f"gold_pool {dt:%Y-%m-%d %H:%M:%S} 是今日收盘后"
        return False, f"gold_pool {dt:%Y-%m-%d %H:%M:%S} 不是今日收盘后（cutoff {cutoff:%H:%M}）"
    except Exception as e:
        return False, f"检查 gold_pool 失败: {e}"


def deploy():
    """调用真实部署脚本。"""
    log("🚀 调用 deploy_now.py 兜底部署…")
    r = subprocess.run([sys.executable, "deploy_now.py"], cwd=WORKSPACE)
    return r.returncode


def write_alert(reason, cloud_status):
    """把告警写入 data/.deploy_alert.json + .ops_status.json + 根目录 ALERT Markdown，供前端/运维卡读取。"""
    rec = {
        "alert": True,
        "reason": reason,
        "cloud_status": cloud_status,
        "time": datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S"),
        "host": socket.gethostname(),
    }
    try:
        os.makedirs(os.path.dirname(ALERT_FILE), exist_ok=True)
        with open(ALERT_FILE, "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False, indent=2)
        log(f"🚨 告警已写入: {ALERT_FILE}")
    except Exception as e:
        log(f"⚠️ 写入告警文件失败: {e}")
    # 同步写入/更新 .ops_status.json，让 shmonitor.html 直接亮红
    try:
        ops_path = os.path.join(WORKSPACE, "data", ".ops_status.json")
        ops = {}
        if os.path.exists(ops_path):
            try:
                ops = json.load(open(ops_path, encoding="utf-8"))
                if not isinstance(ops, dict):
                    ops = {}
            except Exception:
                ops = {}
        ops["deploy_alert"] = rec
        ops["monitor_alert"] = {
            "level": "FAIL",
            "summary": f"收盘部署失败: {reason}",
            "time": rec["time"],
        }
        with open(ops_path, "w", encoding="utf-8") as f:
            json.dump(ops, f, ensure_ascii=False, indent=2)
        log(f"🚨 运维卡告警已同步: {ops_path}")
    except Exception as e:
        log(f"⚠️ 同步 .ops_status.json 失败: {e}")
    # 同时写一份根目录 Markdown 便于人眼查看
    md_path = os.path.join(WORKSPACE, f"ALERT_收盘部署_云端失败_{datetime.now(TZ).strftime('%Y%m%d')}.md")
    try:
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"""# ⚠️ 收盘部署告警

- 时间: {rec['time']}
- 主机: {rec['host']}
- 云端状态: {cloud_status}
- 原因: {reason}

阿狸咪已放弃使用本地陈旧数据兜底部署，等待主人处理。

**建议下一步**：手动触发 GitHub Actions → `cloud_scanner.yml` 或 `cloud_data_fetch.yml`，
待云端成功后再次运行 19:30 自动化。
""")
        log(f"🚨 告警 MD 已写入: {md_path}")
    except Exception as e:
        log(f"⚠️ 写入告警 MD 失败: {e}")


def main():
    ap = argparse.ArgumentParser(description="阿狸咪 19:30 收盘最终部署守卫")
    ap.add_argument("--dry-run", action="store_true", help="不真正触发/等待/部署，只打印判定")
    args = ap.parse_args()

    pat = get_pat()
    if not pat:
        log("❌ 未找到 GitHub PAT（GH_PAT 环境变量或 .gh_pat 文件），无法触发/检查云端。")
        sys.exit(2)

    log("🔍 检查云端今日运行状态…")
    cloud_status, run_id = cloud_status_today(pat)
    log(f"   云端状态: {cloud_status} (run_id={run_id})")

    # 1. 云端已成功 — 但需要校验数据新鲜度（2026-07-20 修：防云端旧数据覆盖）
    if cloud_status == "success":
        remote_raw = remote_scan_time()
        local_raw = local_scan_time()
        remote = parse_ts(remote_raw) if remote_raw else None
        local = parse_ts(local_raw) if local_raw else None
        # 判断云端数据是否今日收盘后新鲜产出
        now = datetime.now(TZ)
        cutoff = now.replace(hour=18, minute=30, second=0, microsecond=0)
        cloud_fresh = remote and remote.date() == now.date() and remote >= cutoff
        if cloud_fresh:
            log(f"✅ 云端已成功部署新鲜数据（线上 {remote:%Y-%m-%d %H:%M} ≥ 今日 cutoof {cutoff:%H:%M}），跳过兜底")
            sys.exit(0)
        if remote and not cloud_fresh:
            log(f"⚠️ 云端虽成功但数据偏旧（线上 {remote:%Y-%m-%d %H:%M} < 今日 cutoff {cutoff:%H:%M}），继续本地兜底判定…")
        elif remote and local and remote >= local:
            log(f"✅ 云端已成功部署（线上 {remote:%Y-%m-%d %H:%M} ≥ 本地 {local:%Y-%m-%d %H:%M}），跳过兜底")
            sys.exit(0)
        log("⚠️ 云端已成功但线上时间戳不如本地，继续进入兜底判定…")
        # 继续下面流程（理论上罕见）

    # 2. 云端正在运行 → 等待
    if cloud_status in ("in_progress", "queued") and run_id:
        if args.dry_run:
            log(f"🧪 [DRY-RUN] 云端 run {run_id} 正在运行，将等待完成")
            sys.exit(0)
        log(f"⏳ 云端 run {run_id} 正在运行，等待完成（最多 60 分钟）…")
        cloud_status = wait_for_run(pat, run_id, timeout=3600)
        log(f"   等待结果: {cloud_status}")
        if cloud_status == "success":
            log("✅ 云端成功，跳过兜底部署")
            sys.exit(0)
        # 失败/超时则继续尝试触发一次

    # 3. 云端未成功 → 尝试触发一次
    if cloud_status != "success":
        if args.dry_run:
            log(f"🧪 [DRY-RUN] 将触发 {CLOUD_WORKFLOW} 并等待")
            sys.exit(0)
        log("🚀 云端尚未成功，尝试触发 cloud_scanner 重跑…")
        # 先触发数据抓取，再触发扫描部署
        # 由于 dispatch 后立即返回，无法等待 data_fetch 完成，所以直接触发 scanner
        # scanner 在云端会先等数据就绪（其 yml 结构不依赖 data_fetch 顺序）。
        # 更稳妥的做法是触发 scanner，它内部包含数据抓取+扫描+部署+闸门。
        if dispatch_cloud(pat, CLOUD_WORKFLOW):
            # GitHub dispatch 是异步的，run 可能延迟 5~30 秒才出现，轮询最多 60 秒
            found = None
            for attempt in range(12):
                time.sleep(5)
                new_status, new_run_id = cloud_status_today(pat)
                if new_run_id and new_status in ("in_progress", "queued", "success"):
                    found = (new_status, new_run_id)
                    break
                log(f"   等待 run 出现… ({attempt + 1}/12)")
            if found:
                new_status, new_run_id = found
                log(f"⏳ 等待新触发 run {new_run_id} (当前 {new_status})…")
                cloud_status = wait_for_run(pat, new_run_id, timeout=3600)
                log(f"   等待结果: {cloud_status}")
            else:
                log("⚠️ 触发后 60 秒内未找到新 run，无法等待")
                cloud_status = "dispatch_lost"
        else:
            cloud_status = "dispatch_failed"

    # 4. 最终判断
    if cloud_status == "success":
        log("✅ 云端最终成功，阿狸咪不兜底部署")
        sys.exit(0)

    # 云端最终失败 → 本地也禁止强推陈旧数据
    # 例外：本地核心数据确实是今日收盘后新鲜产出
    fresh_ok, fresh_msg = local_core_data_fresh()
    if fresh_ok:
        if args.dry_run:
            log(f"🧪 [DRY-RUN] 云端失败，但 {fresh_msg} → 将允许本地兜底部署")
            sys.exit(0)
        log(f"🟡 云端失败，但 {fresh_msg} → 允许本地兜底部署")
        sys.exit(deploy())

    reason = f"云端最终状态={cloud_status}；{fresh_msg}。本地陈旧数据禁止强推。"
    log(f"🚨 {reason}")
    if args.dry_run:
        log("🧪 [DRY-RUN] 将写入告警并退出码 1")
        sys.exit(0)
    write_alert(reason, cloud_status)
    sys.exit(1)


if __name__ == "__main__":
    main()
