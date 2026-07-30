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
- **波动率观测**: `calc_volatility_watch.py`；20日年化波动率；5日 vs 20日；复合信号四色分类。
- **看门狗**: `data_freshness_watchdog.py` 监控 27 核心数据；market 类盘后 15:30 查。**每日 20:30 自动化自修复**(automation-1785047388251)：safe_pull → 重跑陈旧 fetch → update_data_v2.py --fast → push_china_data.py → deploy_now.py --force。
- **缺失待补**: `fetch_sector_rs.py` / `enhance_dist.py` 从未被调用；`fetch_concept_ranking.py` 一天仅 1 次；`fetch_etf_flow.py` 缺失导致 ETF 资金卡不更新。

## 自动化 / 安全
- **排班状态**: 2026-07-23 起阿狸咪家中机全天断线，**全部定时任务由小九（单位机·全天在线）全面接管**；`standalone/data_responsibility.html` 中「双机」= 小九单机跑双机职责，标注「代阿狸咪/🖥️」的即原属阿狸咪、现由小九顶上的任务。阿狸咪恢复联网后其本机 20+ 救援船任务会自动续跑。
- **v8 架构真相（2026-07-31 踩坑纠正）**：v8 **不是 v6 的子项目**，是两个独立仓——**v6 仓 `v8/` 子目录 = 开发+构建源**（index.html → update_v8.py 生成 dist/index.html），**`quant-scanner-v8` 独立仓 = 部署+服务**（GitHub Pages 从 main 出）。`v6/v8/deploy_v8.py` 第 11-12 行明写：源=`REPO/v8/dist/index.html`，目标=`git@github.com:ah-quant999:quant-scanner-v8.git` main。用户浏览器/本地 `quant-scanner-v8/index.html` = **部署版**（小九部署的旧版）；**阿狸咪改 v6/v8/index.html 源后必须等小九跑 update_v8 + deploy_v8 才生效**。present_files `v6/v8/index.html` = 预览源 ≠ 部署版。
- **模型 ID**: 全部自动化统一用 `hy3`（9:00-11:59）/ `deepseek-v4-flash`（12:00 后）。**严禁写入 `ds-V4-FLASH`**；`audit_automations.py` 每日 09:00/19:00 自动审计并修正。
- **北向资金**: 港交所 2024-05 后停止披露 top_buy，系统多处已标"停止"。
- **Cloud**: GitHub Actions 7 workflow 覆盖；Secret `ZSXQ_TOKEN`；候选池=主/创/科前 100 + 港前 50 + 观澜台 + maharo。

## 7-31 排程架构升级（v6 退役 / 云端优先 / 盘中 30 分钟）
- **v6 退役铁律**: 2026-07-31 起 **v6 模板不再改动**（`index_master.html` 不动），等 v8 运行稳定后**整 v6 删除**。双机铁律同步：v6 deploy 仅小九跑。
- **北向资金升级版（2026-07-31）**: **仅展示删**（v8 主页大卡 + 运维"数据新鲜度"表 + 异动监控表），**数据/脚本保留**（`fetch_north_fund.py` / `data/north_fund_*.json` 留作权重计算用），**计算权重里北向分仍保留**（仅标"停更"）。v6 旧 v6 上的北向大卡和运维行**保持原样不动**（v6 不再改）。
- **17:00 算法上云端**（2026-07-31）: `generate_recommend.py` grep 无 LLM 调用（openai/dashscope/qwen/llm 等），是普通计算+重建+部署——**完全能上 GitHub Actions**，**不耗 AI token**。
- **云端盘中扫描不齐**（2026-07-31）: `cloud_intraday.yml` 现有 cron = 9:30 / 10:31 / 11:46 / 13:31 / 14:31，**不是 30 分钟一次**。**缺 4 个整点**（10:00 / 11:00 / 13:00 / 14:00）。B+ 阶段需补。
- **云端已能部署**（2026-07-31 确认）: `cloud_scanner.yml`（18:31）+ `cloud_post_close.yml`（15:30/16:15/16:30）**内部已含 build + 推 gh-pages 步骤**，**不依赖** `pages.yml.disabled`（那个是 push 触发、已禁用）。
- **待 B / B+ 阶段**（2026-07-31 起）:
  - **B**: v8 `index.html` JS 改造，AI 速览 7 行读 JSON
  - **B+**: 新建 3 个云端 workflow（`cloud_premarket.yml` 08:30 / `cloud_close_ultralight.yml` 15:05 / `cloud_weekly_cleanup.yml` 周日 23:00）+ 改 `cloud_intraday.yml` 补 4 个整点
- **A 阶段已落地**（commit 90f75656, 2026-07-31 00:24）: v8 sec-rt 顶部插入 v6 风格 AI 速览 5 行（情绪/健康/指数/异动/期货；ETF+板块跳过因已有同类卡）+ 删运维北向行 + 删异动监控北向行；数字写死用 v6 周一 15:46 真实快照，**B 阶段接 JSON**。
