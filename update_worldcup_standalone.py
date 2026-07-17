#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚠️ 禁止删除此脚本！用户(小九)明确要求锁定版本，不得重写/覆盖为空！
#
update_worldcup_standalone.py — 用 data/worldcup.json（旧版 5000 次 Monte Carlo 格式）
重建 standalone/worldcup.html，包含：
  · 加权预测冠军（Monte Carlo 5000 次）
  · 小组赛胜率榜 / 晋级概率
  · 加权攻防效率 / 各洲对比 / 小组积分榜 / 赛程表
  · 数字彩票概率分析
"""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data", "worldcup.json")
STANDALONE = os.path.join(BASE, "standalone", "worldcup.html")

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def pts(t):
    return t['w'] * 3 + t['d']

def gd(t):
    return t['gf'] - t['ga']

def win_rate(t):
    p = t['w'] + t['d'] + t['l'] or 1
    return round((t['w'] * 100 + t['d'] * 33) / p)

def fmt_data_time(ts):
    return ts[:19].replace('T', ' ')

def render_odds(odds):
    html = '<div style="display:flex;flex-direction:column;gap:6px;">'
    for i, o in enumerate(odds[:8]):
        w = 100 if i == 0 else round(o['prob'] / odds[0]['prob'] * 80)
        c = '#ffd700' if i < 3 else ('#e67e22' if i < 6 else '#3498db')
        html += ('<div style="display:flex;align-items:center;gap:8px;">'
                 f'<span style="font-size:12px;width:20px;">#{i+1}</span>'
                 f'<span style="flex:1;min-width:60px;font-weight:600;">{esc(o["n"])}</span>'
                 f'<span style="font-weight:800;color:{c};width:42px;text-align:right;">{o["prob"]}%</span>'
                 f'<div style="flex:1;height:7px;background:#e0e0e0;border-radius:4px;">'
                 f'<div style="height:100%;width:{w}%;background:{c};border-radius:4px;"></div></div></div>')
    html += '</div>'
    return html

def render_win_rate_list(all_teams):
    sorted_t = sorted(all_teams, key=lambda t: -win_rate(t))
    html = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:3px 14px;font-size:11px;">'
    for i, t in enumerate(sorted_t[:24]):
        wr = win_rate(t)
        color = '#c62828' if wr >= 75 else ('#e65100' if wr >= 50 else '#666')
        html += (f'<div style="display:flex;justify-content:space-between;padding:2px 0;">'
                 f'<span>{i+1}. {esc(t["n"])}</span>'
                 f'<span style="font-weight:600;color:{color};">{wr}%</span></div>')
    html += '</div>'
    return html

def render_qual_probs(qual_probs):
    html = '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;">'
    for gid in sorted(qual_probs.keys()):
        probs = qual_probs[gid]
        sorted_p = sorted(probs.items(), key=lambda x: -x[1])
        html += f'<div style="background:#fff;border-radius:4px;padding:6px 8px;">'
        html += f'<div style="font-weight:700;font-size:12px;color:#1a2a4a;margin-bottom:4px;">组 {gid}</div>'
        for name, prob in sorted_p:
            bar_color = '#c62828' if prob >= 90 else ('#e67e22' if prob >= 50 else ('#3498db' if prob >= 20 else '#b0bec5'))
            html += ('<div style="display:flex;align-items:center;gap:4px;margin-bottom:2px;font-size:11px;">'
                     f'<span style="width:46px;text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{esc(name)}</span>'
                     f'<div style="width:50px;height:5px;background:#e0e0e0;border-radius:2px;flex-shrink:0;">'
                     f'<div style="height:100%;width:{max(5, prob)}%;background:{bar_color};border-radius:2px;"></div></div>'
                     f'<span style="font-weight:700;color:{bar_color};">{prob}%</span></div>')
        html += '</div>'
    html += '</div>'
    return html

def render_adj_eff(all_teams):
    attack = sorted(all_teams, key=lambda t: -(t.get('adj_gf', t['gf'])))[:10]
    defense = sorted(all_teams, key=lambda t: (t.get('adj_ga', t['ga'])))[:10]
    
    a_html = ''
    for i, t in enumerate(attack):
        raw = t['gf']
        adj = float(t.get('adj_gf', t['gf']))
        a_html += (f'<div style="display:flex;justify-content:space-between;padding:3px 0;font-size:12px;">'
                   f'<span>{i+1}. {esc(t["n"])}</span>'
                   f'<span style="color:#888;">原始{raw}球 → <span style="font-weight:600;color:#c62828;">加权{adj:.1f}</span></span></div>')
    
    d_html = ''
    for i, t in enumerate(defense):
        raw = t['ga']
        adj = float(t.get('adj_ga', t['ga']))
        d_html += (f'<div style="display:flex;justify-content:space-between;padding:3px 0;font-size:12px;">'
                   f'<span>{i+1}. {esc(t["n"])}</span>'
                   f'<span style="color:#888;">原始{raw}球 → <span style="font-weight:600;color:#2e7d32;">加权{adj:.1f}</span></span></div>')
    
    return a_html, d_html

def render_regions(all_teams):
    region_names = {'UEFA': '欧洲', 'CONMEBOL': '南美', 'AFC': '亚洲', 'CAF': '非洲', 'CONCACAF': '北美', 'OFC': '大洋洲'}
    regions = {}
    for t in all_teams:
        reg = t.get('region', '?')
        regions.setdefault(reg, []).append(t)
    data = []
    for k, name in region_names.items():
        lst = regions.get(k, [])
        total = len(lst) or 1
        total_pts = sum(pts(t) for t in lst)
        data.append({'name': name, 'n': len(lst), 'avg': total_pts / total})
    data.sort(key=lambda x: -x['avg'])
    html = '<div style="display:grid;grid-template-columns:repeat(6,1fr);gap:6px;font-size:10px;">'
    for d in data:
        html += (f'<div style="background:#fff;border-radius:4px;padding:5px 6px;text-align:center;">'
                 f'<div style="font-weight:700;">{d["name"]}</div>'
                 f'<div style="font-size:11px;">{d["n"]}队</div>'
                 f'<div style="color:#e65100;">均{d["avg"]:.1f}分</div></div>')
    html += '</div>'
    return html

def render_groups(groups):
    html = '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;">'
    for g in groups:
        sorted_t = sorted(g['teams'], key=lambda t: (-pts(t), -gd(t), -t['gf']))
        html += '<div style="background:#f8f9fa;border-radius:6px;padding:8px 10px;">'
        html += f'<div style="font-weight:700;font-size:13px;color:#1a2a4a;margin-bottom:6px;text-align:center;">组 {g["id"]}</div>'
        for i, t in enumerate(sorted_t):
            bg = '#e8f5e9' if i < 2 else ''
            prefix = '⬆' if i < 2 else ''
            html += (f'<div style="padding:3px 0;font-size:11px;{bg and "background:"+bg+";border-radius:3px;padding-left:4px;" or ""}display:flex;justify-content:space-between;">'
                     f'<span>{prefix}{esc(t["name"])}</span>'
                     f'<span style="color:#888;">{t["w"]}/{t["d"]}/{t["l"]} {pts(t)}分 {gd(t):+d}</span></div>')
        html += '</div>'
    html += '</div>'
    return html

def render_schedule(results, knockout):
    # group results by date
    by_date = {}
    for m in results:
        by_date.setdefault(m['d'], []).append(m)
    
    ko_by_date = {}
    for m in knockout:
        ko_by_date.setdefault(m['date'], []).append(m)
    
    months = {'Jun': 6, 'Jul': 7}
    def sort_key(dd):
        parts = dd.split(' ')
        return (months.get(parts[0], 0), int(parts[1]) if len(parts) > 1 else 0)
    
    html = ''
    if ko_by_date:
        html += '<div style="font-weight:700;font-size:15px;color:#333;margin-bottom:8px;">🏆 淘汰赛阶段（倒序：最新在前）</div>'
        # 倒序：决赛(Jul 19)置顶，整段从新到旧
        for dd in sorted(ko_by_date.keys(), key=sort_key, reverse=True):
            matches = ko_by_date[dd]
            html += '<div style="display:flex;gap:10px;padding:4px 0;font-size:13px;border-bottom:1px solid #f0f0f0;">'
            html += f'<span style="color:#888;min-width:70px;font-weight:600;">{dd}</span><span>'
            for mi, m in enumerate(matches):
                if mi > 0:
                    html += '、'
                html += f'<span style="color:#666;font-size:12px;margin-right:4px;">[{esc(m["round"])}]</span>{esc(m["home"])} vs {esc(m["away"])}'
                if m.get('score'):
                    html += f' <b style="color:#c62828;font-size:14px;">{esc(m["score"])}</b>'
                html += f' <span style="color:#999;font-size:12px;">— {esc(m.get("venue", ""))}</span>'
            html += '</span></div>'
    
    if by_date:
        html += '<div style="margin-top:14px;">'
        html += '<div style="font-weight:700;font-size:15px;color:#333;margin:10px 0 8px;">⚽ 小组赛阶段</div>'
        for dd in sorted(by_date.keys(), key=sort_key, reverse=True):
            matches = by_date[dd]
            html += '<div style="display:flex;gap:10px;padding:4px 0;font-size:13px;border-bottom:1px solid #f0f0f0;">'
            html += f'<span style="color:#888;min-width:70px;font-weight:600;">{dd}</span><span>'
            for mi, m in enumerate(matches):
                if mi > 0:
                    html += '、'
                html += f'{esc(m["h"])} vs {esc(m["a"])}'
                if m.get('s'):
                    html += f' <b style="color:#c62828;font-size:14px;">{esc(m["s"])}</b>'
            html += '</span></div>'
        html += '</div>'
    return html

# ===== 彩票概率计算 =====
def C(n, k):
    if k > n or k < 0:
        return 0
    r = 1
    for i in range(1, k + 1):
        r = r * (n - i + 1) // i
    return r

def fmt_odds(n):
    if n >= 1e8:
        return f'{n/1e8:.2f}亿'
    return f'{int(n/10000):,}万'

def render_lottery():
    ssq = [
        {'name': '一等奖', 'cond': '6+1', 'count': 1, 'bonus': '浮动(500-1000万)'},
        {'name': '二等奖', 'cond': '6+0', 'count': 15, 'bonus': '浮动(10-50万)'},
        {'name': '三等奖', 'cond': '5+1', 'count': C(6, 5) * C(27, 1), 'bonus': '3000元'},
        {'name': '四等奖', 'cond': '5+0/4+1', 'count': C(6, 5) * C(27, 1) * 15 + C(6, 4) * C(27, 2), 'bonus': '200元'},
        {'name': '五等奖', 'cond': '4+0/3+1', 'count': C(6, 4) * C(27, 2) * 15 + C(6, 3) * C(27, 3), 'bonus': '10元'},
        {'name': '六等奖', 'cond': '2+1/1+1/0+1', 'count': C(6, 2) * C(27, 4) + C(6, 1) * C(27, 5) + C(27, 6), 'bonus': '5元'},
    ]
    ssq_base = C(33, 6) * C(16, 1)

    dlt = [
        {'name': '一等奖', 'cond': '5+2', 'count': 1, 'bonus': '浮动(封顶1000万)'},
        {'name': '二等奖', 'cond': '5+1', 'count': C(2, 1) * C(10, 1), 'bonus': '浮动(约20万)'},
        {'name': '三等奖', 'cond': '5+0', 'count': C(10, 2), 'bonus': '10000元'},
        {'name': '四等奖', 'cond': '4+2', 'count': C(5, 4) * C(30, 1), 'bonus': '3000元'},
        {'name': '五等奖', 'cond': '4+1', 'count': C(5, 4) * C(30, 1) * C(2, 1) * C(10, 1), 'bonus': '300元'},
        {'name': '六等奖', 'cond': '3+2', 'count': C(5, 3) * C(30, 2), 'bonus': '200元'},
        {'name': '七等奖', 'cond': '4+0', 'count': C(5, 4) * C(30, 1) * C(10, 2), 'bonus': '100元'},
        {'name': '八等奖', 'cond': '3+1/2+2', 'count': C(5, 3) * C(30, 2) * C(2, 1) * C(10, 1) + C(5, 2) * C(30, 3), 'bonus': '15元'},
        {'name': '九等奖', 'cond': '3+0/2+1/1+2/0+2', 'count': C(5, 3) * C(30, 2) * C(10, 2) + C(5, 2) * C(30, 3) * C(2, 1) * C(10, 1) + C(5, 1) * C(30, 4) + C(30, 5), 'bonus': '5元'},
    ]
    dlt_base = C(35, 5) * C(12, 2)

    ssq_fixed = {'三等奖': 3000, '四等奖': 200, '五等奖': 10, '六等奖': 5}
    dlt_fixed = {'三等奖': 10000, '四等奖': 3000, '五等奖': 300, '六等奖': 200, '七等奖': 100, '八等奖': 15, '九等奖': 5}

    def expected(rules, base, fixed):
        t = 0
        for r in rules:
            b = fixed.get(r['name'], 5000000 if '一' in r['name'] else 100000)
            t += b * r['count'] / base
        return t

    ssq_er = expected(ssq, ssq_base, ssq_fixed)
    dlt_er = expected(dlt, dlt_base, dlt_fixed)
    ssq_return = ssq_er / 2 * 100
    dlt_return = dlt_er / 2 * 100
    better = '双色球' if ssq_er > dlt_er else '大乐透'
    better_er = ssq_er if ssq_er > dlt_er else dlt_er
    worse_er = dlt_er if ssq_er > dlt_er else ssq_er
    better_rp = ssq_return if ssq_er > dlt_er else dlt_return
    worse_rp = dlt_return if ssq_er > dlt_er else ssq_return
    year_loss = 312 - ssq_er * 156
    month_loss = 26 - ssq_er * 13
    daily_ssq = 312 - ssq_er * 156
    daily_dlt = 312 - dlt_er * 156

    html = ''
    html += '<div style="background:linear-gradient(135deg,#e3f2fd,#bbdefb);border:2px solid #1976d2;border-radius:12px;padding:16px 20px;margin-bottom:16px;">'
    html += '<div style="font-size:15px;font-weight:900;color:#0d47a1;margin-bottom:10px;">📋 AI测算结论</div>'
    html += '<div style="font-size:12px;line-height:2;color:#333;">'
    html += '<b style="color:#c62828;">1. 两者均为负期望值博弈</b> — 长期必亏，数学上没有"赢钱"可能<br>'
    html += f'<b style="color:#e65100;">2. 若非要二选一：买 <span style="font-size:16px;background:#e8f5e9;padding:2px 8px;border-radius:4px;">🔴 {better}</span></b> — 期望回报 ¥{better_er:.2f} vs ¥{worse_er:.2f}，回本率 {better_rp:.1f}% vs {worse_rp:.1f}%<br>'
    html += '<b style="color:#2e7d32;">3. 推荐玩法：2元单注，不追加不复式</b> — 复式/追加倍数只会同步放大投入和亏损期望，不改变负期望值本质<br>'
    html += f'<b style="color:#6a1b9a;">4. 预算建议：每月不超过 26元（每周3次×2元×4周+2元缓冲）</b> — 月度期望亏损约 ¥{month_loss:.0f}，年度约 ¥{year_loss:.0f}<br>'
    html += '<b style="color:#424242;">5. 正确心态：</b>把2元理解成"买2分钟白日梦"的娱乐消费，而不是投资。中奖是意外，不中是常态。'
    html += '</div></div>'

    html += '<table style="width:100%;border-collapse:collapse;font-size:12px;margin-bottom:16px;">'
    html += '<tr style="background:#1a2a3a;color:#ff9800;"><th style="padding:6px 10px;">指标</th><th style="text-align:center;padding:6px 10px;">🔴 双色球</th><th style="text-align:center;padding:6px 10px;">🟡 大乐透</th></tr>'
    html += '<tr><td style="padding:6px 10px;">单注价格</td><td style="text-align:center;">2元</td><td style="text-align:center;">2元</td></tr>'
    html += f'<tr><td style="padding:6px 10px;">头奖概率</td><td style="text-align:center;color:#c62828;">1/{fmt_odds(ssq_base)}</td><td style="text-align:center;color:#c62828;">1/{fmt_odds(dlt_base)}</td></tr>'
    html += '<tr><td style="padding:6px 10px;">任一中奖概率</td><td style="text-align:center;">6.71%</td><td style="text-align:center;">6.67%</td></tr>'
    html += f'<tr><td style="padding:6px 10px;">单注期望回报</td><td style="text-align:center;color:#c62828;">¥{ssq_er:.2f}</td><td style="text-align:center;color:#c62828;">¥{dlt_er:.2f}</td></tr>'
    html += f'<tr><td style="padding:6px 10px;">回本率</td><td style="text-align:center;">{ssq_return:.1f}%</td><td style="text-align:center;">{dlt_return:.1f}%</td></tr>'
    html += '</table>'

    def prize_table(title, rules, base):
        t = f'<div style="margin-bottom:14px;"><b style="font-size:13px;">{title}</b>'
        t += '<table style="width:100%;border-collapse:collapse;font-size:11px;margin-top:6px;">'
        t += '<tr style="background:#1a2a3a;color:#ff9800;"><th style="padding:4px 8px;">奖项</th><th style="padding:4px 8px;">条件</th><th style="text-align:right;padding:4px 8px;">概率</th><th style="text-align:right;padding:4px 8px;">1/</th><th style="padding:4px 8px;">奖金</th></tr>'
        for i, r in enumerate(rules):
            p = r['count'] / base
            c = '#ff9800' if i < 3 else '#888'
            t += f'<tr><td style="padding:3px 8px;color:{c};">{r["name"]}</td><td style="padding:3px 8px;color:#888;">{r["cond"]}</td><td style="text-align:right;padding:3px 8px;font-size:10px;">{p*100:.8f}%</td><td style="text-align:right;padding:3px 8px;">{round(base/r["count"]):,}</td><td style="padding:3px 8px;">{r["bonus"]}</td></tr>'
        t += '</table></div>'
        return t

    html += prize_table('🔴 双色球 各等奖概率 (33选6 + 16选1)', ssq, ssq_base)
    html += prize_table('🟡 大乐透 各等奖概率 (35选5 + 12选2)', dlt, dlt_base)

    html += '<div style="background:linear-gradient(135deg,#fffde7,#fff8e1);border:1px solid #ffe082;border-radius:10px;padding:12px 16px;font-size:12px;line-height:1.8;margin-top:12px;">'
    html += '<b style="color:#e65100;">🎲 趣味概率对照</b><br>'
    html += '• 双色球头奖 ≈ 一个人在同一年被雷劈中3次的概率<br>'
    html += '• 大乐透头奖 ≈ 连续抛24次硬币全部正面的概率<br>'
    html += '• 双色球中六等奖(5元)概率 5.9% — 买17注约能中小奖一次，但净亏29元<br>'
    html += '• 复式投注(如7+1)多花14元，只增加6种组合，中奖概率从1/1772万提升到7/1772万，几乎无意义<br>'
    html += f'• 年预算156元(每周3注)：双色球期望亏损¥{daily_ssq:.0f}，大乐透期望亏损¥{daily_dlt:.0f}'
    html += '</div>'

    return html


def main():
    with open(DATA, "r", encoding="utf-8") as f:
        d = json.load(f)

    update_time = d.get('update_time', '')
    matchday = d.get('matchday', '')
    status_note = d.get('status_note', '')
    odds = d.get('odds', [])
    all_teams = d.get('all_teams', [])
    qual_probs = d.get('qual_probs', {})
    adj_eff = d.get('adj_eff', {})
    groups = d.get('groups', [])
    results = d.get('results', [])
    knockout = d.get('knockout', [])

    a_html, d_html = render_adj_eff(all_teams)

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>2026世界杯 · 竞彩娱乐独立页</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:"PingFang SC","Microsoft YaHei",sans-serif;background:#f5f7fa;color:#333;padding-top:56px;}}
.header{{background:linear-gradient(135deg,#1a237e,#283593);color:#fff;padding:16px 24px;position:fixed;top:0;left:0;right:0;z-index:9999;}}
.header-brand{{font-size:18px;font-weight:700;}}
.header-sub{{font-size:11px;opacity:.7;margin-top:4px;}}
a{{color:#90caf9;text-decoration:none}}
.container{{max-width:1000px;margin:24px auto;padding:0 16px 60px;}}
.card{{background:#fff;border-radius:10px;padding:20px;box-shadow:0 1px 4px rgba(0,0,0,0.06);margin-bottom:16px;}}
h2{{font-size:16px;margin-bottom:12px;border-left:4px solid #ff6b35;padding-left:8px;}}
.disclaimer{{background:linear-gradient(135deg,#fff3e0,#ffe0b2);border:2px solid #ff9800;border-radius:10px;padding:16px 20px;margin-bottom:16px;}}
.disclaimer-title{{font-size:20px;font-weight:900;color:#e65100;letter-spacing:4px;}}
.disclaimer-sub{{font-size:12px;color:#bf360c;margin-top:6px;}}
.updated{{font-size:12px;color:#999;margin-bottom:12px;}}
</style>
</head>
<body>
<div class="header">
  <div class="header-brand">🏆 九宝量化 V6.0 — 2026世界杯 & 竞彩娱乐</div>
  <div class="header-sub"><a href="index.html" onclick="if(history.length>1){{history.back();return false}}">← 返回导航</a> | 独立页面（静态）· 数据更新：{esc(update_time)}</div>
</div>

<div class="container">

  <div class="disclaimer">
    <div class="disclaimer-title">🤖 AI测算，纯属娱乐 🎲</div>
    <div class="disclaimer-sub">以下所有概率均为数学理论值，不构成任何投注建议。理性参与，量力而行。足球是圆的，一切皆有可能。</div>
  </div>

  <div class="updated">数据更新：{esc(update_time)} · {esc(matchday)} · 每日 07:30 更新</div>
'''
    # status_note banner removed (淘汰赛开战提示已过时，不再渲染)

    html += '''
  <div class="card">
    <h2>🏆 夺冠概率 TOP8（Monte Carlo 5000 次模拟）</h2>
'''
    html += render_odds(odds)
    html += '  </div>\n'

    html += '''
  <div class="card">
    <h2>🎲 晋级概率预测（Monte Carlo 5000 次模拟）</h2>
'''
    html += render_qual_probs(qual_probs)
    html += '  </div>\n'

    html += '''
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px;">
    <div class="card">
      <h2>📊 小组赛胜率榜（前24）</h2>
'''
    html += render_win_rate_list(all_teams)
    html += '''
    </div>
    <div class="card">
      <h2>⚖️ 加权进攻效率 TOP10</h2>
'''
    html += a_html
    html += '''
    </div>
  </div>

  <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px;">
    <div class="card">
      <h2>🛡️ 加权防守效率 TOP10</h2>
'''
    html += d_html
    html += '''
    </div>
    <div class="card">
      <h2>🌍 各洲足联表现对比</h2>
'''
    html += render_regions(all_teams)
    html += '''
    </div>
  </div>

  <div class="card">
    <h2>⚽ 小组积分榜</h2>
'''
    html += render_groups(groups)
    html += '  </div>\n'

    html += '''
  <div class="card">
    <h2>📅 赛程表（已结束场次标红比分）</h2>
'''
    html += render_schedule(results, knockout)
    html += '  </div>\n'

    html += '''
  <div class="card" style="background:linear-gradient(135deg,#f3e5f5,#e1bee7);border:2px solid #8e24aa;">
    <h2>🎰 数字彩票概率分析</h2>
'''
    html += render_lottery()
    html += '  </div>\n'

    html += '''
</div>
</body>
</html>
'''

    with open(STANDALONE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ 已生成 {STANDALONE}")
    print(f"   球队: {len(all_teams)} 支")
    print(f"   赛程: {len(results)} 场小组赛 + {len(knockout)} 场淘汰赛")
    top_str = " / ".join([f"{o['n']} {o['prob']}%" for o in odds[:3]]) if odds else "(无)"
    print(f"   夺冠概率 TOP: {top_str}")

if __name__ == "__main__":
    main()
