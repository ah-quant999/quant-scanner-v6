#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DO NOT DELETE: 独立页生成脚本，standalone/ 目录的来源 (see DO_NOT_DELETE.md)
"""
独立页面提取 v6（最小改动方案）
只改两处：1) CSS 让所有面板可见 2) 隐藏标签栏 + 注入顶栏渲染JS
用法: python extract_panels_v6.py
"""

import re
import os
import shutil

BASE_HTML = "dist/index.html"
OUTPUT_DIR = "standalone"

PANELS = [
    ("overview",   "总览"),
    ("shmonitor",  "数据监控"),
    ("predict",    "预判信号"),
    ("gold",       "金股观测"),
    ("query",      "个股查询"),
    ("health",     "健康看板"),
]

def main():
    print(f"读取 {BASE_HTML} ...")
    with open(BASE_HTML, 'r', encoding='utf-8') as f:
        content = f.read()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"  大小: {len(content)//1024}KB")

    ut_match = re.search(r'"update_time"\s*:\s*"([^"]+)"', content)
    # 优先取扫描数据时间(盘中更新频繁)，fallback 到任意 update_time
    # 导航页应反映"页面最近何时重建"，而非某个特定数据源的时间
    from datetime import datetime
    scan_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"  数据时间: {scan_time} (构建时间)")

    # === 全局修改（对所有页面都一样）===
    # 1. 把 .tab-panel { display: none; } 改为 display: block;
    base_modified = content.replace(
        '.tab-panel { display: none; }',
        '.tab-panel { display: block !important; }'
    )
    base_modified = base_modified.replace(
        '.tab-panel{display:none}',
        '.tab-panel{display:block!important}'
    )
    print("  OK 已修改 .tab-panel 规则为全部可见")

    # 2. 给目标面板加 active 类 + 去掉内联 display:none
    for pid, _ in PANELS:
        base_modified = base_modified.replace(
            f'<div class="tab-panel" id="panel-{pid}" style="display:none;">',
            f'<div class="tab-panel active" id="panel-{pid}">'
        )

    # 2.5 折叠隐藏 panel-logic 的 iframe（standalone 全部可见模式下，min-height:600px iframe 会把下方内容顶出屏幕）
    base_modified = base_modified.replace(
        '<iframe id="logicFrame"',
        '<iframe id="logicFrame" style="display:none;"'
    )
    base_modified = base_modified.replace(
        '<div class="tab-panel" id="panel-logic">',
        '<div class="tab-panel" id="panel-logic" style="display:none;">'
    )

    # 对每个面板生成独立文件
    for target_id, target_name in PANELS:
        print(f"\n生成: {target_id}.html ({target_name}) ...")

        modified = base_modified

        # 隐藏其他面板（用CSS）
        css_hides = ''
        for pid, _ in PANELS:
            if pid != target_id:
                css_hides += f'  #panel-{pid} {{ display: none !important; }}\n'

        # 注入到 </head> 前
        inject = f'''<style>
/* ====== 独立页面：只显示 {target_name} ====== */
html,body{{height:auto;min-height:100vh;overflow-y:auto;padding-top:56px}}
.header{{display:none!important}}
.sa-bar{{
  background:linear-gradient(135deg,#1a237e,#283593);color:#fff;
  padding:10px 20px;display:flex;align-items:center;gap:10px;
  position:fixed;top:0;left:0;right:0;z-index:9999;
}}
.sa-bar .r{{font-size:20px}} .sa-bar .b{{font-size:15px;font-weight:700}}
.sa-bar .s{{font-size:10px;opacity:.7}}
.sa-bar a{{
  margin-left:auto;background:rgba(255,255,255,.15);
  border:1px solid rgba(255,255,255,.3);color:#fff;
  padding:4px 12px;border-radius:4px;text-decoration:none;font-size:11px;
}}
.sa-bar a:hover{{background:rgba(255,255,255,.25)}}
.tabs{{display:none!important}}
{css_hides}
</style>
<script>
// 顶栏
document.addEventListener('DOMContentLoaded',function(){{
  var d=document.createElement('div');d.className='sa-bar';
  d.innerHTML='<span class=r>🚀</span>'
    +'<div><div class=b>九宝量化 V6.0</div><div class=s>独立 · {target_name}</div></div>'
    +'<a href=index.html onclick="if(history.length>1){{history.back();return false}}">← 全部</a>';
  document.body.insertBefore(d,document.body.firstChild);
}});
// 渲染
window.addEventListener('load',function(){{
  var list=[
    ['renderRecommend',0],['renderSummaryCards',0],['renderShMonitor',0],
    ['renderAISummary',0],['renderETFFlow',0],['renderSectorFundFlow',0],
    ['renderUnlistedDataCards',0],['renderCffex',0],['renderConceptRanking',0],
    ['renderMacro',0],['renderUpdateSchedule',0],['renderCalendar',0],
    ['renderHealthDashboard',0],
    ['renderLimitUpHeatmap',0],['renderCapitalFlowCard',0],['renderTop10Daily',0],['renderSectorRotation',0],
    ['renderSuspensionAlert',0],['renderIpoScore',0],
    ['renderPredictSummary',0],['renderSelectedSignals',0],
    ['renderTrendFlow',0],['renderSectorRS',0],['renderMacroOverview',0]
  ];
  list.forEach(function(item){{
    try {{
      var fn=window[item[0]];
      if(typeof fn==='function'){{
        if(item[0]==='renderGoldPool'&&window.NT_DATA&&window.NT_DATA.gold_pool)
          fn(window.NT_DATA.gold_pool,window.NT_DATA.analysis_date);
        else if(item[0]==='renderLhbPredict'&&!window.LHB_DATA)return;
        else if(item[0]==='renderNorthFund'&&!window.NORTH_FUND_DATA)return;
        else fn();
      }}
    }}catch(e){{}}
  }});
  console.log('[standalone] rendered');
}});
</script>
</head>'''

        last_head = modified.rfind('</head>')
        final = modified[:last_head] + inject + modified[last_head+7:]

        # 独立页已位于 standalone/ 目录，内部链接需要从 standalone/xxx.html 降级为 xxx.html
        final = final.replace('href="standalone/', 'href="')
        final = final.replace('href=\"standalone/', 'href=\"')
        final = final.replace("href='standalone/", "href='")
        final = final.replace('src="standalone/', 'src="')
        final = final.replace('src=\"standalone/', 'src=\"')
        final = final.replace("src='standalone/", "src='")

        # standalone 页面不需要 from_tab 切换（单一 panel 展示，无 tab 可切）
        _ft_block = '// [2026-07-13 修复] 独立页(localStorage.from_tab)返回时，切换到原 tab\n'
        _ft_block += 'try {\n'
        _ft_block += '  var fromTab = localStorage.getItem(\'from_tab\');\n'
        _ft_block += '  if (fromTab) {\n'
        _ft_block += '    localStorage.removeItem(\'from_tab\');\n'
        _ft_block += '    switchTabByName(fromTab);\n'
        _ft_block += '  }\n'
        _ft_block += '} catch(e) { /* localStorage 不可用就跳过 */ }'
        final = final.replace(_ft_block, '')

        out_path = os.path.join(OUTPUT_DIR, f"{target_id}.html")
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(final)
        print(f"  OK {len(final)//1024}KB")

    # 导航首页
    cards = ''.join(f'''<a href="{p}.html" class=c><div class=ci>📊</div><div class=cn>{n}</div></a>''' for p,n in PANELS)
    # extra standalone pages (not in PANELS list)
    _extra = [
        ('guide',    '📖', '逻辑详解'),
        ('triple_consensus', '📊', '历史追踪'),
    ]
    # 所有面板（含三线/多维追踪）均指向同目录 standalone 版，避免跳到根目录主站体系
    _rel = lambda p: f"{p}.html"
    cards += ''.join(f'''<a href="{_rel(p)}" class=c><div class=ci>{i}</div><div class=cn>{n}</div></a>''' for p,i,n in _extra)

    idx=f'''<!--
⚠️ 独立页导航 — 逻辑详解 (guide.html) 严禁移除或重写为空。
-->
<!DOCTYPE html><html lang=zh-CN><head><meta charset=UTF-8>
<meta name=viewport content="width=device-width,initial-scale=1.0">
<title>九宝量化 V6.0 - 导航</title>
<style>*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:"PingFang SC","Microsoft YaHei",sans-serif;background:linear-gradient(135deg,#e8eaf6,#f5f7fa);min-height:100vh}}
.hd{{background:linear-gradient(135deg,#1a237e,#283593);color:#fff;padding:40px 24px 28px;text-align:center}}
.hd r{{font-size:48px}} .hd b{{font-size:26px;font-weight:700}} .hd s{{font-size:12px;opacity:.6}} .hd t{{font-size:11px;opacity:.5;margin-top:6px}}
.ct{{max-width:800px;margin:40px auto;padding:0 16px 80px}}
.n{{background:#e8f5e9;border-left:3px solid #4caf50;padding:14px 18px;border-radius:0 8px 8px 0;font-size:12px;color:#2e7d32;margin-bottom:24px;line-height:1.9}}
.gs{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px}}
.c{{background:#fff;border-radius:12px;padding:22px 14px;text-decoration:none;color:#333;box-shadow:0 2px 8px rgba(0,0,0,.06);text-align:center;display:block;transition:transform .15s}}
.c:hover{{transform:translateY(-3px);box-shadow:0 6px 20px rgba(0,0,0,.12)}}
.ci{{font-size:28px;margin-bottom:8px}} .cn{{font-size:14px;font-weight:600}}
.ft{{text-align:center;padding:32px 16px;font-size:11px;color:#bbb;margin-top:48px;border-top:1px solid #e0e0e0}}</style></head>
<body><div class=hd><div class=r>🚀</div><div class=b>九宝量化 V6.0</div><div class=s>独立页面导航</div><div class=t>{scan_time}</div></div>
<div class=ct><div class=gs>{cards}</div></div>
<div class=ft>不构成投资建议</div></body></html>'''
    with open(os.path.join(OUTPUT_DIR,'index.html'),'w',encoding='utf-8') as f:
        f.write(idx)
    print(f"\nOK {len(PANELS)} 个面板完成 | {OUTPUT_DIR}/index.html")

if __name__=='__main__':
    main()
