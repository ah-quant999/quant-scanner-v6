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
MAX_DISPATCH_PER_RUN = 1    # 每轮最多触发 1 个 slot，防止首次运行/长时间停跑后批量触发所有档位
WORKFLOW_COOLDOWN_MIN = 30  # 同一 workflow 近 30 分钟内不重复 dispatch，避免并发堆积

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
    # 收盘数据抓取 / 扫描部署
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


def recent_success(workflow_file, pat, minutes=60):
    """幂等第3层：查 GitHub Actions 运行历史，若该 workflow 近 minutes 分钟内有成功运行
    或在跑中(in_progress/queued)则视为已跑，发令枪跳过（避免与 cron 重复触发）。"""
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{workflow_file}/runs?per_page=5"
    try:
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {pat}", "Accept": "application/vnd.github+json"},
        )
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())
        now = datetime.now(timezone.utc)
        for run in data.get("workflow_runs", []):
            status = run.get("status", "")
            if status not in ("success", "in_progress", "queued"):
                continue
            created = run.get("created_at", "")
            if not created:
                continue
            ct = datetime.fromisoformat(created.replace("Z", "+00:00"))
            if (now - ct).total_seconds() <= minutes * 60:
                return True
    except Exception as e:
        log(f"⚠️ 查询运行历史失败(将放行触发): {e}")
    return False


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


def recent_dispatch_for_workflow(state, workflow_file):
    """同一 workflow 近 WORKFLOW_COOLDOWN_MIN 分钟内是否已 dispatch 过（防止并发堆积）。"""
    now = datetime.now(TZ)
    for sl, ts_str in state.items():
        # 只关注属于该 workflow 的 slot
        for (_, _), wf, slot, _ in SLOTS:
            if wf != workflow_file or slot != sl:
                continue
            try:
                last = datetime.fromisoformat(ts_str)
                # 兼容旧版 UTC 记录：统一转 CST 再比较
                last_cst = last.astimezone(TZ)
                if (now - last_cst).total_seconds() < WORKFLOW_COOLDOWN_MIN * 60:
                    return True, last_cst
            except Exception:
                pass
    return False, None


SLOT_INPUT_WORKFLOWS = {"cloud_post_close.yml", "cloud_intraday.yml"}


def dispatch(workflow_file, slot, pat, dry_run):
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{workflow_file}/dispatches"
    body = {"ref": "main"}
    # 仅对确实定义了 slot 入参的 workflow 传 inputs，否则 GitHub API 返回 422，
    # 导致 cloud_scanner / cloud_data_fetch 等永远无法被发令枪触发（只能靠 cron）。
    if workflow_file in SLOT_INPUT_WORKFLOWS and slot:
        body["inputs"] = {"slot": slot}
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
    is_weekend = now.weekday() >= 5  # 5=Sat, 6=Sun

    pat = get_pat()
    if not pat:
        log("❌ 未找到 GitHub PAT（GH_PAT / .gh_pat / git credential 均无），无法 dispatch。")
        sys.exit(2)
    if dry_run:
        log("🧪 DRY-RUN 模式：不真正 dispatch。")

    build_stamp = get_build_stamp()
    log(f"🕐 当前北京时间 {now.strftime('%Y-%m-%d %H:%M')} {'(周末)' if is_weekend else '(工作日)'} | 线上 build-stamp={build_stamp}")
    log(f"📋 共 {len(SLOTS)} 个档位待判定")

    state = load_state()
    dispatched_any = False
    dispatched_count = 0

    for (h, m), wf, slot, use_stamp in SLOTS:

        # 每轮最多触发 1 个 slot，避免首次运行或长时间停跑后批量触发所有档位
        if dispatched_count >= MAX_DISPATCH_PER_RUN:
            log(f"⏭️ 本轮已达最大触发数({MAX_DISPATCH_PER_RUN})，剩余 slot 下一 15min 周期再判")
            break

        slot_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
        due = now >= (slot_dt + timedelta(minutes=GRACE_MIN))
        if not due:
            continue  # 未到点

        # 幂等判据 1：部署型档位，仅当「本发令枪今日确已发令该档位」且 build-stamp 已 >= 档位时间，
        #   才判定云端已部署完成并跳过。
        #   ⚠️ 关键修正（2026-07-27）：旧逻辑仅凭 build-stamp >= 档位时间就跳过，但 build-stamp
        #      只代表「最后一次部署」，小九本机部署也会顶高它 → 误判「云端已抓数」而永不发令，
        #      云端真失败时被彻底掩盖。现要求必须存在本枪今日发令记录才允许以 build-stamp 跳过，
        #      否则（小九先部署 / 云端 cron 失败）一律重新发令，确保云端失败能被兜底重试。
        if use_stamp and slot in state:
            last_dt = None
            try:
                last_dt = datetime.fromisoformat(state[slot])
            except Exception:
                pass
            if last_dt and last_dt.astimezone(TZ).date() == now.date():
                slot_int = int(slot_dt.strftime("%Y%m%d%H%M%S"))
                if build_stamp >= slot_int:
                    log(f"⏭️ {wf} slot='{slot}' 今日已发令且已部署(build-stamp {build_stamp} >= {slot_int})，跳过")
                    continue

        # 幂等判据 2：今日已触发过该档位则跳过（避免每日重复 dispatch；
        #   真正的失败重试交给 safety-net.yml 兜底重跑）。
        last = state.get(slot)
        if last:
            try:
                last_dt = datetime.fromisoformat(last)
                # 关键修复：统一转 CST 后再比较日期，避免 UTC/CST 跨日误判
                # （旧版用 UTC 存但按本地时区判断，导致昨晚 20:31 被算成今天）
                if last_dt.astimezone(TZ).date() == now.date():
                    log(f"📅 {wf} slot='{slot}' 今日已触发(上次 {last_dt.astimezone(TZ).strftime('%H:%M')})，跳过")
                    continue
            except Exception:
                pass

        # 幂等第3层：同一 workflow 近 WORKFLOW_COOLDOWN_MIN 分钟内已 dispatch → 跳过
        recently_dispatched, last_dispatched = recent_dispatch_for_workflow(state, wf)
        if recently_dispatched:
            log(f"🕐 {wf} 近 {WORKFLOW_COOLDOWN_MIN}min 内已 dispatch(上次 {last_dispatched.strftime('%H:%M')})，跳过")
            continue

        # 幂等第4层：云端 cron 近 60min 已成功跑过该 workflow → 跳过（发令枪不再重复触发）
        if recent_success(wf, pat, minutes=60):
            log(f"🕐 {wf} 近 60min 云端已成功运行，发令枪跳过（避免与 cron 重复）")
            continue

        # 触发
        ok = dispatch(wf, slot, pat, dry_run)
        if ok:
            # 关键修复：统一用 CST 存储，避免时区跨日混乱
            state[slot] = datetime.now(TZ).isoformat()
            dispatched_any = True
            dispatched_count += 1
        # 部署型：dispatch 后 build-stamp 不会立刻更新，依赖冷却期防重；
        # 非部署型(data_fetch)：完全依赖冷却期。

    save_state(state)
    log("🏁 本轮判定完成" + ("，已触发若干档位。" if dispatched_any else "，无需触发。"))


if __name__ == "__main__":
    main()
