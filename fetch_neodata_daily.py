#!/usr/bin/env python3
"""
fetch_neodata_daily.py
每日 neodata 数据抓取（本机专用）。

为何本机做、不放在云端：
  neodata 的临时会话 token 由 WorkBuddy 桌面会话签发，云端 GitHub Actions
  拿不到，因此云端 7 个 cloud_*.yml 都不引用 neodata。本机 17:25 已刷新
  token，本脚本 17:31 紧接其后跑，token 在 23h 有效期内。

流程：
  1) 跑 fetch_52w_high / fetch_sector_fund_flow / fetch_sector_rs → 写 data/
  2) update_data_v2.py --fast 重建 dist（从 data/ 注入）
  3) deploy_now.py --force 部署（其内建 auto source-sync 会推 main，
     三个 neodata json 已在 .gitignore 白名单，云端后续构建也能保留）
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PY = r"C:\Users\Administrator\AppData\Local\Microsoft\WindowsApps\python.exe"
NEO_FILES = ["52w_high.json", "sector_fund_flow.json", "sector_rs.json"]
TOKEN_FILE = os.path.join(ROOT, ".neodata_token")


def run(cmd, timeout=300):
    print(f"[RUN] {cmd}")
    try:
        p = subprocess.run(
            cmd,
            cwd=ROOT,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        if p.stdout:
            print(p.stdout[-800:])
        if p.stderr:
            print(p.stderr[-400:])
        return p.returncode
    except subprocess.TimeoutExpired as e:
        print(f"TIMEOUT after {timeout}s: {e}")
        return -1


def main():
    # 前置检查：token 必须存在，否则三个 fetch 会 401
    if not os.path.exists(TOKEN_FILE):
        print("ERROR: .neodata_token 缺失，跳过 neodata 抓取（请确认 17:25 刷新任务已运行）")
        return 2

    # 1) 抓取三张表
    for name in NEO_FILES:
        script = name.replace(".json", "")
        ec = run(f"{PY} fetch_{script}.py", timeout=180)
        if ec != 0:
            print(f"WARN: fetch_{script}.py 返回 {ec}，该表可能未更新")

    # 2) 重建 dist
    ec = run(f"{PY} update_data_v2.py --fast", timeout=300)
    if ec != 0:
        print(f"WARN: update_data_v2.py 返回 {ec}")

    # 3) 部署（auto source-sync 会把白名单的三个 json 推 origin/main）
    ec = run(f"{PY} deploy_now.py --force", timeout=300)
    if ec != 0:
        print(f"WARN: deploy_now.py 返回 {ec}")
        return 1

    print("neodata 每日抓取 + 部署完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
