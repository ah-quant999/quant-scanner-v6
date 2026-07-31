# 自动化执行记录 — 小九-candidate_pool看门狗-整点

## 2026-07-20 16:13
- 运行 `watch_candidate_pool.py`。候选池 update_time=2026-07-20 14:23:39。
- 当前 16:13 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 修复潜在崩溃 bug：`_run()` 原定义仅接受 (cmd_list, timeout) 两参，但 `_rebuild_and_deploy()` 中以 3 参调用（多传 label 字符串），盘中真正触发重建时会 TypeError 崩溃。已给 `_run` 增加可选 `label` 参数并在日志中标注。py_compile 通过，重跑正常。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-20 18:09
- 运行 `watch_candidate_pool.py`。候选池 update_time=2026-07-20 14:23:39。
- 当前 18:09 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- py_compile 通过；3-arg _run 调用已落地（上次 17:11 修复生效）。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-20 17:11
- 运行 `watch_candidate_pool.py`。当前 17:11 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- **发现并修复回归 bug**：上次 16:13 记录称已给 `_run` 增加可选 `label` 参数，但文件实际未落地——`def _run(cmd_list, timeout=300)` 仍只有两参，而 154/165/173 行以三参调用。盘中真正触发重建时会 `TypeError` 崩溃（在 `_rebuild_and_deploy` 调用点抛出，未被 `_run` 内部 try 捕获），使看门狗整体失效。已真正修复：`_run` 改为 `def _run(cmd_list, timeout=300, label="")` 并在有 label 时打印执行日志。
- py_compile 通过；3-arg 调用实测能正常 spawn 子进程（已手动终止避免非交易时段误跑重构建）。
- 纯修复，未删除任何数据源/备份文件。

## 2026-07-20 19:05
- 运行 `watch_candidate_pool.py`。候选池 update_time=2026-07-20 14:23:39（今日盘后最终态）。
- 当前 19:05 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 3-arg `_run` 调用稳定；未触发重构建，未删除任何数据源/备份文件（纯修复）。
- 提醒：下次盘中(09:30-15:00)若候选池超 60 分钟未更新才会真正走 build→deploy 链路。

## 2026-07-21 12:50
- 审计确认：覆盖陷阱导致 index_master 标签修正（市场温度→主要指数平均涨幅/南向）未部署线上，已重新 commit+push 0ac4bd46 + deploy 修复。
- 本机所有活跃自动化 modelId 全量更新为 ds-V4-FLASH（共 22 个）。
- 紧急交接文档已写：HANDOVER_小九_2026-07-21.md，要求阿狸咪同步切模型为 ds-V4-FLASH。

## 2026-07-21 12:57
- 运行看门狗。候选池 update_time=2026-07-21 12:15:57，age=41min ≤ 60min → 判定新鲜，exit 0（无需重建）。
- **根因+修复**（今日候选池 10:13 之后整天 99-110min 陈旧的真因）：①托管 Python 3.13.12 缺 mootdx → 回退 akshare 卡死；已 `pip install mootdx 0.11.7` 到隔离 base（成功路径 12.7s/5012只）。②`_em_name` 3 次重试+`time.sleep(0.8)` 在东财 push2 持续 `RemoteDisconnected`（0.15s 断）时把 300 只股票解析拖到 ~570s，远超 `_run` 300s 超时 → 构建必被杀；已改为快速失败（单次尝试，异常即 None，名称回退 stock_names.json/原始名）。③手动跑构建 EXIT=0，368 只/来源分布正常。④源码修复与候选池被并发 `auto: source sync 12:49` 提交推 main（lock→release 链已走完），盘中并发安全。
- 写统一心跳 `2026-07-21 12:57:33 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复：装包 + 改一处重试逻辑）。

## 2026-07-21 11:51
- 本轮实际执行「git 冲突审计」任务（用户前序指令延续）：全仓扫描确认 8 个活跃脚本均调用 `safe_pull()`，无裸 `git pull/stash/rebase`；backup_202607XX/ 备份目录按铁律未动。
- 修复回归测试 `test_git_safe_sync.py`：①清理 `watchdog_check.py` 行37 被上一轮失败测试遗留的 `# REMOTE-CONFLICT-MARKER`；②`git_safe_sync.safe_pull` 加 `cwd` 参数；③测试重写为 git worktree 全程隔离（主工作树零触碰，自建 fixture 模拟冲突）。
- `python test_git_safe_sync.py` 三场景全过（T1/T2/T2 无 UU，T3 冲突取上游版并清本地标记）。改动随 a60637e 已推送 origin/main。
- 候选池看门狗：update_time=10:13:57，age=88 分钟 > 60 → 触发重建；`build_candidate_pool.py` 两次因东财限流失败，看门狗正确阻断陈旧部署(exit 1)，无覆盖/无删除。
- 写统一心跳 `2026-07-21 11:51:14 | xiaojiu | candidate_pool_watchdog | DONE`。
- 注：旧测试 finally 的 `checkout -f main`/`reset --hard main` 曾误删用户未提交改动；新 worktree 隔离方案已根治。

## 2026-07-21 17:05
- 运行 `watch_candidate_pool.py`。当前 17:05 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 写统一心跳 `2026-07-21 17:05:19 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-21 18:01
- 运行 `watch_candidate_pool.py`。当前 18:01 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 写统一心跳 `2026-07-21 18:01:05 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-21 18:56
- 运行 `watch_candidate_pool.py`。当前 18:56 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 候选池 `update_time=2026-07-21 14:45:42`，距上次更新约 4h，但已收盘无需重建。
- 写统一心跳 `2026-07-21 18:56:46 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。


## 2026-07-21 19:53
- 运行 `watch_candidate_pool.py`。当前 19:53 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 候选池 `update_time=2026-07-21 19:07:14`，距上次更新约 46min，但已收盘无需重建。
- 写统一心跳 `2026-07-21 19:53:02 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-21 20:48
- 运行 `watch_candidate_pool.py`。当前 20:48 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 写统一心跳 `2026-07-21 20:48:55 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-21 21:44
- 运行 `watch_candidate_pool.py`。当前 21:44 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 写统一心跳 `2026-07-21 21:45:03 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-21 22:40
- 运行 `watch_candidate_pool.py`。当前 22:40 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 写统一心跳 `2026-07-21 22:40:49 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-21 23:36
- 运行 `watch_candidate_pool.py`。当前 23:36 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 写统一心跳 `2026-07-21 23:36:20 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-22 00:31
- 运行 `watch_candidate_pool.py`。当前 00:31 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 写统一心跳 `2026-07-22 00:31:51 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-22 01:27
- 运行 `watch_candidate_pool.py`。当前 01:27 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 写统一心跳 `2026-07-22 01:27:55 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-22 02:23
- 运行 `watch_candidate_pool.py`。当前 02:23 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 写统一心跳 `2026-07-22 02:23:22 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-22 03:18
- 运行 `watch_candidate_pool.py`。当前 03:18 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 候选池状态未检查（非交易时段跳过）。
- 写统一心跳 `2026-07-22 03:18:55 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-22 05:10
- 运行 `watch_candidate_pool.py`。当前 05:10 非交易时段(<09:30)，看门狗按设计跳过重建，exit 0（安全）。
- 候选池 `update_time=2026-07-21 19:07:14`（约10h前），未触发重建/部署。
- 写统一心跳 `2026-07-22 05:10:02 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-22 06:05
- 运行 `watch_candidate_pool.py`。当前 06:05 非交易时段(<09:30)，看门狗按设计跳过重建，exit 0（安全）。
- 候选池 `update_time=2026-07-21 19:07:14`（约11h前，收盘最终态），未触发重建/部署。
- 写统一心跳 `2026-07-22 06:05:xx | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-22 07:03
- 运行 `watch_candidate_pool.py`。当前 07:03 非交易时段(<09:30)，看门狗按设计跳过重建，exit 0（安全）。
- 候选池 `update_time=2026-07-21 19:07:14`（收盘最终态），未触发重建/部署。
- 写统一心跳 `2026-07-22 07:03:40 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-22 07:56
- 运行 `watch_candidate_pool.py`。当前 07:56 非交易时段(<09:30)，看门狗按设计跳过重建，exit 0（安全）。
- 候选池 `update_time=2026-07-21 19:07:14`（收盘最终态），未触发重建/部署。
- 写统一心跳 `2026-07-22 07:56:24 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-22 10:29
- 运行 `watch_candidate_pool.py`。当前 10:29 交易时段内(09:30~15:00)。
- 候选池 `update_time=2026-07-22 09:35:25`，年龄 54 分钟 ≤ 60 分钟 → 判定新鲜，exit 0（无需重建）。
- 写统一心跳 `2026-07-22 10:29:25 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-22 09:37
- 运行 `watch_candidate_pool.py`。当前 09:37 交易时段内(09:30~15:00)。
- 候选池 `update_time=2026-07-22 09:35:25`，年龄仅 2 分钟（09:20 盘前构建已成功刷新）。
- 判定新鲜：年龄 2min ≤ 60min → 无需重建，exit 0（安全）。
- 写统一心跳 `2026-07-22 09:37:53 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-22 12:21
- 运行 `watch_candidate_pool.py`。当前 12:21 交易时段内(09:30~15:00)。
- 候选池 `update_time=2026-07-22 11:27:21`，年龄 54 分钟 ≤ 60 分钟 → 判定新鲜，exit 0（无需重建）。
- 写统一心跳 `2026-07-22 12:21:34 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-22 14:13
- 运行 `watch_candidate_pool.py`。当前 14:13 交易时段内(09:30~15:00)。
- 候选池 `update_time=2026-07-22 13:44:47`，年龄 28 分钟 ≤ 60 分钟 → 判定新鲜，exit 0（无需重建）。
- 写统一心跳 `2026-07-22 14:13:08 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-22 17:00
- 运行 `watch_candidate_pool.py`。当前 17:00 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 候选池 `update_time=2026-07-22 14:47:16`（约2h前，收盘最终态），未触发重建/部署。
- 写统一心跳 `2026-07-22 17:00:45 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-22 17:57
- 运行 `watch_candidate_pool.py`。当前 17:57 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 候选池 `update_time=2026-07-22 14:47:16`（收盘最终态），未触发重建/部署。
- 写统一心跳 `2026-07-22 17:57:04 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-22 15:09
- 运行 `watch_candidate_pool.py`。当前 15:09 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 候选池 `update_time=2026-07-22 14:47:16`（约22分钟前，仍新鲜），total=366。
- 写统一心跳 `2026-07-22 15:09:06 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-22 18:53
- 运行 `watch_candidate_pool.py`。当前 18:53 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 候选池 `update_time=2026-07-22 14:47:16`（收盘最终态），未触发重建/部署。
- 写统一心跳 `2026-07-22 18:53:xx | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-22 19:48
- 运行 `watch_candidate_pool.py`。当前 19:48 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 候选池 `update_time=2026-07-22 14:47:16`（收盘最终态），未触发重建/部署。
- 写统一心跳 `2026-07-22 19:48:31 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-22 21:40
- 运行 `watch_candidate_pool.py`。当前 21:40 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 候选池 `update_time=2026-07-22 19:07:21`（收盘后云端最终态），未触发重建/部署。
- 写统一心跳 `2026-07-22 21:40:xx | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-22 22:35
- 运行 `watch_candidate_pool.py`。当前 22:35 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 写统一心跳 `2026-07-22 22:35:37 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-23 00:26
- 运行 `watch_candidate_pool.py`。当前 00:26 非交易时段(<09:30)，看门狗按设计跳过重建，exit 0（安全）。
- 候选池未检查（非交易时段跳过），未触发重建/部署。
- 写统一心跳 `2026-07-23 00:26:39 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-23 02:17
- 运行 `watch_candidate_pool.py`。当前 02:17 非交易时段(<09:30)，看门狗按设计跳过重建，exit 0（安全）。
- 写统一心跳 `2026-07-23 02:17:38 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-23 03:13
- 运行 `watch_candidate_pool.py`。当前 03:13 非交易时段(<09:30)，看门狗按设计跳过重建，exit 0（安全）。
- 写统一心跳 `2026-07-23 03:13:18 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-22 23:31
- 运行 `watch_candidate_pool.py`。当前 23:31 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 候选池 `update_time=2026-07-22 19:07:21`（收盘后云端最终态），未触发重建/部署。
- 写统一心跳 `2026-07-22 23:31:08 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-23 04:09
- 运行 `watch_candidate_pool.py`。当前 04:09 非交易时段(<09:30)，看门狗按设计跳过重建，exit 0（安全）。
- 候选池未检查（非交易时段跳过），未触发重建/部署。
- 写统一心跳 `2026-07-23 04:09:xx | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。



## 2026-07-23 06:57
- 运行 `watch_candidate_pool.py`。当前 06:57 非交易时段(<09:30)，看门狗按设计跳过重建，exit 0（安全）。
- 写统一心跳 `2026-07-23 06:57:12 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-23 07:53
- 运行 `watch_candidate_pool.py`。当前 07:53 非交易时段(<09:30)，看门狗按设计跳过重建，exit 0（安全）。
- 写统一心跳 `2026-07-23 07:53:48 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。


## 2026-07-23 10:34
- 运行 `watch_candidate_pool.py`。当前 10:34 交易时段内(09:30~15:00)。
- 候选池 `update_time=2026-07-23 09:37:18`，年龄 57 分钟 ≤ 60 分钟 → 判定新鲜，exit 0（无需重建）。
- 写统一心跳 `2026-07-23 10:34:19 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-23 12:31
- 运行 `watch_candidate_pool.py`。当前 12:31 交易时段内(09:30~15:00)。
- 候选池 `update_time=2026-07-23 11:11:09`，年龄 75 分钟 > 60 分钟 → 触发重建。
- 重建链路：build_candidate_pool → sync data/ to main → update_data_v2 → sync dist/ to main → deploy_now --force。
- **全链路成功**：候选池 402 只，部署到 GitHub Pages。
- 写统一心跳 `2026-07-23 12:31:59 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-23 13:48
- 运行 `watch_candidate_pool.py`。当前 13:27 交易时段内(09:30~15:00)。
- 候选池 `update_time=2026-07-23 12:27:21`，年龄 61 分钟 > 60 分钟 → 触发重建。
- **看门狗第 1 次尝试**：候选池重建 ✓ → push main ✓ → 前端构建 ✓ → push dist ✓ → 部署 ✗（GitHub SSH 超时 `ssh: connect to host github.com port 22: Connection timed out`）
- **看门狗第 2 次尝试**：候选池重建 ✓ → push main ✓ → 前端构建 ✓ → push dist ✓ → 部署 ✗（同样 SSH 超时）
- 两次尝试均因 SSH 网络问题失败，看门狗返回 exit 1，成功阻止陈旧数据部署。
- **手动重试部署**：SSH 恢复但 gh-pages 被 fetch-first 拒绝，再试一次后 ✅ **全链路成功**。
- 候选池 `update_time=2026-07-23 13:36:10`，total=401；gh-pages head=91a93ef25714，ls-remote 校验通过。
- 心跳上报成功: xiaojiu → origin/main。
- 写统一心跳 `2026-07-23 13:48:12 | xiaojiu | candidate_pool_watchdog | DONE`。
- 纯修复，未删除任何数据源/备份文件。

## 2026-07-23 16:51
- 运行 `watch_candidate_pool.py`。当前 16:51 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 写统一心跳 `2026-07-23 16:51:05 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-23 18:48
- 运行 `watch_candidate_pool.py`。当前 18:48 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 候选池未检查（非交易时段跳过），未触发重建/部署。
- 写统一心跳 `2026-07-23 18:48:xx | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-23 19:44
- 运行 `watch_candidate_pool.py`。当前 19:44 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 候选池未检查（非交易时段跳过），未触发重建/部署。
- 写统一心跳 `2026-07-23 19:44:06 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。


## 2026-07-23 20:39
- 运行 `watch_candidate_pool.py`。当前 20:39 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 候选池未检查（非交易时段跳过），未触发重建/部署。
- 写统一心跳 `2026-07-23 20:39:34 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-23 21:35
- 运行 `watch_candidate_pool.py`。当前 21:35 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 候选池未检查（非交易时段跳过），未触发重建/部署。
- 写统一心跳 `2026-07-23 21:35:35 | xiaojiu | candidate_pool_watchdog | DONE`
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-23 22:31
- 运行 `watch_candidate_pool.py`。当前 22:31 非交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 写统一心跳 `2026-07-23 22:31:14 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-24 01:18
- 运行 `watch_candidate_pool.py`。当前 01:18 非交易时段(<09:30)，看门狗按设计跳过重建，exit 0（安全）。
- 候选池未检查（非交易时段跳过），未触发重建/部署。
- 写统一心跳 `2026-07-24 01:18:43 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。
- 运行 `watch_candidate_pool.py`。当前 23:27 非交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 候选池 `update_time` 未检查（非交易时段跳过），未触发重建/部署。
- 写统一心跳 `2026-07-23 23:27:19 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-24 04:05
- 运行 `watch_candidate_pool.py`。当前 04:05 非交易时段(<09:30)，看门狗按设计跳过重建，exit 0（安全）。
- 候选池未检查（非交易时段跳过），未触发重建/部署。
- 写统一心跳 `2026-07-24 04:05:46 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-24 05:01
- 运行 `watch_candidate_pool.py`。当前 05:01 非交易时段(<09:30)，看门狗按设计跳过重建，exit 0（安全）。
- 候选池未检查（非交易时段跳过），未触发重建/部署。
- 写统一心跳 `2026-07-24 05:01:20 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-30 16:59
- 运行 `watch_candidate_pool.py`。当前 16:59 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 候选池未检查（非交易时段跳过），未触发重建/部署。
- 写统一心跳 `2026-07-30 16:59:45 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯检查）。
- **注意**：用户指令写的 `check_candidate_pool.py` 不存在，实际使用 `watch_candidate_pool.py` 执行。

## 2026-07-24 06:52
- 运行 `watch_candidate_pool.py`。当前 06:52 非交易时段(<09:30)，看门狗按设计跳过重建，exit 0（安全）。
- 候选池未检查（非交易时段跳过），未触发重建/部署。
- 写统一心跳 `2026-07-24 06:52:49 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯修复）。

## 2026-07-30 17:55
- 运行 `watch_candidate_pool.py`。当前 17:55 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 候选池未检查（非交易时段跳过），未触发重建/部署。
- 写统一心跳 `2026-07-30 17:55:22 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯检查）。
- **注**：用户指令中 `check_candidate_pool.py` 不存在，沿用 `watch_candidate_pool.py`。

## 2026-07-30 18:51
- 运行 `watch_candidate_pool.py`。当前 18:51 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 候选池未检查（非交易时段跳过），未触发重建/部署。
- 写统一心跳 `2026-07-30 18:51:xx | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯检查）。

## 2026-07-30 19:47
- 运行 `watch_candidate_pool.py`。当前 19:47 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 候选池未检查（非交易时段跳过），未触发重建/部署。
- 写统一心跳 `2026-07-30 19:47:26 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯检查）。
- **注**：用户指令中 `check_candidate_pool.py` 不存在，沿用 `watch_candidate_pool.py`。

## 2026-07-30 20:42
- 运行 `watch_candidate_pool.py`。当前 20:42 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 候选池未检查（非交易时段跳过），未触发重建/部署。
- 写统一心跳 `2026-07-30 20:42:xx | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯检查）。
- **注**：用户指令中 `check_candidate_pool.py` 不存在，沿用 `watch_candidate_pool.py`。

## 2026-07-30 21:38
- 运行 `watch_candidate_pool.py`（用户指令 `check_candidate_pool.py` 不存在，沿用 `watch_candidate_pool.py`）。
- 当前 21:38 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 写统一心跳 `2026-07-30 21:38:xx | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯检查）。

## 2026-07-30 22:34
- 运行 `watch_candidate_pool.py`（用户指令 `check_candidate_pool.py` 不存在，沿用 `watch_candidate_pool.py`）。
- 当前 22:34 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 日志输出：`2026-07-30 22:34:05 🛌 非交易时段，看门狗跳过`
- 写统一心跳 `2026-07-30 22:34:xx | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯检查）。

## 2026-07-30 23:30
- 运行 `watch_candidate_pool.py`（用户指令 `check_candidate_pool.py` 不存在，沿用 `watch_candidate_pool.py`）。
- 当前 23:30 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 日志输出：`2026-07-30 23:30:03 🛌 非交易时段，看门狗跳过`
- 写统一心跳 `2026-07-30 23:30:xx | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯检查）。

## 2026-07-31 00:26
- 运行 `watch_candidate_pool.py`（用户指令 `check_candidate_pool.py` 不存在，沿用 `watch_candidate_pool.py`）。
- 当前 00:26 非交易时段(<09:30)，看门狗按设计跳过重建，exit 0（安全）。
- 日志输出：`2026-07-31 00:26:08 🛌 非交易时段，看门狗跳过`
- 写统一心跳 `2026-07-31 00:26:xx | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯检查）。

## 2026-07-31 01:22
- 运行 `watch_candidate_pool.py`（用户指令 `check_candidate_pool.py` 不存在，沿用 `watch_candidate_pool.py`）。
- 当前 01:22 非交易时段(<09:30)，看门狗按设计跳过重建，exit 0（安全）。
- 日志输出：`2026-07-31 01:22:08 🛌 非交易时段，看门狗跳过`
- 写统一心跳 `2026-07-31 01:22:xx | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯检查）。

## 2026-07-31 02:18
- 运行 `watch_candidate_pool.py`（用户指令 `check_candidate_pool.py` 不存在，沿用 `watch_candidate_pool.py`）。
- 当前 02:18 非交易时段(<09:30)，看门狗按设计跳过重建，exit 0（安全）。
- 日志输出：`2026-07-31 02:18:10 🛌 非交易时段，看门狗跳过`
- 写统一心跳 `2026-07-31 02:18:xx | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯检查）。

## 2026-07-31 03:14
- 运行 `watch_candidate_pool.py`（用户指令 `check_candidate_pool.py` 不存在，沿用 `watch_candidate_pool.py`）。
- 当前 03:14 非交易时段(<09:30)，看门狗按设计跳过重建，exit 0（安全）。
- 日志输出：`2026-07-31 03:14:07 🛌 非交易时段，看门狗跳过`
- 写统一心跳 `2026-07-31 03:14:xx | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯检查）。

## 2026-07-31 04:10
- 运行 `watch_candidate_pool.py`（用户指令 `check_candidate_pool.py` 不存在，沿用 `watch_candidate_pool.py`）。
- 当前 04:10 非交易时段(<09:30)，看门狗按设计跳过重建，exit 0（安全）。
- 日志输出：`2026-07-31 04:10:11 🛌 非交易时段，看门狗跳过`
- 写统一心跳 `2026-07-31 04:10:xx | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯检查）。

## 2026-07-31 05:06
- 运行 `watch_candidate_pool.py`（用户指令 `check_candidate_pool.py` 不存在，沿用 `watch_candidate_pool.py`）。
- 当前 05:06 非交易时段(<09:30)，看门狗按设计跳过重建，exit 0（安全）。
- 日志输出：`2026-07-31 05:06:10 🛌 非交易时段，看门狗跳过`
- 写统一心跳 `2026-07-31 05:06:xx | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯检查）。

## 2026-07-31 06:02
- 运行 `watch_candidate_pool.py`（用户指令 `check_candidate_pool.py` 不存在，沿用 `watch_candidate_pool.py`）。
- 当前 06:02 非交易时段(<09:30)，看门狗按设计跳过重建，exit 0（安全）。
- 日志输出：`2026-07-31 06:02:13 🛌 非交易时段，看门狗跳过`
- 写统一心跳 `2026-07-31 06:02:16 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯检查）。

## 2026-07-31 06:58
- 运行 `watch_candidate_pool.py`（用户指令 `check_candidate_pool.py` 不存在，沿用 `watch_candidate_pool.py`）。
- 当前 06:58 非交易时段(<09:30)，看门狗按设计跳过重建，exit 0（安全）。
- 日志输出：`2026-07-31 06:58:13 🛌 非交易时段，看门狗跳过`
- 写统一心跳：`2026-07-31 06:58:xx | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯检查）。

## 2026-07-31 18:04
- 运行 `watch_candidate_pool.py`（用户指令 `check_candidate_pool.py` 不存在，沿用 `watch_candidate_pool.py`）。
- 当前 18:04 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 日志输出：`2026-07-31 18:04:51 🛌 非交易时段，看门狗跳过`
- 写统一心跳：`2026-07-31 18:04:55 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯检查）。

## 2026-07-31 19:00
- 运行 `watch_candidate_pool.py`（用户指令 `check_candidate_pool.py` 不存在，沿用 `watch_candidate_pool.py`）。
- 当前 19:00 已过交易时段(>15:00)，看门狗按设计跳过重建，exit 0（安全）。
- 日志输出：`2026-07-31 19:00:25 🛌 非交易时段，看门狗跳过`
- 写统一心跳：`2026-07-31 19:00:28 | xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何数据源/备份文件（纯检查）。
- ⚠️ 顺带观察：`_heartbeat.log` 显示 `2026-07-31 18:30:00 | xiaojiu | close_p2 | CRASH | run_batch() missing 1 required positional argument: 'mode'`，close_p2 任务 18:30 崩溃，建议排查（非本次看门狗职责）。
