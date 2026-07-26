# ⚠️ 重要文件清单 — 请勿删除（DO NOT DELETE）

本文件为「九宝量化 v6」核心数据/脚本的**防误删标注**。这些文件一旦丢失，
全站行业/板块/概念展示、扫描、部署都会失效，且云端 workflow 也读不到。

## 防护三道闸（任一都能拦住误删）
1. **`.gitignore` 白名单**：所有下方 data 文件都有 `!data/xxx.json` 例外，
   否则会被 `data/*` 兜底忽略而云端永久读不到。改 `.gitignore` 后务必复核。
2. **主仓提交**：关键 data 文件已 `git add` 并提交 `origin/main`，误删可
   `git checkout origin/main -- data/xxx.json` 恢复。
3. **本清单标注**：任何清理/重构操作前，先对照本清单，不确定的文件 → 先读内容再判断。

---

## 一、核心数据文件（data/，缺失即影响全站）

| 文件 | 用途 | 防护状态 |
|---|---|---|
| `data/industry_map.json` | **个股元数据仓**：5309 只股票 industry 100% 覆盖 + concepts（概念映射） | ✅ 白名单 + 已提交 |
| `data/concept_map.json` | 股票→概念 原始反向映射缓存（fetch_concept_map.py 产出） | ✅ 白名单 + 已提交 |
| `data/candidate_pool.json` | 候选池（~309 只，扫描核心，行业/板块/概念齐备） | ✅ 白名单 + 已提交 |
| `data/gold_pool.json` | 金股池（~182 只，行业/板块/概念齐备） | ✅ 白名单 + 已提交 |
| `data/stock_names.json` | 全市场股票名/代码映射（universe 基准） | ✅ 白名单 + 已提交 |
| `data/scan_data.json` | 扫描结果 | ✅ 白名单 |
| `data/multi_resonance_history.json` | 多维共振历史（含基本面新分数） | ✅ 白名单 |
| `data/top10_daily.json` | 每日 TOP10 评分 | ✅ 白名单 |
| `data/macro_data.json` / `data/crisis_data.json` / `data/fomc_summary.json` | 宏观/危机/FOMC | ✅ 白名单 |
| `data/close_summary.json` / `data/market_fund_flow.json` | 收盘/资金流（阿狸咪新增） | ✅ 白名单 |
| `data/.fetch_log.json` / `data/.ops_status.json` | 抓取日志 / 运维状态 | ✅ 白名单 |
| `data/maharo_signals.json` / `data/sector_fund_flow_westock.json` | 研报信号 / 板块资金流 | ✅ 白名单 |

> 合理忽略（**不要误以为丢失**）：`_crisis_hist_cache.json`、`audit_summary.json`、
> `verify_report.json`、`zsxq_token.json` —— 缓存/密钥，自动生成。

---

## 二、核心脚本（repo-temp/，生产代码勿覆盖/误删）

| 脚本 | 用途 |
|---|---|
| `fetch_concept_map.py` | **构建股票→概念映射**（6 线程并行，~6min，回填 industry_map.json） |
| `fetch_industry_map.py` | 重建行业映射（BaoStock 主源 + 东财/同花顺回退） |
| `industry_map_self_heal.py` | 行业地图自愈（缺失字段补抓） |
| `maintain_industry_map.py` | **删退市股 + enrich 股池 + 补行业**（周度） |
| `weekly_maintain_stock_meta.py` | **周度编排：行业→概念→删退补新→核验→部署** |
| `update_data_v2.py` | 全站数据重建（注入行业/板块/概念到 dist） |
| `ensure_standalone_sync.py` | standalone 页面同步（含 build-stamp） |
| `deploy_now.py` | 部署到 gh-pages |
| `build_candidate_pool.py` | 构建候选池 |

---

## 三、周度自动化任务（本机，周日 07:10）

- 任务：`周日 个股元数据维护（行业/概念/删退补新）`
- 执行：`weekly_maintain_stock_meta.py` → 重建行业 → 重建概念 → 删退补新+enrich →
  提交主仓 → **核验覆盖率** → **部署 gh-pages**
- 效果：每周自动补足新股票的一切、删除退市股的一切，并把最新元数据部署上线。

---

## 四、误删应急恢复

```bash
# 从主仓恢复任意被删的 data 文件
git checkout origin/main -- data/industry_map.json
git checkout origin/main -- data/concept_map.json
git checkout origin/main -- data/candidate_pool.json
git checkout origin/main -- data/gold_pool.json

# 重新生成概念映射（如 industry_map 的 concepts 为空）
python fetch_concept_map.py
# 重新 enrich 股池 + 删退补新
python maintain_industry_map.py
```
