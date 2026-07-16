#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
九宝量化 v6.0 — 本地双机「精准发令枪」
================================================
根因：GitHub Actions 定时调度(best-effort)曾整片延迟 ~5h，不可靠。
本脚本由本地双机的精确 OS 定时器(每15分钟)调用，按北京时间判定各档位
是否「已到点 且 尚未部署」，若是则用 GitHub API 精准 dispatch 对应云端
workflow（云端只当算力）。云端不再依赖其自身不可靠的内部定时。

幂等保护：
  1) build-stamp 比对 —— 该档位对应的部署若已发生(build-stamp>=档位时间)，跳过；
  2) 本地状态文件 .dispatch_state.json —— 同一档位 90 分钟内不重复 dispatch
     （避免部署延迟窗口内被反复触发）。

数据源/去向：
  - 读取：git credential（gho_/ghp_ PAT）、环境变量 GH_PAT、或 .gh_pat 文件
  - 读取：线上站点 https://ah-quant999.github.io/quant-scanner-v6/ 的 build-stamp
  - 写入：GitHub API（dispatch workflow）、本地 .dispatch_state.json
  - 绝不触碰 .neodata_token 等 secret 文件。

用法：
  python trigger_cloud_dispatch.py            # 常规运行（每15分钟由自动化调用）
  python trigger_cloud_dispatch.py --dry-run # 只打印判定，不真正 dispatch
"""
import os
import re
import json
import sys
import subprocess
import urllib.request
from datetime import datetime, timedelta, timezone

REPO = "ah-quant999/quant-scanner-v6"
SITE_URL = "https://ah-quant999.github.io/quant-scanner-v6/"
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".dispatch_state.json")
GRACE_MIN = 2               # 到点后宽限，避免边界误触发
TZ = timezone(timedelta(hours=8))   # Asia/Shanghai

# 档位定义：北京时间 (时,分) -> (workflow文件, slot字符串 或 '' , 是否以部署(build-stamp)为幂等判据)
# slot='' 表示 dispatch 时不带档位（该 workflow 任意触发即跑全量，如 data_fetch/scanner）
SLOTS = [
    # 盘前+盘中
    ((9, 20),  "cloud_intraday.yml", "20 1 * * 1-5",  True),
    ((10, 31), "cloud_intraday.yml", "31 2 * * 1-5",  True),
    ((11, 46), "cloud_intraday.yml", "46 3 * * 1-5",  True),
    ((13, 31), "cloud_intraday.yml", "31 5 * * 1-5",  True),
    ((14, 31), "cloud_intraday.yml", "31 6 * * 1-5",  True),
    # 收盘分阶段
    ((15, 30), "cloud_post_close.yml", "30 7 * * 1-5", True),
    ((16, 15), "cloud_post_close.yml", "15 8 * * 1-5", True),
    ((16, 30), "cloud_post_close.yml", "30 8 * * 1-5", True),
    # 收盘数据抓取 / 扫描部署（不部署，仅状态文件防重）
    ((17, 31), "cloud_data_fetch.yml", "", False),
    ((18, 31), "cloud_scanner.yml",  "", True),
]


def log(msg):
    ts = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def get_pat():
    """优先环境变量/文件，否则从 git credential manager 取 PAT。"""
    if os.environ.get("GH_PAT"):
        return os.environ["GH_PAT"].strip()
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".gh_pat")
    if os.path.exists(p):
        try:
            return open(p, encoding="utf-8").read().strip()
        except Exception:
            pass
    try:
        out = subprocess.run(
            "printf 'protocol=https\\nhost=github.com\\n\\n' | git credential fill",
            shell=True, capture_output=True, text=True, timeout=20,
        ).stdout
        for line in out.splitlines():
            if line.startswith("password="):
                return line[len("password="):].strip()
    except Exception as e:
        log(f"⚠️ 读取 git credential 失败: {e}")
    return None


def get_build_stamp():
    """取线上站点 build-stamp（北京时间 YYYYMMDDHHMMSS），失败返回 0。"""
    try:
        req = urllib.request.Request(SITE_URL, headers={"User-Agent": "trigger/1.0"})
        html = urllib.request.urlopen(req, timeout=8).read().decode("utf-8", "ignore")
        m = re.search(r'name="build-stamp"\s+content="(\d+)"', html)
        if m:
            return int(m.group(1))
    except Exception as e:
        log(f"⚠️ 读取 build-stamp 失败: {e}")
    return 0


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log(f"⚠️ 写入状态文件失败: {e}")


def dispatch(workflow_file, slot, pat, dry_run):
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{workflow_file}/dispatches"
    body = {"ref": "main", "inputs": {"slot": slot}}
    if dry_run:
        log(f"🧪 [DRY-RUN] 将 dispatch {workflow_file} slot='{slot}'")
        return True
    cmd = [
        "curl", "-sS", "-X", "POST", url,
        "-H", "Accept: application/vnd.github+json",
        "-H", f"Authorization: Bearer {pat}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(body),
        "-w", "\\nHTTP:%{http_code}",
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        out = r.stdout.strip()
        ok = "HTTP:204" in out or r.returncode == 0 and "HTTP:2" in out
        log(f"{'✅' if ok else '❌'} dispatch {workflow_file} slot='{slot}' -> {out}")
        return ok
    except Exception as e:
        log(f"❌ dispatch {workflow_file} 异常: {e}")
        return False


def main():
    dry_run = "--dry-run" in sys.argv
    now = datetime.now(TZ)
    # 仅工作日（周一~周五）触发交易时段档位
    if now.weekday() >= 5:  # 5=Sat, 6=Sun
        log("📅 周末，跳过交易时段档位触发（周末任务由 GitHub cron 自行处理）")
        return

    pat = get_pat()
    if not pat:
        log("❌ 未找到 GitHub PAT（GH_PAT / .gh_pat / git credential 均无），无法 dispatch。")
        sys.exit(2)
    if dry_run:
        log("🧪 DRY-RUN 模式：不真正 dispatch。")

    build_stamp = get_build_stamp()
    log(f"🕐 当前北京时间 {now.strftime('%Y-%m-%d %H:%M')} | 线上 build-stamp={build_stamp}")
    log(f"📋 共 {len(SLOTS)} 个档位待判定")

    state = load_state()
    dispatched_any = False

    for (h, m), wf, slot, use_stamp in SLOTS:
        slot_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
        due = now >= (slot_dt + timedelta(minutes=GRACE_MIN))
        if not due:
            continue  # 未到点

        # 幂等判据 1：部署型档位，若 build-stamp 已 >= 档位时间，说明已部署
        if use_stamp:
            slot_int = int(slot_dt.strftime("%Y%m%d%H%M%S"))
            if build_stamp >= slot_int:
                log(f"⏭️ {wf} slot='{slot}' 已部署(build-stamp {build_stamp} >= {slot_int})，跳过")
                continue

        # 幂等判据 2：今日已触发过该档位则跳过（避免每日重复 dispatch；
        #   真正的失败重试交给 safety-net.yml 兜底重跑）。
        last = state.get(slot)
        if last:
            try:
                last_dt = datetime.fromisoformat(last)
                if last_dt.astimezone().date() == now.date():
                    log(f"📅 {wf} slot='{slot}' 今日已触发(上次 {last_dt.astimezone(TZ).strftime('%H:%M')})，跳过")
                    continue
            except Exception:
                pass

        # 触发
        ok = dispatch(wf, slot, pat, dry_run)
        if ok:
            state[slot] = datetime.now(timezone.utc).isoformat()
            dispatched_any = True
        # 部署型：dispatch 后 build-stamp 不会立刻更新，依赖冷却期防重；
        # 非部署型(data_fetch)：完全依赖冷却期。

    save_state(state)
    log("🏁 本轮判定完成" + ("，已触发若干档位。" if dispatched_any else "，无需触发。"))


if __name__ == "__main__":
    main()
