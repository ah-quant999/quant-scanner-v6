# 小九-盘中刷新部署 11:46 — 执行历史

## 2026-07-20 11:46 执行（实际 11:42 启动）
- git pull --rebase：无冲突
- run_intraday_scan.py --skip-standalone：10 步全部成功（scanner watch / 涨跌家数 / 盘中NT / 概念排行 / 板块资金 / ETF资金 / 市场快报 / 成交历史 / 两融）
- update_data_v2.py：build-stamp 20260720115133，JS 语法 0 错误；冒烟测试 2 个括号误报（非语法错误，已继续）
- deploy_now.py --force：推送 93 文件，build-stamp 20260720115236，主站↔独立页同源同戳校验通过，心跳 xiaojiu 上报成功
- 线上验证：标题 `九宝量化 v6.0 (20260720115236)` = 今日 11:52:36，CDN 已刷新 ✅

## 2026-07-21 11:46 执行（实际 11:41 启动）
- git pull --rebase：已是最新（PULL_RC=0）
- run_intraday_scan.py --skip-standalone：9 步全部成功（scanner watch / 涨跌家数 / 盘中NT / 概念排行 / 板块资金 / ETF资金 / 市场快报 / 成交历史 / 两融），SCAN_RC=0
- update_data_v2.py：build-stamp 20260721115026，JS 语法 0 错误；冒烟测试 2 个括号误报（非语法错误，已继续）
- deploy_now.py --force：推送 93 文件，build-stamp 20260721115119，主站↔独立页同源同戳校验通过，心跳 xiaojiu 上报成功
- 心跳：_heartbeat.log 追加 `2026-07-21 11:52:35 | xiaojiu | intraday_11_46 | DONE`
- 线上验证：标题 `九宝量化 v6.0 (20260721115119)` = 今日 11:51:19，运维看板 部署:07-21 11:51、数据正确✓/新鲜度✓/构建✓，CDN 已刷新 ✅

## 2026-07-23 11:46 执行（实际 11:41 启动）
- git pull：初次 `git pull --rebase` RC=128（工作树脏，data/dist 有改动）→ 改用 `git_safe_sync.py` safe_pull -> OK（铁律：禁手写 stash，统一走 safe_pull）
- run_intraday_scan.py --skip-standalone：9 步全部成功（scanner watch/涨跌家数/盘中NT/概念排行/板块资金/ETF资金/市场快报/成交历史/两融余额），SCAN_RC=0，耗时约 12 分钟（比往日长，但各步数据文件时间戳持续推进无卡死，属正常）；「✅ 全部步骤成功」
- update_data_v2.py：UPDATE_RC=0，build-stamp 20260723120018，JS 语法 0 错误（8 脚本块）；冒烟测试 4 个括号误报（非语法错误，已继续）；index.html+index_master.html 4,311,126 字符；build-stamp meta placeholder 未找到告警（不致命）
- deploy_now.py --force：**DEPLOY_RC=1 假失败**！根因=推送阶段 github.com **端口22/443 双双超时**（网络闪断），deploy 的 SSH ls-remote 校验超时→误报「远程 gh-pages 未更新」。**实际推送已成功**：重试 HTTPS ls-remote 得 gh-pages HEAD=9a490d33c0dd（正是 deploy 声称"未出现"的 head_sha），git fetch gh-pages 后 `git show FETCH_HEAD:index.html` 标题=`九宝量化 v6.0 (20260723120018)`、candidate_pool updated_at=2026-07-23 11:11:09，确认落地。**教训**：deploy RC≠0 时务必用 HTTPS ls-remote/fetch 核验 origin/gh-pages 真实 HEAD，勿轻信 RC。
- 心跳：_heartbeat.log 追加 `2026-07-23 12:04:13 | xiaojiu | intraday_11_46 | DONE`
- 线上验证：标题 `九宝量化 v6.0 (20260723120018)` = 今日 12:00:18，运维看板 部署:07-23 12:00、数据正确✓/新鲜度✓/构建✓，盘中数据源（盘中监控11:46:22/概念11:50:01/异动11:54:16/板块资金11:50/ETF11:51/成交额11:54/两融11:54）均显示「刚刚」，CDN 已刷新 ✅

## 2026-07-22 11:46 执行（实际 11:41 启动）
- git pull --rebase：已是最新（PULL_RC=0）
- run_intraday_scan.py --skip-standalone：9 步全部成功（watch / 涨跌家数 / 盘中NT / 概念排行 / 板块资金 / ETF资金 / 市场快报 / 成交历史 / 两融余额），SCAN_RC=0；watch_result 11:44:58、sh_sz 11:51:06、nt 11:50:11(二次)、concept 11:49:29、sector 11:49:44、margin 11:51:09、market_alerts 11:51:04 均已落盘
- update_data_v2.py：build-stamp 20260722115435，JS 语法 0 错误（8 脚本块）；冒烟测试 4 个括号误报（非语法错误，已继续）；宏观刷新两遍（OMO/DXY eastmoney/Binance/CoinGecko 失败走 Sina 兜底，不致命）；batch_update 同步 macro_data 等；dist/index*.html 2,872,870 字符已写、data/*.json+静态资源已同步
- deploy_now.py --force：gh-pages 推送 631d6645 deploy:2026-07-22 11:55（origin/gh-pages 已 fetch 确认），main 同步提交 b1d69fc1 auto:source sync 11:55；后台任务 ID 解析失败但进程 17856 已退出、远端已落地
- 心跳：_heartbeat.log 追加 `2026-07-22 11:57:00 | xiaojiu | intraday_11_46 | DONE`
- 线上验证：标题 `九宝量化 v6.0 (20260722115557)` = 今日 11:55:57，运维看板 部署:07-22 11:55、数据正确✓/新鲜度✓/构建✓，盘中数据源均显示「刚刚」，CDN 已刷新 ✅
