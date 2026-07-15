# 📢 给阿狸咪 — 2026-07-15 改造汇总

## 一句话
**所有改动已 push 到 origin/main，你 `git pull` 即可拿到。云端主力跑，你和小九只监控观察。**

---

## 1. 架构变更 ⭐ 最重要

**之前**：小九本机 09:20 兜底检查（和云端同时启动，互相覆盖，监控无效）

**现在**：本机改为**全时段健康监控 + 兜底**
- 每 30 分钟检查一次云端是否正常（09:00~16:30）
- 云端超过 75 分钟无成功部署 → 本机自动补跑 + 强制部署
- 云端 30 分钟内刚部署过 → OK，跳过
- 30~75 分钟 → 宽限期，等待
- 早晨 10:00 前云端没部署 → 给云端 09:20 留窗口，不触发

**对你的影响**：如果你那边也有类似的 09:20 盘前兜底自动化，**请停用或删除**，否则会和云端同时跑、互相覆盖。

---

## 2. 云端 workflow 更新（GitHub Actions）

所有 yml 文件都已推送到 origin/main，你在 GitHub 上能看到：
- `cloud_intraday.yml` — 盘中 5 槽（09:20/10:31/11:46/13:31/14:31）
- `cloud_post_close.yml` — 收盘 3 槽（15:30/16:15/16:30）
- `cloud_data_fetch.yml` — 17:31 抓取（无部署）
- `cloud_scanner.yml` — 18:31 扫描+部署
- `cloud_weekly.yml` — 周任务（周日 06:30 / 周五 19:30 / 周六 07:30）
- `cloud_worldcup.yml` — 世界杯（07:30）
- `safety-net.yml` — 自检（09:15/10:00/11:45/14:30/19:30/21:00）

| 文件名 | 变更 | 原因 |
|---|---|---|
| cloud_intraday.yml | 新 workflow（替代旧的多个 yml） | 统一盘中任务 |
| cloud_data_fetch.yml | 新 workflow | 收盘数据抓取 |
| cloud_post_close.yml | 新 workflow | 收盘分阶段处理 |
| safety-net.yml | 新 workflow | 站点健康自检 |
| 其他 yml | 不变 | — |

---

## 3. ZSXQ_TOKEN 已补到 GitHub Secrets ✅

之前的 token 为空导致 `#1~#3` 盘中任务失败。现已补填：
- Secret Name：`ZSXQ_TOKEN`
- 值在你本机 `data/zsxq_token.json` 的 `"token"` 字段

如果你那边也需要用（比如本地跑 guanlan 脚本）：
```
data/zsxq_token.json 里复制 token 值。
```
token 是 7 月 7 日的，如果过期了需要重新抓。

---

## 4. 本机代码变更

| 文件 | 改了什么 |
|---|---|
| `pre_market_cloud_failover.py` | 从"盘前 09:20 硬编码"改为 **全时段监控**（75 分钟阈值 + 30 分钟宽限 + 早上 10:00 前宽限） |
| `fetch_neodata_daily.py` | （之前已有）每日 17:31 跑 3 张 neodata 表 + 部署 |
| `index_master.html` | 右下角"运维状态"浮窗移入「暂未上架」面板（admin-only，访客不可见） |
| `calc_crds.py` | 新增 `get_market_context()`，CRDS 卡片新增大盘有效性判断 |
| `standalone/guide.html` | CRDS 逻辑详解页新增大盘有效性判断表 |
| `update_data_v2.py` | 新增 OPS_STATUS 数据注入逻辑 |
| `.gitignore` | `data/*` → 白名单 `!data/*.json`，放开 neodata 数据文件 |

---

## 5. 你那边需要注意的

### ✅ 必须做的
1. **`git pull origin main`** 拉最新代码
2. 如果 WorkBuddy 里有「09:20 盘前兜底」类自动化 → **停用或删除**（已被全时段监控替代）

### ✅ 建议做的
3. 打开 https://github.com/ah-quant999/quant-scanner-v6/settings/secrets/actions 确认 `ZSXQ_TOKEN` 是否存在（已补，你确认一下就行）
4. 今晚 18:31 观察云端 `cloud_scanner.yml` 是否成功（GitHub Actions 页面有绿✓就正常）

### ⚠️ 注意
- **本机兜底和云端互不冲突**：你那边如果也有部署脚本，**别在云端定时时间点（09:20/10:31/11:46/13:31/14:31/15:30/16:15/16:30/18:31）手动 deploy**，会和云端抢 gh-pages 分支
- **neodata token**：本机 17:25 自动刷 token、17:31 抓表+部署。如果你也开这个，确保两机不同时跑（错开时间）
- **旧备份 PAUSED 保留**：仓库里的旧备份自动化（盘中槽位备份等）全部继续 PAUSED，不要删。如果哪天 GitHub Actions 挂了，可以一键激活回到"本机独立运行"模式

---

## 6. 当前线上状态（验证用）

打开 https://ah-quant999.github.io/quant-scanner-v6/ -> 🔐 健康看板 -> 📦 暂未上架

| 卡片 | 当前值 |
|---|---|
| 最后部署 | 20260715165037 |
| 盘前兜底状态 | OK |
| neodata 令牌有效至 | 2026-07-16 10:01 |

---

## 7. 一句话总结

> 云端主力部署（09:20~18:31 共 11 次），本机只做三件事：
> ① 每 30 分钟盯着云端是否活着（75 分钟没动静就兜底）
> ② 17:31 补跑 neodata 三张表（云端拿不到 token）
> ③ 19:45 跑实验数据（三重选股，暂未上架）
>
> 你 git pull 后什么都不用做，观察就行。

有问题告诉我或小九。🫡
