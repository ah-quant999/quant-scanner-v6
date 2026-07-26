# 自动化执行日志 — 九宝量化-盘中11:45

## 2026-07-09 11:45 morning_report
- 首次跑：11/12 成功，fetch_mahoro_signals.py 非交互模式 exit=2（stock-scanner/data 缺有效 cookie）。
- 修复：cp 坚果云同步盘 E:/workspace/data/.mahoro_cookies.txt → stock-scanner/data/.mahoro_cookies.txt（cookie 验证有效）。
- 重跑：12/12 全部通过，部署成功。

## 2026-07-10 11:45 morning_report
- 首跑：11/12 成功，guanlan_extractor.py 缺失（exit=2，根目录文件被删）。
- 修复：从 backup_20260709/guanlan_extractor.py 还原桩文件到根目录（该文件仅为"已废弃跳过"桩，exit 0）。
- 重跑：12/12 全部通过，已在 deploy_now.py --force 中完成部署推送。
- 附带发现：DO_NOT_DELETE.txt 在根目录及所有 backup_*/ 中均不存在（与项目记忆"已建立防误删清单"不符），未擅自动手恢复，已提示用户。

## 2026-07-12 11:45 morning_report（周日，非交易日）
- 启动即跳过：脚本判定非交易日（周末），模式 [morning_report] 直接 return，未抓行情、未部署。
- 输出：`⏭️ 非交易日（周末），模式 [morning_report] 跳过，不抓行情`。无报错，无需修复重跑。
- 耗时 1s（仅判定跳过）。

## 2026-07-11 11:45 morning_report（手动/自动化触发，周六）
- 14/14 全部通过，0 失败，已部署 gh-pages（deploy_now.py --force 84.4s）。
- 耗时 8m40s，主要卡点：双机 git pull 29.1s + update_data_v2.py 215.3s（家用机东方财富限流，全市场行情重试极久）；各 fetch 步骤(概念排行56.6/市场预警49.4/板块资金流63.8)均受周末东财限流拖累。
- 无报错，无需修复重跑。

## 2026-07-14 11:45 morning_report（周二，交易日）
- 14/14 全部通过，0 失败，已部署 gh-pages（deploy_now.py --force 128.3s）。
- 耗时 7m04s，卡点：update_data_v2.py 149.7s（家用机东财限流）+ 部署 128.3s + 各东财 fetch（市场预警46.8/板块资金流40.9/概念排行25.4）。
- 无报错，无需修复重跑。脚本自愈/一次性跑通。

## 2026-07-13 11:45 morning_report（周一，交易日）
- 首跑 13/14：步骤3 fetch_mahoro_signals.py --non-interactive 报错 exit=1，JSONDecodeError（读某 JSON 文件 line 2 引号问题）。
- 脚本自带重试机制在末尾自动重跑该失败步骤 [R] ✓ 0.5s，最终 14/14 全部通过、0 失败，已部署 gh-pages（deploy_now.py --force 118.8s）。
- 耗时 7m49s，卡点：update_data_v2.py 158.3s + 部署 118.8s + 各东财 fetch（概念排行35.8/市场预警59.7/板块资金流49.8）。
- 无需我手动修复重跑，脚本自愈完成。
