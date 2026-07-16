#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三方心跳上报 — 写 data/hb_<role>.json 并 push 到 origin/main

目的：让「云端 / 小九 / 阿狸咪」三方健康状态汇聚到 Git 仓库，
      update_data_v2.py 构建时读取并注入运维状态卡，三方监控真正可用。
      （取代原 HANDOVER_LOG.jsonl 机制——该机制因 .gitignore 忽略 +
       构建【之后】才追加写 + 本机 host 用 COMPUTERNAME 与云端期望的
       CAT/ALIMI 字符串不匹配，导致三方监控永远显示 ❓）

用法:
  云端 workflow: python report_heartbeat.py --role cloud --mode cloud_intraday
  本机部署后:     python report_heartbeat.py --role auto --mode deploy
  --no-push:     只写本地文件不 push（供云端随 data 统一提交时使用）

依赖: 仅标准库（json/os/sys/subprocess/datetime/argparse）
数据去向: data/hb_cloud.json / data/hb_xiaojiu.json / data/hb_alimi.json（进 Git，见 .gitignore 例外）
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
ROLES = ("cloud", "xiaojiu", "alimi")


def _git(*args):
    """Git 调用封装：强制 HTTP/1.1（避 GitHub Pages HTTP/2 断连），云端环境补 user 标识。"""
    cmd = ["git", "-c", "http.version=HTTP/1.1"]
    if os.environ.get("GITHUB_ACTIONS") == "true":
        cmd += ["-c", "user.name=heartbeat-bot", "-c", "user.email=bot@users.noreply.github.com"]
    cmd += list(args)
    return subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True)


def detect_role():
    """无 --role 时自动识别本机角色（小九 / 阿狸咪）"""
    # 1. 优先读 .machine_role（每台机器独立，.gitignore 不进 Git）
    mr = os.path.join(BASE_DIR, ".machine_role")
    if os.path.exists(mr):
        v = open(mr, encoding="utf-8").read().strip().lower()
        if v in ("cat", "xiaojiu", "小九"):
            return "xiaojiu"
        if v in ("alimi", "ali", "阿狸咪"):
            return "alimi"
    # 2. 回退到 COMPUTERNAME（小九=LEMONCAT，阿狸咪含 ALIMI）
    cn = os.environ.get("COMPUTERNAME", "").upper()
    if "ALIMI" in cn:
        return "alimi"
    if "LEMONCAT" in cn or "CAT" in cn:
        return "xiaojiu"
    # 3. 默认小九（当前主用机）
    return "xiaojiu"


def write_heartbeat(role, mode):
    os.makedirs(DATA_DIR, exist_ok=True)
    now = datetime.now()
    rec = {
        "status": "ok",
        "last_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "mode": mode,
        "updated_at": now.astimezone().isoformat(),
    }
    path = os.path.join(DATA_DIR, f"hb_{role}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2)
    return path, rec


def push_with_retry(path, role, mode, max_attempts=3):
    msg = f"hb: {role} {mode} {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    for attempt in range(1, max_attempts + 1):
        # 先拉最新（rebase），避免 non-fast-forward
        _git("pull", "--rebase", "origin", "main")
        _git("add", "-f", path)
        c = _git("commit", "-m", msg)
        if c.returncode != 0 and "nothing to commit" not in (c.stdout + c.stderr):
            if attempt < max_attempts:
                continue
        r = _git("push", "origin", "main")
        if r.returncode == 0:
            return True, None
        if attempt < max_attempts:
            continue
        return False, (r.stderr + r.stdout)[-300:]
    return False, "重试耗尽"


def main():
    ap = argparse.ArgumentParser(description="三方心跳上报")
    ap.add_argument("--role", default="auto", choices=["auto", *ROLES])
    ap.add_argument("--mode", default="unknown")
    ap.add_argument("--no-push", action="store_true", help="只写文件不 push")
    args = ap.parse_args()

    role = args.role if args.role != "auto" else detect_role()
    if role not in ROLES:
        print(f"❌ 未知 role: {role}")
        return 1

    path, rec = write_heartbeat(role, args.mode)
    print(f"💓 心跳文件已写: {os.path.basename(path)} (role={role}, mode={args.mode}, time={rec['last_time']})")

    if args.no_push:
        print("   --no-push: 跳过 commit/push（由调用方统一提交）")
        return 0

    ok, err = push_with_retry(path, role, args.mode)
    if ok:
        print(f"✅ 心跳上报成功: {role} → origin/main")
        return 0
    print(f"❌ 心跳上报失败: {err}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
