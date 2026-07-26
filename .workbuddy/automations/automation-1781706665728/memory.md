# 自动化执行日志 — 九宝量化-盘中15:30

## 2026-07-10 15:25
- 命令: `batch_update.py post_close`
- 结果: 10/10 全部成功，零失败
- 耗时: ~6分30秒
- 详情: scanner(1.7s) → sector_fund_flow(65.1s) → concept_ranking(25.7s) → market_alerts(48.2s) → sh_sz_history(1.0s) → up_down_stats(82.0s) → update_data_v2(153.3s) → refresh_standalone(0.5s) → sync_check(10.9s) → deploy(7.2s)

## 2026-07-11 15:25
- 命令: `batch_update.py post_close`
- 结果: 10/10 全部成功，零失败
- 耗时: ~7分40秒
- 详情: code_sync(6.2s) → scanner(1.3s) → sector_fund_flow(58.3s) → concept_ranking(26.8s) → market_alerts(48.9s) → sh_sz_history(1.1s) → up_down_stats(81.3s) → update_data_v2(149.9s) → refresh_standalone(0.6s) → sync_check(9.6s) → deploy(72.4s)
- 备注: 首次运行 ALIMI 角色正常启动（非盘中跳过），deploy 步骤耗时偏长(72.4s)，已正常推送 GitHub Pages

## 2026-07-12 15:34（周日）
- 命令: `batch_update.py post_close`
- 结果: 退出码 0，无报错
- 输出: `非交易日（周末），模式 [post_close] 跳过，不抓行情`
- 说明: 2026-07-12 为周日，脚本内置周末跳过逻辑生效，正常跳过、无需修复。周末行情/部署由 weekend_light 自动化(19:30 阿狸咪)负责。
- 后续: 16:07 用户手动要求修复 crisis_radar/market_signal 返回导航链接，已修复并部署。
- 后续: 16:24 用户"一并修复"—全部 12 个 standalone 独立页返回主站链接统一修复为 ../index.html，含修复 deploy_now.py 强制覆盖 triple/multi_resonance 绕过重写的遗漏。已 deploy_now.py --force 部署完成（构建戳 20260712162350），本地验证零残留旧链接。

## 2026-07-24 15:31（周五，盘中15:30）
- 命令: `batch_update.py post_close`（铁律：只跑这一条）
- 根因: 本地 batch_update.py 被 xiaojiu-bot 自动同步 commit 74e44eea(17:32) 误回退成 13 步坏版（缺 fetch_herding_data/main_stock/suspension + push_china_data，部署超时 180s）→ 闸门 FAIL + 部署假超时。今日自动化 17:38 / 17:48 两次空跑均因闸门失败未部署。
- 修复: 恢复 17 步（补 5 个盘前文件抓取）+ 部署超时 180→600s；commit 14f4ab7d 并 push origin/main。⚠️ 自身编辑失误又引入括号重复 SyntaxError（误提交 14f4ab7d），再修 commit 638bedb0 push（638bedb0 为权威修复版）。
- 结果: 17/17 全步 ✓（含 herding/main_stock/suspension 抓取），部署前闸门 3.3s 通过，[17/17] deploy_now.py --force ✓ 206.3s，退出码 0。
- 验证: `git fetch origin gh-pages` → origin/gh-pages 强制更新至 3ac3df13；线上 index.html 构建戳 **20260724180926**（当日 18:09，新鲜）；candidate_pool.json 在 gh-pages 存在。确认非 07-23 那种「日志成功但远程未更新」假成功。
- 遗留风险: xiaojiu-bot 自动同步仍可能再次回退 batch_update.py；本次修复已在 origin/main(638bedb0)，若再被回退需重跑本修复。

## 2026-07-25 15:26（周六）
- 命令: `batch_update.py post_close`（铁律：只跑这一条）
- 结果: 退出码 0，无报错，无修复
- 输出: `非交易日（周末），模式 [post_close] 跳过，不抓行情`
- 说明: 2026-07-25 为周六，脚本内置周末跳过逻辑生效，正常跳过、无需修复。周末行情/部署由 weekend_light 自动化(19:30 阿狸咪)负责。

## 2026-07-25（本次运行 — 续做全站精选 TAB）
- 任务: 续做并验证"全站精选"TAB 迁移（健康看板内与驾驶舱并列，数据源 top10_daily.json ≥80）。
- 状态: 已完成并验证。源码 index_master.html + index.html 已随 source-sync 自动提交 push（commit 307cb48e），gh-pages 部署 build stamp 20260725212059。
- 线上核验（origin/gh-pages 原始内容）: renderAllsiteSelection×2、allsitePanel×7、data-cat="allsite"×1、cat==='allsite'×1、renderCockpitAllsiteSelection×2、buildCockpitAllsiteHTML×1、top10_daily.json×4、全站数据精选×6。WebFetch 因剥离 script 报代码串 0 为假阴性。
- 结论: 不跑 batch_update（周末跳过），本运行仅为续做/核对功能上线，无需额外部署动作。
