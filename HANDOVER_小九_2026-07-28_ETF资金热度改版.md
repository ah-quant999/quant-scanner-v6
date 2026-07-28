# 📋 交接：ETF资金热度卡片改造（方案C）— 小九→阿狸咪

**发件人**：小九（单位机）
**收件人**：阿狸咪（LEMONCAT 家里机）
**时间**：2026-07-28 17:39
**主人状态**：已下班，回家后将亲自做 v7 改版（redesign-v7/ 系列），本任务为 **v6 站内增强**，由阿狸咪今夜接手。

---

## 任务一句话
在 v6 总览区「国家队ETF」原位置，新增「📊 ETF资金热度」卡片，按 **宽基 / 行业 / 主题 / 跨境** 四分类展示盘中 T+0 榜单；原「国家队ETF」卡片移到健康看板 → 已下架区。主人选择的方案 = **方案C（分类细分）**。

---

## 当前状态（小九 17:39 现场核查，务必先读）
1. **index_master.html 总览区（line 631-639）仍有 `id="ntEtfFlowCard"` 国家队ETF卡片**，只是 `display:none` 隐藏，**未真正移到已下架区**。
2. **代码库里完全没有「ETF资金热度」卡片**（`renderETFIntradayHeat` / `etfHeatTime` / 字符串「ETF资金热度」全局搜不到）—— 疑似 07-28 13:00 被 deploy 内部 `safe_pull` 冲掉，需重做。
3. `data/etf_intraday_heat.json` 当前只有 `top_active`（成交额 TOP10）+ `top_inflow`（主力净流入 TOP10），**无 category 字段**。
4. `fetch_etf_intraday_heat.py` 当前只产出 TOP10，无分类逻辑。
5. `update_data_v2.py` 已有 `ETF_INTRADAY_HEAT` 注入占位（line 1527），无需大改，确认字段即可。

---

## 要做的改动（方案C 详细）

### ① fetch_etf_intraday_heat.py — 加分类
- 在 main() 里给每只 ETF 打 `category` 标签，分类规则（建议正则/关键词匹配，兜底归「其他」）：
  - **宽基**：沪深300 / 中证500 / 中证1000 / 创业板 / 科创50 / 上证50 / 深证成指 / 科创创业50 / 标普500 / 纳指 / 道琼斯 / 恒生指数 / MSCI 等
  - **行业**：证券 / 银行 / 医药 / 医疗 / 芯片 / 半导体 / 新能源 / 军工 / 消费 / 白酒 / 食品 / 地产 / 有色 / 煤炭 / 钢铁 / 化工 / 汽车 / 光伏 / 锂电 / 电力 / 养殖 / 传媒 等
  - **主题**：AI / 人工智能 / 机器人 / 算力 / 数字经济 / 央企 / 国企 / 红利 / 低碳 / 游戏 / 5G / 大数据 / 云计算 / 军工（若重叠行业优先行业）等
  - **跨境**：港股 / 中概 / 纳指 / 标普 / 道琼斯 / 日经 / 德国 / 法国 / 东南亚 / 越南 / 沙特 / 美股 / 恒生 / 韩国 / 印度 / 法国CAC 等
  - **商品**：黄金 / 原油 / 有色ETF / 豆粕 / 煤炭（若未被行业收走）
- 输出结构改为按 category 分组，每组取 TOP N（建议每类 TOP8）：
  ```json
  {
    "update_time": "...",
    "data_date": "...",
    "total": 1528,
    "categories": {
      "宽基":   {"top_active":[...], "top_inflow":[...]},
      "行业":   {"top_active":[...], "top_inflow":[...]},
      "主题":   {"top_active":[...], "top_inflow":[...]},
      "跨境":   {"top_active":[...], "top_inflow":[...]},
      "商品":   {"top_active":[...], "top_inflow":[...]},
      "其他":   {"top_active":[...], "top_inflow":[...]}
    },
    "summary": {"up":..., "down":..., "flat":..., "net_inflow_yi":...}
  }
  ```
- 保留 `amount` / `main_net_inflow` / `pct` / `code` / `name` 字段不变。

### ② update_data_v2.py — 确认注入
- `ETF_INTRADAY_HEAT` 占位已存在（line 1527），字段改为 categories 后无需改注入逻辑（整块 JSON 注入 `window.ETF_INTRADAY_HEAT`）。
- 空数据保护已有（line 1710 附近 `if not data.get("update_time")...`）。

### ③ index_master.html — 加卡片 + 移动国家队ETF
- **新增卡片**：在总览区 line 631-639 那块「ETF+板块 一行两列」网格的**左列**，替换/新增「📊 ETF资金热度」卡片（`id="etfHeatCard"`），内部按 宽基/行业/主题/跨境 四组渲染，每组两列（成交额TOP / 主力净流入TOP）。
- **移动国家队ETF**：把 `ntEtfFlowCard` 整块从总览区剪切到健康看板 → 已下架区（`delistedPanel`，即在 `renderHealthDashboard()` 的已下架分支里，shelf-group 结尾）。可保持 `display:none` 或改为 `display:block`（已下架区由 toggle 控制显隐，render 调用保留）。
- **红涨绿跌**：`.up`=红 `#e94560`，`.down`=绿 `#27ae60`（已是全局样式，渲染时套 class 即可）。
- **时间戳**：用 `setChartTime('etfHeatTime', t, 'etfHeat')` 显示真实抓取时间；`freshLabels` 需新增专用键 `etfHeat:'盘中实时·T+0'`（参考现有 `etfHeatTime` 用法，若未定义则新增 render 函数 `renderETFIntradayHeat()`）。
- **卡片自检表**（`pageAudit` 数组，line ~357400 附近）：总览区 `📊 ETF资金热度` 的 check 改为查 `etfHeatCard` 显隐；暂未上架/已下架区 `💰 国家队ETF(已下架)` 的 check 查 `ntEtfFlowCard` 显隐。

### ④ 构建 + 部署
- 必须 **全量** `update_data_v2.py`（不能 `--fast`，否则 dist 不重建）。
- 再 `deploy_now.py --force`（跳过 pre-deploy audit，非数据闸门）。
- 部署后 `git ls-remote origin gh-pages` 核验 SHA。

---

## 铁律（必读，违反会被 safe_pull 冲掉）
- **改 index_master.html 后必须立即 `git add + commit + push origin main`**。deploy 内部 `safe_pull` 跑 `git reset --hard origin/main`，未入库改动会被静默还原（07-28 13:00 已下架 TAB 改造就是这么被冲掉的，修复 commit db17b4d5）。
- **绝不要 `git add` / 提交 `.neodata_token`**（已 gitignored，严禁进仓库）。
- **主站构建源 = index_master.html**。根 `index.html` 无效；改 UI 只在 index_master.html。
- **改完必须全量 update_data_v2.py 重建再 deploy**，不能 --fast。
- 红涨绿跌配色不要反。

---

## 验证清单（部署后）
- [ ] 线上总览区出现「📊 ETF资金热度」卡，宽基/行业/主题/跨境四组齐全，每组有成交额TOP + 主力净流入TOP
- [ ] 卡片时间戳显示今日盘中（T+0），非陈旧
- [ ] 健康看板 → 已下架区可见「💰 国家队ETF」卡片
- [ ] `data/etf_intraday_heat.json` 含 `categories` 字段且 update_time 为今日盘中
- [ ] gh-pages SHA 已更新

---

## 主人自己做的部分（阿狸咪不要碰）
- **v7 改版**（redesign-v7/ 设计稿 + 新仓库 quant-scanner-v7 + 前端模块化）由主人回家后亲自做。
- 本任务只是 v6 站内增强，不要并入 v7 工作。

---

—— 小九 🛠️ 2026-07-28 17:39
