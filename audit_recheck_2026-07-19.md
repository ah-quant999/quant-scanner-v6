# 九宝量化 — 全面重新审计报告（2026-07-19 周日）

> 审计方法：全部基于**实际证据**（git diff / gh-pages 部署日志 / 文件时间戳 / HANDOVER_LOG），不靠记忆。
> 触发：用户要求对"最新最及时最真实可靠的数据"重新全面审计。

## 核心结论：系统当前**靠谱 ✅**，无致命不靠谱环节

上次审计发现的问题已全部闭环，云端数据链路活跃，周日视角数据最新=周五收盘（正确）。

---

## 一、上次修复是否真上库（最关键，曾高度怀疑"修复被遗忘"）

**证据**：`git diff HEAD stash@{0} -- 12个核心.py + 6个workflow = 0 行差异`

**结论**：线上 `origin/main` 已是最新修复版，`stash@{0}` 只是 autostash 留下的空壳（内容与线上一致）。之前看到 `diff origin/main stash@{0}` 显示 332/169 差异，是审计中途 `git fetch` 把 origin/main 更新到修复版**之前**的旧快照造成的错觉——虚惊一场，无"修复被遗忘未上库"。

已上库并确认的修复（行号证据）：
- `update_data_v2.py` L1495 `_compute_data_updated_at()` + L1534/L1576 ops_status 回写真实文件 ✅
- `deploy_now.py` L33 `timeout=180` / L62 `timeout=120` ✅
- 云端 GTimg 适配（`scanner.py`/`build_candidate_pool.py`）+ lock 精准还原（`_fix_unmerged_files`）+ 周末 T+1 抓数（`fetch_cffex_holdings`/`fetch_inst_trade`）+ 运维卡告警 + 数据正确性 gate ✅

## 二、云端是否真在跑（数据链路最终依赖点）

**证据**：`git log origin/gh-pages` 今天（周日 07-19）有 4 次部署：
```
30a4eab2 deploy: 2026-07-19 13:27
72126d9f deploy 20260719131015
48d7cacc deploy: 2026-07-19 13:00
542ceee8 deploy: 2026-07-19 07:38
```
**结论**：云端 10 档 workflow 活跃部署，数据链路正常。本地 HANDOVER_LOG 无 `CLOUD` host 记录是因为云端不写本地该文件（验证脚本 CAT 才写），属正常。

## 三、数据新鲜度（周日非交易日视角）

| 文件 | 时间戳 | 判定 |
|------|--------|------|
| scan_result / gold_pool / lhb_result / nt_data / crds_result 等 | 2026-07-19 13:19 | ✅ 今天 close_deploy 重建（基于周五数据，正常） |
| watch_result / sector_rs / herding_data / industry_map / suspension_alert / stock_names | 2026-07-17 19:31 | ✅ 周五收盘=周末最新真实数据 |
| north_fund.json | 2026-07-17 10:32 | ✅ 北向已停披露（港交所 2024-05），正确标注"停止" |

**结论**：周日无新交易日，数据最新=周五收盘，符合预期。无"该刷没刷"的异常。

## 四、git SSH 超时（P0 防挂死）

- `batch_update.py` L472 `git pull` 带 `GIT_SSH_COMMAND` + `http.version=HTTP/1.1` ✅
- L497 `git stash pop` 带 `http.version=HTTP/1.1` ✅
- **次要残留**：`push_china_data.py` 等独立推送脚本的 git 调用未显式设 SSH 超时（推送失败仅影响备份，不致命，可后续补）

## 五、脚本调用链完整性

所有核心 `fetch_*.py` 均有调用源（batch_update 或云端 workflow）：
- `fetch_52w_high`(batch_update 引用2) / `fetch_maharo_signals`(workflow 引用2) / `fetch_stock_names`(workflow 引用1) / `fetch_worldcup`(workflow 引用1) ✅

**真孤立脚本（3个，均非核心数据抓取，不影响数据更新）**：
1. `watchdog_check.py` — 监控脚本，功能已被新建的 `intraday_fresh_check.py` 看门狗替代
2. `verify_data_sources.py` — 数据源验证，未接入
3. `fetch_concept_ranking_em.py` — `fetch_concept_ranking.py` 的 EM 冗余版

## 六、自动化任务覆盖（26个）

- 本地盘中(10:30-16:30)/盘前(09:16)/收盘(17:30/18:30)抓取全 **PAUSED**（设计：云端为主）
- 已建兜底：**盘中看门狗**(每半点邮件告警) + **数据新鲜度巡检**(20:00) + **收盘最终部署 19:30**(ACTIVE) + **备份兜底 21:10**(ACTIVE)
- 模型：26 个自动化已全部统一 `hy3`
- **风险（已知权衡）**：云端若盘中失败，本地无自动补跑，仅看门狗告警 → 等下次兜底/人工。非致命。

## 七、部署链路健壮性

- `deploy_now.py`：`_fix_unmerged_files` 精准还原（防 lock 覆盖合法提交）+ `run()/_git() timeout=180/120` ✅
- `verify_frontend_deploy.py`：纳入 `dist/*.json` 核对；`dist/data/` 走坚果云/CDN 不核对（设计，数据同步不依赖 gh-pages 校验）✅
- `close_deploy_guarded.py`：lock 机制 + 云端已更新则跳过部署，不覆盖新鲜云端 ✅

---

## 剩余非致命项（建议清理，不紧急）

| # | 项 | 影响 | 建议 |
|---|----|------|------|
| 1 | 3 个孤立脚本（watchdog_check/verify_data_sources/fetch_concept_ranking_em） | 无（非核心） | 清理或接入 verify_data_sources |
| 2 | push_china_data.py 等推送脚本 git 调用缺 SSH 超时 | 低（推送失败仅影响备份） | 后续补 GIT_SSH_COMMAND |
| 3 | 本地盘中无自动补跑 | 低（依赖云端+看门狗告警） | 已知权衡，保持 |

## 总体评级：靠谱 ✅

- **最新**：周日非交易日，数据最新=周五收盘（正确）
- **及时**：云端活跃（gh-pages 今天 4 次部署）
- **真实**：数据源逻辑已修（周末 T+1 抓数、updated_at 真实时间、ops_status 回写真实文件）
- **可靠**：git SSH 超时防挂死 + lock 精准还原防覆盖 + 看门狗/巡检告警
