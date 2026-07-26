# 九宝量化-盘中扫描补充 09:47

## 2026-07-12 (周日)
- 执行 `python run_intraday_scan.py`，耗时 ~0.6s，无报错。
- 输出：`⏭️ 非交易日（周末），盘中扫描跳过`。脚本正确识别周末并跳过，属正常设计。
- 无需修复、无需重跑。

## 2026-07-13 (周一)
- 执行 `python run_intraday_scan.py`，耗时 ~8m3s，整体 **exit 0（成功）**。
- 全部盘中数据步骤 ✅（scanner watch / 涨跌家数 / 盘中数据NT / 概念排行 / 板块资金 / ETF资金 / 市场快报 / 成交历史 / 两融余额）。
- 末尾自动部署步骤被 `deploy_now.py` 以 **return 2（被锁跳过，非真错误）** 跳过：`git push origin main` 收到 non-fast-forward 拒绝 → 判定「小九已持部署锁」。deploy_now.py 当场确认「线上 gh-pages 最近更新于 6 分钟前」。
- 根因：双机部署锁设计——工作日小九（单位机，盘中早1分钟）持锁部署，阿狸咪部署被跳过属预期；且阿狸咪本地 main 落后于 origin/main、deploy_now 只 fetch 不 pull，推送恒 non-fast-forward。
- 处置：非代码 bug，无需修复；重跑同命令只会再扫 8 分钟并同样跳过，故未重跑。站点由小九在锁内已更新上线。
- 诊断过程中为定位根因曾单独运行 refresh_standalone_and_deploy.py / deploy_now.py --force 抓取完整报错（仅诊断，未改任何脚本）。
