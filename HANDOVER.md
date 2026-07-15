# 📋 九宝量化数据更新交接手册

**版本**：v1.0  
**更新时间**：2026-07-03  
**适用人员**：小九（阿狸咪）  
**项目路径**：`E:\workspace\stock-scanner\`

---

## 🎯 核心任务

**每天早上把最新数据更新到网站**，让主人打开 `https://ah-quant999.github.io/quant-scanner-v6/` 能看到当天的数据。

---

## ⏰ 数据更新时间表

| 时间段 | 任务 | 说明 |
|--------|------|------|
| **07:30** | 更新世界盃数据 | `fetch_worldcup_data.py` |
| **09:15** | 第一次扫描 | `scanner.py` → 更新 `scan_result.json` |
| **09:25** | 更新打新/北向/龙虎榜 | `fetch_ipo_data.py`, `fetch_north_flow.py`, `fetch_lhb.py` |
| **09:45** | 第二次扫描 | `scanner.py` |
| **11:00** | 第三次扫描 | `scanner.py` |
| **13:45** | 第四次扫描 | `scanner.py` |
| **14:30** | 第五次扫描 | `scanner.py`（收盘前最后一次） |
| **17:00** | 更新龙虎榜/公告/研报 | `fetch_lhb.py`, `fetch_announcements.py` |
| **20:30** | 第六次扫描 + 部署 | `scanner.py` → `update_data_v2.py` → `deploy_now.py` |

**简化版（最小执行）**：
- **09:25**：运行 `fetch_ipo_data.py` 和 `fetch_north_flow.py`
- **14:30**：运行 `scanner.py`
- **20:30**：运行 `update_data_v2.py` + `deploy_now.py`

---

## 🚀 标准操作流程（每日必做）

### 步骤1：打开终端

```bash
cd E:\workspace\stock-scanner
```

### 步骤2：更新数据

```bash
# 方法A：运行完整数据更新（推荐）
python update_data_v2.py

# 方法B：分别运行各脚本（如果方法A报错）
python scanner.py              # 扫描股票
python fetch_ipo_data.py       # 打新数据
python fetch_north_flow.py     # 北向资金
python fetch_lhb.py            # 龙虎榜
python fetch_sector_fund_flow.py  # 板块资金流
```

### 步骤3：部署到网站

```bash
python deploy_now.py
```

### 步骤4：验证

1. 打开浏览器访问 `https://ah-quant999.github.io/quant-scanner-v6/`
2. 按 `Ctrl + Shift + R` 强制刷新
3. 检查 `数据更新时间` 是否显示当天时间

---

## 📂 关键文件说明

### 数据文件（`data/` 目录）

| 文件 | 说明 | 更新频率 |
|------|------|---------|
| `scan_result.json` | 扫描结果（核心） | 每2小时 |
| `watch_result.json` | 监控池结果 | 每2小时 |
| `gold_pool.json` | 金股池 | 每2小时 |
| `stock_names.json` | 股票名称映射 | 每日一次 |
| `industry_map.json` | 板块映射 | 每周一次 |
| `ipo_score.json` | 打新评分 | 每日一次 |
| `lhb_result.json` | 龙虎榜结果 | 每日17:00 |
| `etf_subscription.json` | ETF净申赎 | 每日 |
| `worldcup.json` | 世界杯数据 | 每日07:30 |
| `lottery_data.json` | 彩票数据 | 静态（无需更新） |

### 脚本文件（根目录）

| 脚本 | 说明 |
|------|------|
| `scanner.py` | 核心扫描脚本（生成 scan_result.json 等） |
| `update_data_v2.py` | **数据注入脚本**（把 data/*.json 注入到 dist/index.html） |
| `deploy_now.py` | **部署脚本**（git add + commit + push） |
| `fetch_*.py` | 各类数据获取脚本 |

---

## ⚠️ 常见问题排查

### 问题1：`python` 命令找不到

**现象**：
```
'python' 不是内部或外部命令
```

**解决**：
```bash
# 检查 Python 是否安装
python --version

# 如果没安装，从这里下载：
# https://www.python.org/downloads/
```

---

### 问题2：`update_data_v2.py` 运行报错

**现象**：
```
ModuleNotFoundError: No module named 'pypinyin'
```

**解决**：
```bash
pip install pypinyin requests akshare baostock
```

---

### 问题3：`deploy_now.py` 运行报错

**现象**：
```
git: 'push' failed
```

**可能原因**：
1. 没有 GitHub 权限
2. 网络问题（国内访问 GitHub 不稳定）

**解决**：
```bash
# 检查 Git 配置
git remote -v

# 手动推送
git add dist/index.html
git commit -m "update: 每日数据更新"
git push origin main

# 如果网络问题，重试几次
```

---

### 问题4：网站显示旧数据

**现象**：部署成功，但网站显示昨天的数据

**原因**：
1. 浏览器缓存
2. GitHub Pages 部署延迟（通常1-2分钟）

**解决**：
1. 强制刷新：`Ctrl + Shift + R`
2. 等待2分钟后再检查
3. 检查 `dist/index.html` 的 `SCAN_DATA` 中的 `scan_time` 是否是最新时间

---

### 问题5：`scanner.py` 运行太慢

**现象**：运行超过10分钟还没结束

**原因**：
- akshare API 响应慢
- 网络问题

**解决**：
```bash
# 直接运行 update_data_v2.py（它会用已有的 data/*.json）
python update_data_v2.py

# 如果还是慢，跳过 scanner.py，直接用旧数据部署
python update_data_v2.py --skip-scan
```

---

### 问题6：坚果云同步冲突

**现象**：文件上有红色感叹号，或提示"冲突"

**解决**：
1. 右键冲突文件 → "解决冲突"
2. 选择"保留我的版本"或"保留对方版本"
3. 如果不确定，保留**最新的版本**（修改时间最近的）

---

## 🔧 紧急修复指南

### 场景1：网站完全打不开

**检查**：
1. GitHub Pages 服务是否正常：访问 `https://www.githubstatus.com/`
2. 仓库是否被删除：访问 `https://github.com/ah-quant999/quant-scanner-v6`

**修复**：
```bash
# 重新部署
cd E:\workspace\stock-scanner
git status
git add dist/index.html
git commit -m "fix: 重新部署"
git push origin main
```

---

### 场景2：数据文件丢失

**检查**：
```bash
ls -lh data/*.json
```

**修复**：
1. 从 Git 历史恢复：
   ```bash
   git checkout HEAD~1 -- data/scan_result.json
   ```
2. 重新运行脚本：
   ```bash
   python scanner.py
   ```

---

### 场景3：Git 仓库损坏

**现象**：
```
fatal: not a git repository
```

**修复**：
```bash
# 重新克隆仓库
cd E:\workspace
mv stock-scanner stock-scanner.bak
git clone git@github.com:ah-quant999/quant-scanner-v6.git
cd stock-scanner
# 复制数据文件回来
copy ..\stock-scanner.bak\data\*.json data\
```

---

## 📞 紧急联系方式

**主人**：阿狸咪  
**项目仓库**：`https://github.com/ah-quant999/quant-scanner-v6`  
**网站地址**：`https://ah-quant999.github.io/quant-scanner-v6/`

**如果以上方法都无法解决，立即联系主人！**

---

## ✅ 每日检查清单

- [ ] `python --version` 能正常运行（Python 3.8+）
- [ ] `cd E:\workspace\stock-scanner` 能进入项目目录
- [ ] `git remote -v` 能显示 GitHub 地址
- [ ] `data/*.json` 文件存在且有内容（不是空文件）
- [ ] `python update_data_v2.py` 能成功运行
- [ ] `python deploy_now.py` 能成功推送
- [ ] 网站能正常访问且显示最新数据

---

## 📝 备注

1. **密码**：网站有密码保护，主人输入密码后能看到完整内容
2. **无痕模式**：每次都会要求输入密码（正常行为）
3. **数据延迟**：GitHub Pages 部署需要1-2分钟，请耐心等待
4. **网络问题**：如果 GitHub 访问不稳定，可以多试几次 `git push`

---

**祝小九明天顺利！有任何问题立即联系主人。** 🎉
