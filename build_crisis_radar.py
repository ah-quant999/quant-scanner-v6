#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_crisis_radar.py — 危机雷达独立页生成

读取 data/crisis_data.json，按六维（流动性/利率/经济/房地产/全球/汇率）
汇总各指标危险分，再按 货币40%/经济35%/全球25% 加权合成 0-100 综合危机指数，
生成 standalone/crisis_radar.html（全部平铺、无折叠、无下钻）。

综合指数模型：
  指标危险分(0-100) = 近1年历史分位（high_bad 用分位；low_bad 用 100-分位）；历史缺失回退阈值。
  维度分 = 该维度成员指标危险分均值。
  大类分：货币=其成员均值，经济=其成员均值，全球=其成员均值。
  综合指数 = 0.40×货币 + 0.35×经济 + 0.25×全球。

⚠️ 禁止删除（见 DO_NOT_DELETE.txt）。
"""
import json
import os
import math

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, 'data', 'crisis_data.json')
OUT = os.path.join(BASE, 'standalone', 'crisis_radar.html')

# 大类权重
CAT_WEIGHT = {'货币': 0.40, '经济': 0.35, '全球': 0.25}
# 雷达六维（顺序即绘制顺序，顶部开始顺时针）
RADAR_DIMS = ['流动性', '利率', '经济', '房地产', '全球', '汇率']

# 颜色
C_RED = '#E24B4A'
C_ORANGE = '#EF9F27'
C_GREEN = '#4FA85A'
C_INK = '#1f2a44'
C_SUB = '#8a93a6'


def color_of(score):
    if score is None:
        return C_SUB
    if score >= 50:
        return C_RED
    if score >= 30:
        return C_ORANGE
    return C_GREEN


def status_word(score):
    if score is None:
        return '无数据'
    if score >= 70:
        return '危机'
    if score >= 50:
        return '警惕'
    if score >= 30:
        return '关注'
    return '平稳'


def composite_status(idx):
    if idx >= 70:
        return ('系统性危机', C_RED)
    if idx >= 50:
        return ('高度警惕', C_RED)
    if idx >= 30:
        return ('需要关注', C_ORANGE)
    return ('整体平稳', C_GREEN)


def fmt_val(v, unit):
    if v is None:
        return '--'
    if isinstance(v, float):
        if abs(v) >= 100:
            s = f'{v:,.0f}'
        elif abs(v) >= 10:
            s = f'{v:.2f}'
        else:
            s = f'{v:.4f}'.rstrip('0').rstrip('.')
    else:
        s = str(v)
    if unit == '$':
        return '$' + s
    return s + (unit if unit and unit != '$' else '')


def trend_html(trend, direction):
    """趋势箭头：结合方向判断改善/恶化上色（红=恶化，绿=改善）"""
    if trend == 'flat':
        return '<span style="color:#b0b8c8;">→ 持平</span>'
    rising = trend == 'up'
    # high_bad: 上升=恶化(红) ; low_bad: 上升=改善(绿)
    worse = (rising and direction == 'high_bad') or ((not rising) and direction == 'low_bad')
    color = C_RED if worse else C_GREEN
    arrow = '↑' if rising else '↓'
    label = '恶化' if worse else '改善'
    return f'<span style="color:{color};font-weight:700;">{arrow} {label}</span>'


def mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 1) if xs else None


def build():
    with open(DATA, 'r', encoding='utf-8') as f:
        d = json.load(f)
    inds = d['indicators']
    update_time = d.get('update_time', '')

    # ── 维度分 ──
    dim_scores = {}
    for dim in RADAR_DIMS:
        members = [v['score'] for v in inds.values() if v.get('dim') == dim]
        dim_scores[dim] = mean(members)

    # ── 大类分 ──
    cat_scores = {}
    for cat in ('货币', '经济', '全球'):
        members = [v['score'] for v in inds.values() if v.get('cat') == cat]
        cat_scores[cat] = mean(members)

    # ── 综合指数 ──
    composite = 0.0
    wsum = 0.0
    for cat, w in CAT_WEIGHT.items():
        if cat_scores.get(cat) is not None:
            composite += cat_scores[cat] * w
            wsum += w
    composite = round(composite / wsum, 1) if wsum else 0
    comp_word, comp_color = composite_status(composite)

    # ── 渲染雷达 SVG ──
    radar = render_radar(dim_scores)

    # ── 渲染三大类卡片区 ──
    cat_meta = {
        '货币': ('💧 货币流动性', '流动性 · 利率', '货币'),
        '经济': ('🏭 经济基本面', '经济 · 房地产', '经济'),
        '全球': ('🌍 全球风险', '全球 · 汇率', '全球'),
    }
    sections_html = ''
    for cat in ('货币', '经济', '全球'):
        title, sub, _ = cat_meta[cat]
        cs = cat_scores[cat]
        cards = ''
        for key, v in inds.items():
            if v.get('cat') != cat:
                continue
            cards += render_card(v)
        cscolor = color_of(cs)
        sections_html += f'''
  <div class="sec">
    <div class="sec-head">
      <div class="sec-title">{title}<span class="sec-sub">{sub}</span></div>
      <div class="sec-score" style="color:{cscolor};">{cs if cs is not None else '--'}<span class="sec-score-lbl">大类危险分</span></div>
    </div>
    <div class="grid">{cards}</div>
  </div>'''

    # ── 顶部三大类条 ──
    catbar = ''
    for cat, w in CAT_WEIGHT.items():
        cs = cat_scores[cat]
        col = color_of(cs)
        pct = cs if cs is not None else 0
        catbar += f'''
      <div class="catrow">
        <div class="catname">{cat}<span class="catw">权重{int(w*100)}%</span></div>
        <div class="cattrack"><div class="catfill" style="width:{pct}%;background:{col};"></div></div>
        <div class="catval" style="color:{col};">{cs if cs is not None else '--'}</div>
      </div>'''

    html = PAGE.format(
        update_time=update_time,
        composite=composite,
        comp_word=comp_word,
        comp_color=comp_color,
        gauge=render_gauge(composite, comp_color),
        radar=radar,
        catbar=catbar,
        sections=sections_html,
    )

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ 已生成 {OUT}")
    print(f"   综合危机指数: {composite} ({comp_word})")
    print(f"   大类: 货币{cat_scores['货币']} / 经济{cat_scores['经济']} / 全球{cat_scores['全球']}")
    print(f"   六维: " + ' '.join(f'{k}{dim_scores[k]}' for k in RADAR_DIMS))


def render_card(v):
    name = v['name']
    unit = v.get('unit', '')
    score = v.get('score')
    col = color_of(score)
    val = fmt_val(v.get('value'), unit)
    freq = v.get('freq', '')
    date = v.get('date', '')
    pct = v.get('percentile')
    tr = trend_html(v.get('trend', 'flat'), v.get('dir', 'high_bad'))
    sw = status_word(score)
    # 分位条
    if pct is not None:
        pctbar = f'''
        <div class="pctwrap">
          <div class="pcttrack"><div class="pctfill" style="left:{pct}%;"></div></div>
          <div class="pcttxt">近1年分位 <b style="color:{col};">{pct}%</b></div>
        </div>'''
    else:
        pctbar = '<div class="pctwrap"><div class="pcttxt" style="color:#b0b8c8;">阈值判定（无1年历史）</div></div>'
    # 方向说明
    dirtxt = '越高越危险' if v.get('dir') == 'high_bad' else '越低越危险'
    return f'''
      <div class="card" style="border-top:3px solid {col};">
        <div class="c-head">
          <span class="c-name">{name}</span>
          <span class="c-freq">{freq}</span>
        </div>
        <div class="c-val" style="color:{col};">{val}</div>
        <div class="c-meta">{tr} &nbsp;·&nbsp; {dirtxt}</div>
        {pctbar}
        <div class="c-foot">
          <span class="c-badge" style="background:{col};">{sw} {score if score is not None else ''}</span>
          <span class="c-date">{date}</span>
        </div>
      </div>'''


def render_gauge(idx, color):
    """半环仪表（0-100）"""
    # 半圆，从左(180°)到右(0°)
    r = 90
    cx, cy = 120, 120
    frac = max(0, min(100, idx)) / 100.0
    ang = math.pi * (1 - frac)  # 180°->0°
    x = cx + r * math.cos(ang)
    y = cy - r * math.sin(ang)
    # 背景弧
    bg = f'<path d="M {cx-r} {cy} A {r} {r} 0 0 1 {cx+r} {cy}" fill="none" stroke="#e9edf4" stroke-width="16" stroke-linecap="round"/>'
    # 进度弧
    large = 0
    prog = f'<path d="M {cx-r} {cy} A {r} {r} 0 {large} 1 {x:.1f} {y:.1f}" fill="none" stroke="{color}" stroke-width="16" stroke-linecap="round"/>'
    return f'''<svg viewBox="0 0 240 140" width="100%" style="max-width:260px;">
      {bg}{prog}
      <text x="{cx}" y="{cy-8}" text-anchor="middle" font-size="46" font-weight="800" fill="{color}">{idx:.0f}</text>
      <text x="{cx}" y="{cy+16}" text-anchor="middle" font-size="12" fill="#8a93a6">综合危机指数 / 100</text>
    </svg>'''


def render_radar(dim_scores):
    """六维雷达图 SVG"""
    cx, cy, R = 150, 145, 105
    n = len(RADAR_DIMS)
    # 轴角度：顶部开始顺时针
    pts_grid = []
    axis_lines = ''
    labels = ''
    for i, dim in enumerate(RADAR_DIMS):
        ang = -math.pi / 2 + 2 * math.pi * i / n
        # 网格圈顶点(满值)
        gx = cx + R * math.cos(ang)
        gy = cy + R * math.sin(ang)
        axis_lines += f'<line x1="{cx}" y1="{cy}" x2="{gx:.1f}" y2="{gy:.1f}" stroke="#e2e7f0" stroke-width="1"/>'
        # 标签
        lx = cx + (R + 22) * math.cos(ang)
        ly = cy + (R + 22) * math.sin(ang)
        anchor = 'middle'
        if math.cos(ang) > 0.3:
            anchor = 'start'
        elif math.cos(ang) < -0.3:
            anchor = 'end'
        sc = dim_scores.get(dim)
        col = color_of(sc)
        labels += (f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" font-size="12.5" font-weight="700" fill="{C_INK}" dominant-baseline="middle">{dim}</text>'
                   f'<text x="{lx:.1f}" y="{ly+14:.1f}" text-anchor="{anchor}" font-size="11" font-weight="800" fill="{col}" dominant-baseline="middle">{sc if sc is not None else "--"}</text>')

    # 同心网格圈 (25/50/75/100)
    rings = ''
    for frac in (0.25, 0.5, 0.75, 1.0):
        ring_pts = []
        for i in range(n):
            ang = -math.pi / 2 + 2 * math.pi * i / n
            rx = cx + R * frac * math.cos(ang)
            ry = cy + R * frac * math.sin(ang)
            ring_pts.append(f'{rx:.1f},{ry:.1f}')
        rings += f'<polygon points="{" ".join(ring_pts)}" fill="none" stroke="#eef1f7" stroke-width="1"/>'

    # 数据多边形
    data_pts = []
    dots = ''
    for i, dim in enumerate(RADAR_DIMS):
        ang = -math.pi / 2 + 2 * math.pi * i / n
        sc = dim_scores.get(dim) or 0
        rr = R * (sc / 100.0)
        px = cx + rr * math.cos(ang)
        py = cy + rr * math.sin(ang)
        data_pts.append(f'{px:.1f},{py:.1f}')
        col = color_of(dim_scores.get(dim))
        dots += f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.5" fill="{col}"/>'
    poly = f'<polygon points="{" ".join(data_pts)}" fill="rgba(226,75,74,0.16)" stroke="{C_RED}" stroke-width="2"/>'

    return f'''<svg viewBox="0 0 300 300" width="100%" style="max-width:320px;">
      {rings}{axis_lines}{poly}{dots}{labels}
    </svg>'''


# ════════════════════════════════════════
#  页面模板
# ════════════════════════════════════════
PAGE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>危机雷达 · 九宝量化 V6.0</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:"PingFang SC","Microsoft YaHei",-apple-system,sans-serif;background:#f4f6fa;color:#1f2a44;padding-top:52px;-webkit-font-smoothing:antialiased;}}
.header{{background:linear-gradient(135deg,#232b3e,#111726);color:#fff;padding:12px 20px;position:fixed;top:0;left:0;right:0;z-index:999;box-shadow:0 2px 10px rgba(0,0,0,.15);}}
.header .brand{{font-size:16px;font-weight:800;letter-spacing:.5px;}}
.header .sub{{font-size:11px;opacity:.65;margin-top:2px;}}
.header a{{color:#8fb7ff;text-decoration:none;}}
.wrap{{max-width:1040px;margin:12px auto;padding:0 14px 50px;}}
/* Hero */
.hero{{background:#fff;border-radius:14px;padding:14px 16px;box-shadow:0 2px 10px rgba(30,42,68,.06);margin-bottom:12px;display:grid;grid-template-columns:1.1fr 1fr;gap:14px;align-items:center;}}
.hero-left{{display:flex;flex-direction:column;align-items:center;text-align:center;}}
.hero-badge{{display:inline-block;font-size:13px;font-weight:800;color:#fff;padding:4px 14px;border-radius:18px;margin-top:4px;}}
.catbars{{width:100%;margin-top:12px;display:flex;flex-direction:column;gap:7px;}}
.catrow{{display:flex;align-items:center;gap:10px;}}
.catname{{width:88px;font-size:12.5px;font-weight:700;display:flex;flex-direction:column;color:#3a445c;}}
.catw{{font-size:10px;color:#9aa3b5;font-weight:500;}}
.cattrack{{flex:1;height:9px;background:#eef1f7;border-radius:5px;overflow:hidden;}}
.catfill{{height:100%;border-radius:5px;transition:width .6s;}}
.catval{{width:34px;text-align:right;font-size:14px;font-weight:800;}}
.hero-right{{display:flex;flex-direction:column;align-items:center;}}
.radar-cap{{font-size:12px;color:#8a93a6;margin-top:2px;}}
/* Section */
.sec{{background:#fff;border-radius:12px;padding:10px 12px;box-shadow:0 2px 8px rgba(30,42,68,.06);margin-bottom:10px;}}
.sec-head{{display:flex;justify-content:space-between;align-items:baseline;border-bottom:1px solid #eef1f7;padding-bottom:6px;margin-bottom:8px;}}
.sec-title{{font-size:14px;font-weight:800;color:#1f2a44;}}
.sec-sub{{font-size:10px;color:#9aa3b5;font-weight:500;margin-left:6px;}}
.sec-score{{font-size:18px;font-weight:800;display:flex;flex-direction:column;align-items:flex-end;line-height:1;}}
.sec-score-lbl{{font-size:9px;color:#9aa3b5;font-weight:500;margin-top:2px;}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:7px;}}
.card{{background:#fbfcfe;border:1px solid #eef1f7;border-radius:9px;padding:7px 9px;}}
.c-head{{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;}}
.c-name{{font-size:11.5px;font-weight:700;color:#2a3550;}}
.c-freq{{font-size:8.5px;color:#9aa3b5;background:#eef1f7;padding:1px 5px;border-radius:5px;}}
.c-val{{font-size:18px;font-weight:800;line-height:1.05;}}
.c-meta{{font-size:9.5px;color:#8a93a6;margin-top:2px;}}
.pctwrap{{margin-top:5px;}}
.pcttrack{{position:relative;height:5px;background:linear-gradient(90deg,#4FA85A,#EF9F27,#E24B4A);border-radius:3px;}}
.pctfill{{position:absolute;top:-2px;width:2px;height:9px;background:#1f2a44;border-radius:2px;transform:translateX(-1px);box-shadow:0 0 0 2px #fff;}}
.pcttxt{{font-size:9.5px;color:#8a93a6;margin-top:2px;}}
.c-foot{{display:flex;justify-content:space-between;align-items:center;margin-top:5px;}}
.c-badge{{font-size:9.5px;font-weight:700;color:#fff;padding:1px 6px;border-radius:6px;}}
.c-date{{font-size:9px;color:#b0b8c8;}}
/* Method */
.method{{background:#fff;border-radius:12px;padding:12px 14px;box-shadow:0 2px 8px rgba(30,42,68,.06);font-size:11.5px;line-height:1.75;color:#5a6478;}}
.method b{{color:#3a445c;}}
.method .mt{{font-size:14px;font-weight:800;color:#1f2a44;margin-bottom:8px;}}
@media(max-width:720px){{
  .hero{{grid-template-columns:1fr;}}
  .grid{{grid-template-columns:repeat(2,1fr);}}
}}
@media(max-width:460px){{
  .grid{{grid-template-columns:1fr;}}
}}
</style>
</head>
<body>
<div class="header">
  <div class="brand">🛰️ 六维预警雷达 · 九宝量化 V6.0</div>
  <div class="sub"><a href="../index.html" onclick="try{{localStorage.setItem('from_tab','shmonitor');}}catch(e){{}}">← 返回数据监控</a> &nbsp;|&nbsp; 六维预警雷达 · 月度/季度视角 · 中长线 · 数据更新：{update_time}</div>
</div>

<div class="wrap">

  <div class="hero">
    <div class="hero-left">
      {gauge}
      <div class="hero-badge" style="background:{comp_color};">{comp_word}</div>
      <div class="catbars">{catbar}</div>
    </div>
    <div class="hero-right">
      {radar}
      <div class="radar-cap">六维危险分（越靠外越危险 · 0-100）</div>
    </div>
  </div>

  {sections}


</div>
</body>
</html>'''


if __name__ == '__main__':
    build()
