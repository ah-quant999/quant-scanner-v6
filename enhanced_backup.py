#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚡ 九宝量化 21:00 增量审核+备份脚本
=============================================
🔴 核心原则：只审今天新增/修改的，不重复检查已审核过的。
   每天审核在前，备份在后，审核不阻断备份。

流程：
  🔴 0. 最优先：双机代码同步 (git pull/push)
  📊 1. Git变更分析：找出今天改了什么
  📊 2. 增量审计：只审核变更涉及的模块
  💾 3. 备份（永远执行，不受审计影响）
"""

import os, sys, json, re, datetime, shutil, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, 'data')
DIST_DIR = os.path.join(BASE, 'dist')
TODAY = datetime.datetime.now().strftime('%Y%m%d')
TODAY_DATE = datetime.datetime.now().strftime('%Y-%m-%d')

# ═══════════════════════════════════════════════════════════
# 🔴 0. 双机代码同步（最重要，必须放最前）
# ═══════════════════════════════════════════════════════════
def sync_dual_machine():
    """阿狸咪↔小九 代码同步"""
    print("=" * 60)
    print("🔴 步骤0: 双机代码同步（最重要）")
    print("=" * 60)
    
    issues = []
    try:
        r = subprocess.run(['git', 'add', '-A'], cwd=BASE, capture_output=True, text=True, timeout=30)
        r = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=BASE, timeout=30)
        has_changes = r.returncode != 0
        
        if has_changes:
            r = subprocess.run(['git', 'commit', '-m', f'auto: 审核备份前提交 ({TODAY_DATE})'], 
                             cwd=BASE, capture_output=True, text=True, timeout=30)
        
        r = subprocess.run(['git', 'pull', '--rebase', 'origin', 'main'], 
                         cwd=BASE, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            issues.append("git pull 失败")
            print(f"  ⚠ git pull 失败")
        else:
            print(f"  ✓ git pull origin main")
        
        r = subprocess.run(['git', 'push', 'origin', 'main'], 
                         cwd=BASE, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            issues.append("git push 失败")
            print(f"  ⚠ git push 失败")
        else:
            print(f"  ✓ git push origin main")
    
    except Exception as e:
        issues.append(f"git异常: {e}")
        print(f"  ✗ git异常: {e}")
    
    return issues


# ═══════════════════════════════════════════════════════════
# 📊 1. Git变更分析
# ═══════════════════════════════════════════════════════════
def analyze_changes():
    """分析今天的 git 变更，返回受影响的模块列表"""
    print("\n" + "=" * 60)
    print("📊 步骤1: 分析今日变更")
    print("=" * 60)
    
    affected = set()
    
    try:
        # 获取今天修改的文件
        r = subprocess.run([
            'git', 'log', '--oneline', '--name-only', 
            '--since', f'{TODAY_DATE} 00:00', '--until', f'{TODAY_DATE} 23:59'
        ], cwd=BASE, capture_output=True, text=True, timeout=15)
        
        changed_files = [f.strip() for f in r.stdout.split('\n') if f.strip() and not f.startswith(('commit ', 'Author:', 'Date:', '    '))]
        changed_files = [f for f in changed_files if not f.startswith(('Merge', 'auto:'))]
        
        if not changed_files:
            print("  今天无代码变更（周末/假期正常），跳过增量审计")
            return []
        
        print(f"  今日变更文件: {', '.join(set(changed_files))}")
        
        # 映射文件→模块
        for f in changed_files:
            fname = os.path.basename(f)
            
            if 'index_master.html' in f or 'index.html' in f:
                affected.add('前端主页面')
            if 'triple_resonance' in f:
                affected.add('历史追踪')
            if 'lhb' in f or '龙虎榜' in f:
                affected.add('龙虎榜')
            if 'macro' in f or '宏观' in f:
                affected.add('宏观观测')
            if 'herding' in f:
                affected.add('主力抱团')
            if 'sector_fund' in f or '板块' in f:
                affected.add('板块资金')
            if 'main_stock' in f or '主力' in f:
                affected.add('主力动向')
            if 'margin' in f or '两融' in f:
                affected.add('两融数据')
            if 'etf' in f:
                affected.add('ETF申赎')
            if 'nt_data' in f:
                affected.add('国家队')
            if 'lhb_seats' in f or 'lhb_result' in f:
                affected.add('龙虎榜数据')
            if 'gold_pool' in f or 'recommend' in f or 'scanner' in f:
                affected.add('选股信号')
            if 'data/' in f and f.endswith('.json'):
                module = os.path.splitext(fname)[0].replace('_', ' ')
                affected.add(module)
        
        if affected:
            print(f"  受影响的模块: {', '.join(sorted(affected))}")
        else:
            print(f"  变更未关联到具体模块")
        
    except Exception as e:
        print(f"  ✗ 变更分析失败: {e}")
    
    return sorted(affected)


# ═══════════════════════════════════════════════════════════
# 📊 2. 增量审计（只检查受影响的模块）
# ═══════════════════════════════════════════════════════════
def incremental_audit(affected_modules):
    """根据变更模块，执行有针对性的审计"""
    if not affected_modules:
        return {}
    
    print("\n" + "=" * 60)
    print("📊 步骤2: 增量审计（仅审今日变更）")
    print("=" * 60)
    
    all_issues = {}
    
    # 审计映射：模块名 → 审计函数
    audit_map = {
        '历史追踪': audit_history,
        '宏观观测': audit_macro,
        '两融数据': audit_margin_conflict,
        'ETF申赎': audit_margin_conflict,
        '前端主页面': audit_frontend_page,
    }
    
    # 去重执行
    executed = set()
    for module in affected_modules:
        audited = False
        for key, func in audit_map.items():
            if key in module and key not in executed:
                all_issues[key] = func()
                executed.add(key)
                audited = True
                break
        
        if not audited:
            print(f"  - {module}: 无需专项审计（数据文件或脚本变更）")
    
    return all_issues


# ═══════════════════════════════════════════════════════════
# 专项审计函数（精简版，只检查关键项）
# ═══════════════════════════════════════════════════════════

def audit_history():
    """历史追踪：检查假期列表+最新数据完整性"""
    print(f"  📋 历史追踪...")
    issues = []
    
    holidays_2026 = {
        '2026-01-01', '2026-01-02', '2026-01-28', '2026-01-29', '2026-01-30',
        '2026-02-03', '2026-02-04', '2026-04-06', '2026-05-01', '2026-05-04',
        '2026-05-05', '2026-06-19', '2026-10-01', '2026-10-02', '2026-10-03',
        '2026-10-06', '2026-10-07',
    }
    
    def is_trading(d): 
        if d in holidays_2026: return False
        return datetime.datetime.strptime(d, '%Y-%m-%d').weekday() < 5
    
    json_path = os.path.join(DATA_DIR, 'triple_resonance_history.json')
    if not os.path.exists(json_path):
        return ["历史数据文件不存在"]
    
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # 只检查最新7天
        dates = sorted(data.keys())[-7:]
        for d in dates:
            if not is_trading(d):
                issues.append(f"非交易日有数据: {d}")
        
        # 检查最新数据完整性（只查 enter_date/duration_days）
        for d in dates:
            for s in data[d]:
                if not s.get('enter_date') or not s.get('duration_days'):
                    issues.append(f"{d} {s.get('name','?')} 字段缺失")
                    break
        
        if not issues:
            print(f"    ✓ 最新{len(dates)}天正常")
    except Exception as e:
        issues.append(f"历史数据异常: {e}")
        print(f"    ✗ {e}")
    
    return issues


def audit_macro():
    """宏观观测：检查指标是否完整"""
    print(f"  🌍 宏观观测...")
    issues = []
    
    macro_path = os.path.join(DATA_DIR, 'macro_data.json')
    if not os.path.exists(macro_path):
        return ["宏观数据不存在"]
    
    try:
        with open(macro_path, 'r') as f:
            data = json.load(f)
        
        # 检查四大类是否完整
        sections = ['monetary', 'global_macro', 'market_sentiment', 'economy']
        for sec in sections:
            if not data.get(sec):
                issues.append(f"宏观{sec}缺失")
        
        if not issues:
            print(f"    ✓ 四大类完整")
    except Exception as e:
        issues.append(f"宏观数据异常: {e}")
    
    return issues


def audit_margin_conflict():
    """检查两融+ETF写入冲突"""
    print(f"  📊 两融/ETF...")
    issues = []
    
    etf_path = os.path.join(BASE, 'fetch_margin_etf.py')
    if os.path.exists(etf_path):
        with open(etf_path, 'r') as f:
            content = f.read()
        # 确认已修复（不再写margin_data.json）
        if 'fetch_margin_data' in content and 'etf_subscription' not in content.split('def main')[1]:
            issues.append("fetch_margin_etf.py 仍存在两融覆盖风险")
        if not issues:
            print(f"    ✓ 无写入冲突")
    
    return issues


def audit_frontend_page():
    """前端主页面：检查逻辑详解页章节完整"""
    print(f"  🖥️ 前端页面...")
    issues = []
    
    html_path = os.path.join(BASE, 'index_master.html')
    if not os.path.exists(html_path):
        html_path = os.path.join(DIST_DIR, 'index.html')
    if not os.path.exists(html_path):
        return ["找不到主页面"]
    
    required = ['铁律', '总览页', '数据监控', '预判信号', '选股核心信号', '金股池构成', 
                '基础评分', '增强评分因子', '个股查询评分', '扩展信息', '自选复盘']
    
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html = f.read()
        
        missing = [r for r in required if r not in html]
        if missing:
            issues.append(f"逻辑详解缺少: {missing}")
            print(f"    ✗ 缺少章节: {missing}")
        else:
            print(f"    ✓ 逻辑详解章节完整")
    except Exception as e:
        issues.append(str(e))
    
    return issues


# ═══════════════════════════════════════════════════════════
# 📊 3. 清理无关联文件（每次必做）
# ═══════════════════════════════════════════════════════════
def cleanup():
    """清理临时文件、空文件"""
    print("\n" + "=" * 60)
    print("📊 步骤3: 清理临时文件")
    print("=" * 60)
    
    deleted = []
    known_junk = ['.enhance_log.txt', 'concept_history.json', 
                  'stock_sector_cache.json', 'zsxq_selenium_snapshot.txt']
    
    for fname in known_junk:
        for d in [DATA_DIR, os.path.join(DIST_DIR, 'data')]:
            fpath = os.path.join(d, fname)
            if os.path.exists(fpath):
                os.remove(fpath)
                deleted.append(f"{os.path.basename(d)}/{fname}")
    
    # 清理空 backup 目录
    for item in os.listdir(BASE):
        ipath = os.path.join(BASE, item)
        if os.path.isdir(ipath) and item.startswith('backup_'):
            try:
                if not os.listdir(ipath):
                    os.rmdir(ipath)
                    deleted.append(item)
            except: pass
    
    if deleted:
        print(f"  ✓ 已清理: {', '.join(deleted)}")
    else:
        print(f"  ✓ 无待清理文件")
    
    return deleted


# ═══════════════════════════════════════════════════════════
# 💾 4. 备份
# ═══════════════════════════════════════════════════════════
def perform_backup():
    """执行备份"""
    print("\n" + "=" * 60)
    print("💾 步骤4: 执行备份")
    print("=" * 60)
    
    issues = []
    backup_dir = os.path.join(BASE, f'backup_{TODAY}')
    
    try:
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        os.makedirs(backup_dir)
        
        # HTML
        src = os.path.join(DIST_DIR, 'index_master.html')
        if os.path.exists(src):
            shutil.copy2(src, backup_dir)
        
        # data/
        data_src = os.path.join(BASE, 'data')
        if os.path.exists(data_src):
            shutil.copytree(data_src, os.path.join(backup_dir, 'data'))
        
        # .py 脚本
        py_count = 0
        for f in os.listdir(BASE):
            if f.endswith('.py'):
                shutil.copy2(os.path.join(BASE, f), backup_dir)
                py_count += 1
        
        size = sum(os.path.getsize(os.path.join(dp, f)) 
                   for dp, _, fn in os.walk(backup_dir) for f in fn)
        print(f"  ✅ {backup_dir} ({size/1024/1024:.1f}MB, {py_count}脚本)")
        
        # 清理旧备份
        cutoff = datetime.datetime.now() - datetime.timedelta(days=7)
        for item in os.listdir(BASE):
            ipath = os.path.join(BASE, item)
            if not os.path.isdir(ipath): continue
            m = re.match(r'backup_(\d{8})$', item)
            if not m: continue
            try:
                d = datetime.datetime.strptime(m.group(1), '%Y%m%d')
                if d < cutoff:
                    shutil.rmtree(ipath)
                    print(f"  🗑️  已清理过期: {item}")
            except: pass
        
    except Exception as e:
        issues.append(f"备份异常: {e}")
        print(f"  ✗ {e}")
    
    return issues


# ═══════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════
def main():
    print("⚡ 九宝量化 21:00 增量审核+备份")
    print(f"   日期: {TODAY_DATE}")
    print()
    
    # 🔴 0. 双机同步
    sync_issues = sync_dual_machine()
    
    # 📊 1. 分析变更
    affected = analyze_changes()
    
    # 📊 2. 增量审计（仅审变更模块）
    audit_results = incremental_audit(affected) if affected else {}
    
    # 📊 3. 清理
    cleaned = cleanup()
    
    # 💾 4. 备份
    backup_issues = perform_backup()
    
    # ═══ 汇总 ═══
    print("\n" + "=" * 60)
    print("📋 审核汇总")
    print("=" * 60)
    
    total = len(sync_issues)
    for k, v in audit_results.items():
        total += len(v)
    total += len(backup_issues)
    
    if not affected:
        print("  今天无代码变更，跳过增量审计")
    else:
        for module, issues in audit_results.items():
            icon = '✗' if issues else '✓'
            print(f"  {icon} {module}: {'通过' if not issues else str(len(issues))+'个问题'}")
    print(f"  {'✗' if sync_issues else '✓'} 双机同步: {'通过' if not sync_issues else '注意'}")
    print(f"  ✓ 文件清理: {len(cleaned)}个")
    print(f"  {'✗' if backup_issues else '✓'} 备份: {'通过' if not backup_issues else '异常'}")
    
    if total > 0:
        print(f"\n⚠  {total} 个问题需关注（备份已完成不受影响）")
    else:
        print(f"\n✅ 全部通过")

if __name__ == '__main__':
    main()
