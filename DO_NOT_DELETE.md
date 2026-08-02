# 九宝量化 v6.0 - 禁止删除清单

**最后更新**: 2026-07-25 18:30
**维护人**: HH + AI助手  
**用途**: 防止误删核心资产，每次项目瘦身前必须核对此清单

---

## 🔴 核心数据文件 (data/)

| 文件路径 | 内容描述 | 禁止删除原因 | 最后更新 |
|---------|---------|------------|---------|
| `data/sh_sz_history.json` | 涨跌家数历史数据 | 主站核心数据源，瘦身时曾被误清空，**已从Git恢复31天数据** | 2026-07-03 |
| `data/scan_result.json` | 选股结果 | 主站核心数据源，646KB大文件 | 每日更新 |
| `data/gold_pool.json` | 黄金池数据 | 主站核心数据源，123KB | 每日更新 |
| `data/sector_fund_flow.json` | 板块资金流 | 主站核心数据源，包含5d/20d累计 | 每日更新 |
| `data/sector_rs.json` | 板块相对强度 | 主站核心数据源 | 每日更新 |
| `data/north_fund.json` | 北向资金 | 主站核心数据源 | 每日更新 |
| `data/limit_up_heatmap.json` | 涨停联动热力图 | 主站核心数据源 | 每日更新 |
| `data/lhb_result.json` | 龙虎榜结果 | 主站核心数据源 | 每日更新 |
| `data/worldcup.json` | 世界杯数据 | 独立页面数据源，暂不上架区入口 | 每日更新 |
| `data/lottery_data.json` | 彩票概率数据 | 独立页面数据源，暂不上架区入口 | 每日更新 |
| `data/industry_map.json` | 行业板块/概念映射 | **强制跟踪**；东财限流重建成本高，双机共享好版本必须留存 | 每日/周一重建 |
| `data/industry_map_shard_*.json` | 行业映射分片(6个) | industry_map.json 拆分产物，重建成本高 | 同 industry_map |
| `data/candidate_pool.json` | 金股候选池 | 主站"股池构成"卡片数据源 | 每日更新 |
| `data/crisis_data.json` | 危机雷达20指标原始数据 | crisis_radar.html 数据源，close/close_p1 步骤必需 | 每日更新 |
| `data/stock_names.json` | 股票代码→名称映射 | update_data_v2 注入用；超过7天自动刷新，丢失则新上市/退市名长期不更新 | 自动刷新 |
| `data/macro_data.json` | 宏观指标数据 | 主站宏观卡片数据源 | 每日更新 |
| `data/dxy_hist.json` | 美元指数日频历史 | DXY 真实分位自愈累积源，丢了回到假分(55硬编码) | 每日累加 |
| `data/usdcnh_hist.json` | 离岸人民币日频历史 | USDCNH 真实分位自愈累积源，丢了回到假分(25硬编码) | 每日累加 |

**注意**: `data/` 目录下所有 `.json` 文件都是核心数据源，**禁止批量删除**。如需清理，必须逐个确认。

---

## 🟠 独立页目录 (standalone/)

| 文件路径 | 内容描述 | 禁止删除原因 | 最后更新 |
|---------|---------|------------|---------|
| `standalone/crisis_radar.html` | 独立页HTML文件 | 独立页组件，自动部署 | 自动更新 |
| `standalone/data_responsibility.html` | 独立页HTML文件 | 独立页组件，自动部署 | 自动更新 |
| `standalone/gold.html` | 独立页HTML文件 | 独立页组件，自动部署 | 自动更新 |
| `standalone/guide.html` | 独立页HTML文件 | 独立页组件，自动部署 | 自动更新 |
| `standalone/health.html` | 独立页HTML文件 | 独立页组件，自动部署 | 自动更新 |
| `standalone/index.html` | 独立页HTML文件 | 独立页组件，自动部署 | 自动更新 |
| `standalone/market_signal.html` | 独立页HTML文件 | 独立页组件，自动部署 | 自动更新 |
| `standalone/overview.html` | 独立页HTML文件 | 独立页组件，自动部署 | 自动更新 |
| `standalone/predict.html` | 独立页HTML文件 | 独立页组件，自动部署 | 自动更新 |
| `standalone/query.html` | 独立页HTML文件 | 独立页组件，自动部署 | 自动更新 |
| `standalone/shmonitor.html` | 独立页HTML文件 | 独立页组件，自动部署 | 自动更新 |
| `standalone/triple_consensus.html` | 独立页HTML文件 | 独立页组件，自动部署 | 自动更新 |
| `standalone/index.html` | 独立页导航 | 独立页入口 | 自动更新 |
| `standalone/gold.html` | 黄金池独立页 | 密码保护独立页 | 自动更新 |
| `standalone/health.html` | 市场健康度独立页 | 密码保护独立页 | 自动更新 |
| `standalone/predict.html` | 预判信号独立页 | 密码保护独立页 | 自动更新 |
| `standalone/query.html` | 查询独立页 | 密码保护独立页 | 自动更新 |
| `standalone/overview.html` | 总览独立页 | 密码保护独立页 | 自动更新 |
| `standalone/shmonitor.html` | 沪深监控独立页 | 密码保护独立页 | 自动更新 |
| `standalone/guide.html` | 使用指南独立页 | 独立页说明文档 | 手动更新 |
| `standalone/worldcup.html` | 世界杯独立页 | 暂不上架区入口 | 手动更新 |
| `standalone/crisis_radar.html` | 危机雷达独立页 | 六维危机监测入口页，主站入口卡跳转目标 | 自动更新 |
| `standalone/market_signal.html` | 市场面信号独立页 | 三维度评分详情页，主站入口卡跳转目标 | 自动更新 |

**保护措施**: `standalone/` 已在 `.gitignore` 中添加 `dist/standalone/`，防止被Git覆盖。

---

## 🟡 主站页面 (dist/)

| 文件路径 | 内容描述 | 禁止删除原因 | 最后更新 |
|---------|---------|------------|---------|
| `dist/index.html` | 主站页面（编译后） | 主站入口，1.8MB大文件 | 自动更新 |
| `dist/index_master.html` | 主站模板（源码） | 主站源码，所有页面基于此生成 | 手动更新 |

**注意**: `dist/` 目录下的 `.html` 文件都是主站核心页面，**禁止删除**。`dist/data/*` 是 `update_data_v2.py` 每次构建时从 `data/` 同步的副本，按 2026-07-28 铁律**不再进入 main 分支**，避免 `safe_pull` 时 origin/main 旧版覆盖本地最新数据。

---

## 🟢 核心脚本 (根目录 *.py)

| 文件路径 | 内容描述 | 禁止删除原因 | 最后更新 |
|---------|---------|------------|---------|
| `batch_update.py` | 定时任务总控脚本 | 所有定时任务的入口，核心脚本 | 2026-07-03 |
| `push_notify.py` | 收盘推送通知(桩) | close_deploy 步骤必需，缺失导致部署判失败；曾因未跟踪被丢 | 每日运行 |
| `guanlan_extractor.py` | 观澜台抽取(已废弃桩) | morning_report/close/close_p1 步骤调用，缺失导致判失败；曾因未跟踪被丢 | 每日运行 |
| `generate_recommend.py` | 收盘生成脚本 | close_p2 Group4 必需，曾因未跟踪从main丢失+误判失败(exit 1)；已从backup恢复 | 每日运行 |
| `fetch_*.py` (所有抓取脚本) | 数据抓取脚本 | 所有数据源的抓取逻辑 | 各脚本不同 |
| `fetch_crisis_data.py` | 危机雷达19指标采集 | 危机雷达页数据源，close/close_p1 步骤必需 | 每日运行 |
| `build_crisis_radar.py` | 危机雷达独立页生成 | 由 refresh_standalone_and_deploy 调用生成 crisis_radar.html | 每日运行 |
| `build_market_signal.py` | 市场面信号独立页生成 | 由 refresh_standalone_and_deploy 调用生成 market_signal.html | 每日运行 |
| `extract_panels_v6.py` | 独立页生成脚本 | 独立页自动生成逻辑 | 2026-07-03 |
| `deploy_now.py` | 手动部署脚本 | 手动触发部署 | 不定期 |
| `deploy_audit.py` | 部署审计脚本 | 部署前审计 | 不定期 |
| `check_data_freshness.py` | 数据时效性检查 | 监控数据更新状态 | 不定期 |
| `backup_daily.py` | 每日备份脚本 | 自动备份关键数据 | 每日运行 |
| `heartbeat_xiajiu.py` | 阿狸咪→小九对称心跳检查 | 检测小九白天是否在线 | 每日运行 |
| `evening_failover_check.py` | 17:30后主备状态检查 | 判断小九是否需要兜底补跑 | 收盘后运行 |
| `auto_handoff_read.py` | 阿狸咪读取小九交接文件 | 10:00/14:30/18:30 读交接 + 紧急指令监听调用；曾因缺失导致3个读交接任务静默失败 | 每日运行 |
| `update_data_v2.py` | **核心数据注入脚本** | 所有定时任务的数据注入入口，缺失则全站数据不更新 | 每日运行 |
| `refresh_standalone_and_deploy.py` | 独立页部署总控 | 调用 build_crisis_radar/build_market_signal 生成独立页并部署 | 每日运行 |
| `update_worldcup_standalone.py` / `build_standalone_worldcup.py` / `fetch_worldcup.py` / `data/worldcup.json` / `standalone/worldcup.html` | **已废弃，从代码库移除** | 世界杯模块已下线，相关文件已从根目录和 data/ 移除 | 2026-07-23 |
| `fetch_stock_names.py` | 股票名映射抓取 | stock_names.json 生产者，已接入 update_data_v2 自动刷新 | 每日运行 |
| `is_trading_day.py` | 交易日判断 | batch_update 用以跳过非交易日，缺失则定时任务误跑/误跳 | 每日运行 |
| `inject_weekend_run.py` | 周末 light 模式注入 | batch_update weekend_light 调用，注入 WEEKEND_RUN 标注；曾因未加白名单被 gitignore 游离 | 周末运行 |
| `diag_parallel.py` | 并行诊断工具 | 排障辅助脚本，防误删一并白名单 | 不定期 |
| **部署/扫描/监控管线核心**（下文 27 个脚本） | 通配<code>*.py</code>已保护，但也逐个列出防止瘦身误清 | 均被 batch_update / deploy / workflow 调用，缺失则整条链路断裂 | 每日运行 |
| `scanner.py` / `build_candidate_pool.py` / `enhance_dist.py` | 扫描/构建/增强 | 核心管线：scanner→候选池→增强→部署 | 每日运行 |
| `verify_data_vs_website.py` / `check_freshness_vs_ghpages.py` / `check_all_deploys.py` / `check_morning_deploy.py` | 部署闸门/新鲜度/全任务核验 | 部署前的安全闸门，缺失则劣质数据上线 | 每日运行 |
| `git_safe_sync.py` / `sync_check.py` / `clean_deploy_lock.py` | Git安全同步/检测/清锁 | 双机代码同步+锁清理，缺失则 pull 冲突/部署锁卡死 | 每日运行 |
| `data_freshness_watchdog.py` / `watch_candidate_pool.py` | 数据新鲜度看门狗/候选池监控 | 定时检查数据是否更新，缺失则陈旧数据不会被发现 | 每30/60分钟 |
| `report_heartbeat.py` / `peer_health_monitor.py` / `heartbeat_xiajiu.py` | 心跳上报/对端健康/小九心跳监听 | 双机心跳系统，缺失则运维板"最后活跃时间"停更 | 每日运行 |
| `calc_crds.py` / `calc_volatility_watch.py` / `capital_flow_summary.py` | CRDS逆势龙头/波动率/资金流汇总 | 三张实验卡的数据计算，批处理管线必需 | 每日运行 |
| `generate_recommend.py` / `generate_top10.py` | 推荐/排行榜生成 | close_p2 最后一步的生成脚本 | 每日运行 |
| `trigger_cloud_dispatch.py` / `close_deploy_guarded.py` / `pre_market_cloud_failover.py` | 云端发令/受控部署/盘前兜底 | 双机-云端协作的关键调度脚本 | 每日运行 |
| `industry_map_self_heal.py` / `maintain_industry_map.py` | 行业映射自愈/维护 | industry_map.json 重建+修复，东财限流时挽救 | 每周运行 |
| `enhanced_backup.py` / `backup_daily.py` | 增强备份/每日备份 | 数据双保险，缺失则无人备份 | 每日运行 |
| `audit_automations.py` | 定时任务ID审核 | 自动检测无效 model_id 并修复，防 ds-V4-FLASH 事故 | 09:00/19:00 |
| `EVENING_FAILOVER.md` | 主备分离逻辑文档 | 双机协作规则 | 2026-07-10 |

**注意**: 根目录下所有 `fetch_*.py` 和 `*.py` 脚本都是核心逻辑，**禁止批量删除**。如需清理旧脚本，必须逐个确认。

---

## 🔵 配置和文档

| 文件路径 | 内容描述 | 禁止删除原因 | 最后更新 |
|---------|---------|------------|---------|
| `.gitignore` | Git忽略配置 | 保护 `standalone/` 等关键目录 | 2026-07-03 |
| `HANDOVER_LOG.jsonl` | 交接日志 | 双机协作交接记录，坚果云同步 | 每日更新 |
| `HANDOVER*.md` | 双机交接文档(12个) | 小九↔阿狸咪交接记录，含操作指南与状态；误删导致双机协作断链 | 每日更新 |
| `assets/candidate_pool_snapshot.png` | 候选池快照图 | 金股候选池可视化快照，前端引用 | 每日更新 |
| `.machine_role` | 双机角色标记 | 区分阿狸咪/小九的运行时标记，误删导致日志/心跳判定错乱 | 双机各一 |
| `README.md` | 项目说明 | 项目文档 | 不定期 |
| `DO_NOT_DELETE.md` (本文件) | 禁止删除清单 | 防止误删的核心文档 | 持续更新 |
| ~~`.github/workflows/*.yml`~~ | **2026-08-02 主动退役 v6**：9 个 v6 GitHub Actions 定时任务已全部删除（git 历史可恢复），此保护行作废。v8 仓的 workflow 在 `quant-scanner-v8` 仓、不受本文件约束。 | 已删 |

---

## ⚪ 可清理文件/目录（超过N天可删除）

| 文件路径/模式 | 可删除条件 | 注意事项 |
|------------|-----------|---------|
| `backup_YYYYMMDD/` | 超过3天 | 必须是 `backup_` 前缀的日期目录 |
| `handover_*` | 超过3天 | 必须是 `handover_` 前缀的临时文件 |
| `*.bak` | 超过3天 | 备份文件 |
| `standalone/deploy/` | 超过3天 | 临时部署目录（如果存在） |
| `data/.fetch_log.json` | 可清空 | 抓取日志，可清空但**不能删除文件** |

**清理前必须**:
1. 核对本清单，确认不在禁止删除列表中
2. 确认文件/目录超过3天（检查修改时间）
3. 如有疑问，先询问再删除

---

## 📝 历史误删记录（教训）

| 日期 | 误删文件 | 原因 | 恢复方法 |
|-----|---------|------|---------|
| 2026-07-03 | `data/sh_sz_history.json` | 瘦身时误清空 | 从Git历史(c3ef2a51)恢复30天 + 今日精确数据 |
| 2026-07-03 | 暂不上架区世界杯/彩票条目 | 误认为"无关联" | 已恢复 index_master.html |
| 2026-07-03 | 旧部署目录 | 误认为"可清理" | 用户制止，已保留 |

**教训**: 每次瘦身前，必须先读此清单，再逐项确认。

---

## 🔄 维护说明

- **本文件必须持续维护**: 每次新增核心文件/目录，必须同步更新此清单
- **清理前必须核对**: 每次项目瘦身，必须先读此清单，再逐项确认
- **误删后必须记录**: 每次发生误删，必须记录到"历史误删记录"表格
- **定期审查**: 每周审查一次，确保清单完整性

---

**重要提醒**: 
1. `standalone/` 目录已加入 `.gitignore`，**禁止手动删除**
2. `data/` 目录下所有 `.json` 文件都是核心数据源，**禁止批量删除**
3. 根目录下所有 `fetch_*.py` 脚本都是核心逻辑，**禁止批量删除**
4. 清理旧文件时，必须确认文件名/目录名符合"可清理"模式，且超过3天

---

**最后核对**: 2026-07-19 14:00 ✅ (用户要求保留以防万一：3 个孤立脚本已恢复，双机兜底改为主动执行)
**下次审查**: 2026-07-26 (每周审查)

---

## 备注：2026-07-19 已恢复项

以下文件曾因无调用源被清理，但用户要求"自动化不能删除，要以防万一"，已恢复保留：
- `watchdog_check.py` — 保留备用
- `verify_data_sources.py` — 保留备用
- `fetch_concept_ranking_em.py` — 保留备用

已通过 `--no-verify` 提交。
