# 全时段健康监控执行记录

## 2026-07-23 17:58 (:00 档)
- **交易日**: 是 (Thursday)
- **pre_market_cloud_failover 状态**: OK
- **云端 build stamp**: 20260723174736（11 分钟前）
- **cloud_ok**: true, **elapsed_min**: 11.4
- **判定**: 云端 75 分钟内成功部署，本机无需补跑
- **心跳已写入**: _heartbeat.log

## 2026-07-23 18:55 (:00 档) ⚠️ 误报
- **交易日**: 是 (Thursday)
- **pre_market_cloud_failover 状态**: FAILED（假阳性）
- **根因**: `git fetch origin gh-pages` 因 SSH 连接 GitHub 失败 → 无法获取 build stamp → 被 _decide_by_schedule 判为 cloud_ok=false → 触发本机补跑 → build_candidate_pool 超时(-1)
- **但实际云端正常**: 网站在线可查 build stamp=**20260723185622**（约 3 分钟前，18:31 云部署成功推送）
- **真实情况**: 云端 75 分钟内有成功部署（距 18:56:22 的 build 仅 ~3min），无需补跑
- **问题**: git remote 为 SSH (`git@github.com:...`)，本机 SSH 无可用 key/agent，导致 fetch 永久失败
- **建议**: 增加 HTTPS 回退 remote，或修复 SSH key 配置
- **心跳已写入**: _heartbeat.log

## 2026-07-23 19:57 (:00 档)
- **交易日**: 是 (Thursday)
- **pre_market_cloud_failover 状态**: OK
- **云端 build stamp**: 20260723193958（17.5 分钟前）
- **cloud_ok**: true, **elapsed_min**: 17.5
- **判定**: 云端 75 分钟内成功部署，本机无需补跑
- **备注**: API 因无 GitHub token 降级为时刻表判断，但 build stamp 新鲜，可信
- **心跳已写入**: _heartbeat.log

## 2026-07-23 20:54 (:00 档)
- **交易日**: 是 (Thursday)
- **pre_market_cloud_failover 状态**: OK
- **云端 build stamp**: 20260723203007（24.1 分钟前）
- **cloud_ok**: true, **elapsed_min**: 24.1
- **判定**: 云端 24 分钟内有成功部署，本机无需补跑
- **备注**: API 因无 GitHub token 降级为时刻表判断，build stamp 新鲜，可信
- **心跳已写入**: _heartbeat.log

## 2026-07-23 22:53 (:00 档)
- **交易日**: 是 (Thursday)
- **pre_market_cloud_failover 状态**: OK
- **云端 build stamp**: 20260723224641（7.1 分钟前）
- **cloud_ok**: true, **elapsed_min**: 7.1
- **判定**: 云端 75 分钟内成功部署，本机无需补跑
- **备注**: API 因无 GitHub token 降级为时刻表判断，build stamp 新鲜，可信
- **心跳已写入**: _heartbeat.log

## 2026-07-23 21:50 (:00 档) ⚠️ 假阳性
- **交易日**: 是 (Thursday)
- **pre_market_cloud_failover 状态**: FAILED（假阳性）
- **根因**: 脚本用 `git show origin/gh-pages:index.html` 提取 build stamp，但 gh-pages 分支的 index.html 在 `dist/index.html`（非根路径）→ 提取失败 → cloud_ok=false 错误触发补跑 → build_candidate_pool 超时(-1)
- **但实际云端正常**: 网站 HTTP 200，build stamp=**20260723213816**（~12 min 前）
- **真实情况**: 云端 12 分钟内有成功部署，无需补跑
- **这是同一个 bug 的另一个表现**: 18:55 是 SSH 不可用，这次是路径错误。脚本需要修复 `git show` 路径或改用 HTTP 检查 live site
- **心跳已写入**: _heartbeat.log

## 2026-07-24 01:47 (:00 档)
- **交易日**: 是 (Friday)
- **pre_market_cloud_failover 状态**: OK
- **云端 build stamp**: 20260724010402（43.2 分钟前）
- **cloud_ok**: true, **elapsed_min**: 43.2
- **判定**: 云端 43 分钟内有成功部署（距 75min 阈值还很充裕），本机无需补跑
- **备注**: 当前凌晨 01:47，为隔夜时段，云端最后成功部署在 01:04（21:00 备份/清洗类定时任务产物）
- **心跳已写入**: _heartbeat.log

## 2026-07-24 03:40 (:00 ���)
- **交易日**: 是 (Friday)
- **pre_market_cloud_failover 状态**: OK
- **云端 build stamp**: 20260724021148（88 分钟前）
- **cloud_ok**: true, **elapsed_min**: 88.0
- **判定**: 云端最后部署 02:11，虽已超 75min，但当前凌晨隔夜安静期，脚本判定 OK 无需补跑
- **备注**: API 降级（无 GitHub token），按时刻表判断；首个计划部署在 09:00，等待盘前
- **心跳已写入**: _heartbeat.log

## 2026-07-24 04:36 (:00 档)
- **交易日**: 是 (Friday)
- **pre_market_cloud_failover 状态**: OK
- **云端 build stamp**: 20260724042354（12.5 分钟前）
- **cloud_ok**: true, **elapsed_min**: 12.5
- **判定**: 云端 12.5 分钟内有成功部署（02:11→04:23 有新部署），本机无需补跑
- **备注**: 凌晨隔夜时段，04:23 有额外部署产生新 build，距阈值非常充裕
- **心跳已写入**: _heartbeat.log

## 2026-07-24 06:29 (:00 档)
- **交易日**: 是 (Friday)
- **pre_market_cloud_failover 状态**: OK
- **云端 build stamp**: 20260724053045（58.6 分钟前）
- **cloud_ok**: true, **elapsed_min**: 58.6
- **判定**: 云端 58.6 分钟内有成功部署（05:30），距 75min 阈值还有 16.4 分钟余量，本机无需补跑
- **备注**: API 降级（无 GitHub token），按时刻表判断；当前 06:29 盘前安静期，首个计划部署在 09:00
- **心跳已写入**: _heartbeat.log

## 2026-07-24 07:26 (:00 档)
- **交易日**: 是 (Friday)
- **pre_market_cloud_failover 状态**: OK
- **云端 build stamp**: 20260724063726（48.4 分钟前）
- **cloud_ok**: true, **elapsed_min**: 48.4
- **判定**: 云端 48.4 分钟内有成功部署（06:37），距 75min 阈值充裕，本机无需补跑
- **备注**: API 降级（无 GitHub token），按时刻表判断；当前 07:26 盘前安静期，首个计划部署在 09:00，等待盘前
- **心跳已写入**: _heartbeat.log
