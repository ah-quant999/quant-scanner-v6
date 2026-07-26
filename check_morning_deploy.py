# -*- coding: utf-8 -*-
"""
check_morning_deploy.py — 盘前部署自愈探测器（守卫脚本）

用途：
    检测当日 09:20 盘前任务是否「真的跑完并部署成功」。
    被 10:05 兜底自动化(小九-盘前失败自愈)调用：
        退出码 0 = 已成功运行(正常)，无需处理；
        退出码 1 = 未成功运行(需自愈，自动化将自动重跑 pre_market)。

判据（唯一、可靠，杜绝假阴性）：
    读取 premarket_heartbeat.log，若存在「今日 09:00~11:59 的 DONE 留痕」
    → 判为已运行。其余一律判为未运行（包括：任务没跑、跑崩没到部署、
    或只写了 START 没写 DONE）。

    为什么不用 data/*.json 的 mtime？
    因为 cache/token/scan_progress 等辅助文件常在早间被其它任务触碰，
    会制造「假正常」。DONE 留痕是盘前任务「本人」在部署成功后亲手写的，
    不会与其它任务混淆，也不会被下午云端救回的数据误导。

数据去向：
    只读 premarket_heartbeat.log，不写入、不部署、不改任何文件。

依赖：
    Python 3.14 全路径；仓库根目录 repo-temp（cwd 即此）。
    配合 automation-1784506300221(09:20 盘前) 与 10:05 兜底自动化使用。
    09:20 / 10:05 任务须在「部署验证成功后」追加一行：
        echo "$(date +'%Y-%m-%d %H:%M:%S') pre_market DONE" >> premarket_heartbeat.log
"""
import os
import re
import sys
import datetime

REPO = os.path.dirname(os.path.abspath(__file__))
HEARTBEAT = os.path.join(REPO, "premarket_heartbeat.log")
TODAY = datetime.date.today().strftime("%Y-%m-%d")
# 早间窗口：09:00 ~ 11:59（含 09:20 触发后仍在跑、10:05 自愈的情况）
MORNING_DONE_RE = re.compile(
    re.escape(TODAY) + r" (?:0[9]|1[01]):\d\d:\d\d .*pre_market DONE"
)


def morning_deploy_done():
    if not os.path.exists(HEARTBEAT):
        return False
    with open(HEARTBEAT, encoding="utf-8") as f:
        for line in f:
            if MORNING_DONE_RE.search(line):
                return True
    return False


def main():
    done = morning_deploy_done()
    if done:
        print(f"[{TODAY}] MORNING_FIRED — 盘前任务已成功部署，早间数据正常")
        sys.exit(0)
    else:
        print(f"[{TODAY}] MORNING_MISSED — 盘前任务今日未成功部署，需自愈")
        sys.exit(1)


if __name__ == "__main__":
    main()
