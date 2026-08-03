# 九宝量化 — 项目长期备忘录（精简版）

## 环境关键事实
- **Python**: WorkBuddy 托管 `3.13.12`（自动化）+ 系统 `3.14.3`（默认）。**两个 base 都必须能 import mootdx**；build_candidate_pool.py 已加 `GTimg` 回退 + `SKIP_MOOTDX=1` 环境变量可直走 akshare。
- **HTTP 重试预算**: 单只/单点重试+休眠 ≤ 2s。东财/腾讯/新浪/akshare 单次尝试 + 异常即返回 None + 名称回退；akshare 已 monkey-patch `(15,60)` 超时。
- **repo-temp**: `E:\workspace\stock-scanner\repo-temp` 是 `D:\stock-scanner-repo\repo-temp` 的 junction，路径差异正常。

## Git / 部署铁律（按顺序执行，违反即假成功/数据回退）
1. **改源码后必须**：`git add -f <文件>` → `git commit` → `git push origin main` → 再跑 `deploy_now.py --force`。**deploy 第 0 步会 checkout origin/main 覆盖 `index_master.html` + `update_data_v2.py`**，未 push 则修改被擦。
2. **dist 同步**: `dist/` 被 git 跟踪。`deploy_now.py` 的 `_auto_push_source()` **必须在 gh-pages 推送 + dist 重建全部完成后**调用（原 bug：过早调用在 `_ensure_dist_fresh` 之前 + 第5步 `return 0` 漏调用，导致重建后的 dist 永远不进 main、工作区每次残留 dirty）。2026-07-25 已修复（fc50d387）。现在每次部署自动把最新 dist commit+push 到 main，回退源总是最新。**改 deploy_now.py 后必须自测一次：部署后 `git status` 应干净**。
3. **gh-pages 推送**: 必须用 `subprocess.run([...], cwd=tmpdir)` 列表形式 + `--force`；严禁 `cd ... && git push` shell 形式（cmd 会把 `/U` 当开关，导致假成功/线上不更新）。
4. **数据新鲜度闸门（2026-07-25 升级）**: `deploy_now.py` 新增**内容级**校验：扫描 `data/*.json` 内部 `update_time` vs 最近交易日收盘，核心源（crisis/fomc/候选池/涨停/板块/北向）过期即阻断；网络易抖（concept_map）/需交互登录（maharo）仅告警不阻断，避免一陈旧就冻结整次部署。
5. **safe_pull 坑（2026-07-28 踩）**: `git_safe_sync.py::safe_pull()` 本质是 `git reset --hard origin/main`，**会连本地未推送的 commit 一起清掉**（工作区改动也丢）。云端自动化持续 push（heartbeat/cloud_*），remote 永远在前，一旦本地 commit 未 push 就跑 safe_pull，改动即被吞。**正确推送姿势**：`git add -f` → `git commit` → `git fetch origin` → `git rebase origin/main`（保留本地 commit）→ `git push origin main`。**仅当需要拉取远端他人改动且本地无未推送 commit 时**才用 safe_pull。禁止手写 `git pull --autostash`/`stash pop`。`rebase.autoStash=false`。
6. **git add -f**: `.gitignore` 用 `!脚本.py` 白名单放行根 .py；新增 .py / HTML / data 必须 `git add -f`，否则静默忽略。
7. **SSH 超时**: `export GIT_SSH_COMMAND="ssh -o ConnectTimeout=15"`。

## 代码 / 数据规范
- **防误删**: `DO_NOT_DELETE.md` 清单 + pre-commit hook（双机各自 `cp git_hooks/pre-commit .git/hooks/pre-commit && chmod +x`）。
  - ⚠️ **删除受保护文件的正确姿势（2026-07-26 踩坑）**：pre-commit hook 读 `DO_NOT_DELETE.md`，凡删除清单内文件即 `exit 1` 拦截提交。若要从仓库移除某个被清单保护的文件（如误进 dist/ 的凭据），**必须先 edit `DO_NOT_DELETE.md` 移除对应行，再 `git rm`+`git commit`**；否则 commit 会被 hook 静默拦下（且 hook 较慢会让外部工具把 commit 命令后台化截断，误判"提交成功/无改动"）。紧急可用 `git commit --no-verify` 绕过 hook。凭据类文件（`.wc_jwt_cache.json`/`maharo_signals.json`）已从清单移除。
- **交接文档**: 根目录写 `HANDOVER_小九_YYYY-MM-DD.md` / `HANDOVER_阿狸咪_YYYY-MM-DD_时段.md`；禁用旧 MSG_TO_ALIMI_*.md / repo-temp 下。
- **内部脚本名/数据源铁律（2026-07-28 升级）**: 用户面板、逻辑详解页、任何用户可见文本**一律不得暴露**具体数据源、脚本路径、本地/远端文件名、机器节点、跑批时间或内部 API 名称。原型页（v8-prototype）同样适用。数据流细节只写 HANDOVER + 代码注释；前端仅保留指标口径、相对时间、通用说明。
- **"更新于"铁律**: 所有面板必须显示相对日期 `今日/昨日/X天前`+时分，绝不写 `MM-DD HH:MM` 裸日期。驾驶舱用 `_fmtCockpitRel(ts)`，其余用 `fmtDataTime`；改模板必须同步全部 15/16 个 HTML。
- **涨跌色**: 红涨绿跌，空数据 `available=false` 不造假。

## 关键数据源与脚本
- **mootdx 挂起**: `client.bars()` 不释放 socket，每 50 次调用重建客户端 + `gc.collect()` + `_tdx_lock`。
- **板块资金流**: 东财(akshare)主 → neodata 备 → westock 第三源。
- **基本面质量分**: `data/fundamental_quality.json`；A=+40/B=+5/D=-10/C=0；key=`{market}_{code}`。A档阈值已对齐真实上限 70（原 80 死档）。
- **危机雷达**: 货币0.40+经济0.35+全球0.25；档位 0-30/30-50/50-70/70-100。
- **v8 数据结构陷阱（2026-08-02 踩）**：`candidate.json`/`gold_pool.json` 的 `stocks` 永远是 **dict**（`{market}_{code}→obj`）**不是 array**。直接 `.slice/.filter/.map` 全 `TypeError`。v8 `index.html` 已加 `_rcArr()` 工具（array 直传、dict 转 `Object.values`、其他返 `[]`），**新写渲染代码前先验证数据结构 + 用 _rcArr 包一层**。LHB/MAHORO/INST_TRADE 的 `stocks` 才是 array。
- **v8 前端数据源口径（防踩坑）**: `candidate.json.stocks` 仅含 `code/name/market/board_label/sources/industry/concepts/board/sectors`，**无 `score/inst_net_万/yz_net_万/reasons/tags`**；机游共振真实数据在 `lhb_data.json.stocks`（`inst_net_万`+`yz_net_万`+`pct`+`category`+`seats`）。前端 render 要取机构/游资净买必须走 `lhb_data`，不能走 `candidate`。板块资金流看 `sector_fund_flow.json.top_list`（type=行业/概念，net 单位亿）。
- **波动率观测**: `calc_volatility_watch.py`；20日年化波动率；5日 vs 20日；复合信号四色分类。
- **看门狗**: `data_freshness_watchdog.py` 监控 27 核心数据；market 类盘后 15:30 查。**每日 20:30 自动化自修复**(automation-1785047388251)：safe_pull → 重跑陈旧 fetch → update_data_v2.py --fast → push_china_data.py → deploy_now.py --force。
- **缺失待补**: `fetch_sector_rs.py` / `enhance_dist.py` 从未被调用；`fetch_concept_ranking.py` 一天仅 1 次；`fetch_etf_flow.py` 缺失导致 ETF 资金卡不更新。

## 自动化 / 安全
- **排班状态（2026-08-03 锁定·长期架构）**: 彻底改为**「小九单机（单位机）+ GitHub Actions 云端」**，**阿狸咪（家里机）即使恢复联网也绝不接手任何生产任务**，避免双机重复跑的麻烦。`standalone/data_responsibility.html` 中「双机」= 小九单机跑双机职责，标注「代阿狸咪/🖥️」的即原属阿狸咪、现由小九顶上的任务（长期生效，不再恢复双机分工）。阿狸咪本机 23 个 automation 现已全部 PAUSED（含原"周末云端监督与兜底部署" automation-1785510427927），仅保留"紧急指令监听"(automation-1783696499491) 作为主人的兜底呼叫通道（监听≠接手生产，不会与小九重复）。**若阿狸咪误上线导致其任务跑起来，立即 PAUSE 她本机 automation**。
- **v8 架构真相（2026-07-31 踩坑→已分离，2026-08-01 收尾分支）**：v8 与 v6 是**两个独立仓**。**`quant-scanner-v8` 独立仓 = v8 唯一开发+部署源**（GitHub Pages 从 main 出，自身 deploy_v8.py 推 index.html+data/*）。**2026-07-31 已删除 v6 仓 `v8/` 子目录**；**2026-08-01 已删除** `stock-scanner` 的 `origin/v8-temp` 与 `quant-scanner-v8` 的 `v8` 快照分支，两仓现均**只保留 `main` 作为 v8 真相源**。从此 v6 是 v6、v8 是 v8，任何 v8 模板/数据改动必须进 `quant-scanner-v8/main`。git 历史保留可恢复。
- **模型 ID**: 全部自动化统一用 `hy3`（9:00-11:59）/ `deepseek-v4-flash`（12:00 后）。**严禁写入 `ds-V4-FLASH`**；`audit_automations.py` 每日 09:00/19:00 自动审计并修正。
- **北向资金**: 港交所 2024-05 后停止披露 top_buy，系统多处已标"停止"。
- **Cloud**: GitHub Actions 8 workflow 覆盖（v8 侧：`v8_cn_fetch` / `v8_build_deploy` / `v8_algo` / `v8_sync_v6_data` / `cloud_weekly_cleanup`）；Secret `ZSXQ_TOKEN`；候选池=主/创/科前 100 + 港前 50 + 观澜台 + mahoro。
- **v8 已完全脱离 v6（2026-08-03 锁定·最终状态）**: v8 **自包含**,正常运营无任何 v6 运行时依赖。数据生产 = `cloud_fetch_v8.py`(实时/盘前 22 模块) + `algorithms/run_algorithms.py` 原生算法链(盘后/选股/共振)。原 `sync_v6_to_v8.py` 同步桥仅作 `V6_TO_V8` 映射辅助(被 `stage_to_raw.py` 导入,不读 v6);两条拉 v6 工作流 `v8_sync_v6_data.yml`/`v8_sync_legacy.yml` 已 `if:false` 变 inert。**v6 仓已可退役**(git 归档/只读)。分支 `feat/v8-detach-v6`(bb17bf7) 待小九验证全链自包含后 merge 到 main。
- **⚠️ v8 算法铁律(2026-08-03 新增)**: **v8 的算法脚本是带原生钩子的增强版(比 v6 新、含多处修复),任何 v8 算法改动只在 `quant-scanner-v8` 仓做;严禁把 v6 的算法代码覆盖/复制回 v8**(`migrate_v6_algos.py` 已警告"切勿重跑覆盖")。v8 缺资产只补"v8 真没有的"(如 westock 拉取器、历史累加器),不整体搬 v6。

## 8-01 v8 分时段 + v6 同步桥架构（轻量/防臃肿）
- **v8 定时任务矩阵（北京时间）**:
  - 08:25 `v8_cn_fetch.yml` 盘前（akshare）【注:`v8_sync_v6_data.yml` 已于 08-03 `if:false` 停用,不再跑】
  - 10:30/11:30/13:05/14:00/15:05 `v8_cn_fetch.yml` 盘中（含 ETF_DAILY_MONITOR）
  - 15:30 `v8_cn_fetch.yml` 收盘数据（EXPERIMENT）
  - 19:00 【原 `v8_sync_v6_data.yml` 盘后同步,已于 08-03 停用;盘后数据现由 `v8_algo_run` 18:30 原生算法链产出】
  - 17:00 `v8_build_deploy.yml` 盘后算法换算部署 + `v8_algo.yml` 数据体检
  - 周六 21:00 `cloud_weekly_cleanup.yml` 清理 orphan（并入周六 T+1 维护窗口）+ 周日 23:00 `v8_cleanup.yml` 清缓存/修剪心跳日志（删除无用记录）
- **selective build**: `update_v8.py --category/--detect-changes` 只构建目标时段或变化 raw_data 所属类别，避免每次全站重部署。
- **v6 同步桥(已退役·2026-08-03)**: `sync_v6_to_v8.py` 仅作 `V6_TO_V8` 映射辅助(被 `stage_to_raw.py` 导入复用,自身 `sync()` 不再被调用);`v8_sync_v6_data.yml`/`v8_sync_legacy.yml` 已 `if:false` 变 inert。v8 全量数据现由原生链自产,v6 仓可退役。
- **北向资金升级版（2026-07-31）**: **仅展示删**（v8 主页大卡 + 运维"数据新鲜度"表 + 异动监控表），**数据/脚本保留**（`fetch_north_fund.py` / `data/north_fund_*.json` 留作权重计算用），**计算权重里北向分仍保留**（仅标"停更"）。v6 旧 v6 上的北向大卡和运维行**保持原样不动**（v6 不再改）。
- **待 B / B+ 阶段**:
  - **B**: v8 `index.html` JS 改造，AI 速览 7 行读 JSON；给 44 个 `<script>` 加 defer/首屏优先级。
  - **B+**: 处理 SH_SZ_HISTORY 硬编码内联；给 5 个模块补时间戳；cloud_fetch 加备用源。
