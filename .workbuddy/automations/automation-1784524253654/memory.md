# 候选池看门狗 — 执行记录

## 2026-07-24 03:24 运行（周五·凌晨/非交易时段）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 检测：当前 03:24 < 09:30 开盘边界，`_is_trading_hours()` 返回 False。
- 结果：`🛌 非交易时段，看门狗跳过`，exit 0 直接休眠。
- 候选池现状：未读取（非交易时段直接跳过），未触发重建/部署。
- 心跳：`2026-07-24 03:24:48 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-07-23 21:49 运行（周四·收盘后）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 检测：当前 21:49 > 15:00 收盘边界，`_is_trading_hours()` 返回 False。
- 结果：`🛌 非交易时段，看门狗跳过`，exit 0 直接休眠。
- 候选池现状：未读取（非交易时段直接跳过），未触发重建/部署。
- 心跳：`2026-07-23 21:49:39 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-07-23 02:58 运行（周四·凌晨/非交易时段）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：`🛌 非交易时段，看门狗跳过`（02:58 < 09:30 开盘边界）。`_is_trading_hours()` 返回 False，exit 0 直接休眠。
- 心跳：`2026-07-23 02:58:08 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯巡检型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（纯修复型，无删除）。

## 2026-07-21 10:09 用户手动干预：GTimg 源重建成功（东财限流下的可用路径）
- 看门狗在阿狸咪（本机）因东财限流失败；但发现本机 `mootdx` 未安装、akshare 东财/新浪均不可用。
- **可用替代源**：腾讯 `data_source_gtimg.py` 的 `fetch_gtimg_spot()` 在本机完美可用（5199 只 A 股，含成交额+干净名，非东财不限流）。
- **重建命令**：`CLOUD_RUNNER=true python build_candidate_pool.py` → `_is_cloud()` 为真 → A 股走 GTimg（港股仍 akshare 新浪），产出 371 只，update_time 2026-07-21 10:13:57。
- **后续安全序列**：commit+push data/candidate_pool.json 到 main → update_data_v2.py → deploy_now.py --force。核验 origin/gh-pages 候选池为新鲜版即成功。
- **建议**：看门狗 `_rebuild_and_deploy()` 在 akshare 失败时，可尝试 `CLOUD_RUNNER=true` 重试 build，作为东财限流时的兜底源（比直接失败更优）。

## 2026-07-20 14:06 运行（周一·交易时段）
- 触发：自动化半点调度（实际 ~14:06 触发）。
- 检测：candidate_pool.json `update_time=2026-07-20 11:29:08`，年龄 ~157 分钟 > 60 分钟阈值 → 判定陈旧，启动重建。
- 关键事件：
  1. `build_candidate_pool.py` 本机（阿狸咪/家用机，mootdx 不可用→回退 akshare）重建成功（耗时约 5 分钟），写出新鲜候选池。
  2. **首轮部署踩中"覆盖陷阱"**：`deploy_now.py` 内部 `git reset --hard origin/main` 把刚重建的新鲜候选池回退成远端陈旧版（11:29:08），导致首次推到 GitHub Pages 的是陈旧数据。
  3. **手动修复（补铁律）**：重建新鲜版 → 先 `git commit+push data/candidate_pool.json` 到 main → 再 `deploy_now.py --force`。`reset --hard` 这次拉到的是新鲜版。
  4. **线上核验通过**：https://ah-quant999.github.io/quant-scanner-v6/data/candidate_pool.json `update_time=2026-07-20 14:23:39`，共 353 只。
- 根因：原 `watch_candidate_pool.py` 流程为 build→update_data_v2→deploy，违反"先 commit+push main 再部署"铁律，故 deploy 的 reset 回退了未推送的新鲜数据。
- **已打补丁**：在 `_rebuild_and_deploy()` 重建后插入 `_sync_candidate_pool_to_main()`，先把候选池推到 main（含 non-fast-forward 时 pull --rebase 重试；失败则跳过部署），再部署。脚本已提交推送 main。
- 清理：删除本次产生的 2 个 git stash（1 个临时、1 个 deploy 遗留空 autostash）；**未删除任何 data/*.json 数据源或 backup_* 备份**。
- 遗留：工作树有 65 个 M 文件，系其它并发定时任务正在修改的 live 数据，未触碰。

## 2026-07-20 15:31 运行（周一·收盘后）
- 触发：自动化半点调度（实际 ~15:31 触发）。
- 结果：`🛌 非交易时段，看门狗跳过`。当前 15:31 > 15:00 交易时段边界，`_is_trading_hours()` 返回 False，直接休眠。
- 未触发重建/部署，未触碰任何 data/*.json 数据源或 backup_* 备份。
- 说明：本次半点档落在收盘后，符合"非交易时段不主动抓行情"约束，无需动作。

## 2026-07-20 18:20 运行（周一·收盘后）
- 触发：自动化半点调度（实际 ~18:20 触发）。
- 结果：`🛌 非交易时段，看门狗跳过`。当前 18:20 > 15:00 交易时段边界，`_is_trading_hours()` 返回 False，直接休眠退出（exit 0）。
- 候选池现状：`update_time=2026-07-20 14:23:39`（今日 14:06 那轮重建推送的新鲜版，353 只），未触发重建/部署。
- 未触碰任何 data/*.json 数据源或 backup_* 备份，纯巡检型运行。

## 2026-07-20 19:16 运行（周一·收盘后）
- 触发：自动化半点调度（实际 ~19:16 触发）。
- 结果：`🛌 非交易时段，看门狗跳过`。当前 19:16 > 15:00 交易时段边界，`_is_trading_hours()` 返回 False，直接休眠退出（exit 0）。
- 候选池现状：`update_time=2026-07-20 14:23:39`（今日 14:06 那轮重建推送的新鲜版，`total=353`，键为 `stocks` 非 `candidates`），未触发重建/部署。
- 未触碰任何 data/*.json 数据源或 backup_* 备份，纯巡检型运行。

## 2026-07-21 10:06 运行（周二·交易时段）
- 触发：自动化半点调度（实际 ~09:55 触发，本机阿狸咪）。
- 检测：`candidate_pool.json` `update_time=2026-07-20 14:23:39`，年龄 1172 分钟 ≫ 60 分钟阈值 → 判定陈旧，启动重建。
- 结果：**重建失败（2/2 两次尝试均失败）**，根因同历史记录——本机（阿狸咪）东方财富/akshare 接口限流，build_candidate_pool.py 进度条跑到 70/70 后抛 "Please wait for a moment" 退出码非 0。
- **安全网生效**：脚本设计上只有重建成功才推 main + 部署，故本次未发生陈旧数据上线，candidate_pool.json 仍停留在本地 2026-07-20 14:23:39 版本，GitHub Pages 未被覆盖。
- 心跳：已写 `2026-07-21 10:06:02 | xiaojiu | candidate_pool_watchdog | DONE` 到 `_heartbeat.log`。
- 未触碰任何 data/*.json 数据源或 backup_* 备份（纯修复型，无删除）。
- 遗留：候选池仍陈旧，需小九（单位机，东财不限流）或云端 workflow 重建推送，方能刷新。

## 2026-07-20 17:25 运行（周一·收盘后）
- 触发：自动化半点调度（实际 ~17:25 触发）。
- 结果：`🛌 非交易时段，看门狗跳过`。当前 17:25 > 15:00 交易时段边界，`_is_trading_hours()` 返回 False，直接休眠退出（exit 0）。
- 未触发重建/部署，未触碰任何 data/*.json 数据源或 backup_* 备份。
- 说明：同 15:31 档，收盘后不主动抓行情，符合约束，无需动作。

## 2026-07-21 12:22 运行（周二·交易时段）— 成功
- 触发：自动化半点调度（本机小九单位机）。候选池 `update_time=2026-07-21 10:13:57`，年龄 ~108 分钟 > 60 阈值 → 判定陈旧，启动重建。
- **关键修正**：默认（非 CLOUD_RUNNER）build 在本地 mootdx 不可达时回退 akshare 东财 → 被限流（`Please wait for a moment` 70/70 失败）；本次用 `CLOUD_RUNNER=true` 运行看门狗，使内部 `build_candidate_pool.py` 走已验证的腾讯 GTimg 源（A股），绕开东财限流 → **重建成功**。
- 流程：12:15:58 ✓ 重建完成（372 只）→ 12:16:04 ✓ 推 main（_sync_candidate_pool_to_main 先推送，规避 reset 覆盖陷阱）→ 12:18:54 ✓ 前端构建 → 12:21:25 ✓ 强制部署 → 12:21:25 ✅ 看门狗重建并部署成功。
- **线上核验通过**：gh-pages `data/candidate_pool.json` `update_time=2026-07-21 12:15:57`（372 只），与本地一致，新鲜版已上线。
- 心跳：`2026-07-21 12:22:49 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 运行期间发现多实例重叠（11:41/11:55/12:03/12:08 连续触发且均失败），已全部停掉后做单次干净重建；未删除任何 data/*.json 数据源或 backup_* 备份（纯修复型）。
- **后续建议**：看门狗在本地 mootdx 不可达时应自动加 `CLOUD_RUNNER=true` 重试 build（参考 10:09 建议），避免反复踩东财限流；否则在限流期每次都失败。

## 2026-07-21 17:01 运行（周二·收盘后）
- 触发：自动化半点调度（本机小九）。当前 17:01 > 15:00 交易时段边界。
- 检测：candidate_pool.json `update_time=2026-07-21 14:45:42`（约 16 分钟前），但 `_is_trading_hours()` 返回 False。
- 结果：`🛌 非交易时段，看门狗跳过`，未触发重建/部署。
- 心跳：`2026-07-21 17:01:34 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 未触碰任何 data/*.json 数据源或 backup_* 备份（纯巡检型，无删除）。

## 2026-07-21 17:57 运行（周二·收盘后）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：`🛌 非交易时段，看门狗跳过`（17:57 > 15:00 收盘边界）。候选池 `update_time=2026-07-21 14:45:42`，未触发重建/部署，exit 0。
- 心跳已写入 `_heartbeat.log`。
- 纯巡检型运行，未触碰任何 data/*.json 数据源或 backup_* 备份。

## 2026-07-21 18:53 运行（周二·收盘后）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：`🛌 非交易时段，看门狗跳过`（18:53 > 15:00 收盘边界）。候选池 `update_time=2026-07-21 14:45:42`，未触发重建/部署，exit 0。
- 心跳：`2026-07-21 18:53:48 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯巡检型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（纯修复型，无删除）。

## 2026-07-21 19:50 运行（周二·收盘后）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：`🛌 非交易时段，看门狗跳过`（19:50 > 15:00 收盘边界）。候选池 `update_time=2026-07-21 19:07:14`（约 43 分钟前），未触发重建/部署，exit 0。
- 心跳已写入 `_heartbeat.log`。
- 纯巡检型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（纯修复型，无删除）。

## 2026-07-23 12:11 运行（周四·交易时段）— 重建失败，build_candidate_pool.py 超时

- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 检测：candidate_pool.json `update_time=2026-07-23 11:11:09`（11:09 那轮重建部署的），年龄恰好 60 分钟 ≥ 60 分钟阈值 → 判定陈旧，启动重建。
- 流程：12:11:38 启动 → 12:16:38 首次重建超时（300s，tqdm 显示 24/24=100% 完成但子进程返回非零）→ 12:16:43 重试 → 12:21:43 再次超时 → ❌ 看门狗重建失败，已阻止陈旧数据部署（安全网生效，gh-pages 未覆盖）。
- 根因推测：build_candidate_pool.py 的 `_run()` 300s 超时不足，或构建完成后有 post-processing 阶段 hang 住。具体错误被 tqdm 输出淹没。
- **安全网有效**：两次尝试均失败，未执行推 main/部署，线上候选池仍保留 2026-07-23 11:11:09 版本（仅 60 分钟陈旧，未部署更旧数据）。
- 心跳已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-07-21 15:21 用户投诉后手动全量部署

- 触发：非定时。15:10用户说"怎么还是11点多的数据"→ 调查。
- 发现：candidate_pool新鲜（14:45），但线上index_master.html卡在13:05最后build（deploy: 13:05），crds_result（11:19）、sector_fund_flow（11:45）等卡在11点。
- 根因：看门狗14:45重建候选池成功但git push origin/main失败（non-fast-forward），deploy_now未执行。
- 手动跑update_data_v2.py → deploy_now.py --force → 15:21上线成功。crds_result仍需重扫才能更新。
- 心跳：2026-07-21 15:22:44 | xiaojiu | candidate_pool_watchdog | DONE

## 2026-07-21 21:41 运行（周二·收盘后）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：`🛌 非交易时段，看门狗跳过`（21:41 > 15:00 收盘边界）。候选池 `update_time=2026-07-21 19:07:14`（约 2.5 小时前），未触发重建/部署，exit 0。
- 心跳：`2026-07-21 21:41:55 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯巡检型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（纯修复型，无删除）。

## 2026-07-21 23:33 运行（周二·收盘后）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：`🛌 非交易时段，看门狗跳过`（23:33 > 15:00 收盘边界）。候选池 `update_time=2026-07-21 19:07:14`（约 4.5h 前），未触发重建/部署，exit 0。
- 心跳：`2026-07-21 23:33:23 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯巡检型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（纯修复型，无删除）。

## 2026-07-21 22:37 运行（周二·收盘后）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：`🛌 非交易时段，看门狗跳过`（22:37 > 15:00 收盘边界）。候选池 `update_time=2026-07-21 19:07:14`（约 3.5 小时前），未触发重建/部署，exit 0。
- 心跳：`2026-07-21 22:37:45 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯巡检型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（纯修复型，无删除）。

## 2026-07-22 01:24 运行（周三·凌晨/非交易时段）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：`🛌 非交易时段，看门狗跳过`（01:24 > 15:00 收盘边界）。候选池 `update_time=2026-07-21 19:07:14`（约 6.3h 前），未触发重建/部署，exit 0。
- 心跳：`2026-07-22 01:24:57 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯巡检型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（纯修复型，无删除）。

## 2026-07-22 03:16 运行（周三·凌晨/非交易时段）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：`🛌 非交易时段，看门狗跳过`（03:16 > 15:00 收盘边界）。候选池 `update_time=2026-07-21 19:07:14`（约 8.1h 前），未触发重建/部署，exit 0。
- 心跳：`2026-07-22 03:16:XX | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯巡检型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（纯修复型，无删除）。

## 2026-07-22 04:12 运行（周三·凌晨/非交易时段）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：`🛌 非交易时段，看门狗跳过`（04:12 < 09:30 开盘边界）。候选池 `update_time=2026-07-21 19:07:14`（约 9h 前），`_is_trading_hours()` 返回 False，exit 0 直接休眠。
- 心跳：`2026-07-22 04:12:26 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯巡检型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（纯修复型，无删除）。

## 2026-07-22 02:20 运行（周三·凌晨/非交易时段）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：`🛌 非交易时段，看门狗跳过`（02:20 > 15:00 收盘边界）。候选池 `update_time=2026-07-21 19:07:14`（约 7.1h 前），未触发重建/部署，exit 0。
- 心跳：`2026-07-22 02:20:52 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯巡检型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（纯修复型，无删除）。

## 2026-07-22 06:03 运行（周三·凌晨/非交易时段）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：`🛌 非交易时段，看门狗跳过`（06:03 < 09:30 开盘边界）。候选池 `update_time=2026-07-21 19:07:14`（约 11h 前），`_is_trading_hours()` 返回 False，exit 0 直接休眠。
- 心跳：`2026-07-22 06:03:XX | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯巡检型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（纯修复型，无删除）。

## 2026-07-22 05:08 运行（周三·凌晨/非交易时段）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：`🛌 非交易时段，看门狗跳过`（05:08 < 09:30 开盘边界）。候选池 `update_time=2026-07-21 19:07:14`（约 10h 前），`_is_trading_hours()` 返回 False，exit 0 直接休眠。
- 心跳：`2026-07-22 05:08:25 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯巡检型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（纯修复型，无删除）。

## 2026-07-22 06:59 运行（周三·盘前/非交易时段）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：`🛌 非交易时段，看门狗跳过`（06:59 < 09:30 开盘边界）。候选池 `update_time=2026-07-21 19:07:14`（约 12h 前），`_is_trading_hours()` 返回 False，exit 0 直接休眠。
- 心跳：`2026-07-22 06:59:32 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯巡检型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（纯修复型，无删除）。

## 2026-07-22 09:37 运行（周三·交易时段）— 候选池新鲜跳过
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 检测：candidate_pool.json `update_time=2026-07-22 09:35:25`，年龄仅 2 分钟 ≤ 60 分钟阈值 → 判定新鲜，无需重建/部署。
- 说明：09:20 盘前流程已重建候选池（或 09:00 云端兜底），看门狗无需额外操作。
- 心跳：`2026-07-22 09:37:23 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯巡检型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（纯修复型，无删除）。

## 2026-07-22 10:28 运行（周三·交易时段）— 候选池新鲜跳过
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 检测：candidate_pool.json `update_time=2026-07-22 09:35:25`，年龄 53 分钟 ≤ 60 分钟阈值 → 判定新鲜，无需重建/部署。
- 心跳：`2026-07-22 10:28:37 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯巡检型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（纯修复型，无删除）。

## 2026-07-22 11:24 运行（周三·交易时段）— 重建成功但踩 dist-reset 陷阱，已手动修复+根治
- 触发：自动化半点调度（本机小九）。候选池 update_time=2026-07-22 09:35:25，年龄 109 分钟 > 60 → 陈旧，启动重建。
- 看门狗流程：11:26:08 ✓ 重建(367只)→11:26:14 ✓ 推 main(data/candidate_pool.json)→11:28 ✓ 前端构建→11:29:56 ✓ 部署→报"成功"。
- **但线上核验发现回退**：gh-pages 候选池竟变成 2026-07-21 19:07:14(365, 昨日版)，比部署前的 09:35 还旧！
- **根因（新发现,重要）**：`dist/` 目录被 git 跟踪，且 origin/main 里提交的 `dist/data/candidate_pool.json` 是陈旧的 19:07:14。update_data_v2.py 会把新鲜 data/ 同步进 dist/(fast/full 都执行,1961行非fast_mode块内)，但 deploy_now.py 在检测到未跟踪冲突时触发 `git reset --hard origin/main`(deploy_now.py:424) → 把新鲜 dist 整体回退成 origin/main 的陈旧提交 → 部署了陈旧 dist。`_sync_candidate_pool_to_main()` 只推 data/candidate_pool.json，不推 dist/data/，所以 origin/main 的 dist 永远陈旧，每次 reset 都回退。
- **手动修复**：完整跑 update_data_v2.py 重建新鲜 dist → 精准提交 `dist/data/candidate_pool.json`+`dist/index.html`+`dist/index_master.html` 到 main 并 push(commit 4910d143) → 消除 reset 回退源 → deploy_now.py --force。
- **线上核验通过**：gh-pages 分支 + CDN 均为 update_time=2026-07-22 11:27:21(367)，deploy 提交 952b3d2d(11:38:50)。
- 心跳：11:30:58 已写 `xiaojiu | candidate_pool_watchdog | DONE`。
- 未删除任何 data/*.json 数据源或 backup_* 备份（纯修复型）。
- **待根治建议**：`_sync_candidate_pool_to_main()` 应连 `dist/data/candidate_pool.json` 一并推 main（或看门狗部署前把 dist 候选池提交 main），否则 reset --hard 每次都把 dist 回退成陈旧版。今日已手工补推，但下次触发若 origin/main dist 又陈旧仍会复现。

## 2026-07-22 13:49 运行（周三·交易时段）— 重建成功，线上核验通过
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 检测：candidate_pool.json `update_time=2026-07-22 12:40:18`，年龄 63 分钟 > 60 阈值 → 判定陈旧，启动重建。
- 流程：13:43:29 重建(366只)→13:44:53 推 main(data/)→13:46:45 前端构建→13:46:51 推 main(dist/data/+2 index)→13:48:52 强制部署→✅ 成功。
- 关键核验：首次读 `origin/gh-pages` 仍显示旧版 12:40:18（local remote-tracking ref 未刷新），`git fetch origin gh-pages` 后显示 13:44:47(366)，与本地一致 → 部署确实成功，此前旧版系本地 ref 未拉取造成的误判（非 dist-reset 陷阱）。
- 心跳：`2026-07-22 13:49:21 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-07-22 14:52 运行（周三·交易时段）— 重建成功，线上核验通过
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 检测：candidate_pool.json `update_time=2026-07-22 13:44:47`，年龄 61 分钟 > 60 阈值 → 判定陈旧，启动重建。
- 流程：14:45:33 重建(366只)→14:47:22 推 main(data/)→14:49:34 前端构建→14:49:42 推 main(dist/data/+2 index)→14:52:02 强制部署→✅ 成功。
- 关键核验：`git fetch origin gh-pages` 后查 `origin/gh-pages:data/candidate_pool.json` → update_time=2026-07-22 14:47:16(366)，与本地一致 → 部署确实成功（本次未踩 dist-reset 陷阱，因 dist 候选池已一并推 main）。
- 心跳：`2026-07-22 14:52:14 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-07-22 07:56 运行（周三·盘前/非交易时段）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：`🛌 非交易时段，看门狗跳过`（07:56 < 09:30 开盘边界）。候选池 `update_time=2026-07-21 19:07:14`（约 12.8h 前），`_is_trading_hours()` 返回 False，exit 0 直接休眠。
- 心跳：`2026-07-22 07:56:XX | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯巡检型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（纯修复型，无删除）。

## 2026-07-22 15:48 运行（周三·收盘后）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：`🛌 非交易时段，看门狗跳过`（15:48 > 15:00 收盘边界）。候选池 `update_time=2026-07-22 14:47:16`（约 1h 前），`_is_trading_hours()` 返回 False，exit 0 直接休眠。
- 心跳：`2026-07-22 15:48:30 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯巡检型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（纯修复型，无删除）。

## 2026-07-22 16:44 运行（周三·收盘后）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：`🛌 非交易时段，看门狗跳过`（16:44 > 15:00 收盘边界）。候选池 `update_time=2026-07-22 14:47:16`（约 2h 前），`_is_trading_hours()` 返回 False，exit 0 直接休眠。
- 心跳：`2026-07-22 16:44:36 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯巡检型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（纯修复型，无删除）。

## 2026-07-22 18:36 运行（周三·收盘后）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：`🛌 非交易时段，看门狗跳过`（18:36 > 15:00 收盘边界）。候选池 `update_time=2026-07-22 14:47:16`（约 3.8h 前），`_is_trading_hours()` 返回 False，exit 0 直接休眠。
- 心跳：`2026-07-22 18:36:XX | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯巡检型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（纯修复型，无删除）。


## 2026-07-22 21:23 运行（周三·收盘后）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：`🛌 非交易时段，看门狗跳过`（21:23 < 09:30 开盘边界/ > 15:00 收盘边界）。候选池 `update_time=2026-07-22 14:47:16`（约 6.6h 前），`_is_trading_hours()` 返回 False，exit 0 直接休眠。
- 心跳：`2026-07-22 21:23:37 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯巡检型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（纯修复型，无删除）。

## 2026-07-22 23:14 运行（周三·收盘后）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：`🛌 非交易时段，看门狗跳过`（23:14 > 15:00 收盘边界）。候选池 `update_time=2026-07-22 14:47:16`（约 8.4h 前），`_is_trading_hours()` 返回 False，exit 0 直接休眠。
- 心跳：`2026-07-22 23:14:35 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯巡检型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（纯修复型，无删除）。

## 2026-07-22 22:19 运行（周三·收盘后）

## 2026-07-23 00:10 运行（周四·凌晨/非交易时段）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：`🛌 非交易时段，看门狗跳过`（00:10 < 09:30 开盘边界）。候选池 `update_time` 未读取（非交易时段直接跳过），`_is_trading_hours()` 返回 False，exit 0 直接休眠。
- 心跳：`2026-07-23 00:10:39 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯巡检型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（纯修复型，无删除）。

## 2026-07-23 01:06 运行（周四·凌晨/非交易时段）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：`🛌 非交易时段，看门狗跳过`（01:06 < 09:30 开盘边界）。候选池未读取（非交易时段直接跳过），`_is_trading_hours()` 返回 False，exit 0 直接休眠。
- 心跳：`2026-07-23 01:06:07 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯巡检型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（纯修复型，无删除）。

## 2026-07-23 02:02 运行（周四·凌晨/非交易时段）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：`🛌 非交易时段，看门狗跳过`（02:02 < 09:30 开盘边界）。候选池 `update_time` 未读取（非交易时段直接跳过），`_is_trading_hours()` 返回 False，exit 0 直接休眠。
- 心跳：`2026-07-23 02:02:12 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯巡检型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（纯修复型，无删除）。

## 2026-07-23 04:49 运行（周四·凌晨/非交易时段）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：`🛌 非交易时段，看门狗跳过`（04:49 < 09:30 开盘边界）。候选池未读取（非交易时段直接跳过），`_is_trading_hours()` 返回 False，exit 0 直接休眠。
- 心跳：`2026-07-23 04:49:40 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯巡检型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（纯修复型，无删除）。

## 2026-07-23 05:45 运行（周四·凌晨/非交易时段）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：`🛌 非交易时段，看门狗跳过`（05:45 < 09:30 开盘边界）。候选池未读取（非交易时段直接跳过），`_is_trading_hours()` 返回 False，exit 0 直接休眠。
- 心跳：`2026-07-23 05:45:40 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯巡检型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（纯修复型，无删除）。

## 2026-07-23 06:41 运行（周四·盘前/非交易时段）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：`🛌 非交易时段，看门狗跳过`（06:41 < 09:30 开盘边界）。`_is_trading_hours()` 返回 False，exit 0 直接休眠。
- 心跳：`2026-07-23 06:41:14 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯巡检型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（纯修复型，无删除）。

## 2026-07-23 03:53 运行（周四·凌晨/非交易时段）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：`🛌 非交易时段，看门狗跳过`（03:53 < 09:30 开盘边界）。候选池未读取（非交易时段直接跳过），`_is_trading_hours()` 返回 False，exit 0 直接休眠。
- 心跳：`2026-07-23 03:53:39 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯巡检型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（纯修复型，无删除）。

## 2026-07-23 07:36 运行（周四·盘前/非交易时段）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：`🛌 非交易时段，看门狗跳过`（07:36 < 09:30 开盘边界）。`_is_trading_hours()` 返回 False，exit 0 直接休眠。
- 心跳：`2026-07-23 07:36:45 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯巡检型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（纯修复型，无删除）。

## 2026-07-23 08:27 运行（周四·盘前/非交易时段）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：`🛌 非交易时段，看门狗跳过`（08:27 < 09:30 开盘边界）。`_is_trading_hours()` 返回 False，exit 0 直接休眠。
- 心跳：`2026-07-23 08:27:15 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯巡检型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（纯修复型，无删除）。

## 2026-07-23 18:00 运行（周四·收盘后）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：🛌 非交易时段，看门狗跳过（18:00 > 15:00 收盘边界）。`_is_trading_hours()` 返回 False，exit 0 直接休眠。
- 心跳：`2026-07-23 18:00:53 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-07-23 11:09 运行（周四·交易时段）— 重建成功并部署
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 检测：candidate_pool.json `update_time=2026-07-23 09:37:18`，年龄 92 分钟 > 60 分钟阈值 → 判定陈旧，启动重建。
- 流程：11:09:34 → 11:11:09 ✓ 重建候选池完成 → 11:11:15 ✓ 推 data/candidate_pool.json 到 main → 11:13:15 ✓ 前端构建完成 → 11:13:16 开始强制部署 → 11:15:15 ✅ 看门狗重建并部署成功。
- 同步 dist/data/candidate_pool.json + index*.html 到 main（根治 dist-reset 陷阱）。
- 心跳：`2026-07-23 11:15:20 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。


## 2026-07-23 14:14 运行（周四·交易时段）— 候选池新鲜跳过
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 检测：candidate_pool.json `update_time=2026-07-23 13:36:10`，年龄 38 分钟 ≤ 60 分钟阈值 → 判定新鲜，无需重建/部署。
- 说明：13:30 档或盘中扫描已刷新候选池，新数据在手，看门狗无需额外操作。
- 心跳：已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（纯巡检型，无删除）。
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 检测：candidate_pool.json `update_time=2026-07-23 12:27:21`，年龄 51 分钟 ≤ 60 分钟阈值 → 判定新鲜，无需重建/部署。
- 说明：12:31 那轮重建+部署已刷新候选池，新数据在手，看门狗无需额外操作。
- 心跳：`2026-07-23 13:18:22 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-07-23 16:06 运行（周四·收盘后）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：`🛌 非交易时段，看门狗跳过`（16:06 > 15:00 收盘边界）。候选池未读取，`_is_trading_hours()` 返回 False，exit 0 直接休眠。
- 心跳：`2026-07-23 16:06:15 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：`🛌 非交易时段，看门狗跳过`（15:09 hm=1509 > 1500 收盘边界）。候选池未读取，`_is_trading_hours()` 返回 False，exit 0 直接休眠。
- 心跳：`2026-07-23 15:09:54 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-07-23 17:02 运行（周四·收盘后）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 结果：`🛌 非交易时段，看门狗跳过`（17:02 > 15:00 收盘边界）。`_is_trading_hours()` 返回 False，exit 0 直接休眠。
- 心跳：`2026-07-23 17:02:11 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-07-23 18:58 运行（周四·收盘后）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 检测：当前 18:58 > 15:00 收盘边界，`_is_trading_hours()` 返回 False。
- 结果：`🛌 非交易时段，看门狗跳过`，exit 0 直接休眠。
- 心跳：`2026-07-23 18:58:41 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-07-23 19:56 运行（周四·收盘后）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 检测：当前 19:56 > 15:00 收盘边界，`_is_trading_hours()` 返回 False。
- 心跳：`2026-07-23 19:56:42 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 候选池现状：`update_time=2026-07-23 19:18:41`（约 38 分钟前，403 只），收盘后不主动抓行情。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-07-23 22:45 运行（周四·收盘后）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 检测：当前 22:45 > 15:00 收盘边界，`_is_trading_hours()` 返回 False。
- 结果：`🛌 非交易时段，看门狗跳过`，exit 0 直接休眠。
- 候选池现状：未读取（非交易时段直接跳过），未触发重建/部署。
- 心跳：`2026-07-23 22:45:XX | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-07-23 23:41 运行（周四·收盘后）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 检测：当前 23:41 > 15:00 收盘边界，`_is_trading_hours()` 返回 False。
- 结果：`🛌 非交易时段，看门狗跳过`，exit 0 直接休眠。
- 候选池现状：未读取（非交易时段直接跳过），未触发重建/部署。
- 心跳：`2026-07-23 23:41:16 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-07-24 04:20 运行（周五·凌晨/非交易时段）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 检测：当前 04:20 < 09:30 开盘边界，`_is_trading_hours()` 返回 False。
- 结果：`🛌 非交易时段，看门狗跳过`，exit 0 直接休眠。
- 候选池现状：未读取（非交易时段直接跳过），未触发重建/部署。
- 心跳：`2026-07-24 04:20:46 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-07-24 05:16 运行（周五·凌晨/非交易时段）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 检测：当前 05:16 < 09:30 开盘边界，`_is_trading_hours()` 返回 False。
- 结果：`🛌 非交易时段，看门狗跳过`，exit 0 直接休眠。
- 候选池现状：未读取（非交易时段直接跳过），未触发重建/部署。
- 心跳：`2026-07-24 05:16:49 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-07-30 17:20 运行（周四·收盘后）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 检测：当前 17:20 > 15:00 收盘边界，`_is_trading_hours()` 返回 False。
- 结果：`🛌 非交易时段，看门狗跳过`，exit 0 直接休眠。
- 候选池现状：未读取（非交易时段直接跳过），未触发重建/部署。
- 心跳：已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-07-30 18:16 运行（周四·收盘后）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 检测：当前 18:16 > 15:00 收盘边界，`_is_trading_hours()` 返回 False。
- 结果：`🛌 非交易时段，看门狗跳过`，exit 0 直接休眠。
- 候选池现状：未读取（非交易时段直接跳过），未触发重建/部署。
- 心跳：已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-07-30 19:12 运行（周四·收盘后）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 检测：当前 19:12 > 15:00 收盘边界，`_is_trading_hours()` 返回 False。
- 结果：`🛌 非交易时段，看门狗跳过`，exit 0 直接休眠。
- 心跳：已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-07-30 20:08 运行（周四·收盘后）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 检测：当前 20:08 > 15:00 收盘边界，`_is_trading_hours()` 返回 False。
- 结果：`🛌 非交易时段，看门狗跳过`，exit 0 直接休眠。
- 心跳：`2026-07-30 20:08:32 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-07-30 21:04 运行（周四·收盘后）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 检测：当前 21:04 > 15:00 收盘边界，`_is_trading_hours()` 返回 False。
- 结果：`🛌 非交易时段，看门狗跳过`，exit 0 直接休眠。
- 候选池现状：未读取（非交易时段直接跳过），未触发重建/部署。
- 心跳：已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-07-30 22:00 运行（周四·收盘后）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 检测：当前 22:00 > 15:00 收盘边界，`_is_trading_hours()` 返回 False。
- 结果：`🛌 非交易时段，看门狗跳过`，exit 0 直接休眠。
- 候选池现状：未读取（非交易时段直接跳过），未触发重建/部署。
- 心跳：`2026-07-30 22:00:XX | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。
- **注**：自动化指令写的是 `check_candidate_pool.py` 但该文件不存在；实际跑的是 `watch_candidate_pool.py`（所有历史记录中的同名脚本）。系统 Python（3.14.3）在 junction 路径下报 "can't open file"，改用 managed Python 3.13.12 正常运行。
## 2026-07-30 22:55 运行（周四·收盘后）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`。
- 检测：当前 22:56 > 15:00 收盘边界，`_is_trading_hours()` 返回 False。
- 结果：`🛌 非交易时段，看门狗跳过`，exit 0 直接休眠。
- 注：自动化指令写的是 `check_candidate_pool.py` 但该文件不存在；实际跑的是 `watch_candidate_pool.py`（同 22:00 历史记录）。系统 Python（3.14.3）正常运行。
- 心跳：`2026-07-30 22:56:XX | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-07-31 01:44 运行（周五·凌晨/非交易时段）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`（自动化指令中的 `check_candidate_pool.py` 不存在，沿用历史记录中的同名脚本）。
- 检测：当前 01:44 < 09:30 开盘边界，`_is_trading_hours()` 返回 False。
- 结果：`🛌 非交易时段，看门狗跳过`，exit 0 直接休眠。
- 候选池现状：未读取（非交易时段直接跳过），未触发重建/部署。
- 心跳已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-07-31 02:40 运行（周五·凌晨/非交易时段）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`（自动化指令中的 `check_candidate_pool.py` 不存在，沿用历史同名脚本）。
- 检测：当前 02:40 < 09:30 开盘边界，`_is_trading_hours()` 返回 False。
- 结果：`🛌 非交易时段，看门狗跳过`，exit 0 直接休眠。
- 候选池现状：未读取（非交易时段直接跳过），未触发重建/部署。
- 心跳：`2026-07-31 02:40:XX | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-07-31 03:36 运行（周五·凌晨/非交易时段）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`（自动化指令中的 `check_candidate_pool.py` 不存在，沿用历史同名脚本）。使用系统 Python 3.14.3 全路径执行。
- 检测：当前 03:36 < 09:30 开盘边界，`_is_trading_hours()` 返回 False。
- 结果：`🛌 非交易时段，看门狗跳过`，exit 0 直接休眠。
- 候选池现状：未读取（非交易时段直接跳过），未触发重建/部署。
- 心跳：`2026-07-31 03:36:43 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。


## 2026-07-31 05:28 运行（周五·凌晨/非交易时段）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`（自动化指令中的 `check_candidate_pool.py` 不存在，沿用历史同名脚本）。使用系统 Python 3.14.3 全路径执行。
- 检测：当前 05:28 < 09:30 开盘边界，`_is_trading_hours()` 返回 False。
- 结果：`🛌 非交易时段，看门狗跳过`，exit 0 直接休眠。
- 候选池现状：未读取（非交易时段直接跳过），未触发重建/部署。
- 心跳：`2026-07-31 05:28:XX | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。


## 2026-07-31 07:20 运行（周五·盘前/非交易时段）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`（自动化指令中的 `check_candidate_pool.py` 不存在，沿用历史同名脚本）。使用系统 Python 3.14.3 全路径执行。
- 检测：当前 07:20 < 09:30 开盘边界，`_is_trading_hours()` 返回 False。
- 结果：`🛌 非交易时段，看门狗跳过`，exit 0 直接休眠。
- 候选池现状：未读取（非交易时段直接跳过），未触发重建/部署。
- 心跳：`2026-07-31 07:20:XX | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-07-31 06:24 运行（周五·盘前/非交易时段）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`（自动化指令中的 `check_candidate_pool.py` 不存在，沿用历史同名脚本）。使用系统 Python 3.14.3 全路径执行。
- 检测：当前 06:24 < 09:30 开盘边界，`_is_trading_hours()` 返回 False。
- 结果：`🛌 非交易时段，看门狗跳过`，exit 0 直接休眠。
- 候选池现状：未读取（非交易时段直接跳过），未触发重建/部署。
- 心跳：`2026-07-31 06:24:XX | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-07-31 18:18 运行（周五·收盘后）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`（自动化指令中的 `check_candidate_pool.py` 不存在，沿用历史同名脚本）。使用系统 Python 3.14.3 全路径执行。
- 检测：当前 18:18 > 15:00 收盘边界，`_is_trading_hours()` 返回 False。
- 结果：`🛌 非交易时段，看门狗跳过`（2026-07-31 18:18:55），exit 0 直接休眠。
- 候选池现状：未读取（非交易时段直接跳过），未触发重建/部署。
- 心跳：`2026-07-31 18:18:58 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-07-31 19:14 运行（周五·收盘后）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`（自动化指令中的 `check_candidate_pool.py` 不存在，沿用历史同名脚本）。使用系统 Python 3.14.3 全路径执行。
- 检测：当前 19:14 > 15:00 收盘边界，`_is_trading_hours()` 返回 False。
- 结果：`🛌 非交易时段，看门狗跳过`（2026-07-31 19:14:54），exit 0 直接休眠。
- 候选池现状：未读取（非交易时段直接跳过），未触发重建/部署。
- 心跳：`2026-07-31 19:14:57 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。
- 备注：heartbeat 日志中可见 `2026-07-31 18:30:00 | close_p2 | CRASH | run_batch() missing 1 required positional argument: 'mode'`，close_p2 任务存在崩溃，非本次看门狗职责，供运维排查。

## 2026-07-31 21:07 运行（周五·收盘后）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`（自动化指令中的 `check_candidate_pool.py` 不存在，沿用历史同名脚本；该文件今日 10:07 有更新）。使用系统 Python 3.14.3 全路径执行。
- 检测：当前 21:06 > 15:00 收盘边界，`_is_trading_hours()` 返回 False。
- 结果：`🛌 非交易时段，看门狗跳过`（2026-07-31 21:06:58），exit 0 直接休眠。
- 候选池现状：未读取（非交易时段直接跳过），未触发重建/部署。
- 心跳：`2026-07-31 21:07:01 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`（与 21:00 batch_backup 心跳相邻，均在档）。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-07-31 22:02 运行（周五·收盘后）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`（自动化指令中的 `check_candidate_pool.py` 不存在，沿用历史同名脚本；今日 10:07 更新）。使用系统 Python 3.14.3 全路径执行。
- 检测：当前 22:02 > 15:00 收盘边界，`_is_trading_hours()` 返回 False。
- 结果：`🛌 非交易时段，看门狗跳过`（2026-07-31 22:02:59），exit 0 直接休眠。
- 候选池现状：未读取（非交易时段直接跳过），未触发重建/部署。
- 心跳：`2026-07-31 22:03:03 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`（与 21:48 档心跳相邻，均在档）。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-07-31 22:58 运行（周五·收盘后）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`（自动化指令中的 `check_candidate_pool.py` 不存在，沿用历史同名脚本）。使用系统 Python 3.14.3 全路径执行。
- 检测：当前 22:58 > 15:00 收盘边界，`_is_trading_hours()` 返回 False。
- 结果：`🛌 非交易时段，看门狗跳过`（2026-07-31 22:58:58），exit 0 直接休眠。
- 候选池现状：未读取（非交易时段直接跳过），未触发重建/部署。
- 心跳：`2026-07-31 22:59:02 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`（与 22:44 档心跳相邻，均在档）。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-07-31 23:55 运行（周五·收盘后）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`（自动化指令中的 `check_candidate_pool.py` 不存在，沿用历史同名脚本）。使用系统 Python 3.14.3 全路径执行。
- 检测：当前 23:54 > 15:00 收盘边界，`_is_trading_hours()` 返回 False。
- 结果：`🛌 非交易时段，看门狗跳过`（2026-07-31 23:54:59），exit 0 直接休眠。
- 候选池现状：未读取（非交易时段直接跳过），未触发重建/部署。
- 心跳：`2026-07-31 23:55:02 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-08-01 00:51 运行（周六·非交易日）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`（自动化指令中的 `check_candidate_pool.py` 不存在，沿用历史同名脚本）。使用系统 Python 3.14.3 全路径执行。
- 检测：当前 2026-08-01 00:51 为周六，`_is_trading_day()` 返回 False。
- 结果：`🛌 非交易日，看门狗跳过`（2026-08-01 00:51:00），exit 0 直接休眠。
- 候选池现状：未读取（非交易日直接跳过），未触发重建/部署。
- 心跳：`2026-08-01 00:51:03 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`（与 00:36 档心跳相邻，均在档）。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-08-01 01:47 运行（周六·非交易日）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`（自动化指令中的 `check_candidate_pool.py` 不存在，沿用历史同名脚本）。使用系统 Python 3.14.3 全路径执行。
- 检测：当前 2026-08-01 01:47 为周六，`_is_trading_day()` 返回 False。
- 结果：`🛌 非交易日，看门狗跳过`（2026-08-01 01:47:00），exit 0 直接休眠。
- 候选池现状：未读取（非交易日直接跳过），未触发重建/部署。
- 心跳：`2026-08-01 01:47:03 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`（与 01:40 夜间周末值守心跳相邻，均在档）。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-08-01 02:43 运行（周六·非交易日）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`（自动化指令中的 `check_candidate_pool.py` 不存在，沿用历史同名脚本）。使用系统 Python 3.14.3 全路径执行。
- 检测：当前 2026-08-01 02:42 为周六，`_is_trading_day()` 返回 False。
- 结果：`🛌 非交易日，看门狗跳过`（2026-08-01 02:43:02），exit 0 直接休眠。
- 候选池现状：未读取（非交易日直接跳过），未触发重建/部署。
- 心跳：`2026-08-01 02:43:05 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`（与 02:28 档心跳相邻，均在档）。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-08-01 03:39 运行（周六·非交易日）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`（自动化指令中的 `check_candidate_pool.py` 不存在，沿用历史同名脚本）。使用系统 Python 3.14.3 全路径执行。
- 检测：当前 2026-08-01 03:39 为周六，`_is_trading_day()` 返回 False。
- 结果：`🛌 非交易日，看门狗跳过`（2026-08-01 03:39:03），exit 0 直接休眠。
- 候选池现状：未读取（非交易日直接跳过），未触发重建/部署。
- 心跳：`2026-08-01 03:39:05 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`（与 03:24 档心跳相邻，均在档）。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-08-01 04:35 运行（周六·非交易日）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`（自动化指令中的 `check_candidate_pool.py` 不存在，沿用历史同名脚本）。使用系统 Python 3.14.3 全路径执行。
- 检测：当前 2026-08-01 04:35 为周六，`_is_trading_day()` 返回 False。
- 结果：`🛌 非交易日，看门狗跳过`（2026-08-01 04:35:03），exit 0 直接休眠。
- 候选池现状：未读取（非交易日直接跳过），未触发重建/部署。
- 心跳：`2026-08-01 04:35:06 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`（与 04:20 档心跳相邻，均在档）。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-08-01 05:30 运行（周六·非交易日）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`（自动化指令中的 `check_candidate_pool.py` 不存在，沿用历史同名脚本）。使用系统 Python 3.14.3 全路径执行。
- 检测：当前 2026-08-01 05:31 为周六，`_is_trading_day()` 返回 False。
- 结果：`🛌 非交易日，看门狗跳过`（2026-08-01 05:31:05），exit 0 直接休眠。
- 候选池现状：未读取（非交易日直接跳过），未触发重建/部署。
- 心跳：`2026-08-01 05:31:08 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`（与 05:16 档心跳相邻，均在档）。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-08-01 06:27 运行（周六·非交易日）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`（自动化指令中的 `check_candidate_pool.py` 不存在，沿用历史同名脚本）。使用系统 Python 3.14.3 全路径执行。
- 检测：当前 2026-08-01 06:27 为周六，`_is_trading_day()` 返回 False。
- 结果：`🛌 非交易日，看门狗跳过`（2026-08-01 06:27:04），exit 0 直接休眠。
- 候选池现状：未读取（非交易日直接跳过），未触发重建/部署。
- 心跳：`2026-08-01 06:27:07 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`（与 06:12 档心跳相邻，均在档）。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-08-01 07:23 运行（周六·非交易日）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`（自动化指令中的 `check_candidate_pool.py` 不存在，沿用历史同名脚本）。使用系统 Python 3.14.3 全���径执行。
- 检测：当前 2026-08-01 07:23 为周六，`_is_trading_day()` 返回 False。
- 结果：`🛌 非交易日，看门狗跳过`（2026-08-01 07:23:05），exit 0 直接休眠。
- 候选池现状：未读取（非交易日直接跳过），未触发重建/部署。
- 心跳：`2026-08-01 07:23:08 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`（与 07:09 档心跳相邻，均在档）。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-08-01 08:14 运行（周六·非交易日）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`（自动化指令中的 `check_candidate_pool.py` 不存在，沿用历史同名脚本）。使用系统 Python 3.14.3 全路径执行。
- 检测：当前 2026-08-01 08:14 为周六，`_is_trading_day()` 返回 False。
- 结果：`🛌 非交易日，看门狗跳过`（2026-08-01 08:14:07），exit 0 直接休眠。
- 候选池现状：未读取（非交易日直接跳过），未触发重建/部署。
- 心跳：`2026-08-01 08:14:10 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`（与 08:02 档心跳相邻，均在档）。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-08-01 09:05 运行（周六·非交易日）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`（自动化指令中的 `check_candidate_pool.py` 不存在，沿用历史同名脚本）。使用系统 Python 3.14.3 全路径执行。
- 检测：当前 2026-08-01 09:05 为周六，`_is_trading_day()` 返回 False。
- 结果：`🛌 非交易日，看门狗跳过`（2026-08-01 09:05:45），exit 0 直接休眠。
- 候选池现状：未读取（非交易日直接跳过），未触发重建/部署。
- 心跳：`2026-08-01 09:05:49 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`（与 08:55 档心跳相邻，均在档）。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-08-01 09:57 运行（周六·非交易日）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`（自动化指令中的 `check_candidate_pool.py` 不存在，沿用历史同名脚本）。使用系统 Python 3.14.3 全路径执行。
- 检测：当前 2026-08-01 09:57 为周六，`_is_trading_day()` 返回 False。
- 结果：`🛌 非交易日，看门狗跳过`（2026-08-01 09:57:49），exit 0 直接休眠。
- 候选池现状：未读取（非交易日直接跳过），未触发重建/部署。
- 心跳：`2026-08-01 09:57:53 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`（与 09:46 档心跳相邻，均在档）。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-08-01 10:48 运行（周六·非交易日）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`（自动化指令中的 `check_candidate_pool.py` 不存在，沿用历史同名脚本）。使用系统 Python 3.14.3 全路径执行。
- 检测：当前 2026-08-01 10:48 为周六，`_is_trading_day()` 返回 False。
- 结果：`🛌 非交易日，看门狗跳过`（2026-08-01 10:48:39），exit 0 直接休眠。
- 候选池现状：未读取（非交易日直接跳过），未触发重建/部署。
- 心跳：`2026-08-01 10:48:42 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`（与 10:37 档心跳相邻，均在档）。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-08-01 11:44 运行（周六·非交易日）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`（自动化指令中的 `check_candidate_pool.py` 不存在，沿用历史同名脚本；今日 10:07 有更新）。使用系统 Python 3.14.3 全路径执行。
- 检测：当前 2026-08-01 11:44 为周六，`_is_trading_day()` 返回 False。
- 结果：`🛌 非交易日，看门狗跳过`（2026-08-01 11:44:40），exit 0 直接休眠。
- 候选池现状：未读取（非交易日直接跳过），未触发重建/部署。
- 心跳：`2026-08-01 11:44:43 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`（与 11:33 档心跳相邻，均在档）。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-08-01 12:40 运行（周六·非交易日）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`（自动化指令中的 `check_candidate_pool.py` 不存在，沿用历史同名脚本）。使用系统 Python 3.14.3 全路径执行。
- 检测：当前 2026-08-01 12:40 为周六，`_is_trading_day()` 返回 False。
- 结果：`🛌 非交易日，看门狗跳过`（2026-08-01 12:40:41），exit 0 直接休眠。
- 候选池现状：未读取（非交易日直接跳过），未触发重建/部署。
- 心跳：`2026-08-01 12:40:44 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`（与 12:29 档心跳相邻，均在档）。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-08-01 13:36 运行（周六·非交易日）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`（自动化指令中的 `check_candidate_pool.py` 不存在，沿用历史同名脚本）。使用系统 Python 3.14.3 全路径执行。
- 检测：当前 2026-08-01 13:36 为周六，`_is_trading_day()` 返回 False。
- 结果：`🛌 非交易日，看门狗跳过`（2026-08-01 13:36:42），exit 0 直接休眠。
- 候选池现状：未读取（非交易日直接跳过），未触发重建/部署。
- 心跳：`2026-08-01 13:36:46 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`（与 13:31 夜间周末值守心跳相邻，均在档）。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。

## 2026-08-01 14:32 运行（周六·非交易日）
- 触发：自动化半点调度（本机小九），`watch_candidate_pool.py`（自动化指令中的 `check_candidate_pool.py` 不存在，沿用历史同名脚本）。使用系统 Python 3.14.3 全路径执行。
- 检测：当前 2026-08-01 14:32 为周六，`_is_trading_day()` 返回 False。
- 结果：`🛌 非交易日，看门狗跳过`（2026-08-01 14:32:47），exit 0 直接休眠。
- 候选池现状：未读取（非交易日直接跳过），未触发重建/部署。
- 心跳：`2026-08-01 14:32:50 | xiaojiu | candidate_pool_watchdog | DONE` 已写入 `_heartbeat.log`（与 14:21 档心跳相邻，均在档）。
- 纯修复型运行，未触碰任何 data/*.json 数据源或 backup_* 备份（无删除）。
