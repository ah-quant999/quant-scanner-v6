# 收盘二段检查补跑部署 — 执行记录

## 2026-07-25 19:05
- 判定：周六（周末），非交易日 → 跳过退出，未执行任何命令。

## 2026-07-24 19:05
- 判定：周五交易日，执行三步兜底
- Steps:
  1. `batch_update.py close_p2` — ✅ 23/23 全部通过 (7m 18s)
  2. `update_data_v2.py` — ✅ 数据块注入成功 (1m 51s)
  3. `deploy_now.py --force` — ✅ 部署成功，224 files, build stamp 20260724191228
- gh-pages: ade3282 (forced update)
- 心跳已上报到 origin/main ✅

## 2026-07-22 19:05
- 判定：周三交易日，执行三步兜底
- Steps:
  1. `batch_update.py close_p2` — fetch_lhb ✅ (119.9s), build_candidate_pool ✅ (238.3s), scanner.py full ❌ 超时挂死(10min+)
  2. `update_data_v2.py` — 宏观数据采集完成(PMI/CPI/PPI/USDCNH/DXY)，后续写文件阶段挂死，终止
  3. `deploy_now.py --force` — 首次因未设 GIT_SSH_COMMAND 卡死; 重设后 ✅ 部署成功
- 部署结果：97 files, build stamp 20260722192306
- ⚠️ scanner.py full 挂死，候选池扫描未完成 → 金股池数据依赖旧扫描
- 线上：https://ah-quant999.github.io/quant-scanner-v6/ ✅

## 2026-07-19 19:00
- 判定：星期日（周末），非交易日 → 跳过退出，未执行任何命令。

## 2026-07-17 19:05
- 判定：周五交易日，所有4个数据文件均已更新到今天（17:42-17:47）
- 结果：跳过 batch_close_p2 / update_data_v2，直接执行 deploy_now.py --force
- ⚠️ 小九（单位机）已在 ~18:29 部署，origin/main 领先本地
- 本地 lock 提交与远端冲突，脚本自动安全跳过（他机持锁）
- 线上 gh-pages 已是最新 ✅

## 2026-07-14 18:35
- 判定：周二交易日，所有4个数据文件均已更新到今天（07-14）
- 结果：跳过 batch_close_p2 / update_data_v2，直接执行 deploy_now.py --force
- ⚠️ PowerShell 找不到 git → 改用 Git Bash 重跑
- 部署成功：84 files, build stamp 20260714183242
- 线上：https://ah-quant999.github.io/quant-scanner-v6/ ✅

## 2026-07-12 18:30
- 判定：星期日（周末），非交易日 → 跳过退出，未执行任何命令。

## 2026-07-11 18:30
- 判定：星期六（周末），非交易日 → 跳过退出，未执行任何命令。

## 2026-07-10 18:30
- 判定：周五交易日，所有4个数据文件均已更新到今天（18:26-18:29）
- 结果：跳过 batch_update / update_data_v2，直接执行 deploy_now.py --force
- 首次失败：non-fast-forward（双机同步冲突，其他机器已抢锁）
- 恢复：git pull --rebase origin main 后重试成功
- 部署：https://ah-quant999.github.io/quant-scanner-v6/ ✅（77 files, 18:31 build stamp）
