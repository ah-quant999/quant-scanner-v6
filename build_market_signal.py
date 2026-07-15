#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_market_signal.py — 市场面信号独立页生成

读取 data/sh_index_fib.json、data/macro_data.json、data/fomc_summary.json、
data/cffex_holdings.json、data/sector_fund_flow.json、data/margin_data.json、
data/north_fund.json、data/lhb_result.json，
按技术面/资金面/机构面三维度评分，生成 standalone/market_signal.html。

本页只展示评分与数据速览，数据来源说明统一放到 standalone/guide.html。
"""
import json
import os
import math

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'standalone', 'market_signal.html')


def load(name):
    p = os.path.join(BASE, 'data', name)
    if not os.path.exists(p):
        return {}
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)


def score_color(n):
    if n >= 7:
        return '#2e7d32'
    if n >= 5:
        return '#e65100'
    if n >= 3:
        return '#ef6c00'
    return '#c62828'


def score_bg(n):
    if n >= 7:
        return 'rgba(46,125,50,0.06)'
    if n >= 5:
        return 'rgba(230,81,0,0.05)'
    if n >= 3:
        return 'rgba(239,108,0,0.05)'
    return 'rgba(198,40,40,0.06)'


def score_border(n):
    if n >= 7:
        return '#4caf50'
    if n >= 5:
        return '#ff9800'
    if n >= 3:
        return '#ff9800'
    return '#ef5350'


def parse_date(s):
    if not s:
        return None
    s = str(s)
    if len(s) == 8 and s.isdigit():
        return f'{s[:4]}-{s[4:6]}-{s[6:]}'
    return s


def fresh_of(date_str):
    from datetime import datetime
    d = None
    s = str(date_str) if date_str else ''
    for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%Y%m%d'):
        try:
            d = datetime.strptime(s, fmt)
            break
        except Exception:
            pass
    if not d:
        return ('—', '#bbb', '无日期')
    diff = (datetime.now() - d).days
    if diff < 0:
        diff = 0
    if diff <= 2:
        return ('✅', '#2e7d32', f'{diff}天前')
    if diff <= 7:
        return ('🟡', '#f9a825', f'{diff}天前')
    if diff <= 31:
        return ('🟠', '#ef6c00', f'{diff}天前')
    return ('🔴', '#c62828', f'{diff}天前')


def safe(v):
    if v is None or v == '':
        return '—'
    return str(v)


def build():
    fib = load('sh_index_fib.json')
    macro = load('macro_data.json')
    fomc = load('fomc_summary.json')
    cffex = load('cffex_holdings.json')
    sf = load('sector_fund_flow.json')
    margin = load('margin_data.json')
    north = load('north_fund.json')
    lhb = load('lhb_result.json')

    cur = fib.get('current', {})
    windows = fib.get('windows', [])
    nxt = next((w for w in windows if w.get('status') == 'future'), None)

    # 技术面评分
    tech_score = 5
    tech_detail = []
    decline_days = cur.get('days_down', 0) or 0
    decline_pct = cur.get('total_pct', 0) or 0
    if decline_days >= 30:
        tech_score -= 2
        tech_detail.append(f'回调{decline_days}天')
    elif decline_days >= 15:
        tech_score -= 1
        tech_detail.append(f'回调{decline_days}天')
    if decline_pct <= -5:
        tech_score -= 2
        tech_detail.append(f'累计{decline_pct:.1f}%')
    elif decline_pct <= -3:
        tech_score -= 1
    if nxt:
        dleft = nxt.get('days_left', 99)
        if dleft <= 5:
            tech_detail.append(f'窗口临近:{nxt.get("name")}({nxt.get("date")})')
        elif dleft <= 10:
            tech_detail.append(f'窗口:{nxt.get("name")}({nxt.get("date")})')
    if not tech_detail:
        tech_detail.append('震荡整理')
    tech_score = max(1, min(10, tech_score))

    # 资金面评分
    fund_score = 5
    fund_detail = []
    msh = margin.get('sh', [])
    mlast = msh[-1] if msh else {}
    rz = mlast.get('rz_balance', 0) or 0
    ssum = sf.get('summary', {})
    sf_in = ssum.get('in_count', 0) or 0
    sf_out = ssum.get('out_count', 0) or 0
    if rz >= 15000:
        fund_score += 2
        fund_detail.append('两融≥1.5万亿')
    elif rz >= 14500:
        fund_score += 1
        fund_detail.append('两融回升')
    if sf_in > sf_out:
        fund_score += 1
        fund_detail.append('板块流入>流出')
    elif sf_out > sf_in:
        fund_score -= 1
        fund_detail.append('板块流出>流入')
    if sf_in >= 8:
        fund_score += 1
        fund_detail.append('多板块流入')
    fund_score = max(1, min(10, fund_score))

    # 机构面评分
    inst_score = 5
    inst_detail = []
    cffex_net = cffex.get('net_total', 0) or 0
    cffex_abs = abs(cffex_net)
    if cffex_net < -8000:
        inst_score -= 2
        inst_detail.append(f'净空{cffex_abs}手')
    elif cffex_net < -3000:
        inst_score -= 1
        inst_detail.append(f'净空{cffex_abs}手')
    elif cffex_net > 3000:
        inst_score += 1
        inst_detail.append(f'净多{cffex_abs}手')
    fomc_label = fomc.get('summary', '')
    if '转鹰' in fomc_label or '加息' in fomc_label:
        inst_score -= 1
        inst_detail.append('FOMC转鹰')
    inst_score = max(1, min(10, inst_score))

    avg_score = round((tech_score + fund_score + inst_score) / 3)
    sentiment_word = '偏多' if avg_score >= 7 else '震荡' if avg_score >= 5 else '偏空'
    sentiment_color = score_color(avg_score)

    # 综合结论
    sf_ind_in = [s for s in sf.get('sectors_in', []) if s.get('type') == '行业']
    sf_ind_out = [s for s in sf.get('sectors_out', []) if s.get('type') == '行业']
    sf_total_in = sum(x.get('net', 0) for x in sf_ind_in)
    sf_total_out = sum(abs(x.get('net', 0)) for x in sf_ind_out)
    lhb_stocks = lhb.get('stocks', [])
    pure_res = [s for s in lhb_stocks if s.get('category') == '纯共振']
    if avg_score >= 7 and sf_total_in > sf_total_out and len(pure_res) >= 2:
        final_word = '🟢 资金+机构+技术面共振偏多，可适当参与。'
    elif avg_score >= 5:
        final_word = '🟡 多空分歧，资金偏多但宏观承压，轻仓等待方向。'
    else:
        final_word = '🔴 偏空信号为主，建议减仓观望。'

    # 数据行
    def row(name, value, prev, date, vc=None):
        f = fresh_of(date)
        val_html = f'<b style="color:{vc or "#1a1a1a"};">{safe(value)}</b>' if value not in (None, '') else '<span style="color:#bbb;">—</span>'
        return f'<tr style="border-top:1px solid #f2f2f2;">' \
               f'<td style="padding:5px 8px;color:#444;font-size:11px;white-space:nowrap;">{name}</td>' \
               f'<td style="padding:5px 8px;text-align:center;font-size:12px;white-space:nowrap;">{val_html}</td>' \
               f'<td style="padding:5px 8px;color:#888;font-size:10.5px;white-space:nowrap;">{safe(prev)}</td>' \
               f'<td style="padding:5px 8px;color:#999;font-size:10.5px;white-space:nowrap;">{safe(parse_date(date))}</td>' \
               f'<td style="padding:5px 8px;text-align:center;font-size:11px;" title="{f[2]}"><span style="color:{f[1]};">{f[0]}</span></td>' \
               '</tr>'

    def dim_block(title, icon, score, rows):
        sc = score_color(score)
        h = f'<div style="margin-bottom:18px;">' \
            f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;">' \
            f'<span style="font-size:13px;font-weight:700;color:#333;">{icon} {title}</span>' \
            f'<span style="font-size:11px;font-weight:700;color:#fff;background:{sc};border-radius:10px;padding:1px 8px;">{score}/10</span>' \
            f'</div>' \
            f'<table style="width:100%;border-collapse:collapse;background:#fff;border:1px solid #ececec;border-radius:6px;overflow:hidden;">' \
            f'<tr style="background:#fafafa;">' \
            f'<th style="padding:4px 8px;text-align:left;font-size:10px;color:#999;font-weight:600;">指标</th>' \
            f'<th style="padding:4px 8px;text-align:center;font-size:10px;color:#999;font-weight:600;">现值</th>' \
            f'<th style="padding:4px 8px;text-align:left;font-size:10px;color:#999;font-weight:600;">前值/环比</th>' \
            f'<th style="padding:4px 8px;text-align:left;font-size:10px;color:#999;font-weight:600;">日期</th>' \
            f'<th style="padding:4px 8px;text-align:center;font-size:10px;color:#999;font-weight:600;">新</th>' \
            f'</tr>'
        for r in rows:
            h += r
        h += '</table></div>'
        return h

    # 技术面行
    top_sec = sf.get('sectors_in', [{}])[0] if sf.get('sectors_in') else {}
    sf_upd = sf.get('update_time', '')
    south = north.get('south_flow', {})
    tech_rows = [
        row('上证指数', cur.get('index'), f'高点 {cur.get("peak_close")}({cur.get("peak_date")})', cur.get('date'), '#1a1a1a'),
        row('连跌天数', cur.get('days_down'), '—', cur.get('date'), '#c62828' if cur.get('days_down', 0) >= 15 else '#1a1a1a'),
        row('累计跌幅', f'{cur.get("total_pct")}%', '—', cur.get('date'), '#c62828' if (cur.get('total_pct') or 0) < 0 else '#2e7d32'),
        row('运行模式', cur.get('mode'), '—', cur.get('date')),
        row('下个时间窗', f'{nxt.get("name")} {nxt.get("date")}' if nxt else None, '—', nxt.get('date') if nxt else None),
    ]

    # 资金面行
    south_total = south.get('total')
    south_dir = south.get('direction', '')
    fund_rows = [
        row('两融余额', f'{rz}亿' if rz else None, '—', mlast.get('date_raw'), '#1a1a1a'),
        row('板块资金流', f'{sf_in}流入 / {sf_out}流出', '—', sf_upd),
        row('最强板块', f'{top_sec.get("name")} +{top_sec.get("net")}亿(连{top_sec.get("consecutive_days")}天)' if top_sec.get('name') else None, '—', sf_upd),
        row('南向资金(日)', f'{south_total}亿 {south_dir}' if south_total is not None else None, '—', north.get('update_time')),
        row('北向资金', '已停披露', '2024.5起港交所停披露', north.get('update_time') or '—', '#888'),
    ]

    # 机构面行
    cf = cffex.get('positions', {})
    cf_date = cffex.get('date', '')
    def net_cell(v): return f'{v}手' if v is not None else '—'
    inst_rows = [
        row('中信整体净持仓', f'{cffex_net}手', '—', cf_date, '#c62828' if cffex_net < 0 else '#2e7d32'),
        row('沪深300(IF)', net_cell(cf.get('IF', {}).get('net')), '—', cf_date, '#c62828' if (cf.get('IF', {}).get('net') or 0) < 0 else '#2e7d32'),
        row('中证500(IC)', net_cell(cf.get('IC', {}).get('net')), '—', cf_date, '#c62828' if (cf.get('IC', {}).get('net') or 0) < 0 else '#2e7d32'),
        row('中证1000(IM)', net_cell(cf.get('IM', {}).get('net')), '—', cf_date, '#c62828' if (cf.get('IM', {}).get('net') or 0) < 0 else '#2e7d32'),
        row('上证50(IH)', net_cell(cf.get('IH', {}).get('net')), '—', cf_date, '#c62828' if (cf.get('IH', {}).get('net') or 0) < 0 else '#2e7d32'),
        row('FOMC利率', f'{fomc.get("last_rate")}%' if fomc.get('last_rate') is not None else None, f'下次会议 {fomc.get("next_meeting_date") or "—"}', fomc.get('last_rate_date')),
    ]

    def score_card(name, icon, score, detail):
        return f'''<div style="background:{score_bg(score)};border-radius:10px;padding:14px 8px 12px;border-left:3px solid {score_border(score)};text-align:center;">
          <div style="display:flex;align-items:center;justify-content:center;gap:3px;margin-bottom:6px;">
            <span style="font-size:16px;">{icon}</span>
            <span style="font-size:12px;font-weight:600;color:#666;">{name}</span>
          </div>
          <div style="font-size:28px;font-weight:800;color:{score_color(score)};text-align:center;margin-bottom:6px;letter-spacing:-1px;">{score}<span style="font-size:12px;font-weight:500;color:#aaa;margin-left:1px;">/10</span></div>
          <div style="background:#e0e0e0;border-radius:3px;height:5px;overflow:hidden;margin-bottom:6px;">
            <div style="background:{score_color(score)};height:100%;width:{score*10}%;border-radius:3px;"></div>
          </div>
          <div style="font-size:10px;color:#888;line-height:1.45;text-align:center;">{detail}</div>
        </div>'''

    update_time = (sf.get('update_time') or fib.get('update_time') or macro.get('update_time') or '—')

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>短线/中线市场温度计 · 九宝量化 V6.0</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:"PingFang SC","Microsoft YaHei",-apple-system,sans-serif;background:#f4f6fa;color:#1f2a44;padding-top:52px;-webkit-font-smoothing:antialiased;}}
.header{{background:linear-gradient(135deg,#283593,#5c6bc0);color:#fff;padding:12px 20px;position:fixed;top:0;left:0;right:0;z-index:999;box-shadow:0 2px 10px rgba(0,0,0,.15);}}
.header .brand{{font-size:16px;font-weight:800;letter-spacing:.5px;}}
.header .sub{{font-size:11px;opacity:.75;margin-top:2px;}}
.header a{{color:#c5cae9;text-decoration:none;}}
.wrap{{max-width:960px;margin:18px auto;padding:0 14px 70px;}}
.hero{{background:#fff;border-radius:14px;padding:16px 18px;box-shadow:0 2px 14px rgba(30,42,68,.06);margin-bottom:14px;}}
.hero-title{{font-size:16px;font-weight:800;color:#1f2a44;margin-bottom:8px;display:flex;align-items:center;gap:8px;}}
.hero-verdict{{font-size:12px;line-height:1.7;padding:8px 14px;background:linear-gradient(135deg,#fafbfc,#f0f2f5);border-radius:8px;border:1px solid #eaeaea;margin-bottom:14px;}}
.score-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:18px;}}
.sec{{background:#fff;border-radius:14px;padding:16px 18px;box-shadow:0 2px 14px rgba(30,42,68,.06);margin-bottom:14px;}}
.sec-title{{font-size:14px;font-weight:800;color:#1f2a44;margin-bottom:10px;}}
.method-link{{font-size:11px;color:#5c6bc0;margin-top:10px;text-align:right;}}
.update-time{{font-size:10px;color:#9aa3b5;margin-top:8px;text-align:right;}}
@media(max-width:720px){{.score-grid{{grid-template-columns:1fr;}}}}
</style>
</head>
<body>
<div class="header">
  <div class="sub"><a href="../index.html" onclick="try{{localStorage.setItem('from_tab','shmonitor');}}catch(e){{}}">← 返回数据监控</a> &nbsp;|&nbsp; 技术/资金/机构三维度</div>
</div>

<div class="wrap">
  <div class="sec">
    <div class="sec-title">📋 三维度数据速览</div>
    {dim_block('技术面', '📉', tech_score, tech_rows)}
    {dim_block('资金面', '💰', fund_score, fund_rows)}
    {dim_block('机构面', '🏦', inst_score, inst_rows)}
  </div>
</div>
</body>
</html>'''

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"[build_market_signal] ✓ 已生成 {OUT}")


if __name__ == '__main__':
    build()
