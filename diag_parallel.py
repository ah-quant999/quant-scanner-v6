#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""diag_parallel.py — 诊断并行组失败的具体子任务

用法: python diag_parallel.py
后台运行，输出到 diag_parallel.log
"""
import time
import batch_update as B


def run_group(name, steps):
    print(f"\n{'#'*60}\n##### {name} ({len(steps)} tasks) #####")
    t0 = time.time()
    ok, elapsed, detail = B.run_parallel_group(
        steps, B.MODES.get("close_p1", {}).get("max_parallel", 6)
    )
    print(f"group_ok={ok} elapsed={elapsed:.1f}s")
    fails = []
    for j, (cmd, tmo) in enumerate(steps):
        r = detail.get(j, (cmd, False, 0, "NOT_RUN"))
        c, o, e, d = r
        status = "OK" if o else "FAIL"
        if not o:
            fails.append(cmd)
            print(f"  [{status}] {c}  {e:.1f}s  detail={d}")
        else:
            print(f"  [{status}] {c}  {e:.1f}s")
    print(f"  >>> 失败子任务: {fails if fails else '无'}")
    return ok, fails


if __name__ == "__main__":
    print(f"诊断开始 {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"COMPUTERNAME={__import__('os').environ.get('COMPUTERNAME')}")

    # close_p1 的 Group 2：22 个数据抓取
    p1 = B.MODES["close_p1"]["steps"][1]
    run_group("close_p1 PARALLEL_GROUP_22 (数据抓取)", p1)

    # close_p2 的 Group 4：10 个生成脚本（排除已知正常且极慢的 fetch_industry_map.py）
    p2_raw = B.MODES["close_p2"]["steps"][2]
    p2 = [s for s in p2_raw if s[0] != "fetch_industry_map.py"]
    run_group("close_p2 PARALLEL_GROUP_10 (生成, 排除industry_map)", p2)

    print(f"\n诊断结束 {time.strftime('%Y-%m-%d %H:%M:%S')}")
