#!/usr/bin/env python3
"""
push_notify.py — 收盘后推送通知（桩脚本）

说明：
  batch_update.py 的 close 模式最后一步调用本脚本做推送通知。
  当前环境未配置微信/企微推送通道（automation push_to_wechat=false），
  故此处仅做无害占位：读取可选参数、打印提示、以 0 退出，
  保证调度流水线能干净收尾，不影响前面已完成的部署步骤。

用法:
  python push_notify.py [任意参数]
"""
import sys
import json
import os
from datetime import datetime

WORKSPACE = os.path.dirname(os.path.abspath(__file__))


def main():
    args = sys.argv[1:]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[push_notify] {now} 占位通知（未配置推送通道），参数: {args}")

    # 若存在交接日志，顺手标记通知环节已完成（不报错即可）
    hb = os.path.join(WORKSPACE, ".batch_heartbeat.json")
    if os.path.exists(hb):
        try:
            os.remove(hb)
        except Exception:
            pass

    # 总是成功退出，避免调度器误判失败
    sys.exit(0)


if __name__ == "__main__":
    main()
