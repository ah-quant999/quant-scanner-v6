#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
push_china_data.py — 双机收盘后把本轮产出的中国源数据提交到 main

【架构定位】
双机（小九/阿狸咪）在中国网络抓取板块资金/概念/龙虎榜/北向/研报/斐波那契等，
这些中国数据源在美区云端 runner 抓不到（60s 超时），必须由双机作为「上游」推到 main，
云端（cloud_scanner / cloud_post_close / cloud_intraday）checkout main 后直接复用，
不再重复抓取。

【为什么需要本脚本（根因修复）】
原流程里，中国源数据推到 main 的动作藏在 deploy_now.py 内部，而 deploy_now.py 只在
close_deploy_guarded.py 决定「本地兜底部署」时才跑。当云端当天部署成功时，守卫会
sys.exit(0) 跳过 → deploy_now.py 不跑 → 双机当天新鲜中国数据永不进 main →
云端次日构建用的仍是旧 main 数据，于是出现「最新数据跑了却一直部署旧数据」。

本脚本把「推数据到 main」从「部署」中解耦出来，由 batch_update.py 的 close_p2 / close
模式在产出数据后必定调用（不受 19:30 部署守卫跳过影响），确保每天双机的新鲜数据进入 main。

【与 push_experiment_files.py 的区别】
- push_experiment_files.py 只推 data/experiment/（三重选股实验，专属白名单）
- 本脚本推 data/*.json（已在 .gitignore 白名单内的中国源数据），用 `git add -A data/`
  自动尊重 .gitignore，不会纳入 zsxq_token.json 等机密，也不会纳入未白名单的新文件。
"""
import os
import sys
import subprocess
from datetime import datetime

WORKSPACE = os.path.dirname(os.path.abspath(__file__))


def run(cmd, cwd=WORKSPACE, env=None):
    return subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, env=env)


def main():
    # 仅暂存已在 .gitignore 白名单内的 data/*.json（git add -A 尊重 .gitignore：
    # 机密文件如 zsxq_token.json / .neodata_token 被忽略，不会纳入；
    # 未加入白名单的新 json 同样被忽略，避免误入仓）。
    r = run("git add -A data/")
    if r.returncode != 0:
        print(f"[push_china] git add 失败: {r.stderr[:200]}")
        return 1

    # 检查是否有可提交内容
    r = run("git diff --cached --stat")
    if not r.stdout.strip():
        print("[push_china] 无新增/修改内容，跳过")
        return 0

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    msg = f"auto: sync 双机中国源数据 {now}"
    r = run(f'git commit -m "{msg}"')
    if r.returncode != 0:
        # 可能是 nothing to commit（极端竞态）
        if "nothing to commit" in (r.stdout + r.stderr):
            print("[push_china] nothing to commit，跳过")
            return 0
        print(f"[push_china] commit 失败: {r.stderr[:200]}")
        return 1

    # push 带 SSH 超时保护 + HTTP/1.1（家用机 git push 常挂死，15s 超时后失败而非无限等待）
    env = os.environ.copy()
    env["GIT_SSH_COMMAND"] = "ssh -o ConnectTimeout=15"
    r = run("git -c http.version=HTTP/1.1 push origin main", env=env)
    if r.returncode != 0:
        print(f"[push_china] push 失败: {r.stderr[:200]}")
        return 1

    print(f"[push_china] 已提交并推送中国源数据到 main ({now})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
