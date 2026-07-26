# 盘后刷新部署（16:31）执行记忆

## 2026-07-24 16:31 执行

**流程**：git pull --rebase（stash pop 冲突 16UU）→ 15 fetch/更新脚本（generate_one_look.py 不存在跳过）→ update_data_v2.py 重建 → deploy_now.py --force（首次因非快进失败→git reset origin/main 重试成功）→ 心跳 → WebFetch 验证。

**结果**：全部成功，页面标题 `九宝量化 v6.0 (20260724164539)`（build stamp=2026-07-24 16:45:39），103 文件推 gh-pages（62955df）。

### 关键观察
- git stash pop 遗留 16 个 UU 文件（dist/ 和 standalone/ 冲突），`deploy_now.py` 的 `_fix_unmerged_files` 只清理到 14 个，剩余 2 个 UU（dist/index.html, dist/index_master.html）需手动 `git add`。
- 部署锁冲突：第一次 push 被 non-fast-forward 拒绝，deploy 脚本误判"另一台机器持有部署锁"——实为本地 HEAD 与 origin/main 分叉。手动 `git reset origin/main`（保留数据）后重试成功。
- 龙虎榜 72 只，1 只机游共振（盛屯矿业 600711，机构 2.48亿+游资 1.17亿）。
- 板块资金：半导体 +102.3亿（连11天），P0 本地累加 140 板块有 5 日累计。
- cockpit 回测：18 有效信号，胜率 22.2%，平均收益 -1.43%。
- generate_one_look.py 仍不存在（RC=2，跳过）。

## 2026-07-23 16:31 执行

**流程**：git pull --rebase → 11 个 fetch 脚本 → 6 个更新/生成脚本 → update_data_v2.py 重建前端 → deploy_now.py --force 部署 → 心跳 → WebFetch 验证。

**结果**：全部成功，页面标题 `九宝量化 v6.0 (20260723164053)`（build stamp=2026-07-23 16:40:53），验证通过。

### 关键观察
- 全部 11 个 fetch 脚本 OK（fetch_lhb 75 只龙虎榜，机游共振 2 只；fetch_concept_ranking 374 概念板块；fetch_sector_fund_flow 东财历史接口服务器不可用，P0 本地累加 123 个板块有真实5日累计）。
- 第二组：update_triple_resonance_daily OK（scan_data.json 缺失，历史追踪 327 只）；update_multi_resonance_daily 覆盖更新 OK；calc_crds OK（230 只→209 有效）；generate_recommend 废弃跳过；generate_top10 OK（20 只，TOP1 香农芯创 75 分）；generate_one_look.py 不存在(RC=2，按失败继续跳过)；cockpit_backtest_now OK（17 信号，胜率 50%）。
- update_data_v2.py 全量重建，冒烟 4 警告(已知问题)继续。
- deploy_now.py --force：源码自动提交→推 main→重建 dist→推 gh-pages（100 文件）。心跳上报正常。
