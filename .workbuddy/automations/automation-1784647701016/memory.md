# 收盘后驾驶舱回测 — 执行记录

## 2026-07-22 19:10 (自动化触发)
- **7 步全部成功**
- cockpit_backtest.py：有效信号 11，胜率 50.0%，平均收益 -1.1%
- backtest_comprehensive.py：4 策略，最佳持有 1~3 日，胜率 40%~50%
- update_data_v2.py → dist 构建成功（冒烟测试有括号警告但未阻止）
- git add/commit/push → main 分支已更新
- deploy_now.py --force → gh-pages 部署成功
- 提交 hash：a0bf7f5a
- 部署 URL：https://ah-quant999.github.io/quant-scanner-v6/

## 2026-07-25 19:14 (自动化触发)
- **7 步全部成功**
- cockpit_backtest_now.py：有效信号 36，胜率 11.8%，平均收益 -2.27%（≥80 分 3 只胜率 0%）
- backtest_comprehensive.py：5 策略，最佳持有 1~3 日，胜率 26.7%~50%
- update_data_v2.py → dist 构建成功（4,594,676 字符），冒烟测试括号警告未阻止
- git add/commit/push → main 已更新（提交 0a6852f5 → push 17079758，中间 safe_pull 一次）
- deploy_now.py --force → gh-pages 部署成功（build stamp: 20260725191620）
- 提交 hash：17079758
- 部署 URL：https://ah-quant999.github.io/quant-scanner-v6/
