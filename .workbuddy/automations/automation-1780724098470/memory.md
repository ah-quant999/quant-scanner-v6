# 九宝量化-全盘扫描 09:15(盘前全量) 执行摘要

- 2026-07-09 09:07 `python batch_update.py pre_market` 跑完，Exit Code 0。10 步中 9 成功，部署 `deploy_now.py --force` ✓ 成功。
  失败：`fetch_mahoro_signals.py --non-interactive`（exit=2，重试后仍失败）。按铁律未自行改脚本/自由发挥，仅运行该单条命令。mahoro 取数源问题需人工处理。
- 2026-07-12 09:07（周日）`python batch_update.py pre_market` 跑完，Exit Code 0。非交易日（周末）自动跳过，不抓行情、不部署。无报错，无需修复/重跑。
- 2026-07-13 09:07（周一，交易日）`python batch_update.py pre_market` 跑完，Exit Code 0。10 步全部成功（含对 [4] scanner.py full 的自动重试：首跑因 py_mini_racer/mini_racer.dll V8 引擎崩溃 exit=2147483651 失败，末尾重试 ✓ 0.9s）。部署 `deploy_now.py --force` ✓ 128.6s 成功。交接日志已写、心跳已清理。按铁律仅运行单条命令，未自行改脚本/自由发挥；失败由 batch 内部重试机制自愈。
- 2026-07-14 09:07（周二，交易日）`python batch_update.py pre_market` 跑完，Exit Code 0，总时长 6m47s。10 步中 [2] fetch_mahoro_signals.py 首跑 JSONDecodeError exit=1，末尾 batch 内部重试自愈 ✓ 0.5s；最终 10 成功 0 失败。部署 `deploy_now.py --force` ✓ 128.5s 成功，交接日志已写、心跳已清理。按铁律仅运行单条命令，未自行改脚本/自由发挥；mahoro 偶发取数失败由 batch 重试机制自愈，无需人工介入。
