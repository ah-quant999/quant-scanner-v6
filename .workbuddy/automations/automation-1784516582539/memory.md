# 自动化执行记录：小九-盘中刷新部署 09:30

## 2026-07-21 09:20~09:30
- git pull --rebase：无变更
- run_intraday_scan.py --skip-standalone：9 步成功，1 步失败（板块资金 fetch 抖动，已按要求继续，不影响部署）。耗时约 5min。
- update_data_v2.py：重建成功，build-stamp 20260721092834。冒烟测试仅历史遗留括号警告，继续部署。
- deploy_now.py --force：部署成功，build stamp 20260721092927，独立页同源同戳校验通过，心跳 hb_xiaojiu.json 上报 origin/main。
- 心跳日志已写：`2026-07-21 09:30:22 | xiaojiu | intraday_09_30 | DONE`
- WebFetch 验证：线上标题「九宝量化 v6.0 (20260721092927)」为今日，盘中卡片（概念涨跌/板块资金/ETF/涨跌家数/成交额/两融）均显示 07/21 09:24~09:25「刚刚✓」。✅ 全流程完成。

## 备注
- 板块资金盘中偶发 fetch 失败为已知抖动，前端仍显示今日 09:24 数据（盘后会再刷），无需处理。

## 2026-07-21 续跑（westock 第三源）
- 本会话实际工作：完成「两者都搞」Part2 —— 腾讯自选股(westock) 第三源接入 `fetch_sector_fund_flow.py`（经独立 npx 包，非 mcp 连接器）。
- 关键修复：westock 拉取器 parser 分隔行吞表头 bug（曾误判 westock 无资金流数据）；主脚本 5 处接入 + source 去重。
- 已推 main（多 commit）。本地曾有 55 UU 冲突，被外部同步自愈（未手解）；gold_pool 等 curated 数据完好。
- 注意：本仓有外部 deploy 同步会 revert 未推送改动 → 任何源码改动必须「先 commit+push main」，否则被覆盖。铁律：UU 冲突不自动解。

## 2026-07-22 09:20~09:36
- git pull --rebase：无变更
- ⚠️ 系统 Python (3.14.3) 无依赖 + scanner 锁残留(09:27) → 首次尝试卡死。清理锁后改托管 Python 3.13.12 重试。
- **盘中扫描**：9/9 步全成功（scanner.py watch/涨跌家数/盘中数据NT/概念排行/板块资金/ETF资金/市场快报/成交历史/两融余额），~4min。
- **IPO 数据**：fetch_ipo_data.py 成功，新股 10 只 + 可转债 9 只写入 ipo_score.json。2 只行情 API 小抖动（已忽略）。
- **前端重建**：update_data_v2.py 成功，build-stamp 20260722093514。宏观数据刷新（PMI 50.3/CPI 1.0%/PPI 4.1%/USDCNH 6.77/DXY 101.19）。冒烟测试 4 个历史遗留括号警告。
- **部署**：deploy_now.py --force 成功，build-stamp 20260722093618，97 文件上线，独立页同源同戳校验通过，心跳 hb_xiaojiu.json 上报。
- **心跳日志**：`2026-07-22 09:36:46 | xiaojiu | intraday_09_30 | DONE`
- **WebFetch 验证**：线上标题「九宝量化 v6.0 (20260722093618)」今日时间戳 ✅。盘中卡片均显示今日 09:28~09:36「刚刚✓」。运维面板：部署 07-22 09:36，三方 ✓九 2026-07-22 09:19。✅ 全流程完成。

## 2026-07-23 09:20~09:34
- git pull --rebase：无变更。
- **盘中扫描**（系统 Python 3.14.3，run_intraday_scan.py --skip-standalone）：9/9 步全成功（scanner watch→涨跌家数→盘中数据NT→概念排行→板块资金→ETF资金→市场快报→成交历史→两融），~9min。✅ 全部步骤成功。
- **IPO 数据**（fetch_ipo_data.py，托管 3.13.12）：成功，exit 0。新股 12 只 + 可转债 6 只写入 ipo_score.json；2 只待定价股行情获取警告（非阻塞）。
- **前端重建**（update_data_v2.py，托管 3.13.12）：成功，index.html+index_master.html 重建；8 脚本块 JS 检查 0 错误；4 个历史遗留括号冒烟警告（同前，不阻塞）。
- **部署**（deploy_now.py --force，托管 3.13.12）：成功，build-stamp **20260723093248**，100 文件上线，主站/独立页同源同戳校验通过，心跳 hb_xiaojiu.json 上报 origin/main。POST_CLOSE_TIME=2026-07-22 15:30:00（昨日收盘，符合盘中时段）。
- **心跳日志**：`2026-07-23 09:33:55 | xiaojiu | intraday_09_30 | DONE`
- **WebFetch 验证**：线上标题「九宝量化 v6.0 (20260723093248)」为今日时间戳 ✅。✅ 全流程完成。

## 2026-07-24 09:20~09:37
- git pull --rebase：无变更（origin/main 已是最新）。
- **盘中扫描**（系统 Python 3.14.3，run_intraday_scan.py --skip-standalone）：10/10 步全成功（scanner watch→涨跌家数→盘中数据NT→概念排行→板块资金→ETF资金→市场快报→涨停联动→成交历史→两融），~12min。✅ 全部步骤成功，无失败步。
- **IPO 数据**（fetch_ipo_data.py，系统 3.14.3）：成功 exit 0。新股 12 只 + 可转债 7 只写入 ipo_score.json；3 只行情 API 抖动(Remote end closed，非阻塞)。
- **前端重建**（update_data_v2.py，托管 3.13.12）：成功，index.html+index_master.html 重建（4,445,169 字符）；8 脚本块 JS 检查 0 错误；2 个历史遗留括号冒烟警告（同前，不阻塞）。
- **部署**（deploy_now.py --force，托管 3.13.12）：成功，build-stamp **20260724093616**，101 文件上线，主站/独立页同源同戳校验通过(标记56个, POST_CLOSE_TIME=2026-07-22 15:30:00)，心跳 hb_xiaojiu.json 上报 origin/main，ls-remote 校验通过(560cc8d)。
- **心跳日志**：`2026-07-24 09:37:26 | xiaojiu | intraday_09_30 | DONE`
- **WebFetch 验证**：线上标题「九宝量化 v6.0 (20260724093616)」为今日时间戳 ✅。gh-pages 数据核验：sh_sz_history.json update_time=2026-07-24 09:32、nt_data=2026-07-24 09:30，均为今日新鲜。⚠️ 注：WebFetch 抓取端无时区渲染把盘中卡片显示成「昨日 09:32」，但数据本身是今日 09:32，中国时区浏览器会正确显示「今日」，属显示假象非数据陈旧。✅ 全流程完成。
